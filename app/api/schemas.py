"""Pydantic request/response models — validation at the API boundary."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class MemoryIn(BaseModel):
    """One family member's memory as submitted by a client."""

    member: str = Field(min_length=1, max_length=100, description="Name of the family member")
    text: str = Field(min_length=3, max_length=4_000, description="The memory in the member's own words")
    date: str | None = Field(default=None, description="Free-form date the memory refers to")
    tags: list[str] = Field(default_factory=list, max_length=20, description="Optional labels")


class Memory(MemoryIn):
    """A stored memory with server-assigned identity and timestamp."""

    id: str
    created_at: datetime


class QuestionIn(BaseModel):
    """A cross-perspective question against a family's shared memory."""

    question: str = Field(min_length=3, max_length=1_000)
    limit: int = Field(default=12, ge=1, le=50, description="Maximum memories to retrieve")


class AnswerOut(BaseModel):
    """A synthesized answer plus the memories it was drawn from."""

    answer: str
    memories: list[Memory]
    used_ai: bool = Field(description="True when an LLM produced the answer, False for the deterministic path")
