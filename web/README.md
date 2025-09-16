# ArxOS Web Interface

## Overview

This directory contains the **current HTMX-based web interface** for ArxOS building management. It provides a web-based dashboard for building operations while maintaining the ASCII terminal aesthetic.

## Technology Stack

- **HTMX** - Dynamic HTML without JavaScript
- **Tailwind CSS** - Utility-first CSS framework  
- **Alpine.js** - Minimal client-side interactivity
- **Go Templates** - Server-side HTML generation

## Architecture

```
┌─────────────────────────────────────────┐
│           HTMX Web Interface            │
├─────────────────────────────────────────┤
│  Templates (HTML)    │  Handlers (Go)   │
│  ├─ layouts/         │  ├─ router.go    │
│  ├─ pages/           │  ├─ handlers.go  │
│  └─ partials/        │  └─ templates.go │
└─────────────────────────────────────────┘
                    │
                    ▼
        ┌──────────────────────┐
        │  ArxOS API Server    │
        │     (Go Backend)     │
        └──────────────────────┘
```

## Features

### Current HTMX Interface
- **Dashboard**: Building overview with statistics
- **Building Management**: List, view, and manage buildings
- **ASCII Floor Plans**: Terminal-style floor plan display in browser
- **Equipment Search**: Find and manage building equipment
- **Real-time Updates**: HTMX-powered dynamic content

### Key Benefits
- **No JavaScript complexity** - Pure HTMX approach
- **Terminal aesthetic** - ASCII art in web interface
- **Fast and lightweight** - Server-rendered HTML
- **Real-time updates** - HTMX handles dynamic content

## Directory Structure

```
web/
├── templates/              # HTMX templates
│   ├── layouts/
│   │   └── base.html      # Main layout with HTMX/Tailwind
│   ├── pages/
│   │   ├── dashboard.html  # Dashboard page
│   │   ├── buildings.html  # Buildings list
│   │   └── login.html     # Authentication
│   └── partials/
│       └── floor_plan.html # ASCII floor plan fragment
├── static/                # Static assets (future)
└── README.md              # This file
```

## Backend Integration

The web interface is served by Go handlers in `internal/handlers/web/`:
- **handlers.go** - HTTP request handlers
- **router.go** - Route definitions and middleware
- **templates.go** - Template loading and rendering

## Usage

The web interface is accessible when running ArxOS in server mode:

```bash
# Start ArxOS server
arx serve

# Access web interface
open http://localhost:8080
```

## Future Development

This HTMX interface focuses on **building operations and management**. For **advanced 3D visualization**, see the planned Svelte interface in `/frontend/`.

### Interface Hierarchy
1. **Terminal ASCII** - Primary interface for building operations
2. **HTMX Web** - Web-based building management (this interface)
3. **Mobile AR** - Field technician precise positioning
4. **Frontend 3D** - Advanced visualization and analysis (future)

Each interface serves different user needs in the ArxOS ecosystem.