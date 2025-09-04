# Arxos: Bidirectional Spatial Intelligence System

> Note: Arxos is RF-only and terminal-first. No web servers or WASM runtime are part of the core runtime; all interaction happens locally via the terminal and RF mesh.

## Executive Summary

Arxos transforms consumer iPhones into professional building intelligence scanners through a bidirectional translation system between augmented reality and compressed spatial data. The system enables crowd-sourced building mapping where field workers earn rewards for accurate technical markups, creating comprehensive building intelligence that serves facility management, emergency response, and compliance automation.
## Canonical Specifications

- ArxObject (13-byte) spec: `../technical/arxobject_specification.md`
- Mesh protocol deep dive: `../technical/mesh_architecture.md`
- Terminal API (commands): `../technical/TERMINAL_API.md`
- Protocols index: `../12-protocols/MESH_PROTOCOL.md`


### The Core Innovation

```
Reality ←→ AR Interface ←→ ArxObject ←→ SQL/ASCII ←→ Terminal Queries ←→ Reality
```

This circular data flow maintains semantic meaning while achieving 10,000:1 compression ratios, enabling building intelligence to transmit over bandwidth-limited networks and store on resource-constrained devices.

## System Architecture

### Three-Layer Technology Stack

```
┌─────────────────────────────────────────────┐
│           Input Layer (AR/LiDAR)            │
│  • iPhone LiDAR for structure capture       │
│  • AR markup for object placement           │
│  • Snapchat-style interface                 │
└────────────────┬─────────────────────────────┘
                 │
┌────────────────▼─────────────────────────────┐
│       Processing Layer (Pure Rust)          │
│  • Semantic compression engine              │
│  • Bidirectional translation                │
│  • BILT token calculation                   │
└────────────────┬─────────────────────────────┘
                 │
┌────────────────▼─────────────────────────────┐
│         Storage Layer (SQLite)              │
│  • Local-first architecture                 │
│  • R-tree spatial indexing                  │
│  • Offline operation                        │
└──────────────────────────────────────────────┘
```

## Key Features

### 1. Crowd-Sourced Building Intelligence
- Field workers mark equipment during routine tasks
- AR interface ensures accurate 3D positioning
- BILT tokens reward quality contributions
- Multiple workers verify and improve data

### 2. Professional-Grade Accuracy
- LiDAR captures structure automatically (walls, doors, rooms)
- Human experts add technical details (circuit numbers, specifications)
- Verification system ensures data quality
- Audit trails maintain accountability

### 3. Universal Deployment
- Single Rust core, with native UIs (SwiftUI/Compose) for mobile
- Runs on local devices; no web runtime or WASM
- No platform-specific code required
- 3MB binary serves all platforms

### 4. Offline-First Operation
- SQLite database on each device
- Works without internet connection
- Syncs when connectivity available
- No server dependencies

## Implementation Targets

### Hillsborough County Schools Pilot
- **Scale**: 300 schools, 500 buildings
- **Users**: Maintenance staff, facilities managers
- **Timeline**: 12-month rollout
- **Value**: Automated compliance, emergency response, maintenance optimization

### Performance Metrics
- **Compression**: 500MB → 50KB (10,000:1 ratio)
- **Query Speed**: <50ms for spatial queries
- **Storage**: ~50KB per building
- **Training**: 2 hours per worker

## Documentation Structure

### Core Documentation
1. **[00-overview](.)** - Executive summary and quick start
2. **[01-vision](../01-vision/)** - Problem, solution, and impact
3. **[02-arxobject](../02-arxobject/)** - Data model and compression
4. **[03-architecture](../03-architecture/)** - Technical architecture
5. **[04-sql-database](../04-sql-database/)** - SQLite spatial database
6. **[05-holographic](../05-holographic/)** - Progressive/visionary compression ideas
7. **[06-implementation](../06-implementation/)** - Development guide and status
8. **[07-ios-integration](../07-ios-integration/)** - iOS terminal and capture notes
9. **[08-bilt-economics](../08-bilt-economics/)** - Token reward system and economics
10. **[09-deployment](../09-deployment/)** - Deployment guides (RF-only)
11. **[12-protocols](../12-protocols/)** - Protocol specifications
12. **[11-case-studies](../11-case-studies/)** - Hillsborough County pilot

### Quick Start Guides
- [Developer Quick Start](quickstart-developer.md)
- Field Worker Guide (coming soon)
- Building Owner Guide (coming soon)
- Emergency Responder Access (coming soon)

## Quick Start

### For Developers
```bash
# Clone repository
git clone https://github.com/arxos/arxos.git
cd arxos

# Install Rust (use offline installer if air-gapped)
# See https://rustup.rs for options

# Build core binaries (RF-only)
cargo build --release -p arxos-service -p arxos-terminal

# Run the local RF service (serial/BLE configured via CLI flags or config)
./target/release/arxos-service --help

# Launch the terminal client
./target/release/arxos --help
```

### For Field Workers
1. Download Arxos app from TestFlight
2. Complete 2-hour training module
3. Scan first room with LiDAR
4. Mark equipment with AR interface
5. Earn BILT tokens for contributions

### For Building Owners
1. Register building in system
2. Assign field workers
3. Monitor mapping progress
4. Access compliance reports
5. Enable emergency responder access

## Key Metrics

### Compression Efficiency
| Data Type | Original | Compressed | Ratio |
|-----------|----------|------------|-------|
| Room scan | 50MB | 5KB | 10,000:1 |
| Building | 500MB | 50KB | 10,000:1 |
| District | 150GB | 15MB | 10,000:1 |

### Economic Model
| Action | BILT Reward | USD Value |
|--------|------------|-----------|
| Basic markup | 10 points | $0.10 |
| Technical details | 20 points | $0.20 |
| Safety equipment | 50 points | $0.50 |
| Full room | 100 points | $1.00 |

### Development Timeline
| Phase | Duration | Deliverable |
|-------|----------|-------------|
| MVP | 3 months | Single school pilot |
| Rollout | 5 months | 50 schools |
| Full deployment | 4 months | 300 schools |

## Success Criteria

### Technical Success
- ✓ 10,000:1 compression achieved
- ✓ <50ms query response time
- ✓ Offline operation capability
- ✓ Native local deployment

### Business Success
- ✓ 2-hour training sufficient
- ✓ $50/building mapping cost
- ✓ 90% accuracy on first pass
- ✓ ROI within 6 months

### User Success
- ✓ Workers earn $20-50/day in BILT
- ✓ Owners save 30% on compliance
- ✓ Emergency response time -5 minutes
- ✓ Maintenance costs -20%

## Next Steps

1. **Review** [Vision Documentation](../01-vision/)
2. **Understand** [Technical Architecture](../03-architecture/)
3. **Learn** [ArxObject Model](../02-arxobject/)
4. **Implement** [Development Guide](../06-implementation/)
5. **Deploy** [Production Setup](../10-deployment/)

---

*"Snapchat for Buildings: Making spatial intelligence as easy as social media"*