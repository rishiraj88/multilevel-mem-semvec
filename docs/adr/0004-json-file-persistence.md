# ADR-0004: JSON-file persistence for the hackathon

- **Status:** Accepted
- **Date:** 2026-07-15
- **Deciders:** Maintainers

## Context and Problem Statement

Memories must survive process restarts for the demo, but standing up a database is out
of scope and would add infrastructure the hackathon does not need.

## Decision Drivers

- Zero external infrastructure; runs anywhere `uv` runs.
- Durable across restarts.
- Safe against corruption on write; safe under concurrent requests.
- Easy to reset between tests via a temp path.

## Considered Options

1. **JSON file** behind a `MemoryStore` with a lock and atomic temp-file replace.
2. SQLite via SQLAlchemy.
3. In-memory only (lost on restart).

## Decision

Use a **JSON file** store (`MEMORY_FILE`, default `memory_store.json`) exposed behind a
`MemoryStore` interface. Writes take a `threading.Lock` and use write-temp-then-replace
for atomicity. The interface keeps the door open for a vector/SQL backend later.

## Consequences

- **Positive:** No infra; trivial reset in tests (`tmp_path`); durable; atomic writes.
- **Negative / trade-offs:** Single-node only; whole-file rewrite per save; not for
  production scale or concurrent multi-process writers.
- **Follow-ups:** Replace with a vector store when adopting `SemvecCortex`
  ([ADR-0002](0002-cortex-provider-abstraction.md)); keep the `MemoryStore` protocol.
