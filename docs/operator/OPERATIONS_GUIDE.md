# SVGX Engine Operations Guide

## Overview

This guide provides comprehensive instructions for deploying, monitoring, and maintaining the SVGX Engine in production environments. It covers all operational aspects including deployment, scaling, monitoring, troubleshooting, and disaster recovery.

## Table of Contents

1. [System Architecture](#system-architecture)
2. [Deployment](#deployment)
3. [Configuration](#configuration)
4. [Monitoring](#monitoring)
5. [Scaling](#scaling)
6. [Backup and Recovery](#backup-and-recovery)
7. [Troubleshooting](#troubleshooting)
8. [Security](#security)
9. [Performance Tuning](#performance-tuning)
10. [Disaster Recovery](#disaster-recovery)

## System Architecture

### Components

The SVGX Engine consists of the following components:

1. **API Server**: FastAPI-based REST API and WebSocket server
2. **Authentication Service**: JWT-based authentication and authorization
3. **Collaboration Engine**: Real-time collaborative editing
4. **State Management**: Multi-backend state persistence
5. **Monitoring**: Prometheus metrics and health checks
6. **Load Balancer**: Horizontal scaling support
7. **Database**: PostgreSQL for persistent data
8. **Cache**: Redis for session and state caching

### Network Architecture

```
Internet
    │
    ▼
[Load Balancer] (NGINX/HAProxy)
    │
    ▼
[API Gateway] (Kubernetes Ingress)
    │
    ▼
[SVGX Engine Instances] (Multiple pods)
    │
    ▼
[Database Layer] (PostgreSQL + Redis)
```

## Deployment

### Prerequisites

- Kubernetes cluster (v1.24+)
- PostgreSQL database (v15+)
- Redis cluster (v7.0+)
- NGINX Ingress Controller
- Cert-Manager for SSL certificates
- Prometheus Operator for monitoring

### Quick Start Deployment

1. **Clone the repository**
```bash
git clone https://github.com/your-org/svgx-engine.git
cd svgx-engine
```

2. **Create namespace**
```bash
kubectl create namespace svgx
```

3. **Create secrets**
```bash
kubectl create secret generic svgx-secrets \
  --from-literal=redis-url="redis://redis-cluster:6379/0" \
  --from-literal=postgres-url="postgresql://user:pass@postgres:5432/svgx" \
  --from-literal=jwt-secret="your-super-secret-jwt-key" \
  -n svgx
```

4. **Deploy the application**
```bash
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/ingress.yaml
kubectl apply -f k8s/monitoring.yaml
```

5. **Verify deployment**
```bash
kubectl get pods -n svgx
kubectl get services -n svgx
kubectl get ingress -n svgx
```

### Production Deployment

#### 1. Environment Configuration

Create environment-specific configuration:

```yaml
# config/production.yaml
environment: production
log_level: INFO
database:
  url: postgresql://user:pass@postgres:5432/svgx
  pool_size: 20
  max_overflow: 30
redis:
  url: redis://redis-cluster:6379/0
  pool_size: 10
security:
  jwt_secret: ${JWT_SECRET}
  jwt_expires_in: 3600
  rate_limit_requests_per_minute: 100
monitoring:
  prometheus_enabled: true
  health_check_interval: 30
scaling:
  min_replicas: 3
  max_replicas: 10
  target_cpu_utilization: 70
```

#### 2. Database Setup

```sql
-- Create database
CREATE DATABASE svgx;

-- Create user
CREATE USER svgx_user WITH PASSWORD 'secure_password';

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE svgx TO svgx_user;

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";
```

#### 3. Redis Configuration

```redis
# redis.conf
maxmemory 2gb
maxmemory-policy allkeys-lru
save 900 1
save 300 10
save 60 10000
```

#### 4. SSL Certificate Setup

```bash
# Install cert-manager
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.12.0/cert-manager.yaml

# Create cluster issuer
kubectl apply -f - <<EOF
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: admin@your-domain.com
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
    - http01:
        ingress:
          class: nginx
EOF
```

## Configuration

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `ENVIRONMENT` | Environment name | `development` | No |
| `LOG_LEVEL` | Logging level | `INFO` | No |
| `REDIS_URL` | Redis connection URL | `redis://localhost:6379/0` | Yes |
| `POSTGRES_URL` | PostgreSQL connection URL | - | Yes |
| `JWT_SECRET` | JWT signing secret | - | Yes |
| `API_HOST` | API server host | `0.0.0.0` | No |
| `API_PORT` | API server port | `8000` | No |
| `CORS_ORIGINS` | CORS allowed origins | `*` | No |
| `RATE_LIMIT_REQUESTS_PER_MINUTE` | Rate limit requests | `100` | No |
| `HEALTH_CHECK_INTERVAL` | Health check interval (seconds) | `30` | No |

### Kubernetes Configuration

#### Resource Limits

```yaml
resources:
  requests:
    memory: "512Mi"
    cpu: "250m"
  limits:
    memory: "1Gi"
    cpu: "500m"
```

#### Health Checks

```yaml
livenessProbe:
  httpGet:
    path: /health/
    port: 8000
  initialDelaySeconds: 30
  periodSeconds: 10
  timeoutSeconds: 5
  failureThreshold: 3

readinessProbe:
  httpGet:
    path: /health/
    port: 8000
  initialDelaySeconds: 5
  periodSeconds: 5
  timeoutSeconds: 3
  failureThreshold: 3
```

#### Auto-scaling

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: svgx-engine-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: svgx-engine
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

## Monitoring

### Prometheus Configuration

```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: svgx-engine-monitor
spec:
  selector:
    matchLabels:
      app: svgx-engine
  endpoints:
  - port: http
    path: /metrics/prometheus
    interval: 30s
    scrapeTimeout: 10s
```

### Grafana Dashboards

Import the following dashboards:

1. **SVGX Engine Overview**: System health and performance
2. **Collaboration Metrics**: Real-time collaboration statistics
3. **Error Tracking**: Error rates and types
4. **Resource Usage**: CPU, memory, and disk usage

### Alerting Rules

```yaml
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: svgx-engine-alerts
spec:
  groups:
  - name: svgx-engine.rules
    rules:
    - alert: SVGXEngineHighErrorRate
      expr: rate(svgx_engine_errors_total[5m]) > 0.1
      for: 2m
      labels:
        severity: warning
      annotations:
        summary: "High error rate detected"
        description: "SVGX Engine is experiencing a high error rate"

    - alert: SVGXEngineHighResponseTime
      expr: histogram_quantile(0.95, rate(svgx_engine_request_duration_seconds_bucket[5m])) > 2
      for: 2m
      labels:
        severity: warning
      annotations:
        summary: "High response time detected"
        description: "95th percentile response time is {{ $value }} seconds"

    - alert: SVGXEnginePodDown
      expr: up{job="svgx-engine"} == 0
      for: 1m
      labels:
        severity: critical
      annotations:
        summary: "SVGX Engine pod is down"
        description: "SVGX Engine pod {{ $labels.pod }} is down"
```

### Health Checks

#### Manual Health Check

```bash
# Check API health
curl -f http://localhost:8000/health/

# Check detailed health
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/health/summary/

# Check metrics
curl http://localhost:8000/metrics/prometheus
```

#### Automated Health Checks

```bash
#!/bin/bash
# health_check.sh

HEALTH_URL="http://localhost:8000/health/"
METRICS_URL="http://localhost:8000/metrics/prometheus"

# Check API health
if ! curl -f -s $HEALTH_URL > /dev/null; then
    echo "ERROR: API health check failed"
    exit 1
fi

# Check metrics endpoint
if ! curl -f -s $METRICS_URL > /dev/null; then
    echo "ERROR: Metrics endpoint check failed"
    exit 1
fi

echo "Health checks passed"
exit 0
```

## Scaling

### Horizontal Scaling

#### Manual Scaling

```bash
# Scale to 5 replicas
kubectl scale deployment svgx-engine --replicas=5 -n svgx

# Check scaling status
kubectl get pods -n svgx
```

#### Auto-scaling Configuration

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: svgx-engine-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: svgx-engine
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 10
        periodSeconds: 60
    scaleUp:
      stabilizationWindowSeconds: 60
      policies:
      - type: Percent
        value: 100
        periodSeconds: 15
```

### Load Balancing

#### NGINX Configuration

```nginx
upstream svgx_backend {
    server svgx-engine-service:80;
    keepalive 32;
}

# Rate limiting
limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
limit_req_zone $binary_remote_addr zone=websocket:10m rate=100r/s;

server {
    listen 80;
    server_name svgx-engine.example.com;

    # API rate limiting
    location / {
        limit_req zone=api burst=20 nodelay;
        proxy_pass http://svgx_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_read_timeout 300s;
        proxy_send_timeout 300s;
    }

    # WebSocket rate limiting
    location /ws {
        limit_req zone=websocket burst=50 nodelay;
        proxy_pass http://svgx_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_read_timeout 300s;
        proxy_send_timeout 300s;
    }
}
```

## Backup and Recovery

### Database Backup

#### Automated Backup Script

```bash
#!/bin/bash
# backup_database.sh

BACKUP_DIR="/backups"
DATE=$(date +%Y%m%d_%H%M%S)
DB_NAME="svgx"
DB_USER="svgx_user"
DB_HOST="postgres"

# Create backup directory
mkdir -p $BACKUP_DIR

# Create database backup
pg_dump -h $DB_HOST -U $DB_USER -d $DB_NAME > $BACKUP_DIR/svgx_backup_$DATE.sql

# Compress backup
gzip $BACKUP_DIR/svgx_backup_$DATE.sql

# Keep only last 7 days of backups
find $BACKUP_DIR -name "svgx_backup_*.sql.gz" -mtime +7 -delete

echo "Backup completed: svgx_backup_$DATE.sql.gz"
```

#### Kubernetes CronJob for Backup

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: svgx-backup
  namespace: svgx
spec:
  schedule: "0 2 * * *"  # Daily at 2 AM
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: backup
            image: postgres:15
            command:
            - /bin/bash
            - -c
            - |
              pg_dump -h postgres -U svgx_user -d svgx > /backups/svgx_backup_$(date +%Y%m%d_%H%M%S).sql
              gzip /backups/svgx_backup_*.sql
              find /backups -name "svgx_backup_*.sql.gz" -mtime +7 -delete
            env:
            - name: PGPASSWORD
              valueFrom:
                secretKeyRef:
                  name: svgx-secrets
                  key: postgres-password
            volumeMounts:
            - name: backup-storage
              mountPath: /backups
          volumes:
          - name: backup-storage
            persistentVolumeClaim:
              claimName: svgx-backup-pvc
          restartPolicy: OnFailure
```

### State Backup

#### API-based Backup

```bash
# Create state backup
curl -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"state_type": "canvas", "backup_type": "full"}' \
  http://localhost:8000/state/backup/

# List backups
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/state/backups/

# Restore from backup
curl -X POST \
  -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/state/restore/backup_id_123
```

### Recovery Procedures

#### Database Recovery

```bash
# Stop the application
kubectl scale deployment svgx-engine --replicas=0 -n svgx

# Restore database
pg_restore -h postgres -U svgx_user -d svgx svgx_backup_20240101_120000.sql

# Restart the application
kubectl scale deployment svgx-engine --replicas=3 -n svgx

# Verify recovery
curl -f http://localhost:8000/health/
```

#### State Recovery

```bash
# Restore state from backup
curl -X POST \
  -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/state/restore/backup_id_123

# Verify state restoration
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/state/retrieve/canvas_state_123
```

## Troubleshooting

### Common Issues

#### 1. High Memory Usage

**Symptoms:**
- Pods restarting frequently
- High memory usage in metrics
- Slow response times

**Diagnosis:**
```bash
# Check memory usage
kubectl top pods -n svgx

# Check memory limits
kubectl describe pod svgx-engine-xxx -n svgx

# Check application logs
kubectl logs -f deployment/svgx-engine -n svgx
```

**Solutions:**
- Increase memory limits
- Optimize application code
- Add memory monitoring alerts

#### 2. Database Connection Issues

**Symptoms:**
- 500 errors on API calls
- Connection timeout errors
- Database connection pool exhausted

**Diagnosis:**
```bash
# Check database connectivity
kubectl exec -it svgx-engine-xxx -n svgx -- nc -zv postgres 5432

# Check database logs
kubectl logs postgres-pod -n database

# Check connection pool status
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/health/summary/
```

**Solutions:**
- Increase database connection pool size
- Check database resource limits
- Verify network connectivity

#### 3. WebSocket Connection Issues

**Symptoms:**
- Real-time collaboration not working
- WebSocket connection failures
- Users unable to see live updates

**Diagnosis:**
```bash
# Check WebSocket endpoint
curl -i -N -H "Connection: Upgrade" \
  -H "Upgrade: websocket" \
  -H "Sec-WebSocket-Version: 13" \
  -H "Sec-WebSocket-Key: test" \
  http://localhost:8000/runtime/events

# Check WebSocket logs
kubectl logs -f deployment/svgx-engine -n svgx | grep websocket
```

**Solutions:**
- Verify WebSocket proxy configuration
- Check CORS settings
- Ensure proper SSL termination

#### 4. Rate Limiting Issues

**Symptoms:**
- 429 errors
- Users getting blocked
- API calls failing

**Diagnosis:**
```bash
# Check rate limit analytics
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/security/rate-limits/analytics/

# Check rate limit configuration
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/security/rate-limits/config/
```

**Solutions:**
- Adjust rate limit settings
- Add users to whitelist
- Implement client-side retry logic

### Log Analysis

#### Application Logs

```bash
# Get recent logs
kubectl logs --tail=100 deployment/svgx-engine -n svgx

# Follow logs in real-time
kubectl logs -f deployment/svgx-engine -n svgx

# Get logs from specific pod
kubectl logs svgx-engine-xxx -n svgx

# Get logs with timestamps
kubectl logs deployment/svgx-engine -n svgx --timestamps
```

#### Error Analysis

```bash
# Get error logs
kubectl logs deployment/svgx-engine -n svgx | grep ERROR

# Get logs for specific time period
kubectl logs deployment/svgx-engine -n svgx --since=1h

# Get logs for specific user
kubectl logs deployment/svgx-engine -n svgx | grep "user_id=123"
```

### Performance Tuning

#### Database Optimization

```sql
-- Analyze table statistics
ANALYZE;

-- Check slow queries
SELECT query, calls, total_time, mean_time
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 10;

-- Check index usage
SELECT schemaname, tablename, indexname, idx_scan, idx_tup_read, idx_tup_fetch
FROM pg_stat_user_indexes
ORDER BY idx_scan DESC;
```

#### Redis Optimization

```bash
# Check Redis memory usage
redis-cli info memory

# Check Redis performance
redis-cli info stats

# Monitor Redis commands
redis-cli monitor
```

#### Application Optimization

```python
# Enable connection pooling
DATABASE_CONFIG = {
    'pool_size': 20,
    'max_overflow': 30,
    'pool_pre_ping': True,
    'pool_recycle': 3600
}

# Enable caching
CACHE_CONFIG = {
    'default_timeout': 300,
    'key_prefix': 'svgx:',
    'serializer': 'json'
}

# Optimize WebSocket handling
WEBSOCKET_CONFIG = {
    'max_connections': 1000,
    'ping_interval': 30,
    'ping_timeout': 10
}
```

## Security

### Access Control

#### User Management

```bash
# Create admin user
curl -X POST \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin@example.com",
    "email": "admin@example.com",
    "password": "secure_password",
    "role": "admin"
  }' \
  http://localhost:8000/admin/users/

# List users
curl -H "Authorization: Bearer $ADMIN_TOKEN" \
  http://localhost:8000/admin/users/
```

#### Network Security

```yaml
# Network policies
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: svgx-network-policy
  namespace: svgx
spec:
  podSelector:
    matchLabels:
      app: svgx-engine
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: ingress-nginx
    ports:
    - protocol: TCP
      port: 8000
  egress:
  - to:
    - namespaceSelector:
        matchLabels:
          name: database
    ports:
    - protocol: TCP
      port: 5432
  - to:
    - namespaceSelector:
        matchLabels:
          name: redis
    ports:
    - protocol: TCP
      port: 6379
```

### SSL/TLS Configuration

```yaml
# TLS secret
apiVersion: v1
kind: Secret
metadata:
  name: svgx-tls
  namespace: svgx
type: kubernetes.io/tls
data:
  tls.crt: <base64-encoded-certificate>
  tls.key: <base64-encoded-private-key>
```

### Security Monitoring

```yaml
# Security alerts
- alert: SVGXEngineSuspiciousActivity
  expr: rate(svgx_engine_failed_logins_total[5m]) > 10
  for: 2m
  labels:
    severity: warning
  annotations:
    summary: "Suspicious login activity detected"
    description: "High rate of failed login attempts"

- alert: SVGXEngineRateLimitExceeded
  expr: rate(svgx_engine_rate_limit_hits_total[5m]) > 50
  for: 2m
  labels:
    severity: warning
  annotations:
    summary: "Rate limit exceeded"
    description: "High rate of rate limit violations"
```

## Disaster Recovery

### Backup Strategy

1. **Database Backups**: Daily automated backups
2. **State Backups**: Real-time state persistence
3. **Configuration Backups**: Version-controlled configuration
4. **Documentation**: Runbook and procedures

### Recovery Procedures

#### Complete System Recovery

```bash
# 1. Stop all services
kubectl scale deployment svgx-engine --replicas=0 -n svgx

# 2. Restore database
pg_restore -h postgres -U svgx_user -d svgx latest_backup.sql

# 3. Restore state
curl -X POST \
  -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/state/restore/latest_backup_id

# 4. Restart services
kubectl scale deployment svgx-engine --replicas=3 -n svgx

# 5. Verify recovery
curl -f http://localhost:8000/health/
```

#### Partial Recovery

```bash
# Recover specific canvas
curl -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"canvas_id": "canvas_123"}' \
  http://localhost:8000/state/restore/canvas_backup_id

# Recover user data
curl -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user_123"}' \
  http://localhost:8000/admin/users/restore/
```

### Business Continuity

1. **Multi-region deployment**: Deploy across multiple regions
2. **Load balancing**: Use global load balancers
3. **Data replication**: Replicate data across regions
4. **Failover procedures**: Automated failover mechanisms

## Support and Maintenance

### Regular Maintenance Tasks

1. **Security Updates**: Monthly security patches
2. **Database Maintenance**: Weekly database optimization
3. **Log Rotation**: Daily log management
4. **Backup Verification**: Weekly backup testing
5. **Performance Monitoring**: Continuous performance tracking

### Support Contacts

- **Technical Support**: tech-support@svgx-engine.com
- **Security Issues**: security@svgx-engine.com
- **Emergency**: +1-555-0123 (24/7)
- **Documentation**: https://docs.svgx-engine.com

### Escalation Procedures

1. **Level 1**: Basic troubleshooting and monitoring
2. **Level 2**: Advanced troubleshooting and configuration
3. **Level 3**: Development team and architecture
4. **Level 4**: Vendor support and external resources

## Conclusion

This operations guide provides comprehensive coverage of all operational aspects of the SVGX Engine. Regular review and updates of this guide ensure smooth operation and quick resolution of issues.

For additional support or questions, please refer to the documentation or contact the support team.
