# ArxOS Mobile iOS

Native iOS application for ArxOS - Git for Buildings, featuring ARKit integration for equipment scanning and terminal interface.

## Features

- **Terminal Interface**: Full ArxOS CLI functionality in mobile terminal
- **AR Equipment Scanning**: ARKit-powered equipment detection and tagging
- **Equipment Management**: List, filter, and manage building equipment
- **Rust Core Integration**: High-performance backend via FFI bindings
- **Offline Capabilities**: Work without internet connection

## Architecture

This iOS app follows the **Rust Core + Native UI Shell** architecture:

```
┌─────────────────────────────────────────────────────────────┐
│                    iOS Native Shell                         │
├─────────────────────────────────────────────────────────────┤
│  SwiftUI Views  │  ARKit Integration  │  Terminal Interface │
│  ├── ContentView│  ├── ARScanView     │  ├── TerminalView   │
│  ├── ARScanView │  ├── ARViewContainer│  └── Command Input  │
│  └── EquipmentList│  └── Equipment Detection│              │
└─────────────────────────────────────────────────────────────┘
                                       ↕
┌─────────────────────────────────────────────────────────────┐
│                    Rust Core (FFI)                         │
├─────────────────────────────────────────────────────────────┤
│  Spatial Processing │  Git Operations │  Equipment Logic    │
│  ├── AR Data Proc. │  ├── Local Repo │  ├── Validation    │
│  ├── Coordinates   │  ├── Sync       │  └── Management     │
│  └── Validation    │  └── History    │                     │
└─────────────────────────────────────────────────────────────┘
```

## Requirements

- iOS 17.0+
- Xcode 15.0+
- Device with ARKit support (iPhone/iPad with A12 chip or later)
- LiDAR support recommended for enhanced AR scanning

## Setup

1. **Open in Xcode**:
   ```bash
   open mobile-ios/ArxOSMobile.xcodeproj
   ```

2. **Build Rust Core** (if not already built):
   ```bash
   cd crates/arxos-mobile
   cargo build --release
   ```

3. **Run on Device**:
   - Connect iOS device with ARKit support
   - Select device in Xcode
   - Build and run (⌘+R)

## Project Structure

```
mobile-ios/
├── ArxOSMobile.xcodeproj/          # Xcode project
├── ArxOSMobile/                    # Main app source
│   ├── ArxOSMobileApp.swift       # App entry point
│   ├── ContentView.swift           # Main tab view
│   ├── Views/                      # SwiftUI views
│   │   ├── TerminalView.swift     # Terminal interface
│   │   ├── ARScanView.swift       # AR scanning
│   │   ├── ARViewContainer.swift  # ARKit integration
│   │   └── EquipmentListView.swift# Equipment management
│   ├── Services/                   # Business logic
│   │   └── ArxOSCore.swift        # Rust FFI integration
│   ├── Assets.xcassets/           # App assets
│   └── Preview Content/           # SwiftUI previews
├── Package.swift                   # Swift Package Manager
└── Podfile                        # CocoaPods dependencies
```

## Key Components

### TerminalView
- Full ArxOS CLI functionality
- Command execution through Rust core
- Real-time output display
- Command history and autocomplete

### ARScanView
- ARKit-powered equipment scanning
- Real-time equipment detection
- Manual equipment tagging
- Spatial data capture

### EquipmentListView
- Equipment inventory management
- Search and filtering
- Status monitoring
- Maintenance tracking

### ArxOSCore Service
- Rust FFI integration
- Command execution
- AR data processing
- Git operations

## AR Scanning Workflow

1. **Start AR Session**: Tap "Start AR Scan"
2. **Camera Opens**: Live AR view with equipment detection
3. **Detect Equipment**: AI-powered equipment recognition
4. **Tag Equipment**: Tap to tag detected equipment
5. **Save Scan**: Commit AR data to ArxOS repository

## Terminal Commands

The mobile terminal supports all ArxOS CLI commands:

```bash
# Room management
arx room create --name "Classroom 301" --floor 3
arx room list
arx room show 301

# Equipment management  
arx equipment add --name "VAV-301" --type HVAC --room-id 301
arx equipment list
arx equipment update VAV-301

# System commands
arx status
arx diff
arx history
```

## Development

### Adding New Features

1. **UI Components**: Add SwiftUI views in `Views/`
2. **Business Logic**: Extend `ArxOSCore.swift` service
3. **Rust Integration**: Update FFI bindings in `crates/arxos-mobile`

### Testing

- **Unit Tests**: Test individual components
- **Integration Tests**: Test Rust FFI integration
- **UI Tests**: Test SwiftUI interfaces
- **AR Tests**: Test on physical devices with ARKit

## Deployment

### App Store Distribution

1. **Configure Signing**: Set up Apple Developer account
2. **Build Archive**: Create release build
3. **Upload**: Submit to App Store Connect
4. **Review**: Apple review process
5. **Release**: Publish to App Store

### Enterprise Distribution

1. **Enterprise Certificate**: Obtain enterprise developer certificate
2. **Build**: Create enterprise build
3. **Distribute**: Internal app distribution
4. **Install**: Install on enterprise devices

## Troubleshooting

### Common Issues

- **ARKit Not Available**: Ensure device supports ARKit
- **Camera Permissions**: Grant camera access in Settings
- **Rust Build Errors**: Ensure Rust toolchain is installed
- **FFI Linking**: Verify Rust library is properly linked

### Debug Mode

Enable debug logging:
```swift
// In ArxOSCore.swift
let debugMode = true
```

## Contributing

1. Follow Swift coding standards
2. Add unit tests for new features
3. Test on multiple device types
4. Ensure AR functionality works on physical devices

## License

Same as main ArxOS project - Open Source.

---

**ArxOS Mobile iOS** - Bringing Git for Buildings to mobile devices with native AR capabilities.
