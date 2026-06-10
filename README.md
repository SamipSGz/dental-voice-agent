# Dental Voice Agent

An AI-powered inbound and outbound voice agent for dental appointment management, built with [VAPI.ai](https://vapi.ai) and FastAPI.

Patients can **book**, **reschedule**, and **cancel** dental appointments through a natural phone conversation — no app, no website.

**Live demo:** Call **+1 (320) 436-9246**
> Or test via VAPI dashboard → Assistants → Dental Appointment Assistant → Talk button (no phone needed)

---

## How it works

```
Patient calls +1 (320) 436-9246
         │
         ▼
    ┌──────────┐   tool calls (HTTP POST)   ┌─────────────────────────┐
    │  VAPI.ai │ ─────────────────────────▶ │  FastAPI Backend         │
    │  Voice   │ ◀───────────────────────── │  /vapi/webhook           │
    │  Agent   │   JSON results             │                         │
    └──────────┘                            │  ┌─────────────────────┐ │
                                            │  │   SQLite / Postgres │ │
                                            │  │  patients           │ │
                                            │  │  appointments       │ │
                                            │  └─────────────────────┘ │
                                            └─────────────────────────┘
```

VAPI manages the full voice pipeline (STT → LLM → TTS). During a call, whenever the assistant needs to check availability, book, or cancel, it POSTs a tool call to our backend which performs the DB operation and returns the result. The assistant reads it back to the patient in natural speech.

---

## Features

- Inbound calls — book, reschedule, or cancel via voice
- Outbound calls — automated appointment reminders
- Patient recognition — looks up returning patients by phone number
- Real-time slot availability — no double-booking possible
- Human escalation — transfers to live agent when needed
- Structured logging (structlog), Prometheus metrics, Sentry support
- Docker + docker-compose for local and production
- GitHub Actions CI/CD — lint, type check, tests, Docker build, SSH deploy

---

## Tech stack

| Layer | Technology |
|---|---|
| Voice platform | VAPI.ai (free tier) |
| Backend | FastAPI + Python 3.12 |
| Database | SQLite (dev) / PostgreSQL (prod) |
| ORM | SQLAlchemy 2.0 |
| Containerization | Docker + docker-compose |
| CI/CD | GitHub Actions |
| Monitoring | structlog + Prometheus + Sentry |

---

## Quickstart

### Prerequisites
- Python 3.12+
- [VAPI account](https://dashboard.vapi.ai) (free)

### 1. Clone and configure

```bash
git clone https://github.com/your-username/dental-voice-agent
cd dental-voice-agent
cp .env.example .env
# Fill in your VAPI_API_KEY, VAPI_PHONE_NUMBER_ID, VAPI_ASSISTANT_ID
```

### 2. Run locally

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
uvicorn app.main:app --reload
```

API docs: `http://localhost:8000/docs`

### 3. Run with Docker + PostgreSQL

```bash
docker compose up --build
```

### 4. Run tests

```bash
cd backend
pytest tests/ -v --cov=app
```

---

## VAPI setup

1. **Create account** at [dashboard.vapi.ai](https://dashboard.vapi.ai)
2. **Buy a phone number** → copy the Phone Number ID → `VAPI_PHONE_NUMBER_ID` in `.env`
3. **Create assistant** using the VAPI API (see below) or paste `vapi_config/assistant_config.json` in the dashboard
4. Copy the **Assistant ID** → `VAPI_ASSISTANT_ID` in `.env`
5. **Expose webhook** with ngrok: `ngrok http 8000`
6. Update `serverUrl` in assistant config to your ngrok/production URL + `/vapi/webhook`

**Push assistant config via API:**
```bash
curl -X PATCH https://api.vapi.ai/assistant/<ASSISTANT_ID> \
  -H "Authorization: Bearer <PRIVATE_KEY>" \
  -H "Content-Type: application/json" \
  -d @vapi_config/assistant_config.json
```

---

## Environment variables

| Variable | Description | Required |
|---|---|---|
| `DATABASE_URL` | PostgreSQL or SQLite connection URL | Yes |
| `VAPI_API_KEY` | VAPI public key | Yes |
| `VAPI_PHONE_NUMBER_ID` | VAPI phone number ID | Yes |
| `VAPI_ASSISTANT_ID` | VAPI assistant ID | Yes |
| `VAPI_WEBHOOK_SECRET` | HMAC secret for webhook verification | Recommended |
| `CLINIC_NAME` | Clinic display name | Yes |
| `CLINIC_TIMEZONE` | Timezone (e.g. `America/New_York`) | Yes |
| `SENTRY_DSN` | Sentry DSN for error tracking | No |

See `.env.example` for all options.

---

## API reference

Full docs: [`docs/api_design.md`](docs/api_design.md)

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/vapi/webhook` | VAPI tool-call handler |
| `GET` | `/api/v1/appointments/availability` | Check slots for a date |
| `POST` | `/api/v1/appointments/` | Book appointment |
| `PATCH` | `/api/v1/appointments/{id}` | Reschedule |
| `DELETE` | `/api/v1/appointments/{id}` | Cancel |
| `GET` | `/api/v1/patients/lookup` | Find patient by phone |
| `POST` | `/api/v1/outbound/call` | Trigger outbound reminder call |
| `GET` | `/health` | Health check |

---

## Conversation flows

See [`vapi_config/conversation_flows/`](vapi_config/conversation_flows/) for detailed call scripts:
- [Scheduling](vapi_config/conversation_flows/scheduling_flow.md)
- [Rescheduling](vapi_config/conversation_flows/rescheduling_flow.md)
- [Cancellation](vapi_config/conversation_flows/cancellation_flow.md)

---

## Testing

See [`docs/testing_report.md`](docs/testing_report.md) for full test results and sample transcripts of all three use cases.

```
18 passed in 0.13s  —  87% coverage
```

---

## CI/CD

| Workflow | Trigger | Steps |
|---|---|---|
| `ci.yml` | Push / PR to `main` | Lint → Type check → Tests → Docker build |
| `deploy.yml` | Push to `main`, version tags | Build → Push Docker Hub → SSH deploy |

**Required GitHub secrets for deployment:**
`DOCKER_USERNAME`, `DOCKER_TOKEN`, `DEPLOY_HOST`, `DEPLOY_USER`, `DEPLOY_SSH_KEY`

---

## Production deployment

```bash
git clone https://github.com/your-username/dental-voice-agent /opt/dental-voice-agent
cd /opt/dental-voice-agent
cp .env.example .env.production  # fill in production values
docker compose -f docker-compose.prod.yml up -d
```
