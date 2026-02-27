"""Check-in node — handles daily health check-in conversations."""

from __future__ import annotations

import logging
from typing import Any

from langchain_core.messages import AIMessage
from langchain_google_genai import ChatGoogleGenerativeAI

from checkup.agent.state import ConversationState
from checkup.config import settings

logger = logging.getLogger(__name__)

CHECKIN_SYSTEM_PROMPT = """\
You are a caring health check-in assistant for an elderly parent.
The parent is responding to a daily check-in about how they're feeling.

Your job:
1. Acknowledge their response warmly.
2. Ask a brief follow-up if their response is vague (e.g., "okay" → "Any pain or discomfort today?").
3. Extract key health indicators from their message and return them as a structured assessment.
4. If they mention concerning symptoms, note those clearly.

Respond conversationally in 2-3 sentences. Be kind and patient — you're talking to someone's parent.
End with an encouraging note.
"""

RISK_ASSESSMENT_PROMPT = """\
Based on the following health check-in response from an elderly person, assess the risk level.

Response: {response}

Classify as:
- "low" — Normal day, no concerning symptoms (e.g., "I'm fine", "Had a good day", mild everyday aches)
- "medium" — Minor but notable symptoms that should be tracked (e.g., "didn't sleep well", "lost appetite", "mild dizziness")
- "high" — Potentially serious symptoms requiring caregiver attention (e.g., "chest pain", "fell down", "can't breathe", "very confused", "severe pain")

Reply with ONLY the risk level label: low, medium, or high.
"""


async def checkin(state: ConversationState) -> dict[str, Any]:
    """Process a daily check-in response from the elderly parent."""
    english_text = state.get("english_text", "")

    llm = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash",
        google_api_key=settings.google_api_key,
        temperature=0.4,
    )

    # Generate conversational check-in response
    checkin_response = await llm.ainvoke([
        {"role": "system", "content": CHECKIN_SYSTEM_PROMPT},
        {"role": "user", "content": english_text},
    ])

    # Assess risk level
    risk_response = await llm.ainvoke([
        {"role": "system", "content": RISK_ASSESSMENT_PROMPT.format(response=english_text)},
        {"role": "user", "content": english_text},
    ])

    risk_level = risk_response.content.strip().lower()
    if risk_level not in {"low", "medium", "high"}:
        risk_level = "low"

    answer = checkin_response.content.strip()
    logger.info("Check-in processed — risk_level=%s", risk_level)

    # Build health summary for logging
    health_summary = {
        "raw_response": english_text,
        "risk_level": risk_level,
    }

    result: dict[str, Any] = {
        "response_text": answer,
        "risk_level": risk_level,
        "health_summary": health_summary,
        "messages": [AIMessage(content=answer)],
    }

    # If high risk, prepare caregiver alert
    if risk_level == "high":
        result["caregiver_alert"] = (
            f"🚨 ALERT: Your parent reported concerning symptoms during today's check-in.\n\n"
            f"What they said: \"{english_text}\"\n\n"
            f"Please check on them as soon as possible."
        )

    return result
