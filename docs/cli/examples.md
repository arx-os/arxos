# Examples & Use Cases

This document provides practical examples of using the Arxos CLI for common building management workflows.

## Getting Started Examples

### Basic Setup and Connection

```bash
# Login to your organization
arxos auth login --org="acme-buildings"

# Connect to a building
arxos connect building://acme-buildings/office-tower-main

# Verify connection
arxos connection status

# Explore the building structure
arxos find floors
arxos find rooms in floor:1
```

### First Queries

```bash
# Find all electrical outlets
arxos find outlets

# Find outlets on a specific floor
arxos find outlets in floor:45

# Find outlets with specific voltage
arxos find outlets where voltage=120

# Count total outlets in building
arxos count outlets
```

## Common Query Patterns

### Spatial Queries

```bash
# Find objects near a specific location
arxos find outlets within 10ft of coordinates:(100,200,300)

# Find objects in a room
arxos find fixtures in room:R-205

# Find adjacent objects
arxos find walls adjacent-to room:R-205

# Find objects within a bounding box
arxos find beams in bbox:(0,0,0)-(100,100,15)

# Find path between objects
arxos find path from outlet:R45-23 to panel:MP-1
```

### Property-Based Queries

```bash
# Find objects with specific properties
arxos find outlets where gfci=true
arxos find beams where material="steel"
arxos find rooms where area > 200sqft

# Find objects missing properties
arxos find outlets where missing-property:gfci

# Complex property queries
arxos find outlets where voltage=120 AND amperage=20 AND gfci=true
```

### Relationship Queries

```bash
# Find connected objects
arxos find outlets connected-to circuit:C-101

# Find objects serving other objects
arxos find panels serving outlet:R45-23

# Trace connections
arxos trace electrical-path from outlet:R45-23 to source

# Find dependencies
arxos find dependencies-of beam:B-101
```

## Object Management Examples

### Creating Objects

```bash
# Create a new outlet
arxos create outlet --id=R45-30 \
  --voltage=120 \
  --amperage=20 \
  --location=(125,200,300) \
  --wall=W-101

# Create with relationships
arxos create outlet R45-31 \
  --connected-to circuit:C-101 \
  --mounted-on wall:W-101 \
  --gfci=true

# Create from template
arxos create outlet --template=standard-gfci --id=R45-32
```

### Modifying Objects

```bash
# Change a single property
arxos set outlet:R45-23.voltage=240

# Change multiple properties
arxos set outlet:R45-23 voltage=240 amperage=30 gfci=true

# Conditional modifications
arxos modify outlet:R45-23 amperage=30 --if="voltage=240"

# Move an object
arxos move outlet:R45-23 to (150,200,300)
```

### Batch Operations

```bash
# Update multiple objects at once
arxos batch-set "outlets in floor:45" gfci=true

# Create multiple objects from CSV
arxos import outlets --file=new-outlets.csv

# Update based on query
arxos update "outlets where voltage=120 AND gfci=false" set gfci=true
```

## System-Specific Examples

### Electrical System Management

```bash
# Find overloaded circuits
arxos find circuits where current-load > capacity * 0.8

# Find outlets without GFCI in wet areas
arxos find outlets where location-type="bathroom" AND gfci=false

# Trace electrical path
arxos trace electrical from outlet:R45-23 to panel:MP-1

# Find all outlets on a circuit
arxos find outlets connected-to circuit:C-101

# Calculate total load on panel
arxos calculate total-load on panel:MP-1

# Find panels with available capacity
arxos find panels where available-capacity > 10A
```

### Mechanical System Management

```bash
# Find oversized ducts
arxos find ducts where diameter > required-diameter * 1.2

# Find pipes with insufficient insulation
arxos find pipes where fluid-temp > 140F AND insulation-r-value < 10

# Trace HVAC airflow
arxos trace airflow from room:R-205 to ahu:AHU-1

# Find equipment due for maintenance
arxos find equipment where last-maintenance < now() - 90days

# Calculate room CFM requirements
arxos calculate cfm-required for room:R-205

# Find VAV boxes with control issues
arxos find vav-boxes where damper-position = "stuck"
```

### Structural System Management

```bash
# Find overloaded beams
arxos find beams where current-load > design-load * 0.9

# Find columns supporting critical loads
arxos find columns supporting beams where load > 10000lbs

# Check structural connections
arxos validate connections for beam:B-101

# Find structural modifications since date
arxos find structural.* where modified-since:"2024-01-01"

# Calculate tributary area
arxos calculate tributary-area for beam:B-101

# Find seismic restraints
arxos find restraints where type="seismic"
```

## Maintenance and Operations

### Preventive Maintenance

```bash
# Find equipment due for service
arxos find equipment where next-service-date < now() + 30days

# Generate maintenance schedule
arxos report maintenance-schedule --timeframe="next-quarter"

# Track maintenance history
arxos history equipment:HVAC-101 --type=maintenance

# Find components with recurring issues
arxos find * where maintenance-frequency > 4/year

# Schedule bulk maintenance
arxos schedule maintenance "equipment where type=fan" --date="2024-06-01"
```

### Space Management

```bash
# Find underutilized rooms
arxos find rooms where occupancy-rate < 0.6

# Calculate space utilization
arxos calculate utilization for floor:45 --timeframe="last-month"

# Find rooms needing reconfiguration
arxos find rooms where layout-efficiency < 0.8

# Track space changes over time
arxos history room:R-205 --property=area --since="last-year"

# Optimize space allocation
arxos optimize space-allocation for floor:45
```

### Energy Management

```bash
# Find high energy consuming equipment
arxos find equipment where energy-consumption > baseline * 1.2

# Calculate building energy usage
arxos calculate energy-usage --timeframe="last-month" --breakdown=system

# Find opportunities for energy savings
arxos analyze energy-savings --recommendations

# Track energy performance
arxos report energy-performance --compare-to="last-year"

# Find inefficient lighting
arxos find lighting where efficiency < 100lm/W
```

## Compliance and Safety

### Building Code Compliance

```bash
# Check accessibility compliance
arxos validate accessibility room:R-205 --code=ADA

# Find fire safety violations
arxos find walls where fire-rating < required-fire-rating

# Check egress paths
arxos validate egress from room:R-205 --occupancy=50

# Find code violations
arxos compliance-check floor:45 --code=IBC-2021

# Generate compliance report
arxos report compliance --building=all --export=pdf
```

### Safety Inspections

```bash
# Find safety equipment needing inspection
arxos find safety-equipment where last-inspection < now() - 365days

# Check emergency systems
arxos validate emergency-systems floor:45

# Find missing safety features
arxos find rooms where missing-property:smoke-detector

# Generate safety inspection checklist
arxos checklist safety-inspection --area=floor:45

# Track inspection history
arxos audit safety-inspections --since="last-year"
```

## Advanced Workflows

### Transaction-Based Operations

```bash
# Complex multi-object modification
arxos transaction begin --description="Relocate electrical panel MP-1"

  # Move panel
  arxos move panel:MP-1 to room:R-150
  
  # Reroute circuits
  arxos modify circuits connected-to panel:MP-1 \
    recalculate-path --destination=room:R-150
  
  # Update load calculations
  arxos recalculate loads affected-by panel:MP-1
  
  # Validate constraints
  arxos validate-constraints panel:MP-1
  
# Commit if all validations pass
arxos transaction commit
```

### Real-Time Collaboration

```bash
# Start collaborative session
arxos session start "MEP Coordination Meeting" \
  --invite=alice@company.com,bob@company.com

# Watch for changes in work area
arxos watch floor:45 --events=modifications --notify=immediate

# Share current view with team
arxos share-view floor:45 --filter="electrical,mechanical"

# Resolve conflicts collaboratively
arxos conflicts resolve-interactive --with-team
```

### Data Analysis and Reporting

```bash
# Generate system summary report
arxos report system-summary --systems=electrical,mechanical \
  --format=html --export=building-summary.html

# Analyze space utilization trends
arxos analyze space-utilization --timeframe="last-year" \
  --breakdown=department --export=csv

# Compare buildings
arxos compare buildings \
  --building1=tower-main \
  --building2=tower-north \
  --metrics=energy,space,cost

# Export data for external analysis
arxos export "outlets in building" \
  --format=csv --include-relationships \
  --output=outlet-analysis.csv
```

## Integration Examples

### BIM Integration

```bash
# Import from Revit model
arxos import architectural-model.rvt \
  --validate-constraints \
  --merge-strategy=update-existing

# Sync with BIM model
arxos sync-bim --model=main-architectural.rvt \
  --conflict-resolution=prompt

# Export for BIM coordination
arxos export "structural.* in floor:45" \
  --format=ifc --output=floor45-structural.ifc

# Validate BIM coordination
arxos validate-coordination --models=arch.rvt,mep.rvt,struct.rvt
```

### External Systems Integration

```bash
# Import from facility management system
arxos import maintenance-data.csv \
  --type=equipment --match-by=asset-tag

# Export to energy management system
arxos export "equipment where type=hvac" \
  --format=json --include-energy-data \
  --output=hvac-for-ems.json

# Sync with IoT sensors
arxos sync-sensors --building=main --systems=hvac,electrical

# Update from work order system
arxos update equipment --from-workorders=completed-2024-01.csv
```

## Troubleshooting Examples

### Performance Issues

```bash
# Profile slow queries
arxos profile query "find outlets where voltage > 100"

# Optimize query with spatial bounds
arxos find outlets in floor:45 where voltage > 100 \
  --spatial-index=octree

# Monitor performance
arxos perf monitor --duration=5m --operations=query,modify

# Generate performance report
arxos perf report --timeframe="last-week" --export=perf-report.html
```

### Data Validation

```bash
# Find constraint violations
arxos validate-constraints --all --show-violations

# Check relationship integrity
arxos validate-relationships --repair-orphans

# Find duplicate objects
arxos find-duplicates --criteria=location,properties

# Repair data inconsistencies
arxos repair-data --fix=constraints,relationships,duplicates
```

### Sync and Collaboration Issues

```bash
# Resolve sync conflicts
arxos conflicts list
arxos conflict resolve <conflict-id> --strategy=merge

# Reset sync state
arxos sync reset --confirm

# Recover from sync corruption
arxos sync recover --method=rebuild-from-server

# Export conflict resolution report
arxos conflicts export --format=csv --timeframe="last-week"
```

## Automation and Scripting

### Scheduled Operations

```bash
# Schedule regular data validation
arxos schedule validate-constraints \
  --interval=daily --time=2am --email-report

# Automate maintenance reminders
arxos schedule maintenance-reminders \
  --interval=weekly --day=monday

# Schedule performance monitoring
arxos schedule perf-monitor \
  --interval=hourly --alert-threshold=2s
```

### Custom Scripts

```bash
# Create custom workflow script
cat > quarterly-review.arxos << 'EOF'
# Quarterly building review script
transaction begin "Quarterly Review"

# Update equipment inspection dates
update "equipment where type=hvac" set last-inspection=today()

# Generate compliance report
report compliance --export=quarterly-compliance.pdf

# Calculate energy efficiency metrics
calculate energy-efficiency --export=energy-metrics.csv

transaction commit
EOF

# Execute custom script
arxos script quarterly-review.arxos --confirm
```

### API Integration

```bash
# Generate API documentation from CLI usage
arxos api generate-docs --from-cli --format=openapi

# Convert CLI commands to API calls
arxos api translate "find outlets in floor:45" --format=curl

# Batch API operations
arxos api batch --file=api-operations.json --parallel=5
```

These examples demonstrate the flexibility and power of the Arxos CLI for managing complex building systems. The key is to start with simple queries and gradually build up to more complex operations as you become familiar with your building's data structure and relationships.