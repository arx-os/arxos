# ArxOS CLI Reference

Complete command reference for the `arx` command-line interface.

---

## Table of Contents

- [Building Commands](#building-commands)
- [Equipment Commands](#equipment-commands)
- [Room Commands](#room-commands)
- [Import/Export Commands](#importexport-commands)
- [Git Commands](#git-commands)
- [AR Commands](#ar-commands)
- [Spreadsheet Commands](#spreadsheet-commands)
- [Visualization Commands](#visualization-commands)
- [Search & Query Commands](#search--query-commands)
- [Game Commands](#game-commands)
- [Configuration Commands](#configuration-commands)
- [Utility Commands](#utility-commands)

---

## Building Commands

### `arx init`
Initialize a new building project.

```bash
arx init <BUILDING_NAME> [OPTIONS]

# Examples
arx init "Office Building"
arx init "School Complex" --location "123 Main St, NYC"
arx init "Hospital" --description "Regional medical center"
```

**Options:**
- `--location <LOCATION>` - Building address
- `--description <DESC>` - Building description

### `arx list`
List buildings or building components.

```bash
arx list [--building <NAME>] [--floor <NUM>]

# Examples
arx list                                    # List all buildings
arx list --building "Office Building"       # List floors
arx list rooms --floor 1                    # List rooms on floor 1
```

---

## Equipment Commands

### `arx add equipment`
Add equipment to a building.

```bash
arx add equipment --building <NAME> --floor <NUM> --name <NAME> --type <TYPE> [OPTIONS]

# Examples
arx add equipment --building "Office" --floor 1 \
  --name "VAV-101" --type HVAC --position "10,20,3"

arx add equipment --building "Office" --floor 2 \
  --name "Light-201" --type Electrical --position "5,10,2.5" \
  --room "Conference Room A"
```

**Required:**
- `--building <NAME>` - Building name
- `--floor <NUM>` - Floor number
- `--name <NAME>` - Equipment name
- `--type <TYPE>` - Equipment type (HVAC, Electrical, Plumbing, Safety, AV, Furniture, Network)

**Optional:**
- `--position <X,Y,Z>` - Equipment position
- `--room <ROOM_NAME>` - Assign to room
- `--properties <KEY=VALUE>` - Additional properties (repeat for multiple)

### `arx remove equipment`
Remove equipment from a building.

```bash
arx remove equipment <EQUIPMENT_ID> --building <NAME>

# Example
arx remove equipment "VAV-101" --building "Office Building"
```

### `arx update equipment`
Update equipment properties.

```bash
arx update equipment <ID> --building <NAME> [OPTIONS]

# Examples
arx update equipment "VAV-101" --building "Office" --status Maintenance
arx update equipment "VAV-101" --building "Office" --property "temp=72"
```

---

## Room Commands

### `arx add room`
Add a room to a building floor.

```bash
arx add room --building <NAME> --floor <NUM> --name <NAME> --type <TYPE> [OPTIONS]

# Examples
arx add room --building "Office" --floor 1 \
  --name "Conference Room A" --type Office \
  --dimensions "10x8x3"

arx add room --building "Office" --floor 2 \
  --name "Server Room" --type Utility \
  --position "0,0,0" --dimensions "5x5x3"
```

**Required:**
- `--building <NAME>` - Building name
- `--floor <NUM>` - Floor number  
- `--name <NAME>` - Room name
- `--type <TYPE>` - Room type (Office, Classroom, Utility, Storage, etc.)

**Optional:**
- `--position <X,Y,Z>` - Room center position
- `--dimensions <WxDxH>` - Width x Depth x Height
- `--wing <WING_NAME>` - Assign to wing

### `arx remove room`
Remove a room from a building.

```bash
arx remove room <ROOM_ID> --building <NAME> --floor <NUM>

# Example
arx remove room "Conference Room A" --building "Office" --floor 1
```

---

## Import/Export Commands

### `arx import`
Import building data from IFC or other formats.

```bash
arx import <FILE> [OPTIONS]

# Examples
arx import building.ifc
arx import building.ifc --output "Custom Name"
arx import building.ifc --merge --building "Existing Building"
```

**Options:**
- `--output <NAME>` - Custom building name
- `--merge` - Merge with existing building
- `--building <NAME>` - Target building for merge

### `arx export`
Export building data to various formats.

```bash
arx export <FORMAT> --building <NAME> --output <FILE> [OPTIONS]

# IFC Export
arx export ifc --building "Office" --output building.ifc
arx export ifc --building "Office" --output building.ifc --delta

# AR Export (glTF/USDZ)
arx export ar --building "Office" --format gltf --output model.gltf
arx export ar --building "Office" --format usdz --output model.usdz

# Documentation Export
arx docs --building "Office" --output docs/ --format html
```

**Formats:**
- `ifc` - Industry Foundation Classes
- `ar` - AR formats (glTF, USDZ)
- `docs` - HTML documentation

**AR Format Options:**
- `--format <gltf|usdz>` - AR format
- `--anchors` - Include spatial anchors
- `--optimize` - Optimize for mobile

---

## Git Commands

### `arx diff`
Show uncommitted changes.

```bash
arx diff --building <NAME>

# Example
arx diff --building "Office Building"
```

### `arx commit`
Commit changes to version control.

```bash
arx commit --building <NAME> -m <MESSAGE>

# Example
arx commit --building "Office" -m "Added floor 2 HVAC equipment"
```

### `arx log`
View commit history.

```bash
arx log --building <NAME> [OPTIONS]

# Examples
arx log --building "Office"
arx log --building "Office" --limit 10
arx log --building "Office" --author "john@example.com"
```

### `arx history`
View detailed change history with diffs.

```bash
arx history --building <NAME>

# Example
arx history --building "Office Building"
```

---

## AR Commands

### `arx ar pending`
Manage pending AR-detected equipment.

```bash
arx ar pending --building <NAME>

# Example  
arx ar pending --building "Office Building"
```

**Interactive mode:**
- Navigate pending items
- Confirm or reject detections
- Assign to rooms
- Review confidence scores

### `arx ar process`
Process AR scan data.

```bash
arx ar process <SCAN_FILE> --building <NAME> [OPTIONS]

# Examples
arx ar process scan.json --building "Office"
arx ar process scan.json --building "Office" --confidence 0.8
arx ar process scan.json --building "Office" --auto-confirm
```

**Options:**
- `--confidence <THRESHOLD>` - Minimum confidence (0.0-1.0)
- `--auto-confirm` - Auto-confirm high-confidence detections
- `--email <EMAIL>` - Attribution email

---

## Spreadsheet Commands

### `arx spreadsheet`
Open interactive spreadsheet editor (Excel-like TUI).

```bash
arx spreadsheet <TYPE> --building <NAME> [OPTIONS]

# Examples
arx spreadsheet equipment --building "Office"
arx spreadsheet rooms --building "Office"
arx spreadsheet sensors --building "Office"

# With filtering
arx spreadsheet equipment --building "Office" --filter "HVAC"
arx spreadsheet equipment --building "Office" --filter "/*/floor-02/*"
```

**Types:**
- `equipment` - Edit equipment data
- `rooms` - Edit room data
- `sensors` - View sensor data (read-only)

**Options:**
- `--filter <PATTERN>` - Filter rows by glob pattern
- `--no-git` - Don't auto-commit changes
- `--read-only` - Open in read-only mode

**Keyboard Shortcuts (in spreadsheet):**
- `Arrow keys` - Navigate cells
- `Enter` - Edit cell
- `Esc` - Cancel edit
- `Ctrl-S` - Save changes
- `Ctrl-F` - Search
- `Ctrl-Q` - Quit
- `Ctrl-Z/Ctrl-Y` - Undo/Redo
- `?` - Show help

---

## Visualization Commands

### `arx render`
Render building visualization.

```bash
arx render --building <NAME> [OPTIONS]

# Examples
arx render --building "Office"                    # ASCII 2D
arx render --building "Office" --three-d          # Terminal 3D
arx render --building "Office" --three-d --show-status  # With status colors
```

**Options:**
- `--three-d` - 3D rendering mode
- `--show-status` - Color equipment by status
- `--floor <NUM>` - Show specific floor only

### `arx dashboard`
Interactive dashboards.

```bash
arx dashboard <TYPE> --building <NAME>

# Examples
arx dashboard status --building "Office"    # Status overview
arx dashboard health --building "Office"    # Health monitoring
arx watch --building "Office"               # Live watch mode
```

**Types:**
- `status` - Building status dashboard
- `health` - Equipment health dashboard

---

## Search & Query Commands

### `arx search`
Search for equipment or rooms.

```bash
arx search <QUERY> [--building <NAME>]

# Examples
arx search "VAV"                           # Search all buildings
arx search "VAV" --building "Office"       # Search specific building
arx search "HVAC" --type equipment         # Search equipment only
```

### `arx query`
Query by ArxAddress path.

```bash
arx query <ADDRESS_PATTERN>

# Examples
arx query "/usa/ny/brooklyn/*/floor-01/*"
arx query "/usa/ny/brooklyn/ps-118/floor-*/room-*"
arx query "/usa/**/floor-02/*/hvac-*"      # Any floor 02 HVAC
```

### `arx filter`
Filter equipment/rooms by criteria.

```bash
arx filter [OPTIONS]

# Examples
arx filter --floor 2
arx filter --type HVAC
arx filter --status Critical
arx filter --floor 2 --type HVAC --status Warning
```

---

## Game Commands

### `arx game review`
Review contractor PRs interactively.

```bash
arx game review --pr-id <ID> --building <NAME> [OPTIONS]

# Examples
arx game review --pr-id pr_001 --building "Office" --interactive
arx game review --pr-id pr_002 --building "Office" --auto-mode
```

**Options:**
- `--interactive` - Interactive review mode
- `--auto-mode` - Automated validation
- `--strict` - Strict constraint checking

### `arx game plan`
Interactive equipment placement planning.

```bash
arx game plan --building <NAME> [OPTIONS]

# Examples
arx game plan --building "Office" --interactive
arx game plan --building "Office" --floor 1 --type HVAC
```

**Options:**
- `--interactive` - Interactive planning mode
- `--floor <NUM>` - Focus on specific floor
- `--type <TYPE>` - Plan specific equipment type

---

## Configuration Commands

### `arx config`
Manage ArxOS configuration.

```bash
# View current config
arx config show

# Set configuration values
arx config set <KEY> <VALUE>

# Examples
arx config set user.name "John Doe"
arx config set user.email "john@example.com"
arx config set render.theme "dark"
arx config set git.auto_commit true
```

**Configuration Keys:**
- `user.name` - User name for attribution
- `user.email` - User email for commits
- `render.theme` - UI theme (dark, light, auto)
- `git.auto_commit` - Auto-commit changes
- `git.gpg_sign` - GPG sign commits
- `export.default_format` - Default export format

### `arx config wizard`
Interactive configuration setup.

```bash
arx config wizard
```

---

## Utility Commands

### `arx help`
Show help information.

```bash
arx help [COMMAND]

# Examples
arx help                    # General help
arx help add                # Help for 'add' command
arx help spreadsheet        # Help for spreadsheet editor
```

### `arx version`
Show version information.

```bash
arx version
```

### `arx doctor`
Check system health and configuration.

```bash
arx doctor [--building <NAME>]
```

---

## Advanced Usage

### Glob Patterns in Filters
ArxOS supports powerful glob patterns for filtering:

```bash
# All equipment on floor 02
arx spreadsheet equipment --filter "/*/floor-02/*"

# All boilers anywhere
arx spreadsheet equipment --filter "/**/boiler-*"

# All HVAC on floor 02 in any wing
arx spreadsheet equipment --filter "/*/floor-02/wing-*/hvac-*"

# Multiple wildcards
arx query "/usa/*/brooklyn/**/floor-0[123]/*"
```

### Piping and Scripting
```bash
# Export and pipe to other tools
arx export ifc --building "Office" --output - | ifc-validator

# Batch operations
for building in $(arx list --json | jq -r '.[].name'); do
  arx export ifc --building "$building" --output "${building}.ifc"
done

# Generate reports
arx query "/usa/ny/**" --json | jq '.[] | select(.equipment_type == "HVAC")'
```

### Environment Variables
```bash
# Set default building
export ARXOS_BUILDING="Office Building"
arx list          # Uses ARXOS_BUILDING

# Set config path
export ARXOS_CONFIG_PATH="$HOME/.config/arxos/config.toml"

# Set verbose mode
export ARXOS_VERBOSE=1
arx import building.ifc
```

### Configuration File
ArxOS reads configuration from `~/.config/arxos/config.toml`:

```toml
[user]
name = "John Doe"
email = "john@example.com"

[git]
auto_commit = true
gpg_sign = false

[render]
theme = "auto"
enable_mouse = true

[export]
default_format = "ifc"
ar_format = "gltf"
```

---

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | General error |
| 2 | Invalid arguments |
| 3 | File not found |
| 4 | Permission denied |
| 5 | Git error |
| 6 | IFC parsing error |
| 10 | Configuration error |

---

## Common Workflows

### Workflow 1: Import and Edit Building
```bash
# 1. Import IFC file
arx import building.ifc --output "Office Building"

# 2. View structure
arx list --building "Office Building"

# 3. Edit equipment in spreadsheet
arx spreadsheet equipment --building "Office Building"

# 4. Commit changes
arx commit --building "Office Building" -m "Updated equipment data"
```

### Workflow 2: Add New Floor with Equipment
```bash
# 1. Add rooms
arx add room --building "Office" --floor 3 \
  --name "Room 301" --type Office --dimensions "10x8x3"

# 2. Add equipment
arx add equipment --building "Office" --floor 3 \
  --name "VAV-301" --type HVAC --room "Room 301"

# 3. Visualize
arx render --building "Office" --three-d --floor 3

# 4. Commit
arx commit --building "Office" -m "Added floor 3"
```

### Workflow 3: AR Integration
```bash
# 1. Start AR scan on mobile device
# (Mobile app captures equipment)

# 2. Review pending equipment
arx ar pending --building "Office"

# 3. Confirm or reject detections interactively
# (Use arrow keys, Enter to confirm, R to reject)

# 4. Changes auto-committed
arx log --building "Office"
```

### Workflow 4: Export for Stakeholders
```bash
# 1. Export IFC for BIM tools
arx export ifc --building "Office" --output office.ifc

# 2. Export glTF for 3D viewers
arx export ar --building "Office" --format gltf --output office.gltf

# 3. Generate documentation
arx docs --building "Office" --output docs/

# 4. Package for distribution
tar -czf office-building-export.tar.gz office.ifc office.gltf docs/
```

### Workflow 5: Health Monitoring
```bash
# 1. Configure sensor mappings (via spreadsheet)
arx spreadsheet equipment --building "Office"

# 2. Monitor health dashboard
arx dashboard health --building "Office"

# 3. Query critical equipment
arx filter --status Critical --building "Office"

# 4. Generate health report
arx query "/**/floor-*/room-*" --json | \
  jq '[.[] | select(.health_status == "Critical")]' > critical_equipment.json
```

---

## Tips & Best Practices

### Performance
- Use `--filter` to limit data for large buildings
- Use `--floor` to focus on specific floors
- Enable caching in config for frequently accessed buildings

### Version Control
- Commit regularly with descriptive messages
- Use meaningful commit messages for change tracking
- Review `arx diff` before committing

### Data Quality
- Always specify positions when adding equipment/rooms
- Use consistent naming conventions
- Validate with `arx doctor` regularly

### Automation
- Use `--json` output for scripting
- Set `ARXOS_BUILDING` for batch operations
- Use `--no-git` when making bulk changes, commit once at end

---

## Troubleshooting

### "Building not found"
```bash
# List available buildings
arx list

# Check current directory has building.yaml files
ls *.yaml
```

### "Permission denied"
```bash
# Check file permissions
ls -la *.yaml

# Ensure you have write access to the directory
```

### "Git error"
```bash
# Configure git if not set up
arx config set user.name "Your Name"
arx config set user.email "your@email.com"

# Check git status
cd <building-directory>
git status
```

### Performance Issues
```bash
# Enable caching
arx config set persistence.enable_cache true

# Use filters for large datasets
arx spreadsheet equipment --filter "floor-02/*"
```

---

## See Also

- **[User Guide](core/USER_GUIDE.md)** - Complete usage guide
- **[API Reference](API_REFERENCE.md)** - Programmatic API
- **[Architecture](core/ARCHITECTURE.md)** - System design
- **[Examples](../examples/)** - Example files

For more help, run `arx help <command>` or visit https://github.com/arx-os/arxos/docs

