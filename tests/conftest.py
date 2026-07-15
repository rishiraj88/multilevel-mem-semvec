"""Shared pytest configuration.

Keeps headless test runs deterministic and offline: the LLM synthesis path is
disabled by clearing OPENAI_API_KEY, so tests never reach the network and need
no secret. `main.py` calls load_dotenv() at import, which can pull a real key
from a local .env — this fixture neutralizes that for the whole session.
"""

from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def _disable_llm(monkeypatch: pytest.MonkeyPatch) -> None:
    """Force the deterministic answer path (used_ai == False) in every test."""
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
