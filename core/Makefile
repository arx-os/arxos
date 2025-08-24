# Arxos Core Makefile

# Variables
BINARY_NAME=arxos-server
MAIN_PATH=cmd/server/main.go
BUILD_DIR=build
GO=go
GOFLAGS=-v

# Version info
VERSION ?= $(shell git describe --tags --always --dirty)
BUILD_TIME=$(shell date +%FT%T%z)
LDFLAGS=-ldflags "-X main.Version=${VERSION} -X main.BuildTime=${BUILD_TIME}"

# Colors for output
RED=\033[0;31m
GREEN=\033[0;32m
YELLOW=\033[1;33m
NC=\033[0m # No Color

.PHONY: all build run test clean install deps lint fmt vet migrate dev prod docker help

## help: Display this help message
help:
	@echo "Arxos Core Build System"
	@echo ""
	@echo "Usage:"
	@echo "  make [target]"
	@echo ""
	@echo "Targets:"
	@awk '/^[a-zA-Z\-\_0-9]+:/ { \
		helpMessage = match(lastLine, /^## (.*)/); \
		if (helpMessage) { \
			helpCommand = substr($$1, 0, index($$1, ":")-1); \
			helpMessage = substr(lastLine, RSTART + 3, RLENGTH); \
			printf "  ${GREEN}%-15s${NC} %s\n", helpCommand, helpMessage; \
		} \
	} \
	{ lastLine = $$0 }' $(MAKEFILE_LIST)

## all: Build and test everything
all: deps fmt vet test build

## deps: Download and install dependencies
deps:
	@echo "${YELLOW}Installing dependencies...${NC}"
	$(GO) mod download
	$(GO) mod tidy

## build: Build the binary
build:
	@echo "${YELLOW}Building $(BINARY_NAME)...${NC}"
	@mkdir -p $(BUILD_DIR)
	$(GO) build $(GOFLAGS) $(LDFLAGS) -o $(BUILD_DIR)/$(BINARY_NAME) $(MAIN_PATH)
	@echo "${GREEN}Build complete: $(BUILD_DIR)/$(BINARY_NAME)${NC}"

## run: Run the application
run:
	@echo "${YELLOW}Running $(BINARY_NAME)...${NC}"
	$(GO) run $(MAIN_PATH)

## dev: Run in development mode with hot reload
dev:
	@echo "${YELLOW}Starting development server...${NC}"
	@if ! command -v air > /dev/null; then \
		echo "${YELLOW}Installing air for hot reload...${NC}"; \
		go install github.com/cosmtrek/air@latest; \
	fi
	ENV=development air

## test: Run all tests
test:
	@echo "${YELLOW}Running tests...${NC}"
	$(GO) test -v -cover -race ./...

## test-short: Run short tests
test-short:
	@echo "${YELLOW}Running short tests...${NC}"
	$(GO) test -short -v ./...

## test-coverage: Run tests with coverage report
test-coverage:
	@echo "${YELLOW}Running tests with coverage...${NC}"
	$(GO) test -v -coverprofile=coverage.out ./...
	$(GO) tool cover -html=coverage.out -o coverage.html
	@echo "${GREEN}Coverage report: coverage.html${NC}"

## benchmark: Run benchmarks
benchmark:
	@echo "${YELLOW}Running benchmarks...${NC}"
	$(GO) test -bench=. -benchmem ./...

## clean: Clean build artifacts
clean:
	@echo "${YELLOW}Cleaning...${NC}"
	@rm -rf $(BUILD_DIR)
	@rm -f coverage.out coverage.html
	@rm -f *.log
	@echo "${GREEN}Clean complete${NC}"

## install: Install the binary
install: build
	@echo "${YELLOW}Installing $(BINARY_NAME)...${NC}"
	@cp $(BUILD_DIR)/$(BINARY_NAME) $(GOPATH)/bin/
	@echo "${GREEN}Installed to $(GOPATH)/bin/$(BINARY_NAME)${NC}"

## fmt: Format code
fmt:
	@echo "${YELLOW}Formatting code...${NC}"
	$(GO) fmt ./...
	@echo "${GREEN}Formatting complete${NC}"

## vet: Run go vet
vet:
	@echo "${YELLOW}Running go vet...${NC}"
	$(GO) vet ./...
	@echo "${GREEN}Vet complete${NC}"

## lint: Run linter
lint:
	@echo "${YELLOW}Running linter...${NC}"
	@if ! command -v golangci-lint > /dev/null; then \
		echo "${YELLOW}Installing golangci-lint...${NC}"; \
		curl -sSfL https://raw.githubusercontent.com/golangci/golangci-lint/master/install.sh | sh -s -- -b $(go env GOPATH)/bin; \
	fi
	golangci-lint run

## migrate: Run database migrations
migrate:
	@echo "${YELLOW}Running migrations...${NC}"
	@if [ -f .env ]; then \
		export $$(cat .env | xargs) && \
		migrate -path migrations -database "$$DATABASE_URL" up; \
	else \
		echo "${RED}Error: .env file not found${NC}"; \
		exit 1; \
	fi

## migrate-down: Rollback last migration
migrate-down:
	@echo "${YELLOW}Rolling back migration...${NC}"
	@if [ -f .env ]; then \
		export $$(cat .env | xargs) && \
		migrate -path migrations -database "$$DATABASE_URL" down 1; \
	else \
		echo "${RED}Error: .env file not found${NC}"; \
		exit 1; \
	fi

## seed: Seed the database
seed:
	@echo "${YELLOW}Seeding database...${NC}"
	$(GO) run scripts/seed/main.go

## db-setup: Setup PostgreSQL with PostGIS
db-setup:
	@echo "${YELLOW}Setting up PostgreSQL with PostGIS...${NC}"
	@chmod +x ../scripts/database/setup-postgres.sh
	@../scripts/database/setup-postgres.sh dev

## db-test-setup: Setup test PostgreSQL with PostGIS
db-test-setup:
	@echo "${YELLOW}Setting up test PostgreSQL with PostGIS...${NC}"
	@chmod +x ../scripts/database/setup-postgres.sh
	@../scripts/database/setup-postgres.sh test

## db-stop: Stop all database containers
db-stop:
	@echo "${YELLOW}Stopping database containers...${NC}"
	@cd .. && docker-compose down

## test-with-db: Run tests with PostgreSQL
test-with-db: db-test-setup
	@echo "${YELLOW}Running tests with PostgreSQL...${NC}"
	@export $$(cat .env.test | xargs) && $(GO) test -v ./...
	@echo "${GREEN}Tests complete${NC}"

## docker: Build Docker image
docker:
	@echo "${YELLOW}Building Docker image...${NC}"
	docker build -t arxos-server:$(VERSION) .
	@echo "${GREEN}Docker image built: arxos-server:$(VERSION)${NC}"

## docker-run: Run in Docker
docker-run: docker
	@echo "${YELLOW}Running in Docker...${NC}"
	docker run -p 8080:8080 --env-file .env arxos-server:$(VERSION)

## prod: Build for production
prod:
	@echo "${YELLOW}Building for production...${NC}"
	CGO_ENABLED=0 GOOS=linux GOARCH=amd64 $(GO) build \
		-a -installsuffix cgo \
		$(LDFLAGS) \
		-o $(BUILD_DIR)/$(BINARY_NAME)-linux-amd64 \
		$(MAIN_PATH)
	@echo "${GREEN}Production build complete${NC}"

## generate: Generate code
generate:
	@echo "${YELLOW}Generating code...${NC}"
	$(GO) generate ./...
	@echo "${GREEN}Code generation complete${NC}"

## mod-update: Update all dependencies
mod-update:
	@echo "${YELLOW}Updating dependencies...${NC}"
	$(GO) get -u ./...
	$(GO) mod tidy
	@echo "${GREEN}Dependencies updated${NC}"

## security: Run security checks
security:
	@echo "${YELLOW}Running security checks...${NC}"
	@if ! command -v gosec > /dev/null; then \
		echo "${YELLOW}Installing gosec...${NC}"; \
		go install github.com/securego/gosec/v2/cmd/gosec@latest; \
	fi
	gosec ./...

# Default target
.DEFAULT_GOAL := help