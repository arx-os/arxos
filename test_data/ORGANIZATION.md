# Test Data Organization

This directory contains test fixtures for the ArxOS test suite.

## Structure

### `/inputs/`
Sample input files in various formats that the converter processes:
- `.ifc` - Industry Foundation Classes files
- `.csv` - COBie CSV exports
- `.json` - Haystack JSON files
- `.gbxml` - Green Building XML files

### `/expected/`
Expected output files for validation:
- `.bim.txt` - Expected BIM text format outputs
- `.txt` - Other expected text outputs

## Usage

Test files reference these fixtures using relative paths:
```go
inputFile := "../../test_data/inputs/sample.ifc"
expectedOutput := "../../test_data/expected/building_from_ifc.bim.txt"
```

## Adding New Test Data

1. Place input files in `/inputs/` with descriptive names
2. Place expected outputs in `/expected/` with matching names
3. Use consistent naming: `sample_<format>` for inputs, `<description>_output` for expected