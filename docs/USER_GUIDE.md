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
8. [Particle Effects & Animations](#particle-effects--animations)
9. [Configuration](#configuration)
10. [Troubleshooting](#troubleshooting)
11. [Examples](#examples)
12. [Best Practices](#best-practices)

---

## Introduction

ArxOS is a powerful terminal-based building management system that provides Git-like version control for building data, advanced 3D visualization, and real-time interactive controls. It's designed for facility managers, building operators, and anyone who needs to manage and visualize building infrastructure.

### Key Features

- **Git-like Version Control**: Track changes to building data with full history
- **Advanced Search & Filter**: Find equipment, rooms, and buildings with fuzzy matching and regex support
- **3D Visualization**: Interactive 3D building visualization with real-time controls
- **Particle Effects**: Advanced visual effects for equipment status and building health
- **Terminal-First**: Full functionality in terminal environment
- **Multi-format Support**: IFC, YAML, JSON data formats
- **Hardware Integration**: Support for sensors and IoT devices

---

## Installation

### Prerequisites

- Rust 1.70+ (for development)
- Git (for version control)
- Terminal with Unicode support

### Building from Source

```bash
# Clone the repository
git clone https://github.com/your-username/arxos.git
cd arxos

# Build the project
cargo build --release

# Install globally (optional)
cargo install --path .
```

### Verify Installation

```bash
arxos --version
```

---

## Quick Start

### 1. Initialize a Building Project

```bash
# Create a new building project
mkdir my-building
cd my-building

# Initialize Git repository
git init

# Create building configuration
arxos config init
```

### 2. Import Building Data

```bash
# Import IFC file
arxos import building.ifc --building "My Building"

# Check status
arxos status
```

### 3. Explore Your Building

```bash
# List all equipment
arxos list equipment

# Search for HVAC equipment
arxos search "HVAC" --equipment

# View 3D visualization
arxos render --building "My Building" --3d
```

### 4. Interactive 3D Mode

```bash
# Start interactive 3D session
arxos interactive --building "My Building" --show-status --show-rooms
```

---

## Core Commands

### Building Management

#### `arxos status`
Show the current status of your building data.

```bash
arxos status
# Shows: modified files, untracked changes, current branch
```

#### `arxos diff`
Show differences between versions.

```bash
arxos diff
arxos diff --building "Building Name"
arxos diff HEAD~1  # Compare with previous commit
```

#### `arxos history`
Show commit history.

```bash
arxos history
arxos history --building "Building Name" --limit 10
```

### Data Import/Export

#### `arxos import`
Import building data from various formats.

```bash
# Import IFC file
arxos import building.ifc --building "Building Name"

# Import with custom settings
arxos import building.ifc --building "Building Name" --spatial-index --verbose
```

#### `arxos export`
Export building data to various formats.

```bash
# Export to JSON
arxos export --building "Building Name" --format json

# Export specific floor
arxos export --building "Building Name" --floor 2 --format yaml
```

---

## Search & Filter System

ArxOS provides powerful search and filtering capabilities with fuzzy matching, regex support, and real-time highlighting.

### Basic Search

```bash
# Search for equipment
arxos search "HVAC"

# Search with case sensitivity
arxos search "hvac" --case-sensitive

# Search with regex
arxos search "VAV.*Unit" --regex
```

### Advanced Filtering

```bash
# Filter by equipment type
arxos filter --equipment-type "HVAC"

# Filter by status
arxos filter --status "Critical"

# Filter by floor
arxos filter --floor 2

# Filter by room
arxos filter --room "Conference Room A"

# Multiple filters
arxos filter --equipment-type "HVAC" --floor 2 --status "Warning"
```

### Output Formats

```bash
# Table format (default)
arxos search "HVAC" --format table

# JSON format
arxos search "HVAC" --format json

# YAML format
arxos search "HVAC" --format yaml

# Verbose output
arxos search "HVAC" --verbose
```

### Search Features

- **Fuzzy Matching**: Automatically handles typos and partial matches
- **Multi-field Search**: Searches across names, types, system types, and paths
- **Regex Support**: Full regex pattern matching
- **Real-time Highlighting**: Highlights matching text in results
- **Performance Optimized**: Efficient search with result caching

---

## 3D Visualization

ArxOS provides advanced 3D building visualization with multiple projection types and interactive controls.

### Basic 3D Rendering

```bash
# Render building in 3D
arxos render --building "Building Name" --3d

# Different projection types
arxos render --building "Building Name" --3d --projection isometric
arxos render --building "Building Name" --3d --projection orthographic
arxos render --building "Building Name" --3d --projection perspective

# Different view angles
arxos render --building "Building Name" --3d --view-angle topdown
arxos render --building "Building Name" --3d --view-angle front
arxos render --building "Building Name" --3d --view-angle side
```

### Rendering Options

```bash
# Show equipment status
arxos render --building "Building Name" --3d --show-status

# Show room boundaries
arxos render --building "Building Name" --3d --show-rooms

# Show equipment connections
arxos render --building "Building Name" --3d --show-connections

# Custom scale and size
arxos render --building "Building Name" --3d --scale 2.0 --width 150 --height 50
```

### Output Formats

```bash
# ASCII output (default)
arxos render --building "Building Name" --3d --format ascii

# Advanced ASCII art
arxos render --building "Building Name" --3d --format advanced

# JSON output
arxos render --building "Building Name" --3d --format json

# YAML output
arxos render --building "Building Name" --3d --format yaml
```

---

## Interactive 3D Rendering

ArxOS provides real-time interactive 3D rendering with keyboard and mouse controls.

### Starting Interactive Mode

```bash
# Basic interactive session
arxos interactive --building "Building Name"

# With status indicators
arxos interactive --building "Building Name" --show-status

# With room boundaries
arxos interactive --building "Building Name" --show-rooms

# With connections
arxos interactive --building "Building Name" --show-connections

# Custom FPS and size
arxos interactive --building "Building Name" --fps 60 --width 150 --height 50
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

## Particle Effects & Animations

ArxOS includes advanced particle effects and animation systems for enhanced visual feedback.

### Equipment Status Effects

Equipment automatically displays status indicators with particle effects:

- **Healthy**: Green checkmark with subtle pulse
- **Warning**: Yellow warning symbol with gentle animation
- **Critical**: Red X with urgent blinking
- **Maintenance**: Wrench icon with maintenance alert particles
- **Offline**: Gray circle with fade effect

### Maintenance Alerts

```bash
# Create maintenance alert effect
arxos interactive --building "Building Name" --show-maintenance

# Alert levels:
# - Low: Orange diamond
# - Medium: Orange circle
# - High: Red circle
# - Critical: Red alert symbol
```

### Particle Effects

ArxOS supports various particle effects:

- **Smoke**: Rising smoke particles for environmental effects
- **Fire**: Flickering fire particles for emergency visualization
- **Sparks**: Energy spark particles for electrical equipment
- **Dust**: Falling dust particles for environmental effects
- **Status Indicators**: Pulsing status particles for equipment health
- **Connections**: Flowing connection particles for equipment relationships

### Animation Types

- **Camera Movement**: Smooth camera transitions with easing
- **Status Transitions**: Animated status changes
- **Building Fade**: Smooth building appearance/disappearance
- **Selection Highlight**: Pulsing highlight effects
- **Floor Transitions**: Animated floor changes
- **View Mode Changes**: Smooth transitions between view modes

---

## Configuration

ArxOS uses a configuration file (`arx.toml`) for persistent settings.

### Configuration File

```toml
# arx.toml
[building]
name = "My Building"
description = "Main office building"

[rendering]
default_projection = "isometric"
default_view_angle = "isometric"
show_status = true
show_rooms = true
show_connections = false

[search]
case_sensitive = false
use_regex = false
fuzzy_matching = true
max_results = 100

[interactive]
target_fps = 30
show_fps = true
show_help = false
enable_mouse = true

[effects]
enable_particles = true
enable_animations = true
max_particles = 1000
quality_level = "medium"
```

### Configuration Commands

```bash
# Show current configuration
arxos config show

# Set configuration value
arxos config set rendering.default_projection "orthographic"

# Reset to defaults
arxos config reset

# Validate configuration
arxos config validate
```

---

## Troubleshooting

### Common Issues

#### "Building not found" Error
```bash
# Check available buildings
arxos list buildings

# Verify building name spelling
arxos status
```

#### "No results found" in Search
```bash
# Try fuzzy search
arxos search "hvac" --fuzzy

# Check case sensitivity
arxos search "HVAC" --case-sensitive

# Use regex for complex patterns
arxos search "VAV.*" --regex
```

#### Interactive Mode Not Working
```bash
# Check terminal compatibility
arxos interactive --building "Building Name" --help

# Try different FPS settings
arxos interactive --building "Building Name" --fps 15

# Disable mouse support
arxos interactive --building "Building Name" --no-mouse
```

#### Performance Issues
```bash
# Reduce particle count
arxos interactive --building "Building Name" --max-particles 500

# Lower FPS target
arxos interactive --building "Building Name" --fps 15

# Disable effects
arxos interactive --building "Building Name" --no-effects
```

### Debug Mode

```bash
# Enable debug logging
RUST_LOG=debug arxos interactive --building "Building Name"

# Verbose output
arxos search "HVAC" --verbose --debug
```

---

## Examples

### Example 1: Building Health Check

```bash
# Search for critical equipment
arxos search "critical" --status

# Filter by floor
arxos filter --floor 2 --status "Critical"

# Visualize in 3D with status indicators
arxos interactive --building "Building Name" --show-status --show-maintenance
```

### Example 2: Equipment Inventory

```bash
# List all HVAC equipment
arxos filter --equipment-type "HVAC" --format json > hvac_equipment.json

# Search for specific equipment
arxos search "VAV" --equipment --regex

# Export equipment data
arxos export --building "Building Name" --equipment-type "HVAC" --format yaml
```

### Example 3: Building Comparison

```bash
# Compare current state with previous version
arxos diff HEAD~1

# Show history of changes
arxos history --building "Building Name" --limit 10

# Export differences
arxos diff --format json > changes.json
```

### Example 4: Interactive Building Tour

```bash
# Start interactive session
arxos interactive --building "Building Name" --show-status --show-rooms --show-connections

# Use controls:
# - Arrow keys to move around
# - Page Up/Down to change floors
# - 1-4 to switch view modes
# - T/I/C to toggle overlays
# - H for help
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
- **Examples**: See `examples/` directory for usage examples
- **Issues**: Report issues on GitHub
- **Community**: Join the ArxOS community discussions

---

**Happy building management with ArxOS!** 🏗️✨
