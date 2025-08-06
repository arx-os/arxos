# 🚀 MCP-Engineering Production Deployment Guide

## Overview
This guide will help you deploy the MCP-Engineering integration to production. The system is 95% complete and ready for production use.

## ✅ Pre-Deployment Checklist

### 1. System Requirements
- [ ] Kubernetes cluster (or Docker Swarm)
- [ ] PostgreSQL 15+ database
- [ ] Redis 7+ instance
- [ ] Load balancer (nginx/HAProxy)
- [ ] SSL certificates
- [ ] Monitoring stack (Prometheus + Grafana)

### 2. Security Requirements
- [ ] JWT secret keys (production-grade)
- [ ] Database credentials
- [ ] API keys for external services
- [ ] SSL/TLS certificates
- [ ] Firewall rules

### 3. Infrastructure Requirements
- [ ] Minimum 4GB RAM per service
- [ ] 2 CPU cores per service
- [ ] 50GB storage for databases
- [ ] Network connectivity to external APIs

## 🏗️ Production Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Load Balancer │    │   MCP Service   │    │   PostgreSQL    │
│   (nginx/HA)    │◄──►│   (FastAPI)     │◄──►│   Database      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       ▼                       │
         │              ┌─────────────────┐              │
         │              │     Redis       │              │
         │              │   (Caching)     │              │
         │              └─────────────────┘              │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Prometheus    │    │     Grafana     │    │   MLflow        │
│   (Monitoring)  │    │   (Dashboards)  │    │   (ML Models)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 📋 Deployment Steps

### Step 1: Environment Setup

```bash
# Create production environment file
cat > .env.production << EOF
# Service Configuration
MCP_HOST=0.0.0.0
MCP_PORT=8001
MCP_RELOAD=false
LOG_LEVEL=INFO

# Database Configuration
DATABASE_URL=postgresql://mcp_user:${PROD_DB_PASSWORD}@postgres-prod:5432/mcp_db

# Redis Configuration
REDIS_URL=redis://redis-prod:6379

# JWT Configuration
JWT_SECRET_KEY=${PROD_JWT_SECRET}
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# Email Configuration
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=${PROD_SMTP_USER}
SMTP_PASSWORD=${PROD_SMTP_PASS}
FROM_EMAIL=noreply@arxos.com

# Cloud Storage
AWS_ACCESS_KEY_ID=${PROD_AWS_KEY}
AWS_SECRET_ACCESS_KEY=${PROD_AWS_SECRET}
AWS_REGION=us-east-1
AWS_S3_BUCKET=arxos-mcp-reports

# Monitoring
PROMETHEUS_URL=http://prometheus:9090
GRAFANA_URL=http://grafana:3000
EOF
```

### Step 2: Docker Compose Production

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  mcp-service:
    build: .
    image: arxos/mcp-service:latest
    ports:
      - "8001:8001"
    environment:
      - REDIS_URL=redis://redis-prod:6379
      - DATABASE_URL=postgresql://mcp_user:${PROD_DB_PASSWORD}@postgres-prod:5432/mcp_db
      - JWT_SECRET_KEY=${PROD_JWT_SECRET}
      - MCP_HOST=0.0.0.0
      - MCP_PORT=8001
      - MCP_RELOAD=false
      - LOG_LEVEL=INFO
    depends_on:
      - redis-prod
      - postgres-prod
    networks:
      - mcp-prod-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8001/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  redis-prod:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_prod_data:/data
    command: redis-server --appendonly yes --maxmemory 1gb --maxmemory-policy allkeys-lru
    networks:
      - mcp-prod-network
    restart: unless-stopped

  postgres-prod:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: mcp_db
      POSTGRES_USER: mcp_user
      POSTGRES_PASSWORD: ${PROD_DB_PASSWORD}
    ports:
      - "5432:5432"
    volumes:
      - postgres_prod_data:/var/lib/postgresql/data
    networks:
      - mcp-prod-network
    restart: unless-stopped

  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    networks:
      - mcp-prod-network
    restart: unless-stopped

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_USER=admin
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD}
    volumes:
      - grafana_data:/var/lib/grafana
    networks:
      - mcp-prod-network
    restart: unless-stopped

volumes:
  redis_prod_data:
    driver: local
  postgres_prod_data:
    driver: local
  prometheus_data:
    driver: local
  grafana_data:
    driver: local

networks:
  mcp-prod-network:
    driver: bridge
```

### Step 3: Kubernetes Deployment (Alternative)

```yaml
# k8s/mcp-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mcp-service
  namespace: arxos
spec:
  replicas: 3
  selector:
    matchLabels:
      app: mcp-service
  template:
    metadata:
      labels:
        app: mcp-service
    spec:
      containers:
      - name: mcp-service
        image: arxos/mcp-service:latest
        ports:
        - containerPort: 8001
        env:
        - name: REDIS_URL
          value: "redis://redis-prod:6379"
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: mcp-secrets
              key: database-url
        - name: JWT_SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: mcp-secrets
              key: jwt-secret
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
            port: 8001
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8001
          initialDelaySeconds: 5
          periodSeconds: 5
```

### Step 4: Database Migration

```bash
# Run database migrations
python -m alembic upgrade head

# Initialize knowledge base
python -c "
from knowledge.knowledge_base import KnowledgeBase
kb = KnowledgeBase()
kb.initialize_database()
print('✅ Knowledge base initialized')
"

# Initialize ML models
python -c "
from ml.model_manager import ModelManager
mm = ModelManager()
mm.initialize_models()
print('✅ ML models initialized')
"
```

### Step 5: Service Deployment

```bash
# Build production image
docker build -t arxos/mcp-service:latest .

# Push to registry
docker push arxos/mcp-service:latest

# Deploy with Docker Compose
docker-compose -f docker-compose.prod.yml up -d

# Or deploy with Kubernetes
kubectl apply -f k8s/
```

### Step 6: Load Balancer Configuration

```nginx
# nginx.conf
upstream mcp_backend {
    server mcp-service-1:8001;
    server mcp-service-2:8001;
    server mcp-service-3:8001;
}

server {
    listen 80;
    server_name mcp.arxos.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name mcp.arxos.com;

    ssl_certificate /etc/ssl/certs/mcp.arxos.com.crt;
    ssl_certificate_key /etc/ssl/private/mcp.arxos.com.key;

    location / {
        proxy_pass http://mcp_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /health {
        proxy_pass http://mcp_backend;
        access_log off;
    }

    location /metrics {
        proxy_pass http://mcp_backend;
        access_log off;
    }
}
```

## 🔍 Post-Deployment Verification

### 1. Health Checks
```bash
# Check service health
curl -f https://mcp.arxos.com/health

# Check API endpoints
curl -X POST https://mcp.arxos.com/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'

# Check WebSocket connection
wscat -c wss://mcp.arxos.com/api/v1/ws/validation/test
```

### 2. Performance Testing
```bash
# Run load tests
ab -n 1000 -c 10 https://mcp.arxos.com/health

# Test validation endpoint
curl -X POST https://mcp.arxos.com/api/v1/validate \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "building_data": {
      "area": 8000,
      "height": 25,
      "type": "commercial"
    },
    "validation_type": "structural"
  }'
```

### 3. Monitoring Verification
```bash
# Check Prometheus metrics
curl http://prometheus:9090/api/v1/query?query=up

# Check Grafana dashboards
curl -u admin:$GRAFANA_PASSWORD http://grafana:3000/api/dashboards

# Check Redis performance
redis-cli -h redis-prod info memory
```

## 📊 Production Monitoring

### Key Metrics to Monitor
- **Response Time**: < 200ms for validation requests
- **Throughput**: > 1000 requests/minute
- **Error Rate**: < 1%
- **Memory Usage**: < 80% of allocated
- **CPU Usage**: < 70% average
- **Database Connections**: < 80% of pool
- **Cache Hit Rate**: > 90%

### Alerting Rules
```yaml
# prometheus/alerts.yml
groups:
- name: mcp-service
  rules:
  - alert: MCPServiceDown
    expr: up{job="mcp-service"} == 0
    for: 1m
    labels:
      severity: critical
    annotations:
      summary: "MCP Service is down"

  - alert: HighResponseTime
    expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 0.5
    for: 2m
    labels:
      severity: warning
    annotations:
      summary: "High response time detected"

  - alert: HighErrorRate
    expr: rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m]) > 0.05
    for: 2m
    labels:
      severity: critical
    annotations:
      summary: "High error rate detected"
```

## 🔧 Maintenance Procedures

### Daily Tasks
- [ ] Check service health
- [ ] Review error logs
- [ ] Monitor performance metrics
- [ ] Verify backup status

### Weekly Tasks
- [ ] Review performance trends
- [ ] Update security patches
- [ ] Clean up old logs
- [ ] Verify SSL certificates

### Monthly Tasks
- [ ] Update ML models
- [ ] Review and update building codes
- [ ] Performance optimization
- [ ] Security audit

## 🚨 Troubleshooting

### Common Issues

#### 1. Service Won't Start
```bash
# Check logs
docker logs mcp-service

# Check dependencies
docker-compose ps

# Verify environment variables
docker exec mcp-service env | grep MCP
```

#### 2. Database Connection Issues
```bash
# Test database connection
docker exec postgres-prod pg_isready -U mcp_user -d mcp_db

# Check database logs
docker logs postgres-prod
```

#### 3. Redis Connection Issues
```bash
# Test Redis connection
docker exec redis-prod redis-cli ping

# Check Redis memory
docker exec redis-prod redis-cli info memory
```

#### 4. Performance Issues
```bash
# Check resource usage
docker stats

# Check slow queries
docker exec postgres-prod psql -U mcp_user -d mcp_db -c "SELECT * FROM pg_stat_activity WHERE state = 'active';"
```

## 📈 Scaling Guidelines

### Horizontal Scaling
- Add more MCP service replicas
- Use load balancer for distribution
- Implement database read replicas
- Add Redis cluster for caching

### Vertical Scaling
- Increase CPU/memory limits
- Optimize database queries
- Implement connection pooling
- Use SSD storage for databases

## 🔒 Security Checklist

- [ ] SSL/TLS certificates installed
- [ ] JWT secrets rotated regularly
- [ ] Database passwords strong
- [ ] Firewall rules configured
- [ ] API rate limiting enabled
- [ ] Input validation implemented
- [ ] SQL injection protection
- [ ] XSS protection enabled
- [ ] CORS properly configured
- [ ] Security headers set

## 📞 Support Contacts

- **Technical Support**: tech-support@arxos.com
- **Emergency**: oncall@arxos.com
- **Documentation**: docs.arxos.com/mcp
- **Monitoring**: grafana.arxos.com

---

**Status**: ✅ Ready for Production Deployment
**Next Steps**: Deploy to staging environment for final testing 