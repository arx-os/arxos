# Database Migration Management Guide

## Overview

The Arxos Platform uses Alembic for structured and versioned database schema migrations, ensuring safe, repeatable, and reversible changes across all services.

## Architecture

### Service-Specific Migrations

Each Python-based service has its own Alembic configuration:

- **arx_svg_parser**: SVG parsing and BIM data management
- **arx-bas-iot**: Building automation and IoT device management
- **arx-backend**: Core backend services (Go-based, uses SQL migrations)

### Migration Structure

```
service/
├── alembic.ini              # Alembic configuration
├── alembic/
│   ├── env.py               # Environment configuration
│   ├── script.py.mako       # Migration template
│   └── versions/            # Migration scripts
│       ├── 001_initial.py
│       ├── 002_add_tables.py
│       └── ...
```

## Setup and Configuration

### 1. Alembic Installation

Alembic is included in service requirements:

```bash
# For arx-bas-iot
pip install alembic==1.13.1

# For arx_svg_parser (already configured)
# alembic is already in requirements.txt
```

### 2. Database Configuration

Each service has its own database configuration:

**arx_svg_parser** (SQLite):
```ini
sqlalchemy.url = sqlite:///./data/arx_svg_parser.db
```

**arx-bas-iot** (SQLite):
```ini
sqlalchemy.url = sqlite:///./data/arx_bas_iot.db
```

**arx-backend** (PostgreSQL):
```ini
sqlalchemy.url = postgresql://arxos:arxos_password@localhost:5432/arxos_db
```

### 3. Environment Configuration

Each service's `alembic/env.py` is configured for:
- **Model imports**: Import your SQLAlchemy models
- **Metadata**: Set `target_metadata` for autogenerate
- **Database connection**: Configure connection handling

## Migration Scripts

### Modular Migration Structure

The monolithic `001_create_arx_schema.sql` has been split into modular migrations:

#### 1. Initial Users and Projects (`001_initial_users.py`)
```python
"""Initial users and projects schema"""
def upgrade() -> None:
    # Enable PostGIS extension
    op.execute('CREATE EXTENSION IF NOT EXISTS postgis')

    # Create users table
    op.create_table('users', ...)

    # Create projects table
    op.create_table('projects', ...)

    # Create indexes
    op.create_index('idx_projects_user_id', 'projects', ['user_id'])

def downgrade() -> None:
    # Drop indexes
    op.drop_index('idx_projects_user_id', table_name='projects')

    # Drop tables in reverse order
    op.drop_table('projects')
    op.drop_table('users')
```

#### 2. Buildings and Floors (`002_add_buildings_floors.py`)
```python
"""Add buildings and floors tables"""
def upgrade() -> None:
    # Create buildings table
    op.create_table('buildings', ...)

    # Create floors table
    op.create_table('floors', ...)

    # Create indexes
    op.create_index('idx_buildings_project_id', 'buildings', ['project_id'])
    op.create_index('idx_buildings_owner_id', 'buildings', ['owner_id'])
    op.create_index('idx_floors_building_id', 'floors', ['building_id'])

def downgrade() -> None:
    # Drop indexes and tables in reverse order
    ...
```

#### 3. Rooms Schema (`003_create_rooms_schema.py`)
```python
"""Create rooms schema with spatial geometry"""
def upgrade() -> None:
    # Create rooms table with PostGIS geometry
    op.create_table('rooms', ...)

    # Create spatial and regular indexes
    op.execute('CREATE INDEX idx_rooms_geom ON rooms USING GIST (geom)')
    op.create_index('idx_rooms_assigned_to', 'rooms', ['assigned_to'])
    # ... more indexes

def downgrade() -> None:
    # Drop indexes and table
    ...
```

#### 4. BIM Objects (`004_add_bim_objects.py`)
```python
"""Add BIM objects (walls, doors, windows)"""
def upgrade() -> None:
    # Create walls, doors, windows tables
    op.create_table('walls', ...)
    op.create_table('doors', ...)
    op.create_table('windows', ...)

    # Create spatial indexes for each
    op.execute('CREATE INDEX idx_walls_geom ON walls USING GIST (geom)')
    # ... more indexes

def downgrade() -> None:
    # Drop tables and indexes in reverse order
    ...
```

#### 5. Devices, Labels, Zones (`005_add_devices_labels_zones.py`)
```python
"""Add devices, labels, and zones tables"""
def upgrade() -> None:
    # Create devices, labels, zones tables
    op.create_table('devices', ...)
    op.create_table('labels', ...)
    op.create_table('zones', ...)

    # Create spatial indexes
    op.execute('CREATE INDEX idx_devices_geom ON devices USING GIST (geom)')
    # ... more indexes

def downgrade() -> None:
    # Drop tables and indexes in reverse order
    ...
```

#### 6. Collaboration Tables (`006_add_collaboration_tables.py`)
```python
"""Add collaboration and management tables"""
def upgrade() -> None:
    # Create collaboration tables
    op.create_table('drawings', ...)
    op.create_table('comments', ...)
    op.create_table('assignments', ...)
    op.create_table('object_history', ...)
    op.create_table('categories', ...)
    op.create_table('user_category_permissions', ...)
    op.create_table('audit_logs', ...)
    op.create_table('chat_messages', ...)
    op.create_table('catalog_items', ...)

    # Create indexes
    op.create_index('idx_drawings_project_id', 'drawings', ['project_id'])
    # ... more indexes

def downgrade() -> None:
    # Drop tables and indexes in reverse order
    ...
```

## Usage

### Local Development

#### 1. Check Migration Status
```bash
# Check current migration
alembic current

# View migration history
alembic history --verbose

# Show pending migrations
alembic heads
```

#### 2. Run Migrations
```bash
# Upgrade to latest version
alembic upgrade head

# Upgrade to specific revision
alembic upgrade 003

# Downgrade to previous version
alembic downgrade -1

# Downgrade to specific revision
alembic downgrade 002
```

#### 3. Create New Migration
```bash
# Create empty migration
alembic revision -m "Add new feature"

# Auto-generate migration from model changes
alembic revision --autogenerate -m "Add new table"

# Create migration with specific revision ID
alembic revision --rev-id 007 -m "Add user preferences"
```

#### 4. Validate Migrations
```bash
# Check for issues
alembic check

# Validate against database
alembic upgrade head
alembic downgrade base
alembic upgrade head
```

### Service-Specific Commands

#### arx_svg_parser
```bash
cd arx_svg_parser
alembic current
alembic upgrade head
```

#### arx-bas-iot
```bash
cd arx-bas-iot
alembic current
alembic upgrade head
```

#### arx-backend
```bash
cd arx-backend
alembic current
alembic upgrade head
```

## CI/CD Integration

### Automated Validation

The `.github/workflows/db_migrations.yml` workflow:

1. **Triggers** on migration file changes
2. **Sets up** PostgreSQL test database with PostGIS
3. **Validates** all service migrations
4. **Generates** comprehensive reports
5. **Comments** on PRs with results
6. **Fails** builds on migration errors

### Workflow Steps

1. **Setup Environment**:
   - PostgreSQL with PostGIS
   - Python 3.11
   - Alembic and dependencies

2. **Validate Migrations**:
   - Check current status
   - Run migrations to head
   - Verify migration history

3. **Safety Analysis**:
   - Check for destructive operations
   - Analyze data loss risks
   - Verify rollback capability

4. **Reporting**:
   - Generate validation reports
   - Upload artifacts
   - Comment on PRs

### Trigger Conditions

```yaml
on:
  push:
    branches: [ main, develop ]
    paths:
      - 'arx-backend/migrations/**/*.py'
      - 'arx_svg_parser/migrations/**/*.py'
      - 'arx-bas-iot/alembic/**/*.py'
      - '.github/workflows/db_migrations.yml'
  pull_request:
    branches: [ main, develop ]
    paths:
      - 'arx-backend/migrations/**/*.py'
      - 'arx_svg_parser/migrations/**/*.py'
      - 'arx-bas-iot/alembic/**/*.py'
      - '.github/workflows/db_migrations.yml'
```

## Best Practices

### 1. Migration Naming

**Format**: `{revision_id}_{description}.py`

**Examples**:
```python
001_initial_users.py
002_add_buildings_floors.py
003_create_rooms_schema.py
004_add_bim_objects.py
005_add_devices_labels_zones.py
006_add_collaboration_tables.py
```

### 2. Upgrade and Downgrade Functions

**Always implement both**:
```python
def upgrade() -> None:
    """Upgrade to this revision."""
    # Create tables, indexes, constraints

def downgrade() -> None:
    """Downgrade from this revision."""
    # Drop in reverse order
    # Drop indexes first, then tables
```

### 3. Foreign Key Order

**Follow dependency order**:
1. **Independent tables** (no foreign keys)
2. **Referenced tables** (referenced by others)
3. **Dependent tables** (have foreign keys)

### 4. Index Management

**Create indexes in upgrade**:
```python
def upgrade() -> None:
    # Create table
    op.create_table('users', ...)

    # Create indexes
    op.create_index('idx_users_email', 'users', ['email'])
    op.create_index('idx_users_username', 'users', ['username'])

def downgrade() -> None:
    # Drop indexes first
    op.drop_index('idx_users_username', table_name='users')
    op.drop_index('idx_users_email', table_name='users')

    # Then drop table
    op.drop_table('users')
```

### 5. Spatial Indexes

**Use PostGIS spatial indexes**:
```python
def upgrade() -> None:
    # Create table with geometry column
    op.create_table('rooms', ...)

    # Create spatial index
    op.execute('CREATE INDEX idx_rooms_geom ON rooms USING GIST (geom)')

def downgrade() -> None:
    # Drop spatial index
    op.execute('DROP INDEX IF EXISTS idx_rooms_geom')

    # Drop table
    op.drop_table('rooms')
```

### 6. Data Safety

**Avoid destructive operations**:
```python
# ❌ Avoid
op.drop_column('users', 'old_column')

# ✅ Better approach
# 1. Add new column
op.add_column('users', sa.Column('new_column', sa.String()))
# 2. Migrate data
op.execute('UPDATE users SET new_column = old_column')
# 3. Drop old column in separate migration
```

## Troubleshooting

### Common Issues

#### 1. Migration Conflicts
```bash
# Check for conflicting revisions
alembic heads

# Resolve conflicts
alembic merge heads -m "Merge conflicting revisions"
```

#### 2. Database Connection Issues
```bash
# Check database URL
alembic show

# Test connection
alembic current
```

#### 3. Missing Dependencies
```bash
# Install Alembic
pip install alembic

# Install database drivers
pip install psycopg2-binary  # PostgreSQL
pip install sqlite3          # SQLite (built-in)
```

#### 4. Rollback Issues
```bash
# Check migration history
alembic history --verbose

# Force to specific revision
alembic stamp 003

# Manual rollback
alembic downgrade -1
```

### Debugging Commands

```bash
# Show current revision
alembic current

# Show migration history
alembic history --verbose

# Show pending migrations
alembic heads

# Check for issues
alembic check

# Show configuration
alembic show
```

### Error Recovery

#### 1. Failed Migration
```bash
# Check current state
alembic current

# Rollback to previous version
alembic downgrade -1

# Fix migration script
# Re-run migration
alembic upgrade head
```

#### 2. Database Inconsistency
```bash
# Stamp database to specific revision
alembic stamp 003

# Run migrations from that point
alembic upgrade head
```

#### 3. Missing Migration Files
```bash
# Check migration directory
ls alembic/versions/

# Recreate missing migrations
alembic revision --autogenerate -m "Recreate missing migration"
```

## Performance Considerations

### 1. Migration Speed

**Large tables**:
- Use `CREATE INDEX CONCURRENTLY` for PostgreSQL
- Batch data migrations
- Use temporary tables for complex changes

### 2. Downtime Minimization

**Zero-downtime migrations**:
- Add columns as nullable first
- Migrate data in batches
- Drop old columns in separate migration

### 3. Rollback Performance

**Fast rollbacks**:
- Keep downgrade functions simple
- Avoid complex data transformations in rollback
- Use database-specific optimizations

## Security

### 1. Database Credentials

**Environment variables**:
```bash
# Use environment variables for sensitive data
export DATABASE_URL="postgresql://user:pass@host:port/db"
```

### 2. Migration Permissions

**Least privilege**:
- Use dedicated migration user
- Grant only necessary permissions
- Separate read/write permissions

### 3. Audit Trail

**Track changes**:
- Log all migration executions
- Record who ran migrations
- Maintain migration history

## Monitoring and Maintenance

### 1. Migration Health

**Regular checks**:
```bash
# Check migration status
alembic current

# Verify all services
for service in arx_svg_parser arx-bas-iot arx-backend; do
    cd $service
    alembic current
done
```

### 2. Performance Monitoring

**Track migration times**:
- Monitor upgrade/downgrade duration
- Alert on slow migrations
- Track database size changes

### 3. Backup Strategy

**Before migrations**:
```bash
# Backup production database
pg_dump arxos_db > backup_$(date +%Y%m%d_%H%M%S).sql

# Verify backup
pg_restore --dry-run backup_file.sql
```

## Support and Resources

### Documentation
- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [PostGIS Documentation](https://postgis.net/documentation/)

### Tools
- **Alembic**: Migration framework
- **SQLAlchemy**: ORM and database toolkit
- **PostGIS**: Spatial database extension

### Team Contacts
- **Database Team**: db-team@arxos.com
- **DevOps Team**: devops@arxos.com
- **Security Team**: security@arxos.com

---

*Last updated: 2024-01-15*
*Version: 1.0*
