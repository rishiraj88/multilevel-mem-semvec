# ADR-0001: FastAPI + Pydantic + Uvicorn as the stack

- **Status:** Accepted
- **Date:** 2026-07-15
- **Deciders:** Maintainers

## Context and Problem Statement

We need a RESTful API for the Family Chronicle with strong request validation,
automatic OpenAPI docs, and a low-boilerplate path from schema to endpoint, runnable
headless for demos and CI.

## Decision Drivers

- Fast to build within a hackathon window.
- First-class validation and typed request/response models.
- Auto-generated OpenAPI/Swagger for reviewers.
- Headless ASGI serving for containers/CI.
- Matches the repo's stated FastAPI conventions (`.github/copilot-instructions.md`).

## Considered Options

1. **FastAPI + Pydantic + Uvicorn.**
2. Flask + marshmallow.
3. Django REST Framework.

## Decision

Use **FastAPI** with **Pydantic** models and **Uvicorn** as the ASGI server. It gives
typed validation, `response_model` enforcement, correct HTTP semantics, and OpenAPI
docs out of the box with minimal code — the best fit for the scope and timeline.

## Consequences

- **Positive:** Minimal boilerplate; 422 validation for free; Swagger UI at `/docs`;
  `TestClient` makes endpoint tests trivial.
- **Negative / trade-offs:** ASGI/async model is heavier than a micro-framework; for a
  synchronous file store we accept sync handlers.
- **Follow-ups:** Group endpoints under `APIRouter(tags=...)` during the layered
  refactor (see [ADR-0003](0003-cluster-multitenancy.md) and the C4 component view).
