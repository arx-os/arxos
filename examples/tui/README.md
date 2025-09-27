# ArxOS TUI Examples

This directory contains practical examples demonstrating how to use the ArxOS Terminal User Interface (TUI) for various building management workflows.

## Examples

### 🏗️ Building Inspection Workflow
**File**: `building-inspection.sh`

A comprehensive building inspection workflow that demonstrates:
- Dashboard overview for building status
- Building explorer for hierarchical navigation
- Equipment manager for detailed equipment analysis
- Floor plan visualization for spatial analysis
- Spatial queries for location-based analysis

**Usage**:
```bash
# Basic inspection
./building-inspection.sh

# Custom building ID
./building-inspection.sh ARXOS-002

# Custom building ID and inspector
./building-inspection.sh ARXOS-002 "John Doe"
```

**Features**:
- Step-by-step guided workflow
- Error handling and validation
- TUI configuration management
- Progress tracking
- Optional report generation

### ⚙️ Equipment Monitoring Workflow
**File**: `equipment-monitoring.sh`

A continuous equipment monitoring system that demonstrates:
- Real-time equipment status monitoring
- Alert detection and threshold management
- Automated TUI investigation workflows
- Periodic detailed analysis
- Spatial analysis integration

**Usage**:
```bash
# Basic monitoring (30-second intervals)
./equipment-monitoring.sh

# Custom building ID
./equipment-monitoring.sh ARXOS-002

# Custom interval and alert threshold
./equipment-monitoring.sh ARXOS-002 60 10
```

**Features**:
- Continuous monitoring loop
- Alert detection and escalation
- Automated investigation workflows
- Periodic detailed analysis
- Configurable thresholds

## Configuration

### Environment Variables

Both examples use environment variables for configuration:

```bash
# Core TUI settings
export ARXOS_TUI_ENABLED=true
export ARXOS_TUI_THEME=dark
export ARXOS_TUI_UPDATE_INTERVAL=1s

# Performance settings
export ARXOS_TUI_MAX_EQUIPMENT=1000
export ARXOS_TUI_REAL_TIME=true
export ARXOS_TUI_ANIMATIONS=true

# UI settings
export ARXOS_TUI_COMPACT_MODE=false
export ARXOS_TUI_SHOW_COORDINATES=true
export ARXOS_TUI_SHOW_CONFIDENCE=true
```

### Customization

You can customize the examples by modifying:

1. **Building IDs**: Change default building IDs
2. **Intervals**: Adjust monitoring intervals
3. **Thresholds**: Modify alert thresholds
4. **TUI Settings**: Customize TUI behavior
5. **Workflows**: Add or remove workflow steps

## Integration

### CI/CD Integration

These examples can be integrated into CI/CD pipelines:

```yaml
# GitHub Actions example
- name: Building Inspection
  run: |
    export ARXOS_TUI_ENABLED=true
    export ARXOS_TUI_COMPACT_MODE=true
    ./examples/tui/building-inspection.sh ${{ env.BUILDING_ID }}
```

### Cron Jobs

For automated monitoring:

```bash
# Add to crontab for daily inspections
0 9 * * * /path/to/arxos/examples/tui/building-inspection.sh ARXOS-001

# Add to crontab for hourly monitoring
0 * * * * /path/to/arxos/examples/tui/equipment-monitoring.sh ARXOS-001 3600 5
```

### Docker Integration

```dockerfile
# Dockerfile example
FROM golang:1.19-alpine

COPY . /app
WORKDIR /app

# Install ArxOS
RUN go build -o arx ./cmd/arx

# Copy examples
COPY examples/tui/ /app/examples/tui/
RUN chmod +x /app/examples/tui/*.sh

# Set default command
CMD ["./examples/tui/building-inspection.sh"]
```

## Best Practices

### Error Handling

- Always check return codes
- Provide meaningful error messages
- Log errors for debugging
- Gracefully handle TUI failures

### Performance

- Use appropriate update intervals
- Limit equipment display for large buildings
- Disable animations on slow terminals
- Use compact mode for limited screen space

### Security

- Validate input parameters
- Use environment variables for secrets
- Implement proper access controls
- Log security events

### Monitoring

- Track workflow execution times
- Monitor equipment status changes
- Log alert frequencies
- Generate performance reports

## Troubleshooting

### Common Issues

#### TUI Not Starting
```bash
# Check if TUI is enabled
echo $ARXOS_TUI_ENABLED

# Verify terminal compatibility
echo $TERM

# Test with demo mode
./arx visualize --tui --demo
```

#### Performance Issues
```bash
# Reduce update frequency
export ARXOS_TUI_UPDATE_INTERVAL=5s

# Disable animations
export ARXOS_TUI_ANIMATIONS=false

# Use compact mode
export ARXOS_TUI_COMPACT_MODE=true
```

#### Script Errors
```bash
# Check script permissions
ls -la examples/tui/*.sh

# Run with debug output
bash -x examples/tui/building-inspection.sh

# Check logs
tail -f ~/.arxos/logs/tui.log
```

### Debug Mode

Enable debug mode for detailed logging:

```bash
# Environment variable
export ARXOS_TUI_DEBUG=true

# Command line flag
./arx visualize --tui --debug
```

## Contributing

To add new examples:

1. **Create script file**: `example-name.sh`
2. **Add shebang**: `#!/bin/bash`
3. **Set executable**: `chmod +x example-name.sh`
4. **Add error handling**: `set -e`
5. **Document usage**: Add comments and help text
6. **Update README**: Add description and usage

### Script Template

```bash
#!/bin/bash
# Example Description
# This script demonstrates...

set -e

echo "🚀 Example Title"
echo "================"
echo

# Configuration
PARAM1="${1:-default}"
PARAM2="${2:-default}"

echo "Parameter 1: $PARAM1"
echo "Parameter 2: $PARAM2"
echo

# Set TUI configuration
export ARXOS_TUI_ENABLED="true"
export ARXOS_TUI_THEME="dark"

# Function to run TUI command
run_tui() {
    local mode="$1"
    local description="$2"
    
    echo "🚀 Starting $description..."
    
    if ! ./arx visualize $mode --tui; then
        echo "❌ Failed to start $description"
        return 1
    fi
    
    echo "✅ $description completed"
}

# Main workflow
echo "Starting workflow..."
run_tui "" "Dashboard"

echo "✅ Example completed successfully!"
```

## Support

For help with examples:

1. **Check logs**: `~/.arxos/logs/tui.log`
2. **Enable debug**: `export ARXOS_TUI_DEBUG=true`
3. **Test components**: Run individual TUI modes
4. **Report issues**: GitHub Issues with example details

---

**Ready to explore?** Start with the building inspection workflow:

```bash
./examples/tui/building-inspection.sh
```
