"""JSON-file-backed memory store — zero-infra persistence for the hackathon."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from typing import Any
from uuid import uuid4

from app.api.schemas import Memory, MemoryIn


class JsonMemoryStore:
    """Small JSON-backed store keyed by cluster id.

    Writes take a lock and use write-temp-then-replace for atomicity. Suitable for
    a single-process demo; not for multi-process or high-scale use (see ADR-0004).
    """

    def __init__(self, path: Path | str) -> None:
        self.path = Path(path)
        self._lock = Lock()
        self._memories: dict[str, list[dict[str, Any]]] = {}
        self._load()

    def _load(self) -> None:
        if not self.path.exists():
            return
        try:
            self._memories = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            self._memories = {}

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(".tmp")
        temporary.write_text(json.dumps(self._memories, indent=2), encoding="utf-8")
        temporary.replace(self.path)

    def add(self, cluster_id: str, memory: MemoryIn) -> Memory:
        item = Memory(id=str(uuid4()), created_at=datetime.now(timezone.utc), **memory.model_dump())
        with self._lock:
            self._memories.setdefault(cluster_id, []).append(item.model_dump(mode="json"))
            self._save()
        return item

    def list(self, cluster_id: str) -> list[Memory]:
        return [Memory.model_validate(item) for item in self._memories.get(cluster_id, [])]

    def get(self, cluster_id: str, memory_id: str) -> Memory | None:
        for item in self._memories.get(cluster_id, []):
            if item.get("id") == memory_id:
                return Memory.model_validate(item)
        return None
