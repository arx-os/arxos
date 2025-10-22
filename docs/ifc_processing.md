# ArxOS IFC Processing Module

## Overview

The IFC processing module handles Industry Foundation Classes (IFC) files, converting them into ArxOS's Git-based building data format.

## Architecture

### Core Components

- **IFCProcessor**: Main processor for IFC files
- **SpatialEntity**: Represents spatial data extracted from IFC
- **IFCError**: Comprehensive error handling
- **BoundingBox**: 3D bounding box representation

### Error Handling

The module uses `thiserror` for structured error handling:

```rust
#[derive(Error, Debug)]
pub enum IFCError {
    #[error("IFC file not found: {path}")]
    FileNotFound { path: String },
    
    #[error("Invalid IFC file format: {reason}")]
    InvalidFormat { reason: String },
    
    #[error("IFC parsing error: {message}")]
    ParsingError { message: String },
}
```

### Logging

The module uses the `log` crate for structured logging:

- `info!`: General processing information
- `warn!`: Non-critical issues
- `error!`: Critical errors

## Usage

### Basic IFC Processing

```rust
use arxos::ifc::IFCProcessor;

let processor = IFCProcessor::new();
let building = processor.process_file("building.ifc")?;
```

### File Validation

```rust
let is_valid = processor.validate_ifc_file("building.ifc")?;
```

### Spatial Data Extraction

```rust
let spatial_data = processor.extract_spatial_data(&ifc_bytes)?;
```

## Testing

The module includes comprehensive tests:

- Unit tests for individual components
- Integration tests for file processing
- Error handling tests
- Mock data tests

Run tests with:

```bash
cargo test
```

## Future Enhancements

- Custom STEP parser implementation
- Coordinate system transformations
- Advanced spatial queries
- Performance optimizations
