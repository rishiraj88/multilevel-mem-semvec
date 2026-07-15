# ADR-0005: Retrieval + optional LLM synthesis with deterministic fallback

- **Status:** Accepted
- **Date:** 2026-07-15
- **Deciders:** Maintainers

## Context and Problem Statement

A question must be answered coherently from many members' memories. We want LLM-quality
synthesis when available, but the demo and tests must be deterministic and must work
offline without an API key.

## Decision Drivers

- Coherence across perspectives (reconcile, don't concatenate contradictions).
- Deterministic, offline-capable tests and demo.
- Transparent about which path produced the answer.

## Considered Options

1. **Retrieve first, then synthesize with the LLM if configured; otherwise a
   deterministic join.** Expose `used_ai` in the response.
2. LLM-only (fails without a key; non-deterministic tests).
3. Deterministic-only (no LLM-quality synthesis).

## Decision

Always **retrieve across all members**, then **synthesize**: if an LLM is configured,
prompt it to answer *only* from supplied memories and to reconcile conflicting
perspectives; otherwise return a deterministic join of the top memories. The response
carries `used_ai` so callers/tests know which path ran; tests assert the deterministic
path (`used_ai is False`).

## Consequences

- **Positive:** Works offline; reproducible tests; better answers when a key is present;
  honest signalling via `used_ai`.
- **Negative / trade-offs:** Two answer paths to maintain; keyword retrieval is shallow.
- **Follow-ups:** Replace keyword retrieval with semantic recall via `SemvecCortex`
  ([ADR-0002](0002-cortex-provider-abstraction.md)).
