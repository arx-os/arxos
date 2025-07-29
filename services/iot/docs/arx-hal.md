# ArxHAL (Hardware Abstraction Layer)

## Overview

ArxHAL (Hardware Abstraction Layer) defines semantic interfaces for building systems regardless of physical hardware. It provides a standardized way to describe device capabilities, inputs, outputs, and behaviors in a vendor-agnostic manner.

## Purpose

ArxHAL enables:
- **Vendor Neutrality**: Define device interfaces without being tied to specific hardware
- **Interoperability**: Standardize communication between different device types
- **Scalability**: Easily add new device types and capabilities
- **Maintainability**: Centralized device definitions and behavior profiles

## Schema Structure

### Basic Schema Format

```json
{
  "$schema": "https://arxos.dev/specs/arxhal.schema.json",
  "object_type": "device_type",
  "version": "1.0.0",
  "description": "Device description",
  "inputs": {
    "sensor_name": {
      "unit": "unit_of_measurement",
      "type": "float|int|boolean",
      "description": "Sensor description",
      "range": [min_value, max_value],
      "accuracy": "accuracy_specification"
    }
  },
  "outputs": {
    "control_name": {
      "type": "float|int|boolean",
      "description": "Control description",
      "range": [min_value, max_value],
      "default": default_value
    }
  },
  "behavior_profile": "profile_name",
  "alarms": {
    "alarm_name": {
      "description": "Alarm description",
      "threshold": threshold_value,
      "unit": "unit_of_measurement",
      "severity": "info|warning|error|critical"
    }
  },
  "metadata": {
    "manufacturer": "vendor_name",
    "model": "model_name",
    "category": "device_category",
    "tags": ["tag1", "tag2"]
  }
}
```

### Input Fields

Input fields represent sensors and measurements:

- **unit**: Unit of measurement (e.g., "°C", "ppm", "%")
- **type**: Data type ("float", "int", "boolean")
- **description**: Human-readable description
- **range**: Optional [min, max] range for validation
- **accuracy**: Optional accuracy specification
- **protocol_mapping**: Optional protocol-specific mappings

### Output Fields

Output fields represent controls and actuators:

- **type**: Data type ("float", "int", "boolean")
- **description**: Human-readable description
- **unit**: Optional unit of measurement
- **range**: Optional [min, max] range for validation
- **default**: Default value for the output
- **protocol_mapping**: Optional protocol-specific mappings

### Behavior Profiles

Behavior profiles define how devices should behave:

- **Standard Profiles**: Predefined behavior patterns
- **Custom Profiles**: Device-specific behaviors
- **Conditional Logic**: Rules for different operating modes

### Alarms

Alarm definitions for monitoring and alerting:

- **Threshold-based**: Numeric thresholds with units
- **Boolean-based**: True/false alarm conditions
- **Severity Levels**: info, warning, error, critical

## Device Types

### HVAC Devices

#### Air Handling Units (AHU)
```json
{
  "object_type": "ahu",
  "inputs": {
    "temp_sensor": { "unit": "°C", "type": "float" },
    "co2_sensor": { "unit": "ppm", "type": "int" },
    "pressure_sensor": { "unit": "Pa", "type": "float" }
  },
  "outputs": {
    "fan_relay": { "type": "boolean" },
    "damper_position": { "unit": "%", "type": "float" },
    "heating_valve": { "unit": "%", "type": "float" }
  }
}
```

#### Variable Air Volume (VAV)
```json
{
  "object_type": "vav",
  "inputs": {
    "temperature": { "unit": "°C", "type": "float" },
    "pressure": { "unit": "Pa", "type": "float" },
    "airflow": { "unit": "m³/h", "type": "float" }
  },
  "outputs": {
    "damper_position": { "unit": "%", "type": "float" },
    "fan_status": { "type": "boolean" }
  }
}
```

### Lighting Devices

#### LED Controllers
```json
{
  "object_type": "led_controller",
  "inputs": {
    "motion_sensor": { "type": "boolean" },
    "ambient_light": { "unit": "lux", "type": "float" }
  },
  "outputs": {
    "brightness": { "unit": "%", "type": "float" },
    "color_temp": { "unit": "K", "type": "float" },
    "power_state": { "type": "boolean" }
  }
}
```

### Security Devices

#### Access Control
```json
{
  "object_type": "access_control",
  "inputs": {
    "card_reader": { "type": "boolean" },
    "door_sensor": { "type": "boolean" },
    "motion_sensor": { "type": "boolean" }
  },
  "outputs": {
    "door_lock": { "type": "boolean" },
    "alarm": { "type": "boolean" },
    "indicator_light": { "type": "boolean" }
  }
}
```

## Protocol Mapping

ArxHAL schemas can include protocol-specific mappings:

```json
{
  "inputs": {
    "temperature": {
      "unit": "°C",
      "type": "float",
      "protocol_mapping": {
        "modbus": {
          "register": 40001,
          "type": "float",
          "scale": 1.0
        },
        "mqtt": {
          "topic": "sensor/temperature",
          "type": "float"
        }
      }
    }
  }
}
```

## Validation

Use the ArxHAL validator to ensure schema compliance:

```bash
# Validate a single schema
python tools/validate_schema.py arx-hal/schemas/ahu_schema.json

# Validate all schemas in a directory
python tools/validate_schema.py --validate-all arx-hal/

# Generate an example schema
python tools/validate_schema.py --generate-example example.json
```

## Best Practices

### Naming Conventions
- Use descriptive, lowercase names for fields
- Separate words with underscores
- Be consistent across similar device types

### Documentation
- Provide clear descriptions for all fields
- Include units where applicable
- Document any special requirements or limitations

### Versioning
- Use semantic versioning (X.Y.Z)
- Increment version when making breaking changes
- Maintain backward compatibility when possible

### Testing
- Validate schemas before deployment
- Test with real hardware when possible
- Include unit tests for complex behaviors

## Integration with Arxos

ArxHAL schemas integrate with:

- **Device Registry**: Automatic device type registration
- **Telemetry API**: Standardized data collection
- **ArxDrivers**: Protocol-specific mappings
- **ArxLink**: Communication protocol compatibility

## Contributing

To contribute ArxHAL schemas:

1. Create a new schema file in `arx-hal/schemas/`
2. Follow the established format and conventions
3. Include comprehensive documentation
4. Test with the validation tool
5. Submit for review and approval

## Examples

See the `arx-hal/examples/` directory for complete device definitions:

- `belimo_vav_example.json`: VAV device with protocol mappings
- `ahu_schema.json`: Complete AHU schema definition
- Additional examples for various device types

## Resources

- [ArxHAL Schema Specification](https://arxos.dev/specs/arxhal.schema.json)
- [Validation Tool Documentation](tools/validate_schema.py)
- [Device Type Catalog](examples/)
- [Contributing Guidelines](contributing.md) 