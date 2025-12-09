# ArxOS Documentation

**Git for Buildings** – Terminal-first building data management

---

## Getting Started

- **[Getting Started Guide](./getting-started.md)** – Installation, first building, basic workflows
- **[CLI Reference](./cli-reference.md)** – Complete command-line interface documentation
- **[Data Format](./data-format.md)** – YAML schema and Git storage structure

---

## Core Features

- **[Architecture](./architecture.md)** – System design, single binary approach, feature gates
- **[IFC Import/Export](./ifc.md)** – Industry Foundation Classes file handling
- **[Web Interface](./web.md)** – Progressive Web App (WASM) usage and deployment

---

## Development

- **[Building from Source](./development/building.md)** – Compilation and installation
- **[Testing](./development/testing.md)** – Running tests and benchmarks
- **[Contributing](./development/contributing.md)** – Contribution guidelines

---

## Quick Reference

```bash
# Initialize a new building
arx init --name "My Building"

# Import IFC file
arx import building.ifc

# List building data
arx list

# Start web interface
arx web

# Get help
arx --help
```

---

**Rust API Documentation:** See `/docs/rustdoc/` for generated Rust documentation
