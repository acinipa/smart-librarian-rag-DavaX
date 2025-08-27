# moderation_ext.py
from typing import List, Tuple, Dict, Any
from openai import OpenAI

# Reusable polite message
BLOCK_MESSAGE_EXT = (
    "Please let’s keep the conversation respectful. I am an AI chatbot that **recommends books** "
    "based on your interests (e.g., *friendship*, *magic*, *war*, *dystopia*). "
    "Please tell me what kind of book you are looking for."
)

_client = OpenAI()

def check_with_openai_moderation(text: str) -> Tuple[bool, List[str], Dict[str, Any]]:
    """
    Returns: (blocked, reasons, raw)
      - blocked: True if OpenAI Moderation marks the content as problematic
      - reasons: list of triggered categories
      - raw: the full response for debugging/logging
    """
    resp = _client.moderations.create(
        model="omni-moderation-latest",  # recommended model in the docs
        input=text
    )
    # The SDK returns .results[0] with fields: flagged, categories{...}
    result = resp.results[0]
    flagged = bool(result.flagged)
    reasons = [cat for cat, v in result.categories.items() if v]
    return flagged, reasons, resp.model_dump()
