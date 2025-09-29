# ArxOS Mobile Technical Specifications

## System Architecture

### High-Level Architecture
```
┌─────────────────────────────────────┐
│           React Native App          │
├─────────────────────────────────────┤
│         Redux Store                 │
├─────────────────────────────────────┤
│      API Client & Sync Queue        │
├─────────────────────────────────────┤
│      Local SQLite Database          │
├─────────────────────────────────────┤
│    AR Engine & Spatial Processing   │
└─────────────────────────────────────┘
```

### Component Architecture
```
Mobile App
├── Presentation Layer
│   ├── Screens (React Components)
│   ├── Components (Reusable UI)
│   └── Navigation (React Navigation)
├── Business Logic Layer
│   ├── Redux Slices
│   ├── Services
│   └── Utilities
├── Data Layer
│   ├── API Client
│   ├── Local Storage
│   └── Sync Manager
└── Platform Layer
    ├── AR Engine
    ├── Camera
    └── Native Modules
```

## Data Models

### Core Data Types

#### Equipment
```typescript
interface Equipment {
  id: string;
  name: string;
  type: string;
  status: 'normal' | 'needs-repair' | 'failed' | 'offline' | 'maintenance';
  location: {
    buildingId: string;
    floorId: string;
    roomId: string;
    coordinates?: {
      x: number;
      y: number;
      z: number;
    };
  };
  specifications: {
    model: string;
    manufacturer: string;
    serialNumber: string;
    installationDate: Date;
  };
  lastUpdated: Date;
  lastUpdatedBy: string;
}
```

#### Equipment Status Update
```typescript
interface EquipmentStatusUpdate {
  id: string;
  equipmentId: string;
  status: 'normal' | 'needs-repair' | 'failed' | 'offline' | 'maintenance';
  notes: string;
  photos: string[];
  location: {
    latitude: number;
    longitude: number;
    accuracy: number;
  };
  timestamp: Date;
  technicianId: string;
  buildingId: string;
  floorId: string;
  roomId: string;
  syncStatus: 'pending' | 'synced' | 'failed';
}
```

#### Spatial Anchor
```typescript
interface SpatialAnchor {
  id: string;
  equipmentId: string;
  position: {
    x: number;
    y: number;
    z: number;
  };
  rotation: {
    x: number;
    y: number;
    z: number;
    w: number;
  };
  confidence: number;
  platform: 'ARKit' | 'ARCore';
  buildingId: string;
  createdAt: Date;
  updatedAt: Date;
}
```

#### Sync Queue Item
```typescript
interface SyncQueueItem {
  id: string;
  type: 'equipment_update' | 'spatial_update' | 'photo_upload';
  data: any;
  priority: 'low' | 'medium' | 'high';
  retryCount: number;
  maxRetries: number;
  createdAt: Date;
  lastAttempt: Date;
  status: 'pending' | 'processing' | 'completed' | 'failed';
}
```

## API Specifications

### Authentication
```typescript
// Login Request
interface LoginRequest {
  username: string;
  password: string;
  deviceInfo: {
    platform: 'ios' | 'android';
    version: string;
    deviceId: string;
  };
}

// Login Response
interface LoginResponse {
  accessToken: string;
  refreshToken: string;
  expiresIn: number;
  user: {
    id: string;
    username: string;
    role: string;
    permissions: string[];
  };
}
```

### Equipment API
```typescript
// Search Equipment
GET /api/v1/mobile/equipment/search
Query Parameters:
- q: string (search query)
- building: string (building ID)
- floor?: string (floor ID)
- room?: string (room ID)
- type?: string (equipment type)
- status?: string (equipment status)
- limit?: number (default: 20)
- offset?: number (default: 0)

Response:
{
  equipment: Equipment[];
  total: number;
  hasMore: boolean;
}

// Get Equipment Details
GET /api/v1/mobile/equipment/{equipmentId}
Response: Equipment

// Update Equipment Status
PUT /api/v1/mobile/equipment/{equipmentId}/status
Body: EquipmentStatusUpdate
Response: {
  success: boolean;
  updateId: string;
  syncedAt: string;
}

// Upload Equipment Photos
POST /api/v1/mobile/equipment/{equipmentId}/photos
Body: FormData with photos
Response: {
  photos: string[];
  uploadedAt: string;
}
```

### Spatial API
```typescript
// Create Spatial Anchor
POST /api/v1/mobile/spatial/anchors
Body: {
  equipmentId: string;
  position: Vector3;
  rotation: Quaternion;
  confidence: number;
  platform: string;
}
Response: {
  anchorId: string;
  success: boolean;
}

// Update Spatial Anchor
PUT /api/v1/mobile/spatial/anchors/{anchorId}
Body: {
  position: Vector3;
  rotation: Quaternion;
  confidence: number;
}
Response: {
  success: boolean;
  updatedAt: string;
}

// Get Building Spatial Anchors
GET /api/v1/mobile/spatial/anchors/building/{buildingId}
Response: SpatialAnchor[]
```

### Sync API
```typescript
// Sync Equipment Updates
POST /api/v1/mobile/sync/equipment-updates
Body: EquipmentStatusUpdate[]
Response: {
  synced: number;
  failed: number;
  errors: string[];
}

// Sync Spatial Updates
POST /api/v1/mobile/sync/spatial-updates
Body: SpatialAnchor[]
Response: {
  synced: number;
  failed: number;
  errors: string[];
}

// Get Sync Status
GET /api/v1/mobile/sync/status
Response: {
  lastSync: string;
  pendingUpdates: number;
  syncInProgress: boolean;
}
```

## Database Schema

### Local SQLite Schema
```sql
-- Equipment cache
CREATE TABLE equipment_cache (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    type TEXT NOT NULL,
    status TEXT NOT NULL,
    building_id TEXT NOT NULL,
    floor_id TEXT,
    room_id TEXT,
    specifications TEXT, -- JSON
    last_updated TEXT,
    cached_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Equipment status updates queue
CREATE TABLE equipment_updates_queue (
    id TEXT PRIMARY KEY,
    equipment_id TEXT NOT NULL,
    status TEXT NOT NULL,
    notes TEXT,
    photos TEXT, -- JSON array
    location TEXT, -- JSON
    building_id TEXT NOT NULL,
    floor_id TEXT,
    room_id TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    synced_at TEXT,
    sync_status TEXT DEFAULT 'pending',
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3
);

-- Spatial anchors cache
CREATE TABLE spatial_anchors_cache (
    id TEXT PRIMARY KEY,
    equipment_id TEXT NOT NULL,
    position TEXT NOT NULL, -- JSON
    rotation TEXT NOT NULL, -- JSON
    confidence REAL DEFAULT 0.0,
    platform TEXT NOT NULL,
    building_id TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Spatial updates queue
CREATE TABLE spatial_updates_queue (
    id TEXT PRIMARY KEY,
    equipment_id TEXT NOT NULL,
    spatial_anchor_id TEXT,
    position TEXT NOT NULL, -- JSON
    rotation TEXT NOT NULL, -- JSON
    confidence REAL DEFAULT 0.0,
    platform TEXT NOT NULL,
    building_id TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    synced_at TEXT,
    sync_status TEXT DEFAULT 'pending',
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3
);

-- Sync status
CREATE TABLE sync_status (
    id INTEGER PRIMARY KEY,
    last_sync TEXT,
    sync_in_progress INTEGER DEFAULT 0,
    pending_updates INTEGER DEFAULT 0,
    last_error TEXT
);

-- App settings
CREATE TABLE app_settings (
    key TEXT PRIMARY KEY,
    value TEXT,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);
```

## Redux Store Structure

### Store Configuration
```typescript
interface RootState {
  auth: AuthState;
  equipment: EquipmentState;
  spatial: SpatialState;
  sync: SyncState;
  ar: ARState;
  network: NetworkState;
  app: AppState;
}
```

### Auth State
```typescript
interface AuthState {
  isAuthenticated: boolean;
  user: User | null;
  token: string | null;
  refreshToken: string | null;
  loading: boolean;
  error: string | null;
}
```

### Equipment State
```typescript
interface EquipmentState {
  searchResults: Equipment[];
  selectedEquipment: Equipment | null;
  statusUpdates: EquipmentStatusUpdate[];
  searchHistory: string[];
  loading: boolean;
  error: string | null;
}
```

### Spatial State
```typescript
interface SpatialState {
  anchors: SpatialAnchor[];
  selectedAnchor: SpatialAnchor | null;
  arSessionActive: boolean;
  arTrackingState: 'normal' | 'limited' | 'notAvailable';
  loading: boolean;
  error: string | null;
}
```

### Sync State
```typescript
interface SyncState {
  isOnline: boolean;
  syncInProgress: boolean;
  lastSync: Date | null;
  pendingUpdates: number;
  failedUpdates: number;
  syncErrors: string[];
}
```

### AR State
```typescript
interface ARState {
  isSupported: boolean;
  permissionGranted: boolean;
  sessionActive: boolean;
  trackingState: 'normal' | 'limited' | 'notAvailable';
  detectedAnchors: SpatialAnchor[];
  selectedAnchor: SpatialAnchor | null;
  cameraPosition: Vector3 | null;
  cameraRotation: Quaternion | null;
}
```

## Service Layer Architecture

### API Service
```typescript
class APIService {
  private baseURL: string;
  private token: string | null = null;
  private refreshToken: string | null = null;

  constructor(baseURL: string) {
    this.baseURL = baseURL;
  }

  // Authentication
  async login(credentials: LoginRequest): Promise<LoginResponse>;
  async refreshToken(): Promise<string>;
  async logout(): Promise<void>;

  // Equipment operations
  async searchEquipment(query: string, buildingId: string, filters?: any): Promise<Equipment[]>;
  async getEquipment(equipmentId: string): Promise<Equipment>;
  async updateEquipmentStatus(update: EquipmentStatusUpdate): Promise<void>;
  async uploadPhotos(equipmentId: string, photos: string[]): Promise<string[]>;

  // Spatial operations
  async createSpatialAnchor(anchor: SpatialAnchor): Promise<string>;
  async updateSpatialAnchor(anchorId: string, updates: Partial<SpatialAnchor>): Promise<void>;
  async getBuildingAnchors(buildingId: string): Promise<SpatialAnchor[]>;

  // Sync operations
  async syncEquipmentUpdates(updates: EquipmentStatusUpdate[]): Promise<SyncResult>;
  async syncSpatialUpdates(updates: SpatialAnchor[]): Promise<SyncResult>;
  async getSyncStatus(): Promise<SyncStatus>;
}
```

### Sync Service
```typescript
class SyncService {
  private db: SQLiteDatabase;
  private apiService: APIService;

  constructor(db: SQLiteDatabase, apiService: APIService) {
    this.db = db;
    this.apiService = apiService;
  }

  // Queue management
  async queueEquipmentUpdate(update: EquipmentStatusUpdate): Promise<void>;
  async queueSpatialUpdate(update: SpatialAnchor): Promise<void>;
  async getPendingUpdates(): Promise<SyncQueueItem[]>;

  // Sync operations
  async syncPendingUpdates(): Promise<SyncResult>;
  async syncEquipmentUpdates(): Promise<SyncResult>;
  async syncSpatialUpdates(): Promise<SyncResult>;

  // Conflict resolution
  async resolveConflicts(conflicts: Conflict[]): Promise<void>;
  async mergeUpdates(updates: EquipmentStatusUpdate[]): Promise<EquipmentStatusUpdate[]>;

  // Status management
  async markUpdateAsSynced(updateId: string): Promise<void>;
  async markUpdateAsFailed(updateId: string, error: string): Promise<void>;
  async incrementRetryCount(updateId: string): Promise<void>;
}
```

### AR Service
```typescript
class ARService {
  private arSession: ARSession | null = null;
  private isSupported: boolean = false;

  constructor() {
    this.checkSupport();
  }

  // Session management
  async startSession(): Promise<void>;
  async stopSession(): Promise<void>;
  async pauseSession(): Promise<void>;
  async resumeSession(): Promise<void>;

  // Anchor operations
  async createAnchor(position: Vector3, rotation: Quaternion): Promise<SpatialAnchor>;
  async updateAnchor(anchorId: string, position: Vector3, rotation: Quaternion): Promise<void>;
  async removeAnchor(anchorId: string): Promise<void>;
  async getAnchors(): Promise<SpatialAnchor[]>;

  // Equipment detection
  async detectEquipment(equipmentId: string): Promise<SpatialAnchor | null>;
  async overlayEquipment(equipment: Equipment): Promise<void>;
  async navigateToEquipment(equipmentId: string): Promise<void>;

  // Camera operations
  async getCameraPosition(): Promise<Vector3>;
  async getCameraRotation(): Promise<Quaternion>;
  async capturePhoto(): Promise<string>;
}
```

## Performance Specifications

### Response Time Requirements
- **App Launch**: < 2 seconds
- **Equipment Search**: < 1 second
- **Status Update**: < 500ms
- **AR Session Start**: < 3 seconds
- **Photo Capture**: < 1 second
- **Offline Sync**: < 5 seconds for 100 updates

### Memory Requirements
- **Base App**: < 100MB RAM
- **AR Session**: < 200MB RAM
- **Photo Storage**: < 500MB local storage
- **Database**: < 100MB local storage

### Battery Optimization
- **Background Sync**: Limited to WiFi
- **GPS Usage**: Only when updating location
- **Camera Usage**: Only during AR sessions
- **Network Requests**: Batched and optimized

## Security Specifications

### Authentication
- **JWT Tokens**: Access token (15 min) + Refresh token (7 days)
- **Token Storage**: Secure storage (Keychain/Keystore)
- **Biometric Auth**: Touch ID/Face ID support
- **Certificate Pinning**: Prevent MITM attacks

### Data Protection
- **Local Encryption**: SQLite database encryption
- **Photo Encryption**: Encrypted photo storage
- **Network Encryption**: TLS 1.3 for all API calls
- **Data Validation**: Input validation and sanitization

### Privacy
- **Location Data**: Only collected when updating equipment
- **Photo Data**: Stored locally, uploaded to secure server
- **User Data**: Minimal data collection, GDPR compliant
- **Analytics**: Anonymous usage analytics only

## Error Handling

### Error Types
```typescript
enum ErrorType {
  NETWORK_ERROR = 'NETWORK_ERROR',
  AUTHENTICATION_ERROR = 'AUTHENTICATION_ERROR',
  VALIDATION_ERROR = 'VALIDATION_ERROR',
  AR_ERROR = 'AR_ERROR',
  SYNC_ERROR = 'SYNC_ERROR',
  STORAGE_ERROR = 'STORAGE_ERROR',
  CAMERA_ERROR = 'CAMERA_ERROR',
  UNKNOWN_ERROR = 'UNKNOWN_ERROR'
}

interface AppError {
  type: ErrorType;
  message: string;
  code?: string;
  details?: any;
  timestamp: Date;
  userId?: string;
  deviceId?: string;
}
```

### Error Recovery
- **Network Errors**: Automatic retry with exponential backoff
- **Authentication Errors**: Automatic token refresh
- **AR Errors**: Graceful fallback to text input
- **Sync Errors**: Queue for retry, manual sync option
- **Storage Errors**: Data recovery, cache cleanup

## Testing Specifications

### Unit Testing
- **Coverage Target**: 80%+ code coverage
- **Framework**: Jest + React Native Testing Library
- **Focus Areas**: Services, utilities, Redux slices
- **Mocking**: API calls, native modules, AR functionality

### Integration Testing
- **API Integration**: Test API client with mock server
- **Database Integration**: Test SQLite operations
- **AR Integration**: Test AR functionality with mock data
- **Sync Integration**: Test sync mechanisms

### End-to-End Testing
- **Framework**: Detox (React Native E2E)
- **Test Scenarios**: Complete user workflows
- **Platforms**: iOS and Android
- **Devices**: Multiple device sizes and OS versions

### Performance Testing
- **Load Testing**: Test with large datasets
- **Memory Testing**: Monitor memory usage
- **Battery Testing**: Test battery consumption
- **Network Testing**: Test offline/online scenarios

## Deployment Specifications

### Build Configuration
```typescript
// Development
const devConfig = {
  apiBaseURL: 'https://api-dev.arxos.com',
  logLevel: 'debug',
  enableAnalytics: false,
  enableCrashReporting: false
};

// Staging
const stagingConfig = {
  apiBaseURL: 'https://api-staging.arxos.com',
  logLevel: 'info',
  enableAnalytics: true,
  enableCrashReporting: true
};

// Production
const prodConfig = {
  apiBaseURL: 'https://api.arxos.com',
  logLevel: 'error',
  enableAnalytics: true,
  enableCrashReporting: true
};
```

### App Store Requirements
- **iOS**: iOS 13.0+ support, App Store guidelines compliance
- **Android**: API level 21+ support, Play Store guidelines compliance
- **Permissions**: Camera, Location, Network access
- **Privacy**: Privacy policy, data usage disclosure

### CI/CD Pipeline
- **Build**: Automated builds for all environments
- **Testing**: Automated test execution
- **Code Quality**: ESLint, TypeScript checks
- **Deployment**: Automated app store submissions
- **Monitoring**: Crash reporting, analytics integration

## Monitoring & Analytics

### Performance Monitoring
- **App Performance**: Load times, crash rates
- **API Performance**: Response times, error rates
- **AR Performance**: Tracking accuracy, session stability
- **Sync Performance**: Success rates, sync times

### User Analytics
- **Usage Patterns**: Feature usage, session duration
- **Error Tracking**: Error frequency, user impact
- **Performance Metrics**: App responsiveness, battery usage
- **Business Metrics**: Equipment updates, AR usage

### Crash Reporting
- **Real-time Alerts**: Critical error notifications
- **Error Aggregation**: Group similar errors
- **User Context**: Device info, user actions
- **Resolution Tracking**: Error resolution progress

This technical specification provides the foundation for implementing the ArxOS mobile application with a focus on reliability, performance, and maintainability.
