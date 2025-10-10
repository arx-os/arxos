# IFC Converter Test Output

This directory contains sample output from IFC format conversion, used for testing and validation.

## Files

- `building_from_ifc.bim.txt` - Output from IFC BIM model conversion
- `sample_floorplan.txt` - Reference floor plan output

## Purpose

These files serve as:
1. **Reference outputs** for IFC converter testing
2. **Regression test baselines** to ensure converter accuracy
3. **Format examples** showing what the IFC converter produces
4. **Integration test data** for the IFC conversion pipeline

## Usage

```bash
# Run converter accuracy tests
make test-integration

# Compare output against baseline
diff test_data/expected/building_from_ifc.bim.txt actual_output.bim.txt

# Validate converter output format
arx validate test_data/expected/building_from_ifc.bim.txt

# Test IFC converter
arx convert ifc-to-bim test_data/inputs/sample.ifc > test_output.bim.txt
diff test_data/expected/building_from_ifc.bim.txt test_output.bim.txt
```
