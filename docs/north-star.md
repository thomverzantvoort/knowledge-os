## North star

A personal **YouTube/podcast triage and deep-dive system**: each week you quickly see what was published, decide what is worth your time, and for kept items you can explore details and **chat with grounded answers linked to timestamps**.

Not a corpus-wide RAG engine yet. **Ingest wide, process deep only for what you keep.**

---

## Three MVP surfaces

| Surface | Purpose |
|---------|---------|
| **Weekly digest** | New content in a time window, ranked/scored for you, quick skim |
| **Library** | All ingested videos; filter kept vs everything |
| **Chat** | Select kept video(s), ask questions, get answers with citations |

---

## Data pipeline (tiered)

### Tier 1: Every ingested video (always)

- Fetch from subscribed channels (no shorts)
- Store: metadata, thumbnail URL, **full raw transcript** (snippets JSON)
- Generate: **short digest blurb + tags** from title, description, and ~first 15 min of transcript
- Optional: simple relevance score vs your interest profile (tags/keywords)
- **No** detailed summary, **no** chunking, **no** embeddings

### Tier 2: Kept / interesting videos only

Triggered when you mark a video as kept (or on first deep-dive):

- **Timestamped outline** (structured chapters + summaries + start times) for detail view and navigation
- **Chunk raw transcript** (~60 sec windows, overlap) for search and chat
- **Embed chunks** for semantic retrieval in chat

### Tier 3: Later (not MVP)

- Cross-video / corpus-wide search over kept content
- Daily sync automation, proxy/IP rotation for scraping at scale
- Richer personalization, reranking, hybrid FTS + vector tuning

---

## What each artifact is for

| Artifact | Used for |
|----------|----------|
| Raw transcript | Source of truth, chunking, citations, reprocessing |
| Digest blurb | Weekly cards, library previews, sorting |
| Timestamped outline | Skimming, chapters, jump links (`?t=`), detail page |
| Embedded chunks | Chat retrieval (evidence with timestamps) |

**Chat grounds on retrieved raw chunks, not the full transcript and not the summary.**

---

## MVP build order

1. **Ingest** channel videos in a window (e.g. 336h initially) → persist metadata, thumbnail, raw transcript  
2. **Digest job** → blurb + tags (+ basic relevance) for each new item  
3. **Weekly digest UI** → cards with blurb, thumbnail, watch link, **keep / dismiss**  
4. **Library UI** → all videos + filter kept  
5. **Deep processing job** → on kept: outline + chunk + embed  
6. **Chat UI** → select kept video(s), Q&A with timestamp citations  

---

## Explicit non-goals for MVP

- Embedding every published video  
- Full-transcript LLM passes for digest  
- Cross-channel “ask my whole corpus” RAG  
- Perfect backfill beyond RSS limits (accept ~15 recent per feed for now, extend later)  
- Production scraping infra (proxies, etc.)  

---

## One-line summary

**Scrape channel videos → store raw transcripts → generate cheap digest blurbs for weekly triage → on videos you keep, build timestamped outlines and embedded chunks → chat against those chunks with citations.**

That is the MVP. RAG tuning, corpus search, and infra hardening come after this loop works end to end.