# Core System

Core ARXOS system components and business logic.

## Purpose

This directory contains the fundamental components of the ARXOS platform including the backend server, ArxObject engine, topology analysis, and semantic processing.

## Structure

```
core/
├── aql/                 # ARXOS Query Language implementation
├── arxobject/           # Core ArxObject data model and engine
├── backend/             # Go backend server and API
├── bim/                 # Building Information Modeling components
├── ingestion/           # Data ingestion and processing pipeline
├── pipeline/            # Data processing pipeline
├── semantic/            # Semantic analysis and processing
└── topology/            # Topological analysis and relationships
```

## Key Components

- **Backend**: Go-based REST API server with Chi router
- **ArxObject Engine**: Intelligent building component management
- **Topology**: Spatial and relationship analysis
- **Semantic**: AI-powered building data understanding
- **BIM**: 3D visualization and modeling

## Documentation

For detailed information, see:
- [Architecture Overview](../../docs/architecture/overview.md)
- [ArxObject System](../../docs/architecture/arxobjects.md)
- [Development Guide](../../docs/development/guide.md)
