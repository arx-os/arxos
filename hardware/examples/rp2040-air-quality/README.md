# ArxOS RP2040 Air Quality Sensor

This example demonstrates how to connect an RP2040 with MQ-135 air quality sensor
to ArxOS using Rust and the rp-hal ecosystem.

## Hardware Requirements

- Raspberry Pi Pico (RP2040)
- MQ-135 air quality sensor
- 10kΩ pull-up resistor
- Breadboard and jumper wires

## Wiring Diagram

```
RP2040         MQ-135
------         ------
3.3V     -----> VCC
GND      -----> GND
GPIO 26  -----> AOUT (ADC)
GPIO 27  -----> DOUT (Digital)
```

## Configuration

1. **WiFi Setup**: Update the WiFi credentials in the code:
   ```rust
   const WIFI_SSID: &str = "YOUR_WIFI_SSID";
   const WIFI_PASSWORD: &str = "YOUR_WIFI_PASSWORD";
   ```

2. **MQTT Setup**: Configure MQTT broker connection:
   ```rust
   const MQTT_BROKER: &str = "YOUR_MQTT_BROKER_IP";
   const MQTT_USER: &str = "YOUR_MQTT_USERNAME";
   const MQTT_PASSWORD: &str = "YOUR_MQTT_PASSWORD";
   ```

3. **Sensor Configuration**: Update sensor information:
   ```rust
   const SENSOR_ID: &str = "aq_001";
   const ROOM_PATH: &str = "/B1/3/301/HVAC";
   const BUILDING_ID: &str = "B1";
   ```

## MQTT Broker Setup

1. Install an MQTT broker (e.g., Mosquitto)
2. Create user credentials
3. Configure topic permissions
4. Update broker IP in the code

## Installation

1. Install Rust and the RP2040 toolchain:
   ```bash
   cargo install probe-rs
   ```

2. Build and flash the project:
   ```bash
   cargo run
   ```

3. Open Serial Monitor to view sensor readings

## Data Format

The sensor publishes JSON data in this format:

```json
{
  "apiVersion": "arxos.io/v1",
  "kind": "SensorData",
  "metadata": {
    "sensor_id": "aq_001",
    "sensor_type": "air-quality",
    "room_path": "/B1/3/301/HVAC",
    "timestamp": "2024-12-01T10:30:00Z",
    "source": "mqtt"
  },
  "data": {
    "value": 85,
    "unit": "ppm",
    "status": "normal",
    "confidence": 0.88,
    "air_quality": "good",
    "voltage": 2.1,
    "digital_reading": 0
  },
  "alerts": [
    {
      "level": "info",
      "message": "Air quality: good",
      "timestamp": "2024-12-01T10:30:00Z"
    }
  ],
  "_arxos": {
    "processed": true,
    "validated": true,
    "device_id": "rp2040_aq_001",
    "mqtt_topic": "arxos/sensors/air_quality"
  }
}
```

## MQTT Topics

- **Data**: `arxos/sensors/air_quality/aq_001`
- **Control**: `arxos/sensors/aq_001/control`
- **Status**: `arxos/sensors/aq_001/status`
- **Calibration**: `arxos/sensors/aq_001/calibration`

## Control Commands

Send JSON commands to the control topic:

```json
{"command": "read_now"}
{"command": "calibrate"}
{"command": "status"}
```

## Troubleshooting

- **WiFi Connection Issues**: Check SSID and password
- **MQTT Connection Issues**: Verify broker IP and credentials
- **Sensor Reading Issues**: Check wiring and power supply
- **Build Issues**: Ensure RP2040 toolchain is properly installed

## Features

- ✅ Real-time air quality monitoring
- ✅ MQTT broker integration
- ✅ Remote control commands
- ✅ Sensor calibration support
- ✅ JSON data format
- ✅ Error handling and retry logic
- ✅ Configurable alert thresholds
- ✅ Status reporting
- ✅ Memory-safe Rust implementation