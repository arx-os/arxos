# Arxos Deployment Tiers

## Overview

Arxos scales from basic presence detection to real-time activity tracking based on user hardware choices. The same 13-byte ArxObject protocol and software platform support all tiers.

## Tier 1: Presence Detection

### Target Use Cases
- Vacation homes and cabins
- Storage facilities
- Rarely occupied spaces
- Budget-conscious deployments
- Long-range rural coverage

### Hardware Configuration
```yaml
Sensors: PIR motion sensors + door/window contacts
Processing: ESP32 with LoRa
Networking: LoRa mesh (SF12 for long range)
Power: Battery (2-5 year life)
Cost: $50-75 per room
```

### Capabilities
```
Updates: Every 30-60 seconds
Data: Room occupied/vacant
Latency: 5-30 seconds
Privacy: Complete (no identification possible)
Range: 10+ km in rural areas
```

### Example Output
```
Building Status - Updated 14:32
══════════════════════════════════
Living Room:    OCCUPIED (2:30)
Kitchen:        VACANT   (0:45)
Bedroom 1:      OCCUPIED (8:15)
Bedroom 2:      VACANT   (12:30)
Bathroom:       OCCUPIED (0:02)
Garage:         VACANT   (3 days)
```

## Tier 2: Occupancy Counting

### Target Use Cases
- Office buildings
- Schools and universities
- Retail spaces
- Basic emergency response
- HVAC optimization

### Hardware Configuration
```yaml
Sensors: ESP32 WiFi CSI + basic CSI processing
Processing: Raspberry Pi Zero per zone
Networking: LoRa mesh (SF7-9)
Power: USB or PoE
Cost: $150-200 per room
```

### Capabilities
```
Updates: Every 5-15 seconds
Data: Person count + general activity
Latency: 15-60 seconds
Privacy: Anonymous counting only
Range: 1-5 km
```

### Example Output
```
Floor 2 Occupancy - Live
════════════════════════
Conference Room A: 6 people [meeting]
Conference Room B: 0 people [vacant]  
Open Office:      12 people [working]
Kitchen:           3 people [break]
Reception:         1 person  [desk work]

Total Floor: 22 people
Peak Today: 34 people (11:30 AM)
```

## Tier 3: Activity Recognition

### Target Use Cases
- Healthcare facilities
- Senior living communities
- High-security areas
- Advanced building automation
- Comprehensive emergency response

### Hardware Configuration
```yaml
Sensors: Multiple ESP32s + dedicated CSI hardware
Processing: Raspberry Pi 4 per zone
Networking: WiFi backbone + LoRa backup
Power: PoE or hardwired
Cost: $400-600 per room
```

### Capabilities
```
Updates: Every 1-5 seconds
Data: Activity classification + movement patterns
Latency: 2-10 seconds
Privacy: Anonymous activity tracking
Range: Building-wide WiFi coverage
```

### Example Output
```
Patient Wing - Real-time Activity
═══════════════════════════════════
Room 201: 1 person lying down     [normal]
Room 202: 1 person walking        [active] 
Room 203: 0 people                [vacant]
Room 204: 1 person sitting        [stable]
Hallway:  2 people walking north  [staff?]
Nurses:   3 people at station     [shift change]

🟡 Alert: Room 205 - No movement 2+ hours
```

## Tier 4: High-Precision Tracking

### Target Use Cases
- Research facilities
- High-security installations
- Advanced healthcare monitoring
- Real-time emergency response
- Gaming/entertainment venues

### Hardware Configuration
```yaml
Sensors: Industrial CSI arrays + multiple frequencies
Processing: NVIDIA Jetson Nano per zone
Networking: Dedicated WiFi 6 + fiber backbone
Power: Hardwired with UPS backup
Cost: $1500-3000 per room
```

### Capabilities
```
Updates: 10-60 Hz real-time
Data: Precise positioning + gesture recognition
Latency: 50-200 ms
Privacy: Detailed (but still anonymous)
Range: Enterprise-grade coverage
```

### Example Output
```
Security Zone Alpha - Live Tracking (60 Hz)
═══════════════════════════════════════════
│                                          │
│   @  Person 1: (3.2m, 4.1m)            │
│      Velocity: 0.8 m/s northeast        │
│      Activity: Walking                   │
│      Confidence: 97%                     │
│                                          │
│      ○  Person 2: (1.8m, 2.3m)         │
│         Activity: Standing               │
│         Duration: 4:32                   │
│         Posture: Upright                 │
│                                          │
│   ◊  Equipment Cart: (5.1m, 1.2m)      │
│      Status: Stationary                  │
│      Last moved: 0:23 ago                │
│                                          │
└──────────────────────────────────────────┘

Video game quality: ~100ms response time
```

## Tier 5: Enterprise/Research Grade

### Target Use Cases
- Military installations
- Critical infrastructure
- Advanced research facilities
- Maximum capability deployment
- Custom requirements

### Hardware Configuration
```yaml
Sensors: Custom sensor arrays + multiple modalities
Processing: GPU clusters or edge servers
Networking: Dedicated fiber + redundant wireless
Power: Primary + backup + generator
Cost: $10,000+ per zone (custom)
```

### Capabilities
```
Updates: 100+ Hz with prediction
Data: Full environmental awareness
Latency: <50ms with edge computing
Privacy: Configurable (anonymous to detailed)
Range: Campus-wide with redundancy
```

## Migration Paths

### Start Small, Scale Up
```
Year 1: Deploy Tier 1 (basic presence)
Year 2: Upgrade key rooms to Tier 2 (counting)
Year 3: Add Tier 3 for critical areas (activity)
Year 4: Tier 4 for specialized needs (precision)

Same Arxos software throughout!
```

### Mixed Deployment
```
Storage rooms:     Tier 1 (presence only)
Offices:          Tier 2 (occupancy counting)
Bathrooms:        Tier 3 (emergency detection)
Security zones:   Tier 4 (precision tracking)
```

## Hardware Abstraction Layer

### Transport Agnostic Protocol
```rust
pub trait Transport {
    fn send(&self, obj: &ArxObject) -> Result<()>;
    fn receive(&self) -> Result<Vec<ArxObject>>;
    fn latency_ms(&self) -> u32;
    fn bandwidth_bps(&self) -> u32;
}

impl Transport for LoRaMesh { /* Low bandwidth, high latency */ }
impl Transport for WiFiMesh { /* Medium bandwidth, medium latency */ }
impl Transport for EthernetBackbone { /* High bandwidth, low latency */ }
```

### Sensor Abstraction
```rust
pub trait Sensor {
    fn detect(&self) -> Vec<Detection>;
    fn capabilities(&self) -> SensorCapabilities;
    fn power_consumption(&self) -> PowerProfile;
}

impl Sensor for PIRMotion { /* Binary presence */ }
impl Sensor for WiFiCSI { /* Position + activity */ }
impl Sensor for IndustrialArray { /* Precision tracking */ }
```

## Cost-Benefit Analysis

### Total Cost of Ownership (10 rooms, 5 years)

**Tier 1**: $500 hardware + $0 maintenance = **$500**
- Basic presence detection
- Battery powered, minimal maintenance

**Tier 2**: $1,500 hardware + $500 maintenance = **$2,000**
- Occupancy counting + basic automation savings
- ROI through energy optimization

**Tier 3**: $5,000 hardware + $1,500 maintenance = **$6,500**
- Advanced features + emergency response value
- ROI through safety and operational efficiency

**Tier 4**: $20,000 hardware + $5,000 maintenance = **$25,000**
- Research/security applications
- ROI depends on specific use case value

## Privacy Considerations by Tier

### Tier 1: Maximum Privacy
- Only binary presence
- No identification possible
- No activity tracking
- Complete anonymity

### Tier 2: Anonymous Counting
- People counting only
- No individual tracking
- No personal characteristics
- Anonymous statistics

### Tier 3: Anonymous Activity
- Activity classification
- Still no identification
- Movement patterns (anonymous)
- Privacy-preserving emergency response

### Tier 4: Detailed but Anonymous
- Precise positioning
- Rich activity data
- Still no personal identification
- Advanced privacy controls

## Real-World Deployments

### Rural Cabin (Tier 1)
```
Challenge: Monitor remote property
Solution: LoRa presence sensors
Result: 5-year battery life, 10km range
Cost: $200 total
```

### Office Building (Tier 2)
```
Challenge: Optimize HVAC and lighting
Solution: WiFi occupancy counting
Result: 30% energy savings
Cost: $3,000 for 20 rooms
ROI: 18 months
```

### Senior Living (Tier 3)
```
Challenge: Fall detection without cameras
Solution: Activity recognition system
Result: 15-second emergency response
Cost: $12,000 for 30 rooms
Value: Lives saved, family peace of mind
```

### Research Lab (Tier 4)
```
Challenge: Precise movement analysis
Solution: High-frequency tracking
Result: 50ms latency, cm precision
Cost: $50,000 custom deployment
Value: Research data previously impossible
```

## Future Roadmap

### Hardware Evolution
- ESP32 → ESP32-C6 (better CSI)
- Pi 4 → Pi 5 (more processing power)
- LoRa → LoRa 2.4 (higher bandwidth)
- WiFi 6 → WiFi 7 (lower latency)

### Software Evolution
- Improved ML models
- Better privacy guarantees
- Enhanced visualization
- Cloud integration (optional)

The platform grows with technology while maintaining backward compatibility with existing deployments.