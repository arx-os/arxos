# ArxOS CLI Reference

## Overview

The ArxOS CLI (`arx`) provides command-line access to all building management functionality. It follows a hierarchical command structure with subcommands for different modules and operations.

## Installation

### From Source
```bash
git clone https://github.com/arx-os/arxos.git
cd arxos
go build -o arx cmd/arx/main.go
```

### From Binary
```bash
# Download latest release
curl -L https://github.com/arx-os/arxos/releases/latest/download/arx-linux-amd64 -o arx
chmod +x arx
sudo mv arx /usr/local/bin/
```

## Configuration

### Initial Setup
```bash
arx config init
```

This creates a configuration file at `~/.arxos/config.yaml`:

```yaml
api:
  base_url: "https://api.arxos.com"
  api_key: "your-api-key"
  timeout: 30s

auth:
  username: "your-username"
  password: "your-password"

logging:
  level: "info"
  format: "json"
  output: "stdout"

cache:
  enabled: true
  ttl: "1h"
  max_size: "100MB"
```

### Authentication
```bash
# Login with username/password
arx auth login

# Set API key
arx config set api.api_key "your-api-key"

# Check authentication status
arx auth status
```

## Global Options

All commands support these global options:

- `--config, -c`: Configuration file path
- `--verbose, -v`: Verbose output
- `--quiet, -q`: Quiet output
- `--output, -o`: Output format (json, yaml, table)
- `--help, -h`: Show help
- `--version`: Show version

## Analytics Commands

### Energy Analytics

#### Get Energy Data
```bash
# Get energy consumption data
arx analytics energy data --building main --start 2024-01-01 --end 2024-01-31

# Get energy data for specific room
arx analytics energy data --room "/buildings/main/floors/2/rooms/classroom-205"

# Get real-time energy data
arx analytics energy data --realtime

# Export energy data to CSV
arx analytics energy data --building main --format csv --output energy_data.csv
```

#### Energy Recommendations
```bash
# Get energy optimization recommendations
arx analytics energy recommendations --building main

# Get recommendations for specific room
arx analytics energy recommendations --room "/buildings/main/floors/2/rooms/classroom-205"

# Get high-priority recommendations only
arx analytics energy recommendations --priority high
```

#### Energy Baselines
```bash
# Calculate energy baselines
arx analytics energy baseline --building main --period 30d

# Update energy baselines
arx analytics energy baseline --update --building main
```

### Predictive Analytics

#### Generate Forecasts
```bash
# Generate energy consumption forecast
arx analytics forecast energy --building main --duration 7d

# Generate occupancy forecast
arx analytics forecast occupancy --room "/buildings/main/floors/2/rooms/classroom-205" --duration 24h

# Generate maintenance forecast
arx analytics forecast maintenance --building main --duration 30d
```

#### Model Management
```bash
# List predictive models
arx analytics models list

# Train new model
arx analytics models train --type energy --building main --data-period 90d

# Evaluate model performance
arx analytics models evaluate --model-id model_001
```

### Performance Monitoring

#### KPI Management
```bash
# List KPIs
arx analytics kpis list --building main

# Create new KPI
arx analytics kpis create --name "Energy Efficiency" --metric energy_consumption --threshold 1000

# Update KPI threshold
arx analytics kpis update kpi_001 --threshold 1200
```

#### Alerts
```bash
# List active alerts
arx analytics alerts list --status active

# Acknowledge alert
arx analytics alerts acknowledge alert_001

# Create alert rule
arx analytics alerts create --name "High Energy Usage" --condition "energy_consumption > 1000" --building main
```

### Anomaly Detection

#### Detect Anomalies
```bash
# Detect anomalies in energy data
arx analytics anomalies detect --metric energy_consumption --building main --period 7d

# Detect anomalies in specific room
arx analytics anomalies detect --room "/buildings/main/floors/2/rooms/classroom-205" --metric temperature
```

#### Anomaly Management
```bash
# List anomalies
arx analytics anomalies list --status open

# Mark anomaly as resolved
arx analytics anomalies resolve anomaly_001

# Get anomaly details
arx analytics anomalies show anomaly_001
```

### Reports

#### Generate Reports
```bash
# Generate energy report
arx analytics reports generate energy --building main --period 30d --format pdf

# Generate performance report
arx analytics reports generate performance --building main --period 7d --format html

# Generate custom report
arx analytics reports generate custom --template energy_summary --building main --output report.pdf
```

#### Report Management
```bash
# List reports
arx analytics reports list

# Schedule report
arx analytics reports schedule --template energy_summary --building main --frequency weekly

# Download report
arx analytics reports download report_001 --output energy_report.pdf
```

## IT Management Commands

### Version Control (Git-like Operations)

#### Branch Management
```bash
# Create a new branch for room configuration
arx it vc branch create "/buildings/main/floors/2/rooms/classroom-205" "feature-interactive-board" "main"

# List branches for a room
arx it vc branch list "/buildings/main/floors/2/rooms/classroom-205"
```

#### Commit Operations
```bash
# Commit changes to room configuration
arx it vc commit "/buildings/main/floors/2/rooms/classroom-205" "main" "Add interactive board setup" "it-admin@school.edu"

# Show commit history
arx it vc log "/buildings/main/floors/2/rooms/classroom-205" "main"

# Rollback to previous commit
arx it vc rollback "/buildings/main/floors/2/rooms/classroom-205" "main" "commit_1234567890"
```

#### Push/Pull Operations
```bash
# Push changes to physical deployment
arx it vc push "/buildings/main/floors/2/rooms/classroom-205" "main"

# Pull latest changes from physical deployment
arx it vc pull "/buildings/main/floors/2/rooms/classroom-205" "main"
```

#### Pull Request Management
```bash
# Create a pull request
arx it vc pr create "/buildings/main/floors/2/rooms/classroom-205" "Add Interactive Board" "Replace projector with interactive board" "teacher@school.edu" "main" "feature-interactive-board"

# Review a pull request
arx it vc pr review "pr_1234567890" "true" "it-manager@school.edu"

# Merge a pull request
arx it vc pr merge "pr_1234567890" "true"

# List pull requests for a room
arx it vc pr list "/buildings/main/floors/2/rooms/classroom-205"
```

#### Feature Requests and Emergency Fixes
```bash
# Create a feature request
arx it vc feature-request create "/buildings/main/floors/2/rooms/classroom-205" "Add Smart Board" "Need interactive whiteboard for better engagement" "high" "teacher@school.edu"

# Create an emergency fix
arx it vc emergency-fix create "/buildings/main/floors/2/rooms/classroom-205" "Projector not working" "critical" "teacher@school.edu"
```

### Asset Management

#### Asset Operations
```bash
# List assets
arx it assets list --building main

# List assets by room
arx it assets list --room "/buildings/main/floors/2/rooms/classroom-205"

# List assets by type
arx it assets list --type laptop

# Get asset details
arx it assets show asset_001

# Create new asset
arx it assets create --name "Dell Latitude 5520" --type laptop --room "/buildings/main/floors/2/rooms/classroom-205"

# Update asset
arx it assets update asset_001 --status maintenance --notes "Under repair"

# Delete asset
arx it assets delete asset_001
```

#### Asset Search
```bash
# Search assets by name
arx it assets search "Dell"

# Search assets by serial number
arx it assets search --serial "ABC123"

# Search assets by asset tag
arx it assets search --tag "LAP-001"
```

#### Asset Reports
```bash
# Generate asset inventory report
arx it assets report inventory --building main --format csv

# Generate asset status report
arx it assets report status --building main

# Generate asset location report
arx it assets report location --building main --floor 2
```

### Room Setup Management

#### Room Operations
```bash
# List room setups
arx it rooms list --building main

# Get room setup details
arx it rooms show "/buildings/main/floors/2/rooms/classroom-205"

# Create room setup
arx it rooms create --room "/buildings/main/floors/2/rooms/classroom-205" --type traditional

# Update room setup
arx it rooms update "/buildings/main/floors/2/rooms/classroom-205" --type modern

# Delete room setup
arx it rooms delete "/buildings/main/floors/2/rooms/classroom-205"
```

#### Room Templates
```bash
# List room templates
arx it rooms templates list

# Create room template
arx it rooms templates create --name "Traditional Classroom" --type traditional

# Apply template to room
arx it rooms apply-template "/buildings/main/floors/2/rooms/classroom-205" --template traditional_classroom
```

#### Room Summary
```bash
# Get room summary
arx it rooms summary "/buildings/main/floors/2/rooms/classroom-205"

# Get building summary
arx it rooms summary --building main

# Get floor summary
arx it rooms summary --building main --floor 2
```

### Work Order Management

#### Work Order Operations
```bash
# List work orders
arx it workorders list --status open

# List work orders by room
arx it workorders list --room "/buildings/main/floors/2/rooms/classroom-205"

# Get work order details
arx it workorders show wo_001

# Create work order
arx it workorders create --room "/buildings/main/floors/2/rooms/classroom-205" --title "Install Projector" --type installation

# Update work order
arx it workorders update wo_001 --status in_progress --assigned-to "technician@school.edu"

# Complete work order
arx it workorders complete wo_001 --notes "Projector installed successfully"
```

#### Work Order Search
```bash
# Search work orders by title
arx it workorders search "projector"

# Search work orders by assignee
arx it workorders search --assigned-to "technician@school.edu"

# Search work orders by priority
arx it workorders search --priority high
```

### Inventory Management

#### Parts Management
```bash
# List parts
arx it inventory parts list

# Get part details
arx it inventory parts show part_001

# Create new part
arx it inventory parts create --name "HDMI Cable" --category "Cables" --unit-price 25.0

# Update part
arx it inventory parts update part_001 --quantity 50

# Delete part
arx it inventory parts delete part_001
```

#### Suppliers
```bash
# List suppliers
arx it inventory suppliers list

# Create supplier
arx it inventory suppliers create --name "Tech Supply Co" --contact "sales@techsupply.com"

# Update supplier
arx it inventory suppliers update supplier_001 --phone "+1-555-0123"
```

#### Purchase Orders
```bash
# List purchase orders
arx it inventory orders list

# Create purchase order
arx it inventory orders create --supplier supplier_001 --items "part_001:10,part_002:5"

# Get purchase order details
arx it inventory orders show po_001

# Update purchase order status
arx it inventory orders update po_001 --status received
```

#### Inventory Reports
```bash
# Generate low stock report
arx it inventory report low-stock --threshold 10

# Generate inventory valuation report
arx it inventory report valuation --building main

# Generate supplier performance report
arx it inventory report suppliers --period 30d
```

## Workflow Commands

### Workflow Management

#### Workflow Operations
```bash
# List workflows
arx workflow list

# Get workflow details
arx workflow show workflow_001

# Create workflow
arx workflow create --name "Energy Optimization" --description "Automated energy optimization"

# Update workflow
arx workflow update workflow_001 --status active

# Delete workflow
arx workflow delete workflow_001
```

#### Workflow Execution
```bash
# Execute workflow
arx workflow execute workflow_001 --input '{"building_id": "building_001"}'

# Execute workflow with file input
arx workflow execute workflow_001 --input-file input.json

# Get execution status
arx workflow status execution_001

# List executions
arx workflow executions list --workflow workflow_001
```

#### Workflow Templates
```bash
# List workflow templates
arx workflow templates list

# Create workflow from template
arx workflow create --template energy_optimization --name "Building A Energy Optimization"

# Export workflow as template
arx workflow export workflow_001 --template-name "Custom Energy Optimization"
```

### n8n Integration

#### n8n Operations
```bash
# Test n8n connection
arx workflow n8n test-connection

# List n8n workflows
arx workflow n8n list

# Import n8n workflow
arx workflow n8n import workflow_001

# Export workflow to n8n
arx workflow n8n export workflow_001
```

## CMMS/CAFM Commands

### Facility Management

#### Building Operations
```bash
# List buildings
arx facility buildings list

# Get building details
arx facility buildings show building_001

# Create building
arx facility buildings create --name "Main Building" --address "123 School St"

# Update building
arx facility buildings update building_001 --status active
```

#### Space Management
```bash
# List spaces
arx facility spaces list --building building_001

# Get space details
arx facility spaces show space_001

# Create space
arx facility spaces create --building building_001 --name "Classroom 205" --type classroom

# Update space
arx facility spaces update space_001 --capacity 30
```

### Work Order Management

#### Work Order Operations
```bash
# List work orders
arx facility workorders list --status open

# Get work order details
arx facility workorders show wo_001

# Create work order
arx facility workorders create --title "HVAC Maintenance" --building building_001 --type maintenance

# Update work order
arx facility workorders update wo_001 --status in_progress --assigned-to "technician@school.edu"

# Complete work order
arx facility workorders complete wo_001 --notes "Maintenance completed successfully"
```

#### Maintenance Scheduling
```bash
# List maintenance schedules
arx facility maintenance list --building building_001

# Create maintenance schedule
arx facility maintenance create --asset asset_001 --frequency monthly --type preventive

# Update maintenance schedule
arx facility maintenance update schedule_001 --frequency quarterly

# Generate maintenance calendar
arx facility maintenance calendar --building building_001 --month 2024-01
```

### Inspection Management

#### Inspection Operations
```bash
# List inspections
arx facility inspections list --building building_001

# Get inspection details
arx facility inspections show inspection_001

# Create inspection
arx facility inspections create --building building_001 --type safety --inspector "inspector@school.edu"

# Update inspection
arx facility inspections update inspection_001 --status completed --score 95
```

#### Inspection Templates
```bash
# List inspection templates
arx facility inspections templates list

# Create inspection template
arx facility inspections templates create --name "Safety Inspection" --type safety

# Apply template to inspection
arx facility inspections apply-template inspection_001 --template safety_inspection
```

## Hardware Platform Commands

### Device Management

#### Device Operations
```bash
# List devices
arx hardware devices list --building main

# Get device details
arx hardware devices show device_001

# Register device
arx hardware devices register --name "Temperature Sensor 001" --type sensor --protocol mqtt

# Update device
arx hardware devices update device_001 --status online

# Delete device
arx hardware devices delete device_001
```

#### Device Configuration
```bash
# Configure device
arx hardware devices configure device_001 --config-file config.json

# Get device configuration
arx hardware devices config device_001

# Update device firmware
arx hardware devices firmware device_001 --version 1.2.3
```

### Protocol Management

#### Protocol Operations
```bash
# List protocols
arx hardware protocols list

# Test protocol connection
arx hardware protocols test mqtt --host mqtt.arxos.com --port 1883

# Configure protocol gateway
arx hardware protocols configure mqtt --host mqtt.arxos.com --port 1883 --username user --password pass
```

### Certification

#### Certification Operations
```bash
# List certifications
arx hardware certifications list --device device_001

# Run certification test
arx hardware certifications test device_001 --test-suite safety_basic

# Get certification details
arx hardware certifications show cert_001

# Download certificate
arx hardware certifications download cert_001 --output certificate.pdf
```

#### Test Management
```bash
# List test suites
arx hardware tests list

# Run specific test
arx hardware tests run safety_basic --device device_001

# Get test results
arx hardware tests results test_001
```

## Building Path Commands

### Path Operations
```bash
# List building structure
arx building list

# Get building details
arx building show main

# List floors
arx building floors list --building main

# List rooms
arx building rooms list --building main --floor 2

# Get room details
arx building rooms show "/buildings/main/floors/2/rooms/classroom-205"
```

### Path Validation
```bash
# Validate building path
arx building validate "/buildings/main/floors/2/rooms/classroom-205"

# Check path exists
arx building exists "/buildings/main/floors/2/rooms/classroom-205"

# Get path info
arx building info "/buildings/main/floors/2/rooms/classroom-205"
```

## Configuration Commands

### Configuration Management
```bash
# Show current configuration
arx config show

# Set configuration value
arx config set api.base_url "https://api.arxos.com"

# Get configuration value
arx config get api.base_url

# Reset configuration
arx config reset

# Validate configuration
arx config validate
```

### Environment Management
```bash
# List environments
arx env list

# Switch environment
arx env switch production

# Show current environment
arx env current

# Create environment
arx env create staging --api-url "https://staging-api.arxos.com"
```

## Utility Commands

### Data Export/Import
```bash
# Export data
arx export --type assets --building main --format csv --output assets.csv

# Import data
arx import --type assets --file assets.csv --building main

# Backup data
arx backup --building main --output backup_2024-01-15.tar.gz

# Restore data
arx restore --file backup_2024-01-15.tar.gz --building main
```

### System Information
```bash
# Show system info
arx system info

# Show version
arx version

# Check system health
arx system health

# Show logs
arx logs --level error --lines 100
```

### Interactive Mode
```bash
# Start interactive mode
arx interactive

# Run command in interactive mode
arx interactive --command "analytics energy data --building main"
```

## Output Formats

### Table Format (Default)
```bash
arx it assets list --building main
```

### JSON Format
```bash
arx it assets list --building main --output json
```

### YAML Format
```bash
arx it assets list --building main --output yaml
```

### CSV Format
```bash
arx it assets list --building main --output csv
```

## Examples

### Complete IT Asset Setup
```bash
# 1. Create room setup
arx it rooms create --room "/buildings/main/floors/2/rooms/classroom-205" --type traditional

# 2. Add assets to room
arx it assets create --name "Epson Projector" --type projector --room "/buildings/main/floors/2/rooms/classroom-205"
arx it assets create --name "Elmo Doc Camera" --type doc_camera --room "/buildings/main/floors/2/rooms/classroom-205"
arx it assets create --name "Dell Docking Station" --type docking_station --room "/buildings/main/floors/2/rooms/classroom-205"

# 3. Create work order for installation
arx it workorders create --room "/buildings/main/floors/2/rooms/classroom-205" --title "Install Classroom Equipment" --type installation --priority high

# 4. Get room summary
arx it rooms summary "/buildings/main/floors/2/rooms/classroom-205"
```

### Energy Optimization Workflow
```bash
# 1. Check current energy consumption
arx analytics energy data --building main --realtime

# 2. Get optimization recommendations
arx analytics energy recommendations --building main --priority high

# 3. Create workflow for automation
arx workflow create --name "Energy Optimization" --template energy_optimization

# 4. Execute workflow
arx workflow execute workflow_001 --input '{"building_id": "building_001"}'
```

### Maintenance Management
```bash
# 1. List open work orders
arx facility workorders list --status open

# 2. Create maintenance schedule
arx facility maintenance create --asset asset_001 --frequency monthly --type preventive

# 3. Generate maintenance calendar
arx facility maintenance calendar --building main --month 2024-01

# 4. Complete work order
arx facility workorders complete wo_001 --notes "Maintenance completed successfully"
```

## Troubleshooting

### Common Issues

#### Authentication Errors
```bash
# Check authentication status
arx auth status

# Re-authenticate
arx auth login

# Check API key
arx config get api.api_key
```

#### Connection Issues
```bash
# Test API connection
arx system health

# Check configuration
arx config show

# Test specific endpoint
arx analytics energy data --building main --dry-run
```

#### Permission Errors
```bash
# Check user permissions
arx auth permissions

# List available commands
arx --help
```

### Debug Mode
```bash
# Enable debug logging
arx --verbose analytics energy data --building main

# Show detailed error information
arx --debug it assets list --building main
```

### Log Files
```bash
# Show log file location
arx logs --info

# Follow logs in real-time
arx logs --follow

# Filter logs by level
arx logs --level error --lines 50
```

## Support

For CLI support and questions:

- **Documentation**: https://docs.arxos.com/cli
- **Support Email**: cli-support@arxos.com
- **GitHub Issues**: https://github.com/arx-os/arxos/issues
- **Community Forum**: https://community.arxos.com