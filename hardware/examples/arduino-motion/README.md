# ArxOS Arduino Motion Sensor

This example demonstrates how to connect an Arduino with PIR motion sensor
to ArxOS using Rust and the avr-hal ecosystem.

## Hardware Requirements

- Arduino Uno/Nano
- PIR motion sensor (HC-SR501)
- Ethernet Shield or WiFi module
- Breadboard and jumper wires

## Wiring Diagram

```
Arduino        PIR Sensor
-------        ----------
5V       -----> VCC
GND      -----> GND
Pin 2    -----> OUT
Pin 13   -----> LED (optional)
```

## Configuration

1. **Ethernet Setup**: Configure network settings:
   ```rust
   const WEBHOOK_URL: &str = "http://YOUR_WEBHOOK_ENDPOINT/sensor-data";
   const WEBHOOK_PORT: u16 = 80;
   ```

2. **Sensor Configuration**: Update sensor information:
   ```rust
   const SENSOR_ID: &str = "motion_001";
   const ROOM_PATH: &str = "/B1/3/301/HVAC";
   const BUILDING_ID: &str = "B1";
   ```

## Webhook Endpoint Setup

1. Create a webhook endpoint that accepts POST requests
2. Configure it to process JSON sensor data
3. Update the webhook URL in the code
4. Ensure the endpoint is accessible from your network

## Installation

1. Install Rust and the Arduino toolchain:
   ```bash
   cargo install ravedude
   ```

2. Build and flash the project:
   ```bash
   cargo run
   ```

3. Open Serial Monitor to view sensor readings

## Data Format

The sensor sends JSON data in this format:

```json
{
  "apiVersion": "arxos.io/v1",
  "kind": "SensorData",
  "metadata": {
    "sensor_id": "motion_001",
    "sensor_type": "motion",
    "room_path": "/B1/3/301/HVAC",
    "timestamp": "2024-12-01T10:30:00Z",
    "source": "webhook"
  },
  "data": {
    "value": true,
    "unit": "boolean",
    "status": "normal",
    "confidence": 1.0,
    "motion_detected": true,
    "duration": 5
  },
  "alerts": [
    {
      "level": "info",
      "message": "Motion detected",
      "timestamp": "2024-12-01T10:30:00Z"
    }
  ],
  "_arxos": {
    "processed": true,
    "validated": true,
    "device_id": "arduino_motion_001",
    "webhook_url": "http://YOUR_WEBHOOK_ENDPOINT/sensor-data"
  }
}
```

## Motion Detection Logic

- **Motion Detected**: Sends `true` when PIR sensor triggers
- **Motion Stopped**: Sends `false` when motion ends
- **Timeout**: Automatically stops motion after 30 seconds
- **Status Check**: Periodic status updates every minute

## Troubleshooting

- **Ethernet Connection Issues**: Check network configuration
- **Webhook Connection Issues**: Verify endpoint URL and accessibility
- **Sensor Issues**: Check PIR sensor sensitivity and positioning
- **Build Issues**: Ensure Arduino toolchain is properly installed

## Features

- ✅ Real-time motion detection
- ✅ Webhook endpoint integration
- ✅ HTTP POST requests
- ✅ JSON data format
- ✅ Error handling and retry logic
- ✅ Motion timeout handling
- ✅ Status LED indication
- ✅ Periodic status checks
- ✅ Configurable motion timeout
- ✅ Memory-safe Rust implementation