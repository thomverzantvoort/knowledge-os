# Architecture

Technical design for Knowledge-OS ingest and data model. Product goals live in [north-star.md](north-star.md).

---

## Domain model

Three concepts, in order:


| Concept          | Meaning                       | Example                               |
| ---------------- | ----------------------------- | ------------------------------------- |
| **Subscription** | A feed you follow             | Fireship on YouTube, Lenny's Substack |
| **Content item** | One thing that feed published | A video, an article                   |
| **Body**         | Raw text for that item        | Transcript (with snippets), markdown  |


**Platform** (YouTube, Substack) is not a separate entity. It is `subscriptions.kind`, which selects which adapter and job logic to run.

**Content type** (video, article) is `content_items.kind`.

All content types share one library. Filter by subscription kind or content kind in the UI.

---

## Database

### Tables

```
subscriptions
  └── content_items  (1:N)
        └── content_bodies  (1:1)
```

#### `subscriptions`

A channel, newsletter, or RSS feed you subscribe to.


| Column                     | Type        | Notes                                                   |
| -------------------------- | ----------- | ------------------------------------------------------- |
| `id`                       | UUID        | PK                                                      |
| `kind`                     | enum        | Platform adapter: `youtube_channel`, `substack` (later) |
| `external_id`              | string      | Channel ID, Substack slug, etc. Unique globally         |
| `title`                    | string      | Filled by enrich step                                   |
| `url`                      | string      | Channel or publication URL                              |
| `is_active`                | bool        | Inactive subscriptions are skipped by sync              |
| `last_synced_at`           | timestamptz | Set after a successful sync job                         |
| `created_at`, `updated_at` | timestamptz |                                                         |


#### `content_items`

Metadata for one published video or article.


| Column                     | Type        | Notes                                             |
| -------------------------- | ----------- | ------------------------------------------------- |
| `id`                       | UUID        | PK                                                |
| `subscription_id`          | UUID        | FK → `subscriptions.id`                           |
| `external_id`              | string      | Video ID or article slug. Unique per subscription |
| `kind`                     | enum        | `video`, `article` (later)                        |
| `title`                    | string      |                                                   |
| `description`              | string      | Nullable                                          |
| `url`                      | string      |                                                   |
| `thumbnail_url`            | string      | Nullable for articles                             |
| `author`                   | string      | Channel name or newsletter author                 |
| `published_at`             | timestamptz | Indexed                                           |
| `body_status`              | enum        | `pending`, `available`, `unavailable`             |
| `processing_status`        | enum        | `ingested` for now; `kept` etc. later             |
| `created_at`, `updated_at` | timestamptz |                                                   |


Unique constraint: `(subscription_id, external_id)`.

#### `content_bodies`

Raw body text, stored separately so metadata and payload can evolve independently.


| Column                     | Type        | Notes                                                |
| -------------------------- | ----------- | ---------------------------------------------------- |
| `id`                       | UUID        | PK                                                   |
| `content_item_id`          | UUID        | FK → `content_items.id`, unique (1:1)                |
| `body_kind`                | enum        | `transcript`, `markdown` (later)                     |
| `language_code`            | string      | Nullable                                             |
| `is_generated`             | bool        | Nullable; relevant for auto-generated transcripts    |
| `text`                     | text        | Full plain text                                      |
| `snippets`                 | JSONB       | Timestamped segments; transcripts only               |
| `error`                    | text        | Last fetch error when `body_status` is `unavailable` |
| `fetched_at`               | timestamptz |                                                      |
| `created_at`, `updated_at` | timestamptz |                                                      |


### Enums


| Enum               | Values (now)                          | Values (later) |
| ------------------ | ------------------------------------- | -------------- |
| `SubscriptionKind` | `youtube_channel`                     | `substack`     |
| `ContentKind`      | `video`                               | `article`      |
| `BodyKind`         | `transcript`                          | `markdown`     |
| `BodyStatus`       | `pending`, `available`, `unavailable` |                |
| `ProcessingStatus` | `ingested`                            | `kept`, etc.   |


### Migration from current schema

The codebase still uses `sources`, `source_id`, `SourceKind`, and `transcript_status`. The target names above replace those during the ingest implementation pass.

---

## Ingest pipeline

Ingest fetches external data and writes it to the three tables. It does not run digest, chunking, embeddings, or chat (see north-star tiers 2+).

### Layered layout

```text
app/ingest/
├── adapters/          # Internet → plain Python objects. No database imports.
│   └── youtube.py
├── operations/          # Database operations. No HTTP. Thin read/write helpers.
│   ├── subscriptions.py
│   └── content.py
├── jobs/                # Ingest tasks. Wires adapters + operations + commits.
│   ├── upsert_subscription.py
│   ├── sync_subscription.py
│   └── sync_all.py
└── runner.py            # Entrypoints for scripts and (later) API background tasks.
```


| Layer         | Responsibility                          | Example                                              |
| ------------- | --------------------------------------- | ---------------------------------------------------- |
| **Adapter**   | Fetch from an external platform         | RSS feed, transcript API                             |
| **Operation** | Read/write database rows                | `ensure_subscription`, `save_body`                   |
| **Job**       | Complete ingest task                    | Register subscription, sync one feed, sync all feeds |
| **Runner**    | Invoke jobs with config from `settings` | `run_sync()`, `run_initial_ingest()`                 |


### Layer rules

- Adapters never import SQLAlchemy.
- Operations never import feedparser, httpx for ingest, or platform SDKs.
- Jobs own transaction boundaries and orchestration.
- Scripts and API routes call runner or jobs; they contain no business logic.

### Data flow: register a subscription

```text
seed_subscriptions.py
  → jobs/upsert_subscription.py
      → operations/subscriptions.py     ensure row exists
      → adapters/youtube.py             fetch title + URL from RSS
      → operations/subscriptions.py     update metadata
      → commit
```

Input contract: `SubscriptionInput` (`kind`, `external_id`, `is_active`). Same shape for local JSON today and FastAPI `POST /subscriptions` later. No file path in `app/config.py`; the dev script holds the JSON path locally.

### Data flow: sync content

```text
sync_youtube.py
  → runner.run_sync()
    → jobs/sync_all.py
      → jobs/sync_subscription.py         per subscription
          → adapters/youtube.py         list items in time window
          → operations/content.py         ensure content_item rows
          → adapters/youtube.py         fetch transcript when needed
          → operations/content.py         save body, set body_status
          → operations/subscriptions.py   set last_synced_at
          → commit (one commit per subscription)
```

### Idempotency


| Case                                              | Action                                                         |
| ------------------------------------------------- | -------------------------------------------------------------- |
| Content item not in DB                            | Insert item, fetch body                                        |
| Item exists, `body_status` available              | Skip body fetch                                                |
| Item exists, `body_status` pending or unavailable | Retry body fetch                                               |
| Body fetch fails                                  | Store error on `content_bodies`, set `body_status` unavailable |
| Re-run sync                                       | No duplicate rows (`subscription_id` + `external_id` unique)   |


Initial ingest and recurring sync use the **same job** with different time windows from config (`ingest_initial_window_hours` vs `ingest_sync_window_hours`). There is no separate "what's new" job; new items are discovered by scanning the feed and skipping existing rows.

### RSS constraint

YouTube channel sync uses RSS (`feeds/videos.xml`). RSS returns roughly the **15 most recent** entries per channel. A larger initial time window filters those entries; it does not backfill older history. Accept this for MVP.

### Adapter boundary

Adapters return plain dataclasses or Pydantic models. Jobs map them before calling operations:

```text
ContentItemDraft   → operations/content.ensure_content_item
BodyDraft          → operations/content.save_body
```

YouTube maps `VideoData` and `Transcript` to drafts. Substack will map post metadata and markdown to the same drafts later.

---

## Configuration

Ingest-related settings live in `app/config.py`:


| Setting                       | Purpose                                        |
| ----------------------------- | ---------------------------------------------- |
| `ingest_initial_window_hours` | First ingest window (default 336)              |
| `ingest_sync_window_hours`    | Recurring sync window (default 168)            |
| `ingest_subscription_id`      | Optional: sync one subscription only (env var) |
| `transcript_languages`        | Preferred transcript languages                 |
| `exclude_shorts`              | Skip YouTube Shorts in RSS                     |


No argparse in `scripts/`. Tune behavior via config and `.env`.

---

## Scripts (dev entrypoints)

```text
scripts/
  seed_subscriptions.py         # Read local JSON → upsert_subscription job
  ingest_initial_youtube.py     # runner.run_initial_ingest()
  sync_youtube.py               # runner.run_sync()
  probe_youtube_channel.py      # Debug adapter only; no database
```

```text
data/input/
  subscriptions.json            # Dev-only subscription list
```

Example operator flow:

```bash
uv run python scripts/seed_subscriptions.py
uv run python scripts/ingest_initial_youtube.py
uv run python scripts/sync_youtube.py
```

---

## `app/` layout (target)

```text
app/
├── config.py
├── database/
│   ├── session.py
│   └── models/
│       ├── subscription.py
│       ├── content_item.py
│       ├── content_body.py
│       └── enums.py
├── ingest/
│   ├── adapters/
│   ├── operations/
│   ├── jobs/
│   └── runner.py
├── api/              # later: FastAPI routes
├── processing/       # later: digest, chunking, embeddings (north-star tier 2)
└── retrieval/        # later: search + chat
```

Ingest is one bounded module. Processing and retrieval are separate concerns that read from `content_items` and `content_bodies` but do not live inside `ingest/`.

---

## Extending to new platforms

Add one adapter file and one branch in `jobs/sync_subscription.py`:

```text
ingest/adapters/substack.py     # RSS or scrape → ContentItemDraft + BodyDraft (markdown)
```

`operations/content.py` stays unchanged. `subscriptions.kind` selects the adapter.

Meetings and other non-feed data are out of scope for ingest. If needed later, model them in a separate domain rather than stretching these tables.

---

## Relationship to north-star


| North-star step                     | Architecture component        |
| ----------------------------------- | ----------------------------- |
| Ingest channel videos + transcripts | `ingest/` jobs and operations |
| Digest blurb + tags                 | `processing/` (not built)     |
| Weekly digest / library UI          | `api/` + frontend (not built) |
| Deep processing on kept items       | `processing/` (not built)     |
| Chat with citations                 | `retrieval/` (not built)      |


Tier 1 ingest stores raw bodies (`content_bodies`) as the source of truth for all downstream work.

---

## Current implementation status


| Area                                                 | Status                          |
| ---------------------------------------------------- | ------------------------------- |
| DB schema (initial migration)                        | Done; uses old `sources` naming |
| YouTube adapter (RSS + transcripts)                  | Done at `ingest/youtube.py`     |
| Subscription upsert from JSON                        | Partial at `ingest/sources.py`  |
| Content persistence + sync jobs                      | Not built                       |
| Schema rename (`subscriptions`, `body_status`, etc.) | Planned                         |
| Ingest folder layout (adapters / operations / jobs)  | Planned                         |


