# IDE Autocomplete Setup for ArxOS

This guide shows how to configure your IDE for TOML autocomplete and validation in ArxOS configuration files.

---

## VSCode Setup

### 1. Install Extensions

Install the **Even Better TOML** extension:
- Extension ID: `tamasfe.even-better-toml`
- Provides syntax highlighting, validation, and autocomplete for TOML files

### 2. Install Taplo CLI (Optional)

For advanced validation:
```bash
cargo install taplo-cli
```

### 3. Configuration

VSCode will automatically recognize `.toml` files. For custom settings, add to `.vscode/settings.json`:

```json
{
  "evenBetterToml.formatter.alignEntries": true,
  "evenBetterToml.formatter.indentTables": true,
  "[toml]": {
    "editor.defaultFormatter": "tamasfe.even-better-toml",
    "editor.formatOnSave": true
  }
}
```

---

## IntelliJ IDEA / RustRover Setup

### 1. TOML Plugin

The TOML plugin is built-in for RustRover and recent IntelliJ IDEA versions.

For older versions:
- Go to **Settings → Plugins**
- Search for "TOML"
- Install the TOML plugin

### 2. Enable Formatting

- **Settings → Editor → Code Style → TOML**
- Configure indentation and formatting preferences

---

## Neovim Setup

### 1. Install Taplo LSP

Using `mason.nvim`:
```lua
require("mason").setup()
require("mason-lspconfig").setup({
  ensure_installed = { "taplo" }
})
```

### 2. Configure LSP

```lua
require("lspconfig").taplo.setup({
  settings = {
    evenBetterToml = {
      schema = {
        enabled = true
      }
    }
  }
})
```

---

## Configuration File Locations

ArxOS looks for configuration in the following order:

1. `./arx.toml` (project-specific)
2. `./.arx/config.toml` (project-specific, hidden)
3. `~/.arx/config.toml` (user-level)
4. `/etc/arx/config.toml` (system-level, Linux/macOS)

---

## Example Configuration

See [`arx.toml.example`](../../arx.toml.example) for a fully commented example configuration.

---

## Validation

### Using Taplo CLI

```bash
# Validate TOML syntax
taplo check arx.toml

# Format TOML file
taplo format arx.toml
```

### Using Cargo

ArxOS validates configuration at runtime:
```bash
# Check configuration validity
arx config --show
```

---

## Troubleshooting

### Autocomplete Not Working

1. Ensure the TOML extension/plugin is installed
2. Restart your IDE
3. Check that the file has `.toml` extension

### Validation Errors

1. Run `taplo check arx.toml` to see syntax errors
2. Compare with `arx.toml.example`
3. Check [Configuration Documentation](../core/CONFIGURATION.md)

---

## References

- [Taplo Documentation](https://taplo.tamasfe.dev/)
- [Even Better TOML Extension](https://marketplace.visualstudio.com/items?itemName=tamasfe.even-better-toml)
- [ArxOS Configuration Guide](../core/CONFIGURATION.md)
