# ArxOS Quick Start Guide

Get up and running with ArxOS in under 5 minutes!

## Prerequisites

- **Go 1.21+** - [Download](https://golang.org/dl/)
- **Docker & Docker Compose** - [Download](https://www.docker.com/products/docker-desktop)
- **Git** - [Download](https://git-scm.com/downloads)
- **Make** - Usually pre-installed on macOS/Linux
- **PostgreSQL 14+** - [Download](https://www.postgresql.org/download/)

## 🚀 Quick Start

### 1. Clone and Setup

```bash
# Clone the repository
git clone https://github.com/arx-os/arxos.git
cd arxos

# Copy environment configuration
cp .env.example .env

# Start the development environment
docker-compose up -d

# For testing environment, use:
# docker-compose -f docker-compose.test.yml up -d
```

### 2. Database Setup

```bash
# Create main database and user
psql -h localhost -p 5432 -U postgres -d postgres -c "
CREATE USER arxos WITH PASSWORD 'arxos' CREATEDB;
CREATE DATABASE arxos OWNER arxos;
"

# Enable PostGIS extensions
psql -h localhost -p 5432 -U postgres -d arxos -c "
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;
CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";
"

# Create test database and user (for running tests)
psql -h localhost -p 5432 -U postgres -d postgres -c "
CREATE USER arxos_test WITH PASSWORD 'test_password' CREATEDB;
CREATE DATABASE arxos_test OWNER arxos_test;
"

# Enable PostGIS extensions for test database
psql -h localhost -p 5432 -U postgres -d arxos_test -c "
ALTER USER arxos_test CREATEDB CREATEROLE SUPERUSER;
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;
CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";
"
```

### 3. Install Dependencies

```bash
# Download Go modules
go mod download

# Run database migrations
go run cmd/arx/main.go migrate up

# Or use the Makefile for setup
make setup
```

### 4. Build and Run

```bash
# Build the application
make build

# Run the CLI
./bin/arx --help

# Run the API server
./bin/arx server

# Run tests
make test

# Run integration tests
make test-integration
```

## 🔧 Configuration

### Environment Variables

ArxOS uses environment variables with the `ARXOS_` prefix for configuration:

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
export ARXOS_DB_PASSWORD=arxos

# PostGIS configuration (primary database)
export POSTGIS_HOST=localhost
export POSTGIS_PORT=5432
export POSTGIS_DATABASE=arxos
export POSTGIS_USER=arxos
export POSTGIS_PASSWORD=arxos
export POSTGIS_SSLMODE=disable
export POSTGIS_SRID=900913

# Security configuration
export ARXOS_JWT_SECRET=your-secure-jwt-secret-key
export ARXOS_JWT_EXPIRY=24h
export ARXOS_ENABLE_AUTH=false
export ARXOS_ENABLE_TLS=false

# Redis configuration
export REDIS_HOST=localhost
export REDIS_PORT=6379
export REDIS_PASSWORD=""
export REDIS_DB=0
```

### Configuration Files

Configuration files are located in `configs/`:

- `configs/environments/development.yml` - Development settings
- `configs/environments/production.yml` - Production settings
- `configs/environments/test.yml` - Test settings
- `configs/api.example.yaml` - API server configuration example

## 🧪 Testing

### Run Tests

```bash
# Unit tests
make test

# Integration tests
make test-integration

# Specific test
go test -v ./test/integration/services/ -run TestBuildingService

# Test with timeout
go test -v ./test/integration/services/ -run TestBuildingService -timeout 2m
```

### Test Database

The test suite uses a separate database (`arxos_test`) to avoid conflicts with development data. Make sure you've set up the test database as shown in the Database Setup section above.

## 📱 Mobile Development

### Prerequisites

- **Node.js 20+** - [Download](https://nodejs.org/)
- **React Native CLI** - `npm install -g @react-native-community/cli`
- **iOS**: Xcode 15+ and iOS Simulator
- **Android**: Android Studio and Android SDK

### Setup

```bash
# Navigate to mobile directory
cd mobile

# Install dependencies
npm install

# iOS setup
cd ios && pod install && cd ..

# Run on iOS
npm run ios

# Run on Android
npm run android
```

### Mobile Dependencies

The mobile app uses modern dependencies:

- **React Native**: 0.73.6
- **TypeScript**: 5.3.3
- **React**: 18.3.1
- **Node.js**: 20+

## 🏗️ First Building

### Create Your First Building

```bash
# Create a building
./bin/arx building create --name "Main Campus" --address "123 University Ave"

# Add floors
./bin/arx building floor add --building "Main Campus" --name "Ground Floor" --level 0
./bin/arx building floor add --building "Main Campus" --name "First Floor" --level 1

# Add rooms
./bin/arx building room add --building "Main Campus" --floor "Ground Floor" --name "Lobby" --type common
./bin/arx building room add --building "Main Campus" --floor "First Floor" --name "Conference Room A" --type meeting
```

### Import Building Data

```bash
# Import from IFC file
./bin/arx ifc import /path/to/building.ifc

# Import from other formats
./bin/arx import /path/to/building.json
```

### Query Building Data

```bash
# List all buildings
./bin/arx building list

# Query specific rooms
./bin/arx query "/Main Campus/First Floor/*" --type meeting

# Get building statistics
./bin/arx building stats "Main Campus"
```

## 🔧 Development Commands

### Testing

```bash
# Run all tests
make test

# Run tests with coverage
make test-coverage

# Run integration tests
make test-integration

# Run specific module tests
go test ./internal/spatial/...
```

### Building

```bash
# Build for current platform
make build

# Build for all platforms
make build-all

# Clean build artifacts
make clean
```

### Development Server

```bash
# Start development server
make run-dev

# View logs
make logs

# Stop all services
make stop
```

## 📊 Monitoring

### Performance Monitoring

```bash
# Run performance tests
make perf-test

# Check service health
make health

# View system logs
make logs
```

### System Health

```bash
# Check system health
make health

# View system status
./bin/arx status

# Check database connectivity
docker-compose ps postgis
```

## 🛠️ Common Tasks

### Database Management

```bash
# Run migrations
./bin/arx migrate up

# Rollback migrations
./bin/arx migrate down

# Create new migration
./bin/arx migrate create "add_new_table"

# Reset database
make db-reset
```

### Configuration

```bash
# View current configuration
./bin/arx config show

# Set configuration value
./bin/arx config set "database.host" "localhost"

# Validate configuration
./bin/arx config validate
```

### Workflow Automation

```bash
# List workflows
./bin/arx workflow list

# Execute workflow
./bin/arx workflow execute "energy-optimization" --input '{"building_id": "Main Campus"}'

# Test n8n connection
./bin/arx workflow n8n test-connection
```

## 🔍 Troubleshooting

### Common Issues

1. **Database Connection Failed**
   ```bash
   # Check if PostgreSQL is running
   docker ps | grep postgres

   # Check database exists
   psql -h localhost -p 5432 -U postgres -l | grep arxos
   ```

2. **Test Database Issues**
   ```bash
   # Recreate test database
   psql -h localhost -p 5432 -U postgres -d postgres -c "
   DROP DATABASE IF EXISTS arxos_test;
   CREATE DATABASE arxos_test OWNER arxos_test;
   "
   ```

3. **Configuration Issues**
   ```bash
   # Validate configuration
   go run cmd/arx/main.go config validate

   # Test configuration loading
   go run cmd/arx/main.go config test
   ```

4. **Mobile Build Issues**
   ```bash
   # Clean and reinstall
   cd mobile
   rm -rf node_modules package-lock.json
   npm install
   cd ios && pod install && cd ..
   ```

### Logs

```bash
# Application logs
docker-compose logs -f arxos

# Database logs
docker-compose logs -f postgres

# All services
docker-compose logs -f
```

### Getting Help

- **Documentation**: Check `docs/` directory
- **Issues**: [GitHub Issues](https://github.com/arx-os/arxos/issues)
- **Discussions**: [GitHub Discussions](https://github.com/arx-os/arxos/discussions)
- **CLI Help**: `./bin/arx help <command>`

## 🎯 Next Steps

1. **Read the Documentation**: Start with `docs/architecture/SERVICE_ARCHITECTURE.md`
2. **Explore Examples**: Check `examples/` directory
3. **Join the Community**: [GitHub Discussions](https://github.com/arx-os/arxos/discussions)
4. **Develop**: Read `docs/deployment/DEPLOYMENT_GUIDE.md`

## 📚 Additional Resources

- [Architecture Overview](docs/architecture/SERVICE_ARCHITECTURE.md)
- [API Documentation](docs/api/API_DOCUMENTATION.md)
- [Deployment Guide](docs/deployment/DEPLOYMENT_GUIDE.md)
- [Integration Flow](docs/integration/INTEGRATION_FLOW.md)
- [CLI Integration](docs/integration/CLI_INTEGRATION.md)

---

**Welcome to ArxOS!** 🎉 You're now ready to start building the future of building management.
