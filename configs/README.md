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
├── infrastructure/        # Infrastructure and deployment configs
│   ├── nginx/            # Web server configuration
│   ├── prometheus/       # Monitoring configuration
│   └── grafana/          # Dashboard configuration
└── api.example.yaml      # API server configuration example
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
# Core configuration
export ARXOS_MODE=development
export ARXOS_VERSION=1.0.0
export ARXOS_STATE_DIR=./state
export ARXOS_CACHE_DIR=./cache

# Database configuration
export ARXOS_DB_HOST=localhost
export ARXOS_DB_PORT=5432
export ARXOS_DB_NAME=arxos
export ARXOS_DB_USER=arxos
export ARXOS_DB_PASSWORD=password

# PostGIS configuration (primary database)
export POSTGIS_HOST=localhost
export POSTGIS_PORT=5432
export POSTGIS_DATABASE=arxos
export POSTGIS_USER=arxos
export POSTGIS_PASSWORD=password
export POSTGIS_SSLMODE=disable
export POSTGIS_SRID=900913

# Security configuration
export ARXOS_JWT_SECRET=your-secure-jwt-secret-key
export ARXOS_JWT_EXPIRY=24h
export ARXOS_ENABLE_AUTH=true
export ARXOS_ENABLE_TLS=false

# Redis configuration
export REDIS_HOST=localhost
export REDIS_PORT=6379
export REDIS_PASSWORD=""
export REDIS_DB=0

# API configuration
export ARXOS_API_TIMEOUT=30s
export ARXOS_API_RETRY_ATTEMPTS=3
export ARXOS_API_RETRY_DELAY=1s
```

## Configuration Structure

### Core Configuration
```yaml
# Core settings
mode: local                    # local, cloud, hybrid
version: "1.0.0"
state_dir: "./state"
cache_dir: "./cache"

# Cloud settings
cloud:
  enabled: false
  base_url: "https://api.arxos.io"
  sync_enabled: false
  sync_interval: "5m"

# Storage settings
storage:
  backend: "local"             # local, s3, gcs, azure
  local_path: "./data"
  cloud_bucket: ""
  cloud_region: ""
  cloud_prefix: "arxos"
```

### Database Configuration
```yaml
# PostGIS configuration (primary)
postgis:
  host: "localhost"
  port: 5432
  database: "arxos"
  user: "arxos"
  password: ""
  ssl_mode: "disable"
  srid: 900913

# Database configuration (legacy)
database:
  type: "postgis"
  driver: "postgres"
  host: "localhost"
  port: 5432
  database: "arxos"
  username: "arxos"
  ssl_mode: "disable"
  max_open_conns: 25
  max_idle_conns: 5
  conn_lifetime: "30m"
  migrations_path: "./internal/migrations"
  auto_migrate: true
```

### Security Configuration
```yaml
security:
  jwt_secret: "change-this-secret-in-production"
  jwt_expiry: "24h"
  jwt_algorithm: "HS256"        # HS256, HS384, HS512, RS256, RS384, RS512
  session_timeout: "24h"
  api_rate_limit: 1000
  api_rate_limit_window: "1m"
  enable_auth: false
  enable_tls: false
  allowed_origins: ["*"]
  bcrypt_cost: 10
```

### Test Configuration
```yaml
# Test environment configuration
postgis:
  host: "localhost"
  port: 5432
  database: "arxos_test"       # Separate test database
  user: "arxos_test"           # Separate test user
  password: "test_password"
  ssl_mode: "disable"
  srid: 900913

security:
  jwt_secret: "test_jwt_secret_key_for_integration_tests"
  jwt_expiry: "24h"
  jwt_algorithm: "HS256"
  cors_origins: ["*"]
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

## Test Database Setup

For testing, you need to set up a separate test database:

```bash
# Create test database and user
psql -h localhost -p 5432 -U postgres -d postgres -c "
CREATE USER arxos_test WITH PASSWORD 'test_password' CREATEDB;
CREATE DATABASE arxos_test OWNER arxos_test;
"

# Grant permissions and enable extensions
psql -h localhost -p 5432 -U postgres -d arxos_test -c "
ALTER USER arxos_test CREATEDB CREATEROLE SUPERUSER;
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;
CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";
"
```

## Development

To modify configuration:

1. Edit the appropriate file in `configs/`
2. Use environment variables for overrides
3. Test with `arx config validate`
4. Deploy with `arx config generate`

## Configuration Validation

```bash
# Validate configuration
arx config validate

# Generate configuration from templates
arx config generate --env=production

# Test configuration loading
arx config test --config=configs/environments/development.yml
```

## Migration Notes

### Phase 1 Changes (Configuration Standardization)
- Standardized environment variables to use `ARXOS_` prefix
- Unified configuration loading system
- Added PostGIS as primary database configuration
- Added JWT algorithm configuration
- Created test configuration structure

### Phase 4 Changes (Database ID Standardization)
- Added UUID support to all database tables
- Created migration system for legacy IDs
- Added test database setup requirements
- Updated configuration for dual-ID support