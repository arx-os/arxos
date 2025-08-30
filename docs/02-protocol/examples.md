# Real-World ArxObject Examples

## Actual Packets from the Building Game

### Example Building: Alafia Elementary School

Let's follow a day in the life of ArxObjects at a real school.

### Morning: Lights Turn On

```c
// Maintenance Mike arrives at 6 AM, turns on hallway lights
// Light switch object sends update
{
    0x0201,           // ID: Switch 201 (hallway)
    0x11,             // Type: Light switch
    0x1F40, 0x0BB8,   // Location: (8000, 3000) mm from origin
    0x05C8,           // Z: 1480mm (switch height)
    {15, 0, 100, 1}   // Circuit 15, Toggle, 100% on, Group 1
}
// Transmission time: 0.104 seconds
// BILT earned: Mike gets 5 tokens for manual control
```

### 7 AM: HVAC Startup Sequence

```c
// Thermostat reads cold temperature, starts heating
// Temperature sensor packet
{
    0x0301,           // ID: Sensor 301 (main hallway)
    0x30,             // Type: Temperature sensor
    0x2134, 0x0FA0,   // Location: (8500, 4000) mm
    0x09C4,           // Z: 2500mm (ceiling mount)
    {55, 45, 0x03, 0xE8}  // 15°C, 45% humidity, 1000 PPM CO2
}

// Thermostat response packet
{
    0x0302,           // ID: Thermostat 302
    0x20,             // Type: Thermostat
    0x2134, 0x0FA0,   // Same location as sensor
    0x05DC,           // Z: 1500mm (wall mount)
    {62, 55, 0x10, 45}   // Setpoint 22°C, Current 15°C, Heat mode, 45% humidity
}

// HVAC Tech Sarah configured this last week
// She earned 100 BILT for optimizing the schedule
```

### 8 AM: Students Arrive

```c
// Motion sensors detect arrivals
{
    0x0401,           // ID: Motion sensor (entrance)
    0x31,             // Type: Motion sensor
    0x0000, 0x0FA0,   // Location: (0, 4000) mm - front door
    0x0BB8,           // Z: 3000mm (above door)
    {1, 47, 10, 200}  // Motion detected, 47 people counted, 10 min timeout, high sensitivity
}

// Classroom CO2 levels start rising
{
    0x0501,           // ID: CO2 sensor (Room 201)
    0x32,             // Type: CO2 sensor
    0x3A98, 0x1388,   // Location: (15000, 5000) mm
    0x0960,           // Z: 2400mm
    {0x05, 0xDC, 0x02, 0x01}  // 1500 PPM, Warning level, Rising trend
}

// Teacher Tom notices high CO2 in his terminal
// Opens window, earns 10 BILT for improving air quality
```

### 10 AM: Electrical Load Monitoring

```c
// Computer lab powers up, outlets report load
// Outlet strip in computer lab
{
    0x0601,           // ID: Outlet 601 (computer lab)
    0x10,             // Type: Electrical outlet
    0x4650, 0x1770,   // Location: (18000, 6000) mm
    0x0000,           // Z: 0 (floor level)
    {22, 20, 0xC1, 85}  // Circuit 22, 20A, On+Grounded+Smart, 85% load
}

// Electrical panel sees increased load
{
    0x0001,           // ID: Main panel
    0x13,             // Type: Electrical panel
    0x0000, 0x0000,   // Location: (0, 0) - utility room
    0x0000,           // Z: 0
    {200, 42, 0x00, 67}  // 200A main, 42 circuits, Normal status, 67% load
}

// Facilities Manager Bob gets alert: "High load in computer lab"
// Investigates, finds space heater, earns 50 BILT for preventing overload
```

### Noon: Lunch Room Chaos

```c
// Multiple rapid updates from cafeteria
// Batch packet header
{0x82, 0x00, 0x00, ...}  // Batch start, 10 packets following

// Freezer door opened
{
    0x0701,           // ID: Freezer door
    0x40,             // Type: Door
    0x5DC0, 0x2328,   // Location: (24000, 9000) mm
    0x0000,           // Z: 0
    {1, 0, 2, 0}      // Open, Unlocked, Staff access, Normal
}

// Temperature spike in freezer
{
    0x0702,           // ID: Freezer temp sensor
    0x30,             // Type: Temperature sensor
    0x5DC0, 0x2328,   // Same location
    0x0FA0,           // Z: 4000mm (inside freezer)
    {15, 0, 0, 0}     // -25°C (encoded as 15), 0% humidity
}

// Batch end
{0x83, 0x00, 0x00, ...}

// Kitchen staff gets achievement: "Cold Chain Hero" + 25 BILT
```

### 2 PM: Network Diagnostics

```c
// IT Admin Chris checks mesh network health
{
    0x0801,           // ID: Mesh node (main)
    0x72,             // Type: Meshtastic node
    0x2710, 0x1388,   // Location: (10000, 5000) mm - center of building
    0x0FA0,           // Z: 4000mm (ceiling mount)
    {8, 240, 100, 47}  // 8 peers, Excellent signal (240/255), 100% battery, 47 packets/hour
}

// WiFi access point status
{
    0x0802,           // ID: WiFi AP (library)
    0x70,             // Type: WiFi AP
    0x3E80, 0x1B58,   // Location: (16000, 7000) mm
    0x0BB8,           // Z: 3000mm (ceiling)
    {6, 31, 185, 45}  // Channel 6, 31 clients, -70dBm signal, 45% bandwidth used
}

// Chris earned 500 BILT this week for maintaining 99.9% uptime
```

### 3 PM: After School Discovery

```c
// New player joins! Janitor James downloads Arxos app
// His avatar appears in the building
{
    0x0901,           // ID: Player (James)
    0x7F,             // Type: Player avatar
    0x2134, 0x0BB8,   // Current location in building
    0x0000,           // Z: Ground floor
    {0x60, 5, 0, 12}  // Janitor class, Level 5, 0 BILT today, Company 12
}

// James discovers unmapped storage room!
// Scans with iPhone, creates new room object
{
    0x0A01,           // ID: Storage room (newly discovered)
    0x50,             // Type: Room
    0x6D60, 0x0FA0,   // Location: (28000, 4000) mm
    0x0000,           // Z: Ground floor
    {0, 0, 18, 1}     // Empty, Lights off, 18°C, Poor air quality
}

// Discovery bonus! James earns 100 BILT
// Building map updates for all players
```

### 5 PM: End of Day Optimization

```c
// Building AI notices patterns, suggests optimizations
// Sends summary packet
{
    0x0002,           // ID: Building summary
    0x52,             // Type: Building
    0x0000, 0x0000,   // Origin
    0x0000,           // Z: 0
    {3, 5, 45, 0xA5}  // 3 floors, 5% occupied, 45% power usage, Various alerts
}

// Optimization achieved:
// - 23% energy saved today
// - 92% comfort maintained
// - 15 faults prevented
// Total BILT distributed: 847 tokens to 12 players
```

### Emergency Example: Fire Drill

```c
// Fire alarm triggered - rapid packet burst
// All door locks release simultaneously
{
    0xFFFF,           // BROADCAST to all doors
    0x40,             // Type: Door
    0x0000, 0x0000,   // Any location
    0x0000,           // Any height
    {1, 0, 0, 2}      // Open, Unlocked, Public access, ALARM
}

// All lights turn on for evacuation
{
    0xFFFF,           // BROADCAST to all lights
    0x11,             // Type: Light switch
    0x0000, 0x0000,   // Any location
    0x0000,           // Any height
    {0, 0, 100, 0xFF} // Any circuit, Any type, 100% on, ALL groups
}

// Emergency responders see building state on arrival
// Fire Chief tablet shows all ArxObjects via mesh
```

### Packet Traffic Analysis

```bash
# Terminal view of packet flow
$ arxos monitor --live

[06:00:01] RX: Switch 0x0201 → Lights ON (Mike earned 5 BILT)
[06:00:02] TX: ACK 0x0201
[07:00:00] RX: Sensor 0x0301 → 15°C (Cold!)
[07:00:01] RX: Thermostat 0x0302 → Heating started
[07:00:02] TX: Subscribe 0x0302 (monitoring HVAC)
[08:00:15] RX: Motion 0x0401 → 47 people entered
[08:00:16] RX: CO2 0x0501 → 1500 PPM (High!)
[08:00:20] RX: Window 0x0502 → OPENED (Tom earned 10 BILT)
...
[17:00:00] RX: Building 0x0002 → Daily summary
[17:00:01] TX: Query ALL → Preparing night mode
[17:00:05] RX: Batch 127 objects → Full building state

Daily Statistics:
- Packets transmitted: 3,847
- Bandwidth used: 50.2 KB (vs 1.5 MB traditional)
- Cache hit rate: 96.3%
- BILT tokens earned: 847
- Players active: 12
- New objects mapped: 7
```

### Decoding Packets in Terminal

```bash
# Decode any packet
$ arxos decode 02011114F00BB805C80F00640

Packet Decode:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ID:       0x0201 (Switch in Zone 2)
Type:     0x11 (Light Switch)
Location: X=8000mm, Y=3000mm, Z=1480mm
          (Main hallway, switch height)
Properties:
  [0] Circuit: 15
  [1] Type: Toggle switch
  [2] Level: 100% (fully on)
  [3] Group: 1 (hallway lights)

Building: Alafia Elementary
Player Credit: Mike (Maintenance)
BILT Earned: 5 tokens
```

### Common Packet Sequences

#### Morning Startup
1. Motion detected → Lights on → HVAC starts → CO2 monitoring begins

#### Fault Detection
1. High current → Breaker warning → Outlet identified → Maintenance dispatched

#### Player Discovery
1. New area entered → LiDAR scan → Objects created → BILT rewarded → Map updated

#### Energy Optimization
1. Room empty → Lights dim → HVAC reduces → Outlets standby → Savings calculated

### The Power of 13 Bytes

Every packet tells a story. Every byte has meaning. Every player contributes to the building's intelligence.

Traditional BAS would need 400+ bytes per object and complex protocols. Arxos does it in 13 bytes over packet radio, making building automation accessible to everyone.

---

→ Next: [Mesh Network Documentation](../03-mesh-network/)