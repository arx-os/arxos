# ArxIDE Tauri Backend

This is the Rust backend for ArxIDE, a professional desktop CAD IDE for building information modeling. The backend provides native system integration, file operations, and project management capabilities.

## Architecture

### Core Components

- **Commands Module**: Tauri commands that can be invoked from the frontend
- **Project Management**: Handles project creation, loading, saving, and validation
- **File Operations**: Native file system operations with proper error handling
- **Export Formats**: Support for SVGX, DXF, and IFC export formats
- **State Management**: Thread-safe application state with recent projects tracking

### Data Structures

#### ProjectData
```rust
pub struct ProjectData {
    pub id: String,                    // Unique project identifier
    pub name: String,                  // Project name
    pub description: String,           // Project description
    pub created_at: String,           // ISO 8601 timestamp
    pub last_modified: String,        // ISO 8601 timestamp
    pub objects: Vec<serde_json::Value>, // CAD objects
    pub constraints: Vec<serde_json::Value>, // Geometric constraints
    pub settings: HashMap<String, serde_json::Value>, // Project settings
}
```

#### ArxideError
Custom error type for comprehensive error handling:
```rust
pub enum ArxideError {
    FileError(std::io::Error),
    SerializationError(serde_json::Error),
    ValidationError(String),
    ProjectNotFound(String),
    ExportError(String),
    SystemError(String),
}
```

## API Reference

### Core Commands

#### `initialize_arxide()`
Initializes the ArxIDE application and loads recent projects.

**Returns**: `Result<(), String>`

#### `get_recent_projects()`
Retrieves the list of recently opened projects.

**Returns**: `Result<Vec<ProjectData>, String>`

#### `greet(name: String)`
Simple greeting command for testing.

**Parameters**:
- `name`: User's name

**Returns**: `Result<String, String>`

#### `create_project(name: String, description: String)`
Creates a new project with the specified name and description.

**Parameters**:
- `name`: Project name (required, non-empty)
- `description`: Project description (max 1000 characters)

**Returns**: `Result<ProjectData, String>`

#### `open_project(path: String)`
Opens a project from the specified file path.

**Parameters**:
- `path`: File path to the project file

**Returns**: `Result<ProjectData, String>`

#### `save_project(project: ProjectData, path: String)`
Saves a project to the specified file path.

**Parameters**:
- `project`: Project data to save
- `path`: File path where to save the project

**Returns**: `Result<(), String>`

### File Operations

#### `read_file(path: String)`
Reads a file from the native file system.

**Parameters**:
- `path`: File path to read

**Returns**: `Result<String, String>`

#### `write_file(path: String, content: String)`
Writes content to a file on the native file system.

**Parameters**:
- `path`: File path to write
- `content`: Content to write

**Returns**: `Result<(), String>`

#### `watch_file(path: String)`
Sets up file watching for the specified path.

**Parameters**:
- `path`: File path to watch

**Returns**: `Result<(), String>`

### Export Commands

#### `export_to_svgx(project: ProjectData)`
Exports a project to SVGX format.

**Parameters**:
- `project`: Project data to export

**Returns**: `Result<String, String>` (SVGX content)

#### `export_to_dxf(project: ProjectData)`
Exports a project to DXF format.

**Parameters**:
- `project`: Project data to export

**Returns**: `Result<String, String>` (DXF content)

#### `export_to_ifc(project: ProjectData)`
Exports a project to IFC format.

**Parameters**:
- `project`: Project data to export

**Returns**: `Result<String, String>` (IFC content)

### System Information

#### `get_system_info()`
Retrieves system information including platform, architecture, and version.

**Returns**: `Result<HashMap<String, String>, String>`

## Error Handling

The backend implements comprehensive error handling with:

- **Custom Error Types**: `ArxideError` enum for different error scenarios
- **Validation**: Input validation for all commands
- **Logging**: Structured logging with different levels (debug, info, warn, error)
- **Graceful Degradation**: Non-critical errors don't crash the application

### Error Categories

1. **File Errors**: IO operations, file not found, permission denied
2. **Serialization Errors**: JSON parsing, data format issues
3. **Validation Errors**: Invalid input data, missing required fields
4. **System Errors**: Environment issues, resource limitations
5. **Export Errors**: Format-specific export failures

## State Management

The application uses a thread-safe global state with:

- **Recent Projects**: List of recently opened projects (max 10)
- **Current Project**: Currently active project
- **Application State**: Initialization status and configuration

### State Persistence

Recent projects are automatically saved to:
- **macOS**: `~/Library/Application Support/arxide/recent_projects.json`
- **Linux**: `~/.local/share/arxide/recent_projects.json`
- **Windows**: `%APPDATA%\arxide\recent_projects.json`

## Development

### Prerequisites

- Rust 1.70 or later
- Tauri CLI
- Node.js and npm (for frontend)

### Building

```bash
# Build the backend
cargo build

# Build for release
cargo build --release

# Run tests
cargo test

# Run integration tests
cargo test --test integration_tests
```

### Testing

The backend includes comprehensive tests:

- **Unit Tests**: Individual function testing
- **Integration Tests**: End-to-end command testing
- **Error Handling Tests**: Error scenario validation
- **File Operation Tests**: File I/O testing

### Logging

The application uses structured logging with different levels:

```rust
log::debug!("Debug information");
log::info!("General information");
log::warn!("Warning messages");
log::error!("Error messages");
```

To enable logging, set the `RUST_LOG` environment variable:
```bash
RUST_LOG=debug cargo run
```

## Security Considerations

- **Input Validation**: All user inputs are validated
- **Path Sanitization**: File paths are validated before use
- **Error Information**: Sensitive information is not exposed in error messages
- **Resource Limits**: File operations have reasonable size limits

## Performance

- **Async Operations**: All file operations are asynchronous
- **Memory Management**: Efficient data structures and proper cleanup
- **Caching**: Recent projects are cached in memory
- **Lazy Loading**: Resources are loaded on demand

## Dependencies

### Core Dependencies
- `tauri`: Desktop application framework
- `serde`: Serialization/deserialization
- `tokio`: Async runtime
- `chrono`: Date/time handling
- `uuid`: Unique identifier generation

### Development Dependencies
- `tempfile`: Temporary file creation for testing
- `env_logger`: Logging implementation
- `thiserror`: Error handling utilities

## Contributing

1. Follow Rust coding standards
2. Add tests for new functionality
3. Update documentation for API changes
4. Ensure error handling is comprehensive
5. Validate all inputs and outputs

## License

MIT License - see LICENSE file for details.
