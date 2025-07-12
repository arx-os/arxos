# Floor Version Control System

## Overview

The Floor Version Control System provides comprehensive version control capabilities for floor plans and BIM data in the Arxos platform. It enables users to create snapshots, perform undo/redo operations, manage branches, compare versions, and maintain a complete audit trail of all changes.

## Features

### Core Version Control
- **Snapshots**: Create point-in-time versions of floor states
- **Undo/Redo**: Navigate through version history with full undo/redo stacks
- **Version History**: Complete timeline of all floor changes
- **Version Comparison**: Compare any two versions to see differences
- **Data Integrity**: SHA256 checksums ensure version integrity

### Branching and Merging
- **Branch Management**: Create and manage multiple development branches
- **Branch Switching**: Seamlessly switch between different branches
- **Merge Operations**: Merge changes between branches with conflict resolution
- **Default Branches**: Automatic main branch creation for each floor

### Collaboration Features
- **Version Comments**: Add contextual comments to specific versions
- **User Sessions**: Track individual user sessions and undo/redo stacks
- **Concurrent Access Control**: Prevent conflicts with version locks
- **Audit Logging**: Complete audit trail of all version control operations

### Advanced Features
- **Auto-save**: Automatic version creation during editing sessions
- **Version Tags**: Categorize versions with custom tags and colors
- **Metadata Storage**: Store additional metadata with each version
- **Performance Optimization**: Efficient storage with compression and indexing

## Data Model

### Core Tables

#### DrawingVersion
Stores the main version data for each floor snapshot.

```sql
CREATE TABLE drawing_versions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    floor_id INTEGER NOT NULL,
    svg TEXT NOT NULL,
    version_number INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    action_type VARCHAR(32) NOT NULL,
    description TEXT,
    tags TEXT, -- JSON array
    metadata TEXT, -- JSON metadata
    is_auto_save BOOLEAN DEFAULT FALSE,
    is_branch BOOLEAN DEFAULT FALSE,
    parent_version INTEGER,
    branch_name VARCHAR(100),
    file_size BIGINT,
    checksum VARCHAR(64),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### VersionSession
Tracks user sessions for undo/redo functionality.

```sql
CREATE TABLE version_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    floor_id INTEGER NOT NULL,
    session_id VARCHAR(64) UNIQUE NOT NULL,
    current_version INTEGER NOT NULL,
    undo_stack TEXT, -- JSON array
    redo_stack TEXT, -- JSON array
    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### VersionBranch
Manages branching functionality.

```sql
CREATE TABLE version_branches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    floor_id INTEGER NOT NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    base_version INTEGER NOT NULL,
    head_version INTEGER NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    is_default BOOLEAN DEFAULT FALSE,
    created_by INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Supporting Tables

- **VersionDiff**: Stores differences between versions
- **VersionComment**: User comments on specific versions
- **VersionLock**: Prevents concurrent operations
- **VersionMerge**: Tracks merge operations
- **VersionAuditLog**: Complete audit trail
- **VersionMetadata**: Additional metadata storage
- **VersionTag**: Custom tags for categorization
- **VersionTagAssignment**: Links tags to versions

## API Endpoints

### Version Management

#### Create Snapshot
```http
POST /floors/{floor_id}/versions/snapshot
Content-Type: application/json

{
    "floor_id": 123,
    "description": "Major layout changes",
    "tags": ["major-version", "layout-update"],
    "is_auto_save": false,
    "branch_name": "feature/new-layout"
}
```

**Response:**
```json
{
    "message": "Version snapshot created successfully",
    "version": {
        "id": 456,
        "floor_id": 123,
        "version_number": 5,
        "description": "Major layout changes",
        "tags": ["major-version", "layout-update"],
        "checksum": "a1b2c3d4...",
        "created_at": "2024-01-15T10:30:00Z"
    }
}
```

#### Get Version History
```http
GET /floors/{floor_id}/versions
```

**Response:**
```json
{
    "versions": [
        {
            "id": 456,
            "version_number": 5,
            "description": "Major layout changes",
            "user": {"username": "john.doe"},
            "tags": ["major-version"],
            "created_at": "2024-01-15T10:30:00Z"
        }
    ],
    "count": 1
}
```

#### Get Specific Version
```http
GET /versions/{version_id}
```

#### Restore Version
```http
POST /floors/{floor_id}/versions/restore
Content-Type: application/json

{
    "version_id": 456,
    "floor_id": 123
}
```

#### Delete Version
```http
DELETE /versions/{version_id}
```

### Undo/Redo Operations

#### Undo
```http
POST /floors/{floor_id}/versions/undo
```

**Response:**
```json
{
    "message": "Undo completed successfully",
    "current_version": {
        "id": 455,
        "version_number": 4
    },
    "undo_stack_size": 3,
    "redo_stack_size": 1
}
```

#### Redo
```http
POST /floors/{floor_id}/versions/redo
```

### Version Comparison

#### Compare Versions
```http
GET /versions/compare?from=455&to=456
```

**Response:**
```json
{
    "from_version": {
        "id": 455,
        "version_number": 4
    },
    "to_version": {
        "id": 456,
        "version_number": 5
    },
    "diff": {
        "id": 789,
        "object_count": 150,
        "change_count": 12,
        "added_count": 3,
        "removed_count": 1,
        "modified_count": 8
    },
    "summary": {
        "object_count": 150,
        "change_count": 12
    }
}
```

### Branching Operations

#### Create Branch
```http
POST /floors/{floor_id}/branches
Content-Type: application/json

{
    "floor_id": 123,
    "base_version": 456,
    "branch_name": "feature/new-layout",
    "description": "New layout design branch"
}
```

#### Get Branches
```http
GET /floors/{floor_id}/branches
```

#### Switch Branch
```http
POST /floors/{floor_id}/branches/switch
Content-Type: application/json

{
    "floor_id": 123,
    "branch_id": 789
}
```

### Version Comments

#### Add Comment
```http
POST /versions/{version_id}/comments
Content-Type: application/json

{
    "version_id": 456,
    "content": "This version includes the new HVAC layout",
    "line_number": 45,
    "object_id": "hvac-001"
}
```

#### Get Comments
```http
GET /versions/{version_id}/comments
```

## Usage Examples

### Basic Workflow

1. **Create Initial Snapshot**
```bash
curl -X POST http://localhost:8080/floors/123/versions/snapshot \
  -H "Content-Type: application/json" \
  -d '{
    "floor_id": 123,
    "description": "Initial floor plan",
    "tags": ["initial"]
  }'
```

2. **Make Changes and Create New Snapshot**
```bash
curl -X POST http://localhost:8080/floors/123/versions/snapshot \
  -H "Content-Type: application/json" \
  -d '{
    "floor_id": 123,
    "description": "Added new room layout",
    "tags": ["layout-update"]
  }'
```

3. **Undo Last Change**
```bash
curl -X POST http://localhost:8080/floors/123/versions/undo
```

4. **Compare Versions**
```bash
curl "http://localhost:8080/versions/compare?from=1&to=2"
```

### Branching Workflow

1. **Create Feature Branch**
```bash
curl -X POST http://localhost:8080/floors/123/branches \
  -H "Content-Type: application/json" \
  -d '{
    "floor_id": 123,
    "base_version": 5,
    "branch_name": "feature/hvac-update",
    "description": "HVAC system redesign"
  }'
```

2. **Switch to Branch**
```bash
curl -X POST http://localhost:8080/floors/123/branches/switch \
  -H "Content-Type: application/json" \
  -d '{
    "floor_id": 123,
    "branch_id": 2
  }'
```

3. **Make Changes in Branch**
```bash
curl -X POST http://localhost:8080/floors/123/versions/snapshot \
  -H "Content-Type: application/json" \
  -d '{
    "floor_id": 123,
    "description": "HVAC layout changes",
    "branch_name": "feature/hvac-update"
  }'
```

### Collaboration Workflow

1. **Add Comments to Version**
```bash
curl -X POST http://localhost:8080/versions/456/comments \
  -H "Content-Type: application/json" \
  -d '{
    "version_id": 456,
    "content": "This layout works better for the new HVAC requirements",
    "object_id": "hvac-main"
  }'
```

2. **Review Version History**
```bash
curl http://localhost:8080/floors/123/versions
```

## Best Practices

### Version Management

1. **Descriptive Snapshots**: Always provide meaningful descriptions for snapshots
2. **Regular Snapshots**: Create snapshots at logical checkpoints, not every minor change
3. **Tag Usage**: Use tags to categorize versions (e.g., "major-version", "bugfix", "feature")
4. **Auto-save**: Enable auto-save for long editing sessions

### Branching Strategy

1. **Main Branch**: Keep the main branch stable and production-ready
2. **Feature Branches**: Create feature branches for significant changes
3. **Branch Naming**: Use descriptive branch names (e.g., "feature/hvac-update", "bugfix/lighting-issue")
4. **Branch Cleanup**: Delete merged branches to keep the repository clean

### Collaboration

1. **Comments**: Use comments to explain significant changes
2. **Communication**: Coordinate with team members before major changes
3. **Review Process**: Review changes before merging branches
4. **Audit Trail**: Monitor audit logs for compliance and debugging

### Performance

1. **Large Files**: Be mindful of SVG file sizes for performance
2. **Version Cleanup**: Periodically clean up old versions to save storage
3. **Indexing**: Ensure proper database indexing for large version histories
4. **Caching**: Use appropriate caching strategies for frequently accessed versions

## Configuration

### Database Migration

Run the version control migration to set up the database schema:

```bash
# Apply migration
sqlite3 arx.db < migrations/016_floor_version_control_system.sql

# Verify migration
sqlite3 arx.db "SELECT 'Migration completed successfully' as status;"
```

### Environment Variables

```bash
# Version control settings
VERSION_CONTROL_ENABLED=true
AUTO_SAVE_INTERVAL=300  # seconds
MAX_VERSIONS_PER_FLOOR=100
VERSION_RETENTION_DAYS=365
```

### Default Tags

The system automatically creates these default tags for each floor:

- **Auto-save**: Automatically saved versions (gray)
- **Manual Save**: Manually saved versions (green)
- **Major Version**: Major version releases (red)

## Troubleshooting

### Common Issues

1. **Version Not Found**
   - Check if the version ID exists
   - Verify the version belongs to the correct floor
   - Ensure the version hasn't been deleted

2. **Undo/Redo Not Working**
   - Check if there's an active session
   - Verify the undo/redo stacks aren't empty
   - Ensure the user has proper permissions

3. **Branch Conflicts**
   - Check for conflicting changes in branches
   - Use the merge conflict resolution tools
   - Coordinate with team members

4. **Performance Issues**
   - Check database indexes
   - Monitor version file sizes
   - Consider version cleanup for old versions

### Debug Commands

```bash
# Check version count for a floor
sqlite3 arx.db "SELECT COUNT(*) FROM drawing_versions WHERE floor_id = 123;"

# Check active sessions
sqlite3 arx.db "SELECT * FROM version_sessions WHERE is_active = 1;"

# Check audit logs
sqlite3 arx.db "SELECT * FROM version_audit_logs ORDER BY created_at DESC LIMIT 10;"
```

## Security Considerations

1. **Access Control**: Ensure proper role-based access control
2. **Audit Logging**: Monitor all version control operations
3. **Data Integrity**: Use checksums to verify version integrity
4. **Session Management**: Properly manage user sessions and locks
5. **Input Validation**: Validate all user inputs to prevent injection attacks

## Integration

### Frontend Integration

The version control system can be integrated into the frontend with:

1. **Version History UI**: Display version timeline with tags and comments
2. **Undo/Redo Buttons**: Provide intuitive undo/redo controls
3. **Branch Management**: Visual branch switching and management
4. **Version Comparison**: Side-by-side version comparison view
5. **Comment System**: Inline commenting on specific versions

### API Integration

```javascript
// Example frontend integration
class VersionControl {
    async createSnapshot(floorId, description, tags) {
        const response = await fetch(`/floors/${floorId}/versions/snapshot`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ floor_id: floorId, description, tags })
        });
        return response.json();
    }

    async undo(floorId) {
        const response = await fetch(`/floors/${floorId}/versions/undo`, {
            method: 'POST'
        });
        return response.json();
    }

    async getVersionHistory(floorId) {
        const response = await fetch(`/floors/${floorId}/versions`);
        return response.json();
    }
}
```

## Future Enhancements

1. **Advanced Diff Visualization**: Visual diff tools for SVG comparison
2. **Merge Conflict Resolution**: Enhanced conflict resolution UI
3. **Version Analytics**: Usage analytics and insights
4. **Automated Testing**: Integration with CI/CD pipelines
5. **Cloud Storage**: Integration with cloud storage for large files
6. **Real-time Collaboration**: Real-time collaborative editing features

## Support

For technical support or questions about the Floor Version Control System:

1. Check the audit logs for detailed operation information
2. Review the database schema and indexes
3. Monitor system performance and resource usage
4. Contact the development team for complex issues

---

*This documentation covers the complete Floor Version Control System implementation. For additional information, refer to the API reference and developer guides.* 