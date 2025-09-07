# ArxOS Frontend (Optional)

The ArxOS web frontend provides an optional D3.js visualization for users who prefer a graphical interface over the terminal.

## Status

The web frontend is optional. ArxOS is terminal-first, and all functionality is available through the CLI.

## Planned Features

If implemented, the frontend would provide:

- **D3.js Building Visualization**: Interactive 2D floor plans and system diagrams
- **Query Interface**: Web-based SQL query builder
- **Real-time Updates**: WebSocket connection for live building state
- **BILT Marketplace**: Trading interface for building data access rights

## Technology Stack

- **Svelte**: Reactive UI framework
- **D3.js**: Data visualization
- **WebSocket**: Real-time updates
- **PostgreSQL**: Same database as terminal

## Architecture

```
Terminal (Primary Interface)
         |
    PostgreSQL
         |
    Web API (Optional)
         |
    Svelte + D3.js
```

## Note

The terminal interface is the primary way to interact with ArxOS. This web frontend is purely optional for users who prefer visual interfaces. All core functionality is available through the terminal.