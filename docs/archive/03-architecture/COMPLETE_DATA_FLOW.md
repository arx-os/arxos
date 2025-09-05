---
title: ArxOS Complete Data Flow Architecture
summary: End-to-end data flow from LiDAR and user input to 13-byte ArxObjects, local storage, mesh distribution, and terminal/AR consumption.
owner: Lead Architecture
last_updated: 2025-09-04
---
# ArxOS Complete Data Flow Architecture

> Canonicals:
> - 13-byte object spec: [../technical/arxobject_specification.md](../technical/arxobject_specification.md)
> - Mesh protocol/architecture: [../12-protocols/MESH_PROTOCOL.md](../12-protocols/MESH_PROTOCOL.md), [../technical/mesh_architecture.md](../technical/mesh_architecture.md)
> - Terminal commands/API: [../technical/TERMINAL_API.md](../technical/TERMINAL_API.md)

## Overview

This document provides the definitive specification for the complete data flow loop in ArxOS, from LiDAR scanning through mesh network distribution to terminal/mobile consumption. This is the core architecture that must be preserved and implemented.

## The Complete Data Flow Loop

```
LiDAR Scan → User Input → ArxObject → Database → Mesh Network → Terminal/Mobile → User Interaction
     ↑                                                                                    ↓
     └────────────────────────────────────────────────────────────────────────────────────┘
```

## Phase 1: Data Creation (LiDAR + User Input)

### 1.1 LiDAR Scanning
```swift
// iOS CameraView.swift - LiDAR scanning process
struct CameraView: View {
    @State private var isScanning = false
    @State private var scanProgress: Double = 0.0
    
    private func processLiDARData(_ result: LiDARScanResult) -> [ArxObject] {
        var arxObjects: [ArxObject] = []
        
        for point in result.points {
            if point.confidence > 0.8 {
                let arxObject = ArxObject(
                    buildingId: 0x0001,
                    objectType: .outlet, // Determined by ML classification
                    x: Int16(point.position.x * 1000), // Convert to mm
                    y: Int16(point.position.y * 1000),
                    z: Int16(point.position.z * 1000),
                    properties: [0x12, 0x34, 0x56, 0x78] // User input details
                )
                arxObjects.append(arxObject)
            }
        }
        return arxObjects
    }
}
```

### 1.2 User Input Integration
```swift
// User adds details through AR interface
func addUserDetails(_ arxObject: ArxObject, details: UserInput) -> ArxObject {
    return ArxObject(
        buildingId: arxObject.buildingId,
        objectType: arxObject.objectType,
        x: arxObject.x,
        y: arxObject.y,
        z: arxObject.z,
        properties: [
            details.circuitNumber,    // 0x12 = Circuit 18
            details.voltage,          // 0x34 = 120V
            details.amperage,         // 0x56 = 20A
            details.status            // 0x78 = ON
        ]
    )
}
```

### 1.3 ArxObject Structure
```rust
// Core 13-byte ArxObject structure
#[repr(C, packed)]
pub struct ArxObject {
    pub building_id: u16,    // Building context
    pub object_type: u8,     // Object type (outlet, door, HVAC, etc.)
    pub x: u16,              // X position in mm
    pub y: u16,              // Y position in mm
    pub z: u16,              // Z position in mm
    pub properties: [u8; 4], // User input details (circuit, voltage, etc.)
}
```

## Phase 2: Data Storage (SQLite Database)

### 2.1 Database Schema
```sql
-- Core ArxObject storage
CREATE TABLE arxobjects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    building_id INTEGER NOT NULL,
    object_type INTEGER NOT NULL,
    x INTEGER NOT NULL,
    y INTEGER NOT NULL,
    z INTEGER NOT NULL,
    properties BLOB NOT NULL,  -- 4-byte property array
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Spatial indexes for fast queries
    INDEX idx_arxobjects_spatial (x, y, z),
    INDEX idx_arxobjects_building (building_id),
    INDEX idx_arxobjects_type (object_type)
);
```

### 2.2 Storage Implementation
```rust
// ArxObject storage in Rust
impl ArxObjectStore {
    pub fn store(&self, obj: &ArxObject) -> Result<ArxObjectId, Box<dyn Error>> {
        let conn = self.pool.get()?;
        
        conn.execute(
            "INSERT OR REPLACE INTO arxobjects 
             (building_id, object_type, x, y, z, properties) 
             VALUES (?1, ?2, ?3, ?4, ?5, ?6)",
            params![
                obj.building_id,
                obj.object_type,
                obj.x,
                obj.y,
                obj.z,
                &obj.properties[..],
            ],
        )?;
        
        Ok(conn.last_insert_rowid() as ArxObjectId)
    }
}
```

## Phase 3: Data Distribution (Mesh Network)

### 3.1 Service Layer Integration
```rust
// ArxOS Service handles mesh distribution
impl ArxOSService {
    async fn handle_mesh_message(&mut self, arxobject: ArxObject) -> Result<()> {
        // Store in database
        self.database.store_arxobject(&arxobject)?;
        
        // Process building intelligence
        self.process_building_intelligence(&arxobject).await?;
        
        // Forward to terminal interface if in interactive mode
        if self.terminal_interface.is_active() {
            self.terminal_interface.display_arxobject(&arxobject).await?;
        }
        
        Ok(())
    }
}
```

### 3.2 Meshtastic Integration
```rust
// Meshtastic client for mesh distribution
impl MeshtasticClient {
    pub async fn send_arxobject(&mut self, arxobject: ArxObject) -> Result<()> {
        // Convert ArxObject to Meshtastic message
        let meshtastic_data = self.protocol_translator.encode_arxobject(arxobject)?;
        
        // Send via serial connection
        if let Some(port) = &mut self.connection {
            port.write_all(&meshtastic_data)?;
            port.flush()?;
        }
        
        Ok(())
    }
}
```

### 3.3 Protocol Translation
```rust
// Convert between ArxOS and Meshtastic protocols
impl ProtocolTranslator {
    pub fn encode_arxobject(&self, arxobject: ArxObject) -> Result<Vec<u8>> {
        // Convert ArxObject to bytes
        let arxobject_bytes = arxobject.to_bytes();
        
        // Create Meshtastic message wrapper
        let meshtastic_message = MeshtasticMessage {
            id: 0, // Will be set by Meshtastic
            payload: arxobject_bytes,
            from: 0, // Will be set by Meshtastic
            to: 0,   // Broadcast
            channel: "arxos".to_string(),
            want_ack: false,
            hop_limit: 3,
            want_response: false,
        };
        
        // Encode as protobuf
        let mut buf = Vec::new();
        meshtastic_message.encode(&mut buf)?;
        
        Ok(buf)
    }
}
```

## Phase 4: Data Consumption (Terminal Interface)

### 4.1 Terminal Query Processing
```rust
// Terminal command execution
impl ArxOSService {
    async fn execute_command(&mut self, command: String) -> Result<()> {
        let parts: Vec<&str> = command.trim().split_whitespace().collect();
        
        match parts[0] {
            "query" => {
                if parts.len() > 1 {
                    let query = parts[1..].join(" ");
                    let results = self.database.query(&query)?;
                    self.terminal_interface.display_query_results(&results).await?;
                }
            }
            "status" => {
                let node_info = self.meshtastic_client.get_node_info().await?;
                self.terminal_interface.display_status(&node_info).await?;
            }
            _ => {
                self.terminal_interface.display_error(&format!("Unknown command: {}", parts[0])).await?;
            }
        }
        
        Ok(())
    }
}
```

### 4.2 ASCII Visualization
```rust
// ASCII rendering for terminal display
impl TerminalInterface {
    pub async fn display_query_results(&self, results: &[ArxObject]) -> Result<()> {
        println!("Query Results ({} objects):", results.len());
        for (i, arxobject) in results.iter().enumerate() {
            println!("  {}: {:?}", i + 1, arxobject);
        }
        Ok(())
    }
    
    pub async fn display_status(&self, node_info: &NodeInfo) -> Result<()> {
        println!("ArxOS Service Status:");
        println!("  Node ID: 0x{:04X}", node_info.node_id);
        println!("  Connected: {}", node_info.is_connected);
        println!("  Port: {}", node_info.port);
        println!("  Baud Rate: {}", node_info.baud_rate);
        Ok(())
    }
}
```

## Phase 5: Data Consumption (Mobile AR Interface)

### 5.1 AR Overlay Generation
```swift
// iOS AR overlay rendering
class ARFrameProcessor {
    func processFrame(cameraFrame: CVPixelBuffer, lidarDepth: ARDepthData) -> ARFrame {
        // 1. Detect objects in 3D space
        let objects = semanticDetect(lidarDepth)
        
        // 2. Convert to ArxObjects (13 bytes each)
        let arxobjects = compressToArxObjects(objects)
        
        // 3. Generate ASCII for each object
        var asciiOverlays: [(String, CGPoint)] = []
        for obj in arxobjects {
            let ascii = generateASCII(obj)
            let position = projectToScreen(obj.position, cameraMatrix)
            asciiOverlays.append((ascii, position))
        }
        
        // 4. Composite ASCII over camera feed
        let arFrame = cameraFrame.copy()
        for (ascii, pos) in asciiOverlays {
            arFrame = renderASCIIAt(arFrame, ascii, pos, transparency: 0.7)
        }
        
        return arFrame
    }
}
```

### 5.2 Distance-Based Rendering
```swift
// Render different detail levels based on distance
func renderObject(_ object: ArxObject, distance: Float) {
    switch distance {
    case 0..<1: // Near - Full detail
        renderFullDetail(object)
    case 1..<5: // Medium - Simplified
        renderSimplified(object)
    case 5..<20: // Far - Icon only
        renderIcon(object)
    default: // Very far - Hidden
        return
    }
}
```

## Phase 6: User Interaction Loop

### 6.1 Terminal Interaction
```bash
# User queries building systems from terminal
arx> query "electrical panel circuit:18"

# ASCII output in terminal
╔════════════════════════════════════════╗
║         ELECTRICAL PANEL 2A            ║
╠════════════════════════════════════════╣
║ Circuit 18: [████████████████████] 20A ║
║ Voltage: 120V                          ║
║ Status: ON                             ║
║ Location: Room 201, (1.5m, 2.0m)      ║
╚════════════════════════════════════════╝
```

### 6.2 Mobile AR Interaction
```swift
// User points iPhone at electrical panel
// AR overlay shows:
╔════════════════════════════════════════╗
║         ⚡ POWER NODE 2A               ║
║    Circuit 18: [████████████████████] ║
║    Energy: 20A @ 120V                  ║
║    Status: ACTIVE                      ║
║    [Tap to toggle] [Swipe for details] ║
╚════════════════════════════════════════╝
```

### 6.3 Gesture Recognition
```swift
// Gesture-based building control
func onARGesture(_ gesture: UIGestureRecognizer, target: ArxObject) {
    switch gesture {
    case .tap:
        // Query object status
        sendMeshQuery(.status, target: target.id)
    case .longPress:
        // Show detailed information
        sendMeshQuery(.details, target: target.id)
    case .swipeUp:
        // Turn on/activate
        sendMeshCommand(.activate, target: target.id)
    case .swipeDown:
        // Turn off/deactivate
        sendMeshCommand(.deactivate, target: target.id)
    }
}
```

## Complete Data Flow Examples

### Example 1: Electrical Panel Mapping
```
1. User scans electrical panel with iPhone LiDAR
2. ArxOS detects panel automatically
3. User adds details: "Circuit 18, 120V, 20A, ON"
4. System creates ArxObject (13 bytes)
5. Stores in local SQLite database
6. Transmits via Meshtastic mesh network
7. Other users see panel in terminal/AR
8. User can query "electrical panel circuit:18"
9. System returns ASCII visualization
10. User can interact via AR gestures
```

### Example 2: HVAC System Mapping
```
1. User scans HVAC vent with iPhone LiDAR
2. ArxOS detects vent automatically
3. User adds details: "Zone 2-1, 200 CFM, Supply"
4. System creates ArxObject (13 bytes)
5. Stores in local SQLite database
6. Transmits via Meshtastic mesh network
7. Facilities manager queries "hvac vents floor:2"
8. System returns ASCII visualization
9. Manager can see all HVAC systems
10. Changes sync to mesh network instantly
```

## Key Architecture Principles

### 1. Single Source of Truth
- The ArxObject database is the single source of truth
- All interfaces (terminal, mobile, AR) read from the same data
- Changes propagate through mesh network instantly

### 2. Universal Data Format
- 13-byte ArxObject works across all interfaces
- Same data structure for storage, transmission, and display
- No format conversion needed between layers

### 3. Progressive Disclosure
- Load building skeleton first (100 bytes)
- Load floor outlines on demand (200 bytes per floor)
- Load room details when needed (150 bytes per room)
- Load specific objects on request (13 bytes each)

### 4. Air-Gapped Operation
- No internet connectivity required
- All communication via LoRa mesh network
- Complete data sovereignty maintained

### 5. Real-Time Synchronization
- Changes propagate through mesh network instantly
- All users see updates in real-time
- No central server required

## Implementation Status

### ✅ Implemented
- ArxObject protocol (13-byte structure)
- SQLite database schema
- Service architecture
- Meshtastic client integration
- Terminal interface framework
- iOS LiDAR scanning

### 🚧 In Progress
- Protocol translation layer
- AR overlay rendering
- Gesture recognition
- Mesh network synchronization

### ❌ Not Started
- Real-time AR rendering
- Advanced gesture recognition
- Multi-user synchronization
- Performance optimization

## Critical Preservation Points

1. **ArxObject Structure**: The 13-byte format must never change
2. **Database Schema**: SQLite schema must remain compatible
3. **Mesh Protocol**: Meshtastic integration must be preserved
4. **Service Architecture**: Service layer separation must be maintained
5. **Air-Gap Compliance**: No internet connectivity at any layer

## Conclusion

This complete data flow architecture is the foundation of ArxOS. It enables:
- **Crowd-sourced building intelligence** through LiDAR scanning
- **Real-time mesh network distribution** via LoRa radio
- **Multiple interface consumption** through terminal and AR
- **Complete air-gapped operation** with no internet dependency
- **Universal data format** that works across all layers

The 13-byte ArxObject is the universal building intelligence format that flows seamlessly from creation to consumption across all interfaces, enabling a truly decentralized building intelligence network.
