"""The Cortex: retrieve across all members, then synthesize one coherent answer.

Synthesis is provided by pluggable `Synthesizer` implementations tried in order —
an LLM first (when configured), the deterministic keyword synthesizer last, which
always produces an answer. This is the seam where a future `SemvecSynthesizer`
(semantic cross-perspective recall) plugs in (see ADR-0002, ADR-0005).
"""

from __future__ import annotations

import re
from typing import Protocol

from openai import OpenAI

from app.api.schemas import AnswerOut, Memory
from app.core.config import Settings
from app.store.base import MemoryStore

STOP_WORDS = {
    "a", "an", "and", "are", "at", "be", "by", "for", "from", "has", "he", "her", "in",
    "is", "it", "of", "on", "or", "she", "the", "to", "was", "we", "were", "who", "with",
    "our", "their", "they", "i",
}


def _terms(value: str) -> set[str]:
    return {word for word in re.findall(r"[a-z0-9]+", value.lower()) if word not in STOP_WORDS}


def _haystack(memory: Memory) -> set[str]:
    return _terms(f"{memory.member} {memory.text} {' '.join(memory.tags)}")


def rank_memories(memories: list[Memory], question: str, limit: int) -> list[Memory]:
    """Rank memories by term overlap with the question across all members.

    Falls back to all memories (capped at `limit`) when nothing matches, so a
    question always has context to answer from when the cluster is non-empty.
    """
    terms = _terms(question)
    ranked = sorted(memories, key=lambda memory: len(terms & _haystack(memory)), reverse=True)
    matching = [memory for memory in ranked if terms & _haystack(memory)]
    return (matching or memories)[:limit]


class Synthesizer(Protocol):
    """Turns a question + retrieved memories into an answer, or None to defer."""

    used_ai: bool

    def synthesize(self, question: str, memories: list[Memory]) -> str | None: ...


class KeywordSynthesizer:
    """Deterministic, offline synthesizer. Always returns an answer."""

    used_ai = False

    def synthesize(self, question: str, memories: list[Memory]) -> str:
        joined = "; ".join(f"{memory.member} remembers: {memory.text}" for memory in memories[:5])
        return f"Based on the family memories: {joined}"


class LLMSynthesizer:
    """OpenAI-backed synthesizer. Returns None when unconfigured or on failure."""

    used_ai = True

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def synthesize(self, question: str, memories: list[Memory]) -> str | None:
        if not self._settings.openai_api_key:
            return None
        context = "\n".join(
            f"- {memory.member} ({memory.date or 'date unknown'}): {memory.text}" for memory in memories
        )
        try:
            client = OpenAI(api_key=self._settings.openai_api_key)
            response = client.responses.create(
                model=self._settings.openai_model,
                instructions=(
                    "You are the Family Chronicle agent. Answer only from supplied memories. "
                    "Combine perspectives, mention uncertainty when memories conflict, and do not invent facts."
                ),
                input=f"Question: {question}\n\nMemories:\n{context}",
            )
            return response.output_text.strip()
        except Exception:
            return None


class Cortex:
    """Orchestrates retrieval and synthesis over a cluster's shared memory."""

    def __init__(self, store: MemoryStore, synthesizers: list[Synthesizer]) -> None:
        self._store = store
        self._synthesizers = list(synthesizers)

    def run(self, cluster_id: str, question: str, limit: int) -> AnswerOut:
        memories = rank_memories(self._store.list(cluster_id), question, limit)
        if not memories:
            return AnswerOut(answer="I don't have any memories for this family yet.", memories=[], used_ai=False)
        for synthesizer in self._synthesizers:
            answer = synthesizer.synthesize(question, memories)
            if answer:
                return AnswerOut(answer=answer, memories=memories, used_ai=synthesizer.used_ai)
        # Reached only if every synthesizer defers; keep the contract intact.
        return AnswerOut(answer="No answer could be synthesized.", memories=memories, used_ai=False)
