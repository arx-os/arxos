#!/bin/bash

# ArxOS Backup Script
# Performs automated backups of PostgreSQL database with PostGIS data

set -euo pipefail

# Configuration
BACKUP_DIR="${BACKUP_DIR:-/backups}"
POSTGRES_HOST="${POSTGRES_HOST:-localhost}"
POSTGRES_PORT="${POSTGRES_PORT:-5432}"
POSTGRES_DB="${POSTGRES_DB:-arxos}"
POSTGRES_USER="${POSTGRES_USER:-arxos}"
POSTGRES_PASSWORD="${POSTGRES_PASSWORD}"
BACKUP_RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-7}"
BACKUP_SCHEDULE="${BACKUP_SCHEDULE:-0 2 * * *}"
S3_BUCKET="${BACKUP_S3_BUCKET:-}"
AWS_ACCESS_KEY_ID="${AWS_ACCESS_KEY_ID:-}"
AWS_SECRET_ACCESS_KEY="${AWS_SECRET_ACCESS_KEY:-}"

# Timestamp for backup file
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="${BACKUP_DIR}/arxos_backup_${TIMESTAMP}.sql.gz"
BACKUP_LOG="${BACKUP_DIR}/backup_${TIMESTAMP}.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${1}" | tee -a "${BACKUP_LOG}"
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

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."

    # Check if pg_dump is available
    if ! command -v pg_dump &> /dev/null; then
        log_error "pg_dump not found. Please install postgresql-client."
        exit 1
    fi

    # Check if backup directory exists
    if [ ! -d "${BACKUP_DIR}" ]; then
        log_info "Creating backup directory: ${BACKUP_DIR}"
        mkdir -p "${BACKUP_DIR}"
    fi

    # Check database connectivity
    export PGPASSWORD="${POSTGRES_PASSWORD}"
    if ! pg_isready -h "${POSTGRES_HOST}" -p "${POSTGRES_PORT}" -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" &> /dev/null; then
        log_error "Cannot connect to PostgreSQL database"
        exit 1
    fi

    log_success "Prerequisites check completed"
}

# Perform database backup
perform_backup() {
    log_info "Starting database backup..."
    log_info "Database: ${POSTGRES_DB}@${POSTGRES_HOST}:${POSTGRES_PORT}"

    # Set PostgreSQL password
    export PGPASSWORD="${POSTGRES_PASSWORD}"

    # Perform pg_dump with PostGIS support
    if pg_dump \
        -h "${POSTGRES_HOST}" \
        -p "${POSTGRES_PORT}" \
        -U "${POSTGRES_USER}" \
        -d "${POSTGRES_DB}" \
        --verbose \
        --no-owner \
        --no-privileges \
        --format=custom \
        --compress=9 \
        --file="${BACKUP_FILE%.gz}" \
        2>> "${BACKUP_LOG}"; then

        # Compress the backup
        log_info "Compressing backup..."
        gzip "${BACKUP_FILE%.gz}"

        # Get file size
        BACKUP_SIZE=$(du -h "${BACKUP_FILE}" | cut -f1)
        log_success "Backup completed successfully (${BACKUP_SIZE})"
    else
        log_error "Backup failed"
        exit 1
    fi
}

# Upload to S3 if configured
upload_to_s3() {
    if [ -z "${S3_BUCKET}" ]; then
        log_info "S3 upload not configured, skipping..."
        return
    fi

    log_info "Uploading backup to S3..."

    # Configure AWS CLI
    export AWS_ACCESS_KEY_ID="${AWS_ACCESS_KEY_ID}"
    export AWS_SECRET_ACCESS_KEY="${AWS_SECRET_ACCESS_KEY}"

    # Upload to S3
    if aws s3 cp "${BACKUP_FILE}" "s3://${S3_BUCKET}/backups/${TIMESTAMP}/" \
        --storage-class STANDARD_IA \
        --metadata "timestamp=${TIMESTAMP},database=${POSTGRES_DB}"; then
        log_success "Backup uploaded to S3: s3://${S3_BUCKET}/backups/${TIMESTAMP}/"
    else
        log_error "Failed to upload backup to S3"
    fi
}

# Clean up old backups
cleanup_old_backups() {
    log_info "Cleaning up old backups..."

    # Local cleanup
    find "${BACKUP_DIR}" -name "arxos_backup_*.sql.gz" -type f -mtime +${BACKUP_RETENTION_DAYS} -delete
    find "${BACKUP_DIR}" -name "backup_*.log" -type f -mtime +${BACKUP_RETENTION_DAYS} -delete

    # S3 cleanup if configured
    if [ -n "${S3_BUCKET}" ]; then
        log_info "Cleaning up old S3 backups..."
        aws s3 ls "s3://${S3_BUCKET}/backups/" | while read -r line; do
            BACKUP_DATE=$(echo "$line" | awk '{print $1}')
            DAYS_OLD=$(( ($(date +%s) - $(date -d "${BACKUP_DATE}" +%s)) / 86400 ))

            if [ "${DAYS_OLD}" -gt "${BACKUP_RETENTION_DAYS}" ]; then
                BACKUP_KEY=$(echo "$line" | awk '{print $4}')
                aws s3 rm "s3://${S3_BUCKET}/backups/${BACKUP_KEY}" --recursive
                log_info "Deleted old backup: ${BACKUP_KEY}"
            fi
        done
    fi

    log_success "Cleanup completed"
}

# Verify backup integrity
verify_backup() {
    log_info "Verifying backup integrity..."

    # Test if the backup file can be read
    if gunzip -t "${BACKUP_FILE}" 2>> "${BACKUP_LOG}"; then
        log_success "Backup file integrity verified"
    else
        log_error "Backup file is corrupted"
        exit 1
    fi
}

# Send notification (can be extended for Slack, email, etc.)
send_notification() {
    local status="${1}"
    local message="${2}"

    # Log the notification
    log_info "Notification: ${status} - ${message}"

    # TODO: Implement actual notification sending
    # Example: Send to webhook
    # curl -X POST "${WEBHOOK_URL}" \
    #     -H "Content-Type: application/json" \
    #     -d "{\"status\":\"${status}\",\"message\":\"${message}\"}"
}

# Main execution
main() {
    log_info "========================================="
    log_info "ArxOS Backup Script"
    log_info "Started at: $(date)"
    log_info "========================================="

    # Run backup steps
    check_prerequisites
    perform_backup
    verify_backup
    upload_to_s3
    cleanup_old_backups

    log_info "========================================="
    log_success "Backup process completed successfully"
    log_info "Ended at: $(date)"
    log_info "========================================="

    # Send success notification
    send_notification "SUCCESS" "ArxOS backup completed successfully at ${TIMESTAMP}"
}

# Handle scheduled execution
if [ "${1:-}" = "schedule" ]; then
    log_info "Setting up scheduled backup with cron pattern: ${BACKUP_SCHEDULE}"

    # Install cron job
    echo "${BACKUP_SCHEDULE} /backup/backup.sh" | crontab -

    # Keep container running
    crond -f
else
    # Run backup immediately
    main
fi