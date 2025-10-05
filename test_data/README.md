# Converter Test Output

This directory contains sample output from various format converters, used for testing and validation.

## Files

- `building_from_cobie.bim.txt` - Output from COBie spreadsheet conversion
- `building_from_gbxml.bim.txt` - Output from gbXML energy model conversion  
- `building_from_haystack.bim.txt` - Output from Haystack IoT data conversion
- `building_from_ifc.bim.txt` - Output from IFC BIM model conversion
- `merged_building.bim.txt` - Output from merging multiple input formats
- `sample_floorplan.txt` - Reference floor plan output

## Purpose

These files serve as:
1. **Reference outputs** for converter testing
2. **Regression test baselines** to ensure converter accuracy
3. **Format examples** showing what each converter produces
4. **Integration test data** for the conversion pipeline

## Usage

```bash
# Run converter accuracy tests
make test-integration

# Compare output against baselines
diff test_data/expected/building_from_ifc.bim.txt actual_output.bim.txt

# Validate converter output format
arx validate test_data/expected/building_from_ifc.bim.txt

# Test specific converter
arx convert ifc-to-bim test_data/inputs/sample.ifc > test_output.bim.txt
diff test_data/expected/building_from_ifc.bim.txt test_output.bim.txt
```
