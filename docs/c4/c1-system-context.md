# C4 Level 1 — System Context

How the Family Chronicle fits among its users and neighbouring systems.

```mermaid
C4Context
    title System Context — The Family Chronicle

    Person(member, "Family Member", "Contributes memories and asks cross-perspective questions")

    System(chronicle, "Family Chronicle API", "Stores per-member memories and answers questions from one coherent shared family state")

    System_Ext(openai, "OpenAI API", "Optional LLM synthesis over retrieved memories")
    System_Ext(semvec, "Semvec Cortex", "Target semantic-vector engine for coherent cross-perspective recall")

    Rel(member, chronicle, "Stores memories, asks questions", "HTTPS / JSON")
    Rel(chronicle, openai, "Synthesizes an answer (when configured)", "HTTPS")
    Rel(chronicle, semvec, "Retrieves coherent shared state (target)", "HTTPS / REST")
```

**Notes**
- One family = one **cluster** (`cluster_id`). All operations are cluster-scoped.
- OpenAI is optional: without a key, a deterministic keyword answer is returned.
- Semvec Cortex is the intended semantic backend; the abstraction is in place today
  (see [ADR-0002](../adr/0002-cortex-provider-abstraction.md)).
