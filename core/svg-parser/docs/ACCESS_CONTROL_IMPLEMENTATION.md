# Access Control Implementation

## Overview

The Access Control system provides comprehensive role-based permissions, floor-specific access controls, audit trails, and permission inheritance for the Arxos platform. This implementation ensures secure and granular access control across all building management operations.

## Architecture

### Core Components

1. **AccessControlService** - Main service class handling all access control operations
2. **Role-Based Permissions** - Hierarchical role system with inheritance
3. **Floor-Specific Access Controls** - Granular permissions for individual floors
4. **Audit Trail System** - Comprehensive logging of all access control events
5. **Permission Inheritance** - Automatic permission propagation through role hierarchy

### Database Schema

```sql
-- Users table
CREATE TABLE users (
    user_id TEXT PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    primary_role TEXT NOT NULL,
    secondary_roles TEXT,
    organization TEXT,
    created_at TEXT NOT NULL,
    last_login TEXT,
    is_active INTEGER DEFAULT 1,
    metadata TEXT
);

-- Permissions table
CREATE TABLE permissions (
    permission_id TEXT PRIMARY KEY,
    role TEXT NOT NULL,
    resource_type TEXT NOT NULL,
    resource_id TEXT,
    permission_level INTEGER NOT NULL,
    floor_id TEXT,
    building_id TEXT,
    created_at TEXT NOT NULL,
    expires_at TEXT,
    metadata TEXT
);

-- Audit logs table
CREATE TABLE audit_logs (
    log_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    action TEXT NOT NULL,
    resource_type TEXT NOT NULL,
    resource_id TEXT NOT NULL,
    floor_id TEXT,
    building_id TEXT,
    details TEXT,
    ip_address TEXT,
    user_agent TEXT,
    timestamp TEXT NOT NULL,
    success INTEGER DEFAULT 1,
    error_message TEXT
);

-- Role hierarchy table
CREATE TABLE role_hierarchy (
    role TEXT PRIMARY KEY,
    inherits_from TEXT,
    permissions TEXT,
    metadata TEXT
);
```

## Role Hierarchy

Based on the ARXOS flowchart, the following role hierarchy is implemented:

```
OWNER (Level 4)
├── ADMIN (Level 3)
    ├── MANAGEMENT (Level 2)
        ├── ARCHITECT (Level 2)
            ├── ENGINEER (Level 2)
                ├── CONTRACTOR (Level 2)
                    ├── INSPECTOR (Level 2)
                        ├── TENANT (Level 1)
                            └── TEAM (Level 1)
```

### Role Permissions Matrix

| Role | Floor | Building | Version | Branch | Annotation | Comment | Asset | CMMS | Export | Import |
|------|-------|----------|---------|--------|------------|---------|-------|------|--------|--------|
| OWNER | Owner | Owner | Owner | Owner | Owner | Owner | Owner | Owner | Owner | Owner |
| ADMIN | Admin | Admin | Admin | Admin | Admin | Admin | Admin | Admin | Admin | Admin |
| MANAGEMENT | Write | Write | Write | Write | Write | Write | Write | Write | Write | Read |
| ARCHITECT | Write | Write | Write | Write | Write | Write | Read | Read | Write | Read |
| ENGINEER | Write | Read | Write | Write | Write | Write | Read | Read | Read | None |
| CONTRACTOR | Write | Read | Read | Read | Write | Write | Read | Read | Read | None |
| INSPECTOR | Read | Read | Read | Read | Write | Write | Read | Read | Read | None |
| TENANT | Read | Read | Read | Read | Read | Write | Read | Read | Read | None |
| TEAM | Read | Read | Read | Read | Read | Read | Read | Read | Read | None |

## Features

### 1. Role-Based Permissions

- **Hierarchical Roles**: Roles inherit permissions from parent roles
- **Primary & Secondary Roles**: Users can have multiple roles
- **Permission Levels**: READ (1), WRITE (2), ADMIN (3), OWNER (4)
- **Resource-Specific Permissions**: Granular control over different resource types

### 2. Floor-Specific Access Controls

- **Floor-Level Permissions**: Specific permissions for individual floors
- **Building Context**: Permissions scoped to building-floor combinations
- **Bulk Permission Management**: Grant multiple permissions at once
- **Access Summaries**: Comprehensive overview of floor access

### 3. Audit Trail System

- **Comprehensive Logging**: All access control events are logged
- **Detailed Context**: IP addresses, user agents, timestamps
- **Success/Failure Tracking**: Distinguish between successful and failed actions
- **Export Capabilities**: Export audit logs for compliance

### 4. Permission Inheritance

- **Automatic Propagation**: Permissions automatically inherited from parent roles
- **Override Capabilities**: Child roles can have specific permissions that override inheritance
- **Flexible Hierarchy**: Easy to modify role relationships

## API Endpoints

### User Management

#### Create User
```http
POST /access-control/users
Content-Type: application/json

{
    "username": "john_doe",
    "email": "john@example.com",
    "primary_role": "contractor",
    "secondary_roles": ["inspector"],
    "organization": "ABC Construction"
}
```

#### Get User
```http
GET /access-control/users/{user_id}
```

#### List Users
```http
GET /access-control/users?role=contractor&organization=ABC&active_only=true
```

### Permission Management

#### Grant Permission
```http
POST /access-control/permissions
Content-Type: application/json

{
    "role": "contractor",
    "resource_type": "floor",
    "resource_id": "floor_001",
    "permission_level": 2,
    "floor_id": "floor_001",
    "building_id": "building_001",
    "expires_at": "2024-12-31T23:59:59"
}
```

#### Check Permission
```http
POST /access-control/permissions/check
Content-Type: application/json

{
    "user_id": "user_123",
    "resource_type": "floor",
    "action": "update",
    "resource_id": "floor_001",
    "floor_id": "floor_001",
    "building_id": "building_001"
}
```

#### Revoke Permission
```http
DELETE /access-control/permissions/{permission_id}
```

#### Get Floor Permissions
```http
GET /access-control/permissions/floor/{building_id}/{floor_id}
```

### Audit Logs

#### Log Audit Event
```http
POST /access-control/audit-logs
Content-Type: application/json

{
    "user_id": "user_123",
    "action": "create",
    "resource_type": "floor",
    "resource_id": "floor_001",
    "floor_id": "floor_001",
    "building_id": "building_001",
    "details": {"operation": "floor_creation"},
    "ip_address": "192.168.1.100",
    "user_agent": "Mozilla/5.0...",
    "success": true
}
```

#### Get Audit Logs
```http
GET /access-control/audit-logs?user_id=user_123&resource_type=floor&start_date=2024-01-01&limit=100
```

#### Export Audit Logs
```http
GET /access-control/audit-logs/export?start_date=2024-01-01&end_date=2024-12-31
```

### Floor Access Control

#### Get Floor Access Summary
```http
GET /access-control/floors/{building_id}/{floor_id}/access-summary
```

#### Grant Bulk Permissions
```http
POST /access-control/floors/{building_id}/{floor_id}/permissions/bulk
Content-Type: application/json

[
    {
        "role": "contractor",
        "resource_type": "floor",
        "permission_level": 2
    },
    {
        "role": "inspector",
        "resource_type": "annotation",
        "permission_level": 2
    }
]
```

## Frontend Integration

### Access Control Manager

The frontend provides a comprehensive interface for managing access control:

```javascript
// Initialize access control manager
const accessControlManager = new AccessControlManager();

// Create user
await accessControlManager.createUser({
    username: "john_doe",
    email: "john@example.com",
    primary_role: "contractor"
});

// Grant permission
await accessControlManager.grantPermission({
    role: "contractor",
    resource_type: "floor",
    permission_level: 2,
    floor_id: "floor_001"
});

// Check permission
const hasPermission = accessControlManager.hasPermission(
    "floor", "update", "floor_001"
);

// Log activity
accessControlManager.logActivity(
    "update", "floor", "floor_001", 
    {details: "Updated floor layout"}
);
```

### Real-Time Updates

The system supports real-time updates via WebSocket connections:

```javascript
// Handle real-time updates
accessControlManager.handleRealTimeUpdate({
    type: "permission_granted",
    role: "contractor",
    resource_type: "floor"
});
```

## Usage Examples

### 1. Setting Up Floor Access for Construction Project

```python
# Create users for construction project
contractor_user = access_control.create_user(
    username="site_contractor",
    email="contractor@construction.com",
    primary_role=UserRole.CONTRACTOR,
    organization="ABC Construction"
)

inspector_user = access_control.create_user(
    username="building_inspector",
    email="inspector@city.gov",
    primary_role=UserRole.INSPECTOR,
    organization="City Building Department"
)

# Grant floor-specific permissions
access_control.grant_permission(
    role=UserRole.CONTRACTOR,
    resource_type=ResourceType.FLOOR,
    permission_level=PermissionLevel.WRITE,
    floor_id="floor_001",
    building_id="building_001"
)

access_control.grant_permission(
    role=UserRole.INSPECTOR,
    resource_type=ResourceType.ANNOTATION,
    permission_level=PermissionLevel.WRITE,
    floor_id="floor_001",
    building_id="building_001"
)
```

### 2. Checking Permissions Before Operations

```python
# Check if user can update floor
permission_result = access_control.check_permission(
    user_id="contractor_user_id",
    resource_type=ResourceType.FLOOR,
    action=ActionType.UPDATE,
    floor_id="floor_001",
    building_id="building_001"
)

if permission_result["success"]:
    # Proceed with floor update
    update_floor_layout()
    
    # Log the activity
    access_control.log_audit_event(
        user_id="contractor_user_id",
        action=ActionType.UPDATE,
        resource_type=ResourceType.FLOOR,
        resource_id="floor_001",
        floor_id="floor_001",
        building_id="building_001",
        details={"operation": "layout_update"}
    )
else:
    # Handle permission denied
    raise PermissionError("Insufficient permissions")
```

### 3. Generating Access Reports

```python
# Get floor access summary
summary = access_control.get_floor_access_summary("building_001", "floor_001")

print(f"Floor {summary['floor_id']} Access Summary:")
print(f"Total Permissions: {summary['permission_count']}")
print(f"Recent Activities: {summary['activity_count']}")

# Get audit logs for compliance
audit_logs = access_control.get_audit_logs(
    resource_type=ResourceType.FLOOR,
    resource_id="floor_001",
    start_date=datetime(2024, 1, 1),
    end_date=datetime(2024, 12, 31)
)

for log in audit_logs["logs"]:
    print(f"{log['timestamp']}: {log['user_id']} {log['action']} {log['resource_type']}")
```

## Security Considerations

### 1. Permission Validation

- All operations validate permissions before execution
- Permission checks are performed at the service layer
- Failed permission checks are logged for security monitoring

### 2. Audit Trail Security

- All access control events are logged with full context
- Audit logs are tamper-evident and cannot be modified
- IP addresses and user agents are captured for security analysis

### 3. Role Hierarchy Security

- Role inheritance is carefully controlled to prevent privilege escalation
- Parent roles cannot inherit permissions from child roles
- Role modifications require appropriate administrative privileges

### 4. Data Protection

- Sensitive user information is encrypted at rest
- Permission data is protected with appropriate access controls
- Audit logs are retained according to compliance requirements

## Performance Considerations

### 1. Permission Caching

- User permissions are cached to reduce database queries
- Permission inheritance is calculated once and cached
- Cache invalidation occurs when permissions are modified

### 2. Database Optimization

- Indexes on frequently queried columns
- Efficient queries for permission checks
- Pagination for large audit log datasets

### 3. Scalability

- Horizontal scaling support for high-traffic environments
- Efficient permission checking algorithms
- Optimized audit log storage and retrieval

## Testing

### Unit Tests

Comprehensive test coverage includes:

- User creation and management
- Permission granting and revocation
- Permission checking and inheritance
- Audit log creation and retrieval
- Floor-specific access controls
- Role hierarchy validation

### Integration Tests

- End-to-end permission workflows
- API endpoint testing
- Frontend integration testing
- Real-time update testing

### Security Tests

- Permission bypass attempts
- Role escalation testing
- Audit log integrity verification
- Input validation testing

## Deployment

### 1. Database Setup

```bash
# Initialize access control database
python -c "from services.access_control import AccessControlService; AccessControlService()"
```

### 2. Service Integration

```python
# Add to main application
from routers.access_control import router as access_control_router

app.include_router(access_control_router, prefix="/access-control")
```

### 3. Frontend Integration

```html
<!-- Include access control styles and scripts -->
<link rel="stylesheet" href="static/css/access_control.css">
<script src="static/js/access_control_manager.js"></script>
```

## Monitoring and Maintenance

### 1. Health Checks

- Database connectivity monitoring
- Permission service availability
- Audit log system health

### 2. Performance Monitoring

- Permission check response times
- Audit log write performance
- Database query optimization

### 3. Security Monitoring

- Failed permission attempts
- Unusual access patterns
- Audit log anomalies

## Future Enhancements

### 1. Advanced Features

- Time-based permissions (temporary access)
- Conditional permissions (based on context)
- Permission templates for common scenarios
- Advanced role inheritance rules

### 2. Integration Features

- LDAP/Active Directory integration
- Single Sign-On (SSO) support
- Multi-factor authentication
- API key management

### 3. Analytics and Reporting

- Permission usage analytics
- Access pattern analysis
- Compliance reporting
- Security dashboard

## Conclusion

The Access Control implementation provides a robust, scalable, and secure foundation for managing permissions across the Arxos platform. With comprehensive role-based access control, floor-specific permissions, detailed audit trails, and flexible permission inheritance, the system ensures that users have appropriate access while maintaining security and compliance requirements.

The modular design allows for easy extension and customization, while the comprehensive testing ensures reliability and security. The frontend integration provides an intuitive interface for administrators to manage access control effectively. 