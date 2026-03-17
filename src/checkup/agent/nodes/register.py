"""Registration node — collect and persist a new parent profile."""

from __future__ import annotations

import json
import logging
from typing import Any

from langchain_core.messages import AIMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from sqlalchemy import select

from checkup.agent.state import ConversationState
from checkup.config import settings

logger = logging.getLogger(__name__)

_EXTRACT_PROMPT = """\
The user wants to register their health profile with this WhatsApp health monitoring service.

Extract the following fields from their message (return JSON only, no extra text):
{{
  "parent_name": "<string or null>",
  "age": <integer or null>,
  "caregiver_phone": "<E.164 phone number string or null>",
  "known_conditions": ["<condition>", ...],
  "medications": [
    {{"name": "<name>", "dosage": "<dosage>", "times": ["HH:MM", ...]}}
  ]
}}

If a field is not mentioned, use null (or [] for lists).

User message: {message}
"""

_MISSING_INFO_RESPONSE = """\
Welcome to CheckUp! 🙏 I'll help set up your health profile.

Please share the following details:
• Your name
• Your age
• Your caregiver's phone number (family member who should receive alerts)
• Any health conditions (e.g., diabetes, hypertension)
• Your medications with dosage and timing (e.g., "Metformin 500mg at 8 AM and 8 PM")

You can share all this in one message!
"""

_ALREADY_REGISTERED_RESPONSE = """\
You're already registered! Here's your current profile:

👤 Name: {parent_name}
🎂 Age: {age}
📱 Caregiver: {caregiver_phone}
🏥 Conditions: {conditions}
💊 Medications: {medications}

To update your profile, please contact your caregiver or send your updated details.
"""

_SUCCESS_RESPONSE = """\
✅ Registration successful! Welcome to CheckUp, {parent_name}!

Your health profile has been saved:
👤 Name: {parent_name}
🎂 Age: {age}
📱 Caregiver alerts will go to: {caregiver_phone}
🏥 Conditions: {conditions}
💊 Medications: {medications}

I'll check in with you every morning at 9 AM. You can also ask me health questions any time! 🙏
"""


async def register(state: ConversationState) -> dict[str, Any]:
    """Handle parent registration — collect info and persist to DB."""
    from datetime import time
    from checkup.db.session import async_session
    from checkup.scheduler.models import ParentProfile

    user_phone = state.get("user_phone", "")
    english_text = state.get("english_text", "")

    # Check if already registered.
    async with async_session() as session:
        result = await session.execute(
            select(ParentProfile).where(ParentProfile.parent_phone == user_phone)
        )
        existing = result.scalar_one_or_none()

    if existing:
        conditions_str = ", ".join(existing.known_conditions or []) or "None"
        meds_str = (
            ", ".join(m["name"] for m in (existing.medications or [])) or "None"
        )
        response = _ALREADY_REGISTERED_RESPONSE.format(
            parent_name=existing.parent_name,
            age=existing.age or "—",
            caregiver_phone=existing.caregiver_phone,
            conditions=conditions_str,
            medications=meds_str,
        )
        logger.info("Registration attempted for already-registered parent %s", user_phone)
        return {
            "response_text": response,
            "parent_profile_id": existing.id,
            "messages": [AIMessage(content=response)],
        }

    # Extract fields from the user's message.
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash",
        google_api_key=settings.google_api_key,
        temperature=0,
    )

    extracted: dict[str, Any] = {}
    try:
        llm_response = await llm.ainvoke([
            {"role": "user", "content": _EXTRACT_PROMPT.format(message=english_text)},
        ])
        raw = llm_response.content.strip()
        # Strip markdown code fences if present.
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        extracted = json.loads(raw)
    except Exception as e:
        logger.warning("Failed to extract registration fields: %s", e)

    parent_name = extracted.get("parent_name")
    caregiver_phone = extracted.get("caregiver_phone")

    # If we're missing the minimum required fields, ask the user.
    if not parent_name or not caregiver_phone:
        logger.info("Registration incomplete for %s — asking for missing fields", user_phone)
        return {
            "response_text": _MISSING_INFO_RESPONSE,
            "messages": [AIMessage(content=_MISSING_INFO_RESPONSE)],
        }

    # Persist the new profile.
    age = extracted.get("age")
    known_conditions = extracted.get("known_conditions") or []
    medications = extracted.get("medications") or []

    async with async_session() as session:
        profile = ParentProfile(
            parent_phone=user_phone,
            caregiver_phone=caregiver_phone,
            parent_name=parent_name,
            age=age,
            known_conditions=known_conditions,
            medications=medications,
            preferred_language=state.get("detected_language") or "te",
            checkin_time=time(9, 0),
            is_active=True,
        )
        session.add(profile)
        await session.commit()
        await session.refresh(profile)
        profile_id = profile.id

    conditions_str = ", ".join(known_conditions) or "None"
    meds_str = ", ".join(m["name"] for m in medications) if medications else "None"
    response = _SUCCESS_RESPONSE.format(
        parent_name=parent_name,
        age=age or "—",
        caregiver_phone=caregiver_phone,
        conditions=conditions_str,
        medications=meds_str,
    )

    logger.info("Registered new parent %s (id=%d)", parent_name, profile_id)
    return {
        "response_text": response,
        "parent_profile_id": profile_id,
        "messages": [AIMessage(content=response)],
    }
