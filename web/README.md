# ArxOS Web Interface

## Overview

This directory contains the **HTMX-based web interface** for ArxOS building management. It provides a clean, functional interface for building operations - similar to how GitHub provides repository management.

## Technology Stack

- **HTMX** - Dynamic HTML without JavaScript
- **Tailwind CSS** - Utility-first CSS framework
- **Go Templates** - Server-side HTML generation
- **Pure CSS** - For UI interactions (no JavaScript)

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

### Features
- **Dashboard**: Building overview with statistics
- **Building Management**: List, view, and manage buildings
- **ASCII Floor Plans**: Terminal-style floor plan display
- **Equipment Search**: Find and manage building equipment
- **Real-time Updates**: HTMX-powered dynamic content

### Design Philosophy
- **No JavaScript** - Pure HTML/CSS/HTMX approach
- **Functional over fancy** - Like GitHub for buildings
- **Server-side rendering** - Fast and reliable
- **Progressive enhancement** - Works everywhere

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

## Interface Philosophy

ArxOS follows the GitHub model - a functional web interface for managing complex data structures. Just as developers use GitHub to manage code repositories, building operators use ArxOS to manage building infrastructure.

The interface prioritizes:
- **Clarity** over complexity
- **Function** over form
- **Speed** over effects
- **Reliability** over novelty

No JavaScript frameworks, no build steps, no client-side state management. Just clean, server-rendered HTML with HTMX for dynamic updates.