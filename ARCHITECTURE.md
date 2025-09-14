# ArxOS Architecture

## Overview

ArxOS is a building management platform that combines database-driven operations with text-based Building-as-Code workflows. This document outlines the core technical decisions and architecture.

## Core Components

### 1. Data Storage

**Primary Format: BIM Text Files (.bim.txt)**
- Human-readable building information
- Git-versionable
- Universal addressing: `ARXOS-NA-US-NY-NYC-0001/N/3/A/301/E/OUTLET_02`

**Runtime Storage: SQLite**
- Fast queries and indexing
- Zero configuration
- Good enough for 2D floor plans + equipment

**Future: PostgreSQL + PostGIS** (when needed for):
- 3D spatial queries
- Multi-building proximity searches
- AR anchor persistence
- Heat maps and spatial analytics

### 2. CLI Tools

**Minimal Approach:**
- `bim import` - PDF to .bim.txt conversion
- `bim validate` - Schema validation
- Let Unix tools (grep, sed, awk) handle queries
- Add commands only when bash becomes painful

### 3. API Server

- REST API with SQLite backend
- JWT authentication
- Serves as bridge between database and text files
- Handles AR anchor storage (as blobs initially)

## AR/Spatial Data Strategy

### Phase 1: Simple 2D (Current)
```sql
-- SQLite: Store simple coordinates
CREATE TABLE equipment_locations (
    building_uuid TEXT,
    equipment_path TEXT,
    floor INTEGER,
    x_meters REAL,
    y_meters REAL,
    ar_anchor_blob BLOB,  -- Store raw, process later
    PRIMARY KEY (building_uuid, equipment_path)
);
```

### Phase 2: Full Spatial (Future)
```sql
-- PostgreSQL/PostGIS: When spatial queries needed
CREATE TABLE ar_anchors (
    id UUID PRIMARY KEY,
    building_uuid TEXT,
    equipment_path TEXT,
    anchor_transform GEOMETRY(PointZ, 4326),
    rotation FLOAT[]
);
```

## Data Flow

```
PDF Import → .bim.txt files → Git Repository
                ↓
            SQLite DB (cache for queries)
                ↓
            REST API
                ↓
    Web UI / Mobile App / CLI
```

## Key Principles

1. **Text files are source of truth** - Database is just a cache
2. **Start simple** - SQLite now, PostGIS when needed
3. **Unix philosophy** - Small tools that do one thing well
4. **Progressive enhancement** - Add complexity only when required

## Directory Structure

```
arxos/
├── cmd/
│   ├── bim/              # Building-as-Code CLI
│   └── arxos-server/     # API server
├── internal/
│   ├── bim/              # Parser/writer for .bim.txt
│   ├── database/         # SQLite implementation
│   └── api/              # REST endpoints
└── buildings/            # Git repo of .bim.txt files
```