# ArxObject Type Definitions

## All Building Objects as Game Entities

### Type Categories (Like Character Classes)

```
0x00-0x0F: System/Meta Objects (Admin Class)
0x10-0x1F: Electrical Objects (Electrician Class)
0x20-0x2F: HVAC Objects (Mechanical Class)
0x30-0x3F: Sensor Objects (Any Class)
0x40-0x4F: Security Objects (Security Class)
0x50-0x5F: Structural Objects (Builder Class)
0x60-0x6F: Plumbing Objects (Plumber Class)
0x70-0x7F: Network Objects (IT Class)
```

### Electrical Objects (0x10-0x1F)

#### 0x10: Electrical Outlet
```c
properties[0] = circuit_id;     // Which breaker (0-255)
properties[1] = max_amps;        // Rating (15, 20, 30...)
properties[2] = status;          // Bit 0: On/Off, Bit 1: Fault
properties[3] = load_percent;    // Current usage (0-100%)

// BILT Reward: 25 tokens per outlet mapped
// Class Required: Electrician
```

#### 0x11: Light Switch
```c
properties[0] = circuit_id;      // Which breaker
properties[1] = switch_type;     // 0=Toggle, 1=Dimmer, 2=3way
properties[2] = dim_level;       // 0-100% brightness
properties[3] = group_id;        // Lighting group/zone

// BILT Reward: 20 tokens per switch
// Class Required: Electrician
```

#### 0x12: Circuit Breaker
```c
properties[0] = panel_id;        // Which panel
properties[1] = breaker_amps;    // 15, 20, 30, 40...
properties[2] = status;          // Bit 0: On/Off, Bit 1: Tripped
properties[3] = load_percent;    // Current vs rated

// BILT Reward: 50 tokens (important infrastructure)
// Class Required: Master Electrician
```

#### 0x13: Electrical Panel
```c
properties[0] = main_amps;       // 100, 200, 400...
properties[1] = num_breakers;    // Total circuits
properties[2] = status;          // Overall health
properties[3] = load_percent;    // Total load

// BILT Reward: 100 tokens (critical infrastructure)
// Class Required: Master Electrician
```

### HVAC Objects (0x20-0x2F)

#### 0x20: Thermostat
```c
properties[0] = setpoint_temp;   // Target temp (°C + 40)
properties[1] = current_temp;    // Actual temp (°C + 40)
properties[2] = mode;            // 0=Off, 1=Heat, 2=Cool, 3=Auto
properties[3] = fan_mode;        // 0=Auto, 1=On, 2=Circulate

// BILT Reward: 30 tokens
// Class Required: HVAC Tech
```

#### 0x21: Air Vent
```c
properties[0] = damper_percent;  // 0-100% open
properties[1] = airflow_cfm;     // Cubic feet/minute
properties[2] = temperature;     // Supply air temp
properties[3] = zone_id;        // Which HVAC zone

// BILT Reward: 15 tokens per vent
// Class Required: HVAC Tech
```

#### 0x22: VAV Box
```c
properties[0] = airflow_cfm_hi; // High byte of CFM
properties[1] = airflow_cfm_lo; // Low byte of CFM
properties[2] = damper_percent; // Position 0-100%
properties[3] = heating_stage;  // 0=Off, 1-3=Stages

// BILT Reward: 40 tokens (complex equipment)
// Class Required: HVAC Tech
```

### Sensor Objects (0x30-0x3F)

#### 0x30: Temperature Sensor
```c
properties[0] = temp_celsius;    // Temperature + 40
properties[1] = humidity;        // 0-100%
properties[2] = pressure_hi;    // Pressure MSB
properties[3] = pressure_lo;    // Pressure LSB

// BILT Reward: 10 tokens (easy to install)
// Class Required: Any
```

#### 0x31: Motion Sensor
```c
properties[0] = detected;       // 0=No motion, 1=Motion
properties[1] = count;          // People count
properties[2] = timeout_min;    // Minutes before reset
properties[3] = sensitivity;    // 0-255 scale

// BILT Reward: 15 tokens
// Class Required: Any
```

#### 0x32: CO2 Sensor
```c
properties[0] = co2_ppm_hi;    // PPM high byte
properties[1] = co2_ppm_lo;    // PPM low byte
properties[2] = status;         // Air quality level
properties[3] = trend;          // Rising/falling/stable

// BILT Reward: 20 tokens (air quality important)
// Class Required: Any
```

#### 0x33: Light Sensor
```c
properties[0] = lux_hi;        // Illuminance high byte
properties[1] = lux_lo;        // Illuminance low byte
properties[2] = color_temp;    // Kelvin / 100
properties[3] = uv_index;      // UV radiation level

// BILT Reward: 10 tokens
// Class Required: Any
```

### Security Objects (0x40-0x4F)

#### 0x40: Door
```c
properties[0] = status;        // 0=Closed, 1=Open, 2=Ajar
properties[1] = lock_state;    // 0=Unlocked, 1=Locked
properties[2] = access_level;  // Required clearance
properties[3] = alarm_status;  // 0=Normal, 1=Forced, 2=Held

// BILT Reward: 20 tokens
// Class Required: Security or Facilities
```

#### 0x41: Window
```c
properties[0] = status;        // 0=Closed, 1=Open, 2=Broken
properties[1] = lock_state;    // 0=Unlocked, 1=Locked
properties[2] = tint_level;    // 0-100% tinting
properties[3] = alarm_status;  // Security state

// BILT Reward: 15 tokens
// Class Required: Any
```

#### 0x42: Camera
```c
properties[0] = status;        // 0=Off, 1=Recording, 2=Motion
properties[1] = direction;     // 0-255 degrees
properties[2] = zoom_level;    // 1-10x zoom
properties[3] = storage_days;  // Days of storage left

// BILT Reward: 30 tokens
// Class Required: Security
```

### Structural Objects (0x50-0x5F)

#### 0x50: Room
```c
properties[0] = occupancy;     // Number of people
properties[1] = light_level;   // 0-100% brightness
properties[2] = temperature;   // Celsius + 40
properties[3] = air_quality;   // 0-255 scale

// BILT Reward: 50 tokens (defines space)
// Class Required: Facilities Manager
```

#### 0x51: Floor
```c
properties[0] = floor_number;  // 0-255
properties[1] = num_zones;     // Zone count
properties[2] = occupancy_pct; // 0-100% occupied
properties[3] = alert_status;  // Any alerts

// BILT Reward: 100 tokens (major structure)
// Class Required: Facilities Manager
```

#### 0x52: Building
```c
properties[0] = num_floors;    // Total floors
properties[1] = occupancy_pct; // Building occupancy
properties[2] = power_usage;   // % of capacity
properties[3] = system_health; // Overall status

// BILT Reward: 500 tokens (entire building!)
// Class Required: Building Owner
```

### Plumbing Objects (0x60-0x6F)

#### 0x60: Water Valve
```c
properties[0] = valve_percent; // 0-100% open
properties[1] = flow_rate;     // Gallons/minute
properties[2] = pressure;      // PSI
properties[3] = temperature;   // Water temp

// BILT Reward: 25 tokens
// Class Required: Plumber
```

#### 0x61: Water Meter
```c
properties[0] = flow_hi;       // Flow rate high byte
properties[1] = flow_lo;       // Flow rate low byte
properties[2] = total_hi;      // Total usage high
properties[3] = total_lo;      // Total usage low

// BILT Reward: 35 tokens
// Class Required: Plumber
```

### Network Objects (0x70-0x7F)

#### 0x70: WiFi Access Point
```c
properties[0] = channel;       // WiFi channel
properties[1] = client_count;  // Connected devices
properties[2] = signal_strength; // -dBm + 100
properties[3] = bandwidth_pct;  // Usage percent

// BILT Reward: 20 tokens
// Class Required: IT Admin
```

#### 0x71: Network Switch
```c
properties[0] = port_count;    // Total ports
properties[1] = ports_active;  // In use
properties[2] = uplink_speed;  // Gbps
properties[3] = vlan_count;    // VLANs configured

// BILT Reward: 30 tokens
// Class Required: IT Admin
```

#### 0x72: Meshtastic Node
```c
properties[0] = mesh_peers;    // Connected nodes
properties[1] = signal_quality; // 0-255 scale
properties[2] = battery_pct;   // If battery powered
properties[3] = packets_hour;  // Traffic volume

// BILT Reward: 100 tokens (critical infrastructure!)
// Class Required: Mesh Network Admin
```

### Special Objects (0x7F)

#### 0x7F: Player Avatar
```c
properties[0] = player_class;  // Electrician, HVAC, etc
properties[1] = skill_level;   // 1-100 experience
properties[2] = tokens_earned; // BILT balance / 10
properties[3] = guild_id;      // Company/team

// This represents a player in the building
// Shows up on other players' terminals
```

### Discovery Rewards

| Action | BILT Tokens | Achievement |
|--------|-------------|-------------|
| First to map building | 1000 | Pioneer Badge |
| Complete floor mapping | 200 | Cartographer Badge |
| Fix critical fault | 500 | Hero Badge |
| 100 objects mapped | 250 | Contributor Badge |
| Connect mesh node | 100 | Network Badge |

### Object Interactions

Objects can interact like game mechanics:
- **Outlet + Motion Sensor** = Auto-off when room empty
- **Thermostat + Window** = HVAC off when window open
- **Light + Light Sensor** = Daylight harvesting
- **Door + Camera** = Security automation

Players earn bonus BILT for creating useful interactions!

---

→ Next: [Properties Bit-Packing](properties.md)