# ArxOS JSON Schemas

This directory contains JSON Schema definitions for ArxOS configuration and data files.

## Purpose

JSON Schemas provide:
- **IDE Autocomplete**: IntelliSense and autocomplete support in editors
- **Validation**: Catch configuration errors before runtime
- **Documentation**: Inline documentation for configuration fields
- **Type Safety**: Ensure configuration values match expected types

## Available Schemas

### `config.schema.json`

JSON Schema for ArxOS configuration files (`arx.toml`).

**Usage:**
- IDE autocomplete for configuration files
- Validation of configuration values
- Documentation for all configuration options

**Schema Version:** 1.0.0  
**JSON Schema Draft:** Draft-07

**Configuration Sections:**
- `user`: User information and Git commit preferences
- `paths`: File and directory paths
- `building`: Building-specific settings
- `performance`: Performance and optimization settings
- `ui`: User interface preferences

## Integration

The schema is integrated into the codebase via:
- `src/config/schema.rs`: Provides schema access via `ConfigSchema::json_schema()`
- `docs/development/IDE_AUTOCOMPLETE_SETUP.md`: IDE setup instructions

## IDE Setup

See [IDE Autocomplete Setup](../docs/development/IDE_AUTOCOMPLETE_SETUP.md) for detailed instructions on configuring your IDE to use these schemas.

### Quick Setup (VSCode)

Add to `.vscode/settings.json`:

```json
{
  "json.schemas": [
    {
      "fileMatch": ["arx.toml", ".arx/config.toml", "**/arx.toml"],
      "url": "./schemas/config.schema.json"
    }
  ]
}
```

## Schema Validation

The schema uses:
- **JSON Schema Draft-07**: Modern, widely supported schema version
- **Type Validation**: Enforces correct types (string, integer, boolean, etc.)
- **Enum Constraints**: Restricts values to allowed options
- **Range Constraints**: Validates numeric ranges (min/max)
- **Required Fields**: Ensures essential configuration is present
- **Default Values**: Documents default values for optional fields
- **Examples**: Provides example values for better IDE support

## Maintenance

### Updating Schemas

When updating configuration structures in Rust code:

1. **Update the schema** to match the new structure
2. **Update `src/config/schema.rs`** if field documentation changes
3. **Increment schema version** if making breaking changes
4. **Test IDE autocomplete** to ensure changes work correctly

### Schema Versioning

- **Major version** (X.0.0): Breaking changes (removed fields, changed types)
- **Minor version** (0.X.0): New fields added (backward compatible)
- **Patch version** (0.0.X): Documentation updates, bug fixes

Current schema version: **1.0.0**

## Future Schemas

Potential additional schemas:
- `building.schema.json`: Schema for building YAML files
- `sensor-data.schema.json`: Schema for sensor data JSON files
- `ar-scan.schema.json`: Schema for AR scan data files

## Testing

To validate the schema:

```bash
# Validate JSON syntax
python3 -m json.tool schemas/config.schema.json > /dev/null

# Validate against JSON Schema meta-schema (requires jsonschema package)
python3 -m pip install jsonschema
python3 -c "import json, jsonschema; schema = json.load(open('schemas/config.schema.json')); jsonschema.Draft7Validator.check_schema(schema)"
```

## References

- [JSON Schema Specification](https://json-schema.org/)
- [JSON Schema Draft-07](https://json-schema.org/draft-07/schema#)
- [IDE Autocomplete Setup Guide](../docs/development/IDE_AUTOCOMPLETE_SETUP.md)
- [Configuration Documentation](../docs/core/CONFIGURATION.md)

