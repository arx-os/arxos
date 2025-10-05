# ArxOS Platform Configuration

This directory contains system-level configuration files for the ArxOS Building Operating System platform.

## Directory Structure

```
configs/
├── environments/           # Environment-specific application configs
│   ├── development.yml    # Development environment settings
│   ├── production.yml     # Production environment settings
│   └── test.yml          # Test environment settings
├── services/              # External service configurations
│   ├── postgis.yml       # PostGIS database configuration
│   ├── redis.yml         # Redis cache configuration
│   └── ifc-service.yml   # IfcOpenShell service configuration
└── infrastructure/        # Infrastructure and deployment configs
    ├── nginx/            # Web server configuration
    ├── prometheus/       # Monitoring configuration
    └── grafana/          # Dashboard configuration
```

## Configuration Loading

The ArxOS application loads configuration in the following order:

1. **Default values** (from `internal/config` package)
2. **Environment-specific config** (from `configs/environments/`)
3. **Service configs** (from `configs/services/`)
4. **Environment variables** (override all file-based configs)

## Environment Variables

All configuration values can be overridden using environment variables with the `ARXOS_` prefix:

```bash
# Database configuration
export ARXOS_DB_HOST=localhost
export ARXOS_DB_PORT=5432
export ARXOS_DB_NAME=arxos

# PostGIS configuration
export POSTGIS_HOST=localhost
export POSTGIS_PORT=5432
export POSTGIS_DATABASE=arxos

# Redis configuration
export REDIS_HOST=localhost
export REDIS_PORT=6379
```

## Service Configuration

Each service has its own configuration file in `configs/services/`:

- **PostGIS**: Spatial database configuration
- **Redis**: Cache and session storage
- **IFC Service**: Building model processing

## Infrastructure Configuration

Infrastructure components are configured in `configs/infrastructure/`:

- **Nginx**: Web server and reverse proxy
- **Prometheus**: Metrics collection and monitoring
- **Grafana**: Dashboards and visualization

## Development

To modify configuration:

1. Edit the appropriate file in `configs/`
2. Use environment variables for overrides
3. Test with `arx config validate`
4. Deploy with `arx config generate`