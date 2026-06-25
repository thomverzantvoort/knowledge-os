# Knowledge OS

A personal YouTube triage and deep-dive system. Subscribe to channels, sync videos on a schedule, get a cheap AI digest blurb and relevance score for each one, then deep-dive only on the content you actually want to keep.

> Ingest wide. Process deep only for what you keep.

---

## What it does

| Stage | What happens |
| ----- | ------------ |
| **Ingest** | Syncs subscribed YouTube channels via RSS, fetches transcripts, stores metadata in Postgres |
| **Enrich** | Runs a cheap LLM pass per video: blurb, tags, relevance score against your interest profile |
| **Library UI** | Login-protected React app showing all ingested content as a card grid, filterable by time window |
| **Deep processing** | Not built yet: timestamped outline + transcript chunks + embeddings for kept videos |
| **Chat** | Not built yet: Q&A with timestamp citations against kept video chunks |

---

## Stack

| Layer | Tech |
| ----- | ---- |
| Backend | Python 3.12 + FastAPI + uvicorn |
| Frontend | React 19 + Vite + TypeScript + Tailwind CSS + shadcn |
| Database | Postgres 17 |
| Migrations | SQLAlchemy + Alembic |
| LLM | OpenAI (configurable model) |
| Auth | Single-user JWT (bcrypt hash in env) |
| Package management | `uv` (backend), `pnpm` (frontend) |

---

## Repo layout

```text
knowledge-os/
├── backend/          # FastAPI service, ingest pipeline, processing, API
├── frontend/         # React SPA
├── data/             # Local seed input (subscriptions.json, etc.)
├── docs/             # Architecture, north-star, stage specs
├── docker/           # Docker Compose for local Postgres
├── AGENTS.md         # Rules for coding agents
└── README.md         # This file
```

---

## Local setup

### Prerequisites

- Docker (for Postgres)
- Python 3.12+ with [`uv`](https://docs.astral.sh/uv/)
- Node.js with [`pnpm`](https://pnpm.io/)

### 1. Start Postgres

```bash
docker compose -f docker/compose.dev.yml up -d
```

### 2. Configure the backend

```bash
cp backend/.env.example backend/.env
```

Fill in `backend/.env`:

```env
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=knowledge_os

OPENAI_API_KEY=sk-...

AUTH_USERNAME=you@example.com
# Generate with: cd backend && uv run python scripts/hash_password.py yourpassword
AUTH_PASSWORD_HASH=$2b$12$...
JWT_SECRET=a-long-random-string-at-least-32-chars
```

### 3. Run migrations and seed data

```bash
cd backend
uv sync
uv run alembic upgrade head
uv run python scripts/seed_interest_profile.py
uv run python scripts/seed_subscriptions.py   # needs data/input/subscriptions.json
```

### 4. Ingest and enrich content

```bash
uv run python scripts/ingest_initial_youtube.py
uv run python scripts/sync_youtube.py
```

### 5. Start the API

```bash
uv run uvicorn app.main:app --reload --port 8000
```

### 6. Start the frontend

```bash
cd frontend
pnpm install
pnpm dev
```

Open [http://localhost:5173](http://localhost:5173), sign in, and browse your library.

---

## Docs

- [`docs/north-star.md`](docs/north-star.md) — product vision and build order
- [`docs/architecture.md`](docs/architecture.md) — system design, DB schema, API reference
- [`AGENTS.md`](AGENTS.md) — coding conventions for agents and humans
- [`backend/AGENTS.md`](backend/AGENTS.md) — backend-specific conventions
