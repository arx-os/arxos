# ArxOS ESP32 Temperature & Humidity Sensor

This example demonstrates how to connect an ESP32 with DHT22 sensor
to ArxOS using Rust and the esp-rs ecosystem.

## Hardware Requirements

- ESP32 development board
- DHT22 temperature/humidity sensor
- 10kΩ pull-up resistor
- Breadboard and jumper wires

## Wiring Diagram

```
ESP32          DHT22
-----          -----
3.3V    -----> VCC
GND     -----> GND
GPIO 4  -----> DATA (with 10kΩ pull-up to 3.3V)
```

## Configuration

1. **WiFi Setup**: Update the WiFi credentials in the code:
   ```rust
   const WIFI_SSID: &str = "YOUR_WIFI_SSID";
   const WIFI_PASSWORD: &str = "YOUR_WIFI_PASSWORD";
   ```

2. **GitHub API Setup**: Configure GitHub integration:
   ```rust
   const GITHUB_TOKEN: &str = "YOUR_GITHUB_TOKEN";
   const GITHUB_OWNER: &str = "YOUR_GITHUB_USERNAME";
   const GITHUB_REPO: &str = "YOUR_BUILDING_REPO";
   ```

3. **Sensor Configuration**: Update sensor information:
   ```rust
   const SENSOR_ID: &str = "temp_hum_001";
   const ROOM_PATH: &str = "/B1/3/301/HVAC";
   const BUILDING_ID: &str = "B1";
   ```

## GitHub Token Setup

1. Go to GitHub Settings > Developer settings > Personal access tokens
2. Generate a new token with `repo` permissions
3. Copy the token and paste it in the code

## Installation

1. Install Rust and the ESP32 toolchain:
   ```bash
   cargo install espup
   espup install
   ```

2. Build and flash the project:
   ```bash
   cargo run
   ```

3. Open Serial Monitor to view sensor readings

## Data Format

The sensor creates YAML files in this format:

```yaml
apiVersion: arxos.io/v1
kind: SensorData
metadata:
  sensor_id: temp_hum_001
  sensor_type: temperature_humidity
  room_path: /B1/3/301/HVAC
  timestamp: 2024-12-01T10:30:00Z
  source: github-api

data:
  temperature:
    value: 72.5
    unit: fahrenheit
    status: normal
    confidence: 0.95
  humidity:
    value: 45.0
    unit: percent
    status: normal
    confidence: 0.92

alerts:
  - level: info
    message: "Temperature within normal range"
    timestamp: 2024-12-01T10:30:00Z

_arxos:
  processed: true
  validated: true
  device_id: esp32_temp_hum_001
```

## Troubleshooting

- **WiFi Connection Issues**: Check SSID and password
- **GitHub API Errors**: Verify token permissions and repository access
- **Sensor Reading Errors**: Check wiring and power supply
- **Build Issues**: Ensure ESP32 toolchain is properly installed

## Features

- ✅ Real-time temperature and humidity monitoring
- ✅ Automatic GitHub API integration
- ✅ Error handling and retry logic
- ✅ Configurable alert thresholds
- ✅ YAML data format compatibility
- ✅ Git commit integration
- ✅ Rate limiting compliance
- ✅ Memory-safe Rust implementation