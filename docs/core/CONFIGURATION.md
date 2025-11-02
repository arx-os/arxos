# ArxOS Configuration Guide

## Overview

ArxOS uses a hierarchical configuration system that allows you to configure the tool at multiple levels, with clear precedence rules ensuring that more specific settings override general ones.

## Configuration Precedence

Configuration is loaded and merged in the following order (highest to lowest priority):

1. **Environment Variables** (highest priority)
2. **Project Config** (`arx.toml` in current directory)
3. **User Config** (`~/.arx/config.toml`)
4. **Global Config** (`/etc/arx/config.toml`)
5. **Default Values** (lowest priority)

This means:
- Environment variables always override file-based configuration
- Project-specific configs override user configs
- User configs override global configs
- Defaults are used when no config file exists

## Configuration Files

### Project Configuration (`arx.toml`)

Located in the current working directory. This is the highest priority file-based configuration.

```toml
[user]
name = "Project User"
email = "project@example.com"

[building]
auto_commit = false
default_coordinate_system = "LOCAL"
```

### User Configuration (`~/.arx/config.toml`)

Located in your home directory. Use this for personal preferences that apply across all projects.

```bash
mkdir -p ~/.arx
cat > ~/.arx/config.toml << EOF
[user]
name = "Your Name"
email = "your.email@example.com"
organization = "Your Organization"

[performance]
max_parallel_threads = 8
cache_enabled = true

[ui]
verbosity = "Verbose"
use_emoji = true
EOF
```

### Global Configuration (`/etc/arx/config.toml`)

System-wide configuration (requires root/admin access). Use for organization-wide defaults.

## Environment Variables

All configuration can be overridden using environment variables. Prefix configuration keys with `ARX_` and use uppercase with underscores.

### Available Environment Variables

#### User Configuration
- `ARX_USER_NAME` - User's full name
- `ARX_USER_EMAIL` - User's email address
- `ARX_USER_ORGANIZATION` - User's organization (optional)

#### Path Configuration
- `ARX_DEFAULT_IMPORT_PATH` - Default directory for importing IFC files
- `ARX_BACKUP_PATH` - Directory for backup files

#### Building Configuration
- `ARX_AUTO_COMMIT` - Auto-commit changes (true/false)

#### Performance Configuration
- `ARX_MAX_THREADS` - Maximum parallel threads
- `ARX_MEMORY_LIMIT_MB` - Memory limit in MB

#### UI Configuration
- `ARX_VERBOSITY` - Output verbosity level (silent, normal, verbose, debug)

### Example

```bash
export ARX_USER_NAME="Environment User"
export ARX_AUTO_COMMIT="false"
export ARX_VERBOSITY="verbose"
arx import building.ifc
```

## Configuration Structure

### User Configuration

```toml
[user]
name = "User Name"
email = "user@example.com"
organization = "Organization Name"  # Optional
commit_template = "feat: {operation} {building_name}"
```

### Path Configuration

```toml
[paths]
default_import_path = "./buildings"
backup_path = "./backups"
template_path = "./templates"
temp_path = "./temp"
```

**Note**: Paths don't need to exist when configuration is loaded. They will be created if needed.

### Building Configuration

```toml
[building]
default_coordinate_system = "WGS84"  # Options: WGS84, UTM, LOCAL
auto_commit = true
naming_pattern = "{building_name}-{timestamp}"
validate_on_import = true
```

### Performance Configuration

```toml
[performance]
max_parallel_threads = 8  # Default: number of CPU cores
memory_limit_mb = 1024   # Default: 1024 MB (1 GB)
cache_enabled = true
cache_path = "./cache"
show_progress = true
```

### UI Configuration

```toml
[ui]
use_emoji = true
verbosity = "Normal"  # Options: Silent, Normal, Verbose, Debug
color_scheme = "Auto"  # Options: Auto, Always, Never
detailed_help = false
```

## Configuration Validation

Configuration is validated when loaded. The validation rules are:

### Relaxed Validation (on load)
- Paths don't need to exist (they may be created later)
- Basic type and format validation
- Value range checks

### Strict Validation (on save/update)
- Paths must exist and be accessible
- All fields must be valid
- Cross-field validation (e.g., no duplicate paths)

### Validation Errors

If configuration validation fails, you'll see a clear error message:

```
Configuration validation failed: user.email - Email must be valid format
```

## Default Values

When no configuration files exist, ArxOS uses these defaults:

| Setting | Default Value |
|---------|--------------|
| `user.name` | "ArxOS User" |
| `user.email` | "user@arxos.com" |
| `building.auto_commit` | `true` |
| `building.default_coordinate_system` | "WGS84" |
| `performance.max_parallel_threads` | Number of CPU cores |
| `performance.memory_limit_mb` | 1024 |
| `ui.verbosity` | "Normal" |
| `ui.use_emoji` | `true` |

## Examples

### Example 1: Project-Specific Configuration

Create `arx.toml` in your project directory:

```toml
[user]
name = "Project Team"
email = "team@company.com"

[building]
auto_commit = false  # Manual commits for this project
default_coordinate_system = "LOCAL"
```

### Example 2: Using Environment Variables

For CI/CD or temporary overrides:

```bash
ARX_AUTO_COMMIT=false ARX_VERBOSITY=verbose arx import building.ifc
```

### Example 3: Mixed Configuration

```toml
# ~/.arx/config.toml (user config)
[user]
name = "John Doe"
email = "john@example.com"

[performance]
max_parallel_threads = 16
cache_enabled = true
```

```toml
# ./arx.toml (project config - overrides user config)
[building]
auto_commit = false  # Override default for this project

[performance]
max_parallel_threads = 4  # Override user config for this project
```

Result:
- `user.name` = "John Doe" (from user config)
- `user.email` = "john@example.com" (from user config)
- `building.auto_commit` = `false` (from project config)
- `performance.max_parallel_threads` = 4 (from project config, overrides user config)
- `performance.cache_enabled` = `true` (from user config)

## Viewing Current Configuration

Use the `arx config show` command to view the effective configuration:

```bash
arx config show
```

This shows the merged configuration with all precedence rules applied.

## Troubleshooting

### Configuration Not Loading

1. Check file syntax (must be valid TOML)
2. Verify file permissions
3. Check for validation errors
4. Use `arx config show` to see what's being loaded

### Environment Variables Not Working

1. Ensure variable names start with `ARX_`
2. Use uppercase with underscores
3. Check for typos
4. Verify the variable is exported in your shell

### Path Validation Errors

If you see path validation errors, you can:
1. Create the required directories
2. Use absolute paths
3. Ensure directory permissions are correct

## Best Practices

1. **Use Project Configs** for project-specific settings
2. **Use User Config** for personal preferences
3. **Use Environment Variables** for CI/CD and temporary overrides
4. **Keep Configs Simple** - only override what you need
5. **Validate Early** - use `arx config show` to verify your configuration

## See Also

- [API Reference](./API_REFERENCE.md) - Complete configuration API
- [Operations Guide](./OPERATIONS.md) - Operational procedures
- [Troubleshooting Guide](./TROUBLESHOOTING.md) - Common issues and solutions

