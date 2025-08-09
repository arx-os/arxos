# Arxos Platform Schema Validation Guide

## Overview

The Arxos Platform includes automated schema validation to ensure SQL migrations follow best practices for foreign key ordering and indexing. This system prevents deployment issues and maintains database performance.

## Validation Rules

### 1. Foreign Key Order Validation

**Rule**: Foreign keys must reference tables that are created before the referencing table.

**Why**: Prevents migration failures due to forward references.

**Example - ✅ Correct**:
```sql
-- Referenced table first
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL
);

-- Referencing table second
CREATE TABLE projects (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    name VARCHAR(255) NOT NULL
);
```

**Example - ❌ Incorrect**:
```sql
-- Referencing table first (will fail)
CREATE TABLE projects (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),  -- users table not created yet
    name VARCHAR(255) NOT NULL
);

-- Referenced table second
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL
);
```

### 2. Foreign Key Index Validation

**Rule**: Every foreign key column must have an index.

**Why**: Optimizes join performance and enforces best practices.

**Example - ✅ Correct**:
```sql
CREATE TABLE projects (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    name VARCHAR(255) NOT NULL
);

-- Index on foreign key
CREATE INDEX idx_projects_user_id ON projects(user_id);
```

**Example - ❌ Incorrect**:
```sql
CREATE TABLE projects (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),  -- No index on user_id
    name VARCHAR(255) NOT NULL
);
```

## Usage

### Local Validation

```bash
# Validate foreign key order
python scripts/validate_fk_order.py arx-database/*.sql

# Validate foreign key indexes
python scripts/validate_fk_indexes.py arx-database/*.sql

# Generate fixes for missing indexes
python scripts/validate_fk_indexes.py arx-database/*.sql --generate-fixes

# Verbose output
python scripts/validate_fk_order.py arx-database/*.sql --verbose

# Save detailed report
python scripts/validate_fk_order.py arx-database/*.sql --output report.json
```

### CI/CD Integration

The schema validation runs automatically on:
- **Push to main/develop branches**
- **Pull requests** that modify SQL files
- **Path changes** to `arx-database/`, `scripts/validate_*.py`, or `.github/workflows/schema_ci.yml`

## Validation Scripts

### `scripts/validate_fk_order.py`

**Purpose**: Validates foreign key declaration order.

**Features**:
- Parses SQL files for CREATE TABLE statements
- Builds dependency graph of table relationships
- Detects circular dependencies
- Generates optimal table creation order
- Reports forward references and cycles

**Output**:
```
✅ Schema validation PASSED

📊 SUMMARY:
  • Tables found: 15
  • Dependencies: 12
  • Errors: 0
  • Warnings: 0
```

### `scripts/validate_fk_indexes.py`

**Purpose**: Validates that foreign keys have proper indexes.

**Features**:
- Parses CREATE INDEX statements
- Identifies PRIMARY KEY and UNIQUE constraints
- Checks foreign key column coverage
- Generates CREATE INDEX recommendations
- Reports unused indexes

**Output**:
```
✅ Index validation PASSED

📊 SUMMARY:
  • Foreign keys found: 8
  • Indexes found: 12
  • Missing indexes: 0
  • Index coverage: 100.0%
  • Unused indexes: 2
```

## Best Practices

### 1. Table Creation Order

**Recommended Order**:
1. **Independent tables** (no foreign keys)
2. **Referenced tables** (referenced by others)
3. **Dependent tables** (have foreign keys)

**Example**:
```sql
-- 1. Independent tables
CREATE TABLE users (...);
CREATE TABLE categories (...);

-- 2. Referenced tables
CREATE TABLE buildings (
    id SERIAL PRIMARY KEY,
    owner_id INTEGER REFERENCES users(id)
);

-- 3. Dependent tables
CREATE TABLE floors (
    id SERIAL PRIMARY KEY,
    building_id INTEGER REFERENCES buildings(id)
);
```

### 2. Index Naming Convention

**Format**: `idx_{table_name}_{column_name}`

**Examples**:
```sql
CREATE INDEX idx_projects_user_id ON projects(user_id);
CREATE INDEX idx_buildings_owner_id ON buildings(owner_id);
CREATE INDEX idx_floors_building_id ON floors(building_id);
```

### 3. Composite Indexes

**For multiple foreign keys**:
```sql
CREATE INDEX idx_table_fk1_fk2 ON table(fk1, fk2);
```

### 4. Performance Considerations

**Index Types**:
- **B-tree**: Default for most cases
- **Hash**: For equality comparisons only
- **GIN**: For array columns
- **GiST**: For geometric data

**Example**:
```sql
-- Spatial index for geometry columns
CREATE INDEX idx_buildings_geom ON buildings USING GIST (geom);
```

## Troubleshooting

### Common Issues

#### 1. Forward Reference Error
```
❌ Forward reference: Table 'projects' references 'users' which is defined later
```

**Solution**: Reorder table creation so referenced tables come first.

#### 2. Missing Index Error
```
❌ Missing index on foreign key 'user_id' in table 'projects'
```

**Solution**: Add index for the foreign key column:
```sql
CREATE INDEX idx_projects_user_id ON projects(user_id);
```

#### 3. Circular Dependency Error
```
❌ Circular dependency detected: users -> projects -> users
```

**Solution**: Restructure schema to eliminate circular references.

### Debugging Commands

```bash
# Show dependency graph
python scripts/validate_fk_order.py arx-database/*.sql --show-graph

# Show optimal table order
python scripts/validate_fk_order.py arx-database/*.sql --show-order

# Generate fixes for missing indexes
python scripts/validate_fk_indexes.py arx-database/*.sql --generate-fixes

# Save detailed report
python scripts/validate_fk_order.py arx-database/*.sql --output fk_report.json
python scripts/validate_fk_indexes.py arx-database/*.sql --output index_report.json
```

## CI/CD Integration

### GitHub Actions Workflow

The `.github/workflows/schema_ci.yml` workflow:

1. **Triggers** on SQL file changes
2. **Validates** foreign key order and indexes
3. **Generates** detailed reports
4. **Comments** on PRs with results
5. **Fails** build on violations
6. **Uploads** artifacts for review

### Workflow Steps

1. **Find SQL Files**: Locates all `.sql` files in `arx-database/`
2. **Validate FK Order**: Checks table creation order
3. **Validate FK Indexes**: Ensures proper indexing
4. **Generate Report**: Creates detailed validation report
5. **Comment on PR**: Posts results to pull request
6. **Fail on Errors**: Stops deployment on violations

### Artifacts

The workflow generates:
- `schema-validation-report.md`: Detailed validation report
- `performance_report.json`: Index coverage analysis
- PR comments with validation results

## Performance Impact

### Index Overhead
- **Storage**: ~10-20% additional space
- **Write Performance**: Slight overhead on INSERT/UPDATE
- **Read Performance**: Significant improvement on JOINs

### Recommendations
- **Monitor** query performance after adding indexes
- **Test** with realistic data volumes
- **Consider** dropping unused indexes

## Migration Guidelines

### Adding New Tables

1. **Check dependencies** before creating table
2. **Add indexes** for all foreign keys
3. **Test locally** before committing
4. **Follow naming conventions**

### Modifying Existing Tables

1. **Add foreign keys** with proper indexes
2. **Update existing data** if needed
3. **Test migration** on staging
4. **Monitor performance** after deployment

## Monitoring and Maintenance

### Regular Tasks

1. **Weekly**: Review validation reports
2. **Monthly**: Analyze index usage
3. **Quarterly**: Review schema performance
4. **Annually**: Update validation rules

### Performance Monitoring

```sql
-- Check index usage
SELECT schemaname, tablename, indexname, idx_scan, idx_tup_read, idx_tup_fetch
FROM pg_stat_user_indexes
ORDER BY idx_scan DESC;

-- Check foreign key performance
SELECT
    tc.table_name,
    kcu.column_name,
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name
FROM information_schema.table_constraints AS tc
JOIN information_schema.key_column_usage AS kcu
    ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage AS ccu
    ON ccu.constraint_name = tc.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY';
```

## Support and Resources

### Documentation
- [PostgreSQL Foreign Key Documentation](https://www.postgresql.org/docs/current/ddl-constraints.html)
- [PostgreSQL Index Documentation](https://www.postgresql.org/docs/current/indexes.html)

### Tools
- **pgAdmin**: GUI for database management
- **psql**: Command-line interface
- **pg_stat_statements**: Query performance monitoring

### Team Contacts
- **Database Team**: db-team@arxos.com
- **DevOps Team**: devops@arxos.com
- **Security Team**: security@arxos.com

---

*Last updated: 2024-01-15*
*Version: 1.0*
