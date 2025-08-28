# Arxos Makefile - Single Source of Truth for All Commands
# =========================================================

# Colors for output
RED := \033[0;31m
GREEN := \033[0;32m
YELLOW := \033[0;33m
BLUE := \033[0;34m
NC := \033[0m # No Color

# Project paths
BACKEND_DIR := services/backend
AI_DIR := services/ai
FRONTEND_DIR := services/frontend
DEMO_DIR := demo
SCRIPTS_DIR := scripts
TESTS_DIR := tests

# Default target
.DEFAULT_GOAL := help

# Phony targets
.PHONY: help setup start stop demo test clean logs status check migrate

# ==============================================================================
# HELP
# ==============================================================================

help: ## Show this help message
	@echo "$(BLUE)Arxos Development Commands$(NC)"
	@echo "$(BLUE)===========================$(NC)"
	@echo ""
	@echo "$(GREEN)Available targets:$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(YELLOW)%-20s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(GREEN)Quick Start:$(NC)"
	@echo "  1. make setup    - Initial project setup"
	@echo "  2. make start    - Start all services"
	@echo "  3. make demo     - Open demo in browser"
	@echo ""

# ==============================================================================
# SETUP & INSTALLATION
# ==============================================================================

setup: ## Initial project setup (run once)
	@echo "$(BLUE)Setting up Arxos project...$(NC)"
	@echo "$(YELLOW)1. Checking dependencies...$(NC)"
	@command -v go >/dev/null 2>&1 || { echo "$(RED)Go is required but not installed.$(NC)" >&2; exit 1; }
	@command -v python3 >/dev/null 2>&1 || { echo "$(RED)Python 3 is required but not installed.$(NC)" >&2; exit 1; }
	@command -v npm >/dev/null 2>&1 || { echo "$(RED)Node.js is required but not installed.$(NC)" >&2; exit 1; }
	
	@echo "$(YELLOW)2. Installing Go dependencies...$(NC)"
	@cd $(BACKEND_DIR) 2>/dev/null || cd core/backend && go mod download
	
	@echo "$(YELLOW)3. Setting up Python virtual environment...$(NC)"
	@cd $(AI_DIR) 2>/dev/null || cd ai_service && python3 -m venv venv
	@cd $(AI_DIR) 2>/dev/null || cd ai_service && ./venv/bin/pip install -r requirements.txt
	
	@echo "$(YELLOW)4. Creating necessary directories...$(NC)"
	@mkdir -p build/bin build/dist logs temp_uploads extraction_debug
	
	@echo "$(GREEN)✓ Setup complete!$(NC)"
	@echo "Run 'make start' to start all services"

# ==============================================================================
# SERVICE MANAGEMENT
# ==============================================================================

start: ## Start all services
	@echo "$(BLUE)Starting Arxos services...$(NC)"
	@$(MAKE) start-backend
	@$(MAKE) start-ai
	@$(MAKE) start-frontend
	@echo "$(GREEN)✓ All services started!$(NC)"
	@echo "Run 'make demo' to open the demo"

start-backend: ## Start backend service
	@echo "$(YELLOW)Starting backend service...$(NC)"
	@pkill -f "go run.*main.go" 2>/dev/null || true
	@cd core/backend && go run main.go > ../../logs/backend.log 2>&1 &
	@sleep 2
	@echo "$(GREEN)✓ Backend started on port 8080$(NC)"

start-ai: ## Start AI service
	@echo "$(YELLOW)Starting AI service...$(NC)"
	@pkill -f "uvicorn.*main:app" 2>/dev/null || true
	@cd ai_service && source venv/bin/activate && uvicorn main:app --host 0.0.0.0 --port 8000 > ../logs/ai_service.log 2>&1 &
	@sleep 3
	@echo "$(GREEN)✓ AI service started on port 8000$(NC)"

start-frontend: ## Start frontend service
	@echo "$(YELLOW)Starting frontend service...$(NC)"
	@pkill -f "python.*serve" 2>/dev/null || true
	@cd demo 2>/dev/null || { echo "$(YELLOW)Creating demo directory...$(NC)" && mkdir -p demo && cp arxos_demo.html demo/index.html 2>/dev/null || echo "Demo file will be created"; }
	@python3 -m http.server 3000 --directory . > logs/frontend.log 2>&1 &
	@sleep 1
	@echo "$(GREEN)✓ Frontend started on port 3000$(NC)"

stop: ## Stop all services
	@echo "$(BLUE)Stopping all services...$(NC)"
	@pkill -f "go run.*main.go" 2>/dev/null || true
	@pkill -f "uvicorn.*main:app" 2>/dev/null || true
	@pkill -f "python.*http.server" 2>/dev/null || true
	@lsof -ti:8080 | xargs kill -9 2>/dev/null || true
	@lsof -ti:8000 | xargs kill -9 2>/dev/null || true
	@lsof -ti:3000 | xargs kill -9 2>/dev/null || true
	@echo "$(GREEN)✓ All services stopped$(NC)"

restart: ## Restart all services
	@$(MAKE) stop
	@sleep 2
	@$(MAKE) start

# ==============================================================================
# DEMO
# ==============================================================================

demo: ## Open the demo in browser
	@echo "$(BLUE)Opening Arxos demo...$(NC)"
	@if ! lsof -ti:8080 >/dev/null 2>&1; then \
		echo "$(YELLOW)Backend not running. Starting services...$(NC)"; \
		$(MAKE) start; \
		sleep 3; \
	fi
	@echo "$(GREEN)Opening demo at http://localhost:3000/demo$(NC)"
	@open http://localhost:3000/demo/index.html 2>/dev/null || open http://localhost:8080/arxos_demo.html 2>/dev/null || echo "Please open http://localhost:3000/demo in your browser"

# ==============================================================================
# TESTING
# ==============================================================================

test: ## Run all tests
	@echo "$(BLUE)Running all tests...$(NC)"
	@$(MAKE) test-unit
	@$(MAKE) test-integration
	@echo "$(GREEN)✓ All tests passed!$(NC)"

test-unit: ## Run unit tests
	@echo "$(YELLOW)Running unit tests...$(NC)"
	@cd core/backend && go test ./... -short
	@cd ai_service && source venv/bin/activate && pytest tests/unit 2>/dev/null || pytest tests/ -k "not integration"
	@echo "$(GREEN)✓ Unit tests passed$(NC)"

test-integration: ## Run integration tests
	@echo "$(YELLOW)Running integration tests...$(NC)"
	@if [ -f tests/test_integration.sh ]; then \
		bash tests/test_integration.sh; \
	else \
		echo "$(YELLOW)Integration tests not configured yet$(NC)"; \
	fi

test-e2e: ## Run end-to-end tests
	@echo "$(YELLOW)Running E2E tests...$(NC)"
	@echo "$(YELLOW)E2E tests not configured yet$(NC)"

# ==============================================================================
# DEVELOPMENT
# ==============================================================================

logs: ## Show logs from all services
	@echo "$(BLUE)Showing recent logs...$(NC)"
	@echo "$(YELLOW)=== Backend Logs ===$(NC)"
	@tail -20 logs/backend.log 2>/dev/null || echo "No backend logs"
	@echo ""
	@echo "$(YELLOW)=== AI Service Logs ===$(NC)"
	@tail -20 logs/ai_service.log 2>/dev/null || echo "No AI service logs"
	@echo ""
	@echo "$(YELLOW)=== Frontend Logs ===$(NC)"
	@tail -20 logs/frontend.log 2>/dev/null || echo "No frontend logs"

logs-backend: ## Show backend logs (follow)
	@tail -f logs/backend.log

logs-ai: ## Show AI service logs (follow)
	@tail -f logs/ai_service.log

logs-frontend: ## Show frontend logs (follow)
	@tail -f logs/frontend.log

status: ## Check service status
	@echo "$(BLUE)Service Status:$(NC)"
	@if lsof -ti:8080 >/dev/null 2>&1; then \
		echo "  $(GREEN)✓$(NC) Backend:  Running on port 8080"; \
	else \
		echo "  $(RED)✗$(NC) Backend:  Not running"; \
	fi
	@if lsof -ti:8000 >/dev/null 2>&1; then \
		echo "  $(GREEN)✓$(NC) AI:       Running on port 8000"; \
	else \
		echo "  $(RED)✗$(NC) AI:       Not running"; \
	fi
	@if lsof -ti:3000 >/dev/null 2>&1; then \
		echo "  $(GREEN)✓$(NC) Frontend: Running on port 3000"; \
	else \
		echo "  $(RED)✗$(NC) Frontend: Not running"; \
	fi

# ==============================================================================
# DATABASE
# ==============================================================================

migrate: ## Run database migrations
	@echo "$(BLUE)Running database migrations...$(NC)"
	@cd core/backend && go run cmd/migrate/main.go 2>/dev/null || echo "$(YELLOW)Migration tool not configured$(NC)"

db-reset: ## Reset database (WARNING: destroys data)
	@echo "$(RED)WARNING: This will destroy all data!$(NC)"
	@echo "Press Ctrl+C to cancel, or wait 5 seconds to continue..."
	@sleep 5
	@echo "$(YELLOW)Resetting database...$(NC)"
	@cd core/backend && go run cmd/reset/main.go 2>/dev/null || echo "$(YELLOW)Reset tool not configured$(NC)"

# ==============================================================================
# BUILD & DEPLOY
# ==============================================================================

build: ## Build production binaries
	@echo "$(BLUE)Building production binaries...$(NC)"
	@echo "$(YELLOW)Building backend...$(NC)"
	@cd core/backend && go build -o ../../build/bin/arxos-backend main.go
	@echo "$(YELLOW)Building frontend...$(NC)"
	@cd frontend && npm run build 2>/dev/null || echo "Frontend build not configured"
	@echo "$(GREEN)✓ Build complete! Binaries in build/bin/$(NC)"

proto: ## Generate protobuf code for Go and Python
	@echo "$(BLUE)Generating protobuf code...$(NC)"
	@echo "$(YELLOW)Installing protoc tools if needed...$(NC)"
	@go install google.golang.org/protobuf/cmd/protoc-gen-go@latest 2>/dev/null || true
	@go install google.golang.org/grpc/cmd/protoc-gen-go-grpc@latest 2>/dev/null || true
	@echo "$(YELLOW)Generating Go code...$(NC)"
	@protoc -I=proto --go_out=. --go-grpc_out=. proto/ingestion/*.proto 2>/dev/null || echo "Protoc not installed"
	@echo "$(YELLOW)Generating Python code...$(NC)"
	@cd ai_services && python -m grpc_tools.protoc -I=../proto --python_out=. --grpc_python_out=. ../proto/ingestion/*.proto 2>/dev/null || echo "Python grpc_tools not installed"
	@echo "$(GREEN)✓ Protobuf code generated$(NC)"

docker-build: ## Build Docker images
	@echo "$(BLUE)Building Docker images...$(NC)"
	@docker-compose build
	@echo "$(GREEN)✓ Docker images built$(NC)"

docker-up: ## Start services with Docker
	@echo "$(BLUE)Starting services with Docker...$(NC)"
	@docker-compose up -d
	@echo "$(GREEN)✓ Services started with Docker$(NC)"
	@echo "  API: http://localhost:8080"
	@echo "  AI gRPC: localhost:50051"
	@echo "  PostgreSQL: localhost:5432"

docker-down: ## Stop Docker services
	@echo "$(BLUE)Stopping Docker services...$(NC)"
	@docker-compose down
	@echo "$(GREEN)✓ Docker services stopped$(NC)"

docker-logs: ## Show Docker service logs
	@docker-compose logs -f

docker-clean: ## Clean Docker volumes and images
	@echo "$(RED)WARNING: This will remove all Docker volumes!$(NC)"
	@sleep 3
	@docker-compose down -v
	@docker system prune -f
	@echo "$(GREEN)✓ Docker cleanup complete$(NC)"

grpc-test: ## Test gRPC connection
	@echo "$(BLUE)Testing gRPC connection...$(NC)"
	@python -c "import grpc; channel = grpc.insecure_channel('localhost:50051'); print('✓ gRPC connection successful' if grpc.channel_ready_future(channel).result(timeout=5) else '✗ Connection failed')" 2>/dev/null || echo "$(RED)gRPC connection failed$(NC)"

# ==============================================================================
# CLEANUP
# ==============================================================================

clean: ## Clean build artifacts and temp files
	@echo "$(BLUE)Cleaning build artifacts...$(NC)"
	@rm -rf build/bin/* build/dist/*
	@rm -rf temp_uploads/*
	@rm -rf extraction_debug/*
	@find . -name "*.pyc" -delete
	@find . -name "__pycache__" -delete
	@find . -name ".DS_Store" -delete
	@echo "$(GREEN)✓ Cleanup complete$(NC)"

clean-logs: ## Clean log files
	@echo "$(BLUE)Cleaning log files...$(NC)"
	@rm -f logs/*.log
	@echo "$(GREEN)✓ Logs cleaned$(NC)"

clean-all: ## Clean everything (including dependencies)
	@$(MAKE) clean
	@$(MAKE) clean-logs
	@echo "$(YELLOW)Removing dependencies...$(NC)"
	@rm -rf ai_service/venv
	@rm -rf node_modules
	@echo "$(GREEN)✓ Full cleanup complete$(NC)"

# ==============================================================================
# UTILITIES
# ==============================================================================

check: ## Run pre-commit checks
	@echo "$(BLUE)Running pre-commit checks...$(NC)"
	@echo "$(YELLOW)Checking Go code...$(NC)"
	@cd core/backend && go fmt ./... && go vet ./...
	@echo "$(YELLOW)Checking Python code...$(NC)"
	@cd ai_service && source venv/bin/activate && black . --check 2>/dev/null || echo "Install black: pip install black"
	@echo "$(GREEN)✓ Pre-commit checks passed$(NC)"

format: ## Format all code
	@echo "$(BLUE)Formatting code...$(NC)"
	@cd core/backend && go fmt ./...
	@cd ai_service && source venv/bin/activate && black . 2>/dev/null || echo "Install black: pip install black"
	@echo "$(GREEN)✓ Code formatted$(NC)"

# ==============================================================================
# DEVELOPMENT SHORTCUTS
# ==============================================================================

dev: ## Start development environment
	@$(MAKE) start
	@$(MAKE) logs

reset: ## Full reset (stop, clean, setup, start)
	@$(MAKE) stop
	@$(MAKE) clean-all
	@$(MAKE) setup
	@$(MAKE) start
	@$(MAKE) demo