# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What is beets-flask

A web UI for [beets](https://beets.io/), the music library manager. It adds a browser-based interface for previewing and confirming imports, searching the library, undoing imports, and managing the inbox — all backed by beets under the hood.

## Architecture

The app is composed of four cooperating processes, typically run together via Docker:

1. **Quart server** (`backend/beets_flask/server/`) — async Python HTTP/WebSocket server. REST API under `/api_v1/`, real-time events via Socket.io. Entry point: `beets_flask.server.app:create_app` (factory pattern).
2. **RQ workers** (`backend/launch_redis_workers.py`) — background jobs for import and preview generation, backed by Redis.
3. **Watchdog worker** (`backend/launch_watchdog_worker.py`) — monitors the inbox directory for new files and enqueues previews.
4. **React SPA** (`frontend/`) — served by Vite in dev mode (port 5173, proxies API/WS to port 5001) or as static files in production.

**Data stores:**
- `/config/beets/library.db` — beets' own SQLite music library
- `/config/beets-flask/beets-flask-sqlite.db` — beets-flask app state
- Redis — RQ job queues (`import`, `preview`)

**Frontend → backend communication:** REST JSON (`/api_v1/`) + Socket.io WebSocket (`/socket.io/`). In dev mode Vite proxies both to `localhost:5001`.

**Type sharing:** `backend/generate_types.py` generates TypeScript types from Python definitions. Run it after changing shared data shapes.

## Commands

### Backend

```bash
cd backend
pip install -e .[dev,test]   # install with dev + test extras

ruff check .                  # lint
ruff format .                 # format
mypy .                        # type-check

pytest                        # all tests
pytest tests/unit/test_foo.py::test_bar   # single test
coverage run -m pytest && coverage report
```

### Frontend

```bash
cd frontend
pnpm install

pnpm run dev          # Vite dev server on :5173
pnpm run build        # production build
pnpm run lint         # ESLint
pnpm run format       # Prettier
pnpm run check-types  # tsc
pnpm run analyze      # bundle visualizer
```

### Docker (typical dev workflow)

```bash
docker compose -f docker/docker-compose.dev.yaml up    # dev (live reload)
docker compose -f docker/docker-compose.yaml up        # production
docker compose -f docker/docker-compose.tests.yaml up  # run tests in container
```

## Testing

Backend tests live in `backend/tests/`, split into `unit/` and `integration/`. Key fixtures in `backend/tests/conftest.py`:

- `testapp` / `client` — Quart test app + HTTP client
- `db_session` — SQLAlchemy session against a temp database
- `beets_lib` — real beets library pointing at test audio files in `tests/data/audio/`
- `local_redis` — `FakeStrictRedis` so no real Redis is needed

`asyncio_mode = "auto"` is set globally, so async test functions work without decoration.

## Code conventions

**Python:** Ruff (linter + formatter) and mypy with `check_untyped_defs`. NumPy-style docstrings, imperative mood. Pre-commit hooks auto-fix Ruff issues.

**TypeScript/React:** ESLint + Prettier (zero warnings in CI). Package manager is **pnpm** — do not use npm or yarn.

**API responses:** a custom JSON encoder in the backend handles `bytes`, `datetime`, `Enum`, and `dataclass` types — avoid plain `dict` responses that bypass it.

## Key config environment variables

| Variable | Purpose |
|---|---|
| `IB_SERVER_CONFIG` | Server mode: `dev`, `test`, or `prod` |
| `BEETSDIR` | Path to beets config directory |
| `BEETSFLASKDIR` | Path to beets-flask config/state directory |
| `LOG_LEVEL_*` | Per-module log levels |
| `USER_ID` / `GROUP_ID` | Container user (preserve file ownership) |
