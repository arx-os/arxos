# ArxOS Deployment Guide

## Quick Start

### Local Development
```bash
# Start the API server
go run ./cmd/arxos-server --port 8080 --db ./data/arxos.db

# Start the CLI interface
go run ./cmd/arx

# Start the daemon
go run ./cmd/arxd
```

### Docker Deployment
```bash
# Build and start all services
docker-compose up -d

# Check service health
docker-compose ps
docker-compose logs arxos-server
```

## Production Deployment

### Prerequisites
- Docker and Docker Compose installed
- Domain name configured (optional, for HTTPS)
- SSL certificate or Let's Encrypt setup

### Environment Configuration

Create a `.env` file:
```env
# Server Configuration
ARXOS_PORT=8080
ARXOS_DB_PATH=/app/data/arxos.db
ARXOS_LOG_LEVEL=info

# Security
ARXOS_CORS_ORIGINS=https://yourdomain.com,https://app.yourdomain.com
ARXOS_RATE_LIMIT_RPM=100
ARXOS_RATE_LIMIT_BURST=10

# SSL/TLS
TRAEFIK_EMAIL=your-email@example.com
DOMAIN_NAME=yourdomain.com
```

### Deployment Steps

1. **Clone and prepare**:
   ```bash
   git clone https://github.com/arx-os/arxos.git
   cd arxos
   cp .env.example .env
   # Edit .env with your configuration
   ```

2. **Start services**:
   ```bash
   docker-compose up -d
   ```

3. **Verify deployment**:
   ```bash
   curl http://localhost:8080/health
   curl http://localhost:8080/ready
   ```

4. **Setup SSL (production)**:
   ```bash
   # Update docker-compose.yml with your domain
   # Restart to obtain SSL certificates
   docker-compose down
   docker-compose up -d
   ```

### Database Management

#### Backup
```bash
# Manual backup
docker-compose exec arxos-server sqlite3 /app/data/arxos.db ".backup /app/data/backup.db"

# Automated backups are included in docker-compose.yml
```

#### Restore
```bash
# Stop service
docker-compose stop arxos-server

# Restore database
docker-compose run --rm -v ./backups:/backups arxos-server \
  cp /backups/arxos-20231212-120000.db /app/data/arxos.db

# Restart service
docker-compose start arxos-server
```

### Monitoring

#### Health Checks
- Health endpoint: `GET /health`
- Readiness endpoint: `GET /ready`
- Metrics endpoint: `GET /metrics` (if enabled)

#### Logs
```bash
# View logs
docker-compose logs -f arxos-server

# Log levels: debug, info, warn, error
```

### Scaling

#### Horizontal Scaling
```bash
# Scale server instances
docker-compose up -d --scale arxos-server=3

# Load balancer configuration required
```

#### Database Scaling
For high-load scenarios, consider:
- Read replicas
- Connection pooling
- Database sharding (for multi-tenant setups)

### Security Checklist

- [ ] HTTPS enabled with valid certificates
- [ ] CORS origins properly configured
- [ ] Rate limiting enabled
- [ ] Database access restricted
- [ ] Log levels set appropriately
- [ ] Regular security updates
- [ ] Backup strategy implemented

### Troubleshooting

#### Common Issues

1. **Database connection errors**:
   ```bash
   # Check file permissions
   docker-compose exec arxos-server ls -la /app/data/
   
   # Check disk space
   df -h
   ```

2. **High memory usage**:
   ```bash
   # Monitor resource usage
   docker stats
   
   # Adjust memory limits in docker-compose.yml
   ```

3. **SSL certificate issues**:
   ```bash
   # Check Traefik logs
   docker-compose logs traefik
   
   # Verify domain DNS
   nslookup yourdomain.com
   ```

### Performance Tuning

#### Database Optimization
```sql
-- Enable WAL mode for better concurrency
PRAGMA journal_mode=WAL;

-- Optimize cache size
PRAGMA cache_size=10000;

-- Enable foreign keys
PRAGMA foreign_keys=ON;
```

#### Server Configuration
```env
# Increase connection limits
ARXOS_MAX_CONNECTIONS=100

# Adjust timeouts
ARXOS_READ_TIMEOUT=30s
ARXOS_WRITE_TIMEOUT=30s
```

### Updates and Maintenance

#### Updating ArxOS
```bash
# Pull latest changes
git pull origin main

# Rebuild and restart
docker-compose build
docker-compose up -d
```

#### Database Migrations
```bash
# Run migrations
docker-compose exec arxos-server ./arxos-server migrate

# Check migration status
docker-compose exec arxos-server ./arxos-server migrate --status
```

### Support

For issues and support:
- GitHub Issues: https://github.com/arx-os/arxos/issues
- Documentation: https://docs.arxos.dev
- Community: https://discord.gg/arxos