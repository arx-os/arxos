# Arxos Demo Applications

This directory contains demonstration and diagnostic tools for the Arxos BIM system.

## PDF Wall Extraction Tools

### Diagnostic Tools (Main Deliverables)
- `hcps_diagnostic.html` - Version 1: Initial diagnostic tool (33 walls extraction)
- `hcps_diagnostic_v2.html` - Version 2: Enhanced extraction (40 walls)
- `hcps_diagnostic_v3.html` - Version 3: Advanced 1:1 accuracy (576+ walls)

### Wall Extractors
- `pdf_wall_extractor.html` - Original PDF wall extraction tool
- `pdf_wall_extractor_v2.html` - Enhanced version with better accuracy

### Reference Files
- `alafia_walls.html` - Wall extraction reference implementation
- `alafia_accurate.html` - Accuracy testing reference

## BIM Viewers
- `bim_viewer.html` - 2D BIM viewer interface
- `bim_3d_viewer.html` - 3D BIM visualization tool

## Demo Applications
- `demo.html` - Main Arxos demo interface
- `demo_upload.html` - File upload demonstration

## Running Demos

To run these demos locally:

```bash
# Using the demo script
./start_demo.sh

# Or start a simple HTTP server
python3 -m http.server 8080
# Then navigate to http://localhost:8080/demos/
```

## Development Notes

These tools demonstrate various capabilities of the Arxos system:
- PDF to BIM conversion with 95%+ accuracy
- Real-time wall extraction and visualization
- 2D/3D BIM rendering
- File upload and processing workflows

For production use, refer to the main Arxos API documentation.