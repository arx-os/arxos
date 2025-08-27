# Cross-System Connection Examples

## Overview
Building systems are deeply interconnected. Electrical powers everything, HVAC needs power and controls, network equipment needs both power and cooling, and BAS controls multiple systems. This document shows how these connections work in practice.

## Key Connection Types

### 1. Power Connections (Electrical → Other Systems)
```
electrical/panel/mdf/breaker/24 
    → powers → hvac/ahu/1
    → powers → hvac/ahu/1/fan/supply
    → powers → hvac/ahu/1/fan/return
```

### 2. Control Connections (BAS → Equipment)
```
bas/controller/main
    → controls → hvac/ahu/1
    → controls → hvac/vav/f1_101
    → monitors → bas/sensor/temp_f1_101
```

### 3. Data Connections (Network → Devices)
```
network/switch/core_sw_1/port/24
    → data → bas/controller/main
    → data → security/camera/entrance_1 (PoE)
    → data → access/reader/front_door
```

## Real-World Example: HVAC Air Handler Unit

An AHU has multiple cross-system connections:

```yaml
arxobject:
  id: hq/hvac/ahu/1
  type: air_handler
  system: hvac
  name: "Air Handler Unit 1"
  
  # Cross-system connections
  power_source: hq/electrical/panel/mdf/breaker/24/circuit/hvac/ahu_1
  power_load:
    voltage: 208
    current: 22.5
    power: 8100
    phase: three
  
  data_connection: hq/network/switch/bas_sw_1/port/24
  
  critical: true  # Critical for server room cooling
  
  relationships:
    fed_from: 
      - hq/electrical/panel/mdf/breaker/24
    controlled_by:
      - hq/bas/controller/main
    serves:
      - hq/f1/room/101
      - hq/f1/room/102
      - hq/f1/corridor/north
    monitors:
      - hq/bas/sensor/ahu_1_sat  # Supply air temp
      - hq/bas/sensor/ahu_1_rat  # Return air temp
    requires_chilled_water:
      - hq/plumbing/chilled_water/supply/ahu_1
      - hq/plumbing/chilled_water/return/ahu_1
    requires_hot_water:
      - hq/plumbing/hot_water/supply/ahu_1
      - hq/plumbing/hot_water/return/ahu_1
```

## Example: Network Switch with Multiple Dependencies

```yaml
arxobject:
  id: hq/network/switch/core_sw_1
  type: switch
  system: network
  name: "Core Switch 1"
  
  # Primary power (outlet)
  power_source: hq/electrical/panel/idf_1/breaker/5/circuit/outlet/rack_1
  power_load:
    voltage: 120
    current: 2.5
    power: 300
    
  # Backup power (UPS)
  relationships:
    backup_power:
      - hq/electrical/ups/idf_1
    redundant_power:
      - hq/electrical/panel/idf_1/breaker/6/circuit/outlet/rack_1_b
    requires_cooling:
      - hq/hvac/crac/idf_1  # Computer Room AC
    monitored_by:
      - hq/bas/sensor/temp_idf_1
      - hq/bas/sensor/humidity_idf_1
    powers_poe_devices:
      - hq/security/camera/hallway_1
      - hq/security/camera/hallway_2
      - hq/network/ap/floor_1_north
      - hq/voip/phone/reception
```

## Example: Security Camera (PoE Powered)

```yaml
arxobject:
  id: hq/security/camera/entrance_1
  type: ip_camera
  system: security
  name: "Main Entrance Camera"
  
  # Gets both power AND data from network switch
  power_source: hq/network/switch/poe_sw_1/port/8
  data_connection: hq/network/switch/poe_sw_1/port/8
  
  power_load:
    voltage: 48  # PoE voltage
    current: 0.5
    power: 25    # Watts
    
  properties:
    poe_standard: "802.3at"
    poe_class: 4
    network_bandwidth: "100mbps"
    vlan: "security"
```

## Dependency Chain Example

When tracing dependencies, we can see the full chain:

```
Security Camera (entrance_1)
  └─ Powered by: PoE Switch (port 8)
      └─ Powered by: Electrical Outlet (rack_2)
          └─ Fed from: Breaker 10 (Panel IDF-1)
              └─ Fed from: Panel IDF-1
                  └─ Fed from: Breaker 35 (Panel MDF)
                      └─ Fed from: Panel MDF
                          └─ Fed from: Main Transformer
                          
  └─ Data from: PoE Switch (port 8)
      └─ Uplink to: Core Switch
          └─ Connected to: Firewall
              └─ Connected to: Router
                  └─ Connected to: ISP
                  
  └─ Cooled by: HVAC System
      └─ CRAC Unit (IDF-1)
          └─ Powered by: Breaker 15 (Panel IDF-1)
          └─ Chilled water from: Chiller 1
              └─ Powered by: Panel CHW
```

## Critical Path Analysis

For critical systems, we track all dependencies:

### Server Room Dependencies
```
Server Room (IDF-1)
  ├─ Power: Panel IDF-1 (w/ UPS backup, Generator failover)
  ├─ Cooling: CRAC Unit 1 (critical)
  │   ├─ Power: Dedicated circuit
  │   ├─ Chilled Water: Loop 1
  │   └─ Controls: BAS Controller
  ├─ Monitoring:
  │   ├─ Temperature sensors (4)
  │   ├─ Humidity sensor
  │   ├─ Water leak detection
  │   └─ Smoke detection
  └─ Network: Redundant uplinks to core
```

## Query Examples

### Find all equipment powered by a specific breaker:
```sql
SELECT * FROM arxobjects 
WHERE relationships.fed_from CONTAINS 'electrical/panel/mdf/breaker/24'
```

### Find all HVAC equipment and their power sources:
```sql
SELECT id, name, power_source, power_load 
FROM arxobjects 
WHERE system = 'hvac' AND power_source IS NOT NULL
```

### Find critical equipment with single points of failure:
```sql
SELECT id, name, system 
FROM arxobjects 
WHERE critical = true 
  AND NOT EXISTS (relationships.backup_power)
```

### Trace all systems affected by a panel outage:
```sql
WITH RECURSIVE affected AS (
  SELECT id, name, system 
  FROM arxobjects 
  WHERE power_source LIKE '%panel/mdf%'
  
  UNION ALL
  
  SELECT a.id, a.name, a.system
  FROM arxobjects a
  JOIN affected p ON a.power_source = p.id
)
SELECT DISTINCT system, COUNT(*) as affected_count
FROM affected
GROUP BY system
```

## Benefits of Cross-System Connections

1. **Impact Analysis**: Instantly know what's affected by an outage
2. **Load Balancing**: See electrical loads across panels and circuits
3. **Maintenance Planning**: Understand all systems affected by maintenance
4. **Energy Optimization**: Track power consumption by system
5. **Redundancy Verification**: Identify single points of failure
6. **Compliance**: Ensure critical systems have required backup power
7. **Troubleshooting**: Quickly trace problems across systems

## Implementation Notes

- Every equipment object should have a `power_source` if it uses electricity
- Critical equipment must have `critical: true` flag
- Use standard relationship types (powers, controls, monitors, serves)
- Include load information for proper electrical calculations
- Track both primary and backup/redundant connections
- Maintain bi-directional relationships for complete traceability