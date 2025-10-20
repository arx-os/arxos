#!/bin/bash

# ArxOS Restore Script
# Restores PostgreSQL database from backup

set -euo pipefail

# Configuration
BACKUP_DIR="${BACKUP_DIR:-/backups}"
POSTGRES_HOST="${POSTGRES_HOST:-localhost}"
POSTGRES_PORT="${POSTGRES_PORT:-5432}"
POSTGRES_DB="${POSTGRES_DB:-arxos}"
POSTGRES_USER="${POSTGRES_USER:-arxos}"
POSTGRES_PASSWORD="${POSTGRES_PASSWORD}"
S3_BUCKET="${BACKUP_S3_BUCKET:-}"
AWS_ACCESS_KEY_ID="${AWS_ACCESS_KEY_ID:-}"
AWS_SECRET_ACCESS_KEY="${AWS_SECRET_ACCESS_KEY:-}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging functions
log() {
    echo -e "${1}"
}

log_success() {
    log "${GREEN}✓ ${1}${NC}"
}

log_error() {
    log "${RED}✗ ${1}${NC}"
}

log_info() {
    log "${YELLOW}ℹ ${1}${NC}"
}

# Show usage
usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Options:
    -f, --file FILE          Backup file to restore from
    -s, --s3-key KEY         S3 key of backup to restore
    -l, --list               List available backups
    -d, --date DATE          Restore from specific date (YYYYMMDD)
    -y, --yes                Skip confirmation prompt
    -h, --help               Show this help message

Examples:
    $0 --list                                    # List available backups
    $0 --file /backups/arxos_backup_20240101.sql.gz  # Restore from local file
    $0 --s3-key backups/20240101/arxos_backup.sql.gz # Restore from S3
    $0 --date 20240101                          # Restore from date

EOF
    exit 0
}

# List available backups
list_backups() {
    log_info "Available backups:"

    # List local backups
    log_info "\nLocal backups:"
    if [ -d "${BACKUP_DIR}" ]; then
        ls -lh "${BACKUP_DIR}"/arxos_backup_*.sql.gz 2>/dev/null | awk '{print $9, $5}' || log_info "No local backups found"
    fi

    # List S3 backups if configured
    if [ -n "${S3_BUCKET}" ]; then
        log_info "\nS3 backups:"
        aws s3 ls "s3://${S3_BUCKET}/backups/" --recursive | grep ".sql.gz" || log_info "No S3 backups found"
    fi
}

# Download backup from S3
download_from_s3() {
    local s3_key="${1}"
    local local_file="${BACKUP_DIR}/$(basename "${s3_key}")"

    log_info "Downloading backup from S3..."

    # Configure AWS CLI
    export AWS_ACCESS_KEY_ID="${AWS_ACCESS_KEY_ID}"
    export AWS_SECRET_ACCESS_KEY="${AWS_SECRET_ACCESS_KEY}"

    # Download from S3
    if aws s3 cp "s3://${S3_BUCKET}/${s3_key}" "${local_file}"; then
        log_success "Downloaded backup from S3"
        echo "${local_file}"
    else
        log_error "Failed to download backup from S3"
        exit 1
    fi
}

# Find backup by date
find_backup_by_date() {
    local date="${1}"

    # Look for local backup first
    local local_backup="${BACKUP_DIR}/arxos_backup_${date}_*.sql.gz"
    if ls ${local_backup} 1> /dev/null 2>&1; then
        echo "$(ls -t ${local_backup} | head -1)"
        return
    fi

    # Look in S3 if configured
    if [ -n "${S3_BUCKET}" ]; then
        local s3_key=$(aws s3 ls "s3://${S3_BUCKET}/backups/" --recursive | grep "${date}" | grep ".sql.gz" | head -1 | awk '{print $4}')
        if [ -n "${s3_key}" ]; then
            download_from_s3 "${s3_key}"
            return
        fi
    fi

    log_error "No backup found for date: ${date}"
    exit 1
}

# Verify backup file
verify_backup_file() {
    local backup_file="${1}"

    if [ ! -f "${backup_file}" ]; then
        log_error "Backup file not found: ${backup_file}"
        exit 1
    fi

    # Check if it's a valid gzip file
    if ! gunzip -t "${backup_file}" 2>/dev/null; then
        log_error "Invalid or corrupted backup file: ${backup_file}"
        exit 1
    fi

    log_success "Backup file verified: ${backup_file}"
}

# Create temporary database for validation
create_temp_database() {
    local temp_db="arxos_restore_temp_$(date +%s)"

    log_info "Creating temporary database for validation..."

    export PGPASSWORD="${POSTGRES_PASSWORD}"
    createdb -h "${POSTGRES_HOST}" -p "${POSTGRES_PORT}" -U "${POSTGRES_USER}" "${temp_db}"

    echo "${temp_db}"
}

# Drop temporary database
drop_temp_database() {
    local temp_db="${1}"

    log_info "Dropping temporary database..."

    export PGPASSWORD="${POSTGRES_PASSWORD}"
    dropdb -h "${POSTGRES_HOST}" -p "${POSTGRES_PORT}" -U "${POSTGRES_USER}" "${temp_db}" 2>/dev/null || true
}

# Validate restore in temporary database
validate_restore() {
    local backup_file="${1}"
    local temp_db=$(create_temp_database)

    log_info "Validating restore in temporary database..."

    # Restore to temporary database
    export PGPASSWORD="${POSTGRES_PASSWORD}"
    if gunzip -c "${backup_file}" | pg_restore \
        -h "${POSTGRES_HOST}" \
        -p "${POSTGRES_PORT}" \
        -U "${POSTGRES_USER}" \
        -d "${temp_db}" \
        --no-owner \
        --no-privileges \
        --verbose 2>/dev/null; then

        # Run basic validation queries
        local table_count=$(psql -h "${POSTGRES_HOST}" -p "${POSTGRES_PORT}" -U "${POSTGRES_USER}" -d "${temp_db}" -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';")

        if [ "${table_count}" -gt 0 ]; then
            log_success "Validation successful: ${table_count} tables found"
            drop_temp_database "${temp_db}"
            return 0
        else
            log_error "Validation failed: No tables found in restored database"
            drop_temp_database "${temp_db}"
            return 1
        fi
    else
        log_error "Validation failed: Restore process failed"
        drop_temp_database "${temp_db}"
        return 1
    fi
}

# Perform restore
perform_restore() {
    local backup_file="${1}"
    local skip_confirmation="${2:-false}"

    log_info "========================================="
    log_info "ArxOS Database Restore"
    log_info "========================================="
    log_info "Backup file: ${backup_file}"
    log_info "Target database: ${POSTGRES_DB}@${POSTGRES_HOST}:${POSTGRES_PORT}"

    # Confirm restore
    if [ "${skip_confirmation}" != "true" ]; then
        log_info ""
        log_info "${RED}WARNING: This will REPLACE all data in the database!${NC}"
        read -p "Are you sure you want to continue? (yes/no): " confirmation

        if [ "${confirmation}" != "yes" ]; then
            log_info "Restore cancelled"
            exit 0
        fi
    fi

    # Verify backup file
    verify_backup_file "${backup_file}"

    # Validate restore
    if ! validate_restore "${backup_file}"; then
        log_error "Restore validation failed"
        exit 1
    fi

    # Drop existing database
    log_info "Dropping existing database..."
    export PGPASSWORD="${POSTGRES_PASSWORD}"
    dropdb -h "${POSTGRES_HOST}" -p "${POSTGRES_PORT}" -U "${POSTGRES_USER}" --if-exists "${POSTGRES_DB}"

    # Create new database
    log_info "Creating new database..."
    createdb -h "${POSTGRES_HOST}" -p "${POSTGRES_PORT}" -U "${POSTGRES_USER}" "${POSTGRES_DB}"

    # Enable PostGIS extension
    log_info "Enabling PostGIS extension..."
    psql -h "${POSTGRES_HOST}" -p "${POSTGRES_PORT}" -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" -c "CREATE EXTENSION IF NOT EXISTS postgis;"

    # Restore database
    log_info "Restoring database..."
    if gunzip -c "${backup_file}" | pg_restore \
        -h "${POSTGRES_HOST}" \
        -p "${POSTGRES_PORT}" \
        -U "${POSTGRES_USER}" \
        -d "${POSTGRES_DB}" \
        --no-owner \
        --no-privileges \
        --verbose; then

        log_success "Database restored successfully"

        # Run post-restore checks
        log_info "Running post-restore checks..."
        local table_count=$(psql -h "${POSTGRES_HOST}" -p "${POSTGRES_PORT}" -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';")
        local building_count=$(psql -h "${POSTGRES_HOST}" -p "${POSTGRES_PORT}" -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" -t -c "SELECT COUNT(*) FROM buildings;" 2>/dev/null || echo "0")
        local equipment_count=$(psql -h "${POSTGRES_HOST}" -p "${POSTGRES_PORT}" -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" -t -c "SELECT COUNT(*) FROM equipment;" 2>/dev/null || echo "0")

        log_info "Tables: ${table_count}"
        log_info "Buildings: ${building_count}"
        log_info "Equipment: ${equipment_count}"

        log_info "========================================="
        log_success "Restore completed successfully"
        log_info "========================================="
    else
        log_error "Restore failed"
        exit 1
    fi
}

# Parse command line arguments
BACKUP_FILE=""
S3_KEY=""
DATE=""
SKIP_CONFIRMATION="false"

while [[ $# -gt 0 ]]; do
    case $1 in
        -f|--file)
            BACKUP_FILE="$2"
            shift 2
            ;;
        -s|--s3-key)
            S3_KEY="$2"
            shift 2
            ;;
        -l|--list)
            list_backups
            exit 0
            ;;
        -d|--date)
            DATE="$2"
            shift 2
            ;;
        -y|--yes)
            SKIP_CONFIRMATION="true"
            shift
            ;;
        -h|--help)
            usage
            ;;
        *)
            log_error "Unknown option: $1"
            usage
            ;;
    esac
done

# Determine backup file to restore
if [ -n "${BACKUP_FILE}" ]; then
    # Use specified file
    RESTORE_FILE="${BACKUP_FILE}"
elif [ -n "${S3_KEY}" ]; then
    # Download from S3
    RESTORE_FILE=$(download_from_s3 "${S3_KEY}")
elif [ -n "${DATE}" ]; then
    # Find by date
    RESTORE_FILE=$(find_backup_by_date "${DATE}")
else
    log_error "No backup specified. Use --file, --s3-key, or --date option."
    usage
fi

# Perform restore
perform_restore "${RESTORE_FILE}" "${SKIP_CONFIRMATION}"