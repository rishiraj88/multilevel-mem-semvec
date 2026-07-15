# Architecture — The Family Chronicle (arc42)

Documentation follows the [arc42](https://arc42.org) template. C4 diagrams live in
[`../c4/`](../c4/); architecture decisions in [`../adr/`](../adr/).

---

## 1. Introduction and Goals

The Family Chronicle is a REST API that weaves a **shared, searchable family history**
from memories contributed by multiple family members. It answers cross-perspective
questions coherently instead of surfacing contradictory fragments.

**Quality goals**

| # | Quality        | Motivation                                                        |
| - | -------------- | ----------------------------------------------------------------- |
| 1 | Coherence      | One shared answer across perspectives — the core value prop.      |
| 2 | Simplicity     | Hackathon scope; zero-infra, runnable with one `uv` command.      |
| 3 | Determinism    | Reproducible demo & tests; works offline without an LLM key.      |
| 4 | Extensibility  | Swap the retrieval engine (keyword → semantic Semvec Cortex).     |

**Stakeholders:** family members (contributors & askers), hackathon reviewers, maintainers.

## 2. Constraints

- **Language/stack:** Python ≥ 3.11, FastAPI, Pydantic, Uvicorn.
- **Tooling:** `uv` for dependency management and headless run/test (see AGENTS.md).
- **Environment:** must run headless (CI/containers) and on the author's Windows host.
- **Persistence:** no external database for the demo — file-backed store only.
- **Secrets:** configuration and API keys come from environment variables only.

## 3. Context and Scope

See C4 Level 1 — [`../c4/c1-system-context.md`](../c4/c1-system-context.md).

- **System:** Family Chronicle API.
- **External actors:** family members via an HTTP client.
- **External systems:** OpenAI (optional synthesis); Semvec Cortex (target semantic engine).
- **In scope:** store/list memories, answer questions per family cluster.
- **Out of scope:** auth, real vector DB, multi-node replication.

## 4. Solution Strategy

| Goal        | Approach                                                                 |
| ----------- | ------------------------------------------------------------------------ |
| Coherence   | Retrieve across all members, synthesize **one** answer reconciling views. |
| Multi-tenancy | `cluster_id` scopes every operation — one family per cluster.          |
| Extensibility | `Cortex` abstraction with pluggable providers (see [ADR-0002](../adr/0002-cortex-provider-abstraction.md)). |
| Determinism | Keyword retrieval + deterministic fallback answer; LLM optional.         |
| Ops         | `uv` headless serve/test; JSON store; env-driven config.                 |

## 5. Building Block View

- **Level 1 (Context):** [`../c4/c1-system-context.md`](../c4/c1-system-context.md)
- **Level 2 (Containers):** [`../c4/c2-container.md`](../c4/c2-container.md)
- **Level 3 (Components):** [`../c4/c3-component.md`](../c4/c3-component.md)

Top-level building blocks: **API layer** (routers + schemas) → **Cortex service**
(retrieve + synthesize) → **MemoryStore** (persistence). Config/logging in **Core**.

## 6. Runtime View

**Store a memory** (`POST /v1/cluster/{id}/store`)
1. Router validates `MemoryIn` (Pydantic → 422 on failure).
2. `MemoryStore.add` assigns `id` + `created_at`, appends under `cluster_id`, saves atomically.
3. Returns `Memory` with `201`.

**Answer a question** (`POST /v1/cluster/{id}/run`)
1. Router validates `QuestionIn`.
2. `Cortex.retrieve(cluster_id, question, limit)` ranks memories across all members.
3. If empty → helpful message, `used_ai=false`.
4. Else `Cortex.synthesize` — LLM if configured, else deterministic join.
5. Returns `AnswerOut` (`answer`, `memories`, `used_ai`).

## 7. Deployment View

Single process. Headless: `uv run uvicorn main:app --host 0.0.0.0 --port 8000`.
State persists to a JSON file (`MEMORY_FILE`). Container/CI friendly — no TTY, no DB.
Per PROBLEM.md building block B4: one instance per person **or** a REST cluster where
each family shares a `cluster_id`.

## 8. Cross-cutting Concepts

- **Configuration:** env vars (`MEMORY_FILE`, `OPENAI_API_KEY`, `OPENAI_MODEL`), `.env` optional.
- **Error handling:** consistent JSON error envelope; correct HTTP status codes.
- **Validation:** Pydantic field constraints at the edge.
- **Concurrency:** lock + atomic temp-file replace in the JSON store.
- **Observability:** `/health` liveness; structured logs (planned).
- **Persistence abstraction:** `MemoryStore` protocol; JSON adapter now, vector store later.

## 9. Architecture Decisions

Records in [`../adr/`](../adr/):

| ADR | Decision |
| --- | -------- |
| [0001](../adr/0001-fastapi-framework.md) | FastAPI + Pydantic + Uvicorn as the stack |
| [0002](../adr/0002-cortex-provider-abstraction.md) | Pluggable `Cortex` retrieval/synthesis provider |
| [0003](../adr/0003-cluster-multitenancy.md) | Cluster-per-family multi-tenancy model |
| [0004](../adr/0004-json-file-persistence.md) | JSON-file persistence for the hackathon |
| [0005](../adr/0005-answer-synthesis-strategy.md) | Retrieval + optional LLM synthesis with fallback |
| [0006](../adr/0006-uv-headless-tooling.md) | `uv` for dependency mgmt and headless run/test |
| [0007](../adr/0007-arc42-c4-documentation.md) | Document with arc42 + C4 + ADRs |

## 10. Quality Requirements

- Reproducible demo: 3 members × 5 memories → coherent answer, every run.
- Test suite green offline via `uv run pytest -q`.
- Startup to first request < 2 s on a laptop.
- Cluster isolation: no cross-family leakage.

## 11. Risks and Technical Debt

- Keyword retrieval is shallow vs. true semantic recall → Semvec Cortex is the target.
- JSON store is single-node, not for production scale.
- No auth — any client can read/write any cluster.
- A live API key was committed to `.env` — **rotate it**; keep secrets out of the tree.

## 12. Glossary

| Term    | Meaning                                                                 |
| ------- | ----------------------------------------------------------------------- |
| Cluster | A family's shared memory scope, keyed by `cluster_id`.                  |
| Cortex  | The retrieval + synthesis engine producing one coherent shared state.   |
| Memory  | One member's recorded perspective (member, text, date, tags).           |
| Semvec  | Target semantic-vector engine for cross-perspective coherent recall.    |
| Member  | A family member who contributes memories and asks questions.            |
