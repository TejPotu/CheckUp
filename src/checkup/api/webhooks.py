"""Webhook endpoints for Meta WhatsApp Cloud API."""

from __future__ import annotations

import json
import logging

from fastapi import APIRouter, Request, Response, HTTPException
from langchain_core.messages import HumanMessage
from sqlalchemy import select

from checkup.config import settings
from checkup.messaging.meta_client import meta_client

logger = logging.getLogger(__name__)

router = APIRouter(tags=["webhooks"])


@router.get("/webhook")
async def verify_webhook(request: Request) -> Response:
    """Handle Meta's webhook verification challenge (GET).

    Meta sends a GET request with hub.mode, hub.verify_token, and hub.challenge.
    We must respond with the challenge value if the verify token matches.
    """
    params = request.query_params
    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")

    if mode == "subscribe" and token == settings.meta_verify_token:
        logger.info("Webhook verified successfully")
        return Response(content=challenge, media_type="text/plain")

    logger.warning("Webhook verification failed: invalid token")
    raise HTTPException(status_code=403, detail="Verification failed")


@router.post("/webhook")
async def handle_inbound(request: Request) -> dict[str, str]:
    """Handle inbound WhatsApp messages from Meta.

    Flow:
    1. Verify Meta's HMAC-SHA256 signature (if META_APP_SECRET is set).
    2. Parse the inbound message.
    3. Invoke the LangGraph agent with the message.
    4. Send the response back via WhatsApp.
    5. Persist a HealthLog if this was a check-in.
    6. If a caregiver alert is set, look up the caregiver and send it.
    """
    raw_body = await request.body()
    signature = request.headers.get("X-Hub-Signature-256", "")
    if not meta_client.verify_signature(raw_body, signature):
        raise HTTPException(status_code=403, detail="Invalid signature")

    payload = json.loads(raw_body)

    parsed = meta_client.parse_inbound(payload)
    if not parsed:
        return {"status": "ok"}

    from_number = parsed["from_number"]
    body = parsed["body"]
    logger.info("Inbound from %s: %s", from_number, body[:80])

    graph = request.app.state.graph

    initial_state = {
        "messages": [HumanMessage(content=body)],
        "user_phone": from_number,
        "original_text": body,
        "detected_language": "",
        "english_text": "",
        "intent": "",
        "parent_profile_id": None,
        "rag_context": None,
        "health_summary": None,
        "risk_level": None,
        "response_text": "",
        "caregiver_alert": None,
    }

    try:
        result = await graph.ainvoke(
            initial_state,
            config={"configurable": {"thread_id": from_number}},
        )

        response_text = result.get("response_text", "")
        if response_text:
            await meta_client.send_text(from_number, response_text)

        # Persist a HealthLog entry for check-in interactions.
        if result.get("intent") == "checkin":
            await _save_health_log(
                from_number=from_number,
                data=result.get("health_summary") or {},
                risk_level=result.get("risk_level") or "low",
            )

        # Send caregiver alert if needed.
        caregiver_alert = result.get("caregiver_alert")
        if caregiver_alert:
            await _send_caregiver_alert(from_number, caregiver_alert)

    except Exception as e:
        logger.error("Error processing message from %s: %s", from_number, e, exc_info=True)
        await meta_client.send_text(
            from_number,
            "🙏 Sorry, I encountered an issue. Please try again or contact your family member.",
        )

    return {"status": "ok"}


async def _save_health_log(from_number: str, data: dict, risk_level: str) -> None:
    """Persist a HealthLog row for the parent identified by phone number."""
    from datetime import datetime
    from checkup.db.session import async_session
    from checkup.scheduler.models import ParentProfile, HealthLog

    try:
        async with async_session() as session:
            profile_result = await session.execute(
                select(ParentProfile).where(ParentProfile.parent_phone == from_number)
            )
            profile = profile_result.scalar_one_or_none()
            if not profile:
                return

            log = HealthLog(
                parent_id=profile.id,
                timestamp=datetime.utcnow(),
                log_type="checkin",
                data=data,
                risk_level=risk_level,
            )
            session.add(log)
            await session.commit()
            logger.debug("Saved HealthLog for parent %d (risk=%s)", profile.id, risk_level)
    except Exception as e:
        logger.error("Failed to save health log for %s: %s", from_number, e)


async def _send_caregiver_alert(from_number: str, alert_message: str) -> None:
    """Look up the caregiver phone for the given parent and send the alert."""
    from checkup.db.session import async_session
    from checkup.scheduler.models import ParentProfile

    try:
        async with async_session() as session:
            result = await session.execute(
                select(ParentProfile).where(ParentProfile.parent_phone == from_number)
            )
            profile = result.scalar_one_or_none()

        if profile and profile.caregiver_phone:
            await meta_client.send_text(profile.caregiver_phone, alert_message)
            logger.info("Caregiver alert sent to %s for parent %s", profile.caregiver_phone, from_number)
        else:
            logger.warning("No caregiver phone found for parent %s — alert not sent", from_number)
    except Exception as e:
        logger.error("Failed to send caregiver alert for %s: %s", from_number, e)


@router.post("/status")
async def handle_status(request: Request) -> dict[str, str]:
    """Handle delivery status callbacks from Meta."""
    payload = await request.json()
    logger.debug("Status callback: %s", payload)
    return {"status": "ok"}
