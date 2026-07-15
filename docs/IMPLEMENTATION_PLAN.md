# Implementation Plan — The Family Chronicle REST API

> A shared, searchable family memory service built with **FastAPI**, backed by a
> pluggable **Cortex** memory provider (Semvec target, keyword+LLM fallback for the
> hackathon), managed and run head­less with **uv**.

---

## 1. Objective

Deliver a RESTful API where multiple family members feed memories into a shared
"cluster" and ask cross-perspective questions ("who was at the wedding?") that are
answered from **one coherent shared state** rather than contradictory fragments.

This maps directly to the problem statement:

| PROBLEM.md requirement                              | Implementation                                              |
| --------------------------------------------------- | ----------------------------------------------------------- |
| One cluster per family, shared knowledge            | `cluster_id` path segment scopes all memory                 |
| `/v1/cluster/{id}/store`                            | `POST` a memory from one member's perspective               |
| `/v1/cluster/{id}/run`                              | `POST` a question → coherent cross-perspective answer       |
| Multi-source, cross-perspective recall              | Retrieve across **all** members, synthesize one answer      |
| "Breaks without Semvec" (contradictory RAG)         | `Cortex` abstraction; semantic provider is the target       |
| Demo: 3 members × 5 memories, one coherent answer   | Seed script + pytest scenario reproduce the demo            |

---

## 2. Scope

**In scope (hackathon deliverable)**
- REST endpoints: health, store memory, list memories, run a question.
- Cluster-scoped multi-tenancy (one family = one cluster).
- Retrieval + answer synthesis behind a `Cortex` interface.
- Deterministic keyword retrieval with an optional LLM synthesis layer.
- JSON-file persistence (durable across restarts, zero-infra).
- pytest scenarios covering happy paths, validation, empty state, and the demo.
- uv-based headless run & test configuration.
- arc42 documentation with C4 diagrams and ADRs.

**Out of scope (documented as future work)**
- Authentication / per-member authorization.
- A real vector store / embeddings persistence.
- Horizontal scaling, migrations, and multi-node cluster replication.

---

## 3. Target Architecture (summary)

```
Client ──HTTP──▶ FastAPI app ──▶ MemoryStore (persistence)
                      │
                      └────────▶ Cortex (retrieval + synthesis)
                                    ├─ KeywordCortex   (deterministic, offline)
                                    ├─ LLMCortex       (OpenAI synthesis over retrieved set)
                                    └─ SemvecCortex    (target: semantic shared-state recall)
```

- **API layer** (`app/api/`): routers, request/response Pydantic schemas, HTTP semantics.
- **Service layer** (`app/services/`): `Cortex` orchestration — retrieve, then synthesize.
- **Persistence** (`app/store/`): `MemoryStore` interface; JSON file adapter for the demo.
- **Core** (`app/core/`): config (env-driven), logging, error shape.

This layered layout is **implemented** in the `app/` package (§7); root `main.py` is the
thin `main:app` entrypoint. The public contract in §4 is unchanged.

Full detail: [`arc42/architecture.md`](arc42/architecture.md) ·
C4 diagrams: [`c4/`](c4/) · Decisions: [`adr/`](adr/).

---

## 4. API Contract

Base path: `/v1`. Error shape (per repo REST conventions):
`{"error": {"code": "...", "message": "...", "details": {...}}}`.

| Method | Path                               | Purpose                              | Success | Errors            |
| ------ | ---------------------------------- | ------------------------------------ | ------- | ----------------- |
| GET    | `/health`                          | Liveness probe                       | 200     | —                 |
| POST   | `/v1/cluster/{cluster_id}/store`   | Add one member's memory              | 201     | 400, 422          |
| GET    | `/v1/cluster/{cluster_id}/memories`| List a family's memories             | 200     | —                 |
| GET    | `/v1/cluster/{cluster_id}/memories/{memory_id}` | Fetch one memory        | 200     | 404               |
| POST   | `/v1/cluster/{cluster_id}/run`     | Ask a cross-perspective question     | 200     | 422               |

**Schemas**
- `MemoryIn`: `member` (1–100), `text` (3–4000), `date?`, `tags[]` (≤20).
- `Memory`: `MemoryIn` + `id` (UUID), `created_at` (UTC).
- `QuestionIn`: `question` (3–1000), `limit` (1–50, default 12).
- `AnswerOut`: `answer`, `memories[]`, `used_ai` (bool — was LLM synthesis used).

---

## 5. Milestones

1. **M0 — Baseline (done):** single-file app + smoke tests pass.
2. **M1 — Docs & decisions (done):** arc42, C4, ADRs, this plan.
3. **M2 — uv headless config (done):** `uv run` serve/test; pytest config; seed script.
4. **M3 — Layered refactor (done):** `app/` package — `api/`, `services/` (`Cortex`),
   `store/` (`MemoryStore`), `core/`; contract unchanged; `main:app` preserved.
5. **M4 — Test scenarios (done):** full pytest suite in `tests/test_main.py`
   (14 scenarios) — verified green end-to-end via `TestClient`.
6. **M5 — Demo:** seed 3 members × 5 memories; verify one coherent wedding answer.

---

## 6. Test Strategy (pytest)

Run headless: `uv run pytest -q`. Deterministic by default — LLM disabled in tests
so `used_ai is False` and assertions are stable (no network, no API key needed).

Scenario coverage:
- **Store & recall across perspectives** — two members, one question returns both.
- **The demo scenario** — 3 members × 5 memories; "who was at the wedding?" returns
  the wedding memories from multiple members coherently.
- **Empty cluster** — helpful non-error answer, `memories == []`.
- **Cluster isolation** — memories in family-A never leak into family-B's answers.
- **Validation** — empty `member`, too-short `text`, `limit` out of range → 422.
- **Persistence round-trip** — store, reload `MemoryStore` from file, list returns data.
- **Health** — `GET /health` → `{"status": "ok"}`.
- **Contract** — response models match schema; `201` on store, `Location`-friendly.

Fixtures isolate state via `tmp_path` + `monkeypatch` on the store (as in the
existing test). LLM path tested separately by monkeypatching the synth function.

---

## 7. Refactor Steps (M3, contract-preserving)

1. `app/core/config.py` — settings from env (`MEMORY_FILE`, `OPENAI_*`).
2. `app/store/json_store.py` — move `MemoryStore`; define `MemoryStore` protocol.
3. `app/services/cortex.py` — `Cortex` protocol + `KeywordCortex`, `LLMCortex` wrapper.
4. `app/api/schemas.py` — Pydantic models. `app/api/routes.py` — `APIRouter(tags=...)`.
5. `app/main.py` — `create_app()` wiring; keep `main:app` import path working.
6. Re-run suite; public routes/behaviour unchanged.

> **Status: done.** The `app/` package now matches the C4 component view; the store
> and synthesizers are injectable via `create_app(...)`, which keeps tests offline and
> deterministic. `main.py` remains the `main:app` entrypoint (loads `.env`, calls
> `create_app()`).

---

## 8. uv / Headless Configuration (M2)

See [`../pyproject.toml`](../pyproject.toml) and [`RUNNING.md`](RUNNING.md).

- **Install:** `uv sync` (creates `.venv`, installs deps + dev group).
- **Serve headless:** `uv run uvicorn main:app --host 0.0.0.0 --port 8000`
  (no `--reload`, no TTY needed — suitable for CI/containers).
- **Test headless:** `uv run pytest -q` (config in `[tool.pytest.ini_options]`).
- **Seed demo:** `uv run python scripts/seed_demo.py`.
- Determinism in headless CI: tests set `OPENAI_API_KEY` empty so no external calls.

---

## 9. Risks & Mitigations

| Risk                                             | Mitigation                                             |
| ------------------------------------------------ | ------------------------------------------------------ |
| RAG returns contradictory fragments              | Synthesize over the **whole** retrieved set; prompt to reconcile conflicting perspectives; `Cortex` abstraction lets us swap in semantic recall. |
| LLM unavailable / no key                         | Deterministic keyword fallback always returns an answer; `used_ai` flags which path ran. |
| Secret leakage (`.env` holds a live key)         | `.env*` gitignored; **rotate the committed key**; read config only from env. |
| JSON store concurrency                           | `threading.Lock` + atomic temp-file replace on write.  |
| Non-determinism in tests                         | LLM disabled in tests; assert on the deterministic path. |

---

## 10. Definition of Done

- All §6 scenarios pass via `uv run pytest -q`.
- `uv run uvicorn main:app ...` serves the contract in §4; `GET /health` is 200.
- Demo reproduces a coherent cross-perspective wedding answer.
- arc42 doc, C4 diagrams, and ADRs are present and cross-linked.
