# ArxOS GitHub Actions

This directory contains reusable GitHub Actions for the ArxOS "Git for Buildings" project. These actions provide automated workflows for IFC processing, spatial validation, building reporting, and equipment monitoring.

## 🚀 Available Actions

### 1. IFC Processor (`ifc-processor`)
Converts IFC files to YAML equipment data and commits to Git.

**Features:**
- ✅ IFC file validation
- ✅ YAML data generation
- ✅ Automatic Git commits
- ✅ Spatial validation
- ✅ Processing reports

**Usage:**
```yaml
- uses: ./.github/actions/ifc-processor
  with:
    ifc-file: 'path/to/building.ifc'
    output-dir: 'building-data'
    commit-message: 'Import building: {ifc-file}'
    validate-spatial: 'true'
```

### 2. Spatial Validator (`spatial-validator`)
Validates spatial coordinates and equipment placement.

**Features:**
- ✅ Coordinate system validation
- ✅ Universal path checking
- ✅ Spatial tolerance validation
- ✅ Comprehensive error reporting

**Usage:**
```yaml
- uses: ./.github/actions/spatial-validator
  with:
    data-path: 'building-data'
    tolerance: '0.1'
    check-coordinate-systems: 'true'
    check-universal-paths: 'true'
    fail-on-errors: 'true'
```

### 3. Building Reporter (`building-reporter`)
Generates comprehensive building status reports and analytics.

**Features:**
- ✅ Multiple report types (status, energy, equipment, summary)
- ✅ Multiple output formats (markdown, json, html)
- ✅ Equipment and room analytics
- ✅ Automatic Git commits

**Usage:**
```yaml
- uses: ./.github/actions/building-reporter
  with:
    data-path: 'building-data'
    report-type: 'summary'
    output-format: 'markdown'
    commit-report: 'true'
```

### 4. Equipment Monitor (`equipment-monitor`)
Monitors equipment health and generates alerts for critical issues.

**Features:**
- ✅ Real-time equipment monitoring
- ✅ Configurable alert thresholds
- ✅ GitHub issue creation
- ✅ Webhook notifications
- ✅ Dry-run mode

**Usage:**
```yaml
- uses: ./.github/actions/equipment-monitor
  with:
    data-path: 'building-data'
    monitoring-interval: '60'
    alert-thresholds: '{"temperature": {"min": 15, "max": 25}}'
    create-issues: 'true'
    issue-labels: 'equipment-alert,critical'
```

## 📋 Workflow Examples

### Complete IFC Import Workflow
```yaml
name: Import IFC Building Data

on:
  workflow_dispatch:
    inputs:
      ifc_file:
        description: 'Path to IFC file'
        required: true

jobs:
  import-and-validate:
    runs-on: ubuntu-latest
    steps:
      - name: Process IFC file
        uses: ./.github/actions/ifc-processor
        with:
          ifc-file: ${{ github.event.inputs.ifc_file }}
          output-dir: 'building-data'
      
      - name: Validate spatial data
        uses: ./.github/actions/spatial-validator
        with:
          data-path: 'building-data'
      
      - name: Generate report
        uses: ./.github/actions/building-reporter
        with:
          data-path: 'building-data'
          report-type: 'summary'
```

### Automated Monitoring Workflow
```yaml
name: Equipment Health Monitoring

on:
  schedule:
    - cron: '0 * * * *'  # Every hour

jobs:
  monitor:
    runs-on: ubuntu-latest
    steps:
      - name: Monitor equipment
        uses: ./.github/actions/equipment-monitor
        with:
          data-path: 'building-data'
          create-issues: 'true'
```

## 🔧 Configuration

### Environment Variables
- `GITHUB_TOKEN`: Required for Git operations and issue creation
- `WEBHOOK_URL`: Optional webhook for external notifications

### Input Parameters

#### IFC Processor
| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `ifc-file` | ✅ | - | Path to IFC file |
| `output-dir` | ❌ | `building-data` | Output directory |
| `commit-message` | ❌ | `Process IFC file: {ifc-file}` | Git commit message |
| `validate-spatial` | ❌ | `true` | Enable spatial validation |

#### Spatial Validator
| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `data-path` | ✅ | - | Path to building data |
| `tolerance` | ❌ | `0.1` | Validation tolerance (meters) |
| `check-coordinate-systems` | ❌ | `true` | Validate coordinate systems |
| `check-universal-paths` | ❌ | `true` | Validate universal paths |
| `fail-on-errors` | ❌ | `true` | Fail on validation errors |

#### Building Reporter
| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `data-path` | ✅ | - | Path to building data |
| `report-type` | ❌ | `summary` | Type of report |
| `output-format` | ❌ | `markdown` | Output format |
| `commit-report` | ❌ | `true` | Commit report to Git |

#### Equipment Monitor
| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `data-path` | ✅ | - | Path to building data |
| `monitoring-interval` | ❌ | `60` | Interval in minutes |
| `alert-thresholds` | ❌ | `{"temperature": {"min": 15, "max": 25}}` | JSON thresholds |
| `create-issues` | ❌ | `true` | Create GitHub issues |
| `dry-run` | ❌ | `false` | Dry-run mode |

## 📊 Outputs

Each action provides structured outputs for use in subsequent steps:

### IFC Processor Outputs
- `processed-files`: Number of YAML files created
- `commit-hash`: Git commit hash
- `processing-time`: Processing time in seconds

### Spatial Validator Outputs
- `validation-passed`: Boolean validation result
- `errors-found`: Number of errors
- `warnings-found`: Number of warnings
- `validation-time`: Validation time in seconds

### Building Reporter Outputs
- `report-path`: Path to generated report
- `report-size`: Report size in bytes
- `equipment-count`: Equipment items analyzed
- `rooms-count`: Rooms analyzed

### Equipment Monitor Outputs
- `equipment-monitored`: Equipment items monitored
- `alerts-generated`: Number of alerts
- `issues-created`: GitHub issues created
- `critical-alerts`: Critical alerts found

## 🛠️ Development

### Adding New Actions
1. Create a new directory in `.github/actions/`
2. Add `action.yml` with proper metadata
3. Implement the action logic
4. Add tests and documentation
5. Update this README

### Testing Actions
```bash
# Test locally with act (if available)
act -j import-ifc

# Test individual action
act -j validate-spatial
```

## 📚 Best Practices

1. **Error Handling**: Always provide meaningful error messages
2. **Logging**: Use structured logging for debugging
3. **Caching**: Cache Rust dependencies for faster builds
4. **Security**: Use minimal permissions and validate inputs
5. **Documentation**: Keep action descriptions up to date
6. **Testing**: Test actions with various input combinations

## 🔗 Related Documentation

- [ArxOS Architecture](../ARXOS_ARCHITECTURE_V2.md)
- [Development Roadmap](../DEVELOPMENT_ROADMAP.md)
- [IFC Processing Guide](../docs/ifc_processing.md)

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](../LICENSE) file for details.
