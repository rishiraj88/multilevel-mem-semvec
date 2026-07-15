# ADR-0006: uv for dependency management and headless run/test

- **Status:** Accepted
- **Date:** 2026-07-15
- **Deciders:** Maintainers

## Context and Problem Statement

The project must be reproducibly installed, tested, and served **headless** (CI,
containers, non-interactive shells). AGENTS.md mandates uv: *"Use UV for python
packages … (uv run python -m pytest -q)"*.

## Decision Drivers

- Reproducible, fast environment creation and locking.
- One command to serve and one to test, no TTY required.
- Consistent behaviour across the author's Windows host and Linux CI.

## Considered Options

1. **uv** (`uv sync`, `uv run …`) with `pyproject.toml` + `[dependency-groups]`.
2. pip + venv + requirements.txt.
3. Poetry.

## Decision

Use **uv**. Dependencies and the `dev` group live in `pyproject.toml`; `uv sync`
provisions `.venv`; everything runs through `uv run`:

- Serve headless: `uv run uvicorn main:app --host 0.0.0.0 --port 8000`
- Test headless: `uv run pytest -q` (config in `[tool.pytest.ini_options]`)
- Seed demo: `uv run python scripts/seed_demo.py`

Tests run with the LLM disabled so headless CI needs no secret and stays deterministic.

## Consequences

- **Positive:** Reproducible; fast; single toolchain for install/run/test; lockable via
  `uv.lock`; no interactive prompts.
- **Negative / trade-offs:** Contributors must install uv; `uv.lock` should be committed
  for full reproducibility.
- **Follow-ups:** Commit `uv.lock`; wire the same commands into CI. See
  [RUNNING.md](../RUNNING.md).
