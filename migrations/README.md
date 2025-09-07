# Database Migrations

PostgreSQL migrations for ArxOS.

## Running Migrations

```bash
# Apply all migrations
psql -d arxos < migrations/001_initial_schema.sql
psql -d arxos < migrations/002_sample_data.sql

# Or using sqlx-cli
sqlx migrate run
```

## Migration Files

- `001_initial_schema.sql` - Core database schema with buildings and building_objects tables
- `002_sample_data.sql` - Sample building with hierarchical object structure

## Schema Overview

The database uses a hierarchical path structure similar to a filesystem:

```
/electrical/circuits/2/outlet_2B
/plumbing/supply/hot/valve_3
/hvac/zones/north/thermostat_1
/spaces/floor_2/room_205
```

Objects are stored with:
- Hierarchical paths for navigation
- Physical location coordinates
- Status and health tracking
- Flexible JSON properties
- Parent-child relationships