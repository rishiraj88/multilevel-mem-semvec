"""HTTP routes for the Family Chronicle API."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response, status

from app.api.deps import get_cortex, get_store
from app.api.schemas import AnswerOut, Memory, MemoryIn, QuestionIn
from app.services.cortex import Cortex
from app.store.base import MemoryStore

system_router = APIRouter(tags=["system"])
cluster_router = APIRouter(prefix="/v1/cluster", tags=["cluster"])


@system_router.get("/health")
def health() -> dict[str, str]:
    """Liveness probe."""
    return {"status": "ok"}


@cluster_router.post("/{cluster_id}/store", response_model=Memory, status_code=status.HTTP_201_CREATED)
def store_memory(
    cluster_id: str,
    memory: MemoryIn,
    response: Response,
    store: MemoryStore = Depends(get_store),
) -> Memory:
    """Add one family member's perspective to the shared memory."""
    if not cluster_id.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="cluster_id must not be empty")
    created = store.add(cluster_id, memory)
    response.headers["Location"] = f"/v1/cluster/{cluster_id}/memories/{created.id}"
    return created


@cluster_router.get("/{cluster_id}/memories", response_model=list[Memory])
def list_memories(cluster_id: str, store: MemoryStore = Depends(get_store)) -> list[Memory]:
    """List every memory recorded for a family."""
    return store.list(cluster_id)


@cluster_router.get("/{cluster_id}/memories/{memory_id}", response_model=Memory)
def get_memory(cluster_id: str, memory_id: str, store: MemoryStore = Depends(get_store)) -> Memory:
    """Fetch a single memory by id."""
    memory = store.get(cluster_id, memory_id)
    if memory is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="memory not found")
    return memory


@cluster_router.post("/{cluster_id}/run", response_model=AnswerOut)
def run_agent(cluster_id: str, request: QuestionIn, cortex: Cortex = Depends(get_cortex)) -> AnswerOut:
    """Retrieve shared memories and synthesize a cross-perspective answer."""
    return cortex.run(cluster_id, request.question, request.limit)
