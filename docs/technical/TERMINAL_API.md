# ArxOS Terminal API

## Overview

ArxOS provides a terminal-based interface for building intelligence queries and operations. All interactions are performed through command-line interfaces, maintaining complete air-gap security.

## Core Commands

### Connection Commands

#### `connect <device>`
Connect to a mesh network node.

**Usage:**
```bash
arx> connect /dev/ttyUSB0
arx> connect bluetooth://meshtastic-001
arx> connect serial://COM3
```

**Parameters:**
- `device`: Connection method and device identifier
  - USB LoRa dongle: `/dev/ttyUSB0` (Linux) or `COM3` (Windows)
  - Bluetooth: `bluetooth://<device-name>`
  - Serial: `serial://<port>`

**Response:**
```
Connected to mesh network
Node ID: 0x0001
Signal: -72 dBm
Neighbors: 3 nodes
```

#### `disconnect`
Disconnect from the current mesh network.

**Usage:**
```bash
arx> disconnect
```

**Response:**
```
Disconnected from mesh network
```

#### `status`
Show current connection and network status.

**Usage:**
```bash
arx> status
```

**Response:**
```
ArxOS Terminal Status
====================
Connected: Yes
Node ID: 0x0001
Signal: -72 dBm
Neighbors: 3 nodes
  - Node 0x0002 (RSSI: -65 dBm, 1 hop)
  - Node 0x0003 (RSSI: -78 dBm, 2 hops)
  - Node 0x0004 (RSSI: -82 dBm, 1 hop)
Last Query: 2.3s ago
```

### Query Commands

#### `query <expression>`
Query building data using ArxOS Query Language (AQL).

**Usage:**
```bash
arx> query "outlets room:205"
arx> query "equipment type:hvac floor:2"
arx> query "emergency exits"
arx> query "circuit B-7"
```

**Query Syntax:**
- `room:<number>` - Filter by room number
- `floor:<number>` - Filter by floor
- `type:<type>` - Filter by equipment type
- `circuit:<id>` - Filter by electrical circuit
- `status:<status>` - Filter by status

**Response:**
```
Query Results: 3 outlets found in room 205
==========================================
Outlet 1: Circuit B-7, Panel 2A, Status: Active
  Position: (1200, 800, 1200) mm
  Properties: 120V, 20A, GFCI
Outlet 2: Circuit B-8, Panel 2A, Status: Active
  Position: (2400, 800, 1200) mm
  Properties: 120V, 20A, Standard
Outlet 3: Circuit B-9, Panel 2A, Status: Active
  Position: (3600, 800, 1200) mm
  Properties: 120V, 20A, Standard
```

#### `scan <room>`
Initiate a room scan (mobile app only).

**Usage:**
```bash
arx> scan room:205
arx> scan current
```

**Response:**
```
Scan initiated for room 205
Switch to LiDAR tab for camera interface
```

### Visualization Commands

#### `visualize <room>`
Display ASCII art visualization of room systems.

**Usage:**
```bash
arx> visualize room:205
arx> visualize floor:2
```

**Response:**
```
Room 205 - Electrical Systems
=============================
┌─────────────────────────────────────┐
│  ⚡     ⚡     ⚡     ⚡     ⚡      │
│  B-7   B-8   B-9   B-10  B-11     │
│                                     │
│  🚪                                 │
│  Door                               │
│                                     │
│  🔮                                 │
│  HVAC                               │
│                                     │
│  ⚡     ⚡     ⚡     ⚡     ⚡      │
│  B-12  B-13  B-14  B-15  B-16     │
└─────────────────────────────────────┘

Legend:
⚡ = Electrical Outlet
🚪 = Door
🔮 = HVAC Unit
```

#### `overlay <system>`
Toggle system overlay in visualization.

**Usage:**
```bash
arx> overlay electrical
arx> overlay hvac
arx> overlay plumbing
arx> overlay all
```

### System Commands

#### `help [command]`
Show help information.

**Usage:**
```bash
arx> help
arx> help query
arx> help connect
```

#### `exit`
Exit the ArxOS terminal.

**Usage:**
```bash
arx> exit
```

## Mobile App Commands

### LiDAR Scanning

#### `scan start`
Start LiDAR scanning (mobile app only).

**Usage:**
```bash
arx> scan start
```

**Response:**
```
LiDAR scanning started
Point camera at building features
Move slowly around the area
```

#### `scan stop`
Stop LiDAR scanning.

**Usage:**
```bash
arx> scan stop
```

**Response:**
```
LiDAR scanning stopped
Processing point cloud data...
ArxObjects generated: 15
Sent to mesh network
```

## Error Handling

### Connection Errors
```
Error: Failed to connect to device
  Device: /dev/ttyUSB0
  Reason: Device not found
  Suggestion: Check USB connection and device permissions
```

### Query Errors
```
Error: Invalid query syntax
  Query: "outlets room:"
  Reason: Missing room number
  Suggestion: Use format "room:<number>"
```

### Network Errors
```
Error: Mesh network timeout
  Reason: No response from nodes
  Suggestion: Check mesh network connectivity
```

## Command History

ArxOS maintains command history for easy navigation:

- `↑` / `↓` - Navigate command history
- `Ctrl+R` - Search command history
- `Ctrl+L` - Clear screen
- `Tab` - Command completion

## Configuration

### Terminal Settings
```bash
# Set terminal preferences
arx> config terminal width 80
arx> config terminal height 24
arx> config colors on
```

### Mesh Settings
```bash
# Configure mesh network
arx> config mesh frequency 915.0
arx> config mesh power 14
arx> config mesh timeout 30
```

## Examples

### Basic Workflow
```bash
# Connect to mesh network
arx> connect /dev/ttyUSB0
Connected to mesh network

# Query building data
arx> query "outlets room:205"
Query Results: 3 outlets found

# Visualize room
arx> visualize room:205
[ASCII art display]

# Check status
arx> status
[Network status]

# Disconnect
arx> disconnect
Disconnected from mesh network
```

### Mobile Workflow
```bash
# Connect via Bluetooth
arx> connect bluetooth://meshtastic-001
Connected to mesh network

# Start LiDAR scan
arx> scan start
LiDAR scanning started

# Stop scan and process
arx> scan stop
ArxObjects generated: 15

# Query scanned data
arx> query "room:205"
Query Results: 15 objects found
```

## Security Notes

- All communication is encrypted
- No internet connectivity required
- Local mesh network only
- Air-gapped architecture
- No data sent to external servers
