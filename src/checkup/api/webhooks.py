"""Webhook endpoints for Meta WhatsApp Cloud API."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Request, Response, HTTPException
from langchain_core.messages import HumanMessage

from checkup.agent.graph import compile_graph
from checkup.config import settings
from checkup.messaging.meta_client import meta_client

logger = logging.getLogger(__name__)

router = APIRouter(tags=["webhooks"])

# Compile graph once (without checkpointer for now; add in production)
_graph = compile_graph()


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
    1. Parse the inbound message.
    2. Invoke the LangGraph agent with the message.
    3. Send the response back via WhatsApp.
    4. If a caregiver alert is set, send it to the caregiver.
    """
    payload = await request.json()

    # Parse the inbound message
    parsed = meta_client.parse_inbound(payload)
    if not parsed:
        # Not a text message (could be a status update) — acknowledge silently
        return {"status": "ok"}

    from_number = parsed["from_number"]
    body = parsed["body"]
    logger.info("Inbound from %s: %s", from_number, body[:80])

    # Invoke the LangGraph agent
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
        result = await _graph.ainvoke(
            initial_state,
            config={"configurable": {"thread_id": from_number}},
        )

        # Send the response back to the parent
        response_text = result.get("response_text", "")
        if response_text:
            await meta_client.send_text(from_number, response_text)

        # Send caregiver alert if needed
        caregiver_alert = result.get("caregiver_alert")
        if caregiver_alert:
            # TODO: Look up caregiver phone from parent profile
            # For now, log the alert
            logger.warning("CAREGIVER ALERT for %s: %s", from_number, caregiver_alert)

    except Exception as e:
        logger.error("Error processing message from %s: %s", from_number, e, exc_info=True)
        # Send a generic error response
        await meta_client.send_text(
            from_number,
            "🙏 Sorry, I encountered an issue. Please try again or contact your family member."
        )

    return {"status": "ok"}


@router.post("/status")
async def handle_status(request: Request) -> dict[str, str]:
    """Handle delivery status callbacks from Meta."""
    payload = await request.json()
    logger.debug("Status callback: %s", payload)
    return {"status": "ok"}
