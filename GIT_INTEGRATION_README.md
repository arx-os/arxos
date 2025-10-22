# ArxOS Git Integration

This document describes the Git integration capabilities of ArxOS, which enables building data to be stored and synchronized with Git repositories (GitHub, GitLab, or local repositories).

## Overview

ArxOS Git integration provides a bridge between the PostGIS database (operational data) and Git repositories (version control and collaboration). This enables:

- **Version Control**: Track changes to building configurations over time
- **Collaboration**: Multiple team members can work on building data simultaneously
- **CI/CD Integration**: Automated workflows using GitHub Actions or GitLab CI
- **Backup & Recovery**: Git repositories serve as distributed backups
- **Audit Trail**: Complete history of who changed what and when

## Architecture

The Git integration follows a hybrid architecture:

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   PostGIS DB    │◄──►│   ArxOS Core     │◄──►│  Git Repository │
│ (Operational)   │    │   (Sync Layer)   │    │ (Version Ctrl)  │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

- **PostGIS**: Primary operational database for real-time data, spatial queries, and IFC processing
- **Git Repository**: Version control layer for configuration, collaboration, and automation
- **ArxOS Sync Layer**: Bidirectional synchronization between PostGIS and Git

## Data Format

Building data is stored in Git repositories using YAML files following a Kubernetes-style manifest format:

### Building Configuration (`building.yml`)
```yaml
apiVersion: arxos.io/v1
kind: Building
metadata:
  name: "Empire State Building"
  id: "bldg_empire-state"
  createdAt: "2024-01-01T00:00:00Z"
  updatedAt: "2024-01-01T00:00:00Z"
spec:
  address: "350 5th Ave, New York, NY 10118"
  coordinates:
    x: 0.0
    y: 0.0
    z: 0.0
status:
  phase: Active
```

### Equipment Configuration (`equipment/B1/3/301/HVAC/VAV-301.yml`)
```yaml
apiVersion: arxos.io/v1
kind: Equipment
metadata:
  name: "VAV Unit 301"
  path: "/B1/3/301/HVAC/VAV-301"
  id: "eq_vav-301"
spec:
  manufacturer: "Carrier"
  model: "VAV-301"
  serial_number: "SN123456"
  location:
    x: 10.5
    y: 15.2
    z: 2.8
  capacity:
    cfm: 1200
  setpoints:
    cooling: 72.0
    heating: 68.0
status:
  operational_state: Active
  health: Good
  last_updated: "2024-01-01T00:00:00Z"
```

## Universal Path System

ArxOS uses a universal path system for addressing building components:

```
/BUILDING/FLOOR/ROOM/SYSTEM/EQUIPMENT
```

Examples:
- `/B1/3/301/HVAC/VAV-301` - VAV unit in room 301, floor 3, building B1
- `/EMPIRE-STATE/ROOF/MER-NORTH/HVAC/AHU-01` - Air handling unit on roof
- `/CAMPUS-WEST/1/101/LIGHTS/ZONE-A` - Lighting zone in room 101

These paths are automatically converted to Git file paths:
- `/B1/3/301/HVAC/VAV-301` → `equipment/B1/3/301/HVAC/VAV-301.yml`

## CLI Commands

### Export Building Data to Git
```bash
# Export to remote GitHub repository
arx export --to-git B1 --repo-url https://github.com/company/building-b1

# Export to local Git repository
arx export --to-git B1 --local-path ./building-repos/b1

# Export with custom branch and commit message
arx export --to-git B1 --repo-url https://github.com/company/building-b1 --branch feature/update-hvac --commit-message "Update HVAC configuration"
```

### Import Building Data from Git
```bash
# Import from remote GitHub repository
arx import --from-git https://github.com/company/building-b1 --repository B1

# Import from local Git repository
arx import --from-git --local-path ./building-repos/b1 --repository B1

# Import with overwrite
arx import --from-git https://github.com/company/building-b1 --repository B1 --overwrite
```

### Synchronize Building Data
```bash
# Bidirectional sync (default)
arx sync B1 --repo-url https://github.com/company/building-b1

# Push only (ArxOS → Git)
arx sync B1 --repo-url https://github.com/company/building-b1 --direction push

# Pull only (Git → ArxOS)
arx sync B1 --repo-url https://github.com/company/building-b1 --direction pull

# Dry run to see what would be synced
arx sync B1 --repo-url https://github.com/company/building-b1 --dry-run
```

## Git Providers

ArxOS supports multiple Git providers:

### GitHub Provider
- **Authentication**: Personal Access Token (`GITHUB_TOKEN` environment variable)
- **Features**: Full API support including Pull Requests, Issues, Workflows
- **Rate Limits**: Respects GitHub API rate limits

### GitLab Provider
- **Authentication**: Personal Access Token (`GITLAB_TOKEN` environment variable)
- **Features**: Basic Git operations (advanced features require additional implementation)
- **Status**: Placeholder implementation (returns "not implemented" errors)

### Local Provider
- **Authentication**: None required
- **Features**: Full local Git operations using go-git
- **Use Case**: Development, testing, and offline scenarios

## Repository Structure

A typical building repository structure:

```
building-repo/
├── building.yml                    # Building configuration
├── floors/                         # Floor configurations
│   ├── B1/
│   │   ├── 1.yml
│   │   ├── 2.yml
│   │   └── 3.yml
│   └── B2/
│       ├── 1.yml
│       └── 2.yml
├── rooms/                          # Room configurations
│   ├── B1/
│   │   ├── 1/
│   │   │   ├── 101.yml
│   │   │   ├── 102.yml
│   │   │   └── 103.yml
│   │   └── 2/
│   │       ├── 201.yml
│   │       └── 202.yml
│   └── B2/
│       └── 1/
│           ├── 101.yml
│           └── 102.yml
├── equipment/                      # Equipment configurations
│   ├── B1/
│   │   ├── 1/
│   │   │   ├── 101/
│   │   │   │   ├── HVAC/
│   │   │   │   │   ├── VAV-101.yml
│   │   │   │   │   └── RTU-101.yml
│   │   │   │   ├── ELECTRICAL/
│   │   │   │   │   ├── Panel-101.yml
│   │   │   │   │   └── Outlet-101.yml
│   │   │   │   └── PLUMBING/
│   │   │   │       ├── Toilet-101.yml
│   │   │   │       └── Sink-101.yml
│   │   │   └── 102/
│   │   │       └── HVAC/
│   │   │           └── VAV-102.yml
│   │   └── 2/
│   │       └── 201/
│   │           └── HVAC/
│   │               └── VAV-201.yml
│   └── B2/
│       └── 1/
│           └── 101/
│               └── HVAC/
│                   └── VAV-101.yml
├── .github/                        # GitHub Actions workflows
│   └── workflows/
│       ├── sync.yml               # Hourly sync with ArxOS
│       ├── alerts.yml             # Alert on configuration changes
│       └── energy-optimization.yml # Energy optimization workflow
└── README.md                       # Repository documentation
```

## GitHub Actions Integration

### Hourly Sync Workflow (`.github/workflows/sync.yml`)
```yaml
name: Sync with ArxOS
on:
  schedule:
    - cron: '0 * * * *'  # Every hour
  workflow_dispatch:

jobs:
  sync:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Sync with ArxOS
        run: |
          arx sync ${{ github.repository }} --repo-url ${{ github.server_url }}/${{ github.repository }}
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

### Alert Workflow (`.github/workflows/alerts.yml`)
```yaml
name: Configuration Alerts
on:
  push:
    paths:
      - 'equipment/**/*.yml'
      - 'building.yml'

jobs:
  alert:
    runs-on: ubuntu-latest
    steps:
      - name: Send Alert
        run: |
          echo "Building configuration changed in ${{ github.repository }}"
          # Send notification to building management system
```

## Best Practices

### 1. Branch Strategy
- **`main`**: Stable, production-ready configurations
- **`feature/*`**: Planned changes and improvements
- **`emergency/*`**: Emergency fixes and immediate actions
- **`realtime/*`**: Ephemeral sensor data and real-time updates

### 2. Commit Messages
Use descriptive commit messages:
```bash
# Good
arx export --to-git B1 --commit-message "Update HVAC setpoints for energy optimization"

# Bad
arx export --to-git B1 --commit-message "update"
```

### 3. File Organization
- Keep related equipment in the same directory structure
- Use consistent naming conventions
- Include metadata for traceability

### 4. Security
- Use environment variables for tokens
- Never commit sensitive data (passwords, API keys)
- Use repository secrets for CI/CD

## Error Handling

The Git integration includes comprehensive error handling:

### Common Errors
- **Authentication failures**: Check token validity and permissions
- **Rate limit exceeded**: Implement exponential backoff
- **Network issues**: Retry with circuit breaker pattern
- **Merge conflicts**: Manual resolution required

### Error Recovery
```bash
# Check repository status
arx sync B1 --repo-url https://github.com/company/building-b1 --dry-run

# Force push (use with caution)
arx sync B1 --repo-url https://github.com/company/building-b1 --direction push --overwrite
```

## Performance Considerations

### File Operations
- **Write Performance**: ~750 files/sec for local Git operations
- **Read Performance**: ~118,000 files/sec for local Git operations
- **Network Operations**: Limited by Git provider API rate limits

### Optimization Strategies
- Use local Git repositories for development
- Batch operations when possible
- Implement caching for frequently accessed data
- Use shallow clones for large repositories

## Testing

The Git integration includes comprehensive test coverage:

### Unit Tests
- YAML serialization/deserialization
- Path conversion functions
- Git provider operations

### Integration Tests
- End-to-end sync workflows
- Multi-provider compatibility
- Error handling scenarios
- Performance benchmarks

### Running Tests
```bash
# Run all Git integration tests
go test ./internal/serialization/ ./internal/infrastructure/git/ ./internal/cli/commands/integration/ -v

# Run specific test categories
go test ./internal/serialization/ -v
go test ./internal/infrastructure/git/ -v
go test ./internal/cli/commands/integration/ -v
```

## Troubleshooting

### Common Issues

1. **"Failed to create Git provider"**
   - Check configuration parameters
   - Verify authentication tokens
   - Ensure repository exists

2. **"Clean working tree" error**
   - Normal behavior when no changes to commit
   - Indicates successful sync with no modifications

3. **"Unsupported Git provider"**
   - Check provider type spelling
   - Ensure provider is implemented

4. **"Repository not found"**
   - Verify repository URL
   - Check authentication permissions
   - Ensure repository exists

### Debug Mode
```bash
# Enable verbose output
arx sync B1 --repo-url https://github.com/company/building-b1 --verbose

# Dry run to see operations
arx sync B1 --repo-url https://github.com/company/building-b1 --dry-run
```

## Future Enhancements

### Planned Features
- **GitLab Full Implementation**: Complete GitLab API support
- **Bitbucket Provider**: Support for Bitbucket repositories
- **Conflict Resolution**: Automated merge conflict resolution
- **Real-time Sync**: WebSocket-based real-time synchronization
- **Mobile Integration**: SMS/MMS field updates to Git repositories

### Advanced Workflows
- **Automated Testing**: CI/CD integration for building data validation
- **Deployment Pipelines**: Staged deployment of building configurations
- **Monitoring Integration**: Real-time monitoring of Git operations
- **Analytics**: Usage analytics and performance metrics

## Contributing

To contribute to the Git integration:

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/git-integration-enhancement`
3. **Make changes**: Follow Go best practices and existing patterns
4. **Add tests**: Ensure comprehensive test coverage
5. **Submit PR**: Include description of changes and test results

### Development Setup
```bash
# Clone repository
git clone https://github.com/arx-os/arxos.git
cd arxos

# Install dependencies
go mod download

# Run tests
go test ./internal/serialization/ ./internal/infrastructure/git/ ./internal/cli/commands/integration/ -v

# Build CLI
go build -o arx ./cmd/arx
```

## License

This Git integration is part of ArxOS and follows the same license terms as the main project.
