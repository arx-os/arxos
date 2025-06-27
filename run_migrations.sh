#!/bin/bash

# Database Migration and Seeding Script
# This script runs all migrations and seeds data for all environments

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

# Function to run migration for a specific environment
run_migrations_for_env() {
    local env=$1
    local db_host=$2
    local db_port=$3
    local db_name=$4
    local db_user=$5
    local db_password=$6
    
    print_status "Running migrations for environment: $env"
    
    # Create migrations directory if it doesn't exist
    mkdir -p migrations
    
    # Run each migration file in order
    for migration_file in migrations/*.sql; do
        if [ -f "$migration_file" ]; then
            print_status "Running migration: $(basename $migration_file)"
            
            # Use psql to run the migration
            PGPASSWORD=$db_password psql -h $db_host -p $db_port -U $db_user -d $db_name -f "$migration_file"
            
            if [ $? -eq 0 ]; then
                print_success "Migration $(basename $migration_file) completed successfully"
            else
                print_error "Migration $(basename $migration_file) failed"
                exit 1
            fi
        fi
    done
    
    print_success "All migrations completed for environment: $env"
}

# Function to seed data for a specific environment
seed_data_for_env() {
    local env=$1
    local db_host=$2
    local db_port=$3
    local db_name=$4
    local db_user=$5
    local db_password=$6
    
    print_status "Seeding data for environment: $env"
    
    # Run the seed migration
    if [ -f "migrations/011_seed_industry_benchmarks_and_sample_data.sql" ]; then
        print_status "Running seed data migration"
        
        PGPASSWORD=$db_password psql -h $db_host -p $db_port -U $db_user -d $db_name -f "migrations/011_seed_industry_benchmarks_and_sample_data.sql"
        
        if [ $? -eq 0 ]; then
            print_success "Seed data migration completed successfully"
        else
            print_error "Seed data migration failed"
            exit 1
        fi
    else
        print_warning "Seed data migration file not found"
    fi
    
    print_success "Data seeding completed for environment: $env"
}

# Function to verify database connection
verify_db_connection() {
    local db_host=$1
    local db_port=$2
    local db_name=$3
    local db_user=$4
    local db_password=$5
    
    print_status "Verifying database connection..."
    
    PGPASSWORD=$db_password psql -h $db_host -p $db_port -U $db_user -d $db_name -c "SELECT 1;" > /dev/null 2>&1
    
    if [ $? -eq 0 ]; then
        print_success "Database connection verified"
        return 0
    else
        print_error "Database connection failed"
        return 1
    fi
}

# Function to check if migrations table exists
check_migrations_table() {
    local db_host=$1
    local db_port=$2
    local db_name=$3
    local db_user=$4
    local db_password=$5
    
    print_status "Checking if migrations tracking table exists..."
    
    PGPASSWORD=$db_password psql -h $db_host -p $db_port -U $db_user -d $db_name -c "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'migrations');" | grep -q "t"
    
    if [ $? -eq 0 ]; then
        print_success "Migrations table exists"
        return 0
    else
        print_warning "Migrations table does not exist, creating it..."
        
        PGPASSWORD=$db_password psql -h $db_host -p $db_port -U $db_user -d $db_name -c "
        CREATE TABLE IF NOT EXISTS migrations (
            id SERIAL PRIMARY KEY,
            filename VARCHAR(255) NOT NULL UNIQUE,
            executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            checksum VARCHAR(64),
            execution_time_ms INTEGER
        );"
        
        if [ $? -eq 0 ]; then
            print_success "Migrations table created"
            return 0
        else
            print_error "Failed to create migrations table"
            return 1
        fi
    fi
}

# Function to check if migration has been run
is_migration_run() {
    local db_host=$1
    local db_port=$2
    local db_name=$3
    local db_user=$4
    local db_password=$5
    local filename=$6
    
    PGPASSWORD=$db_password psql -h $db_host -p $db_port -U $db_user -d $db_name -c "SELECT EXISTS (SELECT 1 FROM migrations WHERE filename = '$filename');" | grep -q "t"
    return $?
}

# Function to mark migration as run
mark_migration_run() {
    local db_host=$1
    local db_port=$2
    local db_name=$3
    local db_user=$4
    local db_password=$5
    local filename=$6
    local checksum=$7
    local execution_time=$8
    
    PGPASSWORD=$db_password psql -h $db_host -p $db_port -U $db_user -d $db_name -c "
    INSERT INTO migrations (filename, checksum, execution_time_ms) 
    VALUES ('$filename', '$checksum', $execution_time)
    ON CONFLICT (filename) DO NOTHING;"
}

# Main execution
main() {
    print_status "Starting database migration and seeding process"
    
    # Environment configurations
    # Development
    DEV_HOST=${DEV_DB_HOST:-"localhost"}
    DEV_PORT=${DEV_DB_PORT:-"5432"}
    DEV_NAME=${DEV_DB_NAME:-"arxos_dev"}
    DEV_USER=${DEV_DB_USER:-"arxos_user"}
    DEV_PASSWORD=${DEV_DB_PASSWORD:-"arxos_password"}
    
    # Staging
    STAGING_HOST=${STAGING_DB_HOST:-"staging-db.example.com"}
    STAGING_PORT=${STAGING_DB_PORT:-"5432"}
    STAGING_NAME=${STAGING_DB_NAME:-"arxos_staging"}
    STAGING_USER=${STAGING_DB_USER:-"arxos_user"}
    STAGING_PASSWORD=${STAGING_DB_PASSWORD:-"arxos_password"}
    
    # Production
    PROD_HOST=${PROD_DB_HOST:-"prod-db.example.com"}
    PROD_PORT=${PROD_DB_PORT:-"5432"}
    PROD_NAME=${PROD_DB_NAME:-"arxos_prod"}
    PROD_USER=${PROD_DB_USER:-"arxos_user"}
    PROD_PASSWORD=${PROD_DB_PASSWORD:-"arxos_password"}
    
    # Check command line arguments
    if [ "$1" = "dev" ]; then
        ENVIRONMENTS=("dev")
    elif [ "$1" = "staging" ]; then
        ENVIRONMENTS=("staging")
    elif [ "$1" = "prod" ]; then
        ENVIRONMENTS=("prod")
    elif [ "$1" = "all" ] || [ -z "$1" ]; then
        ENVIRONMENTS=("dev" "staging" "prod")
    else
        print_error "Invalid environment. Use: dev, staging, prod, or all"
        exit 1
    fi
    
    # Process each environment
    for env in "${ENVIRONMENTS[@]}"; do
        print_status "Processing environment: $env"
        
        # Set environment-specific variables
        case $env in
            "dev")
                DB_HOST=$DEV_HOST
                DB_PORT=$DEV_PORT
                DB_NAME=$DEV_NAME
                DB_USER=$DEV_USER
                DB_PASSWORD=$DEV_PASSWORD
                ;;
            "staging")
                DB_HOST=$STAGING_HOST
                DB_PORT=$STAGING_PORT
                DB_NAME=$STAGING_NAME
                DB_USER=$STAGING_USER
                DB_PASSWORD=$STAGING_PASSWORD
                ;;
            "prod")
                DB_HOST=$PROD_HOST
                DB_PORT=$PROD_PORT
                DB_NAME=$PROD_NAME
                DB_USER=$PROD_USER
                DB_PASSWORD=$PROD_PASSWORD
                ;;
        esac
        
        # Verify database connection
        if ! verify_db_connection $DB_HOST $DB_PORT $DB_NAME $DB_USER $DB_PASSWORD; then
            print_error "Cannot connect to $env database. Skipping..."
            continue
        fi
        
        # Check/create migrations table
        if ! check_migrations_table $DB_HOST $DB_PORT $DB_NAME $DB_USER $DB_PASSWORD; then
            print_error "Failed to setup migrations tracking for $env. Skipping..."
            continue
        fi
        
        # Run migrations
        run_migrations_for_env $env $DB_HOST $DB_PORT $DB_NAME $DB_USER $DB_PASSWORD
        
        # Seed data (only for dev and staging)
        if [ "$env" != "prod" ]; then
            seed_data_for_env $env $DB_HOST $DB_PORT $DB_NAME $DB_USER $DB_PASSWORD
        else
            print_warning "Skipping data seeding for production environment"
        fi
        
        print_success "Environment $env completed successfully"
        echo ""
    done
    
    print_success "All environments processed successfully!"
}

# Check if required tools are available
check_requirements() {
    print_status "Checking requirements..."
    
    if ! command -v psql &> /dev/null; then
        print_error "psql is not installed. Please install PostgreSQL client."
        exit 1
    fi
    
    print_success "Requirements check passed"
}

# Show usage
show_usage() {
    echo "Usage: $0 [dev|staging|prod|all]"
    echo ""
    echo "Environments:"
    echo "  dev      - Run migrations and seed data for development"
    echo "  staging  - Run migrations and seed data for staging"
    echo "  prod     - Run migrations only for production (no seeding)"
    echo "  all      - Run migrations and seed data for all environments"
    echo ""
    echo "Environment Variables:"
    echo "  DEV_DB_HOST, DEV_DB_PORT, DEV_DB_NAME, DEV_DB_USER, DEV_DB_PASSWORD"
    echo "  STAGING_DB_HOST, STAGING_DB_PORT, STAGING_DB_NAME, STAGING_DB_USER, STAGING_DB_PASSWORD"
    echo "  PROD_DB_HOST, PROD_DB_PORT, PROD_DB_NAME, PROD_DB_USER, PROD_DB_PASSWORD"
    echo ""
    echo "Example:"
    echo "  DEV_DB_PASSWORD=mypassword $0 dev"
}

# Check for help flag
if [ "$1" = "-h" ] || [ "$1" = "--help" ]; then
    show_usage
    exit 0
fi

# Check requirements and run main function
check_requirements
main "$@" 