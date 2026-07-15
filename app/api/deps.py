"""FastAPI dependencies that expose per-app singletons to route handlers."""

from __future__ import annotations

from fastapi import Request

from app.services.cortex import Cortex
from app.store.base import MemoryStore


def get_store(request: Request) -> MemoryStore:
    return request.app.state.store


def get_cortex(request: Request) -> Cortex:
    return request.app.state.cortex
