# ArxOS MVP - Terminal Rendering & CLI Validation

**Status:** ✅ **COMPLETE** - Ready for Testing

## What This MVP Does

This MVP validates the core ArxOS concept: **create building structures via CLI and render them as ASCII floor plans in the terminal**. It proves that the universal naming convention and CLI language work intuitively before investing in complex features.

## Features Implemented

### ✅ 1. Building Management
```bash
# Create buildings
arx building create --name "Main School" --address "123 Main St"

# List buildings
arx building list

# Get building details
arx building get <building-id>
```

### ✅ 2. Floor Management
```bash
# Create floor
arx floor create --building <id> --level 3 --name "Third Floor"

# List floors
arx floor list --building <id>
```

### ✅ 3. Room Management with Positioning
```bash
# Create room with position and dimensions
arx room create --floor <id> --name "Classroom" --number "301" \
  --x 0 --y 0 --width 30 --height 20

# Move room to new position
arx room move <room-id> --x 10 --y 20

# Resize room
arx room resize <room-id> --width 40 --height 25

# List rooms
arx room list --floor <id>
```

### ✅ 4. Equipment with Automatic Path Generation
```bash
# Create equipment - path is auto-generated!
arx equipment create --name "VAV-301" --type hvac \
  --building <id> --floor <id> --room <id> \
  --x 15 --y 10

# Output shows:
#   Path: /TEST-SCHOOL/3/301/HVAC/VAV-301  🎯 (Auto-generated)
```

**Path Format:** `/BUILDING/FLOOR/ROOM/SYSTEM/EQUIPMENT`

Example paths:
- `/MAIN/3/301/HVAC/VAV-301` - HVAC equipment in room 301
- `/MAIN/3/IDF-3A/NETWORK/SW-01` - Network switch in IDF
- `/MAIN/3/HALL-3A/LIGHTING/LIGHT-1` - Light in hallway

### ✅ 5. ASCII Floor Plan Rendering
```bash
# Render floor plan in terminal
arx render <building-id> --floor 3
```

Opens an interactive TUI showing:
- Rooms as ASCII boxes
- Equipment as symbols (H=HVAC, S=Switch, L=Light, etc.)
- Real-time visualization of your building structure

## Quick Start

### 1. Build ArxOS
```bash
cd /Users/joelpate/repos/arxos
go build -o arx ./cmd/arx
```

### 2. Run the Integration Test
```bash
./test_mvp_workflow.sh
```

This creates a complete test building with:
- 1 building ("Test School")
- 1 floor (Floor 3)
- 3 rooms (Classroom 301, IDF-3A, Hallway)
- 3 pieces of equipment (VAV, Switch, Light)

### 3. View the Floor Plan
```bash
./arx render <building-id> --floor 3
```

## Manual Testing Workflow

Follow the demo script from the plan:

```bash
# 1. Create building
arx building create --name "Main School" --address "123 School St"
# Output: Building ID: b1a2c3d4...

# 2. Create floor
arx floor create --building b1a2c3d4 --level 3 --name "Third Floor"
# Output: Floor ID: f5e6d7c8...

# 3. Create rooms with layout
arx room create --floor f5e6d7c8 --name "Classroom" --number "301" \
  --x 0 --y 0 --width 30 --height 20

arx room create --floor f5e6d7c8 --name "IDF-3A" --number "IDF-3A" \
  --x 35 --y 0 --width 10 --height 10

arx room create --floor f5e6d7c8 --name "Hallway" --number "HALL-3A" \
  --x 0 --y 25 --width 50 --height 10

# 4. Add equipment
arx equipment create --name "VAV-301" --type hvac \
  --building b1a2c3d4 --floor f5e6d7c8 --room <room-301-id> \
  --x 15 --y 10
# Output: Path generated: /MAIN-SCHOOL/3/301/HVAC/VAV-301

arx equipment create --name "SW-01" --type network \
  --building b1a2c3d4 --floor f5e6d7c8 --room <idf-id> \
  --x 38 --y 5
# Output: Path generated: /MAIN-SCHOOL/3/IDF-3A/NETWORK/SW-01

# 5. Render!
arx render b1a2c3d4 --floor 3
```

## What This Validates

✅ **Naming Convention Works** - Paths generate correctly and consistently
✅ **CLI Language Feels Right** - Commands are intuitive and memorable
✅ **Visual Feedback** - See structure immediately in the terminal
✅ **Workflow is Smooth** - Create → Edit → View cycle works naturally
✅ **Real-World Usable** - Can map actual buildings at your workplace

## Technical Architecture

### Code Organization
```
/Users/joelpate/repos/arxos/
├── internal/
│   ├── cli/commands/
│   │   ├── render.go          # NEW: TUI rendering command
│   │   ├── room.go             # ENHANCED: +move, +resize commands
│   │   └── equipment.go        # ENHANCED: Shows auto-generated paths
│   ├── usecase/
│   │   ├── equipment_usecase.go  # ENHANCED: Path generation logic
│   │   └── room_usecase.go       # ENHANCED: Location/dimension handling
│   ├── domain/
│   │   └── entities.go           # ENHANCED: Room model with Location/Width/Height
│   └── tui/
│       ├── models/
│       │   └── floor_plan.go     # Floor plan TUI model
│       └── services/
│           ├── floor_plan_renderer.go  # ASCII rendering
│           └── data_service.go         # Database integration
├── pkg/naming/
│   └── path.go                  # Universal naming convention helpers
└── test_mvp_workflow.sh         # Integration test script
```

### Key Components

**Path Generation** (`pkg/naming/path.go`):
- `GenerateEquipmentPath()` - Creates universal paths
- `BuildingCodeFromName()` - Extracts building code
- `GetSystemCode()` - Maps equipment types to system codes
- `GenerateEquipmentCode()` - Creates equipment identifiers

**Equipment Use Case** (`internal/usecase/equipment_usecase.go`):
- Looks up building, floor, room details
- Generates path automatically on creation
- Stores path in `equipment.path` column

**Room Management** (`internal/usecase/room_usecase.go`):
- Handles room creation with location/dimensions
- Supports move and resize operations
- Stores geometry in PostGIS

**TUI Rendering** (`internal/tui/`):
- FloorPlanRenderer - ASCII box drawing
- DataService - Loads from real database repositories
- Equipment symbols (H, E, L, P, S, etc.)

## System Requirements

- **Go:** 1.24+
- **PostgreSQL:** 14+ with PostGIS extension
- **Terminal:** Any terminal with Unicode support

## Database Schema

The MVP uses these tables (already exist):
- `buildings` - Building records
- `floors` - Floor records with levels
- `rooms` - Room records with geometry (PostGIS POLYGON), width, length
- `equipment` - Equipment records with path column

## Next Steps After MVP

Based on real usage feedback, decide:

1. **Is the naming convention intuitive?**
   - Do colleagues understand `/BUILDING/FLOOR/ROOM/SYSTEM/EQUIPMENT`?
   - Are the auto-generated codes recognizable?

2. **Do colleagues understand the CLI?**
   - Is `arx room create` intuitive?
   - Do they prefer manual creation or IFC import?

3. **What features would actually help daily work?**
   - More visualization options?
   - Better equipment search?
   - Integration with existing tools?

## Known Limitations (By Design)

This MVP intentionally excludes:
- ❌ IFC import (manual creation only)
- ❌ BAS integration
- ❌ Version control / Git features
- ❌ Mobile app
- ❌ HTTP API
- ❌ Multi-user features
- ❌ Advanced analytics
- ❌ 3D visualization

These are **deferred**, not missing. The MVP focuses on validating the core concept first.

## Deployment to Workplace

When ready to use at work:

```bash
# 1. Initialize ArxOS
./arx init --mode workplace

# 2. Setup database
./scripts/setup-dev-database.sh

# 3. Run migrations
./arx migrate up

# 4. Map one real building
# Follow the manual testing workflow above

# 5. Show colleagues
./arx render <your-building-id> --floor 3
```

## Success Metrics

✅ **Technical Success:**
- [x] Code compiles without errors
- [x] All CLI commands work with real data
- [x] Paths generate correctly
- [x] TUI renders floor plans
- [x] Integration test passes

✅ **Product Success:**
- [ ] You can map one floor at work in < 30 minutes
- [ ] Colleagues understand the naming convention
- [ ] Visual output is useful for your work
- [ ] You'd actually use this daily

## Support

For issues or questions:
1. Check the integration test output
2. Review the plan document: `/arxos-mvp---terminal-rendering.plan.md`
3. Verify database connection: `./arx health`
4. Check migrations: `./arx migrate status`

## Timeline

**Development Time:** ~6 hours (target: 15-20 hours)
- Render command: ✅ Complete
- Path generation: ✅ Complete
- Room positioning: ✅ Complete
- TUI wiring: ✅ Complete
- Integration test: ✅ Complete

**Status:** Ready for real-world validation! 🚀

