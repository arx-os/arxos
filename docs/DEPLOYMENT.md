# ArxOS Deployment Guide

## Overview

ArxOS is designed for simple deployment. The entire platform compiles to a single Go binary with embedded templates and assets, making deployment straightforward.

## Quick Start

### Single Binary Deployment

```bash
# Build the binary
go build -o arxos-server ./cmd/arxos-server

# Run it
./arxos-server -port 8080
```

That's it! No Node.js, no build step, no complex dependencies.

## Production Deployment Options

### 1. Systemd Service (Linux)

Create `/etc/systemd/system/arxos.service`:

```ini
[Unit]
Description=ArxOS Building Intelligence Platform
After=network.target

[Service]
Type=simple
User=arxos
Group=arxos
WorkingDirectory=/var/lib/arxos
ExecStart=/usr/local/bin/arxos-server -port 8080
Restart=always
RestartSec=10
StandardOutput=append:/var/log/arxos/server.log
StandardError=append:/var/log/arxos/error.log

# Security
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/var/lib/arxos

[Install]
WantedBy=multi-user.target
```

Setup and start:

```bash
# Create user and directories
sudo useradd -r -s /bin/false arxos
sudo mkdir -p /var/lib/arxos /var/log/arxos
sudo chown arxos:arxos /var/lib/arxos /var/log/arxos

# Copy binary
sudo cp arxos-server /usr/local/bin/
sudo chmod +x /usr/local/bin/arxos-server

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable arxos
sudo systemctl start arxos

# Check status
sudo systemctl status arxos
sudo journalctl -u arxos -f
```

### 2. Docker Deployment

#### Dockerfile

```dockerfile
# Build stage
FROM golang:1.21-alpine AS builder

WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download

COPY . .
RUN CGO_ENABLED=1 GOOS=linux go build -a -installsuffix cgo -o arxos-server ./cmd/arxos-server

# Runtime stage
FROM alpine:latest

RUN apk --no-cache add ca-certificates sqlite

WORKDIR /root/

COPY --from=builder /app/arxos-server .
COPY --from=builder /app/internal/web/templates ./internal/web/templates

EXPOSE 8080

CMD ["./arxos-server"]
```

#### Docker Compose

```yaml
version: '3.8'

services:
  arxos:
    build: .
    ports:
      - "8080:8080"
    volumes:
      - arxos-data:/var/lib/arxos
      - ./config.yaml:/etc/arxos/config.yaml
    environment:
      - ARXOS_PORT=8080
      - ARXOS_STATE_DIR=/var/lib/arxos
      - ARXOS_MODE=production
      - ARXOS_LOG_LEVEL=info
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "wget", "--spider", "-q", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 3

volumes:
  arxos-data:
```

Run with Docker Compose:

```bash
docker-compose up -d
docker-compose logs -f
```

### 3. Kubernetes Deployment

#### Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: arxos
  namespace: default
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
        image: arxos/arxos-server:latest
        ports:
        - containerPort: 8080
        env:
        - name: ARXOS_MODE
          value: "production"
        - name: ARXOS_STATE_DIR
          value: "/data"
        volumeMounts:
        - name: data
          mountPath: /data
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
        resources:
          requests:
            memory: "128Mi"
            cpu: "100m"
          limits:
            memory: "512Mi"
            cpu: "500m"
      volumes:
      - name: data
        persistentVolumeClaim:
          claimName: arxos-pvc
```

#### Service

```yaml
apiVersion: v1
kind: Service
metadata:
  name: arxos-service
spec:
  selector:
    app: arxos
  ports:
    - protocol: TCP
      port: 80
      targetPort: 8080
  type: LoadBalancer
```

#### Ingress

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: arxos-ingress
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  tls:
  - hosts:
    - arxos.example.com
    secretName: arxos-tls
  rules:
  - host: arxos.example.com
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

### 4. Cloud Platforms

#### AWS EC2

```bash
# Launch EC2 instance (Amazon Linux 2)
aws ec2 run-instances \
  --image-id ami-0c55b159cbfafe1f0 \
  --instance-type t3.micro \
  --key-name your-key \
  --security-groups arxos-sg

# SSH into instance
ssh -i your-key.pem ec2-user@<instance-ip>

# Install and run
wget https://github.com/arxos/arxos/releases/latest/download/arxos-server-linux-amd64
chmod +x arxos-server-linux-amd64
sudo mv arxos-server-linux-amd64 /usr/local/bin/arxos-server

# Create systemd service (see above)
```

#### Google Cloud Run

```bash
# Build and push image
gcloud builds submit --tag gcr.io/PROJECT-ID/arxos

# Deploy
gcloud run deploy arxos \
  --image gcr.io/PROJECT-ID/arxos \
  --platform managed \
  --port 8080 \
  --allow-unauthenticated \
  --region us-central1
```

#### Heroku

Create `Procfile`:
```
web: ./arxos-server -port $PORT
```

Deploy:
```bash
heroku create arxos-app
git push heroku main
heroku logs --tail
```

## Configuration

### Environment Variables

```bash
# Core settings
ARXOS_PORT=8080                    # Server port
ARXOS_STATE_DIR=/var/lib/arxos    # Data directory
ARXOS_LOG_LEVEL=info               # Log level: debug, info, warn, error
ARXOS_MODE=production              # Mode: local, cloud, hybrid

# Database
ARXOS_DB_PATH=/var/lib/arxos/arxos.db  # SQLite database path
ARXOS_DB_MAX_CONNECTIONS=25            # Max DB connections

# Security
ARXOS_SESSION_SECRET=<random-string>   # Session encryption key
ARXOS_CORS_ORIGINS=https://app.com     # Allowed CORS origins
ARXOS_RATE_LIMIT=1000                  # Requests per hour

# Cloud features
ARXOS_CLOUD_ENDPOINT=https://api.arxos.io
ARXOS_CLOUD_API_KEY=<your-api-key>
ARXOS_SYNC_INTERVAL=5m
```

### Configuration File

Create `config.yaml`:

```yaml
mode: production
port: 8080
state_dir: /var/lib/arxos

database:
  path: /var/lib/arxos/arxos.db
  max_connections: 25
  
security:
  session_secret: ${SESSION_SECRET}
  cors_origins:
    - https://app.example.com
    - https://www.example.com
  rate_limit:
    requests_per_hour: 1000
    
cloud:
  enabled: true
  endpoint: https://api.arxos.io
  api_key: ${API_KEY}
  sync_interval: 5m
  
telemetry:
  enabled: true
  endpoint: https://telemetry.arxos.io
```

## Reverse Proxy Setup

### Nginx

```nginx
server {
    listen 80;
    server_name arxos.example.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name arxos.example.com;

    ssl_certificate /etc/letsencrypt/live/arxos.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/arxos.example.com/privkey.pem;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;

    location / {
        proxy_pass http://localhost:8080;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Server-sent events
    location /events {
        proxy_pass http://localhost:8080/events;
        proxy_http_version 1.1;
        proxy_set_header Connection '';
        proxy_buffering off;
        proxy_cache off;
    }
}
```

### Caddy

```caddyfile
arxos.example.com {
    reverse_proxy localhost:8080
    
    header {
        X-Frame-Options SAMEORIGIN
        X-Content-Type-Options nosniff
        X-XSS-Protection "1; mode=block"
    }
}
```

## SSL/TLS Setup

### Let's Encrypt with Certbot

```bash
# Install certbot
sudo apt-get update
sudo apt-get install certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d arxos.example.com

# Auto-renewal
sudo systemctl enable certbot.timer
```

### Built-in TLS

ArxOS can serve HTTPS directly:

```bash
./arxos-server \
  -port 443 \
  -tls-cert /path/to/cert.pem \
  -tls-key /path/to/key.pem
```

## Database Management

### Backup

```bash
# SQLite backup
sqlite3 /var/lib/arxos/arxos.db ".backup /backup/arxos-$(date +%Y%m%d).db"

# Or use the built-in backup
./arxos-server backup --output /backup/arxos-backup.db
```

### Restore

```bash
# SQLite restore
cp /backup/arxos-20240120.db /var/lib/arxos/arxos.db

# Or use the built-in restore
./arxos-server restore --input /backup/arxos-backup.db
```

### Migration

```bash
# Run migrations
./arxos-server migrate

# Rollback
./arxos-server migrate --rollback --version 3
```

## Monitoring

### Health Checks

```bash
# Basic health check
curl http://localhost:8080/health

# Detailed health check
curl http://localhost:8080/ready
```

### Prometheus Metrics

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'arxos'
    static_configs:
      - targets: ['localhost:8080']
    metrics_path: '/metrics'
```

### Logging

Configure structured logging:

```yaml
logging:
  level: info
  format: json
  output: /var/log/arxos/server.log
  rotate:
    max_size: 100MB
    max_age: 30d
    max_backups: 10
```

## Performance Tuning

### SQLite Optimization

```sql
-- Run these pragmas on startup
PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;
PRAGMA cache_size = -64000;  -- 64MB cache
PRAGMA temp_store = MEMORY;
PRAGMA mmap_size = 268435456;  -- 256MB memory-mapped I/O
```

### System Limits

```bash
# Increase file descriptors
echo "* soft nofile 65536" >> /etc/security/limits.conf
echo "* hard nofile 65536" >> /etc/security/limits.conf

# Increase network buffers
echo "net.core.rmem_max = 134217728" >> /etc/sysctl.conf
echo "net.core.wmem_max = 134217728" >> /etc/sysctl.conf
sysctl -p
```

### Resource Limits

```yaml
# Docker resource limits
deploy:
  resources:
    limits:
      cpus: '2'
      memory: 1G
    reservations:
      cpus: '0.5'
      memory: 256M
```

## Security Hardening

### Firewall Rules

```bash
# UFW (Ubuntu)
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable

# iptables
sudo iptables -A INPUT -p tcp --dport 8080 -j ACCEPT
sudo iptables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT
sudo iptables -P INPUT DROP
```

### Security Headers

Always set these headers (handled by ArxOS automatically):

- `X-Frame-Options: SAMEORIGIN`
- `X-Content-Type-Options: nosniff`
- `X-XSS-Protection: 1; mode=block`
- `Content-Security-Policy: default-src 'self'`
- `Strict-Transport-Security: max-age=31536000`

### Rate Limiting

Built-in rate limiting is enabled by default:

```yaml
rate_limiting:
  enabled: true
  requests_per_hour: 1000
  burst: 100
```

## Troubleshooting

### Common Issues

#### Port Already in Use

```bash
# Find process
lsof -i:8080
# Kill it
kill -9 <PID>
```

#### Database Locked

```bash
# Check for locks
fuser /var/lib/arxos/arxos.db
# Enable WAL mode
sqlite3 /var/lib/arxos/arxos.db "PRAGMA journal_mode=WAL;"
```

#### High Memory Usage

```bash
# Check memory
free -h
# Restart service
sudo systemctl restart arxos
```

### Debug Mode

```bash
# Enable debug logging
ARXOS_LOG_LEVEL=debug ./arxos-server

# Enable pprof
./arxos-server -pprof

# Access pprof
go tool pprof http://localhost:6060/debug/pprof/heap
```

## Scaling

### Horizontal Scaling

ArxOS supports horizontal scaling with shared storage:

```yaml
# Multiple instances with shared NFS
volumes:
  - type: nfs
    source: nfs-server:/arxos-data
    target: /var/lib/arxos
```

### Load Balancing

Use any standard load balancer:

```nginx
upstream arxos {
    server arxos1:8080;
    server arxos2:8080;
    server arxos3:8080;
}

server {
    location / {
        proxy_pass http://arxos;
    }
}
```

## Support

- Documentation: https://docs.arxos.io
- GitHub Issues: https://github.com/arxos/arxos/issues
- Email: support@arxos.io