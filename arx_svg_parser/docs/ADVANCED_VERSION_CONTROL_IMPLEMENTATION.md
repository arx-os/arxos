# Advanced Version Control Implementation

## Overview

The Advanced Version Control system provides comprehensive version management for floor data including branching, merging, conflict resolution, annotations, and comments. This implementation supports collaborative development workflows with robust conflict detection and resolution capabilities.

## Architecture

### Core Components

1. **VersionControlService** - Main service handling all version control operations
2. **Database Schema** - SQLite-based storage for versions, branches, merges, conflicts, annotations, and comments
3. **File Storage** - JSON-based version data storage with hash verification
4. **FastAPI Router** - RESTful API endpoints for all operations
5. **Frontend Manager** - JavaScript module for UI integration
6. **Conflict Resolution** - Automated and manual conflict detection and resolution

### Data Models

#### Version
```python
@dataclass
class Version:
    version_id: str
    floor_id: str
    building_id: str
    branch_name: str
    parent_version_id: Optional[str]
    version_type: VersionType
    version_number: str
    commit_message: str
    author: str
    created_at: datetime
    data_hash: str
    data_size: int
    metadata: Dict[str, Any]
```

#### Branch
```python
@dataclass
class Branch:
    branch_name: str
    floor_id: str
    building_id: str
    base_version_id: str
    current_version_id: str
    status: BranchStatus
    created_by: str
    created_at: datetime
    last_updated: datetime
    description: str
    metadata: Dict[str, Any]
```

#### MergeRequest
```python
@dataclass
class MergeRequest:
    merge_id: str
    source_branch: str
    target_branch: str
    floor_id: str
    building_id: str
    status: MergeStatus
    created_by: str
    created_at: datetime
    merged_at: Optional[datetime]
    merged_by: Optional[str]
    conflicts: List[Dict[str, Any]]
    resolution_strategy: str
    description: str
    metadata: Dict[str, Any]
```

## Features

### 1. Branching and Merging

#### Parallel Version Branches
- Create feature branches from any existing version
- Independent development workflows
- Branch-specific version numbering
- Branch status tracking (active, merged, deleted, conflict)

#### Branch Merge Functionality
- Automated conflict detection
- Multiple resolution strategies (source, target, manual)
- Merge request workflow
- Conflict resolution tracking

#### Conflict Resolution Tools
- Object-level conflict detection
- Property-level conflict identification
- Visual conflict comparison
- Resolution strategy selection

#### Branch Visualization
- Timeline-based branch display
- Version node visualization
- Branch relationship mapping
- Interactive branch switching

### 2. Annotations and Comments

#### Version Annotation System
- Object-specific annotations
- Position-based annotations
- Multiple annotation types (note, issue, improvement, bug)
- Rich text content support

#### Comment Threads
- Version-level comments
- Annotation-level comments
- Threaded discussion support
- Author tracking and timestamps

#### Annotation Export/Import
- JSON-based export format
- Complete annotation history
- Metadata preservation
- Cross-project import support

#### Annotation Search
- Full-text search across annotations
- Title and content search
- Author-based filtering
- Date range filtering

## API Endpoints

### Version Management

#### Create Version
```http
POST /v1/version-control/version
Content-Type: application/json

{
    "floor_data": {...},
    "floor_id": "floor-1",
    "building_id": "building-1",
    "branch_name": "main",
    "commit_message": "Initial commit",
    "author": "user@example.com",
    "parent_version_id": "optional-parent-id",
    "version_type": "minor"
}
```

#### Get Version History
```http
GET /v1/version-control/versions/{building_id}/{floor_id}?branch_name={branch_name}
```

#### Get Version Data
```http
GET /v1/version-control/version/{version_id}
```

### Branch Management

#### Create Branch
```http
POST /v1/version-control/branch
Content-Type: application/json

{
    "branch_name": "feature-branch",
    "floor_id": "floor-1",
    "building_id": "building-1",
    "base_version_id": "version-id",
    "created_by": "user@example.com",
    "description": "Feature branch description"
}
```

#### Get Branches
```http
GET /v1/version-control/branches/{building_id}/{floor_id}
```

### Merge Management

#### Create Merge Request
```http
POST /v1/version-control/merge-request
Content-Type: application/json

{
    "source_branch": "feature-branch",
    "target_branch": "main",
    "floor_id": "floor-1",
    "building_id": "building-1",
    "created_by": "user@example.com",
    "description": "Merge description"
}
```

#### Resolve Conflict
```http
POST /v1/version-control/merge/{merge_id}/resolve-conflict
Content-Type: application/json

{
    "conflict_id": "conflict-id",
    "resolution": "source|target|manual",
    "resolved_by": "user@example.com"
}
```

#### Execute Merge
```http
POST /v1/version-control/merge/{merge_id}/execute
Content-Type: application/json

{
    "executed_by": "user@example.com"
}
```

### Annotations

#### Add Annotation
```http
POST /v1/version-control/annotation
Content-Type: application/json

{
    "version_id": "version-id",
    "floor_id": "floor-1",
    "building_id": "building-1",
    "title": "Annotation title",
    "content": "Annotation content",
    "author": "user@example.com",
    "object_id": "optional-object-id",
    "position_x": 100.0,
    "position_y": 200.0,
    "annotation_type": "note"
}
```

#### Get Annotations
```http
GET /v1/version-control/annotations/{version_id}
```

#### Search Annotations
```http
GET /v1/version-control/annotations/search/{building_id}/{floor_id}?query={search_query}
```

### Comments

#### Add Comment
```http
POST /v1/version-control/comment
Content-Type: application/json

{
    "parent_id": "version-or-annotation-id",
    "parent_type": "version|annotation",
    "content": "Comment content",
    "author": "user@example.com"
}
```

#### Get Comments
```http
GET /v1/version-control/comments/{parent_id}?parent_type={version|annotation}
```

### Visualization and Export

#### Get Branch Graph
```http
GET /v1/version-control/branch-graph/{building_id}/{floor_id}
```

#### Export Version Data
```http
GET /v1/version-control/export/{building_id}/{floor_id}?include_annotations=true&include_comments=true
```

## Frontend Integration

### Version Control Manager

The frontend provides a comprehensive JavaScript module for managing all version control operations:

```javascript
// Initialize manager
const vcManager = new VersionControlManager();

// Create version
const result = await vcManager.createVersion(
    floorData, floorId, buildingId, branchName, 
    commitMessage, author, options
);

// Create branch
const branchResult = await vcManager.createBranch(
    branchName, floorId, buildingId, baseVersionId, 
    createdBy, description
);

// Create merge request
const mergeResult = await vcManager.createMergeRequest(
    sourceBranch, targetBranch, floorId, buildingId, 
    createdBy, description
);

// Add annotation
const annotationResult = await vcManager.addAnnotation(
    versionId, floorId, buildingId, title, content, 
    author, options
);
```

### UI Components

#### Branch Management
- Branch creation and deletion
- Branch switching and comparison
- Branch status visualization
- Branch timeline display

#### Version History
- Chronological version display
- Version comparison tools
- Commit message and author tracking
- Version type indicators

#### Merge Requests
- Merge request creation
- Conflict visualization
- Resolution strategy selection
- Merge execution workflow

#### Annotations and Comments
- Annotation creation and editing
- Comment threading
- Search and filtering
- Export functionality

## Database Schema

### Versions Table
```sql
CREATE TABLE versions (
    version_id TEXT PRIMARY KEY,
    floor_id TEXT NOT NULL,
    building_id TEXT NOT NULL,
    branch_name TEXT NOT NULL,
    parent_version_id TEXT,
    version_type TEXT NOT NULL,
    version_number TEXT,
    commit_message TEXT,
    author TEXT,
    created_at TEXT NOT NULL,
    data_hash TEXT,
    data_size INTEGER,
    metadata TEXT
);
```

### Branches Table
```sql
CREATE TABLE branches (
    branch_name TEXT,
    floor_id TEXT NOT NULL,
    building_id TEXT NOT NULL,
    base_version_id TEXT NOT NULL,
    current_version_id TEXT NOT NULL,
    status TEXT NOT NULL,
    created_by TEXT,
    created_at TEXT NOT NULL,
    last_updated TEXT NOT NULL,
    description TEXT,
    metadata TEXT,
    PRIMARY KEY (branch_name, floor_id, building_id)
);
```

### Merge Requests Table
```sql
CREATE TABLE merge_requests (
    merge_id TEXT PRIMARY KEY,
    source_branch TEXT NOT NULL,
    target_branch TEXT NOT NULL,
    floor_id TEXT NOT NULL,
    building_id TEXT NOT NULL,
    status TEXT NOT NULL,
    created_by TEXT,
    created_at TEXT NOT NULL,
    merged_at TEXT,
    merged_by TEXT,
    conflicts TEXT,
    resolution_strategy TEXT,
    description TEXT,
    metadata TEXT
);
```

### Conflicts Table
```sql
CREATE TABLE conflicts (
    conflict_id TEXT PRIMARY KEY,
    merge_id TEXT NOT NULL,
    conflict_type TEXT NOT NULL,
    object_id TEXT,
    property_name TEXT,
    source_value TEXT,
    target_value TEXT,
    resolution TEXT,
    resolved_by TEXT,
    resolved_at TEXT,
    created_at TEXT NOT NULL
);
```

### Annotations Table
```sql
CREATE TABLE annotations (
    annotation_id TEXT PRIMARY KEY,
    version_id TEXT NOT NULL,
    floor_id TEXT NOT NULL,
    building_id TEXT NOT NULL,
    object_id TEXT,
    position_x REAL,
    position_y REAL,
    annotation_type TEXT NOT NULL,
    title TEXT,
    content TEXT,
    author TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    metadata TEXT
);
```

### Comments Table
```sql
CREATE TABLE comments (
    comment_id TEXT PRIMARY KEY,
    parent_id TEXT NOT NULL,
    parent_type TEXT NOT NULL,
    author TEXT,
    content TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    metadata TEXT
);
```

## Usage Examples

### Basic Workflow

1. **Create Initial Version**
```python
result = vc_service.create_version(
    floor_data, "floor-1", "building-1", "main",
    "Initial floor layout", "user@example.com"
)
```

2. **Create Feature Branch**
```python
result = vc_service.create_branch(
    "feature-room-101", "floor-1", "building-1",
    base_version_id, "user@example.com",
    "Add room 101 modifications"
)
```

3. **Make Changes and Commit**
```python
result = vc_service.create_version(
    modified_floor_data, "floor-1", "building-1",
    "feature-room-101", "Add room 101", "user@example.com"
)
```

4. **Create Merge Request**
```python
result = vc_service.create_merge_request(
    "feature-room-101", "main", "floor-1", "building-1",
    "user@example.com", "Merge room 101 changes"
)
```

5. **Resolve Conflicts (if any)**
```python
result = vc_service.resolve_conflict(
    conflict_id, "source", "user@example.com"
)
```

6. **Execute Merge**
```python
result = vc_service.execute_merge(merge_id, "user@example.com")
```

### Annotation Workflow

1. **Add Annotation to Version**
```python
result = vc_service.add_annotation(
    version_id, "floor-1", "building-1",
    "Room 101 Issue", "Window placement needs adjustment",
    "user@example.com", object_id="window-1",
    position_x=150.0, position_y=200.0
)
```

2. **Add Comment to Annotation**
```python
result = vc_service.add_comment(
    annotation_id, "annotation",
    "I'll fix this in the next version",
    "user@example.com"
)
```

3. **Search Annotations**
```python
result = vc_service.search_annotations(
    "floor-1", "building-1", "window"
)
```

## Testing

### Test Coverage

The implementation includes comprehensive tests covering:

- Database initialization and schema
- Version creation and retrieval
- Branch management operations
- Merge request workflow
- Conflict detection and resolution
- Annotation and comment functionality
- Search and export features
- Error handling and edge cases
- Concurrent access scenarios
- Data integrity verification

### Running Tests

```bash
# Run all version control tests
pytest tests/test_version_control.py -v

# Run specific test categories
pytest tests/test_version_control.py::TestVersionControlService::test_create_version -v
pytest tests/test_version_control.py::TestVersionControlService::test_merge_workflow -v
```

## Performance Considerations

### Optimization Strategies

1. **Lazy Loading** - Version data loaded only when needed
2. **Hash Verification** - Quick integrity checks using SHA256 hashes
3. **Indexed Queries** - Database indexes for common query patterns
4. **Batch Operations** - Efficient bulk operations for large datasets
5. **Caching** - Version metadata caching for frequently accessed data

### Scalability Features

1. **Partitioned Storage** - Floor-based data partitioning
2. **Compression** - JSON data compression for large versions
3. **Cleanup Tasks** - Automated cleanup of orphaned data
4. **Connection Pooling** - Database connection management
5. **Async Operations** - Non-blocking operations for better performance

## Security Features

### Access Control

1. **User Authentication** - JWT-based authentication
2. **Authorization** - Role-based access control
3. **Audit Logging** - Complete operation logging
4. **Data Validation** - Input validation and sanitization
5. **SQL Injection Prevention** - Parameterized queries

### Data Protection

1. **Hash Verification** - Data integrity checks
2. **Encrypted Storage** - Sensitive data encryption
3. **Backup and Recovery** - Automated backup procedures
4. **Version Isolation** - Secure version separation
5. **Conflict Resolution** - Safe merge operations

## Deployment

### Requirements

```txt
fastapi>=0.68.0
sqlite3
pathlib
dataclasses
uuid
hashlib
json
datetime
logging
```

### Configuration

```python
# Version control configuration
VERSION_CONTROL_CONFIG = {
    "db_path": "./data/version_control.db",
    "storage_path": "./data/versions",
    "max_versions_per_branch": 1000,
    "max_branches_per_floor": 50,
    "compression_enabled": True,
    "cleanup_interval_hours": 24
}
```

### Integration

```python
# Add to main app.py
from routers.version_control import router as version_control_router

app.include_router(version_control_router, prefix="/v1")
```

## Future Enhancements

### Planned Features

1. **Git-like Operations** - Clone, push, pull functionality
2. **Advanced Merging** - Three-way merge algorithms
3. **Version Tagging** - Named version tags and releases
4. **Branch Protection** - Protected branch rules
5. **Webhook Integration** - External system notifications
6. **Advanced Analytics** - Version usage analytics
7. **Multi-language Support** - Internationalization
8. **Mobile Support** - Mobile-optimized interface

### Performance Improvements

1. **Distributed Storage** - Cloud storage integration
2. **Real-time Collaboration** - WebSocket-based real-time updates
3. **Advanced Caching** - Redis-based caching layer
4. **Background Processing** - Async task processing
5. **CDN Integration** - Content delivery optimization

## Conclusion

The Advanced Version Control system provides a robust foundation for collaborative floor data management. With comprehensive branching, merging, annotation, and comment capabilities, it supports complex development workflows while maintaining data integrity and performance.

The implementation is production-ready, well-tested, and includes comprehensive documentation for easy integration and maintenance. 