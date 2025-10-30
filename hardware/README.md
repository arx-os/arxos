# ArxOS Hardware Integration

This directory contains reference examples for hardware integration with ArxOS. The actual hardware integration implementation is in `src/hardware/` in the main codebase.

## ⚠️ Reference Only

**These examples are provided for reference only** and demonstrate how to integrate various hardware platforms (ESP32, RP2040, Arduino) with ArxOS. They are not part of the main build and may not compile with the current workspace configuration.

## 📁 Directory Structure

```
hardware/
└── examples/       # Reference examples for hardware integration
    ├── arduino-motion/     # Arduino + PIR motion sensor
    ├── esp32-temperature/  # ESP32 + DHT22 temperature/humidity
    └── rp2040-air-quality/ # RP2040 + MQ-135 air quality
```

## 🦀 Active Implementation

The actual hardware integration code is in `src/hardware/`:
- **Sensor Data Ingestion**: `src/hardware/ingestion.rs`
- **Data Types**: `src/hardware/data_types.rs`
- **Status Updates**: `src/hardware/status_updater.rs`

These modules handle sensor data from local files and integrate with the main ArxOS building data system.

## 🚀 Using Hardware Integration

The hardware integration is handled through the main ArxOS codebase:

1. **Sensor Data Format**: Sensors should output data in the ArxOS format (see `examples/README.md`)
2. **File-based Ingestion**: Place sensor data files in `./sensor-data/` directory
3. **Command Handler**: Use `arxos sensor ingest` to process sensor data files
4. **Automatic Status Updates**: Equipment status is automatically updated based on sensor readings

## 📚 Documentation

- **Examples**: See `examples/README.md` for hardware integration examples
- **Active Code**: See `src/hardware/` for the actual implementation
- **Command Reference**: See `docs/COMMAND_REFERENCE.md` for sensor commands

## 🔧 Development

The main hardware integration follows Rust best practices:
- Memory-safe implementations
- Proper error handling
- Path safety for file operations
- Comprehensive documentation
- Type-safe sensor data structures
