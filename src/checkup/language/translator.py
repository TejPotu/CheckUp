"""Telugu ↔ English translation using Gemini's multilingual capability."""

from __future__ import annotations

import logging

from langchain_google_genai import ChatGoogleGenerativeAI

from checkup.config import settings

logger = logging.getLogger(__name__)

_TRANSLATE_TO_EN_PROMPT = """\
Translate the following text from Telugu to English.
The text may be in Telugu script (తెలుగు) or Romanized Telugu (e.g., "naaku tala noppi ga undi").
Translate it into clear, natural English. Only return the translation, nothing else.
If the text is already in English, return it as-is.

Text: {text}
"""

_TRANSLATE_TO_TE_PROMPT = """\
Translate the following English text into Telugu script (తెలుగు).
Use natural, conversational Telugu that an elderly person would easily understand.
Avoid complex or overly formal words. Keep medical terms simple.
Only return the Telugu translation, nothing else.

Text: {text}
"""


def _get_llm() -> ChatGoogleGenerativeAI:
    return ChatGoogleGenerativeAI(
        model="gemini-2.0-flash",
        google_api_key=settings.google_api_key,
        temperature=0.1,
    )


async def translate_to_english(text: str) -> str:
    """Translate Telugu (script or Romanized) text to English."""
    if not text.strip():
        return text

    llm = _get_llm()
    response = await llm.ainvoke([
        {"role": "user", "content": _TRANSLATE_TO_EN_PROMPT.format(text=text)},
    ])
    result = response.content.strip()
    logger.info("Translated to English: '%s' → '%s'", text[:60], result[:60])
    return result


async def translate_response(text: str, target_lang: str) -> str:
    """Translate an English response back to the target language.

    Args:
        text: English text to translate.
        target_lang: Target language code ("te" for Telugu).

    Returns:
        Translated text. If target_lang is "en", returns text unchanged.
    """
    if target_lang != "te" or not text.strip():
        return text

    llm = _get_llm()
    response = await llm.ainvoke([
        {"role": "user", "content": _TRANSLATE_TO_TE_PROMPT.format(text=text)},
    ])
    result = response.content.strip()
    logger.info("Translated to Telugu: '%s' → '%s'", text[:60], result[:60])
    return result
