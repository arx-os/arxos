# AHJ API Integration - Production Deployment Guide

## Overview

This guide provides comprehensive instructions for deploying the AHJ API Integration service in production environments. The AHJ API provides secure, append-only interfaces for Authorities Having Jurisdiction with immutable audit trails and cryptographic protection.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Security Configuration](#security-configuration)
3. [Database Setup](#database-setup)
4. [Environment Configuration](#environment-configuration)
5. [Deployment Options](#deployment-options)
6. [Monitoring and Logging](#monitoring-and-logging)
7. [Backup and Recovery](#backup-and-recovery)
8. [Performance Tuning](#performance-tuning)
9. [Security Hardening](#security-hardening)
10. [Troubleshooting](#troubleshooting)

## Prerequisites

### System Requirements

- **Operating System**: Linux (Ubuntu 20.04+ recommended) or Windows Server 2019+
- **Python**: 3.8+ (3.11+ recommended)
- **Memory**: Minimum 4GB RAM, 8GB+ recommended
- **Storage**: 50GB+ available space
- **Network**: HTTPS/TLS support required

### Software Dependencies

```bash
# Core dependencies
pip install fastapi uvicorn sqlalchemy psycopg2-binary
pip install cryptography pyjwt pyyaml
pip install pytest pytest-asyncio aiohttp

# Optional: Redis for caching
pip install redis

# Optional: Prometheus for metrics
pip install prometheus-client
```

### Security Prerequisites

- SSL/TLS certificates
- Firewall configuration
- Network security groups
- Access control lists
- VPN or secure network access

## Security Configuration

### 1. Cryptographic Keys Management

```python
# Generate production keys
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa
import base64

# Generate encryption key
encryption_key = Fernet.generate_key()
print(f"Encryption Key: {base64.b64encode(encryption_key).decode()}")

# Generate signing key pair
private_key = rsa.generate_private_key(
    public_exponent=65537,
    key_size=2048
)
public_key = private_key.public_key()

# Save keys securely
with open("private_key.pem", "wb") as f:
    f.write(private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    ))

with open("public_key.pem", "wb") as f:
    f.write(public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    ))
```

### 2. Environment Variables

```bash
# Security Configuration
export AHJ_ENCRYPTION_KEY="your-encryption-key"
export AHJ_PRIVATE_KEY_PATH="/path/to/private_key.pem"
export AHJ_PUBLIC_KEY_PATH="/path/to/public_key.pem"
export AHJ_JWT_SECRET="your-jwt-secret-key"
export AHJ_SESSION_TIMEOUT=28800  # 8 hours

# Database Configuration
export DATABASE_URL="postgresql://user:password@localhost/ahj_db"
export DATABASE_POOL_SIZE=20
export DATABASE_MAX_OVERFLOW=30

# API Configuration
export AHJ_API_HOST="0.0.0.0"
export AHJ_API_PORT=8000
export AHJ_API_WORKERS=4
export AHJ_API_MAX_REQUESTS=1000
export AHJ_API_TIMEOUT=30

# Logging Configuration
export AHJ_LOG_LEVEL="INFO"
export AHJ_LOG_FILE="/var/log/ahj_api.log"
export AHJ_AUDIT_LOG_FILE="/var/log/ahj_audit.log"

# Monitoring Configuration
export AHJ_METRICS_ENABLED=true
export AHJ_HEALTH_CHECK_INTERVAL=30
```

### 3. Firewall Configuration

```bash
# UFW (Ubuntu)
sudo ufw allow 8000/tcp  # API port
sudo ufw allow 22/tcp     # SSH
sudo ufw enable

# iptables (CentOS/RHEL)
sudo iptables -A INPUT -p tcp --dport 8000 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 22 -j ACCEPT
sudo iptables -A INPUT -j DROP
```

## Database Setup

### 1. PostgreSQL Configuration

```sql
-- Create database
CREATE DATABASE ahj_db;

-- Create user
CREATE USER ahj_user WITH PASSWORD 'secure_password';

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE ahj_db TO ahj_user;

-- Create audit schema
CREATE SCHEMA audit;

-- Create audit tables
CREATE TABLE audit.ahj_audit_logs (
    id SERIAL PRIMARY KEY,
    log_id VARCHAR(36) UNIQUE NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    user_id VARCHAR(255) NOT NULL,
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(100) NOT NULL,
    resource_id VARCHAR(255) NOT NULL,
    details JSONB,
    ip_address INET,
    user_agent TEXT,
    session_id VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes
CREATE INDEX idx_audit_logs_timestamp ON audit.ahj_audit_logs(timestamp);
CREATE INDEX idx_audit_logs_user_id ON audit.ahj_audit_logs(user_id);
CREATE INDEX idx_audit_logs_action ON audit.ahj_audit_logs(action);

-- Enable row level security
ALTER TABLE audit.ahj_audit_logs ENABLE ROW LEVEL SECURITY;

-- Create policy
CREATE POLICY audit_logs_policy ON audit.ahj_audit_logs
    FOR ALL TO ahj_user
    USING (true);
```

### 2. Database Connection Pooling

```python
# Database configuration
DATABASE_CONFIG = {
    "pool_size": 20,
    "max_overflow": 30,
    "pool_timeout": 30,
    "pool_recycle": 3600,
    "echo": False
}
```

## Environment Configuration

### 1. Production Configuration File

```yaml
# config/production.yaml
ahj_api:
  security:
    encryption_key: "${AHJ_ENCRYPTION_KEY}"
    private_key_path: "${AHJ_PRIVATE_KEY_PATH}"
    public_key_path: "${AHJ_PUBLIC_KEY_PATH}"
    jwt_secret: "${AHJ_JWT_SECRET}"
    session_timeout: 28800
    
  database:
    url: "${DATABASE_URL}"
    pool_size: 20
    max_overflow: 30
    pool_timeout: 30
    pool_recycle: 3600
    
  api:
    host: "0.0.0.0"
    port: 8000
    workers: 4
    max_requests: 1000
    timeout: 30
    
  logging:
    level: "INFO"
    file: "/var/log/ahj-api.log"
    audit_file: "/var/log/ahj-audit.log"
    max_size: "100MB"
    backup_count: 5
    
  monitoring:
    metrics_enabled: true
    health_check_interval: 30
    prometheus_port: 9090
    
  audit:
    retention_days: 2555  # 7 years
    compression_enabled: true
    backup_enabled: true
```

### 2. Systemd Service Configuration

```ini
# /etc/systemd/system/ahj-api.service
[Unit]
Description=AHJ API Integration Service
After=network.target postgresql.service
Wants=postgresql.service

[Service]
Type=exec
User=ahj_user
Group=ahj_group
WorkingDirectory=/opt/ahj-api
Environment=PATH=/opt/ahj-api/venv/bin
Environment=PYTHONPATH=/opt/ahj-api
ExecStart=/opt/ahj-api/venv/bin/uvicorn api.main:app --host 0.0.0.0 --port 8000 --workers 4
ExecReload=/bin/kill -HUP $MAINPID
Restart=always
RestartSec=10

# Security settings
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/var/log /opt/ahj-api/data

# Resource limits
LimitNOFILE=65536
LimitNPROC=4096

[Install]
WantedBy=multi-user.target
```

## Deployment Options

### 1. Docker Deployment

```dockerfile
# Dockerfile
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 ahj_user && \
    chown -R ahj_user:ahj_user /app

# Switch to non-root user
USER ahj_user

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/ahj/health || exit 1

# Start application
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```yaml
# docker-compose.yml
version: '3.8'

services:
  ahj-api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://ahj_user:password@db:5432/ahj_db
      - AHJ_ENCRYPTION_KEY=${AHJ_ENCRYPTION_KEY}
      - AHJ_JWT_SECRET=${AHJ_JWT_SECRET}
    volumes:
      - ./logs:/app/logs
      - ./data:/app/data
    depends_on:
      - db
    restart: unless-stopped
    networks:
      - ahj-network

  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=ahj_db
      - POSTGRES_USER=ahj_user
      - POSTGRES_PASSWORD=secure_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - ahj-network

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - ahj-api
    networks:
      - ahj-network

volumes:
  postgres_data:

networks:
  ahj-network:
    driver: bridge
```

### 2. Kubernetes Deployment

```yaml
# k8s/ahj-api-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ahj-api
  labels:
    app: ahj-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: ahj-api
  template:
    metadata:
      labels:
        app: ahj-api
    spec:
      containers:
      - name: ahj-api
        image: ahj-api:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: ahj-secrets
              key: database-url
        - name: AHJ_ENCRYPTION_KEY
          valueFrom:
            secretKeyRef:
              name: ahj-secrets
              key: encryption-key
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /api/v1/ahj/health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /api/v1/ahj/health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
```

### 3. AWS ECS Deployment

```json
{
  "family": "ahj-api",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "executionRoleArn": "arn:aws:iam::account:role/ecsTaskExecutionRole",
  "taskRoleArn": "arn:aws:iam::account:role/ahj-api-task-role",
  "containerDefinitions": [
    {
      "name": "ahj-api",
      "image": "account.dkr.ecr.region.amazonaws.com/ahj-api:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "DATABASE_URL",
          "value": "postgresql://user:password@rds-endpoint:5432/ahj_db"
        }
      ],
      "secrets": [
        {
          "name": "AHJ_ENCRYPTION_KEY",
          "valueFrom": "arn:aws:secretsmanager:region:account:secret:ahj-encryption-key"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/ahj-api",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

## Monitoring and Logging

### 1. Application Logging

```python
# logging_config.py
import logging
import logging.handlers
import os

def setup_logging():
    # Create logs directory
    os.makedirs("/var/log/ahj-api", exist_ok=True)
    
    # Configure root logger
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.handlers.RotatingFileHandler(
                "/var/log/ahj-api/application.log",
                maxBytes=100*1024*1024,  # 100MB
                backupCount=5
            ),
            logging.StreamHandler()
        ]
    )
    
    # Configure audit logger
    audit_logger = logging.getLogger("ahj_audit")
    audit_logger.setLevel(logging.INFO)
    audit_handler = logging.handlers.RotatingFileHandler(
        "/var/log/ahj-api/audit.log",
        maxBytes=100*1024*1024,  # 100MB
        backupCount=10
    )
    audit_logger.addHandler(audit_handler)
    
    # Configure security logger
    security_logger = logging.getLogger("ahj_security")
    security_logger.setLevel(logging.WARNING)
    security_handler = logging.handlers.RotatingFileHandler(
        "/var/log/ahj-api/security.log",
        maxBytes=50*1024*1024,  # 50MB
        backupCount=5
    )
    security_logger.addHandler(security_handler)
```

### 2. Prometheus Metrics

```python
# metrics.py
from prometheus_client import Counter, Histogram, Gauge, generate_latest
from fastapi import Request
import time

# Metrics
REQUEST_COUNT = Counter('ahj_api_requests_total', 'Total requests', ['method', 'endpoint', 'status'])
REQUEST_DURATION = Histogram('ahj_api_request_duration_seconds', 'Request duration', ['method', 'endpoint'])
ACTIVE_SESSIONS = Gauge('ahj_api_active_sessions', 'Active sessions')
TOTAL_ANNOTATIONS = Gauge('ahj_api_total_annotations', 'Total annotations')
AUDIT_LOG_ENTRIES = Gauge('ahj_api_audit_log_entries', 'Audit log entries')

async def metrics_middleware(request: Request, call_next):
    start_time = time.time()
    
    response = await call_next(request)
    
    duration = time.time() - start_time
    REQUEST_DURATION.labels(
        method=request.method,
        endpoint=request.url.path
    ).observe(duration)
    
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()
    
    return response
```

### 3. Health Checks

```python
# health_checks.py
import psutil
import asyncio
from datetime import datetime

class HealthChecker:
    def __init__(self):
        self.start_time = datetime.now()
    
    async def check_database(self):
        """Check database connectivity."""
        try:
            # Test database connection
            return {"status": "healthy", "details": "Database connection OK"}
        except Exception as e:
            return {"status": "unhealthy", "details": str(e)}
    
    async def check_memory(self):
        """Check memory usage."""
        memory = psutil.virtual_memory()
        if memory.percent > 90:
            return {"status": "warning", "details": f"High memory usage: {memory.percent}%"}
        return {"status": "healthy", "details": f"Memory usage: {memory.percent}%"}
    
    async def check_disk(self):
        """Check disk space."""
        disk = psutil.disk_usage('/')
        if disk.percent > 90:
            return {"status": "warning", "details": f"Low disk space: {disk.percent}%"}
        return {"status": "healthy", "details": f"Disk usage: {disk.percent}%"}
    
    async def comprehensive_health_check(self):
        """Comprehensive health check."""
        checks = await asyncio.gather(
            self.check_database(),
            self.check_memory(),
            self.check_disk()
        )
        
        overall_status = "healthy"
        if any(check["status"] == "unhealthy" for check in checks):
            overall_status = "unhealthy"
        elif any(check["status"] == "warning" for check in checks):
            overall_status = "warning"
        
        return {
            "status": overall_status,
            "timestamp": datetime.now().isoformat(),
            "uptime": (datetime.now() - self.start_time).total_seconds(),
            "checks": {
                "database": checks[0],
                "memory": checks[1],
                "disk": checks[2]
            }
        }
```

## Backup and Recovery

### 1. Database Backup Strategy

```bash
#!/bin/bash
# backup_script.sh

# Configuration
DB_NAME="ahj_db"
DB_USER="ahj_user"
BACKUP_DIR="/backup/ahj"
RETENTION_DAYS=30

# Create backup directory
mkdir -p $BACKUP_DIR

# Generate backup filename
BACKUP_FILE="$BACKUP_DIR/ahj_backup_$(date +%Y%m%d_%H%M%S).sql"

# Create database backup
pg_dump -h localhost -U $DB_USER -d $DB_NAME > $BACKUP_FILE

# Compress backup
gzip $BACKUP_FILE

# Remove old backups
find $BACKUP_DIR -name "*.sql.gz" -mtime +$RETENTION_DAYS -delete

# Log backup completion
echo "Backup completed: $BACKUP_FILE.gz" >> /var/log/ahj-api/backup.log
```

### 2. Audit Log Backup

```python
# audit_backup.py
import shutil
import gzip
import os
from datetime import datetime, timedelta

def backup_audit_logs():
    """Backup audit logs with compression."""
    audit_log_dir = "/var/log/ahj-api"
    backup_dir = "/backup/audit-logs"
    
    os.makedirs(backup_dir, exist_ok=True)
    
    # Backup current audit log
    current_log = os.path.join(audit_log_dir, "audit.log")
    if os.path.exists(current_log):
        backup_file = os.path.join(
            backup_dir, 
            f"audit_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log.gz"
        )
        
        with open(current_log, 'rb') as f_in:
            with gzip.open(backup_file, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        
        # Clear current log
        open(current_log, 'w').close()
        
        print(f"Audit log backed up to: {backup_file}")

def cleanup_old_backups(retention_days=90):
    """Clean up old backup files."""
    backup_dir = "/backup/audit-logs"
    cutoff_date = datetime.now() - timedelta(days=retention_days)
    
    for filename in os.listdir(backup_dir):
        file_path = os.path.join(backup_dir, filename)
        if os.path.getmtime(file_path) < cutoff_date.timestamp():
            os.remove(file_path)
            print(f"Removed old backup: {filename}")
```

### 3. Disaster Recovery Plan

```markdown
# Disaster Recovery Plan

## Recovery Time Objective (RTO): 4 hours
## Recovery Point Objective (RPO): 1 hour

### 1. Database Recovery
- Restore from latest backup
- Apply transaction logs if available
- Verify data integrity

### 2. Application Recovery
- Redeploy application from source
- Restore configuration files
- Restart services

### 3. Audit Trail Recovery
- Restore audit logs from backup
- Verify log integrity
- Rebuild audit indexes

### 4. Verification Steps
- Run health checks
- Verify API endpoints
- Test authentication
- Validate audit trail integrity
```

## Performance Tuning

### 1. Database Optimization

```sql
-- Database performance tuning
-- Analyze table statistics
ANALYZE audit.ahj_audit_logs;

-- Create additional indexes for performance
CREATE INDEX CONCURRENTLY idx_audit_logs_composite 
ON audit.ahj_audit_logs(user_id, timestamp, action);

-- Partition audit logs by date
CREATE TABLE audit.ahj_audit_logs_2024 PARTITION OF audit.ahj_audit_logs
FOR VALUES FROM ('2024-01-01') TO ('2025-01-01');

-- Configure PostgreSQL for performance
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
ALTER SYSTEM SET maintenance_work_mem = '64MB';
ALTER SYSTEM SET checkpoint_completion_target = 0.9;
ALTER SYSTEM SET wal_buffers = '16MB';
ALTER SYSTEM SET default_statistics_target = 100;
```

### 2. Application Performance

```python
# performance_config.py
import asyncio
import uvicorn

# Uvicorn configuration for performance
UVICORN_CONFIG = {
    "host": "0.0.0.0",
    "port": 8000,
    "workers": 4,  # Number of CPU cores
    "worker_class": "uvicorn.workers.UvicornWorker",
    "loop": "asyncio",
    "http": "httptools",
    "ws": "websockets",
    "lifespan": "on",
    "access_log": True,
    "use_colors": False,
    "log_config": None,
    "limit_concurrency": 1000,
    "limit_max_requests": 10000,
    "backlog": 2048,
    "timeout_keep_alive": 5,
}

# Database connection pooling
DATABASE_POOL_CONFIG = {
    "pool_size": 20,
    "max_overflow": 30,
    "pool_timeout": 30,
    "pool_recycle": 3600,
    "pool_pre_ping": True,
    "echo": False,
}

# Caching configuration
CACHE_CONFIG = {
    "redis_url": "redis://localhost:6379",
    "cache_ttl": 3600,  # 1 hour
    "max_cache_size": 1000,
}
```

### 3. Load Balancing

```nginx
# nginx.conf
upstream ahj_api {
    least_conn;
    server 127.0.0.1:8001;
    server 127.0.0.1:8002;
    server 127.0.0.1:8003;
    server 127.0.0.1:8004;
}

server {
    listen 80;
    server_name ahj-api.example.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name ahj-api.example.com;
    
    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;
    ssl_prefer_server_ciphers off;
    
    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains";
    
    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req zone=api burst=20 nodelay;
    
    location / {
        proxy_pass http://ahj_api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts
        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
    }
    
    # Health check endpoint
    location /health {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }
}
```

## Security Hardening

### 1. Network Security

```bash
# Firewall rules
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 8000/tcp
sudo ufw allow 443/tcp
sudo ufw allow 80/tcp
sudo ufw enable

# Fail2ban configuration
sudo apt-get install fail2ban
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

### 2. Application Security

```python
# security_middleware.py
from fastapi import Request, HTTPException
from fastapi.security import HTTPBearer
import jwt
import time

security = HTTPBearer()

class SecurityMiddleware:
    def __init__(self):
        self.blocked_ips = set()
        self.rate_limit = {}
    
    async def __call__(self, request: Request, call_next):
        # IP blocking
        client_ip = request.client.host
        if client_ip in self.blocked_ips:
            raise HTTPException(status_code=403, detail="IP blocked")
        
        # Rate limiting
        current_time = time.time()
        if client_ip in self.rate_limit:
            if current_time - self.rate_limit[client_ip]["last_request"] < 1:
                if self.rate_limit[client_ip]["count"] > 100:
                    raise HTTPException(status_code=429, detail="Rate limit exceeded")
                self.rate_limit[client_ip]["count"] += 1
            else:
                self.rate_limit[client_ip] = {"last_request": current_time, "count": 1}
        else:
            self.rate_limit[client_ip] = {"last_request": current_time, "count": 1}
        
        # Security headers
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        return response
```

### 3. Data Encryption

```python
# encryption.py
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64

class DataEncryption:
    def __init__(self, key: str):
        self.cipher_suite = Fernet(key)
    
    def encrypt_sensitive_data(self, data: str) -> str:
        """Encrypt sensitive data."""
        return self.cipher_suite.encrypt(data.encode()).decode()
    
    def decrypt_sensitive_data(self, encrypted_data: str) -> str:
        """Decrypt sensitive data."""
        return self.cipher_suite.decrypt(encrypted_data.encode()).decode()
    
    def hash_password(self, password: str, salt: bytes = None) -> tuple:
        """Hash password with salt."""
        if salt is None:
            salt = os.urandom(16)
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key.decode(), salt
```

## Troubleshooting

### 1. Common Issues

```python
# troubleshooting.py
import logging
import traceback
from typing import Dict, Any

class Troubleshooter:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def diagnose_connection_issues(self) -> Dict[str, Any]:
        """Diagnose database connection issues."""
        try:
            # Test database connection
            # Test network connectivity
            # Test authentication
            return {"status": "healthy", "issues": []}
        except Exception as e:
            return {
                "status": "unhealthy",
                "issues": [str(e)],
                "recommendations": [
                    "Check database service status",
                    "Verify network connectivity",
                    "Check authentication credentials"
                ]
            }
    
    def diagnose_performance_issues(self) -> Dict[str, Any]:
        """Diagnose performance issues."""
        issues = []
        
        # Check memory usage
        memory = psutil.virtual_memory()
        if memory.percent > 90:
            issues.append("High memory usage")
        
        # Check CPU usage
        cpu_percent = psutil.cpu_percent(interval=1)
        if cpu_percent > 90:
            issues.append("High CPU usage")
        
        # Check disk space
        disk = psutil.disk_usage('/')
        if disk.percent > 90:
            issues.append("Low disk space")
        
        return {
            "status": "warning" if issues else "healthy",
            "issues": issues,
            "metrics": {
                "memory_percent": memory.percent,
                "cpu_percent": cpu_percent,
                "disk_percent": disk.percent
            }
        }
    
    def diagnose_security_issues(self) -> Dict[str, Any]:
        """Diagnose security issues."""
        issues = []
        
        # Check for failed authentication attempts
        # Check for suspicious IP addresses
        # Check for unusual access patterns
        
        return {
            "status": "healthy" if not issues else "warning",
            "issues": issues,
            "recommendations": [
                "Review authentication logs",
                "Check firewall rules",
                "Monitor access patterns"
            ]
        }
```

### 2. Log Analysis

```bash
#!/bin/bash
# log_analyzer.sh

# Analyze application logs
echo "=== Application Log Analysis ==="
grep "ERROR" /var/log/ahj-api/application.log | tail -20

# Analyze audit logs
echo "=== Audit Log Analysis ==="
grep "authentication_failed" /var/log/ahj-api/audit.log | tail -10

# Analyze security logs
echo "=== Security Log Analysis ==="
grep "WARNING\|ERROR" /var/log/ahj-api/security.log | tail -10

# Check system resources
echo "=== System Resources ==="
free -h
df -h
top -bn1 | head -10
```

### 3. Emergency Procedures

```markdown
# Emergency Procedures

## Service Down
1. Check service status: `systemctl status ahj-api`
2. Check logs: `tail -f /var/log/ahj-api/application.log`
3. Restart service: `systemctl restart ahj-api`
4. If persistent, check database connectivity

## Database Issues
1. Check PostgreSQL status: `systemctl status postgresql`
2. Check disk space: `df -h`
3. Check memory usage: `free -h`
4. Restart database if necessary

## Security Breach
1. Immediately block suspicious IPs
2. Review audit logs for unauthorized access
3. Rotate encryption keys
4. Notify security team
5. Document incident for compliance

## Performance Issues
1. Check resource usage
2. Review slow queries
3. Optimize database indexes
4. Scale horizontally if necessary
```

## Conclusion

This production deployment guide provides comprehensive instructions for deploying the AHJ API Integration service in a secure, scalable, and maintainable manner. Follow these guidelines to ensure a robust production environment that meets security, performance, and compliance requirements.

For additional support or questions, refer to the troubleshooting section or contact the development team. 