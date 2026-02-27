"""FastAPI application entrypoint."""

from __future__ import annotations

import logging

from fastapi import FastAPI

from checkup.api.webhooks import router as webhook_router
from checkup.config import settings

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="CheckUp",
    description="WhatsApp health agent for remotely monitoring elderly parents",
    version="0.1.0",
)

app.include_router(webhook_router, prefix="/api")


@app.get("/health")
async def health_check():
    """Simple health-check endpoint."""
    return {"status": "ok", "env": settings.app_env}
