.PHONY: help up down logs ps migrate revision test-backend test-frontend e2e lint fmt

help: ## Lista los comandos disponibles
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-16s %s\n", $$1, $$2}'

up: ## Levanta todo el stack (db, redis, backend, frontend)
	docker compose up --build -d

down: ## Detiene el stack (conserva volúmenes)
	docker compose down

logs: ## Sigue los logs de todos los servicios
	docker compose logs -f

ps: ## Estado de los servicios
	docker compose ps

migrate: ## Aplica migraciones Alembic
	docker compose exec backend alembic upgrade head

revision: ## Crea una migración: make revision m="mensaje"
	docker compose exec backend alembic revision --autogenerate -m "$(m)"

test-backend: ## Tests backend con cobertura
	docker compose exec backend pytest --cov=app --cov-report=term-missing

test-frontend: ## Tests unitarios frontend (Vitest)
	docker compose exec frontend npm test

e2e: ## Tests E2E (Playwright) contra el stack levantado
	cd frontend && E2E_BASE_URL=http://localhost:3000 npx playwright test

lint: ## Lint + tipos (backend y frontend)
	docker compose exec backend sh -c "ruff check . && ruff format --check . && mypy app"
	docker compose exec frontend sh -c "npm run lint && npm run typecheck"

fmt: ## Formatea el backend
	docker compose exec backend sh -c "ruff check --fix . && ruff format ."
