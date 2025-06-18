# Makefile for KomuniTech

.PHONY: help install install-dev test test-cov lint format run migrate seed clean docker-build docker-up docker-down

# Default target
.DEFAULT_GOAL := help

# Variables
PYTHON := python3
PIP := $(PYTHON) -m pip
FLASK := flask
PYTEST := pytest
BLACK := black
ISORT := isort
FLAKE8 := flake8

# Help command
help: ## Show this help message
	@echo "KomuniTech Makefile"
	@echo "==================="
	@echo ""
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# Installation
install: ## Install production dependencies
	$(PIP) install -r requirements.txt

install-dev: install ## Install development dependencies
	$(PIP) install -r test-requirements.txt
	$(PIP) install black isort flake8 pylint

# Testing
test: ## Run tests
	$(PYTEST) tests/ -v

test-cov: ## Run tests with coverage
	$(PYTEST) tests/ -v --cov=app --cov-report=html --cov-report=term

test-unit: ## Run unit tests only
	$(PYTEST) tests/unit/ -v

test-integration: ## Run integration tests only
	$(PYTEST) tests/integration/ -v

test-watch: ## Run tests in watch mode
	$(PYTEST) tests/ -v --watch

# Code Quality
lint: ## Run linting
	$(FLAKE8) app/ tests/ --max-line-length=120 --extend-ignore=E203,W503
	$(PYTHON) -m pylint app/ --disable=C0114,C0115,C0116,R0903,R0801

format: ## Format code
	$(BLACK) app/ tests/
	$(ISORT) app/ tests/

check-format: ## Check code formatting
	$(BLACK) --check app/ tests/
	$(ISORT) --check-only app/ tests/

# Database
db-init: ## Initialize database
	$(FLASK) db init

db-migrate: ## Create new migration
	$(FLASK) db migrate -m "$(message)"

db-upgrade: ## Apply migrations
	$(FLASK) db upgrade

db-downgrade: ## Rollback migration
	$(FLASK) db downgrade

db-seed: ## Seed database with initial data
	$(FLASK) seed-db

db-reset: ## Reset database (drop all tables and recreate)
	$(FLASK) db downgrade base
	$(FLASK) db upgrade
	$(FLASK) seed-db

# Running the application
run: ## Run development server
	$(FLASK) run --debug

run-prod: ## Run production server
	gunicorn --bind 0.0.0.0:5000 --workers 4 --timeout 120 run:app

# Docker
docker-build: ## Build Docker image
	docker build -t komunitech:latest .

docker-up: ## Start Docker containers
	docker compose up -d

docker-down: ## Stop Docker containers
	docker compose down

docker-logs: ## View Docker logs
	docker compose logs -f

docker-shell: ## Shell into web container
	docker compose exec web /bin/bash

docker-db-shell: ## Shell into database container
	docker compose exec db psql -U komunitech_user -d komunitech_db

docker-restart: ## Restart Docker containers
	docker compose restart

docker-rebuild: docker-down ## Rebuild and restart containers
	docker compose build --no-cache
	docker compose up -d

# Maintenance
clean: ## Clean up temporary files
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf *.egg-info
	rm -rf build/
	rm -rf dist/

clean-uploads: ## Clean uploaded files (careful!)
	@echo "This will delete all uploaded files. Are you sure? [y/N]"
	@read -r response; \
	if [ "$$response" = "y" ]; then \
		rm -rf app/static/uploads/*; \
		echo "Uploaded files deleted."; \
	else \
		echo "Operation cancelled."; \
	fi

# Development shortcuts
dev: install-dev db-upgrade db-seed ## Setup development environment
	@echo "Development environment ready!"

reset-dev: clean db-reset ## Reset development environment
	@echo "Development environment reset!"

# Production
deploy-check: test lint ## Run checks before deployment
	@echo "All checks passed! Ready for deployment."

# Utilities
shell: ## Open Python shell with app context
	$(FLASK) shell

routes: ## Show all routes
	$(FLASK) routes

create-admin: ## Create admin user
	@read -p "Username: " username; \
	read -p "Email: " email; \
	read -p "Name: " name; \
	read -s -p "Password: " password; \
	echo ""; \
	$(FLASK) create-admin --username $$username --email $$email --name "$$name" --password $$password

backup-db: ## Backup database
	@mkdir -p backups
	@if [ -f app/app.db ]; then \
		cp app/app.db backups/app-$$(date +%Y%m%d-%H%M%S).db; \
		echo "Database backed up to backups/"; \
	else \
		echo "No database file found!"; \
	fi

# Git hooks
install-hooks: ## Install git hooks
	@echo "#!/bin/sh" > .git/hooks/pre-commit
	@echo "make lint" >> .git/hooks/pre-commit
	@echo "make test-unit" >> .git/hooks/pre-commit
	@chmod +x .git/hooks/pre-commit
	@echo "Git hooks installed!"