# ArxOS User Guide

**Version:** 2.0  
**Date:** December 2024  
**Author:** Joel (Founder)

---

## Table of Contents

1. [Introduction](#introduction)
2. [Installation](#installation)
3. [Quick Start](#quick-start)
4. [Core Commands](#core-commands)
5. [Search & Filter System](#search--filter-system)
6. [3D Visualization](#3d-visualization)
7. [Interactive 3D Rendering](#interactive-3d-rendering)
8. [Configuration](#configuration)
9. [Troubleshooting](#troubleshooting)
10. [Examples](#examples)
11. [Best Practices](#best-practices)

---

## Introduction

**This guide is for anyone who wants to use ArxOS to manage building data.** You don't need to be a developer or know how to code.

ArxOS is a powerful terminal-based building management system that provides Git-like version control for building data, advanced 3D visualization, and real-time interactive controls. It's designed for facility managers, building operators, and anyone who needs to manage and visualize building infrastructure.

> **Note:** If you're a developer looking to contribute or build ArxOS from source, see the [README.md](../README.md) for development information.

### Key Features

- **Git-like Version Control**: Track changes to building data with full history
- **Advanced Search & Filter**: Find equipment, rooms, and buildings with regex support
- **3D Visualization**: Interactive 3D building visualization with real-time controls
- **Terminal-First**: Full functionality in terminal environment
- **Multi-format Support**: IFC, YAML, JSON data formats
- **Hardware Integration**: Support for sensors and IoT devices
- **Mobile Apps**: iOS and Android apps with AR integration

---

## Installation

> **Note:** ArxOS currently requires building from source (pre-built binaries coming soon). See the [README.md](../README.md) for installation instructions.

### Verify Installation

Once you have ArxOS installed, verify it works:

```bash
arx --version
```

---

## Quick Start

Once you have ArxOS installed (see the README for installation instructions), here's how to get started:

### 1. Import Your First Building

```bash
# Import an IFC file
arx import building.ifc
```

This will:
- Read your IFC file
- Extract building hierarchy (floors, rooms, equipment)
- Generate YAML building data
- Display a summary

### 2. Explore Your Building Data

```bash
# Check the status of your building data
arx status

# Search for specific equipment
arx search "VAV"

# View everything on the 2nd floor
arx filter --floor 2
```

### 3. Visualize Your Building

```bash
# View in 3D with status indicators
arx render --building "Your Building Name" --three-d --show-status

# Start an interactive 3D exploration session
arx interactive --building "Your Building Name" --show-status --show-rooms
```

---

## Core Commands

### Building Management

#### `arx status`
Show the current status of your building data.

```bash
arx status
# Shows: modified files, untracked changes, current branch

# Verbose output
arx status --verbose
```

#### `arx diff`
Show differences between versions.

```bash
arx diff
arx diff --file building.yaml
arx diff --commit HEAD~1  # Compare with previous commit
arx diff --stat  # Show only statistics
```

#### `arx history`
Show commit history.

```bash
arx history
arx history --limit 20
arx history --verbose
```

#### `arx stage`, `arx commit`, `arx unstage`
Git staging commands for building data.

```bash
# Stage all changes
arx stage --all

# Stage specific file
arx stage building.yaml

# Commit staged changes
arx commit "Update equipment status"

# Unstage changes
arx unstage building.yaml
```

### Data Import/Export

#### `arx import`
Import building data from IFC file.

```bash
# Import IFC file (generates YAML)
arx import building.ifc

# Import with Git repository
arx import building.ifc --repo ./building-repo
```

#### `arx export`
Export building data to Git repository.

```bash
# Export current building data
arx export --repo ./export-repo
```

---

## Search & Filter System

ArxOS provides powerful search and filtering capabilities with regex support.

### Basic Search

```bash
# Search across all data types
arx search "HVAC"

# Search only in equipment names
arx search "VAV" --equipment

# Search in room names
arx search "Conference" --rooms

# Case-sensitive search
arx search "hvac" --case-sensitive

# Search with regex pattern
arx search "VAV.*" --regex

# Limit number of results
arx search "HVAC" --limit 25

# Verbose output with details
arx search "HVAC" --verbose
```

### Advanced Filtering

```bash
# Filter by equipment type
arx filter --equipment-type "HVAC"

# Filter by status
arx filter --status "Critical"

# Filter by floor
arx filter --floor 2

# Filter by room
arx filter --room "Conference Room A"

# Multiple filters
arx filter --equipment-type "HVAC" --floor 2 --status "Warning"

# Show only critical equipment
arx filter --critical-only

# Show only healthy equipment
arx filter --healthy-only

# Show only equipment with alerts
arx filter --alerts-only

# Output in different formats
arx filter --equipment-type "HVAC" --format json
arx filter --status "Critical" --format yaml
```

### Search Features

- **Multi-field Search**: Searches across equipment, rooms, and buildings
- **Regex Support**: Full regex pattern matching with `--regex` flag
- **Case Sensitivity**: Control with `--case-sensitive` flag
- **Flexible Filtering**: Combine multiple filter criteria
- **Multiple Output Formats**: table, json, yaml

---

## 3D Visualization

ArxOS provides advanced 3D building visualization with multiple projection types and interactive controls.

### Basic 3D Rendering

```bash
# Render building in 3D
arx render --building "Building" --three-d

# Different projection types
arx render --building "Building" --three-d --projection isometric
arx render --building "Building" --three-d --projection orthographic
arx render --building "Building" --three-d --projection perspective

# Different view angles
arx render --building "Building" --three-d --view-angle topdown
arx render --building "Building" --three-d --view-angle front
arx render --building "Building" --three-d --view-angle side

# Render specific floor
arx render --building "Building" --floor 2 --three-d
```

### Rendering Options

```bash
# Show equipment status indicators
arx render --building "Building" --three-d --show-status

# Show room boundaries
arx render --building "Building" --three-d --show-rooms

# Custom scale
arx render --building "Building" --three-d --scale 2.0

# Enable spatial index for enhanced queries
arx render --building "Building" --three-d --spatial-index
```

### Output Formats

```bash
# ASCII output (default)
arx render --building "Building" --three-d --format ascii

# Advanced ASCII art
arx render --building "Building" --three-d --format advanced

# JSON output
arx render --building "Building" --three-d --format json

# YAML output
arx render --building "Building" --three-d --format yaml
```

---

## Interactive 3D Rendering

ArxOS provides real-time interactive 3D rendering with keyboard controls.

### Starting Interactive Mode

```bash
# Basic interactive session
arx interactive --building "Building"

# With status indicators
arx interactive --building "Building" --show-status

# With room boundaries
arx interactive --building "Building" --show-rooms

# With connections
arx interactive --building "Building" --show-connections

# Custom FPS and canvas size
arx interactive --building "Building" --fps 60 --width 150 --height 50

# Show FPS counter and help overlay
arx interactive --building "Building" --show-fps --show-help
```

### Interactive Controls

#### Camera Movement
- **Arrow Keys**: Move camera up, down, left, right
- **W/S**: Move camera forward/backward
- **A/D**: Rotate camera left/right
- **Q/E**: Rotate camera up/down
- **R**: Reset camera to default position

#### Zoom Controls
- **+/-**: Zoom in/out
- **0**: Reset zoom level
- **Mouse Wheel**: Zoom in/out (if mouse support enabled)

#### View Modes
- **1**: Standard view
- **2**: Cross-section view
- **3**: Connections view
- **4**: Maintenance view
- **T**: Toggle room boundaries
- **I**: Toggle status indicators
- **C**: Toggle equipment connections

#### Navigation
- **Page Up/Down**: Change floors
- **Mouse Click**: Select equipment (if mouse support enabled)
- **ESC/Q**: Quit interactive mode
- **H**: Toggle help overlay

### Interactive Features

- **Real-time Updates**: Live equipment status and building health
- **Equipment Selection**: Click to select and highlight equipment
- **Floor Navigation**: Seamless multi-floor building exploration
- **View Mode Switching**: Different visualization modes for different needs
- **Performance Monitoring**: FPS counter and session statistics

---

## Configuration

ArxOS uses a configuration file (`arx.toml`) for persistent settings.

### Configuration File

```toml
# arx.toml
[user]
name = "Your Name"
email = "you@example.com"
commit_template = "Update building data"

[paths]
default_import_path = "./imports"
backup_path = "./backups"
template_path = "./templates"
temp_path = "./temp"

[building]
default_coordinate_system = "building_local"
auto_commit = true
validate_on_import = true

[performance]
max_parallel_threads = 4
memory_limit_mb = 1024
cache_enabled = true
show_progress = true

[ui]
use_emoji = true
verbosity = "normal"
color_scheme = "auto"
```

### Configuration Commands

```bash
# Show current configuration
arx config --show

# Set configuration value (format: section.key=value)
arx config --set building.name="My Building"

# Reset to defaults
arx config --reset

# Edit configuration file
arx config --edit
```

---

## Troubleshooting

### Common Issues

#### "Building not found" Error
```bash
# Verify building name spelling
arx status

# Check if building.yaml exists in current directory
ls -la *.yaml
```

#### "No results found" in Search
```bash
# Try case-insensitive search
arx search "hvac"

# Check case sensitivity
arx search "HVAC" --case-sensitive

# Use regex for complex patterns
arx search "VAV.*" --regex

# Search only in specific category
arx search "VAV" --equipment
```

#### Interactive Mode Not Working
```bash
# Check if building data exists
arx render --building "Building" --three-d

# Try different FPS settings
arx interactive --building "Building" --fps 15

# Reduce canvas size for better performance
arx interactive --building "Building" --width 80 --height 30
```

#### Performance Issues
```bash
# Lower FPS target
arx interactive --building "Building" --fps 15

# Reduce canvas size
arx interactive --building "Building" --width 80 --height 25
```

### Debug Mode

```bash
# Enable debug logging
RUST_LOG=debug arx interactive --building "Building"

# Verbose output
arx search "HVAC" --verbose
```

---

## Examples

### Example 1: Building Health Check

```bash
# Filter for critical equipment
arx filter --critical-only

# Filter by floor and status
arx filter --floor 2 --status "Critical"

# Visualize in 3D with status indicators
arx interactive --building "Building" --show-status --show-rooms
```

### Example 2: Equipment Inventory

```bash
# Filter all HVAC equipment and export to JSON
arx filter --equipment-type "HVAC" --format json > hvac_equipment.json

# Search for specific equipment with regex
arx search "VAV" --equipment --regex

# Export building data
arx export --repo ./backup-repo
```

### Example 3: Building Comparison

```bash
# Compare current state with previous version
arx diff --commit HEAD~1

# Show history of changes
arx history --limit 10

# Show diff statistics only
arx diff --stat
```

### Example 4: Interactive Building Tour

```bash
# Start interactive session with all features
arx interactive --building "Building" --show-status --show-rooms --show-connections

# Use keyboard controls:
# - Arrow keys to move camera
# - Page Up/Down to change floors
# - Scale with +/-
# - Show help with H
# - Quit with Q
```

---

## Best Practices

### Data Management

1. **Regular Commits**: Commit changes frequently to maintain history
2. **Descriptive Messages**: Use clear commit messages
3. **Branch Strategy**: Use branches for major changes
4. **Backup**: Regular backups of your Git repository

### Search Optimization

1. **Use Specific Queries**: More specific searches are faster
2. **Limit Results**: Use `--limit` for large datasets
3. **Cache Results**: Repeated searches are cached automatically
4. **Regex Efficiency**: Simple regex patterns are faster

### 3D Rendering

1. **Appropriate Scale**: Use scale factors that fit your terminal
2. **Performance**: Lower FPS for better performance on slow systems
3. **View Modes**: Use appropriate view modes for different tasks
4. **Effects**: Disable effects on low-performance systems

### Interactive Mode

1. **Start Simple**: Begin with basic settings and add features
2. **Performance Monitoring**: Watch FPS counter for performance issues
3. **Help System**: Use H key to access help when needed
4. **Gradual Exploration**: Explore building systematically floor by floor

### Configuration

1. **Default Settings**: Start with default configuration
2. **Incremental Changes**: Make small configuration changes
3. **Validation**: Validate configuration after changes
4. **Documentation**: Document custom configurations

---

## Support

For additional help and support:

- **Documentation**: Check the `docs/` directory for detailed guides
- **Architecture**: See [ARCHITECTURE.md](ARCHITECTURE.md) for system design
- **Mobile Development**: See [MOBILE_FFI_INTEGRATION.md](MOBILE_FFI_INTEGRATION.md)
- **Issues**: Report issues on GitHub
- **Community**: Join the ArxOS community discussions

---

**Happy building management with ArxOS!** 🏗️✨
