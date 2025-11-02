# ArxOS Hardware Integration Guide

**ArxOS Hardware Ecosystem** - Open source sensors for building management

## Overview

ArxOS supports open source hardware sensors that integrate directly with your building's Git repository. Choose from three integration methods based on your engineering preferences and infrastructure needs.

## Integration Methods

### Option 1: Direct GitHub API
**Best for**: Simple setups, direct integration
**Requirements**: GitHub token, HTTP client

```cpp
// ESP32 Arduino example
HTTPClient http;
http.begin("https://api.github.com/repos/your-org/building/contents/sensor-data/temp.json");
http.addHeader("Authorization", "Bearer YOUR_TOKEN");
http.addHeader("Content-Type", "application/json");

String jsonData = "{\"temperature\": 72.5, \"timestamp\": \"2024-12-01T10:30:00Z\"}";
int responseCode = http.PUT(jsonData);
```

### Option 2: Webhook Endpoint
**Best for**: Custom server control, data validation
**Requirements**: Webhook server, HTTP client

```cpp
// ESP32 Arduino example
HTTPClient http;
http.begin("https://your-webhook.com/sensor-data");
http.addHeader("Content-Type", "application/json");

String jsonData = "{\"equipment\": \"VAV-301\", \"temp\": 72.5, \"humidity\": 45}";
int responseCode = http.POST(jsonData);
```

### Option 3: MQTT Broker
**Best for**: Standard IoT protocols, scalability
**Requirements**: MQTT broker, MQTT client

```cpp
// ESP32 Arduino example
#include <PubSubClient.h>

WiFiClient wifiClient;
PubSubClient mqttClient(wifiClient);

void setup() {
    mqttClient.setServer("your-mqtt-broker.com", 1883);
    mqttClient.connect("esp32_sensor");
}

void loop() {
    String jsonData = "{\"equipment\": \"VAV-301\", \"temp\": 72.5}";
    mqttClient.publish("arxos/sensors/VAV-301", jsonData.c_str());
    delay(60000);
}
```

## Sensor Data Format

All sensor data follows the ArxOS YAML format:

```yaml
# sensor-data/VAV-301/temperature-humidity.yml
apiVersion: arxos.io/v1
kind: SensorData
metadata:
  equipment_id: VAV-301
  sensor_id: esp32_001
  sensor_type: temperature_humidity
  location: /B1/3/301/HVAC/VAV-301
  last_updated: 2024-12-01T10:30:00Z

data:
  temperature:
    value: 72.5
    unit: "fahrenheit"
    accuracy: 0.1
  
  humidity:
    value: 45.2
    unit: "percent"
    accuracy: 1.0

alerts:
  temperature:
    high_threshold: 80
    low_threshold: 65
    current_status: "normal"
```

## Supported Hardware

### ESP32 Sensors
- **Temperature/Humidity**: DHT22, SHT30, BME280
- **Air Quality**: SGP30, CCS811, PMS5003
- **Motion**: PIR sensors, ultrasonic sensors
- **Light**: BH1750, TSL2561

### RP2040 Sensors
- **Temperature**: DS18B20, LM35
- **Humidity**: DHT22, SHT30
- **Air Quality**: SGP30, CCS811
- **Pressure**: BMP280, BME280

### Arduino Sensors
- **Temperature**: LM35, DS18B20
- **Humidity**: DHT22, SHT30
- **Motion**: PIR sensors
- **Light**: LDR, BH1750

## ArxOS CLI Commands

```bash
# Sensor management
arx sensor list --equipment VAV-301
arx sensor show --sensor esp32_001
arx sensor calibrate --sensor esp32_001

# Sensor data processing
arx sensor process --path sensor-data/
arx sensor validate --sensor esp32_001
arx sensor history --equipment VAV-301 --days 7

# Equipment integration
arx equipment update VAV-301 --sensor-data sensor-data/VAV-301/
arx equipment monitor --sensors --interval 5
```

## GitHub Actions Integration

### Sensor Monitoring Workflow
```yaml
# .github/workflows/sensor-monitoring.yml
name: Sensor Data Processing

on:
  push:
    paths:
      - 'sensor-data/**/*.yml'
  schedule:
    - cron: '*/5 * * * *'  # Every 5 minutes

jobs:
  process-sensor-data:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Process Sensor Data
        uses: ./.github/actions/sensor-processor
        with:
          data-path: 'sensor-data/'
          alert-thresholds: |
            {
              "temperature": {"min": 65, "max": 80},
              "humidity": {"min": 30, "max": 60},
              "co2": {"max": 1000}
            }
          create-issues: 'true'
```

## Software Integration Architecture

### Current State

**Working ✅**
- Hardware examples compile and run (Arduino, ESP32, RP2040)
- Sensor data format defined
- Git integration from hardware examples (ESP32 posts directly to GitHub)

**Missing ⚠️**
- Integration layer between hardware sensors and main ArxOS application
- Real-time sensor data processing in ArxOS
- Equipment status updates based on sensor readings
- Automated sensor data ingestion pipeline

### Planned Integration Layers

**Phase 1: File-Based Sensor Data Ingestion**

**Architecture:**
```
Hardware Sensor → HTTP/MQTT/Webhook → Git Repository
  ↓
Sensor Data Files (YAML/JSON)
  ↓
Sensor Data Ingestion Service (src/hardware/ingestion.rs - NEW)
  ↓
Sensor Data Normalizer (src/hardware/normalizer.rs - NEW)
  ↓
Equipment Status Updater (src/hardware/updater.rs - NEW)
  ↓
Building Data Update → Git Commit
```

**New Components:**
1. **`SensorIngestionService`** - Read and process sensor data files
2. **`SensorDataNormalizer`** - Normalize diverse sensor formats
3. **`EquipmentMapper`** - Map sensors to equipment in building data
4. **`EquipmentStatusUpdater`** - Update equipment status from sensor data

**Data Flow Example:**
```yaml
# Sensor sends: hardware/examples/esp32-temperature/ sends via GitHub API
metadata:
  device_id: ESP32-001
  sensor_type: temperature
  timestamp: 2025-01-15T10:30:00Z
data:
  temperature: 25.3
  humidity: 45.2

  ↓ (Ingestion Service reads from Git)

# Equipment gets updated in building data:
equipment:
  - id: HVAC-301
    status: Active  # Updated from sensor reading
    sensor_data:
      last_update: 2025-01-15T10:30:00Z
      temperature: 25.3
```

**Phase 2: Real-Time Integration**
- HTTP endpoint listener for sensor data
- MQTT subscriber for real-time updates
- WebSocket updates for live equipment status

**Phase 3: Advanced Features**
- Alert thresholds and notifications
- Trend analysis and prediction
- Predictive maintenance alerts

### Equipment-Sensor Mapping

**Concept:** Assign sensors to specific equipment in building data

```rust
// Future implementation in src/core/equipment.rs
pub struct EquipmentSensorMapping {
    pub equipment_id: String,
    pub sensor_id: String,
    pub sensor_type: SensorType,
    pub thresholds: AlertThresholds,
}

// Update equipment status from sensor
fn update_equipment_from_sensor(
    &mut self,
    equipment_id: &str,
    sensor_data: &SensorData,
) -> Result<(), HardwareError>;
```

## Getting Started

### 1. Choose Integration Method
- **GitHub API**: Direct integration, no server needed
- **Webhook**: Custom server, more control
- **MQTT**: Standard IoT, most scalable

### 2. Select Hardware
- **ESP32**: WiFi, Bluetooth, powerful
- **RP2040**: Low power, cost-effective
- **Arduino**: Simple, educational

### 3. Implement Sensor Code
- Use provided Arduino/ESP32 examples
- Follow ArxOS data format
- Test with your building repository

### 4. Configure ArxOS
- Set up GitHub Actions workflows
- Configure alert thresholds
- Test sensor data processing

### 5. Integration Layer (Future)
- Install sensor data ingestion service
- Configure sensor-to-equipment mapping
- Enable automatic equipment status updates

## Community Resources

- **Hardware Designs**: Open source sensor schematics
- **Firmware Libraries**: Arduino/ESP32 code for ArxOS
- **Integration Examples**: Real-world implementations
- **Documentation**: Detailed setup guides

## Support

- **GitHub Issues**: Report bugs and request features
- **Discussions**: Ask questions and share projects
- **Documentation**: Comprehensive guides and examples
- **Community**: Hardware developers and building managers

---

**ArxOS Hardware Integration** - Bringing open source sensors to building management
