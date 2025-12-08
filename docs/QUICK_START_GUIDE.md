# ArxOS Quick Start Guide

Get started with ArxOS in 5 minutes! This guide covers the most common use cases.

---

## Table of Contents

1. [First-Time Setup](#first-time-setup)
2. [Import Your First Building](#import-your-first-building)
3. [Add and Manage Equipment](#add-and-manage-equipment)
4. [Visualize Your Building](#visualize-your-building)
5. [Browser Requirements](#browser-requirements)
6. [Hardware Integration](#hardware-integration)
7. [Export and Share](#export-and-share)

---

## First-Time Setup

### Install ArxOS

```bash
# Clone the repository
git clone https://github.com/arx-os/arxos.git
cd arxos

# Build from source (requires Rust)
cargo build --release

# Add to PATH (optional)
export PATH="$PATH:$(pwd)/target/release"
```

### Configure Your Identity

```bash
# Set your name and email (used for Git commits)
arx config set user.name "Your Name"
arx config set user.email "your.email@example.com"

# Verify configuration
arx config show
```

**Done!** You're ready to use ArxOS.

---

## Import Your First Building

### From IFC File

```bash
# Import an IFC file
arx import office-building.ifc

# ArxOS will:
# 1. Parse the IFC file
# 2. Extract rooms, equipment, and spatial data
# 3. Create a YAML file (office-building.yaml)
# 4. Initialize a Git repository

# View imported data
arx list --building "office-building"
```

### From Scratch

```bash
# Create a new building
arx init "My Building" --location "123 Main Street"

# Add a floor manually
arx add room --building "My Building" --floor 1 \
  --name "Office 101" --type Office \
  --dimensions "10x8x3"

# View structure
arx list --building "My Building"
```

---

## Add and Manage Equipment

### Adding Equipment

```bash
# Add HVAC equipment to a room
arx add equipment --building "My Building" --floor 1 \
  --name "VAV-101" --type HVAC \
  --position "5,10,2.5" \
  --room "Office 101"

# Add equipment to floor (not specific room)
arx add equipment --building "My Building" --floor 1 \
  --name "Main AHU" --type HVAC \
  --position "0,0,3"
```

### Using Spreadsheet Editor

The **spreadsheet editor** is the fastest way to manage lots of equipment:

```bash
# Open equipment spreadsheet (Excel-like interface)
arx spreadsheet equipment --building "My Building"
```

**Keyboard shortcuts:**
- `Arrow keys` - Navigate
- `Enter` - Edit cell
- `Esc` - Cancel edit
- `Ctrl-S` - Save changes (auto-commits to Git)
- `Ctrl-F` - Search/filter
- `Ctrl-Z` / `Ctrl-Y` - Undo/Redo
- `?` - Show help

### Searching Equipment

```bash
# Search for HVAC equipment
arx search "HVAC" --building "My Building"

# Filter by floor and type
arx filter --floor 2 --type HVAC

# Query by address pattern
arx query "/*/floor-02/*/hvac-*"
```

---

## Visualize Your Building

### 3D Visualization

```bash
# Interactive 3D view (terminal-based)
arx render --building "My Building" --three-d

# With equipment status colors
arx render --building "My Building" --three-d --show-status
```

**3D Controls:**
- `Arrow keys` - Rotate view
- `W/S` - Zoom in/out
- `Space` - Toggle equipment labels
- `Q` - Quit

### Status Dashboard

```bash
# Overview dashboard
arx dashboard status --building "My Building"

# Health monitoring dashboard
arx dashboard health --building "My Building"

# Live watch mode (updates in real-time)
arx watch --building "My Building"
```

---

## Export and Share

### Export to IFC

```bash
# Export for BIM tools (Revit, ArchiCAD, etc.)
arx export ifc --building "My Building" --output building.ifc

# Verify the export
arx export ifc --building "My Building" --output building.ifc --validate
```

### Export for AR/VR

```bash
# Export to glTF (for web viewers, Unity, Unreal)
arx export ar --building "My Building" \
  --format gltf --output building.gltf

# Export to USDZ (for iOS AR Quick Look)
arx export ar --building "My Building" \
  --format usdz --output building.usdz
```

### Generate Documentation

```bash
# Generate HTML documentation
arx docs --building "My Building" --output docs/

# Open in browser
open docs/index.html  # macOS
xdg-open docs/index.html  # Linux
```

## Browser Requirements

### Supported Browsers

ArxOS runs as a **Progressive Web App (PWA)** in modern browsers:

**Desktop:**
- ✅ Chrome/Edge 90+ (Recommended)
- ✅ Firefox 88+
- ✅ Safari 14+

**Mobile:**
- ✅ Chrome Mobile (Android)
- ✅ Safari Mobile (iOS 14+)
- ✅ Samsung Internet
- ✅ Firefox Mobile

**Requirements:**
- WebAssembly support
- IndexedDB for offline storage
- Service Workers for offline mode
- WebGL for 3D visualization

### Installing as PWA

**Desktop (Chrome/Edge):**
1. Visit ArxOS web app
2. Click install icon in address bar (⊕)
3. Launch from desktop/start menu

**Mobile:**
1. Visit ArxOS in browser
2. Tap "Add to Home Screen"
3. Launch like native app

**Offline Mode:**
- PWA caches all assets
- Works without internet connection
- Syncs changes when online

---

## Hardware Integration

### Connecting to Building Automation Systems

ArxOS integrates with existing building automation via standard protocols:

**BACnet (Building Automation and Control Networks):**
```bash
# Discover BACnet devices on network
arx hardware discover --protocol bacnet

# Add BACnet device
arx hardware add --protocol bacnet \
  --device-id 12345 \
  --address 192.168.1.100 \
  --building "Office Building"

# Monitor all BACnet points
arx hardware monitor --protocol bacnet --device-id 12345
```

**Modbus (Industrial Sensors):**
```bash
# Connect to Modbus TCP device
arx hardware add --protocol modbus \
  --address 192.168.1.50 \
  --port 502 \
  --building "Factory"

# Read specific registers
arx hardware read --protocol modbus \
  --address 192.168.1.50 \
  --register 40001 \
  --count 10
```

**MQTT (IoT Sensors):**
```bash
# Subscribe to MQTT broker
arx hardware mqtt \
  --broker mqtt.building.local \
  --topic sensors/hvac/# \
  --building "Office Building"

# Monitor in real-time
arx hardware monitor --protocol mqtt
```

**See:** [Vendor Integration Guide](VENDOR_INTEGRATION.md) for detailed protocol setup

---

## Export and Share

## Common Workflows

### Workflow 1: Daily Equipment Updates (5 minutes)

```bash
# 1. Open spreadsheet
arx spreadsheet equipment --building "Office Building"

# 2. Update cells (status, properties, etc.)
# 3. Press Ctrl-S to save
# 4. Changes auto-committed!

# View changes
arx diff --building "Office Building"
```

### Workflow 2: Add New Floor (10 minutes)

```bash
# 1. Add rooms
arx add room --building "Office" --floor 3 --name "301" --type Office
arx add room --building "Office" --floor 3 --name "302" --type Office
arx add room --building "Office" --floor 3 --name "303" --type Conference

# 2. Add equipment via spreadsheet (faster for multiple items)
arx spreadsheet equipment --building "Office"

# 3. Visualize
arx render --building "Office" --three-d --floor 3

# 4. Commit
arx commit --building "Office" -m "Added floor 3 with equipment"
```

### Workflow 3: Hardware Integration (20 minutes)

```bash
# Discover BACnet devices on building network
arx hardware discover --protocol bacnet

# Add discovered device
arx hardware add --protocol bacnet --device-id 12345 --address 192.168.1.100

# Monitor sensor readings in real-time
arx hardware monitor --protocol bacnet

# Link sensors to equipment in spreadsheet
arx spreadsheet equipment --building "Office"

# Export with sensor mappings
arx export ifc --building "Office" --output updated.ifc

# Share with team
git push origin main
```

### Workflow 4: Generate Report for Client (15 minutes)

```bash
# 1. Export documentation
arx docs --building "Client Building" --output client-report/

# 2. Export 3D model
arx export ar --building "Client Building" \
  --format gltf --output client-report/building.gltf

# 3. Export IFC for their BIM tools
arx export ifc --building "Client Building" \
  --output client-report/building.ifc

# 4. Package everything
tar -czf client-report.tar.gz client-report/

# 5. Send to client
# (client-report.tar.gz contains docs, 3D model, and IFC)
```

---

## Tips & Tricks

### Speed Up Your Workflow

**1. Use environment variables:**
```bash
# Set default building
export ARXOS_BUILDING="Office Building"

# Now you can omit --building flag
arx list
arx search "HVAC"
arx spreadsheet equipment
```

**2. Use shell aliases:**
```bash
# Add to your ~/.bashrc or ~/.zshrc
alias arx-office='arx --building "Office Building"'
alias arx-school='arx --building "School Complex"'

# Usage
arx-office list
arx-school spreadsheet equipment
```

**3. Use filters for large buildings:**
```bash
# Only show floor 2
arx spreadsheet equipment --filter "/*/floor-02/*"

# Only HVAC equipment
arx spreadsheet equipment --filter "/**/hvac-*"
```

### Data Management

**Best practices:**
- ✅ Commit regularly with descriptive messages
- ✅ Use meaningful equipment/room IDs
- ✅ Add properties to equipment for metadata
- ✅ Review `arx diff` before committing
- ✅ Use spreadsheet for bulk updates

**Backup your data:**
```bash
# ArxOS uses Git, so your data is versioned!
# But you should still back up your repository

# Clone for backup
git clone /path/to/my-building.git /backup/my-building.git

# Or push to remote
git remote add backup https://github.com/you/building-backup.git
git push backup main
```

### Keyboard Shortcuts (Universal)

These work in most ArxOS interactive modes:

- `?` - Show context-specific help
- `Q` - Quit
- `Ctrl-C` - Cancel operation
- `/` - Start search (in some views)
- `Esc` - Close dialogs/cancel

---

## Troubleshooting

### "Building not found"

**Problem:** `Error: Building 'Office' not found`

**Solution:**
```bash
# List available buildings
arx list

# Make sure you're in the right directory
ls *.yaml

# If YAML file exists but named differently, use exact name
arx list --building "Office Building"  # Not "Office"
```

### "Permission denied"

**Problem:** `Error: Permission denied when saving`

**Solution:**
```bash
# Check file permissions
ls -la *.yaml

# Fix permissions
chmod 644 *.yaml

# Check if file is locked by another process
lsof *.yaml
```

### "Git error: user not configured"

**Problem:** `Error: Git config incomplete`

**Solution:**
```bash
# Configure Git identity
arx config set user.name "Your Name"
arx config set user.email "your@example.com"

# Or use global Git config
git config --global user.name "Your Name"
git config --global user.email "your@example.com"
```

### Spreadsheet not saving

**Problem:** Changes in spreadsheet aren't persisting

**Solution:**
- Press `Ctrl-S` explicitly to save
- Check bottom status bar for "Saved" message
- If `--no-git` flag was used, changes save but don't commit

### Performance is slow

**Problem:** Operations taking long time

**Solution:**
```bash
# Enable caching
arx config set persistence.enable_cache true

# Use filters for large datasets
arx spreadsheet equipment --filter "floor-02/*"

# Focus on specific floor
arx render --building "Large Building" --floor 2
```

---

## Next Steps

### Learn More

- **[CLI Reference](CLI_REFERENCE.md)** - Complete command documentation
- **[User Guide](core/USER_GUIDE.md)** - Detailed feature guide
- **[API Reference](API_REFERENCE.md)** - For developers
- **[Examples](../examples/)** - Sample building files

### Join the Community

- **GitHub:** https://github.com/arx-os/arxos
- **Issues:** Report bugs or request features
- **Discussions:** Ask questions and share use cases

### Contribute

ArxOS is open source! Contributions welcome:
- Fix bugs
- Add features
- Improve documentation
- Share example buildings
- Deploy sensors and earn rewards (DePIN network)

---

## Quick Reference Card

```
COMMON COMMANDS:
  arx import <file>                  Import IFC building
  arx list                           List buildings
  arx spreadsheet equipment          Edit equipment
  arx render --three-d               Visualize 3D
  arx search <query>                 Search equipment
  arx commit -m "message"            Commit changes
  arx export ifc --output file.ifc   Export to IFC
  arx hardware discover              Discover devices
  arx hardware monitor               Monitor sensors
  arx dashboard status               Status overview
  arx help                           Show help

KEYBOARD SHORTCUTS (Spreadsheet):
  Enter       Edit cell
  Esc         Cancel edit
  Ctrl-S      Save
  Ctrl-F      Search
  Ctrl-Z      Undo
  Ctrl-Y      Redo
  ?           Help
  Q           Quit

KEYBOARD SHORTCUTS (3D Render):
  Arrows      Rotate
  W/S         Zoom
  Space       Toggle labels
  Q           Quit
```

---

**You're all set!** Start with `arx import` or `arx init` to begin managing your building data.

