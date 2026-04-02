---
description: "Use when writing, reviewing, or refactoring Python code for the FastAPI surveillance-camera backend. Covers Python 3.12 syntax, Pylance strict type checking, FastAPI and Pydantic v2 conventions, async route handlers, dependency injection, Redis, Firebase, MinIO, Loguru, Frigate NVR events, FCM push notifications, and pytest test structure."
applyTo: "api/**/*.py"
---

# Python – FastAPI Surveillance Camera Backend

## Runtime

- Target **Python 3.12**. Rely on built-in generics (`list[str]`, `dict[str, int]`, `tuple[int, ...]`) — no `from __future__ import annotations` needed.
- Use the `X | None` union syntax instead of `Optional[X]`.
- Prefer `match`/`case` for multi-branch dispatch on event types or status codes.

## Pylance (strict mode)

- All functions and methods must have **full type annotations** on parameters and return types.
- No implicit re-exports: only re-export symbols that are explicitly listed in `__all__`.
- Do not suppress Pylance errors with `# type: ignore` unless the suppression is unavoidable and has an inline comment explaining why.
- `reportMissingTypeStubs` warnings on third-party packages are expected and acceptable; suppress selectively with `# type: ignore[import-untyped]`.

## FastAPI conventions

- Use `async def` for all route handlers. Use `def` only for sync CPU-bound tasks run via `asyncio.run_in_executor`.
- Register routers with `APIRouter(prefix="/...", tags=["..."])` and include them in `main.py` via `app.include_router(...)`.
- Use the `lifespan` context manager for startup/shutdown logic — do **not** use the deprecated `@app.on_event` decorator.
- Always raise `HTTPException` with an appropriate `status_code` from `fastapi import status` (e.g. `status.HTTP_404_NOT_FOUND`).
- Inject shared resources (Redis, MinIO, Firebase) through `Depends()` using typed dependency functions defined in `lib/dependencies.py`.

## Pydantic v2

- Use `model_validate(data)` instead of `.parse_obj(data)`.
- Use `model_dump()` instead of `.dict()`.
- Use `model_dump(mode="json")` when serialising for Redis or HTTP responses.
- Define models in `models/` and keep validation logic inside the model using `@field_validator` or `@model_validator`.

## Logging

- Use **Loguru** (`from loguru import logger`) for all logging — never the stdlib `logging` module.
- Log at `DEBUG` for internal state, `INFO` for lifecycle events, `WARNING` for recoverable issues, `ERROR` for exceptions.
- Include structured context with `logger.bind(event_id=..., camera=...)` where helpful.

## Project stack

| Library                     | Usage                                         |
| --------------------------- | --------------------------------------------- |
| `fastapi[standard]`         | API framework, request/response validation    |
| `pydantic` v2               | Data models, settings (`BaseSettings`)        |
| `redis[hiredis]`            | Async Redis client; session/event caching     |
| `firebase-admin`            | Firestore, FCM push notification dispatch     |
| `minio`                     | Object storage for camera clips and snapshots |
| `python-jose[cryptography]` | JWT creation and verification                 |
| `passlib` / `bcrypt`        | Password hashing                              |
| `loguru`                    | Structured logging                            |

## Domain conventions

- **Frigate NVR**: camera events originate from Frigate via MQTT or HTTP webhooks. Event models map to Frigate's JSON schema.
- **Event lifecycle**: `new` → `update` → `end`. Handle all three states when polling or receiving events.
- **FCM notifications**: sent via Firebase Admin SDK after an event is persisted. Include `camera`, `label`, `score`, and a clip/snapshot URL in the notification payload.
- **MinIO storage**: clips are stored as `.mp4`, snapshots as `.jpg`. Use presigned URLs with a short TTL for download endpoints.
- **Redis caching**: event state and config are cached in Redis with a TTL. Use `redis_datastore.py` helpers rather than raw client calls.

## Testing

- Tests live in `tests/unit/` (no I/O mocks needed) and `tests/integration/` (real or mocked external services).
- Use `conftest.py` fixtures — never instantiate shared resources inside individual test functions.
- Mark async tests with `@pytest.mark.anyio` (or the configured async backend in `pytest.ini`).
- Keep unit tests free of FastAPI `TestClient` — test business logic directly through service/task functions.
- Use `TestClient` or `AsyncClient` only in integration tests.
