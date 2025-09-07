# ArxOS Documentation

## Overview

ArxOS transforms buildings into queryable databases. Every outlet, light, valve, and piece of equipment becomes part of a hierarchical data structure that can be queried like a database.

## Available Documentation

- [TERMINAL.md](TERMINAL.md) - Terminal interface command reference
- [../ARCHITECTURE.md](../ARCHITECTURE.md) - System architecture and design

## Key Concepts

### Buildings as File Systems

```
/building_42/
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

### Navigation Commands

- `CD` - Change directory
- `LS` - List contents
- `LOOK` - Describe location
- `INSPECT` - Show object details
- `PWD` - Print working directory

### Query Examples

```sql
-- Find maintenance issues
SELECT * FROM objects WHERE needs_repair = true

-- Find objects by type
SELECT * FROM objects WHERE type = 'outlet'

-- Trace connections
TRACE outlet_2B_north UPSTREAM
```

## Archive

Legacy documentation from earlier project phases (RF mesh, ArxObjects, etc.) is preserved in [archive/](archive/) for historical reference.