# AR ASCII Overlay: Reality as a Living Game

> Concept note. For API/commands, see `../technical/TERMINAL_API.md`. For ArxObject spec, see `../technical/arxobject_specification.md`.

## The Complete Workflow

```
[iPhone Camera View of Your Living Room]
         ↓
[LiDAR Depth Scan]
         ↓
[Semantic Object Detection]
         ↓
[ASCII Art Overlay in AR]
         ↓
[Touch/Gesture Interaction]
         ↓
[13-byte Updates over Radio]
```

## What You See Through Your iPhone

### Reality View (Camera)
```
┌──────────────────────────────┐
│                              │
│     [Actual Chair]           │
│                              │
│            [Lamp]            │
│                              │
│   [Table]                    │
│                              │
│                [Plant]       │
└──────────────────────────────┘
```

### AR ASCII Overlay (Transparent)
```
┌──────────────────────────────┐
│                              │
│     ⚔️ SPAWN POINT           │
│     HP: [████░░░░]           │
│            🔥                │
│         BONFIRE              │
│   ⚏ ALTAR                    │
│   Items: 3                   │
│                ♥ +50HP       │
└──────────────────────────────┘
```

### Combined AR View (What User Sees)
```
┌──────────────────────────────┐
│                              │
│   [Chair] + ⚔️ SPAWN POINT   │
│            ↙                 │
│        [Lamp] + 🔥 BONFIRE   │
│                              │
│  [Table] + ⚏ ALTAR (3 items) │
│                              │
│          [Plant] + ♥ HEAL    │
└──────────────────────────────┘
```

## Interaction Modes

### 1. Scan Mode (Default)
- Point iPhone at objects
- See ASCII labels floating above real items
- Depth-aware rendering (closer objects render on top)

### 2. Game Mode (Battle)
When enemies spawn from chair:
```
Reality: [Your actual chair]
Overlay: 
    ⚔️⚔️⚔️
    ☠️ Hollow Lv.5
    ☠️ Hollow Lv.3
    ☠️ Hollow Lv.4
    
    [COMBAT ENGAGED]
    Roll: Swipe
    Attack: Tap
    Block: Hold
```

### 3. Crafting Mode (At table/altar)
```
Reality: [Your table]
Overlay:
    ╔═══════════════╗
    ║  CRAFTING     ║
    ╠═══════════════╣
    ║ 🗡️ + 🔥 = ⚔️🔥 ║
    ║ Sword + Fire  ║
    ║ = Fire Sword  ║
    ╚═══════════════╝
    
    Drag items to combine
```

### 4. Social Mode (Multiplayer)
Other players appear as ASCII avatars:
```
Reality: [Empty space in room]
Overlay:
    @Player2
    [====||--]
    Lv.42 Knight
    
    ⚡@Player3
    [||------]
    Lv.12 Mage
    
    Text Chat:
    Player2: "Boss in kitchen!"
    Player3: "Need healing"
```

## Technical Implementation

### Offline AR Alignment (No Shared Cloud Maps)

Android viewer-only devices can still render AR overlays by aligning to a local coordinate frame without LiDAR:

1. Fiducial Markers (preferred)
   - Place 2–3 printed markers (e.g., AprilTag/ArUco) at known coordinates in building mm-space
   - Detect via camera; solve for pose; map screen projection to ArxObject positions
2. 3-Point Manual Alignment
   - User taps three known reference points in camera view that correspond to known (x,y,z) in mm
   - Solve similarity transform; persist locally for the room
3. IMU + Visual Odometry (drift-managed)
   - Use device IMU + monocular VO to maintain relative pose
   - Periodically re-anchor with fiducials or reference taps

Notes:
- No internet or cloud anchors are used; anchors are local and saved per-room.
- iOS LiDAR path uses depth for faster convergence; Android path relies on fiducials/manual alignment.

### Frame Processing Pipeline (Rust-style pseudocode)
```rust
fn process_ar_frame(camera_frame: &Frame, depth: Option<&DepthMap>, anchors: &Anchors) -> ARFrame {
    // 1) Detect or load objects
    let objects = match depth {
        Some(d) => semantic_detect_from_depth(d),     // iOS LiDAR
        None => anchors.known_objects(),              // Android viewer-only uses anchors
    };

    // 2) Convert to ArxObjects (13 bytes)
    let arxobjects: Vec<ArxObject> = objects.into_iter().map(to_arxobject).collect();

    // 3) Generate ASCII overlays
    let overlays: Vec<AsciiOverlay> = arxobjects
        .iter()
        .map(|obj| AsciiOverlay {
            ascii: generate_ascii(obj),
            screen_xy: anchors.project(obj.position_mm),
        })
        .collect();

    // 4) Composite overlays
    let mut frame = camera_frame.clone();
    for ov in overlays { frame = render_ascii(frame, &ov); }

    // 5) Handle interaction and broadcast minimal updates (13 bytes)
    if let Some(touch) = read_touch() {
        if let Some(obj) = pick_object_at(&arxobjects, touch) {
            interact_with(obj);
            rf_mesh_broadcast(obj); // 13 bytes
        }
    }

    frame
}
```

### ASCII Rendering Styles

#### Distance-based Detail
```
Near (< 1m):
    ╔════════════╗
    ║  BONFIRE   ║
    ║    🔥🔥    ║
    ║  Rest? Y/N ║
    ╚════════════╝

Medium (1-3m):
    [🔥 Bonfire]
    
Far (> 3m):
    🔥
```

#### Health/Status Bars
```
Above creatures:
    Hollow Knight
    HP: [████░░░░░░]
    MP: [██████░░░░]
    ☠️

Above items:
    Healing Fountain
    [████████░░] 80%
    ♥ +50HP
```

#### Environmental Effects
```
Rain (affects whole screen):
    ¦ ¦  ¦   ¦  ¦
     ¦  ¦  ¦ ¦
    ¦   ¦ ¦  ¦ ¦

Fog (distance fade):
    Near:  ████████
    Mid:   ░░░░████
    Far:   ░░░░░░░░
```

## Multiplayer AR Synchronization

### The Magic: 13 Bytes Per Update

When Player 1 lights the lamp/bonfire:
```
Transmission: [01 00 94 88 13 E8 03 E8 03 01 00 00 00]
              └─┘ └─┘ └─┘ └──────────────┘ └─────────┘
               ID Type Pos   Position(mm)   Properties
                        └─> Lamp/Bonfire      └─> Lit=1
```

Player 2's phone receives this and immediately:
1. Updates their AR overlay
2. Shows fire animation
3. Plays bonfire sound
4. All from 13 bytes!

### Gesture Recognition

```
Tap on object → Interact
    Chair: Activate spawn
    Lamp: Light bonfire
    Table: Open crafting
    Plant: Heal

Swipe up → Special action
    Bonfire: Rest
    Altar: Pray
    Door: Open

Pinch → Examine closer
    Shows detailed ASCII art
    
Spread → Area scan
    Shows all objects as ASCII grid
```

## The Revolutionary Aspect

**You're not streaming video or 3D models.**
**You're streaming MEANING.**

Traditional AR multiplayer:
- 5MB per frame × 30fps = 150MB/second
- Requires 5G or WiFi
- Massive server infrastructure

ArxOS AR:
- 13 bytes per change
- Works over packet radio
- Peer-to-peer, no servers
- **11,538,461× more efficient**

This means:
- AR games in subway tunnels
- Multiplayer in wilderness
- Post-disaster gaming networks
- Truly decentralized metaverse

## Example Gameplay Session

```
1. You scan your living room with iPhone
2. It becomes a dungeon level
3. Your chair spawns enemies (ASCII overlaid)
4. You fight them using gestures
5. Your friend joins from across town
6. They see the same enemies (via LoRa radio!)
7. You both fight together in AR
8. Victory updates propagate in 13-byte packets
9. The "dungeon" (your room) is cleared
10. New room unlocked: Your kitchen is next level!
```

## The Future

Imagine entire cities as shared game worlds:
- Every building is a dungeon
- Every park is a battlefield  
- Every coffee shop is a tavern
- All synchronized via packet radio
- All rendered as ASCII art
- All interactive through AR

**Reality becomes the game engine.**
**ASCII becomes the universal language.**
**13 bytes become entire worlds.**

This is Arxos: Turning reality into a living, breathing, shared game world, transmitted through the narrowest possible bandwidth, rendered in the most universal format, and experienced through the simplest possible interface.