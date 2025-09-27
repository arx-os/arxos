# ArxOS Deployment Guide

## Overview

This guide covers deploying ArxOS in various environments, from development to production.

## Prerequisites

### System Requirements

#### Minimum Requirements
- **CPU**: 2 cores
- **Memory**: 4GB RAM
- **Storage**: 20GB SSD
- **OS**: Linux (Ubuntu 20.04+), macOS, or Windows

#### Recommended Requirements
- **CPU**: 4+ cores
- **Memory**: 8GB+ RAM
- **Storage**: 100GB+ SSD
- **OS**: Linux (Ubuntu 22.04+)

### Software Dependencies

- **Go**: 1.21 or later
- **Docker**: 20.10 or later
- **Docker Compose**: 2.0 or later
- **PostgreSQL**: 13+ with PostGIS extension
- **Redis**: 6.0 or later (optional)

## Development Deployment

### Local Development

#### 1. Clone Repository
```bash
git clone https://github.com/arx-os/arxos.git
cd arxos
```

#### 2. Environment Setup
```bash
# Copy environment template
cp env.example .env

# Edit configuration
nano .env
```

#### 3. Start Services
```bash
# Start development environment
docker-compose -f docker/docker-compose.dev.yml up -d

# Check services
docker-compose -f docker/docker-compose.dev.yml ps
```

#### 4. Run Migrations
```bash
# Run database migrations
go run cmd/arx/main.go migrate up

# Seed test data (optional)
go run cmd/arx/main.go seed test-data
```

#### 5. Start Application
```bash
# Start in development mode
go run cmd/arx/main.go daemon start --config configs/development.yml

# Or use air for hot reload
air -c .air.toml
```

### Docker Development

#### 1. Build Image
```bash
# Build development image
docker build -f Dockerfile.dev -t arxos:dev .

# Or use docker-compose
docker-compose -f docker/docker-compose.dev.yml build
```

#### 2. Run Container
```bash
# Run with docker-compose
docker-compose -f docker/docker-compose.dev.yml up

# Or run directly
docker run -p 8080:8080 --env-file .env arxos:dev
```

## Staging Deployment

### Docker Compose

#### 1. Configuration
```yaml
# docker-compose.staging.yml
version: '3.8'

services:
  arxos:
    image: arxos:staging
    ports:
      - "8080:8080"
    environment:
      - ENV=staging
      - DATABASE_URL=postgres://arxos:${POSTGRES_PASSWORD}@postgres:5432/arxos
      - REDIS_URL=redis://redis:6379
    depends_on:
      - postgres
      - redis
    volumes:
      - ./configs:/app/configs
      - ./logs:/app/logs
    restart: unless-stopped

  postgres:
    image: postgis/postgis:15-3.3
    environment:
      - POSTGRES_DB=arxos
      - POSTGRES_USER=arxos
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./scripts/init-postgis.sql:/docker-entrypoint-initdb.d/init-postgis.sql
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./configs/nginx:/etc/nginx
      - ./ssl:/etc/ssl
    depends_on:
      - arxos
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
```

#### 2. Deploy
```bash
# Set environment variables
export POSTGRES_PASSWORD=$(openssl rand -base64 32)

# Deploy services
docker-compose -f docker-compose.staging.yml up -d

# Run migrations
docker-compose -f docker-compose.staging.yml exec arxos arx migrate up

# Check status
docker-compose -f docker-compose.staging.yml ps
```

### Kubernetes

#### 1. Namespace
```yaml
# k8s/namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: arxos-staging
```

#### 2. ConfigMap
```yaml
# k8s/configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: arxos-config
  namespace: arxos-staging
data:
  config.yaml: |
    api:
      host: "0.0.0.0"
      port: 8080
    database:
      host: "postgres"
      port: 5432
      database: "arxos"
    redis:
      host: "redis"
      port: 6379
```

#### 3. Secret
```yaml
# k8s/secret.yaml
apiVersion: v1
kind: Secret
metadata:
  name: arxos-secrets
  namespace: arxos-staging
type: Opaque
data:
  database-password: <base64-encoded-password>
  jwt-secret: <base64-encoded-jwt-secret>
  redis-password: <base64-encoded-redis-password>
```

#### 4. Deployment
```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: arxos
  namespace: arxos-staging
spec:
  replicas: 2
  selector:
    matchLabels:
      app: arxos
  template:
    metadata:
      labels:
        app: arxos
    spec:
      containers:
      - name: arxos
        image: arxos:staging
        ports:
        - containerPort: 8080
        env:
        - name: DATABASE_PASSWORD
          valueFrom:
            secretKeyRef:
              name: arxos-secrets
              key: database-password
        - name: JWT_SECRET
          valueFrom:
            secretKeyRef:
              name: arxos-secrets
              key: jwt-secret
        volumeMounts:
        - name: config
          mountPath: /app/configs
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 5
      volumes:
      - name: config
        configMap:
          name: arxos-config
```

#### 5. Service
```yaml
# k8s/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: arxos-service
  namespace: arxos-staging
spec:
  selector:
    app: arxos
  ports:
  - port: 80
    targetPort: 8080
  type: ClusterIP
```

#### 6. Deploy
```bash
# Apply configurations
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secret.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml

# Check deployment
kubectl get pods -n arxos-staging
kubectl get services -n arxos-staging
```

## Production Deployment

### Docker Compose Production

#### 1. Production Configuration
```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  arxos:
    image: arxos:latest
    ports:
      - "8080:8080"
    environment:
      - ENV=production
      - DATABASE_URL=postgres://arxos:${POSTGRES_PASSWORD}@postgres:5432/arxos
      - REDIS_URL=redis://redis:6379
    depends_on:
      - postgres
      - redis
    volumes:
      - ./configs:/app/configs
      - ./logs:/app/logs
      - ./ssl:/app/ssl
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: '1.0'
        reservations:
          memory: 1G
          cpus: '0.5'

  postgres:
    image: postgis/postgis:15-3.3
    environment:
      - POSTGRES_DB=arxos
      - POSTGRES_USER=arxos
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./backups:/backups
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 4G
          cpus: '2.0'
        reservations:
          memory: 2G
          cpus: '1.0'

  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis_data:/data
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 1G
          cpus: '0.5'
        reservations:
          memory: 512M
          cpus: '0.25'

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./configs/nginx:/etc/nginx
      - ./ssl:/etc/ssl
      - ./logs/nginx:/var/log/nginx
    depends_on:
      - arxos
    restart: unless-stopped

  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./configs/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
    restart: unless-stopped

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD}
    volumes:
      - grafana_data:/var/lib/grafana
      - ./configs/grafana:/etc/grafana/provisioning
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
  prometheus_data:
  grafana_data:
```

#### 2. Deploy Production
```bash
# Set production environment variables
export POSTGRES_PASSWORD=$(openssl rand -base64 32)
export REDIS_PASSWORD=$(openssl rand -base64 32)
export GRAFANA_PASSWORD=$(openssl rand -base64 32)

# Deploy production stack
docker-compose -f docker-compose.prod.yml up -d

# Run migrations
docker-compose -f docker-compose.prod.yml exec arxos arx migrate up

# Check all services
docker-compose -f docker-compose.prod.yml ps
```

### Kubernetes Production

#### 1. Production Namespace
```yaml
# k8s/production/namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: arxos-production
  labels:
    environment: production
```

#### 2. Production ConfigMap
```yaml
# k8s/production/configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: arxos-config
  namespace: arxos-production
data:
  config.yaml: |
    api:
      host: "0.0.0.0"
      port: 8080
      tls:
        enabled: true
        cert_file: "/app/ssl/tls.crt"
        key_file: "/app/ssl/tls.key"
    database:
      host: "postgres"
      port: 5432
      database: "arxos"
      ssl_mode: "require"
      max_connections: 25
    redis:
      host: "redis"
      port: 6379
      password: "${REDIS_PASSWORD}"
    logging:
      level: "info"
      format: "json"
    monitoring:
      enabled: true
      prometheus:
        enabled: true
        port: 9090
```

#### 3. Production Secret
```yaml
# k8s/production/secret.yaml
apiVersion: v1
kind: Secret
metadata:
  name: arxos-secrets
  namespace: arxos-production
type: Opaque
data:
  database-password: <base64-encoded-password>
  jwt-secret: <base64-encoded-jwt-secret>
  redis-password: <base64-encoded-redis-password>
  tls-cert: <base64-encoded-tls-cert>
  tls-key: <base64-encoded-tls-key>
```

#### 4. Production Deployment
```yaml
# k8s/production/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: arxos
  namespace: arxos-production
spec:
  replicas: 3
  selector:
    matchLabels:
      app: arxos
  template:
    metadata:
      labels:
        app: arxos
    spec:
      containers:
      - name: arxos
        image: arxos:latest
        ports:
        - containerPort: 8080
        - containerPort: 9090
        env:
        - name: DATABASE_PASSWORD
          valueFrom:
            secretKeyRef:
              name: arxos-secrets
              key: database-password
        - name: JWT_SECRET
          valueFrom:
            secretKeyRef:
              name: arxos-secrets
              key: jwt-secret
        - name: REDIS_PASSWORD
          valueFrom:
            secretKeyRef:
              name: arxos-secrets
              key: redis-password
        volumeMounts:
        - name: config
          mountPath: /app/configs
        - name: ssl
          mountPath: /app/ssl
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 60
          periodSeconds: 30
          timeoutSeconds: 10
          failureThreshold: 3
        readinessProbe:
          httpGet:
            path: /ready
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3
      volumes:
      - name: config
        configMap:
          name: arxos-config
      - name: ssl
        secret:
          secretName: arxos-secrets
          items:
          - key: tls-cert
            path: tls.crt
          - key: tls-key
            path: tls.key
```

#### 5. Production Service
```yaml
# k8s/production/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: arxos-service
  namespace: arxos-production
spec:
  selector:
    app: arxos
  ports:
  - name: http
    port: 80
    targetPort: 8080
  - name: https
    port: 443
    targetPort: 8080
  type: LoadBalancer
```

#### 6. Ingress
```yaml
# k8s/production/ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: arxos-ingress
  namespace: arxos-production
  annotations:
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    nginx.ingress.kubernetes.io/force-ssl-redirect: "true"
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
spec:
  tls:
  - hosts:
    - api.arxos.com
    secretName: arxos-tls
  rules:
  - host: api.arxos.com
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

## Monitoring and Observability

### Prometheus Configuration
```yaml
# configs/prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "alerts.yml"

scrape_configs:
  - job_name: 'arxos'
    static_configs:
      - targets: ['arxos:8080']
    metrics_path: /metrics
    scrape_interval: 5s

  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres:5432']

  - job_name: 'redis'
    static_configs:
      - targets: ['redis:6379']
```

### Grafana Dashboards
```json
{
  "dashboard": {
    "title": "ArxOS Production Dashboard",
    "panels": [
      {
        "title": "Request Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(http_requests_total[5m])",
            "legendFormat": "{{method}} {{endpoint}}"
          }
        ]
      },
      {
        "title": "Response Time",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))",
            "legendFormat": "95th percentile"
          }
        ]
      }
    ]
  }
}
```

## Backup and Recovery

### Database Backup
```bash
# Create backup script
#!/bin/bash
# scripts/backup.sh

BACKUP_DIR="/backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="arxos_backup_${DATE}.sql"

# Create backup
docker-compose exec postgres pg_dump -U arxos arxos > "${BACKUP_DIR}/${BACKUP_FILE}"

# Compress backup
gzip "${BACKUP_DIR}/${BACKUP_FILE}"

# Keep only last 7 days
find "${BACKUP_DIR}" -name "arxos_backup_*.sql.gz" -mtime +7 -delete

echo "Backup completed: ${BACKUP_FILE}.gz"
```

### Application Backup
```bash
# Backup application data
#!/bin/bash
# scripts/app-backup.sh

BACKUP_DIR="/backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="arxos_app_${DATE}.tar.gz"

# Create application backup
tar -czf "${BACKUP_DIR}/${BACKUP_FILE}" \
  --exclude="node_modules" \
  --exclude=".git" \
  /app

echo "Application backup completed: ${BACKUP_FILE}"
```

### Recovery
```bash
# Restore database
#!/bin/bash
# scripts/restore.sh

BACKUP_FILE=$1
if [ -z "$BACKUP_FILE" ]; then
  echo "Usage: $0 <backup_file>"
  exit 1
fi

# Restore database
docker-compose exec -T postgres psql -U arxos arxos < "${BACKUP_FILE}"

echo "Database restored from: ${BACKUP_FILE}"
```

## Security Considerations

### SSL/TLS Configuration
```yaml
# configs/nginx/ssl.conf
server {
    listen 443 ssl http2;
    server_name api.arxos.com;
    
    ssl_certificate /etc/ssl/tls.crt;
    ssl_certificate_key /etc/ssl/tls.key;
    
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;
    ssl_prefer_server_ciphers off;
    
    location / {
        proxy_pass http://arxos:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Environment Security
```bash
# Secure environment variables
export POSTGRES_PASSWORD=$(openssl rand -base64 32)
export JWT_SECRET=$(openssl rand -base64 64)
export REDIS_PASSWORD=$(openssl rand -base64 32)

# Set file permissions
chmod 600 .env
chmod 600 configs/*.yml
```

## Troubleshooting

### Common Issues

#### Database Connection Issues
```bash
# Check database connectivity
docker-compose exec arxos arx system health

# Check database logs
docker-compose logs postgres

# Test database connection
docker-compose exec arxos arx config test database
```

#### Application Issues
```bash
# Check application logs
docker-compose logs arxos

# Check application status
docker-compose exec arxos arx system status

# Restart application
docker-compose restart arxos
```

#### Performance Issues
```bash
# Check resource usage
docker stats

# Check database performance
docker-compose exec postgres psql -U arxos -d arxos -c "SELECT * FROM pg_stat_activity;"

# Check application metrics
curl http://localhost:8080/metrics
```

### Log Analysis
```bash
# View logs with filtering
docker-compose logs arxos | grep ERROR

# Follow logs in real-time
docker-compose logs -f arxos

# Export logs
docker-compose logs arxos > arxos.log
```

This deployment guide provides comprehensive information for deploying ArxOS in various environments with proper monitoring, security, and backup strategies.
