# ArxOS Configuration Files

This directory contains configuration files for different ArxOS components and deployment scenarios.

## Structure

```
configs/
├── development.yml      # Development environment configuration
├── production.yml       # Production environment configuration
├── daemon.yaml         # Daemon service configuration
├── nginx/              # Nginx reverse proxy configurations
│   ├── nginx.conf     # Main nginx configuration
│   └── sites/         # Site-specific configurations
│       ├── arxos.conf      # ArxOS API configuration
│       └── monitoring.conf # Monitoring services
└── README.md           # This file
```

## Configuration Files

### Application Configurations

#### development.yml
- **Purpose**: Development environment settings with PostGIS primary
- **Features**: Debug logging, hot reload, lower security settings for ease of development
- **Database**: PostGIS only
- **Usage**: `arx --config configs/development.yml`

#### production.yml
- **Purpose**: Production environment with hardened security and performance tuning
- **Features**: JSON logging, TLS enabled, Redis caching, monitoring integration
- **Database**: PostGIS only (no fallback)
- **Usage**: `arx --config configs/production.yml`

### Service Configurations

#### daemon.yaml
- **Purpose**: File watching daemon for automatic IFC import/export
- **Features**:
  - Directory watching for IFC files
  - Automatic import processing
  - Scheduled exports (BIM, CSV, JSON)
  - Repository synchronization
  - Health monitoring
- **Usage**: `arx daemon start --config configs/daemon.yaml`

### Nginx Configurations

#### nginx/nginx.conf
- **Purpose**: Main nginx configuration with performance optimizations
- **Features**:
  - HTTP/2 and SSL/TLS support
  - Gzip compression
  - Rate limiting zones
  - Upstream load balancing
  - Security headers

#### nginx/sites/arxos.conf
- **Purpose**: ArxOS API reverse proxy configuration
- **Endpoints**:
  - `/api/v1/` - Main API endpoints with caching
  - `/api/v1/auth/` - Authentication with strict rate limiting
  - `/api/v1/upload/` - File uploads with increased limits
  - `/api/v1/ws/` - WebSocket connections
  - `/health`, `/ready`, `/metrics` - Health and monitoring

#### nginx/sites/monitoring.conf
- **Purpose**: Monitoring services reverse proxy
- **Services**:
  - Grafana: `grafana.arxos.example.com`
  - Prometheus: `prometheus.arxos.example.com`
  - Jaeger: `jaeger.arxos.example.com`
  - PgAdmin: `pgadmin.arxos.example.com`

## Environment Variables

All configurations support environment variable substitution using the format `${VARIABLE_NAME:-default_value}`.

### Common Variables

```bash
# Database
POSTGIS_HOST=localhost
POSTGIS_PORT=5432
POSTGRES_DB=arxos
POSTGRES_USER=arxos
POSTGRES_PASSWORD=secure_password

# Application
ARX_DB_TYPE=postgis  # postgis only
ARX_LOG_LEVEL=info
API_PORT=8080

# Daemon
DAEMON_WATCH_PATHS=/data/ifc
DAEMON_AUTO_IMPORT=true
DAEMON_AUTO_EXPORT=true

# Security
JWT_SECRET=change-in-production
ARX_ENABLE_TLS=true
```

## Usage Examples

### Development Setup

```bash
# Start with development configuration
arx --config configs/development.yml serve

# Start daemon for file watching
arx daemon start --config configs/daemon.yaml
```

### Production Deployment with Docker

```bash
# Using Docker Compose
docker-compose -f docker/docker-compose.base.yml \
               -f docker/docker-compose.prod.yml up -d

# The container will automatically use production.yml
```

### Nginx Setup

```bash
# Copy nginx configurations to nginx directory
cp -r configs/nginx/* /etc/nginx/

# Test configuration
nginx -t

# Reload nginx
nginx -s reload
```

## Configuration Priority

Configurations are loaded in the following order (later overrides earlier):

1. Built-in defaults
2. Configuration file (development.yml, production.yml, etc.)
3. Environment variables
4. Command-line flags

## Features Comparison

| Feature | Development | Production |
|---------|------------|------------|
| Database | PostGIS only | PostGIS only |
| Logging | Text/Debug | JSON/Warn |
| TLS | Disabled | Enabled |
| Caching | Memory | Redis |
| Rate Limiting | Relaxed | Strict |
| Debug Endpoints | Enabled | Disabled |
| Hot Reload | Enabled | Disabled |
| Monitoring | Optional | Enabled |

## PostGIS Configuration

All configurations now support PostGIS as the primary spatial database:

- **SRID 900913**: Custom coordinate system for millimeter precision
- **Connection Pooling**: Optimized for concurrent access
- **Spatial Indices**: Automatic creation for geometry columns
- **Query Caching**: Enabled for improved performance

## Security Notes

### Development
- Uses default passwords (change in production!)
- CORS allows localhost origins
- Debug endpoints exposed
- TLS disabled for ease of development

### Production
- Requires strong passwords via environment variables
- CORS restricted to configured domains
- Debug endpoints disabled
- TLS required with proper certificates
- Rate limiting enforced
- Security headers applied

## Monitoring Integration

Both development and production configurations support monitoring:

- **Prometheus**: Metrics collection on port 9090
- **Grafana**: Visualization on port 3000
- **Jaeger**: Distributed tracing on port 16686
- **Health Checks**: `/health`, `/ready`, `/metrics` endpoints

## Troubleshooting

### Configuration Not Loading

1. Check file path: `arx --config path/to/config.yml`
2. Validate YAML syntax: `yamllint configs/*.yml`
3. Check environment variables: `env | grep ARX_`
4. Review logs: `arx --config configs/development.yml --log-level debug`

### Database Connection Issues

1. Verify PostGIS is running: `docker ps | grep postgis`
2. Check connection settings in config file
3. Test connection: `psql -h localhost -U arxos -d arxos`
4. Review database logs: `docker logs arxos-postgis`

### Nginx Issues

1. Test configuration: `nginx -t`
2. Check error logs: `tail -f /var/log/nginx/error.log`
3. Verify upstream services: `curl http://arxos-api:8080/health`
4. Check SSL certificates: `openssl x509 -in /etc/nginx/ssl/arxos.crt -text`

## Best Practices

1. **Never commit sensitive data** - Use environment variables for secrets
2. **Use appropriate config for environment** - Don't use development.yml in production
3. **Rotate secrets regularly** - Especially JWT secrets and database passwords
4. **Monitor resource usage** - Set appropriate limits in configuration
5. **Keep configurations versioned** - Track changes in Git
6. **Test configuration changes** - Use staging environment first
7. **Document custom settings** - Add comments for non-obvious configurations

## Migration from Old Configuration

If upgrading from previous configuration:

1. Update database type to `postgis`
2. Add PostGIS connection settings
3. Run migrations: `arx migrate up`
4. Verify spatial extensions: `arx db check`

## Support

For configuration issues:
1. Check documentation: `/docs/configuration.md`
2. Review examples in this directory
3. Open issue: https://github.com/arx-os/arxos/issues