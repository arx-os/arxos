# ArxObject Fractal Generation Engine

> **Technical specification for the infinite procedural generation system built into every 13-byte ArxObject**

## Overview

The ArxObject Fractal Generation Engine transforms each 13-byte structure into a seed for infinite procedural content. This enables ArxOS to create a fully explorable terminal-based open world where users can zoom from molecular structure to city-wide systems, all generated deterministically from compact seeds.

## Core Concept: Fractal Seeds

Every ArxObject contains a 4-byte `properties` field that acts as DNA for procedural generation:

```rust
pub struct ArxObject {
    pub building_id: u16,      // Which universe/realm
    pub object_type: u8,        // What it appears to be at this scale
    pub x: i16,                 // Position in mm (signed for relative coords)
    pub y: i16,                 // Position in mm
    pub z: i16,                 // Position in mm
    pub properties: [u8; 4],    // THE FRACTAL SEED
}
```

## Fractal Generation Algorithm

### Seed Generation

```rust
/// Generate deterministic seed from object identity
pub fn fractal_seed(&self) -> u64 {
    let mut seed: u64 = 0;
    seed ^= (self.building_id as u64) << 48;
    seed ^= (self.object_type as u64) << 40;
    seed ^= ((self.x as u32) as u64) << 24;
    seed ^= ((self.y as u32) as u64) << 8;
    seed ^= (self.z as u32) as u64;
    seed ^= (self.properties[0] as u64) << 32;
    seed ^= (self.properties[1] as u64) << 16;
    seed ^= (self.properties[2] as u64) << 8;
    seed ^= self.properties[3] as u64;
    seed
}
```

### Zooming IN: Sub-Object Generation

When exploring inside an object, the engine generates sub-components:

```rust
pub fn generate_contained_object(&self, relative_pos: (i16, i16, i16), scale: f32) -> ArxObject {
    let seed = self.fractal_seed();
    
    // Determine sub-object type based on parent and scale
    let sub_type = match self.object_type {
        OUTLET => match (seed % 3) {
            0 => COMPONENT_TERMINAL,
            1 => COMPONENT_SCREW,
            _ => COMPONENT_HOUSING,
        },
        ELECTRICAL_PANEL => match (seed % 4) {
            0 => CIRCUIT_BREAKER,
            1 => COMPONENT_WIRE,
            2 => COMPONENT_TERMINAL,
            _ => COMPONENT_LABEL,
        },
        _ => GENERIC_COMPONENT,
    };
    
    // Calculate absolute position
    let abs_x = self.x.saturating_add(relative_pos.0);
    let abs_y = self.y.saturating_add(relative_pos.1);
    let abs_z = self.z.saturating_add(relative_pos.2);
    
    // Generate fractal properties for sub-object
    let sub_properties = generate_sub_properties(seed, relative_pos, scale);
    
    ArxObject::with_properties(
        self.building_id,
        sub_type,
        abs_x, abs_y, abs_z,
        sub_properties,
    )
}
```

### Zooming OUT: System Generation

When viewing larger context, the engine generates parent systems:

```rust
pub fn generate_containing_system(&self, scale: f32) -> ArxObject {
    let seed = self.fractal_seed();
    
    // Determine parent system type
    let container_type = match self.object_type {
        OUTLET | LIGHT_SWITCH => ELECTRICAL_PANEL,
        CIRCUIT_BREAKER => ELECTRICAL_ROOM,
        THERMOSTAT | HVAC_VENT => HVAC_SYSTEM,
        LIGHT => LIGHTING_CIRCUIT,
        _ => {
            if scale < 0.1 { BUILDING }
            else if scale < 1.0 { ROOM }
            else { SYSTEM_ASSEMBLY }
        }
    };
    
    // Snap to grid for parent position
    let container_x = (self.x / 1000) * 1000;
    let container_y = (self.y / 1000) * 1000;
    let container_z = (self.z / 500) * 500;
    
    ArxObject::with_properties(
        self.building_id,
        container_type,
        container_x, container_y, container_z,
        generate_container_properties(seed, scale),
    )
}
```

## Scale Levels

### Scale > 10.0: Molecular Detail
At extreme zoom, everything breaks down to base components:
- `COMPONENT_SCREW`: Individual fasteners
- `COMPONENT_WIRE`: Wire segments
- `COMPONENT_MATERIAL`: Raw materials
- `COMPONENT_CONNECTOR`: Joints and connections

### Scale 2.0-10.0: Component Level
Objects reveal their internal structure:
- Outlets show terminals, screws, housing
- Panels show breakers, buses, wiring
- Thermostats show sensors, displays, circuits

### Scale 0.5-2.0: Object Level (Default)
Standard building objects as field workers expect:
- Outlets, switches, lights
- HVAC vents, thermostats
- Doors, windows, walls

### Scale 0.1-0.5: System Level
Objects aggregate into systems:
- Electrical circuits and panels
- HVAC zones and equipment
- Plumbing runs and risers

### Scale < 0.1: Building Level
Entire building as meta-object:
- Statistical summaries
- System counts and capacities
- Overall building intelligence

## Implied Properties Generation

Properties are generated on-demand from object type and seed:

```rust
pub struct ImpliedProperties {
    pub power_requirements: Option<PowerSpec>,
    pub material: MaterialType,
    pub maintenance_interval: Option<u32>, // days
    pub expected_lifespan: Option<u32>,    // years
    pub weight_kg: Option<f32>,
    pub dimensions_mm: Option<(u16, u16, u16)>,
}

impl ImpliedProperties {
    fn from_object(obj: &ArxObject) -> Self {
        match obj.object_type {
            OUTLET => Self {
                power_requirements: Some(PowerSpec { 
                    voltage: 120, 
                    amperage: 15 
                }),
                material: MaterialType::Plastic,
                maintenance_interval: Some(365),
                expected_lifespan: Some(30),
                weight_kg: Some(0.1),
                dimensions_mm: Some((70, 115, 45)),
            },
            ELECTRICAL_PANEL => Self {
                power_requirements: Some(PowerSpec { 
                    voltage: 240, 
                    amperage: 200 
                }),
                material: MaterialType::Metal,
                maintenance_interval: Some(180),
                expected_lifespan: Some(40),
                weight_kg: Some(20.0),
                dimensions_mm: Some((400, 600, 150)),
            },
            // ... more types
        }
    }
}
```

## Terminal World Rendering

The fractal engine enables rich ASCII art worlds:

```
Normal View (Scale 1.0):
╔════════════════════════════════════════╗
║ Room 205 - Classroom                   ║
║                                        ║
║  █████████████████████████████         ║
║  █                           █   ══    ║
║  █    . . . . . . . . . .    █   ╪     ║
║  █    . . . . . . . . . .    █         ║
║  █    . . . . . . . . . .    o━━━━━/   ║
║  █                           █         ║
║  ███████████████████████████████       ║
╚════════════════════════════════════════╝

Zoomed Into Outlet (Scale 5.0):
╔════════════════════════════════════════╗
║ Outlet Interior                        ║
║                                        ║
║     ┌─────────────────────┐            ║
║     │  ⊕  Terminal 1  ⊕   │            ║
║     │                     │            ║
║     │  ═══════════════    │            ║
║     │                     │            ║
║     │  ⊕  Terminal 2  ⊕   │            ║
║     └─────────────────────┘            ║
║            [Ground]                    ║
╚════════════════════════════════════════╝

Zoomed Out to Panel (Scale 0.2):
╔════════════════════════════════════════╗
║ Electrical Panel EP-2A                 ║
║                                        ║
║  [15A][15A][20A][20A][30A][--]         ║
║  [15A][15A][20A][20A][30A][--]         ║
║  [15A][15A][20A][50A][50A][--]         ║
║                                        ║
║  Connected: 27 outlets, 15 lights      ║
║  Load: 67% (134A / 200A)               ║
╚════════════════════════════════════════╝
```

## Performance Considerations

### Deterministic Generation
- Same seed ALWAYS produces same sub-objects
- No randomness - purely deterministic from seed
- Enables caching and prediction

### Memory Efficiency  
- Only 13 bytes stored per object
- Everything else generated on-demand
- No need to store sub-components

### Network Optimization
- Transmit only core 13-byte objects
- Recipients generate detail locally
- Massive bandwidth savings (10,000:1 or more)

## Gaming Applications

The fractal engine enables terminal-based gaming experiences:

1. **Exploration Mode**: Navigate through buildings at any scale
2. **Build Mode**: Place objects that auto-generate sub-components
3. **Repair Mode**: Zoom into equipment to fix at component level
4. **System Mode**: View and optimize entire building systems

## Future Extensions

### Temporal Fractals
- Objects change over time based on seed + timestamp
- Wear patterns emerge from usage
- Predictive maintenance from fractal decay

### Behavioral Fractals
- Objects exhibit behaviors based on seed
- Electrical loads vary by time of day
- HVAC responds to occupancy patterns

### Network Fractals
- Objects form emergent networks
- Power flows through electrical fractals
- Data routes through network fractals

---

*"From 13 bytes, an entire universe unfolds. This is the power of fractal compression."*