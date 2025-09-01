# ArxOS API Reference

## Core Library API

### ArxObject

The fundamental data structure representing any building element.

```rust
use arxos_core::arxobject::ArxObject;

// Create a new ArxObject
let outlet = ArxObject::new(
    0x0001,  // building_id
    0x10,    // object_type (OUTLET)
    1500,    // x position (mm)
    2000,    // y position (mm)
    300,     // z position (mm)
);

// Set properties
outlet.properties = [
    15,   // Circuit number
    120,  // Voltage
    20,   // Amperage
    1,    // Status (powered)
];

// Serialize to bytes
let bytes = outlet.to_bytes(); // Returns [u8; 13]

// Deserialize from bytes
let restored = ArxObject::from_bytes(&bytes);
```

### Object Types

Standard building infrastructure types:

```rust
use arxos_core::arxobject::object_types;

// Electrical
object_types::OUTLET           // 0x10
object_types::LIGHT_SWITCH     // 0x11
object_types::CIRCUIT_BREAKER  // 0x12
object_types::ELECTRICAL_PANEL  // 0x13

// HVAC
object_types::THERMOSTAT       // 0x20
object_types::AIR_VENT         // 0x21
object_types::HVAC_UNIT        // 0x22

// Safety
object_types::FIRE_ALARM       // 0x40
object_types::SMOKE_DETECTOR   // 0x41
object_types::EMERGENCY_EXIT   // 0x42

// Plumbing
object_types::WATER_VALVE      // 0x60
object_types::WATER_METER      // 0x61
object_types::FAUCET           // 0x63

// Structural
object_types::WALL             // 0x54
object_types::FLOOR            // 0x51
object_types::CEILING          // 0x55
object_types::DOOR             // 0x40
object_types::WINDOW           // 0x41
```

### Point Cloud Processing

Convert LiDAR scans to ArxObjects:

```rust
use arxos_core::point_cloud_parser::PointCloudParser;
use arxos_core::point_cloud_parser_enhanced::EnhancedPointCloudParser;

// Basic parser
let parser = PointCloudParser::new();
let cloud = parser.parse_ply("scan.ply")?;
let objects = parser.to_arxobjects(&cloud, building_id);

// Enhanced parser with tunable parameters
let mut parser = EnhancedPointCloudParser::new();
parser.voxel_size = 0.10;  // 10cm voxels
parser.min_points_per_voxel = 3;
let objects = parser.to_arxobjects(&cloud, building_id);

// Presets for different scan types
let dense_parser = EnhancedPointCloudParser::for_dense_scan();
let sparse_parser = EnhancedPointCloudParser::for_sparse_scan();
```

### Progressive Rendering

Render ArxObjects at different detail levels:

```rust
use arxos_core::progressive_renderer::ProgressiveRenderer;
use arxos_core::detail_store::DetailLevel;

let renderer = ProgressiveRenderer::new();

// Create detail level
let detail = DetailLevel {
    basic: true,
    material: 0.5,
    systems: 0.3,
    historical: 0.0,
    simulation: 0.0,
    predictive: 0.0,
};

// Render object
let ascii = renderer.render_object(&arxobject, &detail);

// Render with specific templates
let ascii = renderer.render_outlet(&arxobject);
let ascii = renderer.render_thermostat(&arxobject);
```

### Database Operations

Store and query ArxObjects:

```rust
use arxos_core::database::Database;

// Initialize database
let mut db = Database::new("building.db")?;

// Store objects
db.store_arxobject(&arxobject)?;
db.store_batch(&objects)?;

// Query objects
let outlets = db.query_by_type(object_types::OUTLET)?;
let floor_1 = db.query_by_height(0.0, 3.0)?;
let area = db.query_by_region(x_min, x_max, y_min, y_max)?;

// Update object
arxobject.properties[0] = 0;  // Turn off
db.update_arxobject(&arxobject)?;
```

### Mesh Network Communication

Send ArxObjects over packet radio:

```rust
use arxos_core::mesh_network::MeshNode;

// Initialize mesh node
let mut node = MeshNode::new(node_id, lora_config);

// Broadcast object update
node.broadcast_arxobject(&arxobject).await?;

// Send directed message
node.send_to(target_node_id, &arxobject).await?;

// Receive updates
let update = node.receive().await?;
match update {
    MeshPacket::ObjectUpdate(obj) => {
        // Handle object update
    }
    MeshPacket::QuestAssignment(quest) => {
        // Handle new quest
    }
}
```

## Gamification API

### Quest System

Create and manage maintenance quests:

```rust
use arxos_core::gamification::{Quest, QuestType};

// Create quest
let quest = Quest {
    id: 1,
    quest_type: QuestType::Inspection,
    title: "Appease the Smoke Spirits",
    description: "Test all smoke detectors on Floor 2",
    targets: vec![detector1_id, detector2_id, detector3_id],
    reward_xp: 500,
    time_limit: Some(3600),  // 1 hour
};

// Assign to player
quest_manager.assign(player_id, quest);

// Check progress
let progress = quest_manager.get_progress(player_id, quest.id);
println!("Progress: {}/{}",rogress.completed, progress.total);

// Complete quest
quest_manager.complete(player_id, quest.id)?;
```

### Achievement System

Track player accomplishments:

```rust
use arxos_core::gamification::Achievement;

// Define achievements
let achievement = Achievement {
    id: "monthly_hero",
    name: "Realm Protector",
    description: "Complete monthly inspection",
    xp_reward: 1000,
    badge: "🛡️",
};

// Check if earned
if player.inspections_this_month >= 1 {
    player.award_achievement(achievement);
}
```

## AR Overlay API

### AR Rendering

Overlay game elements on camera feed:

```rust
use arxos_core::ar::{ARRenderer, AROverlay};

let ar_renderer = ARRenderer::new();

// Process camera frame
let frame = camera.capture_frame();
let depth = lidar.get_depth_map();

// Detect objects in view
let visible_objects = ar_renderer.detect_objects(&frame, &depth);

// Generate overlays
let overlays = visible_objects.iter().map(|obj| {
    AROverlay {
        object: obj.clone(),
        ascii: renderer.render_object(obj, &detail),
        position: ar_renderer.project_to_screen(obj.position),
        transparency: 0.7,
    }
}).collect();

// Composite onto frame
let ar_frame = ar_renderer.composite(&frame, &overlays);
```

### Gesture Recognition

Handle AR interactions:

```rust
use arxos_core::ar::{GestureDetector, Gesture};

let detector = GestureDetector::new();

// Process touch input
match detector.detect(&touch_points) {
    Gesture::Tap(position) => {
        let object = ar_renderer.get_object_at(position);
        if let Some(obj) = object {
            interact_with(obj);
        }
    }
    Gesture::Swipe(direction) => {
        // Handle swipe
    }
    Gesture::Pinch(scale) => {
        // Handle zoom
    }
}
```

## Terminal Interface API

### SSH Commands

Available commands in the SSH terminal:

```bash
# Query objects
arxos> list outlets
arxos> find thermostat floor:2
arxos> show object:0x1234

# Building overview
arxos> map floor:1
arxos> stats
arxos> health

# Quest management
arxos> quests active
arxos> quest complete:5
arxos> leaderboard

# System control
arxos> test smoke_detectors
arxos> reset breaker:15
arxos> set thermostat:3 temp:72
```

### Terminal Rendering

ASCII art generation for terminal display:

```rust
use arxos_core::terminal::{TerminalRenderer, ViewMode};

let renderer = TerminalRenderer::new();

// Render floor plan
let floor_plan = renderer.render_floor(&objects, floor_num);

// Render in different modes
let ascii = renderer.render(ViewMode::Map, &objects);
let ascii = renderer.render(ViewMode::List, &objects);
let ascii = renderer.render(ViewMode::Quest, &active_quests);
```

## Hardware Integration API

### ESP32 Firmware

Interface with ESP32 mesh nodes:

```c
#include "arxos.h"

// Initialize ArxOS node
arxos_init(NODE_ID, LORA_FREQ);

// Create ArxObject
ArxObject outlet = {
    .building_id = 0x0001,
    .object_type = TYPE_OUTLET,
    .x = 1500,
    .y = 2000,
    .z = 300,
    .properties = {15, 120, 20, 1}
};

// Broadcast update
arxos_broadcast(&outlet);

// Receive updates
ArxObject received;
if (arxos_receive(&received)) {
    // Process received object
}
```

### LoRa Configuration

Configure packet radio parameters:

```rust
use arxos_core::transport::lora::{LoRaConfig, SpreadingFactor};

let config = LoRaConfig {
    frequency: 915_000_000,  // 915 MHz (US)
    spreading_factor: SpreadingFactor::SF7,
    bandwidth: 125_000,  // 125 kHz
    coding_rate: 5,
    tx_power: 20,  // 20 dBm
    preamble_length: 8,
    sync_word: 0x12,
    crc: true,
};
```

## Error Handling

All API functions return `Result<T, ArxError>`:

```rust
use arxos_core::error::ArxError;

match db.store_arxobject(&obj) {
    Ok(_) => println!("Stored successfully"),
    Err(ArxError::Database(e)) => eprintln!("Database error: {}", e),
    Err(ArxError::Network(e)) => eprintln!("Network error: {}", e),
    Err(ArxError::Validation(e)) => eprintln!("Invalid object: {}", e),
    Err(e) => eprintln!("Unexpected error: {}", e),
}
```

## Performance Guidelines

### Memory Usage
- ArxObject: 13 bytes
- Quest: 64 bytes
- Achievement: 128 bytes
- Floor cache: ~10KB per floor

### Processing Time
- PLY parsing: ~1s per 100k points
- Voxelization: ~100ms per room
- ASCII render: <1ms
- AR overlay: ~16ms per frame

### Network Bandwidth
- Object update: 13 bytes
- Quest assignment: 26 bytes
- Floor sync: ~5KB
- Building sync: ~50KB

## Examples

See the `examples/` directory for complete working examples:
- `ply_to_arxobject_demo.rs` - PLY parsing pipeline
- `fractal_game_streaming.rs` - Progressive rendering
- `lidar_to_game_ar.rs` - Complete AR workflow
- `test_iphone_scan.rs` - iPhone LiDAR processing