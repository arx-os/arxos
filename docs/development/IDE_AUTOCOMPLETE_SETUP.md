# IDE Autocomplete Setup for ArxOS Configuration

**Last Updated:** January 2025

## Overview

ArxOS provides a JSON schema for configuration files that enables IDE autocomplete, validation, and documentation. This guide shows how to set up autocomplete in popular IDEs.

## Prerequisites

- ArxOS JSON schema file: `schemas/config.schema.json`
- IDE with JSON schema support (VSCode, IntelliJ, etc.)

## Visual Studio Code

### Method 1: Project-Level Configuration (Recommended)

1. Create `.vscode/settings.json` in your project root:

```json
{
  "json.schemas": [
    {
      "fileMatch": ["arx.toml", ".arx/config.toml", "**/arx.toml"],
      "url": "./schemas/config.schema.json",
      "schema": {
        "$schema": "http://json-schema.org/draft-07/schema#"
      }
    }
  ]
}
```

**Note**: VSCode's JSON schema support for TOML is limited. For better TOML support, see the TOML extension method below.

### Method 2: Using TOML Extension

1. Install the "Even Better TOML" extension (id: `tamasfe.even-better-toml`)

2. Add to `.vscode/settings.json`:

```json
{
  "evenBetterToml.schema.enabled": true,
  "evenBetterToml.schema.associations": {
    "arx.toml": "./schemas/config.schema.json",
    "**/.arx/config.toml": "./schemas/config.schema.json"
  }
}
```

3. Create a TOML schema reference file `schemas/arx.toml.schema.json`:

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "ArxOS Configuration Schema Reference",
  "type": "object",
  "$ref": "./config.schema.json"
}
```

### Method 3: Global User Settings

Add to your global VSCode settings (`~/.config/Code/User/settings.json` on Linux, `~/Library/Application Support/Code/User/settings.json` on macOS):

```json
{
  "json.schemas": [
    {
      "fileMatch": ["**/arx.toml", "**/.arx/config.toml"],
      "url": "file:///path/to/arxos/schemas/config.schema.json"
    }
  ]
}
```

## JetBrains IDEs (IntelliJ, CLion, etc.)

### Method 1: Using JSON Schema

1. Go to **File → Settings → Languages & Frameworks → Schemas and DTDs → JSON Schema Mappings**
2. Click **+** to add a new schema
3. Configure:
   - **Name**: ArxOS Configuration
   - **Schema file**: Point to `schemas/config.schema.json`
   - **Schema version**: Draft 7
   - **File path patterns**: `**/arx.toml`, `**/.arx/config.toml`

### Method 2: Using TOML Plugin

1. Install the **TOML** plugin (if not already installed)
2. Go to **File → Settings → Languages & Frameworks → TOML**
3. Enable schema validation
4. Add schema mapping for `arx.toml` files

## Vim/Neovim

### Using coc.nvim

1. Install `coc-json` extension:

```vim
:CocInstall coc-json
```

2. Add to your `coc-settings.json`:

```json
{
  "json.schemas": [
    {
      "fileMatch": ["arx.toml", ".arx/config.toml"],
      "url": "./schemas/config.schema.json"
    }
  ]
}
```

### Using nvim-lspconfig

1. Configure `jsonls` in your Neovim config:

```lua
require('lspconfig').jsonls.setup {
  settings = {
    json = {
      schemas = {
        {
          fileMatch = { "arx.toml", ".arx/config.toml" },
          url = "./schemas/config.schema.json"
        }
      }
    }
  }
}
```

## Emacs

### Using lsp-mode

1. Install `lsp-mode` and `lsp-json`

2. Add to your `init.el`:

```elisp
(with-eval-after-load 'lsp-json
  (add-to-list 'lsp-json-schemas
               `(:fileMatch ,(rx (or "arx.toml" ".arx/config.toml"))
                 :url "file:///path/to/arxos/schemas/config.schema.json")))
```

## Verifying Setup

### Test Configuration File

Create a test `arx.toml` file:

```toml
[user]
name = "Test User"
email = "test@example.com"

[performance]
max_parallel_threads = 8
```

### Expected Behavior

When properly configured, you should see:
- ✅ **Autocomplete**: Typing `[user.` should show suggestions
- ✅ **Validation**: Invalid values (e.g., `max_parallel_threads = 0`) should show errors
- ✅ **Documentation**: Hovering over fields should show descriptions
- ✅ **Type hints**: Invalid types should be highlighted

## Troubleshooting

### Autocomplete Not Working

1. **Check file association**: Ensure your IDE recognizes `arx.toml` as a config file
2. **Verify schema path**: Confirm the schema file path is correct
3. **Restart IDE**: Some IDEs require a restart to load schema changes
4. **Check schema format**: Validate that `schemas/config.schema.json` is valid JSON

### Validation Errors Showing Incorrectly

1. **Schema version**: Ensure your IDE supports JSON Schema Draft 7
2. **File matching**: Check that your file pattern matches the config file name
3. **Schema syntax**: Verify the schema file is valid JSON Schema

### TOML-Specific Issues

Since the schema is JSON but config files are TOML:
- Some IDEs may have limited TOML schema support
- Consider using a TOML-to-JSON converter for validation
- Use TOML-specific extensions when available

## Schema Location

The ArxOS configuration schema is located at:
- **Relative path**: `schemas/config.schema.json` (from project root)
- **Absolute path**: `<arxos-install>/schemas/config.schema.json`

## Related Documentation

- [Configuration Guide](../core/CONFIGURATION.md) - Complete configuration reference
- [API Reference](../core/API_REFERENCE.md) - Configuration API documentation
- [Developer Onboarding](./DEVELOPER_ONBOARDING.md) - Development setup

## Contributing

If you set up autocomplete for another IDE, please contribute your configuration to this document!

