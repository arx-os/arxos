# Progressive Construction Pipeline Demo Makefile

# Build the demo
build:
	@echo "Building Progressive Construction Demo..."
	@go build -o progressive-construction-demo .

# Run the demo
demo: build
	@echo "Running Progressive Construction Pipeline Demo..."
	@mkdir -p demo output temp
	@./progressive-construction-demo

# Run tests
test:
	@echo "Running Progressive Construction Pipeline tests..."
	@go test -v .

# Run benchmarks
benchmark:
	@echo "Running Progressive Construction Pipeline benchmarks..."
	@go test -bench=. -benchmem .

# Clean up generated files
clean:
	@echo "Cleaning up demo files..."
	@rm -rf progressive-construction-demo output temp demo
	@rm -f *.json *.obj *.mtl

# Setup demo environment
setup:
	@echo "Setting up demo environment..."
	@mkdir -p demo output temp
	@echo "Demo directories created."
	@echo "Note: Place sample PDF files in the 'demo' directory to test with real data."

# Run full demo cycle
full-demo: clean setup build demo
	@echo "Full demo cycle completed!"

# Show help
help:
	@echo "Progressive Construction Pipeline Demo"
	@echo "====================================="
	@echo ""
	@echo "Available targets:"
	@echo "  build      - Build the demo executable"
	@echo "  demo       - Run the demo"
	@echo "  test       - Run unit tests"
	@echo "  benchmark  - Run performance benchmarks"
	@echo "  setup      - Create demo directories"
	@echo "  clean      - Clean up generated files"
	@echo "  full-demo  - Run complete demo cycle"
	@echo "  help       - Show this help message"

.PHONY: build demo test benchmark clean setup full-demo help