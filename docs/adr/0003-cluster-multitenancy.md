# ADR-0003: Cluster-per-family multi-tenancy

- **Status:** Accepted
- **Date:** 2026-07-15
- **Deciders:** Maintainers

## Context and Problem Statement

Multiple families use the service; each family's memories must be shared among its own
members but isolated from other families. PROBLEM.md specifies a REST cluster addressed
as `/v1/cluster/{id}/store` and `/run`.

## Decision Drivers

- Isolation between families; sharing within a family.
- URL shape mandated by the problem statement.
- Simple, stateless routing key.

## Considered Options

1. **`cluster_id` path segment** scoping every operation (one family = one cluster).
2. Per-member instances with no shared state (building block B4, single-person mode).
3. A global store with a `family` filter field.

## Decision

Use a **`cluster_id` path parameter** as the tenancy key. All store/list/run operations
are scoped to their cluster. This matches the required URLs and yields natural isolation
with in-cluster sharing. (Single-person B4 mode is just a cluster with one member.)

## Consequences

- **Positive:** Matches the contract; trivial isolation; easy demo (`family-1`).
- **Negative / trade-offs:** No auth means any caller can address any cluster —
  acceptable for the hackathon, flagged as future work.
- **Follow-ups:** Add authorization mapping members→clusters if productionized.
