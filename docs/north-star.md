## North star

A personal **YouTube/podcast triage and deep-dive system**: new content lands in an inbox you clear on your terms, saved items get rich summaries, and you can **chat with one video at a time** using the full transcript as context.

Not a corpus-wide RAG engine yet. **Ingest wide, process deep only for what you save.**

---

## Three MVP surfaces

| Surface         | Purpose                                                                 |
| --------------- | ----------------------------------------------------------------------- |
| **Inbox Zero**  | Untriaged new content in a time window, ranked for you; clear the queue |
| **Library**     | Saved items only; outline + detailed summary; entry point to chat       |
| **History**     | Everything ingested, chronological archive (blurbs only unless saved)   |

**Chat** is not a top-level nav item. It is a dedicated view per saved video (`/library/:id/chat`), opened from Library, with a reference sidebar for outline or summary while you talk.

---

## Inbox Zero (triage)

- Shows **unread** items from the last **7 days**, sorted by **relevance score** (personal interest profile).
- Goal: **inbox zero** — triage what is new without opening YouTube or pasting URLs elsewhere.
- **Click a card** → preview panel with full blurb, tags, metadata (not a direct jump to YouTube).
- **Close without choosing** → item **stays in Inbox Zero**.
- **Save** → mark `interested`, leave inbox, trigger Tier 2 processing; when ready, jump to that item in Library.
- **Pass** → mark `dismissed`, leave inbox, no deep processing; item remains in History with blurb only.
- **Unread items older than the inbox window** fall out of Inbox into History automatically (no forced Pass).

### Digest blurb (Tier 1)

The blurb is for **personal triage**, not a generic video description. It should answer: what is this really about **for me**, and is it worth saving or passing? Prompt context includes the interest profile (`context_prose`, domain weights, channel notes).

---

## Library (saved items)

- Only **`interested`** items, chronological (or by relevance later).
- Detail view tabs: **Outline** (timestamped chapters, jump links `?t=`) | **Summary** (longer narrative recap).
- Both are generated on **Save** (Tier 2). Default tab: Outline.
- **Chat** button → dedicated chat view for that video; reference panel toggles Outline | Summary on the side (desktop) or bottom sheet (mobile).

---

## History (archive)

- **All** ingested content items, chronological.
- Includes passed, expired-from-inbox unread, and saved items (saved items also appear in Library).
- Blurb + metadata only unless the item was saved (then full Tier 2 artifacts exist when opened from Library).
- Channel filter / search: later milestone for “find this podcast while listening.”

---

## Data pipeline (tiered)

### Tier 1: Every ingested video (always)

- Fetch from subscribed channels (no shorts)
- Store: metadata, thumbnail URL, **full raw transcript** (snippets JSON)
- Generate: **personal triage blurb + tags + relevance score** from title, description, and ~first 15 min of transcript
- **No** detailed summary, **no** timestamped outline, **no** chunking, **no** embeddings

### Tier 2: Saved videos only

Triggered when you **Save** in Inbox Zero:

- **Timestamped outline** — structured chapters + short section summaries + start times
- **Detailed narrative summary** — longer prose recap for “what did I miss?”
- Stored in `content_artifacts` (summary + chapters JSON)

Chat for a single saved video (MVP):

- **Full raw transcript** in the LLM context (plus system prompt and interest profile)
- Timestamp citations in answers (`[12:34]` → YouTube `?t=...`)
- Chunking + embeddings **deferred** until needed (very long transcripts or corpus-wide chat)

### Tier 3: Later (not MVP)

- Chunk transcript + embed for retrieval (long single videos, or corpus scale)
- Cross-video / corpus-wide “wisdom” chat over all saved content
- Weekly AI overview of the whole inbox batch
- Multi-video canvas UI (drag videos onto a chat workspace)
- Daily sync automation, proxy/IP rotation for scraping at scale

---

## What each artifact is for

| Artifact            | Used for                                                       |
| ------------------- | -------------------------------------------------------------- |
| Raw transcript      | Source of truth, chat context, citations, reprocessing           |
| Digest blurb        | Inbox cards, History previews, relevance ranking               |
| Timestamped outline | Library detail, skimming, chapters, jump links (`?t=`)         |
| Detailed summary    | Library detail, narrative recap without watching               |
| Embedded chunks     | Future: long-video fallback and corpus-wide retrieval          |

**MVP chat grounds on the full transcript for one video, not the blurb and not the generated summaries.** Summaries are for human reading; the transcript is for accurate Q&A.

---

## User status model

| Status        | UI label | Inbox | Library | History |
| ------------- | -------- | ----- | ------- | ------- |
| `unread`      | (new)    | Yes*  | No      | Yes     |
| `interested`  | Saved    | No    | Yes     | Yes     |
| `dismissed`   | Passed   | No    | No      | Yes     |

\*Unread only while inside the inbox time window (e.g. 7 days since publish).

---

## MVP build order

| Step | What                                                        | Status   |
| ---- | ----------------------------------------------------------- | -------- |
| 1    | Ingest → metadata, thumbnail, raw transcript                | Done     |
| 2    | Digest job → personal blurb + tags + relevance              | Done     |
| 3    | Auth + basic library grid                                   | Done     |
| 4    | Inbox Zero UI → preview panel, Save / Pass, status PATCH    | Next     |
| 5    | History UI → all items, chronological                       | Next     |
| 6    | Library UI → saved only, Outline \| Summary detail            | Next     |
| 7    | Deep job on Save → outline + detailed summary               | Next     |
| 8    | Chat UI → per-video view, full transcript, citations        | Next     |
| 9    | History channel filter / search                             | Later    |
| 10   | Improve blurb prompt (personal “for me / skip” framing)     | Ongoing  |

---

## Explicit non-goals for MVP

- Embedding every published video
- Full-transcript LLM passes at ingest (only blurbs at Tier 1)
- Cross-channel “ask my whole corpus” RAG
- Weekly AI batch overview of all new videos
- Multi-video canvas / drag-to-chat workspace
- Multi-user auth (solo `.env` password is fine for now)
- Perfect backfill beyond RSS limits (accept ~15 recent per feed for now)
- Production scraping infra (proxies, etc.)

---

## One-line summary

**Sync subscribed channels → cheap personal blurbs for Inbox Zero triage → on Save, generate outline + detailed summary → Library for study → chat with the full transcript per saved video.**

Corpus RAG, embeddings at scale, and infra hardening come after this loop works end to end.
