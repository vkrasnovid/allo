.PHONY: help up down build migrate seed test lint clean

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

up: ## Start all services
	docker compose up -d

down: ## Stop all services
	docker compose down

build: ## Build all services
	docker compose build

migrate: ## Run database migrations
	@echo "Migrations run automatically on booking service startup"
	docker compose exec booking python -m alembic upgrade head

seed: ## Seed test data
	docker compose exec booking python seed.py

test: test-booking test-engine ## Run all tests

test-booking: ## Run booking service tests
	PYTHONPATH=/opt/allo/booking:/opt/allo/shared \
		python -m pytest /opt/allo/booking/tests/ -v

test-engine: ## Run engine tests
	PYTHONPATH=/opt/allo/engine:/opt/allo/shared \
		python -m pytest /opt/allo/engine/tests/ -v

lint: ## Run linting (flake8)
	python -m flake8 booking/src engine/src shared/notifications/src --max-line-length=120

clean: ## Clean Python cache files
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete

db-shell: ## Connect to PostgreSQL
	docker compose exec postgres psql -U allo -d allo

redis-cli: ## Connect to Redis
	docker compose exec redis redis-cli -a allo_redis_pass

logs: ## Show logs from all services
	docker compose logs -f

.PHONY: help up down build migrate seed test test-booking test-engine lint clean db-shell redis-cli logs
