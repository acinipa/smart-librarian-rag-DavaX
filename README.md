# Smart Librarian (RAG + Tool Calling + Moderation + EN Voice)
A minimal, production-minded Streamlit app that recommends books using:
- **RAG** over a local **ChromaDB** vector store
- **OpenAI embeddings** + **Chat Completions** (tool calling)
- A local **tool** that returns full summaries by exact title
- **External moderation** (OpenAI Moderation API)
- Optional **Voice mode (English only)** via your browser mic

## Requirements
- **Python 3.10+** (3.11 recommended)
- An **OpenAI API key** with access to:
  - `text-embedding-3-small` (or similar) for embeddings
  - `gpt-4o-mini` (chat)
  - `gpt-4o-transcribe` *or* `whisper-1` (speech-to-text)
  - `omni-moderation-latest` (moderation)
- OS: Windows / macOS / Linux
- Browser with microphone permission (for Voice mode)

## Quickstart (Local)
### 1) Clone & enter the project
  git clone https://github.com/acinipa/smart-librarian-rag-DavaX.git

### 2) Create a virtual environment
  python -m venv .venv
  . .\.venv\Scripts\Activate.ps1

### 3) Install dependencies
  pip install -r requirements.txt
  
### 4) Configure environment
  set your API key

### 5) Configure environment
  streamlit run app.py

## Usage
  1. Type a request (e.g., “I want a book about friendship and magic”).
  2. The app:
     - Moderates your input,
     - Runs RAG (semantic search over 20 books),
     - The model chooses exactly one candidate,
     - Calls the tool get_summary_by_title to fetch the full summary,
     - Replies with a recommendation + summary.
       
  3. Voice Mode (English only)
     - Toggle “🎙️ Voice mode (English voice only)” in the sidebar.
     - While ON: typed input is disabled. Click the mic widget, speak English, click again to stop.
     - Non-English transcripts are rejected with a prompt to retry in English.
       
       
