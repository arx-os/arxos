# File-Based Storage System for ArxOS

This document explains the file-based storage system that replaced the previous SQLite database implementation in ArxOS.

## Overview

ArxOS has migrated from SQLite database storage to a lightweight file-based storage system optimized for RF mesh environments. This change eliminates database dependencies while maintaining data persistence and retrieval capabilities.

## Architecture

### Storage Components

1. **FileStorage** - Primary file-based storage implementation
2. **MemoryDatabase** - In-memory storage for testing and lightweight use cases  
3. **Database Trait** - Common interface for both implementations

### File Structure

The file storage system organizes data as follows:

```
arxos_data/
├── index.json              # Metadata index for fast lookups
├── building_100_type_1.jsonl   # Objects for building 100, type 1
├── building_100_type_2.jsonl   # Objects for building 100, type 2
├── building_101_type_1.jsonl   # Objects for building 101, type 1
└── ...
```

### Storage Format

- **JSONL Format**: Each object is stored as one JSON line for efficient appends
- **Index File**: JSON file containing object metadata for fast lookups
- **Building/Type Sharding**: Objects are automatically organized by building ID and object type

## Key Features

### 1. Lightweight Dependencies
- No SQLite or other database dependencies
- Pure Rust implementation with minimal external crates
- Suitable for embedded and resource-constrained environments

### 2. RF Mesh Optimization
- Append-only file operations minimize disk I/O
- Index caching for fast queries
- Automatic file organization by building/type

### 3. Backward Compatibility
- Maintains the same `Database` trait interface
- Existing code continues to work without changes
- Simple migration path from SQLite

### 4. Flexible Storage Options
- **FileStorage**: Persistent file-based storage
- **MemoryDatabase**: Fast in-memory storage for testing

## Usage Examples

### Basic Storage Operations

```rust
use arxos_core::file_storage::{FileStorage, FileStorageConfig, Database};
use arxos_core::ArxObject;

// Create file storage
let config = FileStorageConfig::default();
let mut storage = FileStorage::new(config)?;

// Store an object
let object = ArxObject::new(0x1234, object_types::OUTLET, 100, 200, 150);
let id = storage.store_object(&object)?;

// Retrieve an object
let retrieved = storage.get_object(&id)?;

// Get all objects for a building
let building_objects = storage.get_building_objects(100)?;
```

### Memory Database for Testing

```rust
use arxos_core::file_storage::{MemoryDatabase, Database};

let mut db = MemoryDatabase::new();
let id = db.store_object(&object)?;
let retrieved = db.get_object(&id)?;
```

### Storage Statistics

```rust
let stats = storage.get_stats()?;
println!("Total objects: {}", stats.total_objects);
println!("Storage size: {} bytes", stats.storage_size_bytes);
```

## Configuration

### FileStorageConfig Options

```rust
pub struct FileStorageConfig {
    pub base_path: PathBuf,           // Storage directory
    pub max_objects_per_file: usize,  // Objects per file (future use)
    pub enable_compression: bool,      // Compression support (future use)
}
```

### Default Configuration

- **Base Path**: `./arxos_data`
- **Max Objects Per File**: 1000
- **Compression**: Disabled

## Migration from SQLite

The migration from SQLite to file storage was designed to be seamless:

### What Changed
- Removed `rusqlite` dependency from all Cargo.toml files
- Replaced database modules with `file_storage` module
- Updated imports across the codebase

### What Stayed the Same
- Database trait interface remains identical
- Existing code continues to work without modification
- Same ArxObject storage and retrieval semantics

### Migration Steps Completed
1. ✅ Removed SQLite dependencies from Cargo.toml files
2. ✅ Deleted database-specific source files
3. ✅ Updated lib.rs to remove database module references
4. ✅ Created new file_storage.rs implementation
5. ✅ Updated all imports to use file_storage
6. ✅ Removed old SQL database documentation
7. ✅ Created new file storage documentation

## Performance Characteristics

### Advantages
- **Startup Time**: No database initialization overhead
- **Memory Usage**: Lower baseline memory usage
- **Dependencies**: Eliminated SQLite dependency
- **Portability**: Works on all platforms without native libs

### Trade-offs
- **Query Performance**: Some complex queries may be slower
- **Concurrent Access**: Limited concurrent write support
- **Data Integrity**: Manual backup/recovery vs automatic transactions

## Future Enhancements

### Planned Features
1. **File Compression**: Optional compression for storage efficiency
2. **Batch Operations**: Optimized batch insert/update operations  
3. **Query Indexing**: Additional indices for complex queries
4. **Concurrent Access**: Reader/writer lock support
5. **Data Migration**: Tools for importing/exporting data

### Compatibility
The file storage system is designed to support future enhancements while maintaining backward compatibility with the current Database trait interface.

## Troubleshooting

### Common Issues

**Storage Directory Permissions**
```bash
# Ensure write permissions to storage directory
chmod 755 ./arxos_data
```

**Index Corruption**
```rust
// The index will be automatically rebuilt from data files if corrupted
// Manual rebuild (if needed):
storage.compact()?;
```

**Large File Sizes**
```rust
// Monitor storage statistics
let stats = storage.get_stats()?;
if stats.storage_size_bytes > threshold {
    // Consider archiving old data
}
```

## Integration with ArxOS

The file storage system integrates seamlessly with other ArxOS components:

- **Mesh Network**: Efficient storage of received ArxObjects
- **Report Generator**: Fast data access for report generation
- **Data Aggregator**: Streamlined data processing pipeline
- **Terminal Interface**: Real-time data display and queries

## Conclusion

The migration to file-based storage aligns with ArxOS's goals of being lightweight, dependency-free, and optimized for RF mesh environments. The new system maintains compatibility while reducing complexity and improving portability across different deployment scenarios.