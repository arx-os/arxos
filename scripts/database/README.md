# Arxos Database Setup

PostgreSQL with PostGIS for spatial building data management.

## Overview

Arxos uses **PostgreSQL 15 with PostGIS 3.3** as its primary database, providing:
- **3D Spatial Support** - Full 3D geometry with Z-axis coordinates
- **Nanometer Precision** - Ultra-precise measurements for building elements
- **Geographic Coordinates** - SRID 4326 (WGS84) for real-world positioning
- **Spatial Indexing** - GIST indexes for fast spatial queries

## Quick Start

### 1. Setup Development Database

```bash
# Start PostgreSQL with PostGIS
cd /Users/joelpate/repos/arxos/core
make db-setup

# Verify setup
../scripts/database/verify-postgis.sh

# Run migrations
make migrate
```

### 2. Setup Test Database

```bash
# Start test PostgreSQL (port 5433)
make db-test-setup

# Run tests with PostgreSQL
make test-with-db
```

## Database Architecture

### Spatial Features Used

- **PostGIS Geometry Types**:
  - `GEOMETRY(PointZ, 4326)` - 3D points for devices/sensors
  - `GEOMETRY(Polygon, 4326)` - Building/room boundaries  
  - `GEOMETRY(LineString, 4326)` - Walls, pipes, ducts

- **Spatial Functions**:
  - `ST_Distance()` - Distance calculations
  - `ST_Within()` - Containment queries
  - `ST_DWithin()` - Proximity searches
  - `ST_MakePoint()` - Coordinate creation

- **Precision Levels**:
  - Nanometer precision for internal calculations
  - Automatic conversion to/from millimeters for display
  - Z-axis support for multi-floor buildings

### Key Tables

```sql
-- ArxObjects with spatial data
CREATE TABLE arx_objects (
    id UUID PRIMARY KEY,
    building_id UUID NOT NULL,
    
    -- Nanometer precision coordinates
    x_nano BIGINT NOT NULL,
    y_nano BIGINT NOT NULL,
    z_nano BIGINT NOT NULL,
    
    -- PostGIS geometry (optional)
    geom GEOMETRY(PointZ, 4326),
    
    -- Automatic spatial triggers
    -- Updates geom when x_nano/y_nano/z_nano change
);

-- Spatial indexes for performance
CREATE INDEX idx_arx_objects_geom ON arx_objects USING GIST(geom);
CREATE INDEX idx_arx_objects_building ON arx_objects(building_id);
```

## Docker Setup

### Development Environment

```yaml
# docker-compose.test.yml
services:
  postgres:
    image: postgis/postgis:15-3.3-alpine
    ports:
      - "5432:5432"
    environment:
      POSTGRES_DB: arxos
      POSTGRES_USER: arxos
      POSTGRES_PASSWORD: arxos_dev
```

### Test Environment

```yaml
services:
  postgres-test:
    image: postgis/postgis:15-3.3-alpine
    ports:
      - "5433:5432"  # Different port
    environment:
      POSTGRES_DB: arxos_test
      POSTGRES_USER: arxos_test
      POSTGRES_PASSWORD: arxos_test
```

## Migration System

### Running Migrations

```bash
# Forward migration
make migrate

# Rollback last migration
make migrate-down

# Create new migration
migrate create -ext sql -dir migrations <name>
```

### Migration History

22 migrations providing:
1. Basic BIM schema
2. Asset inventory tables
3. CMMS integration
4. PostGIS spatial columns
5. Nanometer precision upgrade
6. Performance optimizations

## Connection Details

### Development
```
Host: localhost
Port: 5432
Database: arxos
User: arxos
Password: arxos_dev
SSL: disabled
```

### Testing
```
Host: localhost
Port: 5433
Database: arxos_test
User: arxos_test
Password: arxos_test
SSL: disabled
```

## Verification

### Check PostGIS Installation

```bash
# Run verification script
./scripts/database/verify-postgis.sh

# Manual check
psql -h localhost -U arxos -d arxos -c "SELECT PostGIS_version();"
```

### Test Spatial Queries

```sql
-- Find all objects within 10 meters
SELECT * FROM arx_objects
WHERE ST_DWithin(
    geom,
    ST_SetSRID(ST_MakePoint(-73.935242, 40.730610, 0), 4326),
    10
);

-- Calculate distances between objects
SELECT 
    a.id as obj1,
    b.id as obj2,
    ST_Distance(a.geom, b.geom) as distance_meters
FROM arx_objects a, arx_objects b
WHERE a.id != b.id
AND a.building_id = b.building_id;
```

## Troubleshooting

### PostGIS Not Found

```bash
# Connect to database
docker exec -it arxos-postgres psql -U arxos -d arxos

# Enable extension
CREATE EXTENSION IF NOT EXISTS postgis;
```

### Migration Failures

```bash
# Check migration status
migrate -path migrations -database $DATABASE_URL version

# Force version (use carefully)
migrate -path migrations -database $DATABASE_URL force <version>
```

### Connection Issues

```bash
# Check if PostgreSQL is running
docker ps | grep postgres

# Test connection
pg_isready -h localhost -p 5432

# Check logs
docker logs arxos-postgres
```

## Performance Tips

1. **Use Spatial Indexes** - Always create GIST indexes on geometry columns
2. **Batch Inserts** - Use COPY or batch INSERT for large datasets
3. **Connection Pooling** - Configured in db.go (25 max connections)
4. **Vacuum Regularly** - PostgreSQL auto-vacuum is enabled

## Security Notes

- Change default passwords in production
- Use SSL connections in production
- Implement row-level security for multi-tenant scenarios
- Regular backups with pg_dump

## Why PostgreSQL/PostGIS Only?

Previously, SQLite was used for lightweight testing but has been removed because:
- **No Spatial Support** - SQLite lacks PostGIS capabilities
- **Testing Accuracy** - Tests should run against production-like database
- **Maintenance Overhead** - Two database systems increased complexity
- **Feature Parity** - All environments now have full spatial capabilities

## Resources

- [PostGIS Documentation](https://postgis.net/documentation/)
- [PostgreSQL 15 Docs](https://www.postgresql.org/docs/15/)
- [Spatial SQL Tutorial](https://postgis.net/workshops/postgis-intro/)