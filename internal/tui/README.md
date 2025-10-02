# ArxOS TUI Package

This package implements the Terminal User Interface (TUI) for ArxOS using the Bubble Tea framework.

## Architecture

The TUI follows clean architecture principles with clear separation of concerns:

```
tui/
├── main.go              # TUI entry points and initialization
├── models/              # Bubble Tea models (state management)
│   ├── dashboard.go     # Main dashboard model
│   ├── building.go      # Building explorer model
│   ├── equipment.go     # Equipment management model
│   └── query.go         # Spatial query interface model
├── components/          # Reusable TUI components
│   ├── progress.go      # Progress bars and spinners
│   ├── status.go        # Status indicators
│   ├── spatial_view.go  # Spatial data visualization
│   ├── equipment_list.go # Equipment listing
│   └── alerts.go        # Alert notifications
├── services/            # TUI-specific services
│   ├── postgis_client.go # PostGIS integration for TUI
│   ├── real_time.go     # Real-time data updates
│   └── spatial_renderer.go # Spatial data rendering
├── utils/               # TUI utilities
│   ├── styles.go        # Lip Gloss styling
│   ├── layout.go        # Layout utilities
│   └── events.go        # Event handling
└── config.go           # TUI configuration
```

## Design Principles

1. **Clean Architecture**: Clear separation between models, components, and services
2. **Go Conventions**: Follow standard Go package organization and naming
3. **Performance**: Efficient rendering and minimal resource usage
4. **Maintainability**: Modular, testable, and extensible code
5. **User Experience**: Professional, intuitive interface

## Integration

The TUI integrates seamlessly with existing CLI commands:
- Commands can be run with `--tui` flag for interactive mode
- Maintains full CLI compatibility for automation
- Shares configuration and services with CLI layer

## Usage

```bash
# Interactive dashboard
arx visualize dashboard --tui

# Interactive equipment management
arx query equipment --tui

# Interactive building explorer
arx repo status --tui
```
