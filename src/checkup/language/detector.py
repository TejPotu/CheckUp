"""Language detection — identifies Telugu script, Romanized Telugu, or English."""

from __future__ import annotations

import re
import logging

logger = logging.getLogger(__name__)

# Unicode range for Telugu script
_TELUGU_PATTERN = re.compile(r"[\u0C00-\u0C7F]")

# Common Romanized Telugu words / fragments that hint at Telugu in Latin script
_TELUGU_ROMAN_HINTS = {
    "naaku", "naku", "undi", "undhi", "amma", "nanna", "baaga", "baga",
    "ledu", "ledhu", "chala", "inka", "entha", "ela", "enti", "emiti",
    "valla", "manchi", "cheppu", "cheppandi", "noppi", "jaramu", "jalubu",
    "kallu", "tala", "kaalu", "kaduppu", "okasari", "tablet", "mandhu",
    "mandalu", "tinanu", "thinnanu", "nidra", "raaledu", "vacchindi",
    "ayyindi", "chesanu", "chesina", "vundi", "ayya", "rojuu", "roju",
    "evariki", "evaru", "meeru", "nenu", "maaku", "memu",
}


def detect_language(text: str) -> str:
    """Detect the language of the incoming message.

    Returns:
        "te"  — Telugu (native script or Romanized).
        "en"  — English (fallback).
    """
    if not text or not text.strip():
        return "en"

    # Check for Telugu script characters
    telugu_chars = len(_TELUGU_PATTERN.findall(text))
    if telugu_chars >= 2:
        logger.debug("Detected Telugu script (%d chars)", telugu_chars)
        return "te"

    # Check for Romanized Telugu hints
    words = set(text.lower().split())
    matches = words & _TELUGU_ROMAN_HINTS
    if len(matches) >= 1:
        logger.debug("Detected Romanized Telugu (hints: %s)", matches)
        return "te"

    return "en"
