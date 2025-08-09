# Arxos Database Documentation

## Overview

This directory contains comprehensive documentation for the Arxos database architecture, schema design, migration history, and operational procedures. The documentation is designed to help future developers understand design decisions, constraints, and best practices.

## Documentation Structure

```
arx-docs/database/
├── README.md                    # This file - main documentation index
├── schema/                      # Individual table documentation
│   ├── users.md                # User management table
│   ├── projects.md             # Project organization table
│   ├── buildings.md            # Building information table
│   ├── floors.md               # Floor management table
│   ├── categories.md           # Category classification table
│   ├── rooms.md                # Room spatial data table
│   ├── walls.md                # Wall BIM objects table
│   ├── doors.md                # Door BIM objects table
│   ├── windows.md              # Window BIM objects table
│   ├── devices.md              # Device management table
│   ├── labels.md               # Text labels table
│   ├── zones.md                # Spatial zones table
│   ├── drawings.md             # Drawing management table
│   ├── comments.md             # Comment system table
│   ├── assignments.md          # Task assignments table
│   ├── object_history.md       # Change tracking table
│   ├── audit_logs.md           # Audit logging table
│   ├── user_category_permissions.md # Permission system table
│   ├── chat_messages.md        # Chat functionality table
│   └── catalog_items.md        # Equipment catalog table
├── migrations.md               # Migration history and procedures
├── design_decisions.md         # Architecture and design rationale
├── performance_guide.md        # Performance optimization guide
├── constraints.md              # Data integrity constraints
├── partitioning.md             # Table partitioning strategy
└── operational_guide.md        # Database operations and maintenance
```

## Database Architecture

### **Primary Database**: PostgreSQL with PostGIS
- **PostgreSQL 17**: Primary relational database for all Arxos applications
- **PostGIS 3.5.3**: Spatial database extension for BIM and CAD data
- **Migration Strategy**: All existing databases will be migrated to PostgreSQL 17/PostGIS 3.5.3
- **Development Standard**: All new development uses PostgreSQL 17/PostGIS 3.5.3 exclusively

### Table Categories

#### **Level 1: Base Tables (No Dependencies)**
- `users` - User authentication and management

#### **Level 2: Project Organization**
- `projects` - Project management and organization

#### **Level 3: Building Infrastructure**
- `buildings` - Building information and metadata
- `floors` - Floor management within buildings
- `categories` - Classification system for BIM objects

#### **Level 4: BIM Objects**
- `rooms` - Room spatial data and metadata
- `walls` - Wall BIM objects with spatial geometry
- `doors` - Door BIM objects with spatial geometry
- `windows` - Window BIM objects with spatial geometry
- `devices` - Device management and placement
- `labels` - Text labels and annotations
- `zones` - Spatial zones and areas

#### **Level 5: Collaboration & Audit**
- `comments` - Comment system for objects
- `assignments` - Task assignment and tracking
- `object_history` - Change tracking and versioning
- `audit_logs` - Comprehensive audit logging
- `user_category_permissions` - Permission system
- `chat_messages` - Chat functionality
- `catalog_items` - Equipment catalog management
- `drawings` - Drawing management and storage

### Key Features

#### **Spatial Data Management**
- PostGIS integration for geometric data
- Spatial indexes (GiST) for performance
- Support for complex spatial queries

#### **Performance Optimization**
- Strategic indexing for common query patterns
- Table partitioning for large audit/history tables
- Composite indexes for multi-column queries
- Partial indexes for filtered data

#### **Data Integrity**
- Foreign key constraints for referential integrity
- NOT NULL constraints for required fields
- CHECK constraints for domain validation
- Unique constraints for business rules

#### **Audit and Compliance**
- Comprehensive change tracking
- User activity logging
- Data retention policies
- Compliance-ready audit trails

## Quick Reference

### Database Connection
```bash
# PostgreSQL connection string
postgresql://username:password@localhost/arxos_db_pg17

# Environment variable
export DATABASE_URL="postgresql://username:password@localhost/arxos_db_pg17"
```

### Common Operations

#### **Schema Validation**
```bash
cd arxos/infrastructure/database
python tools/schema_validator.py
```

#### **Migration Management**
```bash
# Apply migrations
alembic upgrade head

# Check status
alembic current

# Rollback
alembic downgrade -1
```

#### **Performance Monitoring**
```bash
# Analyze partitioning candidates
python tools/analyze_partitioning.py

# Benchmark performance
python tools/benchmark_partitioning.py

# Maintain partitions
python tools/maintain_partitions.py
```

#### **Data Integrity**
```bash
# Audit constraints
python tools/audit_constraints.py

# Apply constraints
psql -d arxos_db -f migrations/006_add_constraints.sql
```

## Documentation Standards

### Schema Documentation Format

Each table documentation follows this structure:

1. **Purpose**: Why the table exists and its role in the system
2. **Schema**: Complete table definition with constraints
3. **Relationships**: Foreign key relationships and dependencies
4. **Indexes**: Performance indexes and their rationale
5. **Constraints**: Data integrity constraints and business rules
6. **Usage Patterns**: Common query patterns and optimizations
7. **Migration History**: Key changes and their rationale

### Migration Documentation

- **Version Control**: All migrations are version-controlled
- **Rollback Strategy**: Every migration includes rollback procedures
- **Testing**: Migrations are tested in CI/CD pipeline
- **Documentation**: Changes are documented with rationale

### Performance Documentation

- **Index Strategy**: Rationale for each index
- **Query Patterns**: Common queries and their optimization
- **Partitioning**: Table partitioning strategy and maintenance
- **Monitoring**: Performance monitoring and alerting

## Contributing

### Adding New Tables

1. **Document First**: Create schema documentation before implementation
2. **Follow Hierarchy**: Place tables in appropriate dependency level
3. **Add Indexes**: Include performance indexes for common queries
4. **Add Constraints**: Implement appropriate data integrity constraints
5. **Update Documentation**: Keep documentation synchronized with changes

### Modifying Existing Tables

1. **Review Impact**: Assess impact on dependent tables and queries
2. **Create Migration**: Use Alembic for version-controlled changes
3. **Test Thoroughly**: Test in staging environment before production
4. **Update Documentation**: Update relevant documentation files
5. **Validate**: Run schema validation and performance tests

### Documentation Updates

1. **Keep Current**: Update documentation with schema changes
2. **Include Rationale**: Document design decisions and trade-offs
3. **Add Examples**: Include practical usage examples
4. **Cross-Reference**: Link related documentation sections
5. **Review Regularly**: Periodically review and update documentation

## CI/CD Integration

### Documentation Validation

The CI/CD pipeline includes documentation validation:

- **Schema Sync**: Ensures documentation matches actual schema
- **Migration Documentation**: Validates migration documentation
- **Performance Documentation**: Checks performance guide accuracy
- **Constraint Documentation**: Validates constraint documentation

### Automated Checks

```bash
# Validate documentation sync
python tools/validate_documentation.py

# Check schema documentation
python tools/check_schema_docs.py

# Validate migration docs
python tools/validate_migration_docs.py
```

## Support and Maintenance

### Getting Help

1. **Check Documentation**: Start with relevant documentation files
2. **Review Schema**: Examine table documentation for design rationale
3. **Check Migrations**: Review migration history for context
4. **Performance Guide**: Consult performance optimization guide
5. **Operational Guide**: Review operational procedures

### Maintenance Tasks

- **Monthly**: Review and update performance documentation
- **Quarterly**: Audit and update constraint documentation
- **Semi-annually**: Review and update design decisions
- **Annually**: Comprehensive documentation review and cleanup

## Related Documentation

- **API Documentation**: Application-level database usage
- **Deployment Guide**: Database deployment and configuration
- **Monitoring Guide**: Database monitoring and alerting
- **Security Guide**: Database security and access control
- **Backup Guide**: Database backup and recovery procedures

---

*This documentation is maintained by the Database Team and updated with each schema change. For questions or contributions, please contact the database team.*
