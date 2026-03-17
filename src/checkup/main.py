"""FastAPI application entrypoint."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from checkup.api.webhooks import router as webhook_router
from checkup.config import settings

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize long-lived resources on startup."""
    from checkup.agent.graph import compile_graph

    try:
        from checkup.agent.memory import get_checkpointer
        checkpointer = await get_checkpointer()
        app.state.graph = compile_graph(checkpointer=checkpointer)
        logger.info("Graph compiled with Postgres checkpointer")
    except Exception as exc:
        logger.warning("Postgres checkpointer unavailable (%s) — using stateless graph", exc)
        app.state.graph = compile_graph()

    yield


app = FastAPI(
    title="CheckUp",
    description="WhatsApp health agent for remotely monitoring elderly parents",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(webhook_router, prefix="/api")


@app.get("/health")
async def health_check():
    """Simple health-check endpoint."""
    return {"status": "ok", "env": settings.app_env}
