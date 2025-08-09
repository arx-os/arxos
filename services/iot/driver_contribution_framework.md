# ArxDriver Contribution Framework

## Overview

The ArxDriver Contribution Framework enables open contribution of hardware drivers and configurations to the Arxos platform. Contributors earn usage-based shares of hardware metadata value, similar to markup shares for buildings.

## Purpose

This framework allows Arxos to decentralize the development of hardware integrations while fairly compensating field technicians, developers, and engineers who contribute. Arxos becomes the canonical registry of open, trusted infrastructure drivers — maintained by the people who build and maintain the systems themselves.

## Core Components

### ArxDriver

A declarative YAML config that maps a physical device to an ArxObject using protocols like MQTT, LoRa, BACnet, etc.

**Specifications:**
- **Versioning**: Git commit-based
- **Format**: YAML (.yaml)
- **Registry**: arxos_registry/arxdrivers/
- **Fields**:
  - `id`: Unique object-type.driver identifier
  - `protocol`: Communication protocol
  - `mapping`: Data field mappings
  - `logic`: Optional fault or behavior rules
  - `shares`: List of contributors with share percentages
  - `linked_hardware`: Manufacturer + SKU metadata

### Example ArxDriver

```yaml
id: sensor.temp.lora.milesight_em300th
type: driver
object_type: sensor.temp.lora
protocol: lora
status: published
source: community
version: 1.0.0
shares:
  - user_id: user_123
    username: electric.james
    pct: 0.6
    contribution: Created and tested initial ArxDriver
  - user_id: user_456
    username: edge.marina
    pct: 0.25
    contribution: Added MQTT fault mappings
  - user_id: arxos_bot
    pct: 0.15
    contribution: Auto-parsed manufacturer specs
linked_hardware:
  manufacturer: Milesight
  model: EM300-TH
  sku: MS-EM300-TH
  datasheet_url: https://milesight.com/EM300-TH
```

## Contributor Roles

### 1. Driver Author
- **Description**: Writes and uploads initial ArxDriver
- **Responsibilities**:
  - Create driver configuration
  - Define data mappings
  - Document hardware specifications
  - Test basic functionality

### 2. Hardware Tester
- **Description**: Installs and validates device
- **Responsibilities**:
  - Physical device installation
  - Field testing and validation
  - Performance benchmarking
  - Real-world usage testing

### 3. Fault Simulator
- **Description**: Creates edge case tests and triggers
- **Responsibilities**:
  - Stress testing scenarios
  - Edge case identification
  - Failure mode analysis
  - Recovery testing

### 4. Metadata Curator
- **Description**: Parses hardware specs or adds to ArxIndex
- **Responsibilities**:
  - Extract manufacturer specifications
  - Standardize metadata formats
  - Maintain hardware database
  - Quality assurance

### 5. Field Verifier
- **Description**: Uploads photo proof or QR scan of real installation
- **Responsibilities**:
  - Document real installations
  - Provide installation photos
  - Verify hardware compatibility
  - Community validation

## Usage Triggers & Revenue Sharing

### 1. Driver Install
- **Description**: A device driver is installed via CLI or automatically matched in the field
- **Payout**: usage_weighted
- **Source**: enterprise tier fee or subscription
- **Revenue Model**: Based on usage frequency and enterprise tier

### 2. ArxKit Export
- **Description**: Hardware is included in a BOM for an ArxKit export or job install
- **Payout**: fixed_split
- **Source**: margin on kit or referral
- **Revenue Model**: Fixed percentage of kit markup

### 3. Driver Matched
- **Description**: Driver is auto-matched to a live sensor and used in runtime monitoring
- **Payout**: usage_weighted
- **Source**: live data subscription
- **Revenue Model**: Based on data usage and monitoring time

### 4. ArxReady Certification
- **Description**: Contributor provides field proof, testing results, or lab certs that move a device into the ArxReady category
- **Payout**: bonus
- **Source**: certification or QA budget
- **Revenue Model**: One-time bonus for certification

## Payout Model

### Currency & Method
- **Currency**: Fiat or ArxCredit token
- **Method**: Linked payout wallet (e.g. PayPal or bank)
- **Frequency**: Quarterly
- **Threshold**: $25 minimum before payout is triggered

### Transparency
- All payouts and shares are publicly auditable
- Git-based versioning ensures transparency
- Public ledger with build + use logs

## Governance

### Curation
- Maintained by Arxos Foundation core team
- Quality standards and review processes
- Technical validation and security checks

### Disputes
- Contributor voting or DAO-style claim board
- Transparent dispute resolution process
- Community-driven decision making

### Auditability
- All share assignments and payout records are transparent and Git-based
- Public audit trail for all transactions
- Version control for all driver configurations

## Getting Started

### 1. Create an ArxDriver

```yaml
# Example: Temperature Sensor Driver
id: sensor.temp.mqtt.dht22
type: driver
object_type: sensor.temp
protocol: mqtt
status: draft
source: community
version: 1.0.0
shares:
  - user_id: your_user_id
    username: your_username
    pct: 1.0
    contribution: Initial driver creation
linked_hardware:
  manufacturer: DHT
  model: DHT22
  sku: DHT22-SENSOR
  datasheet_url: https://example.com/dht22
mapping:
  temperature:
    mqtt_topic: "sensor/dht22/temperature"
    data_type: float
    unit: celsius
    range: [-40, 80]
  humidity:
    mqtt_topic: "sensor/dht22/humidity"
    data_type: float
    unit: percent
    range: [0, 100]
logic:
  fault_detection:
    - condition: "temperature < -40 or temperature > 80"
      action: "mark_sensor_faulty"
    - condition: "humidity < 0 or humidity > 100"
      action: "mark_sensor_faulty"
```

### 2. Submit for Review

1. Create a pull request to the arxos_registry/arxdrivers/ repository
2. Include hardware specifications and datasheets
3. Provide testing documentation
4. Add installation instructions

### 3. Community Validation

- Peer review by other contributors
- Field testing by hardware testers
- Metadata validation by curators
- Security review by security contributors

### 4. Publication

Once approved:
- Driver is published to the registry
- Contributors receive their share assignments
- Driver becomes available for installation
- Usage tracking begins

## Best Practices

### Driver Development
- Follow YAML formatting standards
- Include comprehensive hardware documentation
- Provide clear data mapping specifications
- Add fault detection logic where applicable
- Test thoroughly before submission

### Documentation
- Include manufacturer datasheets
- Provide installation instructions
- Document testing procedures
- Add troubleshooting guides
- Include performance benchmarks

### Quality Assurance
- Validate all data mappings
- Test edge cases and failure modes
- Verify hardware compatibility
- Ensure security compliance
- Document known limitations

## Integration with Arxos Platform

### Device Registry Integration
- Drivers automatically register devices in the BAS & IoT platform
- Telemetry data flows through validated drivers
- Device health monitoring uses driver specifications

### Security Integration
- Security validation occurs through the arx-security framework
- Hardware threat detection uses driver metadata
- Firmware security assessment leverages driver specifications

### Analytics Integration
- Performance analytics use driver-defined metrics
- Usage tracking enables revenue sharing
- Quality metrics inform driver improvements

## Support and Resources

### Documentation
- [Arxos Platform Documentation](../arx-docs/)
- [BAS & IoT Platform Guide](README.md)
- [Security Framework](../arx-security/)

### Community
- Contributor forums and discussions
- Peer review and collaboration
- Mentorship and training programs

### Tools
- Driver validation tools
- Testing frameworks
- Documentation templates
- Revenue tracking dashboards

## License and Terms

This framework operates under the Arxos platform license and terms. All contributions are subject to the project's license and confidentiality agreements.

---

*This framework enables the decentralized development of hardware integrations while ensuring fair compensation for contributors and maintaining high quality standards.*
