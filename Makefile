.PHONY: db-up db-down api web test lint

db-up:
	docker compose up -d db

db-down:
	docker compose down

api:
	cd api && uv run uvicorn app.main:app --reload

web:
	cd web && pnpm dev

test:
	cd api && uv run pytest

lint:
	cd api && uv run ruff check .
	cd web && pnpm lint