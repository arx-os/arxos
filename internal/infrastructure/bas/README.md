# BAS Integration Package

## Overview

This package provides BAS (Building Automation System) integration capabilities for ArxOS, enabling import and management of control points from systems like Johnson Controls Metasys, Siemens Desigo, Honeywell EBI, and Tridium Niagara.

## Components

### CSV Parser (`csv_parser.go`)

Parses BAS point list exports in CSV format.

**Features:**
- Smart column detection (handles various column names)
- Location text parsing (extracts floor/room from text)
- Point type inference (temperature, pressure, flow, etc.)
- BAS system type detection
- Validation and error handling

**Usage:**
```go
parser := bas.NewCSVParser()

// Parse CSV file
result, err := parser.ParseCSV("metasys_export.csv")
if err != nil {
    // Handle error
}

// Convert to domain entities
buildingID := types.FromString("bldg-001")
systemID := types.FromString("sys-001")
points := parser.ToBASPoints(result, buildingID, systemID)

// Parse location text
location := parser.ParseLocationText("Floor 3 Room 301")
// location.Floor = "3"
// location.Room = "301"
```

## Supported BAS Systems

### Johnson Controls Metasys
- CSV exports from Site Management Portal (SMP)
- Standard column format
- Auto-detected from filename containing "metasys"

### Siemens Desigo
- CSV exports from Desigo CC
- Standard point database format
- Auto-detected from filename containing "desigo" or "siemens"

### Honeywell EBI
- CSV exports from EBI R500
- Database manager exports
- Auto-detected from filename containing "honeywell" or "ebi"

### Tridium Niagara
- CSV exports from Niagara Workbench
- Station point exports
- Auto-detected from filename containing "niagara" or "tridium"

### Generic
- Any BAS with CSV export
- Minimum columns: Point Name, Device, Object Type
- Manual system type specification

## CSV Column Mapping

The parser automatically detects these column name variations:

| Standard | Variations |
|----------|------------|
| Point Name | PointName, Point_Name, Name, Point ID, PointID |
| Device | Device ID, DeviceID, Device_ID, Device Instance |
| Object Type | ObjectType, Object_Type, Type, Point Type |
| Description | Desc, Label |
| Units | Unit, Engineering Units, EU |
| Location | Room, Space, Area, Zone |

All detection is case-insensitive.

## Point Type Inference

The parser infers point types from object type, description, and units:

| Inferred Type | Detection Criteria |
|---------------|-------------------|
| temperature | Description contains "temp" OR units = "degF/degC" |
| pressure | Description contains "pressure" OR units = "PSI/Pa" |
| flow | Description contains "flow" OR units = "CFM/GPM" |
| control | Description contains "damper/valve" |
| fan_status | Description contains "fan/blower" |
| setpoint | Description contains "setpoint/sp" |
| analog_sensor | Object type = "Analog Input" |
| analog_control | Object type = "Analog Output" |
| binary_sensor | Object type = "Binary Input" |
| binary_control | Object type = "Binary Output" |

## Location Parsing

The parser extracts structured location from free text:

**Input Examples:**
- "Floor 3 Room 301" → Floor: 3, Room: 301
- "3rd Floor Room 301" → Floor: 3, Room: 301
- "Fl 3 Rm 301" → Floor: 3, Room: 301
- "Level 2 Conference A" → Floor: 2, Room: a
- "Building 1 Floor 3 Room 301" → Building: 1, Floor: 3, Room: 301

## Error Handling

The parser handles errors gracefully:

- **Missing required columns**: Returns error with list of missing columns
- **Empty rows**: Skips automatically
- **Parse errors**: Collects per-row errors, continues processing
- **Invalid file**: Validates before parsing
- **Large files**: Checks 100MB limit

**Example Error Handling:**
```go
result, err := parser.ParseCSV("points.csv")
if err != nil {
    return err
}

// Check for partial errors
if len(result.ParseErrors) > 0 {
    for _, parseErr := range result.ParseErrors {
        log.Printf("Warning: %s", parseErr)
    }
}

// Process successfully parsed points
for _, point := range result.Points {
    // ...
}
```

## Testing

Run tests:
```bash
# Unit tests
go test ./internal/infrastructure/bas/...

# With coverage
go test ./internal/infrastructure/bas/... -cover

# Benchmark
go test ./internal/infrastructure/bas/... -bench=.
```

## Performance

**Benchmarks** (1000 points):
- Parse CSV: ~5-10ms
- Column detection: <1ms per file
- Location parsing: <1ms per point

**Memory Usage:**
- Small files (<1MB): <10MB RAM
- Large files (10MB): ~50MB RAM
- Streaming for files >100MB (future)

## Future Enhancements

- [ ] XML parser for advanced exports
- [ ] JSON parser for modern systems
- [ ] Excel (.xlsx) parser
- [ ] Live BACnet connection (read-only)
- [ ] Modbus TCP connection (read-only)
- [ ] Real-time value monitoring
- [ ] Historical data import

## Related Documentation

- [BAS Integration Guide](../../../docs/integration/BAS_INTEGRATION.md)
- [PostGIS BAS Repository](../postgis/bas_point_repo.go)
- [BAS Domain Models](../../domain/bas.go)
- [BAS Import Use Case](../../usecase/bas_import_usecase.go)

