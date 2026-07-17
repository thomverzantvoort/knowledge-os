# Rollout sparring notes

Captured from the deployment / product sparring session (2026-07-17).
Working doc in `temp/` until decisions land in `docs/` or the product is further along.

**North star for this phase:** improve the product until it feels like a solid V1, then learn production by putting it on a Hetzner VPS. Multi-model, RAG, and “wisdom mode” come after that.

---

## Context from the sparring session

### Why Hetzner (not Supabase / Vercel-first)

- Personal learning project, not a SaaS product yet.
- Sovereign / EU-friendly story matters for company AI work: one VPS in Amsterdam / Falkenstein / etc., data and app colocated.
- Doing it the harder way (compose + Caddy + your own Postgres) teaches the same shape clients want on Azure / GCP.
- Managed platforms are fine for demos; weaker for “I can run this myself.”



### Target runtime shape (one cheap VPS)

```text
Internet → Caddy (HTTPS + static SPA + /api reverse proxy)
              ├─ frontend (Vite build, static)
              └─ FastAPI
                    ├─ Postgres (same box, not public)
                    └─ jobs (same image, separate process / cron)
```

- **One Docker image, two processes** for API vs sync/enrich jobs (not necessarily two different images).
- Deep-on-Save can stay `create_task` for a while; split to a worker when jobs get heavy.
- No Kubernetes. Compose on one VM is enough.
- Frontend is static files served by Caddy, not a long-running Node server.



### Git / environments

- Laptop = true **dev** (local Postgres via compose, local API, local Vite).
- Feature branch → merge to `main` → GitHub Actions deploys to Hetzner (**prod**).
- No mandatory long-lived `develop` branch unless a staging box is added later (`dev.yourdomain`).



### LLM stack (decisions for now)


| Topic                   | Decision                                                                                  |
| ----------------------- | ----------------------------------------------------------------------------------------- |
| Providers for V1        | **OpenAI only**                                                                           |
| Abstraction             | Keep thin `AgentClient` + `get_agent()` factory; widen later                              |
| OpenRouter              | Optional convenience gateway later; not needed for V1                                     |
| Custom “router” product | No; factory + model list is enough                                                        |
| Langfuse                | Useful later for traces / evals; **not** a model router; add after chat is useful         |
| Evals                   | Matter more as quality grows; golden fixtures + schemas first, Langfuse to organize later |


---



## Phased rollout



### Phase 0 — Improve the product (current priority)

Goal: a V1 you are happy to use daily. Stay on OpenAI.

#### 0.1 User settings

- **Subscriptions:** see all active subscriptions (the feeds content is pulled from); manage them (add / edit / deactivate as the API allows).
- **Interest profile:** edit the context used for digests / summaries (domain weights, context prose, channel notes, output language, etc.).
- **System prompts:** edit the prompts that drive digest / deep outline / deep summary (and later chat), so quality is tunable without code deploys.



#### 0.2 Chat (Library)

- From a saved Library item, open detail with **outline + summary on the left**, **chat on the right**.
- Chat grounded on the **full transcript** for that video (per north-star), with timestamp citations.
- OpenAI only for now.



#### 0.3 UI polish

- Faster triage and library actions (buttons / affordances so you do not always need click → panel → action).
- General UX cleanup until Inbox / Library / History feel crisp.

**Exit criteria for Phase 0:** settings work, chat works, UI feels good enough that you want this running 24/7.

---



### Phase 1 — Production on Hetzner (learn deploy)

Goal: log in from anywhere, use the real UI against real data on your VPS.

1. Backend Dockerfile + production compose (Caddy, API, Postgres, optional cron/worker).
2. Caddyfile: TLS, SPA static files, `/api/*` → FastAPI.
3. Secrets / env on the server (not in git).
4. Firewall, Postgres not public, backups (`pg_dump`).
5. Domain + HTTPS; `AUTH_COOKIE_SECURE` and prod CORS / same-origin API.
6. Scheduled sync (cron or worker) instead of only manual scripts.

**Exit criteria:** you can open the site, log in, triage, chat; sync runs on a schedule; restore from backup is possible.

---



### Phase 2 — CI/CD

Goal: merge to `main` updates production without manual SSH ritual.

1. GitHub Actions on PR: lint + tests (no deploy).
2. On push to `main`: build images / frontend, push (e.g. GHCR), deploy over SSH (`compose pull && up`, Alembic migrate), health check.
3. Optional later: staging environment on a second cheap box or second compose project.

**Exit criteria:** a green merge to `main` is what ships V1 updates.

Note: Phase 1 and 2 can overlap (first manual deploy, then automate the same steps). Prefer getting a working manual Hetzner deploy before polishing Actions.

---



### Phase 3 — Multi-model and chat upgrades

Goal: choose models in chat without rewriting the app.

- Add Anthropic (and maybe Mistral) via the existing factory.
- In chat UI: pick OpenAI vs Anthropic (etc.) per conversation or message.
- Improve streaming UX.
- Still no requirement for OpenRouter unless you want many models with one key.

---



### Phase 4 — Beyond subscriptions

- Add one-off videos / URLs you find online (not only subscribed feeds).
- Process them through the same ingest → (optional save) → deep → chat path.

---



### Phase 5 — Personal knowledge / RAG (“wisdom mode”)

Goal: store **insights** from chat (not full transcripts), embed those, and ask questions across your personal knowledge base.

- Explicit “save this insight” (or similar) from chat.
- Embeddings + retrieval over insights / curated notes.
- Separate “wisdom” mode: ask across saved insights, not raw corpus transcripts.
- Full-transcript corpus RAG stays deferred unless needed; transcripts remain source of truth per video chat.

This is the latest / school-horizon idea, not near-term.

---



## Priority order (short)

1. **Product V1:** settings (subscriptions, profile, prompts) → Library chat layout → UI polish (OpenAI).
2. **Hetzner + Caddy:** get it live and usable.
3. **GitHub Actions / CI/CD:** make shipping boring.
4. **Multi-provider + streaming.**
5. **One-off URL ingest.**
6. **Insights + RAG wisdom mode.**

---



## Explicit non-goals for the near term

- Building a multi-tenant SaaS.
- Supabase / Vercel as the primary production path for this learning track.
- Langfuse / OpenRouter before chat + deploy are solid.
- Corpus-wide embedding of every transcript.
- Kubernetes.

---



## Mapping to existing docs


| Doc                        | Role                                              |
| -------------------------- | ------------------------------------------------- |
| `docs/north-star.md`       | Product intent (Inbox / Library / chat / tiers)   |
| `docs/architecture.md`     | Technical design; already assumes Caddy + `/api`  |
| `temp/rollout-sparring.md` | This file: phased rollout + deploy / LLM sparring |


When Phase 0 scope is stable, fold the product bits into north-star / architecture and keep infra notes in a future `docs/deploy.md` (not created yet).