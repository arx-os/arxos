# Legacy Documentation

## Lessons from the Go Implementation

### Why This Section Exists

Before pivoting to Rust and mesh networks, Arxos was built in Go with web interfaces. This section preserves valuable lessons learned and explains the evolution of the project.

### The Original Vision (Still Valid)

The core concept remains unchanged:
- Buildings as navigable filesystems
- Terminal-first interface
- Hierarchical object model
- Progressive construction from PDFs
- Open source alternative to proprietary BAS

What changed was the **implementation approach**.

### The Journey

#### Phase 1: Go + Web (Original)
```
Initial approach:
- Go backend with Gin framework
- PostgreSQL database
- React frontend
- SVG rendering
- REST APIs

Problems discovered:
- 400+ byte JSON objects
- Internet dependency
- Complex deployment
- Not suitable for embedded
- Required constant connectivity
```

#### Phase 2: The Bandwidth Realization
```
Key insight:
"What if internet isn't available?"
"What if we only have 1 kbps?"

This led to:
- 13-byte protocol design
- Mesh network architecture
- Terminal-only interface
- ESP32 hardware platform
```

#### Phase 3: Rust + Mesh (Current)
```
Current approach:
- Rust for embedded safety
- LoRa mesh networks
- ASCII terminal rendering
- No internet required
- $25 hardware nodes
```

### Technical Lessons Learned

#### 1. Data Size Matters
```go
// Old: 400+ bytes
type Object struct {
    ID          uuid.UUID      `json:"id"`
    Type        string         `json:"type"`
    Name        string         `json:"name"`
    Location    Location       `json:"location"`
    Properties  PropertyMap    `json:"properties"`
    Metadata    interface{}    `json:"metadata"`
}

// New: 13 bytes
struct ArxObject {
    id: u16,
    object_type: u8,
    x: u16, y: u16, z: u16,
    properties: [u8; 4],
}
```

#### 2. Network Assumptions
```go
// Old: Assumed constant internet
func (c *Client) Sync() error {
    resp, err := http.Post(c.serverURL + "/sync", "application/json", data)
    // What if network is down?
}

// New: Mesh network, works offline
fn transmit(obj: ArxObject) {
    mesh.broadcast(obj.to_bytes());
    // Works without internet
}
```

#### 3. Complexity Creep
```
Old stack:
- Docker containers
- Kubernetes orchestration
- PostgreSQL + Redis
- React + Redux
- OAuth authentication
- WebSocket connections
= Hundreds of dependencies

New stack:
- Single binary
- No database needed
- Terminal interface
- Local-first
- Physical security
= Minimal dependencies
```

### Architectural Insights

#### Building Navigation Metaphor (Preserved)
```bash
# This concept works perfectly
/campus/building-a/floor-2/room-201/outlet-01

# Natural hierarchy
# Filesystem-like navigation
# Git-like operations
```

#### ASCII Rendering (Enhanced)
```
Original: ASCII as fallback
Current: ASCII as primary

Discovered: ASCII is actually better
- Universal compatibility
- Fast rendering
- Low bandwidth
- SSH accessible
- No GPU needed
```

#### Progressive Construction (Refined)
```
Original: Upload PDF → Extract → Model
Current: Scan building → Map → Mesh

The progressive approach remains:
1. Start with topology
2. Add measurements
3. Validate in field
4. Continuous refinement
```

### Migration Path

For those with existing Go deployments:

#### Data Migration
```go
// Export from Go
func ExportToArxos(objects []Object) []ArxObject {
    arxObjects := make([]ArxObject, len(objects))
    for i, obj := range objects {
        arxObjects[i] = ArxObject{
            ID: uint16(obj.ID.ID()),
            Type: mapType(obj.Type),
            X: uint16(obj.Location.X * 1000),
            Y: uint16(obj.Location.Y * 1000),
            Z: uint16(obj.Location.Z * 1000),
            Properties: packProperties(obj.Properties),
        }
    }
    return arxObjects
}
```

#### Gradual Transition
1. Keep Go system running
2. Deploy mesh nodes alongside
3. Bridge data between systems
4. Gradually move to mesh
5. Decommission Go system

### What We Kept

These concepts proved valuable:
- **Building as filesystem**
- **Terminal-first design**
- **Hierarchical addressing**
- **Progressive refinement**
- **PDF extraction pipeline**
- **Git-like operations**
- **Infrastructure as Code**

### What We Dropped

These added complexity without value:
- **Web interfaces** → Terminal only
- **Cloud dependencies** → Local mesh
- **User accounts** → Physical access
- **Databases** → In-memory cache
- **Containers** → Native binaries
- **REST APIs** → Binary protocol
- **SVG rendering** → ASCII art

### Community Contributions

The Go implementation attracted contributors who provided valuable insights:

- **@mikej**: "Why not use LoRa for buildings?"
- **@sarah_k**: "13 bytes is enough for HVAC"
- **@alexm**: "Meshtastic already solved mesh"
- **@chen**: "Rust would be perfect for this"

### Open Source Philosophy

Both implementations share the same philosophy:
- **Open hardware**: Anyone can build nodes
- **Open protocol**: No vendor lock-in
- **Open source**: Complete transparency
- **Open community**: Everyone contributes

### Looking Forward

The journey from Go to Rust taught us:
1. **Constraints drive innovation**
2. **Simpler is better**
3. **Bandwidth is precious**
4. **Terminal interfaces are timeless**
5. **Community knows best**

### Historical Artifacts

Preserved for reference:
- [Go Architecture](go-architecture.md) - Original design
- [Lessons Learned](lessons-learned.md) - Detailed insights
- [Migration Notes](migration-notes.md) - Go to Rust transition

### Credits

Special thanks to early adopters who tested the Go version and provided feedback that led to the mesh revolution.

---

*"We had to build it wrong to learn how to build it right"*