# ArxObject System Hierarchy Specification

## Overview
This document defines the complete naming convention and hierarchy for all building systems in Arxos. Each system follows a logical flow from source to end device, enabling technicians to trace systems as they would in the field.

## Core Naming Convention

### Format
```
building_id/system/component_hierarchy/instance_id
```

### Rules
- Use underscores (`_`) as separators
- Lowercase only
- No special characters except underscore
- Building ID is unique per building (user-defined with standardized format)
- Follow physical/logical flow from source to endpoint

## Building ID Format

### Structure
```
[company]_[building_name]_[location_identifier]
```

### Examples
- `acme_hq_main_street_12345`
- `walmart_store_2847_phoenix`
- `stanford_med_building_a`

### Metadata
Each building ID carries metadata:
```json
{
  "full_name": "Acme Headquarters",
  "address": "123 Main Street, San Francisco, CA 94105",
  "coordinates": {"lat": 37.7749, "lng": -122.4194},
  "type": "office",
  "year_built": 2018,
  "square_footage": 50000
}
```

## Spatial Hierarchy

### Format
```
building_id/floor/space_type/space_id/component
```

### Examples
```
building_id/f1/r101                    # Floor 1, Room 101
building_id/f1/r101/wall_north         # North wall of room
building_id/f1/r101/door_main          # Main door
building_id/f1/corridor_main           # Main corridor
building_id/b1/mechanical_room         # Basement 1 mechanical room
building_id/roof/rtu_area_1           # Roof RTU area
building_id/exterior/parking_lot_a    # Exterior areas
```

## System Hierarchies

### 1. Electrical System

#### Hierarchy Flow
Service → Transformer → Meter → Panel → Breaker → Circuit → Device

#### Naming Structure
```
building_id/electrical/service/main
building_id/electrical/transformer/t1
building_id/electrical/meter/main
building_id/electrical/meter/submeter_hvac
building_id/electrical/panel/mdf                      # Main distribution
building_id/electrical/panel/mdf/breaker/1
building_id/electrical/panel/mdf/breaker/1/circuit
building_id/electrical/panel/idf_f1                   # Floor 1 sub-panel
building_id/electrical/panel/idf_f1/breaker/1
building_id/electrical/junction/f1_hallway_j1
building_id/electrical/disconnect/hvac_rtu_1
building_id/electrical/outlet/f1_r101_north_1
building_id/electrical/switch/f1_r101_entrance
building_id/electrical/lighting/f1_r101_ceiling_1
building_id/electrical/emergency/generator/1
building_id/electrical/emergency/ats/main
building_id/electrical/ups/server_room_1
```

#### Metadata Example
```json
{
  "id": "building_id/electrical/panel/mdf/breaker/1",
  "type": "breaker",
  "properties": {
    "make": "Square D",
    "model": "QO120",
    "rating_amps": 20,
    "poles": 1,
    "voltage": "120V",
    "circuit_number": "1",
    "circuit_name": "Lighting - Floor 1 North",
    "wire_size": "12 AWG",
    "wire_type": "THHN",
    "conduit": "3/4 EMT",
    "length_feet": 150
  },
  "location": "building_id/b1/electrical_room",
  "serves": ["building_id/f1/r101", "building_id/f1/r102"],
  "fed_from": "building_id/electrical/panel/mdf"
}
```

### 2. HVAC System

#### Hierarchy Flow  
Plant → Distribution → Terminal Units → Zones

#### Naming Structure
```
# Cooling Plant
building_id/hvac/chiller/1
building_id/hvac/chiller/1/compressor/1
building_id/hvac/cooling_tower/1
building_id/hvac/cooling_tower/1/fan/1
building_id/hvac/pump/chw_primary_1          # Chilled water primary
building_id/hvac/pump/chw_secondary_1
building_id/hvac/pump/cw_1                   # Condenser water

# Heating Plant
building_id/hvac/boiler/1
building_id/hvac/boiler/1/burner
building_id/hvac/pump/hw_primary_1           # Hot water

# Air Handling
building_id/hvac/ahu/1
building_id/hvac/ahu/1/fan/supply
building_id/hvac/ahu/1/fan/return
building_id/hvac/ahu/1/coil/cooling
building_id/hvac/ahu/1/coil/heating
building_id/hvac/ahu/1/filter/primary
building_id/hvac/ahu/1/damper/oa             # Outside air
building_id/hvac/ahu/1/damper/ra             # Return air

# Distribution
building_id/hvac/duct/supply_main_f1
building_id/hvac/duct/return_main_f1
building_id/hvac/vav/f1_101                  # VAV box for room 101
building_id/hvac/vav/f1_101/damper
building_id/hvac/vav/f1_101/reheat_coil
building_id/hvac/diffuser/f1_r101_1
building_id/hvac/grille/f1_r101_return_1

# Packaged Units
building_id/hvac/rtu/1                       # Rooftop unit
building_id/hvac/split/f1_server_room_1      # Split system
building_id/hvac/ptac/f1_r101_1             # Package terminal AC

# Exhaust Systems
building_id/hvac/exhaust/bathroom_f1_1
building_id/hvac/exhaust/kitchen_main
building_id/hvac/exhaust/parking_garage_1
```

#### Metadata Example
```json
{
  "id": "building_id/hvac/vav/f1_101",
  "type": "vav_box",
  "properties": {
    "make": "Titus",
    "model": "DESV",
    "size": "10 inch",
    "max_cfm": 1000,
    "min_cfm": 200,
    "reheat_coil": true,
    "reheat_capacity_kw": 5
  },
  "location": "building_id/f1/ceiling_plenum",
  "serves": ["building_id/f1/r101"],
  "fed_from": "building_id/hvac/ahu/1",
  "controls": {
    "thermostat": "building_id/bas/sensor/temp_f1_r101",
    "controller": "building_id/bas/controller/vav_f1_101"
  }
}
```

### 3. Plumbing System

#### Hierarchy Flow
Source → Meter → Riser → Branch → Fixture

#### Naming Structure
```
# Water Supply
building_id/plumbing/water/main_entry
building_id/plumbing/water/meter/main
building_id/plumbing/water/backflow_preventer/main
building_id/plumbing/water/riser/cold_1
building_id/plumbing/water/riser/hot_1
building_id/plumbing/water/heater/1
building_id/plumbing/water/heater/1/tank
building_id/plumbing/water/pump/booster_1
building_id/plumbing/water/branch/f1_north_cold
building_id/plumbing/water/valve/f1_r101_shutoff
building_id/plumbing/water/fixture/f1_r101_sink_1
building_id/plumbing/water/fixture/f1_r101_toilet_1

# Drainage
building_id/plumbing/drain/stack/1
building_id/plumbing/drain/branch/f1_r101
building_id/plumbing/drain/trap/f1_r101_sink_1
building_id/plumbing/drain/cleanout/f1_co_1
building_id/plumbing/drain/pump/sump_1
building_id/plumbing/drain/pump/ejector_1

# Gas
building_id/plumbing/gas/meter/main
building_id/plumbing/gas/riser/1
building_id/plumbing/gas/branch/roof_rtu
building_id/plumbing/gas/valve/hvac_boiler_1
building_id/plumbing/gas/regulator/kitchen_1

# Specialty
building_id/plumbing/compressed_air/compressor/1
building_id/plumbing/medical_gas/oxygen/tank/1
building_id/plumbing/medical_gas/oxygen/outlet/or_1
```

### 4. Fire & Life Safety System

#### Naming Structure
```
# Fire Alarm
building_id/fire_alarm/panel/main
building_id/fire_alarm/panel/annunciator_lobby
building_id/fire_alarm/detector/smoke_f1_r101
building_id/fire_alarm/detector/heat_kitchen_1
building_id/fire_alarm/detector/duct_ahu_1
building_id/fire_alarm/pull_station/f1_exit_1
building_id/fire_alarm/horn_strobe/f1_corridor_1

# Sprinkler
building_id/sprinkler/riser/main
building_id/sprinkler/valve/control_1
building_id/sprinkler/valve/zone_f1
building_id/sprinkler/fdc/front_entrance        # Fire dept connection
building_id/sprinkler/head/f1_r101_1
building_id/sprinkler/flow_switch/f1
building_id/sprinkler/tamper_switch/main_valve
building_id/sprinkler/pump/fire_pump_1

# Suppression
building_id/suppression/fm200/server_room
building_id/suppression/kitchen_hood/1
building_id/suppression/co2/electrical_room

# Emergency
building_id/emergency/lighting/f1_corridor_1
building_id/emergency/exit_sign/f1_stair_1
```

### 5. Security & Access Control

#### Naming Structure
```
# Access Control
building_id/access/controller/main
building_id/access/panel/f1
building_id/access/reader/f1_main_entrance
building_id/access/lock/f1_r101_door_main
building_id/access/strike/f1_stair_1
building_id/access/rex/f1_main_entrance         # Request to exit
building_id/access/gate/parking_entry

# Video Surveillance
building_id/security/nvr/main                   # Network video recorder
building_id/security/camera/exterior_entrance_1
building_id/security/camera/f1_lobby_1
building_id/security/camera/ptz_roof_1          # Pan-tilt-zoom

# Intrusion
building_id/security/intrusion/panel/main
building_id/security/motion/f1_r101
building_id/security/door_contact/f1_exit_1
building_id/security/glass_break/f1_lobby_1
building_id/security/duress/f1_reception
```

### 6. Vertical Transportation

#### Naming Structure
```
# Elevators
building_id/elevator/car/1
building_id/elevator/car/1/motor
building_id/elevator/car/1/controller
building_id/elevator/car/1/door_operator
building_id/elevator/car/1/safety_brake
building_id/elevator/shaft/1/pit
building_id/elevator/shaft/1/machine_room
building_id/elevator/call_button/f1_up
building_id/elevator/lantern/f1

# Escalators
building_id/escalator/lobby_1
building_id/escalator/lobby_1/motor
building_id/escalator/lobby_1/handrail
building_id/escalator/lobby_1/step_chain
```

### 7. Building Automation System (BAS)

#### Naming Structure
```
# Controllers
building_id/bas/server/main
building_id/bas/controller/main
building_id/bas/controller/f1
building_id/bas/controller/ahu_1
building_id/bas/controller/vav_f1_101

# Sensors
building_id/bas/sensor/temp_f1_r101
building_id/bas/sensor/humidity_f1_r101
building_id/bas/sensor/co2_f1_r101
building_id/bas/sensor/occupancy_f1_r101
building_id/bas/sensor/pressure_duct_ahu_1
building_id/bas/sensor/flow_chw_main

# Actuators
building_id/bas/actuator/valve_chw_ahu_1
building_id/bas/actuator/damper_vav_f1_101
```

### 8. IT/Telecommunications

#### Naming Structure
```
# Network Infrastructure
building_id/it/mdf/main                        # Main distribution frame
building_id/it/idf/f1                         # Intermediate dist frame
building_id/it/rack/mdf_1
building_id/it/switch/core_1
building_id/it/switch/access_f1_1
building_id/it/router/main
building_id/it/firewall/main
building_id/it/ups/mdf_1
building_id/it/ap/f1_r101                     # Wireless access point

# Structured Cabling
building_id/it/patch_panel/idf_f1_1
building_id/it/jack/f1_r101_desk_1
building_id/it/cable/backbone_1
building_id/it/fiber/riser_1

# Telecommunications
building_id/telecom/pbx/main
building_id/telecom/phone/f1_r101_desk
building_id/telecom/antenna/das_f1            # Distributed antenna
```

### 9. Site Systems

#### Naming Structure
```
# Parking
building_id/site/parking/gate/entry_main
building_id/site/parking/gate/exit_main
building_id/site/parking/sensor/space_a1
building_id/site/parking/light/lot_a_pole_1
building_id/site/parking/kiosk/pay_1

# Landscape
building_id/site/irrigation/controller/main
building_id/site/irrigation/valve/zone_1
building_id/site/irrigation/sprinkler/lawn_1_head_1

# Site Infrastructure
building_id/site/lighting/pole_1
building_id/site/storm/catch_basin_1
building_id/site/storm/detention_pond_1
```

### 10. Environmental & Sustainability

#### Naming Structure
```
# Solar
building_id/solar/array/roof_1
building_id/solar/panel/roof_1_string_1_panel_1
building_id/solar/inverter/1
building_id/solar/combiner/1
building_id/solar/meter/production

# Battery Storage
building_id/battery/system/main
building_id/battery/rack/1
building_id/battery/module/rack_1_module_1
building_id/battery/bms/main                   # Battery management system

# Other
building_id/wind/turbine/1
building_id/rainwater/tank/1
building_id/greywater/treatment/main
```

## Cross-Reference Structure

### Primary ID (System Hierarchy)
```
building_id/electrical/panel/mdf/breaker/12/circuit/outlet/1
```

### Location Metadata
```json
{
  "spatial_location": "building_id/f1/r101",
  "wall": "north",
  "height_inches": 18,
  "coordinates": {
    "x": 1200,
    "y": 3400, 
    "z": 1200
  }
}
```

### Relationships
```json
{
  "fed_from": "building_id/electrical/panel/mdf/breaker/12",
  "powers": [],
  "controlled_by": ["building_id/electrical/switch/f1_r101_entrance"],
  "in_zone": "building_id/electrical/circuit/12",
  "wiring_path": [
    "building_id/electrical/panel/mdf",
    "building_id/electrical/junction/f1_j1",
    "building_id/electrical/conduit/f1_north_3_4",
    "building_id/f1/r101/wall_north"
  ]
}
```

## Query Patterns

### Spatial Queries
```sql
-- All systems in room 101
SELECT * FROM building_id/**
WHERE metadata.spatial_location = "building_id/f1/r101"

-- All electrical on floor 1
SELECT * FROM building_id/electrical/**
WHERE metadata.spatial_location LIKE "building_id/f1/%"
```

### System Queries
```sql
-- Everything on circuit 12
SELECT * FROM building_id/electrical/panel/mdf/breaker/12/**

-- All VAV boxes served by AHU-1
SELECT * FROM building_id/hvac/vav/*
WHERE metadata.fed_from = "building_id/hvac/ahu/1"
```

### Cross-System Queries
```sql
-- Find electrical circuits powering HVAC equipment
SELECT * FROM building_id/electrical/**/circuit/*
WHERE metadata.powers LIKE "building_id/hvac/%"

-- All equipment in emergency power
SELECT * FROM building_id/**
WHERE metadata.emergency_power = true
```

## Implementation Guidelines

### 1. ID Generation
- IDs are immutable once created
- Use deterministic generation based on location/function
- Include building_id prefix always

### 2. Metadata Standards
- Always include spatial_location for physical objects
- Include fed_from/serves relationships
- Add make/model/serial for equipment
- Include installation_date and warranty info

### 3. Navigation
- Support filesystem-style navigation (cd, ls, pwd)
- Allow navigation by both system and spatial hierarchies
- Implement symlink-style references between hierarchies

### 4. Validation Rules
- Enforce parent existence before child creation
- Validate electrical loads don't exceed breaker ratings
- Ensure HVAC zones have proper sensor coverage
- Check plumbing fixtures have proper drainage

## Migration Strategy

### From Existing Systems
```
Old Format: Panel:MDF:Breaker:12:Outlet:1
New Format: building_id/electrical/panel/mdf/breaker/12/circuit/outlet/1

Old Format: Floor1:Room101:NorthWall:Outlet1  
New Format: building_id/f1/r101/wall_north/outlet_1
```

### Bulk Import Templates
- CSV format for each system type
- Validation before import
- Relationship resolution after import
- Spatial location mapping tools

## Future Extensions

### Digital Twin Integration
- Real-time sensor data updates
- Predictive maintenance flags
- Energy optimization paths
- Fault detection rules

### AR/VR Support
- Spatial coordinate precision
- Visual marker associations
- Model linking
- Maintenance procedure attachments

### AI/ML Applications
- Pattern recognition in naming
- Automatic relationship discovery
- Anomaly detection in hierarchies
- Optimization suggestions

## Appendix: Standard Abbreviations

### Common Terms
- mdf = main distribution frame
- idf = intermediate distribution frame
- ahu = air handling unit
- vav = variable air volume
- rtu = rooftop unit
- chw = chilled water
- hw = hot water
- cw = condenser water
- oa = outside air
- ra = return air
- ups = uninterruptible power supply
- ats = automatic transfer switch

### Directions
- n = north
- s = south  
- e = east
- w = west
- ne = northeast
- nw = northwest
- se = southeast
- sw = southwest

### Floors
- f = floor (f1, f2, f3)
- b = basement (b1, b2)
- m = mezzanine (m1)
- p = penthouse (p1)
- r = roof

## Version History

- v1.0 - Initial specification (2024-08-26)
- Based on electrical system expertise and extended to all building systems
- Designed for Arxos building intelligence platform