# Wi-Fi CSI Sensing for Building Intelligence

## Overview

Channel State Information (CSI) from Wi-Fi signals can create a 3D understanding of building occupancy without cameras. This technology uses the perturbations in radio waves to detect presence, movement, and activities.

## How It Works

### 1. Signal Transmission
- Wi-Fi router transmits radio waves (2.4GHz or 5GHz)
- Signals propagate through the building space
- Standard Wi-Fi hardware, no special equipment needed

### 2. Signal Perturbation
When radio waves encounter objects/people:
- **Reflection**: Bounces off surfaces
- **Absorption**: Energy absorbed by materials
- **Diffraction**: Bends around edges
- **Scattering**: Disperses in multiple directions

Human bodies (mostly water) create distinct signatures in the signal.

### 3. CSI Data Collection
```
Channel State Information contains:
- Amplitude (signal strength)
- Phase (timing information)
- Frequency response
- For each OFDM subcarrier (typically 30-114 subcarriers)
```

### 4. Signal Processing Pipeline
```
Raw CSI → Noise Filtering → Feature Extraction → Pattern Recognition → ArxObject
```

## Integration with Arxos Platform

### Scalable Hardware Integration
The same CSI sensing algorithms scale across deployment tiers:

**Tier 1 (Basic)**: No CSI - PIR sensors only
- Simple presence detection
- Battery powered ESP32
- LoRa-only communication

**Tier 2 (Occupancy)**: Basic CSI on ESP32
- Simple presence counting
- Raspberry Pi Zero processing
- LoRa + WiFi communication

**Tier 3 (Activity)**: Advanced CSI processing
- Activity recognition and classification
- Raspberry Pi 4 with ML models
- WiFi backbone with LoRa backup

**Tier 4 (Precision)**: Professional CSI arrays
- Real-time tracking and prediction
- Jetson GPU acceleration
- Dedicated network infrastructure

### Tier-Specific Data Flow
```
Tier 2: ESP32 CSI → Pi Zero → Simple ML → LoRa
Tier 3: Multi-ESP32 → Pi 4 → Advanced ML → WiFi
Tier 4: Sensor Array → Jetson → GPU ML → Fiber
```

## Computational Requirements

### Lightweight (ESP32 Possible)
- Presence detection: ~10 MIPS
- Simple motion detection: ~50 MIPS
- RSSI-based proximity: ~5 MIPS

### Moderate (Raspberry Pi Required)
- Activity recognition: ~500 MIPS
- Fall detection: ~1000 MIPS
- Multi-person tracking: ~2000 MIPS

### Heavy (Not Suitable for Arxos)
- Pose estimation: ~10 GFLOPS
- Gesture recognition: ~5 GFLOPS
- Through-wall imaging: ~20 GFLOPS

## Research References

### Key Papers
1. **MIT CSAIL** - "Capturing the Human Figure Through a Wall" (2018)
   - Demonstrates through-wall pose estimation
   - Uses specialized RF hardware

2. **CMU** - "Towards WiFi-based Human Pose Estimation" (2020)
   - Commodity Wi-Fi for pose detection
   - Deep learning approach

3. **UC Santa Barbara** - "WiFall: Device-free Fall Detection" (2017)
   - Fall detection with commercial routers
   - 87% accuracy with simple classifiers

## Privacy Advantages

### What CSI Cannot Capture
- Facial features
- Skin color
- Clothing details
- Personal identifying marks
- Voice or conversations

### What CSI Can Detect
- Presence/absence
- Number of people
- General activity (walking, sitting, falling)
- Breathing rate (with sufficient resolution)
- Coarse location within room

## Technical Specifications

### CSI Data Format
```c
struct CSI_Sample {
    uint32_t timestamp;      // Microseconds since boot
    uint8_t  mac_addr[6];    // Transmitter MAC
    int8_t   rssi;           // Received signal strength
    uint8_t  channel;        // Wi-Fi channel
    uint16_t subcarriers[64]; // Complex values (amplitude + phase)
};
// Total: ~140 bytes per sample
```

### Compressed ArxObject Format
```c
struct CSI_ArxObject {
    uint16_t id;           // 0x8000 range for temporal objects
    uint8_t  type;         // 0x80: presence, 0x81: motion, 0x82: fall
    uint16_t x, y, z;      // Position in mm
    uint8_t  confidence;   // 0-255 detection confidence
    uint8_t  person_count; // Number of people detected
    uint8_t  activity;     // Activity classification
    uint8_t  reserved;     // Future use
};
// Total: 13 bytes (maintains protocol)
```

## Implementation Considerations

### Challenges
1. **Multipath interference** - Reflections create noise
2. **Environmental changes** - Furniture movement affects baseline
3. **Processing latency** - Real-time requirements for emergency detection
4. **Power consumption** - Continuous CSI sampling drains battery

### Solutions
1. **Adaptive filtering** - Learn environment baseline
2. **Differential CSI** - Track changes, not absolutes
3. **Edge processing** - Distribute computation
4. **Duty cycling** - Sample on motion trigger

## Future Research Directions

1. **LoRa-based sensing** - Use 915MHz for better penetration
2. **Multi-modal fusion** - Combine CSI with ArxObject static map
3. **Federated learning** - Improve models without sharing data
4. **Mesh-based sensing** - Use entire mesh network as distributed antenna

## Prototype Requirements

### Minimum Viable Prototype
- 1x ESP32 with CSI firmware
- 1x Raspberry Pi 4 for processing
- Router with monitor mode support
- Test environment with controlled movement

### Software Stack
```
ESP32:
- ESP-IDF with CSI collection
- UDP streaming to Pi

Raspberry Pi:
- Python CSI processing library
- scikit-learn for classification
- ArxObject encoder
- LoRa broadcast module
```

## Ethical Considerations

While CSI sensing is privacy-preserving by nature, we must consider:
- Consent for monitoring
- Data retention policies
- Activity inference boundaries
- Emergency override protocols

The system should default to maximum privacy with opt-in for enhanced features.