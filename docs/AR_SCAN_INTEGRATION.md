# ArxOS AR Scan Integration Guide

**Version:** 1.0  
**Date:** December 2024  
**Author:** ArxOS Development Team

---

## Overview

ArxOS supports AR (Augmented Reality) and LiDAR scan integration for automatic equipment detection and building mapping. This feature allows mobile devices to scan buildings and create pending equipment items that can be reviewed and confirmed before being added to the building data.

## Features

- **AR/LiDAR Integration**: Automatic equipment detection from mobile scans
- **Pending Equipment Workflow**: Review and confirm detected equipment
- **Confidence-Based Filtering**: Only high-confidence detections create pending items
- **CLI Management**: Full command-line interface for pending equipment management
- **Git Integration**: Automatic commits of confirmed equipment

---

## AR Scan Data Format

ArxOS accepts AR scan data in JSON format from mobile applications:

```json
{
  "detectedEquipment": [
    {
      "name": "VAV-301",
      "type": "HVAC",
      "position": {
        "x": 10.5,
        "y": 8.2,
        "z": 0.0
      },
      "confidence": 0.95,
      "detectionMethod": "ARKit"
    },
    {
      "name": "Light-Fixture-301",
      "type": "Lighting",
      "position": {
        "x": 10.0,
        "y": 10.0,
        "z": 2.5
      },
      "confidence": 0.88,
      "detectionMethod": "LiDAR"
    }
  ],
  "roomBoundaries": {
    "walls": [
      {
        "startPoint": {"x": 8.0, "y": 5.0, "z": 0.0},
        "endPoint": {"x": 13.0, "y": 5.0, "z": 0.0},
        "height": 3.0,
        "thickness": 0.2
      }
    ],
    "openings": [
      {
        "position": {"x": 10.5, "y": 5.0, "z": 0.0},
        "width": 0.9,
        "height": 2.1,
        "type": "door"
      }
    ]
  }
}
```

---

## Workflow

### 1. AR Scan Processing

Process an AR scan to create pending equipment:

```bash
# Process AR scan and create pending equipment
arx process-ar-scan scan.json --building "Main Building" --confidence 0.8
```

This will:
1. Validate the scan data
2. Filter by confidence threshold (default: 0.8)
3. Create pending equipment items
4. Save pending IDs to a JSON file (optional)

### 2. List Pending Equipment

View pending equipment that needs confirmation:

```bash
# List all pending equipment
arx ar pending list --building "Main Building"

# With verbose output
arx ar pending list --building "Main Building" --verbose

# Filter by floor
arx ar pending list --building "Main Building" --floor 2
```

### 3. Confirm Individual Equipment

Confirm a single pending equipment item:

```bash
# Confirm and create equipment
arx ar pending confirm <pending_id> --building "Main Building" --commit

# Without Git commit (save only)
arx ar pending confirm <pending_id> --building "Main Building"
```

### 4. Batch Confirm Multiple Items

Confirm multiple pending items at once:

```bash
# Confirm multiple pending equipment
arx ar pending batch-confirm <id1> <id2> <id3> --building "Main Building" --commit
```

### 5. Reject Equipment

Reject pending equipment that was incorrectly detected:

```bash
# Reject a pending equipment item
arx ar pending reject <pending_id>
```

---

## Configuration

### Confidence Threshold

Control the minimum confidence score for creating pending equipment:

- **Default**: 0.8 (80%)
- **Recommended**: 0.75-0.90 for balance between false positives and misses
- **High precision**: 0.9+ (fewer items, higher quality)
- **High recall**: 0.6+ (more items, needs more review)

```bash
# Set confidence threshold during processing
arx process-ar-scan scan.json --building "Main Building" --confidence 0.85
```

### Detection Methods

ArxOS supports multiple detection methods:

- **ARKit**: iOS ARKit-based detection
- **ARCore**: Android ARCore-based detection
- **LiDAR**: LiDAR sensor detection (iPhone 12 Pro+, iPad Pro)
- **AI**: AI-powered object detection
- **Manual**: Manual tagging

---

## Data Persistence

### Pending Equipment Storage

Pending equipment can be saved to file during processing:

```bash
# Save pending equipment to file
arx process-ar-scan scan.json \
  --building "Main Building" \
  --confidence 0.8 \
  --output pending-equipment.json
```

This creates a JSON file containing all pending equipment IDs:

```json
{
  "building": "Main Building",
  "pending_ids": [
    "pending_1701234567",
    "pending_1701234568"
  ],
  "created_at": "2024-12-01T10:30:00Z"
}
```

### Loading Pending Equipment

Pending equipment files can be loaded and processed:

```bash
# Future: Load and confirm pending equipment from file
# (Feature planned for next release)
```

---

## Integration with Mobile Apps

### iOS (Swift)

```swift
import ARKit

// AR session callback
func session(_ session: ARSession, didUpdate frame: ARFrame) {
    // Detect equipment
    let detectedEquipment = detectEquipment(frame: frame)
    
    // Convert to ArxOS format
    let arxosData = convertToArxOSFormat(equipment: detectedEquipment)
    
    // Send to ArxOS
    sendToArxOS(data: arxosData)
}
```

### Android (Kotlin)

```kotlin
import com.google.ar.core.ArCoreApk

// AR session callback
fun onFrame(frame: Frame) {
    // Detect equipment
    val detectedEquipment = detectEquipment(frame)
    
    // Convert to ArxOS format
    val arxosData = convertToArxOSFormat(detectedEquipment)
    
    // Send to ArxOS
    sendToArxOS(arxosData)
}
```

---

## Best Practices

### 1. Scan Quality

- **Lighting**: Ensure adequate lighting for AR detection
- **Stability**: Hold device steady while scanning
- **Coverage**: Scan entire room/floor for comprehensive data
- **Movement**: Slow, deliberate movements for better accuracy

### 2. Confidence Thresholds

- **Production**: Use 0.8+ for fewer false positives
- **Development**: Use 0.7+ for testing and calibration
- **Emergency**: Use 0.9+ for critical equipment only

### 3. Review Process

- **Always review**: Review pending equipment before confirming
- **Verify accuracy**: Check position and equipment type
- **Batch operations**: Use batch confirm for multiple similar items
- **Git commits**: Commit changes regularly

### 4. Data Validation

- **Check positions**: Verify equipment positions are reasonable
- **Validate types**: Confirm equipment types are correct
- **Review boundaries**: Check room boundaries are accurate
- **Threshold limits**: Ensure values are within acceptable ranges

---

## Troubleshooting

### Common Issues

#### "No pending equipment found"

**Cause**: Confidence threshold too high, or scan didn't detect any equipment  
**Solution**: Lower the confidence threshold or re-scan the area

```bash
# Lower confidence threshold
arx process-ar-scan scan.json --building "Main Building" --confidence 0.6
```

#### "Invalid AR scan data"

**Cause**: JSON format incorrect or missing required fields  
**Solution**: Validate JSON against expected schema

```bash
# Validate JSON format
cat scan.json | python -m json.tool
```

#### "Equipment not found during confirmation"

**Cause**: Pending equipment was already confirmed or rejected  
**Solution**: Check pending equipment list

```bash
# List pending equipment
arx ar pending list --building "Main Building" --verbose
```

---

## API Reference

### CLI Commands

```bash
# AR scan processing
arx process-ar-scan <file> --building <name> [--confidence <float>] [--output <file>]

# Pending equipment management
arx ar pending list --building <name> [--floor <level>] [--verbose]
arx ar pending confirm <id> --building <name> [--commit]
arx ar pending reject <id>
arx ar pending batch-confirm <ids...> --building <name> [--commit]
```

### Rust API

```rust
use arxos::ar_integration::{
    process_ar_scan_to_pending,
    validate_ar_scan_data,
    PendingEquipmentManager,
    PendingEquipment
};

// Process AR scan
let pending_ids = process_ar_scan_to_pending(&scan_data, building_name, 0.8)?;

// Create pending equipment manager
let manager = PendingEquipmentManager::new(building_name.to_string());

// Add pending equipment
let pending_id = manager.add_pending_equipment(
    &detected_info,
    scan_id,
    floor_level,
    room_name,
    confidence_threshold
)?;

// Confirm pending equipment
let equipment_id = manager.confirm_pending(pending_id, &mut building_data)?;
```

---

## Examples

### Complete Workflow

```bash
# 1. Process AR scan
arx process-ar-scan room_scan.json --building "Office Building" --confidence 0.8

# 2. Review pending equipment
arx ar pending list --building "Office Building" --verbose

# 3. Confirm individual items
arx ar pending confirm pending_1701234567 --building "Office Building" --commit

# 4. Batch confirm multiple items
arx ar pending batch-confirm pending_1701234568 pending_1701234569 --building "Office Building" --commit

# 5. Reject false positives
arx ar pending reject pending_1701234570
```

### Integration with Sensor Data

```bash
# 1. Process AR scan to find equipment
arx process-ar-scan scan.json --building "Building A" --confidence 0.85

# 2. Confirm equipment positions
arx ar pending batch-confirm <ids> --building "Building A" --commit

# 3. Update sensor mappings
arx sensor process sensor-data/ --building "Building A" --commit

# 4. Equipment now has sensor data attached
arx render --building "Building A" --show-status
```

---

## Status

**Current Version**: 1.0  
**Last Updated**: December 2024  
**Maintainer**: ArxOS Development Team

---

## See Also

- [Hardware Integration Guide](hardware_integration.md)
- [User Guide](USER_GUIDE.md)
- [Architecture Documentation](ARCHITECTURE.md)

