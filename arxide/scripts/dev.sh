#!/bin/bash

# ArxIDE Development Script
# This script automates common development tasks

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."

    local missing_deps=()

    if ! command_exists cargo; then
        missing_deps+=("Rust/Cargo")
    fi

    if ! command_exists npm; then
        missing_deps+=("Node.js/npm")
    fi

    if ! command_exists tauri; then
        missing_deps+=("Tauri CLI")
    fi

    if [ ${#missing_deps[@]} -ne 0 ]; then
        print_error "Missing dependencies: ${missing_deps[*]}"
        print_status "Please install the missing dependencies and try again."
        exit 1
    fi

    print_success "All prerequisites are installed"
}

# Function to clean build artifacts
clean() {
    print_status "Cleaning build artifacts..."

    # Clean Rust build artifacts
    if [ -d "src-tauri/target" ]; then
        rm -rf src-tauri/target
        print_success "Cleaned Rust build artifacts"
    fi

    # Clean Node.js build artifacts
    if [ -d "dist" ]; then
        rm -rf dist
        print_success "Cleaned Node.js build artifacts"
    fi

    if [ -d "node_modules" ]; then
        rm -rf node_modules
        print_success "Cleaned node_modules"
    fi

    print_success "Clean completed"
}

# Function to install dependencies
install() {
    print_status "Installing dependencies..."

    # Install Node.js dependencies
    if [ ! -d "node_modules" ]; then
        npm install
        print_success "Installed Node.js dependencies"
    else
        print_status "Node.js dependencies already installed"
    fi

    # Install Rust dependencies (this happens automatically on build)
    print_success "Dependencies installation completed"
}

# Function to run tests
test() {
    print_status "Running tests..."

    # Run Rust tests
    print_status "Running Rust tests..."
    cd src-tauri
    cargo test
    cd ..

    # Run frontend tests
    print_status "Running frontend tests..."
    npm test

    print_success "All tests completed"
}

# Function to build the application
build() {
    print_status "Building ArxIDE..."

    # Build frontend
    print_status "Building frontend..."
    npm run build:frontend

    # Build Tauri application
    print_status "Building Tauri application..."
    npm run build

    print_success "Build completed successfully"
}

# Function to run in development mode
dev() {
    print_status "Starting ArxIDE in development mode..."

    # Set logging level for better debugging
    export RUST_LOG=info

    # Start the development server
    npm run dev
}

# Function to run in preview mode
preview() {
    print_status "Starting ArxIDE in preview mode..."

    npm run preview
}

# Function to lint code
lint() {
    print_status "Running linters..."

    # Lint frontend code
    print_status "Linting frontend code..."
    npm run lint

    # Check TypeScript types
    print_status "Checking TypeScript types..."
    npm run type-check

    # Lint Rust code
    print_status "Linting Rust code..."
    cd src-tauri
    cargo clippy
    cd ..

    print_success "Linting completed"
}

# Function to format code
format() {
    print_status "Formatting code..."

    # Format frontend code
    print_status "Formatting frontend code..."
    npm run format

    # Format Rust code
    print_status "Formatting Rust code..."
    cd src-tauri
    cargo fmt
    cd ..

    print_success "Code formatting completed"
}

# Function to check for security vulnerabilities
security_check() {
    print_status "Checking for security vulnerabilities..."

    # Check npm dependencies
    print_status "Checking npm dependencies..."
    npm audit

    # Check Rust dependencies
    print_status "Checking Rust dependencies..."
    cd src-tauri
    cargo audit
    cd ..

    print_success "Security check completed"
}

# Function to show help
show_help() {
    echo "ArxIDE Development Script"
    echo ""
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  clean           Clean build artifacts"
    echo "  install         Install dependencies"
    echo "  test            Run all tests"
    echo "  build           Build the application"
    echo "  dev             Run in development mode"
    echo "  preview         Run in preview mode"
    echo "  lint            Run linters"
    echo "  format          Format code"
    echo "  security        Check for security vulnerabilities"
    echo "  help            Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 clean        # Clean build artifacts"
    echo "  $0 install      # Install dependencies"
    echo "  $0 test         # Run tests"
    echo "  $0 build        # Build application"
    echo "  $0 dev          # Start development server"
}

# Main script logic
main() {
    # Check prerequisites first
    check_prerequisites

    # Parse command line arguments
    case "${1:-help}" in
        clean)
            clean
            ;;
        install)
            install
            ;;
        test)
            test
            ;;
        build)
            build
            ;;
        dev)
            dev
            ;;
        preview)
            preview
            ;;
        lint)
            lint
            ;;
        format)
            format
            ;;
        security)
            security_check
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            print_error "Unknown command: $1"
            echo ""
            show_help
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"
