# Alembic Migration Guide for Arxos Database

## Overview

This guide explains how to use Alembic for database schema migrations in the Arxos platform. Alembic provides version-controlled database schema evolution with rollback capabilities.

## Quick Start

### 1. Install Dependencies

```bash
cd infrastructure/database
pip install -r requirements.txt
```

### 2. Initialize Alembic (First Time Only)

```bash
alembic init alembic
```

### 3. Configure Database URL

Edit `alembic.ini` and update the `sqlalchemy.url`:

```ini
sqlalchemy.url = postgresql://username:password@localhost/arxos_db
```

### 4. Run Migrations

```bash
# Apply all pending migrations
alembic upgrade head

# Check current migration state
alembic current

# View migration history
alembic history --verbose
```

## Migration Workflow

### Creating a New Migration

#### Method 1: Manual Migration (Recommended for complex changes)

```bash
alembic revision -m "add new table"
```

This creates a new migration file in `alembic/versions/`. Edit the file to add your schema changes:

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

#### Method 2: Autogenerate Migration (For model changes)

1. **Setup autogeneration** (one-time):
   ```bash
   python setup_autogenerate.py
   ```

2. **Update your models** in `models.py`

3. **Generate migration**:
   ```bash
   alembic revision --autogenerate -m "add new field to user table"
   ```

4. **Review and edit** the generated migration file

### Applying Migrations

```bash
# Apply all pending migrations
alembic upgrade head

# Apply specific migration
alembic upgrade <revision_id>

# Apply relative migration
alembic upgrade +1  # Apply next migration
alembic upgrade -1  # Rollback one migration
```

### Rolling Back Migrations

```bash
# Rollback to specific revision
alembic downgrade <revision_id>

# Rollback one migration
alembic downgrade -1

# Rollback all migrations
alembic downgrade base
```

## Migration Best Practices

### 1. Migration File Naming

Use descriptive names that indicate the purpose:

```bash
alembic revision -m "add user authentication fields"
alembic revision -m "create building management tables"
alembic revision -m "add spatial indexes for performance"
```

### 2. Migration Structure

Always include both `upgrade()` and `downgrade()` functions:

```python
def upgrade() -> None:
    # Add your schema changes here
    op.create_table('example', ...)
    op.create_index('idx_example', 'example', ['column'])

def downgrade() -> None:
    # Reverse your changes here
    op.drop_index('idx_example', 'example')
    op.drop_table('example')
```

### 3. Foreign Key Dependencies

Ensure tables are created in the correct order:

```python
def upgrade() -> None:
    # Create referenced table first
    op.create_table('users', ...)

    # Then create referencing table
    op.create_table('posts',
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id')),
        ...
    )
```

### 4. Index Management

Create indexes for performance:

```python
def upgrade() -> None:
    op.create_table('posts', ...)
    op.create_index('idx_posts_user_id', 'posts', ['user_id'])
    op.create_index('idx_posts_created_at', 'posts', ['created_at'])

def downgrade() -> None:
    op.drop_index('idx_posts_created_at', 'posts')
    op.drop_index('idx_posts_user_id', 'posts')
    op.drop_table('posts')
```

### 5. Data Migrations

For data changes, use raw SQL:

```python
def upgrade() -> None:
    # Schema changes
    op.add_column('users', sa.Column('email', sa.String(255)))

    # Data changes
    op.execute("UPDATE users SET email = username || '@example.com' WHERE email IS NULL")

def downgrade() -> None:
    op.drop_column('users', 'email')
```

## PostGIS Integration

### Geometry Columns

For PostGIS geometry columns, use Text type and cast:

```python
def upgrade() -> None:
    op.create_table('rooms',
        sa.Column('geom', sa.Text()),  # Store as text
        ...
    )
    # Convert to geometry after table creation
    op.execute("ALTER TABLE rooms ALTER COLUMN geom TYPE geometry(Polygon, 4326)")

def downgrade() -> None:
    op.drop_table('rooms')
```

### Spatial Indexes

```python
def upgrade() -> None:
    op.execute("CREATE INDEX idx_rooms_geom ON rooms USING GIST (geom)")

def downgrade() -> None:
    op.execute("DROP INDEX idx_rooms_geom")
```

## CI/CD Integration

### GitHub Actions

The CI pipeline automatically tests migrations:

1. **On Pull Requests**: Tests migration files
2. **On Main Branch**: Applies migrations to test database
3. **Validation**: Checks migration syntax and dependencies

### Local Testing

Test migrations locally before pushing:

```bash
# Create test database
createdb arxos_test

# Update alembic.ini for test database
sed -i 's/arxos_db/arxos_test/' alembic.ini

# Test migrations
alembic upgrade head
alembic downgrade base
```

## Troubleshooting

### Common Issues

#### 1. "Target database is not up to date"

**Solution**: Apply pending migrations
```bash
alembic upgrade head
```

#### 2. "Can't locate revision identified by"

**Solution**: Check migration history and current state
```bash
alembic history --verbose
alembic current
```

#### 3. "Foreign key constraint violation"

**Solution**: Check table creation order in migration
```python
# Ensure referenced table exists first
op.create_table('users', ...)
op.create_table('posts',
    sa.Column('user_id', sa.ForeignKey('users.id')),
    ...
)
```

#### 4. "PostGIS extension not available"

**Solution**: Enable PostGIS extension
```python
def upgrade() -> None:
    op.execute('CREATE EXTENSION IF NOT EXISTS postgis')
    # ... rest of migration
```

### Debugging Tips

1. **Check migration state**:
   ```bash
   alembic current
   alembic history --verbose
   ```

2. **Test specific migration**:
   ```bash
   alembic upgrade <revision_id>
   alembic downgrade <revision_id>
   ```

3. **View migration SQL**:
   ```bash
   alembic upgrade head --sql
   ```

4. **Check database schema**:
   ```sql
   \dt  -- List tables
   \d+ table_name  -- Describe table
   ```

## Migration Commands Reference

### Basic Commands

```bash
# Initialize Alembic
alembic init alembic

# Create new migration
alembic revision -m "description"

# Apply migrations
alembic upgrade head
alembic upgrade +1
alembic upgrade <revision>

# Rollback migrations
alembic downgrade -1
alembic downgrade base
alembic downgrade <revision>

# Check status
alembic current
alembic history
alembic show <revision>
```

### Advanced Commands

```bash
# Generate migration from models
alembic revision --autogenerate -m "description"

# Show migration SQL without applying
alembic upgrade head --sql

# Stamp database with current revision
alembic stamp head

# Mark database as up to date
alembic stamp <revision>
```

## File Structure

```
infrastructure/database/
├── alembic.ini                 # Alembic configuration
├── alembic/
│   ├── env.py                  # Migration environment
│   └── versions/               # Migration files
│       ├── 001_create_initial_schema.py
│       └── 002_add_new_feature.py
├── models.py                   # SQLAlchemy models (for autogeneration)
├── requirements.txt            # Python dependencies
└── setup_autogenerate.py      # Autogeneration setup script
```

## Security Considerations

1. **Database Credentials**: Never commit database passwords to version control
2. **Migration Files**: Review all generated migrations before applying
3. **Backup**: Always backup database before applying migrations
4. **Testing**: Test migrations on staging environment first

## Performance Tips

1. **Batch Operations**: Use batch operations for large data migrations
2. **Indexes**: Create indexes after data insertion for better performance
3. **Transactions**: Use transactions for data consistency
4. **Monitoring**: Monitor migration execution time and resource usage

## Next Steps

1. **Review existing migrations** in `alembic/versions/`
2. **Test the migration system** with a local database
3. **Set up autogeneration** for future model changes
4. **Integrate with your application** deployment process

For more information, see the [Alembic documentation](https://alembic.sqlalchemy.org/).
