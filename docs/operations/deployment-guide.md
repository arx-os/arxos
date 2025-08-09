# Production Deployment Guide for Enterprise Features

## 🚀 **Enterprise Features Production Deployment**

This guide provides step-by-step instructions for deploying the Arxos enterprise features to production environments.

---

## 📋 **Prerequisites**

### **System Requirements**
- **CPU**: 4+ cores (8+ recommended for high load)
- **RAM**: 16GB+ (32GB+ for enterprise deployments)
- **Storage**: 100GB+ SSD storage
- **Network**: High-speed internet connection
- **OS**: Linux (Ubuntu 20.04+ or CentOS 8+)

### **Software Requirements**
- **Docker**: 20.10+
- **Docker Compose**: 2.0+
- **Kubernetes**: 1.24+ (for K8s deployment)
- **PostgreSQL**: 14+ with PostGIS extension
- **Redis**: 6.2+
- **Prometheus**: 2.40+
- **Grafana**: 9.0+
- **Jaeger**: 1.40+

---

## 🔧 **Deployment Options**

### **Option 1: Docker Compose Deployment (Recommended for SMEs)**

#### **Step 1: Environment Setup**
```bash
# Clone the repository
git clone https://github.com/your-org/arxos.git
cd arxos

# Create production environment file
cp .env.example .env.production

# Configure production environment variables
cat > .env.production << EOF
# Database Configuration
DATABASE_URL=postgresql://arxos:secure_password@postgres:5432/arxos
REDIS_URL=redis://redis:6379

# Security Configuration
JWT_SECRET=your_super_secure_jwt_secret_here
ENCRYPTION_KEY=your_32_byte_encryption_key_here

# Monitoring Configuration
PROMETHEUS_ENABLED=true
JAEGER_ENABLED=true
GRAFANA_ENABLED=true

# Enterprise Features Configuration
CIRCUIT_BREAKER_ENABLED=true
RETRY_MECHANISM_ENABLED=true
HEALTH_CHECK_ENABLED=true
RATE_LIMITING_ENABLED=true

# Alerting Configuration
SLACK_WEBHOOK_URL=your_slack_webhook_url
EMAIL_SMTP_SERVER=smtp.gmail.com
EMAIL_SMTP_PORT=587
EMAIL_USERNAME=alerts@yourcompany.com
EMAIL_PASSWORD=your_email_password
EOF
```

#### **Step 2: Production Docker Compose**
```yaml
# docker-compose.production.yml
version: '3.8'

services:
  # Core Arxos Services with Enterprise Features
  svgx-engine:
    build:
      context: .
      dockerfile: Dockerfile.production
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - JWT_SECRET=${JWT_SECRET}
      - ENCRYPTION_KEY=${ENCRYPTION_KEY}
      - CIRCUIT_BREAKER_ENABLED=${CIRCUIT_BREAKER_ENABLED}
      - RETRY_MECHANISM_ENABLED=${RETRY_MECHANISM_ENABLED}
      - HEALTH_CHECK_ENABLED=${HEALTH_CHECK_ENABLED}
      - RATE_LIMITING_ENABLED=${RATE_LIMITING_ENABLED}
    depends_on:
      - postgres
      - redis
      - prometheus
      - jaeger
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Database
  postgres:
    image: postgis/postgis:15-3.3
    environment:
      - POSTGRES_DB=arxos
      - POSTGRES_USER=arxos
      - POSTGRES_PASSWORD=secure_password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

  # Cache
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped

  # Monitoring Stack
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./infrastructure/monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    restart: unless-stopped

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3001:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana_data:/var/lib/grafana
      - ./infrastructure/monitoring/grafana/dashboards:/etc/grafana/provisioning/dashboards
    restart: unless-stopped

  jaeger:
    image: jaegertracing/all-in-one:latest
    ports:
      - "16686:16686"
      - "6831:6831/udp"
    environment:
      - COLLECTOR_OTLP_ENABLED=true
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
  prometheus_data:
  grafana_data:
```

#### **Step 3: Deploy**
```bash
# Deploy with production configuration
docker-compose -f docker-compose.production.yml --env-file .env.production up -d

# Verify deployment
docker-compose -f docker-compose.production.yml ps

# Check logs
docker-compose -f docker-compose.production.yml logs -f svgx-engine
```

### **Option 2: Kubernetes Deployment (Recommended for Enterprise)**

#### **Step 1: Create Kubernetes Manifests**
```yaml
# k8s/namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: arxos-enterprise
```

```yaml
# k8s/configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: arxos-config
  namespace: arxos-enterprise
data:
  DATABASE_URL: "postgresql://arxos:secure_password@postgres:5432/arxos"
  REDIS_URL: "redis://redis:6379"
  CIRCUIT_BREAKER_ENABLED: "true"
  RETRY_MECHANISM_ENABLED: "true"
  HEALTH_CHECK_ENABLED: "true"
  RATE_LIMITING_ENABLED: "true"
```

```yaml
# k8s/secret.yaml
apiVersion: v1
kind: Secret
metadata:
  name: arxos-secrets
  namespace: arxos-enterprise
type: Opaque
data:
  JWT_SECRET: <base64-encoded-jwt-secret>
  ENCRYPTION_KEY: <base64-encoded-encryption-key>
```

```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: svgx-engine
  namespace: arxos-enterprise
spec:
  replicas: 3
  selector:
    matchLabels:
      app: svgx-engine
  template:
    metadata:
      labels:
        app: svgx-engine
    spec:
      containers:
      - name: svgx-engine
        image: arxos/svgx-engine:latest
        ports:
        - containerPort: 8000
        envFrom:
        - configMapRef:
            name: arxos-config
        - secretRef:
            name: arxos-secrets
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
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
```

```yaml
# k8s/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: svgx-engine-service
  namespace: arxos-enterprise
spec:
  selector:
    app: svgx-engine
  ports:
  - port: 80
    targetPort: 8000
  type: LoadBalancer
```

#### **Step 2: Deploy to Kubernetes**
```bash
# Apply Kubernetes manifests
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secret.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml

# Verify deployment
kubectl get pods -n arxos-enterprise
kubectl get services -n arxos-enterprise
```

---

## 🔒 **Security Configuration**

### **SSL/TLS Configuration**
```nginx
# nginx.conf
server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /etc/ssl/certs/your-cert.pem;
    ssl_certificate_key /etc/ssl/private/your-key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;

    location / {
        proxy_pass http://svgx-engine:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### **Firewall Configuration**
```bash
# UFW Firewall Rules
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw allow 8000/tcp  # Arxos API
sudo ufw allow 9090/tcp  # Prometheus
sudo ufw allow 3001/tcp  # Grafana
sudo ufw enable
```

---

## 📊 **Monitoring Setup**

### **Prometheus Configuration**
```yaml
# prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "alert_rules.yml"

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093

scrape_configs:
  - job_name: 'arxos-enterprise'
    static_configs:
      - targets: ['svgx-engine:8000']
    metrics_path: '/metrics'
    scrape_interval: 5s

  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres:5432']

  - job_name: 'redis'
    static_configs:
      - targets: ['redis:6379']
```

### **Grafana Dashboards**
```json
{
  "dashboard": {
    "title": "Arxos Enterprise Metrics",
    "panels": [
      {
        "title": "Circuit Breaker Status",
        "type": "stat",
        "targets": [
          {
            "expr": "arxos_circuit_breaker_state",
            "legendFormat": "{{service}}"
          }
        ]
      },
      {
        "title": "Request Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(arxos_requests_total[5m])",
            "legendFormat": "{{endpoint}}"
          }
        ]
      },
      {
        "title": "Error Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(arxos_errors_total[5m])",
            "legendFormat": "{{error_type}}"
          }
        ]
      }
    ]
  }
}
```

---

## 🚨 **Alerting Configuration**

### **Alert Rules**
```yaml
# alert_rules.yml
groups:
  - name: arxos_alerts
    rules:
      - alert: HighErrorRate
        expr: rate(arxos_errors_total[5m]) > 0.1
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value }} errors per second"

      - alert: CircuitBreakerOpen
        expr: arxos_circuit_breaker_state == 2
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Circuit breaker is open"
          description: "Circuit breaker for {{ $labels.service }} is open"

      - alert: HighMemoryUsage
        expr: (node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes) / node_memory_MemTotal_bytes > 0.9
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High memory usage"
          description: "Memory usage is {{ $value | humanizePercentage }}"
```

---

## 🔄 **CI/CD Pipeline**

### **GitHub Actions Workflow**
```yaml
# .github/workflows/deploy-enterprise.yml
name: Deploy Enterprise Features

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    - name: Install dependencies
      run: |
        pip install -r requirements-enterprise.txt
    - name: Run enterprise tests
      run: |
        python test_enterprise_features_simple.py

  security-scan:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - name: Run security scan
      uses: snyk/actions/python@master
      env:
        SNYK_TOKEN: ${{ secrets.SNYK_TOKEN }}

  deploy:
    needs: [test, security-scan]
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
    - uses: actions/checkout@v3
    - name: Deploy to production
      run: |
        # Deploy to your production environment
        echo "Deploying enterprise features to production"
```

---

## 📋 **Post-Deployment Checklist**

### **✅ Health Checks**
- [ ] All services are running and healthy
- [ ] Database connections are established
- [ ] Redis cache is accessible
- [ ] Prometheus metrics are being collected
- [ ] Grafana dashboards are populated
- [ ] Jaeger tracing is working

### **✅ Security Verification**
- [ ] SSL/TLS certificates are valid
- [ ] Firewall rules are properly configured
- [ ] JWT tokens are being generated and validated
- [ ] Rate limiting is active
- [ ] Input validation is working
- [ ] Audit logging is enabled

### **✅ Performance Validation**
- [ ] Response times are within acceptable limits
- [ ] Circuit breakers are functioning properly
- [ ] Retry mechanisms are working
- [ ] Graceful degradation is operational
- [ ] Memory usage is stable
- [ ] CPU usage is reasonable

### **✅ Monitoring Verification**
- [ ] Alerts are configured and tested
- [ ] Dashboards are displaying correct data
- [ ] Log aggregation is working
- [ ] Error tracking is functional
- [ ] Performance profiling is active

---

## 🆘 **Troubleshooting**

### **Common Issues and Solutions**

#### **1. Circuit Breaker Not Working**
```bash
# Check circuit breaker configuration
curl -X GET "http://localhost:8000/health/circuit-breakers"

# Verify metrics
curl -X GET "http://localhost:9090/api/v1/query?query=arxos_circuit_breaker_state"
```

#### **2. High Memory Usage**
```bash
# Check memory usage
docker stats

# Restart services if needed
docker-compose restart svgx-engine
```

#### **3. Database Connection Issues**
```bash
# Check database connectivity
docker exec -it postgres psql -U arxos -d arxos -c "SELECT 1;"

# Verify connection pool
curl -X GET "http://localhost:8000/health/database"
```

#### **4. Monitoring Not Working**
```bash
# Check Prometheus targets
curl -X GET "http://localhost:9090/api/v1/targets"

# Verify Grafana data sources
curl -X GET "http://localhost:3001/api/datasources"
```

---

## 📞 **Support and Maintenance**

### **Contact Information**
- **Technical Support**: tech-support@arxos.com
- **Security Issues**: security@arxos.com
- **Performance Issues**: performance@arxos.com

### **Maintenance Schedule**
- **Daily**: Health check verification
- **Weekly**: Performance review and optimization
- **Monthly**: Security updates and compliance checks
- **Quarterly**: Full system audit and capacity planning

---

**Last Updated**: December 2024
**Version**: 1.0.0
**Status**: ✅ **Production Ready**
