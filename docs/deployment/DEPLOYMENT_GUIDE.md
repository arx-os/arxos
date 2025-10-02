# ArxOS IfcOpenShell Integration - Production Deployment Guide

## Overview

This guide provides comprehensive instructions for deploying the ArxOS IfcOpenShell integration in a production environment. The integration includes advanced IFC processing capabilities with enterprise-grade monitoring, caching, and load balancing.

## Architecture

### Components

- **ArxOS Main Application**: Core building management system
- **IfcOpenShell Service**: Python microservice for IFC processing
- **Redis Cache**: High-performance caching layer
- **PostGIS Database**: Spatial database for building data
- **Nginx Load Balancer**: Request routing and load balancing
- **Prometheus**: Metrics collection and monitoring
- **Grafana**: Visualization and alerting dashboard

### Service Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Nginx LB      │────│   ArxOS App     │────│   PostGIS DB    │
│   (Port 80)     │    │   (Port 8080)   │    │   (Port 5432)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │
         │                       │
         ▼                       ▼
┌─────────────────┐    ┌─────────────────┐
│ IfcOpenShell    │    │   Redis Cache   │
│ Service         │    │   (Port 6379)   │
│ (Port 5000)     │    └─────────────────┘
└─────────────────┘
         │
         ▼
┌─────────────────┐
│   Prometheus    │
│   (Port 9090)   │
└─────────────────┘
         │
         ▼
┌─────────────────┐
│    Grafana      │
│   (Port 3000)   │
└─────────────────┘
```

## Prerequisites

### System Requirements

- **CPU**: Minimum 4 cores, recommended 8+ cores
- **Memory**: Minimum 8GB RAM, recommended 16+ GB
- **Storage**: Minimum 100GB SSD, recommended 500+ GB
- **Network**: Stable internet connection for service communication

### Software Requirements

- Docker Engine 20.10+
- Docker Compose 2.0+
- Git (for source code management)

### Environment Variables

Create a `.env` file with the following variables:

```bash
# Database Configuration
POSTGRES_PASSWORD=your_secure_postgres_password
POSTGRES_USER=arxos
POSTGRES_DB=arxos

# IfcOpenShell Service Configuration
IFC_JWT_SECRET=your_secure_jwt_secret_key
IFC_MAX_FILE_SIZE_MB=200
IFC_CACHE_ENABLED=true
IFC_CACHE_TTL_SECONDS=7200
IFC_AUTH_ENABLED=true

# Monitoring Configuration
GRAFANA_PASSWORD=your_secure_grafana_password

# Redis Configuration
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=0

# ArxOS Configuration
ARXOS_MODE=production
ARXOS_LOG_LEVEL=info
ARXOS_TUI_ENABLED=false
```

## Deployment Steps

### 1. Clone Repository

```bash
git clone https://github.com/your-org/arxos.git
cd arxos
```

### 2. Configure Environment

```bash
# Copy environment template
cp env.example .env

# Edit environment variables
nano .env
```

### 3. Build and Deploy

```bash
# Build all services
docker-compose -f docker-compose.prod.yml build

# Start all services
docker-compose -f docker-compose.prod.yml up -d

# Check service status
docker-compose -f docker-compose.prod.yml ps
```

### 4. Verify Deployment

```bash
# Check ArxOS health
curl http://localhost/health

# Check IfcOpenShell service health
curl http://localhost:5000/health

# Check database connection
docker-compose -f docker-compose.prod.yml exec postgis pg_isready -U arxos

# Check Redis connection
docker-compose -f docker-compose.prod.yml exec redis redis-cli ping
```

## Service Configuration

### ArxOS Main Application

**Configuration File**: `configs/production.yml`

```yaml
database:
  host: postgis
  port: 5432
  name: arxos
  user: arxos
  password: ${POSTGRES_PASSWORD}

ifc:
  service:
    enabled: true
    url: http://ifcopenshell-service:5000
    timeout: 30s
    retries: 3
    circuit_breaker:
      enabled: true
      failure_threshold: 5
      recovery_timeout: 60s
  fallback:
    enabled: true
    parser: native
  performance:
    cache_enabled: true
    cache_ttl: 2h
    max_file_size: 200MB

logging:
  level: info
  format: json
```

### IfcOpenShell Service

**Configuration File**: Environment variables

```bash
# Service Configuration
FLASK_ENV=production
LOG_LEVEL=info

# Cache Configuration
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=0
IFC_CACHE_ENABLED=true
IFC_CACHE_TTL_SECONDS=7200

# Security Configuration
IFC_AUTH_ENABLED=true
IFC_JWT_SECRET=your_secure_jwt_secret

# Performance Configuration
IFC_MAX_FILE_SIZE_MB=200
```

### Redis Cache

**Configuration**: Redis configuration in Docker Compose

```yaml
redis:
  image: redis:7-alpine
  command: redis-server --appendonly yes --maxmemory 1gb --maxmemory-policy allkeys-lru
  volumes:
    - redis_data:/data
```

### PostGIS Database

**Configuration**: Database initialization script

```sql
-- Initialize PostGIS extensions
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;
CREATE EXTENSION IF NOT EXISTS fuzzystrmatch;
CREATE EXTENSION IF NOT EXISTS postgis_tiger_geocoder;

-- Create ArxOS database schema
\i /docker-entrypoint-initdb.d/init-postgis.sql
```

## Monitoring and Alerting

### Prometheus Configuration

**File**: `configs/prometheus/prometheus.yml`

- Scrapes metrics from all services every 30 seconds
- Collects performance, health, and error metrics
- Configures alerting rules for critical issues

### Grafana Dashboards

**Access**: http://localhost:3000
**Default Credentials**: admin / (see GRAFANA_PASSWORD in .env)

**Key Dashboards**:
- ArxOS Service Overview
- IfcOpenShell Performance
- System Resource Usage
- Error Rate Monitoring

### Alert Rules

**Critical Alerts**:
- Service Down (1 minute)
- Database Connection Failed (1 minute)
- Redis Connection Failed (1 minute)
- High Error Rate (>10% for 2 minutes)
- High Response Time (>5s for 3 minutes)

**Warning Alerts**:
- High Memory Usage (>3GB for 5 minutes)
- Low Cache Hit Rate (<50% for 10 minutes)
- High CPU Usage (>80% for 5 minutes)

## Load Balancing

### Nginx Configuration

**File**: `configs/nginx/nginx.conf`

**Features**:
- Round-robin load balancing
- Health checks and failover
- Rate limiting (10 req/s for API, 5 req/s for IFC)
- Request buffering and compression
- Extended timeouts for IFC processing

**Upstream Configuration**:
```nginx
upstream ifcopenshell_backend {
    least_conn;
    server ifcopenshell-service:5000 max_fails=3 fail_timeout=30s;
    keepalive 16;
}
```

## Scaling

### Horizontal Scaling

**IfcOpenShell Service**:
```bash
# Scale to 5 replicas
docker-compose -f docker-compose.prod.yml up -d --scale ifcopenshell-service=5
```

**ArxOS Application**:
```bash
# Scale to 3 replicas
docker-compose -f docker-compose.prod.yml up -d --scale arxos=3
```

### Vertical Scaling

**Resource Limits** (in docker-compose.prod.yml):
```yaml
deploy:
  resources:
    limits:
      memory: 4G
      cpus: '2.0'
    reservations:
      memory: 1G
      cpus: '0.5'
```

## Security

### Authentication

**JWT Configuration**:
- IfcOpenShell service uses JWT for API authentication
- Secret key configured via `IFC_JWT_SECRET` environment variable
- Token validation on all API endpoints

### Network Security

**Internal Network**:
- All services communicate via internal Docker network
- External access only through Nginx load balancer
- Database and cache not exposed externally

**Rate Limiting**:
- API endpoints: 10 requests/second
- IFC processing: 5 requests/second
- Burst allowance for temporary spikes

### Data Security

**Database**:
- Encrypted connections (configure SSL certificates)
- Regular backups with encryption
- Access control via PostgreSQL roles

**File Storage**:
- IFC files processed in memory (not persisted)
- Cache data encrypted in Redis
- Log files with sensitive data redaction

## Backup and Recovery

### Database Backup

```bash
# Create backup
docker-compose -f docker-compose.prod.yml exec postgis pg_dump -U arxos arxos > backup_$(date +%Y%m%d_%H%M%S).sql

# Restore backup
docker-compose -f docker-compose.prod.yml exec -T postgis psql -U arxos arxos < backup_file.sql
```

### Configuration Backup

```bash
# Backup configuration files
tar -czf config_backup_$(date +%Y%m%d_%H%M%S).tar.gz configs/ .env docker-compose.prod.yml
```

### Disaster Recovery

1. **Service Failure**: Automatic failover via Docker health checks
2. **Database Failure**: Restore from latest backup
3. **Complete System Failure**: Rebuild from configuration backup

## Troubleshooting

### Common Issues

**Service Won't Start**:
```bash
# Check logs
docker-compose -f docker-compose.prod.yml logs [service-name]

# Check resource usage
docker stats
```

**High Memory Usage**:
```bash
# Check memory usage
docker-compose -f docker-compose.prod.yml exec ifcopenshell-service ps aux

# Restart service
docker-compose -f docker-compose.prod.yml restart ifcopenshell-service
```

**Database Connection Issues**:
```bash
# Test database connection
docker-compose -f docker-compose.prod.yml exec postgis pg_isready -U arxos

# Check database logs
docker-compose -f docker-compose.prod.yml logs postgis
```

### Performance Optimization

**Cache Optimization**:
- Monitor cache hit rates in Grafana
- Adjust cache TTL based on usage patterns
- Scale Redis if memory usage is high

**Database Optimization**:
- Monitor query performance
- Add indexes for frequently queried data
- Consider read replicas for heavy read workloads

**Service Optimization**:
- Monitor CPU and memory usage
- Scale services based on load patterns
- Optimize IFC file processing parameters

## Maintenance

### Regular Tasks

**Daily**:
- Monitor service health and performance
- Check error rates and alerts
- Review resource usage

**Weekly**:
- Update service dependencies
- Review and rotate security keys
- Analyze performance trends

**Monthly**:
- Update system packages
- Review and update monitoring rules
- Test disaster recovery procedures

### Updates

**Service Updates**:
```bash
# Pull latest images
docker-compose -f docker-compose.prod.yml pull

# Update services
docker-compose -f docker-compose.prod.yml up -d
```

**Configuration Updates**:
1. Update configuration files
2. Test in staging environment
3. Deploy to production with rolling updates

## Support

### Logs and Monitoring

**Service Logs**:
```bash
# View all logs
docker-compose -f docker-compose.prod.yml logs -f

# View specific service logs
docker-compose -f docker-compose.prod.yml logs -f ifcopenshell-service
```

**Monitoring Access**:
- Grafana: http://localhost:3000
- Prometheus: http://localhost:9090
- Service Health: http://localhost/health

### Contact Information

- **Technical Support**: support@arxos.com
- **Documentation**: https://docs.arxos.com
- **Issue Tracking**: https://github.com/your-org/arxos/issues

---

**Last Updated**: 2024-01-01
**Version**: 1.0.0
