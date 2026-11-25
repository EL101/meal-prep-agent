.PHONY: setup services migrate api worker mobile test lint evals

setup:            ## install backend + mobile deps
	cd backend && uv sync
	cd mobile && npm install

services:         ## start local Postgres + Redis
	docker compose up -d

migrate:          ## apply DB migrations
	cd backend && uv run alembic upgrade head

api:              ## FastAPI on :8000 with reload
	cd backend && uv run fastapi dev app/main.py

worker:           ## arq worker for Claude jobs
	cd backend && uv run arq app.worker.settings.WorkerSettings --watch app

mobile:           ## Expo dev server
	cd mobile && npx expo start

test:
	cd backend && uv run pytest

lint:
	cd backend && uv run ruff check . && uv run ruff format --check . && uv run mypy app evals
	cd mobile && npx tsc --noEmit

evals:            ## runs real Claude calls (costs money)
	cd backend && uv run python -m evals.run
