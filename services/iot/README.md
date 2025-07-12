# Arxos BAS & IoT Platform

A comprehensive Building Automation System (BAS) and Internet of Things (IoT) platform for smart building management and device telemetry.

## Overview

The Arxos BAS & IoT Platform provides a complete solution for managing building automation systems, IoT devices, and real-time telemetry data. It includes device registry management, telemetry collection, RF node integration, and integration with the broader Arxos ecosystem.

## Features

### Device Registry
- **Device Management**: Register, update, and manage IoT devices and BAS components
- **Device Discovery**: Automatic discovery of new devices on the network
- **Device Classification**: Categorize devices by type, manufacturer, and capabilities
- **Health Monitoring**: Track device status, connectivity, and performance metrics
- **Configuration Management**: Store and manage device configurations and settings

### Telemetry API
- **Real-time Data Collection**: Collect telemetry data from various device types
- **Data Processing**: Process and normalize telemetry data for analysis
- **Data Storage**: Store telemetry data with efficient compression and indexing
- **Data Export**: Export telemetry data in various formats (JSON, CSV, Parquet)
- **Alerting**: Configure alerts based on telemetry thresholds and conditions

### RF Node Integration
- **Arduino Firmware**: Complete firmware for RF mesh network nodes
- **Mesh Networking**: Support for mesh network topology and routing
- **Synchronization Protocol**: ArxLink protocol for device synchronization
- **Security**: Encrypted communication and authentication

### Integration Capabilities
- **Arxos Ecosystem**: Seamless integration with other Arxos components
- **Building Models**: Link devices to building models and floor plans
- **Compliance**: Support for building code compliance and AHJ requirements
- **Analytics**: Integration with Arxos analytics for building performance insights

### Driver Contribution Framework
- **ArxDriver System**: Open framework for hardware driver contributions
- **Revenue Sharing**: Usage-based compensation for contributors
- **Quality Assurance**: Multi-role validation and testing
- **Community Governance**: Transparent review and approval processes

## Architecture

```
arx-bas-iot/
├── device_registry.py      # Device management and registry
├── telemetry_api.py        # Telemetry collection and processing
├── firmware/              # Arduino firmware for RF nodes
│   └── rf_node.ino        # RF node firmware
├── protocol/              # Communication protocols
│   └── arxlink_sync.py    # ArxLink synchronization protocol
├── requirements.txt        # Python dependencies
├── README.md              # This file
├── driver_contribution_framework.md  # Driver contribution framework
└── tests/                 # Test suite
    ├── test_device_registry.py
    └── test_telemetry_api.py
```

## Installation

1. Clone the repository:
```bash
git clone https://github.com/arxos/arx-bas-iot.git
cd arx-bas-iot
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Initialize the database:
```python
from device_registry import DeviceRegistry
registry = DeviceRegistry()
registry.initialize_database()
```

## Usage

### Device Registry

```python
from device_registry import DeviceRegistry

# Initialize registry
registry = DeviceRegistry()

# Register a new device
device = registry.register_device(
    device_id="sensor_001",
    device_type="temperature_sensor",
    manufacturer="Arxos",
    model="TEMP-100",
    location="Building A, Floor 1, Room 101",
    capabilities=["temperature", "humidity"],
    coordinates={"x": 10.5, "y": 20.3, "z": 2.1}
)

# Get device information
device_info = registry.get_device("sensor_001")

# Update device status
registry.update_device_status("sensor_001", "online", {"last_seen": "2024-01-15T10:30:00Z"})
```

### Telemetry API

```python
from telemetry_api import TelemetryAPI

# Initialize telemetry API
telemetry = TelemetryAPI()

# Submit telemetry data
telemetry.submit_data(
    device_id="sensor_001",
    timestamp="2024-01-15T10:30:00Z",
    data={
        "temperature": 22.5,
        "humidity": 45.2,
        "battery_level": 85
    }
)

# Query telemetry data
data = telemetry.query_data(
    device_id="sensor_001",
    start_time="2024-01-15T00:00:00Z",
    end_time="2024-01-15T23:59:59Z",
    metrics=["temperature", "humidity"]
)

# Export data
telemetry.export_data(
    device_ids=["sensor_001", "sensor_002"],
    start_time="2024-01-01T00:00:00Z",
    end_time="2024-01-31T23:59:59Z",
    format="csv",
    output_file="telemetry_export.csv"
)
```

## Configuration

The platform uses SQLite for data storage by default. For production deployments, consider using PostgreSQL or another enterprise database.

### Environment Variables

- `ARX_BAS_DATABASE_URL`: Database connection string
- `ARX_BAS_LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR)
- `ARX_BAS_TELEMETRY_RETENTION_DAYS`: Number of days to retain telemetry data

## Testing

Run the test suite:

```bash
python -m pytest tests/
```

## Contributing

### General Contributions

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

### Driver Contributions

For hardware driver contributions, see the [ArxDriver Contribution Framework](driver_contribution_framework.md) for detailed information about:

- Creating and submitting hardware drivers
- Revenue sharing and compensation models
- Contributor roles and responsibilities
- Quality standards and review processes
- Integration with the Arxos platform

## License

This project is part of the Arxos platform and is licensed under the same terms as the main Arxos project.

## Support

For support and questions, please refer to the main Arxos documentation or create an issue in this repository. 