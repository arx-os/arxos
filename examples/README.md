# ArxOS Examples

Example demonstrations of ArxOS concepts. These are documentation examples that show the intended usage patterns.

## Available Examples

### navigate.rs
Demonstrates terminal navigation concepts:
- Loading buildings from database
- Navigating filesystem-like paths
- Using cd, ls, inspect commands

### query.rs  
Demonstrates SQL query patterns:
- SELECT queries on building objects
- Filtering by type, status, path
- Finding maintenance issues

### load_building.rs
Demonstrates database integration:
- Connecting to PostgreSQL
- Loading building objects
- Finding objects by path

## Run Examples

```bash
# Run navigation demo
cargo run --example navigate

# Run query demo
cargo run --example query

# Run loader demo
cargo run --example load_building
```

## Example Queries

```sql
-- Find all outlets
SELECT * FROM objects WHERE type = 'outlet'

-- Find maintenance issues
SELECT * FROM objects WHERE needs_repair = true

-- Find objects on circuit 2
SELECT * FROM objects WHERE path LIKE '/electrical/circuits/2/%'

-- Find failed equipment
SELECT * FROM objects WHERE status = 'failed'
```

## Example Paths

```
/electrical/circuits/2/outlet_2B
/electrical/panels/panel_1
/plumbing/supply/hot/valve_3
/hvac/zones/north/thermostat_1
/spaces/floor_2/room_205
```

## Terminal Commands

```bash
# Navigate to electrical systems
cd /electrical
ls
cd circuits/2
inspect outlet_2B

# Trace connections
trace outlet_2B upstream

# Find nearby objects
near 5

# Query from terminal
SELECT * FROM objects WHERE type = 'outlet'
```