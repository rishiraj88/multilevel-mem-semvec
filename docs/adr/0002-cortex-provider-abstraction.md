# ADR-0002: Pluggable Cortex retrieval/synthesis provider

- **Status:** Accepted
- **Date:** 2026-07-15
- **Deciders:** Maintainers

## Context and Problem Statement

PROBLEM.md frames the value as coherent **cross-perspective** recall and states the
demo "breaks without Semvec" because naïve RAG pulls contradictory fragments. We need
the answer engine ("Cortex") to be swappable: a deterministic offline engine for the
hackathon demo/tests, an LLM synthesizer when available, and a semantic Semvec engine
as the eventual target — without changing the public API.

## Decision Drivers

- Coherence is the core quality goal.
- Must run and test deterministically offline (no key, no network).
- Must not lock the HTTP contract to any one retrieval technology.
- Clear seam for a future Semvec/vector backend.

## Considered Options

1. **Introduce a `Cortex` abstraction** (`retrieve` + `synthesize`) with interchangeable
   providers: `KeywordCortex`, `LLMCortex`, and a future `SemvecCortex`.
2. Hardcode OpenAI RAG directly in the route handler.
3. Hardcode keyword search only.

## Decision

Adopt a **`Cortex` provider abstraction**. Retrieval ranks memories across **all**
members of a cluster; synthesis produces one coherent answer that reconciles
perspectives. Providers are selected by configuration; the target is `SemvecCortex`.

## Consequences

- **Positive:** Swap engines without touching routes/schemas; tests pin the
  deterministic provider; honours the "shared coherent state" goal.
- **Negative / trade-offs:** One extra layer of indirection vs. inlining.
- **Follow-ups:** Extract `app/services/cortex.py` in the M3 refactor; implement the
  `SemvecCortex` adapter when the Semvec endpoint is available. See
  [ADR-0005](0005-answer-synthesis-strategy.md).
