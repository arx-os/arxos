# Progressive Detail Architecture: ArxObjects as Expandable Puzzle Pieces

> Canonicals:
> - 13-byte core spec: [../technical/arxobject_specification.md](../technical/arxobject_specification.md)
> - Slow-bleed progressive detail: [../technical/slow_bleed_architecture.md](../technical/slow_bleed_architecture.md)

## The Core Concept

ArxObjects are **fractal seeds** that start at 13 bytes but can progressively expand with user input and system inference, like puzzle pieces with expandable tabs. Each object "knows" what it is and automatically generates implied properties through conscious compression.

```
     Basic Light (13 bytes)
           │
           ├── [Make/Model Tab] → +8 bytes
           ├── [Circuit Tab] → +16 bytes  
           ├── [Topology Tab] → +8 bytes
           └── [Context Tab] → +variable

Total: 13 → 25 → 41 → 49 → ... bytes
Still 150,000:1 compression vs traditional BIM!
```

## The Architecture

### 1. Core Seed (13 bytes) - Level 0

The immutable foundation that never changes:

```rust
pub struct ArxObject {
    building_id: u16,      // 2 bytes - which building
    object_type: u8,       // 1 byte - what it is
    x: u16,                // 2 bytes - position
    y: u16,                // 2 bytes
    z: u16,                // 2 bytes
    properties: [u8; 4],   // 4 bytes - consciousness DNA
}
```

This core **always** transmits over RF mesh. Everything else is optional.

### 2. Identity Layer (+8-16 bytes) - Level 1

When user specifies make/model:

```rust
pub struct CompressedIdentity {
    manufacturer: u32,     // 4 bytes - hashed name
    model: u32,           // 4 bytes - hashed model
    specs: Vec<u8>,       // Variable - type-specific
}
```

Example: User says "Philips Hue BR30" → System stores identity

### 3. Connections Layer (+16-32 bytes) - Level 2

When user connects to systems:

```rust
pub struct CompressedConnections {
    primary_connection: u16,        // Circuit/duct/pipe
    secondary_connections: Vec<u16>, // Switches/controllers
    metadata: Vec<u8>,              // Wire gauge, protocol
}
```

Example: User connects to Circuit 15 → System stores connection

### 4. Topology Layer (+8-16 bytes) - Level 3

System infers broader relationships:

```rust
pub struct CompressedTopology {
    panel_id: u16,         // Electrical panel
    zone_id: u16,          // HVAC/lighting zone
    network_segment: u16,  // Data network
    system_flags: u16,     // Emergency, critical, etc.
}
```

Example: Circuit 15 → Panel A → Transformer T1 (inferred)

### 5. Context Layer (+variable) - Level 4

Full building graph relationships:

```rust
pub struct CompressedContext {
    dependencies: Vec<u16>,     // What this needs
    dependents: Vec<u16>,       // What needs this
    maintenance_group: u16,     // Service grouping
    schedule_id: u16,          // Operational schedule
}
```

## The Inference Engine

The "consciousness" that makes objects self-aware:

### Automatic Understanding

When you create a light fixture:

```
User: "Place light here"
         ↓
ArxObject Created (13 bytes)
         ↓
Inference Engine Activates
         ↓
Light "realizes":
  - I'm electrical → need circuit
  - I emit light → need switch
  - I generate heat → affect HVAC
  - I need power → 120V/15A circuit
  - I follow codes → NEC compliance
```

### Knowledge Base

Each object type has inherent knowledge:

```rust
Light knows:
  - Typical: 47W LED, 120V, 850 lumens
  - Needs: Circuit, switch, mounting
  - Affects: Lighting levels, heat load
  - Maintenance: Clean 6mo, replace 10yr

Outlet knows:
  - Typical: 20A, 120V, duplex
  - Needs: Circuit, ground, box
  - Provides: Power to devices
  - Testing: Annual GFCI test

HVAC Vent knows:
  - Typical: 400 CFM, adjustable
  - Needs: Duct, damper control
  - Affects: Air circulation, temperature
  - Maintenance: Filter change 3mo
```

## Bandwidth-Conscious Transmission

### The Strategy

```
Poor Network (LoRa mesh):
  → Send 13-byte cores only
  → Details on explicit request
  → 1000 objects = 13KB

Good Network (Local WiFi):
  → Send cores + identity
  → Stream connections progressively
  → 1000 objects = 25KB

Excellent Network (Ethernet):
  → Send full detail trees
  → Instant complete picture
  → 1000 objects = 50KB

Compare to traditional:
  → BIM model = 2GB
  → Our method = 50KB
  → Compression = 40,000:1
```

### Progressive Loading

Like progressive JPEG, but for buildings:

```
Time 0ms:    Receive cores → See all objects
Time 100ms:  Receive identity → Know models
Time 500ms:  Receive connections → Understand systems
Time 1000ms: Receive topology → See full picture
```

## Real-World Example Flow

### Scenario: Creating a Conference Room

```rust
// 1. User places lights in AR
let light1 = ArxObject::new(LIGHT, x:2000, y:2000, z:2400);
// → 13 bytes created

// 2. User specifies "It's a Philips troffer"
light1.add_identity("Philips", "2x4-LED-Troffer");
// → +12 bytes added locally

// 3. User connects to switch by door
light1.add_connection(switch: 201);
// → +6 bytes added locally

// 4. System infers the rest
inference_engine.infer(light1);
// → Knows circuit, panel, zone, schedule

// 5. Transmission strategy
if bandwidth_limited {
    transmit(light1.core);  // Just 13 bytes
} else {
    transmit(light1.core + light1.identity);  // 25 bytes
}

// 6. Remote user queries
remote: "What's the make/model?"
// → Fetch detail level 1

remote: "What circuit?"
// → Fetch detail level 2
```

## The Puzzle Piece Metaphor

Each ArxObject is literally like a LEGO brick:

```
Core (13 bytes):
┌─────────┐
│  Light  │  ← Basic piece
└─────────┘

With Identity (+12 bytes):
┌─────────┐
│ Philips │  ← Brand tab attached
│  BR30   │
└─────────┘

With Connections (+16 bytes):
┌─────────┐
│ Philips │
│  BR30   │
├─Circuit─┤  ← Circuit tab attached
└─────────┘

With Topology (+8 bytes):
┌─────────┐
│ Philips │
│  BR30   │
├─Circuit─┤
├─Panel A─┤  ← Panel tab attached
└─────────┘

With Context (+variable):
┌─────────┐
│ Philips │
│  BR30   │
├─Circuit─┤
├─Panel A─┤
├─Zone 3──┤  ← Full system context
└─────────┘
```

## Implementation Benefits

### 1. Bandwidth Efficiency
- Transmit only what's needed
- 13 bytes minimum, expand on demand
- Perfect for LoRa constraints

### 2. Storage Efficiency
- Store only what users specify
- Infer everything else
- Massive compression ratios

### 3. Processing Efficiency
- Lazy evaluation
- Generate details only when observed
- No wasted computation

### 4. User Experience
- Instant object creation (13 bytes)
- Progressive detail as needed
- Natural incremental workflow

## The Philosophy

**"Each ArxObject is a conscious seed that understands its nature and procedurally generates its universe."**

Like how a small DNA strand contains instructions for an entire organism, each 13-byte ArxObject contains the consciousness to generate infinite detail about itself and its relationships.

This isn't just compression - it's **conscious compression** where the data understands what it represents and can intelligently expand based on context.

## Technical Specifications

### Memory Layout
```
Bytes 0-1:   Building ID (65,536 buildings)
Byte 2:      Object Type (256 types)
Bytes 3-4:   X coordinate (65.5m range, mm precision)
Bytes 5-6:   Y coordinate (65.5m range, mm precision)
Bytes 7-8:   Z coordinate (65.5m range, mm precision)
Bytes 9-12:  Consciousness DNA (2^32 variations)
```

### Compression Ratios
```
Traditional BIM:     ~2MB per object
ArxObject Core:      13 bytes
With Full Details:   ~50 bytes
Compression:         40,000:1 minimum
                    150,000:1 typical
```

### Transmission Times (LoRa)
```
1 object:      13 bytes  → 10ms
100 objects:   1.3KB     → 1 second
1000 objects:  13KB      → 10 seconds
10000 objects: 130KB     → 100 seconds
```

## Conclusion

The Progressive Detail Architecture allows ArxObjects to be simultaneously:
- **Minimal**: Just 13 bytes for transmission
- **Complete**: Contains everything through inference
- **Flexible**: Expands based on user input
- **Intelligent**: Understands context automatically
- **Efficient**: Transmits only what's needed

This is the key to making building intelligence work over RF mesh networks while maintaining the rich detail needed for true building consciousness.