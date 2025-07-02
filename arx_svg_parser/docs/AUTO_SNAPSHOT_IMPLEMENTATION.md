# Auto-Snapshot Features Implementation

## Overview

The Auto-Snapshot system provides intelligent, automated snapshotting capabilities for the Arxos platform. It implements sophisticated change detection, intelligent scheduling, and automated cleanup to ensure data integrity while optimizing storage usage.

## Features Implemented

### ✅ Intelligent Snapshotting
- **Change Detection**: Advanced algorithms to detect meaningful changes in floor data
- **Priority-Based Scheduling**: Snapshots are prioritized based on change magnitude and type
- **Complexity Scoring**: Evaluates the complexity of changes to determine snapshot importance
- **Velocity Tracking**: Monitors change rate to optimize snapshot timing

### ✅ Auto-Snapshot After Major Changes
- **Major Edit Detection**: Automatically creates snapshots when significant changes occur
- **Threshold-Based Triggers**: Configurable thresholds for different types of changes
- **Real-Time Monitoring**: Continuous monitoring of floor modifications
- **Smart Filtering**: Distinguishes between minor edits and major changes

### ✅ Time-Based Auto-Snapshot
- **Configurable Intervals**: Time-based snapshots with customizable intervals
- **Activity-Aware Scheduling**: Only creates snapshots when there's actual activity
- **Rate Limiting**: Prevents excessive snapshots during high-activity periods
- **Background Processing**: Non-intrusive snapshot creation

### ✅ Change Threshold Detection
- **Multi-Metric Analysis**: Considers additions, modifications, and deletions
- **Object-Type Weighting**: Different weights for different object types
- **Relationship Tracking**: Monitors changes in object relationships
- **Historical Analysis**: Uses change history to improve detection accuracy

### ✅ Snapshot Cleanup Policies
- **Retention Policies**: Configurable retention periods for different snapshot types
- **Automatic Cleanup**: Background cleanup of old snapshots
- **Manual Cleanup**: User-triggered cleanup operations
- **Storage Optimization**: Compresses and archives old snapshots

## Architecture

### Core Components

#### 1. AutoSnapshotService
The main service orchestrating all auto-snapshot operations.

```python
class AutoSnapshotService:
    - Configuration management
    - Service lifecycle management
    - Event handling and callbacks
    - Integration with external systems
```

#### 2. IntelligentSnapshotScheduler
Determines when snapshots should be created based on various factors.

```python
class IntelligentSnapshotScheduler:
    - Rate limiting
    - Priority calculation
    - Trigger evaluation
    - Activity tracking
```

#### 3. ChangeDetector
Analyzes changes in floor data to determine snapshot necessity.

```python
class ChangeDetector:
    - Change comparison algorithms
    - Metrics calculation
    - Complexity scoring
    - Velocity tracking
```

#### 4. SnapshotCleanupManager
Manages cleanup operations and retention policies.

```python
class SnapshotCleanupManager:
    - Retention policy enforcement
    - Cleanup scheduling
    - Statistics tracking
    - Storage optimization
```

### Data Models

#### SnapshotConfig
Configuration for auto-snapshot behavior.

```python
@dataclass
class SnapshotConfig:
    enabled: bool = True
    time_interval_minutes: int = 15
    change_threshold: int = 10
    major_edit_threshold: int = 25
    max_snapshots_per_hour: int = 4
    max_snapshots_per_day: int = 24
    retention_days: int = 30
    cleanup_enabled: bool = True
    compression_enabled: bool = True
    backup_enabled: bool = True
```

#### ChangeMetrics
Metrics for tracking changes.

```python
@dataclass
class ChangeMetrics:
    object_count: int = 0
    edit_count: int = 0
    deletion_count: int = 0
    addition_count: int = 0
    modification_count: int = 0
    last_change_time: Optional[datetime] = None
    change_velocity: float = 0.0
    complexity_score: float = 0.0
```

#### SnapshotMetadata
Metadata for snapshots.

```python
@dataclass
class SnapshotMetadata:
    trigger: SnapshotTrigger
    priority: SnapshotPriority
    change_metrics: ChangeMetrics
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    description: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    system_events: List[str] = field(default_factory=list)
```

## API Endpoints

### Configuration Management

#### Get Configuration
```http
GET /api/v1/auto-snapshot/config
```

**Response:**
```json
{
    "enabled": true,
    "time_interval_minutes": 15,
    "change_threshold": 10,
    "major_edit_threshold": 25,
    "max_snapshots_per_hour": 4,
    "max_snapshots_per_day": 24,
    "retention_days": 30,
    "cleanup_enabled": true,
    "compression_enabled": true,
    "backup_enabled": true
}
```

#### Update Configuration
```http
PUT /api/v1/auto-snapshot/config
Content-Type: application/json

{
    "enabled": true,
    "time_interval_minutes": 30,
    "change_threshold": 15,
    "major_edit_threshold": 30,
    "max_snapshots_per_hour": 6,
    "max_snapshots_per_day": 36,
    "retention_days": 45,
    "cleanup_enabled": true,
    "compression_enabled": true,
    "backup_enabled": true
}
```

### Change Tracking

#### Track Changes
```http
POST /api/v1/auto-snapshot/track-changes
Content-Type: application/json

{
    "floor_id": "floor_001",
    "current_data": {
        "rooms": [{"object_id": "room_001", "name": "Test Room"}],
        "devices": [{"object_id": "device_001", "name": "Test Device"}]
    },
    "previous_data": {
        "rooms": [{"object_id": "room_001", "name": "Old Room"}]
    },
    "user_id": "user_001",
    "session_id": "session_001"
}
```

**Response:**
```json
{
    "id": "snapshot_001",
    "floor_id": "floor_001",
    "created_at": "2024-01-15T10:30:00Z",
    "description": "Auto-snapshot (change_threshold): 1 added, 1 modified - Change threshold met (2 changes)",
    "tags": ["change_threshold", "high", "auto-snapshot", "additions", "modifications"],
    "trigger": "change_threshold",
    "priority": "high",
    "is_auto_save": true,
    "change_metrics": {
        "object_count": 2,
        "edit_count": 2,
        "addition_count": 1,
        "modification_count": 1,
        "deletion_count": 0,
        "change_velocity": 2.5,
        "complexity_score": 3.0
    }
}
```

### Manual Snapshot Creation

#### Create Manual Snapshot
```http
POST /api/v1/auto-snapshot/create-manual
Content-Type: application/json

{
    "floor_id": "floor_001",
    "description": "Manual snapshot before major changes",
    "tags": ["manual", "pre-major-change"],
    "user_id": "user_001",
    "session_id": "session_001"
}
```

### Service Monitoring

#### Get Service Statistics
```http
GET /api/v1/auto-snapshot/stats
```

**Response:**
```json
{
    "active_floors": 5,
    "running": true,
    "config": {
        "enabled": true,
        "time_interval_minutes": 15,
        "change_threshold": 10
    },
    "cleanup_stats": {
        "total_cleanups": 12,
        "total_removed": 45,
        "last_cleanup": {
            "floor_id": "floor_001",
            "timestamp": "2024-01-15T09:00:00Z",
            "removed_count": 3,
            "kept_count": 15
        }
    },
    "scheduler_stats": {
        "floor_activity_count": 5,
        "snapshot_history_count": 5
    }
}
```

### Floor Management

#### Activate Floor
```http
POST /api/v1/auto-snapshot/floors/{floor_id}/activate
```

#### Deactivate Floor
```http
POST /api/v1/auto-snapshot/floors/{floor_id}/deactivate
```

#### Get Floor Snapshots
```http
GET /api/v1/auto-snapshot/floors/{floor_id}/snapshots?limit=50&offset=0
```

#### Get Floor Activity
```http
GET /api/v1/auto-snapshot/floors/{floor_id}/activity
```

### Cleanup Operations

#### Trigger Cleanup for Floor
```http
POST /api/v1/auto-snapshot/cleanup/{floor_id}
```

#### Trigger Cleanup for All Floors
```http
POST /api/v1/auto-snapshot/cleanup/all
```

### Health Check
```http
GET /api/v1/auto-snapshot/health
```

## Frontend Integration

### AutoSnapshotManager Class

The frontend provides a comprehensive JavaScript manager for auto-snapshot functionality.

```javascript
const autoSnapshotManager = new AutoSnapshotManager({
    apiBaseUrl: '/api/v1/auto-snapshot',
    updateInterval: 5000,
    enableNotifications: true,
    enableRealTimeUpdates: true
});

// Track changes
await autoSnapshotManager.trackChanges('floor_001', currentData, {
    previousData: previousData,
    userId: 'user_001',
    sessionId: 'session_001'
});

// Create manual snapshot
await autoSnapshotManager.createManualSnapshot('floor_001', {
    description: 'Manual snapshot',
    tags: ['manual', 'important']
});

// Update configuration
await autoSnapshotManager.updateConfiguration({
    time_interval_minutes: 30,
    change_threshold: 15
});
```

### UI Components

#### Configuration Panel
```javascript
autoSnapshotManager.renderConfigurationPanel(container);
```

#### Statistics Panel
```javascript
autoSnapshotManager.renderStatsPanel(container);
```

#### Floor Activity Panel
```javascript
autoSnapshotManager.renderFloorActivityPanel(container, 'floor_001');
```

## Configuration Options

### Time-Based Snapshots
- **time_interval_minutes**: Interval between time-based snapshots (1-1440 minutes)
- **max_snapshots_per_hour**: Maximum snapshots per hour (1-100)
- **max_snapshots_per_day**: Maximum snapshots per day (1-1000)

### Change Detection
- **change_threshold**: Minimum changes to trigger snapshot (1-1000)
- **major_edit_threshold**: Changes to trigger major edit snapshot (1-1000)
- **priority_thresholds**: Custom thresholds for different priority levels

### Retention and Cleanup
- **retention_days**: Days to keep snapshots (1-365)
- **cleanup_enabled**: Enable automatic cleanup
- **compression_enabled**: Enable snapshot compression
- **backup_enabled**: Enable snapshot backup

## Intelligent Features

### Change Detection Algorithm

1. **Object Comparison**: Compares current and previous floor data
2. **Change Classification**: Categorizes changes as additions, modifications, or deletions
3. **Complexity Scoring**: Calculates complexity based on object types and relationships
4. **Velocity Tracking**: Monitors change rate over time

### Priority Calculation

```python
def _calculate_priority(self, change_metrics: ChangeMetrics) -> SnapshotPriority:
    total_changes = (change_metrics.addition_count + 
                    change_metrics.modification_count + 
                    change_metrics.deletion_count)
    
    for priority, threshold in sorted(self.config.priority_thresholds.items(), 
                                    key=lambda x: x[1], reverse=True):
        if total_changes >= threshold:
            return priority
    
    return SnapshotPriority.LOW
```

### Rate Limiting

- **Hourly Limits**: Prevents excessive snapshots during high-activity periods
- **Daily Limits**: Ensures reasonable storage usage
- **Floor-Specific Tracking**: Tracks limits per floor independently

### Cleanup Policies

- **Retention Periods**: Different retention for auto-snapshots vs manual snapshots
- **Automatic Cleanup**: Background cleanup based on retention policies
- **Manual Cleanup**: User-triggered cleanup operations
- **Storage Optimization**: Compression and archiving of old snapshots

## Performance Considerations

### Optimization Strategies

1. **Lazy Loading**: Snapshots are created only when necessary
2. **Background Processing**: Non-blocking snapshot creation
3. **Efficient Storage**: Compression and deduplication
4. **Smart Caching**: Caches frequently accessed snapshot data

### Scalability Features

- **Floor Isolation**: Each floor operates independently
- **Configurable Limits**: Adjustable rate limits and thresholds
- **Resource Management**: Efficient memory and storage usage
- **Background Tasks**: Asynchronous processing for heavy operations

## Security Features

### Access Control
- **User Authentication**: Snapshots are associated with users
- **Session Tracking**: Tracks user sessions for audit purposes
- **Permission Checks**: Validates user permissions for operations

### Data Integrity
- **Checksum Validation**: Ensures snapshot data integrity
- **Version Control**: Maintains snapshot history and relationships
- **Audit Logging**: Comprehensive logging of all operations

## Monitoring and Analytics

### Metrics Tracked
- **Snapshot Creation Rate**: Number of snapshots created over time
- **Change Detection Accuracy**: Effectiveness of change detection
- **Storage Usage**: Disk space used by snapshots
- **Cleanup Efficiency**: Effectiveness of cleanup operations

### Health Monitoring
- **Service Status**: Real-time service health monitoring
- **Performance Metrics**: Response times and throughput
- **Error Tracking**: Comprehensive error logging and alerting

## Testing

### Test Coverage
- **Unit Tests**: Individual component testing
- **Integration Tests**: End-to-end workflow testing
- **Performance Tests**: Load and stress testing
- **Security Tests**: Access control and data integrity testing

### Test Scenarios
1. **Change Detection**: Various change scenarios and thresholds
2. **Rate Limiting**: High-activity scenarios
3. **Cleanup Operations**: Retention policy enforcement
4. **Error Handling**: Network failures and edge cases

## Deployment

### Requirements
- **Python 3.8+**: Required for async/await support
- **SQLite**: Database for snapshot storage
- **Redis**: Optional for caching (if enabled)
- **FastAPI**: Web framework for API endpoints

### Configuration
```bash
# Environment variables
AUTO_SNAPSHOT_ENABLED=true
AUTO_SNAPSHOT_TIME_INTERVAL=15
AUTO_SNAPSHOT_CHANGE_THRESHOLD=10
AUTO_SNAPSHOT_RETENTION_DAYS=30
```

### Startup
```python
# Initialize service
auto_snapshot_service = create_auto_snapshot_service()
await auto_snapshot_service.start()
```

## Future Enhancements

### Planned Features
1. **Machine Learning**: ML-based change prediction and optimization
2. **Distributed Snapshots**: Multi-node snapshot distribution
3. **Advanced Compression**: More efficient compression algorithms
4. **Real-Time Analytics**: Live analytics dashboard
5. **Integration APIs**: Third-party system integrations

### Performance Improvements
1. **Parallel Processing**: Concurrent snapshot creation
2. **Incremental Snapshots**: Delta-based snapshot storage
3. **Predictive Cleanup**: ML-based cleanup optimization
4. **Smart Scheduling**: AI-powered snapshot scheduling

## Troubleshooting

### Common Issues

#### High Storage Usage
- **Check retention policies**: Reduce retention periods
- **Enable compression**: Reduce snapshot sizes
- **Review change thresholds**: Increase thresholds to reduce snapshots

#### Performance Issues
- **Adjust rate limits**: Reduce snapshot frequency
- **Optimize change detection**: Fine-tune detection algorithms
- **Enable caching**: Improve response times

#### Missing Snapshots
- **Check configuration**: Verify auto-snapshot is enabled
- **Review thresholds**: Ensure thresholds are appropriate
- **Monitor logs**: Check for errors in snapshot creation

### Debugging

#### Enable Debug Logging
```python
import logging
logging.getLogger('auto_snapshot').setLevel(logging.DEBUG)
```

#### Monitor Service Stats
```http
GET /api/v1/auto-snapshot/stats
```

#### Check Floor Activity
```http
GET /api/v1/auto-snapshot/floors/{floor_id}/activity
```

## Conclusion

The Auto-Snapshot system provides a robust, intelligent, and scalable solution for automated data protection in the Arxos platform. With its sophisticated change detection, flexible configuration, and comprehensive monitoring, it ensures data integrity while optimizing storage usage and system performance.

The implementation is production-ready, well-tested, and includes comprehensive documentation for easy integration and maintenance. 