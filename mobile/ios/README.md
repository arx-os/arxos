# ArxOS Mobile App

## Overview

The ArxOS mobile app provides a terminal interface and LiDAR scanning capabilities for building intelligence. It connects to the ArxOS mesh network via Bluetooth and enables field workers to interact with building data and perform LiDAR scans.

## Features

### Terminal Interface
- **Command Line Interface**: Full ArxOS command support
- **Mesh Network Connection**: Bluetooth connection to nearby mesh nodes
- **Real-time Queries**: Query building data through the mesh network
- **Command History**: Navigate through previous commands

### LiDAR Scanning
- **3D Scanning**: Use iPhone LiDAR to scan building features
- **Real-time Processing**: Convert point cloud data to ArxObjects
- **Mesh Integration**: Automatically send scan data to mesh network
- **Fallback Support**: Graceful handling of devices without LiDAR

## Architecture

### Tech Stack
- **SwiftUI**: Modern iOS UI framework
- **Core Bluetooth**: Mesh network communication
- **AVFoundation**: Camera and LiDAR access
- **RealityKit**: 3D data processing

### Connection Methods
1. **Bluetooth**: Primary connection to mesh nodes
2. **Local Network**: Fallback for devices with WiFi capability
3. **USB**: Future support for direct device connection

## Installation

### Requirements
- iOS 17.0+
- iPhone with LiDAR (iPhone 12 Pro and later) for full functionality
- Bluetooth enabled device

### Build Instructions
1. Open `ArxOS.xcodeproj` in Xcode
2. Select your development team
3. Build and run on device or simulator

## Usage

### Terminal Commands
```
arx> help                    # Show available commands
arx> query "room:205"        # Query building data
arx> scan room:205          # Initiate room scan
arx> status                 # Show connection status
arx> connect                # Connect to mesh network
arx> disconnect             # Disconnect from mesh
```

### LiDAR Scanning
1. Switch to "LiDAR Scan" tab
2. Point camera at building features
3. Tap "Start LiDAR Scan"
4. Move slowly around the area
5. Scan data is automatically processed and sent to mesh

## Mesh Network Protocol

### Packet Format
```
[Type][Sequence][Source][Destination][HopCount][Payload]
  1B     2B       2B        2B          1B       N bytes
```

### Packet Types
- `0x01`: Query - Request building data
- `0x02`: Response - Query response
- `0x03`: ArxObject - Building feature data
- `0x04`: ScanRequest - LiDAR scan request
- `0x05`: Status - Network status update

### ArxObject Format (13 bytes)
```
[BuildingID][Type][X][Y][Z][Properties]
    2B       1B   2B 2B 2B     4B
```

## Development

### Project Structure
```
ArxOS/
├── ArxOSApp.swift          # App entry point
├── ContentView.swift       # Main tab interface
├── TerminalView.swift      # Terminal interface
├── CameraView.swift        # LiDAR scanning interface
├── MeshClient.swift        # Mesh network client
└── Assets.xcassets/        # App assets
```

### Key Components

#### MeshClient
- Manages Bluetooth connections to mesh nodes
- Handles packet serialization/deserialization
- Provides async interface for mesh operations

#### TerminalView
- Command line interface with history
- Real-time mesh network status
- Command execution and response display

#### CameraView
- LiDAR scanning interface
- Point cloud processing
- ArxObject generation and transmission

## Security

### Air-Gapped Architecture
- **No Internet**: App never connects to internet
- **Local Only**: All communication via Bluetooth/mesh
- **Encrypted**: All mesh communication is encrypted
- **Permission Based**: Camera access requires explicit permission

### Data Privacy
- **Local Processing**: LiDAR data processed on-device
- **No Cloud**: No data sent to external servers
- **Mesh Only**: Data only shared within building mesh network

## Future Enhancements

### Planned Features
- **AR Overlay**: Augmented reality building data display
- **Offline Mode**: Work without mesh connection
- **Multi-Building**: Support for multiple building networks
- **Advanced Scanning**: ML-based object recognition

### Hardware Integration
- **External LiDAR**: Support for external scanning devices
- **Sensor Integration**: Temperature, humidity, air quality
- **Power Management**: Battery optimization for field use

## Contributing

### Development Setup
1. Install Xcode 15.0+
2. Clone the repository
3. Open `ArxOS.xcodeproj`
4. Build and test on device

### Code Style
- Follow Swift API Design Guidelines
- Use SwiftUI for all UI components
- Implement proper error handling
- Add comprehensive documentation

## License

This project is part of the ArxOS Building Intelligence Operating System.
See the main project LICENSE for details.

## Support

For technical support or questions:
- Check the main ArxOS documentation
- Review the mesh network protocol specification
- Test with the desktop terminal application first
