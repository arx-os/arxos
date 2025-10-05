# ArxOS Directory Structure Guide

## Overview

ArxOS uses a clear, organized directory structure that separates application data from build system caches. This guide explains the purpose and location of each directory.

## Directory Structure

### **Application Data Directory: `~/.arxos/`**

The `~/.arxos/` directory contains all ArxOS application data and state:

```
~/.arxos/                           # Main ArxOS application directory
├── cache/                          # Unified cache system
│   ├── l1/                        # L1: In-memory cache (not stored on disk)
│   ├── l2/                        # L2: Local disk cache (persistent)
│   └── l3/                        # L3: Redis cache (when enabled)
├── repositories/                   # Building repositories (Git-like)
│   └── [building-id]/             # Individual building repositories
├── logs/                          # Application logs
├── temp/                          # Temporary files
├── config/                        # User configuration
├── buildings/                     # Building data (legacy, use repositories/)
├── imports/                        # Import staging area
├── exports/                       # Export staging area
├── data/                          # Application data
└── run/                           # Runtime files
```

**Purpose**: ArxOS application state, building data, and user configuration.

### **Build System Cache: `~/.cache/`**

The `~/.cache/` directory contains only build system and development tool caches:

```
~/.cache/                          # System-wide cache (XDG Base Directory)
└── arxos/                         # ArxOS build cache
    ├── go-build/                 # Go compiler cache
    ├── go-mod/                   # Go module cache
    ├── docker/                   # Docker build cache
    └── test-cache/               # Test execution cache
```

**Purpose**: Build system caches, compiler caches, and development tool artifacts.

## Cache Architecture

### **Unified Cache System**

ArxOS implements a **multi-tier caching strategy**:

#### **L1 Cache (In-Memory)**
- **Location**: Memory only (not stored on disk)
- **Purpose**: Fastest access for frequently used data
- **Capacity**: ~10,000 entries
- **TTL**: 5 minutes (short-lived)
- **Use Cases**: 
  - API response caching
  - User session data
  - Real-time TUI data
  - Query results

#### **L2 Cache (Local Disk)**
- **Location**: `~/.arxos/cache/l2/`
- **Purpose**: Persistent cache for medium-term data
- **Capacity**: ~1GB disk space
- **TTL**: 1 hour (medium-lived)
- **Use Cases**:
  - IFC file processing results
  - Building geometry data
  - Spatial queries
  - Configuration templates

#### **L3 Cache (Network/Redis)**
- **Location**: Redis server (when enabled)
- **Purpose**: Shared cache across multiple instances
- **Capacity**: Configurable (typically 10GB+)
- **TTL**: 24 hours (long-lived)
- **Use Cases**:
  - Shared building data
  - Cross-instance synchronization
  - Enterprise deployments

### **Cache Key Strategy**

Cache keys follow a hierarchical naming convention:

```
[type]:[context]:[identifier]

Examples:
- ifc:building:ARXOS-NA-US-CA-LAX-0001:processed
- spatial:query:building:ARXOS-NA-US-CA-LAX-0001:rooms
- api:response:buildings:list
- config:template:local:development
```

## Configuration

### **Cache Configuration**

Cache behavior is configured in `~/.arxos/config/arxos.yaml`:

```yaml
unified_cache:
  l1:
    enabled: true
    max_entries: 10000
    default_ttl: 5m
  l2:
    enabled: true
    max_size_mb: 1000
    default_ttl: 1h
    path: "~/.arxos/cache/l2"
  l3:
    enabled: false
    default_ttl: 24h
    host: "localhost"
    port: 6379
    password: ""
    db: 0
```

### **Environment Variables**

Cache paths can be overridden using environment variables:

```bash
# Application data directory
export ARXOS_STATE_DIR="~/.arxos"

# Cache directory (relative to state directory)
export ARXOS_CACHE_DIR="cache"

# Build cache directory
export ARXOS_BUILD_CACHE_DIR="~/.cache/arxos"
```

## Migration

### **From Old Cache Structure**

If you have an existing ArxOS installation, use the migration tool:

```bash
# Migrate cache data to unified structure
go run cmd/cache-migrate/main.go migrate

# Validate migration
go run cmd/cache-migrate/main.go validate

# Clean up old cache directories
go run cmd/cache-migrate/main.go cleanup
```

### **Manual Migration**

If you prefer manual migration:

1. **Backup existing data**:
   ```bash
   cp -r ~/.arxos/cache ~/.arxos/cache.backup
   ```

2. **Create new structure**:
   ```bash
   mkdir -p ~/.arxos/cache/l2
   ```

3. **Move cache data**:
   ```bash
   # Move IFC cache
   mv ~/.arxos/cache/ifc/* ~/.arxos/cache/l2/ 2>/dev/null || true
   
   # Move spatial cache
   mv ~/.arxos/cache/spatial/* ~/.arxos/cache/l2/ 2>/dev/null || true
   
   # Move API cache
   mv ~/.arxos/cache/api/* ~/.arxos/cache/l2/ 2>/dev/null || true
   ```

4. **Remove old structure**:
   ```bash
   rm -rf ~/.arxos/cache/ifc ~/.arxos/cache/spatial ~/.arxos/cache/api
   ```

## Best Practices

### **Directory Management**

1. **Never mix application data with build caches**
2. **Use `~/.arxos/` for all application data**
3. **Use `~/.cache/` only for build system caches**
4. **Regularly clean up temporary files**

### **Cache Management**

1. **Monitor cache usage**:
   ```bash
   arx cache stats
   ```

2. **Clear cache when needed**:
   ```bash
   arx cache clear
   ```

3. **Warm cache for better performance**:
   ```bash
   arx cache warm
   ```

### **Backup Strategy**

1. **Backup application data**:
   ```bash
   tar -czf arxos-backup.tar.gz ~/.arxos/
   ```

2. **Don't backup build caches** (they can be regenerated)

3. **Include cache in backups** (contains processed data)

## Troubleshooting

### **Common Issues**

#### **Cache Directory Confusion**
- **Problem**: Application data in `~/.cache/`
- **Solution**: Move to `~/.arxos/cache/`

#### **Permission Issues**
- **Problem**: Cannot write to cache directory
- **Solution**: Fix permissions:
  ```bash
  chmod -R 755 ~/.arxos/cache/
  ```

#### **Disk Space Issues**
- **Problem**: Cache directory too large
- **Solution**: Clear cache or increase limits:
  ```bash
  arx cache clear
  # Or increase max_size_mb in config
  ```

#### **Migration Issues**
- **Problem**: Migration fails
- **Solution**: Check logs and retry:
  ```bash
  arx cache migrate --verbose
  ```

### **Debugging**

Enable debug logging to troubleshoot cache issues:

```bash
export ARXOS_LOG_LEVEL=debug
arx cache stats --verbose
```

## Security Considerations

### **Cache Security**

1. **L1 Cache**: In-memory only, cleared on restart
2. **L2 Cache**: Local files, use appropriate permissions
3. **L3 Cache**: Network access, use authentication

### **Data Protection**

1. **Encrypt sensitive cache data**
2. **Use secure Redis connections**
3. **Regularly rotate cache keys**

## Performance Tuning

### **Cache Sizing**

Adjust cache sizes based on your usage:

```yaml
unified_cache:
  l1:
    max_entries: 20000  # Increase for more memory
  l2:
    max_size_mb: 2000   # Increase for more disk cache
  l3:
    enabled: true       # Enable for shared caching
```

### **TTL Optimization**

Optimize TTL values for your use case:

```yaml
unified_cache:
  l1:
    default_ttl: 2m     # Shorter for volatile data
  l2:
    default_ttl: 2h     # Longer for stable data
  l3:
    default_ttl: 48h    # Longest for shared data
```

## Conclusion

The ArxOS directory structure provides a clear separation between application data and build system caches. The unified cache system offers optimal performance through multi-tier caching while maintaining simplicity and clarity.

For more information, see:
- [Unified Cache Architecture](../architecture/UNIFIED_CACHE_ARCHITECTURE.md)
- [Configuration Guide](../config/README.md)
- [Troubleshooting Guide](../troubleshooting/README.md)
