# Building Infrastructure-as-Code (IAC) Workflow

This document describes the building infrastructure-as-code (IAC) workflow, where buildings are managed through declarative YAML configurations, version control, and automated deployment processes.

## Table of Contents

1. [Overview](#overview)
2. [Initialization](#initialization)
3. [Building-as-Code Concepts](#building-as-code-concepts)
4. [Version Control](#version-control)
5. [Configuration Management](#configuration-management)
6. [Deployment Pipelines](#deployment-pipelines)
7. [Automation and Integration](#automation-and-integration)
8. [Monitoring and Observability](#monitoring-and-observability)
9. [Security and Compliance](#security-and-compliance)
10. [Testing and Validation](#testing-and-validation)
11. [Disaster Recovery](#disaster-recovery)

## Overview

Building Infrastructure-as-Code transforms building management from manual, error-prone processes into automated, repeatable, and version-controlled operations. Every building element, system configuration, and operational rule is defined as code that can be deployed, tested, and rolled back with the same rigor as software applications.

### Key Benefits

- **Consistency**: Every building follows the same configuration patterns
- **Reproducibility**: Buildings can be recreated from code definitions
- **Version Control**: Complete history of building changes and rollback capability
- **Automation**: Automated deployment and configuration management
- **Compliance**: Built-in validation and compliance checking
- **Collaboration**: Multiple teams can work on building configurations simultaneously

## Initialization

### The `arx init` Command

Initialization is the **first step** in the Building IAC workflow - it creates the foundational building filesystem that enables all subsequent operations.

#### Basic Initialization

```bash
# Initialize a new building
arx init building:main

# Initialize with specific configuration
arx init building:hq --type office --floors 5 --area "25,000 sq ft"

# Initialize from existing building data
arx init building:main --from-pdf "floor_plan.pdf"

# Initialize with custom configuration
arx init building:main --config "building_config.yml"
```

#### What Gets Created

The `arx init` command creates a complete building filesystem structure:

```
building:main/
├── .arxos/                    # Metadata directory
│   ├── config/               # Building configuration
│   │   ├── arxos.yml        # Main building config
│   │   └── environments/     # Environment-specific configs
│   ├── objects/              # ArxObject database
│   │   └── index.db         # Spatial and property indexes
│   ├── vcs/                  # Version control data
│   │   ├── snapshots/        # Building state snapshots
│   │   └── branches/         # Version branches
│   └── cache/                # Temporary data and cache
├── arxos.yml                 # Main building configuration
├── floor:1/                  # First floor
│   └── arxos.yml            # Floor configuration
├── systems/                  # Building systems
│   ├── electrical/
│   │   └── arxos.yml        # Electrical system config
│   ├── hvac/
│   │   └── arxos.yml        # HVAC system config
│   └── automation/
│       └── arxos.yml        # Automation system config
└── schemas/                  # Configuration schemas
    └── arxos.schema.yml     # Building configuration schema
```

#### Bootstrap Process

The initialization process follows this sequence:

1. **Validation**: Check building ID format and existence
2. **Filesystem Creation**: Create directory structure and metadata
3. **ArxObject Initialization**: Create core building hierarchy
4. **Configuration Setup**: Generate initial configuration files
5. **Version Control**: Initialize Git-like version control
6. **Input Processing**: Handle PDF/IFC files and templates
7. **Validation**: Verify the created structure
8. **Success Feedback**: Provide user guidance for next steps

#### Configuration Templates

Arxos provides predefined building templates for common building types:

```bash
# Use office template
arx init building:office --template "standard_office" --floors 3

# Use industrial template
arx init building:warehouse --template "industrial_warehouse" --floors 1

# Use residential template
arx init building:apartment --template "residential_apartment" --floors 4
```

#### From Existing Data

Initialize buildings from existing architectural data:

```bash
# From PDF floor plans
arx init building:main --from-pdf "floor_plan.pdf" --type office

# From IFC files
arx init building:main --from-ifc "building.ifc" --type industrial

# From custom configuration
arx init building:main --config "my_building.yml"
```

## Building-as-Code Concepts

### YAML Structure

Buildings are defined through hierarchical YAML configurations that mirror the physical structure:

```yaml
# arxos.yml - Main building configuration
building_id: "building:main"
type: "office"
floors: 5
area: "25,000 sq ft"
location: "123 Main Street, City, State"
created: "2024-01-15T10:00:00Z"
version: "1.0.0"

# Building systems
systems:
  electrical:
    type: "electrical"
    status: "active"
    voltage: "480V"
    capacity: "800A"
    panels:
      - id: "main_panel"
        type: "main_distribution"
        capacity: "800A"
        voltage: "480V"
        circuits:
          - id: "circuit_1"
            type: "lighting"
            capacity: "20A"
            voltage: "120V"
            status: "active"
  
  hvac:
    type: "hvac"
    status: "active"
    units:
      - id: "ahu_1"
        type: "air_handling_unit"
        capacity: "10,000 CFM"
        status: "active"
        zones:
          - id: "zone_1"
            type: "office"
            area: "5,000 sq ft"
            setpoint: "72°F"
  
  automation:
    type: "automation"
    status: "active"
    protocols: ["BACnet", "Modbus"]
    controllers:
      - id: "controller_1"
        type: "building_controller"
        status: "active"
        protocols: ["BACnet"]
```

### Floor Configuration

Each floor has its own configuration file:

```yaml
# floor:1/arxos.yml
floor_number: 1
height: 3000  # mm
area: "5,000 sq ft"
status: "active"

# Floor systems
systems:
  electrical:
    panels:
      - id: "floor_1_panel"
        type: "sub_panel"
        capacity: "200A"
        voltage: "120V/208V"
  
  hvac:
    zones:
      - id: "floor_1_zone"
        type: "office"
        area: "5,000 sq ft"
        setpoint: "72°F"
        status: "active"

# Rooms on this floor
rooms:
  - id: "room:101"
    type: "conference"
    area: "400 sq ft"
    capacity: "20"
    status: "active"
    systems:
      electrical:
        outlets: 8
        lighting: "LED"
      hvac:
        thermostat: "smart_thermostat"
        setpoint: "72°F"
  
  - id: "room:102"
    type: "office"
    area: "200 sq ft"
    capacity: "2"
    status: "active"
```

### System Configuration

Building systems are configured independently:

```yaml
# systems:electrical/arxos.yml
system_type: "electrical"
status: "active"
voltage: "480V"
capacity: "800A"

# Distribution
distribution:
  main_panel:
    id: "main_panel"
    type: "main_distribution"
    capacity: "800A"
    voltage: "480V"
    status: "active"
    location: "electrical_room"
    
    sub_panels:
      - id: "sub_panel_1"
        type: "lighting"
        capacity: "200A"
        voltage: "120V/208V"
        status: "active"
        circuits:
          - id: "lighting_circuit_1"
            type: "general_lighting"
            capacity: "20A"
            voltage: "120V"
            status: "active"
            outlets: 12
      
      - id: "sub_panel_2"
        type: "power"
        capacity: "200A"
        voltage: "120V/208V"
        status: "active"
        circuits:
          - id: "power_circuit_1"
            type: "general_power"
            capacity: "20A"
            voltage: "120V"
            status: "active"
            outlets: 8

# Load management
load_management:
  peak_demand: "600A"
  average_demand: "400A"
  load_factor: "0.75"
  
# Energy monitoring
energy_monitoring:
  meters:
    - id: "main_meter"
      type: "smart_meter"
      status: "active"
      protocol: "Modbus"
      address: "1"
```

## Version Control

### Git-like Operations

Buildings use Git-like version control for managing changes:

```bash
# Check building status
arx status

# View changes
arx diff

# Stage changes
arx add floor:1/room:101

# Commit changes
arx commit -m "Add new conference room configuration"

# View commit history
arx log

# Create feature branch
arx branch create electrical-upgrade

# Switch to branch
arx branch checkout electrical-upgrade

# Make changes
arx modify systems:electrical --property capacity=1000A

# Commit changes
arx commit -m "Upgrade electrical capacity to 1000A"

# Switch back to main
arx branch checkout main

# Merge changes
arx merge electrical-upgrade

# Delete branch
arx branch delete electrical-upgrade
```

### Branching Strategy

```bash
# Main branch for production
arx branch checkout main

# Development branch for testing
arx branch create development
arx branch checkout development

# Feature branches for specific changes
arx branch create hvac-optimization
arx branch create electrical-upgrade
arx branch create room-reconfiguration

# Hotfix branch for urgent changes
arx branch create hotfix-electrical-issue
```

### Commit Messages

Follow conventional commit format for building changes:

```bash
# Feature additions
arx commit -m "feat: add new conference room configuration"

# Bug fixes
arx commit -m "fix: correct electrical panel capacity calculation"

# Documentation updates
arx commit -m "docs: update HVAC system configuration"

# Breaking changes
arx commit -m "feat!: upgrade electrical system to 1000A capacity

BREAKING CHANGE: Requires new electrical service installation"
```

## Configuration Management

### Environment Configuration

Manage different environments (development, staging, production):

```yaml
# .arxos/config/environments/development.yml
environment: "development"
debug: true
log_level: "debug"
simulation_mode: true

# Override system settings for development
systems:
  electrical:
    simulation_mode: true
    test_loads: true
  
  hvac:
    simulation_mode: true
    test_temperatures: true

# .arxos/config/environments/production.yml
environment: "production"
debug: false
log_level: "info"
simulation_mode: false

# Production-specific settings
systems:
  electrical:
    monitoring: true
    alerts: true
  
  hvac:
    monitoring: true
    alerts: true
```

### Configuration Validation

Validate configurations before deployment:

```bash
# Validate entire building
arx validate

# Validate specific system
arx validate --system electrical

# Validate with specific rules
arx validate --rules electrical_code,hvac_code

# Validate and auto-fix issues
arx validate --fix

# Generate validation report
arx validate --report --output validation_report.html
```

### Configuration Templates

Use templates for common building configurations:

```yaml
# schemas/templates/standard_office.yml
template_name: "standard_office"
description: "Standard office building template"
version: "1.0.0"

# Template parameters
parameters:
  floors:
    type: "integer"
    default: 3
    min: 1
    max: 50
  
  floor_area:
    type: "string"
    default: "5,000 sq ft"
    description: "Area per floor"
  
  building_type:
    type: "string"
    default: "office"
    enum: ["office", "mixed_use", "retail"]

# Template structure
structure:
  - type: "floor"
    repeat: "{{.floors}}"
    properties:
      area: "{{.floor_area}}"
      height: "3000"
  
  - type: "system"
    name: "electrical"
    properties:
      voltage: "480V"
      capacity: "800A"
  
  - type: "system"
    name: "hvac"
    properties:
      type: "vav"
      zones_per_floor: 4
```

## Deployment Pipelines

### CI/CD for Buildings

Automate building deployments through CI/CD pipelines:

```yaml
# .arxos/.github/workflows/deploy.yml
name: Deploy Building Configuration

on:
  push:
    branches: [main, staging]
  pull_request:
    branches: [main]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Validate Configuration
        run: |
          arx validate --rules all
          arx validate --system electrical
          arx validate --system hvac
  
  test:
    runs-on: ubuntu-latest
    needs: validate
    steps:
      - uses: actions/checkout@v3
      
      - name: Run Building Tests
        run: |
          arx test --system electrical
          arx test --system hvac
          arx test --integration
  
  deploy-staging:
    runs-on: ubuntu-latest
    needs: [validate, test]
    if: github.ref == 'refs/heads/staging'
    steps:
      - uses: actions/checkout@v3
      
      - name: Deploy to Staging
        run: |
          arx deploy --environment staging
          arx health-check --environment staging
  
  deploy-production:
    runs-on: ubuntu-latest
    needs: [validate, test]
    if: github.ref == 'refs/heads/main'
    environment: production
    steps:
      - uses: actions/checkout@v3
      
      - name: Deploy to Production
        run: |
          arx deploy --environment production
          arx health-check --environment production
```

### Deployment Commands

```bash
# Deploy to specific environment
arx deploy --environment staging
arx deploy --environment production

# Deploy specific systems
arx deploy --system electrical --environment production

# Deploy with configuration
arx deploy --config deployment_config.yml

# Rollback deployment
arx deploy --rollback HEAD~1

# Preview deployment
arx deploy --preview

# Deploy with validation
arx deploy --validate --environment production
```

### Health Checks

```bash
# Check building health
arx health-check

# Check specific system health
arx health-check --system electrical

# Check with detailed output
arx health-check --verbose

# Continuous monitoring
arx health-check --watch

# Generate health report
arx health-check --report --output health_report.html
```

## Automation and Integration

### Building Rules

Define automated building behavior through rules:

```yaml
# .arxos/config/rules/building_rules.yml
rules:
  - name: "energy_optimization"
    description: "Optimize energy usage based on occupancy"
    triggers:
      - type: "schedule"
        cron: "0 */15 * * * *"  # Every 15 minutes
      - type: "occupancy_change"
        threshold: 10
    
    conditions:
      - type: "occupancy"
        operator: "lt"
        value: 20
        system: "hvac"
    
    actions:
      - type: "setpoint_adjustment"
        system: "hvac"
        parameter: "cooling_setpoint"
        value: "75°F"
        duration: "30m"
      
      - type: "lighting_adjustment"
        system: "electrical"
        parameter: "lighting_level"
        value: "50%"
        duration: "30m"
  
  - name: "maintenance_alerts"
    description: "Alert on maintenance requirements"
    triggers:
      - type: "schedule"
        cron: "0 9 * * 1"  # Every Monday at 9 AM
      - type: "system_status"
        status: "maintenance_required"
    
    conditions:
      - type: "maintenance_due"
        operator: "lte"
        value: "7d"
    
    actions:
      - type: "notification"
        channel: "slack"
        message: "Maintenance required for {{.system_name}}"
      
      - type: "ticket_creation"
        system: "jira"
        project: "MAINT"
        summary: "Maintenance required for {{.system_name}}"
        description: "{{.maintenance_description}}"
```

### External System Integration

Integrate with building management systems:

```yaml
# .arxos/config/integrations/external_systems.yml
integrations:
  - name: "bms"
    type: "building_management_system"
    protocol: "BACnet"
    connection:
      host: "192.168.1.100"
      port: 47808
      device_id: 1234
    
    mappings:
      - arxos_path: "systems:hvac:ahu:1:temperature"
        bms_path: "analog_input:1"
        type: "temperature"
        unit: "celsius"
      
      - arxos_path: "systems:hvac:ahu:1:setpoint"
        bms_path: "analog_output:1"
        type: "temperature"
        unit: "celsius"
  
  - name: "cmms"
    type: "computerized_maintenance_management"
    protocol: "REST"
    connection:
      url: "https://cmms.company.com/api"
      auth:
        type: "bearer"
        token: "${CMMS_API_TOKEN}"
    
    mappings:
      - arxos_path: "systems:electrical:main_panel:maintenance_status"
        cmms_path: "equipment:main_panel:status"
        type: "maintenance_status"
      
      - arxos_path: "systems:hvac:ahu:1:maintenance_schedule"
        cmms_path: "equipment:ahu_1:schedule"
        type: "maintenance_schedule"
  
  - name: "energy_management"
    type: "energy_management_system"
    protocol: "Modbus"
    connection:
      host: "192.168.1.200"
      port: 502
      slave_id: 1
    
    mappings:
      - arxos_path: "systems:electrical:main_meter:power"
        ems_path: "register:1000"
        type: "power"
        unit: "kilowatts"
      
      - arxos_path: "systems:electrical:main_meter:energy"
        ems_path: "register:1001"
        type: "energy"
        unit: "kilowatt_hours"
```

### API Integration

Expose building operations through REST API:

```yaml
# .arxos/config/api/api_config.yml
api:
  version: "v1"
  base_path: "/api/v1"
  authentication:
    type: "jwt"
    secret: "${JWT_SECRET}"
    expiry: "24h"
  
  endpoints:
    - path: "/buildings/{building_id}/status"
      method: "GET"
      description: "Get building status"
      permissions: ["read:building"]
    
    - path: "/buildings/{building_id}/systems/{system_id}/control"
      method: "POST"
      description: "Control building system"
      permissions: ["write:system"]
    
    - path: "/buildings/{building_id}/deploy"
      method: "POST"
      description: "Deploy building configuration"
      permissions: ["deploy:building"]
  
  webhooks:
    - name: "system_status_change"
      url: "https://webhook.company.com/system-status"
      events: ["system.status.changed"]
      headers:
        Authorization: "Bearer ${WEBHOOK_TOKEN}"
    
    - name: "maintenance_alert"
      url: "https://webhook.company.com/maintenance"
      events: ["maintenance.required"]
      headers:
        Authorization: "Bearer ${WEBHOOK_TOKEN}"
```

## Monitoring and Observability

### Metrics Collection

Collect building performance metrics:

```yaml
# .arxos/config/monitoring/metrics.yml
metrics:
  collection_interval: "1m"
  retention_period: "90d"
  
  system_metrics:
    - name: "electrical_power"
      type: "gauge"
      unit: "kilowatts"
      description: "Electrical power consumption"
      collection:
        source: "systems:electrical:main_meter:power"
        interval: "1m"
    
    - name: "hvac_temperature"
      type: "gauge"
      unit: "celsius"
      description: "HVAC system temperature"
      collection:
        source: "systems:hvac:ahu:1:temperature"
        interval: "1m"
    
    - name: "occupancy_count"
      type: "gauge"
      unit: "people"
      description: "Building occupancy count"
      collection:
        source: "building:occupancy:total"
        interval: "5m"
  
  business_metrics:
    - name: "energy_efficiency"
      type: "calculated"
      formula: "electrical_power / occupancy_count"
      unit: "kilowatts_per_person"
      description: "Energy efficiency per person"
    
    - name: "comfort_score"
      type: "calculated"
      formula: "average(hvac_temperature_setpoint - hvac_temperature_actual)"
      unit: "celsius_deviation"
      description: "Temperature comfort deviation"
```

### Alerting

Configure alerts for building issues:

```yaml
# .arxos/config/monitoring/alerts.yml
alerts:
  - name: "high_energy_consumption"
    description: "Alert when energy consumption is high"
    condition:
      metric: "electrical_power"
      operator: "gt"
      threshold: 100  # kW
      duration: "5m"
    
    actions:
      - type: "notification"
        channel: "slack"
        message: "High energy consumption: {{.value}} kW"
      
      - type: "email"
        to: ["facilities@company.com"]
        subject: "High Energy Consumption Alert"
        body: "Building {{.building_id}} is consuming {{.value}} kW"
  
  - name: "hvac_failure"
    description: "Alert when HVAC system fails"
    condition:
      metric: "hvac_status"
      operator: "eq"
      value: "failed"
      duration: "1m"
    
    actions:
      - type: "notification"
        channel: "pagerduty"
        severity: "critical"
        message: "HVAC system failure detected"
      
      - type: "ticket_creation"
        system: "jira"
        project: "OPS"
        summary: "HVAC System Failure"
        description: "HVAC system has failed and requires immediate attention"
        priority: "Blocker"
```

### Dashboards

Create monitoring dashboards:

```yaml
# .arxos/config/monitoring/dashboards.yml
dashboards:
  - name: "building_overview"
    title: "Building Overview"
    refresh_interval: "30s"
    
    panels:
      - title: "System Status"
        type: "status_grid"
        metrics:
          - "electrical_status"
          - "hvac_status"
          - "automation_status"
      
      - title: "Energy Consumption"
        type: "time_series"
        metrics:
          - "electrical_power"
          - "energy_efficiency"
        time_range: "24h"
      
      - title: "Occupancy"
        type: "gauge"
        metrics:
          - "occupancy_count"
      
      - title: "Temperature"
        type: "time_series"
        metrics:
          - "hvac_temperature"
          - "hvac_temperature_setpoint"
        time_range: "24h"
  
  - name: "electrical_system"
    title: "Electrical System"
    refresh_interval: "15s"
    
    panels:
      - title: "Power Consumption"
        type: "time_series"
        metrics:
          - "electrical_power"
          - "electrical_current"
          - "electrical_voltage"
        time_range: "1h"
      
      - title: "Panel Status"
        type: "status_grid"
        metrics:
          - "main_panel_status"
          - "sub_panel_1_status"
          - "sub_panel_2_status"
```

## Security and Compliance

### Access Control

Implement role-based access control:

```yaml
# .arxos/config/security/access_control.yml
access_control:
  roles:
    - name: "building_admin"
      description: "Full building administration access"
      permissions:
        - "building:*"
        - "system:*"
        - "deploy:*"
        - "security:*"
    
    - name: "system_operator"
      description: "System operation and monitoring access"
      permissions:
        - "building:read"
        - "system:read"
        - "system:control"
        - "monitoring:*"
    
    - name: "maintenance_tech"
      description: "Maintenance and inspection access"
      permissions:
        - "building:read"
        - "system:read"
        - "maintenance:*"
        - "inspection:*"
    
    - name: "viewer"
      description: "Read-only access to building information"
      permissions:
        - "building:read"
        - "system:read"
        - "monitoring:read"
  
  users:
    - username: "joel.pate"
      role: "building_admin"
      email: "joel.pate@arxos.com"
      status: "active"
    
    - username: "facilities.team"
      role: "system_operator"
      email: "facilities@company.com"
      status: "active"
    
    - username: "maintenance.team"
      role: "maintenance_tech"
      email: "maintenance@company.com"
      status: "active"
```

### Compliance Rules

Define compliance and regulatory requirements:

```yaml
# .arxos/config/compliance/compliance_rules.yml
compliance:
  - name: "electrical_code"
    description: "National Electrical Code compliance"
    version: "2023"
    rules:
      - rule: "panel_capacity"
        description: "Panel capacity must exceed connected load"
        validation:
          type: "calculation"
          formula: "panel_capacity > total_connected_load * 1.25"
          severity: "error"
      
      - rule: "circuit_protection"
        description: "All circuits must have appropriate protection"
        validation:
          type: "property_check"
          property: "circuit_protection"
          required: true
          severity: "error"
  
  - name: "energy_codes"
    description: "Energy efficiency code compliance"
    version: "2021"
    rules:
      - rule: "lighting_efficiency"
        description: "Lighting must meet minimum efficiency requirements"
        validation:
          type: "property_check"
          property: "lighting_efficiency"
          minimum: "90"
          unit: "lumens_per_watt"
          severity: "warning"
      
      - rule: "hvac_efficiency"
        description: "HVAC systems must meet minimum SEER ratings"
        validation:
          type: "property_check"
          property: "hvac_seer_rating"
          minimum: "14"
          severity: "warning"
  
  - name: "accessibility"
    description: "Americans with Disabilities Act compliance"
    version: "2010"
    rules:
      - rule: "door_widths"
        description: "All doors must meet minimum width requirements"
        validation:
          type: "property_check"
          property: "door_width"
          minimum: "32"
          unit: "inches"
          severity: "error"
      
      - rule: "ramp_slopes"
        description: "Ramp slopes must not exceed maximum values"
        validation:
          type: "calculation"
          formula: "ramp_slope <= 1/12"
          severity: "error"
```

## Testing and Validation

### Building Tests

Test building configurations and systems:

```yaml
# .arxos/config/testing/test_suites.yml
test_suites:
  - name: "electrical_tests"
    description: "Electrical system validation tests"
    tests:
      - name: "load_calculation"
        description: "Verify electrical load calculations"
        type: "calculation"
        input:
          - "systems:electrical:panels:*:circuits:*:load"
        expected:
          formula: "total_load <= main_panel_capacity * 0.8"
        severity: "error"
      
      - name: "circuit_protection"
        description: "Verify circuit protection devices"
        type: "property_validation"
        input:
          - "systems:electrical:panels:*:circuits:*:protection"
        expected:
          required: true
          type: "circuit_breaker"
        severity: "error"
  
  - name: "hvac_tests"
    description: "HVAC system validation tests"
    tests:
      - name: "zone_coverage"
        description: "Verify all areas have HVAC coverage"
        type: "coverage_check"
        input:
          - "floor:*:rooms:*:area"
        expected:
          coverage: "100%"
          system: "hvac"
        severity: "warning"
      
      - name: "temperature_control"
        description: "Verify temperature control capabilities"
        type: "property_validation"
        input:
          - "systems:hvac:zones:*:thermostat"
        expected:
          required: true
          type: "smart_thermostat"
        severity: "error"
  
  - name: "integration_tests"
    description: "System integration tests"
    tests:
      - name: "electrical_hvac_integration"
        description: "Verify electrical and HVAC system integration"
        type: "integration_check"
        input:
          - "systems:electrical:panels:*:circuits:*:load"
          - "systems:hvac:units:*:power_requirement"
        expected:
          relationship: "electrical_supplies_hvac"
          validation: "power_available >= power_required"
        severity: "error"
```

### Test Execution

```bash
# Run all tests
arx test

# Run specific test suite
arx test --suite electrical_tests

# Run tests for specific system
arx test --system electrical

# Run tests with specific severity
arx test --severity error

# Run tests and generate report
arx test --report --output test_report.html

# Run tests in continuous mode
arx test --watch

# Run tests with custom configuration
arx test --config custom_test_config.yml
```

## Disaster Recovery

### Backup Strategies

Implement comprehensive backup strategies:

```yaml
# .arxos/config/backup/backup_strategy.yml
backup:
  strategy: "incremental"
  retention:
    daily: 7
    weekly: 4
    monthly: 12
    yearly: 5
  
  schedules:
    - name: "daily_backup"
      cron: "0 2 * * *"  # 2 AM daily
      type: "incremental"
      systems: ["all"]
    
    - name: "weekly_backup"
      cron: "0 3 * * 0"  # 3 AM Sunday
      type: "full"
      systems: ["all"]
    
    - name: "monthly_backup"
      cron: "0 4 1 * *"  # 4 AM 1st of month
      type: "full"
      systems: ["all"]
  
  storage:
    local:
      path: "/backups/arxos"
      max_size: "100GB"
    
    remote:
      type: "s3"
      bucket: "arxos-backups"
      region: "us-east-1"
      encryption: true
  
  verification:
    - type: "checksum_validation"
      algorithm: "sha256"
    
    - type: "restore_test"
      frequency: "weekly"
      test_systems: ["electrical", "hvac"]
```

### Recovery Procedures

Define recovery procedures for different scenarios:

```yaml
# .arxos/config/recovery/recovery_procedures.yml
recovery:
  scenarios:
    - name: "building_configuration_corruption"
      description: "Recover from corrupted building configuration"
      severity: "high"
      procedures:
        - step: "Stop all building operations"
          command: "arx stop --all"
          description: "Halt all building systems"
        
        - step: "Restore from latest backup"
          command: "arx backup restore --latest"
          description: "Restore building configuration"
        
        - step: "Validate configuration"
          command: "arx validate --all"
          description: "Verify configuration integrity"
        
        - step: "Restart building systems"
          command: "arx start --all"
          description: "Restart all systems"
    
    - name: "system_failure"
      description: "Recover from system failure"
      severity: "medium"
      procedures:
        - step: "Identify failed system"
          command: "arx status --system {system_name}"
          description: "Determine system status"
        
        - step: "Isolate failed system"
          command: "arx stop --system {system_name}"
          description: "Stop failed system"
        
        - step: "Restore system configuration"
          command: "arx backup restore --system {system_name}"
          description: "Restore system from backup"
        
        - step: "Restart system"
          command: "arx start --system {system_name}"
          description: "Restart recovered system"
    
    - name: "data_loss"
      description: "Recover from data loss"
      severity: "critical"
      procedures:
        - step: "Assess data loss extent"
          command: "arx audit --data-loss"
          description: "Identify lost data"
        
        - step: "Restore from backup"
          command: "arx backup restore --point-in-time {timestamp}"
          description: "Restore to specific point in time"
        
        - step: "Verify data integrity"
          command: "arx validate --data-integrity"
          description: "Check data consistency"
        
        - step: "Replay transactions"
          command: "arx replay --since {timestamp}"
          description: "Replay transactions since backup"
```

### Recovery Commands

```bash
# Create backup
arx backup create --name "emergency_backup_$(date +%Y%m%d_%H%M%S)"

# List available backups
arx backup list

# Restore from specific backup
arx backup restore --name "daily_backup_20240115"

# Restore to specific point in time
arx backup restore --point-in-time "2024-01-15T10:00:00Z"

# Restore specific system
arx backup restore --system electrical --name "daily_backup_20240115"

# Verify backup integrity
arx backup verify --name "daily_backup_20240115"

# Export backup
arx backup export --name "daily_backup_20240115" --output "backup.tar.gz"

# Test recovery procedure
arx recovery test --scenario "building_configuration_corruption"
```

This comprehensive Building IAC workflow document provides the foundation for managing buildings as code, from initialization through deployment, monitoring, and disaster recovery. The focus on automation, version control, and integration ensures that building management becomes as reliable and repeatable as software development.
