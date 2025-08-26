# Arxos Query Command System

## Overview

The Arxos Query Command System provides a powerful interface for executing AQL (Arxos Query Language) queries against building infrastructure data. This system enables power users to interact with ArxObjects using familiar SQL-like syntax with building-specific extensions.

## Features

### 🎯 **Core Query Commands**
- **`arx query select`** - Execute SELECT queries with comprehensive formatting
- **`arx query update`** - Update ArxObject properties
- **`arx query validate`** - Mark objects as field-validated
- **`arx query history`** - View object version history
- **`arx query diff`** - Compare object versions

### 🎨 **Multiple Output Formats**
- **Table** - Formatted table with alignment and headers
- **JSON** - Structured JSON output for programmatic use
- **CSV** - Comma-separated values for spreadsheet import
- **ASCII-BIM** - Spatial visualization for building objects
- **Summary** - Concise result overview

### ⚡ **Enhanced Features**
- **Real-time Results** - Live data with watch integration
- **Spatial Queries** - Location-based object finding
- **Hierarchical Navigation** - Building structure awareness
- **Performance Monitoring** - Query execution metrics
- **Error Handling** - Comprehensive error messages and suggestions

## Usage Examples

### Basic SELECT Queries

```bash
# Query all objects in a building
arx query select "* FROM building:hq"

# Query specific object types
arx query select "id, type, confidence FROM building:* WHERE type = 'wall'"

# Query with confidence filtering
arx query select "* FROM building:* WHERE confidence < 0.7"

# Query specific building areas
arx query select "* FROM building:hq:floor:3 WHERE status = 'active'"
```

### Advanced Queries

```bash
# Spatial queries
arx query select "* FROM building:* WHERE geometry NEAR '100,200,50'"

# Relationship queries
arx query select "* FROM building:* WHERE connected_to = 'hvac_system_01'"

# Time-based queries
arx query select "* FROM building:* WHERE updated_at > '2024-01-01'"

# Complex filtering
arx query select "id, type, location FROM building:* WHERE type IN ('wall', 'door') AND confidence > 0.8"
```

### Output Formatting

```bash
# Table format (default)
arx query select "* FROM building:* WHERE type = 'wall'" --format=table

# JSON format for API integration
arx query select "* FROM building:* WHERE type = 'wall'" --format=json

# CSV format for spreadsheet analysis
arx query select "* FROM building:* WHERE type = 'wall'" --format=csv

# ASCII-BIM format for spatial visualization
arx query select "* FROM building:* WHERE type = 'wall'" --format=ascii-bim

# Summary format for quick overview
arx query select "* FROM building:* WHERE type = 'wall'" --format=summary
```

### Query Options

```bash
# Limit results
arx query select "* FROM building:* WHERE type = 'wall'" --limit=10

# Pagination
arx query select "* FROM building:* WHERE type = 'wall'" --offset=20 --limit=10

# Show execution details
arx query select "* FROM building:* WHERE type = 'wall'" --show-sql --explain

# Custom styling
arx query select "* FROM building:* WHERE type = 'wall'" --style=compact --max-width=80
```

## Command Reference

### `arx query select`

Execute SELECT queries with comprehensive formatting options.

**Syntax:**
```bash
arx query select [query] [options]
```

**Options:**
- `--format, -f` - Output format (table|json|csv|ascii-bim|summary)
- `--style, -s` - Display style (default|compact|detailed)
- `--limit, -l` - Limit number of results (default: 100)
- `--offset, -o` - Offset for pagination (default: 0)
- `--show-sql` - Show generated SQL query
- `--explain` - Show query execution plan
- `--output, -O` - Output to file (default: stdout)
- `--pagination` - Enable pagination (default: true)
- `--highlight` - Enable syntax highlighting (default: true)
- `--max-width` - Maximum display width (default: 120)

### `arx query update`

Update ArxObject properties.

**Syntax:**
```bash
arx query update [query]
```

**Examples:**
```bash
# Update confidence score
arx query update "wall_123 SET confidence = 0.95"

# Update multiple properties
arx query update "hvac_01 SET status = 'maintenance', priority = 'high'"
```

### `arx query validate`

Mark objects as field-validated with evidence.

**Syntax:**
```bash
arx query validate [object_id] [options]
```

**Options:**
- `--photo` - Photo evidence file path
- `--notes` - Validation notes
- `--confidence` - Confidence score (0.0-1.0)
- `--validator` - Validator name/ID

**Examples:**
```bash
# Basic validation
arx query validate wall_123

# Validation with evidence
arx query validate wall_123 --photo=wall.jpg --notes="Verified on-site" --confidence=0.95
```

### `arx query history`

View object version history.

**Syntax:**
```bash
arx query history [object_id] [options]
```

**Options:**
- `--format` - Output format (table|json|csv)
- `--limit` - Number of history entries to show
- `--since` - Show changes since date

**Examples:**
```bash
# View full history
arx query history wall_123

# Recent changes only
arx query history wall_123 --limit=5 --since=2024-01-01
```

### `arx query diff`

Compare object versions.

**Syntax:**
```bash
arx query diff [object_id] [options]
```

**Options:**
- `--from` - Start version/date
- `--to` - End version/date
- `--format` - Output format (table|json|csv)
- `--detailed` - Show detailed differences

**Examples:**
```bash
# Compare versions
arx query diff wall_123 --from=2024-01-01 --to=2024-01-15

# Compare specific versions
arx query diff wall_123 --from=v1.0 --to=v1.1
```

## AQL Query Language

### Basic Syntax

AQL follows SQL-like syntax with building-specific extensions:

```sql
SELECT [fields] FROM [target] WHERE [conditions] ORDER BY [field] LIMIT [number]
```

### Target Syntax

Targets use hierarchical building notation:

```sql
building:building_name:floor:floor_number:area:area_name
```

**Examples:**
- `building:*` - All buildings
- `building:hq` - Specific building
- `building:hq:floor:3` - Specific floor
- `building:hq:floor:3:room:*` - All rooms on floor 3

### Field Selection

```sql
-- All fields
SELECT * FROM building:*

-- Specific fields
SELECT id, type, confidence FROM building:*

-- Calculated fields
SELECT id, type, confidence * 100 as confidence_percent FROM building:*
```

### WHERE Conditions

```sql
-- Basic comparisons
WHERE type = 'wall'
WHERE confidence > 0.8
WHERE status IN ('active', 'maintenance')

-- Spatial queries
WHERE geometry NEAR '100,200,50'
WHERE location WITHIN 'boundary_polygon'

-- Relationship queries
WHERE connected_to = 'hvac_system_01'
WHERE parent = 'floor_3'

-- Time-based queries
WHERE created_at > '2024-01-01'
WHERE updated_at BETWEEN '2024-01-01' AND '2024-01-31'
```

### Advanced Features

#### Spatial Operators
- `NEAR` - Find objects within distance
- `WITHIN` - Objects inside boundary
- `INTERSECTS` - Objects intersecting geometry
- `ADJACENT` - Objects touching or adjacent

#### Relationship Operators
- `CONNECTED_TO` - Direct connections
- `PARENT_OF` - Parent-child relationships
- `DEPENDS_ON` - Dependency relationships
- `PART_OF` - Component relationships

#### Time Travel
```sql
-- Query historical state
SELECT * FROM building:* AS OF '2024-01-01'

-- Query version range
SELECT * FROM building:* BETWEEN '2024-01-01' AND '2024-01-31'

-- Query specific version
SELECT * FROM building:* VERSION 5
```

## Integration with Arxos CLI

### Navigation Context

Query commands respect the current navigation context:

```bash
# Navigate to specific building area
arx cd building:hq:floor:3

# Query objects in current location
arx query select "* FROM . WHERE type = 'wall'"

# Query parent building
arx query select "* FROM .. WHERE type = 'hvac'"
```

### Real-time Integration

```bash
# Watch for changes and query in real-time
arx watch --arxobject &
arx query select "* FROM . WHERE last_modified > NOW() - INTERVAL '1 hour'"
```

### Index Integration

Queries automatically use the ArxObject indexer for fast results:

```bash
# Fast queries using cached index
arx query select "* FROM building:* WHERE type = 'wall'"

# Force index rebuild
arx index rebuild
arx query select "* FROM building:* WHERE type = 'wall'"
```

## Performance Optimization

### Query Best Practices

1. **Use Specific Targets** - Query specific building areas instead of entire building
2. **Limit Results** - Use LIMIT clause for large result sets
3. **Index Fields** - Query on indexed fields (id, type, status)
4. **Avoid Wildcards** - Use specific field names instead of `*` when possible
5. **Use Spatial Indexes** - Leverage spatial operators for location-based queries

### Performance Monitoring

```bash
# Show query execution plan
arx query select "* FROM building:* WHERE type = 'wall'" --explain

# Monitor query performance
arx query select "* FROM building:* WHERE type = 'wall'" --show-sql
```

## Error Handling

### Common Error Types

1. **Syntax Errors** - Invalid AQL syntax
2. **Target Errors** - Invalid building targets
3. **Field Errors** - Non-existent fields
4. **Permission Errors** - Insufficient access rights
5. **System Errors** - Database or system issues

### Error Recovery

```bash
# Validate query syntax
arx query select "INVALID QUERY"  # Will show syntax error

# Check target validity
arx query select "* FROM invalid:target"  # Will show target error

# Use help for guidance
arx query select --help
```

## Future Enhancements

### Planned Features

1. **Natural Language Queries** - AI-powered query generation
2. **Query Templates** - Predefined queries for common operations
3. **Advanced Analytics** - Statistical and trend analysis
4. **Machine Learning** - Predictive query suggestions
5. **Collaborative Queries** - Share and collaborate on queries

### Integration Roadmap

1. **Phase 1** - Basic AQL CLI integration ✅
2. **Phase 2** - Enhanced result display ✅
3. **Phase 3** - Real-time query capabilities
4. **Phase 4** - AI-powered query assistance
5. **Phase 5** - Advanced analytics and reporting

## Contributing

### Development Setup

1. **Clone Repository** - `git clone https://github.com/arxos/arxos.git`
2. **Install Dependencies** - `go mod download`
3. **Run Tests** - `go test ./cmd/commands/query/...`
4. **Build CLI** - `go build -o arx ./cmd/commands`

### Testing

```bash
# Run all tests
go test ./cmd/commands/query/...

# Run specific test
go test -v -run TestQueryValidation

# Run with coverage
go test -cover ./cmd/commands/query/...
```

### Code Style

- Follow Go coding standards
- Add tests for new features
- Update documentation for API changes
- Use descriptive variable names
- Add comments for complex logic

## Support

### Getting Help

- **Documentation** - Check this README and related docs
- **Examples** - Review usage examples above
- **Tests** - Examine test files for usage patterns
- **Issues** - Report bugs via GitHub issues

### Common Issues

1. **Import Errors** - Check module configuration
2. **Build Failures** - Verify Go version and dependencies
3. **Query Errors** - Validate AQL syntax and targets
4. **Performance Issues** - Use query optimization techniques

---

**The Arxos Query Command System provides the foundation for powerful building intelligence queries, enabling users to extract insights and manage building infrastructure through an intuitive, SQL-like interface.**
