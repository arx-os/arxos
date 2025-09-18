# ArxOS Docker Configuration

This directory contains the modular Docker setup for ArxOS, organized for different environments and use cases.

## Structure

```
docker/
├── docker-compose.base.yml      # Core services (PostGIS, API)
├── docker-compose.dev.yml       # Development additions (daemon, pgadmin, redis)
├── docker-compose.prod.yml      # Production configuration
├── docker-compose.test.yml      # Test environment
├── docker-compose.monitoring.yml # Observability stack
└── README.md                    # This file
```

## Quick Start

### Development (Default)
```bash
# Uses the root docker-compose.yml which includes base + dev
docker-compose up

# With optional services
docker-compose --profile debug up    # Includes PgAdmin
docker-compose --profile cache up    # Includes Redis
```

### Production
```bash
# Minimal production setup
docker-compose -f docker/docker-compose.base.yml -f docker/docker-compose.prod.yml up -d

# Production with monitoring
docker-compose \
  -f docker/docker-compose.base.yml \
  -f docker/docker-compose.prod.yml \
  -f docker/docker-compose.monitoring.yml \
  up -d
```

### Testing
```bash
# Run all tests in Docker
docker-compose -f docker/docker-compose.test.yml up --abort-on-container-exit

# Clean up after tests
docker-compose -f docker/docker-compose.test.yml down -v
```

## Services

### Core Services (base.yml)
- **postgis**: PostGIS 16.3.4 spatial database
- **arxos-api**: REST API server

### Development Services (dev.yml)
- **arxos-daemon**: File watcher for IFC imports
- **pgadmin**: Database management UI (profile: debug)
- **redis**: Cache layer (profile: cache)

### Production Services (prod.yml)
- **nginx**: Reverse proxy with SSL termination
- **arxos-daemon**: Production daemon configuration
- Enhanced resource limits and health checks

### Monitoring Services (monitoring.yml)
- **prometheus**: Metrics collection
- **grafana**: Metrics visualization
- **loki**: Log aggregation
- **promtail**: Log shipping
- **jaeger**: Distributed tracing

### Test Services (test.yml)
- **postgis-test**: Isolated test database
- **test-runner**: Go test execution
- **sqlite-test-runner**: SQLite fallback testing

## Environment Variables

Create a `.env` file in the project root:

```env
# Database
POSTGRES_DB=arxos
POSTGRES_USER=arxos
POSTGRES_PASSWORD=secure_password_here
POSTGIS_PORT=5432

# Application
API_PORT=8080
LOG_LEVEL=info

# Development
PGADMIN_EMAIL=admin@arxos.local
PGADMIN_PASSWORD=admin
PGADMIN_PORT=5050
REDIS_PORT=6379

# Monitoring
PROMETHEUS_PORT=9090
GRAFANA_PORT=3000
GRAFANA_USER=admin
GRAFANA_PASSWORD=admin
LOKI_PORT=3100
JAEGER_UI_PORT=16686

# Daemon
DAEMON_WATCH_PATHS=/data/ifc
DAEMON_POLL_INTERVAL=5s
DAEMON_AUTO_EXPORT=true
```

## Common Commands

### View logs
```bash
docker-compose logs -f arxos-api
docker-compose logs -f postgis
```

### Access database
```bash
# Via psql
docker exec -it arxos-postgis psql -U arxos -d arxos

# Via PgAdmin (development)
# Navigate to http://localhost:5050
```

### Scale services (production)
```bash
docker-compose -f docker/docker-compose.base.yml -f docker/docker-compose.prod.yml \
  up -d --scale arxos-api=3
```

### Backup database
```bash
docker exec arxos-postgis pg_dump -U arxos arxos > backup.sql
```

### Restore database
```bash
docker exec -i arxos-postgis psql -U arxos arxos < backup.sql
```

## Troubleshooting

### Port conflicts
If ports are already in use, override them in `.env`:
```env
POSTGIS_PORT=5433
API_PORT=8081
```

### Permission issues
Ensure directories exist with correct permissions:
```bash
mkdir -p data/{ifc,exports}
chmod 755 data/{ifc,exports}
```

### Clean restart
```bash
docker-compose down -v  # Remove volumes
docker-compose up --build  # Rebuild images
```

## Architecture Notes

1. **PostGIS Primary**: Uses PostGIS as the primary database with spatial capabilities
2. **SQLite Fallback**: Application supports SQLite for environments without PostGIS
3. **Hybrid Mode**: Can operate with both databases simultaneously
4. **Millimeter Precision**: Custom SRID 900913 for building-local coordinates
5. **Git-like Versioning**: Building data tracked with repository-style versioning

## Security Considerations

- Change default passwords in production
- Use Docker secrets for sensitive data
- Enable TLS in production (see nginx configuration)
- Implement rate limiting at nginx level
- Regular security updates for base images

## Performance Tuning

- PostGIS configured with spatial indices and optimizations
- Connection pooling enabled
- Resource limits set for production
- Monitoring stack for performance insights

## Maintenance

### Update images
```bash
docker-compose pull
docker-compose up -d
```

### Clean unused resources
```bash
docker system prune -a
```

### View resource usage
```bash
docker stats
```