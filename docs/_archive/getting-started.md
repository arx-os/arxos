# Getting Started with ArxOS

**Git for Buildings** – Quick start guide

---

## Installation

### Prerequisites

- **Rust toolchain** (1.75+) – Install from [rustup.rs](https://rustup.rs)
- **Git** – For version control
- **Trunk** (optional) – For web interface: `cargo install trunk`

### Build from Source

```bash
# Clone the repository
git clone https://github.com/arx-os/arxos.git
cd arxos

# Build and install
cargo build --release
cargo install --path .

# Verify installation
arx --help
```

---

## Your First Building

### 1. Initialize a Building

```bash
# Create a new building project
arx init --name "Office Building" --git-init --commit

# This creates:
# - building.yaml (building data)
# - .arxos/ directory (ArxOS metadata)
# - .git/ repository (version control)
```

### 2. Import an IFC File

If you have an IFC file from CAD software:

```bash
# Import IFC to building.yaml
arx import office-building.ifc

# View imported structure
arx render --building "Office Building"
```

### 3. View Your Building

```bash
# List all buildings
arx status

# Show building structure (TUI)
arx render --building "Office Building"

# Interactive 3D view (requires --features render3d)
arx render --building "Office Building" --interactive

# Launch web interface
arx web
```

---

## Basic Workflows

### Version Control

ArxOS uses Git for all building data:

```bash
# Check status
arx status

# View changes
arx diff

# Stage changes
arx stage --all

# Commit changes
arx commit "Added new equipment to floor 2"

# View history
arx history
```

### Search and Query

```bash
# Text search
arx search "boiler"

# Query by address pattern
arx query "/usa/ny/*/floor-*/mech/*"

# Filter by criteria
arx filter --floor 2 --equipment-type HVAC
```

### Equipment Management

```bash
# View equipment
arx equipment list

# Add equipment (via spreadsheet editor)
arx spreadsheet equipment

# Update equipment status via sensors
arx process-sensors --building "Office Building" --sensor-dir ./sensor-data
```

---

## Data Format

ArxOS stores building data in YAML files under Git version control:

```
project/
├── building.yaml          # Main building data
├── .arxos/               # ArxOS metadata
│   └── config.toml       # Local configuration
└── .git/                 # Git repository
```

See [Data Format](./data-format.md) for detailed schema documentation.

---

## Web Interface

Launch the Progressive Web App:

```bash
# Start web server
arx web

# Opens browser at http://localhost:8080
# Works offline after first load
```

See [Web Interface](./web.md) for deployment and configuration.

---

## Next Steps

- **[CLI Reference](./cli-reference.md)** – Complete command documentation
- **[Architecture](./architecture.md)** – Understanding the system design
- **[IFC Import/Export](./ifc.md)** – Working with IFC files
- **[Data Format](./data-format.md)** – YAML schema and Git structure

---

## Common Tasks

### Import a building from IFC
```bash
arx import building.ifc
```

### View building in 3D
```bash
arx render --building "My Building" --interactive
```

### Edit equipment in spreadsheet
```bash
arx spreadsheet equipment
```

### Track changes with Git
```bash
arx status
arx diff
arx commit "Updated HVAC on floor 3"
```

### Launch web dashboard
```bash
arx web
```

---

## Troubleshooting

**Import fails:** Ensure IFC file is valid IFC2x3 or IFC4 format

**3D render not working:** Build with `cargo build --features render3d`

**Web interface won't start:** Install trunk: `cargo install trunk`

**Git conflicts:** Use `arx merge` for interactive conflict resolution

For more help: `arx --help` or `arx <command> --help`
