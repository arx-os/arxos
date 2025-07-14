# Arxos Database Infrastructure

## Overview

The Arxos Database Infrastructure provides comprehensive tools for database schema management, validation, and data integrity enforcement. This includes schema validation, constraint management, and performance monitoring tools.

## Components

### 1. Schema Validator
Validates SQL migration files to ensure proper database schema structure and prevent common issues that can cause deployment failures.

### 2. Constraint Management
Enforces data integrity through NOT NULL and CHECK constraints with comprehensive audit tools and safe migration strategies.

### 3. Performance Monitoring
Includes slow query logging and performance analysis tools for database optimization.

## Schema Validator Purpose

The schema validator prevents invalid migrations by checking:

1. **Foreign Key Ordering**: Ensures referenced tables are created before referencing tables
2. **Index Presence**: Validates that foreign key columns have associated indexes for performance
3. **SQL Syntax**: Checks for proper SQL structure and syntax
4. **Migration Consistency**: Ensures migrations follow best practices

## How Validation Works

### 1. Migration File Parsing

The validator scans all `.sql` files in the `migrations/` directory and:

- Extracts `CREATE TABLE` statements
- Identifies foreign key declarations
- Tracks index creation statements
- Maps table dependencies

### 2. Foreign Key Ordering Validation

**Rule**: Referenced tables must be created before tables that reference them.

**Example - ✅ Valid**:
```sql
-- 001_create_users.sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    name VARCHAR(255)
);

-- 002_create_posts.sql
CREATE TABLE posts (
    id INTEGER PRIMARY KEY,
    user_id INTEGER,
    title VARCHAR(255),
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

**Example - ❌ Invalid**:
```sql
-- 001_create_posts.sql
CREATE TABLE posts (
    id INTEGER PRIMARY KEY,
    user_id INTEGER,
    title VARCHAR(255),
    FOREIGN KEY (user_id) REFERENCES users(id)  -- Error: users table doesn't exist yet
);

-- 002_create_users.sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    name VARCHAR(255)
);
```

### 3. Index Validation

**Rule**: All foreign key columns must have associated indexes for performance.

**Example - ✅ Valid**:
```sql
CREATE TABLE posts (
    id INTEGER PRIMARY KEY,
    user_id INTEGER,
    title VARCHAR(255),
    FOREIGN KEY (user_id) REFERENCES users(id),
    INDEX idx_posts_user_id (user_id)  -- Index on foreign key
);
```

**Example - ❌ Invalid**:
```sql
CREATE TABLE posts (
    id INTEGER PRIMARY KEY,
    user_id INTEGER,
    title VARCHAR(255),
    FOREIGN KEY (user_id) REFERENCES users(id)
    -- Missing index on user_id
);
```

## How to Run Validator Locally

### Prerequisites

- Python 3.8+
- Required packages: `structlog`

### Installation

```bash
# Install dependencies
pip install structlog

# Navigate to infrastructure/database directory
cd infrastructure/database
```

### Basic Usage

```bash
# Validate migrations in default directory (migrations/)
python tools/schema_validator.py

# Validate migrations in specific directory
python tools/schema_validator.py path/to/migrations/

# Enable verbose logging
python tools/schema_validator.py --verbose
```

### Example Output

```
🔍 Running schema validation...

❌ Schema Validation Errors:
  migrations/002_create_posts.sql:15
    missing_referenced_table: Table 'posts' references non-existent table 'users'

  migrations/003_create_comments.sql:20
    missing_foreign_key_index: Foreign key column 'post_id' in table 'comments' lacks an index

📊 Validation Summary:
  Tables found: 3
  Errors: 2
  Warnings: 0
```

## CI Failure Triggers

The CI pipeline will fail if any of the following conditions are met:

### 1. Foreign Key Ordering Violations

- **Error**: Referenced table is defined after referencing table
- **CI Action**: Fail pull request with detailed error report
- **Example**: Table `posts` references `users` but `users` is created in a later migration

### 2. Missing Index Violations

- **Error**: Foreign key column lacks associated index
- **CI Action**: Fail pull request with detailed error report
- **Example**: Foreign key column `user_id` has no index

### 3. SQL Syntax Errors

- **Error**: Invalid SQL syntax in migration files
- **CI Action**: Fail pull request with syntax error details
- **Example**: Malformed CREATE TABLE statement

### 4. Missing Referenced Tables

- **Error**: Foreign key references non-existent table
- **CI Action**: Fail pull request with missing table details
- **Example**: Foreign key references `users` table that doesn't exist

## Data Integrity Constraints

### NOT NULL and CHECK Constraints

The database enforces comprehensive data integrity through NOT NULL and CHECK constraints:

#### Key Constraint Categories

1. **Required Fields**: Email, username, password_hash, names, content fields
2. **Status Fields**: Role, status, type with finite domain values
3. **Timestamp Fields**: Created_at, updated_at with future date validation
4. **Format Validation**: Email format, username format, password hash format
5. **Domain Validation**: Material types, system types, severity levels

#### Constraint Migration Process

1. **Audit Phase**: Run `tools/audit_constraints.py` to identify candidates
2. **Backfill Phase**: Execute `scripts/backfill_nulls.sql` to safely update NULL data
3. **Migration Phase**: Apply `migrations/006_add_constraints.sql` to add constraints
4. **Validation Phase**: Run `tests/test_constraints.py` to verify enforcement

#### Example Constraint Enforcement

## Table Partitioning

### Performance Optimization for Large Tables

The database implements table partitioning to improve performance and manageability of large audit/log/history tables:

#### Partitioning Strategy

1. **Range Partitioning by Date**: Monthly partitions for time-series data
2. **Target Tables**: audit_logs, object_history, slow_query_log, chat_messages
3. **Partition Keys**: created_at, changed_at, timestamp
4. **Retention Policy**: 6-12 months based on table type

#### Partitioning Benefits

- **Query Performance**: 60-90% improvement for time-based queries
- **Maintenance**: Easier cleanup of old data
- **Parallel Processing**: Better query execution across partitions
- **Index Efficiency**: Reduced index maintenance overhead

#### Partitioning Tools

1. **Analysis Tool**: `tools/analyze_partitioning.py` - Identifies partitioning candidates
2. **Migration**: `migrations/007_add_partitioning.sql` - Implements partitioning
3. **Benchmarking**: `tools/benchmark_partitioning.py` - Measures performance improvements
4. **Maintenance**: `tools/maintain_partitions.py` - Automated partition management

#### Quick Start

```bash
# 1. Analyze tables for partitioning
python tools/analyze_partitioning.py --database-url postgresql://localhost/arxos_db

# 2. Apply partitioning migration
psql -d arxos_db -f migrations/007_add_partitioning.sql

# 3. Benchmark performance improvements
python tools/benchmark_partitioning.py --database-url postgresql://localhost/arxos_db

# 4. Set up automated maintenance
python tools/maintain_partitions.py --database-url postgresql://localhost/arxos_db
```

#### Partition Maintenance

- **Monthly Creation**: New partitions created 3 months ahead
- **Retention Cleanup**: Old partitions dropped after retention period
- **Automated Validation**: Partition integrity checks
- **Performance Monitoring**: Query performance tracking

#### Example Partitioned Query

```sql
-- Query automatically uses appropriate partition
SELECT * FROM audit_logs_partitioned 
WHERE created_at >= NOW() - INTERVAL '7 days'
ORDER BY created_at DESC;
```

#### Migration Safety

- **Rollback Function**: `rollback_partitioning_migration()` for safe reversal
- **Data Preservation**: Existing data migrated to partitioned structure
- **Index Optimization**: Performance indexes on partitioned tables
- **Foreign Key Support**: Maintains referential integrity

```sql
-- NOT NULL constraint
ALTER TABLE users ALTER COLUMN email SET NOT NULL;

-- CHECK constraint for finite domain
ALTER TABLE users ADD CONSTRAINT chk_users_role 
CHECK (role IN ('user', 'admin', 'manager', 'viewer'));

-- Format validation
ALTER TABLE users ADD CONSTRAINT chk_users_email_format 
CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$');
```

### Performance Monitoring

The database includes comprehensive performance monitoring:

#### Slow Query Logging

- **Configuration**: `postgresql.conf` with 500ms threshold
- **Parsing**: `tools/parse_slow_queries.py` for analysis
- **Storage**: `slow_query_log` table with metrics
- **Review**: `tools/weekly_slow_query_review.py` for automated analysis

#### Performance Tools

- **Query Analysis**: Parse and rank slow queries by execution time
- **Trend Analysis**: Track query performance over time
- **Automated Reviews**: Weekly analysis with email notifications
- **Database Integration**: Store metrics for historical analysis

## Migration Best Practices

### 1. File Naming Convention

Use descriptive, ordered filenames:

```
migrations/
├── 001_create_users.sql
├── 002_create_posts.sql
├── 003_create_comments.sql
├── 004_add_indexes.sql
├── 005_create_slow_query_log.sql
└── 006_add_constraints.sql
```

### 2. Table Creation Order

Create tables in dependency order:

1. **Independent tables first** (users, categories)
2. **Dependent tables second** (posts, comments)
3. **Junction tables last** (user_roles, post_tags)
4. **Monitoring tables** (audit_logs, slow_query_log)

### 3. Index Strategy

Always add indexes for:

- **Primary keys** (automatic in most databases)
- **Foreign key columns** (required by validator)
- **Frequently queried columns**
- **Unique constraints**
- **Constraint columns** (for CHECK constraint performance)

### 4. Foreign Key Naming

Use descriptive foreign key names:

```sql
-- ✅ Good
FOREIGN KEY (user_id) REFERENCES users(id)
FOREIGN KEY (post_id) REFERENCES posts(id)

-- ❌ Avoid
FOREIGN KEY (uid) REFERENCES u(id)
```

## Integration with CI/CD

### GitHub Actions Workflow

The schema validator is automatically run on:

- **Pull Requests**: When migration files are modified
- **Main Branch**: On pushes to main/develop branches
- **Path Changes**: Only when relevant files are modified

### Workflow Steps

1. **Checkout**: Clone the repository
2. **Setup Python**: Install Python 3.11
3. **Install Dependencies**: Install required packages
4. **Run Validation**: Execute schema validator
5. **Report Results**: Upload validation artifacts
6. **PR Comments**: Add comments to pull requests

### Failure Handling

When validation fails:

1. **Build Fails**: CI pipeline stops with error
2. **PR Comment**: Detailed error message added to PR
3. **Artifacts**: Validation results uploaded for review
4. **Block Merge**: PR cannot be merged until fixed

## Troubleshooting

### Common Issues

#### 1. "Missing Referenced Table" Error

**Problem**: Foreign key references table that doesn't exist yet.

**Solution**: Reorder migrations or create the referenced table first.

```sql
-- Fix: Create users table first
CREATE TABLE users (id INTEGER PRIMARY KEY);
CREATE TABLE posts (
    user_id INTEGER,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

#### 2. "Missing Foreign Key Index" Error

**Problem**: Foreign key column has no index.

**Solution**: Add an index to the foreign key column.

```sql
-- Fix: Add index
CREATE TABLE posts (
    user_id INTEGER,
    FOREIGN KEY (user_id) REFERENCES users(id),
    INDEX idx_posts_user_id (user_id)  -- Add this line
);
```

#### 3. "Parse Error" in Migration File

**Problem**: Invalid SQL syntax in migration file.

**Solution**: Check SQL syntax and fix any syntax errors.

### Debugging Tips

1. **Run Locally**: Test migrations before pushing
2. **Check Order**: Ensure tables are created in dependency order
3. **Add Indexes**: Always index foreign key columns
4. **Review Logs**: Check CI logs for detailed error messages

## Advanced Configuration

### Custom Validation Rules

The validator can be extended with custom rules by modifying `tools/schema_validator.py`:

```python
def custom_validation_rule(self):
    """Add custom validation logic here."""
    pass
```

### Excluding Files

To exclude specific migration files from validation, modify the file pattern in the validator:

```python
# Exclude test files
migration_files = [f for f in self.migrations_dir.glob("*.sql") 
                  if not f.name.startswith("test_")]
```

### Custom Error Messages

Customize error messages by modifying the `ValidationError` class:

```python
@dataclass
class ValidationError:
    error_type: str
    message: str
    file_path: str
    line_number: int
    severity: str = "error"
    custom_field: str = None
```

## Contributing

### Adding New Validation Rules

1. **Identify Pattern**: Determine the SQL pattern to validate
2. **Add Regex**: Create regex pattern in `SchemaValidator.__init__()`
3. **Add Logic**: Implement validation logic in appropriate method
4. **Add Tests**: Create test cases for the new rule
5. **Update Docs**: Document the new validation rule

### Testing

Run tests for the schema validator:

```bash
# Run validator tests
python -m pytest tests/test_schema_validator.py

# Run with coverage
python -m pytest tests/test_schema_validator.py --cov=tools
```

## Support

For issues with the schema validator:

1. **Check Logs**: Review CI/CD logs for detailed error messages
2. **Run Locally**: Test migrations locally before pushing
3. **Review Rules**: Ensure migrations follow validation rules
4. **Open Issue**: Create GitHub issue for bugs or feature requests

## Performance Monitoring

### Slow Query Logging System

The Arxos database infrastructure includes a comprehensive slow query logging system for performance monitoring and optimization:

#### Components

- **PostgreSQL Configuration** (`postgresql.conf`): Enables structured slow query logging
- **Slow Query Parser** (`tools/parse_slow_queries.py`): Analyzes query patterns and performance
- **Database Storage** (`migrations/003_create_slow_query_log.sql`): Stores metrics for trend analysis
- **Weekly Review** (`tools/weekly_slow_query_review.py`): Automated performance analysis
- **CI/CD Integration** (`.github/workflows/weekly_slow_query_review.yml`): Automated weekly execution

#### Quick Start

```bash
# Enable slow query logging
sudo cp postgresql.conf /etc/postgresql/15/main/postgresql.conf
sudo systemctl restart postgresql

# Install dependencies
pip install -r requirements.txt

# Run database migration
psql -d your_database -f migrations/003_create_slow_query_log.sql

# Test parser
python tools/parse_slow_queries.py pg_log --output-format json

# Run weekly review
python tools/weekly_slow_query_review.py --verbose
```

#### Features

- **Structured Logging**: Follows Arxos logging standards with `structlog`
- **Performance Analysis**: Identifies critical and warning performance issues
- **Automated Alerts**: Email notifications for critical queries
- **Trend Tracking**: Historical performance data for trend analysis
- **Dashboard Integration**: Provides metrics for monitoring dashboards

For detailed documentation, see [SLOW_QUERY_LOGGING_GUIDE.md](SLOW_QUERY_LOGGING_GUIDE.md).

## Version History

- **v1.0.0**: Initial release with foreign key ordering and index validation
- **v1.1.0**: Added SQL syntax validation and improved error reporting
- **v1.2.0**: Enhanced CI integration with PR comments and artifacts
- **v1.3.0**: Added comprehensive slow query logging system for performance monitoring
