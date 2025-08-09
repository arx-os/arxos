# Production Deployment Guide

## 🎯 **Overview**

This guide provides comprehensive instructions for deploying Arxos in production environments. It covers system requirements, deployment procedures, configuration management, and monitoring setup.

**Deployment Methods:**
- **Docker Compose**: Simple, single-server deployment
- **Kubernetes**: Scalable, multi-server deployment
- **Cloud Platforms**: AWS, Azure, GCP deployment
- **On-Premises**: Traditional server deployment

---

## 📋 **System Requirements**

### **Minimum Requirements**

#### **Single Server Deployment**
- **CPU**: 4 cores (2.4 GHz or higher)
- **RAM**: 8 GB
- **Storage**: 100 GB SSD
- **Network**: 100 Mbps
- **OS**: Ubuntu 20.04 LTS or CentOS 8

#### **Multi-Server Deployment**
- **Load Balancer**: 2 cores, 4 GB RAM
- **Application Servers**: 4+ cores, 8+ GB RAM each
- **Database Server**: 8+ cores, 16+ GB RAM, 500+ GB SSD
- **Cache Server**: 2+ cores, 4+ GB RAM
- **Storage**: 1+ TB SSD storage

### **Recommended Requirements**

#### **Production Environment**
- **CPU**: 8+ cores per server
- **RAM**: 16+ GB per server
- **Storage**: 1+ TB NVMe SSD
- **Network**: 1 Gbps
- **OS**: Ubuntu 22.04 LTS or RHEL 9

#### **High Availability**
- **Load Balancer**: 4+ cores, 8+ GB RAM
- **Application Servers**: 8+ cores, 32+ GB RAM each
- **Database Server**: 16+ cores, 64+ GB RAM, 2+ TB NVMe SSD
- **Cache Cluster**: 4+ cores, 16+ GB RAM each
- **Storage**: 5+ TB NVMe SSD storage

---

## 🐳 **Docker Compose Deployment**

### **Quick Start**

#### **1. Download Configuration**
```bash
# Clone the repository
git clone https://github.com/arxos/arxos.git
cd arxos

# Copy production configuration
cp docker-compose.prod.yml docker-compose.yml
```

#### **2. Configure Environment**
```bash
# Copy environment template
cp .env.example .env

# Edit environment variables
nano .env
```

#### **3. Set Required Variables**
```bash
# Database configuration
POSTGRES_DB=arxos
POSTGRES_USER=arxos_user
POSTGRES_PASSWORD=secure_password_here

# Redis configuration
REDIS_PASSWORD=secure_redis_password

# Application configuration
ARXOS_SECRET_KEY=your_secret_key_here
ARXOS_DEBUG=False
ARXOS_ALLOWED_HOSTS=your-domain.com,www.your-domain.com

# Email configuration
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
```

#### **4. Deploy Application**
```bash
# Build and start services
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f
```

#### **5. Initialize Database**
```bash
# Run database migrations
docker-compose exec web python manage.py migrate

# Create superuser
docker-compose exec web python manage.py createsuperuser

# Collect static files
docker-compose exec web python manage.py collectstatic --noinput
```

### **Advanced Configuration**

#### **SSL/TLS Setup**
```yaml
# docker-compose.yml
version: '3.8'
services:
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - web
```

#### **Nginx Configuration**
```nginx
# nginx.conf
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;

    location / {
        proxy_pass http://web:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

---

## ☸️ **Kubernetes Deployment**

### **Prerequisites**

#### **Kubernetes Cluster**
```bash
# Check cluster status
kubectl cluster-info

# Verify nodes
kubectl get nodes

# Check storage classes
kubectl get storageclass
```

#### **Required Tools**
```bash
# Install kubectl
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl

# Install Helm
curl https://get.helm.sh/helm-v3.12.0-linux-amd64.tar.gz | tar xz
sudo mv linux-amd64/helm /usr/local/bin/helm
```

### **Deployment Steps**

#### **1. Create Namespace**
```bash
# Create namespace
kubectl create namespace arxos

# Set as default
kubectl config set-context --current --namespace=arxos
```

#### **2. Deploy Database**
```yaml
# postgres.yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: postgres-pvc
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 100Gi
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: postgres
spec:
  replicas: 1
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      containers:
      - name: postgres
        image: postgres:15
        env:
        - name: POSTGRES_DB
          value: "arxos"
        - name: POSTGRES_USER
          value: "arxos_user"
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: postgres-secret
              key: password
        ports:
        - containerPort: 5432
        volumeMounts:
        - name: postgres-storage
          mountPath: /var/lib/postgresql/data
      volumes:
      - name: postgres-storage
        persistentVolumeClaim:
          claimName: postgres-pvc
---
apiVersion: v1
kind: Service
metadata:
  name: postgres
spec:
  selector:
    app: postgres
  ports:
  - port: 5432
    targetPort: 5432
  type: ClusterIP
```

#### **3. Deploy Application**
```yaml
# arxos-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: arxos-web
spec:
  replicas: 3
  selector:
    matchLabels:
      app: arxos-web
  template:
    metadata:
      labels:
        app: arxos-web
    spec:
      containers:
      - name: arxos-web
        image: arxos/arxos:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          value: "postgresql://arxos_user:password@postgres:5432/arxos"
        - name: REDIS_URL
          value: "redis://redis:6379"
        - name: SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: arxos-secret
              key: secret-key
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health/
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready/
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
```

#### **4. Deploy Services**
```bash
# Apply configurations
kubectl apply -f postgres.yaml
kubectl apply -f arxos-deployment.yaml

# Check deployment status
kubectl get pods
kubectl get services
```

#### **5. Configure Ingress**
```yaml
# ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: arxos-ingress
  annotations:
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
spec:
  tls:
  - hosts:
    - your-domain.com
    secretName: arxos-tls
  rules:
  - host: your-domain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: arxos-web
            port:
              number: 8000
```

---

## ☁️ **Cloud Platform Deployment**

### **AWS Deployment**

#### **Using AWS ECS**
```bash
# Install AWS CLI
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# Configure AWS credentials
aws configure
```

#### **ECS Task Definition**
```json
{
  "family": "arxos",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "executionRoleArn": "arn:aws:iam::account:role/ecsTaskExecutionRole",
  "containerDefinitions": [
    {
      "name": "arxos-web",
      "image": "arxos/arxos:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "DATABASE_URL",
          "value": "postgresql://user:pass@rds-endpoint:5432/arxos"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/arxos",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

#### **RDS Database Setup**
```bash
# Create RDS instance
aws rds create-db-instance \
  --db-instance-identifier arxos-db \
  --db-instance-class db.t3.micro \
  --engine postgres \
  --master-username arxos_user \
  --master-user-password secure_password \
  --allocated-storage 20
```

### **Azure Deployment**

#### **Using Azure Container Instances**
```bash
# Login to Azure
az login

# Create resource group
az group create --name arxos-rg --location eastus

# Create container instance
az container create \
  --resource-group arxos-rg \
  --name arxos-web \
  --image arxos/arxos:latest \
  --dns-name-label arxos-web \
  --ports 8000 \
  --environment-variables \
    DATABASE_URL="postgresql://user:pass@azure-db:5432/arxos"
```

### **GCP Deployment**

#### **Using Google Cloud Run**
```bash
# Set project
gcloud config set project your-project-id

# Deploy to Cloud Run
gcloud run deploy arxos-web \
  --image arxos/arxos:latest \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars DATABASE_URL="postgresql://user:pass@cloud-sql:5432/arxos"
```

---

## 🏢 **On-Premises Deployment**

### **Traditional Server Setup**

#### **1. Server Preparation**
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y python3 python3-pip postgresql redis-server nginx

# Create arxos user
sudo useradd -m -s /bin/bash arxos
sudo usermod -aG sudo arxos
```

#### **2. Database Setup**
```bash
# Switch to postgres user
sudo -u postgres psql

# Create database and user
CREATE DATABASE arxos;
CREATE USER arxos_user WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE arxos TO arxos_user;
\q
```

#### **3. Application Setup**
```bash
# Switch to arxos user
sudo su - arxos

# Create application directory
mkdir -p /home/arxos/arxos
cd /home/arxos/arxos

# Clone repository
git clone https://github.com/arxos/arxos.git .

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
nano .env
```

#### **4. Systemd Service**
```ini
# /etc/systemd/system/arxos.service
[Unit]
Description=Arxos Web Application
After=network.target postgresql.service redis-server.service

[Service]
Type=simple
User=arxos
Group=arxos
WorkingDirectory=/home/arxos/arxos
Environment=PATH=/home/arxos/arxos/venv/bin
ExecStart=/home/arxos/arxos/venv/bin/gunicorn arxos.wsgi:application --bind 0.0.0.0:8000 --workers 4
Restart=always

[Install]
WantedBy=multi-user.target
```

#### **5. Nginx Configuration**
```nginx
# /etc/nginx/sites-available/arxos
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ {
        alias /home/arxos/arxos/static/;
    }

    location /media/ {
        alias /home/arxos/arxos/media/;
    }
}
```

---

## 🔧 **Configuration Management**

### **Environment Variables**

#### **Required Variables**
```bash
# Database
DATABASE_URL=postgresql://user:pass@host:5432/arxos
REDIS_URL=redis://host:6379

# Security
SECRET_KEY=your-secret-key-here
DEBUG=False
ALLOWED_HOSTS=your-domain.com,www.your-domain.com

# Email
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
```

#### **Optional Variables**
```bash
# Logging
LOG_LEVEL=INFO
LOG_FILE=/var/log/arxos/app.log

# Cache
CACHE_BACKEND=redis
CACHE_LOCATION=redis://host:6379/1

# File Storage
MEDIA_ROOT=/var/arxos/media
STATIC_ROOT=/var/arxos/static

# Monitoring
SENTRY_DSN=your-sentry-dsn
```

### **Database Configuration**

#### **PostgreSQL Optimization**
```sql
-- Increase connection limits
ALTER SYSTEM SET max_connections = 200;
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
ALTER SYSTEM SET work_mem = '4MB';
ALTER SYSTEM SET maintenance_work_mem = '64MB';

-- Reload configuration
SELECT pg_reload_conf();
```

#### **Redis Configuration**
```bash
# /etc/redis/redis.conf
maxmemory 512mb
maxmemory-policy allkeys-lru
save 900 1
save 300 10
save 60 10000
```

---

## 📊 **Monitoring and Health Checks**

### **Health Check Endpoints**

#### **Application Health**
```bash
# Check application status
curl http://your-domain.com/health/

# Check database connectivity
curl http://your-domain.com/health/db/

# Check cache connectivity
curl http://your-domain.com/health/cache/
```

#### **System Monitoring**
```bash
# Check system resources
htop
df -h
free -h

# Check application logs
tail -f /var/log/arxos/app.log

# Check nginx logs
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log
```

### **Prometheus Metrics**

#### **Application Metrics**
```python
# metrics.py
from prometheus_client import Counter, Histogram, Gauge

# Request metrics
request_count = Counter('arxos_requests_total', 'Total requests', ['method', 'endpoint'])
request_duration = Histogram('arxos_request_duration_seconds', 'Request duration')

# Business metrics
building_count = Gauge('arxos_buildings_total', 'Total buildings')
user_count = Gauge('arxos_users_total', 'Total users')
```

#### **Grafana Dashboard**
```json
{
  "dashboard": {
    "title": "Arxos Production Dashboard",
    "panels": [
      {
        "title": "Request Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(arxos_requests_total[5m])",
            "legendFormat": "{{method}} {{endpoint}}"
          }
        ]
      },
      {
        "title": "Response Time",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(arxos_request_duration_seconds_bucket[5m]))",
            "legendFormat": "95th percentile"
          }
        ]
      }
    ]
  }
}
```

---

## 🔒 **Security Configuration**

### **SSL/TLS Setup**

#### **Let's Encrypt Certificate**
```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

#### **Security Headers**
```nginx
# nginx.conf
add_header X-Frame-Options "SAMEORIGIN" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-XSS-Protection "1; mode=block" always;
add_header Referrer-Policy "strict-origin-when-cross-origin" always;
add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline';" always;
```

### **Firewall Configuration**
```bash
# Configure UFW
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

---

## 🚨 **Troubleshooting**

### **Common Issues**

#### **Database Connection Errors**
```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Check connection
psql -h localhost -U arxos_user -d arxos

# Check logs
sudo tail -f /var/log/postgresql/postgresql-*.log
```

#### **Application Errors**
```bash
# Check application status
sudo systemctl status arxos

# Check logs
sudo journalctl -u arxos -f

# Check environment
echo $DATABASE_URL
echo $SECRET_KEY
```

#### **Performance Issues**
```bash
# Check system resources
htop
iostat -x 1
netstat -i

# Check application performance
curl -w "@curl-format.txt" -o /dev/null -s "http://your-domain.com/"
```

### **Rollback Procedures**

#### **Application Rollback**
```bash
# Docker Compose
docker-compose down
docker-compose up -d --force-recreate

# Kubernetes
kubectl rollout undo deployment/arxos-web

# Traditional
sudo systemctl stop arxos
git checkout previous-version
sudo systemctl start arxos
```

#### **Database Rollback**
```bash
# Restore from backup
pg_restore -h localhost -U arxos_user -d arxos backup.dump

# Point-in-time recovery
pg_restore -h localhost -U arxos_user -d arxos --clean backup.dump
```

---

## 📞 **Support and Maintenance**

### **Regular Maintenance**

#### **Daily Tasks**
```bash
# Check system health
./scripts/health-check.sh

# Monitor logs
tail -f /var/log/arxos/app.log | grep ERROR

# Check disk space
df -h
```

#### **Weekly Tasks**
```bash
# Update system packages
sudo apt update && sudo apt upgrade

# Backup database
pg_dump -h localhost -U arxos_user arxos > backup_$(date +%Y%m%d).sql

# Clean old logs
find /var/log/arxos -name "*.log" -mtime +7 -delete
```

#### **Monthly Tasks**
```bash
# Security updates
sudo apt update && sudo apt upgrade

# Performance review
./scripts/performance-review.sh

# Capacity planning
./scripts/capacity-check.sh
```

### **Support Contacts**
- **Technical Support**: support@arxos.com
- **Emergency Hotline**: +1-555-ARXOS-1
- **Documentation**: https://docs.arxos.com
- **Community Forum**: https://community.arxos.com

---

**Need Help?** Contact our support team or check the [Operations Guide](../operations/) for additional deployment and maintenance information.
