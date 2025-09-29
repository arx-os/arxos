# ArxOS Mobile Application - Design, Architecture & Planning

## Overview

The ArxOS mobile application serves as the **bidirectional data input interface** for building management, enabling field technicians to interact with the building management system through AR and text-based interfaces. This document outlines the complete design, architecture, and implementation plan.

## Core Philosophy

**"Mobile as Data Input Terminal"** - The mobile app is not a consumer-facing application but a **professional tool** for field technicians to:
- Input equipment status updates
- Capture spatial data through AR
- Provide bidirectional communication with the building management system
- Enable offline-first data collection with sync capabilities

## Technical Architecture

### Technology Stack
- **Framework**: React Native (cross-platform)
- **State Management**: Redux Toolkit
- **Local Storage**: SQLite (react-native-sqlite-storage)
- **AR Framework**: React Native AR (react-native-arkit, react-native-ar)
- **Networking**: Axios with offline queue
- **Authentication**: JWT with refresh tokens
- **Push Notifications**: Firebase Cloud Messaging

### Architecture Pattern
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

## Core Features & Data Flow

### 1. Equipment Status Input
**Primary Function**: Allow technicians to update equipment status in the field

**Data Flow**:
```
Field Technician → Mobile App → Status Update → Offline Queue → Sync → PostGIS
```

**Implementation**:
```typescript
interface EquipmentStatusUpdate {
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
}
```

### 2. AR Spatial Data Collection
**Primary Function**: Capture and update spatial positioning of equipment

**AR Data Flow**:
```
AR Camera → Spatial Anchor Detection → Position Update → Sync → PostGIS Spatial Anchors
```

**Implementation**:
```typescript
interface SpatialDataUpdate {
  equipmentId: string;
  spatialAnchor: {
    id: string;
    position: Vector3;
    rotation: Quaternion;
    confidence: number;
  };
  arPlatform: 'ARKit' | 'ARCore';
  timestamp: Date;
  technicianId: string;
  buildingId: string;
}
```

### 3. Text-Based Equipment Lookup
**Primary Function**: Quick equipment identification and status updates

**Text Input Flow**:
```
Text Input → Equipment Search → Equipment Selection → Status Update → Sync
```

**Implementation**:
```typescript
interface EquipmentSearch {
  query: string;
  buildingId: string;
  filters: {
    floor?: string;
    room?: string;
    type?: string;
    status?: string;
  };
}

interface EquipmentSearchResult {
  equipmentId: string;
  name: string;
  type: string;
  location: string;
  status: string;
  lastUpdated: Date;
}
```

## Database Schema Extensions

### Mobile-Specific Tables
```sql
-- Mobile device registration and management
CREATE TABLE mobile_devices (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    device_token TEXT UNIQUE,
    platform TEXT NOT NULL CHECK (platform IN ('ios', 'android')),
    app_version TEXT NOT NULL,
    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Offline equipment status updates queue
CREATE TABLE mobile_equipment_updates (
    id TEXT PRIMARY KEY,
    device_id TEXT NOT NULL,
    equipment_id TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('normal', 'needs-repair', 'failed', 'offline', 'maintenance')),
    notes TEXT,
    photos JSON, -- Array of photo file paths/URLs
    location JSON, -- GPS coordinates and accuracy
    building_id TEXT NOT NULL,
    floor_id TEXT,
    room_id TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    synced_at TIMESTAMP,
    sync_status TEXT DEFAULT 'pending' CHECK (sync_status IN ('pending', 'synced', 'failed')),
    FOREIGN KEY (device_id) REFERENCES mobile_devices(id) ON DELETE CASCADE,
    FOREIGN KEY (equipment_id) REFERENCES equipment(id) ON DELETE CASCADE,
    FOREIGN KEY (building_id) REFERENCES buildings(id) ON DELETE CASCADE
);

-- AR spatial data updates
CREATE TABLE mobile_spatial_updates (
    id TEXT PRIMARY KEY,
    device_id TEXT NOT NULL,
    equipment_id TEXT NOT NULL,
    spatial_anchor_id TEXT,
    position JSON NOT NULL, -- {x, y, z}
    rotation JSON NOT NULL, -- {x, y, z, w} quaternion
    confidence REAL DEFAULT 0.0,
    ar_platform TEXT NOT NULL CHECK (ar_platform IN ('ARKit', 'ARCore')),
    building_id TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    synced_at TIMESTAMP,
    sync_status TEXT DEFAULT 'pending' CHECK (sync_status IN ('pending', 'synced', 'failed')),
    FOREIGN KEY (device_id) REFERENCES mobile_devices(id) ON DELETE CASCADE,
    FOREIGN KEY (equipment_id) REFERENCES equipment(id) ON DELETE CASCADE,
    FOREIGN KEY (building_id) REFERENCES buildings(id) ON DELETE CASCADE
);

-- Push notification queue
CREATE TABLE mobile_notifications (
    id TEXT PRIMARY KEY,
    device_id TEXT NOT NULL,
    title TEXT NOT NULL,
    body TEXT NOT NULL,
    data JSON,
    notification_type TEXT NOT NULL CHECK (notification_type IN ('equipment_alert', 'work_order', 'system_update')),
    sent_at TIMESTAMP,
    delivered_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (device_id) REFERENCES mobile_devices(id) ON DELETE CASCADE
);

-- Mobile app analytics
CREATE TABLE mobile_analytics (
    id TEXT PRIMARY KEY,
    device_id TEXT NOT NULL,
    event_type TEXT NOT NULL,
    event_data JSON,
    session_id TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (device_id) REFERENCES mobile_devices(id) ON DELETE CASCADE
);
```

## API Endpoints Design

### Mobile-Specific API Routes
```typescript
// Device Management
POST   /api/v1/mobile/devices/register
PUT    /api/v1/mobile/devices/{deviceId}
DELETE /api/v1/mobile/devices/{deviceId}

// Equipment Operations
GET    /api/v1/mobile/equipment/search?q={query}&building={id}&floor={id}&room={id}
GET    /api/v1/mobile/equipment/{equipmentId}
PUT    /api/v1/mobile/equipment/{equipmentId}/status
POST   /api/v1/mobile/equipment/{equipmentId}/photos
GET    /api/v1/mobile/equipment/{equipmentId}/history

// Spatial Data
POST   /api/v1/mobile/spatial/anchors
PUT    /api/v1/mobile/spatial/anchors/{anchorId}
GET    /api/v1/mobile/spatial/anchors/building/{buildingId}

// Sync Operations
POST   /api/v1/mobile/sync/equipment-updates
POST   /api/v1/mobile/sync/spatial-updates
GET    /api/v1/mobile/sync/status

// Offline Data
GET    /api/v1/mobile/offline/equipment/{buildingId}
GET    /api/v1/mobile/offline/spatial/{buildingId}
POST   /api/v1/mobile/offline/upload
```

### API Request/Response Examples
```typescript
// Equipment Status Update
interface EquipmentStatusUpdateRequest {
  equipmentId: string;
  status: string;
  notes?: string;
  photos?: string[];
  location: {
    latitude: number;
    longitude: number;
    accuracy: number;
  };
  timestamp: string;
}

interface EquipmentStatusUpdateResponse {
  success: boolean;
  updateId: string;
  syncedAt: string;
  message?: string;
}

// Spatial Data Update
interface SpatialDataUpdateRequest {
  equipmentId: string;
  spatialAnchor: {
    position: { x: number; y: number; z: number };
    rotation: { x: number; y: number; z: number; w: number };
    confidence: number;
  };
  arPlatform: string;
  timestamp: string;
}

// Equipment Search
interface EquipmentSearchRequest {
  query: string;
  buildingId: string;
  filters?: {
    floor?: string;
    room?: string;
    type?: string;
    status?: string;
  };
  limit?: number;
  offset?: number;
}

interface EquipmentSearchResponse {
  equipment: Array<{
    id: string;
    name: string;
    type: string;
    location: string;
    status: string;
    lastUpdated: string;
  }>;
  total: number;
  hasMore: boolean;
}
```

## React Native Implementation

### Project Structure
```
mobile/
├── src/
│   ├── components/
│   │   ├── Equipment/
│   │   │   ├── EquipmentSearch.tsx
│   │   │   ├── EquipmentStatusUpdate.tsx
│   │   │   └── EquipmentDetail.tsx
│   │   ├── AR/
│   │   │   ├── ARCamera.tsx
│   │   │   ├── SpatialAnchorCapture.tsx
│   │   │   └── ARNavigation.tsx
│   │   └── Common/
│   │       ├── OfflineIndicator.tsx
│   │       └── SyncStatus.tsx
│   ├── screens/
│   │   ├── EquipmentScreen.tsx
│   │   ├── ARScreen.tsx
│   │   ├── SearchScreen.tsx
│   │   └── SyncScreen.tsx
│   ├── services/
│   │   ├── api.ts
│   │   ├── sync.ts
│   │   ├── ar.ts
│   │   └── storage.ts
│   ├── store/
│   │   ├── index.ts
│   │   ├── equipmentSlice.ts
│   │   ├── syncSlice.ts
│   │   └── arSlice.ts
│   ├── types/
│   │   ├── equipment.ts
│   │   ├── spatial.ts
│   │   └── api.ts
│   └── utils/
│       ├── offline.ts
│       ├── validation.ts
│       └── constants.ts
├── android/
├── ios/
├── package.json
└── README.md
```

### Core Services Implementation

#### API Service
```typescript
// src/services/api.ts
import axios from 'axios';
import { store } from '../store';
import { syncQueue } from './sync';

class APIService {
  private baseURL: string;
  private token: string | null = null;

  constructor(baseURL: string) {
    this.baseURL = baseURL;
  }

  setToken(token: string) {
    this.token = token;
  }

  async searchEquipment(query: string, buildingId: string, filters?: any) {
    try {
      const response = await axios.get(`${this.baseURL}/mobile/equipment/search`, {
        params: { q: query, building: buildingId, ...filters },
        headers: { Authorization: `Bearer ${this.token}` }
      });
      return response.data;
    } catch (error) {
      throw new Error(`Equipment search failed: ${error.message}`);
    }
  }

  async updateEquipmentStatus(update: EquipmentStatusUpdate) {
    try {
      const response = await axios.put(
        `${this.baseURL}/mobile/equipment/${update.equipmentId}/status`,
        update,
        { headers: { Authorization: `Bearer ${this.token}` } }
      );
      return response.data;
    } catch (error) {
      // Queue for offline sync
      await syncQueue.addEquipmentUpdate(update);
      throw new Error(`Status update queued for sync: ${error.message}`);
    }
  }

  async updateSpatialData(update: SpatialDataUpdate) {
    try {
      const response = await axios.post(
        `${this.baseURL}/mobile/spatial/anchors`,
        update,
        { headers: { Authorization: `Bearer ${this.token}` } }
      );
      return response.data;
    } catch (error) {
      // Queue for offline sync
      await syncQueue.addSpatialUpdate(update);
      throw new Error(`Spatial update queued for sync: ${error.message}`);
    }
  }
}

export const apiService = new APIService(process.env.API_BASE_URL || 'https://api.arxos.com');
```

#### Offline Sync Service
```typescript
// src/services/sync.ts
import SQLite from 'react-native-sqlite-storage';
import { apiService } from './api';

class SyncService {
  private db: SQLite.SQLiteDatabase;

  constructor() {
    this.db = SQLite.openDatabase({
      name: 'arxos_mobile.db',
      location: 'default',
    });
  }

  async addEquipmentUpdate(update: EquipmentStatusUpdate) {
    const query = `
      INSERT INTO mobile_equipment_updates 
      (id, device_id, equipment_id, status, notes, photos, location, building_id, created_at)
      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    `;
    
    await this.db.executeSql(query, [
      update.id,
      update.deviceId,
      update.equipmentId,
      update.status,
      update.notes,
      JSON.stringify(update.photos),
      JSON.stringify(update.location),
      update.buildingId,
      update.timestamp.toISOString()
    ]);
  }

  async syncPendingUpdates() {
    const pendingUpdates = await this.getPendingEquipmentUpdates();
    
    for (const update of pendingUpdates) {
      try {
        await apiService.updateEquipmentStatus(update);
        await this.markUpdateAsSynced(update.id);
      } catch (error) {
        console.error(`Failed to sync update ${update.id}:`, error);
      }
    }
  }

  private async getPendingEquipmentUpdates(): Promise<EquipmentStatusUpdate[]> {
    const query = `
      SELECT * FROM mobile_equipment_updates 
      WHERE sync_status = 'pending'
      ORDER BY created_at ASC
    `;
    
    const [results] = await this.db.executeSql(query);
    const updates: EquipmentStatusUpdate[] = [];
    
    for (let i = 0; i < results.rows.length; i++) {
      const row = results.rows.item(i);
      updates.push({
        id: row.id,
        deviceId: row.device_id,
        equipmentId: row.equipment_id,
        status: row.status,
        notes: row.notes,
        photos: JSON.parse(row.photos),
        location: JSON.parse(row.location),
        buildingId: row.building_id,
        timestamp: new Date(row.created_at)
      });
    }
    
    return updates;
  }

  private async markUpdateAsSynced(updateId: string) {
    const query = `
      UPDATE mobile_equipment_updates 
      SET sync_status = 'synced', synced_at = ?
      WHERE id = ?
    `;
    
    await this.db.executeSql(query, [new Date().toISOString(), updateId]);
  }
}

export const syncService = new SyncService();
```

#### AR Service
```typescript
// src/services/ar.ts
import { ARKit } from 'react-native-arkit';

class ARService {
  async captureSpatialAnchor(equipmentId: string, position: Vector3, rotation: Quaternion) {
    try {
      // Capture AR spatial anchor
      const anchor = await ARKit.createAnchor({
        position: position,
        rotation: rotation,
        name: `equipment_${equipmentId}`
      });

      return {
        id: anchor.identifier,
        position: position,
        rotation: rotation,
        confidence: anchor.confidence || 0.8,
        platform: 'ARKit'
      };
    } catch (error) {
      throw new Error(`Failed to capture spatial anchor: ${error.message}`);
    }
  }

  async detectEquipmentInAR(equipmentId: string): Promise<SpatialAnchor | null> {
    try {
      const anchors = await ARKit.getAnchors();
      const equipmentAnchor = anchors.find(anchor => 
        anchor.name === `equipment_${equipmentId}`
      );
      
      if (equipmentAnchor) {
        return {
          id: equipmentAnchor.identifier,
          position: equipmentAnchor.position,
          rotation: equipmentAnchor.rotation,
          confidence: equipmentAnchor.confidence || 0.8,
          platform: 'ARKit'
        };
      }
      
      return null;
    } catch (error) {
      throw new Error(`Failed to detect equipment in AR: ${error.message}`);
    }
  }
}

export const arService = new ARService();
```

### Redux Store Implementation

#### Equipment Slice
```typescript
// src/store/equipmentSlice.ts
import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import { apiService } from '../services/api';

interface EquipmentState {
  searchResults: EquipmentSearchResult[];
  selectedEquipment: Equipment | null;
  statusUpdates: EquipmentStatusUpdate[];
  loading: boolean;
  error: string | null;
}

const initialState: EquipmentState = {
  searchResults: [],
  selectedEquipment: null,
  statusUpdates: [],
  loading: false,
  error: null
};

export const searchEquipment = createAsyncThunk(
  'equipment/search',
  async ({ query, buildingId, filters }: EquipmentSearchRequest) => {
    return await apiService.searchEquipment(query, buildingId, filters);
  }
);

export const updateEquipmentStatus = createAsyncThunk(
  'equipment/updateStatus',
  async (update: EquipmentStatusUpdate) => {
    return await apiService.updateEquipmentStatus(update);
  }
);

const equipmentSlice = createSlice({
  name: 'equipment',
  initialState,
  reducers: {
    selectEquipment: (state, action: PayloadAction<Equipment>) => {
      state.selectedEquipment = action.payload;
    },
    clearSearchResults: (state) => {
      state.searchResults = [];
    },
    addStatusUpdate: (state, action: PayloadAction<EquipmentStatusUpdate>) => {
      state.statusUpdates.push(action.payload);
    }
  },
  extraReducers: (builder) => {
    builder
      .addCase(searchEquipment.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(searchEquipment.fulfilled, (state, action) => {
        state.loading = false;
        state.searchResults = action.payload.equipment;
      })
      .addCase(searchEquipment.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || 'Search failed';
      })
      .addCase(updateEquipmentStatus.fulfilled, (state, action) => {
        state.statusUpdates.push(action.payload);
      });
  }
});

export const { selectEquipment, clearSearchResults, addStatusUpdate } = equipmentSlice.actions;
export default equipmentSlice.reducer;
```

## Implementation Timeline

### Phase 1: Foundation (4 weeks)
**Week 1-2: Project Setup**
- React Native project initialization
- Redux store setup
- SQLite database configuration
- Basic navigation structure

**Week 3-4: Core Services**
- API service implementation
- Offline sync service
- Local storage management
- Authentication integration

### Phase 2: Equipment Management (6 weeks)
**Week 5-6: Equipment Search**
- Text-based equipment search
- Equipment detail view
- Status update interface
- Photo capture functionality

**Week 7-8: Offline Support**
- Offline data storage
- Sync queue implementation
- Conflict resolution
- Background sync

**Week 9-10: Testing & Optimization**
- Unit testing
- Integration testing
- Performance optimization
- Bug fixes

### Phase 3: AR Integration (8 weeks)
**Week 11-12: AR Foundation**
- ARKit/ARCore integration
- Camera permissions
- Basic AR scene setup
- Spatial anchor detection

**Week 13-14: Equipment AR**
- Equipment overlay in AR
- Spatial anchor capture
- Position updates
- AR navigation

**Week 15-16: AR Data Sync**
- AR data storage
- Spatial data sync
- AR anchor management
- Performance optimization

**Week 17-18: AR Testing**
- AR functionality testing
- Spatial accuracy validation
- Cross-platform testing
- Bug fixes

### Phase 4: Production Ready (4 weeks)
**Week 19-20: Production Features**
- Push notifications
- Analytics integration
- Error handling
- Performance monitoring

**Week 21-22: Deployment**
- App store preparation
- Backend deployment
- Production testing
- Documentation

## Testing Strategy

### Unit Testing
```typescript
// Example test for equipment service
import { equipmentService } from '../services/equipment';

describe('EquipmentService', () => {
  it('should search equipment by query', async () => {
    const results = await equipmentService.searchEquipment('HVAC', 'building-1');
    expect(results).toHaveLength(2);
    expect(results[0].name).toContain('HVAC');
  });

  it('should queue status update when offline', async () => {
    // Mock offline condition
    jest.spyOn(networkInfo, 'isConnected').mockReturnValue(false);
    
    const update = {
      equipmentId: 'equipment-1',
      status: 'needs-repair',
      notes: 'Test update'
    };
    
    await equipmentService.updateStatus(update);
    
    const queuedUpdates = await syncService.getPendingUpdates();
    expect(queuedUpdates).toHaveLength(1);
  });
});
```

### Integration Testing
- API integration tests
- Database integration tests
- AR functionality tests
- Sync mechanism tests

### End-to-End Testing
- Complete user workflows
- Offline/online scenarios
- AR equipment capture
- Data sync validation

## Deployment & Distribution

### App Store Deployment
- **iOS**: App Store Connect
- **Android**: Google Play Console
- **Enterprise**: Internal distribution

### Backend Deployment
- Mobile API service deployment
- Push notification service setup
- Database migration execution
- Monitoring and logging setup

## Success Metrics

### Technical Metrics
- **Sync Success Rate**: >95% of offline updates synced successfully
- **AR Accuracy**: <10cm spatial positioning accuracy
- **App Performance**: <2s load time, <1% crash rate
- **Offline Capability**: 100% core functionality available offline

### Business Metrics
- **Equipment Updates**: Number of status updates per technician per day
- **AR Usage**: Percentage of updates using AR vs text input
- **Data Quality**: Accuracy of spatial data captured
- **User Adoption**: Number of active mobile users

## Risk Mitigation

### Technical Risks
- **AR Platform Differences**: Implement platform-specific AR handling
- **Offline Sync Conflicts**: Implement conflict resolution strategies
- **Performance Issues**: Optimize for low-end devices
- **Data Loss**: Implement robust backup and recovery

### Business Risks
- **User Adoption**: Provide comprehensive training and support
- **Data Accuracy**: Implement validation and verification
- **Integration Issues**: Thorough testing with existing systems
- **Security Concerns**: Implement enterprise-grade security

## Conclusion

The ArxOS mobile application will serve as a **critical data input terminal** for field technicians, enabling bidirectional communication with the building management system through AR and text interfaces. The implementation focuses on **reliability, offline capability, and data accuracy** rather than consumer-facing features.

The architecture is designed to be **scalable, maintainable, and extensible**, with clear separation of concerns and robust error handling. The offline-first approach ensures that technicians can work effectively even without internet connectivity, with automatic sync when connectivity is restored.

This mobile application will significantly enhance the ArxOS ecosystem by providing a **professional-grade field interface** for building management operations.
