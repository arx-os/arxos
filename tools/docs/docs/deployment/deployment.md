# Deployment Guide

## Overview

This guide covers deployment of the Arxos SVG-BIM integration system in various environments.

## System Components

### Core Services
- **arx_svg_parser**: Main Python application with FastAPI
- **arx-symbol-library**: JSON-based symbol definitions
- **arx-backend**: Go-based backend services
- **arx-web-frontend**: Web interface

### Infrastructure
- **arx-database**: SQLite database with migrations
- **arx-infra**: Nginx configuration and infrastructure
- **arx-devops**: CI/CD pipeline and automation

## Development Environment

### Prerequisites
- Python 3.8+
- Go 1.19+
- Node.js 16+
- Docker and Docker Compose

### Local Setup
```bash
# Clone repository
git clone https://github.com/arxos/arxos.git
cd arxos

# Install Python dependencies
cd arx_svg_parser
pip install -r requirements.txt

# Install Go dependencies
cd ../arx-backend
go mod download

# Install Node.js dependencies
cd ../arx-web-frontend
npm install
```

### Environment Configuration
```bash
# Create environment file
cp .env.example .env

# Configure environment variables
export ARX_ENV=development
export ARX_DEBUG=true
export ARX_DB_PATH=./arx_database/arxos_dev.db
```

## Docker Deployment

### Docker Compose Setup
```yaml
version: '3.8'

services:
  arx-svg-parser:
    build: ./arx_svg_parser
    ports:
      - "8000:8000"
    environment:
      - ARX_ENV=production
      - ARX_DB_PATH=/app/data/arxos.db
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs

  arx-backend:
    build: ./arx-backend
    ports:
      - "8080:8080"
    environment:
      - ARX_ENV=production
      - ARX_DB_PATH=/app/data/arxos.db
    volumes:
      - ./data:/app/data

  arx-web-frontend:
    build: ./arx-web-frontend
    ports:
      - "3000:3000"
    environment:
      - REACT_APP_API_URL=http://localhost:8000
      - REACT_APP_BACKEND_URL=http://localhost:8080

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./arx-infra/nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - arx-svg-parser
      - arx-backend
      - arx-web-frontend
```

### Build and Deploy
```bash
# Build all services
docker-compose build

# Start services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

## Production Deployment

### Server Requirements
- **CPU**: 4+ cores
- **Memory**: 8GB+ RAM
- **Storage**: 100GB+ SSD
- **Network**: High-speed internet connection

### Production Setup
```bash
# Install system dependencies
sudo apt update
sudo apt install python3 python3-pip nodejs npm nginx

# Create application user
sudo useradd -m -s /bin/bash arxos
sudo usermod -aG docker arxos

# Clone application
sudo -u arxos git clone https://github.com/arxos/arxos.git /home/arxos/app
cd /home/arxos/app

# Setup Python environment
sudo -u arxos python3 -m venv venv
sudo -u arxos venv/bin/pip install -r arx_svg_parser/requirements.txt

# Setup database
sudo -u arxos mkdir -p /home/arxos/app/data
sudo -u arxos sqlite3 /home/arxos/app/data/arxos.db < arx-database/001_create_arx_schema.sql
```

### Systemd Services
```ini
# /etc/systemd/system/arx-svg-parser.service
[Unit]
Description=Arxos SVG Parser
After=network.target

[Service]
Type=simple
User=arxos
WorkingDirectory=/home/arxos/app/arx_svg_parser
Environment=PATH=/home/arxos/app/venv/bin
ExecStart=/home/arxos/app/venv/bin/python -m uvicorn api.main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

```ini
# /etc/systemd/system/arx-backend.service
[Unit]
Description=Arxos Backend
After=network.target

[Service]
Type=simple
User=arxos
WorkingDirectory=/home/arxos/app/arx-backend
ExecStart=/home/arxos/app/arx-backend/arx-backend
Restart=always

[Install]
WantedBy=multi-user.target
```

### Nginx Configuration
```nginx
# /etc/nginx/sites-available/arxos
server {
    listen 80;
    server_name arxos.example.com;

    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name arxos.example.com;

    ssl_certificate /etc/nginx/ssl/arxos.crt;
    ssl_certificate_key /etc/nginx/ssl/arxos.key;

    # API endpoints
    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Backend endpoints
    location /backend/ {
        proxy_pass http://localhost:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Frontend
    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## Monitoring and Logging

### Application Monitoring
```python
# arx_svg_parser/monitoring.py
import logging
from prometheus_client import Counter, Histogram, start_http_server

# Metrics
REQUEST_COUNT = Counter('arx_requests_total', 'Total requests')
REQUEST_DURATION = Histogram('arx_request_duration_seconds', 'Request duration')

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/arxos/app.log'),
        logging.StreamHandler()
    ]
)
```

### Health Checks
```python
# arx_svg_parser/api/health.py
from fastapi import APIRouter

router = APIRouter()

@router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }

@router.get("/ready")
async def readiness_check():
    # Check database connection
    # Check symbol library
    # Check external services
    return {"status": "ready"}
```

## Security Configuration

### SSL/TLS Setup
```bash
# Generate SSL certificate
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout /etc/nginx/ssl/arxos.key \
    -out /etc/nginx/ssl/arxos.crt

# Configure SSL
sudo nginx -t
sudo systemctl reload nginx
```

### Firewall Configuration
```bash
# Configure UFW firewall
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

### Authentication Setup
```python
# arx_svg_parser/auth/jwt.py
from datetime import datetime, timedelta
import jwt

SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
```

## Backup and Recovery

### Database Backup
```bash
#!/bin/bash
# backup.sh

BACKUP_DIR="/home/arxos/backups"
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup directory
mkdir -p $BACKUP_DIR

# Backup database
sqlite3 /home/arxos/app/data/arxos.db ".backup $BACKUP_DIR/arxos_$DATE.db"

# Backup symbol library
tar -czf $BACKUP_DIR/symbols_$DATE.tar.gz /home/arxos/app/arx-symbol-library/

# Cleanup old backups (keep last 7 days)
find $BACKUP_DIR -name "*.db" -mtime +7 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete
```

### Recovery Procedures
```bash
#!/bin/bash
# restore.sh

BACKUP_FILE=$1
RESTORE_DIR="/home/arxos/app/data"

# Stop services
sudo systemctl stop arx-svg-parser
sudo systemctl stop arx-backend

# Restore database
sqlite3 $RESTORE_DIR/arxos.db ".restore $BACKUP_FILE"

# Restore symbol library
tar -xzf symbols_backup.tar.gz -C /home/arxos/app/

# Start services
sudo systemctl start arx-backend
sudo systemctl start arx-svg-parser
```

## Performance Optimization

### Database Optimization
```sql
-- Create indexes for better performance
CREATE INDEX idx_symbols_system ON symbols(system);
CREATE INDEX idx_symbols_category ON symbols(category);
CREATE INDEX idx_symbols_created ON symbols(created_at);

-- Optimize database settings
PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;
PRAGMA cache_size = 10000;
PRAGMA temp_store = MEMORY;
```

### Application Optimization
```python
# arx_svg_parser/config.py
import os

# Performance settings
MAX_WORKERS = int(os.getenv('MAX_WORKERS', 4))
WORKER_TIMEOUT = int(os.getenv('WORKER_TIMEOUT', 30))
MAX_CONNECTIONS = int(os.getenv('MAX_CONNECTIONS', 100))

# Caching settings
CACHE_TTL = int(os.getenv('CACHE_TTL', 3600))
CACHE_MAX_SIZE = int(os.getenv('CACHE_MAX_SIZE', 1000))
```

## Troubleshooting

### Common Issues
1. **Service won't start**: Check logs and configuration
2. **Database connection errors**: Verify database path and permissions
3. **Symbol loading errors**: Check JSON file format and schema
4. **API authentication errors**: Verify JWT configuration

### Debug Commands
```bash
# Check service status
sudo systemctl status arx-svg-parser
sudo systemctl status arx-backend

# View logs
sudo journalctl -u arx-svg-parser -f
sudo journalctl -u arx-backend -f

# Check database
sqlite3 /home/arxos/app/data/arxos.db ".tables"

# Test API
curl -X GET http://localhost:8000/api/v1/health
```

### Performance Monitoring
```bash
# Monitor system resources
htop
iotop
nethogs

# Monitor application performance
curl -X GET http://localhost:8000/metrics
```

## Scaling Considerations

### Horizontal Scaling
- **Load Balancer**: Use nginx or HAProxy for load balancing
- **Multiple Instances**: Deploy multiple application instances
- **Database Clustering**: Use database clustering for high availability
- **Caching Layer**: Implement Redis for caching

### Vertical Scaling
- **Resource Monitoring**: Monitor CPU, memory, and disk usage
- **Resource Limits**: Set appropriate resource limits
- **Performance Tuning**: Optimize application performance
- **Capacity Planning**: Plan for future growth
