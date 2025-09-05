# Temporal ArxObjects Specification

## Overview

Extending the 13-byte ArxObject protocol to handle dynamic, time-based building events while maintaining backward compatibility and compression efficiency.

## Object Type Classification

### Static Objects (0x00 - 0x7F)
Permanent building infrastructure:
```
0x00-0x1F: Electrical (outlets, switches, lights)
0x20-0x3F: HVAC (vents, thermostats, sensors)
0x40-0x5F: Structural (walls, floors, doors, windows)
0x60-0x7F: Safety (alarms, sprinklers, exits)
```

### Temporal Objects (0x80 - 0xFF)
Dynamic, time-based events:
```
0x80-0x9F: Occupancy (presence, movement, activity)
0xA0-0xBF: Environmental (temperature, humidity, air quality)
0xC0-0xDF: Alerts (emergencies, maintenance, security)
0xE0-0xFF: Reserved for future use
```

## Temporal ArxObject Structure

```rust
#[repr(C, packed)]
pub struct TemporalArxObject {
    // Standard ArxObject fields (13 bytes total)
    pub id: u16,           // High bit set indicates temporal
    pub object_type: u8,   // 0x80-0xFF range
    pub x: u16,            // Position in mm
    pub y: u16,            // Position in mm
    pub z: u16,            // Position in mm
    pub properties: [u8; 4], // Type-specific data
}
```

## Temporal Object Types

### 0x80: PERSON_PRESENT
```rust
properties[0]: confidence  // 0-255 detection confidence
properties[1]: source      // 0=CSI, 1=PIR, 2=Manual
properties[2]: reserved
properties[3]: reserved
```

### 0x81: PERSON_WALKING
```rust
properties[0]: velocity_x  // Signed, dm/s (-12.8 to +12.7 m/s)
properties[1]: velocity_y  // Signed, dm/s
properties[2]: confidence  // 0-255
properties[3]: person_count // 1-255 people
```

### 0x82: PERSON_SITTING
```rust
properties[0]: duration_min // Minutes present (0-255)
properties[1]: confidence   // 0-255
properties[2]: chair_id     // Reference to furniture
properties[3]: reserved
```

### 0x83: PERSON_STANDING
```rust
properties[0]: duration_min // Minutes standing
properties[1]: confidence   // 0-255
properties[2]: activity     // 0=still, 1=shifting, 2=gesturing
properties[3]: reserved
```

### 0x84: PERSON_FALLEN
```rust
properties[0]: severity    // 0-255 (higher = more severe)
properties[1]: duration_sec // Seconds on ground
properties[2]: confidence   // 0-255
properties[3]: flags        // Bit 0: motion_after_fall
```

### 0x85: GROUP_DETECTED
```rust
properties[0]: person_count // 2-255 people
properties[1]: density      // People per sq meter × 10
properties[2]: activity     // 0=static, 1=mingling, 2=evacuating
properties[3]: confidence   // 0-255
```

## Temporal ID Assignment

### ID Structure (16 bits)
```
Bit 15: Temporal flag (1 = temporal object)
Bit 14-12: Zone ID (8 zones)
Bit 11-8: Source device (16 devices)
Bit 7-0: Rolling counter (256 unique IDs)
```

Example:
```
0x8A42 = Temporal | Zone 2 | Device 10 | ID 66
```

## Lifecycle Management

### Creation
```rust
fn create_temporal_object(
    detection: &CsiDetection,
    zone: u8,
    device: u8
) -> TemporalArxObject {
    let id = 0x8000 | (zone << 12) | (device << 8) | next_id();
    
    TemporalArxObject {
        id,
        object_type: classify_activity(detection),
        x: detection.x_mm,
        y: detection.y_mm,
        z: detection.z_mm,
        properties: encode_properties(detection),
    }
}
```

### Update
Temporal objects can be updated in place:
```rust
fn update_temporal_object(
    obj: &mut TemporalArxObject,
    new_detection: &CsiDetection
) {
    obj.x = new_detection.x_mm;
    obj.y = new_detection.y_mm;
    // Update velocity in properties
    obj.properties[0] = calculate_velocity_x(obj.x, new_detection.x_mm);
    obj.properties[1] = calculate_velocity_y(obj.y, new_detection.y_mm);
}
```

### Expiration
```rust
const TEMPORAL_TIMEOUT_MS: u32 = 30_000; // 30 seconds

fn expire_temporal_objects(objects: &mut Vec<TemporalArxObject>) {
    objects.retain(|obj| {
        let age = current_time_ms() - obj.last_update;
        age < TEMPORAL_TIMEOUT_MS
    });
}
```

## Mesh Broadcasting

### Priority Levels
```rust
enum BroadcastPriority {
    Emergency = 0,  // Immediate broadcast (falls, intrusions)
    Alert = 1,      // Quick broadcast (unusual activity)
    Update = 2,     // Normal broadcast (position updates)
    Background = 3, // Low priority (statistics)
}
```

### Broadcast Rules
1. Emergency events interrupt all other broadcasts
2. Updates batched every 100ms
3. Duplicate suppression within 1 second
4. Maximum 10 temporal objects per packet

## ASCII Visualization

### Temporal Object Rendering
```
Static Objects:  █ (wall) ▫ (outlet) ◦ (light)
Temporal Objects: @ (standing) ○ (sitting) ~ (walking) X (fallen)

Floor Plan with Temporal Layer:
┌────────────────────────┐
│█████████▫████████████  │
│                    ~→  │  Person walking east
│  ○ ○ ○   @            │  3 sitting, 1 standing
│  ○ ○ ○                 │  Meeting in progress
│                        │
│█████ ████████▫████████│
│     X                  │  FALL DETECTED!
│                        │
└────────────────────────┘
```

## Integration with Static Objects

### Spatial Relationships
Temporal objects reference static objects:
```rust
// Person sitting references chair
temporal_obj.properties[2] = chair_arxobject_id;

// Fall near specific wall
temporal_obj.x = wall_obj.x + 100; // 100mm from wall
```

### Context Enhancement
Static objects provide context for temporal events:
```rust
fn describe_location(temp_obj: &TemporalArxObject) -> String {
    let nearest_static = find_nearest_static_object(temp_obj);
    match nearest_static.object_type {
        DOOR => format!("Person near door {}", nearest_static.id),
        BATHROOM => format!("Activity in bathroom"),
        CONFERENCE => format!("Meeting in conference room"),
        _ => format!("Position ({}, {})", temp_obj.x, temp_obj.y),
    }
}
```

## Privacy Considerations

### No Persistent Identity
Temporal objects have no persistent ID across sessions:
```rust
// BAD: Tracking specific person
person_id: "John_Smith_UUID"

// GOOD: Anonymous temporal reference
person_id: 0x8A42  // Expires after 30 seconds
```

### Aggregation Only
Multiple temporal objects aggregate to statistics:
```rust
fn generate_statistics(objects: &[TemporalArxObject]) -> Statistics {
    Statistics {
        total_occupancy: count_people(objects),
        average_duration: calculate_average_presence(objects),
        peak_hours: find_busy_periods(objects),
        // No individual tracking
    }
}
```

## Performance Metrics

### Memory Usage
```
Static object:   13 bytes × 10,000 objects = 130 KB
Temporal objects: 13 bytes × 100 active = 1.3 KB
Total building model: ~131 KB RAM
```

### Bandwidth Requirements
```
Update rate: 10 Hz per person
Packet size: 13 bytes + 8 byte header = 21 bytes
Per person: 210 bytes/second
100 people: 21 KB/second
LoRa capacity: Sufficient (250 kbps)
```

### Processing Latency
```
CSI collection: 10ms
Classification: 50ms
ArxObject encoding: 1ms
Mesh broadcast: 100ms
Total latency: ~161ms (acceptable for emergency response)
```

## Future Extensions

### Machine Learning Integration
```rust
struct SmartTemporalObject {
    base: TemporalArxObject,
    predictions: Predictions,
}

struct Predictions {
    next_position: (u16, u16),      // Predicted movement
    activity_probability: [u8; 4],   // ML confidence scores
    anomaly_score: u8,               // Unusual behavior detection
}
```

### Temporal Patterns
```rust
struct TemporalPattern {
    weekday_occupancy: [u8; 24],    // Hourly averages
    weekend_occupancy: [u8; 24],
    peak_traffic_zones: Vec<(u16, u16)>,
    evacuation_routes: Vec<Path>,
}
```

## Backward Compatibility

The temporal extension maintains full compatibility:
1. Legacy systems ignore high-bit IDs
2. 13-byte structure unchanged
3. Static objects unaffected
4. Mesh protocol identical

Systems can opt-in to temporal features while maintaining interoperability with static-only deployments.