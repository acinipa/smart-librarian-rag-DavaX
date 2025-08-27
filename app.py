# app.py
# Smart Librarian — RAG + Tool Calling + External Moderation + Follow-up + Voice Mode (EN only)
# --------------------------------------------------------------------------------------------
# - RAG: ChromaDB (local, persistent) + OpenAI embeddings
# - Chat: OpenAI Chat Completions (gpt-4o-mini)
# - Tool: get_summary_by_title(title) — returns a full summary from a local dictionary
# - Moderation: OpenAI Moderation API (omni-moderation-latest), Pydantic-safe parsing
# - Follow-up: “yes / tell me more / vreau rezumat” triggers summary for last recommendation
# - Voice Mode: English speech ONLY (typed input disabled while Voice mode is ON)

import json
import os
import re
import tempfile
import unicodedata
from typing import Dict, Any, List

import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI
from audio_recorder_streamlit import audio_recorder  # mic widget

from rag import bootstrap_index, RAGEngine
from tools import get_summary_by_title

load_dotenv()

# -------------------------
# Streamlit page setup & CSS
# -------------------------
st.set_page_config(page_title="Smart Librarian DavaX", page_icon="📚", layout="wide")
st.markdown("""
<style>
.main > div { padding-top: 1rem; }
.block-card {
  border: 1px solid #e9ecef; background: #ffffff; border-radius: 16px; padding: 1rem 1.25rem;
  box-shadow: 0 8px 24px rgba(0,0,0,0.06);
}
.badge { background:#f1f3f5; border-radius:999px; padding:.2rem .6rem; font-size:.8rem; }
.reco-title { font-weight:700; font-size:1.2rem; margin-bottom:.2rem;}
.small-muted { color:#6c757d; font-size:.9rem;}
.code { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size:.86rem; }
</style>
""", unsafe_allow_html=True)

st.title("📚 Smart Librarian DavaX")

client = OpenAI()

BLOCK_MESSAGE = (
    "Please keep the conversation respectful. I'm an AI chatbot that **recommends books** "
    "based on your interests (e.g., *friendship*, *magic*, *war*, *dystopia*). "
    "Tell me what kind of book you're looking for."
)

def check_with_openai_moderation(text: str) -> Dict[str, Any]:
    """
    Returns: { 'blocked': bool, 'reasons': list[str], 'raw': dict }
    Resilient to API hiccups: if moderation fails, we fall back to NOT blocked.
    """
    try:
        resp = client.moderations.create(model="omni-moderation-latest", input=text)
        result = resp.results[0]
        cats = getattr(result, "categories", None)
        try:
            cats_dict = cats.model_dump() if cats else {}
        except Exception:
            cats_dict = {}
        reasons = [k for k, v in cats_dict.items() if bool(v)]
        flagged = bool(getattr(result, "flagged", False))
        return {"blocked": flagged, "reasons": reasons, "raw": resp.model_dump()}
    except Exception as e:
        # Log-friendly fallback; do NOT block the convo on moderation outage
        return {"blocked": False, "reasons": ["moderation_error"], "raw": {"error": str(e)}}

# -------------------------
# Bootstrap vector store
# -------------------------
with st.spinner("Initializing the book collection..."):
    try:
        total = bootstrap_index()
        st.caption(f"Vector store ready (collection: **book_summaries**, {total} books).")
    except Exception as e:
        st.error(f"Initialization error: {e}")
        st.stop()

rag = RAGEngine()

# -------------------------
# Tool schema for function calling
# -------------------------
TOOL_SCHEMA = [{
    "type": "function",
    "function": {
        "name": "get_summary_by_title",
        "description": "Returns the full summary for an exact book title.",
        "parameters": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "The EXACT selected book title"}
            },
            "required": ["title"]
        }
    }
}]

SYSTEM_PROMPT = (
    "You are Smart Librarian. You receive user reading preferences and a list of candidates "
    "from a vector store. Your job: pick EXACTLY ONE book from the candidates that best matches "
    "the user's request. After you choose, ALWAYS call `get_summary_by_title` with the EXACT title "
    "and present the full summary in your final answer. Do NOT ask if the user wants a summary "
    "before calling the tool. Do not invent titles not present in candidates. "
    "STAY STRICTLY IN ROLE: you only recommend books. If asked for anything else, politely say you "
    "can only recommend books and ask for reading preferences."
)

# -------------------------
# Chat memory
# -------------------------
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT}]
if "last_reco_title" not in st.session_state:
    st.session_state.last_reco_title = None

# -------------------------
# Sidebar help + Voice Mode (EN only)
# -------------------------
with st.sidebar:
    st.markdown("#### How it works")
    st.write("- RAG: semantic search (ChromaDB + OpenAI embeddings).")
    st.write("- GPT picks **one book** from the retrieved candidates and ALWAYS fetches its summary.")
    st.divider()
    voice_mode = st.toggle(
        "🎙️ Voice mode (English voice only)",
        value=False,
        help="Use your mic to ask the chatbot in **English only**. Typed input is disabled while Voice mode is ON."
    )
    st.caption("Voice mode uses your microphone and accepts **ENGLISH speech only**; "
               "non-English speech will be rejected. While Voice mode is ON, typing is disabled.")
    st.divider()
    st.write("Try:")
    st.code("I want a book about freedom and social control.", language="markdown")
    st.code("What do you recommend if I love fantasy adventures?", language="markdown")
    st.code("I want friendship and magic.", language="markdown")

# -------------------------
# Lightweight follow-up detector (EN + RO)
# -------------------------
_LEET_MAP = str.maketrans({"@":"a","$":"s","0":"o","1":"i","!":"i","3":"e","7":"t","4":"a","5":"s","8":"b"})
def _strip_diacritics(text: str) -> str:
    nfkd = unicodedata.normalize("NFKD", text)
    return "".join(ch for ch in nfkd if not unicodedata.combining(ch))
def _normalize(text: str) -> str:
    t = text.lower()
    t = _strip_diacritics(t)
    t = t.translate(_LEET_MAP)
    t = re.sub(r"\s+", " ", t).strip()
    return t

FOLLOWUP_PATTERNS = [
    r"\byes\b", r"\bok\b", r"\byep\b", r"\byup\b",
    r"\btell me more\b", r"\bmore\b", r"\bsummary\b", r"\bdetails?\b",
    r"\bshow (me )?(more|the summary)\b",
    r"\bda\b", r"\bas vrea sa stiu mai multe\b", r"\bmai multe\b", r"\bvreau rezumat\b",
    r"\bvreau detalii\b", r"\bspune-mi mai multe\b", r"\bvreau sa stiu mai multe\b"
]
FOLLOWUP_REGEX = re.compile("|".join(FOLLOWUP_PATTERNS))
def is_followup_for_summary(user_text: str) -> bool:
    return bool(FOLLOWUP_REGEX.search(_normalize(user_text)))

# -------------------------
# English-only check for Voice mode transcripts
# -------------------------
def is_english_text(text: str, threshold: float = 0.9) -> bool:
    """Heuristic: reject if Romanian diacritics present; else require >=90% A–Z letters among alphabetic chars."""
    if any(ch in text for ch in "ăâîșțĂÂÎȘȚ"):
        return False
    letters = [c for c in text if c.isalpha()]
    if not letters:
        return False
    ascii_letters = [c for c in letters if ("A" <= c <= "Z") or ("a" <= c <= "z")]
    return (len(ascii_letters) / len(letters)) >= threshold

# -------------------------
# Voice transcription helper (OpenAI) — English only
# -------------------------
def transcribe_audio_bytes(audio_bytes: bytes, prefer_model: str = "gpt-4o-transcribe") -> str:
    """
    Saves the bytes to a temp WAV file and transcribes with OpenAI.
    Prefers gpt-4o-transcribe; falls back to whisper-1. Language forced to English when possible.
    """
    if not audio_bytes:
        return ""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
        tmp.write(audio_bytes)
        tmp_path = tmp.name
    try:
        with open(tmp_path, "rb") as f:
            # Try preferred model WITH language hint
            try:
                r = client.audio.transcriptions.create(model=prefer_model, file=f, language="en")
            except Exception:
                try:
                    # Retry preferred model WITHOUT language if param unsupported
                    f.seek(0)
                    r = client.audio.transcriptions.create(model=prefer_model, file=f)
                except Exception:
                    # Fall back to Whisper with language=en
                    f.seek(0)
                    try:
                        r = client.audio.transcriptions.create(model="whisper-1", file=f, language="en")
                    except Exception:
                        f.seek(0)
                        r = client.audio.transcriptions.create(model="whisper-1", file=f)
        return (getattr(r, "text", "") or "").strip()
    finally:
        try:
            os.remove(tmp_path)
        except Exception:
            pass

# -------------------------
# Capture input: Voice ONLY when voice_mode is ON; otherwise text chat
# -------------------------
transcribed_msg = None
if voice_mode:
    audio_bytes = audio_recorder()  # click to start/stop; returns WAV bytes
    if audio_bytes:
        with st.spinner("Transcribing (English only)..."):
            transcribed_msg = transcribe_audio_bytes(audio_bytes)
        if transcribed_msg:
            if not is_english_text(transcribed_msg):
                st.warning("Voice mode accepts **English speech only**. Please try again in English.")
                transcribed_msg = None
            else:
                st.info(f"🎤 You said (EN): {transcribed_msg}")

# While Voice mode is ON, disable typed input (voice only).
typed_msg = None if voice_mode else st.chat_input("What would you like to read?")
user_msg = transcribed_msg if transcribed_msg else typed_msg

if user_msg:
    # Always append the user message so it's visible in the transcript
    st.session_state.messages.append({"role": "user", "content": user_msg})

    # 1) External moderation: if blocked, DO NOT call RAG/LLM — reply politely
    moderation = check_with_openai_moderation(user_msg)
    if moderation["blocked"]:
        reasons = f" (content filter: {', '.join(moderation['reasons'])})" if moderation["reasons"] else ""
        st.session_state.messages.append({"role": "assistant", "content": BLOCK_MESSAGE + reasons})
        st.session_state["skip_infer_once"] = True
    else:
        # 2) Follow-up: if user asks for more/summary and we have a last recommendation,
        #    skip RAG/LLM and show the summary directly.
        if is_followup_for_summary(user_msg) and st.session_state.last_reco_title:
            title = st.session_state.last_reco_title
            try:
                summary = get_summary_by_title(title)
                with st.chat_message("assistant"):
                    st.markdown('<div class="block-card">', unsafe_allow_html=True)
                    st.markdown('<div class="badge">Summary</div>', unsafe_allow_html=True)
                    st.markdown(f'<div class="reco-title">{title}</div>', unsafe_allow_html=True)
                    st.write(summary)
                    st.markdown('</div>', unsafe_allow_html=True)
                st.session_state.messages.append({"role": "assistant", "content": summary})
                st.session_state["skip_infer_once"] = True
            except Exception as e:
                st.session_state.messages.append({"role": "assistant", "content": f"Sorry, couldn't fetch the summary: {e}"})
                st.session_state["skip_infer_once"] = True

# -------------------------
# Render existing history
# -------------------------
for m in st.session_state.messages:
    if m["role"] == "user":
        with st.chat_message("user"):
            st.write(m["content"])
    elif m["role"] == "assistant":
        with st.chat_message("assistant"):
            st.write(m["content"])

# -------------------------
# Core inference (RAG -> LLM choose -> Tool -> Final answer)
# -------------------------
def model_choose_and_call_tool(user_query: str) -> Dict[str, Any]:
    """RAG -> GPT with tool schema (forced call) -> execute local tool -> final text + chosen title."""
    # 1) Retrieve top candidates (semantic search)
    candidates = rag.search(user_query, k=3)
    candidates_json = json.dumps(candidates, ensure_ascii=False)

    # 2) First call: FORCE the tool call so the model doesn't “ask first”
    first_messages: List[Dict[str, str]] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_query},
        {"role": "system", "content": f"Candidates (JSON): {candidates_json}"}
    ]

    first = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=first_messages,
        tools=TOOL_SCHEMA,
        tool_choice={"type": "function", "function": {"name": "get_summary_by_title"}},  # force call
        temperature=0.2
    )

    choice = first.choices[0].message
    tool_calls = choice.tool_calls or []

    # 3) Execute tool(s) locally and capture outputs
    tool_messages: List[Dict[str, str]] = []
    chosen_title = None
    assistant_tool_calls_payload = []

    for tc in tool_calls:
        assistant_tool_calls_payload.append({
            "id": getattr(tc, "id", getattr(tc, "tool_call_id", None)),
            "type": "function",
            "function": {
                "name": getattr(tc.function, "name", None) if getattr(tc, "function", None) else None,
                "arguments": getattr(tc.function, "arguments", None) if getattr(tc, "function", None) else None,
            }
        })

        if getattr(tc, "type", "function") == "function" and getattr(tc, "function", None):
            fn_name = getattr(tc.function, "name", "")
            if fn_name == "get_summary_by_title":
                args_raw = getattr(tc.function, "arguments", "{}") or "{}"
                try:
                    args = json.loads(args_raw)
                except Exception:
                    args = {}
                title = (args.get("title") or "").strip()
                if title:
                    chosen_title = title
                else:
                    # Fallback: if the model forgot to pass a title, pick the top candidate
                    if candidates:
                        chosen_title = candidates[0]["title"]
                        args["title"] = chosen_title

                try:
                    summary = get_summary_by_title(chosen_title)
                    tool_messages.append({
                        "role": "tool",
                        "tool_call_id": assistant_tool_calls_payload[-1]["id"],
                        "content": summary
                    })
                except Exception as e:
                    tool_messages.append({
                        "role": "tool",
                        "tool_call_id": assistant_tool_calls_payload[-1]["id"],
                        "content": f"Error: {e}"
                    })

    # 4) Second call: send back tool outputs so the model can compose the final answer
    second_messages: List[Dict[str, Any]] = first_messages + [
        {
            "role": "assistant",
            "content": choice.content or "",
            "tool_calls": assistant_tool_calls_payload
        },
        *tool_messages
    ]

    second = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=second_messages,
        temperature=0.2
    )

    final_text = second.choices[0].message.content or "I couldn't generate a final answer."
    return {"final_text": final_text, "title": chosen_title}

# Run inference only if the last message is a user message and we didn't block or handle follow-up locally
if (
    st.session_state.messages
    and st.session_state.messages[-1]["role"] == "user"
    and not st.session_state.get("skip_infer_once")
):
    with st.chat_message("assistant"):
        with st.spinner("Searching the library…"):
            result = model_choose_and_call_tool(st.session_state.messages[-1]["content"])
        # Store last recommendation for follow-ups
        if result.get("title"):
            st.session_state.last_reco_title = result["title"]

        st.markdown('<div class="block-card">', unsafe_allow_html=True)
        if result.get("title"):
            st.markdown('<div class="badge">My recommendation</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="reco-title">{result.get("title") or "Answer"}</div>', unsafe_allow_html=True)
        st.write(result["final_text"])
        st.markdown('</div>', unsafe_allow_html=True)

    st.session_state.messages.append({"role": "assistant", "content": result["final_text"]})

# Reset the one-turn skip flag if it was set
if st.session_state.get("skip_infer_once"):
    del st.session_state["skip_infer_once"]
