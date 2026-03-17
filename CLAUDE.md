# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Summary

CheckUp is a WhatsApp AI health agent for remotely monitoring elderly parents. It sends daily check-ins, answers health questions in Telugu (native script and Romanized), sends medication reminders, and alerts caregivers when risk is detected. Built with FastAPI + LangGraph + Gemini + Qdrant + Celery.

## Commands

```bash
# Install (dev)
pip install -e ".[dev]"

# Run server
uvicorn checkup.main:app --host 0.0.0.0 --port 8000

# Run all tests
pytest tests/ -v

# Run a single test file
pytest tests/test_language.py -v

# Lint
ruff check src/

# Celery worker
celery -A checkup.scheduler.tasks worker --loglevel=info

# Celery beat (cron scheduler)
celery -A checkup.scheduler.tasks beat --loglevel=info

# Ingest RAG documents into Qdrant
python -c "import asyncio; from checkup.rag.ingest import ingest_documents; asyncio.run(ingest_documents())"
```

## Architecture

**Request flow:**
1. Meta WhatsApp Cloud API sends a POST to `GET/POST /api/webhook` (`src/checkup/api/webhooks.py`)
2. FastAPI routes to the LangGraph `StateGraph` (`src/checkup/agent/graph.py`)
3. Graph nodes run in order: `detect_language` → `route` → (intent-specific node) → `respond`
4. Response is sent back via `messaging/meta_client.py` using the Meta Cloud API

**LangGraph nodes** (`src/checkup/agent/nodes/`):
- `router.py` — LLM classifies intent: `health_qa`, `checkin`, `medication`, `register`, `escalate`
- `health_qa.py` — retrieves RAG context from Qdrant, answers with Gemini
- `checkin.py` — processes daily check-in, runs two Gemini calls to assess risk (low/medium/high)
- `escalation.py` — sends emergency template, marks `risk_level = "high"`, triggers caregiver alert

Conditional edge after `checkin`: routes to `escalate` if `risk_level == "high"`, otherwise to `respond`.

**Key supporting modules:**
- `language/` — Telugu detection (Unicode range + Romanized keyword set) and Gemini-powered translation
- `rag/` — Gemini embeddings (`models/gemini-embedding-001`, 3072-dim) + Qdrant vector store, top-5 retrieval
- `scheduler/` — Celery tasks for daily check-ins (9 AM IST), medication reminders (every 30 min), missed check-in alerts (11 AM IST), weekly summaries (Sunday 8 PM IST)
- `db/` — async SQLAlchemy session; `scheduler/models.py` defines `ParentProfile`, `HealthLog`, `ScheduledReminder`
- `agent/memory.py` — `AsyncPostgresSaver` checkpointer keyed by `thread_id = user_phone` for multi-turn memory

**State:** `ConversationState` TypedDict in `agent/state.py` (12 fields) flows through every node. `messages` uses LangGraph's `add_messages` reducer.

**Config:** All settings loaded from `.env` via `pydantic-settings` in `config.py`. See `.env.example` for required variables (`GOOGLE_API_KEY`, `META_WHATSAPP_TOKEN`, `META_PHONE_NUMBER_ID`) and optional ones.

## Known Incomplete Areas (see TODO.md)

- **Celery tasks** — all 4 tasks in `scheduler/tasks.py` have `TODO` stubs and don't yet query DB or send messages
- **Multi-turn memory** — `AsyncPostgresSaver` in `agent/memory.py` exists but is not wired into the graph compilation in `webhooks.py`
- **Parent registration** — `register` intent falls through to `health_qa`; actual registration flow not implemented
- **Caregiver alert routing** — webhook handler logs the alert but doesn't look up caregiver phone from DB
- **Qdrant path** — `qdrant_path = "./qdrant_data"` is relative; when running from `notebooks/`, the collection is not found (data lives at project root)
