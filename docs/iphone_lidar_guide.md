# iPhone LiDAR Scanning Guide

## Overview
Arxos processes iPhone LiDAR scans to create compressed building intelligence models using the ArxObject protocol. This guide covers the complete workflow from scanning to ASCII visualization.

## Supported Apps
- **3d Scanner App** - Recommended for detailed scans
- **Polycam** - Good for quick captures
- **Scaniverse** - Alternative option

## Scanning Process

### 1. Capture with iPhone
1. Open your scanning app
2. Scan the room slowly, ensuring complete coverage
3. Export as PLY format (important!)
4. Transfer via AirDrop, iCloud, or Termius SFTP

### 2. Processing Pipeline
```bash
# Basic ASCII rendering
cargo run --example ply_to_ascii <your_scan.ply>

# Enhanced rendering with statistics
cargo run --example ply_to_ascii_enhanced <your_scan.ply>

# 3D video game quality rendering
cargo run --example ply_to_ascii_3d <your_scan.ply>
```

## Technical Details

### ArxObject Protocol
- **Size**: 13 bytes per object
- **Compression**: Typically 98:1 ratio
- **Precision**: Millimeter-level positioning

### Point Cloud Processing
1. **Coordinate Transform**: Y-up (iPhone) → Z-up (building standard)
2. **Voxelization**: 5cm resolution for compression
3. **Object Detection**: RANSAC plane detection for walls/floors/ceilings
4. **Semantic Compression**: Equipment type classification

### ASCII Rendering Features
- Extended gradient palette (40+ characters)
- ANSI color support for height visualization
- Multiple view modes:
  - Top-down density map
  - 3D perspective view
  - Isometric game-style view
  - Cross-section slicing

## Example Output
```
═══ TOP-DOWN VIEW (Density Shaded) ═══
┌────────────────────────────────────┐
│████░░░░████████████████████░░░░████│
│████░░░░░░░░░░░░░░░░░░░░░░░░░░░░████│
│████░░░░░░░░░░░░░░░░░░░░░░░░░░░░████│
│████████████████░░░░████████████████│
└────────────────────────────────────┘
Scene: 2.9m × 3.5m × 1.8m
Compression: 98.2:1
```

## File Locations
- Scanner examples: `src/core/examples/`
- Point cloud parser: `src/core/point_cloud_parser.rs`
- Test data: Use your own iPhone scans in PLY format

## Tips
- Scan slowly for better point density
- Ensure good lighting conditions
- Complete coverage of walls and corners
- Export at highest quality available
- Use PLY format (not OBJ or others)