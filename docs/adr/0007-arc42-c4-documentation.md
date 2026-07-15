# ADR-0007: Document with arc42 + C4 + ADRs

- **Status:** Accepted
- **Date:** 2026-07-15
- **Deciders:** Maintainers

## Context and Problem Statement

Reviewers need to understand the architecture quickly and see why key choices were made.
We want a lightweight, standard, text-based documentation approach that lives in the repo
and renders on GitHub.

## Decision Drivers

- Standard, recognizable structure for reviewers.
- Diagrams-as-code, versioned with the source and rendered on GitHub.
- Decisions captured with their rationale and trade-offs.

## Considered Options

1. **arc42** for the architecture narrative + **C4** (Mermaid) diagrams + **ADRs** (MADR).
2. A single freeform README.
3. External wiki / diagram tool (Confluence, draw.io).

## Decision

Structure docs with **arc42** ([`../arc42/architecture.md`](../arc42/architecture.md)),
embed **C4** Levels 1–3 as Mermaid in [`../c4/`](../c4/) (GitHub-renderable), and record
decisions as **ADRs** in this folder. arc42 §5 links the C4 views; §9 links the ADRs.

## Consequences

- **Positive:** Familiar to reviewers; versioned with code; renders on GitHub; no
  external tooling; decisions are traceable.
- **Negative / trade-offs:** Docs must be kept in step with code as it evolves.
- **Follow-ups:** Update the C4 component view once the M3 layered refactor lands.
