# Current Database Setup

## Overview

This document describes the current database setup for the Arxos development environment, including the PostgreSQL 17 + PostGIS 3.5.3 installation completed on August 2, 2024.

## Current Configuration

### **Database Stack**
- **PostgreSQL**: 17.5 (Homebrew)
- **PostGIS**: 3.5.3
- **Database Name**: `arxos_db_pg17`
- **User**: `joelpate`
- **Host**: `localhost`
- **Port**: `5432`

### **Installation Method**
- **Package Manager**: Homebrew
- **Installation Date**: August 2, 2024
- **Installation Commands**:
  ```bash
  brew install postgresql@17
  brew install postgis
  brew services start postgresql@17
  createdb arxos_db_pg17
  psql -U joelpate -d arxos_db_pg17 -c "CREATE EXTENSION postgis;"
  ```

## Verification Commands

### **Check PostgreSQL Version**
```bash
psql --version
# Expected: psql (PostgreSQL) 17.5 (Homebrew)
```

### **Check PostGIS Installation**
```bash
psql -U joelpate -d arxos_db_pg17 -c "SELECT PostGIS_Version();"
# Expected: 3.5 USE_GEOS=1 USE_PROJ=1 USE_STATS=1
```

### **Test Spatial Functions**
```bash
psql -U joelpate -d arxos_db_pg17 -c "SELECT ST_AsText(ST_GeomFromText('POINT(0 0)'));"
# Expected: POINT(0 0)
```

### **Check Service Status**
```bash
brew services list | grep postgresql
# Expected: postgresql@17 started
```

## Connection Information

### **Connection String**
```
postgresql://joelpate@localhost:5432/arxos_db_pg17
```

### **Environment Variable**
```bash
export DATABASE_URL="postgresql://joelpate@localhost:5432/arxos_db_pg17"
```

## Service Management

### **Start PostgreSQL**
```bash
brew services start postgresql@17
```

### **Stop PostgreSQL**
```bash
brew services stop postgresql@17
```

### **Restart PostgreSQL**
```bash
brew services restart postgresql@17
```

### **Check Service Status**
```bash
brew services list | grep postgresql
```

## Database Operations

### **Connect to Database**
```bash
psql -U joelpate -d arxos_db_pg17
```

### **List All Databases**
```bash
psql -U joelpate -l
```

### **Create New Database**
```bash
createdb new_database_name
```

### **Drop Database**
```bash
dropdb database_name
```

## PostGIS Operations

### **Enable PostGIS in New Database**
```bash
psql -U joelpate -d database_name -c "CREATE EXTENSION postgis;"
```

### **Check PostGIS Functions**
```bash
psql -U joelpate -d arxos_db_pg17 -c "\dx"
```

### **Test Spatial Query**
```bash
psql -U joelpate -d arxos_db_pg17 -c "
SELECT ST_Distance(
  ST_GeomFromText('POINT(0 0)'),
  ST_GeomFromText('POINT(1 1)')
);"
```

## Troubleshooting

### **Common Issues**

#### **PostGIS Extension Not Available**
```bash
# Check if PostGIS files exist for PostgreSQL 17
find /opt/homebrew/Cellar/postgis -name "*.control" | grep postgis
```

#### **Connection Refused**
```bash
# Check if PostgreSQL is running
brew services list | grep postgresql

# Start if not running
brew services start postgresql@17
```

#### **Permission Denied**
```bash
# Check user permissions
psql -U joelpate -d arxos_db_pg17 -c "\du"
```

## Migration from Previous Versions

### **From PostgreSQL 14/15**
This setup was migrated from PostgreSQL 14 and 15 due to PostGIS compatibility issues. The migration process included:

1. **Backup**: Created backup of existing databases
2. **Installation**: Installed PostgreSQL 17 and PostGIS 3.5.3
3. **Database Creation**: Created new database with PostGIS enabled
4. **Cleanup**: Removed old PostgreSQL versions and temporary files

### **Backup Commands Used**
```bash
pg_dump -U joelpate arxos_db_pg14 > backup_$(date +%Y%m%d_%H%M%S).sql
```

## Performance Considerations

### **PostgreSQL 17 Benefits**
- **Improved Performance**: Better query optimization
- **Enhanced Features**: Latest PostgreSQL features
- **Long-term Support**: Extended support timeline
- **Security Updates**: Latest security patches

### **PostGIS 3.5.3 Benefits**
- **Spatial Performance**: Optimized spatial operations
- **Compatibility**: Full compatibility with PostgreSQL 17
- **Feature Rich**: Advanced spatial functions
- **Stability**: Production-ready stability

## Maintenance

### **Regular Maintenance Tasks**
1. **Weekly**: Check for PostgreSQL and PostGIS updates
2. **Monthly**: Review database performance
3. **Quarterly**: Update documentation
4. **Annually**: Comprehensive system review

### **Update Commands**
```bash
# Check for updates
brew outdated | grep postgresql
brew outdated | grep postgis

# Update PostgreSQL and PostGIS
brew upgrade postgresql@17 postgis
```

## Related Documentation

- **[Database Architecture](README.md)**: Overall database design
- **[Migration Guide](migrations.md)**: Database migration procedures
- **[Performance Guide](performance_guide.md)**: Performance optimization
- **[Setup Guide](../../onboarding/LOCAL_SETUP_GUIDE.md)**: Development environment setup

---

*Last Updated: August 2, 2024*
*Setup by: Development Team* 