# ArxOS Quick Start Guide

## Overview

ArxOS is a Building Information Management System that treats buildings as code. It provides Git-like version control for building data, universal addressing for any object in any building, and multiple interface layers from terminal to AR.

## Installation

### Prerequisites
- Go 1.21 or higher
- Git
- SQLite3

### Build from Source

```bash
# Clone the repository
git clone https://github.com/joelpate/arxos
cd arxos

# Build the CLI
go build -o arx ./cmd/arx

# Install to system path
sudo mv arx /usr/local/bin/

# Install ArxOS components
arx install
```

## Basic Usage

### 1. Initialize a Building Repository

Every building in ArxOS has a unique identifier following the pattern:
`ARXOS-{CONTINENT}-{COUNTRY}-{STATE}-{CITY}-{NUMBER}`

```bash
# Create a new building repository
arx repo init ARXOS-NA-US-CA-LAX-0001 --name "My Office Building"

# Navigate to the building directory
cd ~/.arxos/buildings/ARXOS-NA-US-CA-LAX-0001
```

### 2. Define Building Structure

Buildings are defined in `building.bim.txt` files using a simple text format:

```text
# building.bim.txt
## FLOORS
FLOOR 1 "Ground Floor" 0.0
FLOOR 2 "Second Floor" 4.0

## ROOMS
ROOM 1/101 "Lobby" lobby 100.0
ROOM 1/102 "Server Room" datacenter 50.0
ROOM 2/201 "Office Space" office 200.0

## EQUIPMENT
EQUIPMENT 1/102/RACK_01 "Main Server" server operational
EQUIPMENT 2/201/COMP_01 "Workstation 1" computer operational
```

### 3. Version Control

ArxOS uses Git under the hood for version control:

```bash
# Check status
arx repo status

# Commit changes
arx repo commit -m "Added server room equipment"

# View history
arx repo log

# Create a branch for renovations
arx repo branch renovations
```

### 4. Query and Search

```bash
# List all equipment
arx list equipment

# Query by floor
arx query --floor 1

# Find all computers
arx query --type computer

# Check offline equipment
arx query --status offline

# Search for specific items
arx search "server"

# Get details of specific equipment
arx get equipment 1/102/RACK_01
```

### 5. Modify Building

```bash
# Add new equipment
arx add equipment 2/201/PRINT_01 "Network Printer" printer operational

# Add a new room
arx add room 2/202 "Conference Room" conference 50.0

# Remove equipment
arx remove equipment 2/201/COMP_01

# Commit changes
arx repo commit -m "Added printer and conference room"
```

## Universal Addressing

Every object in ArxOS has a unique address:

- Building: `ARXOS-NA-US-CA-LAX-0001`
- Floor: `ARXOS-NA-US-CA-LAX-0001/2`
- Room: `ARXOS-NA-US-CA-LAX-0001/2/201`
- Equipment: `ARXOS-NA-US-CA-LAX-0001/2/201/COMP_01`

This enables precise references across systems and networks.

## BIM File Format

The Building Information Model (BIM) text format is human-readable and version-control friendly:

### Floors
```
FLOOR <number> "<name>" <elevation>
```

### Rooms
```
ROOM <floor>/<number> "<name>" <type> <area>
```
Types: office, conference, datacenter, lobby, utility, storage, kitchen, restroom

### Equipment
```
EQUIPMENT <floor>/<room>/<id> "<name>" <type> <status>
```
Types: computer, server, hvac, electrical, printer, av, network, security
Status: operational, maintenance, offline, error

### Critical Systems
```
CRITICAL <equipment_path> "<description>"
```

## Advanced Features

### SQL Queries

For complex queries, use direct SQL:

```bash
arx query --sql "SELECT * FROM equipment WHERE status = 'maintenance'"
```

### API Server

Start the REST API server:

```bash
# Start server on port 8080
arx serve

# In another terminal, query the API
curl http://localhost:8080/api/buildings
```

### Multiple Buildings

Manage multiple buildings by switching directories:

```bash
# List all buildings
ls ~/.arxos/buildings/

# Switch to a different building
cd ~/.arxos/buildings/ARXOS-NA-US-NY-NYC-0001
```

## Real-World Examples

### Example 1: Emergency Maintenance

```bash
# Find all critical systems
arx query --critical

# Check status of HVAC systems
arx query --type hvac

# Mark system for maintenance
vi building.bim.txt  # Change status to 'maintenance'
arx repo commit -m "HVAC_01 scheduled for emergency maintenance"
```

### Example 2: Office Relocation

```bash
# Create a branch for the move
arx repo branch office-move

# Add new workstations
for i in {1..10}; do
  arx add equipment 3/301/COMP_$(printf %02d $i) "Workstation $i" computer operational
done

# Commit the changes
arx repo commit -m "Added 10 workstations to floor 3"

# Merge when complete
arx repo branch main
arx repo merge office-move
```

### Example 3: Building Audit

```bash
# Generate equipment summary
echo "=== Building Equipment Audit ==="
echo "Total Equipment: $(arx list equipment | wc -l)"
echo "Operational: $(arx query --status operational | wc -l)"
echo "Maintenance: $(arx query --status maintenance | wc -l)"
echo "Offline: $(arx query --status offline | wc -l)"

# List equipment by floor
for floor in 1 2 3; do
  echo "Floor $floor: $(arx query --floor $floor | wc -l) items"
done
```

## Integration

### Git Integration

Since ArxOS uses Git, you can use standard Git commands:

```bash
cd ~/.arxos/buildings/ARXOS-NA-US-CA-LAX-0001
git remote add origin https://github.com/myorg/building-001.git
git push -u origin main
```

### CI/CD Pipeline

Example GitHub Actions workflow:

```yaml
name: Building Validation
on: [push]
jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Install ArxOS
        run: |
          go install github.com/joelpate/arxos/cmd/arx@latest
      - name: Validate BIM
        run: |
          arx validate building.bim.txt
      - name: Check Critical Systems
        run: |
          arx query --critical --status offline
```

## Troubleshooting

### Database Issues

```bash
# Reset database
rm ~/.arxos/data/arxos.db
arx install
```

### Git Conflicts

```bash
# Resolve conflicts in building.bim.txt
vi building.bim.txt
git add building.bim.txt
git commit -m "Resolved conflicts"
```

### Permission Errors

```bash
# Fix permissions
chmod -R 755 ~/.arxos
```

## Next Steps

1. **Run the Demo**: Execute `demos/demo.sh` for an interactive walkthrough
2. **Explore Examples**: Check the `demos/` directory for sample buildings
3. **API Documentation**: Start the server and visit http://localhost:8080/docs
4. **Mobile AR**: See `mobile/README.md` for AR application setup
5. **Web Visualization**: See `web/README.md` for 3D visualization setup

## Support

- GitHub Issues: https://github.com/joelpate/arxos/issues
- Documentation: https://github.com/joelpate/arxos/wiki
- Examples: `/demos` directory in the repository

---

*ArxOS - Building Information as Code*