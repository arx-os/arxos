# ASCII Terminal Interface

## Building Visualization Like Minecraft in Terminal

### The Vision

No web browser. No GUI. Just pure ASCII art that shows your building's state in real-time, playable from any terminal.

```
┌──────────────────────────────────────────────────┐
│ ALAFIA ELEMENTARY - FLOOR 2 [LIVE]              │
├──────────────────────────────────────────────────┤
│                                                  │
│  ┌─────┬─────┬─────┐    ┌─────┬─────┬─────┐   │
│  │ 201 │ 202 │ 203 │    │ 204 │ 205 │ 206 │   │
│  │ ●   │ ○   │ ●   │    │ ○   │ ●   │ ○   │   │
│  └─────┴─────┴─────┘    └─────┴─────┴─────┘   │
│  ════════════════════════════════════════════   │
│        Hallway                                  │
│  ┌─────┬─────┬─────┐    ┌─────┬─────┬─────┐   │
│  │ 207 │ 208 │ 209 │    │ 210 │ 211 │ 212 │   │
│  │ ○   │ ○   │ ●   │    │ ●   │ ○   │ ●   │   │
│  └─────┴─────┴─────┘    └─────┴─────┴─────┘   │
│                                                  │
├──────────────────────────────────────────────────┤
│ ● Light On  ○ Light Off  ▣ Panel  ═ Circuit    │
│ Players: 3  BILT Today: 847  Efficiency: 92%   │
└──────────────────────────────────────────────────┘
```

### Why Terminal?

| Feature | Benefit |
|---------|---------|
| **Universal** | Works on any computer |
| **SSH Access** | Remote management |
| **Low Bandwidth** | Perfect for mesh |
| **No Dependencies** | No browser needed |
| **Fast** | Instant rendering |
| **Scriptable** | Automation friendly |

### Zoom Levels (Like Minecraft)

```
Level 1: City View
━━━━━━━━━━━━━━━━━━━
    □ □ □ □ □
    □ ■ □ ■ □    ■ = Your buildings
    □ □ □ □ □    □ = Other buildings
    □ ■ □ □ ■    ~ = Parks/water
    ~ ~ □ □ □

Level 2: Campus View
━━━━━━━━━━━━━━━━━━━━
    ┌───┐ ┌───┐
    │ A │ │ B │   Buildings
    └───┘ └───┘   with labels
    ┌───────┐
    │   C   │     Relative sizes
    └───────┘

Level 3: Building View
━━━━━━━━━━━━━━━━━━━━━
    ╔═══════╗
    ║ FLOOR3 ║
    ╠═══════╣
    ║ FLOOR2 ║
    ╠═══════╣
    ║ FLOOR1 ║
    ╚═══════╝

Level 4: Floor Plan
━━━━━━━━━━━━━━━━━━━
    [Detailed room layout shown above]

Level 5: Room View
━━━━━━━━━━━━━━━━━━━
    ┌─────────────┐
    │   ROOM 201  │
    │ ○──────○    │  Outlets
    │      ☼      │  Light
    │ ○──────○    │
    │      🚪     │  Door
    └─────────────┘

Level 6: Device View
━━━━━━━━━━━━━━━━━━━━
    ┌──────────────┐
    │ OUTLET 0x4A7B│
    │ Circuit: 15  │
    │ Load: 75%    │
    │ Status: ON   │
    └──────────────┘

Level 7: Bit Level
━━━━━━━━━━━━━━━━━━━━
    Raw: 4A 7B 10 14 72 08 66 04 B0 0F 14 01 50
    │    │  │  └─Properties─┘ └─Location─┘
    │    │  └Type
    └─ID─┘
```

### Navigation Commands

```bash
# Like Minecraft creative mode flying
$ arxos navigate

Commands:
  w/s - North/South
  a/d - East/West
  q/e - Up/Down floors
  +/- - Zoom in/out
  TAB - Next object
  ENTER - Select
  / - Search
  m - Map view
  p - Players nearby
  ? - Help
```

### Character Sets

#### Standard ASCII
```
Walls:    ─ │ ┌ ┐ └ ┘ ├ ┤ ┬ ┴ ┼
Doors:    ╬ ╪ ╫
Windows:  ░ ▒ ▓
Electrical: ○ ● ⚡ ▣
HVAC:     ◈ ◊ ☼ ❄ 
Status:   ✓ ✗ ⚠ ⛔
Players:  @ ☺ ☻
```

#### Extended Unicode (Optional)
```
🔌 Outlet
💡 Light
🌡️ Temperature
🚪 Door
👤 Player
🏢 Building
⚡ Power
🔥 Fire alarm
```

### Real-Time Updates

```bash
# Terminal shows live changes
[08:23:14] Room 201: Light ON (Player: Mike)
[08:23:15] Room 202: Motion detected
[08:23:16] HVAC: Temperature 72°F → 71°F
[08:23:17] Outlet 4A7B: Load 45% → 67%
[08:23:18] Player Sarah joined building
[08:23:19] New object discovered: Sensor 0x5C2A
[08:23:20] BILT earned: Mike +5, Sarah +10
```

### Terminal Modes

#### Explorer Mode
```bash
$ arxos explore
# Free navigation through building
# Discover unmapped areas
# Earn BILT for mapping
```

#### Monitor Mode
```bash
$ arxos monitor --room=201
# Focus on specific area
# See all changes
# Alert on thresholds
```

#### Control Mode
```bash
$ arxos control
# Direct device control
# Execute commands
# Verify changes
```

#### Game Mode
```bash
$ arxos game
# Full RPG interface
# Quest system
# Leaderboards
# Guild chat
```

### Performance

| Metric | Value |
|--------|-------|
| Refresh Rate | 10 FPS |
| Latency | <100ms |
| Bandwidth | 1-2 KB/s |
| CPU Usage | <5% |
| Memory | 10 MB |

### Platform Support

Works everywhere:
- Linux terminal
- macOS Terminal.app
- Windows Terminal
- WSL
- SSH clients
- Serial console
- Web terminal (optional)

### Next Steps

- [ASCII Rendering](ascii-rendering.md) - Drawing buildings
- [Zoom Levels](zoom-levels.md) - Multi-scale views
- [Character Sets](character-sets.md) - Symbol reference
- [Navigation](navigation.md) - Movement system

---

*"Graphics cards are for games. Buildings run in terminals."*