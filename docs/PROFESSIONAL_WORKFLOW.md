# ArxOS Professional BIM Workflow

## Overview

ArxOS integrates seamlessly with professional BIM (Building Information Modeling) tools like AutoCAD, Revit, ArchiCAD, NavisWorks, and Tekla Structures. The system watches IFC (Industry Foundation Classes) files exported by these tools and automatically imports spatial data into a PostGIS database for advanced spatial operations and reporting.

## Architecture

```
BIM Tools (Revit, AutoCAD, etc.)
         |
         v
    IFC Export (Native)
         |
         v
   ArxOS Daemon (Watches)
         |
         v
    PostGIS Import
         |
         v
   Export Generation
    /    |    \
   v     v     v
 .bim.txt CSV  JSON
```

## Key Principles

1. **IFC as Universal Interface**: Professional BIM tools handle IFC export natively - ArxOS simply watches and imports
2. **PostGIS as Single Source of Truth**: All spatial data is stored in PostGIS with millimeter precision
3. **Automatic Synchronization**: Daemon continuously watches for IFC changes and updates the database
4. **Human-Readable Exports**: .bim.txt, CSV, and JSON formats are for humans and reporting, not BIM tools

## Setup Guide

### 1. Install PostGIS Database

```bash
# Using Docker (recommended)
docker run -d \
  --name arxos-postgis \
  -e POSTGRES_DB=arxos \
  -e POSTGRES_USER=arxos \
  -e POSTGRES_PASSWORD=secure_password \
  -p 5432:5432 \
  postgis/postgis:16-3.4

# Or install locally
brew install postgresql postgis  # macOS
sudo apt-get install postgresql postgis  # Ubuntu
```

### 2. Configure ArxOS

Create or update `.arxos/config.yaml`:

```yaml
database:
  type: postgis
  host: localhost
  port: 5432
  database: arxos
  user: arxos
  password: secure_password
  srid: 900913  # Web Mercator for millimeter precision

daemon:
  enabled: true
  watch_paths:
    - "~/Projects/BIM/*.ifc"
    - "C:\\Projects\\*.ifc"  # Windows path
  poll_interval: 5s
  auto_export: true
  export_dir: ".arxos/exports"
```

### 3. Start the Daemon

```bash
# Start daemon to watch for IFC files
arx daemon start

# Check daemon status
arx daemon status
```

## Professional Workflow

### Step 1: Export from BIM Tool

In your BIM software (e.g., Revit):

1. Complete your building model
2. File → Export → IFC
3. Save to watched directory (e.g., `~/Projects/BIM/`)
4. Use IFC4 format for best compatibility

**Revit Example**:
```
File → Export → IFC
Settings:
  - IFC Version: IFC4
  - Space boundaries: 2nd Level
  - Include site information: Yes
  - Coordinate base: Project Base Point
```

**AutoCAD Example**:
```
File → Export → IFC
Options:
  - Export solids as: BREP
  - Include property sets: Yes
  - Spatial structure: Building/Storey/Space
```

### Step 2: Automatic Import

ArxOS daemon automatically:

1. Detects new/modified IFC file
2. Parses IFC entities and spatial data
3. Imports to PostGIS with precise coordinates
4. Maintains spatial indices for fast queries
5. Triggers export generation

```bash
# Monitor import progress
arx daemon logs --follow

# Example log output:
2025-09-17 10:15:23 INFO: Detected IFC file: Building_A.ifc
2025-09-17 10:15:24 INFO: Parsing IFC entities...
2025-09-17 10:15:26 INFO: Found 1,234 equipment items
2025-09-17 10:15:27 INFO: Importing to PostGIS...
2025-09-17 10:15:30 INFO: Import complete
2025-09-17 10:15:31 INFO: Generating exports...
```

### Step 3: Query Spatial Data

```bash
# Find equipment near a point (AR/VR use case)
arx query --near "12.547,8.291,1.127" --radius 2.0

# Find all equipment in a room
arx query --room "A-301"

# Find equipment by type within area
arx query --type HVAC --within "floor:3"

# Complex spatial queries
arx query --sql "SELECT * FROM equipment \
  WHERE ST_DWithin(location, \
    ST_MakePoint(12.5, 8.3, 1.1), 5.0) \
  AND status = 'MAINTENANCE'"
```

### Step 4: Use Generated Exports

Exports are automatically generated in `.arxos/exports/{building_name}/`:

```
.arxos/exports/Building_A/
├── building.bim.txt       # Human-readable text format
├── equipment.csv          # Equipment list for Excel
├── maintenance.csv        # Maintenance schedule
├── summary.csv           # Building statistics
├── building.json         # Complete building data
└── equipment.json        # Equipment with spatial data
```

#### .bim.txt Format (CLI Users)
```
# ArxOS Building Information Model
BUILDING: UUID-001 Medical Center

FLOOR: 3 Third Floor
  ROOM: A-301 Operating Room
    EQUIPMENT: EQ-001 [hvac] AC Unit <maintenance>
      # Serial: AC5000-123
      # Installed: 2024-03-15
    EQUIPMENT: EQ-002 [electrical] Outlet Panel
```

#### CSV Export (Excel/Reports)
```csv
ID,Name,Type,Status,Room,Installed,Notes
EQ-001,AC Unit,HVAC,MAINTENANCE,A-301,2024-03-15,Needs filter
EQ-002,Outlet Panel,ELECTRICAL,OPERATIONAL,A-301,2024-03-15,
```

#### JSON Export (API/Integration)
```json
{
  "uuid": "UUID-001",
  "name": "Medical Center",
  "floors": [
    {
      "level": 3,
      "name": "Third Floor",
      "rooms": [...],
      "equipment": [...]
    }
  ],
  "statistics": {
    "total_equipment": 1234,
    "status_counts": {
      "OPERATIONAL": 1100,
      "MAINTENANCE": 134
    }
  }
}
```

## Advanced Features

### Spatial Precision

PostGIS stores coordinates with millimeter precision using SRID 900913:

```sql
-- Equipment location stored as 3D point
CREATE TABLE equipment (
  id TEXT PRIMARY KEY,
  name TEXT,
  location GEOMETRY(PointZ, 900913),
  ...
);

-- Spatial index for fast queries
CREATE INDEX idx_equipment_location 
  ON equipment USING GIST(location);
```

### Multi-User Collaboration

Multiple BIM tools can export to the same watched directory:

```yaml
daemon:
  watch_paths:
    - "~/Shared/BIM/*.ifc"     # Shared network drive
  merge_strategy: latest        # or 'combine'
  conflict_resolution: timestamp
```

### Version Control Integration

```bash
# Auto-commit exports to Git
arx daemon --git-sync

# Track changes over time
cd .arxos/exports/Building_A
git log --oneline building.bim.txt
```

### Custom Export Triggers

```bash
# Manual export generation
arx export Building_A --format all

# Export specific formats
arx export Building_A --format csv,json

# Export with filters
arx export Building_A --status MAINTENANCE --to maintenance_report.csv
```

## AR/VR Integration

The PostGIS spatial database enables precise AR/VR applications:

```bash
# Query equipment visible from current position
arx query --viewpoint "10.0,5.0,1.7" --fov 90 --distance 10

# Get equipment for HoloLens overlay
arx query --format json --near "${DEVICE_POSITION}" --radius 5 \
  | curl -X POST https://hololens.local/api/overlay
```

## Troubleshooting

### IFC File Not Detected

1. Check daemon is running: `arx daemon status`
2. Verify watch path: `arx daemon config`
3. Check file permissions
4. Review logs: `arx daemon logs`

### Import Errors

```bash
# Validate IFC file
arx validate Building.ifc

# Check PostGIS connection
arx db test

# Re-import with debug info
arx import Building.ifc --debug
```

### Performance Optimization

```bash
# Optimize PostGIS indices
arx db optimize

# Configure daemon performance
arx daemon config --set poll_interval=1s
arx daemon config --set batch_size=1000
```

## Best Practices

1. **IFC Export Settings**:
   - Use IFC4 when available
   - Include property sets
   - Export space boundaries
   - Maintain consistent coordinate systems

2. **Directory Organization**:
   ```
   ~/Projects/BIM/
   ├── Active/        # Watched by daemon
   ├── Archive/       # Historical versions
   └── Templates/     # IFC export templates
   ```

3. **Naming Conventions**:
   ```
   BuildingName_v1.0.ifc
   BuildingName_2025-09-17.ifc
   BuildingName_FINAL.ifc
   ```

4. **Regular Maintenance**:
   ```bash
   # Weekly database optimization
   arx db vacuum
   
   # Monthly export cleanup
   arx export cleanup --older-than 30d
   
   # Quarterly database backup
   arx db backup --to s3://backups/arxos/
   ```

## Integration Examples

### Power BI Dashboard

```python
# Python script for Power BI
import pandas as pd
import json

# Load ArxOS JSON export
with open('.arxos/exports/Building/equipment.json') as f:
    data = json.load(f)

df = pd.DataFrame(data['equipment'])
# Create visualizations...
```

### Maintenance System Integration

```bash
# Export maintenance schedule to CMMS
arx export Building --format csv --status MAINTENANCE | \
  curl -X POST https://cmms.company.com/api/import \
    -H "Content-Type: text/csv" \
    --data-binary @-
```

### Real-time Monitoring

```javascript
// Node.js WebSocket server
const ws = require('ws');
const { exec } = require('child_process');

setInterval(() => {
  exec('arx query --status FAILED --format json', (err, stdout) => {
    if (!err) {
      const failures = JSON.parse(stdout);
      broadcast({ type: 'equipment_failures', data: failures });
    }
  });
}, 5000);
```

## Summary

The ArxOS professional workflow provides:

- **Seamless Integration**: Works with any BIM tool that exports IFC
- **Automatic Synchronization**: Daemon watches and imports changes
- **Spatial Precision**: PostGIS enables millimeter-accurate queries
- **Multiple Export Formats**: .bim.txt for CLI, CSV for Excel, JSON for APIs
- **Real-time Collaboration**: Multiple users, automatic updates
- **AR/VR Ready**: Spatial queries for mixed reality applications

For more information:
- Technical Details: [ARCHITECTURE.md](./ARCHITECTURE.md)
- API Reference: [API.md](./API.md)
- CLI Commands: [CLI.md](./CLI.md)
