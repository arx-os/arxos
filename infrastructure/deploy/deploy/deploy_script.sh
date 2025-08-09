#!/bin/bash

# Arxos Production Deployment Script
# Comprehensive deployment automation with staging, approval, and rollback capability

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
DEPLOYMENT_CONFIG="${SCRIPT_DIR}/deployment_config.yaml"
LOG_FILE="${SCRIPT_DIR}/deployment.log"
BACKUP_DIR="${SCRIPT_DIR}/backups"
MONITORING_LOG="${SCRIPT_DIR}/monitoring.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Deployment configuration
ENVIRONMENT="${ENVIRONMENT:-production}"
DEPLOYMENT_REGION="${DEPLOYMENT_REGION:-us-east-1}"
ROLLBACK_ENABLED="${ROLLBACK_ENABLED:-true}"
HEALTH_CHECK_TIMEOUT="${HEALTH_CHECK_TIMEOUT:-300}"
APPROVAL_REQUIRED="${APPROVAL_REQUIRED:-true}"
BLUE_GREEN_DEPLOYMENT="${BLUE_GREEN_DEPLOYMENT:-true}"
AUTO_ROLLBACK="${AUTO_ROLLBACK:-true}"
MONITORING_ENABLED="${MONITORING_ENABLED:-true}"

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

log_debug() {
    echo -e "${CYAN}[DEBUG]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

# Load configuration
load_config() {
    log_info "Loading deployment configuration..."

    if [[ ! -f "$DEPLOYMENT_CONFIG" ]]; then
        log_warning "Deployment configuration file not found: $DEPLOYMENT_CONFIG"
        log_info "Using default configuration"
    else
        # Parse YAML configuration
        export ENVIRONMENT=$(yq eval '.environment' "$DEPLOYMENT_CONFIG" 2>/dev/null || echo "$ENVIRONMENT")
        export DEPLOYMENT_REGION=$(yq eval '.region' "$DEPLOYMENT_CONFIG" 2>/dev/null || echo "$DEPLOYMENT_REGION")
        export ROLLBACK_ENABLED=$(yq eval '.rollback_enabled' "$DEPLOYMENT_CONFIG" 2>/dev/null || echo "$ROLLBACK_ENABLED")
        export HEALTH_CHECK_TIMEOUT=$(yq eval '.health_check_timeout' "$DEPLOYMENT_CONFIG" 2>/dev/null || echo "$HEALTH_CHECK_TIMEOUT")
        export APPROVAL_REQUIRED=$(yq eval '.approval_required' "$DEPLOYMENT_CONFIG" 2>/dev/null || echo "$APPROVAL_REQUIRED")
        export BLUE_GREEN_DEPLOYMENT=$(yq eval '.blue_green_deployment' "$DEPLOYMENT_CONFIG" 2>/dev/null || echo "$BLUE_GREEN_DEPLOYMENT")
        export AUTO_ROLLBACK=$(yq eval '.auto_rollback' "$DEPLOYMENT_CONFIG" 2>/dev/null || echo "$AUTO_ROLLBACK")
        export MONITORING_ENABLED=$(yq eval '.monitoring_enabled' "$DEPLOYMENT_CONFIG" 2>/dev/null || echo "$MONITORING_ENABLED")
    fi

    # Environment-specific configuration
    case "$ENVIRONMENT" in
        "staging")
            export KUBERNETES_NAMESPACE="arxos-staging"
            export DEPLOYMENT_URL="https://staging.arxos.com"
            export HEALTH_CHECK_ENDPOINTS=("/health" "/api/health" "/api/version")
            ;;
        "production")
            export KUBERNETES_NAMESPACE="arxos-production"
            export DEPLOYMENT_URL="https://app.arxos.com"
            export HEALTH_CHECK_ENDPOINTS=("/health" "/api/health" "/api/version" "/api/metrics")
            ;;
        *)
            log_error "Invalid environment: $ENVIRONMENT"
            exit 1
            ;;
    esac

    log_success "Configuration loaded successfully"
    log_debug "Environment: $ENVIRONMENT"
    log_debug "Region: $DEPLOYMENT_REGION"
    log_debug "Namespace: $KUBERNETES_NAMESPACE"
    log_debug "URL: $DEPLOYMENT_URL"
}

# Pre-deployment validation
pre_deployment_validation() {
    log_info "Starting pre-deployment validation..."

    # Check required tools
    local required_tools=("docker" "kubectl" "helm" "aws" "curl" "jq")
    for tool in "${required_tools[@]}"; do
        if ! command -v "$tool" &> /dev/null; then
            log_error "Required tool not found: $tool"
            exit 1
        fi
    done

    # Check environment variables
    local required_vars=("AWS_ACCESS_KEY_ID" "AWS_SECRET_ACCESS_KEY" "DOCKER_REGISTRY")
    for var in "${required_vars[@]}"; do
        if [[ -z "${!var:-}" ]]; then
            log_error "Required environment variable not set: $var"
            exit 1
        fi
    done

    # Check Kubernetes connectivity
    if ! kubectl cluster-info &> /dev/null; then
        log_error "Kubernetes cluster not accessible"
        exit 1
    fi

    # Check namespace exists
    if ! kubectl get namespace "$KUBERNETES_NAMESPACE" &> /dev/null; then
        log_error "Kubernetes namespace not found: $KUBERNETES_NAMESPACE"
        exit 1
    fi

    # Validate Docker images
    validate_docker_images

    # Check current deployment health
    check_current_deployment_health

    log_success "Pre-deployment validation completed"
}

# Validate Docker images
validate_docker_images() {
    log_info "Validating Docker images..."

    local images=(
        "arxos-backend:latest"
        "arxos-frontend:latest"
        "arxos-svg-parser:latest"
        "arxos-database:latest"
    )

    for image in "${images[@]}"; do
        if ! docker image inspect "$image" &> /dev/null; then
            log_error "Docker image not found: $image"
            exit 1
        fi

        # Check image size
        local image_size=$(docker image inspect "$image" --format='{{.Size}}')
        if [[ $image_size -gt 1073741824 ]]; then  # 1GB
            log_warning "Docker image is large: $image ($(numfmt --to=iec $image_size))"
        fi
    done

    log_success "Docker images validated successfully"
}

# Check current deployment health
check_current_deployment_health() {
    log_info "Checking current deployment health..."

    local max_attempts=10
    local attempt=1

    while [[ $attempt -le $max_attempts ]]; do
        if curl -f -s "$DEPLOYMENT_URL/health" > /dev/null; then
            log_success "Current deployment is healthy"
            return 0
        fi

        log_warning "Health check attempt $attempt/$max_attempts failed"
        sleep 5
        ((attempt++))
    done

    log_error "Current deployment is not healthy"
    return 1
}

# Create comprehensive backup
create_backup() {
    log_info "Creating comprehensive backup..."

    local backup_timestamp=$(date '+%Y%m%d_%H%M%S')
    local backup_path="$BACKUP_DIR/${ENVIRONMENT}_${backup_timestamp}"

    mkdir -p "$backup_path"

    # Backup Kubernetes resources
    log_info "Backing up Kubernetes resources..."
    kubectl get all -n "$KUBERNETES_NAMESPACE" -o yaml > "$backup_path/k8s_resources.yaml"
    kubectl get configmaps -n "$KUBERNETES_NAMESPACE" -o yaml > "$backup_path/configmaps.yaml"
    kubectl get secrets -n "$KUBERNETES_NAMESPACE" -o yaml > "$backup_path/secrets.yaml"
    kubectl get pvc -n "$KUBERNETES_NAMESPACE" -o yaml > "$backup_path/persistent_volumes.yaml"

    # Backup deployment history
    kubectl rollout history deployment/arxos-backend -n "$KUBERNETES_NAMESPACE" > "$backup_path/deployment_history.txt"

    # Backup database (if applicable)
    if [[ -n "${DATABASE_BACKUP_SCRIPT:-}" ]]; then
        log_info "Backing up database..."
        bash "$DATABASE_BACKUP_SCRIPT" "$backup_path"
    fi

    # Create backup manifest
    cat > "$backup_path/backup_manifest.json" << EOF
{
    "environment": "$ENVIRONMENT",
    "timestamp": "$(date -Iseconds)",
    "backup_path": "$backup_path",
    "kubernetes_resources": true,
    "database_backup": ${DATABASE_BACKUP_SCRIPT:+true},
    "deployment_history": true
}
EOF

    # Store backup location for rollback
    echo "$backup_path" > "${SCRIPT_DIR}/latest_backup.txt"

    log_success "Backup created: $backup_path"
}

# Blue-green deployment strategy
blue_green_deployment() {
    log_info "Starting blue-green deployment..."

    # Determine current and new colors
    local current_color=$(kubectl get deployment arxos-backend -n "$KUBERNETES_NAMESPACE" -o jsonpath='{.spec.template.metadata.labels.color}' 2>/dev/null || echo "blue")
    local new_color=$([[ "$current_color" == "blue" ]] && echo "green" || echo "blue")

    log_info "Current color: $current_color, New color: $new_color"

    # Deploy new version with new color
    kubectl apply -f "${SCRIPT_DIR}/k8s/${ENVIRONMENT}/" -l "color=$new_color"

    # Wait for new deployment to be ready
    kubectl rollout status deployment/arxos-backend -n "$KUBERNETES_NAMESPACE" --timeout=300s
    kubectl rollout status deployment/arxos-frontend -n "$KUBERNETES_NAMESPACE" --timeout=300s
    kubectl rollout status deployment/arxos-svg-parser -n "$KUBERNETES_NAMESPACE" --timeout=300s

    # Test new deployment
    test_deployment "$new_color"

    # Switch traffic to new deployment
    switch_traffic "$new_color"

    # Remove old deployment
    kubectl delete deployment -n "$KUBERNETES_NAMESPACE" -l "color=$current_color"

    log_success "Blue-green deployment completed"
}

# Test deployment
test_deployment() {
    local color="$1"
    log_info "Testing deployment with color: $color"

    # Wait for services to be ready
    sleep 60

    # Run health checks
    local max_attempts=30
    local attempt=1

    while [[ $attempt -le $max_attempts ]]; do
        local healthy=true

        for endpoint in "${HEALTH_CHECK_ENDPOINTS[@]}"; do
            if ! curl -f -s "$DEPLOYMENT_URL$endpoint" > /dev/null; then
                log_warning "Health check failed for $endpoint"
                healthy=false
                break
            fi
        done

        if [[ "$healthy" == "true" ]]; then
            log_success "Health checks passed"
            break
        fi

        log_warning "Health check attempt $attempt/$max_attempts failed"
        sleep 10
        ((attempt++))
    done

    if [[ $attempt -gt $max_attempts ]]; then
        log_error "Health checks failed after $max_attempts attempts"
        return 1
    fi

    # Run smoke tests
    run_smoke_tests

    # Run integration tests
    run_integration_tests

    log_success "Deployment testing completed"
}

# Switch traffic between blue/green deployments
switch_traffic() {
    local new_color="$1"
    log_info "Switching traffic to $new_color deployment..."

    # Update service selectors
    kubectl patch service arxos-backend-service -n "$KUBERNETES_NAMESPACE" \
        -p "{\"spec\":{\"selector\":{\"color\":\"$new_color\"}}}"

    kubectl patch service arxos-frontend-service -n "$KUBERNETES_NAMESPACE" \
        -p "{\"spec\":{\"selector\":{\"color\":\"$new_color\"}}}"

    # Wait for traffic to switch
    sleep 30

    log_success "Traffic switched to $new_color deployment"
}

# Run smoke tests
run_smoke_tests() {
    log_info "Running smoke tests..."

    local smoke_tests=(
        "curl -f -s $DEPLOYMENT_URL/api/health"
        "curl -f -s $DEPLOYMENT_URL/api/version"
        "curl -f -s $DEPLOYMENT_URL/api/metrics"
    )

    for test in "${smoke_tests[@]}"; do
        if ! eval "$test" > /dev/null; then
            log_error "Smoke test failed: $test"
            return 1
        fi
    done

    log_success "Smoke tests passed"
}

# Run integration tests
run_integration_tests() {
    log_info "Running integration tests..."

    if [[ -f "${SCRIPT_DIR}/tests/integration_tests.sh" ]]; then
        if ! bash "${SCRIPT_DIR}/tests/integration_tests.sh" "$DEPLOYMENT_URL"; then
            log_error "Integration tests failed"
            return 1
        fi
    fi

    log_success "Integration tests passed"
}

# Staging deployment
staging_deployment() {
    log_info "Starting staging deployment..."

    # Create backup
    create_backup

    # Deploy to staging environment
    if [[ "$BLUE_GREEN_DEPLOYMENT" == "true" ]]; then
        blue_green_deployment
    else
        # Standard deployment
        kubectl apply -f "${SCRIPT_DIR}/k8s/staging/"

        # Wait for deployment to be ready
        kubectl rollout status deployment/arxos-backend -n "$KUBERNETES_NAMESPACE" --timeout=300s
        kubectl rollout status deployment/arxos-frontend -n "$KUBERNETES_NAMESPACE" --timeout=300s
        kubectl rollout status deployment/arxos-svg-parser -n "$KUBERNETES_NAMESPACE" --timeout=300s

        # Test deployment
        test_deployment
    fi

    log_success "Staging deployment completed"
}

# Approval process
approval_process() {
    if [[ "$APPROVAL_REQUIRED" == "true" ]]; then
        log_info "Starting approval process..."

        # Send approval notification
        send_approval_notification

        # Wait for approval
        wait_for_approval

        log_success "Approval received"
    else
        log_info "Approval not required, proceeding with deployment"
    fi
}

# Send approval notification
send_approval_notification() {
    log_info "Sending approval notification..."

    # Send Slack notification
    if [[ -n "${SLACK_WEBHOOK_URL:-}" ]]; then
        local approval_message="{
            \"text\": \"🚀 Arxos Production Deployment Ready for Approval\",
            \"attachments\": [{
                \"fields\": [
                    {\"title\": \"Environment\", \"value\": \"$ENVIRONMENT\", \"short\": true},
                    {\"title\": \"Region\", \"value\": \"$DEPLOYMENT_REGION\", \"short\": true},
                    {\"title\": \"Deployment URL\", \"value\": \"$DEPLOYMENT_URL\", \"short\": false},
                    {\"title\": \"Backup Location\", \"value\": \"$(cat ${SCRIPT_DIR}/latest_backup.txt 2>/dev/null || echo 'N/A')\", \"short\": false}
                ],
                \"color\": \"warning\"
            }]
        }"

        curl -X POST -H 'Content-type: application/json' \
            --data "$approval_message" \
            "$SLACK_WEBHOOK_URL"
    fi

    # Send email notification
    if [[ -n "${EMAIL_RECIPIENTS:-}" ]]; then
        local email_subject="Arxos Production Deployment Approval Required"
        local email_body="Arxos production deployment is ready for approval.

Environment: $ENVIRONMENT
Region: $DEPLOYMENT_REGION
Deployment URL: $DEPLOYMENT_URL
Backup Location: $(cat ${SCRIPT_DIR}/latest_backup.txt 2>/dev/null || echo 'N/A')

Please review and approve the deployment."

        echo "$email_body" | mail -s "$email_subject" \
             -r "deploy@arxos.com" \
             "$EMAIL_RECIPIENTS"
    fi
}

# Wait for approval
wait_for_approval() {
    log_info "Waiting for approval..."

    # Check for approval file (simplified)
    local approval_file="${SCRIPT_DIR}/approval.txt"
    local max_wait_time=3600  # 1 hour
    local wait_time=0

    while [[ $wait_time -lt $max_wait_time ]]; do
        if [[ -f "$approval_file" ]]; then
            local approval_status=$(cat "$approval_file")
            if [[ "$approval_status" == "approved" ]]; then
                log_success "Approval received"
                rm -f "$approval_file"
                return 0
            elif [[ "$approval_status" == "rejected" ]]; then
                log_error "Deployment rejected"
                rm -f "$approval_file"
                exit 1
            fi
        fi

        sleep 30
        ((wait_time += 30))
        log_info "Waiting for approval... ($wait_time seconds elapsed)"
    done

    log_error "Approval timeout exceeded"
    exit 1
}

# Production deployment
production_deployment() {
    log_info "Starting production deployment..."

    # Create comprehensive backup
    create_backup

    # Deploy to production environment
    if [[ "$BLUE_GREEN_DEPLOYMENT" == "true" ]]; then
        blue_green_deployment
    else
        # Standard deployment
        kubectl apply -f "${SCRIPT_DIR}/k8s/production/"

        # Wait for deployment with extended timeout
        kubectl rollout status deployment/arxos-backend -n "$KUBERNETES_NAMESPACE" --timeout=600s
        kubectl rollout status deployment/arxos-frontend -n "$KUBERNETES_NAMESPACE" --timeout=600s
        kubectl rollout status deployment/arxos-svg-parser -n "$KUBERNETES_NAMESPACE" --timeout=600s

        # Test deployment
        test_deployment
    fi

    # Post-deployment monitoring
    if [[ "$MONITORING_ENABLED" == "true" ]]; then
        start_monitoring
    fi

    log_success "Production deployment completed"
}

# Start monitoring
start_monitoring() {
    log_info "Starting post-deployment monitoring..."

    # Monitor for 10 minutes
    local monitoring_duration=600
    local check_interval=30
    local checks=$((monitoring_duration / check_interval))

    for ((i=1; i<=checks; i++)); do
        log_info "Monitoring check $i/$checks"

        # Check health endpoints
        local healthy=true
        for endpoint in "${HEALTH_CHECK_ENDPOINTS[@]}"; do
            if ! curl -f -s "$DEPLOYMENT_URL$endpoint" > /dev/null; then
                log_warning "Health check failed for $endpoint"
                healthy=false
            fi
        done

        # Check resource usage
        local cpu_usage=$(kubectl top pods -n "$KUBERNETES_NAMESPACE" --no-headers | awk '{sum+=$2} END {print sum}')
        local memory_usage=$(kubectl top pods -n "$KUBERNETES_NAMESPACE" --no-headers | awk '{sum+=$3} END {print sum}')

        echo "$(date -Iseconds),$healthy,$cpu_usage,$memory_usage" >> "$MONITORING_LOG"

        if [[ "$healthy" == "false" ]]; then
            log_error "Deployment health check failed during monitoring"
            if [[ "$AUTO_ROLLBACK" == "true" ]]; then
                rollback_deployment
            fi
            return 1
        fi

        sleep $check_interval
    done

    log_success "Post-deployment monitoring completed"
}

# Rollback deployment
rollback_deployment() {
    log_info "Starting deployment rollback..."

    # Get backup location
    local backup_location=$(cat "${SCRIPT_DIR}/latest_backup.txt" 2>/dev/null)

    if [[ -z "$backup_location" || ! -d "$backup_location" ]]; then
        log_error "No backup found for rollback"
        return 1
    fi

    # Restore from backup
    log_info "Restoring from backup: $backup_location"

    # Restore Kubernetes resources
    kubectl apply -f "$backup_location/k8s_resources.yaml"

    # Restore database (if applicable)
    if [[ -f "$backup_location/database_backup.sql" ]]; then
        log_info "Restoring database..."
        if [[ -n "${DATABASE_RESTORE_SCRIPT:-}" ]]; then
            bash "$DATABASE_RESTORE_SCRIPT" "$backup_location/database_backup.sql"
        fi
    fi

    # Wait for rollback to complete
    kubectl rollout status deployment/arxos-backend -n "$KUBERNETES_NAMESPACE" --timeout=300s
    kubectl rollout status deployment/arxos-frontend -n "$KUBERNETES_NAMESPACE" --timeout=300s
    kubectl rollout status deployment/arxos-svg-parser -n "$KUBERNETES_NAMESPACE" --timeout=300s

    # Verify rollback
    test_deployment

    log_success "Rollback completed successfully"
}

# Send deployment notification
send_deployment_notification() {
    local status="$1"
    local message="$2"

    log_info "Sending deployment notification: $status"

    # Send Slack notification
    if [[ -n "${SLACK_WEBHOOK_URL:-}" ]]; then
        local color=$([[ "$status" == "completed" ]] && echo "good" || echo "danger")
        local notification_message="{
            \"text\": \"Deployment $status\",
            \"attachments\": [{
                \"fields\": [
                    {\"title\": \"Environment\", \"value\": \"$ENVIRONMENT\", \"short\": true},
                    {\"title\": \"Status\", \"value\": \"$status\", \"short\": true},
                    {\"title\": \"Message\", \"value\": \"$message\", \"short\": false}
                ],
                \"color\": \"$color\"
            }]
        }"

        curl -X POST -H 'Content-type: application/json' \
            --data "$notification_message" \
            "$SLACK_WEBHOOK_URL"
    fi

    # Send email notification
    if [[ -n "${EMAIL_RECIPIENTS:-}" ]]; then
        local email_subject="Arxos Deployment $status"
        local email_body="Deployment $status

Environment: $ENVIRONMENT
Status: $status
Message: $message
Timestamp: $(date -Iseconds)"

        echo "$email_body" | mail -s "$email_subject" \
             -r "deploy@arxos.com" \
             "$EMAIL_RECIPIENTS"
    fi
}

# Main deployment function
main() {
    log_info "Starting Arxos deployment..."

    # Load configuration
    load_config

    # Pre-deployment validation
    pre_deployment_validation

    # Staging deployment
    if [[ "$ENVIRONMENT" == "staging" ]]; then
        staging_deployment
        send_deployment_notification "completed" "Staging deployment completed successfully"
        log_success "Staging deployment completed"
        exit 0
    fi

    # Production deployment
    if [[ "$ENVIRONMENT" == "production" ]]; then
        # Approval process
        approval_process

        # Production deployment
        if production_deployment; then
            send_deployment_notification "completed" "Production deployment completed successfully"
            log_success "Production deployment completed"
            exit 0
        else
            send_deployment_notification "failed" "Production deployment failed"
            log_error "Production deployment failed"
            exit 1
        fi
    fi
}

# Handle script interruption
trap 'log_error "Deployment interrupted"; rollback_deployment; exit 1' INT TERM

# Run main function
main "$@"
