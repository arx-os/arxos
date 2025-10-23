# ArxOS Hardware Drivers

This directory contains hardware driver implementations for various sensors and platforms.

## 📁 Structure

```
drivers/
├── src/
│   ├── lib.rs          # Main library file
│   ├── dht22.rs        # DHT22 temperature/humidity sensor
│   ├── mq135.rs        # MQ-135 air quality sensor
│   ├── pir.rs          # PIR motion sensor
│   └── common.rs       # Common driver utilities
├── Cargo.toml          # Dependencies
└── README.md           # This file
```

## 🦀 Driver Implementations

### DHT22 Temperature/Humidity Sensor
- `DHT22Driver` for ESP32 and Arduino platforms
- Temperature and humidity reading
- Error handling for sensor failures

### MQ-135 Air Quality Sensor
- `MQ135Driver` for RP2040 and Arduino platforms
- Analog and digital reading support
- Air quality level calculation

### PIR Motion Sensor
- `PIRDriver` for Arduino platforms
- Motion detection with timeout handling
- Digital input reading

### Common Utilities
- `SensorCalibration` for sensor calibration
- `DataValidation` for data validation
- `ErrorRecovery` for error recovery

## 📚 Usage

```rust
use arxos_hardware_drivers::{DHT22Driver, MQ135Driver, PIRDriver};

// Initialize DHT22 sensor
let mut dht22 = DHT22Driver::new(pin)?;

// Read temperature and humidity
let (temp, humidity) = dht22.read()?;

// Initialize MQ-135 sensor
let mut mq135 = MQ135Driver::new(analog_pin, digital_pin)?;

// Read air quality
let air_quality = mq135.read_air_quality()?;

// Initialize PIR sensor
let mut pir = PIRDriver::new(pin)?;

// Check for motion
let motion_detected = pir.is_motion_detected()?;
```

## 🔧 Dependencies

- `embedded-hal` for hardware abstractions
- `nb` for non-blocking operations
- `heapless` for no-std collections
- `arxos_hardware_core` for core types
