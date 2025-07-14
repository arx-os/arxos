# NOT NULL and CHECK Constraints Implementation Guide

## Overview

This guide documents the comprehensive implementation of NOT NULL and CHECK constraints in the Arxos database to strengthen data integrity while maintaining backward compatibility and safe migration strategies.

## Architecture

### Constraint Categories

The implementation covers five main categories of constraints:

1. **NOT NULL Constraints**: Enforce required fields
2. **CHECK Constraints**: Validate finite domain values
3. **Format Validation**: Email, username, password hash formats
4. **Domain Validation**: Material types, system types, severity levels
5. **Timestamp Validation**: Prevent future dates and ensure consistency

### Implementation Components

```
infrastructure/database/
├── tools/
│   ├── audit_constraints.py          # Schema audit tool
│   └── parse_slow_queries.py        # Performance analysis
├── scripts/
│   └── backfill_nulls.sql           # Safe NULL data backfill
├── migrations/
│   └── 006_add_constraints.sql      # Constraint migration
├── tests/
│   └── test_constraints.py          # Unit tests
└── docs/
    └── CONSTRAINT_IMPLEMENTATION_GUIDE.md
```

## Quick Start

### 1. Audit Existing Schema

```bash
# Run comprehensive schema audit
python tools/audit_constraints.py --database-url postgresql://localhost/arxos_db

# Generate detailed report
python tools/audit_constraints.py --output-format markdown --output-file audit_report.md
```

### 2. Backfill NULL Data

```bash
# Execute safe backfill script
psql -d arxos_db -f scripts/backfill_nulls.sql
```

### 3. Apply Constraints

```bash
# Apply constraint migration
psql -d arxos_db -f migrations/006_add_constraints.sql
```

### 4. Validate Constraints

```bash
# Run comprehensive tests
python -m pytest tests/test_constraints.py -v
```

## Detailed Implementation

### Phase 1: Schema Audit

The `audit_constraints.py` tool performs comprehensive analysis:

#### Business Rules

```python
business_rules = {
    'always_required_fields': [
        'email', 'username', 'password_hash', 'name', 'title', 'content',
        'message', 'action', 'change_type', 'object_type', 'object_id'
    ],
    'status_fields': [
        'status', 'role', 'type', 'category', 'material', 'system'
    ],
    'finite_domain_patterns': {
        'status': ['active', 'inactive', 'suspended', 'pending', 'completed', 'cancelled'],
        'role': ['user', 'admin', 'manager', 'viewer'],
        'type': ['education', 'commercial', 'residential', 'industrial'],
        'material': ['concrete', 'steel', 'wood', 'glass', 'plastic', 'metal'],
        'system': ['HVAC', 'electrical', 'plumbing', 'fire', 'security', 'lighting']
    }
}
```

#### Audit Process

1. **Column Analysis**: Identify nullable columns that should be NOT NULL
2. **Domain Analysis**: Find columns with finite value sets for CHECK constraints
3. **Risk Assessment**: Evaluate migration risk based on NULL data count
4. **Recommendation Generation**: Create prioritized constraint recommendations

#### Example Audit Output

```json
{
  "metadata": {
    "audit_timestamp": "2024-01-15T10:30:00",
    "database_name": "arxos_db",
    "tables_audited": 20,
    "processing_metrics": {
      "tables_analyzed": 20,
      "columns_analyzed": 150,
      "constraint_candidates_found": 45
    }
  },
  "summary": {
    "total_constraint_candidates": 45,
    "not_null_candidates": 30,
    "check_candidates": 15,
    "high_priority_tables": ["users", "projects", "buildings"],
    "recommendations": [
      "Start with 3 high-priority tables",
      "Add 30 NOT NULL constraints",
      "Add 15 CHECK constraints",
      "Backfill NULL values in: users.role, projects.name"
    ]
  }
}
```

### Phase 2: Safe Data Backfill

The `backfill_nulls.sql` script safely updates NULL data:

#### Safety Features

- **Automatic Backups**: Creates timestamped backup tables
- **Validation Queries**: Reports remaining NULL values
- **Rollback Instructions**: Provides rollback procedures
- **Business Logic**: Uses appropriate defaults based on context

#### Backfill Strategy

```sql
-- Example: Update NULL status fields to 'active'
UPDATE rooms 
SET status = 'active' 
WHERE status IS NULL;

-- Example: Update NULL timestamps to current time
UPDATE users 
SET created_at = CURRENT_TIMESTAMP 
WHERE created_at IS NULL;

-- Example: Update NULL materials to common defaults
UPDATE walls 
SET material = 'concrete' 
WHERE material IS NULL;
```

#### Validation Report

```sql
-- Summary of backfill operation
DO $$
DECLARE
    summary_record RECORD;
BEGIN
    FOR summary_record IN
        SELECT 
            'users' as table_name,
            COUNT(*) as total_count,
            COUNT(CASE WHEN role IS NULL THEN 1 END) as null_count
        FROM users
        -- ... more tables
    LOOP
        RAISE NOTICE 'Table: % | Total: % | Remaining NULL: %', 
            summary_record.table_name, 
            summary_record.total_count, 
            summary_record.null_count;
    END LOOP;
END $$;
```

### Phase 3: Constraint Migration

The `006_add_constraints.sql` migration adds comprehensive constraints:

#### NOT NULL Constraints

```sql
-- Users table
ALTER TABLE users 
    ALTER COLUMN role SET NOT NULL,
    ALTER COLUMN created_at SET NOT NULL,
    ALTER COLUMN updated_at SET NOT NULL;

-- Projects table
ALTER TABLE projects 
    ALTER COLUMN created_at SET NOT NULL,
    ALTER COLUMN updated_at SET NOT NULL;

-- BIM objects
ALTER TABLE rooms 
    ALTER COLUMN status SET NOT NULL,
    ALTER COLUMN category SET NOT NULL;
```

#### CHECK Constraints

```sql
-- Role validation
ALTER TABLE users 
    ADD CONSTRAINT chk_users_role 
    CHECK (role IN ('user', 'admin', 'manager', 'viewer'));

-- Status validation
ALTER TABLE rooms 
    ADD CONSTRAINT chk_rooms_status 
    CHECK (status IN ('active', 'inactive', 'suspended', 'pending', 'completed', 'cancelled'));

-- Material validation
ALTER TABLE walls 
    ADD CONSTRAINT chk_walls_material 
    CHECK (material IN ('concrete', 'steel', 'wood', 'glass', 'plastic', 'metal'));
```

#### Format Validation

```sql
-- Email format
ALTER TABLE users 
    ADD CONSTRAINT chk_users_email_format 
    CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$');

-- Username format
ALTER TABLE users 
    ADD CONSTRAINT chk_users_username_format 
    CHECK (username ~* '^[a-zA-Z0-9_-]{3,50}$');

-- Password hash format
ALTER TABLE users 
    ADD CONSTRAINT chk_users_password_hash_format 
    CHECK (password_hash ~* '^[a-fA-F0-9]{64}$');
```

#### Performance Indexes

```sql
-- Indexes for constraint checking
CREATE INDEX IF NOT EXISTS idx_users_role_check ON users (role);
CREATE INDEX IF NOT EXISTS idx_rooms_status_check ON rooms (status);
CREATE INDEX IF NOT EXISTS idx_walls_material_check ON walls (material);
```

### Phase 4: Validation Testing

The `test_constraints.py` module provides comprehensive testing:

#### Test Categories

1. **NOT NULL Enforcement**: Verify required fields cannot be NULL
2. **CHECK Validation**: Test finite domain constraints
3. **Format Validation**: Test email, username, password formats
4. **Performance Testing**: Measure constraint impact
5. **Integration Testing**: Verify constraint indexes

#### Example Test

```python
def test_not_null_constraints_users(self, db_helper, clean_database):
    """Test NOT NULL constraints on users table."""
    
    # Test valid data insertion
    valid_user = {
        'email': 'test@example.com',
        'username': 'testuser',
        'password_hash': 'a' * 64,
        'role': 'user'
    }
    user_id = db_helper.insert_test_data('users', valid_user)
    assert user_id is not None
    
    # Test NULL email (should fail)
    invalid_user = valid_user.copy()
    invalid_user['email'] = None
    
    with pytest.raises(psycopg2.IntegrityError) as exc_info:
        db_helper.insert_test_data('users', invalid_user)
    
    assert 'email' in str(exc_info.value).lower()
```

## Constraint Categories

### 1. Required Fields (NOT NULL)

| Table | Column | Reason | Default Value |
|-------|--------|--------|---------------|
| users | email | Business requirement | N/A |
| users | username | Business requirement | N/A |
| users | password_hash | Security requirement | N/A |
| users | role | Application logic | 'user' |
| projects | name | Business requirement | N/A |
| buildings | name | Business requirement | N/A |
| rooms | status | Application state | 'active' |
| rooms | category | Classification | '' |
| walls | material | BIM requirement | 'concrete' |
| devices | system | System classification | 'electrical' |

### 2. Finite Domain Values (CHECK)

| Table | Column | Valid Values | Constraint Name |
|-------|--------|--------------|-----------------|
| users | role | user, admin, manager, viewer | chk_users_role |
| rooms | status | active, inactive, suspended, pending, completed, cancelled | chk_rooms_status |
| walls | material | concrete, steel, wood, glass, plastic, metal | chk_walls_material |
| devices | system | HVAC, electrical, plumbing, fire, security, lighting | chk_devices_system |
| assignments | status | assigned, in_progress, completed, cancelled | chk_assignments_status |
| audit_logs | action | create, update, delete, login, logout, unknown | chk_audit_logs_action |

### 3. Format Validation (CHECK)

| Table | Column | Pattern | Constraint Name |
|-------|--------|---------|-----------------|
| users | email | Email regex | chk_users_email_format |
| users | username | Alphanumeric + underscore/hyphen | chk_users_username_format |
| users | password_hash | 64 hex characters | chk_users_password_hash_format |

### 4. Timestamp Validation (CHECK)

| Table | Column | Validation | Constraint Name |
|-------|--------|------------|-----------------|
| users | created_at | Not in future | chk_users_created_at_future |
| users | updated_at | Not in future | chk_users_updated_at_future |
| projects | created_at | Not in future | chk_projects_created_at_future |
| buildings | created_at | Not in future | chk_buildings_created_at_future |

## Migration Safety

### Rollback Strategy

The migration includes a comprehensive rollback function:

```sql
-- Function to drop all constraints added by this migration
CREATE OR REPLACE FUNCTION rollback_constraints_migration()
RETURNS VOID AS $$
DECLARE
    constraint_record RECORD;
BEGIN
    -- Drop CHECK constraints
    FOR constraint_record IN
        SELECT tc.table_name, tc.constraint_name
        FROM information_schema.table_constraints tc
        WHERE tc.table_schema = 'public' 
        AND tc.constraint_type = 'CHECK'
        AND tc.constraint_name LIKE 'chk_%'
    LOOP
        EXECUTE format('ALTER TABLE %I DROP CONSTRAINT %I', 
                      constraint_record.table_name, 
                      constraint_record.constraint_name);
    END LOOP;
    
    -- Reset NOT NULL constraints
    ALTER TABLE users ALTER COLUMN role DROP NOT NULL;
    -- ... more table rollbacks
END;
$$ LANGUAGE plpgsql;
```

### Backup Strategy

The backfill script creates automatic backups:

```sql
-- Create backup tables with timestamp
DO $$
DECLARE
    backup_suffix TEXT := '_backup_' || TO_CHAR(NOW(), 'YYYYMMDD_HH24MISS');
    table_name TEXT;
BEGIN
    FOR table_name IN 
        SELECT unnest(ARRAY['users', 'projects', 'buildings', ...])
    LOOP
        EXECUTE format('CREATE TABLE %I AS SELECT * FROM %I', 
                      table_name || backup_suffix, 
                      table_name);
    END LOOP;
END $$;
```

## Performance Considerations

### Index Strategy

Performance indexes are added for constraint checking:

```sql
-- Indexes for frequently checked constraint columns
CREATE INDEX IF NOT EXISTS idx_users_role_check ON users (role);
CREATE INDEX IF NOT EXISTS idx_rooms_status_check ON rooms (status);
CREATE INDEX IF NOT EXISTS idx_walls_material_check ON walls (material);
```

### Constraint Performance

- **NOT NULL**: Minimal performance impact
- **CHECK**: Moderate impact, mitigated by indexes
- **Format Validation**: Low impact with regex optimization
- **Domain Validation**: Very low impact with small value sets

### Monitoring

Performance impact is monitored through:

1. **Slow Query Logging**: Tracks constraint-related performance
2. **Unit Tests**: Measure insertion performance
3. **Integration Tests**: Verify overall system performance

## Best Practices

### 1. Migration Order

1. **Audit First**: Always run audit before making changes
2. **Backfill Second**: Update NULL data safely
3. **Test Third**: Validate in staging environment
4. **Deploy Fourth**: Apply to production with monitoring

### 2. Constraint Design

- **Business-Driven**: Base constraints on business requirements
- **Performance-Aware**: Add indexes for constraint checking
- **Maintainable**: Use clear, descriptive constraint names
- **Reversible**: Include rollback procedures

### 3. Testing Strategy

- **Unit Tests**: Test individual constraint enforcement
- **Integration Tests**: Test constraint interactions
- **Performance Tests**: Measure constraint impact
- **Rollback Tests**: Verify rollback procedures

### 4. Monitoring

- **Constraint Violations**: Monitor for constraint errors
- **Performance Impact**: Track query performance changes
- **Data Quality**: Monitor data integrity improvements

## Troubleshooting

### Common Issues

#### 1. Constraint Violation Errors

**Problem**: `IntegrityError` when inserting data

**Solution**: 
- Check data format against constraint requirements
- Verify all required fields are provided
- Ensure domain values are valid

#### 2. Performance Degradation

**Problem**: Slower queries after constraint addition

**Solution**:
- Verify constraint indexes are created
- Monitor slow query logs
- Consider query optimization

#### 3. Migration Failures

**Problem**: Migration fails during constraint application

**Solution**:
- Check for remaining NULL values
- Verify backup tables exist
- Use rollback function if needed

### Debugging Tools

```bash
# Check constraint status
SELECT constraint_name, table_name, constraint_type 
FROM information_schema.table_constraints 
WHERE table_schema = 'public' 
AND constraint_type IN ('CHECK', 'NOT NULL');

# Check for NULL values
SELECT column_name, COUNT(*) as null_count
FROM information_schema.columns c
JOIN (
    SELECT table_name, column_name, COUNT(*) as null_count
    FROM information_schema.columns
    WHERE table_schema = 'public'
    GROUP BY table_name, column_name
) stats ON c.table_name = stats.table_name AND c.column_name = stats.column_name
WHERE c.is_nullable = 'YES'
AND stats.null_count > 0;
```

## Conclusion

The NOT NULL and CHECK constraint implementation provides comprehensive data integrity enforcement while maintaining backward compatibility and safe migration strategies. The implementation follows Arxos standards for:

- **Structured Logging**: Comprehensive audit trails
- **Performance Monitoring**: Impact measurement and optimization
- **Error Handling**: Robust error management and recovery
- **Documentation**: Complete implementation guides and troubleshooting
- **Testing**: Comprehensive unit and integration tests

This implementation strengthens the Arxos database foundation and provides a solid base for future data integrity requirements. 