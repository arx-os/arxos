# Hybrid RF Sensing Architecture

## Overview

Combining multiple RF frequencies (LoRa 915MHz, Wi-Fi 2.4/5GHz) to create multi-resolution occupancy awareness with complementary strengths.

## Frequency Characteristics

### LoRa (915MHz)
```
Wavelength: 33cm
Penetration: Excellent (through multiple walls)
Resolution: Coarse (room-level)
Range: 1-10km
Data Rate: 250kbps
Power: Ultra-low (coin cell battery)
```

### Wi-Fi 2.4GHz
```
Wavelength: 12.5cm
Penetration: Good (1-2 walls)
Resolution: Fine (sub-meter)
Range: 30-100m
Data Rate: 150Mbps
Power: Moderate (needs USB power)
```

### Wi-Fi 5GHz
```
Wavelength: 6cm
Penetration: Poor (line of sight)
Resolution: Very fine (centimeter)
Range: 10-50m
Data Rate: 1Gbps
Power: Higher (needs wall power)
```

## Multi-Resolution Sensing Strategy

```
┌─────────────────────────────────────────┐
│          Hybrid RF Sensing Layers        │
├─────────────────────────────────────────┤
│                                           │
│  Layer 1: LoRa Coarse Detection          │
│  ┌─────────────────────────────────┐    │
│  │ • Building-wide coverage         │    │
│  │ • Presence/absence per room      │    │
│  │ • Through-wall capability        │    │
│  │ • Ultra-low power                │    │
│  └─────────────────────────────────┘    │
│                    ↓                      │
│  Layer 2: WiFi 2.4GHz Activity           │
│  ┌─────────────────────────────────┐    │
│  │ • Room-level activity tracking   │    │
│  │ • Walking/sitting/standing       │    │
│  │ • People counting                │    │
│  │ • Moderate power                 │    │
│  └─────────────────────────────────┘    │
│                    ↓                      │
│  Layer 3: WiFi 5GHz Precision            │
│  ┌─────────────────────────────────┐    │
│  │ • Exact positioning              │    │
│  │ • Gesture recognition            │    │
│  │ • Fall detection                 │    │
│  │ • High power                     │    │
│  └─────────────────────────────────┘    │
└─────────────────────────────────────────┘
```

## Sensing Modes

### Mode 1: Ultra-Low Power (LoRa Only)
```rust
struct UltraLowPowerMode {
    active_sensors: LoRaOnly,
    detection: PresenceAbsence,
    resolution: RoomLevel,
    battery_life: Years(5),
    use_cases: ["Vacation homes", "Storage areas", "Rarely used spaces"],
}
```

### Mode 2: Balanced (LoRa + 2.4GHz)
```rust
struct BalancedMode {
    active_sensors: LoRaPlusWiFi24,
    detection: ActivityRecognition,
    resolution: SubMeter,
    battery_life: Months(6),
    use_cases: ["Offices", "Classrooms", "Living spaces"],
}
```

### Mode 3: High Precision (All Frequencies)
```rust
struct HighPrecisionMode {
    active_sensors: AllFrequencies,
    detection: DetailedTracking,
    resolution: Centimeter,
    battery_life: Days(30),
    use_cases: ["Healthcare", "Security zones", "Elderly care"],
}
```

## Cascade Activation

### Power-Efficient Cascading
```python
def cascade_sensing():
    # Always-on LoRa monitoring
    if lora_detects_presence():
        
        # Activate WiFi 2.4GHz for detail
        wifi_24 = activate_wifi_24ghz()
        activity = wifi_24.classify_activity()
        
        if activity == UNUSUAL or activity == FALL_SUSPECTED:
            
            # Activate WiFi 5GHz for precision
            wifi_5 = activate_wifi_5ghz()
            precise_detection = wifi_5.analyze_detail()
            
            if precise_detection == EMERGENCY:
                broadcast_emergency()
        
        # Power down when not needed
        if no_activity_for(minutes=5):
            wifi_5.sleep()
        if no_activity_for(minutes=15):
            wifi_24.sleep()
```

## Complementary Strengths

### LoRa Strengths
- **Through-wall detection**: See into closed rooms
- **Whole-building coverage**: Single sensor per floor
- **Battery operation**: No wiring needed
- **Weather resistant**: Outdoor deployment

### WiFi 2.4GHz Strengths
- **Activity classification**: Identify what people are doing
- **Multiple people tracking**: Count and track groups
- **Existing infrastructure**: Use current routers
- **Good balance**: Power vs capability

### WiFi 5GHz Strengths
- **Precise localization**: Centimeter-level accuracy
- **Gesture recognition**: Detect specific movements
- **High-speed tracking**: Fast-moving objects
- **Rich data**: Detailed CSI information

## Data Fusion Algorithm

### Weighted Combination
```python
def fuse_rf_data(lora_data, wifi24_data, wifi5_data):
    """
    Combine multi-frequency data for best estimate
    """
    
    # Weights based on signal quality and relevance
    weights = calculate_weights(
        lora_snr=lora_data.signal_quality,
        wifi24_snr=wifi24_data.signal_quality,
        wifi5_snr=wifi5_data.signal_quality if wifi5_data else 0
    )
    
    # Presence confidence (LoRa weighted heavily)
    presence = (
        weights.lora * lora_data.presence +
        weights.wifi24 * wifi24_data.presence * 0.5
    )
    
    # Position estimate (WiFi weighted heavily)
    if wifi5_data:
        position = wifi5_data.position  # Most accurate
    elif wifi24_data:
        position = wifi24_data.position  # Good enough
    else:
        position = lora_data.zone_center  # Coarse fallback
    
    # Activity classification (WiFi 2.4 optimal)
    activity = wifi24_data.activity if wifi24_data else UNKNOWN
    
    return FusedDetection(presence, position, activity)
```

## Interference Mitigation

### Frequency Separation
```
LoRa:   902-928 MHz (spread spectrum)
WiFi:   2400-2483 MHz (channels 1-11)
        5150-5825 MHz (channels 36-165)

Separation: >1.5 GHz (no interference)
```

### Time Division
```python
def time_division_sensing():
    """
    Alternate between frequencies to avoid interference
    """
    schedule = [
        (0,   100,  "LoRa"),     # 0-100ms: LoRa
        (100, 200,  "WiFi_24"),  # 100-200ms: WiFi 2.4
        (200, 300,  "WiFi_5"),   # 200-300ms: WiFi 5
        (300, 1000, "Idle"),     # 300-1000ms: Rest
    ]
    
    for start_ms, end_ms, mode in schedule:
        activate_mode(mode)
        collect_data(duration_ms=end_ms-start_ms)
        deactivate_mode(mode)
```

## Hardware Configuration

### Minimal Setup
```yaml
Per Room:
  - 1x ESP32 (LoRa + WiFi)
  - Power: Battery or USB
  - Cost: ~$15

Per Floor:
  - 1x Raspberry Pi 4
  - Power: Wall adapter
  - Cost: ~$75

Total for 10-room building: ~$300
```

### Optimal Setup
```yaml
Per Room:
  - 2x ESP32 (redundancy)
  - 1x Dedicated CSI collector
  - Power: PoE or USB
  - Cost: ~$45

Per Floor:
  - 2x Raspberry Pi 4 (redundancy)
  - 1x LoRa gateway
  - Power: UPS backed
  - Cost: ~$200

Total for 10-room building: ~$850
```

## Performance Comparison

### Detection Capabilities
```
Metric              LoRa    WiFi2.4  WiFi5   Hybrid
-------------------------------------------------
Presence            Good    Excellent Excel  Excellent
Through-wall        Excel   Good      Poor   Excellent
People counting     Poor    Good      Excel  Excellent
Activity class      None    Good      Excel  Excellent
Fall detection      Poor    Good      Excel  Excellent
Power usage         Excel   Good      Poor   Adaptive
Coverage            Excel   Good      Poor   Excellent
```

## Use Case Examples

### Office Building
```python
def office_building_config():
    return {
        "open_areas": {
            "mode": "WiFi_24",  # Good coverage, activity tracking
            "cascade": True,     # Activate 5GHz if needed
        },
        "private_offices": {
            "mode": "LoRa",      # Privacy, through-door detection
            "cascade": False,    # Respect privacy
        },
        "bathrooms": {
            "mode": "Hybrid",    # All frequencies for safety
            "emergency": True,   # Fall detection enabled
        },
        "stairwells": {
            "mode": "LoRa",      # Concrete penetration
            "cascade": True,     # Safety monitoring
        }
    }
```

### Elderly Care Facility
```python
def elderly_care_config():
    return {
        "all_areas": {
            "mode": "Hybrid",        # Maximum safety
            "fall_detection": True,  # Always active
            "privacy_mode": True,    # No identification
            "alert_threshold": "Low", # Sensitive to falls
        }
    }
```

### School
```python
def school_config():
    return {
        "classrooms": {
            "mode": "LoRa",         # Privacy for students
            "occupancy_only": True, # Count, don't track
        },
        "hallways": {
            "mode": "WiFi_24",      # Traffic flow monitoring
            "crowd_detection": True,
        },
        "emergency": {
            "mode": "Hybrid",       # All sensors active
            "evacuation_mode": True,
        }
    }
```

## Future Research

### LoRa CSI Exploration
- Can LoRa signals provide CSI-like data?
- Lower frequency = better penetration
- Possible coarse activity detection?

### Frequency Hopping
- Dynamic frequency selection
- Avoid interference automatically
- Optimize for environment

### AI-Driven Selection
- Learn optimal frequency per zone
- Adaptive to building materials
- Self-optimizing over time

## Conclusion

Hybrid RF sensing combines the best of multiple frequencies:
- LoRa for coverage and power efficiency
- WiFi 2.4GHz for balanced activity detection  
- WiFi 5GHz for precision when needed

By cascading activation based on need, we achieve comprehensive building awareness while minimizing power consumption. The system adapts to requirements, providing coarse detection everywhere with precision on demand, all while maintaining complete privacy through the ArxObject protocol.