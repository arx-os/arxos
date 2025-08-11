# Arxos CLI Documentation

The Arxos Command Line Interface provides powerful tools for querying, modifying, and managing building data through spatial-first commands that understand architectural relationships and building physics.

## Overview

The Arxos CLI is built around the core concept that buildings are complex spatial and functional systems where objects have relationships, constraints, and behaviors. The CLI provides:

- **Spatial-First Querying**: Query building objects by location, relationships, and properties
- **ArxObject Integration**: Direct manipulation of building objects with constraint validation  
- **Transaction Safety**: Atomic operations that maintain building integrity
- **Real-Time Collaboration**: Live sync and conflict resolution for multi-user editing
- **Physics-Aware Operations**: Commands that understand structural, MEP, and spatial implications

## Quick Start

```bash
# Install Arxos CLI
npm install -g @arxos/cli

# Authenticate to your organization
arxos auth login --org="your-org"

# Connect to a building
arxos connect building://your-org/building-name

# Run your first query
arxos find outlets in floor:1
```

## Documentation Structure

- [**Authentication & Connection**](./auth-connection.md) - Setup and building access
- [**Query Language Reference**](./query-language.md) - Complete syntax and examples
- [**ArxObject Operations**](./arxobject-operations.md) - Object manipulation and validation
- [**Transaction System**](./transactions.md) - Atomic operations and rollback
- [**Real-Time Sync**](./real-time-sync.md) - Collaborative editing and conflict resolution
- [**Performance & Optimization**](./performance.md) - Query optimization and caching
- [**API Reference**](./api-reference.md) - Complete command reference
- [**Examples & Use Cases**](./examples.md) - Common workflows and advanced scenarios
- [**Architecture Overview**](./architecture.md) - Internal system design
- [**Troubleshooting**](./troubleshooting.md) - Common issues and solutions

## Core Concepts

### Spatial-First Design
Buildings are inherently spatial systems. The CLI treats spatial relationships as first-class concepts:

```bash
# Find objects by spatial relationships
arxos find outlets within 10ft of beam:B-101
arxos query "walls adjacent-to room:R-205"
```

### ArxObject Integration
Every building element is an ArxObject with properties, relationships, and constraints:

```bash
# Modify object properties with validation
arxos set outlet:R45-23.voltage=120 --validate-constraints
arxos modify wall:W-101 add-property fire-rating=2hr
```

### Transaction Safety
Complex operations are atomic to maintain building integrity:

```bash
arxos transaction begin
arxos move beam:B-101 to coordinates:(100,200,300)
arxos recalculate structural-loads for floor:45
arxos transaction commit
```

## Getting Help

- Use `arxos help` for command overview
- Use `arxos help <command>` for specific command help
- Visit [examples](./examples.md) for common use cases
- Check [troubleshooting](./troubleshooting.md) for common issues

## Contributing

See our [development guide](../development/README.md) for information on contributing to the Arxos CLI.