# Users Table Documentation

## Purpose

The `users` table is the foundational table for user authentication and management in the Arxos platform. It serves as the base table that many other tables reference, establishing the user hierarchy and access control throughout the system.

### Key Responsibilities

1. **User Authentication**: Store user credentials and authentication data
2. **Access Control**: Define user roles and permissions
3. **Audit Trail**: Track user creation and modification timestamps
4. **Referential Integrity**: Provide foreign key references for user-related data

## Schema Definition

```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'user',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Column Descriptions

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | SERIAL | PRIMARY KEY | Auto-incrementing unique identifier |
| `email` | VARCHAR(255) | UNIQUE, NOT NULL | User's email address (unique) |
| `username` | VARCHAR(100) | UNIQUE, NOT NULL | User's username (unique) |
| `password_hash` | VARCHAR(255) | NOT NULL | Hashed password (never stored in plain text) |
| `role` | VARCHAR(50) | NOT NULL, DEFAULT 'user' | User role for access control |
| `created_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Record creation timestamp |
| `updated_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Record modification timestamp |

## Relationships

### Foreign Key References (Outbound)

The `users` table is referenced by many other tables:

```sql
-- Projects table
projects.user_id -> users.id (CASCADE)

-- Buildings table
buildings.owner_id -> users.id (SET NULL)

-- BIM Objects (rooms, walls, doors, windows, devices, labels, zones)
{object}.created_by -> users.id (SET NULL)
{object}.locked_by -> users.id (SET NULL)
{object}.assigned_to -> users.id (SET NULL)

-- Collaboration tables
comments.user_id -> users.id (CASCADE)
assignments.user_id -> users.id (CASCADE)
object_history.user_id -> users.id (CASCADE)
audit_logs.user_id -> users.id (CASCADE)
user_category_permissions.user_id -> users.id (CASCADE)
chat_messages.user_id -> users.id (CASCADE)
catalog_items.created_by -> users.id (CASCADE)
```

### Relationship Types

- **CASCADE**: When user is deleted, related records are deleted
- **SET NULL**: When user is deleted, foreign key is set to NULL

## Indexes

### Primary Index
```sql
-- Automatic primary key index
PRIMARY KEY (id)
```

### Unique Indexes
```sql
-- Email uniqueness
CREATE UNIQUE INDEX idx_users_email ON users(email);

-- Username uniqueness
CREATE UNIQUE INDEX idx_users_username ON users(username);
```

### Performance Indexes
```sql
-- Role-based queries
CREATE INDEX idx_users_role ON users(role);

-- Timestamp-based queries
CREATE INDEX idx_users_created_at ON users(created_at);
CREATE INDEX idx_users_updated_at ON users(updated_at);
```

### Index Rationale

1. **Primary Key Index**: Enables fast lookups by user ID
2. **Email Index**: Supports authentication and email-based queries
3. **Username Index**: Supports authentication and username-based queries
4. **Role Index**: Enables role-based filtering and access control
5. **Timestamp Indexes**: Support user activity analysis and auditing

## Constraints

### NOT NULL Constraints
```sql
-- Required fields for user creation
ALTER TABLE users ALTER COLUMN email SET NOT NULL;
ALTER TABLE users ALTER COLUMN username SET NOT NULL;
ALTER TABLE users ALTER COLUMN password_hash SET NOT NULL;
ALTER TABLE users ALTER COLUMN role SET NOT NULL;
ALTER TABLE users ALTER COLUMN created_at SET NOT NULL;
ALTER TABLE users ALTER COLUMN updated_at SET NOT NULL;
```

### CHECK Constraints
```sql
-- Email format validation
ALTER TABLE users ADD CONSTRAINT chk_users_email_format
CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$');

-- Username format validation
ALTER TABLE users ADD CONSTRAINT chk_users_username_format
CHECK (username ~* '^[a-zA-Z0-9_-]{3,50}$');

-- Role domain validation
ALTER TABLE users ADD CONSTRAINT chk_users_role_domain
CHECK (role IN ('admin', 'manager', 'user', 'viewer'));

-- Password hash format validation
ALTER TABLE users ADD CONSTRAINT chk_users_password_hash_format
CHECK (password_hash ~* '^[a-f0-9]{64}$');
```

### Unique Constraints
```sql
-- Email uniqueness
ALTER TABLE users ADD CONSTRAINT uq_users_email UNIQUE (email);

-- Username uniqueness
ALTER TABLE users ADD CONSTRAINT uq_users_username UNIQUE (username);
```

## Usage Patterns

### Common Queries

#### **User Authentication**
```sql
-- Authenticate user by email
SELECT id, username, password_hash, role
FROM users
WHERE email = ? AND role != 'inactive';

-- Authenticate user by username
SELECT id, email, password_hash, role
FROM users
WHERE username = ? AND role != 'inactive';
```

#### **User Management**
```sql
-- List all users with role
SELECT id, username, email, role, created_at
FROM users
ORDER BY created_at DESC;

-- Find users by role
SELECT id, username, email
FROM users
WHERE role = ?;

-- Search users by email or username
SELECT id, username, email, role
FROM users
WHERE email ILIKE ? OR username ILIKE ?;
```

#### **User Activity Analysis**
```sql
-- Recent user registrations
SELECT id, username, email, role, created_at
FROM users
WHERE created_at >= NOW() - INTERVAL '30 days'
ORDER BY created_at DESC;

-- User count by role
SELECT role, COUNT(*) as user_count
FROM users
GROUP BY role
ORDER BY user_count DESC;
```

### Performance Optimizations

#### **Index Usage**
- **Authentication queries**: Use email/username indexes for fast lookups
- **Role-based queries**: Use role index for filtering
- **Activity queries**: Use timestamp indexes for date range queries

#### **Query Patterns**
- **Point queries**: Use primary key or unique indexes
- **Range queries**: Use timestamp indexes for date ranges
- **Filtering**: Use role index for role-based filtering

## Migration History

### Version 001: Initial Schema
- Created base users table with authentication fields
- Added unique constraints for email and username
- Implemented role-based access control

### Version 002: Enhanced Constraints
- Added email format validation
- Added username format validation
- Added role domain validation
- Added password hash format validation

### Version 003: Performance Indexes
- Added role index for role-based queries
- Added timestamp indexes for activity analysis
- Optimized index order for common query patterns

## Best Practices

### Data Integrity

1. **Email Validation**: Always validate email format before insertion
2. **Password Security**: Never store plain text passwords, only hashes
3. **Role Management**: Use predefined role values to prevent invalid roles
4. **Timestamp Updates**: Always update `updated_at` when modifying records

### Performance

1. **Index Strategy**: Use appropriate indexes for common query patterns
2. **Query Optimization**: Use indexed columns in WHERE clauses
3. **Connection Pooling**: Use connection pooling for high-concurrency access
4. **Caching**: Cache frequently accessed user data

### Security

1. **Password Hashing**: Use strong hashing algorithms (bcrypt, Argon2)
2. **Input Validation**: Validate all user inputs before database insertion
3. **SQL Injection Prevention**: Use parameterized queries
4. **Access Control**: Implement proper role-based access control

## Monitoring and Maintenance

### Key Metrics

- **User Registration Rate**: Monitor new user creation
- **Authentication Success Rate**: Track login success/failure
- **Role Distribution**: Monitor user role distribution
- **Account Activity**: Track user activity patterns

### Maintenance Tasks

- **Monthly**: Review and clean up inactive users
- **Quarterly**: Audit user roles and permissions
- **Semi-annually**: Review and update password policies
- **Annually**: Comprehensive user data audit

### Backup Considerations

- **Critical Data**: Users table is critical for system operation
- **Backup Frequency**: Daily backups with point-in-time recovery
- **Recovery Testing**: Regular recovery testing for user data
- **Data Retention**: Follow data retention policies for user data

## Related Documentation

- [Projects Table](./projects.md) - User's project relationships
- [Audit Logs Table](./audit_logs.md) - User activity tracking
- [User Category Permissions Table](./user_category_permissions.md) - User permissions
- [Migration Guide](../migrations.md) - Database migration procedures
- [Performance Guide](../performance_guide.md) - Query optimization
- [Security Guide](../security_guide.md) - Database security practices
