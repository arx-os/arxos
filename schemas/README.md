# ArxOS TOML Schemas

This directory contains schema definitions and documentation for ArxOS TOML configuration files.

## Purpose

TOML configuration provides:
- **Human-readable** configuration format
- **Comments** for inline documentation
- **Type safety** through Rust's serde deserialization
- **IDE support** via Taplo and TOML language servers

## Configuration File

### `arx.toml.example`

Example TOML configuration file with all available options documented.

**Location:** `../arx.toml.example`

**Usage:**
```bash
# Copy to create your configuration
cp arx.toml.example arx.toml

# Or create in user directory
cp arx.toml.example ~/.arx/config.toml
```

**Configuration Sections:**
- `user`: User information and Git commit preferences
- `paths`: File and directory paths
- `building`: Building-specific settings
- `performance`: Performance and optimization settings
- `ui`: User interface preferences

## IDE Setup

See [IDE Autocomplete Setup](../docs/development/IDE_AUTOCOMPLETE_SETUP.md) for detailed instructions on configuring your IDE for TOML support.

### Quick Setup (VSCode)

1. Install **Even Better TOML** extension (`tamasfe.even-better-toml`)
2. TOML files will automatically get syntax highlighting and validation

### Quick Setup (RustRover/IntelliJ)

TOML support is built-in. No additional setup required.

## Validation

### Using Taplo

Install Taplo CLI for TOML validation:
```bash
cargo install taplo-cli

# Validate syntax
taplo check arx.toml

# Format file
taplo format arx.toml
```

### Using ArxOS

ArxOS validates configuration at runtime:
```bash
# Show current configuration
arx config --show

# Validate without running
arx config --validate
```

## Configuration Hierarchy

ArxOS loads configuration from multiple locations (in order of precedence):

1. **Project-level**: `./arx.toml`
2. **Project hidden**: `./.arx/config.toml`
3. **User-level**: `~/.arx/config.toml`
4. **System-level**: `/etc/arx/config.toml` (Linux/macOS)

Later configurations override earlier ones.

## Legacy Files

### `config.schema.json`

**Status:** Deprecated

This JSON Schema was created for JSON configuration files, but ArxOS uses TOML. It is kept for reference but is not functional for TOML validation.

For TOML validation, use:
- Taplo CLI (`taplo check`)
- IDE TOML extensions
- ArxOS runtime validation

## Maintenance

### Updating Configuration Structure

When adding new configuration options:

1. **Update Rust code** in `src/config/mod.rs`
2. **Update `arx.toml.example`** with new fields and comments
3. **Update documentation** in `docs/core/CONFIGURATION.md`
4. **Test validation** with `arx config --show`

## References

- [Taplo Documentation](https://taplo.tamasfe.dev/)
- [TOML Specification](https://toml.io/)
- [IDE Autocomplete Setup Guide](../docs/development/IDE_AUTOCOMPLETE_SETUP.md)
- [Configuration Documentation](../docs/core/CONFIGURATION.md)
