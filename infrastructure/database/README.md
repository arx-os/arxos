# Arxos Database Schema Validator

## Overview

The Arxos Database Schema Validator is an automated tool that validates SQL migration files to ensure proper database schema structure and prevent common issues that can cause deployment failures.

## Purpose

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

## Migration Best Practices

### 1. File Naming Convention

Use descriptive, ordered filenames:

```
migrations/
├── 001_create_users.sql
├── 002_create_posts.sql
├── 003_create_comments.sql
└── 004_add_indexes.sql
```

### 2. Table Creation Order

Create tables in dependency order:

1. **Independent tables first** (users, categories)
2. **Dependent tables second** (posts, comments)
3. **Junction tables last** (user_roles, post_tags)

### 3. Index Strategy

Always add indexes for:

- **Primary keys** (automatic in most databases)
- **Foreign key columns** (required by validator)
- **Frequently queried columns**
- **Unique constraints**

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

## Version History

- **v1.0.0**: Initial release with foreign key ordering and index validation
- **v1.1.0**: Added SQL syntax validation and improved error reporting
- **v1.2.0**: Enhanced CI integration with PR comments and artifacts
