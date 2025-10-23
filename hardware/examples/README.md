# ArxOS Hardware Examples

This directory contains complete working examples for integrating open-source hardware sensors with ArxOS using Rust. Each example demonstrates a different integration method and hardware platform.

## 📁 Examples Overview

### ESP32 Temperature & Humidity Sensor
- **Hardware**: ESP32 + DHT22 sensor
- **Integration**: GitHub API
- **Data Format**: YAML
- **Features**: Real-time monitoring, automatic Git commits
- **Directory**: `esp32-temperature/`

### RP2040 Air Quality Sensor
- **Hardware**: RP2040 + MQ-135 sensor
- **Integration**: MQTT Broker
- **Data Format**: JSON
- **Features**: Remote control, calibration, status reporting
- **Directory**: `rp2040-air-quality/`

### Arduino Motion Sensor
- **Hardware**: Arduino + PIR sensor
- **Integration**: Webhook Endpoint
- **Data Format**: JSON
- **Features**: Motion detection, timeout handling, LED indication
- **Directory**: `arduino-motion/`

## 🚀 Quick Start

1. **Choose your integration method**:
   - **GitHub API**: Direct integration with GitHub repositories
   - **MQTT Broker**: Real-time messaging with MQTT
   - **Webhook Endpoint**: HTTP POST to custom endpoints

2. **Select your hardware platform**:
   - **ESP32**: WiFi-enabled, powerful microcontroller
   - **RP2040**: Modern ARM-based microcontroller
   - **Arduino**: Classic, widely-supported platform

3. **Follow the example-specific README** for detailed setup instructions

## 🦀 Rust Implementation

All examples are implemented in Rust using the appropriate embedded HAL:
- **ESP32**: `esp-idf-hal` and `esp-idf-svc`
- **RP2040**: `rp-hal` and `embedded-hal`
- **Arduino**: `avr-hal` and `embedded-hal`

## 📁 Examples Overview

### ESP32 Temperature & Humidity Sensor
- **Hardware**: ESP32 + DHT22 sensor
- **Integration**: GitHub API
- **Data Format**: YAML
- **Features**: Real-time monitoring, automatic Git commits
- **Directory**: `esp32-temperature/`

### RP2040 Air Quality Sensor
- **Hardware**: RP2040 + MQ-135 sensor
- **Integration**: MQTT Broker
- **Data Format**: JSON
- **Features**: Remote control, calibration, status reporting
- **Directory**: `rp2040-air-quality/`

### Arduino Motion Sensor
- **Hardware**: Arduino + PIR sensor
- **Integration**: Webhook Endpoint
- **Data Format**: JSON
- **Features**: Motion detection, timeout handling, LED indication
- **Directory**: `arduino-motion/`

## 🔧 Integration Methods

### 1. GitHub API Integration
**Best for**: Direct repository integration, version control
- ✅ Automatic Git commits
- ✅ Version history
- ✅ Collaboration ready
- ❌ Rate limiting
- ❌ Requires GitHub token

### 2. MQTT Broker Integration
**Best for**: Real-time data, multiple sensors
- ✅ Real-time messaging
- ✅ Remote control
- ✅ Scalable
- ❌ Requires MQTT broker
- ❌ Network dependency

### 3. Webhook Endpoint Integration
**Best for**: Custom processing, existing systems
- ✅ Flexible processing
- ✅ Custom endpoints
- ✅ Simple HTTP
- ❌ Requires webhook server
- ❌ No built-in persistence

## 📊 Data Formats

All examples use the ArxOS sensor data format:

```yaml
apiVersion: arxos.io/v1
kind: SensorData
metadata:
  sensor_id: sensor_001
  sensor_type: temperature
  room_path: /B1/3/301/HVAC
  timestamp: 2024-12-01T10:30:00Z
  source: github-api

data:
  value: 72.5
  unit: fahrenheit
  status: normal
  confidence: 0.95

alerts:
  - level: info
    message: "Temperature within normal range"
    timestamp: 2024-12-01T10:30:00Z

_arxos:
  processed: true
  validated: true
  device_id: esp32_sensor_001
```

## 🛠️ Hardware Requirements

### Common Components
- Breadboard and jumper wires
- Pull-up resistors (10kΩ)
- Power supply (3.3V or 5V)
- USB cable for programming

### Platform-Specific
- **ESP32**: WiFi module, DHT22 sensor
- **RP2040**: WiFi module, MQ-135 sensor
- **Arduino**: Ethernet shield, PIR sensor

## 🔌 Wiring Diagrams

Each example includes detailed wiring diagrams in their respective README files.

## 📚 Documentation

- **Hardware Integration Guide**: `docs/hardware_integration.md`
- **Hardware Examples**: `docs/hardware_examples.md`
- **Development Plan**: `docs/hardware_development_plan.md`

## 🚨 Troubleshooting

### Common Issues
1. **WiFi Connection**: Check SSID and password
2. **Sensor Readings**: Verify wiring and power supply
3. **API Errors**: Check tokens and permissions
4. **Upload Issues**: Ensure correct board selection

### Getting Help
- Check example-specific README files
- Review ArxOS documentation
- Open an issue on GitHub
- Join the community discussions

## 🎯 Next Steps

1. **Choose an example** that matches your needs
2. **Gather hardware** components
3. **Follow setup instructions** step by step
4. **Test integration** with ArxOS
5. **Customize** for your specific use case
6. **Deploy** in your building

## 🤝 Contributing

We welcome contributions to improve these examples:

1. **Bug fixes** and improvements
2. **New hardware platforms** (STM32, Raspberry Pi, etc.)
3. **Additional sensors** (pressure, light, sound, etc.)
4. **Integration methods** (CoAP, LoRaWAN, etc.)
5. **Documentation** improvements

## 📄 License

These examples are part of the ArxOS project and are licensed under the same terms.

---

**Ready to get started?** Choose an example and follow the setup instructions!
