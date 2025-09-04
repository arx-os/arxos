# Point Cloud Processor - External Service

## Purpose
This is an **external service** that processes point clouds and converts them to ASCII descriptions that ArxOS can route.

## Why External?
Per the ArxOS vision: **"ArxOS routes building intelligence, it doesn't process it."**

Point cloud processing is computationally intensive and violates the core principle of staying light (<5MB binary). This service should run separately and communicate with ArxOS via ASCII descriptions.

## Architecture
```
iPhone LiDAR → Point Cloud (1GB) → This Service → ASCII Description → ArxOS → ArxObject (13 bytes)
```

## Communication Protocol
This service sends ASCII descriptions to ArxOS:
```
ROOM @ (10.5, 20.3, 0)m DIMENSIONS:20x15x10
OUTLET @ (10.5, 2.3, 1.2)m CIRCUIT:15
DOOR @ (5.0, 0, 0)m WIDTH:0.9 HEIGHT:2.1
```

## Deployment
- Run offline on a separate local device when needed (no containers required)
- Communicate via local file drop or serial/BLE bridge (ASCII only)
- ArxOS receives ASCII, never processes point clouds directly

## Files
- `point_cloud_parser.rs` - Original parser implementation
- `point_cloud_parser_enhanced.rs` - Enhanced version with plane detection

These files are preserved here for reference but should NOT be compiled into the ArxOS core binary.