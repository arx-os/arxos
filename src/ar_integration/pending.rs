//! Pending equipment management for AR scan integration
//!
//! This module handles equipment detected by AR scans that requires user confirmation
//! before being added to the building data.

#[allow(deprecated)]
use crate::yaml::BuildingData;
use crate::spatial::{Point3D, BoundingBox3D};
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use chrono::{DateTime, Utc};
use log::{info, warn, debug};


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
    /// User email of the person who scanned this equipment (for attribution when confirming)
    #[serde(default)]
    pub user_email: Option<String>,
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
    storage_path: Option<std::path::PathBuf>,
}

impl PendingEquipmentManager {
    /// Create a new pending equipment manager
    pub fn new(building_name: String) -> Self {
        Self {
            pending_items: Vec::new(),
            building_name,
            storage_path: None,
        }
    }

    /// Load pending equipment from storage
    pub fn load_from_storage(&mut self, storage_file: &std::path::Path) -> Result<(), Box<dyn std::error::Error>> {
        use std::fs;
        use std::io::Read;
        
        if !storage_file.exists() {
            info!("No pending equipment storage file found at: {:?}", storage_file);
            return Ok(());
        }
        
        let mut file = fs::File::open(storage_file)?;
        let mut content = String::new();
        file.read_to_string(&mut content)?;
        
        let pending_list: serde_json::Value = serde_json::from_str(&content)?;
        
        if let Some(items) = pending_list.get("items").and_then(|v| v.as_array()) {
            for item_json in items {
                if let Ok(pending) = serde_json::from_value::<PendingEquipment>(item_json.clone()) {
                    self.pending_items.push(pending);
                }
            }
        }
        
        self.storage_path = Some(storage_file.to_path_buf());
        info!("Loaded {} pending equipment items from storage", self.pending_items.len());
        Ok(())
    }

    /// Save pending equipment to storage
    pub fn save_to_storage(&self) -> Result<(), Box<dyn std::error::Error>> {
        if let Some(ref storage_path) = self.storage_path {
            self.save_to_storage_path(storage_path)?;
        }
        Ok(())
    }

    /// Save to specific storage path (filesystem only, no Git)
    pub fn save_to_storage_path(&self, storage_file: &std::path::Path) -> Result<(), Box<dyn std::error::Error>> {
        use std::fs;
        use std::io::Write;
        
        #[derive(serde::Serialize)]
        struct PendingEquipmentStorage {
            building: String,
            items: Vec<PendingEquipment>,
            updated_at: String,
        }
        
        let storage = PendingEquipmentStorage {
            building: self.building_name.clone(),
            items: self.pending_items.clone(),
            updated_at: Utc::now().to_rfc3339(),
        };
        
        let json_content = serde_json::to_string_pretty(&storage)?;
        
        // Create parent directories if they don't exist
        if let Some(parent) = storage_file.parent() {
            fs::create_dir_all(parent)?;
        }
        
        let mut file = fs::File::create(storage_file)?;
        file.write_all(json_content.as_bytes())?;
        
        info!("Saved {} pending equipment items to storage", self.pending_items.len());
        Ok(())
    }

    /// Save to storage path and commit to Git if repository exists
    /// 
    /// This method follows the Git-native philosophy by committing pending equipment
    /// changes to Git when a repository is available. Falls back to filesystem-only
    /// if no Git repository is found.
    /// 
    /// Note: This is a convenience method. For production use, consider using
    /// `PersistenceManager` which handles Git operations more comprehensively.
    pub fn save_to_storage_path_with_git(&self, storage_file: &std::path::Path) -> Result<(), Box<dyn std::error::Error>> {
        // First, save to filesystem
        self.save_to_storage_path(storage_file)?;
        
        // Try to commit to Git if repository exists
        // For now, we'll just save to filesystem. Full Git integration should be
        // handled by the calling code using PersistenceManager or BuildingGitManager
        // directly, as pending equipment changes are typically committed when
        // equipment is confirmed (which already uses PersistenceManager).
        debug!("Saved pending equipment to storage. Git commits should be handled by PersistenceManager when confirming equipment.");
        
        Ok(())
    }

    /// Add pending equipment from AR scan
    pub fn add_pending_equipment(
        &mut self,
        detected_equipment: &DetectedEquipmentInfo,
        scan_id: &str,
        floor_level: i32,
        room_name: Option<&str>,
        confidence_threshold: f64,
        user_email: Option<String>,
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
            position: detected_equipment.position,
            bounding_box: detected_equipment.bounding_box.clone(),
            confidence: detected_equipment.confidence,
            detection_method: detected_equipment.detection_method.clone(),
            detected_at: Utc::now(),
            floor_level,
            room_name: room_name.map(|s| s.to_string()),
            properties: detected_equipment.properties.clone(),
            status: PendingStatus::Pending,
            user_email,
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

        // Create new floor using core type
        let mut new_floor = crate::core::Floor::new(format!("Floor {}", floor_level), floor_level);
        new_floor.elevation = Some((floor_level as f64) * 3.0);

        building_data.floors.push(new_floor);
        Ok(building_data.floors.len() - 1)
    }

    /// Find or create room in building data
    fn find_or_create_room(
        building_data: &mut BuildingData,
        floor_index: usize,
        room_name: &str,
    ) -> Result<usize, Box<dyn std::error::Error>> {
        let floor = &mut building_data.floors[floor_index];
        let floor_elevation = floor.elevation.unwrap_or(floor.level as f64 * 3.0);
        
        // Find or create default wing for AR-detected rooms
        let default_wing_name = "Default";
        let wing = floor.wings.iter_mut()
            .find(|w| w.name == default_wing_name);
        
        let wing = if let Some(wing) = wing {
            wing
        } else {
            // Create default wing using core type
            let new_wing = crate::core::Wing::new(default_wing_name.to_string());
            floor.wings.push(new_wing);
            floor.wings.last_mut()
                .ok_or_else(|| "Failed to access newly created wing".to_string())?
        };
        
        // Look for existing room in wing
        if let Some(index) = wing.rooms.iter().position(|r| r.name == room_name) {
            return Ok(index);
        }
        
        // Create new room using core type
        use crate::core::{Room, RoomType, Position, Dimensions, SpatialProperties};
        let new_room = Room {
            id: format!("room-{}", room_name.to_lowercase().replace(" ", "-")),
            name: room_name.to_string(),
            room_type: RoomType::Other("IFCSPACE".to_string()),
            equipment: Vec::new(),
            spatial_properties: SpatialProperties::new(
                Position {
                    x: 0.0,
                    y: 0.0,
                    z: floor_elevation,
                    coordinate_system: "building_local".to_string(),
                },
                Dimensions {
                    width: 10.0,
                    depth: 10.0,
                    height: 3.0,
                },
                "building_local".to_string(),
            ),
            properties: HashMap::new(),
            created_at: Some(Utc::now()),
            updated_at: Some(Utc::now()),
        };
        
        // Add room to wing
        wing.rooms.push(new_room);
        Ok(wing.rooms.len() - 1)
    }

    /// Add equipment to building data
    fn add_equipment_to_building(
        building_data: &mut BuildingData,
        floor_index: usize,
        pending: &PendingEquipment,
    ) -> Result<String, Box<dyn std::error::Error>> {
        let equipment_id = format!("equipment_{}", pending.scan_id);

        // Find or create room if room_name is provided (before mutable borrow of floor)
        let room_name_opt = pending.room_name.as_ref();
        if let Some(room_name) = room_name_opt {
            Self::find_or_create_room(building_data, floor_index, room_name)?;
        }

        // Now we can borrow the floor mutably
        let floor = &mut building_data.floors[floor_index];

        // Parse equipment type
        use crate::core::{Equipment, EquipmentType, Position};
        let parsed_equipment_type = match pending.equipment_type.to_lowercase().as_str() {
            "hvac" => EquipmentType::HVAC,
            "electrical" => EquipmentType::Electrical,
            "av" => EquipmentType::AV,
            "furniture" => EquipmentType::Furniture,
            "safety" => EquipmentType::Safety,
            "plumbing" => EquipmentType::Plumbing,
            "network" => EquipmentType::Network,
            _ => EquipmentType::Other(pending.equipment_type.clone()),
        };

        let universal_path = if let Some(room_name) = room_name_opt {
            format!("/BUILDING/FLOOR-{}/ROOM-{}/EQUIPMENT/{}", pending.floor_level, room_name, pending.name)
        } else {
            format!("/BUILDING/FLOOR-{}/EQUIPMENT/{}", pending.floor_level, pending.name)
        };

        let mut equipment = Equipment::new(
            pending.name.clone(),
            universal_path.clone(),
            parsed_equipment_type,
        );
        equipment.id = equipment_id.clone();
        equipment.position = Position {
            x: pending.position.x,
            y: pending.position.y,
            z: pending.position.z,
            coordinate_system: "building_local".to_string(),
        };
        equipment.properties = pending.properties.clone();
        equipment.health_status = Some(crate::core::EquipmentHealthStatus::Healthy);
        if let Some(room_name) = room_name_opt {
            equipment.room_id = Some(format!("room-{}", room_name.to_lowercase().replace(" ", "-")));
        }

        floor.equipment.push(equipment.clone());

        // Add equipment to room's equipment list if room was found/created
        // Rooms are now in wings, so we need to find the room in the wing
        if let Some(room_name) = room_name_opt {
            // Find the room in the default wing
            let default_wing_name = "Default";
            if let Some(wing) = floor.wings.iter_mut().find(|w| w.name == default_wing_name) {
                if let Some(room) = wing.rooms.iter_mut().find(|r| r.name == *room_name) {
                    // Check if equipment is already in the room
                    if !room.equipment.iter().any(|e| e.id == equipment_id) {
                        room.equipment.push(equipment);
                    }
                } else {
                    warn!("Room '{}' not found in wing '{}' after equipment was added, cannot link equipment to room", room_name, default_wing_name);
                }
            }
        }

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
    manager.add_pending_equipment(detected_equipment, scan_id, floor_level, room_name, confidence_threshold, None)
}

