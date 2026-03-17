# CheckUp — Project Progress Tracker

## ✅ Completed

### Core Architecture
- [x] Project scaffolding (`pyproject.toml`, `Dockerfile`, `docker-compose.yml`, `.env.example`)
- [x] FastAPI entrypoint (`main.py`, `config.py`)
- [x] Package structure (8 sub-packages)

### LangGraph Agent
- [x] `ConversationState` TypedDict (12 fields)
- [x] StateGraph with 6 nodes: `detect_language → route → (health_qa | checkin | escalate) → respond`
- [x] Conditional routing by intent (5 categories: `health_qa`, `checkin`, `medication`, `escalate`, `register`)
- [x] Post-checkin escalation for high-risk responses
- [x] Verified end-to-end in notebook ✅

### Telugu Language Layer
- [x] Language detector (Telugu script via Unicode + Romanized Telugu via keyword hints)
- [x] Telugu ↔ English translator via Gemini
- [x] Bilingual prompt templates (check-ins, medication reminders, disclaimers)
- [x] Verified: all 10 detection test cases pass ✅

### RAG Pipeline
- [x] Ingestion pipeline: load → chunk → embed → store in Qdrant
- [x] 4 seed health documents (geriatric health, medications, chronic conditions, emergencies)
- [x] 21 chunks ingested into local file-based Qdrant
- [x] Embedding model updated to `gemini-embedding-001`
- [x] Local Qdrant mode (no Docker needed)
- [x] **BUG:** RAG retrieval fails in notebook ("Collection not found") — likely a CWD/path issue since notebook runs from `notebooks/` but `qdrant_data/` is at project root

### Meta WhatsApp Integration
- [x] Meta Cloud API client (`meta_client.py`) — send text, send template
- [x] Webhook endpoints (`/api/webhook`) — verification + inbound message handling
- [x] Webhook signature validation stub

### Scheduler
- [x] SQLAlchemy models: `ParentProfile`, `HealthLog`, `ScheduledReminder`
- [x] Scheduling engine: medication reminders, weekly trends, missed check-in detection
- [x] Celery Beat tasks: daily check-in (9 AM), med reminders (30 min), missed alert (11 AM), weekly summary (Sunday)
- [x] Verified: all 18 unit tests pass ✅

### Documentation & DevOps
- [x] README with architecture, quick start, project structure
- [x] Verification notebook (`notebooks/verify_agent.ipynb`)
- [x] `.gitignore`, pushed to GitHub

---

## 🔧 In Progress

### RAG in Full Agent Flow
- [ ] Fix notebook RAG path issue (collection not found when running from `notebooks/`)
- [ ] Re-test full agent flow with RAG context grounding

---

## 🧪 Manual Verification Checklist

### 1. RAG Pipeline — Answer Quality (Highest Impact)
- [ ] Fix the notebook CWD/path issue so Qdrant collection is found
- [ ] Re-run notebook **Test 1** (Telugu health question about diabetes)
  - **Expected:** Response should reference specific foods from `chronic_conditions.md` (e.g., "limit rice", "include fiber-rich foods", "walk after meals")
  - **Actual:** _____________
- [ ] Re-run notebook **Test 2** (English BP question)
  - **Expected:** Response should mention salt limits, avoiding pickles/papads from the seed docs
  - **Actual:** _____________
- [ ] Try a medication question: _"What are the side effects of Metformin?"_
  - **Expected:** Should pull from `medication_safety.md` ("take with meals to reduce stomach upset")

### 2. Database Layer — CRUD Operations
- [x] Set up local DB (SQLite or Postgres)
- [x] Run `alembic` migrations or `Base.metadata.create_all()` to create tables
- [x] Insert a test `ParentProfile`:
  ```python
  # name="Amma", age=68, conditions=["diabetes","hypertension"], 
  # medications=[{"name":"Metformin","dosage":"500mg","times":["08:00","20:00"]}]
  ```
- [x] Query the profile back and verify all fields
- [x] Insert a `HealthLog` entry and verify it links to the parent
- [x] Insert a `ScheduledReminder` and verify sent/acknowledged flags

### 3. Webhook — Full Pipeline with Mock Payloads
- [ ] Test webhook verification handshake:
  ```bash
  curl "http://localhost:8000/api/webhook?hub.mode=subscribe&hub.verify_token=checkup-verify&hub.challenge=test123"
  # Expected: "test123"
  ```
- [ ] Test inbound Telugu message (mock Meta payload):
  ```bash
  curl -X POST http://localhost:8000/api/webhook \
    -H "Content-Type: application/json" \
    -d '{"object":"whatsapp_business_account","entry":[{"changes":[{"value":{"messages":[{"from":"919876543210","type":"text","text":{"body":"నాకు తలనొప్పి గా ఉంది"}}]}}]}]}'
  ```
  - **Expected:** 200 OK, agent processes Telugu input and generates response
- [ ] Verify the response would be sent back via Meta API (check logs)

### 4. Celery Tasks — Scheduled Jobs
- [ ] Start Redis locally (or mock it)
- [ ] Register a test parent in the DB
- [ ] Trigger `daily_checkin_scan` manually and verify a check-in message is generated
- [ ] Trigger `medication_reminder_scan` and verify reminders fire for due medications
- [ ] Trigger `missed_checkin_alert_scan` and verify caregiver gets alerted
- [ ] Trigger `weekly_summary` and verify trend report is generated

### 5. Multi-Turn Conversation Memory
- [ ] Send 2-3 messages as the same phone number
- [ ] Verify the agent remembers context from previous messages
- [ ] Check that `thread_id` (keyed by phone) persists state across turns

### 6. Edge Cases
- [ ] Send an empty message → should handle gracefully
- [ ] Send a very long message (1000+ chars) → should not crash
- [ ] Send mixed Telugu + English in one message → should detect correctly
- [ ] Simulate high-risk check-in → verify caregiver alert is generated
- [ ] Simulate missed check-in (no response after 2h) → verify alert fires

---

## 📋 Next Steps (Priority Order)

### 1. Fix RAG in Notebook
- The `qdrant_path` defaults to `./qdrant_data` (relative), but the notebook CWD is `notebooks/`
- Fix: use absolute path or adjust CWD in notebook setup cell

### 2. Wire Up Celery Tasks with DB
- The 4 Celery tasks (`daily_checkin_scan`, `missed_checkin_alert_scan`, `medication_reminder_scan`, `weekly_summary`) have `TODO` placeholders
- Need: actual DB queries to fetch active parents, their medications, and health logs
- Depends on: Postgres running (or SQLite for local testing)

### 3. Database Setup (Local)
- Create Alembic migration from SQLAlchemy models
- Option A: Use SQLite for local testing (no Docker)
- Option B: Use Docker Postgres
- Register a test parent profile and verify CRUD

### 4. Webhook End-to-End Test
- Use `curl` or FastAPI `TestClient` with realistic Meta Cloud API payloads
- Test: inbound Telugu message → agent response → outbound message format
- Add proper Meta signature validation

### 5. Conversation Memory
- Wire up `memory.py` (Postgres checkpointer) or use SQLite checkpoint for local testing
- Test: multi-turn conversation context is preserved between messages

### 6. Parent Registration Flow
- Implement the `register` intent handler
- Collect: parent name, age, conditions, medications, caregiver phone
- Store in `ParentProfile` table

### 7. Deployment
- Set up Meta Business Manager + WhatsApp Business Account
- Configure webhook URL (ngrok for dev, cloud for prod)
- Deploy to cloud (Railway, Render, or GCP Cloud Run)

---

## 🚀 Future Features

### Past Medical Records & Tests
- [ ] **Database Models:** Add `MedicalRecord` and `VitalsReading` (e.g., HbA1c, fasting sugar, blood pressure).
- [ ] **Data Ingestion:** Allow users/caregivers to upload PDF reports or images (via WhatsApp) to parse and store test results.
- [ ] **Personalized RAG:** Connect past medical records and test results into the agent's context.
  - _Example:_ Agent can reference historical data: "Your blood pressure was high last week, so please maintain your salt limits today."
- [ ] **Caregiver Summaries:** Generate weekly "Doctor Visit Ready" summaries combining health check logs and recent vitals/lab tests.
