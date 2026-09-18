PYTEST_ARGS ?= --capture=no

# Compose project backing `make outline-up`; the integration suite reads
# OUTLINE_API_URL/OUTLINE_API_TOKEN from the credentials it prints.
COMPOSE := docker compose -f docker/compose.yaml -p outline-client

.DEFAULT_GOAL := help
MAKEFLAGS += --no-print-directory

.PHONY: help install lock upgrade outdated schemas check format test test-integration coverage build code clean outline-up outline-down outline-logs

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2}'

install: ## Sync the locked environment
	uv sync --frozen

lock: ## Update the lock file and re-sync
	uv lock
	$(MAKE) install

upgrade: ## Upgrade dependencies and re-sync
	uv lock --upgrade
	$(MAKE) install

outdated: ## Show available dependency upgrades
	uv lock --upgrade --dry-run

schemas: ## Regenerate the Pydantic schemas from the OpenAPI spec
	uv run python scripts/generate_schemas.py

check: ## Run linters and type checks
	uv run ruff check
	uv run ruff format --check
	uv run mypy . --exclude site

format: ## Auto-format and apply lint fixes
	uv run ruff format
	uv run ruff check --fix

test: ## Run unit tests
	uv run pytest -m "not integration" $(PYTEST_ARGS)

test-integration: ## Run integration tests against a live Outline instance
	uv run pytest -m integration $(PYTEST_ARGS)

coverage: ## Run unit tests with coverage reporting
	uv run pytest -m "not integration" --cov=src --cov-report=term-missing --cov-report=xml --cov-fail-under=80 $(PYTEST_ARGS)

build: ## Build distribution artifacts
	rm -rf dist
	uv build

outline-up: ## Start a local Outline instance on port 8099 and seed an API token
	$(COMPOSE) up -d --wait
	uv run python docker/seed.py

outline-down: ## Stop the local Outline instance and delete its data
	$(COMPOSE) down -v

outline-logs: ## Tail the local Outline instance logs
	$(COMPOSE) logs -f outline

code: ## Open the VS Code workspace
	code .vscode/outline-client.code-workspace

clean: ## Remove build and cache artifacts
	rm -rf dist .mypy_cache .ruff_cache .pytest_cache
	find . -type d -name '__pycache__' -exec rm -rf {} +
