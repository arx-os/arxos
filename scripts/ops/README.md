# Operational Scripts

Core operational scripts for managing the Arxos platform.

## Scripts

### start.sh
Starts all Arxos services in the correct order with proper health checks.

```bash
# Development mode (default)
./start.sh

# Production mode
./start.sh --prod

# With specific services
./start.sh --backend --ai --frontend
```

**What it does:**
1. Cleans up any existing processes
2. Starts backend server (port 8080)
3. Starts AI service (port 8000)
4. Starts frontend (port 3000)
5. Performs health checks
6. Shows service status

### clean.sh
Stops all services and cleans up resources.

```bash
# Basic cleanup
./clean.sh

# Deep clean (includes logs and temp files)
./clean.sh --deep

# Clean specific service
./clean.sh --service backend
```

**What it does:**
1. Stops all running services
2. Kills orphaned processes
3. Cleans up PID files
4. Optionally removes logs and temp files

### manage-access.sh
Manages authentication and access control.

```bash
# Add new admin user
./manage-access.sh add-admin user@example.com

# Reset admin password
./manage-access.sh reset-password admin

# Generate API key
./manage-access.sh generate-key service-name

# List active sessions
./manage-access.sh list-sessions
```

## Service Management

### Service Dependencies
```
Frontend (3000) ─┐
                 ├─> Backend (8080) ─> Database (5432)
AI Service (8000)┘                  └─> Redis (6379)
```

### Health Checks
All scripts include health checks:
- Backend: `GET /health`
- AI Service: `GET /health`
- Database: Connection test
- Redis: PING command

### Logging
- Service logs: `/var/log/arxos/`
- Script logs: `/tmp/arxos-ops-*.log`
- Error logs: `stderr` to console

## Environment Variables

```bash
# Service configuration
ARXOS_ENV=development|staging|production
BACKEND_PORT=8080
AI_SERVICE_PORT=8000
FRONTEND_PORT=3000

# Timeouts
STARTUP_TIMEOUT=30
HEALTH_CHECK_RETRIES=10

# Logging
LOG_LEVEL=debug|info|warn|error
LOG_DIR=/var/log/arxos
```

## Troubleshooting

### Service won't start
1. Check port availability: `lsof -i :8080`
2. Run cleanup: `./clean.sh`
3. Check logs: `tail -f /var/log/arxos/*.log`

### Database connection issues
1. Check PostgreSQL status: `pg_isready`
2. Verify credentials in `.env`
3. Check network connectivity

### Permission denied
```bash
chmod +x *.sh
```

## Best Practices

1. **Always use start.sh** to launch services
2. **Run clean.sh** before deployment
3. **Check health endpoints** after startup
4. **Monitor logs** during operations
5. **Use --dry-run** for testing changes