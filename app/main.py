"""Application factory wiring config, persistence, the Cortex, and routes."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.routes import cluster_router, system_router
from app.core.config import Settings
from app.core.errors import register_error_handlers
from app.services.cortex import Cortex, KeywordSynthesizer, LLMSynthesizer, Synthesizer
from app.store.base import MemoryStore
from app.store.json_store import JsonMemoryStore

# The single-page web UI (served same-origin so there are no CORS concerns).
_STATIC_DIR = Path(__file__).resolve().parent.parent / "static"


def create_app(
    *,
    settings: Settings | None = None,
    store: MemoryStore | None = None,
    synthesizers: list[Synthesizer] | None = None,
) -> FastAPI:
    """Build a configured FastAPI app.

    Injecting `store`/`synthesizers` keeps tests deterministic and offline. When
    omitted, defaults come from the environment (`Settings.from_env`).
    """
    settings = settings or Settings.from_env()
    store = store or JsonMemoryStore(settings.memory_file)
    if synthesizers is None:
        synthesizers = [LLMSynthesizer(settings), KeywordSynthesizer()]

    app = FastAPI(title="Family Chronicle", version="1.0.0")
    app.state.settings = settings
    app.state.store = store
    app.state.cortex = Cortex(store, synthesizers)

    register_error_handlers(app)
    app.include_router(system_router)
    app.include_router(cluster_router)

    # Mounted last so it only serves paths the API routers didn't claim.
    if _STATIC_DIR.is_dir():
        app.mount("/", StaticFiles(directory=_STATIC_DIR, html=True), name="ui")
    return app
