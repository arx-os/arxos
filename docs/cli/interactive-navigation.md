# Interactive ASCII-BIM Navigation

## Overview

The Arxos interactive viewer provides real-time navigation through building infrastructure using smooth zoom transitions and Pixatool-inspired ASCII rendering optimizations. Navigate from campus-level views down to individual microcontroller chips with seamless transitions.

## Features

### Smooth Zoom Transitions
- **7 Zoom Levels**: Campus → Building → Floor → Room → Equipment → Component → Chip
- **Cubic Easing**: Natural acceleration and deceleration during transitions
- **Smart Focus**: Automatically centers on nearest object when zooming in
- **Character Set Interpolation**: Smoothly transitions between zoom-appropriate character sets

### Pixatool-Inspired Rendering
- **Edge Detection**: Automatically detects and enhances edges with box-drawing characters
- **Anti-Aliasing**: Smooths sharp transitions between different regions
- **Smart Clustering**: Groups similar density regions for cleaner appearance
- **Contrast Enhancement**: Adjustable contrast boost for better visibility
- **Material Textures**: Specialized character sets for different materials
- **Dithering**: Ordered dithering for smooth gradients

### Real-Time Performance
- **60 FPS Rendering**: Smooth animations at 16ms refresh rate
- **Optimized Canvas Operations**: Efficient character placement and updates
- **C Engine Integration**: Falls back to Go renderer if C engine unavailable

## Interactive Controls

### Navigation
| Key | Action | Description |
|-----|--------|-------------|
| `+` or `=` | Zoom In | Zoom in one level with smooth transition |
| `-` or `_` | Zoom Out | Zoom out one level with smooth transition |
| `0-6` | Direct Zoom | Jump directly to zoom level (0=Campus, 6=Chip) |
| `↑` or `W` | Pan Up | Move viewport upward |
| `↓` or `S` | Pan Down | Move viewport downward |
| `←` or `A` | Pan Left | Move viewport left |
| `→` or `D` | Pan Right | Move viewport right |
| `C` | Center | Center on current path/object |
| `R` | Reset | Reset viewport to default position |

### Search & Commands
| Key | Action | Description |
|-----|--------|-------------|
| `/` | Search Mode | Enter search mode to find objects |
| `:` | Command Mode | Enter command mode for navigation |
| `ESC` | Cancel | Cancel current mode/operation |
| `Enter` | Execute | Execute search or command |

### Display Options
| Key | Action | Description |
|-----|--------|-------------|
| `Space` | Pause/Resume | Toggle animation pause |
| `F` | Fullscreen | Toggle fullscreen mode (platform-specific) |
| `H` or `?` | Help | Show help overlay |
| `Q` or `ESC` | Quit | Exit interactive mode |

## Zoom Levels

### Level 0: Campus (1 char = 100m)
```
╔════════════════════════════════════════╗
║ Path: / │ Zoom: Campus (0)             ║
╠════════════════════════════════════════╣
║                                        ║
║        ▓▓▓▓    ▓▓▓                   ║
║        ▓HQ▓    ▓W2▓                  ║
║        ▓▓▓▓    ▓▓▓                   ║
║                                        ║
║    ░░░░░░░░░░░░░░░░                  ║
║    ░  Parking Lot  ░                  ║
║    ░░░░░░░░░░░░░░░░                  ║
║                                        ║
╚════════════════════════════════════════╝
```

### Level 1: Building (1 char = 10m)
```
╔════════════════════════════════════════╗
║ Path: /hq │ Zoom: Building (1)         ║
╠════════════════════════════════════════╣
║    ╔═══════════════════╗              ║
║    ║  █████████████    ║              ║
║    ║  █ Floor 3   █    ║              ║
║    ║  █████████████    ║              ║
║    ║  █████████████    ║              ║
║    ║  █ Floor 2   █    ║              ║
║    ║  █████████████    ║              ║
║    ║  █████████████    ║              ║
║    ║  █ Floor 1   █    ║              ║
║    ║  █████╬███████    ║              ║
║    ╚═══════════════════╝              ║
╚════════════════════════════════════════╝
```

### Level 2: Floor (1 char = 1m)
```
╔════════════════════════════════════════╗
║ Path: /floors/1 │ Zoom: Floor (2)      ║
╠════════════════════════════════════════╣
║ ┌────────┬────────┬────────┐          ║
║ │ Room   │ Room   │ Room   │          ║
║ │ 101    │ 102    │ 103    │          ║
║ ├────◊───┴───◊────┴────◊───┤          ║
║ │       Corridor            │          ║
║ ├────◊───┬───◊────┬────◊───┤          ║
║ │ Room   │ Room   │ Room   │          ║
║ │ 104    │ 105    │ 106    │          ║
║ └────────┴────────┴────────┘          ║
╚════════════════════════════════════════╝
```

### Level 3: Room (1 char = 1m)
```
╔════════════════════════════════════════╗
║ Path: /floors/1/room-101 │ Zoom: Room  ║
╠════════════════════════════════════════╣
║    ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓               ║
║    ▓┌─────┐  ┌────┐  ▓               ║
║    ▓│Desk │  │File│  ▓               ║
║    ▓└─────┘  └────┘  ▓               ║
║    ▓                  ═               ║
║    ▓  ┌──────────┐   ═ Window        ║
║    ▓  │Conference│   ═               ║
║    ▓  │  Table   │   ▓               ║
║    ▓  └──────────┘   ▓               ║
║    ▓        ◊        ▓               ║
║    ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓               ║
╚════════════════════════════════════════╝
```

### Level 4: Equipment (1 char = 10cm)
```
╔════════════════════════════════════════╗
║ Path: /electrical/panel │ Zoom: Equip  ║
╠════════════════════════════════════════╣
║    ╔═══════════════════════╗          ║
║    ║ MAIN ELECTRICAL PANEL ║          ║
║    ╠═══════════════════════╣          ║
║    ║ [⊡] [⊡] [⊡] [⊡] [⊡] ║          ║
║    ║  20A  20A  20A  30A  30A║          ║
║    ║                         ║          ║
║    ║ [⊡] [⊡] [⊡] [⊡] [⊡] ║          ║
║    ║  20A  20A  15A  15A  50A║          ║
║    ║                         ║          ║
║    ║ [⊡] [⊡] [⊡] [⊡] [⊡] ║          ║
║    ║  20A  20A  20A  20A  20A║          ║
║    ╚═══════════════════════╝          ║
╚════════════════════════════════════════╝
```

### Level 5: Component (1 char = 1cm)
```
╔════════════════════════════════════════╗
║ Path: /electrical/outlet │ Zoom: Comp  ║
╠════════════════════════════════════════╣
║        ┌─────────────┐                ║
║        │   ◉     ◉   │                ║
║        │             │                ║
║        │      ━      │                ║
║        │             │                ║
║        │   ◉     ◉   │                ║
║        └─────────────┘                ║
║         │ │ │   │ │ │                 ║
║         L N G   L N G                 ║
║        120V    120V                   ║
╚════════════════════════════════════════╝
```

### Level 6: Chip (1 char = 1mm)
```
╔════════════════════════════════════════╗
║ Path: /sensors/temp/chip │ Zoom: Chip  ║
╠════════════════════════════════════════╣
║     ∙∙∙∙∙∙∙∙∙∙∙∙∙∙∙∙∙∙∙              ║
║     ∙┌─────────────────┐∙              ║
║     ∙│ • • • • • • • • │∙              ║
║     ∙│ •             • │∙              ║
║     ∙│ • ┌─────────┐ • │∙              ║
║     ∙│ • │ DS18B20 │ • │∙              ║
║     ∙│ • └─────────┘ • │∙              ║
║     ∙│ •             • │∙              ║
║     ∙│ • • • • • • • • │∙              ║
║     ∙└─────────────────┘∙              ║
║     ∙∙∙∙∙∙∙∙∙∙∙∙∙∙∙∙∙∙∙              ║
╚════════════════════════════════════════╝
```

## Command Mode

### Search Commands
```bash
# Search for object by name
/main panel

# Search for object by type
/type:outlet

# Search with wildcards
/room-10*
```

### Navigation Commands
```bash
# Navigate to absolute path
:/electrical/main-panel

# Navigate to relative path
:../circuit-2

# Navigate to floor
:/floors/2
```

## Material Rendering

The Pixatool renderer includes specialized character sets for different materials:

| Material | Characters | Example |
|----------|-----------|---------|
| Concrete | `█ ▓ ▒ ░` | Solid walls |
| Steel | `╬ ╫ ╪ ┼` | Structural beams |
| Glass | `═ ─ ╌ ┈` | Windows |
| Wood | `▓ ≡ ═ ─` | Doors, furniture |
| Brick | `▚ ▞ ▓ █` | Exterior walls |
| Circuit | `─ │ ┼ ●` | Electrical paths |
| Water | `≈ ~ ∽ ∼` | Plumbing |

## Performance Optimization

### Rendering Pipeline
1. **Object Culling**: Only render objects within viewport
2. **Edge Detection**: Identify and enhance edges
3. **Smart Clustering**: Group similar regions
4. **Anti-Aliasing**: Smooth transitions
5. **Contrast Adjustment**: Enhance visibility
6. **Dithering**: Apply texture patterns

### Benchmarks
- Zoom transition: < 2ms
- Full render cycle: < 16ms (60 FPS)
- Edge detection (80x40): < 1ms
- Anti-aliasing pass: < 0.5ms

## Platform-Specific Features

### macOS
- Fullscreen: Uses AppleScript to maximize terminal
- Smooth scrolling with trackpad gestures

### Linux
- Fullscreen: Sends F11 key to terminal
- Raw terminal mode for instant input

### Windows
- Fullscreen: Uses mode command for larger window
- Compatible with Windows Terminal

## Troubleshooting

### Performance Issues
- Disable Pixatool optimizations: Set `UsePixatool: false`
- Reduce refresh rate: Increase `RefreshRate` to 33ms (30 FPS)
- Use smaller viewport: Reduce terminal window size

### Display Issues
- Check terminal supports Unicode box-drawing characters
- Verify terminal font includes required glyphs
- Try different terminal emulator (iTerm2, Alacritty recommended)

### Navigation Problems
- Reset view with `R` key
- Check current path in header
- Use absolute paths for precise navigation

## Examples

### Starting Interactive Mode
```bash
# View current location interactively
arxos view --mode=live

# Start at specific location
arxos view /electrical/main-panel --mode=live

# Start at specific zoom level
arxos view --zoom=4 --mode=live
```

### Navigating to Equipment
```bash
# In interactive mode:
# 1. Press '/' to search
# 2. Type "main panel"
# 3. Press Enter
# 4. View zooms and centers on main panel

# Or use command mode:
# 1. Press ':'
# 2. Type "/electrical/main-panel"
# 3. Press Enter
```

### Exploring Systems
```bash
# Start at floor level
arxos view /floors/1 --mode=live --zoom=2

# Zoom in with '+' to see room details
# Pan with arrow keys to explore
# Press '4' to jump to equipment level
# Press 'C' to center on current object
```

## Related Documentation

- [ASCII-BIM Terminal](../ascii-bim-terminal.md) - Core visualization system
- [Filesystem Navigation](./filesystem-navigation.md) - Unix-style navigation
- [View Command](./commands.md#view) - Static viewing options
- [Terminal Renderer](../api/terminal-renderer.md) - Rendering API