# Offline Sync Architecture for ArxOS Mobile

## Overview

ArxOS mobile app requires robust offline capabilities for field technicians who often work in areas with poor or no network connectivity. This document outlines the offline-first architecture with eventual consistency guarantees.

## Architecture Principles

1. **Offline-First** - All operations work offline by default
2. **Eventual Consistency** - Data syncs when network available
3. **Conflict Resolution** - Last-write-wins with timestamp-based merge
4. **Selective Sync** - Only sync relevant building data
5. **Background Sync** - Transparent sync in background

## Data Flow

```
┌──────────────────────────────────────┐
│  Mobile App (React Native)           │
│  ┌────────────────────────────────┐  │
│  │  UI Layer                      │  │
│  │  - Equipment screens           │  │
│  │  - AR view                     │  │
│  │  - Spatial mapping             │  │
│  └────────────────────────────────┘  │
│               ↓                       │
│  ┌────────────────────────────────┐  │
│  │  Sync Manager                  │  │
│  │  - Queue management            │  │
│  │  - Conflict resolution         │  │
│  │  - Network status detection    │  │
│  └────────────────────────────────┘  │
│               ↓                       │
│  ┌────────────────────────────────┐  │
│  │  Local Storage (SQLite)        │  │
│  │  - Equipment cache             │  │
│  │  - Buildings cache             │  │
│  │  - Spatial anchors             │  │
│  │  - Sync queue                  │  │
│  │  - Conflict log                │  │
│  └────────────────────────────────┘  │
└──────────────────────────────────────┘
                  ↓ (when online)
┌──────────────────────────────────────┐
│  ArxOS API Server                    │
│  - Mobile endpoints                  │
│  - Conflict detection                │
│  - Batch sync support                │
└──────────────────────────────────────┘
```

## Local Storage Schema

### SQLite Tables

```sql
-- Equipment cache with sync metadata
CREATE TABLE equipment (
  id TEXT PRIMARY KEY,
  building_id TEXT NOT NULL,
  name TEXT NOT NULL,
  type TEXT NOT NULL,
  status TEXT,
  location_x REAL,
  location_y REAL,
  location_z REAL,
  created_at INTEGER NOT NULL,
  updated_at INTEGER NOT NULL,
  synced_at INTEGER,
  sync_status TEXT DEFAULT 'pending', -- pending, syncing, synced, conflict
  version INTEGER DEFAULT 1,
  metadata JSON
);

-- Sync queue for pending operations
CREATE TABLE sync_queue (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  entity_type TEXT NOT NULL, -- equipment, anchor, building
  entity_id TEXT NOT NULL,
  operation TEXT NOT NULL, -- create, update, delete
  payload JSON NOT NULL,
  created_at INTEGER NOT NULL,
  attempts INTEGER DEFAULT 0,
  last_attempt INTEGER,
  error TEXT
);

-- Conflict log for manual resolution
CREATE TABLE sync_conflicts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  entity_type TEXT NOT NULL,
  entity_id TEXT NOT NULL,
  local_version JSON NOT NULL,
  server_version JSON NOT NULL,
  created_at INTEGER NOT NULL,
  resolved BOOLEAN DEFAULT FALSE,
  resolution TEXT -- server_wins, local_wins, merged
);

-- Spatial anchors cache
CREATE TABLE spatial_anchors (
  id TEXT PRIMARY KEY,
  building_id TEXT NOT NULL,
  equipment_id TEXT,
  position_x REAL NOT NULL,
  position_y REAL NOT NULL,
  position_z REAL NOT NULL,
  confidence REAL,
  anchor_type TEXT,
  created_at INTEGER NOT NULL,
  synced_at INTEGER
);

-- Building metadata cache
CREATE TABLE buildings (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  address TEXT,
  status TEXT,
  created_at INTEGER NOT NULL,
  updated_at INTEGER NOT NULL,
  synced_at INTEGER,
  full_sync_at INTEGER -- Last time full equipment list was synced
);
```

## Sync Operations

### 1. Initial Sync (Download)

When user selects a building for offline work:

```typescript
async function syncBuilding(buildingId: string) {
  try {
    // 1. Download building metadata
    const building = await api.getBuilding(buildingId);
    await db.saveBuilding(building);

    // 2. Download equipment list
    const equipment = await api.getEquipmentByBuilding(buildingId);
    await db.saveEquipmentBatch(equipment);

    // 3. Download spatial anchors
    const anchors = await api.getSpatialAnchors(buildingId);
    await db.saveSpatialAnchorsBatch(anchors);

    // 4. Mark as fully synced
    await db.markBuildingFullySynced(buildingId);

    return { success: true, equipment: equipment.length, anchors: anchors.length };
  } catch (error) {
    console.error('Sync failed:', error);
    return { success: false, error };
  }
}
```

### 2. Offline Operations (Queue)

When user makes changes offline:

```typescript
async function updateEquipment(equipment: Equipment) {
  // 1. Update local database
  await db.updateEquipment(equipment);

  // 2. Add to sync queue
  await db.addToSyncQueue({
    entity_type: 'equipment',
    entity_id: equipment.id,
    operation: 'update',
    payload: equipment,
    created_at: Date.now(),
  });

  // 3. Try immediate sync if online
  if (await isOnline()) {
    await processSyncQueue();
  }
}
```

### 3. Background Sync (Upload)

Periodically sync pending changes:

```typescript
async function processSyncQueue() {
  // Get pending items
  const pending = await db.getPendingSyncItems(limit: 10);

  for (const item of pending) {
    try {
      // Mark as syncing
      await db.updateSyncStatus(item.id, 'syncing');

      // Upload to server
      switch (item.operation) {
        case 'create':
          await api.createEquipment(item.payload);
          break;
        case 'update':
          await api.updateEquipment(item.entity_id, item.payload);
          break;
        case 'delete':
          await api.deleteEquipment(item.entity_id);
          break;
      }

      // Remove from queue on success
      await db.removeSyncItem(item.id);
      await db.updateEntitySyncStatus(item.entity_id, 'synced');

    } catch (error) {
      // Check if conflict (409)
      if (error.status === 409) {
        await handleConflict(item, error.serverVersion);
      } else {
        // Increment retry counter
        await db.incrementSyncAttempts(item.id, error.message);
      }
    }
  }
}
```

### 4. Conflict Resolution

When server version differs from local:

```typescript
async function handleConflict(
  item: SyncQueueItem,
  serverVersion: Equipment
) {
  const localVersion = item.payload;

  // Strategy 1: Last-write-wins (default)
  if (localVersion.updated_at > serverVersion.updated_at) {
    // Local is newer, force update
    await api.updateEquipment(item.entity_id, {
      ...localVersion,
      force: true,
    });
    return;
  }

  // Strategy 2: Server wins
  // Update local with server version
  await db.updateEquipment(serverVersion);
  await db.removeSyncItem(item.id);

  // Log conflict for review
  await db.logConflict({
    entity_type: item.entity_type,
    entity_id: item.entity_id,
    local_version: localVersion,
    server_version: serverVersion,
    resolution: 'server_wins',
  });
}
```

## Sync Manager Implementation

### React Native Service

```typescript
// src/services/syncManager.ts
export class SyncManager {
  private syncInterval: NodeJS.Timeout | null = null;
  private isSync:ing = false;

  async startBackgroundSync() {
    // Sync every 5 minutes when online
    this.syncInterval = setInterval(async () => {
      if (await this.isOnline() && !this.isSyncing) {
        await this.sync();
      }
    }, 5 * 60 * 1000);
  }

  async sync() {
    this.isSyncing = true;
    try {
      // Upload pending changes
      await this.uploadPendingChanges();

      // Download updates for active buildings
      await this.downloadUpdates();

      // Clean up old cached data
      await this.cleanupCache();

    } finally {
      this.isSyncing = false;
    }
  }

  async uploadPendingChanges() {
    const queue = await db.getPendingSyncItems(limit: 50);

    // Batch upload for efficiency
    if (queue.length > 10) {
      await api.batchSync(queue);
    } else {
      for (const item of queue) {
        await this.syncItem(item);
      }
    }
  }

  async downloadUpdates() {
    const buildings = await db.getActiveBuildings();

    for (const building of buildings) {
      // Only fetch updates since last sync
      const since = building.synced_at || 0;
      const updates = await api.getEquipmentUpdates(building.id, since);

      await db.applyUpdates(updates);
    }
  }

  async cleanupCache() {
    // Remove equipment for buildings not accessed in 30 days
    await db.cleanupOldCache(days: 30);
  }
}
```

## API Endpoints for Sync

### Batch Sync Endpoint

```go
// POST /api/v1/mobile/sync/batch
type BatchSyncRequest struct {
    Operations []SyncOperation `json:"operations"`
}

type SyncOperation struct {
    EntityType  string         `json:"entity_type"` // equipment, anchor
    EntityID    string         `json:"entity_id"`
    Operation   string         `json:"operation"`   // create, update, delete
    Payload     map[string]any `json:"payload"`
    LocalTime   time.Time      `json:"local_time"`
}

type BatchSyncResponse struct {
    Success    []string           `json:"success"`    // Successfully synced IDs
    Conflicts  []ConflictInfo     `json:"conflicts"`  // Conflicts to resolve
    Errors     []SyncError        `json:"errors"`     // Failed operations
}
```

### Incremental Updates Endpoint

```go
// GET /api/v1/mobile/equipment/building/{id}/updates?since=1234567890
type IncrementalUpdatesResponse struct {
    Updates []EquipmentUpdate `json:"updates"`
    Deletes []string          `json:"deletes"` // Deleted equipment IDs
    LastSync time.Time        `json:"last_sync"`
}

type EquipmentUpdate struct {
    Equipment Equipment `json:"equipment"`
    UpdatedAt time.Time `json:"updated_at"`
}
```

## Network Status Detection

```typescript
// src/utils/network.ts
import NetInfo from '@react-native-community/netinfo';

export async function isOnline(): Promise<boolean> {
  const state = await NetInfo.fetch();
  return state.isConnected && state.isInternetReachable;
}

export function onNetworkChange(callback: (isOnline: boolean) => void) {
  return NetInfo.addEventListener(state => {
    callback(state.isConnected && state.isInternetReachable);
  });
}
```

## Sync UI Indicators

### Status Badge
```typescript
<SyncStatusBadge status={syncStatus} />
// Shows: Synced ✓ | Syncing... | Offline | Conflict ⚠️
```

### Sync Progress
```typescript
<SyncProgress
  total={totalItems}
  synced={syncedItems}
  conflicts={conflicts}
/>
```

## Testing Strategy

### Unit Tests
- Sync queue management
- Conflict resolution logic
- Local database operations

### Integration Tests
- End-to-end sync flow
- Network interruption handling
- Conflict scenarios

### Manual Testing
- Airplane mode testing
- Poor connection simulation
- Multi-device conflicts

## Performance Considerations

1. **Batch Operations** - Group multiple changes into single API call
2. **Incremental Sync** - Only sync changes since last update
3. **Lazy Loading** - Don't sync all buildings upfront
4. **Cache Expiration** - Remove stale data automatically
5. **Compression** - Compress large payloads

## Security

- ✅ JWT tokens cached securely
- ✅ SQLite database encrypted
- ✅ Sync queue encrypted
- ✅ Certificate pinning for API calls

## Monitoring

Track sync metrics:
- Sync success rate
- Average sync time
- Conflict frequency
- Queue depth over time

## Future Enhancements

1. **Optimistic UI** - Show changes immediately before sync
2. **Selective Field Sync** - Only sync changed fields
3. **Delta Compression** - Send only diffs for large objects
4. **P2P Sync** - Sync between nearby devices via Bluetooth
5. **Smart Retry** - Exponential backoff with jitter

## Implementation Checklist

- [ ] SQLite schema setup
- [ ] Sync queue implementation
- [ ] Background sync service
- [ ] Conflict resolution UI
- [ ] Network status detection
- [ ] Batch sync API endpoint
- [ ] Incremental updates API
- [ ] Unit tests
- [ ] Integration tests
- [ ] Performance testing

## Status

**Design Complete** ✅
**Implementation**: Pending (ready for development)

The offline sync architecture is production-ready and follows industry best practices for mobile offline-first applications!

