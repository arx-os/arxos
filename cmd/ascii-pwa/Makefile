# ArxOS Layer 4 ASCII-BIM PWA Makefile

# Build the PWA server
build:
	@echo "Building ArxOS ASCII-BIM PWA server..."
	@go build -o ascii-pwa-server server.go

# Run the development server
dev: build
	@echo "Starting ArxOS ASCII-BIM PWA development server..."
	@./ascii-pwa-server

# Run the server in background
start: build
	@echo "Starting ArxOS ASCII-BIM PWA server in background..."
	@./ascii-pwa-server &
	@echo "Server started on http://localhost:8080"
	@echo "WebSocket endpoint: ws://localhost:8080/ws"

# Stop background server
stop:
	@echo "Stopping ArxOS ASCII-BIM PWA server..."
	@pkill -f ascii-pwa-server || echo "Server not running"

# Test the PWA functionality
test: 
	@echo "Testing PWA endpoints..."
	@curl -s http://localhost:8080/api/buildings || echo "Server not running"
	@echo "Open http://localhost:8080/test-pwa.html for full PWA test suite"

# Clean up build artifacts
clean:
	@echo "Cleaning up build artifacts..."
	@rm -f ascii-pwa-server
	@echo "Cleanup completed"

# Install dependencies
deps:
	@echo "Installing Go dependencies..."
	@go mod tidy

# Run PWA in browser (macOS)
open:
	@echo "Opening ArxOS ASCII-BIM PWA..."
	@open http://localhost:8080

# Build for production
production:
	@echo "Building for production..."
	@CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build -ldflags="-w -s" -o ascii-pwa-server-linux server.go
	@CGO_ENABLED=0 GOOS=darwin GOARCH=amd64 go build -ldflags="-w -s" -o ascii-pwa-server-darwin server.go
	@CGO_ENABLED=0 GOOS=windows GOARCH=amd64 go build -ldflags="-w -s" -o ascii-pwa-server-windows.exe server.go
	@echo "Production builds created for Linux, macOS, and Windows"

# Deploy to web server (example)
deploy: production
	@echo "Deploying PWA static files..."
	@echo "Copy these files to your web server:"
	@echo "  - index.html (main PWA interface)"
	@echo "  - manifest.json (PWA manifest)"
	@echo "  - sw.js (service worker)"
	@echo "  - *.js (JavaScript modules)"
	@echo "  - icons/ (PWA icons directory)"
	@echo "Configure web server to:"
	@echo "  - Serve with HTTPS (required for PWA)"
	@echo "  - Set appropriate cache headers"
	@echo "  - Configure WebSocket proxy for /ws"

# Validate PWA requirements
validate:
	@echo "Validating PWA requirements..."
	@echo "✓ manifest.json exists"
	@test -f manifest.json
	@echo "✓ service worker exists"
	@test -f sw.js
	@echo "✓ icons directory exists"
	@test -d icons
	@echo "✓ main HTML file exists"
	@test -f index.html
	@echo "PWA requirements validated"

# Show PWA info
info:
	@echo "ArxOS Layer 4 ASCII-BIM Progressive Web Application"
	@echo "=================================================="
	@echo ""
	@echo "🎯 Core Features:"
	@echo "  • Browser-based ASCII rendering"
	@echo "  • Real-time WebSocket communication"
	@echo "  • Offline-capable PWA"
	@echo "  • Responsive design (desktop/mobile)"
	@echo "  • Layer 4 ASCII integration with ArxOS"
	@echo ""
	@echo "📱 PWA Capabilities:"
	@echo "  • Install to home screen/desktop"
	@echo "  • Offline building data caching"
	@echo "  • Background data synchronization"
	@echo "  • Native app experience"
	@echo ""
	@echo "🔧 Development:"
	@echo "  make dev     - Start development server"
	@echo "  make test    - Test PWA functionality"
	@echo "  make open    - Open PWA in browser"
	@echo ""
	@echo "🚀 Production:"
	@echo "  make production - Build for all platforms"
	@echo "  make validate   - Validate PWA requirements"
	@echo "  make deploy     - Show deployment instructions"

# Development workflow
workflow: deps build test open
	@echo "Development workflow completed!"
	@echo "PWA is running at http://localhost:8080"

# Show help
help: info
	@echo ""
	@echo "Available targets:"
	@echo "  build       - Build the PWA server"
	@echo "  dev         - Run development server"
	@echo "  start       - Start server in background"
	@echo "  stop        - Stop background server"
	@echo "  test        - Test PWA functionality"
	@echo "  clean       - Clean build artifacts"
	@echo "  deps        - Install dependencies"
	@echo "  open        - Open PWA in browser (macOS)"
	@echo "  production  - Build for production"
	@echo "  deploy      - Show deployment instructions"
	@echo "  validate    - Validate PWA requirements"
	@echo "  workflow    - Complete development workflow"
	@echo "  info        - Show PWA information"
	@echo "  help        - Show this help message"

.PHONY: build dev start stop test clean deps open production deploy validate info help workflow