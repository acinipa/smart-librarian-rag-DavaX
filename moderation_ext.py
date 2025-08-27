# moderation_ext.py
from typing import List, Tuple, Dict, Any
from openai import OpenAI

# Mesaj politicos reutilizabil
BLOCK_MESSAGE_EXT = (
    "Te rog să păstrăm conversația respectuoasă. Sunt un chatbot AI care **recomandă cărți** "
    "în funcție de interesele tale (ex.: *prietenie*, *magie*, *război*, *distopie*). "
    "Spune-mi te rog ce fel de carte cauți."
)

_client = OpenAI()

def check_with_openai_moderation(text: str) -> Tuple[bool, List[str], Dict[str, Any]]:
    """
    Returnează: (blocked, reasons, raw)
      - blocked: True dacă OpenAI Moderation marchează conținutul ca problematic
      - reasons: lista categoriilor declanșate
      - raw: răspunsul complet pt. debugging/logging
    """
    resp = _client.moderations.create(
        model="omni-moderation-latest",  # modelul recomandat în docs
        input=text
    )
    # SDK-ul întoarce .results[0] cu campurile: flagged, categories{...}
    result = resp.results[0]
    flagged = bool(result.flagged)
    reasons = [cat for cat, v in result.categories.items() if v]
    return flagged, reasons, resp.model_dump()
