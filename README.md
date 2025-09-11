# ArxOS - Building Operating System

ArxOS treats buildings as queryable, version-controlled databases. This Go implementation provides a terminal-based interface for managing floor plans and equipment status tracking.

## Vision

ArxOS is evolving into a comprehensive platform that treats buildings and physical assets as living, collaborative repositories - like GitHub for the physical world.

**Core Principles:**
- **Queryable** - "Show me all failed equipment on floor 2"
- **Version Controlled** - Track all changes with Git-like workflows
- **Collaborative** - Multiple technicians, contractors, and owners working together
- **Intelligent** - AI-assisted documentation and predictive maintenance
- **Universal** - From commercial buildings to homes to asset tracking

📚 **[Read the Full Platform Vision](docs/VISION.md)**

## Current Status

**Phase 1 Implementation** ✅
- Terminal-based floor plan viewer
- PDF import with universal parser
- Manual equipment entry commands
- Equipment status tracking  
- ASCII art visualization
- PDF export with inspection reports
- Git integration for version control

**Phase 2 Database & Intelligence Layer** ✅ (NEW!)
- SQLite database for fast queries
- SQL query interface for building data
- Automatic JSON to SQLite migration
- Spatial indexing for proximity searches
- Full-text search on equipment
- Equipment connection tracking
- System tracing (upstream/downstream)
- Impact analysis for failures
- Smart find with proximity search

## Installation

```bash
# Clone the repository
git clone https://github.com/joelpate/arxos.git
cd arxos

# Build the application
go build -o arx cmd/arx/main.go

# Or install globally
go install ./cmd/arx
```

## Quick Start

```bash
# Initialize Git tracking for floor plans
./arx git init

# Import a PDF floor plan
./arx import building_floor_2.pdf

# Migrate data to SQLite database (one-time setup)
./arx db migrate

# View ASCII representation
./arx map

# Add equipment manually
./arx add "Switch SW-01" --type switch --room room_2a --location 10,5

# Mark equipment status
./arx mark "Switch SW-01" --status failed --notes "No power"

# Query the database
./arx query "SELECT * FROM equipment WHERE status = 'failed'"
./arx query "SELECT type, COUNT(*) as count FROM equipment GROUP BY type"

# Export inspection report
./arx export inspection_report.pdf

# Commit changes to Git
./arx git commit "Updated equipment status after inspection"
```

## Command Reference

### Floor Plan Management

```bash
# Import PDF floor plan
./arx import <pdf_file>

# List available floor plans
./arx list

# View ASCII map
./arx map [floor_plan]

# View equipment status summary
./arx status [floor_plan]
```

### Equipment Management

```bash
# Add new equipment
./arx add <name> --type <type> --room <room_id> --location <x,y> [--notes <notes>]
# Types: mdf, idf, switch, access_point, outlet, panel, server

# Remove equipment
./arx remove <equipment_id> [--floor <floor_plan>]

# Mark equipment status
./arx mark <equipment_id> --status <status> [--notes <notes>]
# Statuses: normal, needs-repair, failed
```

### Room Management

```bash
# Create new room
./arx create <room_name> --bounds <minX,minY,maxX,maxY> [--floor <floor_plan>]
```

### Export & Reports

```bash
# Export inspection report (PDF/text format)
./arx export <output.pdf> [--floor <floor_plan>] [--original <original.pdf>]
```

### Database Queries

```bash
# Execute SQL queries on building data
./arx query "SELECT * FROM equipment WHERE status = 'failed'"
./arx query "SELECT * FROM equipment WHERE type = 'outlet' AND room_id = 'room_2b'"
./arx query "SELECT type, COUNT(*) as count FROM equipment GROUP BY type"
./arx query "SELECT e.*, r.name FROM equipment e JOIN rooms r ON e.room_id = r.id"

# Database management
./arx db migrate    # Migrate JSON files to SQLite
./arx db sync       # Sync JSON and database
```

### Equipment Connections

```bash
# Create connections between equipment
./arx connect outlet_2b panel_1 --type power
./arx connect switch_1 idf_100 --type data
./arx connect thermostat_1 hvac_unit_1 --type control

# Remove connections
./arx disconnect outlet_2b panel_1 --type power

# Trace connections
./arx trace outlet_2b upstream     # What powers this outlet?
./arx trace panel_1 downstream     # What does this panel power?
./arx trace switch_1 both          # All connections

# Analyze failure impact
./arx analyze panel_1              # What fails if panel_1 fails?
```

### Smart Search

```bash
# Find equipment with filters
./arx find --type outlet --status failed
./arx find --room room_2b
./arx find --near outlet_2b --distance 5   # Within 5 meters
```

### Version Control

```bash
# Initialize Git repository
./arx git init

# Check status
./arx git status

# Commit changes
./arx git commit "<message>"

# View history
./arx git log
```

## Universal PDF Parser

ArxOS uses a universal PDF parser that attempts multiple strategies:
1. Text extraction from vector PDFs
2. Content stream parsing for embedded text
3. Form field extraction from interactive PDFs
4. Manual entry template when parsing fails

When a PDF cannot be parsed automatically, ArxOS creates a 3x3 grid template that you can populate using the manual entry commands.

## ASCII Map Symbols

```
Equipment Types:
  ◉  Access Point / IDF
  ⚡  MDF / Main Distribution
  ▢  Switch
  ○  Outlet
  ⬡  Panel
  ▣  Server

Status Indicators:
  ✓  Normal (green)
  ⚠  Needs Repair (yellow)
  ✗  Failed (red)
```

## Project Structure

```
arxos/
├── cmd/arx/           # CLI application
├── pkg/models/        # Core data models
├── internal/          # Internal packages
│   ├── pdf/          # PDF parsing/export
│   ├── ascii/        # ASCII rendering
│   ├── state/        # State management
│   └── vcs/          # Git integration
├── scripts/          # Demo scripts
├── test_data/        # Test PDFs
└── .arxos/           # State files (Git tracked)
```

## Demo Scripts

```bash
# Run basic demo
./scripts/demo.sh

# Run manual entry demo
./scripts/demo_manual.sh
```

## Development

```bash
# Run tests
go test ./...

# Run specific test
go test ./cmd/arx -v

# Build for different platforms
GOOS=linux GOARCH=amd64 go build -o arx-linux ./cmd/arx
GOOS=darwin GOARCH=arm64 go build -o arx-mac ./cmd/arx
GOOS=windows GOARCH=amd64 go build -o arx.exe ./cmd/arx
```

## Phase 1 Completed Features ✅

- [x] Set up Go project structure
- [x] Universal PDF parser with fallback strategies
- [x] ASCII map rendering with equipment symbols
- [x] Equipment status tracking (normal, needs-repair, failed)
- [x] Manual equipment/room entry commands
- [x] PDF export with inspection reports
- [x] Git integration for version control
- [x] Comprehensive test coverage
- [x] Demo scripts

## Platform Evolution

ArxOS is transitioning from a CLI tool to a full platform with:
- 🌐 **Web Platform** - GitHub-style building repositories at arxos.io
- 📱 **Mobile Apps** - AR visualization for field workers
- 🤖 **AI Integration** - Natural language commands and automation
- 🔄 **Viral Growth** - Bidirectional user acquisition through network effects

### Documentation

- 📖 **[Platform Vision](docs/VISION.md)** - Complete vision and strategy
- 🏗️ **[Architecture v2](docs/ARCHITECTURE_V2.md)** - Technical architecture for the platform
- ✨ **[Platform Features](docs/PLATFORM_FEATURES.md)** - Detailed feature specifications
- 🗺️ **[Implementation Roadmap](docs/IMPLEMENTATION_ROADMAP.md)** - Phased development plan
- 📐 **[Original Architecture](docs/ARCHITECTURE.md)** - Current CLI architecture
- 📋 **[Development Phases](docs/PHASES.md)** - Original phase planning

## Contributing

This project is in active development. Contributions are welcome! Please read the architecture documents before submitting PRs.

## License

MIT