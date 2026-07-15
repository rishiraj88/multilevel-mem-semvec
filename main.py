"""Deployment entrypoint. Serve headless with:

    uv run uvicorn main:app --host 0.0.0.0 --port 8000

Loads a local .env (if present) then builds the app from environment settings.
Application code lives in the `app` package; see docs/arc42/architecture.md.
"""

from __future__ import annotations

from dotenv import load_dotenv

from app.main import create_app

load_dotenv()
app = create_app()
