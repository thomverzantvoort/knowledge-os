# Knowledge-OS

Personal YouTube/podcast triage system: ingest subscribed channels, rank weekly digests, deep-dive only on kept items with grounded chat + citations.
Read before coding:
1. `AGENTS.md` (universal rules)
2. `backend/AGENTS.md` when touching Python/FastAPI
3. `docs/north-star.md` for product intent
4. `docs/architecture.md` for system design

## Layout
- `backend/` — FastAPI service, ingest pipeline, DB models, Alembic migrations
- `docs/` — specs and design notes
- `data/` — local corpus / seed input (e.g. `data/input/subscriptions.json`)
Frontend is not built yet. Do not invent a frontend stack.
