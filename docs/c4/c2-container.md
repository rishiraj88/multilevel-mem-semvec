# C4 Level 2 — Container

The runtime containers inside the Family Chronicle system.

```mermaid
C4Container
    title Container View — The Family Chronicle

    Person(member, "Family Member", "Uses an HTTP client")

    System_Boundary(chronicle, "Family Chronicle") {
        Container(api, "FastAPI Application", "Python 3.11, FastAPI, Uvicorn", "Exposes /v1/cluster/{id}/store, /memories, /run and /health")
        ContainerDb(store, "Memory Store", "JSON file on disk", "Persists per-cluster memories atomically")
    }

    System_Ext(openai, "OpenAI API", "Optional answer synthesis")
    System_Ext(semvec, "Semvec Cortex", "Target semantic recall engine")

    Rel(member, api, "Stores memories / asks questions", "HTTPS, JSON")
    Rel(api, store, "Reads & writes memories", "file I/O, lock + atomic replace")
    Rel(api, openai, "Synthesizes answer (when key present)", "HTTPS")
    Rel(api, semvec, "Coherent retrieval (target)", "REST")
```

**Containers**
- **FastAPI Application** — the single deployable process; served headless via
  `uv run uvicorn main:app --host 0.0.0.0 --port 8000`.
- **Memory Store** — JSON file (`MEMORY_FILE`, default `memory_store.json`); chosen for
  zero-infra ([ADR-0004](../adr/0004-json-file-persistence.md)). Swappable for a vector store.
