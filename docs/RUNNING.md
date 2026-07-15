# Running & Testing (headless with uv)

All commands run through **uv** — no interactive shell or TTY required, so they work in
CI and containers.

## Prerequisites

- [uv](https://docs.astral.sh/uv/) installed.
- Python ≥ 3.11 (uv can install it: `uv python install 3.11`).

## 1. Install

```bash
uv sync            # creates .venv and installs runtime + dev dependencies
```

## 2. Serve the API (headless)

```bash
uv run uvicorn main:app --host 0.0.0.0 --port 8000
```

- No `--reload` → suitable for CI/containers.
- **Web UI** at `http://localhost:8000/` — a single-page React app (`static/index.html`)
  served same-origin. It loads React from a CDN, so the browser needs internet on first
  load. Add memories, ask questions, and one-click "Seed demo (3×5)".
- OpenAPI docs at `http://localhost:8000/docs`; liveness at `GET /health`.
- Optional LLM synthesis: set `OPENAI_API_KEY` (and optionally `OPENAI_MODEL`).
  Without it, answers use the deterministic keyword path.

## 3. Run the tests (headless)

```bash
uv run pytest -q
```

- Configuration lives in `pyproject.toml` → `[tool.pytest.ini_options]`.
- `tests/conftest.py` clears `OPENAI_API_KEY`, so the suite is deterministic and
  offline — no secret or network needed.

## 4. Run the demo

In one shell, serve the API (step 2). In another:

```bash
uv run python scripts/seed_demo.py
```

Seeds 3 members × 5 memories into `family-1` and asks *"Who was at the wedding?"*,
printing a coherent cross-perspective answer. Override `BASE_URL` / `CLUSTER_ID` via env.

## Environment variables

| Variable         | Default              | Purpose                                    |
| ---------------- | -------------------- | ------------------------------------------ |
| `MEMORY_FILE`    | `memory_store.json`  | Path to the JSON memory store              |
| `OPENAI_API_KEY` | *(unset)*            | Enables LLM synthesis when present          |
| `OPENAI_MODEL`   | `gpt-4o-mini`        | Model used for synthesis                    |
| `BASE_URL`       | `http://localhost:8000` | Target for `scripts/seed_demo.py`       |
| `CLUSTER_ID`     | `family-1`           | Cluster used by the demo script            |

> **Security:** never commit real keys. `.env*` is gitignored; if a key was ever
> committed, rotate it.
