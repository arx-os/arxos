# Arxos Platform Makefile
# Modern dependency management with pyproject.toml

.PHONY: help install install-dev install-prod test test-cov lint format type-check security-check clean setup-dev run-api run-tests docker-build docker-up docker-down

# Default target
help:
	@echo "🚀 Arxos Platform - Available Commands"
	@echo "======================================"
	@echo ""
	@echo "📦 Installation:"
	@echo "  install        - Install production dependencies"
	@echo "  install-dev    - Install with development dependencies (recommended)"
	@echo "  install-prod   - Install production dependencies only"
	@echo "  setup-dev      - Complete development environment setup"
	@echo ""
	@echo "🧪 Testing:"
	@echo "  test           - Run all tests"
	@echo "  test-cov       - Run tests with coverage"
	@echo "  test-unit      - Run unit tests only"
	@echo "  test-integration - Run integration tests only"
	@echo ""
	@echo "🔧 Code Quality:"
	@echo "  lint           - Run linting (flake8)"
	@echo "  format         - Format code (black + isort)"
	@echo "  type-check     - Run type checking (mypy)"
	@echo "  security-check - Run security scanning"
	@echo ""
	@echo "🚀 Development:"
	@echo "  run-api        - Start the API server"
	@echo "  run-tests      - Run tests in watch mode"
	@echo ""
	@echo "🐳 Docker:"
	@echo "  docker-build   - Build Docker image"
	@echo "  docker-up      - Start Docker services"
	@echo "  docker-down    - Stop Docker services"
	@echo ""
	@echo "🧹 Maintenance:"
	@echo "  clean          - Clean build artifacts"
	@echo "  clean-cache    - Clean cache files and temporary data"
	@echo "  update-deps    - Update dependencies"

# Installation targets
install: install-prod

install-dev:
	@echo "📦 Installing with development dependencies..."
	pip install -e ".[dev]"
	@echo "✅ Development dependencies installed"

install-prod:
	@echo "📦 Installing production dependencies..."
	pip install -e .
	@echo "✅ Production dependencies installed"

setup-dev:
	@echo "🚀 Setting up development environment..."
	python scripts/setup_dev.py

# Testing targets
test:
	@echo "🧪 Running all tests..."
	pytest

test-cov:
	@echo "🧪 Running tests with coverage..."
	pytest --cov=application --cov=api --cov=domain --cov=infrastructure --cov-report=term-missing --cov-report=html

test-unit:
	@echo "🧪 Running unit tests..."
	pytest -m unit

test-integration:
	@echo "🧪 Running integration tests..."
	pytest -m integration

# Code quality targets
lint:
	@echo "🔍 Running linting..."
	flake8 application api domain infrastructure tests

format:
	@echo "🎨 Formatting code..."
	black .
	isort .

type-check:
	@echo "🔍 Running type checking..."
	mypy application api domain infrastructure

security-check:
	@echo "🔒 Running security checks..."
	bandit -r application api domain infrastructure
	safety check

# Development targets
run-api:
	@echo "🚀 Starting API server..."
	uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

run-tests:
	@echo "🧪 Running tests in watch mode..."
	pytest-watch

# Docker targets
docker-build:
	@echo "🐳 Building Docker image..."
	docker build -t arxos:latest .

docker-up:
	@echo "🐳 Starting Docker services..."
	docker-compose up -d

docker-down:
	@echo "🐳 Stopping Docker services..."
	docker-compose down

# Maintenance targets
clean:
	@echo "🧹 Cleaning build artifacts..."
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	rm -rf htmlcov/
	rm -rf .coverage*
	@echo "✅ Cleanup complete"

clean-cache:
	@echo "🧹 Cleaning cache files..."
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf htmlcov/
	rm -f .coverage*
	rm -rf *.egg-info/
	@echo "✅ Cache cleanup complete"

update-deps:
	@echo "📦 Updating dependencies..."
	pip install --upgrade pip
	pip install --upgrade -e ".[dev]"
	@echo "✅ Dependencies updated"

# Pre-commit hooks
pre-commit-install:
	@echo "🔧 Installing pre-commit hooks..."
	pre-commit install

pre-commit-run:
	@echo "🔧 Running pre-commit hooks..."
	pre-commit run --all-files

# Database targets
db-migrate:
	@echo "🗄️ Running database migrations..."
	alembic upgrade head

db-seed:
	@echo "🌱 Seeding database..."
	python scripts/seed_database.py

# Health check
health:
	@echo "🏥 Checking service health..."
	curl -f http://localhost:8000/health || echo "❌ API server not responding"
	curl -f http://localhost:6379 || echo "❌ Redis not responding"

# Development shortcuts
dev: install-dev run-api

test-all: test-cov lint type-check security-check

ci: install-dev test-all

# Help for specific targets
help-install:
	@echo "📦 Installation Options:"
	@echo "  make install-dev    - Install with all development tools"
	@echo "  make install-prod   - Install production dependencies only"
	@echo "  make setup-dev      - Complete development environment setup"

help-test:
	@echo "🧪 Testing Options:"
	@echo "  make test           - Run all tests"
	@echo "  make test-cov       - Run tests with coverage report"
	@echo "  make test-unit      - Run unit tests only"
	@echo "  make test-integration - Run integration tests only"

help-quality:
	@echo "🔧 Code Quality Options:"
	@echo "  make lint           - Run flake8 linting"
	@echo "  make format         - Format code with black and isort"
	@echo "  make type-check     - Run mypy type checking"
	@echo "  make security-check - Run security scanning"
	@echo "  make test-all       - Run all quality checks" 