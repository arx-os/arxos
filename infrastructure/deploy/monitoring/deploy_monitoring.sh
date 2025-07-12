#!/bin/bash

# Arxos Platform Monitoring and Alerting System Deployment Script
# This script deploys a comprehensive monitoring stack including Prometheus, Grafana, AlertManager,
# and all supporting components for the Arxos Platform.

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
MONITORING_DIR="$SCRIPT_DIR"
CONFIG_DIR="$MONITORING_DIR/config"
DATA_DIR="$MONITORING_DIR/data"
LOGS_DIR="$MONITORING_DIR/logs"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check if port is available
port_available() {
    ! nc -z localhost "$1" >/dev/null 2>&1
}

# Function to create directories
create_directories() {
    log_info "Creating monitoring directories..."
    
    mkdir -p "$CONFIG_DIR"
    mkdir -p "$DATA_DIR"
    mkdir -p "$LOGS_DIR"
    mkdir -p "$DATA_DIR/prometheus"
    mkdir -p "$DATA_DIR/grafana"
    mkdir -p "$DATA_DIR/alertmanager"
    mkdir -p "$DATA_DIR/elasticsearch"
    mkdir -p "$DATA_DIR/kibana"
    mkdir -p "$DATA_DIR/jaeger"
    
    log_success "Directories created successfully"
}

# Function to check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check for Docker
    if ! command_exists docker; then
        log_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    # Check for Docker Compose
    if ! command_exists docker-compose; then
        log_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    # Check for required ports
    local required_ports=(9090 9093 3000 9200 5601 16686 8080)
    for port in "${required_ports[@]}"; do
        if ! port_available "$port"; then
            log_warning "Port $port is already in use. Please ensure it's available for monitoring services."
        fi
    done
    
    log_success "Prerequisites check completed"
}

# Function to create Docker Compose configuration
create_docker_compose() {
    log_info "Creating Docker Compose configuration..."
    
    cat > "$MONITORING_DIR/docker-compose.yml" << 'EOF'
version: '3.8'

services:
  # Prometheus
  prometheus:
    image: prom/prometheus:latest
    container_name: arxos-prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - ./alert_rules.yml:/etc/prometheus/alert_rules.yml
      - ./data/prometheus:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
      - '--storage.tsdb.retention.time=15d'
      - '--web.enable-lifecycle'
    restart: unless-stopped
    networks:
      - monitoring

  # AlertManager
  alertmanager:
    image: prom/alertmanager:latest
    container_name: arxos-alertmanager
    ports:
      - "9093:9093"
    volumes:
      - ./alertmanager.yml:/etc/alertmanager/alertmanager.yml
      - ./data/alertmanager:/alertmanager
    command:
      - '--config.file=/etc/alertmanager/alertmanager.yml'
      - '--storage.path=/alertmanager'
    restart: unless-stopped
    networks:
      - monitoring

  # Grafana
  grafana:
    image: grafana/grafana:latest
    container_name: arxos-grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=arxos-admin
      - GF_USERS_ALLOW_SIGN_UP=false
      - GF_INSTALL_PLUGINS=grafana-clock-panel,grafana-simple-json-datasource
    volumes:
      - ./data/grafana:/var/lib/grafana
      - ./grafana_dashboards.json:/etc/grafana/provisioning/dashboards/dashboards.json
      - ./grafana_datasources.yml:/etc/grafana/provisioning/datasources/datasources.yml
    restart: unless-stopped
    networks:
      - monitoring

  # Node Exporter (System Metrics)
  node-exporter:
    image: prom/node-exporter:latest
    container_name: arxos-node-exporter
    ports:
      - "9100:9100"
    volumes:
      - /proc:/host/proc:ro
      - /sys:/host/sys:ro
      - /:/rootfs:ro
    command:
      - '--path.procfs=/host/proc'
      - '--path.sysfs=/host/sys'
      - '--collector.filesystem.mount-points-exclude=^/(sys|proc|dev|host|etc)($$|/)'
    restart: unless-stopped
    networks:
      - monitoring

  # Elasticsearch (Log Aggregation)
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.11.0
    container_name: arxos-elasticsearch
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
      - "ES_JAVA_OPTS=-Xms512m -Xmx512m"
    ports:
      - "9200:9200"
    volumes:
      - ./data/elasticsearch:/usr/share/elasticsearch/data
    restart: unless-stopped
    networks:
      - monitoring

  # Kibana (Log Visualization)
  kibana:
    image: docker.elastic.co/kibana/kibana:8.11.0
    container_name: arxos-kibana
    environment:
      - ELASTICSEARCH_HOSTS=http://elasticsearch:9200
    ports:
      - "5601:5601"
    volumes:
      - ./data/kibana:/usr/share/kibana/data
    restart: unless-stopped
    networks:
      - monitoring
    depends_on:
      - elasticsearch

  # Jaeger (Distributed Tracing)
  jaeger:
    image: jaegertracing/all-in-one:latest
    container_name: arxos-jaeger
    ports:
      - "16686:16686"
      - "14268:14268"
    environment:
      - COLLECTOR_OTLP_ENABLED=true
    restart: unless-stopped
    networks:
      - monitoring

  # Arxos API (Application Metrics)
  arxos-api:
    image: arxos/api:latest
    container_name: arxos-api
    ports:
      - "8000:8000"
    environment:
      - MONITORING_ENABLED=true
      - METRICS_PORT=8000
      - LOG_LEVEL=info
    volumes:
      - ./logs:/app/logs
    restart: unless-stopped
    networks:
      - monitoring

  # Arxos Backend (Application Metrics)
  arxos-backend:
    image: arxos/backend:latest
    container_name: arxos-backend
    ports:
      - "8080:8080"
    environment:
      - MONITORING_ENABLED=true
      - METRICS_PORT=8080
      - LOG_LEVEL=info
    volumes:
      - ./logs:/app/logs
    restart: unless-stopped
    networks:
      - monitoring

  # Arxos SVG Parser (Application Metrics)
  arxos-svg-parser:
    image: arxos/svg-parser:latest
    container_name: arxos-svg-parser
    ports:
      - "8001:8000"
    environment:
      - MONITORING_ENABLED=true
      - METRICS_PORT=8000
      - LOG_LEVEL=info
    volumes:
      - ./logs:/app/logs
    restart: unless-stopped
    networks:
      - monitoring

  # Arxos Frontend (Application Metrics)
  arxos-frontend:
    image: arxos/frontend:latest
    container_name: arxos-frontend
    ports:
      - "3000:3000"
    environment:
      - MONITORING_ENABLED=true
      - METRICS_PORT=3000
      - LOG_LEVEL=info
    volumes:
      - ./logs:/app/logs
    restart: unless-stopped
    networks:
      - monitoring

  # Redis (Cache Metrics)
  redis:
    image: redis:7-alpine
    container_name: arxos-redis
    ports:
      - "6379:6379"
    volumes:
      - ./data/redis:/data
    restart: unless-stopped
    networks:
      - monitoring

  # PostgreSQL (Database Metrics)
  postgres:
    image: postgres:15-alpine
    container_name: arxos-postgres
    environment:
      - POSTGRES_DB=arxos
      - POSTGRES_USER=arxos
      - POSTGRES_PASSWORD=arxos-password
    ports:
      - "5432:5432"
    volumes:
      - ./data/postgres:/var/lib/postgresql/data
    restart: unless-stopped
    networks:
      - monitoring

  # Nginx (Web Server Metrics)
  nginx:
    image: nginx:alpine
    container_name: arxos-nginx
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    restart: unless-stopped
    networks:
      - monitoring

  # Custom Metrics Collector
  arxos-metrics:
    image: arxos/metrics:latest
    container_name: arxos-metrics
    ports:
      - "9090:9090"
    environment:
      - PROMETHEUS_ENABLED=true
      - METRICS_PORT=9090
    volumes:
      - ./logs:/app/logs
    restart: unless-stopped
    networks:
      - monitoring

  # Webhook Receiver
  arxos-webhook:
    image: arxos/webhook:latest
    container_name: arxos-webhook
    ports:
      - "8080:8080"
    environment:
      - WEBHOOK_SECRET=your-webhook-secret
    volumes:
      - ./logs:/app/logs
    restart: unless-stopped
    networks:
      - monitoring

networks:
  monitoring:
    driver: bridge
EOF

    log_success "Docker Compose configuration created"
}

# Function to create Grafana datasources configuration
create_grafana_datasources() {
    log_info "Creating Grafana datasources configuration..."
    
    cat > "$MONITORING_DIR/grafana_datasources.yml" << 'EOF'
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
    editable: true

  - name: Elasticsearch
    type: elasticsearch
    access: proxy
    url: http://elasticsearch:9200
    database: "arxos-logs"
    editable: true

  - name: Jaeger
    type: jaeger
    access: proxy
    url: http://jaeger:16686
    editable: true
EOF

    log_success "Grafana datasources configuration created"
}

# Function to create Nginx configuration
create_nginx_config() {
    log_info "Creating Nginx configuration..."
    
    cat > "$MONITORING_DIR/nginx.conf" << 'EOF'
events {
    worker_connections 1024;
}

http {
    upstream grafana {
        server grafana:3000;
    }

    upstream prometheus {
        server prometheus:9090;
    }

    upstream alertmanager {
        server alertmanager:9093;
    }

    upstream kibana {
        server kibana:5601;
    }

    upstream jaeger {
        server jaeger:16686;
    }

    server {
        listen 80;
        server_name monitoring.arxos.com;

        # Grafana
        location /grafana/ {
            proxy_pass http://grafana/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # Prometheus
        location /prometheus/ {
            proxy_pass http://prometheus/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # AlertManager
        location /alertmanager/ {
            proxy_pass http://alertmanager/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # Kibana
        location /kibana/ {
            proxy_pass http://kibana/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # Jaeger
        location /jaeger/ {
            proxy_pass http://jaeger/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # Health check
        location /health {
            access_log off;
            return 200 "healthy\n";
            add_header Content-Type text/plain;
        }
    }
}
EOF

    log_success "Nginx configuration created"
}

# Function to deploy monitoring stack
deploy_monitoring() {
    log_info "Deploying monitoring stack..."
    
    # Copy configuration files
    cp "$MONITORING_DIR/prometheus.yml" "$CONFIG_DIR/"
    cp "$MONITORING_DIR/alert_rules.yml" "$CONFIG_DIR/"
    cp "$MONITORING_DIR/alertmanager.yml" "$CONFIG_DIR/"
    cp "$MONITORING_DIR/grafana_dashboards.json" "$CONFIG_DIR/"
    cp "$MONITORING_DIR/grafana_datasources.yml" "$CONFIG_DIR/"
    cp "$MONITORING_DIR/nginx.conf" "$CONFIG_DIR/"
    
    # Start services
    cd "$MONITORING_DIR"
    docker-compose up -d
    
    log_success "Monitoring stack deployed successfully"
}

# Function to check service health
check_service_health() {
    log_info "Checking service health..."
    
    local services=(
        "prometheus:9090"
        "alertmanager:9093"
        "grafana:3000"
        "elasticsearch:9200"
        "kibana:5601"
        "jaeger:16686"
        "node-exporter:9100"
    )
    
    for service in "${services[@]}"; do
        local service_name="${service%:*}"
        local port="${service#*:}"
        
        if curl -s "http://localhost:$port" >/dev/null 2>&1; then
            log_success "$service_name is healthy"
        else
            log_warning "$service_name is not responding on port $port"
        fi
    done
}

# Function to configure monitoring
configure_monitoring() {
    log_info "Configuring monitoring components..."
    
    # Wait for services to be ready
    sleep 30
    
    # Configure Grafana dashboards
    log_info "Configuring Grafana dashboards..."
    curl -X POST \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer admin:arxos-admin" \
        -d @grafana_dashboards.json \
        http://localhost:3000/api/dashboards/db
    
    # Configure AlertManager
    log_info "Configuring AlertManager..."
    curl -X POST \
        -H "Content-Type: application/json" \
        -d @alertmanager.yml \
        http://localhost:9093/api/v1/receivers
    
    log_success "Monitoring configuration completed"
}

# Function to display monitoring URLs
display_urls() {
    log_info "Monitoring system is ready!"
    echo
    echo "Access URLs:"
    echo "  Grafana Dashboard:     http://localhost:3000 (admin/arxos-admin)"
    echo "  Prometheus:            http://localhost:9090"
    echo "  AlertManager:          http://localhost:9093"
    echo "  Kibana:                http://localhost:5601"
    echo "  Jaeger:                http://localhost:16686"
    echo "  Node Exporter:         http://localhost:9100"
    echo
    echo "API Endpoints:"
    echo "  Arxos API:             http://localhost:8000"
    echo "  Arxos Backend:         http://localhost:8080"
    echo "  Arxos SVG Parser:      http://localhost:8001"
    echo "  Arxos Frontend:        http://localhost:3000"
    echo
    echo "Database Services:"
    echo "  PostgreSQL:            localhost:5432"
    echo "  Redis:                 localhost:6379"
    echo
    echo "Logs:"
    echo "  Application Logs:      $LOGS_DIR"
    echo "  Monitoring Data:       $DATA_DIR"
    echo
}

# Function to stop monitoring stack
stop_monitoring() {
    log_info "Stopping monitoring stack..."
    
    cd "$MONITORING_DIR"
    docker-compose down
    
    log_success "Monitoring stack stopped"
}

# Function to restart monitoring stack
restart_monitoring() {
    log_info "Restarting monitoring stack..."
    
    stop_monitoring
    sleep 5
    deploy_monitoring
    
    log_success "Monitoring stack restarted"
}

# Function to show logs
show_logs() {
    local service="$1"
    
    if [ -z "$service" ]; then
        log_info "Showing all service logs..."
        cd "$MONITORING_DIR"
        docker-compose logs -f
    else
        log_info "Showing logs for $service..."
        cd "$MONITORING_DIR"
        docker-compose logs -f "$service"
    fi
}

# Function to backup monitoring data
backup_monitoring() {
    local backup_dir="$MONITORING_DIR/backups/$(date +%Y%m%d_%H%M%S)"
    
    log_info "Creating backup in $backup_dir..."
    
    mkdir -p "$backup_dir"
    
    # Backup configuration files
    cp -r "$CONFIG_DIR" "$backup_dir/"
    
    # Backup data directories
    cp -r "$DATA_DIR" "$backup_dir/"
    
    # Backup logs
    cp -r "$LOGS_DIR" "$backup_dir/"
    
    # Create backup archive
    tar -czf "$backup_dir.tar.gz" -C "$MONITORING_DIR" "backups/$(basename "$backup_dir")"
    rm -rf "$backup_dir"
    
    log_success "Backup created: $backup_dir.tar.gz"
}

# Function to restore monitoring data
restore_monitoring() {
    local backup_file="$1"
    
    if [ -z "$backup_file" ]; then
        log_error "Please specify backup file to restore"
        exit 1
    fi
    
    if [ ! -f "$backup_file" ]; then
        log_error "Backup file not found: $backup_file"
        exit 1
    fi
    
    log_info "Restoring from backup: $backup_file..."
    
    # Stop services
    stop_monitoring
    
    # Extract backup
    tar -xzf "$backup_file" -C "$MONITORING_DIR"
    
    # Restore data
    local backup_dir=$(tar -tzf "$backup_file" | head -1 | cut -d'/' -f1)
    cp -r "$MONITORING_DIR/$backup_dir/data" "$DATA_DIR/"
    cp -r "$MONITORING_DIR/$backup_dir/config" "$CONFIG_DIR/"
    cp -r "$MONITORING_DIR/$backup_dir/logs" "$LOGS_DIR/"
    
    # Clean up
    rm -rf "$MONITORING_DIR/$backup_dir"
    
    # Restart services
    deploy_monitoring
    
    log_success "Backup restored successfully"
}

# Function to show usage
show_usage() {
    echo "Arxos Platform Monitoring Deployment Script"
    echo
    echo "Usage: $0 [COMMAND]"
    echo
    echo "Commands:"
    echo "  deploy          Deploy the monitoring stack"
    echo "  stop            Stop the monitoring stack"
    echo "  restart         Restart the monitoring stack"
    echo "  status          Check service health"
    echo "  logs [SERVICE]  Show logs (all services or specific service)"
    echo "  backup          Create backup of monitoring data"
    echo "  restore FILE    Restore from backup file"
    echo "  help            Show this help message"
    echo
    echo "Examples:"
    echo "  $0 deploy"
    echo "  $0 logs prometheus"
    echo "  $0 backup"
    echo "  $0 restore backup_20241219_143022.tar.gz"
    echo
}

# Main script logic
main() {
    local command="$1"
    
    case "$command" in
        "deploy")
            check_prerequisites
            create_directories
            create_docker_compose
            create_grafana_datasources
            create_nginx_config
            deploy_monitoring
            configure_monitoring
            check_service_health
            display_urls
            ;;
        "stop")
            stop_monitoring
            ;;
        "restart")
            restart_monitoring
            ;;
        "status")
            check_service_health
            ;;
        "logs")
            show_logs "$2"
            ;;
        "backup")
            backup_monitoring
            ;;
        "restore")
            restore_monitoring "$2"
            ;;
        "help"|"--help"|"-h"|"")
            show_usage
            ;;
        *)
            log_error "Unknown command: $command"
            show_usage
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@" 