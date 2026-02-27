# CheckUp 🩺

**WhatsApp health agent for remotely monitoring elderly parents' health.**

A caring AI assistant that checks in on your elderly parents daily via WhatsApp, answers their health questions in Telugu (తెలుగు), reminds them about medications, and alerts you when something seems concerning.

---

## Features

- **🗣️ Telugu Support** — Parents can message in Telugu script or Romanized Telugu. Responses come back in their preferred language.
- **🤖 AI-Powered Health Q&A** — Answers health questions using RAG with curated geriatric health knowledge.
- **📋 Daily Check-Ins** — Proactive daily health check-ins at a configured time (default 9 AM IST).
- **💊 Medication Reminders** — Sends reminders based on each parent's medication schedule.
- **🚨 Caregiver Alerts** — Immediately notifies you if your parent reports concerning symptoms or misses a check-in.
- **📊 Weekly Summaries** — Sends you a weekly health trend report every Sunday.
- **🧠 LangGraph Agent** — Agentic state management with persistent conversation memory.

---

## Architecture

```
WhatsApp (Parent) ←→ Meta Cloud API ←→ FastAPI ←→ LangGraph Agent
                                                    ├── Telugu Translator (Gemini)
                                                    ├── RAG Health Q&A (Qdrant)
                                                    ├── Check-In + Risk Assessment
                                                    └── Escalation → Caregiver Alert
```

---

## Quick Start

### Prerequisites
- Python 3.11+
- Docker & Docker Compose
- Google Cloud API key (for Gemini)
- Meta Business Account (for WhatsApp Cloud API)

### 1. Clone & Configure

```bash
git clone <repo-url> checkUp && cd checkUp
cp .env.example .env
# Edit .env with your API keys
```

### 2. Start Services

```bash
docker compose up -d
```

This starts PostgreSQL, Redis, Qdrant, the FastAPI app, and Celery workers.

### 3. Ingest Health Knowledge

```bash
python -c "import asyncio; from checkup.rag.ingest import ingest_documents; asyncio.run(ingest_documents())"
```

### 4. Expose Webhook (Development)

```bash
ngrok http 8000
```

Configure the ngrok URL as your webhook in the Meta Developer Console:
- Webhook URL: `https://your-ngrok-url/api/webhook`
- Verify Token: value of `META_VERIFY_TOKEN` in your `.env`

### 5. Test It

Send a WhatsApp message to your configured number. Try:
- `నాకు తలనొప్పి గా ఉంది` (I have a headache)
- `What should I eat for diabetes?`
- `naaku BP ekkuva ga undi` (My BP is high)

---

## Project Structure

```
src/checkup/
├── agent/          # LangGraph agent: state, graph, nodes
├── api/            # FastAPI webhook endpoints
├── language/       # Telugu ↔ English detection & translation
├── rag/            # RAG pipeline: ingest, retrieve, chain
├── scheduler/      # Celery tasks: check-ins, reminders, alerts
├── messaging/      # Meta WhatsApp Cloud API client
└── db/             # SQLAlchemy models & session
```

---

## Testing

```bash
pip install -e ".[dev]"
pytest tests/ -v
```

---

## License

MIT
