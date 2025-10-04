# ArxOS Quick Start Guide

Get up and running with ArxOS in under 5 minutes!

## Prerequisites

- **Go 1.21+** - [Download](https://golang.org/dl/)
- **Docker & Docker Compose** - [Download](https://www.docker.com/products/docker-desktop)
- **Git** - [Download](https://git-scm.com/downloads)
- **Make** - Usually pre-installed on macOS/Linux

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

### 2. Install Dependencies

```bash
# Download Go modules
go mod download

# Run database migrations
go run cmd/arx/main.go migrate up

# Or use the Makefile for setup
make setup
```

### 3. Build and Run

```bash
# Build the application
make build

# Run the CLI
./bin/arx version

# Start the API server
./bin/arx serve
```

### 4. Verify Installation

```bash
# Check system status
./bin/arx status

# List available commands
./bin/arx help

# Test API endpoint
curl http://localhost:8080/health

# Check mobile app (if needed)
cd mobile && npm install && npm start
```

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

# Import from PDF
./bin/arx pdf import /path/to/floorplan.pdf
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

**Port already in use:**
```bash
# Check what's using port 8080
lsof -i :8080

# Kill the process
kill -9 <PID>

# Or use a different port
export ARXOS_API_PORT=8081
./bin/arx serve
```

**Database connection failed:**
```bash
# Check if PostGIS is running
docker-compose ps

# Restart PostGIS
docker-compose restart postgis

# Check database logs
docker-compose logs postgis
```

**Build failures:**
```bash
# Clean and rebuild
make clean
go mod tidy
make build

# Or use the complete cleanup
make clean-all
make build
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
