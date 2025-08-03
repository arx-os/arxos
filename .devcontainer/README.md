# Arxos Development Container

This directory contains the configuration for the Arxos development container environment.

## Files

- `devcontainer.json` - Main configuration file for the development container
- `setup.sh` - Post-creation setup script that installs tools and dependencies
- `data/` - Directory for persistent data storage (PostgreSQL, Redis, logs)

## Prerequisites

Before using the development container, ensure you have:

1. **Docker Desktop** installed and running
2. **VS Code** or **Cursor** with the Dev Containers extension
3. **Git** installed

## Troubleshooting

### Common Issues

1. **Container fails to start**
   - Ensure Docker Desktop is running
   - Check that you have sufficient disk space
   - Verify Docker has proper permissions

2. **Mount errors**
   - The `.devcontainer/data` directory must exist
   - Ensure Docker has access to the project directory

3. **Setup script failures**
   - Check the container logs for specific error messages
   - Some package installations may fail due to network issues
   - The script will continue even if some optional tools fail to install

4. **Docker-in-Docker issues**
   - Ensure Docker Desktop is running
   - Check that Docker has proper permissions
   - The container needs privileged access for Docker-in-Docker

### Manual Setup

If the automatic setup fails, you can manually run the setup script:

```bash
bash .devcontainer/setup.sh
```

### Environment Variables

The setup script creates a `.env` file with the following services:

- **Browser CAD**: http://localhost:3000
- **ArxIDE**: http://localhost:3001
- **Backend API**: http://localhost:8080
- **GUS Agent**: http://localhost:8000
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6379

## Development Tools

The container includes the following development tools:

- **Go 1.24** with goimports, golangci-lint, and delve
- **Python 3.11** with black, flake8, mypy, pytest, and FastAPI
- **Node.js 20** with TypeScript, ESLint, Prettier, and Tailwind CSS
- **Rust 1.75** with rustfmt, clippy, and cargo-watch
- **Docker and Docker Compose**
- **Git and GitHub CLI**

## Data Persistence

The `.devcontainer/data` directory is mounted into the container at `/workspaces/data` and contains:

- `postgres/` - PostgreSQL data files
- `redis/` - Redis data files
- `logs/` - Application log files

This ensures that data persists between container restarts. 