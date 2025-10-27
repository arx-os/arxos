//! Integration tests for AR integration module
//!
//! These tests verify AR scan processing, pending equipment workflow, and confirmation.

use arxos::ar_integration::pending::{PendingEquipmentManager, DetectedEquipmentInfo, DetectionMethod};
use arxos::ar_integration::processing::{ARScanData, DetectedEquipmentData, validate_ar_scan_data};
use arxos::spatial::{Point3D, BoundingBox3D};
use std::collections::HashMap;

#[test]
fn test_pending_equipment_creation() {
    // Test creating pending equipment
    let detected = DetectedEquipmentInfo {
        name: "Test Unit".to_string(),
        equipment_type: "HVAC".to_string(),
        position: Point3D { x: 10.0, y: 20.0, z: 0.0 },
        bounding_box: BoundingBox3D {
            min: Point3D { x: 9.5, y: 19.5, z: -1.0 },
            max: Point3D { x: 10.5, y: 20.5, z: 1.0 },
        },
        confidence: 0.95,
        detection_method: DetectionMethod::LiDAR,
        properties: HashMap::new(),
    };
    
    let mut manager = PendingEquipmentManager::new("test".to_string());
    let result = manager.add_pending_equipment(&detected, "scan_1", 1, Some("Room 101"), 0.8);
    
    assert!(result.is_ok());
    let pending_list = manager.list_pending();
    assert_eq!(pending_list.len(), 1);
}

#[test]
fn test_confidence_filtering() {
    // Test that low confidence equipment is filtered out
    let low_confidence = DetectedEquipmentInfo {
        name: "Low Conf".to_string(),
        equipment_type: "Test".to_string(),
        position: Point3D { x: 0.0, y: 0.0, z: 0.0 },
        bounding_box: BoundingBox3D {
            min: Point3D { x: -0.5, y: -0.5, z: -1.0 },
            max: Point3D { x: 0.5, y: 0.5, z: 1.0 },
        },
        confidence: 0.5, // Below threshold
        detection_method: DetectionMethod::Manual,
        properties: HashMap::new(),
    };
    
    let mut manager = PendingEquipmentManager::new("test".to_string());
    let result = manager.add_pending_equipment(&low_confidence, "scan_1", 1, None, 0.8);
    
    // Should return None for low confidence
    if let Ok(Some(_)) = result {
        panic!("Low confidence equipment should not be added");
    }
    
    assert_eq!(manager.list_pending().len(), 0);
}

#[test]
fn test_batch_operations() {
    // Test batch confirming multiple pending items
    let detected1 = DetectedEquipmentInfo {
        name: "Unit 1".to_string(),
        equipment_type: "HVAC".to_string(),
        position: Point3D { x: 10.0, y: 10.0, z: 0.0 },
        bounding_box: BoundingBox3D {
            min: Point3D { x: 9.5, y: 9.5, z: -1.0 },
            max: Point3D { x: 10.5, y: 10.5, z: 1.0 },
        },
        confidence: 0.95,
        detection_method: DetectionMethod::ARKit,
        properties: HashMap::new(),
    };
    
    let detected2 = DetectedEquipmentInfo {
        name: "Unit 2".to_string(),
        equipment_type: "Lighting".to_string(),
        position: Point3D { x: 20.0, y: 20.0, z: 2.0 },
        bounding_box: BoundingBox3D {
            min: Point3D { x: 19.5, y: 19.5, z: 1.5 },
            max: Point3D { x: 20.5, y: 20.5, z: 2.5 },
        },
        confidence: 0.92,
        detection_method: DetectionMethod::LiDAR,
        properties: HashMap::new(),
    };
    
    let mut manager = PendingEquipmentManager::new("test".to_string());
    
    let id1 = manager.add_pending_equipment(&detected1, "scan_1", 1, None, 0.8).unwrap().unwrap();
    let id2 = manager.add_pending_equipment(&detected2, "scan_1", 1, None, 0.8).unwrap().unwrap();
    
    assert_eq!(manager.list_pending().len(), 2);
    
    // Test batch reject
    let ids = vec![id1.as_str(), id2.as_str()];
    for id in &ids {
        assert!(manager.reject_pending(id).is_ok());
    }
    
    assert_eq!(manager.list_pending().len(), 0);
}

#[test]
fn test_ar_scan_validation_valid() {
    let valid_scan = ARScanData {
        detected_equipment: vec![
            DetectedEquipmentData {
                name: "VAV-301".to_string(),
                equipment_type: "HVAC".to_string(),
                position: Point3D { x: 10.0, y: 20.0, z: 0.0 },
                confidence: 0.95,
                detection_method: Some("ARKit".to_string()),
            },
        ],
    };
    
    assert!(validate_ar_scan_data(&valid_scan).is_ok());
}

#[test]
fn test_ar_scan_validation_invalid() {
    // Test empty equipment list
    let empty_scan = ARScanData {
        detected_equipment: vec![],
    };
    
    assert!(validate_ar_scan_data(&empty_scan).is_err());
    
    // Test invalid position
    let invalid_position = ARScanData {
        detected_equipment: vec![
            DetectedEquipmentData {
                name: "VAV-301".to_string(),
                equipment_type: "HVAC".to_string(),
                position: Point3D { x: 9999.0, y: 9999.0, z: 9999.0 }, // Out of bounds
                confidence: 0.95,
                detection_method: Some("ARKit".to_string()),
            },
        ],
    };
    
    assert!(validate_ar_scan_data(&invalid_position).is_err());
    
    // Test invalid confidence
    let invalid_confidence = ARScanData {
        detected_equipment: vec![
            DetectedEquipmentData {
                name: "VAV-301".to_string(),
                equipment_type: "HVAC".to_string(),
                position: Point3D { x: 10.0, y: 20.0, z: 0.0 },
                confidence: 1.5, // Invalid (> 1.0)
                detection_method: Some("ARKit".to_string()),
            },
        ],
    };
    
    assert!(validate_ar_scan_data(&invalid_confidence).is_err());
}

