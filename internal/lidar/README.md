# LiDAR Module

The LiDAR module provides point cloud processing capabilities for ArxOS, enabling high-precision spatial data capture and equipment detection from 3D scans.

## Overview

This module implements a complete pipeline for processing LiDAR and other point cloud data:
- Multiple format support (PLY, LAS, LAZ, E57)
- Point cloud alignment and registration
- Object detection and segmentation
- Equipment matching with existing building data
- Progressive scan integration

## Architecture

```
lidar/
├── types.go           # Point cloud data structures
├── pipeline.go        # Processing pipeline orchestration
├── formats/           # Format-specific readers
│   ├── ply.go        # Stanford PLY format
│   ├── las.go        # ASPRS LAS format
│   ├── laz.go        # Compressed LAS
│   └── e57.go        # ASTM E57 format
├── processing/        # Processing algorithms
│   ├── alignment.go   # Cloud alignment
│   ├── segmentation.go # Object segmentation
│   ├── filtering.go   # Noise filtering
│   └── matching.go    # Equipment matching
└── tests/            # Unit and integration tests
```

## Processing Pipeline

### 1. Data Ingestion
- Load point cloud from file
- Validate format and structure
- Extract metadata (scanner info, timestamps)

### 2. Preprocessing
- Remove noise and outliers
- Downsample for performance
- Apply color/intensity normalization

### 3. Alignment
- Detect ground plane
- Find building reference points
- Apply transformation matrix
- Register with existing scans

### 4. Segmentation
- Cluster points into objects
- Extract geometric primitives
- Identify walls, floors, ceilings

### 5. Object Detection
- Classify point clusters
- Extract object features
- Generate bounding boxes

### 6. Equipment Matching
- Compare with existing equipment
- Calculate match confidence
- Resolve ambiguities
- Update positions

## Usage

### Basic Point Cloud Processing

```go
import "github.com/arx-os/arxos/internal/lidar"

// Create pipeline
pipeline := lidar.NewPipeline()

// Load point cloud
cloud, err := pipeline.LoadPointCloud("scan.ply")
if err != nil {
    return err
}

// Preprocess
filtered := pipeline.FilterNoise(cloud, lidar.NoiseParams{
    StatisticalK: 50,
    StdDevMultiplier: 1.0,
})

// Downsample for performance
downsampled := pipeline.Downsample(filtered, 0.01) // 1cm resolution
```

### Alignment with Building

```go
// Create aligner
aligner := lidar.NewAligner(building)

// Detect ground plane
ground := aligner.DetectGroundPlane(cloud)

// Align to building coordinates
aligned, transform := aligner.AlignToBuilding(cloud, ground)

// Register with existing coverage
registration := aligner.RegisterWithExisting(aligned, coverageMap)
```

### Object Detection

```go
// Create detector
detector := lidar.NewObjectDetector()

// Segment point cloud
clusters := detector.SegmentObjects(aligned)

// Classify objects
for _, cluster := range clusters {
    object := detector.ClassifyObject(cluster)

    if object.Class == "electrical_outlet" {
        features := detector.ExtractFeatures(object)
        // Process electrical outlet
    }
}
```

### Equipment Matching

```go
// Create matcher
matcher := lidar.NewEquipmentMatcher(building)

// Configure matching parameters
matcher.SetThresholds(lidar.MatchThresholds{
    ShapeSimilarity: 0.8,
    SizeDeviation: 0.15,
    LocationRadius: 1.0, // meters
})

// Find matches for detected objects
for _, detected := range detectedObjects {
    candidates := matcher.FindCandidates(detected)

    if len(candidates) == 1 {
        // High confidence match
        matcher.UpdateEquipment(candidates[0], detected)
    } else {
        // Queue for manual review
        matcher.QueueForReview(detected, candidates)
    }
}
```

### Partial Scan Integration

```go
// Load partial scan (e.g., just one room)
partialScan, _ := pipeline.LoadPointCloud("conference_room.ply")

// Find overlap with existing model
overlap := matcher.DetectOverlap(partialScan, building)

// Merge partial scan
merger := lidar.NewPartialMerger(building)
result := merger.MergePartialScan(partialScan, overlap)

fmt.Printf("Matched: %d equipment\n", result.MatchedCount)
fmt.Printf("Unknown: %d objects\n", result.UnknownCount)
fmt.Printf("Coverage increased by: %.2f%%\n", result.CoverageIncrease)
```

## Supported Formats

### PLY (Polygon File Format)
```go
reader := formats.NewPLYReader()
cloud, err := reader.Read("scan.ply")
```

### LAS/LAZ (ASPRS LAS)
```go
reader := formats.NewLASReader()
cloud, err := reader.Read("scan.las")

// Compressed LAS
reader := formats.NewLAZReader()
cloud, err := reader.Read("scan.laz")
```

### E57 (ASTM E57)
```go
reader := formats.NewE57Reader()
cloud, err := reader.Read("scan.e57")
```

## Configuration

```yaml
lidar:
  processing:
    max_points: 10000000      # Maximum points to process
    downsample_resolution: 0.01 # Meters

  filtering:
    statistical_k: 50         # Neighbors for statistical filter
    std_dev_multiplier: 1.0   # Standard deviation threshold

  alignment:
    icp_iterations: 50        # ICP algorithm iterations
    convergence_threshold: 0.001

  detection:
    min_cluster_size: 100     # Minimum points for object
    cluster_tolerance: 0.05   # Meters

  matching:
    shape_threshold: 0.8      # Shape similarity [0-1]
    size_threshold: 0.15      # Size deviation tolerance
    location_threshold: 1.0   # Location deviation (meters)
```

## Performance Optimization

### Downsampling Strategies

```go
// Voxel grid downsampling
downsampled := pipeline.VoxelDownsample(cloud, 0.01) // 1cm voxels

// Random sampling
sampled := pipeline.RandomSample(cloud, 0.1) // Keep 10%

// Uniform sampling
uniform := pipeline.UniformSample(cloud, 1000000) // Keep 1M points
```

### Parallel Processing

```go
// Enable parallel processing
pipeline.SetParallel(true)
pipeline.SetWorkers(8)

// Process in chunks
chunks := pipeline.ChunkPointCloud(cloud, 1000000)
for _, chunk := range chunks {
    go processChunk(chunk)
}
```

## Testing

```bash
# Run all LiDAR tests
go test ./internal/lidar/...

# Run with test data
go test -v ./internal/lidar/tests/

# Benchmark processing
go test -bench=. ./internal/lidar/processing/
```

## Performance Targets

- Load 1M points: < 1 second
- Process 1M points: < 10 seconds
- Alignment: < 5 seconds
- Object detection: 70% accuracy
- Equipment matching: 80% accuracy

## Dependencies

- Point cloud processing libraries (to be integrated)
- Numerical computation (gonum)
- Parallel processing support

## Future Enhancements

- [ ] Machine learning object classification
- [ ] Real-time streaming processing
- [ ] GPU acceleration
- [ ] Advanced mesh reconstruction
- [ ] Semantic segmentation
- [ ] Change detection between scans