//! AR/LiDAR Data Integration for ArxOS
//!
//! This module handles the integration of AR and LiDAR scan data from mobile applications
//! into the building data structure, enabling real-time updates to the 3D renderer.
//!
//! # Overview
//!
//! The AR integration module provides a complete workflow for processing AR scans from mobile
//! devices and integrating them into building data:
//!
//! 1. **AR Scan Processing**: Parse AR scan data from mobile apps (ARKit/ARCore)
//! 2. **Pending Equipment**: Create pending equipment items for review
//! 3. **Validation**: Validate detected equipment positions and properties
//! 4. **Integration**: Confirm pending items and add them to building data
//! 5. **Persistence**: Store pending equipment state for review
//!
//! # Usage Examples
//!
//! ## Basic AR Integration Workflow
//!
//! ```rust,ignore
//! use arxos::ar_integration::{ARScanData, DetectedEquipment};
//! use arxos::spatial::Point3D;
//! use std::collections::HashMap;
//! use chrono::Utc;
//!
//! // Create AR scan data from mobile app
//! let ar_scan = ARScanData {
//!     scan_id: "scan_001".to_string(),
//!     room_name: "Conference Room A".to_string(),
//!     floor_level: 3,
//!     timestamp: Utc::now(),
//!     coordinate_system: "ARWorld".to_string(),
//!     detected_equipment: vec![
//!         DetectedEquipment {
//!             id: "HVAC-301".to_string(),
//!             name: "VAV Unit".to_string(),
//!             equipment_type: "VAV".to_string(),
//!             position: Point3D { x: 10.0, y: 20.0, z: 3.0 },
//!             bounding_box: Point3D { x: 0.0, y: 0.0, z: 0.0 }.into(),
//!             confidence: 0.95,
//!             detection_method: arxos::ar_integration::DetectionMethod::ARKit,
//!             properties: HashMap::new(),
//!         }
//!     ],
//!     room_boundaries: None,
//!     scan_metadata: arxos::ar_integration::ScanMetadata {
//!         device_type: "iPhone".to_string(),
//!         app_version: "1.0".to_string(),
//!         scan_duration_ms: 5000,
//!         point_count: 1000,
//!         accuracy_estimate: 0.95,
//!         lighting_conditions: "good".to_string(),
//!     },
//! };
//!
//! println!("Scan ID: {}", ar_scan.scan_id);
//! ```
//!
//! ## Pending Equipment Workflow
//!
//! ```rust,ignore
//! use arxos::ar_integration::pending::PendingEquipmentManager;
//! use arxos::ar_integration::processing::process_ar_scan_to_pending;
//! use arxos::ar_integration::processing::ARScanData as ProcessingARScanData;
//! use arxos::spatial::Point3D;
//!
//! // Process AR scan to pending items
//! let scan_data = ProcessingARScanData {
//!     detected_equipment: vec![],
//! };
//! let pending_ids = process_ar_scan_to_pending(&scan_data, "my_building", 0.7)?;
//!
//! // Create manager
//! let manager = PendingEquipmentManager::new("my_building".to_string());
//!
//! // List pending items  
//! let pending = manager.list_pending();
//! for item in pending {
//!     println!("Pending: {} ({:.2} confidence)", item.name, item.confidence);
//! }
//! ```

pub mod json_helpers;
pub mod pending;
pub mod processing;

use crate::core::{
    BoundingBox, Dimensions, Equipment, EquipmentStatus, EquipmentType, Position, RoomType,
    SpatialProperties,
};
use crate::spatial::{BoundingBox3D, Point3D};
use crate::yaml::BuildingData;
use chrono::{DateTime, Utc};
use log::{info, warn};
use serde::{Deserialize, Serialize};
use std::collections::HashMap;

pub use pending::{
    DetectedEquipmentInfo, PendingEquipment, PendingEquipmentManager, PendingStatus,
};
pub use processing::{
    pending_equipment_from_json, pending_equipment_to_json, process_ar_scan_and_save_pending,
    process_ar_scan_to_pending, validate_ar_scan_data,
};

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
    pub fn integrate_ar_scan(
        &mut self,
        scan_data: ARScanData,
    ) -> Result<IntegrationResult, Box<dyn std::error::Error>> {
        info!(
            "Integrating AR scan: {} for room: {}",
            scan_data.scan_id, scan_data.room_name
        );

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
                    warn!(
                        "Failed to integrate equipment {}: {}",
                        detected_equipment.name, e
                    );
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
    fn find_or_create_floor(
        &mut self,
        floor_level: i32,
    ) -> Result<usize, Box<dyn std::error::Error>> {
        // Look for existing floor
        if let Some(index) = self
            .building_data
            .floors
            .iter()
            .position(|f| f.level == floor_level)
        {
            return Ok(index);
        }

        // Create new floor using core type
        use crate::core::Floor;
        let mut new_floor = Floor::new(format!("Floor {}", floor_level), floor_level);
        new_floor.elevation = Some((floor_level as f64) * 3.0); // Assume 3m per floor

        self.building_data.floors.push(new_floor);
        Ok(self.building_data.floors.len() - 1)
    }

    /// Find or create room
    fn find_or_create_room(
        &mut self,
        floor_index: usize,
        room_name: &str,
    ) -> Result<usize, Box<dyn std::error::Error>> {
        let floor = &mut self.building_data.floors[floor_index];

        // Collect all rooms from wings
        let all_rooms: Vec<&Room> = floor
            .wings
            .iter()
            .flat_map(|wing| wing.rooms.iter())
            .collect();

        // Look for existing room
        if let Some(index) = all_rooms.iter().position(|r| r.name == room_name) {
            // Find which wing contains this room
            let mut room_idx = 0;
            for wing in &floor.wings {
                if index < room_idx + wing.rooms.len() {
                    return Ok(room_idx + index);
                }
                room_idx += wing.rooms.len();
            }
        }

        // Create new room using core type
        use crate::core::Room;
        let elevation = floor.elevation.unwrap_or(floor.level as f64 * 3.0);
        let new_room = Room {
            id: format!("room-{}", room_name.to_lowercase().replace(" ", "-")),
            name: room_name.to_string(),
            room_type: RoomType::Other("IFCSPACE".to_string()),
            equipment: Vec::new(),
            spatial_properties: SpatialProperties {
                position: Position {
                    x: 0.0,
                    y: 0.0,
                    z: elevation,
                    coordinate_system: "building_local".to_string(),
                },
                dimensions: Dimensions {
                    width: 10.0,
                    depth: 10.0,
                    height: 3.0,
                },
                bounding_box: BoundingBox {
                    min: Position {
                        x: 0.0,
                        y: 0.0,
                        z: elevation,
                        coordinate_system: "building_local".to_string(),
                    },
                    max: Position {
                        x: 10.0,
                        y: 10.0,
                        z: elevation + 3.0,
                        coordinate_system: "building_local".to_string(),
                    },
                },
                coordinate_system: "building_local".to_string(),
            },
            properties: HashMap::new(),
            created_at: Some(Utc::now()),
            updated_at: Some(Utc::now()),
        };

        // Add to default wing
        use crate::core::Wing;
        if floor.wings.is_empty() {
            floor.wings.push(Wing::new("Default".to_string()));
        }
        floor.wings[0].rooms.push(new_room);
        Ok(floor.wings[0].rooms.len() - 1)
    }

    /// Integrate equipment into building data
    fn integrate_equipment(
        &mut self,
        floor_index: usize,
        room_index: usize,
        detected_equipment: DetectedEquipment,
    ) -> Result<IntegrationAction, Box<dyn std::error::Error>> {
        // Prepare detected position before any borrows
        let detected_pos = Position {
            x: detected_equipment.position.x,
            y: detected_equipment.position.y,
            z: detected_equipment.position.z,
            coordinate_system: "building_local".to_string(),
        };

        // Check if equipment already exists and get its position before mutable borrow
        let existing_position_opt = self.building_data.floors[floor_index]
            .equipment
            .iter()
            .find(|e| e.name == detected_equipment.name)
            .map(|e| e.position.clone());

        // Calculate position difference before mutable borrow if equipment exists
        let position_diff_opt = existing_position_opt.as_ref().map(|existing_pos| {
            self.calculate_position_difference_core(existing_pos, &detected_pos)
        });

        let floor = &mut self.building_data.floors[floor_index];

        // Check if equipment already exists
        if let Some(existing_index) = floor
            .equipment
            .iter()
            .position(|e| e.name == detected_equipment.name)
        {
            // Get position difference we calculated before the mutable borrow
            let position_diff =
                position_diff_opt.expect("Position diff should exist if equipment found");

            // Update existing equipment
            let existing_equipment = &mut floor.equipment[existing_index];

            if position_diff > 1.0 {
                // More than 1 meter difference
                warn!(
                    "Position conflict for equipment {}: existing={:?}, detected={:?}",
                    detected_equipment.name, existing_equipment.position, detected_pos
                );

                // Use AR data if confidence is high
                if detected_equipment.confidence > 0.8 {
                    existing_equipment.position = detected_pos;
                    existing_equipment
                        .properties
                        .insert("last_ar_update".to_string(), Utc::now().to_rfc3339());
                    return Ok(IntegrationAction::ConflictResolved);
                }
            } else {
                // Update with AR data
                existing_equipment.position = detected_pos;
                existing_equipment
                    .properties
                    .insert("last_ar_update".to_string(), Utc::now().to_rfc3339());
                return Ok(IntegrationAction::Updated);
            }
        } else {
            // Add new equipment
            let equipment_name = detected_equipment.name.clone();
            let equipment_id = detected_equipment.id.clone();
            let equipment_type_str = detected_equipment.equipment_type.clone();

            let equipment_type_enum = match equipment_type_str.as_str() {
                "HVAC" => EquipmentType::HVAC,
                "ELECTRICAL" => EquipmentType::Electrical,
                "PLUMBING" => EquipmentType::Plumbing,
                "SAFETY" => EquipmentType::Safety,
                "NETWORK" => EquipmentType::Network,
                "AV" => EquipmentType::AV,
                "FURNITURE" => EquipmentType::Furniture,
                _ => EquipmentType::Other(equipment_type_str.clone()),
            };

            let new_equipment = Equipment {
                id: equipment_id.clone(),
                name: equipment_name.clone(),
                path: format!(
                    "/BUILDING/FLOOR-{}/ROOM-{}/EQUIPMENT/{}",
                    floor.level, room_index, equipment_name
                ),
                address: None,
                equipment_type: equipment_type_enum,
                position: Position {
                    x: detected_equipment.position.x,
                    y: detected_equipment.position.y,
                    z: detected_equipment.position.z,
                    coordinate_system: "building_local".to_string(),
                },
                properties: detected_equipment.properties,
                status: EquipmentStatus::Active,
                health_status: None,
                room_id: None,
                sensor_mappings: None,
            };

            floor.equipment.push(new_equipment);

            // Add equipment to room (find room in wings)
            let mut room_idx = 0;
            for wing in &mut floor.wings {
                if room_index < room_idx + wing.rooms.len() {
                    let actual_room_idx = room_index - room_idx;
                    wing.rooms[actual_room_idx]
                        .equipment
                        .push(floor.equipment.last().unwrap().clone());
                    break;
                }
                room_idx += wing.rooms.len();
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
        // Find room by iterating through wings (room_index is a flat index across all wings)
        let floor = &mut self.building_data.floors[floor_index];
        let mut current_index = 0;
        let mut room = None;

        for wing in &mut floor.wings {
            if room_index < current_index + wing.rooms.len() {
                let local_index = room_index - current_index;
                room = Some(&mut wing.rooms[local_index]);
                break;
            }
            current_index += wing.rooms.len();
        }

        let room = room.ok_or_else(|| format!("Room at index {} not found", room_index))?;

        // Update room properties with AR scan data
        room.properties.insert(
            "ar_scan_walls".to_string(),
            boundaries.walls.len().to_string(),
        );
        room.properties.insert(
            "ar_scan_openings".to_string(),
            boundaries.openings.len().to_string(),
        );
        room.properties.insert(
            "last_ar_boundary_update".to_string(),
            Utc::now().to_rfc3339(),
        );

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

            use crate::core::{BoundingBox, Position};
            let z = room.spatial_properties.position.z;
            room.spatial_properties.bounding_box = BoundingBox {
                min: Position {
                    x: min_x,
                    y: min_y,
                    z,
                    coordinate_system: room.spatial_properties.position.coordinate_system.clone(),
                },
                max: Position {
                    x: max_x,
                    y: max_y,
                    z: z + 3.0,
                    coordinate_system: room.spatial_properties.position.coordinate_system.clone(),
                },
            };
        }

        Ok(())
    }

    /// Update building metadata with scan information
    fn update_building_metadata(&mut self, scan_data: &ARScanData) {
        self.building_data.building.updated_at = Utc::now();

        // Add scan metadata to building properties
        self.building_data.metadata.tags.push("ar_scan".to_string());
        self.building_data
            .metadata
            .tags
            .push(format!("scan_{}", scan_data.scan_id));

        // Update total entities count
        self.building_data.metadata.total_entities += scan_data.detected_equipment.len();
        self.building_data.metadata.spatial_entities += scan_data.detected_equipment.len();
    }

    /// Calculate position difference between two points
    fn calculate_position_difference_core(&self, pos1: &Position, pos2: &Position) -> f64 {
        let dx = pos1.x - pos2.x;
        let dy = pos1.y - pos2.y;
        let dz = pos1.z - pos2.z;
        (dx * dx + dy * dy + dz * dz).sqrt()
    }

    #[allow(dead_code)]
    fn calculate_position_difference(&self, pos1: &Point3D, pos2: &Point3D) -> f64 {
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

    // Parse scan metadata using JSON helpers
    use crate::ar_integration::json_helpers;
    let scan_metadata = ScanMetadata {
        device_type: json_helpers::parse_optional_string(&ar_json, "deviceType", "unknown"),
        app_version: json_helpers::parse_optional_string(&ar_json, "appVersion", "1.0.0"),
        scan_duration_ms: ar_json
            .get("scanDurationMs")
            .and_then(|v| v.as_u64())
            .unwrap_or(0),
        point_count: ar_json
            .get("pointCount")
            .and_then(|v| v.as_u64())
            .unwrap_or(0) as usize,
        accuracy_estimate: json_helpers::parse_optional_f64(&ar_json, "accuracyEstimate", 0.1),
        lighting_conditions: json_helpers::parse_optional_string(
            &ar_json,
            "lightingConditions",
            "unknown",
        ),
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
    let name = equipment_json
        .get("name")
        .and_then(|v| v.as_str())
        .ok_or("Missing equipment name")?;

    use crate::ar_integration::json_helpers;
    let equipment_type = json_helpers::parse_optional_string(equipment_json, "type", "Unknown");

    let position = if let Some(pos) = equipment_json.get("position") {
        json_helpers::parse_position(pos)
    } else {
        return Ok(None); // Skip equipment without position
    };

    let confidence = json_helpers::parse_optional_f64(equipment_json, "confidence", 0.5);
    let detection_method = json_helpers::parse_detection_method(equipment_json);

    // Create bounding box using helper
    let bounding_box = json_helpers::parse_bounding_box(&position, 0.5);

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
    use crate::ar_integration::json_helpers;
    let mut walls = Vec::new();
    let mut openings = Vec::new();

    // Parse walls
    if let Some(walls_array) = boundaries_json.get("walls").and_then(|w| w.as_array()) {
        for wall_json in walls_array {
            if let (Some(start), Some(end)) =
                (wall_json.get("startPoint"), wall_json.get("endPoint"))
            {
                let wall = Wall {
                    start_point: json_helpers::parse_position(start),
                    end_point: json_helpers::parse_position(end),
                    height: json_helpers::parse_optional_f64(wall_json, "height", 3.0),
                    thickness: json_helpers::parse_optional_f64(wall_json, "thickness", 0.2),
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
                    position: json_helpers::parse_position(pos),
                    width: json_helpers::parse_optional_f64(opening_json, "width", 1.0),
                    height: json_helpers::parse_optional_f64(opening_json, "height", 2.0),
                    opening_type: json_helpers::parse_optional_string(opening_json, "type", "door"),
                };
                openings.push(opening);
            }
        }
    }

    Ok(RoomBoundaries {
        walls,
        floor_plane: None,   // Floor plane will be parsed when AR data is available
        ceiling_plane: None, // Ceiling plane will be parsed when AR data is available
        openings,
    })
}
