# ArxOS Quick Start Guide

## Prerequisites

```bash
# Install Rust
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
source $HOME/.cargo/env

# Install PostgreSQL
# macOS:
brew install postgresql
brew services start postgresql

# Linux:
sudo apt-get install postgresql postgresql-contrib
```

## Setup

### 1. Clone and Build

```bash
git clone https://github.com/arx-os/arxos.git
cd arxos
cargo build --release
```

### 2. Create Database

```bash
createdb arxos
psql arxos < migrations/001_initial_schema.sql
psql arxos < migrations/002_sample_data.sql
```

### 3. Configure Database Connection

```bash
export DATABASE_URL="postgresql://localhost/arxos"
```

## Run ArxOS Terminal

```bash
cargo run
```

## Terminal Commands

### Navigation

Navigate the building like a filesystem:

```
arxos:/> cd electrical
arxos:/electrical> ls
  panels/
  circuits/
  outlets/

arxos:/electrical> cd circuits/2
arxos:/electrical/circuits/2> ls
  outlet_2A [OK]
  outlet_2B [FAILED]

arxos:/electrical/circuits/2> pwd
/electrical/circuits/2
```

### Inspection

```
arxos:/> inspect /electrical/circuits/2/outlet_2B
╔════════════════════════════════════════════╗
║ Object: outlet_2B                          ║
╚════════════════════════════════════════════╝

Path:     /electrical/circuits/2/outlet_2B
Type:     outlet
Status:   failed
Health:   25

⚠ NEEDS REPAIR

Properties:
  voltage: 120
```

### Queries

Find objects using SQL:

```sql
-- Find objects needing repair
SELECT * FROM objects WHERE needs_repair = true

-- Find all outlets
SELECT * FROM objects WHERE type = 'outlet'

-- Find objects on floor 2
SELECT * FROM objects WHERE path LIKE '/spaces/floor_2/%'
```

### Tracing Connections

```
arxos:/> trace outlet_2B upstream
Tracing upstream from outlet_2B:
  → circuit_2
    → panel_1
      → main_breaker
```

### Finding Nearby Objects

```
arxos:/electrical/outlets> near 5
Objects within 5m:
  switch_2A - 1.2m away
  outlet_2C - 2.4m away
  thermostat_1 - 4.5m away
```

## Example Session

```bash
# Start terminal
$ cargo run

# Navigate to electrical systems
arxos:/> cd electrical/circuits/2
arxos:/electrical/circuits/2> ls
  outlet_2A [OK]
  outlet_2B [FAILED]

# Check failed outlet
arxos:/electrical/circuits/2> inspect outlet_2B
[Shows outlet details with failed status]

# Find all maintenance issues
arxos:/> SELECT * FROM objects WHERE needs_repair = true
Found 1 object:
  /electrical/circuits/2/outlet_2B - outlet (failed)

# Exit
arxos:/> exit
Goodbye!
```

## Building Structure

ArxOS organizes buildings as hierarchical paths:

```
/
├── electrical/
│   ├── panels/
│   ├── circuits/
│   └── outlets/
├── plumbing/
│   ├── supply/
│   └── drainage/
├── hvac/
│   ├── equipment/
│   └── zones/
└── spaces/
    ├── floor_1/
    ├── floor_2/
    └── floor_3/
```

## Common Queries

```sql
-- Maintenance issues
SELECT * FROM objects WHERE needs_repair = true

-- Equipment by type
SELECT * FROM objects WHERE type = 'thermostat'

-- Failed equipment
SELECT * FROM objects WHERE status = 'failed'

-- Objects in specific area
SELECT * FROM objects WHERE path LIKE '/electrical/%'
```

## Next Steps

- Explore the building with `cd` and `ls`
- Query objects with `SELECT` statements
- Trace connections with `trace`
- Read [TERMINAL.md](docs/TERMINAL.md) for full command reference

## Troubleshooting

### Database Connection Failed
```bash
# Verify PostgreSQL is running
psql -l

# Set DATABASE_URL
export DATABASE_URL="postgresql://localhost/arxos"
```

### No Buildings Found
```bash
# Load sample data
psql arxos < migrations/002_sample_data.sql
```