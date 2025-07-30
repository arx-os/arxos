# Arxos Database Infrastructure

## Overview

The Arxos Database Infrastructure provides comprehensive tools for database schema management, validation, and data integrity enforcement using **PostgreSQL with PostGIS** as the standard database technology. This includes schema validation, constraint management, and performance monitoring tools.

## 🎯 **Database Technology Standard**

### **Primary Database**: PostgreSQL with PostGIS
- **PostgreSQL**: Primary relational database for all Arxos applications
- **PostGIS**: Spatial database extension for CAD and BIM data
- **Migration Strategy**: All existing databases will be migrated to PostgreSQL/PostGIS
- **Development Standard**: All new development uses PostgreSQL/PostGIS exclusively

### **Database Architecture**
```
Arxos Database Stack
├── PostgreSQL 15+ (Primary Database)
│   ├── Core Application Data
│   ├── User Management
│   ├── CAD/BIM Metadata
│   └── System Configuration
├── PostGIS Extension
│   ├── Spatial Data Storage
│   ├── Geometric Calculations
│   ├── CAD Coordinate Systems
│   └── BIM Spatial Relationships
└── Redis (Cache Layer)
    ├── Session Management
    ├── Performance Caching
    └── Real-time Data
```

## Components

### 1. Schema Validator
Validates SQL migration files to ensure proper database schema structure and prevent common issues that can cause deployment failures.

### 2. Constraint Management
Enforces data integrity through NOT NULL and CHECK constraints with comprehensive audit tools and safe migration strategies.

### 3. Performance Monitoring
Includes slow query logging and performance analysis tools for database optimization.

### 4. Spatial Data Management
PostGIS integration for CAD and BIM spatial data with geometric calculations and spatial indexing.

## Schema Validator Purpose

The schema validator prevents invalid migrations by checking:

1. **Foreign Key Ordering**: Ensures referenced tables are created before referencing tables
2. **Index Presence**: Validates that foreign key columns have associated indexes for performance
3. **SQL Syntax**: Checks for proper SQL structure and syntax
4. **Migration Consistency**: Ensures migrations follow best practices
5. **PostGIS Integration**: Validates spatial data types and PostGIS extensions

## How Validation Works

### 1. Migration File Parsing

The validator scans all `.sql` files in the `migrations/` directory and:

- Extracts `CREATE TABLE` statements
- Identifies foreign key declarations
- Tracks index creation statements
- Maps table dependencies
- Validates PostGIS spatial data types

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

### 4. PostGIS Spatial Data Validation

**Rule**: Spatial data must use proper PostGIS data types and spatial indexing.

**Example - ✅ Valid**:
```sql
-- Enable PostGIS extension
CREATE EXTENSION IF NOT EXISTS postgis;

-- Create spatial table
CREATE TABLE cad_objects (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255),
    geometry GEOMETRY(POINT, 4326),  -- Proper PostGIS geometry type
    properties JSONB
);

-- Create spatial index
CREATE INDEX idx_cad_objects_geometry ON cad_objects USING GIST (geometry);
```

**Example - ❌ Invalid**:
```sql
CREATE TABLE cad_objects (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255),
    geometry TEXT,  -- Should use PostGIS geometry type
    properties JSONB
);
```

## Database Migration Strategy

### **Phase 1: PostgreSQL Standardization**
- ✅ **Establish PostgreSQL/PostGIS** as the standard database
- ✅ **Update all documentation** to reflect PostgreSQL/PostGIS
- ✅ **Migrate existing data** to PostgreSQL/PostGIS
- ✅ **Update all applications** to use PostgreSQL/PostGIS

### **Phase 2: Spatial Data Implementation**
- ✅ **Implement PostGIS extensions** for spatial data
- ✅ **Create spatial indexes** for CAD/BIM data
- ✅ **Implement geometric calculations** for CAD operations
- ✅ **Add spatial query optimization** for performance

### **Phase 3: Advanced Features**
- ✅ **Implement spatial constraints** for CAD data integrity
- ✅ **Add spatial performance monitoring** for PostGIS operations
- ✅ **Create spatial data validation** tools
- ✅ **Implement spatial backup and recovery** procedures

## Development Standards

### **Database Technology**
- **Primary**: PostgreSQL 15+ with PostGIS 3.0+
- **Cache**: Redis 7.0+
- **Migration Tool**: Alembic with PostgreSQL support
- **Spatial Data**: PostGIS for all CAD/BIM spatial data

### **Connection Standards**
- **Host**: PostgreSQL server with PostGIS extension
- **Port**: 5432 (PostgreSQL), 6379 (Redis)
- **Authentication**: Role-based access with SSL
- **Connection Pooling**: PgBouncer for production

### **Data Types**
- **Spatial Data**: PostGIS GEOMETRY and GEOGRAPHY types
- **JSON Data**: JSONB for flexible schema
- **Numeric Data**: DECIMAL for precision calculations
- **Text Data**: VARCHAR with proper indexing

---

**Last Updated**: December 2024  
**Version**: 2.0.0  
**Status**: PostgreSQL/PostGIS Standardization
