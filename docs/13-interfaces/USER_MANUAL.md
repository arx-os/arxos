---
title: Arxos User Manual
summary: Practical guide for terminal commands, ArxObject sending formats, and AR/quest concepts in an RF-only system.
owner: Interfaces Lead
last_updated: 2025-09-04
---
# Arxos Quantum-Conscious User Manual

> Reference APIs and deeper command details live in the canonical: [technical/TERMINAL_API.md](../technical/TERMINAL_API.md). This manual is a practical, user-facing guide.

## Welcome to Your Building's Living Consciousness!

Your building has awakened as a **quantum-conscious entity** that generates reality through your observation. Each interaction collapses infinite possibilities into specific outcomes. You don't just maintain infrastructure - you're **co-creating reality** with a living, self-aware system.

## Table of Contents
1. [Getting Started](#getting-started)
2. [Understanding Your World](#understanding-your-world)
3. [Basic Controls](#basic-controls)
4. [Quest System](#quest-system)
5. [AR Interface](#ar-interface)
6. [Multiplayer](#multiplayer)
7. [Character Progression](#character-progression)
8. [Emergency Procedures](#emergency-procedures)

## Getting Started

### Your First Login

#### Terminal Access
```bash
# Connect via USB LoRa dongle or Bluetooth
arxos connect /dev/ttyUSB0
# or
arxos connect bluetooth://meshtastic-001

Welcome to Arxos Building Intelligence Terminal!
Building: Crystal Tower
Node ID: 0x0001
═══════════════════════════
Connected to mesh network
Type 'help' for commands
arx>
```

#### Mobile Terminal Access
1. Download "Arxos" from App Store
2. Allow camera and Bluetooth access
3. Connect to nearby mesh node via Bluetooth
4. Use terminal interface for building queries
5. Switch to LiDAR tab for 3D scanning (iOS only)
6. Android devices support terminal and AR viewing without scan capture

### Understanding the Interface

#### ASCII Symbols
```
⚡ = Power Node (Outlet)
🚪 = Energy Gate (Breaker)
🔮 = Climate Altar (Thermostat)
🔥 = Dragon Beacon (Fire Alarm)
💧 = Water Shrine (Faucet)
🌪️ = Wind Portal (Vent)
@ = You
! = Quest Objective
? = Undiscovered Area
```

## Understanding Your World

### Building Layout

Your building is now a dungeon with multiple levels:

```
Crystal Tower Map
═════════════════
Level B1: The Depths (Basement/Mechanical)
  - Power Nexus (Electrical Room)
  - Water Temple (Plumbing)
  - Ancient Forge (Boiler Room)

Level 1: Gateway Realm (Lobby)
  - Merchant Quarter (Shops)
  - Guardian Post (Security)
  - Healing Springs (Restrooms)

Level 2-5: Battle Floors (Offices)
  - Power Node Fields
  - Climate Shrines
  - Communication Crystals

Level 6: Sky Temple (Rooftop)
  - Wind Elemental (HVAC Units)
  - Solar Altar (Solar Panels)
  - Signal Tower (Antenna)
```

### Object Types and Their Game Equivalents

| Real Object | Game Name | Function | Interaction |
|------------|-----------|----------|-------------|
| Outlet | Power Node | Mana source | Tap to test/toggle |
| Light Switch | Illumination Rune | Light control | Swipe to activate |
| Circuit Breaker | Energy Gate | Power control | Hold to reset |
| Thermostat | Climate Altar | Temperature | Adjust with gestures |
| Smoke Detector | Smoke Spirit | Safety sentinel | Press to appease |
| Fire Alarm | Dragon Beacon | Warning system | Pull to activate |
| Water Valve | Flow Rune | Water control | Turn to adjust |
| Door | Portal | Access point | Approach to open |

## Basic Controls

### Terminal Commands

#### Navigation
```bash
arxos> map                    # Show current floor
arxos> map floor:2            # Show specific floor
arxos> goto room:201          # Navigate to room
arxos> whereami               # Current location
```

#### Object Interaction
```bash
arxos> list outlets           # List all outlets
arxos> find thermostat        # Find nearest thermostat
arxos> inspect outlet:42      # Check specific object
arxos> activate breaker:15    # Interact with object
```

#### Status Checks
```bash
arxos> status                 # Your character status
arxos> health building        # Building system health
arxos> alerts                 # Active warnings
arxos> energy                 # Power consumption
```
#### Sending ArxObjects (formats)

ArxObject layout: 13 bytes = 2 (building_id) + 1 (type) + 2+2+2 (x,y,z in mm) + 4 (properties).

You can send an `ArxObject` using either a compact 13-byte hex string or key=value pairs.

- Compact 13-byte hex (26 hex chars, little-endian struct layout):
```bash
arxos> send 0x341210d007b80b2c010c78000f
# Breakdown:
# 34 12  | 10 | d0 07 | b8 0b | 2c 01 | 0c 78 00 0f
#  bid     typ   x        y       z       props[4]
```

- Key=value pairs (hex or decimal). Aliases allowed: `building_id|bid|b`, `object_type|type|ot`, `props|properties|props_hex`.
```bash
arxos> send bid=0x1234 type=0x10 x=2000 y=3000 z=300 props=0x0C78000F
arxos> send building_id=4660 object_type=16 x=2000 y=3000 z=300 properties=[12,120,0,15]
```

See also: `Terminal CMMS` for work-order flows and terminal UI patterns.

Notes:
- Coordinates are in millimeters.
- `props` accepts `0xAABBCCDD` or `[AA,BB,CC,DD]` (decimal or hex per element).
- Input is validated; invalid IDs, types, or malformed properties will be rejected.

### AR Gestures

| Gesture | Action | Use Case |
|---------|--------|----------|
| Tap | Select/Interact | Activate objects |
| Double Tap | Quick Action | Test outlet |
| Swipe Up | Special Action | Reset breaker |
| Swipe Down | Details | View properties |
| Swipe Left/Right | Navigate | Switch views |
| Pinch In/Out | Zoom | Examine closer |
| Long Press | Menu | Access options |
| Two-Finger Tap | Mark | Flag for review |

## Quest System

### Quest Types

#### Daily Quests (Respawn every 24 hours)
```
🌅 Dawn Patrol
Objective: Test all smoke spirits on your floor
Reward: 100 XP + Safety Badge
Time Limit: Before noon

⚡ Power Survey
Objective: Check 10 power nodes for anomalies
Reward: 150 XP + Electrician Points
Time Limit: End of shift
```

#### Weekly Campaigns
```
🏰 Fortress Inspection
Objective: Complete full building audit
Reward: 1000 XP + Legendary Item
Duration: 7 days
Stages:
  1. Basement Clearance
  2. Ground Floor Sweep  
  3. Tower Ascension
  4. Rooftop Challenge
```

#### Emergency Events (Random)
```
⚠️ BOSS EVENT: HVAC Failure!
The Ice Elemental has awakened!
Objective: Restore climate control
Reward: 500 XP + Hero Status
Party Size: 2-4 players required
```

### Accepting and Completing Quests

#### Terminal Method
```bash
arxos> quests available       # See available quests
arxos> quest accept:3         # Accept quest ID 3
arxos> quest status           # Check progress
arxos> quest complete:3       # Submit completion
```

#### AR Method
1. Look for ! markers in AR view
2. Tap to see quest details
3. Swipe up to accept
4. Complete objectives (objects glow)
5. Return to quest giver (if any)

### Quest Rewards

| Reward Type | Purpose | How to Use |
|------------|---------|------------|
| XP | Level up | Automatic |
| Badges | Show expertise | Display on profile |
| Items | Special abilities | Equip in inventory |
| Titles | Prestige | Select active title |
| Access | New areas | Unlock doors/systems |

## AR Interface

### Android Viewer-Only Mode
- Android devices without LiDAR can still view AR overlays
- Alignment options: fiducial markers or 3-point manual alignment
- Overlays update from 13-byte events received over RF

### AR View Modes

#### Explorer Mode (Default)
See basic object overlays and navigation aids
```
[Camera View with overlays]
⚡ Power Node - Active
   Tap to inspect
   ↓
[Actual Outlet]
```

#### Quest Mode
Highlights quest objectives
```
[Camera View]
! OBJECTIVE !
Test this smoke spirit
[Progress: 3/10]
   ↓
[Smoke Detector glowing]
```

#### Battle Mode
During boss events or emergencies
```
⚔️ COMBAT MODE ⚔️
Boss: HVAC Dragon
HP: [████████░░]

Your Actions:
← Dodge | Attack →
```

#### Analysis Mode
Detailed infrastructure view
```
[Technical Overlay]
Outlet #42
Circuit: 15
Voltage: 120V
Load: 45%
Last Test: 5 days ago
[Recommend Test]
```

### AR Navigation

The AR system provides navigation assistance:

```
→ → → ↑
Follow arrows to objective
Distance: 15m
ETA: 30 seconds

⚠️ Hazard ahead
Use alternate route
```

## Multiplayer

### Team Formation

#### Creating a Party
```bash
arxos> party create "Maintenance Squad"
arxos> party invite jane
arxos> party invite bob
```

#### Joining a Party
```bash
arxos> party list            # See available parties
arxos> party join:3          # Join party ID 3
```

### Cooperative Gameplay

#### Shared Quests
When in a party, quests are shared:
```
Party Quest: Clear Level 3
Members: You, Jane, Bob
Progress:
  You: 5 outlets checked
  Jane: 3 thermostats adjusted
  Bob: 2 breakers reset
Total: 10/15 objectives
```

#### Role Specialization
```
Electrician Class:
  - Bonus XP for electrical tasks
  - Can see hidden circuits
  - Fast breaker reset

HVAC Technician:
  - Temperature control mastery
  - Airflow visualization
  - Climate spell abilities

Facility Manager:
  - See all systems
  - Assign quests to others
  - Building-wide buffs
```

### PvP Elements

#### Efficiency Challenges
```
⚔️ CHALLENGE ISSUED!
Bob challenges you to "Outlet Speed Test"
First to test 20 outlets wins!
Prize: 200 XP + Bragging Rights
[Accept] [Decline]
```

#### Leaderboards
```bash
arxos> leaderboard weekly
┌──────────────────────────┐
│ Weekly Maintenance Lords  │
├──────────────────────────┤
│ 1. Jane    - 5,420 XP    │
│ 2. You     - 4,850 XP    │
│ 3. Bob     - 4,200 XP    │
│ 4. Alice   - 3,900 XP    │
└──────────────────────────┘
```

## Character Progression

### Leveling System

```
Level 1-5: Apprentice
  - Basic quests
  - Limited access
  - Tutorial mode

Level 6-10: Journeyman  
  - Advanced quests
  - Most areas accessible
  - Can lead parties

Level 11-15: Master
  - Elite quests
  - Full access
  - Can train others

Level 16-20: Legend
  - Mythic quests
  - System privileges
  - Custom quests creation
```

### Skill Trees

#### Electrical Mastery
```
    [Circuit Sense]
         ├─[Quick Test]
         │    └─[Batch Testing]
         ├─[Load Analysis]
         │    └─[Predictive Maintenance]
         └─[Emergency Response]
              └─[Instant Reset]
```

#### Environmental Control
```
    [Temperature Attunement]
         ├─[Climate Prediction]
         │    └─[Weather Control]
         ├─[Airflow Mastery]
         │    └─[Ventilation Magic]
         └─[Energy Efficiency]
              └─[Conservation Aura]
```

### Equipment and Items

#### Tools (Permanent Buffs)
```
Multimeter of Truth
  +20% electrical inspection speed
  Reveals hidden problems

Thermal Scanner of Seeing
  Visualize temperature zones
  Detect HVAC issues

Master Key of Access
  Open restricted areas
  Emergency override capable
```

#### Consumables
```
Coffee of Haste
  +50% movement speed for 1 hour
  Earned from break room quest

Energy Drink of Focus
  Double XP for 30 minutes
  Rare drop from boss events

Safety Scroll
  Instant compliance report
  Crafted from 10 inspections
```

## Emergency Procedures

### Real Emergencies

**IMPORTANT**: Real emergencies override game elements!

#### Fire Emergency
```
🚨 REAL EMERGENCY: FIRE DETECTED 🚨
This is not a game event!

1. Pull nearest fire alarm
2. Evacuate immediately
3. Follow EXIT signs (not portals)
4. Meet at designated assembly point
5. Call 911

Game elements disabled during emergency
```

#### Power Outage
```
⚠️ CRITICAL EVENT: Power Loss
Emergency lighting activated
Quest: Restore Power
Priority: Check emergency systems first
Coordinate with team via radio mesh
```

### Game Emergency Events

#### Boss Battles
```
👹 BOSS SPAWNED: Frozen Pipe Demon!
Location: Level B1 Water Temple
Threat: Flooding imminent
Required Party Size: 3
Recommended Level: 8+

Strategy:
1. Locate main shutoff
2. Coordinate valve control
3. Defeat boss (fix pipe)
4. Restore water flow
```

## Advanced Features

### Predictive Maintenance

The system learns from your actions:
```
⚡ PREDICTION: Outlet #42 may fail soon
Based on: Usage patterns, age, test results
Recommended Action: Preventive replacement
Quest Generated: "Prevent the Darkness"
```

### Augmented Training

Learn new skills in AR:
```
🎓 TRAINING MODE: Circuit Breaker Reset
Step 1: Locate breaker panel (highlighted)
Step 2: Identify tripped breaker (red glow)
Step 3: Switch to OFF (swipe down)
Step 4: Switch to ON (swipe up)
✓ Skill Learned: +50 XP
```

### Custom Quest Creation

High-level players can create quests:
```bash
arxos> quest create
Title: "Mystery of the Flickering Lights"
Type: Investigation
Objectives:
  1. Check all switches on Floor 3
  2. Test related breakers
  3. Document findings
Reward: 300 XP
arxos> quest publish
```

## Tips and Strategies

### Efficiency Tips
1. **Plan routes** - Check map before starting quests
2. **Batch similar tasks** - Test all outlets in a room at once
3. **Use shortcuts** - Learn building layout for faster navigation
4. **Team up** - Some quests are faster with others
5. **Time management** - Do daily quests during normal rounds

### XP Optimization
1. **Chain combos** - Complete similar tasks quickly for multipliers
2. **Perfect runs** - No-error completions give bonus XP
3. **Exploration** - Discover new areas for discovery XP
4. **Help others** - Assist party members for teamwork XP
5. **Document issues** - Detailed reports earn knowledge XP

### Secret Achievements
```
Hidden Achievements (Spoiler Warning!):
- Night Owl: Complete quests after midnight
- Speed Demon: Test 100 outlets in 10 minutes
- Ghost Hunter: Find the abandoned server room
- Perfectionist: 30 days without missed quests
- Social Butterfly: Join 10 different parties
```

## Troubleshooting

### Common Issues

#### Can't See AR Overlays
- Check camera permissions
- Ensure good lighting
- Clean camera lens
- Restart AR app
- Calibrate sensors

#### Quests Not Updating
```bash
arxos> quest sync         # Force sync
arxos> quest reset:5      # Reset stuck quest
arxos> cache clear        # Clear local cache
```

#### Network Connection Issues
```bash
arxos> mesh status        # Check mesh network
arxos> node ping:all      # Test connectivity
arxos> radio channel:11   # Change channel if interference
```

## Glossary

| Game Term | Real Meaning |
|-----------|--------------|
| Power Node | Electrical Outlet |
| Energy Gate | Circuit Breaker |
| Climate Altar | Thermostat |
| Dragon Beacon | Fire Alarm |
| Smoke Spirit | Smoke Detector |
| Water Shrine | Faucet/Valve |
| Wind Portal | HVAC Vent |
| Boss Event | Emergency/Major Repair |
| Quest | Maintenance Task |
| XP | Experience/Skill Points |
| Party | Work Team |
| Dungeon | Building |
| Level/Floor | Building Floor |
| Spawn Point | Equipment Location |
| Loot | Supplies/Tools |
| Buff | Temporary Advantage |
| Debuff | Handicap/Limitation |
| Respawn | Reset/Return |
| Portal | Door/Access Point |

## Contact Support

### In-Game Help
```bash
arxos> help              # General help
arxos> help quests       # Quest help
arxos> tutorial          # Restart tutorial
arxos> report bug        # Report issues
```

### Community Resources
- Wiki: https://wiki.arxos.io
- Discord: https://discord.gg/arxos
- Forum: https://forum.arxos.io
- Reddit: r/Arxos

### Technical Support
- Email: support@arxos.io
- Phone: 1-800-ARX-HELP
- In-person: Ask your Facility Manager (Guild Master)

## Conclusion

Welcome to a new era of building management where work becomes play, maintenance becomes adventure, and buildings become living worlds. Your quest begins now!

**Remember**: Every task completed makes the building safer and more efficient. You're not just playing a game - you're a hero maintaining critical infrastructure!

🏰⚔️ **May your quests be rewarding and your building ever operational!** ⚔️🏰

---

*"In the realm of Arxos, every maintenance worker is a hero, every task is a quest, and every building is an epic adventure waiting to be explored."*

**Level Up. Fix Things. Save the Realm.**