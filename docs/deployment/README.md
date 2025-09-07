# ArxOS Deployment Guide

## Table of Contents
- [Prerequisites](#prerequisites)
- [Configuration](#configuration)
- [Docker Deployment](#docker-deployment)
- [Kubernetes Deployment](#kubernetes-deployment)
- [Database Setup](#database-setup)
- [Environment Variables](#environment-variables)
- [Monitoring](#monitoring)
- [Security Considerations](#security-considerations)

## Prerequisites

### System Requirements
- **CPU**: 2+ cores recommended
- **RAM**: 4GB minimum, 8GB recommended
- **Storage**: 20GB minimum for database
- **OS**: Linux (Ubuntu 20.04+), macOS, Windows with WSL2

### Software Requirements
- PostgreSQL 14+
- Docker 20.10+ (for containerized deployment)
- Kubernetes 1.25+ (for K8s deployment)
- Rust 1.75+ (for source builds)

## Configuration

### config.toml
Create a `config.toml` file in the project root:

```toml
# ArxOS Configuration

[database]
url = "postgresql://arxos:password@localhost/arxos"
max_connections = 25
connection_timeout = 30

[api]
host = "0.0.0.0"
port = 3000
cors_origins = ["https://app.example.com"]

[logging]
level = "info"  # trace, debug, info, warn, error
format = "json" # json, compact, full

[market]
enable_trading = true
token_decimals = 8

[rating]
recalculation_interval = 3600  # seconds
cache_duration = 300  # seconds
```

## Docker Deployment

### Dockerfile
```dockerfile
# Build stage
FROM rust:1.75-slim as builder

WORKDIR /app
COPY Cargo.toml Cargo.lock ./
COPY src ./src

RUN apt-get update && apt-get install -y \
    pkg-config \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

RUN cargo build --release

# Runtime stage
FROM debian:bookworm-slim

RUN apt-get update && apt-get install -y \
    ca-certificates \
    libssl3 \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /app/target/release/arxos /usr/local/bin/arxos
COPY config.toml /etc/arxos/config.toml
COPY migrations /etc/arxos/migrations

EXPOSE 3000

ENV RUST_LOG=info
ENV RUST_LOG_JSON=1
ENV DATABASE_URL=postgresql://arxos:password@postgres/arxos

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:3000/api/health || exit 1

CMD ["arxos", "--api", "--config", "/etc/arxos/config.toml"]
```

### docker-compose.yml
```yaml
version: '3.8'

services:
  postgres:
    image: postgres:14-alpine
    environment:
      POSTGRES_DB: arxos
      POSTGRES_USER: arxos
      POSTGRES_PASSWORD: arxos_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./migrations:/docker-entrypoint-initdb.d
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U arxos"]
      interval: 10s
      timeout: 5s
      retries: 5

  arxos:
    build: .
    depends_on:
      postgres:
        condition: service_healthy
    environment:
      DATABASE_URL: postgresql://arxos:arxos_password@postgres/arxos
      RUST_LOG: info
      ARXOS_ENV: production
    ports:
      - "3000:3000"
    volumes:
      - ./config.toml:/etc/arxos/config.toml
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
```

### Running with Docker

```bash
# Build and start services
docker-compose up -d

# View logs
docker-compose logs -f arxos

# Run migrations
docker-compose exec postgres psql -U arxos -d arxos < /docker-entrypoint-initdb.d/001_initial.sql

# Scale API servers
docker-compose up -d --scale arxos=3
```

## Kubernetes Deployment

### namespace.yaml
```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: arxos
```

### configmap.yaml
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: arxos-config
  namespace: arxos
data:
  config.toml: |
    [database]
    url = "postgresql://arxos:password@postgres-service/arxos"
    max_connections = 25
    
    [api]
    host = "0.0.0.0"
    port = 3000
    
    [logging]
    level = "info"
    format = "json"
```

### deployment.yaml
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: arxos-api
  namespace: arxos
spec:
  replicas: 3
  selector:
    matchLabels:
      app: arxos-api
  template:
    metadata:
      labels:
        app: arxos-api
    spec:
      containers:
      - name: arxos
        image: arxos:latest
        ports:
        - containerPort: 3000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: arxos-secrets
              key: database-url
        - name: RUST_LOG
          value: "info"
        - name: ARXOS_ENV
          value: "production"
        volumeMounts:
        - name: config
          mountPath: /etc/arxos
        livenessProbe:
          httpGet:
            path: /api/health/live
            port: 3000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /api/health/ready
            port: 3000
          initialDelaySeconds: 5
          periodSeconds: 5
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
      volumes:
      - name: config
        configMap:
          name: arxos-config
```

### service.yaml
```yaml
apiVersion: v1
kind: Service
metadata:
  name: arxos-service
  namespace: arxos
spec:
  selector:
    app: arxos-api
  ports:
  - protocol: TCP
    port: 80
    targetPort: 3000
  type: LoadBalancer
```

### ingress.yaml
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: arxos-ingress
  namespace: arxos
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  tls:
  - hosts:
    - api.arxos.io
    secretName: arxos-tls
  rules:
  - host: api.arxos.io
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: arxos-service
            port:
              number: 80
```

### Deploy to Kubernetes

```bash
# Create namespace
kubectl apply -f namespace.yaml

# Create secrets
kubectl create secret generic arxos-secrets \
  --from-literal=database-url='postgresql://user:pass@host/db' \
  -n arxos

# Deploy application
kubectl apply -f configmap.yaml
kubectl apply -f deployment.yaml
kubectl apply -f service.yaml
kubectl apply -f ingress.yaml

# Check status
kubectl get pods -n arxos
kubectl logs -f deployment/arxos-api -n arxos
```

## Database Setup

### Initial Setup
```bash
# Create database and user
sudo -u postgres psql <<EOF
CREATE USER arxos WITH PASSWORD 'secure_password';
CREATE DATABASE arxos OWNER arxos;
GRANT ALL PRIVILEGES ON DATABASE arxos TO arxos;
EOF

# Run migrations
for file in migrations/*.sql; do
    psql -U arxos -d arxos -f "$file"
done
```

### Backup Strategy
```bash
# Backup database
pg_dump -U arxos -d arxos -F custom -f arxos_backup_$(date +%Y%m%d).dump

# Restore database
pg_restore -U arxos -d arxos -c arxos_backup_20240115.dump

# Automated daily backups
cat <<EOF > /etc/cron.d/arxos-backup
0 2 * * * postgres pg_dump -U arxos -d arxos -F custom -f /backups/arxos_\$(date +\%Y\%m\%d).dump
EOF
```

### Performance Tuning
```sql
-- PostgreSQL configuration (postgresql.conf)
shared_buffers = 256MB
effective_cache_size = 1GB
maintenance_work_mem = 64MB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100
random_page_cost = 1.1
effective_io_concurrency = 200
min_wal_size = 1GB
max_wal_size = 4GB
max_worker_processes = 8
max_parallel_workers_per_gather = 4
max_parallel_workers = 8
max_parallel_maintenance_workers = 4
```

## Environment Variables

### Required Variables
```bash
DATABASE_URL=postgresql://user:password@host:5432/arxos
ARXOS_ENV=production|development|staging
```

### Optional Variables
```bash
# Logging
RUST_LOG=info|debug|trace|warn|error
RUST_LOG_JSON=1  # Enable JSON logging

# API Configuration
API_HOST=0.0.0.0
API_PORT=3000
API_KEY_SECRET=your-secret-key

# Rate Limiting
RATE_LIMIT_PER_MINUTE=100
RATE_LIMIT_BURST=200

# Market Configuration
ENABLE_TRADING=true
MARKET_DATA_CACHE_TTL=300

# External Services
WEBHOOK_TIMEOUT=30
WEBHOOK_MAX_RETRIES=3
```

## Monitoring

### Prometheus Metrics
```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'arxos'
    static_configs:
      - targets: ['arxos-service:3000']
    metrics_path: '/metrics'
```

### Grafana Dashboard
Import the ArxOS dashboard (ID: 12345) or create custom panels:

- Request rate and latency
- Database connection pool usage
- BILT rating calculations per minute
- Token distributions
- Active webhooks
- Error rates by endpoint

### Logging with ELK Stack
```yaml
# filebeat.yml
filebeat.inputs:
- type: container
  paths:
    - '/var/lib/docker/containers/*/*.log'
  processors:
    - add_kubernetes_metadata:
        host: ${NODE_NAME}
        matchers:
        - logs_path:
            logs_path: "/var/log/containers/"

output.elasticsearch:
  hosts: ['elasticsearch:9200']
```

## Security Considerations

### API Security
1. **Use HTTPS in production** - Configure TLS certificates
2. **API Key Rotation** - Rotate keys regularly
3. **Rate Limiting** - Prevent abuse
4. **Input Validation** - Sanitize all inputs
5. **SQL Injection Prevention** - Use parameterized queries

### Database Security
```sql
-- Create read-only user for analytics
CREATE USER arxos_readonly WITH PASSWORD 'secure_password';
GRANT CONNECT ON DATABASE arxos TO arxos_readonly;
GRANT USAGE ON SCHEMA public TO arxos_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO arxos_readonly;

-- Revoke unnecessary permissions
REVOKE CREATE ON SCHEMA public FROM PUBLIC;
```

### Network Security
```yaml
# NetworkPolicy for Kubernetes
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: arxos-netpol
  namespace: arxos
spec:
  podSelector:
    matchLabels:
      app: arxos-api
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: nginx-ingress
    ports:
    - protocol: TCP
      port: 3000
  egress:
  - to:
    - podSelector:
        matchLabels:
          app: postgres
    ports:
    - protocol: TCP
      port: 5432
```

### Secrets Management
```bash
# Use Kubernetes secrets
kubectl create secret generic arxos-secrets \
  --from-literal=database-url='...' \
  --from-literal=api-key-secret='...' \
  -n arxos

# Or use external secret manager (HashiCorp Vault)
vault kv put secret/arxos database_url="..." api_key="..."
```

## Troubleshooting

### Common Issues

**Database Connection Failed**
```bash
# Check PostgreSQL is running
systemctl status postgresql

# Test connection
psql -U arxos -h localhost -d arxos -c "SELECT 1"

# Check connection string
echo $DATABASE_URL
```

**High Memory Usage**
```bash
# Check memory usage
docker stats arxos

# Adjust connection pool
# In config.toml: max_connections = 10
```

**Slow API Response**
```bash
# Check database indexes
psql -U arxos -d arxos -c "
  SELECT schemaname, tablename, indexname, idx_scan
  FROM pg_stat_user_indexes
  ORDER BY idx_scan;
"

# Add missing indexes
psql -U arxos -d arxos -c "
  CREATE INDEX CONCURRENTLY idx_objects_path 
  ON building_objects(path);
"
```

## Performance Optimization

### Caching Strategy
- Use Redis for session storage
- Cache BILT ratings for 5 minutes
- Cache market data for 1 minute
- Use CDN for static assets

### Database Optimization
- Regular VACUUM and ANALYZE
- Partition large tables by date
- Use connection pooling
- Optimize queries with EXPLAIN ANALYZE

### Horizontal Scaling
- Scale API servers (3-5 instances)
- Use load balancer (nginx, HAProxy)
- Implement database read replicas
- Use message queue for async operations