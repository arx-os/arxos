# Arxos Open Hardware Platform Integration

## Overview

The Arxos Open Hardware Platform provides a comprehensive, vendor-agnostic integration layer for building systems hardware using open protocols, hardware abstraction, and reference firmware. This specification defines how any BAS/IoT hardware can have a home within the Arxos ecosystem.

## Integration with Existing IoT Service

This hardware platform specification extends and enhances the existing IoT service (`arxos/services/iot/`) by providing:

1. **Hardware Abstraction Layer (ArxHAL)** - Standardized device interfaces
2. **Protocol Drivers (ArxDrivers)** - Vendor-agnostic hardware mappings
3. **Communication Protocol (ArxLink)** - Lightweight, secure device communication
4. **Reference Firmware** - Open-source firmware for common platforms
5. **Development Tools** - Flashing, simulation, and validation tools

## Architecture Layers

### 1. ArxHAL (Hardware Abstraction Layer)

Defines semantic interfaces for building systems regardless of physical hardware:

```json
{
  "object_type": "ahu",
  "inputs": {
    "temp_sensor": { "unit": "°C", "type": "float" },
    "co2_sensor": { "unit": "ppm", "type": "int" }
  },
  "outputs": {
    "fan_relay": { "type": "boolean" },
    "damper_position": { "unit": "%", "type": "float" }
  },
  "behavior_profile": "ahu_standard_v1"
}
```

**Integration Points:**
- Extends existing `device_registry.py` with standardized device types
- Provides consistent interface for `telemetry_api.py` data collection
- Enables unified device management across all hardware vendors

### 2. ArxDrivers (Protocol Drivers)

Maps real hardware to ArxHAL-compatible formats:

```yaml
device_id: belimo-vav-01
protocol: modbus
register_map:
  temperature: { address: 40001, type: float }
  damper_position: { address: 40003, type: float }
  fan_status: { address: 10001, type: bool }
mapped_to: ahu
```

**Integration Points:**
- Extends existing `driver_contribution_framework.md` with standardized driver format
- Provides protocol-specific mappings for `telemetry_api.py`
- Enables vendor-agnostic device registration in `device_registry.py`

### 3. ArxLink (Communication Protocol)

Lightweight protocol for device communication:

```json
{
  "type": "object_update",
  "timestamp": 1724382371,
  "object_id": "ahu-001",
  "values": {
    "temp_sensor": 23.5,
    "co2_sensor": 840,
    "fan_relay": true
  }
}
```

**Integration Points:**
- Replaces existing `protocol/arxlink_sync.py` with enhanced specification
- Provides secure, transport-agnostic communication
- Supports multiple transport layers: MQTT, TCP, Serial, LoRa, BLE

### 4. Reference Firmware

Open-source firmware for common platforms:

- **ESP32**: ESP-IDF and Arduino-compatible source code
- **Raspberry Pi**: Gateway device firmware
- **Arduino**: RF node firmware (extends existing `firmware/rf_node.ino`)

## Implementation Roadmap

### Phase 1: ArxHAL Schema Definitions
- [ ] Define JSON schemas for major building systems (AHU, VAV, lighting, security)
- [ ] Create example device definitions
- [ ] Integrate with existing `device_registry.py`

### Phase 2: Protocol Drivers
- [ ] Implement core protocols (Modbus, MQTT, BACnet)
- [ ] Create vendor-specific driver mappings
- [ ] Extend `driver_contribution_framework.md`

### Phase 3: Reference Firmware
- [ ] Develop ESP32 firmware with ArxLink client
- [ ] Create Raspberry Pi gateway firmware
- [ ] Enhance existing Arduino RF node firmware

### Phase 4: ArxLink Implementation
- [ ] Implement Go and Python agents
- [ ] Add packet simulation and testing
- [ ] Integrate with existing telemetry collection

### Phase 5: Development Tools
- [ ] Create flashing tools for firmware deployment
- [ ] Implement hardware simulators
- [ ] Add packet testing and validation tools

### Phase 6: Documentation
- [ ] Complete developer documentation
- [ ] Create integrator guides
- [ ] Provide contribution guidelines

## Directory Structure

```
arxos/services/iot/
├── hardware_platform_specification.json    # This specification
├── HARDWARE_PLATFORM_INTEGRATION.md       # This documentation
├── arx-hal/                               # Hardware Abstraction Layer
│   ├── schemas/                           # JSON schemas
│   └── examples/                          # Example definitions
├── arx-drivers/                           # Protocol drivers
│   ├── protocols/                         # Protocol mappings
│   ├── vendor/                           # Commercial drivers
│   └── custom/                           # Open-source drivers
├── arxlink/                              # Communication protocol
│   ├── spec/                             # Protocol specification
│   ├── clients/                          # Edge agents
│   └── tests/                            # Testing tools
├── firmware/                             # Reference firmware
│   ├── esp32/                            # ESP32 firmware
│   └── rpi/                              # Raspberry Pi firmware
├── tools/                                # Development tools
│   ├── flash.py                          # Firmware flashing
│   ├── simulate_hardware.py              # Hardware simulation
│   └── packet_tester.py                  # Protocol testing
└── docs/                                 # Documentation
    ├── arx-hal.md                        # HAL documentation
    ├── arx-drivers.md                    # Driver documentation
    ├── arxlink-protocol.md               # Protocol documentation
    └── contributing.md                    # Contribution guidelines
```

## Security Features

- **Encryption**: NaCl (libsodium) with Ed25519 keys
- **Authentication**: Device certificates and checksum-based integrity
- **Packet Signing**: Ensures message authenticity
- **Offline Mode**: Works without cloud connectivity
- **Vendor Agnostic**: 100% compatibility across all hardware vendors

## Interoperability

- **Vendor Compatibility**: Works with any BACnet, Modbus, or proprietary API
- **Offline Operation**: Full functionality without cloud connectivity
- **BIM Compatibility**: Integrates with ASCII BIM standards
- **Cloud Optional**: ArxLink and CLI work standalone

## Technology Stack

- **Packet Transport**: MQTT, TCP, Serial, LoRa, BLE
- **Protocol Format**: JSON, MessagePack
- **Firmware Languages**: C++ (Arduino), Python3, ESP-IDF
- **Agent Languages**: Go, Python
- **Security Libraries**: libsodium, OpenSSL (fallback)

## Philosophy

### Goals
- Enable open, interoperable control of building systems
- Treat every device as an ArxObject, regardless of vendor
- Support both low-cost and high-end deployments
- Ensure decentralized, secure communication at the edge

### Non-Goals
- Replace Linux with a full OS
- Force use of Arxos Cloud (ArxLink and CLI must work standalone)
- Mandate custom hardware for adoption

## Integration with Existing Components

### Device Registry Integration
The hardware platform extends the existing `device_registry.py` with:
- Standardized device type definitions via ArxHAL
- Protocol-specific driver mappings
- Vendor-agnostic device registration

### Telemetry API Integration
The `telemetry_api.py` is enhanced with:
- Unified data collection across all hardware types
- Protocol-agnostic data processing
- Standardized telemetry format

### Driver Framework Integration
The existing `driver_contribution_framework.md` is extended with:
- Standardized driver format (YAML/Python)
- Revenue sharing for hardware drivers
- Quality assurance processes

## Next Steps

1. **Review and Approve**: This specification should be reviewed by the Arxos development team
2. **Create Implementation Plan**: Develop detailed implementation tasks for each phase
3. **Set Up Development Environment**: Prepare the directory structure and development tools
4. **Begin Phase 1**: Start with ArxHAL schema definitions for major building systems
5. **Establish Contribution Guidelines**: Create clear guidelines for community contributions

## Contributing

To contribute to the Arxos Open Hardware Platform:

1. **Define Drivers**: Add YAML or Python files to `arx-drivers/custom/` with mappings
2. **Submit Hardware**: Fork and submit under `firmware/` or `vendor/`
3. **Validate Schemas**: Use the provided CLI tool in `tools/validate_schema.py`

This platform provides a comprehensive foundation for integrating any BAS/IoT hardware into the Arxos ecosystem while maintaining vendor neutrality and open standards.
