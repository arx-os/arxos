======================== MECHANICAL (HVAC) SYSTEMS

Major Equipment
- AHU (Air Handling Unit): ▭ w/ supply/return arrows
- RTU (Rooftop Unit): ▭ with fan symbol inside
- FCU (Fan Coil Unit): ▭ with fan + coil loop
- VAV Box: ▭ with diagonal slash or label "VAV"
- Boiler: ○ or ▭ labeled "B"
- Chiller: ▭ with coil symbol
- Cooling Tower: ▭ with fan & water droplet icons
- Heat Exchanger: || lines with crossing arrows
- Pumps: ◯ with arrow or labeled "P"

Fans
- Exhaust Fan: ◯ with fan blades
- Supply Fan: ◯ with outward arrow
- Return Fan: ◯ with inward arrow

Ducting
- Supply Duct: Solid line
- Return Duct: Dashed line
- Exhaust Duct: Dotted line
- Dampers: Slash across duct
  - Fire Damper: Tagged "FD"
  - Volume Damper: Tagged "VD"

Diffusion Devices
- Diffusers: ▭ or ◯ with cross/X
- Grilles: ▭ with parallel lines
- Registers: ▭ with grid or label

Sensors & Controls
- Thermostat: Ⓣ
- Temperature Sensor: ⓉⓈ
- Humidity Sensor: ⒽⓈ

======================== ELECTRICAL SYSTEMS

Power Devices
- Receptacles: ☐ with "GFCI", "R", etc.
- Switches: ☐ labeled "S", "S3", "S4"

Lighting
- Fixture: ⊗ or recessed indicator
- Emergency Light / Exit Sign: ☐ with EL/EXIT

Distribution Equipment
- Panelboard: ▭ labeled "P1", "LP", etc.
- Transformer: ▭ with zigzag symbol
- Motor: ⊙ or labeled "M1", etc.

Cabling & Pathways
- Wiring: Solid line
- Conduit: Dashed line
- Junction Box: ☐ labeled "JB"
- Ground/Bonding: ⏚ or arc to ground

======================== PLUMBING SYSTEMS

Fixtures
- Toilet (WC), Sink, Bathtub, etc.: Standard symbols or labeled abbreviation

Piping Types
- Cold Water (CW): Blue line
- Hot Water (HW): Red line
- Hot Water Return (HWR): Dashed red
- Sanitary Waste (SW): Black solid
- Gas (G): Yellow or labeled
- Vent (V): Dotted line

Valves
- Ball Valve, Gate Valve, Check Valve: Standard schematic symbols
- Pressure Reducing Valve (PRV): PRV tag

Equipment
- Water Heater (WH)
- Pump (P)
- Expansion Tank (ET)
- Grease Interceptor (GI)

======================== LOW VOLTAGE SYSTEMS

Power Supplies
- LV Panel / Power Supply (PS): ▭ labeled "LV" or "PS"

Modules & Components
- Relay Modules
- Terminal Blocks

Routing
- Conduit/Raceway: Dashed
- Cable Tray: Zigzag

======================== TELECOMMUNICATIONS

Devices
- Voice/Data Outlets: ☐ labeled "T", "D", or "VD"
- Wireless Access Point (WAP): ◯ with signal arcs

Network Infrastructure
- Patch Panels / Racks: ▭ labeled "PP", "IDF", "MDF"

Cabling
- Cat5/6: Solid line labeled "C5"/"C6"
- Fiber Optic (FO): Dashed line
- Coaxial: Labeled or symbolized

======================== FIRE ALARM SYSTEMS

Initiation Devices
- Pull Station: ☐ labeled "P"
- Smoke Detector (SD): ⭕
- Heat Detector (HD): ⭕ with dot or labeled "HD"

Notification Appliances
- Horn/Strobe (H/S): ▭ labeled "H/S"
- Speaker (SPKR): ▭ labeled "SPKR"

Control & Monitoring
- Fire Alarm Control Panel (FACP): ▭
- Annunciator (ANN): ▭
- Monitor/Control Modules (MM): Smaller ▭

======================== SECURITY SYSTEMS

Intrusion
- Motion Detector (MD): △ or ⭕ with "MD"
- Glass Break Detector (GB): ◯ with shards/symbol
- Door/Window Contact (DC): ▬ labeled "DC"

Access Control
- Card Reader (CR): ▭
- Mag Lock (ML): ▬
- Keypad (KP): ▭ with numbers

Surveillance
- CCTV Camera: ◯ with angle cone
- PTZ Camera: ◯ with arrows
- Monitor: ▭ with screen frame

======================== BUILDING CONTROLS (BAS/BMS)

Sensors
- Temperature Sensor (TS)
- Humidity Sensor (HS)
- Pressure Sensor (PS)
- Flow Sensor (FS)

Controllers & Modules
- DDC Controllers
- I/O Modules

Field Devices
- Actuators
- Control Dampers
- Control Valves

Networking
- BACnet / Modbus Bus: Dashed line with protocol label

======================== NETWORK SYSTEMS

Core Devices
- Router: ◯ with directional arrows
- Switch: ▭ labeled "SW"
- Firewall: ▭ with flame or shield

Access Points (AP): ◯ with arcs
Servers, Racks, UPS: ▭ labeled "SV", "R", "UPS"
Cabling:
- Ethernet: Solid labeled "CAT6"
- Fiber: Dashed labeled "FO"

======================== AUDIOVISUAL (AV) SYSTEMS

Display & Output
- Display / Projector / Screen: ▭ labeled
- Speakers (SP): ⭕ or ▭ with sound waves
- Microphones (MIC): ◯ labeled "MIC"

Signal Routing
- DSP / Amplifier / Patch Panel: ▭ labeled
- Touch Panel / Keypad (TP/KP): ▭ with icons
- Source Devices (SRC, MP, PC): ▭ with type

Cabling
- HDMI, VGA, XLR, CAT6: Labeled solid lines
- Wireless Presentation (WPG), Receiver (WR), Streaming Server: ▭ with appropriate label

Racks & Enclosures
- AV Rack (AVR)
- AV Box / Floor Box: ▭ embedded

======================== CONNECTOR MODELS

Connectors represent physical connection points between building systems and equipment. All connectors include FloorID for floor-based organization and validation.

### Connector Data Model

```json
{
  "id": 1,
  "object_id": "CONN_001",
  "name": "Electrical Connector A",
  "object_type": "connector",
  "type": "connector",
  "system": "electrical",
  "category": "power",
  "connector_type": "electrical",
  "connection_type": "male",
  "connection_status": "connected",
  "max_capacity": 100.0,
  "current_load": 75.0,
  "floor_id": 5,
  "geometry": {
    "type": "Point",
    "points": [{"x": 150.5, "y": 200.0}]
  },
  "connected_to": ["DEVICE_001", "DEVICE_002"],
  "description": "Main electrical connector for Room 501",
  "status": "active",
  "created_by": 1,
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

### Connector Types

#### Electrical Connectors
- **Power Connectors:** Standard electrical outlets, panels, distribution points
- **Control Connectors:** Low-voltage control connections, sensors, actuators
- **Data Connectors:** Network, communication, and data transmission points

#### Mechanical Connectors
- **HVAC Connectors:** Duct connections, pipe fittings, equipment interfaces
- **Plumbing Connectors:** Pipe connections, valve interfaces, fixture connections
- **Fire Protection:** Sprinkler connections, fire alarm interfaces

#### Low Voltage Connectors
- **Security Connectors:** Access control, surveillance, intrusion detection
- **AV Connectors:** Audio/visual, presentation, entertainment systems
- **Telecommunications:** Voice, data, network infrastructure

### Connection Types

- **Male:** Pin-based connections (plugs, pins)
- **Female:** Socket-based connections (receptacles, sockets)
- **Both:** Bidirectional connections (adapters, couplers)

### Connection Status

- **Connected:** Active connection with equipment
- **Disconnected:** Available but not currently connected
- **Pending:** Planned connection awaiting implementation

### FloorID Integration

All connectors must have a valid `floor_id` that:
- References an existing floor in the building
- Matches the floor of connected objects (devices, rooms)
- Enables floor-based filtering and organization
- Supports floor boundary validation for placement

### Validation Rules

1. **FloorID Required:** All connectors must have a valid floor_id > 0
2. **Floor Consistency:** Connected objects must be on the same floor
3. **Geometry Validation:** Connector coordinates must be within floor bounds
4. **Capacity Validation:** Current load cannot exceed max capacity
5. **Object ID Format:** Must follow standard object ID conventions

### Connector Symbols

Standard connector symbols for different types:
- **Electrical:** ⚡ or ▭ with "E" label
- **HVAC:** ❄️ or ▭ with "H" label  
- **Plumbing:** 💧 or ▭ with "P" label
- **Data:** 📡 or ▭ with "D" label
- **Security:** 🔒 or ▭ with "S" label
- **AV:** 🎵 or ▭ with "AV" label

### Floor-Based Organization

Connectors are organized by floor to support:
- **Floor Filtering:** View connectors by specific floors
- **Floor Grouping:** Group connectors in lists by floor
- **Floor Validation:** Ensure connectors are placed on correct floors
- **Floor Indicators:** Visual floor badges in UI
- **Floor Tooltips:** Floor information in hover tooltips
