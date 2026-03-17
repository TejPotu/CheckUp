"""Meta WhatsApp Cloud API client."""

from __future__ import annotations

import hashlib
import hmac
import logging
from typing import Any, Optional

import httpx

from checkup.config import settings

logger = logging.getLogger(__name__)

META_API_BASE = "https://graph.facebook.com/v21.0"


class MetaWhatsAppClient:
    """Client for sending messages via Meta's WhatsApp Cloud API."""

    def __init__(self) -> None:
        self.token = settings.meta_whatsapp_token
        self.phone_number_id = settings.meta_phone_number_id
        self.api_url = f"{META_API_BASE}/{self.phone_number_id}/messages"
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }

    async def send_text(self, to: str, body: str) -> dict[str, Any]:
        """Send a free-form text message.

        Args:
            to: Recipient phone number in E.164 format.
            body: Message text.

        Returns:
            API response dict.
        """
        if not self.token:
            logger.info("[DEV] Would send to %s: %s", to, body[:120])
            return {}

        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "text",
            "text": {"body": body},
        }
        async with httpx.AsyncClient() as client:
            resp = await client.post(self.api_url, json=payload, headers=self.headers)
            resp.raise_for_status()
            result = resp.json()
            logger.info("Sent text to %s — message_id=%s", to, result.get("messages", [{}])[0].get("id"))
            return result

    async def send_template(
        self,
        to: str,
        template_name: str,
        language_code: str = "te",
        components: Optional[list[dict]] = None,
    ) -> dict[str, Any]:
        """Send an approved template message (for proactive messages outside 24h window).

        Args:
            to: Recipient phone number.
            template_name: Name of the approved template.
            language_code: Language code for the template.
            components: Optional template components with variables.

        Returns:
            API response dict.
        """
        if not self.token:
            logger.info("[DEV] Would send template '%s' to %s", template_name, to)
            return {}

        payload: dict[str, Any] = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {"code": language_code},
            },
        }
        if components:
            payload["template"]["components"] = components

        async with httpx.AsyncClient() as client:
            resp = await client.post(self.api_url, json=payload, headers=self.headers)
            resp.raise_for_status()
            return resp.json()

    @staticmethod
    def parse_inbound(payload: dict) -> Optional[dict[str, str]]:
        """Parse an inbound webhook payload from Meta.

        Returns:
            Dict with 'from_number' and 'body', or None if not a text message.
        """
        try:
            entry = payload["entry"][0]
            changes = entry["changes"][0]
            value = changes["value"]
            message = value["messages"][0]

            return {
                "from_number": message["from"],
                "body": message.get("text", {}).get("body", ""),
                "message_id": message["id"],
                "timestamp": message["timestamp"],
            }
        except (KeyError, IndexError):
            logger.debug("Payload is not a standard text message")
            return None

    @staticmethod
    def verify_signature(payload_body: bytes, signature: str) -> bool:
        """Verify the webhook signature from Meta.

        Args:
            payload_body: Raw request body bytes.
            signature: The X-Hub-Signature-256 header value.

        Returns:
            True if signature is valid.
        """
        if not settings.meta_app_secret:
            logger.warning("META_APP_SECRET not set, skipping signature verification")
            return True

        expected = hmac.new(
            settings.meta_app_secret.encode(),
            payload_body,
            hashlib.sha256,
        ).hexdigest()

        sig_hash = signature.replace("sha256=", "")
        return hmac.compare_digest(expected, sig_hash)


# Module-level singleton
meta_client = MetaWhatsAppClient()
