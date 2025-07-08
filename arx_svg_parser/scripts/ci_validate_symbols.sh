#!/bin/bash

# CI/CD Symbol Validation Script
# Validates all JSON symbol files against the defined schema

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
SCHEMA_PATH="$PROJECT_ROOT/../arx-symbol-library/schemas/symbol.schema.json"
SYMBOLS_PATH="$PROJECT_ROOT/../arx-symbol-library"
PYTHON_SCRIPT="$SCRIPT_DIR/validate_symbols.py"

# Function to print colored output
print_status() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to install dependencies
install_dependencies() {
    print_status $YELLOW "Installing Python dependencies..."
    
    if ! command_exists python3; then
        print_status $RED "Python 3 is not installed"
        exit 1
    fi
    
    # Install jsonschema if not available
    if ! python3 -c "import jsonschema" 2>/dev/null; then
        print_status $YELLOW "Installing jsonschema..."
        pip3 install jsonschema
    fi
    
    print_status $GREEN "✓ Dependencies installed"
}

# Function to validate paths
validate_paths() {
    print_status $YELLOW "Validating paths..."
    
    if [[ ! -f "$SCHEMA_PATH" ]]; then
        print_status $RED "❌ Schema file not found: $SCHEMA_PATH"
        exit 1
    fi
    
    if [[ ! -d "$SYMBOLS_PATH" ]]; then
        print_status $RED "❌ Symbols directory not found: $SYMBOLS_PATH"
        exit 1
    fi
    
    if [[ ! -f "$PYTHON_SCRIPT" ]]; then
        print_status $RED "❌ Validation script not found: $PYTHON_SCRIPT"
        exit 1
    fi
    
    print_status $GREEN "✓ All paths validated"
}

# Function to run validation
run_validation() {
    print_status $YELLOW "Running symbol validation..."
    
    cd "$PROJECT_ROOT"
    
    # Run the Python validation script
    python3 "$PYTHON_SCRIPT" \
        --schema-path "$SCHEMA_PATH" \
        --symbols-path "$SYMBOLS_PATH" \
        --verbose \
        --exit-code
    
    if [[ $? -eq 0 ]]; then
        print_status $GREEN "✓ All symbol files are valid!"
    else
        print_status $RED "❌ Symbol validation failed"
        exit 1
    fi
}

# Function to generate report
generate_report() {
    print_status $YELLOW "Generating validation report..."
    
    cd "$PROJECT_ROOT"
    
    python3 "$PYTHON_SCRIPT" \
        --schema-path "$SCHEMA_PATH" \
        --symbols-path "$SYMBOLS_PATH" \
        --report "validation_report.json"
    
    if [[ -f "validation_report.json" ]]; then
        print_status $GREEN "✓ Validation report generated: validation_report.json"
    else
        print_status $RED "❌ Failed to generate validation report"
    fi
}

# Function to display usage
show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -h, --help          Show this help message"
    echo "  --install-deps       Install dependencies only"
    echo "  --validate-paths     Validate paths only"
    echo "  --report             Generate validation report"
    echo "  --schema-path PATH   Custom schema path"
    echo "  --symbols-path PATH  Custom symbols path"
    echo ""
    echo "Examples:"
    echo "  $0                    # Run full validation"
    echo "  $0 --install-deps     # Install dependencies"
    echo "  $0 --report           # Generate report only"
    echo "  $0 --schema-path /custom/schema.json"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_usage
            exit 0
            ;;
        --install-deps)
            install_dependencies
            exit 0
            ;;
        --validate-paths)
            validate_paths
            exit 0
            ;;
        --report)
            GENERATE_REPORT=true
            shift
            ;;
        --schema-path)
            SCHEMA_PATH="$2"
            shift 2
            ;;
        --symbols-path)
            SYMBOLS_PATH="$2"
            shift 2
            ;;
        *)
            print_status $RED "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Main execution
print_status $GREEN "🚀 Starting symbol validation..."

# Install dependencies
install_dependencies

# Validate paths
validate_paths

# Run validation
run_validation

# Generate report if requested
if [[ "$GENERATE_REPORT" == "true" ]]; then
    generate_report
fi

print_status $GREEN "✅ Symbol validation completed successfully!" 