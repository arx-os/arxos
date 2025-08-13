# Arxos Codebase Cleanup Preview

This document outlines exactly what will be removed during the comprehensive cleanup process.

## Current Codebase Size Analysis

**Total size:** ~78MB
**Target reduction:** ~70% (reducing to ~23MB)

### Directory Sizes (before cleanup):
```
31M  core/
8.3M infrastructure/
4.4M svgx_engine/
4.3M frontend/
3.8M tools/
3.1M arxide/ (TO BE REMOVED)
3.1M docs/
3.1M services/
2.3M tests/
908K application/
644K sdk/ (TO BE REMOVED)
320K api/
344K economy/
272K scripts/
132K schemas/
```

## What Will Be REMOVED

### 1. Dead Code and Abandoned Projects (3.1MB)
- **`arxide/`** - Abandoned desktop application built with Tauri/React
  - Contains 3.1MB of unused desktop app code
  - Was an attempt at creating a desktop CAD application
  - No longer maintained or used

### 2. Unused Services (~1.8MB of services/)
- **`services/ai/`** - Redundant AI service (GUS handles AI functionality)
- **`services/cmms/`** - CMMS integration (not currently used)
- **`services/construction/`** - Construction management (not implemented)
- **`services/data-vendor/`** - Data vendor integration (unused)
- **`services/partners/`** - Partner integration system (unused)
- **`services/planarx/`** - Community/marketplace system (not implemented)
- **`services/mcp/`** - MCP service (functionality moved elsewhere)

### 3. Unused Frontend Attempts (~3MB of frontend/)
- **`frontend/android/`** - Android app attempt (unused)
- **`frontend/ios/`** - iOS app attempt (unused)
- **`frontend/desktop/`** - Desktop frontend (replaced by web)
- **`frontend/fractal-demo/`** - Fractal demonstration (demo code)

### 4. Excessive Documentation (~1.5MB)
- **`docs/DEVELOPMENT/`** - Excessive development docs (keeping essential docs)
- **`reports/`** - Old analysis reports (44KB)
- **`tools/education/`** - Educational materials (not core functionality)

### 5. Test/Example Code (~644KB + examples in other dirs)
- **`sdk/`** - SDK generation code (644KB)
- **`examples/`** - Example code throughout the codebase
- **`plugins/`** - Plugin examples (8KB)
- **Various example directories** within preserved modules

## What Will Be PRESERVED

### Core Backend (31MB - KEEPING ALL)
- **`core/backend/`** - Go backend application (main system)
- **`core/arxobject/`** - ArxObject core functionality
- **`core/constraints/`** - Constraint system
- **`core/optimization/`** - Optimization algorithms
- **`core/spatial/`** - Spatial processing
- **`core/streaming/`** - Streaming engine
- **`core/security/`** - Security middleware
- **`core/shared/`** - Shared utilities

### Essential Frontend (1.3MB - keeping web only)
- **`frontend/web/`** - Main web interface (the primary UI)

### Rendering Engine (4.4MB - KEEPING ALL)
- **`svgx_engine/`** - Complete SVG-X rendering and behavior engine
  - Core rendering capabilities
  - Behavior systems
  - Parser and compiler
  - Runtime engine

### Active Services (1.3MB - keeping essential services)
- **`services/gus/`** - GUS AI agent (actively used)
- **`services/iot/`** - IoT device integration (actively used)
- **`services/arxobject/`** - ArxObject service (core functionality)
- **`services/scale-engine/`** - Scale engine for performance
- **`services/tile-server/`** - Tile server for rendering

### Infrastructure & Data (8.3MB - KEEPING ALL)
- **`infrastructure/`** - Database, caching, monitoring, repositories
- **`schemas/`** - Symbol library schemas (essential data)
- **`api/`** - API layer (essential)
- **`application/`** - Application services (essential)
- **`domain/`** - Domain models (essential)

### Essential Configuration
- **`k8s/`** - Kubernetes configurations
- **`nginx/`** - Web server configuration
- **`migrations/`** - Database migrations
- **Docker files and compose configurations**
- **`requirements.txt`, `go.mod`, etc.**

### Essential Documentation
- **`docs/`** - Keeping core architecture, API, and user documentation
- **`README.md`** and other root documentation files

## Expected Results

### Size Reduction
- **Before:** ~78MB
- **After:** ~23MB  
- **Reduction:** ~70% (55MB removed)

### Complexity Reduction
- **Services:** 10 → 5 services (50% reduction)
- **Frontend platforms:** 5 → 1 platform (80% reduction)
- **Documentation directories:** Significantly reduced
- **Example/test code:** Removed (keeping only essential tests)

## Safety Measures

1. **Complete Backup:** Everything is backed up before deletion
2. **Restoration Instructions:** Clear instructions provided for restoring any component
3. **Validation:** Script validates it's in the correct directory
4. **Error Handling:** Script stops on any error

## How to Execute

1. **Review this preview carefully**
2. **Navigate to the arxos directory:**
   ```bash
   cd /Users/joelpate/repos/arxos
   ```
3. **Run the cleanup script:**
   ```bash
   ./cleanup_script.sh
   ```
4. **Review the generated summary and backup**

## Post-Cleanup Tasks

After running the cleanup, you should:

1. Update `docker-compose.yml` to remove references to deleted services
2. Update CI/CD configurations
3. Update main `README.md` to reflect the simplified architecture
4. Test the remaining functionality
5. Update any import statements or service references

## Rollback Plan

If needed, any component can be restored from the timestamped backup directory created during cleanup. The backup will be located at `../arxos_cleanup_backup_YYYYMMDD_HHMMSS/`

---

**This cleanup will result in a lean, focused codebase that's easy for new engineers to understand while preserving all essential functionality.**