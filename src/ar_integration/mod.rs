//! AR/LiDAR Data Integration for ArxOS
//!
//! This module handles the integration of AR and LiDAR scan data from mobile applications
//! into the building data structure, enabling real-time updates to the 3D renderer.

use crate::yaml::{BuildingData, FloorData, RoomData, EquipmentData, EquipmentStatus};
use crate::spatial::{Point3D, BoundingBox3D};
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use chrono::{DateTime, Utc};
use log::{info, warn};

/// AR scan data structure from mobile applications
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ARScanData {
    pub scan_id: String,
    pub room_name: String,
    pub floor_level: i32,
    pub timestamp: DateTime<Utc>,
    pub coordinate_system: String,
    pub detected_equipment: Vec<DetectedEquipment>,
    pub room_boundaries: Option<RoomBoundaries>,
    pub scan_metadata: ScanMetadata,
}

/// Equipment detected by AR scan
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DetectedEquipment {
    pub id: String,
    pub name: String,
    pub equipment_type: String,
    pub position: Point3D,
    pub bounding_box: BoundingBox3D,
    pub confidence: f64,
    pub detection_method: DetectionMethod,
    pub properties: HashMap<String, String>,
}

/// Detection method used
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum DetectionMethod {
    ARKit,
    ARCore,
    LiDAR,
    Manual,
    AI,
}

/// Room boundaries from AR scan
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RoomBoundaries {
    pub walls: Vec<Wall>,
    pub floor_plane: Option<Plane>,
    pub ceiling_plane: Option<Plane>,
    pub openings: Vec<Opening>,
}

/// Wall structure
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Wall {
    pub start_point: Point3D,
    pub end_point: Point3D,
    pub height: f64,
    pub thickness: f64,
}

/// Plane structure
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Plane {
    pub normal: Point3D,
    pub distance: f64,
    pub bounds: BoundingBox3D,
}

/// Opening in wall (door, window)
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Opening {
    pub position: Point3D,
    pub width: f64,
    pub height: f64,
    pub opening_type: String,
}

/// Scan metadata
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ScanMetadata {
    pub device_type: String,
    pub app_version: String,
    pub scan_duration_ms: u64,
    pub point_count: usize,
    pub accuracy_estimate: f64,
    pub lighting_conditions: String,
}

/// AR data integrator
pub struct ARDataIntegrator {
    building_data: BuildingData,
}

/// Integration result
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct IntegrationResult {
    pub scan_id: String,
    pub equipment_added: usize,
    pub equipment_updated: usize,
    pub rooms_updated: usize,
    pub conflicts_resolved: usize,
    pub integration_timestamp: DateTime<Utc>,
}

impl ARDataIntegrator {
    /// Create a new AR data integrator
    pub fn new(building_data: BuildingData) -> Self {
        Self { building_data }
    }

    /// Integrate AR scan data into building data
    pub fn integrate_ar_scan(&mut self, scan_data: ARScanData) -> Result<IntegrationResult, Box<dyn std::error::Error>> {
        info!("Integrating AR scan: {} for room: {}", scan_data.scan_id, scan_data.room_name);
        
        let mut equipment_added = 0;
        let mut equipment_updated = 0;
        let mut rooms_updated = 0;
        let mut conflicts_resolved = 0;
        
        // Find or create the floor
        let floor_index = self.find_or_create_floor(scan_data.floor_level)?;
        
        // Find or create the room
        let room_index = self.find_or_create_room(floor_index, &scan_data.room_name)?;
        
        // Integrate detected equipment
        for detected_equipment in &scan_data.detected_equipment {
            match self.integrate_equipment(floor_index, room_index, detected_equipment.clone()) {
                Ok(IntegrationAction::Added) => equipment_added += 1,
                Ok(IntegrationAction::Updated) => equipment_updated += 1,
                Ok(IntegrationAction::ConflictResolved) => conflicts_resolved += 1,
                Err(e) => {
                    warn!("Failed to integrate equipment {}: {}", detected_equipment.name, e);
                }
            }
        }
        
        // Update room boundaries if provided
        if let Some(ref boundaries) = scan_data.room_boundaries {
            self.update_room_boundaries(floor_index, room_index, boundaries.clone())?;
            rooms_updated += 1;
        }
        
        // Update building metadata
        self.update_building_metadata(&scan_data);
        
        let result = IntegrationResult {
            scan_id: scan_data.scan_id,
            equipment_added,
            equipment_updated,
            rooms_updated,
            conflicts_resolved,
            integration_timestamp: Utc::now(),
        };
        
        info!("AR scan integration completed: {:?}", result);
        Ok(result)
    }

    /// Find or create floor
    fn find_or_create_floor(&mut self, floor_level: i32) -> Result<usize, Box<dyn std::error::Error>> {
        // Look for existing floor
        if let Some(index) = self.building_data.floors.iter().position(|f| f.level == floor_level) {
            return Ok(index);
        }
        
        // Create new floor
        let new_floor = FloorData {
            id: format!("floor-{}", floor_level),
            name: format!("Floor {}", floor_level),
            level: floor_level,
            elevation: (floor_level as f64) * 3.0, // Assume 3m per floor
            rooms: Vec::new(),
            equipment: Vec::new(),
            bounding_box: None,
        };
        
        self.building_data.floors.push(new_floor);
        Ok(self.building_data.floors.len() - 1)
    }

    /// Find or create room
    fn find_or_create_room(&mut self, floor_index: usize, room_name: &str) -> Result<usize, Box<dyn std::error::Error>> {
        let floor = &mut self.building_data.floors[floor_index];
        
        // Look for existing room
        if let Some(index) = floor.rooms.iter().position(|r| r.name == room_name) {
            return Ok(index);
        }
        
        // Create new room
        let new_room = RoomData {
            id: format!("room-{}", room_name.to_lowercase().replace(" ", "-")),
            name: room_name.to_string(),
            room_type: "IFCSPACE".to_string(),
            area: None,
            volume: None,
            position: Point3D { x: 0.0, y: 0.0, z: floor.elevation },
            bounding_box: BoundingBox3D {
                min: Point3D { x: 0.0, y: 0.0, z: floor.elevation },
                max: Point3D { x: 10.0, y: 10.0, z: floor.elevation + 3.0 },
            },
            equipment: Vec::new(),
            properties: HashMap::new(),
        };
        
        floor.rooms.push(new_room);
        Ok(floor.rooms.len() - 1)
    }

    /// Integrate equipment into building data
    fn integrate_equipment(
        &mut self,
        floor_index: usize,
        room_index: usize,
        detected_equipment: DetectedEquipment,
    ) -> Result<IntegrationAction, Box<dyn std::error::Error>> {
        let floor = &mut self.building_data.floors[floor_index];
        
        // Check if equipment already exists
        if let Some(existing_index) = floor.equipment.iter().position(|e| e.name == detected_equipment.name) {
            // Get existing position before mutable borrow
            let existing_position = floor.equipment[existing_index].position.clone();
            
            // Calculate position difference before mutable borrow
            let position_diff = Self::calculate_position_difference(&existing_position, &detected_equipment.position);
            
            // Update existing equipment
            let existing_equipment = &mut floor.equipment[existing_index];
            
            if position_diff > 1.0 { // More than 1 meter difference
                warn!("Position conflict for equipment {}: existing={:?}, detected={:?}", 
                    detected_equipment.name, existing_equipment.position, detected_equipment.position);
                
                // Use AR data if confidence is high
                if detected_equipment.confidence > 0.8 {
                    existing_equipment.position = detected_equipment.position;
                    existing_equipment.bounding_box = detected_equipment.bounding_box;
                    existing_equipment.properties.insert("last_ar_update".to_string(), Utc::now().to_rfc3339());
                    return Ok(IntegrationAction::ConflictResolved);
                }
            } else {
                // Update with AR data
                existing_equipment.position = detected_equipment.position;
                existing_equipment.bounding_box = detected_equipment.bounding_box;
                existing_equipment.properties.insert("last_ar_update".to_string(), Utc::now().to_rfc3339());
                return Ok(IntegrationAction::Updated);
            }
        } else {
            // Add new equipment
            let equipment_name = detected_equipment.name.clone();
            let equipment_id = detected_equipment.id.clone();
            let equipment_type = detected_equipment.equipment_type.clone();
            
            let new_equipment = EquipmentData {
                id: equipment_id.clone(),
                name: equipment_name.clone(),
                equipment_type: equipment_type.clone(),
                system_type: equipment_type,
                universal_path: format!("/BUILDING/FLOOR-{}/ROOM-{}/EQUIPMENT/{}", 
                    floor.level, room_index, equipment_name),
                position: detected_equipment.position,
                bounding_box: detected_equipment.bounding_box,
                status: EquipmentStatus::Healthy,
                properties: detected_equipment.properties,
            };
            
            floor.equipment.push(new_equipment);
            
            // Add equipment ID to room
            if let Some(room) = floor.rooms.get_mut(room_index) {
                room.equipment.push(equipment_id);
            }
            
            return Ok(IntegrationAction::Added);
        }
        
        Ok(IntegrationAction::Updated)
    }

    /// Update room boundaries from AR scan
    fn update_room_boundaries(
        &mut self,
        floor_index: usize,
        room_index: usize,
        boundaries: RoomBoundaries,
    ) -> Result<(), Box<dyn std::error::Error>> {
        let room = &mut self.building_data.floors[floor_index].rooms[room_index];
        
        // Update room properties with AR scan data
        room.properties.insert("ar_scan_walls".to_string(), boundaries.walls.len().to_string());
        room.properties.insert("ar_scan_openings".to_string(), boundaries.openings.len().to_string());
        room.properties.insert("last_ar_boundary_update".to_string(), Utc::now().to_rfc3339());
        
        // Update bounding box based on walls if available
        if !boundaries.walls.is_empty() {
            let mut min_x = f64::INFINITY;
            let mut min_y = f64::INFINITY;
            let mut max_x = f64::NEG_INFINITY;
            let mut max_y = f64::NEG_INFINITY;
            
            for wall in &boundaries.walls {
                min_x = min_x.min(wall.start_point.x).min(wall.end_point.x);
                min_y = min_y.min(wall.start_point.y).min(wall.end_point.y);
                max_x = max_x.max(wall.start_point.x).max(wall.end_point.x);
                max_y = max_y.max(wall.start_point.y).max(wall.end_point.y);
            }
            
            room.bounding_box = BoundingBox3D {
                min: Point3D { x: min_x, y: min_y, z: room.position.z },
                max: Point3D { x: max_x, y: max_y, z: room.position.z + 3.0 },
            };
        }
        
        Ok(())
    }

    /// Update building metadata with scan information
    fn update_building_metadata(&mut self, scan_data: &ARScanData) {
        self.building_data.building.updated_at = Utc::now();
        
        // Add scan metadata to building properties
        self.building_data.metadata.tags.push("ar_scan".to_string());
        self.building_data.metadata.tags.push(format!("scan_{}", scan_data.scan_id));
        
        // Update total entities count
        self.building_data.metadata.total_entities += scan_data.detected_equipment.len();
        self.building_data.metadata.spatial_entities += scan_data.detected_equipment.len();
    }

    /// Calculate position difference between two points
    fn calculate_position_difference(pos1: &Point3D, pos2: &Point3D) -> f64 {
        let dx = pos1.x - pos2.x;
        let dy = pos1.y - pos2.y;
        let dz = pos1.z - pos2.z;
        (dx * dx + dy * dy + dz * dz).sqrt()
    }

    /// Get the updated building data
    pub fn get_building_data(self) -> BuildingData {
        self.building_data
    }
}

/// Integration action result
#[derive(Debug, Clone)]
enum IntegrationAction {
    Added,
    Updated,
    ConflictResolved,
}

/// Convert mobile AR data to ARScanData
pub fn convert_mobile_ar_data(
    mobile_data: Vec<u8>,
    room_name: String,
    floor_level: i32,
) -> Result<ARScanData, Box<dyn std::error::Error>> {
    // Parse mobile AR data (JSON format from mobile apps)
    let ar_json = serde_json::from_slice::<serde_json::Value>(&mobile_data)?;
    
    let mut detected_equipment = Vec::new();
    
    // Parse detected equipment from mobile data
    if let Some(equipment_array) = ar_json.get("detectedEquipment").and_then(|e| e.as_array()) {
        for (i, equipment) in equipment_array.iter().enumerate() {
            if let Some(equipment_data) = parse_equipment_from_mobile(equipment, i)? {
                detected_equipment.push(equipment_data);
            }
        }
    }
    
    // Parse room boundaries if available
    let room_boundaries = if let Some(boundaries) = ar_json.get("roomBoundaries") {
        Some(parse_room_boundaries_from_mobile(boundaries)?)
    } else {
        None
    };
    
    // Parse scan metadata
    let scan_metadata = ScanMetadata {
        device_type: ar_json.get("deviceType")
            .and_then(|v| v.as_str())
            .unwrap_or("unknown")
            .to_string(),
        app_version: ar_json.get("appVersion")
            .and_then(|v| v.as_str())
            .unwrap_or("1.0.0")
            .to_string(),
        scan_duration_ms: ar_json.get("scanDurationMs")
            .and_then(|v| v.as_u64())
            .unwrap_or(0),
        point_count: ar_json.get("pointCount")
            .and_then(|v| v.as_u64())
            .unwrap_or(0) as usize,
        accuracy_estimate: ar_json.get("accuracyEstimate")
            .and_then(|v| v.as_f64())
            .unwrap_or(0.1),
        lighting_conditions: ar_json.get("lightingConditions")
            .and_then(|v| v.as_str())
            .unwrap_or("unknown")
            .to_string(),
    };
    
    Ok(ARScanData {
        scan_id: format!("scan_{}", Utc::now().timestamp()),
        room_name,
        floor_level,
        timestamp: Utc::now(),
        coordinate_system: "ARWorld".to_string(),
        detected_equipment,
        room_boundaries,
        scan_metadata,
    })
}

/// Parse equipment data from mobile AR data
fn parse_equipment_from_mobile(
    equipment_json: &serde_json::Value,
    index: usize,
) -> Result<Option<DetectedEquipment>, Box<dyn std::error::Error>> {
    let name = equipment_json.get("name")
        .and_then(|v| v.as_str())
        .ok_or("Missing equipment name")?;
    
    let equipment_type = equipment_json.get("type")
        .and_then(|v| v.as_str())
        .unwrap_or("Unknown");
    
    let position = if let Some(pos) = equipment_json.get("position") {
        Point3D {
            x: pos.get("x").and_then(|v| v.as_f64()).unwrap_or(0.0),
            y: pos.get("y").and_then(|v| v.as_f64()).unwrap_or(0.0),
            z: pos.get("z").and_then(|v| v.as_f64()).unwrap_or(0.0),
        }
    } else {
        return Ok(None); // Skip equipment without position
    };
    
    let confidence = equipment_json.get("confidence")
        .and_then(|v| v.as_f64())
        .unwrap_or(0.5);
    
    let detection_method = match equipment_json.get("detectionMethod")
        .and_then(|v| v.as_str())
        .unwrap_or("unknown") {
        "ARKit" => DetectionMethod::ARKit,
        "ARCore" => DetectionMethod::ARCore,
        "LiDAR" => DetectionMethod::LiDAR,
        "Manual" => DetectionMethod::Manual,
        "AI" => DetectionMethod::AI,
        _ => DetectionMethod::Manual,
    };
    
    // Create bounding box (simplified)
    let bounding_box = BoundingBox3D {
        min: Point3D {
            x: position.x - 0.5,
            y: position.y - 0.5,
            z: position.z - 0.5,
        },
        max: Point3D {
            x: position.x + 0.5,
            y: position.y + 0.5,
            z: position.z + 0.5,
        },
    };
    
    Ok(Some(DetectedEquipment {
        id: format!("ar_equipment_{}", index),
        name: name.to_string(),
        equipment_type: equipment_type.to_string(),
        position,
        bounding_box,
        confidence,
        detection_method,
        properties: HashMap::new(),
    }))
}

/// Parse room boundaries from mobile AR data
fn parse_room_boundaries_from_mobile(
    boundaries_json: &serde_json::Value,
) -> Result<RoomBoundaries, Box<dyn std::error::Error>> {
    let mut walls = Vec::new();
    let mut openings = Vec::new();
    
    // Parse walls
    if let Some(walls_array) = boundaries_json.get("walls").and_then(|w| w.as_array()) {
        for wall_json in walls_array {
            if let (Some(start), Some(end)) = (
                wall_json.get("startPoint"),
                wall_json.get("endPoint"),
            ) {
                let wall = Wall {
                    start_point: Point3D {
                        x: start.get("x").and_then(|v| v.as_f64()).unwrap_or(0.0),
                        y: start.get("y").and_then(|v| v.as_f64()).unwrap_or(0.0),
                        z: start.get("z").and_then(|v| v.as_f64()).unwrap_or(0.0),
                    },
                    end_point: Point3D {
                        x: end.get("x").and_then(|v| v.as_f64()).unwrap_or(0.0),
                        y: end.get("y").and_then(|v| v.as_f64()).unwrap_or(0.0),
                        z: end.get("z").and_then(|v| v.as_f64()).unwrap_or(0.0),
                    },
                    height: wall_json.get("height").and_then(|v| v.as_f64()).unwrap_or(3.0),
                    thickness: wall_json.get("thickness").and_then(|v| v.as_f64()).unwrap_or(0.2),
                };
                walls.push(wall);
            }
        }
    }
    
    // Parse openings
    if let Some(openings_array) = boundaries_json.get("openings").and_then(|o| o.as_array()) {
        for opening_json in openings_array {
            if let Some(pos) = opening_json.get("position") {
                let opening = Opening {
                    position: Point3D {
                        x: pos.get("x").and_then(|v| v.as_f64()).unwrap_or(0.0),
                        y: pos.get("y").and_then(|v| v.as_f64()).unwrap_or(0.0),
                        z: pos.get("z").and_then(|v| v.as_f64()).unwrap_or(0.0),
                    },
                    width: opening_json.get("width").and_then(|v| v.as_f64()).unwrap_or(1.0),
                    height: opening_json.get("height").and_then(|v| v.as_f64()).unwrap_or(2.0),
                    opening_type: opening_json.get("type")
                        .and_then(|v| v.as_str())
                        .unwrap_or("door")
                        .to_string(),
                };
                openings.push(opening);
            }
        }
    }
    
    Ok(RoomBoundaries {
        walls,
        floor_plane: None, // TODO: Parse floor plane
        ceiling_plane: None, // TODO: Parse ceiling plane
        openings,
    })
}
