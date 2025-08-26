# Arxos Init Command Implementation

This document describes the implementation of the `arx init` command, which creates the foundational building filesystem structure for Arxos.

## Overview

The `arx init` command is the entry point for working with Arxos - it creates a complete building filesystem with metadata directories, configuration files, and the foundation for all subsequent operations.

## Features Implemented

### ✅ **Core Functionality**
- **Building ID Validation**: Ensures proper `building:name` format
- **Filesystem Creation**: Creates complete `.arxos` metadata directory structure
- **Configuration Generation**: Generates YAML configs for building, floors, and systems
- **Input Processing Framework**: Ready for PDF/IFC/template processing
- **Comprehensive Validation**: Validates all inputs and created structure
- **User Feedback**: Clear success messages and next steps

### ✅ **Command Flags**
- `--type`: Building type (office, residential, industrial, retail)
- `--floors`: Number of floors (1-200)
- `--area`: Total building area (e.g., "25,000 sq ft")
- `--location`: Building location/address
- `--from-pdf`: Initialize from PDF floor plan
- `--from-ifc`: Initialize from IFC file
- `--config`: Use custom configuration file
- `--template`: Use predefined building template
- `--force`: Overwrite existing building if it exists

### ✅ **Building Structure Created**
```
building:main/
├── .arxos/                    # Metadata directory
│   ├── config/               # Building configuration
│   ├── objects/              # ArxObject database
│   ├── vcs/                  # Version control data
│   ├── cache/                # Temporary data and cache
│   └── logs/                 # Building operation logs
├── arxos.yml                 # Main building configuration
├── floor:1/                  # First floor
│   └── arxos.yml            # Floor configuration
├── systems/                  # Building systems
│   ├── electrical/
│   ├── hvac/
│   ├── automation/
│   ├── plumbing/
│   ├── fire_protection/
│   └── security/
└── schemas/                  # Configuration schemas
```

## Usage Examples

### Basic Initialization
```bash
# Initialize a simple office building
arx init building:main

# Initialize with specific configuration
arx init building:hq --type office --floors 5 --area "25,000 sq ft"

# Initialize from existing data
arx init building:warehouse --from-pdf "floor_plan.pdf" --type industrial

# Use a template
arx init building:office --template "standard_office" --floors 3
```

### Advanced Options
```bash
# Force overwrite existing building
arx init building:main --force

# Custom location
arx init building:hq --location "123 Innovation Drive, Tech City, CA"

# Multiple floors with area
arx init building:apartment --type residential --floors 4 --area "50,000 sq ft"
```

## Implementation Details

### Architecture
- **Go CLI Layer**: Handles user input, file operations, configuration generation
- **CGO Bridge**: Ready for integration with C core for ArxObject operations
- **YAML Processing**: Uses `gopkg.in/yaml.v3` for configuration files
- **Error Handling**: Comprehensive validation and user feedback

### Key Functions
1. **`initializeBuilding()`**: Main orchestration function
2. **`createBuildingFilesystem()`**: Creates directory structure
3. **`createInitialConfiguration()`**: Generates YAML configs
4. **`validateBuildingID()`**: Ensures proper building ID format
5. **`validateInitOptions()`**: Validates all command options
6. **`validateBuildingStructure()`**: Verifies created structure

### Configuration Generation
- **Building Config**: Main building properties and system definitions
- **Floor Configs**: Individual floor configurations with height and area
- **System Configs**: Electrical, HVAC, automation, plumbing, fire protection, security
- **Metadata**: Creation timestamps, versions, and status information

## Testing

### Running Tests
```bash
# Run all tests
go test ./commands

# Run specific test
go test -v -run TestValidateBuildingID

# Run tests with coverage
go test -cover ./commands
```

### Test Coverage
- **Unit Tests**: Individual function validation
- **Integration Tests**: Complete workflow testing
- **Edge Cases**: Invalid inputs and error conditions
- **Filesystem Tests**: Directory and file creation verification

## Next Steps

### Phase 2: CGO Integration
- Implement CGO bridge to C core
- Create ArxObject hierarchy via C functions
- Integrate spatial indexing and rendering

### Phase 3: Advanced Features
- PDF floor plan processing
- IFC file import
- Building template system
- Version control implementation

### Phase 4: Navigation Commands
- `arx cd` - Change directory
- `arx ls` - List contents
- `arx pwd` - Show current location
- `arx tree` - Display structure

## Building and Running

### Prerequisites
- Go 1.24.5 or later
- YAML v3 library (`gopkg.in/yaml.v3`)

### Build Commands
```bash
# Navigate to cmd directory
cd cmd

# Install dependencies
go mod tidy

# Build the CLI
go build -o arxos.exe .

# Run the init command
./arxos.exe init building:test --type office --floors 2
```

### Development Workflow
1. **Code Changes**: Modify `init.go` as needed
2. **Run Tests**: `go test ./commands`
3. **Build**: `go build -o arxos.exe .`
4. **Test CLI**: `./arxos.exe init --help`

## Error Handling

### Validation Errors
- **Building ID**: Must follow `building:name` format
- **Building Type**: Must be valid type (office, residential, industrial, retail)
- **Floors**: Must be between 1 and 200
- **Area Format**: Must include numbers and units
- **Input Files**: Cannot specify both PDF and IFC

### Filesystem Errors
- **Directory Creation**: Handles permission and space issues
- **File Writing**: Validates YAML generation and file writing
- **Structure Validation**: Verifies all essential components exist

## Performance Considerations

### Current Implementation
- **File Operations**: Sequential directory and file creation
- **YAML Processing**: In-memory YAML generation
- **Validation**: Linear validation of options and structure

### Future Optimizations
- **Parallel Processing**: Concurrent system configuration creation
- **Batch Operations**: Bulk file operations where possible
- **Caching**: Cache validation results and configuration templates

## Security and Compliance

### File Permissions
- **Directories**: 0755 (rwxr-xr-x)
- **Configuration Files**: 0644 (rw-r--r--)
- **Metadata Files**: 0600 (rw-------)

### Input Validation
- **Building Names**: Alphanumeric, hyphens, underscores only
- **Path Traversal**: Prevents directory traversal attacks
- **File Extensions**: Validates input file types

## Troubleshooting

### Common Issues
1. **Permission Denied**: Check directory write permissions
2. **Invalid Building ID**: Ensure format is `building:name`
3. **YAML Errors**: Verify configuration structure
4. **Import Errors**: Run `go mod tidy` to resolve dependencies

### Debug Mode
```bash
# Enable verbose output
arx init building:test --verbose

# Check help for all options
arx init --help
```

## Contributing

### Code Standards
- **Error Handling**: Use `fmt.Errorf` with `%w` for wrapping
- **Validation**: Comprehensive input validation
- **Documentation**: Clear function and type documentation
- **Testing**: Unit tests for all public functions

### Adding Features
1. **Update Types**: Add new fields to configuration structs
2. **Extend Validation**: Add validation logic for new options
3. **Create Tests**: Add test coverage for new functionality
4. **Update Documentation**: Document new features and usage

This implementation provides a solid foundation for the Arxos CLI, following Go best practices and creating a robust building initialization system.
