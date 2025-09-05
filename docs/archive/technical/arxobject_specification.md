---
title: ArxObject 13-Byte Specification v1.0
summary: Byte-level specification of the 13B ArxObject, including taxonomy, validation rules, and transmission notes.
owner: Lead Architecture
last_updated: 2025-09-04
---
# ArxObject 13-Byte Specification v1.0

## Core Philosophy

The ArxObject is the atomic unit of building intelligence. Every outlet, sensor, room, and system is represented in exactly 13 bytes. This constraint forces elegance and ensures the protocol works over 1 kbps mesh networks.

## Byte-Level Structure

```
Offset  Size  Field         Range           Purpose
------  ----  ------------- --------------- -------------------------------
0x00    2     object_id     0x0000-0xFFFF   Unique identifier within building
0x02    1     object_type   0x00-0xFF       What this object is
0x03    2     x_coordinate  0-65535mm       Position X (0-65.535 meters)
0x05    2     y_coordinate  0-65535mm       Position Y (0-65.535 meters)  
0x07    2     z_coordinate  0-65535mm       Position Z (0-65.535 meters)
0x09    4     properties    Type-specific   Dynamic properties/state
------  ----
Total:  13 bytes
```

## Field Specifications

### Object ID (2 bytes)
- **Range**: 0x0000 - 0xFFFF (65,536 unique objects per building)
- **Assignment**:
  - 0x0000: Reserved (null object)
  - 0x0001-0x00FF: Building-level objects (building, floors)
  - 0x0100-0x0FFF: Infrastructure (panels, mechanical rooms)
  - 0x1000-0xEFFF: General objects (outlets, sensors, etc.)
  - 0xF000-0xFFFE: Temporary/dynamic objects
  - 0xFFFF: Broadcast address

### Object Type (1 byte)
- **Structure**: `CCCTTTTT`
  - CCC (bits 7-5): Category (8 categories)
  - TTTTT (bits 4-0): Type within category (32 types per category)

### Coordinates (6 bytes total, 2 per axis)
- **Unit**: Millimeters (mm)
- **Range**: 0-65,535mm per axis (65.535 meters)
- **Resolution**: 1mm precision
- **Origin**: Building-specific (typically NW corner at ground level)
- **Endianness**: Little-endian for ESP32 compatibility

### Properties (4 bytes)
- **Purpose**: Type-specific dynamic data
- **Update Rate**: Can change up to 20 times per second
- **Encoding**: Depends on object_type

## Object Type Taxonomy

### Category 0: Reserved (0x00-0x0F)
```
0x00: NULL_OBJECT      - Invalid/deleted object
0x01: UNKNOWN          - Type not recognized
0x02-0x0F: Reserved
```

### Category 1: Electrical (0x10-0x1F)
```
0x10: OUTLET           - Standard electrical outlet
      Properties: [circuit_id, voltage_low, voltage_high, amperage]
      
0x11: LIGHT_SWITCH     - Light control switch
      Properties: [circuit_id, state, dimmer_level, group_id]
      
0x12: CIRCUIT_BREAKER  - Individual circuit breaker
      Properties: [panel_id, circuit_num, state, rated_amps]
      
0x13: ELECTRICAL_PANEL - Main or sub panel
      Properties: [panel_id, active_circuits, total_amps_low, total_amps_high]
      
0x14: JUNCTION_BOX     - Electrical junction
      Properties: [circuit_count, wire_gauge, box_type, reserved]
      
0x15: EMERGENCY_LIGHT  - Emergency/exit lighting
      Properties: [circuit_id, battery_level, test_status, lamp_hours]
      
0x16: GENERATOR        - Backup generator
      Properties: [fuel_level, run_hours_low, run_hours_high, state]
      
0x17: TRANSFORMER      - Electrical transformer
      Properties: [primary_voltage, secondary_voltage, load_percent, temp]
      
0x18: METER           - Electrical meter
      Properties: [kwh_low, kwh_mid, kwh_high, current_kw]
      
0x19-0x1F: Reserved
```

### Category 2: HVAC (0x20-0x2F)
```
0x20: THERMOSTAT       - Temperature control
      Properties: [current_temp, setpoint, mode, fan_state]
      
0x21: AIR_VENT         - Supply/return vent
      Properties: [damper_position, air_flow_low, air_flow_high, type]
      
0x22: VAV_BOX          - Variable Air Volume box
      Properties: [zone_id, damper_pos, reheat_state, cfm]
      
0x23: AIR_HANDLER      - AHU/RTU unit
      Properties: [unit_id, supply_temp, return_temp, filter_hours]
      
0x24: CHILLER          - Cooling equipment
      Properties: [supply_temp, return_temp, flow_rate, efficiency]
      
0x25: BOILER           - Heating equipment
      Properties: [supply_temp, return_temp, pressure, fuel_rate]
      
0x26: COOLING_TOWER    - Heat rejection
      Properties: [basin_temp, fan_speed, flow_rate, cycles]
      
0x27: PUMP             - Water/fluid pump
      Properties: [speed_percent, flow_rate, pressure, run_hours]
      
0x28: FAN              - Exhaust/supply fan
      Properties: [speed_percent, cfm_low, cfm_high, static_pressure]
      
0x29-0x2F: Reserved
```

### Category 3: Sensors (0x30-0x3F)
```
0x30: TEMPERATURE      - Temperature sensor
      Properties: [temp_low, temp_high, humidity, calibration]
      
0x31: MOTION           - Occupancy detection
      Properties: [state, sensitivity, timeout, zone_id]
      
0x32: CO2              - Air quality sensor
      Properties: [ppm_low, ppm_high, temp, calibration]
      
0x33: LIGHT            - Illuminance sensor
      Properties: [lux_low, lux_high, color_temp, zone_id]
      
0x34: PRESSURE         - Pressure sensor
      Properties: [pressure_low, pressure_high, type, alarm_state]
      
0x35: HUMIDITY         - Moisture sensor
      Properties: [rh_percent, temp, dew_point, alarm_state]
      
0x36: SMOKE            - Smoke detector
      Properties: [state, sensitivity, battery, test_status]
      
0x37: WATER_LEAK       - Leak detection
      Properties: [state, resistance_low, resistance_high, zone_id]
      
0x38: VIBRATION        - Vibration sensor
      Properties: [amplitude, frequency, axis, alarm_state]
      
0x39: SOUND            - Sound level meter
      Properties: [db_level, frequency, peak_db, avg_db]
      
0x3A-0x3F: Reserved
```

### Category 4: Access/Security (0x40-0x4F)
```
0x40: DOOR             - Door/entrance
      Properties: [state, lock_state, access_level, last_badge]
      
0x41: WINDOW           - Window
      Properties: [state, lock_state, tint_level, alarm_state]
      
0x42: CAMERA           - Security camera
      Properties: [state, pan, tilt, recording]
      
0x43: CARD_READER      - Access control reader
      Properties: [zone_id, last_card_low, last_card_high, mode]
      
0x44: ALARM_PANEL      - Security panel
      Properties: [armed_state, zone_count, alarm_active, trouble]
      
0x45: MOTION_DETECTOR  - Security motion
      Properties: [state, zone_id, sensitivity, tamper]
      
0x46: GLASS_BREAK      - Glass break sensor
      Properties: [state, sensitivity, zone_id, battery]
      
0x47: PANIC_BUTTON     - Emergency button
      Properties: [state, type, zone_id, test_mode]
      
0x48-0x4F: Reserved
```

### Category 5: Structural (0x50-0x5F)
```
0x50: ROOM             - Room/space
      Properties: [room_number, floor_id, occupancy, area_m2]
      
0x51: FLOOR            - Building floor/level
      Properties: [floor_number, total_rooms, occupied_rooms, area_m2]
      
0x52: BUILDING         - Building entity
      Properties: [building_id, total_floors, occupied, efficiency]
      
0x53: ZONE             - HVAC/lighting zone
      Properties: [zone_id, type, active_devices, schedule_id]
      
0x54: WALL             - Wall/partition
      Properties: [wall_id, material, fire_rating, length_m]
      
0x55: CEILING          - Ceiling
      Properties: [height_cm, type, grid_type, area_m2]
      
0x56: COLUMN           - Structural column
      Properties: [column_id, material, load_percent, inspection]
      
0x57: BEAM             - Structural beam
      Properties: [beam_id, material, load_percent, length_m]
      
0x58-0x5F: Reserved
```

### Category 6: Plumbing/Water (0x60-0x6F)
```
0x60: WATER_VALVE      - Shutoff valve
      Properties: [state, type, flow_rate, pressure]
      
0x61: WATER_METER      - Water meter
      Properties: [gallons_low, gallons_high, flow_rate, leak_detect]
      
0x62: WATER_HEATER     - Hot water heater
      Properties: [temp_set, temp_actual, fuel_type, efficiency]
      
0x63: FAUCET           - Sink/faucet
      Properties: [state, flow_rate, temp, filter_hours]
      
0x64: TOILET           - Toilet fixture
      Properties: [flush_count_low, flush_count_high, leak_detect, gpf]
      
0x65: DRAIN            - Floor/sink drain
      Properties: [flow_state, blockage, trap_full, alarm]
      
0x66: SUMP_PUMP        - Sump pump
      Properties: [state, level, run_hours, alarm]
      
0x67: SPRINKLER        - Fire sprinkler head
      Properties: [state, pressure, temp_rating, zone_id]
      
0x68-0x6F: Reserved
```

### Category 7: Network/Computing (0x70-0x7F)
```
0x70: WIFI_AP          - Wireless access point
      Properties: [channel, client_count, signal_strength, data_rate]
      
0x71: NETWORK_SWITCH   - Network switch
      Properties: [port_count, active_ports, bandwidth, vlan_id]
      
0x72: MESHTASTIC_NODE  - Mesh radio node
      Properties: [node_id, hop_count, signal_rssi, battery]
      
0x73: SERVER           - Computer/server
      Properties: [cpu_percent, memory_percent, disk_percent, temp]
      
0x74: UPS              - Uninterruptible power
      Properties: [battery_percent, load_percent, runtime_min, state]
      
0x75: DISPLAY          - Display/kiosk
      Properties: [state, content_id, brightness, schedule_id]
      
0x76: PRINTER          - Printer/copier
      Properties: [state, paper_level, toner_level, job_count]
      
0x77: PHONE            - VoIP phone
      Properties: [state, line_id, extension, call_state]
      
0x78: IOT_GATEWAY      - IoT gateway/hub
      Properties: [device_count, protocol, uptime_hours, data_rate]
      
0x79: PLAYER_AVATAR    - Gamification avatar
      Properties: [player_id, bilt_tokens, level, current_task]
      
0x7A-0x7F: Reserved
```

## Property Encoding Patterns

### Pattern 1: Simple State (1 byte state + 3 bytes data)
```c
properties[0] = state;        // 0=off, 1=on, 2=auto, etc.
properties[1] = value;        // Main value (temp, level, etc.)
properties[2] = extra;        // Secondary value
properties[3] = reserved;     // Future use
```

### Pattern 2: 16-bit Value (2 bytes value + 2 bytes extra)
```c
properties[0-1] = value_16;   // Little-endian 16-bit
properties[2] = status;       // Status flags
properties[3] = config;       // Configuration
```

### Pattern 3: Identification (2 bytes ID + 2 bytes state)
```c
properties[0-1] = related_id; // Related object ID
properties[2] = state;        // Current state
properties[3] = value;        // Current value
```

### Pattern 4: Measurement (scaled integers)
```c
properties[0-1] = measure_low;  // Low precision part
properties[2] = measure_high;   // High precision part
properties[3] = unit_and_scale; // Unit type and scale factor
```

## Validation Rules

### Structural Validation
1. **Size**: Message must be exactly 13 bytes
2. **ID Range**: 0x0001-0xFFFE (0x0000 and 0xFFFF reserved)
3. **Type Range**: Must be defined type or 0x01 (UNKNOWN)
4. **Coordinate Range**: Each axis 0-65535 (mm)

### Logical Validation
1. **Position Sanity**: Objects must be within building bounds
2. **Type Consistency**: Properties must match object_type encoding
3. **Temporal Consistency**: Updates limited to 20Hz per object
4. **Relationship Integrity**: Referenced IDs must exist

### Network Validation
1. **CRC**: Optional 1-byte CRC8 can be appended (14 bytes total)
2. **Sequence**: Optional sequence number for detecting drops
3. **TTL**: Mesh packets include hop count limit

## Extension Mechanism

While the core is always 13 bytes, the slow-bleed protocol allows progressive enhancement:

1. **Base Layer**: 13-byte ArxObject (instant, always available)
2. **Detail Chunks**: Additional 13-byte packets with extended data
3. **Convergence**: Full object knowledge accumulates over time

## Implementation Notes

### Memory Alignment
```c
// Force packed structure (no padding)
#pragma pack(push, 1)
typedef struct {
    uint16_t id;
    uint8_t  type;
    uint16_t x;
    uint16_t y;
    uint16_t z;
    uint8_t  properties[4];
} ArxObject;
#pragma pack(pop)
```

### Endianness
- All multi-byte fields are **little-endian**
- Matches ESP32 native byte order
- Network byte order conversion NOT used (optimization)

### Transmission
```c
// Direct memory transmission
ArxObject obj = {.id = 0x1234, .type = 0x10, ...};
uart_write((uint8_t*)&obj, sizeof(ArxObject));

// Radio transmission
radio.send((uint8_t*)&obj, 13);
```

## Example Objects

### Outlet
```
ID:         0x1234
Type:       0x10 (OUTLET)
Position:   (2000, 3000, 300) = 2m, 3m, 0.3m
Properties: [12, 120, 0, 15] = Circuit 12, 120V, 15A rated
Hex:        34 12 10 D0 07 B8 0B 2C 01 0C 78 00 0F
```

### Thermostat
```
ID:         0x2001
Type:       0x20 (THERMOSTAT)
Position:   (5000, 3000, 1500) = 5m, 3m, 1.5m
Properties: [72, 70, 1, 0] = 72°F current, 70°F set, cooling mode
Hex:        01 20 20 88 13 B8 0B DC 05 48 46 01 00
```

### Room
```
ID:         0x5001
Type:       0x50 (ROOM)
Position:   (10000, 8000, 0) = Center at 10m, 8m, ground
Properties: [205, 2, 3, 45] = Room 205, Floor 2, 3 occupants, 45m²
Hex:        01 50 50 10 27 40 1F 00 00 CD 02 03 2D
```

## Future Considerations

### Reserved Bits
- Object type has 256 possible values, only ~100 defined
- Properties field is type-specific, allowing evolution
- Coordinate space supports buildings up to 65m x 65m x 65m

### Versioning
- Type byte could include version bits if needed
- New types can be added without breaking compatibility
- Unknown types default to 0x01 (UNKNOWN) handling

## Conclusion

The 13-byte ArxObject achieves the impossible: representing complex building intelligence in a packet small enough for 1970s networks, yet rich enough for modern building automation. This is the foundation of democratized building intelligence.