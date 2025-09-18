# ArxOS Quick Start Guide

## Overview

ArxOS is a Building Operating System that provides:
- **PostGIS Spatial Database**: Millimeter-precision spatial storage
- **IFC Import/Export**: Professional BIM integration
- **Multi-Format Export**: BIM, CSV, JSON output formats
- **Daemon Automation**: File watching and auto-processing
- **Git-like Version Control**: Track building changes over time
- **Docker Deployment**: Production-ready containerization

## Prerequisites

- Docker & Docker Compose
- Go 1.21+ (for building from source)
- 4GB RAM minimum
- 10GB disk space

## Installation

### Option 1: Docker (Recommended)

```bash
# Clone the repository
git clone https://github.com/arx-os/arxos
cd arxos

# Start the stack
docker-compose up -d

# Verify installation
docker-compose ps
```

### Option 2: Build from Source

```bash
# Clone the repository
git clone https://github.com/arx-os/arxos
cd arxos

# Build the CLI
go build -o arx ./cmd/arx

# Start PostGIS database
docker-compose up -d postgis

# Verify connection
./arx query --health
```

## Quick Start Tutorial

### 1. Start the System

```bash
# Start PostGIS and API server
docker-compose up -d

# Check system health
./arx query --health
```

### 2. Import an IFC File

```bash
# Import a building from IFC
./arx import ifc path/to/building.ifc --building-id ARXOS-001

# Verify import
./arx query buildings
```

### 3. Query Building Data

```bash
# List all floors
./arx query floors --building ARXOS-001

# Find equipment on floor 2
./arx query equipment --floor 2

# Spatial query - find equipment within 5m of a point
./arx query equipment --near "1000,2000,0" --radius 5000

# Get room information
./arx query rooms --building ARXOS-001 --with-geometry
```

### 4. Export Building Data

```bash
# Export to human-readable BIM format
./arx export bim --building ARXOS-001 --output building.bim.txt

# Export equipment list to CSV
./arx export csv --equipment --output equipment.csv

# Export complete building as JSON
./arx export json --building ARXOS-001 --output building.json
```

### 5. Start the Daemon (Auto-Import)

```bash
# Start daemon to watch for IFC files
./arx daemon start --watch /path/to/ifc/folder

# Check daemon status
./arx daemon status

# Stop daemon
./arx daemon stop
```

## Building Data Model

ArxOS uses a hierarchical spatial model:

```
Building (ARXOS-001)
├── Floor 0 (Ground)
│   ├── Room 101 (Lobby)
│   │   ├── Equipment: Reception Desk
│   │   └── Equipment: Info Display
│   ├── Room 102 (Security)
│   │   └── Equipment: Security Console
│   └── Room 103 (Mechanical)
│       ├── Equipment: HVAC-001
│       └── Equipment: Electrical Panel
├── Floor 1
│   ├── Room 201 (Conference)
│   │   ├── Equipment: Projector
│   │   └── Equipment: Conference Phone
│   └── Room 202 (Open Office)
│       ├── Equipment: Workstations (x20)
│       └── Equipment: Printers (x2)
└── Metadata
    ├── Version: 1.0.0
    ├── Last Modified: 2024-01-15
    └── Total Area: 5000 m²
```

## Spatial Queries with PostGIS

ArxOS leverages PostGIS for advanced spatial queries:

```bash
# Find all equipment in a bounding box
./arx query equipment --bbox "0,0,10000,10000"

# Find rooms containing a specific point
./arx query rooms --contains-point "5000,3000"

# Find nearest equipment to a location
./arx query equipment --nearest "2000,2000,0" --limit 5

# Calculate distances between equipment
./arx query distances --from HVAC-001 --to-type electrical
```

## BIM Text Format

ArxOS uses a human-readable BIM format:

```
BUILDING: ARXOS-001
NAME: Tech Office Building
ADDRESS: 123 Tech Street, San Francisco, CA

FLOOR: 0
  NAME: Ground Floor
  ELEVATION: 0mm

  ROOM: 101
    NAME: Main Lobby
    TYPE: PUBLIC
    AREA: 150m²

    EQUIPMENT: RECEP-01
      NAME: Reception Desk
      TYPE: FURNITURE
      LOCATION: (5000, 3000, 0)
      STATUS: OPERATIONAL

FLOOR: 1
  NAME: First Floor
  ELEVATION: 3500mm

  ROOM: 201
    NAME: Conference Room A
    TYPE: MEETING
    AREA: 50m²
```

## Configuration

### Environment Variables

```bash
# Database
POSTGIS_HOST=localhost
POSTGIS_PORT=5432
POSTGRES_DB=arxos
POSTGRES_USER=arxos
POSTGRES_PASSWORD=secure_password

# Application
ARX_LOG_LEVEL=info
API_PORT=8080

# Daemon
DAEMON_WATCH_PATHS=/data/ifc
DAEMON_AUTO_IMPORT=true
DAEMON_AUTO_EXPORT=true
```

### Configuration Files

- `configs/development.yml` - Development settings
- `configs/production.yml` - Production settings
- `configs/daemon.yaml` - Daemon configuration

## API Endpoints

ArxOS provides a REST API on port 8080:

```bash
# Health check
curl http://localhost:8080/health

# Get all buildings
curl http://localhost:8080/api/v1/buildings

# Get specific building
curl http://localhost:8080/api/v1/buildings/ARXOS-001

# Query equipment
curl http://localhost:8080/api/v1/equipment?floor=2

# Spatial query
curl http://localhost:8080/api/v1/spatial/nearest?point=1000,2000,0&radius=5000
```

## Docker Deployment

### Development

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Production

```bash
# Deploy production stack
docker-compose -f docker/docker-compose.base.yml \
               -f docker/docker-compose.prod.yml up -d

# With monitoring
docker-compose -f docker/docker-compose.base.yml \
               -f docker/docker-compose.prod.yml \
               -f docker/docker-compose.monitoring.yml up -d
```

## Troubleshooting

### Database Connection Issues

```bash
# Check PostGIS is running
docker ps | grep postgis

# Test connection
docker exec -it arxos-postgis psql -U arxos -d arxos -c "SELECT PostGIS_Version();"

# View PostGIS logs
docker logs arxos-postgis
```

### Import Issues

```bash
# Validate IFC file
./arx validate ifc path/to/file.ifc

# Import with verbose logging
ARX_LOG_LEVEL=debug ./arx import ifc file.ifc --building-id ARXOS-001

# Check import history
./arx query imports --recent
```

### Performance

```bash
# Check database statistics
./arx admin db-stats

# Optimize spatial indices
./arx admin optimize-spatial

# Monitor resource usage
docker stats arxos-postgis arxos-api
```

## Best Practices

1. **Building IDs**: Use consistent naming: `ARXOS-{REGION}-{CITY}-{NUMBER}`
2. **IFC Files**: Validate before import using `./arx validate ifc`
3. **Spatial Precision**: Store coordinates in millimeters for accuracy
4. **Version Control**: Commit building changes with meaningful messages
5. **Backups**: Regular PostGIS backups using `pg_dump`

## Examples

### Complete Workflow

```bash
# 1. Start system
docker-compose up -d

# 2. Import building
./arx import ifc office_building.ifc --building-id ARXOS-NA-NYC-001

# 3. Query data
./arx query equipment --building ARXOS-NA-NYC-001 --floor 5

# 4. Export for reporting
./arx export csv --equipment --output report.csv

# 5. Start daemon for automation
./arx daemon start --watch /shared/ifc

# 6. Monitor changes
./arx repo log --building ARXOS-NA-NYC-001
```

## Next Steps

- Review the [full documentation](/docs)
- Try the [interactive demo](./demo.sh)
- Explore the [API documentation](http://localhost:8080/swagger)
- Join the [ArxOS community](https://github.com/arx-os/arxos/discussions)

## Support

- GitHub Issues: https://github.com/arx-os/arxos/issues
- Documentation: https://arxos.io/docs
- Discord: https://discord.gg/arxos