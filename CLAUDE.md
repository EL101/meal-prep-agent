# CLAUDE.md

Meal Prep Agent: a mobile app that builds weekly meal-prep plans. See README.md for the product spec.

## Layout
- `backend/`: Python 3.12, FastAPI, async SQLAlchemy, Alembic, managed with uv
- `mobile/`: Expo (React Native, TypeScript)

## Commands
Backend (run from `backend/`):
- `uv sync`: install deps
- `uv run fastapi dev app/main.py`: run the API on :8000
- `uv run pytest`: tests
- `uv run ruff check . && uv run ruff format --check .`: lint and format check
- `uv run alembic revision --autogenerate -m "..."` then `uv run alembic upgrade head`: migrations

Mobile (run from `mobile/`):
- `npx expo start`: dev server
- `npx tsc --noEmit`: type check
- Add packages with `npx expo install <pkg>`, not `npm install`, so versions match the Expo SDK

## Backend conventions
Layers, top to bottom: `api/` (routes) → `services/` (business logic) → `repositories/` (queries) → `models/` (tables).
- Routes parse requests into `schemas/` models, call a service, and return a schema. No queries or business rules in routes.
- Services hold the rules and own `session.commit()`. They never import from `app.api`.
- Repositories are the only place that runs queries. Subclass `BaseRepository[Model]`.
- Register every new model in `app/models/__init__.py` so Alembic autogenerate sees it.
- Settings come from env vars via `app/config.py`. Never hardcode secrets.

## Before you push
Run the backend lint and tests and the mobile type check above. CI runs the same checks, and pushes to `main` deploy the backend to Railway.

## Git
- Author commits as `ethan <eliu3152@gmail.com>` and leave the committer as Claude, so signed commits show as Verified on GitHub:
  `git commit --author="ethan <eliu3152@gmail.com>" -m "..."`
- Work on a branch and open a PR. Don't push to `main`.
