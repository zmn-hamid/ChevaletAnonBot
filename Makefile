# Makefile for Chevalet Anonymous Telegram Bot
# Usage: make <target>
# Example: make up

.PHONY: help gooz up down restart logs logs-bot logs-db build rebuild status shell db-shell backup restore clean dev-up dev-down test

# Default target - shows help
.DEFAULT_GOAL := help

##@ General

help: ## Show this help message
	@echo "Chevalet Anonymous Telegram Bot - Available Commands:"
	@echo ""
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make \033[36m<target>\033[0m\n"} /^[a-zA-Z_-]+:.*?##/ { printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2 } /^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) } ' $(MAKEFILE_LIST)

##@ Docker Operations

up: ## Start all services (production)
	@echo "Starting services..."
	docker compose up -d
	@echo "Services started! Check logs with: make logs"

down: ## Stop all services
	@echo "Stopping services..."
	docker compose down
	@echo "Services stopped."

restart: ## Restart all services
	@echo "Restarting services..."
	docker compose restart
	@echo "Services restarted."

build: ## Build Docker images
	@echo "Building images..."
	docker compose build
	@echo "Build complete."

rebuild: ## Rebuild and restart services (use after code changes)
	@echo "Rebuilding and restarting..."
	docker compose down
	docker compose up -d --build
	@echo "Rebuild complete! Check logs with: make logs"

##@ Logs & Monitoring

logs: ## Show logs from all services (follow mode)
	docker compose logs -f

logs-bot: ## Show logs from bot only (follow mode)
	docker compose logs -f bot

logs-db: ## Show logs from database only (follow mode)
	docker compose logs -f postgres

logs-tail: ## Show last 100 lines from bot
	docker compose logs --tail=100 bot

status: ## Show status of all containers
	docker compose ps

##@ Development

dev-up: ## Start development environment
	@echo "Starting development environment..."
	docker compose -f docker-compose.dev.yml up -d --build
	@echo "Dev environment started! Check logs with: make dev-logs"

dev-down: ## Stop development environment
	@echo "Stopping development environment..."
	docker compose -f docker-compose.dev.yml down
	@echo "Dev environment stopped."

dev-logs: ## Show development logs
	docker compose -f docker-compose.dev.yml logs -f

shell: ## Open bash shell in bot container
	docker compose exec bot bash

db-shell: ## Open PostgreSQL shell
	docker compose exec postgres psql -U $${DB_USER:-botuser} -d $${DB_NAME:-mydatabase}

##@ Database Operations

backup: ## Backup database to ./backups/
	@echo "Creating backup..."
	@bash backup.sh
	@echo "Backup complete!"

restore: ## Restore database from backup (Usage: make restore FILE=backups/backup_file.sql.gz)
	@if [ -z "$(FILE)" ]; then \
		echo "Error: Please specify backup file"; \
		echo "Usage: make restore FILE=backups/backup_mydatabase_20250128_120000.sql.gz"; \
		echo ""; \
		echo "Available backups:"; \
		ls -lh ./backups/ 2>/dev/null || echo "No backups found"; \
		exit 1; \
	fi
	@echo "Restoring from $(FILE)..."
	@bash restore.sh $(FILE)

db-reset: ## Reset database (WARNING: Deletes all data!)
	@echo "WARNING: This will delete all data!"
	@read -p "Are you sure? Type 'yes' to continue: " confirm; \
	if [ "$$confirm" = "yes" ]; then \
		docker compose down -v; \
		docker compose up -d postgres; \
		sleep 5; \
		docker compose up -d bot; \
		echo "Database reset complete."; \
	else \
		echo "Cancelled."; \
	fi

##@ Maintenance

clean: ## Remove stopped containers and unused images
	@echo "Cleaning up Docker resources..."
	docker compose down --remove-orphans
	docker system prune -f
	@echo "Cleanup complete."

clean-all: ## Remove everything including volumes (WARNING: Deletes database!)
	@echo "WARNING: This will delete the database!"
	@read -p "Are you sure? Type 'yes' to continue: " confirm; \
	if [ "$$confirm" = "yes" ]; then \
		docker compose down -v --remove-orphans; \
		docker system prune -af; \
		echo "All Docker resources removed."; \
	else \
		echo "Cancelled."; \
	fi

logs-clean: ## Remove old log files (older than 30 days)
	@echo "Removing old log files..."
	find ./logs -name "*.log" -mtime +30 -delete 2>/dev/null || true
	find ./backups -name "*.sql.gz" -mtime +60 -delete 2>/dev/null || true
	@echo "Old logs cleaned."

update: ## Pull latest code and rebuild
	@echo "Updating application..."
	git pull
	docker compose up -d --build
	@echo "Update complete!"

##@ Testing & Debugging

test-db: ## Test database connection
	@echo "Testing database connection..."
	docker compose exec bot python -c "from modules.Global.database import db_base; print('✓ Database connection OK')"

test-env: ## Show environment variables in bot container
	docker compose exec bot printenv | grep -E "DB_|BOT_|ADMIN"

check-health: ## Check health status of all containers
	@docker compose ps --format "table {{.Name}}\t{{.Status}}\t{{.Health}}"

inspect: ## Show detailed container information
	docker compose exec bot python -c "import sys; print(f'Python: {sys.version}'); from config import *; print(f'DB Host: {DB_HOST}'); print(f'DB Name: {DB_NAME}')"

##@ Quick Actions

quick-restart: down up logs-tail ## Quick restart: down, up, show logs

deploy: rebuild logs-tail ## Deploy: rebuild and show logs

emergency-stop: ## Emergency stop (force stop all containers)
	@echo "Emergency stop initiated..."
	docker compose kill
	docker compose down
	@echo "All services forcefully stopped."
