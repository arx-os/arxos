# ArxOS - Building Operating System

ArxOS treats buildings as queryable, version-controlled databases. This Go implementation provides a terminal-based interface for managing floor plans and equipment status tracking.

## Vision

Buildings should be treated as living databases that can be:
- **Queried** - "Show me all failed equipment on floor 2"
- **Version Controlled** - Track all changes with Git-like workflows
- **Collaborated On** - Multiple technicians working together
- **Automated** - Integrate with BIM/CAD systems

## Current Status

**Phase 1 Implementation** ✅
- Terminal-based floor plan viewer
- PDF import with universal parser
- Manual equipment entry commands
- Equipment status tracking  
- ASCII art visualization
- PDF export with inspection reports
- Git integration for version control

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

# View ASCII representation
./arx map

# Add equipment manually
./arx add "Switch SW-01" --type switch --room room_2a --location 10,5

# Mark equipment status
./arx mark "Switch SW-01" --status failed --notes "No power"

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

## Roadmap

- **Phase 2** - Enhanced parsing with OCR, better PDF generation
- **Phase 3** - Web interface and collaboration features
- **Phase 4** - Full building OS with BIM integration

See [ARCHITECTURE.md](ARCHITECTURE.md) for design details and [PHASES.md](PHASES.md) for the complete development roadmap.

## Contributing

This project is in active development. Contributions are welcome! Please read the architecture documents before submitting PRs.

## License

MIT