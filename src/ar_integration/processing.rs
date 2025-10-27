//! AR scan processing and pending equipment creation
//!
//! This module handles processing AR scan data and creating pending equipment items
//! that can be reviewed and confirmed by users.

use super::pending::{PendingEquipmentManager, DetectedEquipmentInfo, DetectionMethod, PendingEquipment};
use crate::spatial::{Point3D, BoundingBox3D};
use std::collections::HashMap;
use chrono::Utc;
use log::{info, warn};

/// AR scan data for processing
#[derive(Debug, Clone)]
pub struct ARScanData {
    pub detected_equipment: Vec<DetectedEquipmentData>,
}

#[derive(Debug, Clone)]
pub struct DetectedEquipmentData {
    pub name: String,
    pub equipment_type: String,
    pub position: Point3D,
    pub confidence: f64,
    pub detection_method: Option<String>,
}

/// Process AR scan and create pending equipment
/// 
/// # Arguments
/// 
/// * `scan_data` - Parsed AR scan data
/// * `building_name` - Name of the building
/// * `confidence_threshold` - Minimum confidence score to create pending item
/// 
/// # Returns
/// 
/// Vector of pending equipment IDs created from the scan
pub fn process_ar_scan_to_pending(
    scan_data: &ARScanData,
    building_name: &str,
    confidence_threshold: f64,
) -> Result<Vec<String>, Box<dyn std::error::Error>> {
    info!("Processing AR scan for building: {}", building_name);
    
    let mut manager = PendingEquipmentManager::new(building_name.to_string());
    let mut pending_ids = Vec::new();
    
    for detected_eq in &scan_data.detected_equipment {
        // Validate confidence threshold
        if detected_eq.confidence < confidence_threshold {
            warn!("Filtered equipment '{}' due to low confidence: {:.2} < {:.2}", 
                detected_eq.name, detected_eq.confidence, confidence_threshold);
            continue;
        }
        
        let position = detected_eq.position.clone();
        
        let bounding_box = create_bounding_box_from_position(&position);
        
        // Convert to DetectedEquipmentInfo
        let detected_info = DetectedEquipmentInfo {
            name: detected_eq.name.clone(),
            equipment_type: detected_eq.equipment_type.clone(),
            position,
            bounding_box,
            confidence: detected_eq.confidence,
            detection_method: parse_detection_method(&detected_eq.detection_method),
            properties: HashMap::new(), // Can be extended with additional properties
        };
        
        // Add to pending
        if let Some(pending_id) = manager.add_pending_equipment(
            &detected_info,
            "ar_scan", // Use generic scan_id
            0, // Floor level will be determined during confirmation
            None, // Room name will be determined during confirmation
            confidence_threshold,
        )? {
            pending_ids.push(pending_id);
            info!("Created pending equipment: {} (confidence: {:.2})", 
                detected_info.name, detected_info.confidence);
        }
    }
    
    info!("Created {} pending equipment items from AR scan", pending_ids.len());
    Ok(pending_ids)
}

/// Create bounding box from position (default size)
fn create_bounding_box_from_position(position: &Point3D) -> BoundingBox3D {
    // Default bounding box: 1m x 1m x 2m
    BoundingBox3D {
        min: Point3D {
            x: position.x - 0.5,
            y: position.y - 0.5,
            z: position.z - 1.0,
        },
        max: Point3D {
            x: position.x + 0.5,
            y: position.y + 0.5,
            z: position.z + 1.0,
        },
    }
}

/// Parse detection method from string
fn parse_detection_method(method: &Option<String>) -> DetectionMethod {
    if let Some(ref method_str) = method {
        match method_str.to_lowercase().as_str() {
            "arkit" => DetectionMethod::ARKit,
            "arcore" => DetectionMethod::ARCore,
            "lidar" => DetectionMethod::LiDAR,
            "manual" => DetectionMethod::Manual,
            "ai" => DetectionMethod::AI,
            _ => DetectionMethod::Manual,
        }
    } else {
        DetectionMethod::Manual
    }
}

/// Validate AR scan data
/// 
/// Checks position bounds, equipment types, and other validation rules
pub fn validate_ar_scan_data(scan_data: &ARScanData) -> Result<(), Vec<String>> {
    let mut errors = Vec::new();
    
    // Validate scan ID
    if scan_data.detected_equipment.is_empty() {
        errors.push("AR scan contains no detected equipment".to_string());
    }
    
    // Validate each detected equipment
    for (i, equipment) in scan_data.detected_equipment.iter().enumerate() {
        // Check position bounds (reasonable building dimensions)
        if equipment.position.x.abs() > 1000.0 ||
           equipment.position.y.abs() > 1000.0 ||
           equipment.position.z.abs() > 100.0 {
            errors.push(format!(
                "Equipment '{}' (index {}) has invalid position: ({:.2}, {:.2}, {:.2})",
                equipment.name, i, equipment.position.x, equipment.position.y, equipment.position.z
            ));
        }
        
        // Check confidence bounds
        if equipment.confidence < 0.0 || equipment.confidence > 1.0 {
            errors.push(format!(
                "Equipment '{}' (index {}) has invalid confidence: {:.2}",
                equipment.name, i, equipment.confidence
            ));
        }
        
        // Check equipment type
        if equipment.equipment_type.is_empty() {
            errors.push(format!(
                "Equipment '{}' (index {}) has empty equipment type",
                equipment.name, i
            ));
        }
        
        // Validate equipment name
        if equipment.name.is_empty() {
            errors.push(format!(
                "Equipment at index {} has empty name",
                i
            ));
        }
    }
    
    if errors.is_empty() {
        Ok(())
    } else {
        Err(errors)
    }
}

/// Convert PendingEquipment to JSON for persistence
pub fn pending_equipment_to_json(pending: &PendingEquipment) -> Result<String, Box<dyn std::error::Error>> {
    serde_json::to_string(pending)
        .map_err(|e| format!("Failed to serialize pending equipment: {}", e).into())
}

/// Load pending equipment from JSON
pub fn pending_equipment_from_json(json: &str) -> Result<PendingEquipment, Box<dyn std::error::Error>> {
    serde_json::from_str(json)
        .map_err(|e| format!("Failed to deserialize pending equipment: {}", e).into())
}

/// Save pending equipment IDs to a JSON file
fn save_pending_equipment_to_file(
    pending_ids: &[String],
    file_path: &str,
    building_name: &str,
) -> Result<(), Box<dyn std::error::Error>> {
    
    use std::fs;
    use std::io::Write;
    
    #[derive(serde::Serialize)]
    struct PendingEquipmentList {
        building: String,
        pending_ids: Vec<String>,
        created_at: String,
    }
    
    let pending_list = PendingEquipmentList {
        building: building_name.to_string(),
        pending_ids: pending_ids.to_vec(),
        created_at: Utc::now().to_rfc3339(),
    };
    
    let json_content = serde_json::to_string_pretty(&pending_list)?;
    
    // Create the file
    let mut file = fs::File::create(file_path)?;
    file.write_all(json_content.as_bytes())?;
    
    info!("Pending equipment list saved to: {}", file_path);
    Ok(())
}

/// Process AR scan and save pending equipment to file
/// 
/// This creates pending equipment items and persists them to a YAML file
/// that can be loaded later for confirmation
pub fn process_ar_scan_and_save_pending(
    scan_data: &ARScanData,
    building_name: &str,
    confidence_threshold: f64,
    output_file: Option<&str>,
) -> Result<Vec<String>, Box<dyn std::error::Error>> {
    // Validate scan data first
    if let Err(errors) = validate_ar_scan_data(scan_data) {
        return Err(format!("AR scan validation failed: {:?}", errors).into());
    }
    
    // Process to pending
    let pending_ids = process_ar_scan_to_pending(scan_data, building_name, confidence_threshold)?;
    
    // Save pending equipment to file if output path provided
    if let Some(file) = output_file {
        info!("Saving pending equipment to file: {}", file);
        save_pending_equipment_to_file(&pending_ids, file, building_name)?;
    }
    
    Ok(pending_ids)
}

