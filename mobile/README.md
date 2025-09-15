# ArxOS Mobile AR Application

## Overview

React Native mobile application with augmented reality capabilities for field technicians and facility managers.

## Technology Stack

- **React Native** - Cross-platform mobile framework
- **ARKit** (iOS) / **ARCore** (Android) - AR capabilities
- **React Native Vision Camera** - Camera and QR code scanning
- **React Navigation** - Navigation framework
- **Redux Toolkit** - State management

## Features

### Augmented Reality
- Equipment identification via AR markers
- Spatial anchoring of equipment locations
- Real-time status overlay
- Maintenance history visualization
- Navigation guidance to equipment

### Core Functionality
- QR code scanning for equipment ID
- Offline mode with sync
- Work order management
- Photo documentation
- Voice notes and annotations

## Architecture

```
┌─────────────────────────────────────────┐
│       React Native Application          │
├─────────────────────────────────────────┤
│                                         │
│  ┌──────────────┐  ┌──────────────┐   │
│  │   AR View    │  │  Equipment   │   │
│  │   (ARKit/    │  │   Scanner    │   │
│  │   ARCore)    │  │              │   │
│  └──────────────┘  └──────────────┘   │
│                                         │
│  ┌─────────────────────────────────┐  │
│  │        Redux Store              │  │
│  │  - Building Data                │  │
│  │  - Equipment State              │  │
│  │  - Work Orders                  │  │
│  │  - Offline Queue                │  │
│  └─────────────────────────────────┘  │
│                                         │
└─────────────────────────────────────────┘
                    │
        ┌──────────────────────┐
        │    Sync Service      │
        └──────────────────────┘
                    │
        ┌──────────────────────┐
        │  ArxOS API Server    │
        └──────────────────────┘
```

## Project Structure

```
mobile/
├── src/
│   ├── screens/
│   │   ├── ARViewScreen.tsx        # AR visualization
│   │   ├── EquipmentScreen.tsx     # Equipment details
│   │   ├── ScannerScreen.tsx       # QR/barcode scanner
│   │   └── WorkOrderScreen.tsx     # Work order management
│   ├── components/
│   │   ├── AROverlay.tsx           # AR UI overlay
│   │   ├── EquipmentCard.tsx       # Equipment info card
│   │   └── StatusIndicator.tsx     # Status visualization
│   ├── services/
│   │   ├── ArxOSAPI.ts            # API client
│   │   ├── ARService.ts           # AR functionality
│   │   └── OfflineSync.ts         # Offline sync
│   └── store/
│       ├── buildingSlice.ts       # Building state
│       └── equipmentSlice.ts      # Equipment state
├── ios/                            # iOS-specific code
│   └── ArxOS/
│       └── ARKitBridge.swift      # ARKit integration
└── android/                        # Android-specific code
    └── app/src/main/java/
        └── ARCoreBridge.java      # ARCore integration
```

## Development Setup

```bash
cd mobile

# Install dependencies
npm install

# iOS setup
cd ios && pod install && cd ..

# Run on iOS
npm run ios

# Run on Android
npm run android
```

## AR Marker System

### Equipment Markers
Each equipment piece has a unique AR marker that encodes:
- Building ID
- Equipment path
- Quick access code

### Spatial Anchors
- Cloud anchors for persistent AR placement
- Local anchors for offline mode
- Automatic anchor synchronization

## API Integration

```typescript
import { ArxOSClient } from './services/ArxOSAPI';

const client = new ArxOSClient({
  baseURL: 'https://api.arxos.io',
  building: 'ARXOS-NA-US-NY-NYC-0001'
});

// Get equipment by scanning QR code
const equipment = await client.getEquipmentByCode(qrCode);

// Update equipment status
await client.updateEquipmentStatus(equipmentId, 'MAINTENANCE');

// Submit work order
await client.submitWorkOrder({
  equipmentId,
  issue: 'Not cooling properly',
  photos: [photo1, photo2],
  voiceNote: audioFile
});
```

## Offline Capabilities

- Local SQLite database for offline storage
- Queue system for pending updates
- Automatic sync when connection restored
- Conflict resolution for concurrent edits

## Security

- Biometric authentication
- Encrypted local storage
- Certificate pinning for API calls
- Role-based access control

## Future Enhancements

- AI-powered equipment diagnostics
- Predictive maintenance alerts
- Remote assistance with AR sharing
- Integration with smart glasses
- Voice-controlled operations