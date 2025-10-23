# ArxOS Hardware Core

This directory contains the core hardware abstractions, types, and traits for ArxOS hardware integration.

## 📁 Structure

```
core/
├── src/
│   ├── lib.rs          # Main library file
│   ├── sensor.rs       # Sensor abstractions
│   ├── data.rs         # Data structures
│   ├── error.rs        # Error types
│   └── traits.rs       # Hardware traits
├── Cargo.toml          # Dependencies
└── README.md           # This file
```

## 🦀 Core Components

### Sensor Abstractions
- `Sensor` trait for common sensor operations
- `SensorData` struct for standardized data format
- `SensorConfig` for configuration management

### Data Structures
- `ArxOSData` for standardized data format
- `Metadata` for sensor metadata
- `Alerts` for alert management

### Error Handling
- `HardwareError` enum for hardware-specific errors
- `Result<T>` type aliases for consistent error handling

### Hardware Traits
- `ReadSensor` trait for sensor reading operations
- `SendData` trait for data transmission
- `ConfigureSensor` trait for sensor configuration

## 📚 Usage

```rust
use arxos_hardware_core::{Sensor, SensorData, HardwareError};

// Implement sensor trait
struct TemperatureSensor {
    // sensor implementation
}

impl Sensor for TemperatureSensor {
    type Error = HardwareError;
    
    fn read(&mut self) -> Result<SensorData, Self::Error> {
        // sensor reading implementation
    }
}
```

## 🔧 Dependencies

- `serde` for serialization
- `embedded-hal` for hardware abstractions
- `heapless` for no-std collections
- `thiserror` for error handling
