.PHONY: help dev down logs test test-web test-api test-ai test-rls lint lint-web lint-api lint-ai seed openapi clean

DEFAULT_GOAL := help

help: ## Display this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

# ---------- Lifecycle ----------
dev: ## Start the full stack with Docker Compose in detached mode
	docker compose up -d

down: ## Stop the stack
	docker compose down

logs: ## Tail logs
	docker compose logs -f

# ---------- Tests ----------
test: test-web test-api test-ai ## Run all test suites

test-web: ## Vitest (apps/web)
	cd apps/web && npm test -- --run

test-api: ## pytest-django (apps/api, SQLite fast path)
	cd apps/api && uv run pytest

test-rls: ## RLS + postgresql_only suite against a real Postgres (Story 1.8)
	cd apps/api && uv run pytest -m "rls or postgresql_only" --ds=path_advisor.settings.test_postgres

test-ai: ## pytest (apps/ai-service)
	cd apps/ai-service && uv run pytest

# ---------- Linting ----------
lint: lint-web lint-api lint-ai ## Lint everything

lint-web:
	cd apps/web && npm run lint && npx tsc --noEmit

lint-api:
	cd apps/api && uv run ruff check . && uv run ruff format --check . && uv run mypy .

lint-ai:
	cd apps/ai-service && uv run ruff check . && uv run ruff format --check .

# ---------- Seed & OpenAPI ----------
seed: ## Idempotent dev seed (super-user + MinIO buckets)
	cd apps/api && uv run python scripts/seed_dev.py

openapi: ## Regenerate openapi.json + TS client for the web app
	cd apps/api && uv run python scripts/export_openapi.py
	bash packages/openapi/scripts/generate-ts-client.sh

# ---------- Maintenance ----------
clean: ## Remove generated artifacts
	rm -rf packages/openapi/openapi.json apps/web/src/lib/api/generated
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
	find . -type d -name .pytest_cache -prune -exec rm -rf {} +
	find . -type d -name .ruff_cache -prune -exec rm -rf {} +
	find . -type d -name .mypy_cache -prune -exec rm -rf {} +
