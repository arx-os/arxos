# Arxos Mobile AR Application Documentation

## Overview

The Arxos Mobile AR application extends the building intelligence platform with augmented reality capabilities, allowing field workers to visualize, interact with, and update building equipment data in real-time through spatial anchoring.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Mobile AR Application                     │
├─────────────────────────────────────────────────────────────┤
│  React Native Framework                                      │
│  ├── ViroReact AR Engine (ARKit/ARCore)                    │
│  ├── Equipment Visualization Components                     │
│  ├── Offline-First Data Management                         │
│  └── Real-time Sync Service                                │
├─────────────────────────────────────────────────────────────┤
│                    API Integration Layer                     │
│  ├── REST API Client (Axios)                               │
│  ├── WebSocket for Real-time Updates                       │
│  └── Offline Queue Management                              │
├─────────────────────────────────────────────────────────────┤
│                 Arxos Backend (Go Server)                   │
│  ├── AR-specific API Endpoints                             │
│  ├── Spatial Anchor Storage                                │
│  └── Equipment Data Management                             │
└─────────────────────────────────────────────────────────────┘
```

## Key Features

### 1. Spatial Equipment Anchoring
- **Persistent AR Anchors**: Equipment positions are saved as spatial anchors that persist across sessions
- **Cross-Platform Support**: Anchors work on both iOS (ARKit) and Android (ARCore)
- **Multi-User Synchronization**: Multiple users can view the same equipment in the same spatial locations

### 2. Equipment Information Overlay
- **Real-time Data Display**: View equipment specifications, status, and maintenance history
- **Interactive Labels**: Tap equipment labels to view/edit details
- **Visual Status Indicators**: Color-coded status (green=normal, yellow=needs-repair, red=failed)

### 3. Equipment Management
- **Add New Equipment**: Place virtual equipment markers in physical space
- **Update Equipment Data**: Edit specifications, status, and notes in AR view
- **Voice Input**: Use voice commands to update equipment information hands-free
- **QR/Barcode Scanning**: Quick equipment identification and data entry

### 4. Offline Capability
- **Local Data Caching**: Work without network connection
- **Operation Queue**: Changes are queued and synced when connection restored
- **Conflict Resolution**: Smart merging of offline changes with server updates

## Technical Stack

### Core Technologies
- **Framework**: React Native 0.72+
- **AR Engine**: ViroReact (wrapper for ARKit/ARCore)
- **State Management**: React Context API + Custom Hooks
- **Navigation**: React Navigation 6
- **API Client**: Axios with interceptors for auth/retry
- **Local Storage**: AsyncStorage + SQLite for complex queries
- **Platform Requirements**:
  - iOS 14+ (ARKit 4.0+)
  - Android API 24+ (ARCore 1.0+)

### Development Dependencies
```json
{
  "react-native": "0.72.x",
  "react-viro": "2.23.0",
  "axios": "^1.5.0",
  "@react-navigation/native": "^6.1.0",
  "@react-native-async-storage/async-storage": "^1.19.0",
  "react-native-sqlite-storage": "^6.0.1",
  "react-native-voice": "^3.2.4",
  "react-native-camera": "^4.2.1"
}
```

## API Integration

### Authentication Flow
1. Mobile app authenticates using existing `/api/v1/auth/login` endpoint
2. Receives JWT token stored securely in device keychain
3. Token included in all API requests as Bearer token
4. Automatic token refresh before expiration

### AR-Specific Endpoints

#### Get Building Anchors
```http
GET /api/v1/ar/buildings/{building_id}/anchors
Authorization: Bearer {token}

Response:
{
  "anchors": [
    {
      "id": "anchor_123",
      "equipment_id": "equip_456",
      "platform": "ios",
      "anchor_data": "base64_encoded_anchor",
      "position": {
        "x": 1.5,
        "y": 0.0,
        "z": -2.0
      },
      "created_at": "2024-09-12T10:00:00Z"
    }
  ]
}
```

#### Save Equipment Anchor
```http
POST /api/v1/ar/anchors
Authorization: Bearer {token}
Content-Type: application/json

{
  "equipment_id": "equip_456",
  "building_id": "build_789",
  "platform": "ios",
  "anchor_data": "base64_encoded_anchor",
  "position": {
    "x": 1.5,
    "y": 0.0,
    "z": -2.0
  }
}
```

#### Update Equipment via AR
```http
PUT /api/v1/equipment/{equipment_id}
Authorization: Bearer {token}
Content-Type: application/json

{
  "name": "HVAC Unit 3",
  "type": "hvac",
  "manufacturer": "Carrier",
  "model": "Infinity 19VS",
  "serial_number": "CAR123456",
  "status": "normal",
  "notes": "Serviced via AR inspection"
}
```

## Data Models

### AR Anchor Model
```go
type ARAnchor struct {
    ID           string    `json:"id"`
    EquipmentID  string    `json:"equipment_id"`
    BuildingID   string    `json:"building_id"`
    Platform     string    `json:"platform"` // "ios" or "android"
    AnchorData   []byte    `json:"anchor_data"` // Platform-specific anchor
    Position     Position  `json:"position"`
    CreatedAt    time.Time `json:"created_at"`
    UpdatedAt    time.Time `json:"updated_at"`
}

type Position struct {
    X float64 `json:"x"`
    Y float64 `json:"y"`
    Z float64 `json:"z"`
}
```

### Extended Equipment Model
```go
type Equipment struct {
    // Existing fields
    ID         string          `json:"id"`
    Name       string          `json:"name"`
    Type       string          `json:"type"`
    Location   Point           `json:"location"`
    RoomID     string          `json:"room_id"`
    Status     EquipmentStatus `json:"status"`
    Notes      string          `json:"notes"`
    MarkedBy   string          `json:"marked_by"`
    MarkedAt   time.Time       `json:"marked_at"`
    
    // New AR-specific fields
    Manufacturer   string    `json:"manufacturer,omitempty"`
    Model          string    `json:"model,omitempty"`
    SerialNumber   string    `json:"serial_number,omitempty"`
    InstallDate    time.Time `json:"install_date,omitempty"`
    LastServiceDate time.Time `json:"last_service_date,omitempty"`
    ARAnchorID     string    `json:"ar_anchor_id,omitempty"`
}
```

## Mobile App Architecture

### Component Structure
```
src/
├── components/
│   ├── ar/
│   │   ├── ARSession.tsx           # Main AR session manager
│   │   ├── EquipmentLabel.tsx      # Equipment info display
│   │   ├── EquipmentPlacer.tsx     # New equipment placement
│   │   ├── StatusIndicator.tsx     # Visual status markers
│   │   └── ARControls.tsx          # AR UI controls
│   ├── common/
│   │   ├── Button.tsx
│   │   ├── Input.tsx
│   │   └── LoadingSpinner.tsx
│   └── forms/
│       ├── EquipmentForm.tsx
│       └── LoginForm.tsx
├── services/
│   ├── api/
│   │   ├── client.ts               # Axios configuration
│   │   ├── auth.ts                 # Authentication service
│   │   ├── equipment.ts            # Equipment API calls
│   │   └── ar.ts                   # AR-specific API calls
│   ├── ar/
│   │   ├── anchorManager.ts        # Spatial anchor management
│   │   └── arService.ts            # AR session management
│   └── sync/
│       ├── offlineQueue.ts         # Offline operation queue
│       └── syncService.ts          # Data synchronization
├── hooks/
│   ├── useAuth.ts
│   ├── useEquipment.ts
│   └── useAR.ts
├── screens/
│   ├── LoginScreen.tsx
│   ├── BuildingListScreen.tsx
│   ├── ARViewScreen.tsx
│   └── EquipmentDetailScreen.tsx
├── navigation/
│   └── AppNavigator.tsx
└── utils/
    ├── storage.ts
    └── permissions.ts
```

### State Management Pattern
```typescript
// contexts/ARContext.tsx
interface ARContextState {
  session: ViroARSceneNavigator | null;
  anchors: Map<string, ARAnchor>;
  equipment: Map<string, Equipment>;
  isTracking: boolean;
  selectedEquipment: Equipment | null;
}

const ARContext = createContext<ARContextState>();

export const useAR = () => {
  const context = useContext(ARContext);
  if (!context) {
    throw new Error('useAR must be used within ARProvider');
  }
  return context;
};
```

## Security Considerations

### Data Protection
- **Token Storage**: JWT tokens stored in iOS Keychain / Android Keystore
- **Secure Communication**: All API calls over HTTPS
- **Data Encryption**: Sensitive equipment data encrypted at rest
- **Session Management**: Automatic logout on app background/inactivity

### Permissions
- **Camera**: Required for AR functionality
- **Location**: Optional, for GPS-based equipment discovery
- **Microphone**: Optional, for voice input features
- **Storage**: Required for offline data caching

## Performance Optimization

### AR Performance
- **Anchor Limit**: Maximum 50 anchors loaded simultaneously
- **LOD System**: Level-of-detail based on distance from camera
- **Occlusion Culling**: Hide equipment behind walls/obstacles
- **Frame Rate Target**: Maintain 60 FPS for smooth AR experience

### Network Optimization
- **Data Compression**: GZIP compression for API responses
- **Image Caching**: Equipment photos cached locally
- **Batch Syncing**: Queue multiple changes for single sync request
- **Delta Updates**: Only sync changed fields

## Testing Strategy

### Unit Tests
```javascript
// __tests__/services/arService.test.js
describe('ARService', () => {
  it('should load building anchors', async () => {
    const anchors = await arService.loadBuildingAnchors('building_123');
    expect(anchors).toHaveLength(5);
    expect(anchors[0]).toHaveProperty('equipment_id');
  });
});
```

### Integration Tests
- Mock AR session for non-AR devices
- Test offline/online transitions
- Verify sync conflict resolution
- API integration with test backend

### E2E Tests (Detox)
```javascript
// e2e/arWorkflow.test.js
describe('AR Equipment Workflow', () => {
  it('should add new equipment in AR', async () => {
    await element(by.id('ar-button')).tap();
    await element(by.id('add-equipment')).tap();
    await element(by.id('equipment-type')).typeText('HVAC');
    await element(by.id('save-button')).tap();
    await expect(element(by.text('Equipment added'))).toBeVisible();
  });
});
```

## Deployment

### Build Configuration

#### iOS
```bash
# Install dependencies
cd ios && pod install

# Development build
npx react-native run-ios

# Production build
npx react-native run-ios --configuration Release
```

#### Android
```bash
# Development build
npx react-native run-android

# Production build
cd android && ./gradlew assembleRelease
```

### Environment Variables
```javascript
// config/env.js
export const config = {
  API_BASE_URL: __DEV__ 
    ? 'http://localhost:8080/api/v1'
    : 'https://api.arxos.io/api/v1',
  AR_CLOUD_API_KEY: process.env.AR_CLOUD_API_KEY,
  ENABLE_VOICE: true,
  OFFLINE_SYNC_INTERVAL: 60000, // 1 minute
};
```

## Troubleshooting

### Common Issues

1. **AR Tracking Lost**
   - Ensure adequate lighting
   - Scan more of the environment
   - Reset AR session if needed

2. **Anchors Not Persisting**
   - Check platform-specific anchor limits
   - Verify anchor data is being saved to backend
   - Clear local anchor cache and reload

3. **Offline Sync Failures**
   - Check for conflicting changes
   - Verify network connectivity
   - Review sync queue for errors

## Future Enhancements

### Planned Features
- **Multi-user Collaboration**: Real-time shared AR sessions
- **3D Model Import**: Display actual equipment 3D models
- **Maintenance Workflows**: Guided AR maintenance procedures
- **Analytics Dashboard**: AR usage and interaction metrics
- **Cloud Anchors**: Cross-device anchor sharing via AR Cloud

### Performance Improvements
- **Metal/Vulkan Rendering**: Direct GPU access for better performance
- **Mesh Optimization**: Reduce polygon count for complex models
- **Predictive Loading**: Pre-load nearby equipment data
- **Edge Computing**: Process AR data at edge servers

## Support

For technical support and questions:
- GitHub Issues: https://github.com/arxos/mobile-ar/issues
- Documentation: https://docs.arxos.io/mobile-ar
- Email: ar-support@arxos.io