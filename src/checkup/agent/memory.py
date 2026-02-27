"""Postgres-backed checkpointer for LangGraph conversation persistence."""

from __future__ import annotations

import logging

from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from checkup.config import settings

logger = logging.getLogger(__name__)


async def get_checkpointer() -> AsyncPostgresSaver:
    """Create and set up the Postgres checkpointer.

    Uses the DATABASE_URL from settings. The checkpointer stores
    conversation state keyed by thread_id (= parent's phone number).
    """
    # Convert async URL to sync format for psycopg (langgraph uses psycopg, not asyncpg)
    db_url = settings.database_url.replace("postgresql+asyncpg://", "postgresql://")

    checkpointer = AsyncPostgresSaver.from_conn_string(db_url)
    await checkpointer.setup()
    logger.info("Postgres checkpointer initialized")
    return checkpointer
