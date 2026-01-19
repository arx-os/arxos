# Arxos

**Git for Buildings** – Terminal-first building data management with Git-native storage.

## Overview

ArxOS is a command-line tool for managing building data (IFC models, equipment, sensors) using Git as the version control foundation. Store building information in YAML, track changes with Git, and collaborate like software development.

## Installation

```bash
# Clone the repository
git clone https://github.com/arx-os/arxos.git
cd arxos

# Build and install
cargo build --release
cargo install --path .
```

## Quick Start

```bash
# Initialize a new building project
arx init --name "My Building"

# Import an IFC file
arx import building.ifc

# List building data
arx list

# View building structure
arx show

# Start the web interface
arx web
```

## Features

- **Git-native storage** – All building data stored as YAML, versioned with Git
- **IFC import/export** – Parse and convert Industry Foundation Classes files
- **3D visualization** – WebGPU-powered rendering in the browser
- **Terminal UI** – Interactive building exploration and editing
- **Web interface** – Progressive Web App (WASM) for browser-based access
- **Equipment tracking** – Manage HVAC, electrical, and other building systems
- **Sensor integration** – Real-time hardware monitoring and data collection

## Architecture

ArxOS is a single Rust binary (`arx`) with feature-gated modules:

- `/src` – Core application (single binary architecture)
- `/contracts` – Ethereum smart contracts (optional economy layer)
- `/examples` – Sample buildings and data files
- `/templates` – Starting scaffolds for `arx init`
- `/test_data` – Test fixtures for CI

## Documentation

Documentation is minimal by design. Use `arx --help` for command reference.

## Development

```bash
# Run tests
cargo test

# Run with logging
RUST_LOG=debug cargo run -- <command>

# Build for web (WASM)
cd src/web
trunk serve
```

## License

MIT
