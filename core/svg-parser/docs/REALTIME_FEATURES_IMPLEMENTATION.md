# Real-time Features Implementation

## Overview

This document describes the comprehensive real-time features implementation for the Arxos platform, including multi-user synchronization, WebSocket connections, user presence indicators, collaborative editing locks, conflict resolution, and advanced caching strategies.

## Architecture

### Core Components

1. **RealTimeService** - Main orchestrator for all real-time features
2. **WebSocketManager** - Handles WebSocket connections and room management
3. **CollaborativeEditingManager** - Manages editing locks and conflict prevention
4. **ConflictResolutionManager** - Handles conflict detection and resolution
5. **CacheService** - Advanced caching with Redis integration
6. **IntelligentPreloader** - Predictive data loading

### Service Integration

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Frontend      │    │   WebSocket      │    │   Cache         │
│   JavaScript    │◄──►│   Manager        │◄──►│   Service       │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌──────────────────┐
                       │   RealTime       │
                       │   Service        │
                       └──────────────────┘
                              │
                    ┌─────────┴─────────┐
                    ▼                   ▼
            ┌──────────────┐    ┌──────────────┐
            │Collaborative │    │  Conflict    │
            │   Editing    │    │ Resolution   │
            └──────────────┘    └──────────────┘
```

## Real-time Service Implementation

### WebSocket Manager

**File**: `services/realtime_service.py`

The WebSocket manager handles all real-time communication:

```python
class WebSocketManager:
    def __init__(self):
        self.active_connections: Dict[str, Any] = {}  # user_id -> websocket
        self.room_connections: Dict[str, Set[str]] = {}  # room_id -> set of user_ids
        self.user_presence: Dict[str, UserPresence] = {}
        self.editing_locks: Dict[str, EditingLock] = {}
        self.conflicts: Dict[str, Conflict] = {}
```

**Key Features**:
- **Connection Management**: Handles WebSocket connections and disconnections
- **Room Management**: Users can join/leave rooms (floors, buildings)
- **Message Broadcasting**: Send messages to specific users or entire rooms
- **User Presence**: Track user activity and status
- **Automatic Cleanup**: Removes expired locks and inactive users

### Collaborative Editing Manager

**File**: `services/realtime_service.py`

Manages collaborative editing locks to prevent conflicts:

```python
class CollaborativeEditingManager:
    async def acquire_lock(self, user_id: str, username: str, lock_type: LockType, 
                          resource_id: str, metadata: Dict[str, Any] = None) -> Tuple[bool, str]:
        # Check if resource is already locked
        # Create new lock if available
        # Notify other users about lock acquisition
```

**Lock Types**:
- `FLOOR_EDIT` - Floor-level editing
- `OBJECT_EDIT` - Object-level editing
- `ROUTE_EDIT` - Route editing
- `GRID_CALIBRATION` - Grid calibration
- `ANALYTICS_VIEW` - Analytics view

**Features**:
- **Automatic Expiration**: Locks expire after 5 minutes
- **Conflict Prevention**: Prevents multiple users from editing same resource
- **Lock Notifications**: Real-time notifications when locks are acquired/released
- **Graceful Cleanup**: Automatic lock release on user disconnection

### Conflict Resolution Manager

**File**: `services/realtime_service.py`

Handles conflict detection and resolution:

```python
class ConflictResolutionManager:
    async def detect_conflict(self, resource_id: str, user_id_1: str, user_id_2: str, 
                            conflict_type: str, description: str, severity: ConflictSeverity):
        # Create conflict record
        # Notify involved users
        # Provide resolution options
```

**Conflict Severity Levels**:
- `LOW` - Minor conflicts (e.g., cursor position)
- `MEDIUM` - Moderate conflicts (e.g., object properties)
- `HIGH` - Significant conflicts (e.g., object deletion)
- `CRITICAL` - Critical conflicts (e.g., floor structure)

**Resolution Strategies**:
- **Accept Mine**: Keep current user's changes
- **Accept Theirs**: Accept other user's changes
- **Merge**: Combine both sets of changes
- **Manual Resolution**: User decides manually

## Cache Service Implementation

### Redis Cache Manager

**File**: `services/cache_service.py`

Advanced caching with Redis integration and fallback local cache:

```python
class RedisCacheManager:
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_client = None
        self.cache_configs = self._initialize_cache_configs()
        self.local_cache: Dict[str, CacheItem] = {}  # Fallback local cache
```

**Cache Strategies**:
- `FLOOR_DATA` - Floor information (1 hour TTL)
- `OBJECT_DATA` - Object data (30 minutes TTL)
- `ROUTE_DATA` - Route information (30 minutes TTL)
- `ANALYTICS_DATA` - Analytics data (2 hours TTL)
- `GRID_CALIBRATION` - Grid calibration (1 hour TTL)
- `USER_SESSION` - User session data (30 minutes TTL)
- `SEARCH_RESULTS` - Search results (15 minutes TTL)

**Features**:
- **Redis Integration**: Primary cache with Redis
- **Local Fallback**: Local cache when Redis unavailable
- **Intelligent Eviction**: LRU + priority-based eviction
- **Pattern Invalidation**: Invalidate related cache entries
- **Access Tracking**: Track cache hits and access patterns

### Intelligent Preloader

**File**: `services/cache_service.py`

Predictive data loading based on user behavior:

```python
class IntelligentPreloader:
    async def predict_and_preload(self, user_id: str, current_floor_id: str):
        # Analyze user patterns
        # Preload related data
        # Optimize for common workflows
```

**Preloading Patterns**:
- **Floor Access**: Preload floor data, objects, routes
- **Analytics View**: Preload analytics data
- **Grid Calibration**: Preload grid calibration data
- **Building Floors**: Preload adjacent floors

## Frontend Integration

### Real-time Manager

**File**: `arx-web-frontend/static/js/realtime_manager.js`

Comprehensive JavaScript module for frontend real-time features:

```javascript
class RealTimeManager {
    constructor() {
        this.websocket = null;
        this.userId = null;
        this.currentRoom = null;
        this.isConnected = false;
        this.activeLocks = new Map();
        this.conflicts = new Map();
    }
}
```

**Key Features**:
- **WebSocket Connection**: Automatic connection and reconnection
- **User Presence**: Track and display user activity
- **Collaborative Editing**: Lock acquisition and management
- **Conflict Resolution**: Handle and resolve conflicts
- **Cache Management**: Preload and invalidate cache
- **Event System**: Comprehensive event handling

### Usage Examples

**Connecting to Real-time Service**:
```javascript
// Initialize real-time manager
const realtimeManager = new RealTimeManager();

// Connect to WebSocket
await realtimeManager.connect();

// Join a floor room
await realtimeManager.joinRoom('floor_123');
```

**Collaborative Editing**:
```javascript
// Acquire editing lock
const lockId = await realtimeManager.acquireLock('floor_edit', 'floor_123');

// Check if resource is locked
const lock = realtimeManager.isLocked('floor_123', 'floor_edit');

// Release lock when done
realtimeManager.releaseLock(lockId);
```

**Conflict Resolution**:
```javascript
// Listen for conflicts
realtimeManager.addEventListener('conflict_detected', (conflict) => {
    console.log('Conflict detected:', conflict);
});

// Resolve conflict
realtimeManager.resolveConflict('conflict_id', 'accept_mine');
```

**Cache Management**:
```javascript
// Preload floor data
await realtimeManager.preloadFloorData('floor_123');

// Get cache statistics
const stats = await realtimeManager.getCacheStats();

// Invalidate floor cache
await realtimeManager.invalidateFloorCache('floor_123');
```

## API Endpoints

### WebSocket Endpoint

**Endpoint**: `ws://host/v1/realtime/ws/{user_id}`

**Message Types**:
- `join_room` - Join a room
- `leave_room` - Leave a room
- `update_presence` - Update user presence
- `acquire_lock` - Acquire editing lock
- `release_lock` - Release editing lock
- `resolve_conflict` - Resolve conflict
- `broadcast` - Broadcast message to room

### REST Endpoints

**Join Room**: `POST /v1/realtime/join-room`
```json
{
    "user_id": "user123",
    "room_id": "floor_456"
}
```

**Acquire Lock**: `POST /v1/realtime/acquire-lock`
```json
{
    "user_id": "user123",
    "lock_type": "floor_edit",
    "resource_id": "floor_456",
    "metadata": {}
}
```

**Get Room Users**: `GET /v1/realtime/room-users/{room_id}`

**Get Cache Stats**: `GET /v1/realtime/cache-stats`

**Preload Floor**: `POST /v1/realtime/preload-floor`
```json
{
    "floor_id": "floor_456"
}
```

## Testing

### Test Coverage

**File**: `tests/test_realtime_features.py`

Comprehensive test suite covering:

1. **WebSocket Manager Tests**:
   - Connection/disconnection
   - Room management
   - Message broadcasting
   - User presence

2. **Collaborative Editing Tests**:
   - Lock acquisition/release
   - Conflict prevention
   - Lock expiration

3. **Conflict Resolution Tests**:
   - Conflict detection
   - Resolution strategies
   - User notifications

4. **Cache Service Tests**:
   - Cache operations
   - Invalidation strategies
   - Statistics tracking

5. **Integration Tests**:
   - Full collaborative workflow
   - Cache with real-time integration

### Running Tests

```bash
# Run all real-time tests
pytest tests/test_realtime_features.py -v

# Run specific test class
pytest tests/test_realtime_features.py::TestWebSocketManager -v

# Run with coverage
pytest tests/test_realtime_features.py --cov=services.realtime_service --cov=services.cache_service
```

## Performance Considerations

### Scalability

1. **WebSocket Connections**:
   - Efficient connection pooling
   - Automatic cleanup of inactive connections
   - Load balancing support

2. **Cache Performance**:
   - Redis clustering support
   - Local cache fallback
   - Intelligent eviction policies

3. **Memory Management**:
   - Automatic cleanup of expired locks
   - User presence cleanup
   - Conflict resolution cleanup

### Monitoring

1. **Connection Metrics**:
   - Active WebSocket connections
   - Room occupancy
   - User presence statistics

2. **Cache Metrics**:
   - Hit/miss ratios
   - Eviction rates
   - Preload effectiveness

3. **Performance Metrics**:
   - Lock acquisition times
   - Conflict resolution times
   - Message delivery latency

## Security Considerations

### Authentication

1. **User Validation**: Validate user_id in WebSocket connections
2. **Room Access**: Verify user permissions for room access
3. **Lock Authorization**: Ensure users can only lock their authorized resources

### Data Protection

1. **Message Encryption**: WebSocket messages can be encrypted
2. **Cache Security**: Sensitive data not cached in local storage
3. **Conflict Privacy**: Conflict details only shared with involved users

## Deployment

### Requirements

1. **Redis Server**: For caching and session storage
2. **WebSocket Support**: FastAPI with WebSocket support
3. **Python Dependencies**: See requirements.txt

### Configuration

```python
# Redis configuration
REDIS_URL = "redis://localhost:6379"

# Cache configuration
CACHE_TTL = {
    "floor_data": 3600,
    "object_data": 1800,
    "route_data": 1800
}

# Lock configuration
LOCK_TIMEOUT = 300  # 5 minutes
CONFLICT_TIMEOUT = 60  # 1 minute
```

### Environment Variables

```bash
# Redis configuration
REDIS_URL=redis://localhost:6379

# Cache settings
CACHE_ENABLED=true
CACHE_TTL_FLOOR=3600

# Real-time settings
REALTIME_ENABLED=true
LOCK_TIMEOUT=300
```

## Future Enhancements

### Planned Features

1. **Advanced Conflict Resolution**:
   - Machine learning-based conflict prediction
   - Automatic conflict resolution
   - Conflict history and analysis

2. **Enhanced Caching**:
   - Distributed caching with Redis Cluster
   - Cache warming strategies
   - Predictive caching based on ML

3. **Real-time Analytics**:
   - User behavior analytics
   - Performance monitoring
   - Usage pattern analysis

4. **Mobile Support**:
   - WebSocket optimization for mobile
   - Offline conflict resolution
   - Sync when reconnected

### Integration Opportunities

1. **Notification System**: Integration with push notifications
2. **Audit Logging**: Comprehensive audit trail
3. **Analytics Dashboard**: Real-time performance monitoring
4. **Mobile Apps**: Native mobile app integration

## Conclusion

The real-time features implementation provides a comprehensive foundation for collaborative editing, user presence, and performance optimization. The modular architecture allows for easy extension and customization while maintaining high performance and reliability.

Key benefits:
- **Real-time Collaboration**: Multiple users can work simultaneously
- **Conflict Prevention**: Automatic lock management prevents conflicts
- **Performance Optimization**: Intelligent caching improves response times
- **Scalability**: Designed to handle large numbers of concurrent users
- **Reliability**: Robust error handling and automatic recovery

The implementation is production-ready and includes comprehensive testing, documentation, and monitoring capabilities. 