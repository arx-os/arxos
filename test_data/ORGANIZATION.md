# Test Data Organization

This directory contains test fixtures for the ArxOS test suite.

## Structure

### `/inputs/`
Sample input files for IFC processing:
- `.ifc` - Industry Foundation Classes files (ONLY format supported)

**Error Testing Files:**
- `malformed.ifc` - Malformed IFC file for error handling tests

### `/expected/`
Expected output files for validation:
- `.bim.txt` - Expected BIM text format outputs
- `.txt` - Other expected text outputs

**Available Expected Outputs:**
- `building_from_ifc.bim.txt` - IFC conversion output
- `sample_floorplan.txt` - Reference floor plan

## Usage

Test files reference these fixtures using relative paths:
```go
inputFile := "../../test_data/inputs/sample.ifc"
expectedOutput := "../../test_data/expected/building_from_ifc.bim.txt"
```

## Adding New Test Data

1. Place IFC input files in `/inputs/` with descriptive names
2. Place expected outputs in `/expected/` with matching names
3. Use consistent naming: `sample_<description>.ifc` for inputs, `building_from_ifc.bim.txt` for expected
4. For error testing: use `malformed_<description>.ifc` or `invalid_<description>.ifc` naming
5. Update this documentation when adding new test scenarios

## Error Testing

The test data includes malformed files to test error handling:
- `malformed.ifc` - Contains invalid coordinates, circular references, and missing placements
- Use these files to ensure converters handle errors gracefully
- Expected behavior: Converter should detect errors and provide meaningful error messages
