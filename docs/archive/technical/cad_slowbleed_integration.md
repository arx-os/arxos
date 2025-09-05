---
title: CAD and Slow-Bleed Integration Guide
summary: How ASCII CAD integrates with slow-bleed to render progressively as detail accumulates.
owner: Interfaces Lead
last_updated: 2025-09-04
---
# CAD and Slow-Bleed Integration Guide

> Canonical specs referenced: `slow_bleed_architecture.md` (protocol), `ascii_cad_system.md` (renderer), `arxobject_specification.md` (13-byte). This guide focuses on integration patterns.

## Overview

This document explains how the ASCII CAD system integrates with the slow-bleed protocol to create progressively detailed technical drawings from mesh network data.

## The Integration Architecture

```
┌─────────────────┐     13-byte packets    ┌──────────────────┐
│   Mesh Network  │ ──────────────────────> │ Slow-Bleed Node  │
│  (LoRa/Radio)   │                         │  (Accumulator)   │
└─────────────────┘                         └──────────────────┘
                                                     │
                                            Progressive Detail
                                                     ↓
┌─────────────────┐     Render Commands    ┌──────────────────┐
│   ASCII CAD     │ <────────────────────── │ Progressive      │
│    Renderer     │                         │   Renderer       │
└─────────────────┘                         └──────────────────┘
```

## Data Flow

### 1. Initial Discovery (0-20% Complete)

**Mesh Network Provides:**
- 13-byte ArxObject packet
- Basic position and type

**CAD Display:**
```
[o] 1234 @ (5,3,1)  // Simple marker
```

**Code Example:**
```rust
// In slow_bleed_node.rs
fn process_live_packet(&mut self, packet: MeshPacket) {
    let object = ArxObject::from_packet(&packet);
    self.live_objects.insert(object.id, object);
    
    // Mark as having basic detail
    self.detail_store.get_completeness(object.id).basic = true;
}

// In CAD renderer
if detail_level.completeness() < 0.2 {
    // Render as simple point
    canvas.draw_point(object.position, get_symbol(object.type));
}
```

### 2. Material Properties (20-50% Complete)

**Mesh Network Provides:**
- Material density chunks
- Thermal properties
- Visual properties

**CAD Display:**
```
 ___
|o o|  // Basic ASCII art
|___|
 1234
 Mat: 75%
```

**Integration:**
```rust
// Detail chunks accumulate
fn process_detail_packet(&mut self, packet: MeshPacket) {
    if let Some(chunk) = DetailChunk::from_packet(&packet) {
        match chunk.chunk_type {
            ChunkType::MaterialDensity => {
                self.detail_store.update_material(chunk);
            }
            // ...
        }
    }
}

// CAD uses accumulated detail
fn render_intermediate(&self, object: &ArxObject, detail: &DetailLevel) {
    if detail.material > 0.5 {
        // Show material-appropriate symbol
        let symbol = match object.material_type() {
            Material::Metal => "═",
            Material::Plastic => "─",
            Material::Concrete => "▓",
        };
        self.draw_with_material(object, symbol);
    }
}
```

### 3. System Connections (50-80% Complete)

**Mesh Network Provides:**
- Electrical connections
- HVAC connections
- Network topology

**CAD Display:**
```
 ___
|o o| 120V
|___| Circuit 12
 1234
  │
  └──── To Panel A
```

**Integration:**
```rust
// Connection chunks build graph
struct ConnectionChunk {
    source_id: u16,
    target_id: u16,
    connection_type: ConnectionType,
    properties: [u8; 4],
}

// CAD renders connections
fn render_connections(&mut self, object: &ArxObject, connections: &[Connection]) {
    for conn in connections {
        let path = self.route_connection(object.position, conn.target_position);
        self.draw_line(path, conn.get_line_style());
    }
}
```

### 4. CAD-Level Detail (80-100% Complete)

**Mesh Network Provides:**
- Detailed geometry
- Precise dimensions
- Simulation models
- Predictive analytics

**CAD Display:**
```
╔═══════════════╗
║  ┌─────┐      ║
║  │ 72° │      ║ Current
║  │ ─── │      ║
║  │ 70° │      ║ Setpoint
║  └─────┘      ║
║  [▲] [▼]      ║
╚═══════════════╝
ID: 2A3F | Zone 3
📊 Thermal model: Active
💨 Airflow: Balanced
⚡ Efficiency: 92%
```

**Full Integration:**
```rust
// Complete object with all details
struct CompleteObject {
    base: ArxObject,
    geometry: DetailedGeometry,
    connections: Vec<Connection>,
    history: PerformanceHistory,
    simulation: SimulationModel,
    predictions: Predictions,
}

// CAD renders with full fidelity
fn render_cad_level(&mut self, complete: &CompleteObject) {
    // Draw precise geometry
    self.render_geometry(&complete.geometry);
    
    // Add system connections
    self.render_system_diagram(&complete.connections);
    
    // Overlay analytics
    if self.options.show_analytics {
        self.render_performance_overlay(&complete.history);
    }
    
    // Show predictions
    if self.options.show_predictions {
        self.render_predictions(&complete.predictions);
    }
}
```

## Bandwidth-Aware Rendering

### Progressive Enhancement Strategy

```rust
impl ProgressiveRenderer {
    fn select_render_mode(&self, object: &ArxObject, bandwidth: f32) -> RenderMode {
        let detail = self.detail_store.get_completeness(object.id);
        
        match (detail.completeness(), bandwidth) {
            (c, b) if b < 100.0 => RenderMode::Minimal,      // Very low bandwidth
            (c, _) if c < 0.2 => RenderMode::Basic,          // Just discovered
            (c, _) if c < 0.5 => RenderMode::Intermediate,   // Some detail
            (c, _) if c < 0.8 => RenderMode::Detailed,       // Most detail
            _ => RenderMode::CadLevel,                       // Full detail
        }
    }
}
```

## Real-Time Updates

### Live Data Integration

While detail accumulates slowly, live data updates immediately:

```rust
// Live update (20 times per second allowed)
fn update_live_data(&mut self, object_id: u16, properties: [u8; 4]) {
    if let Some(object) = self.live_objects.get_mut(&object_id) {
        object.properties = properties;
        
        // Update CAD display immediately
        self.cad_renderer.update_live_value(object_id, properties);
    }
}

// CAD shows live values even with partial detail
fn render_with_live_data(&self, object: &ArxObject, detail: &DetailLevel) {
    let base_render = self.get_base_render(object, detail);
    
    // Overlay current live values
    if object.object_type == ObjectType::Thermostat {
        let current_temp = object.properties[0];
        self.overlay_text(&format!("{}°", current_temp), base_render.temp_position);
    }
}
```

## Practical Example: Room Rendering

### Stage 1: Discovery (Hour 0)
```
□ □ □ □ □
□       □
□       □
□ □ □ □ □
Room 205
```

### Stage 2: Components Identified (Hour 6)
```
□ □ □ □ □
□ o   s □  o: outlet
□       □  s: switch
□ t   ○ □  t: thermostat
□ □ D □ □  D: door
Room 205
4 objects mapped
```

### Stage 3: Connections Visible (Day 1)
```
╔═══════════╗
║ o═══════s ║  Circuit 1
║           ║
║ t━━━━━━━○ ║  HVAC Zone
║     D     ║
╚═══════════╝
Room 205
Power: 0.3kW
Temp: 72°F
```

### Stage 4: Full CAD Detail (Week 1)
```
╔═══════════════════════════╗
║ ⊡═══════════════════════⊟ ║ Circuit 1 (15A)
║ │                       │ ║ 
║ │  ┌─────┐              │ ║ VAV-205
║ │  │ 72° │              │ ║ ├─ Supply
║ └──│ ─── │──────────────○ ║ └─ Return
║    │ 70° │                ║
║    └─────┘      ┌────┐    ║ Occupancy: 2
║                 │    │    ║ CO₂: 450ppm
║                 │ ## │    ║ Efficiency: 94%
╚═════════════════╪════╪════╝
                  └────┘
                   Door
              [OCCUPIED]
```

## Memory-Efficient Implementation

### Chunk Prioritization

```rust
impl DetailStore {
    fn prioritize_chunks(&mut self, viewport: &Viewport) {
        // Keep chunks for visible objects
        self.chunks.retain(|&(object_id, _), _| {
            if let Some(object) = self.get_object(object_id) {
                viewport.is_visible(object.position)
            } else {
                false
            }
        });
        
        // Prioritize nearly-complete objects
        for object_id in self.get_nearly_complete(0.7) {
            self.boost_priority(object_id);
        }
    }
}
```

### Rendering Cache

```rust
struct RenderCache {
    rendered_objects: HashMap<(u16, u32), RenderedObject>,  // (id, detail_hash)
    max_cache_size: usize,
}

impl RenderCache {
    fn get_or_render(&mut self, object: &ArxObject, detail: &DetailLevel) -> &RenderedObject {
        let key = (object.id, detail.hash());
        
        if !self.rendered_objects.contains_key(&key) {
            let rendered = self.render_object(object, detail);
            self.rendered_objects.insert(key, rendered);
            self.enforce_cache_limit();
        }
        
        &self.rendered_objects[&key]
    }
}
```

## Configuration

### CAD Display Options

```rust
pub struct CadSlowBleedConfig {
    // Progressive rendering
    pub show_incomplete_objects: bool,
    pub minimum_detail_to_show: f32,  // 0.0 to 1.0
    pub highlight_active_downloads: bool,
    
    // Performance
    pub cache_rendered_objects: bool,
    pub max_cache_mb: usize,
    
    // Visual options
    pub show_detail_percentage: bool,
    pub show_download_progress: bool,
    pub animate_accumulation: bool,
}
```

## Best Practices

1. **Always Show Something**: Even 13 bytes is enough for a basic marker
2. **Indicate Progress**: Show users that detail is accumulating
3. **Cache Aggressively**: Rendering is expensive, cache when possible
4. **Prioritize Viewport**: Focus bandwidth on visible objects
5. **Graceful Degradation**: Never crash on incomplete data

## Conclusion

The integration of ASCII CAD with the slow-bleed protocol creates a unique progressive enhancement system where technical drawings literally "develop" over time like a photograph. This matches the physical reality of building systems - you don't need microsecond updates for infrastructure that changes slowly.

The constraint of 1 kbps mesh networks, rather than limiting us, has led to an innovative approach where patience is rewarded with rich detail, and immediate needs are served with essential data.