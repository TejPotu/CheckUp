"""Escalation node — handles emergencies and caregiver alerts."""

from __future__ import annotations

import logging
from typing import Any

from langchain_core.messages import AIMessage

from checkup.agent.state import ConversationState

logger = logging.getLogger(__name__)

EMERGENCY_RESPONSE_EN = """\
🚨 I understand this sounds serious. Here's what to do right now:

1. If you feel you're in danger, please call emergency services (108) immediately.
2. I'm alerting your family member right now so they can check on you.
3. Try to stay calm and sit or lie down in a comfortable position.
4. Don't take any new medication without talking to your doctor.

Your family has been notified. Someone will reach out to you very soon. 🙏

⚠️ This is not medical advice. Please call 108 or visit the nearest hospital for emergencies.
"""


async def escalate(state: ConversationState) -> dict[str, Any]:
    """Handle an escalation — send emergency response and alert caregiver."""
    english_text = state.get("english_text", "")
    existing_alert = state.get("caregiver_alert")

    logger.warning("ESCALATION triggered for phone=%s", state.get("user_phone", "unknown"))

    # Prepare caregiver alert if not already set by check-in node
    caregiver_alert = existing_alert or (
        f"🚨 URGENT: Your parent has requested help or reported an emergency.\n\n"
        f"What they said: \"{english_text}\"\n\n"
        f"Please contact them immediately or call emergency services (108)."
    )

    return {
        "response_text": EMERGENCY_RESPONSE_EN,
        "risk_level": "high",
        "caregiver_alert": caregiver_alert,
        "messages": [AIMessage(content=EMERGENCY_RESPONSE_EN)],
    }
