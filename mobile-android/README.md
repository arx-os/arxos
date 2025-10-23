# ArxOS Mobile Android

Native Android application for ArxOS - Git for Buildings, featuring ARCore integration for equipment scanning and Jetpack Compose terminal interface.

## Features

- **Terminal Interface**: Full ArxOS CLI functionality in mobile terminal
- **AR Equipment Scanning**: ARCore-powered equipment detection and tagging
- **Equipment Management**: List, filter, and manage building equipment
- **Rust Core Integration**: High-performance backend via FFI bindings
- **Offline Capabilities**: Work without internet connection

## Architecture

This Android app follows the **Rust Core + Native UI Shell** architecture:

```
┌─────────────────────────────────────────────────────────────┐
│                    Android Native Shell                     │
├─────────────────────────────────────────────────────────────┤
│  Jetpack Compose │  ARCore Integration │  Terminal Interface│
│  ├── Screens     │  ├── ARScreen       │  ├── TerminalScreen│
│  ├── Components  │  ├── ARViewContainer│  └── Command Input  │
│  └── ViewModels  │  └── Equipment Detection│              │
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

- Android 7.0 (API 24)+
- Android Studio Hedgehog | 2023.1.1+
- Device with ARCore support
- Camera and location permissions

## Setup

1. **Open in Android Studio**:
   ```bash
   # Open the mobile-android directory in Android Studio
   ```

2. **Build Rust Core** (if not already built):
   ```bash
   cd crates/arxos-mobile
   cargo build --release
   ```

3. **Run on Device**:
   - Connect Android device with ARCore support
   - Enable Developer Options and USB Debugging
   - Build and run (Shift+F10)

## Project Structure

```
mobile-android/
├── app/
│   ├── src/main/
│   │   ├── java/com/arxos/mobile/
│   │   │   ├── MainActivity.kt              # App entry point
│   │   │   ├── ui/
│   │   │   │   ├── ArxOSApp.kt             # Main app composable
│   │   │   │   ├── screens/                # Jetpack Compose screens
│   │   │   │   │   ├── TerminalScreen.kt   # Terminal interface
│   │   │   │   │   ├── ARScreen.kt         # AR scanning
│   │   │   │   │   └── EquipmentScreen.kt  # Equipment management
│   │   │   │   └── theme/                  # Material Design theme
│   │   │   │       ├── Theme.kt
│   │   │   │       ├── Color.kt
│   │   │   │       └── Type.kt
│   │   ├── res/                             # Android resources
│   │   │   └── values/
│   │   │       └── strings.xml
│   │   └── AndroidManifest.xml
│   └── build.gradle
├── build.gradle
└── settings.gradle
```

## Key Components

### TerminalScreen
- Full ArxOS CLI functionality
- Command execution through Rust core
- Real-time output display
- Command history and execution

### ARScreen
- ARCore-powered equipment scanning
- Real-time equipment detection
- Manual equipment tagging
- Spatial data capture

### EquipmentScreen
- Equipment inventory management
- Search and filtering
- Status monitoring
- Maintenance tracking

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

## Dependencies

### Core Dependencies
- **Jetpack Compose**: Modern Android UI toolkit
- **ARCore**: Google's AR platform
- **Material Design 3**: Latest Material Design components
- **Navigation Compose**: Navigation for Compose
- **ViewModel**: State management
- **Coroutines**: Asynchronous programming

## Development

### Adding New Features

1. **UI Components**: Add Compose screens in `ui/screens/`
2. **Business Logic**: Extend service classes
3. **Rust Integration**: Update FFI bindings in `crates/arxos-mobile`

### Testing

- **Unit Tests**: Test individual components
- **Integration Tests**: Test Rust FFI integration
- **UI Tests**: Test Compose interfaces
- **AR Tests**: Test on physical devices with ARCore

## Deployment

### Google Play Store Distribution

1. **Configure Signing**: Set up Google Play Console
2. **Build Release**: Create signed release build
3. **Upload**: Submit to Google Play Console
4. **Review**: Google review process
5. **Release**: Publish to Play Store

## Troubleshooting

### Common Issues

- **ARCore Not Available**: Ensure device supports ARCore
- **Camera Permissions**: Grant camera access in Settings
- **Rust Build Errors**: Ensure Rust toolchain is installed
- **FFI Linking**: Verify Rust library is properly linked

## Contributing

1. Follow Kotlin coding standards
2. Add unit tests for new features
3. Test on multiple device types
4. Ensure AR functionality works on physical devices

## License

Same as main ArxOS project - Open Source.

---

**ArxOS Mobile Android** - Bringing Git for Buildings to Android devices with native AR capabilities.