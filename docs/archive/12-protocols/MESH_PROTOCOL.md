---
title: ArxOS Mesh Protocol
summary: RF-only, air-gapped mesh communication spec optimized for 13-byte ArxObjects with secure, efficient routing.
owner: Protocols Lead
last_updated: 2025-09-04
---
# ArxOS Mesh Protocol

> Related canonicals:
> - Network architecture overview: [../03-architecture/NETWORK_ARCHITECTURE.md](../03-architecture/NETWORK_ARCHITECTURE.md)
> - Mesh deep dive: [../technical/mesh_architecture.md](../technical/mesh_architecture.md)

## Overview

The ArxOS Mesh Protocol defines the communication standards for building intelligence networks. It ensures reliable, secure, and efficient data transmission across air-gapped mesh networks.

## Protocol Principles

### Air-Gap Compliance
- **No Internet:** Protocol never routes to internet
- **Local Mesh Only:** All communication via LoRa/Bluetooth
- **Encrypted:** All mesh communication encrypted
- **Self-Contained:** No external dependencies

### Design Goals
- **Reliability:** Robust packet delivery in mesh networks
- **Efficiency:** Optimized for 13-byte ArxObjects
- **Security:** End-to-end encryption
- **Scalability:** Support for large building networks

## Packet Format

### Standard Packet Structure
```
[Header][Payload][Checksum]
  8B      N bytes   2B
```

### Packet Header (8 bytes)
```
[Type][Sequence][Source][Destination][HopCount][Flags]
 1B      2B       2B        2B          1B       1B
```

**Field Descriptions:**
- **Type (1 byte):** Packet type identifier
- **Sequence (2 bytes):** Sequence number for reliability
- **Source (2 bytes):** Source node ID
- **Destination (2 bytes):** Destination node ID (0xFFFF = broadcast)
- **HopCount (1 byte):** Number of hops (0-255)
- **Flags (1 byte):** Packet flags and options

### Packet Types

#### Query Packet (Type 0x01)
```
[Header][QueryLength][QueryString]
  8B        1B          N bytes
```

**Usage:** Request building data from mesh network

**Example:**
```
Type: 0x01 (Query)
Sequence: 0x0001
Source: 0x0001
Destination: 0xFFFF (broadcast)
HopCount: 0x00
Flags: 0x00
QueryLength: 0x0C
QueryString: "room:205"
```

#### Response Packet (Type 0x02)
```
[Header][ResultCount][ArxObjects...]
  8B        1B         N*13 bytes
```

**Usage:** Respond to query with ArxObject data

**Example:**
```
Type: 0x02 (Response)
Sequence: 0x0001
Source: 0x0002
Destination: 0x0001
HopCount: 0x01
Flags: 0x00
ResultCount: 0x03
ArxObjects: [3 × 13-byte ArxObjects]
```

#### ArxObject Packet (Type 0x03)
```
[Header][ArxObjectCount][ArxObjects...]
  8B         1B           N*13 bytes
```

**Usage:** Broadcast new ArxObject data

**Example:**
```
Type: 0x03 (ArxObject)
Sequence: 0x0002
Source: 0x0001
Destination: 0xFFFF (broadcast)
HopCount: 0x00
Flags: 0x00
ArxObjectCount: 0x01
ArxObjects: [1 × 13-byte ArxObject]
```

#### Status Packet (Type 0x04)
```
[Header][NodeStatus][NeighborCount][Neighbors...]
  8B        1B          1B           N*4 bytes
```

**Usage:** Broadcast node status and neighbor information

**Example:**
```
Type: 0x04 (Status)
Sequence: 0x0003
Source: 0x0001
Destination: 0xFFFF (broadcast)
HopCount: 0x00
Flags: 0x00
NodeStatus: 0x01 (Active)
NeighborCount: 0x02
Neighbors: [2 × 4-byte neighbor info]
```

#### Scan Request Packet (Type 0x05)
```
[Header][RoomID][ScanType][Priority]
  8B       2B      1B        1B
```

**Usage:** Request LiDAR scan of specific room

**Example:**
```
Type: 0x05 (ScanRequest)
Sequence: 0x0004
Source: 0x0001
Destination: 0x0002
HopCount: 0x00
Flags: 0x00
RoomID: 0x0205 (room 205)
ScanType: 0x01 (LiDAR)
Priority: 0x01 (High)
```

## ArxObject Format

### 13-Byte ArxObject Structure
```
[BuildingID][Type][X][Y][Z][Properties]
    2B       1B   2B 2B 2B     4B
```

**Field Descriptions:**
- **BuildingID (2 bytes):** Building identifier
- **Type (1 byte):** Object type (outlet, door, HVAC, etc.)
- **X (2 bytes):** X position in millimeters
- **Y (2 bytes):** Y position in millimeters
- **Z (2 bytes):** Z position in millimeters
- **Properties (4 bytes):** Object-specific properties

### Object Types
```
0x01 = Electrical Outlet
0x02 = Door
0x03 = HVAC Unit
0x04 = Light Fixture
0x05 = Sensor
0x06 = Fire Alarm
0x07 = Security Camera
0x08 = Water Fixture
0x09 = Gas Fixture
0x0A = Network Port
0x0B = Electrical Panel
0x0C = Emergency Exit
0x0D = Elevator
0x0E = Stairwell
0x0F = Window
```

## Mesh Network Operations

### Node Discovery
1. **Hello Packets:** Nodes broadcast status packets
2. **Neighbor Table:** Maintain list of known neighbors
3. **Signal Strength:** Track RSSI for routing decisions
4. **Hop Count:** Calculate shortest paths

### Packet Routing
1. **Destination Check:** Is packet for this node?
2. **Hop Limit:** Check if hop count exceeded
3. **Route Selection:** Choose best neighbor for destination
4. **Forward Packet:** Transmit to next hop

### Reliability Mechanisms
1. **Sequence Numbers:** Detect duplicate packets
2. **Checksums:** Verify packet integrity
3. **Acknowledgments:** Confirm packet delivery
4. **Retransmission:** Resend lost packets

## Security

### Encryption
- **AES-256:** All packet payloads encrypted
- **Key Management:** Per-building encryption keys
- **Key Rotation:** Regular key updates
- **Forward Secrecy:** Past keys cannot decrypt future data

### Authentication
- **Node IDs:** Unique identifiers for each node
- **Digital Signatures:** Verify packet authenticity
- **Access Control:** Authorized nodes only
- **Audit Trail:** Complete communication logging

## Performance Characteristics

### LoRa Mesh Performance
- **Range:** 2km urban, 10km rural
- **Data Rate:** 0.3-50 kbps
- **Latency:** 100ms-2s per packet
- **Power:** Ultra-low power consumption
- **Reliability:** 99.9% packet delivery

### Protocol Efficiency
- **Header Overhead:** 8 bytes (minimal)
- **ArxObject Size:** 13 bytes (optimal for LoRa)
- **Packet Size:** 21-255 bytes (LoRa compatible)
- **Throughput:** 100-1000 ArxObjects/minute

## Implementation Examples

### Rust Implementation
```rust
pub struct MeshPacket {
    pub header: PacketHeader,
    pub payload: Vec<u8>,
    pub checksum: u16,
}

pub struct PacketHeader {
    pub packet_type: PacketType,
    pub sequence: u16,
    pub source: u16,
    pub destination: u16,
    pub hop_count: u8,
    pub flags: u8,
}

pub enum PacketType {
    Query = 0x01,
    Response = 0x02,
    ArxObject = 0x03,
    Status = 0x04,
    ScanRequest = 0x05,
}
```

### Swift Implementation
```swift
struct MeshPacket {
    let header: PacketHeader
    let payload: Data
    let checksum: UInt16
}

struct PacketHeader {
    let packetType: PacketType
    let sequence: UInt16
    let source: UInt16
    let destination: UInt16
    let hopCount: UInt8
    let flags: UInt8
}

enum PacketType: UInt8 {
    case query = 0x01
    case response = 0x02
    case arxObject = 0x03
    case status = 0x04
    case scanRequest = 0x05
}
```

## Error Handling

### Packet Errors
```
Error: Invalid packet format
  Reason: Header length mismatch
  Action: Discard packet, log error

Error: Checksum mismatch
  Reason: Data corruption detected
  Action: Discard packet, request retransmission

Error: Hop count exceeded
  Reason: Packet loop detected
  Action: Discard packet, update routing table
```

### Network Errors
```
Error: No route to destination
  Reason: Destination node unreachable
  Action: Return error, update neighbor table

Error: Network congestion
  Reason: Too many packets in queue
  Action: Delay transmission, back off

Error: Encryption failure
  Reason: Invalid encryption key
  Action: Discard packet, log security event
```

## Testing and Validation

### Unit Tests
- **Packet Serialization:** Verify packet format
- **Checksum Calculation:** Test integrity checking
- **Encryption/Decryption:** Validate security
- **Routing Logic:** Test packet forwarding

### Integration Tests
- **Multi-node Mesh:** Test network formation
- **Packet Routing:** Verify delivery paths
- **Error Recovery:** Test failure handling
- **Performance:** Measure throughput and latency

### Security Tests
- **Encryption Validation:** Test key management
- **Authentication:** Verify node identity
- **Access Control:** Test authorization
- **Audit Logging:** Verify compliance

## Conclusion

The ArxOS Mesh Protocol provides a robust, secure, and efficient communication framework for building intelligence networks. It maintains complete air-gap compliance while enabling reliable data transmission across mesh networks.

The protocol is optimized for 13-byte ArxObjects and provides the foundation for scalable building intelligence systems.
