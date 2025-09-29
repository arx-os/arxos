# ArxOS TUI Quick Start Guide

## 🚀 Get Started in 5 Minutes

ArxOS Terminal User Interface (TUI) is built on **Clean Architecture principles** with **go-blueprint patterns**, providing a powerful command-line experience for building management with real-time spatial visualizations.

### 1. Prerequisites

```bash
# Ensure you have ArxOS CLI installed
which arx

# Check Go version (1.19+)
go version
```

### 2. Basic Usage

```bash
# Start the interactive dashboard
./arx visualize --tui

# Or use the demo mode (no database required)
./arx visualize --tui --demo
```

### 3. Essential Commands

| Command | Description |
|---------|-------------|
| `./arx visualize --tui` | Interactive dashboard |
| `./arx visualize explorer --tui` | Building explorer |
| `./arx visualize equipment --tui` | Equipment manager |
| `./arx visualize floorplan --tui` | Floor plan view |
| `./arx visualize query --tui` | Spatial queries |

### 4. Quick Navigation

#### Dashboard
- `Tab` - Switch tabs
- `↑↓` - Navigate equipment
- `r` - Refresh data
- `q` - Quit

#### Building Explorer
- `↑↓` - Navigate items
- `Enter` - Drill down
- `Backspace` - Go back
- `q` - Quit

#### Equipment Manager
- `t` - Filter by type
- `s` - Filter by status
- `/` - Search mode
- `r` - Refresh

#### Floor Plan
- `↑↓` - Switch floors
- `g` - Toggle grid
- `+/-` - Zoom
- `q` - Quit

### 5. Configuration

#### Environment Variables (Quick Setup)

```bash
# Enable TUI
export ARXOS_TUI_ENABLED=true

# Set theme
export ARXOS_TUI_THEME=dark

# Adjust performance
export ARXOS_TUI_MAX_EQUIPMENT=500
export ARXOS_TUI_UPDATE_INTERVAL=2s
```

#### Configuration File

Create `~/.arxos/config.json`:

```json
{
  "tui": {
    "enabled": true,
    "theme": "dark",
    "update_interval": "1s",
    "max_equipment_display": 1000,
    "real_time_enabled": true,
    "animations_enabled": true
  }
}
```

### 6. Troubleshooting

#### TUI Won't Start
```bash
# Check if enabled
echo $ARXOS_TUI_ENABLED

# Try demo mode
./arx visualize --tui --demo

# Check terminal support
echo $TERM
```

#### Performance Issues
```bash
# Reduce update frequency
export ARXOS_TUI_UPDATE_INTERVAL=5s

# Disable animations
export ARXOS_TUI_ANIMATIONS=false

# Limit equipment display
export ARXOS_TUI_MAX_EQUIPMENT=100
```

#### Display Problems
```bash
# Try light theme
export ARXOS_TUI_THEME=light

# Use compact mode
export ARXOS_TUI_COMPACT_MODE=true

# Disable mouse support
export ARXOS_TUI_ENABLE_MOUSE=false
```

### 7. Example Workflows

#### Building Inspection
```bash
# 1. Start dashboard for overview
./arx visualize --tui

# 2. Switch to building explorer
# Press 'e' or use: ./arx visualize explorer --tui

# 3. Navigate to specific equipment
# Use ↑↓ and Enter to drill down

# 4. Check equipment status
# Use equipment manager: ./arx visualize equipment --tui
```

#### Floor Plan Analysis
```bash
# 1. Start floor plan view
./arx visualize floorplan --tui

# 2. Navigate floors
# Use ↑↓ to switch between floors

# 3. Toggle grid for measurements
# Press 'g' to show/hide grid

# 4. Zoom for detail
# Use +/- to zoom in/out
```

#### Spatial Queries
```bash
# 1. Start spatial query interface
./arx visualize query --tui

# 2. Select query type
# Use Tab to switch between radius, bbox, floor, type

# 3. Adjust parameters
# Use ←→ to modify values

# 4. Execute query
# Press Enter to run
```

### 8. Pro Tips

#### Performance
- Use `compact_mode=true` for small terminals
- Set `max_equipment_display=100` for large buildings
- Use `update_interval=5s` for remote databases

#### Customization
- Customize equipment symbols in config
- Use environment variables for deployment
- Create custom color schemes

#### Integration
- Use TUI alongside REST API
- Integrate into CI/CD pipelines
- Combine with external tools

### 9. Next Steps

1. **Read the full guide**: [TUI_USER_GUIDE.md](./TUI_USER_GUIDE.md)
2. **Explore examples**: Check `examples/` directory
3. **Configure for your needs**: Customize settings
4. **Join the community**: GitHub discussions

### 10. Need Help?

- **Documentation**: [docs/](./)
- **Examples**: [examples/](../examples/)
- **Issues**: GitHub Issues
- **Discussions**: GitHub Discussions

---

**Ready to explore your building data?** Start with:

```bash
./arx visualize --tui --demo
```
