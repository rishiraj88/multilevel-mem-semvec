"""Application configuration, sourced from environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    """Immutable runtime settings.

    `openai_api_key` is None when no usable key is configured, which switches the
    Cortex to its deterministic keyword synthesis path.
    """

    memory_file: Path
    openai_api_key: str | None
    openai_model: str

    @classmethod
    def from_env(cls) -> "Settings":
        key = os.getenv("OPENAI_API_KEY") or ""
        # Treat an unset or placeholder key as "no LLM configured".
        if not key or key.startswith("your-"):
            key = ""
        return cls(
            memory_file=Path(os.getenv("MEMORY_FILE", "memory_store.json")),
            openai_api_key=key or None,
            openai_model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        )
