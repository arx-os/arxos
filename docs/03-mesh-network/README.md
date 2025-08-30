# Mesh Network Architecture

## Building Intelligence Without Internet

### The Revolutionary Concept

Buildings communicate like a multiplayer game - no central server, no internet required. Each building is a node in a city-wide mesh network, sharing data via packet radio.

```
Traditional:                    Arxos Mesh:
━━━━━━━━━━━━━━━━━━━━━━━━━     ━━━━━━━━━━━━━━━━━━━━━━━━━
Building → Internet → Cloud     Building ←→ Building ←→ Building
    ↓         ↓         ↓            ↕           ↕           ↕
Hackers   Outages    Bills      Building ←→ Building ←→ Building
                                     ↕           ↕           ↕
                                Building ←→ Building ←→ Building

$5000/month for connectivity    $0/month - peer to peer radio
```

### Core Technology Stack

1. **Physical Layer**: LoRa radio (915 MHz ISM band)
2. **Network Layer**: Meshtastic protocol
3. **Application Layer**: ArxObject protocol (13 bytes)
4. **Game Layer**: Player interactions and BILT rewards

### Why Mesh Networks?

| Feature | Traditional Network | Mesh Network |
|---------|-------------------|--------------|
| **Cost** | $5000+ setup, $500/month | $25 per node, $0/month |
| **Security** | Internet exposed | Air-gapped |
| **Reliability** | Single point of failure | Self-healing |
| **Range** | Limited to cable runs | 1-10 km per hop |
| **Setup** | Network engineers | Plug and play |
| **Ownership** | ISP controlled | You own it |

### Network Topology

```
     [Building A]
      /    |    \
     /     |     \
[Shop] [Library] [School]
   |   \   |   /   |
   |    \  |  /    |
[House]  [Park]  [Office]
   |    /  |  \    |
   |   /   |   \   |
[Clinic] [Mall] [Factory]
     \     |     /
      \    |    /
     [Building B]

Each node can route for others
No central authority needed
Data hops building to building
```

### LoRa Radio Specifications

| Parameter | Value | Impact |
|-----------|-------|--------|
| **Frequency** | 915 MHz (US) | Penetrates walls |
| **Power** | 100 mW | 1-10 km range |
| **Data Rate** | 0.3-5.4 kbps | Perfect for ArxObjects |
| **Spreading Factor** | SF7-SF12 | Trade speed for range |
| **Bandwidth** | 125-500 kHz | Adjustable |
| **Encryption** | AES-128 | Secure by default |

### Meshtastic Integration

Arxos leverages Meshtastic for mesh networking:

```python
# Meshtastic handles:
- Mesh routing algorithms
- Encryption/decryption
- Packet acknowledgments
- Automatic retries
- Node discovery
- Channel management

# Arxos adds:
- 13-byte ArxObject protocol
- Building-specific routing
- BILT token distribution
- Game mechanics
- Terminal interface
```

### Packet Flow Example

```
1. Player updates outlet in Building A
   ArxObject: {0x0601, 0x10, ...} (13 bytes)
   
2. Meshtastic wraps in mesh packet
   [Source][Dest][Hop][ArxObject] (19 bytes total)
   
3. Radio transmits at 915 MHz
   Time: 152 ms at SF7 (fast mode)
   
4. Building B receives and routes
   Checks: Is this for me? No → forward
   
5. Building C receives target packet
   Unwraps ArxObject, updates cache
   
6. Player in Building C sees update
   Terminal shows: "Outlet 0x0601 updated"
   
Total time: ~500 ms across 3 buildings
```

### Range and Coverage

#### Single Node Range
```
Open air:        10+ km
Urban:           1-3 km  
Inside building: 100-300m
Through floors:  3-5 floors

With external antenna:
Open air:        50+ km
Urban:           5-10 km
```

#### Mesh Extension
```
Direct range:     1 km
1 hop:           2 km
2 hops:          3 km
3 hops:          4 km
...
10 hops:         11 km (entire city)

Each building extends the network!
```

### Bandwidth Management

At 1 kbps sustained rate:

```
Per Second:
- 7 full ArxObject updates
- 25 delta updates
- 100 cached queries

Per Minute:
- 420 object updates
- Entire building state

Per Hour:
- 25,200 updates
- Multiple building syncs
```

### Channel Allocation

```
Channel 0: Building Operations (primary)
  - ArxObject updates
  - Control commands
  - Status queries
  
Channel 1: Player Chat (secondary)
  - Team coordination
  - Discovery announcements
  - BILT transactions
  
Channel 2: Emergency (priority)
  - Fire/safety alerts
  - System failures
  - Evacuation commands
  
Channel 3: Maintenance (background)
  - Firmware updates
  - Diagnostics
  - Network management
```

### Security Layers

1. **Physical Security**
   - Limited radio range
   - Directional antennas possible
   - Physical access indicators

2. **Encryption**
   - AES-128 at minimum
   - Per-channel keys
   - Rolling codes for commands

3. **Authentication**
   - Node whitelisting
   - Player credentials
   - Building ownership proof

4. **Air Gap**
   - No internet connection
   - No remote access
   - No cloud dependency

### Mesh Network Gaming

#### Discovery Mechanics
```bash
# Player enters new area
"Discovering nearby buildings..."
"Found 3 buildings in range:"
"  - Office Complex (247 objects, 5 players online)"
"  - Shopping Mall (892 objects, 12 players online)"  
"  - School (421 objects, 3 players online)"
"Join which building? [1-3]"

# Player joins building mesh
"Syncing with Office Complex..."
"Downloaded 247 objects (3.2 KB)"
"You earned 50 BILT for joining!"
```

#### Collaborative Mapping
```bash
# Multiple players map same building
Player1: "Mapping electrical panel..."
Player2: "Found unmapped storage room!"
Player3: "Updating HVAC zones..."

# All updates flow through mesh
# Everyone sees real-time progress
# BILT rewards split among contributors
```

### Network Resilience

```
Normal Operation:
A ←→ B ←→ C ←→ D

Node B fails:
A ←→ X   X ←→ C ←→ D
    ↓       ↑
    E ←→ F ←→

Automatic rerouting:
A ←→ E ←→ F ←→ C ←→ D

No data lost!
No manual intervention!
```

### City-Wide Mesh Benefits

1. **Disaster Communication**
   - Works when cell towers fail
   - Building status across city
   - Emergency coordination

2. **Energy Coordination**
   - Load balancing between buildings
   - Demand response without internet
   - Peer-to-peer energy trading

3. **Knowledge Sharing**
   - Solutions propagate automatically
   - Best practices spread virally
   - Community-driven optimization

### Implementation Requirements

```yaml
Minimum Setup:
- 1x ESP32 with LoRa ($25)
- 1x Antenna ($5)
- Power supply ($5)
- Total: $35 per node

Recommended Setup:
- ESP32 + LoRa module
- External antenna
- Weatherproof enclosure
- Battery backup
- Total: $75 per node

Professional Setup:
- High-gain antenna
- Solar power option
- Lightning protection
- Mounting hardware
- Total: $150 per node
```

### Next Steps

- [Meshtastic Integration](meshtastic.md) - Detailed setup
- [Routing Algorithms](routing.md) - How packets find their way
- [Bandwidth Optimization](bandwidth.md) - Making 1 kbps work
- [Security Hardening](security.md) - Protecting the mesh

---

*"Every building a node, every node a gateway to building intelligence"*