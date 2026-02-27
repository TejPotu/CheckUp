"""Router node — classifies user intent to direct the graph flow."""

from __future__ import annotations

import logging
from typing import Any

from langchain_core.messages import HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI

from checkup.agent.state import ConversationState
from checkup.config import settings

logger = logging.getLogger(__name__)

ROUTER_SYSTEM_PROMPT = """\
You are an intent classifier for a WhatsApp health-check agent that monitors elderly parents.

Given the user message (already translated to English), classify the intent into EXACTLY one of:
- "health_qa"   — The user is asking a health-related question (symptoms, medications, conditions, diet, exercise).
- "checkin"     — The user is responding to a daily health check-in (reporting how they feel, vitals, mood).
- "medication"  — The user is asking about or confirming medication intake.
- "register"    — The user wants to register / update their health profile.
- "escalate"    — The user is reporting an emergency or asking to talk to a doctor / caregiver.

Reply with ONLY the intent label, nothing else.
"""


async def route(state: ConversationState) -> dict[str, Any]:
    """Classify user intent from the English-translated message."""
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash",
        google_api_key=settings.google_api_key,
        temperature=0,
    )
    english_text = state.get("english_text", state.get("original_text", ""))

    response = await llm.ainvoke([
        {"role": "system", "content": ROUTER_SYSTEM_PROMPT},
        {"role": "user", "content": english_text},
    ])

    intent = response.content.strip().lower().strip('"\'')

    valid_intents = {"health_qa", "checkin", "medication", "register", "escalate"}
    if intent not in valid_intents:
        logger.warning("Router returned unknown intent '%s', defaulting to health_qa", intent)
        intent = "health_qa"

    logger.info("Classified intent: %s", intent)
    return {"intent": intent}
