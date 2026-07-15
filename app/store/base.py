"""Persistence contract for cluster-scoped memories."""

from __future__ import annotations

from typing import Protocol

from app.api.schemas import Memory, MemoryIn


class MemoryStore(Protocol):
    """A per-cluster memory store. Implementations must be safe for concurrent requests."""

    def add(self, cluster_id: str, memory: MemoryIn) -> Memory:
        """Persist a memory under `cluster_id` and return it with id + timestamp."""
        ...

    def list(self, cluster_id: str) -> list[Memory]:
        """Return every memory for `cluster_id` (empty list if none)."""
        ...

    def get(self, cluster_id: str, memory_id: str) -> Memory | None:
        """Return a single memory by id, or None if not found in the cluster."""
        ...
