# Getting Started with ArxOS

## Welcome
ArxOS is a modern building management system built on **Clean Architecture principles** with **go-blueprint patterns** that helps you organize, visualize, and query building data with advanced spatial capabilities. This guide will help you get up and running quickly.

## Prerequisites

### System Requirements
- **Operating System**: Linux, macOS, or Windows (with WSL2)
- **Memory**: Minimum 4GB RAM (8GB recommended)
- **Storage**: 10GB free disk space
- **Docker**: Version 20.10 or later
- **Docker Compose**: Version 2.0 or later

### Optional Requirements
- **Tesseract**: For OCR capabilities in PDF import (version 4.0+)
- **Go**: For building from source (version 1.21+)

## Installation

### Quick Start with Docker (Recommended)

1. **Clone the repository**
```bash
git clone https://github.com/arxos/arxos.git
cd arxos
```

2. **Configure environment**
```bash
cp .env.example .env
# Edit .env with your preferred settings
```

3. **Start services**
```bash
docker-compose up -d
```

4. **Verify installation**
```bash
# Check services are running
docker-compose ps

# Check API health
curl http://localhost:8080/health
```

5. **Access the system**
- API: http://localhost:8080
- Documentation: http://localhost:8080/docs

### Manual Installation

#### 1. Install PostgreSQL with PostGIS

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install postgresql-14 postgresql-14-postgis-3
```

**macOS:**
```bash
brew install postgresql@14
brew install postgis
```

#### 2. Create Database

```bash
# Connect to PostgreSQL
sudo -u postgres psql

# Create database and user
CREATE USER arxos WITH PASSWORD 'secure_password';
CREATE DATABASE arxos OWNER arxos;
\c arxos
CREATE EXTENSION postgis;
CREATE EXTENSION pgcrypto;
\q
```

#### 3. Install ArxOS

```bash
# Download latest release
wget https://github.com/arxos/arxos/releases/latest/download/arxos-linux-amd64.tar.gz
tar -xzf arxos-linux-amd64.tar.gz

# Or build from source
go build -o arxos cmd/arxos/main.go
```

#### 4. Run Migrations

```bash
# Set database URL
export DATABASE_URL="postgres://arxos:secure_password@localhost:5432/arxos?sslmode=disable"

# Run migrations
./arxos migrate up
```

#### 5. Start Server

```bash
./arxos serve --port 8080
```

## First Steps

### 1. Authentication

Create your first user account:

```bash
curl -X POST http://localhost:8080/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@example.com",
    "password": "secure_password",
    "name": "Admin User"
  }'
```

Login to get access token:

```bash
curl -X POST http://localhost:8080/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@example.com",
    "password": "secure_password"
  }'

# Save the returned token for future requests
export TOKEN="your_jwt_token_here"
```

### 2. Create Your First Building

```bash
curl -X POST http://localhost:8080/api/v1/buildings \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Main Office Building",
    "address": "123 Business Ave, Tech City, TC 12345",
    "origin": {
      "latitude": 37.7749,
      "longitude": -122.4194,
      "altitude": 10.0
    }
  }'
```

### 3. Import Building Data

#### Import IFC File
```bash
curl -X POST http://localhost:8080/api/v1/import \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@/path/to/building.ifc" \
  -F "format=ifc" \
  -F "building_id=your_building_id"
```

#### Import PDF Floor Plans
```bash
curl -X POST http://localhost:8080/api/v1/import \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@/path/to/floorplans.pdf" \
  -F "format=pdf" \
  -F "building_id=your_building_id" \
  -F "options={\"ocr_enabled\":true,\"extract_diagrams\":true}"
```

#### Check Import Status
```bash
curl -X GET http://localhost:8080/api/v1/import/{job_id}/status \
  -H "Authorization: Bearer $TOKEN"
```

### 4. Query Equipment

#### Find Equipment Near a Point
```bash
curl -X POST http://localhost:8080/api/v1/spatial/proximity \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "center": {"x": 100, "y": 200, "z": 10},
    "radius": 50,
    "types": ["hvac", "electrical"]
  }'
```

#### Find K Nearest Neighbors
```bash
curl -X POST http://localhost:8080/api/v1/spatial/knn \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "center": {"x": 100, "y": 200, "z": 10},
    "k": 5,
    "types": ["sensor"]
  }'
```

#### Query by Bounding Box
```bash
curl -X POST http://localhost:8080/api/v1/spatial/bounding-box \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "min": {"x": 0, "y": 0, "z": 0},
    "max": {"x": 500, "y": 500, "z": 30}
  }'
```

### 5. Real-time Updates

Subscribe to spatial changes using Server-Sent Events:

```javascript
const eventSource = new EventSource(
  'http://localhost:8080/api/v1/spatial/stream?' +
  'center_x=100&center_y=200&center_z=10&radius=50',
  { headers: { 'Authorization': 'Bearer ' + token } }
);

eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Equipment update:', data);
};
```

## Key Concepts

### Coordinate Systems

ArxOS uses two coordinate systems:

1. **Global Coordinates (GPS)**
   - WGS84 (SRID 4326) for geographic positions
   - Used for building origins and real-world mapping
   - Format: `{latitude: 37.7749, longitude: -122.4194, altitude: 10.0}`

2. **Local Coordinates**
   - Cartesian coordinates relative to building origin
   - X: East-West (positive = East)
   - Y: North-South (positive = North)
   - Z: Vertical (positive = Up)
   - Units: Meters

### Building Hierarchy

```
Building
├── Floors
│   ├── Rooms
│   │   └── Equipment
│   └── Equipment (floor-level)
└── Equipment (building-level)
```

### Equipment Types

Standard equipment types include:
- **HVAC**: Heating, ventilation, air conditioning
- **Electrical**: Panels, transformers, generators
- **Plumbing**: Pipes, valves, pumps
- **Sensor**: Temperature, humidity, occupancy
- **Security**: Cameras, access control, alarms

### Confidence Levels

Import and position data includes confidence scores:
- **High**: Direct measurement or verified data (>90%)
- **Medium**: Calculated or inferred data (60-90%)
- **Low**: Estimated or uncertain data (<60%)

## Common Workflows

### Building Setup Workflow

1. Create building with GPS origin
2. Import IFC or PDF files
3. Review and adjust imported data
4. Add additional equipment manually
5. Configure monitoring and alerts

### Maintenance Planning Workflow

1. Query equipment by type or location
2. Filter by maintenance schedule
3. Generate work orders
4. Track completion status
5. Update equipment records

### Spatial Analysis Workflow

1. Define area of interest
2. Query equipment in area
3. Analyze spatial relationships
4. Generate reports
5. Export results

## Configuration

### Environment Variables

Key configuration options in `.env`:

```bash
# Database
DATABASE_URL=postgres://user:pass@localhost:5432/arxos
DATABASE_MAX_CONNECTIONS=100
DATABASE_MAX_IDLE=10

# Server
SERVER_PORT=8080
SERVER_HOST=0.0.0.0
JWT_SECRET=your_secret_key
JWT_EXPIRY=24h

# Spatial
SPATIAL_CACHE_SIZE_MB=100
SPATIAL_CACHE_TTL=5m
SPATIAL_BATCH_SIZE=1000

# Import
IMPORT_MAX_FILE_SIZE=100MB
IMPORT_OCR_ENABLED=true
IMPORT_PARALLEL_WORKERS=4

# Logging
LOG_LEVEL=info
LOG_FORMAT=json
```

### Performance Tuning

For large deployments (>100k equipment items):

1. **Increase cache size**
```bash
SPATIAL_CACHE_SIZE_MB=500
```

2. **Optimize PostgreSQL**
```sql
-- Increase shared buffers
ALTER SYSTEM SET shared_buffers = '2GB';
-- Increase work memory
ALTER SYSTEM SET work_mem = '64MB';
-- Reload configuration
SELECT pg_reload_conf();
```

3. **Create additional indices**
```bash
./arxos optimize-indices --analyze
```

## Troubleshooting

### Common Issues

#### Database Connection Failed
```
Error: failed to connect to database
```
**Solution**: Check DATABASE_URL and PostgreSQL is running

#### Import Takes Too Long
```
Import job timeout after 300s
```
**Solution**: Increase timeout or reduce file size

#### Spatial Query Slow
```
Query took 5000ms
```
**Solution**: Run `ANALYZE` and check indices:
```bash
./arxos db analyze
./arxos db explain-query "SELECT ..."
```

#### OCR Not Working
```
OCR engine not available
```
**Solution**: Install Tesseract:
```bash
# Ubuntu/Debian
sudo apt-get install tesseract-ocr

# macOS
brew install tesseract
```

### Getting Help

- **Documentation**: https://docs.arxos.io
- **API Reference**: https://api.arxos.io/docs
- **GitHub Issues**: https://github.com/arxos/arxos/issues
- **Community Forum**: https://forum.arxos.io
- **Email Support**: support@arxos.io

## Next Steps

- [API Reference](../api/): Complete API documentation
- [Developer Guide](../developer-guide/): Architecture and development
- [Import Guide](./import-guide.md): Detailed import instructions
- [Spatial Queries](./spatial-queries.md): Advanced spatial operations
- [Best Practices](./best-practices.md): Production deployment guide