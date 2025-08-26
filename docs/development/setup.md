# Arxos Development Setup

This guide covers setting up the Arxos development environment for the new C/Go/AR/CLI architecture.

## Prerequisites

### System Requirements
- **Operating System**: Windows 10/11, macOS 10.15+, or Linux (Ubuntu 20.04+)
- **Memory**: 8GB RAM minimum, 16GB recommended
- **Storage**: 10GB free space for development environment
- **Terminal**: PowerShell (Windows), Terminal.app (macOS), or GNOME Terminal (Linux)

### Required Software
- **Go**: Version 1.21+ ([Download](https://golang.org/dl/))
- **GCC/Clang**: C compiler for the core engines
  - **Windows**: MinGW-w64 or Visual Studio Build Tools
  - **macOS**: Xcode Command Line Tools
  - **Linux**: `build-essential` package
- **Git**: Version 2.30+ ([Download](https://git-scm.com/))
- **PostgreSQL**: Version 14+ with PostGIS extension
- **Node.js**: Version 18+ (for CLI development tools)

## Environment Setup

### 1. Clone the Repository
```bash
git clone https://github.com/arxos/arxos.git
cd arxos
```

### 2. Install Go Dependencies
```bash
cd core
go mod download
go mod tidy
```

### 3. Build C Core Engines
```bash
cd c
make clean
make all
```

**Note**: If you encounter build issues, ensure your C compiler is properly configured and accessible from your PATH.

### 4. Set Environment Variables
Create a `.env` file in the `core/` directory:

```bash
# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=arxos_dev
DB_USER=arxos_user
DB_PASSWORD=your_password

# Development Settings
ENV=development
LOG_LEVEL=debug
CORE_PATH=./c
```

### 5. Database Setup
```sql
-- Create database and user
CREATE DATABASE arxos_dev;
CREATE USER arxos_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE arxos_dev TO arxos_user;

-- Enable PostGIS extension
\c arxos_dev
CREATE EXTENSION postgis;
```

## Development Workflow

### 1. Core Development (C)
- **Location**: `core/c/`
- **Build**: `make all` or `make debug`
- **Test**: `make test`
- **Clean**: `make clean`

### 2. CLI Development (Go)
- **Location**: `core/cmd/`
- **Build**: `go build ./...`
- **Test**: `go test ./...`
- **Run**: `go run main.go`

### 3. Testing
```bash
# Run all tests
go test ./...

# Run specific test suite
go test ./internal/arxobject

# Run with coverage
go test -cover ./...

# Run C tests
cd c && make test
```

### 4. Performance Testing
```bash
# Run performance benchmarks
go test -bench=. ./...

# Run specific benchmark
go test -bench=BenchmarkArxObjectCreation ./internal/arxobject
```

## IDE Configuration

### VS Code / Cursor
Install these extensions:
- **Go**: Official Go extension
- **C/C++**: Microsoft C/C++ extension
- **PostgreSQL**: PostgreSQL extension
- **GitLens**: Git integration

### GoLand / IntelliJ
- Enable Go module support
- Configure C/C++ toolchain
- Set up database connections

## Troubleshooting

### Common Issues

#### C Build Failures
```bash
# Check compiler version
gcc --version
clang --version

# Verify PATH includes compiler
echo $PATH

# On Windows, ensure MinGW is in PATH
where gcc
```

#### Go Module Issues
```bash
# Clear module cache
go clean -modcache

# Verify module dependencies
go mod verify

# Update dependencies
go get -u ./...
```

#### Database Connection Issues
```bash
# Test PostgreSQL connection
psql -h localhost -U arxos_user -d arxos_dev

# Check PostGIS extension
\dx postgis
```

### Performance Issues
- Ensure CGO is enabled: `export CGO_ENABLED=1`
- Check C compiler optimization flags in Makefile
- Verify Go build tags are correct

## Next Steps

After setup, proceed to:
1. [Development Guide](guide.md) - Core development concepts
2. [ArxObject Development](arxobject-dev.md) - ArxObject system development
3. [CLI Development](cli-dev.md) - Command-line interface development
4. [Testing Guide](../testing/README.md) - Testing strategies and examples

## Support

For setup issues:
1. Check the [troubleshooting section](#troubleshooting)
2. Review [GitHub Issues](https://github.com/arxos/arxos/issues)
3. Consult the [Architecture Documentation](../architecture/README.md)
