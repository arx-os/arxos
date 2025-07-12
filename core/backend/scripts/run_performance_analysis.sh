#!/bin/bash

# Database Performance Analysis Runner
# This script runs comprehensive database performance analysis for Arxos

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
ANALYSIS_SCRIPT="$SCRIPT_DIR/database_performance_analysis.sql"
GO_ANALYZER="$PROJECT_ROOT/cmd/database-performance/main.go"
MIGRATION_FILE="$PROJECT_ROOT/migrations/012_database_performance_optimization.sql"

# Default database connection parameters
DB_HOST=${DB_HOST:-"localhost"}
DB_PORT=${DB_PORT:-"5432"}
DB_USER=${DB_USER:-"postgres"}
DB_PASSWORD=${DB_PASSWORD:-""}
DB_NAME=${DB_NAME:-"arxos"}

# Function to print colored output
print_status() {
    local color=$1
    local message=$2
    echo -e "${color}[$(date '+%Y-%m-%d %H:%M:%S')] ${message}${NC}"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check database connection
check_db_connection() {
    print_status $BLUE "Checking database connection..."
    
    if ! command_exists psql; then
        print_status $RED "Error: psql command not found. Please install PostgreSQL client."
        exit 1
    fi
    
    # Test connection
    if ! PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "SELECT 1;" >/dev/null 2>&1; then
        print_status $RED "Error: Cannot connect to database. Please check your connection parameters:"
        echo "  Host: $DB_HOST"
        echo "  Port: $DB_PORT"
        echo "  User: $DB_USER"
        echo "  Database: $DB_NAME"
        echo "  Password: ${DB_PASSWORD:0:3}***"
        exit 1
    fi
    
    print_status $GREEN "Database connection successful!"
}

# Function to run SQL analysis
run_sql_analysis() {
    print_status $BLUE "Running SQL performance analysis..."
    
    if [ ! -f "$ANALYSIS_SCRIPT" ]; then
        print_status $RED "Error: Analysis script not found: $ANALYSIS_SCRIPT"
        exit 1
    fi
    
    # Create output directory
    OUTPUT_DIR="$SCRIPT_DIR/analysis_output"
    mkdir -p "$OUTPUT_DIR"
    
    # Run analysis and save output
    OUTPUT_FILE="$OUTPUT_DIR/sql_analysis_$(date '+%Y%m%d_%H%M%S').txt"
    
    print_status $YELLOW "Running SQL analysis (this may take a few minutes)..."
    
    if PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -f "$ANALYSIS_SCRIPT" > "$OUTPUT_FILE" 2>&1; then
        print_status $GREEN "SQL analysis completed successfully!"
        print_status $BLUE "Results saved to: $OUTPUT_FILE"
        
        # Show summary
        echo ""
        print_status $BLUE "=== SQL Analysis Summary ==="
        if grep -q "PERFORMANCE SUMMARY" "$OUTPUT_FILE"; then
            grep -A 10 "PERFORMANCE SUMMARY" "$OUTPUT_FILE"
        else
            print_status $YELLOW "No summary found in output. Check the full report."
        fi
    else
        print_status $RED "Error: SQL analysis failed. Check the output file: $OUTPUT_FILE"
        exit 1
    fi
}

# Function to run Go analyzer
run_go_analyzer() {
    print_status $BLUE "Running Go performance analyzer..."
    
    if [ ! -f "$GO_ANALYZER" ]; then
        print_status $RED "Error: Go analyzer not found: $GO_ANALYZER"
        return 1
    fi
    
    if ! command_exists go; then
        print_status $RED "Error: Go command not found. Please install Go."
        return 1
    fi
    
    # Set environment variables for Go analyzer
    export DB_HOST DB_PORT DB_USER DB_PASSWORD DB_NAME
    
    # Run Go analyzer
    cd "$(dirname "$GO_ANALYZER")"
    if go run main.go; then
        print_status $GREEN "Go analyzer completed successfully!"
    else
        print_status $RED "Error: Go analyzer failed."
        return 1
    fi
}

# Function to apply optimizations
apply_optimizations() {
    print_status $BLUE "Applying database optimizations..."
    
    if [ ! -f "$MIGRATION_FILE" ]; then
        print_status $RED "Error: Migration file not found: $MIGRATION_FILE"
        return 1
    fi
    
    print_status $YELLOW "Applying performance optimization migration..."
    
    if PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -f "$MIGRATION_FILE" >/dev/null 2>&1; then
        print_status $GREEN "Database optimizations applied successfully!"
    else
        print_status $RED "Error: Failed to apply database optimizations."
        return 1
    fi
}

# Function to show usage
show_usage() {
    echo "Usage: $0 [OPTIONS] [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  analyze     Run SQL performance analysis (default)"
    echo "  go-analyze  Run Go performance analyzer"
    echo "  optimize    Apply database optimizations"
    echo "  all         Run all analysis and optimizations"
    echo ""
    echo "Options:"
    echo "  -h, --help     Show this help message"
    echo "  --check-only   Only check database connection"
    echo ""
    echo "Environment Variables:"
    echo "  DB_HOST       Database host (default: localhost)"
    echo "  DB_PORT       Database port (default: 5432)"
    echo "  DB_USER       Database user (default: postgres)"
    echo "  DB_PASSWORD   Database password"
    echo "  DB_NAME       Database name (default: arxos)"
    echo ""
    echo "Examples:"
    echo "  $0 analyze"
    echo "  $0 all"
    echo "  DB_HOST=myhost DB_PASSWORD=mypass $0 analyze"
}

# Function to run all analysis
run_all_analysis() {
    print_status $BLUE "Running complete performance analysis and optimization..."
    
    check_db_connection
    run_sql_analysis
    run_go_analyzer
    apply_optimizations
    
    print_status $GREEN "Complete analysis and optimization finished!"
}

# Main script logic
main() {
    # Parse command line arguments
    COMMAND="analyze"
    CHECK_ONLY=false
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_usage
                exit 0
                ;;
            --check-only)
                CHECK_ONLY=true
                shift
                ;;
            analyze|go-analyze|optimize|all)
                COMMAND="$1"
                shift
                ;;
            *)
                print_status $RED "Unknown option: $1"
                show_usage
                exit 1
                ;;
        esac
    done
    
    # Show banner
    echo ""
    print_status $BLUE "=========================================="
    print_status $BLUE "  Arxos Database Performance Analysis"
    print_status $BLUE "=========================================="
    echo ""
    
    # Check database connection first
    check_db_connection
    
    if [ "$CHECK_ONLY" = true ]; then
        print_status $GREEN "Database connection check completed successfully!"
        exit 0
    fi
    
    # Run requested command
    case $COMMAND in
        analyze)
            run_sql_analysis
            ;;
        go-analyze)
            run_go_analyzer
            ;;
        optimize)
            apply_optimizations
            ;;
        all)
            run_all_analysis
            ;;
        *)
            print_status $RED "Unknown command: $COMMAND"
            show_usage
            exit 1
            ;;
    esac
    
    echo ""
    print_status $GREEN "Performance analysis completed successfully!"
}

# Run main function
main "$@" 