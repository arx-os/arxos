# ArxOS JSON API Reference

The ArxOS CLI supports JSON output for all commands, enabling seamless integration with scripts, automation tools, and external systems. This document describes the JSON output format and provides usage examples.

## Global JSON Flag

Add the `--json` flag to any ArxOS command to receive structured JSON output instead of human-readable text:

```bash
arx --json [command]
```

## JSON Output Structure

All JSON responses follow a consistent wrapper format:

```json
{
  "success": true|false,
  "data": <command-specific-data>,
  "error": "error message if success=false",
  "timestamp": 1757554965,
  "command": "command-name",
  "version": "1.0.0"
}
```

### Fields

- **success**: Boolean indicating if the command executed successfully
- **data**: Command-specific response data (only present if success=true)
- **error**: Error message (only present if success=false)
- **timestamp**: Unix timestamp when the response was generated
- **command**: Name of the command that was executed
- **version**: ArxOS version that generated the response

## Command-Specific Responses

### Import Command

Import a PDF floor plan and receive structured information about the extraction:

```bash
arx --json import floor_plan.pdf
```

Response:
```json
{
  "success": true,
  "data": {
    "source_file": "floor_plan.pdf",
    "floor_plan": {
      "name": "floor_plan",
      "building": "Imported Building",
      "level": 1,
      "room_count": 9,
      "equipment_count": 12,
      "file_path": "floor_plan.json"
    },
    "state_file": ".arxos/floor_plan.json",
    "extraction_type": "standard",
    "processing_time_ms": 5.2
  },
  "timestamp": 1757554965,
  "command": "import",
  "version": "1.0.0"
}
```

### List Command

List all available floor plans with detailed information:

```bash
arx --json list
```

Response:
```json
{
  "success": true,
  "data": [
    {
      "name": "Floor 2",
      "building": "Building 42",
      "level": 2,
      "room_count": 8,
      "equipment_count": 15,
      "file_path": "floor2.json"
    }
  ],
  "timestamp": 1757554968,
  "command": "list",
  "version": "1.0.0"
}
```

### Status Command

Get comprehensive status information about a floor plan:

```bash
arx --json status
```

Response:
```json
{
  "success": true,
  "data": {
    "floor_plan": {
      "name": "Floor 2",
      "building": "Building 42", 
      "level": 2,
      "room_count": 8,
      "equipment_count": 15,
      "file_path": "floor2.json"
    },
    "equipment_summary": {
      "normal": 12,
      "needs_repair": 2,
      "failed": 1,
      "unknown": 0
    },
    "failed_equipment": [
      {
        "id": "outlet_2b",
        "name": "Outlet 2B",
        "type": "outlet",
        "status": "failed",
        "room_id": "room_2b",
        "location": {"x": 15.5, "y": 10.2},
        "notes": "Ground fault detected"
      }
    ],
    "needs_repair": [
      {
        "id": "switch_1a",
        "name": "Switch 1A",
        "type": "switch",
        "status": "needs-repair",
        "room_id": "room_1a",
        "notes": "Port 3 intermittent"
      }
    ],
    "total_equipment": 15
  },
  "timestamp": 1757554972,
  "command": "status",
  "version": "1.0.0"
}
```

### Query Command

Execute SQL queries and receive structured results:

```bash
arx --json query "SELECT name, type, status FROM equipment WHERE status = 'failed'"
```

Response:
```json
{
  "success": true,
  "data": {
    "columns": ["name", "type", "status"],
    "rows": [
      ["Outlet 2B", "outlet", "failed"],
      ["Panel 1A", "panel", "failed"]
    ],
    "row_count": 2,
    "query": "SELECT name, type, status FROM equipment WHERE status = 'failed'"
  },
  "timestamp": 1757554982,
  "command": "query",
  "version": "1.0.0"
}
```

### Monitor Command (Snapshot)

Get a real-time snapshot of building system metrics:

```bash
arx --json monitor --snapshot
```

Response:
```json
{
  "success": true,
  "data": {
    "timestamp": "2025-09-10T21:42:55Z",
    "system_health": {
      "score": 87.5,
      "status": "good",
      "healthy_systems": 12,
      "critical_systems": 1,
      "uptime_seconds": 3600
    },
    "energy_metrics": {
      "electrical": {
        "efficiency": 92.3,
        "total_flow": 1250.5,
        "total_loss": 96.2
      }
    },
    "connection_metrics": {
      "active_connections": 45,
      "total_connections": 48,
      "error_rate": 2.1,
      "throughput_mbps": 854.2
    },
    "equipment_metrics": {
      "outlet_2b": {
        "health_score": 15.2,
        "failure_probability": 0.85,
        "maintenance_due": "2025-09-15T09:00:00Z"
      }
    },
    "alerts": [
      {
        "id": "alert_001",
        "type": "equipment_failure",
        "severity": "critical",
        "message": "Outlet 2B has failed - ground fault detected",
        "equipment_id": "outlet_2b",
        "timestamp": "2025-09-10T21:30:00Z",
        "acknowledged": false
      }
    ]
  },
  "timestamp": 1757554975,
  "command": "monitor",
  "version": "1.0.0"
}
```

### Trace Command

Trace equipment connections with structured path information:

```bash
arx --json trace outlet_2b upstream
```

Response:
```json
{
  "success": true,
  "data": {
    "start_equipment": "outlet_2b",
    "direction": "upstream",
    "max_depth": 10,
    "results": [
      {
        "level": 1,
        "equipment": {
          "id": "circuit_15",
          "name": "Circuit 15",
          "type": "circuit",
          "status": "normal"
        }
      },
      {
        "level": 2,
        "equipment": {
          "id": "panel_2b",
          "name": "Panel 2B",
          "type": "panel",
          "status": "normal"
        }
      }
    ],
    "total_found": 2
  },
  "timestamp": 1757554990,
  "command": "trace", 
  "version": "1.0.0"
}
```

## Integration Examples

### Shell Scripts

Use jq to process ArxOS JSON output:

```bash
#!/bin/bash
# Get all failed equipment
failed_equipment=$(arx --json status | jq -r '.data.failed_equipment[].id')
echo "Failed equipment: $failed_equipment"

# Check system health
health_score=$(arx --json monitor --snapshot | jq -r '.data.system_health.score')
if (( $(echo "$health_score < 80" | bc -l) )); then
    echo "WARNING: System health below 80%: $health_score%"
fi
```

### Python Integration

```python
import subprocess
import json

def get_equipment_status():
    """Get equipment status from ArxOS"""
    result = subprocess.run(['arx', '--json', 'status'], 
                          capture_output=True, text=True)
    data = json.loads(result.stdout)
    
    if data['success']:
        return data['data']
    else:
        raise Exception(f"ArxOS error: {data['error']}")

def find_failed_equipment():
    """Find all failed equipment"""
    result = subprocess.run(['arx', '--json', 'query', 
                           'SELECT * FROM equipment WHERE status = "failed"'],
                          capture_output=True, text=True)
    data = json.loads(result.stdout)
    
    if data['success']:
        return data['data']['rows']
    else:
        raise Exception(f"Query failed: {data['error']}")

# Usage
status = get_equipment_status()
print(f"Total equipment: {status['total_equipment']}")
print(f"Failed equipment: {len(status['failed_equipment'])}")
```

### Monitoring Integration

Use ArxOS JSON output with monitoring systems like Prometheus:

```bash
#!/bin/bash
# Extract metrics for Prometheus
SNAPSHOT=$(arx --json monitor --snapshot)

# Extract system health score
HEALTH_SCORE=$(echo "$SNAPSHOT" | jq -r '.data.system_health.score')
echo "arxos_system_health_score $HEALTH_SCORE"

# Extract active alerts count
ALERT_COUNT=$(echo "$SNAPSHOT" | jq -r '.data.summary.active_alerts')
echo "arxos_active_alerts_total $ALERT_COUNT"

# Extract connection health
CONN_HEALTH=$(echo "$SNAPSHOT" | jq -r '.data.summary.connection_health')
echo "arxos_connection_health_percent $CONN_HEALTH"
```

## Error Handling

When commands fail, the JSON response includes error information:

```json
{
  "success": false,
  "error": "PDF file not found: missing_file.pdf",
  "timestamp": 1757554995,
  "command": "import",
  "version": "1.0.0"
}
```

Always check the `success` field before processing the `data` field in your integrations.

## UNIX Pipe Compatibility

ArxOS JSON output is designed to work seamlessly with UNIX pipes and standard tools:

```bash
# Count failed equipment
arx --json status | jq '.data.failed_equipment | length'

# List equipment types
arx --json query "SELECT DISTINCT type FROM equipment" | jq -r '.data.rows[][0]'

# Monitor system health
arx --json monitor --snapshot | jq '.data.system_health.score'

# Export equipment list to CSV
arx --json query "SELECT name, type, status FROM equipment" | \
  jq -r '.data.rows[] | @csv' > equipment.csv
```

This JSON API enables ArxOS to integrate seamlessly with modern DevOps workflows, monitoring systems, and automation tools while maintaining its terminal-native philosophy.