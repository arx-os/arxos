# Database Migrations Documentation

## Overview

The Arxos database uses Alembic for version-controlled database schema evolution. This system provides safe, reversible migrations with comprehensive testing and rollback capabilities.

## Migration Architecture

### Version Control System

- **Alembic**: Python-based migration framework
- **Version Tracking**: Database schema version tracking
- **Rollback Support**: Full downgrade capabilities
- **CI/CD Integration**: Automated migration testing

### Migration Structure

```
arxos/infrastructure/database/
├── alembic/
│   ├── versions/                    # Migration files
│   │   ├── 001_create_initial_schema.py
│   │   ├── 002_add_indexes.py
│   │   ├── 003_create_slow_query_log.py
│   │   ├── 004_add_constraints.py
│   │   ├── 005_add_partitioning.py
│   │   └── ...
│   ├── env.py                       # Alembic environment
│   └── script.py.mako              # Migration template
├── migrations/                      # SQL migration files
│   ├── 001_create_arx_schema.sql
│   ├── 002_indexes.sql
│   ├── 003_create_slow_query_log.sql
│   ├── 004_add_constraints.sql
│   ├── 005_add_partitioning.sql
│   └── ...
└── alembic.ini                     # Alembic configuration
```

## Migration Types

### 1. Schema Migrations

#### **Table Creation**
```python
def upgrade() -> None:
    op.create_table('new_table',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

def downgrade() -> None:
    op.drop_table('new_table')
```

#### **Table Modification**
```python
def upgrade() -> None:
    op.add_column('existing_table', 
        sa.Column('new_column', sa.String(length=100), nullable=True)
    )

def downgrade() -> None:
    op.drop_column('existing_table', 'new_column')
```

### 2. Index Migrations

#### **Index Creation**
```python
def upgrade() -> None:
    op.create_index('idx_table_column', 'table_name', ['column_name'])

def downgrade() -> None:
    op.drop_index('idx_table_column', 'table_name')
```

#### **Composite Indexes**
```python
def upgrade() -> None:
    op.create_index('idx_table_col1_col2', 'table_name', 
                   ['column1', 'column2'])

def downgrade() -> None:
    op.drop_index('idx_table_col1_col2', 'table_name')
```

### 3. Constraint Migrations

#### **NOT NULL Constraints**
```python
def upgrade() -> None:
    op.alter_column('table_name', 'column_name',
                   existing_type=sa.String(length=255),
                   nullable=False)

def downgrade() -> None:
    op.alter_column('table_name', 'column_name',
                   existing_type=sa.String(length=255),
                   nullable=True)
```

#### **CHECK Constraints**
```python
def upgrade() -> None:
    op.create_check_constraint(
        'chk_table_column_domain',
        'table_name',
        'column_name IN (\'value1\', \'value2\', \'value3\')'
    )

def downgrade() -> None:
    op.drop_constraint('chk_table_column_domain', 'table_name')
```

### 4. Partitioning Migrations

#### **Table Partitioning**
```python
def upgrade() -> None:
    # Create partitioned parent table
    op.execute("""
        CREATE TABLE table_partitioned (
            id SERIAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ) PARTITION BY RANGE (created_at)
    """)
    
    # Create partitions
    op.execute("""
        CREATE TABLE table_p2024_01 
        PARTITION OF table_partitioned
        FOR VALUES FROM ('2024-01-01') TO ('2024-02-01')
    """)

def downgrade() -> None:
    op.drop_table('table_partitioned')
```

## Migration Workflow

### 1. Creating New Migrations

#### **Manual Migration Creation**
```bash
# Create new migration file
alembic revision -m "add new table"

# Edit the generated file in alembic/versions/
# Add upgrade() and downgrade() functions
```

#### **Autogenerate Migration**
```bash
# Generate migration from model changes
alembic revision --autogenerate -m "add new field"

# Review and edit the generated migration
# Remove any unwanted changes
```

### 2. Migration Development

#### **Local Development**
```bash
# Set up local database
createdb arxos_dev

# Apply migrations to development database
alembic upgrade head

# Test migration
alembic downgrade -1
alembic upgrade +1
```

#### **Testing Migrations**
```bash
# Run migration tests
python -m pytest tests/test_migrations.py

# Test rollback functionality
alembic downgrade base
alembic upgrade head
```

### 3. Production Deployment

#### **Pre-deployment Checklist**
- [ ] Migration tested in staging environment
- [ ] Rollback procedures verified
- [ ] Database backup created
- [ ] Downtime window scheduled (if needed)
- [ ] Team notified of deployment

#### **Deployment Commands**
```bash
# Check current migration state
alembic current

# Apply pending migrations
alembic upgrade head

# Verify migration success
alembic current
```

## Versioning Conventions

### Migration Naming

#### **Format**: `{version}_{description}.py`
```
001_create_initial_schema.py
002_add_performance_indexes.py
003_create_audit_logs.py
004_add_data_constraints.py
005_implement_partitioning.py
```

#### **Description Guidelines**
- Use descriptive, action-oriented names
- Include the main table or feature affected
- Keep names concise but informative
- Use lowercase with underscores

### Version Numbering

#### **Sequential Versioning**
- Start with 001 for initial migration
- Increment sequentially for each migration
- Use leading zeros for proper sorting
- Never reuse version numbers

#### **Branch Versioning** (for complex changes)
```
001_create_base_schema.py
002_add_user_tables.py
002a_add_user_indexes.py
002b_add_user_constraints.py
003_add_bim_tables.py
```

## Rollback Strategy

### 1. Automatic Rollback

#### **Alembic Downgrade**
```bash
# Rollback one migration
alembic downgrade -1

# Rollback to specific version
alembic downgrade 003

# Rollback to base (remove all migrations)
alembic downgrade base
```

#### **Downgrade Functions**
```python
def downgrade() -> None:
    # Always implement the reverse of upgrade()
    op.drop_table('new_table')
    op.drop_index('idx_table_column', 'table_name')
    op.drop_constraint('chk_constraint', 'table_name')
```

### 2. Manual Rollback Procedures

#### **Emergency Rollback**
```sql
-- For critical issues, manual rollback may be needed
-- Example: Rollback table partitioning
SELECT rollback_partitioning_migration();

-- Drop partitioned tables
DROP TABLE IF EXISTS audit_logs_partitioned CASCADE;
DROP TABLE IF EXISTS object_history_partitioned CASCADE;

-- Restore original tables
CREATE TABLE audit_logs AS SELECT * FROM audit_logs_backup;
```

#### **Data Recovery**
```sql
-- Restore data from backup
CREATE TABLE table_restored AS 
SELECT * FROM table_backup_20240101;

-- Update foreign key references
UPDATE dependent_table 
SET table_id = (SELECT id FROM table_restored WHERE old_id = table_id);
```

### 3. Rollback Testing

#### **Pre-deployment Testing**
```bash
# Test full rollback cycle
alembic upgrade head
alembic downgrade base
alembic upgrade head

# Verify data integrity
python tools/validate_migration.py
```

#### **Rollback Validation**
```python
def test_migration_rollback():
    # Apply migration
    alembic.upgrade()
    
    # Verify migration applied
    assert table_exists('new_table')
    
    # Rollback migration
    alembic.downgrade()
    
    # Verify rollback successful
    assert not table_exists('new_table')
```

## CI/CD Integration

### 1. Automated Testing

#### **Migration Validation**
```yaml
# .github/workflows/migrations.yml
- name: Test Migrations
  run: |
    # Set up test database
    createdb arxos_test
    
    # Apply all migrations
    alembic upgrade head
    
    # Test rollback
    alembic downgrade base
    alembic upgrade head
    
    # Validate schema
    python tools/schema_validator.py
```

#### **Performance Testing**
```yaml
- name: Performance Testing
  run: |
    # Benchmark before migration
    python tools/benchmark_partitioning.py --baseline
    
    # Apply migration
    alembic upgrade head
    
    # Benchmark after migration
    python tools/benchmark_partitioning.py --compare
```

### 2. Deployment Pipeline

#### **Staging Deployment**
```yaml
- name: Deploy to Staging
  run: |
    # Apply migrations to staging
    alembic upgrade head
    
    # Run integration tests
    python -m pytest tests/integration/
    
    # Performance validation
    python tools/validate_performance.py
```

#### **Production Deployment**
```yaml
- name: Deploy to Production
  run: |
    # Create backup
    pg_dump arxos_prod > backup_$(date +%Y%m%d_%H%M%S).sql
    
    # Apply migrations
    alembic upgrade head
    
    # Verify deployment
    alembic current
    python tools/validate_deployment.py
```

## Best Practices

### 1. Migration Development

#### **Always Include Rollback**
```python
def upgrade() -> None:
    # Add new column
    op.add_column('users', sa.Column('phone', sa.String(20)))

def downgrade() -> None:
    # Remove column
    op.drop_column('users', 'phone')
```

#### **Test Thoroughly**
- Test migration in isolation
- Test with realistic data volumes
- Test rollback functionality
- Test performance impact

#### **Document Changes**
```python
"""
Migration: Add user phone numbers
Description: Add phone number field to users table for contact information
Author: Database Team
Date: 2024-01-15
Dependencies: None
Rollback: Safe - drops column only
"""
```

### 2. Production Safety

#### **Backup Before Migration**
```bash
# Create timestamped backup
pg_dump arxos_prod > backup_$(date +%Y%m%d_%H%M%S).sql

# Verify backup integrity
pg_restore --list backup_*.sql
```

#### **Gradual Rollout**
```bash
# Apply to subset of servers first
alembic upgrade head --database-url=replica1

# Monitor for issues
python tools/monitor_migration.py

# Apply to all servers
alembic upgrade head
```

#### **Monitoring During Migration**
```sql
-- Monitor migration progress
SELECT * FROM alembic_version;

-- Check for blocking queries
SELECT * FROM pg_stat_activity WHERE state = 'active';

-- Monitor table locks
SELECT * FROM pg_locks WHERE NOT granted;
```

### 3. Performance Considerations

#### **Large Table Migrations**
```python
# For large tables, use batch processing
def upgrade() -> None:
    # Add column with default value
    op.add_column('large_table', 
                  sa.Column('new_column', sa.String(100), nullable=True))
    
    # Update in batches
    op.execute("""
        UPDATE large_table 
        SET new_column = 'default_value' 
        WHERE new_column IS NULL
    """)
```

#### **Index Creation**
```python
# Create indexes concurrently to avoid locks
def upgrade() -> None:
    op.create_index('idx_large_table_column', 'large_table', ['column'],
                   postgresql_concurrently=True)
```

## Troubleshooting

### Common Issues

#### **Migration Conflicts**
```bash
# Check migration state
alembic current
alembic history

# Resolve conflicts
alembic stamp head
alembic upgrade head
```

#### **Failed Migrations**
```bash
# Check migration logs
tail -f alembic.log

# Manual rollback if needed
psql -d arxos_db -c "DELETE FROM alembic_version WHERE version_num = 'failed_version';"
```

#### **Performance Issues**
```sql
-- Check for long-running queries
SELECT pid, query, query_start 
FROM pg_stat_activity 
WHERE state = 'active' AND query_start < NOW() - INTERVAL '5 minutes';

-- Kill blocking queries if necessary
SELECT pg_terminate_backend(pid) 
FROM pg_stat_activity 
WHERE state = 'active' AND query_start < NOW() - INTERVAL '10 minutes';
```

### Recovery Procedures

#### **Emergency Rollback**
```bash
# Stop application
sudo systemctl stop arxos-app

# Rollback migration
alembic downgrade -1

# Restart application
sudo systemctl start arxos-app

# Verify system health
python tools/health_check.py
```

#### **Data Recovery**
```bash
# Restore from backup
pg_restore -d arxos_prod backup_20240115_143022.sql

# Verify data integrity
python tools/validate_data.py

# Reapply migrations if needed
alembic upgrade head
```

## Related Documentation

- [Schema Documentation](./schema/) - Individual table documentation
- [Performance Guide](./performance_guide.md) - Query optimization
- [Constraints Guide](./constraints.md) - Data integrity constraints
- [Partitioning Guide](./partitioning.md) - Table partitioning strategy
- [Operational Guide](./operational_guide.md) - Database operations

---

*This documentation is maintained by the Database Team. For questions about migrations, contact the database team.* 