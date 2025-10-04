# ArxOS Docker Configuration

This document explains the organization and usage of Docker Compose files in ArxOS.

## 📁 File Organization

ArxOS follows a clean, intuitive Docker Compose file organization:

```
/docker-compose.yml              # Default development configuration
/docker-compose.override.yml     # Local personal overrides (gitignore'd)
/docker-compose.prod.yml         # Production deployment configuration  
/docker-compose.test.yml         # Integration testing configuration
```

## 🚀 Quick Start

### Development (Default)
```bash
# Start all development services
docker-compose up

# Start with detached mode
docker-compose up -d

# Start specific services only
docker-compose up postgis redis

# View logs
docker-compose logs -f arxos-dev
```

### Production
```bash
# Use production configuration
docker-compose -f docker-compose.prod.yml up -d

# Production with environment file
docker-compose -f docker-compose.prod.yml --env-file .env.production up -d
```

### Testing
```bash
# Start test environment
docker-compose -f docker-compose.test.yml up

# Run integration tests
docker-compose -f docker-compose.test.yml up --abort-on-container-exit
```

## ⚙️ Configuration Files Explained

### `docker-compose.yml` (Default/Development)
- **Purpose**: Primary development environment
- **Usage**: `docker-compose up` 
- **Features**:
  - Source code mounting for live development
  - Debug logging enabled
  - Development database (`arxos_dev`)
  - Redis caching enabled
  - IFC service with development settings

### `docker-compose.override.yml` (Local Customizations)
- **Purpose**: Personal local overrides
- **Usage**: Automatically loaded by `docker-compose`
- **Features**:
  - Local environment variables
  - Custom volume mounts
  - Modified ports
  - Personal database credentials
- **⚠️ Note**: Not committed to version control

### `docker-compose.prod.yml` (Production)
- **Purpose**: Production deployment
- **Usage**: `docker-compose -f docker-compose.prod.yml up`
- **Features**:
  - Production-grade security
  - Resource limits and monitoring
  - Nginx load balancer
  - Prometheus/Grafana monitoring
  - Health checks and restart policies

### `docker-compose.test.yml` (Testing)
- **Purpose**: Integration and testing
- **Usage**: `docker-compose -f docker-compose.test.yml up`
- **Features**:
  - Isolated test database (`arxos_test`)
  - Limited memory usage
  - Test fixtures mounted
  - Debug logging for troubleshooting

## 🔧 Customization

### Local Development Override
Create `docker-compose.override.yml`:
```yaml
services:
  arxos-dev:
    environment:
      - ARXOS_LOG_LEVEL=debug
    volumes:
      - ./my-local-data:/app/local-data
    ports:
      - "9090:9090"  # Debug port
```

### Environment Variables
Create appropriate `.env` files:
```bash
# .env.development
POSTGIS_PASSWORD=my_local_password
ARXOS_LOG_LEVEL=debug

# .env.production  
POSTGIS_PASSWORD=secure_production_password
ARXOS_LOG_LEVEL=info
```

## 📊 Service Architecture

### Development Stack
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   arxos-dev     │────│ ifcopenshell-    │────│     redis        │
│   (Go App)      │    │     service      │    │    (Cache)      │
│   Port: 8080    │    │   (Python)      │    │   Port: 6379    │
│                 │    │   Port: 5000     │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
          │
          │
┌─────────────────┐
│    postgis      │
│   (Database)    │
│   Port: 5432    │
└─────────────────┘
```

### Production Stack
```
[Internet] ──► [Nginx] ──► [ArxOS App] ──► [PostGIS]
                   │                              │
                   └─► [Monitor/Grafana] ─────────┘
```

## 🛠️ Management Commands

### Common Operations
```bash
# Build services
docker-compose build

# Restart specific service
docker-compose restart arxos-dev

# View service status
docker-compose ps

# Clean up
docker-compose down
docker-compose down -v  # Include volumes

# Update services
docker-compose pull
docker-compose up -d --force-recreate
```

### Debug Commands
```bash
# Execute commands in running container
docker-compose exec arxos-dev arxos --help
docker-compose exec postgis psql -U arxos -d arxos_dev

# View logs
docker-compose logs arxos-dev
docker-compose logs --tail=100 ifcopenshell-service

# Check service health
docker-compose exec redis redis-cli ping
curl http://localhost:8080/health
```

## 🔍 Troubleshooting

### Common Issues

1. **Port Conflicts**: Services won't start
   ```bash
   # Check what's using ports
   lsof -i :8080
   lsof -i :5432
   
   # Solution: Modify port mappings in compose files
   ```

2. **Database Connection**: Can't connect to PostGIS
   ```bash
   # Check database is healthy
   docker-compose exec postgis pg_isready -U arxos -d arxos_dev
   
   # Check network connectivity
   docker-compose exec arxos-dev ping postgis
   ```

3. **Volume Issues**: Data not persisting
   ```bash
   # List volumes
   docker volume ls
   
   # Inspect volume
   docker volume inspect arxos_postgis-dev-data
   ```

4. **Build Failures**: Services won't build
   ```bash
   # Clean build
   docker-compose build --no-cache
   
   # Build individual service
   docker-compose build arxos-dev
   ```

### Performance Optimization

For better performance during development:
```yaml
# Add to docker-compose.override.yml
services:
  postgis:
    environment:
      - shared_preload_libraries=pg_stat_statements
      - max_connections=100
      - shared_buffers=256MB
```

## 📚 Additional Resources

- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [ArxOS Development Guide](../../QUICKSTART.md)
- [Production Deployment Guide](../deployment/DEPLOYMENT_GUIDE.md)
