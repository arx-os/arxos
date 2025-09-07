# ArxOS - Buildings as Queryable Databases

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Rust](https://img.shields.io/badge/rust-1.75%2B-orange.svg)](https://www.rust-lang.org)
[![API](https://img.shields.io/badge/API-REST%20%2B%20SSE-green.svg)](docs/api/README.md)

ArxOS transforms physical buildings into queryable, real-time databases with tokenized economic incentives. Navigate through building systems like a file system, query equipment with SQL, trace connections through infrastructure, and participate in the building data economy through the BILT token system.

## Quick Start

### Prerequisites

```bash
# Install Rust
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# Install PostgreSQL
brew install postgresql  # macOS
brew services start postgresql
```

### Setup

```bash
# Clone repository
git clone https://github.com/arx-os/arxos.git
cd arxos

# Create database and run all migrations
createdb arxos
for file in migrations/*.sql; do
    psql arxos < "$file"
done

# Build
cargo build --release

# Run API server (recommended)
cargo run -- --api --port 3000

# Or run terminal interface
cargo run -- --building <building-id>
```

## Terminal Interface

Navigate buildings like a filesystem:

```
arxos:/> cd electrical/circuits/2
arxos:/electrical/circuits/2> ls
  outlet_2A [OK]
  outlet_2B [FAILED]

arxos:/electrical/circuits/2> inspect outlet_2B
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

## Core Commands

### Navigation
- `cd <path>` - Change directory
- `ls [path]` - List contents
- `pwd` - Print working directory
- `look` - Describe current location

### Inspection
- `inspect <object>` - Show object details
- `trace <object> upstream` - Trace connections
- `near [radius]` - Find nearby objects

### Queries
```sql
SELECT * FROM objects WHERE type = 'outlet'
SELECT * FROM objects WHERE needs_repair = true
SELECT * FROM objects WHERE path LIKE '/electrical/%'
```

## Building Structure

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

## 🏗️ Key Features

### Core Capabilities
- **SQL Query Engine** - Query buildings with SQL syntax
- **Real-time Events** - Server-Sent Events for live updates
- **Webhook System** - Push notifications to external systems
- **Bulk Operations** - Efficient batch processing
- **Audit History** - Complete change tracking

### BILT Rating System (0z-1A)
- **Algorithmic Valuation** - Data completeness determines rating
- **Real-time Updates** - Every contribution affects rating
- **Market Integration** - Ratings drive token value

### Token Economics
- **Contribution Rewards** - Earn tokens for data contributions
- **Reputation System** - Build trust through quality work
- **Market Feeds** - Real-time pricing and valuations

## Architecture

ArxOS implements a sophisticated event-driven architecture:

- **REST API** - Full CRUD operations (src/api/)
- **Event System** - PostgreSQL LISTEN/NOTIFY (src/events/)
- **Rating Engine** - BILT rating calculations (src/rating/)
- **Market Layer** - Token economics (src/market/)
- **Terminal Interface** - CLI navigation (src/terminal.rs)
- **PostgreSQL** - Persistent storage with triggers

## 📡 API Overview

### REST Endpoints
```bash
# Building Objects
GET    /api/objects              # List objects
POST   /api/objects              # Create object
PATCH  /api/objects/{id}         # Update object
DELETE /api/objects/{id}         # Delete object

# BILT Ratings
GET    /api/buildings/{id}/rating           # Current rating
GET    /api/buildings/{id}/rating/breakdown # Component scores

# Market & Tokens
POST   /api/contributions                   # Record contribution
GET    /api/contributors/{id}/profile       # Reputation profile
GET    /api/tokens/{building_id}           # Token information

# Real-time Events
GET    /api/events                          # Server-Sent Events stream
```

### Event Types
- `object.created`, `object.updated`, `object.deleted`
- `bilt.rating.changed`, `bilt.rating.calculated`
- `state.changed`, `alert.raised`

## 💰 Building Whisperer Integration

ArxOS implements the "Building Whisperer" vision:

1. **Every contribution creates value** - Worker data becomes tokens
2. **Instant valuation** - Contributions affect ratings immediately
3. **Market signals** - Rating changes trigger trading opportunities
4. **Information asymmetry** - Real-time data provides advantages

## Documentation

- [API Documentation](docs/api/README.md)
- [Quick Start Guide](QUICK_START.md)
- [Terminal Commands](docs/TERMINAL.md)
- [Architecture](ARCHITECTURE.md)
- [Deployment Guide](docs/deployment/README.md)
- [BILT Rating System](docs/bilt-rating.md)
- [Token Economics](docs/token-economics.md)

## License

MIT