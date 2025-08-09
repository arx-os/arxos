#!/bin/bash

# Arxos Production Environment Setup Script
# This script sets up the complete production environment for the Arxos pipeline

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
ENVIRONMENT=${1:-"production"}
DB_HOST=${2:-"localhost"}
DB_PORT=${3:-"5432"}
DB_NAME=${4:-"arxos_prod"}
DB_USER=${5:-"arxos_user"}
DB_PASSWORD=${6:-"arxos_password"}

# Functions
print_header() {
    echo -e "${BLUE}================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}================================${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Check if running as root
check_root() {
    if [[ $EUID -eq 0 ]]; then
        print_warning "This script should not be run as root"
        read -p "Continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
}

# Setup environment variables
setup_environment() {
    print_header "Setting Up Environment Variables"

    # Create .env file for production
    cat > .env.production << EOF
# Arxos Production Environment Configuration

# Database Configuration
DATABASE_URL=postgresql://${DB_USER}:${DB_PASSWORD}@${DB_HOST}:${DB_PORT}/${DB_NAME}
DB_HOST=${DB_HOST}
DB_PORT=${DB_PORT}
DB_NAME=${DB_NAME}
DB_USER=${DB_USER}
DB_PASSWORD=${DB_PASSWORD}

# Application Configuration
ENVIRONMENT=${ENVIRONMENT}
LOG_LEVEL=INFO
DEBUG=false

# Pipeline Configuration
PIPELINE_MAX_EXECUTIONS=100
PIPELINE_TIMEOUT=300
PIPELINE_RETRY_ATTEMPTS=3

# Monitoring Configuration
METRICS_ENABLED=true
HEALTH_CHECK_INTERVAL=60
ALERT_EMAIL=admin@arxos.com

# Security Configuration
SECRET_KEY=$(openssl rand -hex 32)
JWT_SECRET=$(openssl rand -hex 32)
ENCRYPTION_KEY=$(openssl rand -hex 32)

# Backup Configuration
BACKUP_RETENTION_DAYS=30
BACKUP_SCHEDULE="0 2 * * *"

# Analytics Configuration
ANALYTICS_ENABLED=true
ANALYTICS_RETENTION_DAYS=90
PERFORMANCE_MONITORING=true
EOF

    print_success "Environment variables configured"
}

# Setup database
setup_database() {
    print_header "Setting Up Database"

    # Check if PostgreSQL is available
    if ! command -v psql &> /dev/null; then
        print_error "PostgreSQL is not installed"
        print_info "Please install PostgreSQL and try again"
        exit 1
    fi

    # Create database and user
    print_info "Creating database and user..."

    # Create user (if it doesn't exist)
    psql -h $DB_HOST -p $DB_PORT -U postgres -c "CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';" || true

    # Create database
    psql -h $DB_HOST -p $DB_PORT -U postgres -c "CREATE DATABASE $DB_NAME OWNER $DB_USER;" || true

    # Grant privileges
    psql -h $DB_HOST -p $DB_PORT -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;"

    # Run migrations
    print_info "Running database migrations..."
    cd arx-backend

    # Apply pipeline migrations
    if [[ -f "migrations/004_create_pipeline_tables.sql" ]]; then
        psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -f migrations/004_create_pipeline_tables.sql
        print_success "Pipeline tables created"
    fi

    cd ..
    print_success "Database setup completed"
}

# Setup monitoring
setup_monitoring() {
    print_header "Setting Up Monitoring"

    # Create monitoring configuration
    cat > monitoring_config.json << EOF
{
    "enabled": true,
    "metrics_collection": {
        "cpu_usage": true,
        "memory_usage": true,
        "disk_usage": true,
        "pipeline_executions": true,
        "error_rates": true
    },
    "alerting": {
        "cpu_threshold": 80,
        "memory_threshold": 85,
        "disk_threshold": 90,
        "error_rate_threshold": 5
    },
    "retention": {
        "metrics_days": 30,
        "logs_days": 90,
        "backups_days": 30
    }
}
EOF

    # Create log directories
    mkdir -p logs/{pipeline,monitoring,analytics}
    mkdir -p backups/{full,incremental,schemas}

    print_success "Monitoring setup completed"
}

# Setup security
setup_security() {
    print_header "Setting Up Security"

    # Create security configuration
    cat > security_config.json << EOF
{
    "authentication": {
        "jwt_secret": "$(openssl rand -hex 32)",
        "jwt_expiry": 3600,
        "refresh_token_expiry": 86400
    },
    "encryption": {
        "algorithm": "AES-256-GCM",
        "key_rotation_days": 90
    },
    "access_control": {
        "max_login_attempts": 5,
        "lockout_duration": 300,
        "session_timeout": 1800
    },
    "audit_logging": {
        "enabled": true,
        "retention_days": 365,
        "log_level": "INFO"
    }
}
EOF

    # Set proper file permissions
    chmod 600 .env.production
    chmod 600 security_config.json
    chmod 600 monitoring_config.json

    print_success "Security setup completed"
}

# Setup backup automation
setup_backup_automation() {
    print_header "Setting Up Backup Automation"

    # Create backup script
    cat > scripts/backup_pipeline.sh << 'EOF'
#!/bin/bash

# Pipeline Backup Script
BACKUP_DIR="backups/$(date +%Y%m%d)"
mkdir -p $BACKUP_DIR

# Database backup
pg_dump -h $DB_HOST -p $DB_PORT -U $DB_USER $DB_NAME > $BACKUP_DIR/database_backup.sql

# File system backup
tar -czf $BACKUP_DIR/pipeline_files.tar.gz \
    schemas/ \
    arx-symbol-library/ \
    svgx_engine/behavior/ \
    docs/systems/

# Cleanup old backups (keep last 30 days)
find backups/ -type d -mtime +30 -exec rm -rf {} \;

echo "Backup completed: $BACKUP_DIR"
EOF

    chmod +x scripts/backup_pipeline.sh

    # Add to crontab
    (crontab -l 2>/dev/null; echo "0 2 * * * $(pwd)/scripts/backup_pipeline.sh") | crontab -

    print_success "Backup automation setup completed"
}

# Setup performance optimization
setup_performance_optimization() {
    print_header "Setting Up Performance Optimization"

    # Create performance configuration
    cat > performance_config.json << EOF
{
    "caching": {
        "enabled": true,
        "redis_host": "localhost",
        "redis_port": 6379,
        "cache_ttl": 3600
    },
    "database": {
        "connection_pool_size": 20,
        "max_connections": 100,
        "query_timeout": 30
    },
    "pipeline": {
        "max_concurrent_executions": 10,
        "execution_timeout": 300,
        "retry_attempts": 3
    },
    "monitoring": {
        "metrics_interval": 60,
        "health_check_interval": 30,
        "performance_tracking": true
    }
}
EOF

    print_success "Performance optimization setup completed"
}

# Setup logging
setup_logging() {
    print_header "Setting Up Logging"

    # Create log configuration
    cat > logging_config.json << EOF
{
    "version": 1,
    "disable_existing_loggers": false,
    "formatters": {
        "standard": {
            "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
        },
        "detailed": {
            "format": "%(asctime)s [%(levelname)s] %(name)s:%(lineno)d: %(message)s"
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "INFO",
            "formatter": "standard",
            "stream": "ext://sys.stdout"
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "DEBUG",
            "formatter": "detailed",
            "filename": "logs/pipeline.log",
            "maxBytes": 10485760,
            "backupCount": 5
        },
        "error_file": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "ERROR",
            "formatter": "detailed",
            "filename": "logs/errors.log",
            "maxBytes": 10485760,
            "backupCount": 5
        }
    },
    "loggers": {
        "pipeline": {
            "level": "DEBUG",
            "handlers": ["console", "file"],
            "propagate": false
        },
        "monitoring": {
            "level": "INFO",
            "handlers": ["console", "file"],
            "propagate": false
        },
        "analytics": {
            "level": "INFO",
            "handlers": ["console", "file"],
            "propagate": false
        }
    },
    "root": {
        "level": "INFO",
        "handlers": ["console", "error_file"]
    }
}
EOF

    print_success "Logging setup completed"
}

# Setup health checks
setup_health_checks() {
    print_header "Setting Up Health Checks"

    # Create health check script
    cat > scripts/health_check.sh << 'EOF'
#!/bin/bash

# Health Check Script
HEALTH_STATUS="healthy"
ERRORS=()

# Check database connectivity
if ! psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "SELECT 1;" > /dev/null 2>&1; then
    HEALTH_STATUS="unhealthy"
    ERRORS+=("Database connection failed")
fi

# Check pipeline services
if ! python3 -c "from svgx_engine.services.pipeline_integration import PipelineIntegrationService; print('Pipeline service OK')" > /dev/null 2>&1; then
    HEALTH_STATUS="unhealthy"
    ERRORS+=("Pipeline service unavailable")
fi

# Check monitoring service
if ! python3 -c "from svgx_engine.services.monitoring import get_monitoring; print('Monitoring service OK')" > /dev/null 2>&1; then
    HEALTH_STATUS="unhealthy"
    ERRORS+=("Monitoring service unavailable")
fi

# Check disk space
DISK_USAGE=$(df . | awk 'NR==2 {print $5}' | sed 's/%//')
if [ $DISK_USAGE -gt 90 ]; then
    HEALTH_STATUS="degraded"
    ERRORS+=("Disk usage is ${DISK_USAGE}%")
fi

# Output health status
echo "Health Status: $HEALTH_STATUS"
if [ ${#ERRORS[@]} -gt 0 ]; then
    echo "Errors:"
    for error in "${ERRORS[@]}"; do
        echo "  - $error"
    done
fi

exit $([ "$HEALTH_STATUS" = "healthy" ] && echo 0 || echo 1)
EOF

    chmod +x scripts/health_check.sh

    print_success "Health checks setup completed"
}

# Setup production deployment
setup_production_deployment() {
    print_header "Setting Up Production Deployment"

    # Create production deployment script
    cat > scripts/deploy_production.sh << 'EOF'
#!/bin/bash

# Production Deployment Script
set -e

echo "Starting production deployment..."

# Load environment variables
source .env.production

# Stop existing services
echo "Stopping existing services..."
pkill -f "python.*pipeline" || true
pkill -f "go.*main" || true

# Backup current state
echo "Creating backup..."
./scripts/backup_pipeline.sh

# Deploy new code
echo "Deploying new code..."
git pull origin main

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt
cd arx-backend && go mod download && cd ..

# Run database migrations
echo "Running database migrations..."
cd arx-backend
psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -f migrations/004_create_pipeline_tables.sql
cd ..

# Start services
echo "Starting services..."
nohup python3 -m svgx_engine.services.pipeline_integration > logs/pipeline.log 2>&1 &
nohup go run arx-backend/main.go > logs/backend.log 2>&1 &

# Wait for services to start
sleep 10

# Run health checks
echo "Running health checks..."
./scripts/health_check.sh

echo "Production deployment completed successfully!"
EOF

    chmod +x scripts/deploy_production.sh

    print_success "Production deployment setup completed"
}

# Setup monitoring dashboard
setup_monitoring_dashboard() {
    print_header "Setting Up Monitoring Dashboard"

    # Create dashboard configuration
    cat > dashboard_config.json << EOF
{
    "dashboard": {
        "title": "Arxos Pipeline Monitoring",
        "refresh_interval": 30,
        "theme": "dark"
    },
    "widgets": [
        {
            "id": "pipeline_executions",
            "title": "Pipeline Executions",
            "type": "line_chart",
            "data_source": "pipeline_metrics",
            "metric": "executions_per_hour"
        },
        {
            "id": "success_rate",
            "title": "Success Rate",
            "type": "gauge",
            "data_source": "pipeline_metrics",
            "metric": "success_rate"
        },
        {
            "id": "execution_time",
            "title": "Average Execution Time",
            "type": "line_chart",
            "data_source": "pipeline_metrics",
            "metric": "avg_execution_time"
        },
        {
            "id": "system_health",
            "title": "System Health",
            "type": "status",
            "data_source": "health_checks"
        }
    ],
    "alerts": [
        {
            "name": "High Error Rate",
            "condition": "error_rate > 5",
            "severity": "warning"
        },
        {
            "name": "Slow Execution",
            "condition": "avg_execution_time > 300",
            "severity": "warning"
        },
        {
            "name": "System Unhealthy",
            "condition": "health_status != 'healthy'",
            "severity": "critical"
        }
    ]
}
EOF

    print_success "Monitoring dashboard setup completed"
}

# Main setup function
main() {
    print_header "Arxos Production Environment Setup"
    print_info "Environment: $ENVIRONMENT"
    print_info "Database: $DB_HOST:$DB_PORT/$DB_NAME"

    # Check requirements
    check_root

    # Setup all components
    setup_environment
    setup_database
    setup_monitoring
    setup_security
    setup_backup_automation
    setup_performance_optimization
    setup_logging
    setup_health_checks
    setup_production_deployment
    setup_monitoring_dashboard

    print_header "Production Setup Complete"
    print_success "Arxos pipeline is ready for production deployment!"
    print_info "Next steps:"
    print_info "1. Review configuration files"
    print_info "2. Test the deployment with: ./scripts/deploy_production.sh"
    print_info "3. Monitor the system with: ./scripts/health_check.sh"
    print_info "4. Set up monitoring dashboards"
    print_info "5. Configure alerting"
}

# Run main function
main "$@"
