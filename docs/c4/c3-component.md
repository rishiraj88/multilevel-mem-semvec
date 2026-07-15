# C4 Level 3 — Component

Components inside the **FastAPI Application** container. This layered layout is
implemented in the `app/` package (M3 in the [implementation plan](../IMPLEMENTATION_PLAN.md));
root `main.py` is the thin `main:app` entrypoint that builds the app via `create_app()`.

```mermaid
C4Component
    title Component View — FastAPI Application

    Container_Boundary(api, "FastAPI Application") {
        Component(routes, "API Router", "FastAPI APIRouter", "HTTP semantics, status codes, error envelope")
        Component(schemas, "Schemas", "Pydantic models", "MemoryIn, Memory, QuestionIn, AnswerOut — validation")
        Component(cortex, "Cortex Service", "Python", "Orchestrates retrieve → synthesize")
        Component(keyword, "KeywordCortex", "Python", "Deterministic term-overlap retrieval + join")
        Component(llm, "LLMCortex", "OpenAI client", "Synthesizes one coherent answer over the retrieved set")
        Component(storec, "MemoryStore", "Python protocol + JSON adapter", "Per-cluster CRUD, atomic persistence")
        Component(config, "Core / Config", "env-driven", "Settings, logging, error shape")
    }

    ContainerDb(file, "JSON file", "disk", "memory_store.json")
    System_Ext(openai, "OpenAI API", "LLM")

    Rel(routes, schemas, "Validates with")
    Rel(routes, cortex, "run(): asks a question")
    Rel(routes, storec, "store()/list(): CRUD memories")
    Rel(cortex, keyword, "Retrieves & ranks")
    Rel(cortex, llm, "Synthesizes (when configured)")
    Rel(cortex, storec, "Reads memories")
    Rel(llm, openai, "Calls", "HTTPS")
    Rel(storec, file, "Reads/writes", "lock + temp-file replace")
    Rel(routes, config, "Reads settings")
```

**Responsibilities**
- **API Router** — maps HTTP to services; owns status codes (201/200/422) and the
  `{"error": {...}}` envelope.
- **Schemas** — Pydantic validation at the boundary.
- **Cortex Service** — the coherence engine: retrieve across **all** members, then
  synthesize one answer ([ADR-0002](../adr/0002-cortex-provider-abstraction.md),
  [ADR-0005](../adr/0005-answer-synthesis-strategy.md)).
- **KeywordCortex / LLMCortex** — pluggable providers; `SemvecCortex` is the target.
- **MemoryStore** — persistence protocol; JSON adapter for the demo.
- **Core/Config** — env-driven configuration and logging.
