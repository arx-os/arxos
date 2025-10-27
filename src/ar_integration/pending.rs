//! Pending equipment management for AR scan integration
//!
//! This module handles equipment detected by AR scans that requires user confirmation
//! before being added to the building data.

use crate::yaml::{BuildingData, FloorData, EquipmentData, EquipmentStatus};
use crate::spatial::{Point3D, BoundingBox3D};
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use chrono::{DateTime, Utc};
use log::{info, warn};

/// Pending equipment from AR scan
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PendingEquipment {
    pub id: String,
    pub scan_id: String,
    pub name: String,
    pub equipment_type: String,
    pub position: Point3D,
    pub bounding_box: BoundingBox3D,
    pub confidence: f64,
    pub detection_method: DetectionMethod,
    pub detected_at: DateTime<Utc>,
    pub floor_level: i32,
    pub room_name: Option<String>,
    pub properties: HashMap<String, String>,
    pub status: PendingStatus,
}

/// Pending equipment status
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum PendingStatus {
    #[serde(rename = "pending")]
    Pending,
    #[serde(rename = "confirmed")]
    Confirmed,
    #[serde(rename = "rejected")]
    Rejected,
}

/// Detection method used
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum DetectionMethod {
    #[serde(rename = "ARKit")]
    ARKit,
    #[serde(rename = "ARCore")]
    ARCore,
    #[serde(rename = "LiDAR")]
    LiDAR,
    #[serde(rename = "Manual")]
    Manual,
    #[serde(rename = "AI")]
    AI,
}

/// Pending equipment manager
pub struct PendingEquipmentManager {
    pending_items: Vec<PendingEquipment>,
    building_name: String,
}

impl PendingEquipmentManager {
    /// Create a new pending equipment manager
    pub fn new(building_name: String) -> Self {
        Self {
            pending_items: Vec::new(),
            building_name,
        }
    }

    /// Add pending equipment from AR scan
    pub fn add_pending_equipment(
        &mut self,
        detected_equipment: &DetectedEquipmentInfo,
        scan_id: &str,
        floor_level: i32,
        room_name: Option<&str>,
        confidence_threshold: f64,
    ) -> Result<Option<String>, Box<dyn std::error::Error>> {
        // Filter by confidence threshold
        if detected_equipment.confidence < confidence_threshold {
            info!(
                "Equipment '{}' filtered out: confidence {} < threshold {}",
                detected_equipment.name, detected_equipment.confidence, confidence_threshold
            );
            return Ok(None);
        }

        let pending_id = format!("pending_{}", Utc::now().timestamp());
        
        let pending = PendingEquipment {
            id: pending_id.clone(),
            scan_id: scan_id.to_string(),
            name: detected_equipment.name.clone(),
            equipment_type: detected_equipment.equipment_type.clone(),
            position: detected_equipment.position.clone(),
            bounding_box: detected_equipment.bounding_box.clone(),
            confidence: detected_equipment.confidence,
            detection_method: detected_equipment.detection_method.clone(),
            detected_at: Utc::now(),
            floor_level,
            room_name: room_name.map(|s| s.to_string()),
            properties: detected_equipment.properties.clone(),
            status: PendingStatus::Pending,
        };

        info!("Added pending equipment: {} (confidence: {:.2})", pending.name, pending.confidence);
        self.pending_items.push(pending);

        Ok(Some(pending_id))
    }

    /// Get all pending equipment
    pub fn list_pending(&self) -> Vec<&PendingEquipment> {
        self.pending_items
            .iter()
            .filter(|item| item.status == PendingStatus::Pending)
            .collect()
    }

    /// Get pending equipment by ID
    pub fn get_pending(&self, id: &str) -> Option<&PendingEquipment> {
        self.pending_items.iter().find(|item| item.id == id)
    }

    /// Confirm pending equipment and create actual equipment
    pub fn confirm_pending(
        &mut self,
        pending_id: &str,
        building_data: &mut BuildingData,
    ) -> Result<String, Box<dyn std::error::Error>> {
        // First, update the status
        if let Some(pending) = self.pending_items
            .iter_mut()
            .find(|item| item.id == pending_id && item.status == PendingStatus::Pending) {
            pending.status = PendingStatus::Confirmed;
        }

        // Then get the pending data (clone to avoid borrow issues)
        let pending = self.pending_items
            .iter()
            .find(|item| item.id == pending_id)
            .ok_or_else(|| format!("Pending equipment '{}' not found", pending_id))?
            .clone();

        // Find or create the floor
        let floor_index = Self::find_or_create_floor(building_data, pending.floor_level)?;
        
        // Create equipment in building data
        let equipment_id = Self::add_equipment_to_building(
            building_data,
            floor_index,
            &pending,
        )?;

        info!("Confirmed pending equipment '{}' as equipment '{}'", pending_id, equipment_id);
        Ok(equipment_id)
    }

    /// Reject pending equipment
    pub fn reject_pending(&mut self, pending_id: &str) -> Result<(), Box<dyn std::error::Error>> {
        let pending = self.pending_items
            .iter_mut()
            .find(|item| item.id == pending_id && item.status == PendingStatus::Pending)
            .ok_or_else(|| format!("Pending equipment '{}' not found", pending_id))?;

        pending.status = PendingStatus::Rejected;
        
        info!("Rejected pending equipment '{}'", pending_id);
        Ok(())
    }

    /// Batch confirm multiple pending items
    pub fn batch_confirm(
        &mut self,
        pending_ids: Vec<&str>,
        building_data: &mut BuildingData,
    ) -> Result<Vec<String>, Box<dyn std::error::Error>> {
        let mut confirmed_equipment_ids = Vec::new();
        
        for pending_id in pending_ids {
            match self.confirm_pending(pending_id, building_data) {
                Ok(equipment_id) => confirmed_equipment_ids.push(equipment_id),
                Err(e) => {
                    warn!("Failed to confirm pending equipment '{}': {}", pending_id, e);
                }
            }
        }

        info!("Batch confirmed {} pending equipment items", confirmed_equipment_ids.len());
        Ok(confirmed_equipment_ids)
    }

    /// Find or create floor
    fn find_or_create_floor(building_data: &mut BuildingData, floor_level: i32) -> Result<usize, Box<dyn std::error::Error>> {
        if let Some(index) = building_data.floors.iter().position(|f| f.level == floor_level) {
            return Ok(index);
        }

        // Create new floor
        let new_floor = FloorData {
            id: format!("floor-{}", floor_level),
            name: format!("Floor {}", floor_level),
            level: floor_level,
            elevation: (floor_level as f64) * 3.0,
            rooms: Vec::new(),
            equipment: Vec::new(),
            bounding_box: None,
        };

        building_data.floors.push(new_floor);
        Ok(building_data.floors.len() - 1)
    }

    /// Add equipment to building data
    fn add_equipment_to_building(
        building_data: &mut BuildingData,
        floor_index: usize,
        pending: &PendingEquipment,
    ) -> Result<String, Box<dyn std::error::Error>> {
        let floor = &mut building_data.floors[floor_index];
        let equipment_id = format!("equipment_{}", pending.scan_id);

        let equipment = EquipmentData {
            id: equipment_id.clone(),
            name: pending.name.clone(),
            equipment_type: pending.equipment_type.clone(),
            system_type: pending.equipment_type.clone(),
            universal_path: format!("/BUILDING/FLOOR-{}/EQUIPMENT/{}", pending.floor_level, pending.name),
            position: pending.position.clone(),
            bounding_box: pending.bounding_box.clone(),
            status: EquipmentStatus::Healthy,
            properties: pending.properties.clone(),
            sensor_mappings: None,
        };

        floor.equipment.push(equipment);
        Ok(equipment_id)
    }
}

/// Detected equipment information (from AR scan)
#[derive(Debug, Clone)]
pub struct DetectedEquipmentInfo {
    pub name: String,
    pub equipment_type: String,
    pub position: Point3D,
    pub bounding_box: BoundingBox3D,
    pub confidence: f64,
    pub detection_method: DetectionMethod,
    pub properties: HashMap<String, String>,
}

/// Create pending equipment from AR scan
pub fn create_pending_equipment_from_ar_scan(
    detected_equipment: &DetectedEquipmentInfo,
    scan_id: &str,
    floor_level: i32,
    room_name: Option<&str>,
    confidence_threshold: f64,
) -> Result<Option<String>, Box<dyn std::error::Error>> {
    let mut manager = PendingEquipmentManager::new("default".to_string());
    manager.add_pending_equipment(detected_equipment, scan_id, floor_level, room_name, confidence_threshold)
}

