# ARXOS Production Deployment Guide

## Overview

This guide covers the secure deployment of ARXOS in a production environment.

## Prerequisites

- Kubernetes cluster (1.25+) or Docker Swarm
- PostgreSQL 15+ with SSL enabled
- Valid SSL certificates
- Configured DNS
- Backup storage (S3/GCS/Azure)
- Monitoring infrastructure
- SMTP server for notifications

## Security Checklist

### Pre-Deployment

- [ ] Review security configuration (`security-config.yaml`)
- [ ] Generate strong encryption keys
- [ ] Configure secrets management (Vault/AWS Secrets Manager)
- [ ] Set up SSL certificates
- [ ] Configure firewall rules
- [ ] Set up monitoring and alerting
- [ ] Review and update dependencies
- [ ] Run security scan on container images
- [ ] Configure backup strategy
- [ ] Set up DDoS protection

### Environment Variables

```bash
# Required Security Environment Variables
export TWO_FACTOR_ENCRYPTION_KEY=$(openssl rand -hex 32)
export JWT_PRIVATE_KEY=$(openssl genrsa 2048)
export JWT_PUBLIC_KEY=$(openssl rsa -in private.key -pubout)
export DATABASE_ENCRYPTION_KEY=$(openssl rand -hex 32)
export CSRF_SECRET=$(openssl rand -hex 32)
export SESSION_SECRET=$(openssl rand -hex 32)

# External Services
export SMTP_HOST="smtp.example.com"
export SMTP_PORT="587"
export SMTP_USER="notifications@arxos.io"
export SMTP_PASSWORD="secure_password"
export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/..."
export SIEM_ENDPOINT="https://siem.example.com/api/events"

# Database
export DATABASE_URL="postgresql://user:pass@host:5432/arxos?sslmode=require"
export DATABASE_SSL_CERT="/path/to/cert.pem"
export DATABASE_SSL_KEY="/path/to/key.pem"
export DATABASE_SSL_CA="/path/to/ca.pem"

# Vault (if using HashiCorp Vault)
export VAULT_ADDR="https://vault.example.com:8200"
export VAULT_TOKEN="s.xxxxxxxxxx"
```

### Database Setup

```sql
-- Create production database
CREATE DATABASE arxos_production;

-- Create application user with limited privileges
CREATE USER arxos_app WITH ENCRYPTED PASSWORD 'strong_password';
GRANT CONNECT ON DATABASE arxos_production TO arxos_app;
GRANT USAGE ON SCHEMA public TO arxos_app;
GRANT CREATE ON SCHEMA public TO arxos_app;

-- Enable SSL
ALTER SYSTEM SET ssl = on;
ALTER SYSTEM SET ssl_cert_file = '/etc/postgresql/server.crt';
ALTER SYSTEM SET ssl_key_file = '/etc/postgresql/server.key';
ALTER SYSTEM SET ssl_ca_file = '/etc/postgresql/ca.crt';

-- Enable audit logging
ALTER SYSTEM SET log_statement = 'all';
ALTER SYSTEM SET log_connections = on;
ALTER SYSTEM SET log_disconnections = on;
```

### Kubernetes Deployment

```yaml
# arxos-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: arxos-api
  namespace: production
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
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
        fsGroup: 1000
      containers:
      - name: arxos
        image: arxos/api:latest
        imagePullPolicy: Always
        ports:
        - containerPort: 8080
          name: http
        env:
        - name: ENV
          value: "production"
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: arxos-secrets
              key: database-url
        envFrom:
        - secretRef:
            name: arxos-secrets
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
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
        securityContext:
          allowPrivilegeEscalation: false
          readOnlyRootFilesystem: true
          capabilities:
            drop:
            - ALL
```

### NGINX Configuration

```nginx
# /etc/nginx/sites-available/arxos
server {
    listen 443 ssl http2;
    server_name arxos.io;

    # SSL Configuration
    ssl_certificate /etc/ssl/certs/arxos.crt;
    ssl_certificate_key /etc/ssl/private/arxos.key;
    ssl_protocols TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    ssl_stapling on;
    ssl_stapling_verify on;

    # Security Headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'nonce-$request_id'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:;" always;

    # Rate Limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req zone=api burst=20 nodelay;

    # Proxy to API
    location / {
        proxy_pass http://localhost:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Request-ID $request_id;
        
        # Timeouts
        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
        
        # Buffering
        proxy_buffering on;
        proxy_buffer_size 4k;
        proxy_buffers 8 4k;
        proxy_busy_buffers_size 8k;
    }

    # Block suspicious paths
    location ~ /\. {
        deny all;
    }

    # Security.txt
    location /.well-known/security.txt {
        alias /var/www/arxos/.well-known/security.txt;
    }
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name arxos.io;
    return 301 https://$server_name$request_uri;
}
```

### Monitoring Setup

```yaml
# prometheus-config.yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

alerting:
  alertmanagers:
  - static_configs:
    - targets:
      - alertmanager:9093

rule_files:
  - "alerts.yml"

scrape_configs:
  - job_name: 'arxos'
    static_configs:
    - targets: ['arxos-api:8080']
    metrics_path: '/metrics'
```

```yaml
# alerts.yml
groups:
- name: arxos_alerts
  rules:
  - alert: HighErrorRate
    expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
    for: 5m
    labels:
      severity: critical
    annotations:
      summary: "High error rate detected"
      
  - alert: SecurityBreachAttempt
    expr: security_alerts_total{severity="critical"} > 0
    for: 1m
    labels:
      severity: critical
    annotations:
      summary: "Critical security alert detected"
      
  - alert: DatabaseDown
    expr: up{job="postgresql"} == 0
    for: 1m
    labels:
      severity: critical
    annotations:
      summary: "Database is down"
```

### Backup Configuration

```bash
#!/bin/bash
# backup.sh

# Database backup
pg_dump $DATABASE_URL | gzip > backup_$(date +%Y%m%d_%H%M%S).sql.gz

# Encrypt backup
openssl enc -aes-256-cbc -salt -in backup.sql.gz -out backup.sql.gz.enc -k $BACKUP_ENCRYPTION_KEY

# Upload to S3
aws s3 cp backup.sql.gz.enc s3://arxos-backups/$(date +%Y/%m/%d)/

# Clean up old backups (keep 30 days)
aws s3 rm s3://arxos-backups/ --recursive --exclude "*" --include "*/backup_*.sql.gz.enc" --older-than 30
```

### Post-Deployment

- [ ] Verify SSL certificate installation
- [ ] Test authentication flow
- [ ] Verify 2FA for admin accounts
- [ ] Test rate limiting
- [ ] Verify backup and restore
- [ ] Test monitoring alerts
- [ ] Run security scan
- [ ] Load testing
- [ ] Penetration testing
- [ ] Document emergency procedures

## Security Maintenance

### Daily Tasks
- Review security alerts
- Check failed authentication attempts
- Monitor rate limiting logs
- Verify backup completion

### Weekly Tasks
- Review audit logs
- Check for security updates
- Test incident response procedures
- Review user access permissions

### Monthly Tasks
- Rotate secrets and API keys
- Review and update firewall rules
- Security vulnerability scanning
- Test disaster recovery

### Quarterly Tasks
- Penetration testing
- Security audit
- Update security documentation
- Review compliance requirements

## Incident Response

### Security Breach Detected

1. **Immediate Actions**
   - Enable maintenance mode
   - Isolate affected systems
   - Preserve evidence
   - Notify security team

2. **Investigation**
   - Review audit logs
   - Identify attack vector
   - Assess data exposure
   - Document findings

3. **Remediation**
   - Patch vulnerabilities
   - Reset affected credentials
   - Update security rules
   - Deploy fixes

4. **Recovery**
   - Restore from clean backup if needed
   - Verify system integrity
   - Resume normal operations
   - Monitor for recurrence

5. **Post-Incident**
   - Complete incident report
   - Update security procedures
   - Notify affected users (if required)
   - Implement preventive measures

## Compliance

### GDPR Compliance
- Data encryption at rest and in transit
- User consent management
- Right to erasure implementation
- Data portability features
- Audit logging

### SOC 2 Requirements
- Access controls
- Encryption standards
- Monitoring and alerting
- Incident response procedures
- Change management

## Support

For security issues: security@arxos.io
For general support: support@arxos.io

---

*Last Updated: 2024-12-25*
*Version: 1.0.0*