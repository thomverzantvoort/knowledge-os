# Stage 2: Digest System — Backend Plan

## Context

Stage 1 (ingest pipeline) is complete: YouTube channels sync → videos + transcripts stored in DB. This plan implements Stage 2: enrichment of every item with a cheap AI blurb + tags + relevance score, plus a FastAPI layer to serve that data for a digest/library UI.

North-star step sequence being implemented: **2 (digest job) → partial 3 (API backend for digest + library UI)**.

Frontend is a follow-up plan once the API is working.

---

## Scope

**Not in scope:** frontend, deep summaries (Tier 2), embeddings, chat, automated tests (add after implementation).

---

## Implementation Order

### Phase 1 — Schema migration

**File to create:** `backend/alembic/versions/<new_revision>_add_digest_schema.py`
Down-revision: `c8a2f1e94b3d`

`upgrade()` must do (in order):

1. **Add `user_status` PostgreSQL enum + column on `content_items`:**
   ```sql
   CREATE TYPE user_status AS ENUM ('unread', 'interested', 'dismissed')
   ALTER TABLE content_items ADD COLUMN user_status user_status NOT NULL DEFAULT 'unread'
   ```
   In Alembic: `op.execute("CREATE TYPE user_status AS ENUM ('unread', 'interested', 'dismissed')")` then `op.add_column(...)` with `server_default="unread"`.

   Triage states: `unread` (default), `interested` (kept for deep processing later), `dismissed` (hidden from weekly digest).

2. **Add `enrichment` JSONB column on `content_items`** (nullable):
   `op.add_column("content_items", sa.Column("enrichment", JSONB(), nullable=True))`

   Stored shape (written by enrichment job):
   ```json
   {
     "blurb": "...",
     "tags": ["..."],
     "content_type": "tutorial",
     "domain_matches": ["ai", "swe"],
     "relevance_score": 1.0,
     "input_kind": "full",
     "profile_version": 1,
     "enriched_at": "2025-06-23T12:00:00Z"
   }
   ```
   `input_kind`: `full` (title + description + transcript excerpt) or `metadata_only` (no transcript available).
   `profile_version`: copied from `user_interest_profiles.version` at enrichment time; used to detect stale enrichments when the profile changes.

3. **Replace unique constraint on `content_bodies`:**
   Drop: `content_bodies_content_item_id_key` (PostgreSQL auto-name for `unique=True` on the column)
   Add: `uq_content_bodies_item_kind` on `(content_item_id, body_kind)`
   This enables one transcript + one `summary_deep` per item (Tier 2).

4. **Add `summary_deep` to `body_kind` enum:**
   `op.execute("ALTER TYPE body_kind ADD VALUE IF NOT EXISTS 'summary_deep'")`
   (PostgreSQL 17 allows ADD VALUE in a transaction; no COMMIT workaround needed.)
   Forward-looking for Tier 2; no job writes this body kind in Stage 2.

5. **Create `user_interest_profiles` table:**
   Columns: `id UUID PK`, `version INT NOT NULL DEFAULT 1`, `domain_weights JSONB NOT NULL`, `context_prose TEXT`, `channel_notes JSONB`, `created_at TIMESTAMPTZ`, `updated_at TIMESTAMPTZ`

   Bump `version` when `domain_weights`, `context_prose`, or `channel_notes` change materially; enrichment job re-processes items whose stored `profile_version` is stale.

`downgrade()`: reverse in reverse order. Note: removing an enum value from `body_kind` is not possible in PostgreSQL; document this in the migration docstring.

---

### Phase 2 — Python model + enum updates

**`backend/app/database/models/enums.py`** (modify):
- Add `class UserStatus(StrEnum): UNREAD = "unread"; INTERESTED = "interested"; DISMISSED = "dismissed"`
- Add `SUMMARY_DEEP = "summary_deep"` to `BodyKind`

**`backend/app/database/models/content_item.py`** (modify):
- Add imports: `JSONB` from `sqlalchemy.dialects.postgresql`, `UserStatus` from enums
- Add columns:
  ```python
  user_status: Mapped[UserStatus] = mapped_column(
      Enum(UserStatus, name="user_status", native_enum=True),
      nullable=False, default=UserStatus.UNREAD
  )
  enrichment: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
  ```

**`backend/app/database/models/content_body.py`** (modify):
- Remove `unique=True` from `content_item_id` column
- Add `__table_args__`:
  ```python
  __table_args__ = (UniqueConstraint("content_item_id", "body_kind", name="uq_content_bodies_item_kind"),)
  ```

**`backend/app/database/models/user_interest_profile.py`** (create):
```python
class UserInterestProfile(Base, TimestampMixin):
    __tablename__ = "user_interest_profiles"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    domain_weights: Mapped[dict] = mapped_column(JSONB, nullable=False)
    context_prose: Mapped[str | None] = mapped_column(Text)
    channel_notes: Mapped[dict | None] = mapped_column(JSONB)
```

**`backend/app/database/models/__init__.py`** (modify): export `UserInterestProfile`

**`backend/alembic/env.py`** (modify): add `UserInterestProfile` to import so autogenerate picks it up

---

### Phase 3 — Fix `_get_or_create_body`

**`backend/app/ingest/operations/content.py`** (modify):

Current `_get_or_create_body` queries only by `content_item_id`. After the constraint change it must also filter by `body_kind` to avoid returning the wrong body when multiple kinds exist:

```python
def _get_or_create_body(session: Session, item: ContentItem, body_kind: BodyKind) -> ContentBody:
    body = session.scalar(
        select(ContentBody).where(
            ContentBody.content_item_id == item.id,
            ContentBody.body_kind == body_kind,
        )
    )
    if body is None:
        body = ContentBody(content_item_id=item.id, body_kind=body_kind, fetched_at=datetime.now(timezone.utc))
        session.add(body)
    return body
```

Update callers `save_body` and `mark_body_unavailable` to pass `body.body_kind` / `body_kind` argument. Public signatures are unchanged.

---

### Phase 4 — Config + dependencies

**`backend/app/config.py`** (modify):
- Add `openai_api_key: str | None = None` (optional at startup; enrichment runner validates and fails fast when missing)
- Add `openai_simple_model: str = "gpt-4o-mini"` (Tier 1 digest / cheap passes)
- Add `openai_model: str = "gpt-4o"` (Tier 2 deep analysis; content_artifacts later)
- Add `enrichment_transcript_max_seconds: int = 900` (15 minutes, per north-star)
- Add `enrichment_window_hours: int | None = None` (optional batch window; `None` = all pending items)

Provider-prefixed fields are intentional for now; a shared LLM factory (OpenAI, Anthropic, Mistral, Google, etc.) can sit in front of these later without renaming env vars per job.

**`backend/pyproject.toml`** (modify): add to dependencies:
- `openai>=2.43.0`
- `fastapi>=0.115.0`
- `uvicorn[standard]>=0.30.0` — install with `uv add "uvicorn[standard]"`

Run `uv lock` after editing.

---

### Phase 5 — Interest profile seed

**`backend/scripts/seed_interest_profile.py`** (create):

Inserts one `UserInterestProfile` row. Idempotent (skips if any profile exists). No argparse — config via `.env`.

Domain weights:
```python
{
    "ai": 1.0,
    "eu_ai": 0.95,       # European AI / Dutch tech ecosystem
    "swe": 0.85,
    "productivity": 0.7,
    "smarter": 0.65,
    "investing": 0.6,
    "entrepreneurship": 0.6,
}
```

`context_prose`: natural language description of the user — injected into every AI enrichment call so the blurb is contextualised to what's relevant to this specific person.

`channel_notes`: per-channel hints for the model, e.g.:
```python
{
    "boost": ["Fireship"],
    "deprioritize": ["reaction", "drama"]
}
```
Serialized into the enrichment prompt alongside `context_prose`.

Run with: `uv run python scripts/seed_interest_profile.py`

---

### Phase 6 — Processing module

Layout mirrors `app/ingest/`:
```
app/processing/
├── __init__.py
├── sampling.py            # transcript excerpt by time (no DB imports)
├── jobs/
│   ├── __init__.py
│   └── enrich_items.py
├── enrichment.py          # Anthropic adapter (no DB imports)
└── runner.py
```

**`backend/app/processing/sampling.py`**:

Time-based transcript excerpt from `snippets` JSON (not character truncation). Aligns with north-star "~first 15 min".

```python
def excerpt_transcript(snippets: list[dict] | None, max_seconds: float = 900.0) -> str:
    """Join snippet text while snippet.start < max_seconds."""
```

Also truncate `description` to a sensible char cap (~1000) before sending to the model.

**`backend/app/processing/enrichment.py`**:

Anthropic adapter. No DB imports.

```python
@dataclass
class InterestProfileInput:
    domain_keys: list[str]           # keys the model may return in domain_matches
    context_prose: str | None
    channel_notes: dict | None
    author: str | None               # channel name for channel_notes context

def enrich_item(
    *,
    title: str,
    description: str | None,
    transcript_excerpt: str | None,
    input_kind: Literal["full", "metadata_only"],
    profile: InterestProfileInput,
) -> dict:
    """Calls Claude Haiku. Returns {blurb, tags, content_type, domain_matches}. Raises on API/JSON error."""
```

Prompt asks for JSON with:
- `blurb`: 1-2 sentences of what it's actually about (not a re-statement of the title)
- `tags`: 3-7 lowercase topic tags
- `content_type`: one of `tutorial | explainer | opinion | interview | news | demo | other`
- `domain_matches`: subset of the profile's domain keys

Prompt context includes: `context_prose`, `channel_notes` (boost/deprioritize lists), and `author` when present.

Input assembly:
- **full**: title + truncated description + transcript excerpt from `sampling.excerpt_transcript(snippets, max_seconds=settings.enrichment_transcript_max_seconds)`
- **metadata_only**: title + truncated description only; prompt notes lower confidence (no transcript)

Model: `claude-haiku-4-5-20251001`, `max_tokens=512`.

**`backend/app/processing/jobs/enrich_items.py`**:

Key functions:
- `_items_needing_enrichment(session, window_hours)` → items where:
  - `enrichment IS NULL` OR `(enrichment->>'profile_version')::int < current_profile.version`
  - AND optionally `published_at >= now() - window_hours` when `window_hours` is set
  - Includes **all** `body_status` values: `available` → full path; `pending` / `unavailable` → metadata-only path
- `_compute_relevance(domain_matches, domain_weights) -> float` → **max** weight among matched domains (0.0 if no matches). A strong single-topic match (e.g. only `ai` at 1.0) scores 1.0, not ~0.19 from dividing by total weight.
- `_build_enrichment_payload(llm_result, relevance_score, input_kind, profile_version) -> dict` → full JSONB blob including `enriched_at`
- `enrich_pending_items(session) -> dict[str, int]` → processes all pending items, commits per-item for partial progress. Returns `{processed, failed, skipped}`.

When a transcript becomes available after a metadata-only enrichment (`body_status` changes to `available`), the next run re-enriches because full input supersedes metadata-only (or treat stale `input_kind` like stale `profile_version`).

Idempotency: skip items with current `profile_version` and appropriate `input_kind`; re-runs are safe.

**`backend/app/processing/runner.py`**:
```python
def run_enrichment(*, window_hours: int | None = None) -> dict[str, int]:
    # validates openai_api_key is set before calling API
    with get_session() as session:
        return enrich_pending_items(session, window_hours=window_hours or settings.enrichment_window_hours)
```

**`backend/scripts/run_enrichment.py`** (create): CLI entry, prints counts. Uses `settings.enrichment_window_hours` by default.

**`backend/scripts/sync_youtube.py`** (modify): call `run_enrichment()` after `run_sync()` so daily sync + enrichment runs in one command. Pass `window_hours=settings.ingest_sync_window_hours` so only the sync window is enriched on each run (not full backfill every time).

---

### Phase 7 — FastAPI API layer

Per `backend/AGENTS.md`: all route handlers must be `async def`. This requires an async SQLAlchemy session alongside the existing sync one.

**`backend/app/database/session.py`** (modify): add async session factory using `postgresql+psycopg_async://` DSN (psycopg3 ships the async driver; no new package needed). Sync session stays untouched for CLI scripts.

**Layout:**
```
app/api/
├── __init__.py
├── deps.py                # get_db async dependency
├── schemas.py             # Pydantic response models
├── main.py                # FastAPI app, CORS, router registration
└── routes/
    ├── __init__.py
    ├── items.py           # GET /items, PATCH /items/{id}/status
    └── subscriptions.py   # GET /subscriptions
```

**`backend/app/api/schemas.py`**:
- `EnrichmentOut`: blurb, tags, content_type, domain_matches, relevance_score, input_kind, profile_version, enriched_at
- `ContentItemOut`: id, subscription_id, title, description, url, thumbnail_url, author, published_at, user_status, enrichment (nullable)
- `SubscriptionOut`: id, title, url
- `PaginatedItemsOut`: items, total, limit, offset
- `StatusUpdateIn`: status: UserStatus

**`GET /items`** — query params:
- `sort`: `chronological` | `relevance` (default `relevance` for digest view)
- `status`: `all` | `unread` | `interested` | `dismissed` (default `unread` for weekly digest; use `all` for library)
- `subscription_id`: optional UUID filter
- `domain`: optional domain key filter
- `published_after`: optional ISO datetime (weekly digest window)
- `window_hours`: optional int alternative to `published_after` (e.g. `168` = last week)
- `limit` (default 50, max 200), `offset`

Default digest query: `?sort=relevance&status=unread&window_hours=168` (excludes dismissed).

Sort by relevance: `ORDER BY (enrichment->>'relevance_score')::float DESC NULLS LAST, published_at DESC`

Metadata-only items sort after full enrichments at the same score: secondary sort on `input_kind` (`full` before `metadata_only`) or apply a small score penalty (e.g. `relevance_score * 0.85`) at write time.

Domain filter: `enrichment->'domain_matches' @> '["<domain>"]'::jsonb`

**`PATCH /items/{id}/status`** — body: `StatusUpdateIn` (`unread` | `interested` | `dismissed`). Returns updated `ContentItemOut`.

**`GET /subscriptions`** — all active subscriptions ordered by title.

**`backend/app/api/main.py`**:
- CORS: `allow_origins=["http://localhost:5173"]` (Vite default)
- Include items + subscriptions routers

Start: `uv run uvicorn app.api.main:app --reload --port 8000`

---

## File list (creation order)

| # | File | Action |
|---|------|--------|
| 1 | `backend/alembic/versions/<new>_add_digest_schema.py` | create |
| 2 | `backend/app/database/models/enums.py` | modify |
| 3 | `backend/app/database/models/content_item.py` | modify |
| 4 | `backend/app/database/models/content_body.py` | modify |
| 5 | `backend/app/database/models/user_interest_profile.py` | create |
| 6 | `backend/app/database/models/__init__.py` | modify |
| 7 | `backend/alembic/env.py` | modify |
| 8 | `backend/app/ingest/operations/content.py` | modify |
| 9 | `backend/app/config.py` | modify |
| 10 | `backend/pyproject.toml` | modify + `uv lock` |
| 11 | `backend/scripts/seed_interest_profile.py` | create |
| 12 | `backend/app/processing/__init__.py` | create (empty) |
| 13 | `backend/app/processing/sampling.py` | create |
| 14 | `backend/app/processing/jobs/__init__.py` | create (empty) |
| 15 | `backend/app/processing/enrichment.py` | create |
| 16 | `backend/app/processing/jobs/enrich_items.py` | create |
| 17 | `backend/app/processing/runner.py` | create |
| 18 | `backend/scripts/run_enrichment.py` | create |
| 19 | `backend/scripts/sync_youtube.py` | modify |
| 20 | `backend/app/database/session.py` | modify |
| 21 | `backend/app/api/__init__.py` | create (empty) |
| 22 | `backend/app/api/deps.py` | create |
| 23 | `backend/app/api/schemas.py` | create |
| 24 | `backend/app/api/routes/__init__.py` | create (empty) |
| 25 | `backend/app/api/routes/items.py` | create |
| 26 | `backend/app/api/routes/subscriptions.py` | create |
| 27 | `backend/app/api/main.py` | create |

---

## Verification

```bash
# 1. Run migration
cd backend && uv run alembic upgrade head

# 2. Seed interest profile
uv run python scripts/seed_interest_profile.py

# 3. Sync + enrich (uses existing channels)
uv run python scripts/sync_youtube.py
# Should print sync results then enrichment counts

# 4. Start API
uv run uvicorn app.api.main:app --reload --port 8000

# 5. Check endpoints
curl "http://localhost:8000/items?sort=relevance&status=unread&window_hours=168&limit=10" | python -m json.tool
curl "http://localhost:8000/subscriptions" | python -m json.tool
curl -X PATCH "http://localhost:8000/items/<id>/status" \
  -H "Content-Type: application/json" \
  -d '{"status": "interested"}'
curl -X PATCH "http://localhost:8000/items/<id>/status" \
  -H "Content-Type: application/json" \
  -d '{"status": "dismissed"}'

# 6. Verify existing tests still pass
uv run pytest -m "not integration"
```

---

## Key decisions

- **Sync session for CLI, async session for API**: AGENTS.md requires `async def` routes. Psycopg3 ships the async driver — no new package. Sync session stays for scripts.
- **Commit-per-item in enrichment**: partial progress preserved; idempotent re-runs via `enrichment IS NULL` / stale `profile_version` / upgraded `input_kind`.
- **15-minute transcript excerpt via snippets**: matches north-star; not character-based truncation.
- **Metadata-only enrichment**: items without transcripts still get blurbs and scores; flagged with `input_kind: metadata_only`.
- **`dismissed` user status**: hides noise from the weekly digest; `interested` maps to north-star "keep".
- **Relevance score = max matched domain weight**: strong single-topic videos rank correctly; no division by total profile weight.
- **`profile_version` on interest profile + enrichment JSON**: bump profile version to trigger re-enrichment without schema changes.
- **`channel_notes` in prompt**: per-channel boost/deprioritize hints alongside `context_prose`.
- **`openai_api_key` optional in settings**: required only when `run_enrichment()` runs, so sync-only scripts work without the key.
- **Enrichment window on daily sync**: `sync_youtube.py` passes `ingest_sync_window_hours` so each run only enriches recent items; use `run_enrichment.py` without a window for full backfill.
- **No `app/api/operations/` layer**: only 2 endpoints with simple queries — a separate operations layer is premature abstraction.
- **`eu_ai` as a separate domain**: Dutch/European AI coverage is specific enough to warrant its own key separate from `ai`.
