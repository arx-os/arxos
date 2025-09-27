# ArxOS Terminal User Interface (TUI) User Guide

## Overview

The ArxOS Terminal User Interface (TUI) provides a powerful, interactive command-line experience for managing building information modeling (BIM) data. Built with the Bubble Tea framework, it offers professional ASCII art visualizations, real-time data updates, and intuitive navigation.

## Features

### 🏗️ **Building Explorer**
- Hierarchical navigation: Building → Floors → Rooms → Equipment
- Detailed information display for each level
- Equipment overview with spatial relationships

### ⚙️ **Equipment Manager**
- Advanced filtering by type, status, and custom search
- Dynamic sorting capabilities
- Real-time status monitoring
- Batch operations support

### 🗺️ **Floor Plan Visualization**
- Professional ASCII art floor plans
- Equipment positioning visualization
- Interactive zoom and pan controls
- Grid and label toggles

### 🔍 **Spatial Query Interface**
- Multiple query types (radius, bounding box, floor, equipment type)
- Interactive parameter adjustment
- Results visualization with spatial data
- Query history and export capabilities

### 📊 **Interactive Dashboard**
- Real-time metrics display
- Equipment status overview
- Alert management
- Performance monitoring

## Installation & Setup

### Prerequisites

- Go 1.19 or later
- Terminal with Unicode support
- ArxOS CLI installed

### Configuration

TUI settings are integrated into the main ArxOS configuration system. You can configure TUI options through:

1. **Configuration File**: `~/.arxos/config.json`
2. **Environment Variables**: `ARXOS_TUI_*` prefixed variables
3. **Command Line Flags**: `--tui-*` options

#### Example Configuration

```json
{
  "tui": {
    "enabled": true,
    "theme": "dark",
    "update_interval": "1s",
    "max_equipment_display": 1000,
    "real_time_enabled": true,
    "animations_enabled": true,
    "spatial_precision": "1mm",
    "grid_scale": "1:10",
    "show_coordinates": true,
    "show_confidence": true,
    "compact_mode": false,
    "custom_symbols": {
      "hvac": "H",
      "electrical": "E",
      "fire_safety": "F",
      "plumbing": "P",
      "lighting": "L",
      "outlet": "O",
      "sensor": "S",
      "camera": "C"
    },
    "color_scheme": "default",
    "viewport_size": 20,
    "refresh_rate": 30,
    "enable_mouse": true,
    "enable_bracketed_paste": true
  }
}
```

#### Environment Variables

```bash
# Core TUI settings
export ARXOS_TUI_ENABLED=true
export ARXOS_TUI_THEME=dark
export ARXOS_TUI_UPDATE_INTERVAL=1s

# Performance settings
export ARXOS_TUI_MAX_EQUIPMENT=1000
export ARXOS_TUI_REALTIME=true
export ARXOS_TUI_ANIMATIONS=true

# Spatial settings
export ARXOS_TUI_SPATIAL_PRECISION=1mm
export ARXOS_TUI_GRID_SCALE=1:10

# UI settings
export ARXOS_TUI_SHOW_COORDINATES=true
export ARXOS_TUI_SHOW_CONFIDENCE=true
export ARXOS_TUI_COMPACT_MODE=false

# Advanced settings
export ARXOS_TUI_COLOR_SCHEME=default
export ARXOS_TUI_VIEWPORT_SIZE=20
export ARXOS_TUI_REFRESH_RATE=30
export ARXOS_TUI_ENABLE_MOUSE=true
export ARXOS_TUI_ENABLE_BRACKETED_PASTE=true
```

## Usage

### Basic Commands

```bash
# Dashboard
./arx visualize --tui

# Building Explorer
./arx visualize explorer --tui

# Equipment Manager
./arx visualize equipment --tui

# Floor Plan
./arx visualize floorplan --tui

# Spatial Query
./arx visualize query --tui
```

### Advanced Usage

```bash
# Specify building ID
./arx visualize --tui --building ARXOS-001

# Use custom config
./arx visualize --tui --config /path/to/config.json

# Enable debug mode
./arx visualize --tui --debug
```

## Navigation & Controls

### Universal Controls

| Key | Action |
|-----|--------|
| `Tab` | Switch between tabs/views |
| `↑↓` or `jk` | Navigate up/down |
| `←→` or `hl` | Navigate left/right |
| `Enter` | Select/confirm |
| `Escape` | Cancel/back |
| `r` | Refresh data |
| `q` or `Ctrl+C` | Quit |

### Dashboard Controls

| Key | Action |
|-----|--------|
| `Tab` | Switch between tabs (Overview, Equipment, Alerts, Metrics) |
| `↑↓` | Navigate equipment list |
| `r` | Refresh data |
| `q` | Quit |

### Building Explorer Controls

| Key | Action |
|-----|--------|
| `↑↓` | Navigate items |
| `Enter` | Drill down to next level |
| `Backspace` or `h` | Go back to previous level |
| `r` | Refresh data |
| `q` | Quit |

### Equipment Manager Controls

| Key | Action |
|-----|--------|
| `↑↓` | Navigate equipment list |
| `t` | Cycle filter type |
| `s` | Cycle filter status |
| `o` | Cycle sort order |
| `r` | Reverse sort order |
| `/` | Search mode |
| `R` | Full refresh |
| `PgUp/PgDn` | Page up/down |
| `Home/End` | Jump to top/bottom |
| `q` | Quit |

### Floor Plan Controls

| Key | Action |
|-----|--------|
| `↑↓` or `jk` | Navigate floors |
| `g` | Toggle grid |
| `l` | Toggle labels |
| `+/-` | Zoom in/out |
| `r` | Refresh data |
| `q` | Quit |

### Spatial Query Controls

| Key | Action |
|-----|--------|
| `↑↓` | Navigate query options |
| `Enter` | Execute query |
| `←→` | Adjust parameters |
| `Tab` | Switch between query types |
| `r` | Refresh results |
| `q` | Quit |

## Themes & Customization

### Built-in Themes

- **Dark**: Default theme with dark background
- **Light**: Light theme with light background
- **Auto**: Automatically adapts to terminal theme

### Custom Color Schemes

You can create custom color schemes by modifying the `color_scheme` setting:

```json
{
  "tui": {
    "color_scheme": "custom",
    "custom_colors": {
      "primary": "#00ff00",
      "secondary": "#0088ff",
      "accent": "#ff8800",
      "error": "#ff0000",
      "warning": "#ffff00",
      "success": "#00ff00"
    }
  }
}
```

### Custom Equipment Symbols

Customize equipment symbols for better visualization:

```json
{
  "tui": {
    "custom_symbols": {
      "hvac": "❄️",
      "electrical": "⚡",
      "fire_safety": "🔥",
      "plumbing": "💧",
      "lighting": "💡",
      "outlet": "🔌",
      "sensor": "📡",
      "camera": "📹"
    }
  }
}
```

## Performance Optimization

### Large Datasets

For buildings with many equipment items:

```json
{
  "tui": {
    "max_equipment_display": 500,
    "viewport_size": 15,
    "refresh_rate": 15,
    "real_time_enabled": false
  }
}
```

### Slow Networks

For remote database connections:

```json
{
  "tui": {
    "update_interval": "5s",
    "real_time_enabled": false,
    "animations_enabled": false
  }
}
```

### Terminal Compatibility

For older terminals:

```json
{
  "tui": {
    "theme": "light",
    "animations_enabled": false,
    "enable_mouse": false,
    "enable_bracketed_paste": false
  }
}
```

## Troubleshooting

### Common Issues

#### TUI Not Starting

1. Check if TUI is enabled:
   ```bash
   echo $ARXOS_TUI_ENABLED
   ```

2. Verify terminal compatibility:
   ```bash
   echo $TERM
   ```

3. Check configuration:
   ```bash
   ./arx visualize --tui --debug
   ```

#### Performance Issues

1. Reduce update frequency:
   ```bash
   export ARXOS_TUI_UPDATE_INTERVAL=5s
   ```

2. Disable animations:
   ```bash
   export ARXOS_TUI_ANIMATIONS=false
   ```

3. Limit equipment display:
   ```bash
   export ARXOS_TUI_MAX_EQUIPMENT=100
   ```

#### Display Issues

1. Check Unicode support:
   ```bash
   ./arx visualize --tui --theme light
   ```

2. Verify terminal size:
   ```bash
   stty size
   ```

3. Test with minimal config:
   ```bash
   ./arx visualize --tui --compact
   ```

### Debug Mode

Enable debug mode for detailed logging:

```bash
# Environment variable
export ARXOS_TUI_DEBUG=true

# Command line flag
./arx visualize --tui --debug
```

### Log Files

TUI logs are written to:
- `~/.arxos/logs/tui.log` - General TUI logs
- `~/.arxos/logs/tui-debug.log` - Debug logs (when debug mode enabled)

## Examples

### Basic Building Exploration

```bash
# Start with dashboard
./arx visualize --tui

# Navigate to building explorer
# Press 'e' to switch to explorer mode

# Drill down through building hierarchy
# Use ↑↓ to navigate, Enter to select
```

### Equipment Management

```bash
# Start equipment manager
./arx visualize equipment --tui

# Filter by type
# Press 't' to cycle through equipment types

# Search for specific equipment
# Press '/' to enter search mode

# Sort by status
# Press 's' to cycle through status filters
```

### Floor Plan Visualization

```bash
# Start floor plan view
./arx visualize floorplan --tui

# Navigate floors
# Use ↑↓ to switch between floors

# Toggle grid
# Press 'g' to show/hide grid

# Zoom controls
# Use +/- to zoom in/out
```

### Spatial Queries

```bash
# Start spatial query interface
./arx visualize query --tui

# Select query type
# Use Tab to switch between radius, bbox, floor, type

# Adjust parameters
# Use ←→ to modify values

# Execute query
# Press Enter to run the query
```

## Integration

### CLI Integration

TUI modes can be integrated into scripts:

```bash
#!/bin/bash
# Building inspection script

# Start with dashboard
./arx visualize --tui --building $BUILDING_ID

# Automatically switch to equipment view
# (requires TUI automation features)
```

### API Integration

TUI can work alongside the REST API:

```bash
# Start TUI in one terminal
./arx visualize --tui

# Use API in another terminal
curl http://localhost:8080/api/v1/buildings/ARXOS-001/equipment
```

## Best Practices

### Configuration Management

1. **Use environment variables** for deployment-specific settings
2. **Use config files** for user-specific preferences
3. **Version control** your configuration files
4. **Document** custom configurations

### Performance

1. **Limit equipment display** for large buildings
2. **Adjust update intervals** based on data freshness needs
3. **Disable animations** on slow terminals
4. **Use compact mode** for limited screen space

### User Experience

1. **Start with dashboard** for overview
2. **Use building explorer** for detailed navigation
3. **Use equipment manager** for bulk operations
4. **Use floor plans** for spatial understanding
5. **Use spatial queries** for specific searches

## Support

### Getting Help

1. **Check logs**: `~/.arxos/logs/tui.log`
2. **Enable debug mode**: `--debug` flag
3. **Verify configuration**: `./arx config validate`
4. **Test with demo**: `./arx visualize --tui --demo`

### Reporting Issues

When reporting issues, please include:

1. **Configuration**: `./arx config show`
2. **Environment**: `env | grep ARXOS`
3. **Terminal info**: `echo $TERM`
4. **Logs**: Relevant log file excerpts
5. **Steps to reproduce**: Detailed reproduction steps

### Contributing

To contribute to TUI development:

1. **Fork the repository**
2. **Create a feature branch**
3. **Follow Go coding standards**
4. **Add tests for new features**
5. **Update documentation**
6. **Submit a pull request**

## Changelog

### v0.1.0 (Current)

- ✅ Interactive dashboard with real-time updates
- ✅ Building explorer with hierarchical navigation
- ✅ Equipment manager with filtering and sorting
- ✅ Floor plan visualization with ASCII art
- ✅ Spatial query interface with multiple query types
- ✅ Configuration integration with main ArxOS config
- ✅ Environment variable support
- ✅ Theme support (dark/light/auto)
- ✅ Custom equipment symbols
- ✅ Performance optimization options
- ✅ Comprehensive error handling
- ✅ Debug mode and logging

### Future Features

- 🔄 Real-time collaboration
- 🔄 Advanced spatial analysis
- 🔄 Export capabilities (PDF, SVG)
- 🔄 Custom viewport layouts
- 🔄 Plugin system
- 🔄 Keyboard shortcut customization
- 🔄 Mouse support enhancement
- 🔄 Multi-building support
- 🔄 Advanced filtering options
- 🔄 Data visualization charts

---

**ArxOS TUI** - Professional Building Information Modeling in the Terminal
