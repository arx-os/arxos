# Progressive Construction Pipeline Demo

This demo showcases the ArxOS Progressive Construction Pipeline - the complete **PDF → Measurements → LiDAR → 3D** workflow that transforms 2D building plans into precise 3D digital twins.

## Overview

The Progressive Construction Pipeline is ArxOS's core differentiator, implementing a 4-stage process:

1. **PDF Ingestion & Analysis** - Extract architectural elements from building plans
2. **Measurements Standardization** - Calibrate and validate dimensions against building codes
3. **LiDAR Guided Scanning** - Fuse PDF data with high-precision LiDAR measurements
4. **3D Reconstruction** - Generate accurate 3D models with sub-millimeter precision

## Quick Start

```bash
# Build and run the demo
make demo

# Or run the full cycle
make full-demo
```

## Usage

### Basic Demo
```bash
# Build the demo
make build

# Run with default configuration
./progressive-construction-demo
```

### Custom Configuration
The demo can be configured by modifying the pipeline configuration in `main.go`:

```go
config := &pipeline.PipelineConfig{
    EnableLiDARFusion:   true,     // Enable LiDAR integration
    RequiredAccuracy:    1.0,      // Accuracy requirement (mm)
    ConfidenceThreshold: 0.75,     // Minimum confidence threshold
    Generate3DMesh:      true,     // Generate 3D mesh files
    GenerateASCII:       true,     // Generate ASCII preview
    ValidateAgainstCode: true,     // Validate against building codes
}
```

### Testing
```bash
# Run unit tests
make test

# Run performance benchmarks
make benchmark
```

## Demo Output

The demo generates several outputs:

- **Pipeline Results** (`output/pipeline-results.json`) - Detailed processing results
- **ArxObjects** (`output/arxobjects/`) - Individual architectural objects
- **3D Mesh** (`output/*.obj`) - Generated 3D model (if enabled)
- **Progress Log** - Real-time processing updates

### Sample Output
```
ArxOS Progressive Construction Pipeline Demo
==========================================

Processing: ./demo/sample-floorplan.pdf
Building ID: demo-building-001

Starting Progressive Construction Pipeline...

[validation] 5.0% - Input validation complete
[pdf] 25.0% - PDF processing complete - 15 objects extracted
[measurements] 50.0% - Measurements extraction and calibration complete
[lidar] 75.0% - LiDAR fusion complete
[reconstruction] 90.0% - 3D reconstruction complete
[complete] 100.0% - Progressive construction pipeline complete

Pipeline Results Summary
========================
Processing Time: 2.34s
Total Objects Created: 18
Overall Confidence: 0.87
3D Mesh Generated: output/demo-building-001.obj

Stage Results:
--------------
✓ pdf: 15 objects, 0.82 confidence, 450ms processing time
✓ measurements: 15 objects, 0.89 confidence, 380ms processing time
✓ lidar: 16 objects, 0.91 confidence, 620ms processing time
✓ reconstruction: 1 objects, 0.90 confidence, 890ms processing time

Object Types Created:
--------------------
  room: 4
  wall: 8
  door: 2
  window: 3
  column: 1

Demo completed successfully!
Total processing time: 2.34s
Generated files in: ./output
```

## Architecture

The demo showcases the integration of all pipeline components:

```
PDF File → PDFStage → MeasurementStage → LiDARStage → ReconstructionStage → 3D Model
    ↓           ↓              ↓              ↓              ↓
ArxObjects → Enhanced → Calibrated → Fused → Reconstructed
                       ArxObjects   ArxObjects   ArxObjects
```

Each stage processes and enhances ArxObjects with:
- **Geometry** - Spatial coordinates and dimensions  
- **Properties** - Material, structural, and metadata
- **Confidence** - Multi-source confidence scoring
- **Relationships** - Spatial and functional connections

## Key Features Demonstrated

### PDF Processing
- Architectural element detection (walls, doors, windows, rooms)
- Scale extraction and coordinate transformation
- Measurement annotation parsing
- Building plan analysis with AI service integration

### Measurements Standardization  
- Dimension calibration and validation
- Building code compliance checking (IBC standards)
- Scale factor calculation and application
- Precision enhancement through multi-source validation

### LiDAR Integration
- Point cloud processing and plane detection
- PDF-to-LiDAR alignment algorithms
- Geometric fusion and accuracy improvement
- Sub-millimeter precision validation

### 3D Reconstruction
- Volumetric mesh generation from 2D plans
- Floor, wall, ceiling, and opening geometry
- OBJ/glTF export with materials
- Structural validation and optimization

## Performance Metrics

The demo tracks key performance indicators:

- **Processing Speed** - End-to-end workflow timing
- **Accuracy** - Geometric precision measurements  
- **Confidence** - Multi-stage confidence scoring
- **Object Yield** - Architectural elements extracted
- **Validation** - Building code compliance results

## Requirements

- Go 1.21+
- ArxOS core libraries
- AI service (Python) for PDF processing
- LiDAR processing libraries (optional)
- 3D mesh generation tools

## Troubleshooting

### Common Issues

1. **"AI service execution failed"** - Ensure Python AI service is running
2. **"LiDAR stage failed"** - Disable LiDAR fusion for PDF-only demo
3. **"Invalid file path"** - Place PDF files in `demo/` directory
4. **Low confidence scores** - Adjust `ConfidenceThreshold` in configuration

### Debug Mode
Set `ARXOS_DEBUG=1` for verbose logging:
```bash
ARXOS_DEBUG=1 ./progressive-construction-demo
```

## Next Steps

After running the demo:

1. **Try Real Data** - Place architectural PDFs in `demo/` directory
2. **Customize Pipeline** - Modify stage configurations
3. **Integration** - Connect to existing ArxOS workflows
4. **Performance** - Profile with larger datasets

This demo represents ArxOS's core value proposition: transforming traditional 2D building documentation into precise, intelligent 3D digital twins through progressive construction methodology.