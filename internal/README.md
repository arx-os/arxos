# Internal Packages

This directory contains the private application code for Arxos. These packages are not intended to be imported by external projects.

## Package Structure

### Core Business Logic
- **`core/`** - Domain models and business logic for buildings, equipment, and users
- **`services/`** - Business services including auth, sync, and building management
- **`database/`** - Database abstraction layer and SQLite implementation

### API & Web
- **`api/`** - REST API server, handlers, and middleware
  - `handlers/` - HTTP request handlers
  - `services/` - API-specific services
- **`web/`** - HTMX web interface handlers and templates
- **`middleware/`** - HTTP middleware (auth, rate limiting, validation)

### Data Processing
- **`import/`** - File importers (PDF, IFC, OCR)
- **`rendering/`** - ASCII and SVG rendering engines
- **`search/`** - Search indexing and query engine

### Infrastructure
- **`daemon/`** - Background service for file watching and sync
- **`config/`** - Configuration management
- **`storage/`** - File storage abstraction
- **`email/`** - Email notification service

### Utilities
- **`common/`** - Shared utilities
  - `logger/` - Logging utilities
  - `state/` - State management
  - `vcs/` - Version control integration
  - `output/` - Output formatting

### Monitoring & Maintenance
- **`connections/`** - Equipment connection graph analysis
- **`maintenance/`** - Predictive maintenance algorithms
- **`monitoring/`** - System monitoring and alerts
- **`recovery/`** - Error recovery handlers

### Archived/Experimental
- **`_archive/`** - Experimental or deprecated packages (not used in production)

## Package Dependencies

```
┌─────────────┐
│   api/      │──────────┐
└──────┬──────┘          │
       │                 ▼
       │          ┌─────────────┐
       │          │  services/  │
       │          └──────┬──────┘
       │                 │
       ▼                 ▼
┌─────────────┐   ┌─────────────┐
│  database/  │◄──│    core/    │
└─────────────┘   └─────────────┘
```

## Guidelines

1. **No Circular Dependencies** - Packages must not import each other circularly
2. **Clear Interfaces** - Use interfaces for abstraction between layers
3. **Single Responsibility** - Each package should have one clear purpose
4. **Documentation** - All exported types and functions must have godoc comments
5. **Testing** - Each package should have corresponding test files

## Import Rules

- `api/` can import from `services/`, `database/`, `core/`
- `services/` can import from `database/`, `core/`
- `database/` can import from `core/` only
- `core/` should not import from other internal packages
- `common/` utilities can be imported by any package
- `_archive/` packages should not be imported

## Package Sizes

Target package sizes:
- Small: 1-3 files (utilities)
- Medium: 4-8 files (focused features)
- Large: 9-15 files (major subsystems)
- Too Large: >15 files (consider splitting)