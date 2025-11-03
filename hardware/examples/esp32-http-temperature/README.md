# ArxOS ESP32 HTTP Temperature Sensor

This example demonstrates how to connect an ESP32 with DHT22 sensor to ArxOS using **HTTP POST** requests to the ArxOS sensor ingestion server.

## Overview

This modern approach uses the ArxOS HTTP ingestion server (`/sensors/ingest` endpoint) which provides:
- ✅ Real-time sensor data processing
- ✅ Automatic equipment status updates
- ✅ Built-in validation and error handling
- ✅ WebSocket support for live updates
- ✅ No MQTT broker required

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

## Prerequisites

1. **ArxOS HTTP Server Running**: Start the ArxOS sensor ingestion server:
   ```bash
   arx sensors http --building "Your Building" --host 0.0.0.0 --port 3000
   ```

2. **ESP32 Toolchain**: Install Rust and ESP32 tools:
   ```bash
   cargo install espup
   espup install
   source $HOME/export-esp.sh
   ```

## Configuration

Update `src/main.rs` with your settings:

```rust
// WiFi credentials
const WIFI_SSID: &str = "YOUR_WIFI_SSID";
const WIFI_PASSWORD: &str = "YOUR_WIFI_PASSWORD";

// ArxOS HTTP endpoint
const ARXOS_HOST: &str = "192.168.1.100";  // Your ArxOS server IP
const ARXOS_PORT: u16 = 3000;
const ARXOS_ENDPOINT: &str = "http://192.168.1.100:3000/sensors/ingest";

// Sensor identification
const SENSOR_ID: &str = "esp32_temp_001";
const SENSOR_TYPE: &str = "temperature_humidity";
const ROOM_PATH: &str = "/B1/3/301/HVAC";
const BUILDING_ID: &str = "B1";
const EQUIPMENT_ID: &str = "HVAC-301";  // Optional: linked equipment
```

## Data Format

The sensor sends JSON data to the HTTP endpoint:

```json
{
  "api_version": "arxos.io/v1",
  "kind": "SensorData",
  "metadata": {
    "sensor_id": "esp32_temp_001",
    "sensor_type": "temperature_humidity",
    "room_path": "/B1/3/301/HVAC",
    "timestamp": "2024-12-01T10:30:00Z",
    "source": "http",
    "building_id": "B1",
    "equipment_id": "HVAC-301"
  },
  "data": {
    "temperature": 72.5,
    "humidity": 45.0
  },
  "alerts": [],
  "arxos": {
    "processed": false,
    "validated": false,
    "device_id": "esp32_001"
  }
}
```

## Building and Flashing

```bash
cd esp32-http-temperature
cargo run
```

## Features

- ✅ **HTTP POST to ArxOS**: Direct integration with sensor ingestion API
- ✅ **Automatic retry**: Retry logic for network failures
- ✅ **Rate limiting**: Built-in throttling (60s intervals)
- ✅ **Error handling**: Comprehensive error recovery
- ✅ **JSON serialization**: Clean data format
- ✅ **LED status**: Visual feedback for transmission status
- ✅ **Memory-safe**: Rust implementation with no undefined behavior

## Troubleshooting

### HTTP Connection Issues
- **404 Not Found**: Check that the ArxOS server is running on the correct port
- **Connection Refused**: Verify firewall settings and network connectivity
- **Timeout**: Check WiFi signal strength and server responsiveness

### Sensor Reading Issues
- **NaN values**: Check DHT22 wiring and power supply
- **Reading errors**: Verify pull-up resistor (10kΩ)
- **CRC errors**: May indicate sensor malfunction or power issues

### Build Issues
- **Toolchain errors**: Run `espup install` and source the export script
- **Dependency issues**: Run `cargo update` to fetch latest versions

## Response Handling

The ArxOS server returns:

```json
{
  "success": true,
  "message": "Successfully ingested sensor data from esp32_temp_001",
  "sensor_id": "esp32_temp_001",
  "timestamp": "2024-12-01T10:30:00Z"
}
```

On error (400 Bad Request):

```json
{
  "success": false,
  "message": "Invalid sensor data format"
}
```

## Monitoring in ArxOS

Once sensor data is ingested:

1. **Check equipment status**:
   ```bash
   arx equipment status --equipment-id HVAC-301
   ```

2. **View sensor history**:
   ```bash
   arx sensors history --sensor-id esp32_temp_001
   ```

3. **WebSocket updates**: Connect to `ws://192.168.1.100:3000` for live data

## Advanced Features

### Custom Alert Thresholds

Configure alerts in the ArxOS sensor mapping:

```yaml
# sensor_mappings.yaml
equipment_sensor_mappings:
  - equipment_id: "HVAC-301"
    sensor_id: "esp32_temp_001"
    sensor_type: "temperature"
    threshold_min: 65.0
    threshold_max: 80.0
    alert_on_out_of_range: true
```

### Multiple Sensors

You can have multiple ESP32 sensors sending to the same endpoint:

```
Endpoint: http://192.168.1.100:3000/sensors/ingest

Sensor 1: esp32_temp_001 -> /B1/3/301/HVAC
Sensor 2: esp32_temp_002 -> /B1/3/302/HVAC
Sensor 3: esp32_temp_003 -> /B1/4/401/HVAC
```

Each sensor is uniquely identified by `sensor_id` in the metadata.

## Security Considerations

⚠️ **Production Deployment**:
- Use HTTPS with TLS certificates for production
- Implement authentication tokens for sensor registration
- Configure firewall rules to restrict access
- Use WiFi WPA2/WPA3 encryption
- Store credentials securely (use ESP32 NVS or secure storage)

## Next Steps

1. **Deploy multiple sensors** throughout your building
2. **Configure equipment mappings** in ArxOS
3. **Set up alert thresholds** for anomaly detection
4. **Enable WebSocket client** for real-time monitoring
5. **Integrate with automation** systems

## Comparison with Other Methods

| Method | Pros | Cons |
|--------|------|------|
| **HTTP** (this example) | Simple, real-time, no broker | Requires server running |
| **GitHub API** | No server needed, versioned | Slower, rate limited |
| **MQTT** | Standard protocol, scalable | Requires MQTT broker |
| **WebSocket** | Bidirectional, real-time | More complex setup |

## Support

- **ArxOS Docs**: `docs/features/HARDWARE_INTEGRATION.md`
- **ESP32 Docs**: `hardware/examples/esp32-temperature/`
- **Issues**: GitHub Issues on ArxOS repository

---

**Ready to deploy?** Start the ArxOS server and flash this firmware!

