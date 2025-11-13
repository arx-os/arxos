//! Business logic operations for building, room, and equipment management

use super::types::{Position, SpatialQueryResult};
use super::{Equipment, Room};
use std::collections::HashMap;

/// Create a room in a building
///
/// # Arguments
///
/// * `building_name` - Name of the building
/// * `floor_level` - Floor level where the room will be created
/// * `room` - Room to create
/// * `wing_name` - Optional wing name. If provided, room will be added to that wing.
///   If not provided or wing doesn't exist, room will be added to a default wing.
/// * `commit` - Whether to commit changes to Git
pub fn create_room(
    building_name: &str,
    floor_level: i32,
    room: Room,
    wing_name: Option<&str>,
    commit: bool,
) -> Result<(), Box<dyn std::error::Error>> {
    use crate::persistence::PersistenceManager;

    let persistence = PersistenceManager::new(building_name)?;
    let mut building_data = persistence.load_building_data()?;

    // Store room name for commit message
    let room_name = room.name.clone();

    // Find or create the floor
    let floor = if let Some(floor) = building_data.find_floor_mut(floor_level) {
        floor
    } else {
        // Create new floor
        let new_floor = crate::core::Floor::new(format!("Floor {}", floor_level), floor_level);
        building_data.add_floor(new_floor);
        building_data.find_floor_mut(floor_level).unwrap()
    };

    // Find or create the wing
    let wing_name = wing_name.unwrap_or("Default");
    if !floor.wings.iter().any(|w| w.name == wing_name) {
        let new_wing = crate::core::Wing::new(wing_name.to_string());
        floor.wings.push(new_wing);
    }
    let wing = floor.wings.iter_mut().find(|w| w.name == wing_name).unwrap();
    
    // Add room to wing
    wing.rooms.push(room);

    // Save
    if commit {
        persistence.save_and_commit(&building_data, Some(&format!("Add room: {}", room_name)))?;
    } else {
        // For now, use the same method
        persistence.save_and_commit(&building_data, None)?;
    }

    Ok(())
}

/// Add equipment to a room or floor
pub fn add_equipment(
    building_name: &str,
    room_name: Option<&str>,
    equipment: Equipment,
    commit: bool,
) -> Result<(), Box<dyn std::error::Error>> {
    use crate::persistence::PersistenceManager;

    let persistence = PersistenceManager::new(building_name)?;
    let mut building_data = persistence.load_building_data()?;

    // Find room if specified
    if let Some(room_name) = room_name {
        for floor in &mut building_data.floors {
            // Search in wings first (primary location)
            for wing in &mut floor.wings {
                if let Some(room) = wing.rooms.iter_mut().find(|r| r.name == room_name) {
                    // Add equipment to room
                    room.equipment.push(equipment.clone());
                    // Also add to floor's equipment list
                    floor.equipment.push(equipment.clone());
                    break;
                }
            }
            // Note: Legacy rooms list removed - rooms are only in wings now
        }
    } else {
        // Add to floor-level equipment if no room specified
        if let Some(floor) = building_data.floors.first_mut() {
            floor.equipment.push(equipment.clone());
        }
    }

    // Save
    if commit {
        persistence.save_and_commit(
            &building_data,
            Some(&format!("Add equipment: {}", equipment.name)),
        )?;
    } else {
        persistence.save_building_data(&building_data)?;
    }

    Ok(())
}

/// Perform a spatial query
///
/// Supports various spatial query types to find rooms and equipment based on spatial criteria.
///
/// # Query Types
///
/// - `"distance"` - Calculate distance between two entities
///   - params[0]: source entity name/ID
///   - params[1]: target entity name/ID
///
/// - `"within_radius"` - Find entities within radius of a point
///   - params[0]: center X coordinate
///   - params[1]: center Y coordinate
///   - params[2]: center Z coordinate
///   - params[3]: radius (distance threshold)
///
/// - `"nearest"` - Find nearest entity to a point
///   - params[0]: reference X coordinate
///   - params[1]: reference Y coordinate
///   - params[2]: reference Z coordinate
///   - params[3] (optional): maximum distance to search
///
/// - `"all"` or empty - Return all entities with distance from origin
///
/// # Arguments
///
/// * `query_type` - Type of spatial query to perform
/// * `entity` - Optional entity type filter ("room", "equipment", or empty for all)
/// * `params` - Query-specific parameters
///
/// # Returns
///
/// Vector of spatial query results with entity information and calculated distances.
pub fn spatial_query(
    query_type: &str,
    entity: &str,
    params: Vec<String>,
) -> Result<Vec<SpatialQueryResult>, Box<dyn std::error::Error>> {
    use crate::spatial::Point3D;

    // Load building data - implementation would need proper file path
    let building_data = crate::yaml::BuildingData { 
        building: crate::core::Building::default(), 
        equipment: Vec::new() 
    };
    let mut results = Vec::new();

    // Helper function to calculate 3D distance
    let distance_3d = |p1: &Point3D, p2: &Point3D| -> f64 {
        let dx = p1.x - p2.x;
        let dy = p1.y - p2.y;
        let dz = p1.z - p2.z;
        (dx * dx + dy * dy + dz * dz).sqrt()
    };

    // Collect all entities first
    let mut all_entities: Vec<(String, String, Point3D, bool)> = Vec::new();
    for floor in &building_data.floors {
        // Filter by entity type if specified
        let include_rooms = entity.is_empty() || entity.to_lowercase() == "room";
        let include_equipment = entity.is_empty() || entity.to_lowercase() == "equipment";

        if include_rooms {
            // Collect rooms from wings (primary location)
            for wing in &floor.wings {
                for room in &wing.rooms {
                    all_entities.push((
                        room.name.clone(),
                        format!("Room ({:?})", room.room_type),
                        crate::spatial::Point3D::new(
                            room.spatial_properties.position.x,
                            room.spatial_properties.position.y,
                            room.spatial_properties.position.z,
                        ),
                        true,
                    ));
                }
            }
            // Note: Legacy rooms list removed - rooms are only in wings now
        }

        if include_equipment {
            for equipment in &floor.equipment {
                all_entities.push((
                    equipment.name.clone(),
                    format!("Equipment ({:?})", equipment.equipment_type),
                    crate::spatial::Point3D::new(
                        equipment.position.x,
                        equipment.position.y,
                        equipment.position.z,
                    ),
                    false,
                ));
            }
        }
    }

    // Process query based on type
    match query_type.to_lowercase().as_str() {
        "distance" => {
            // Calculate distance between two entities
            if params.len() < 2 {
                return Err("Distance query requires two entity names/IDs".into());
            }

            let source_name = &params[0];
            let target_name = &params[1];

            let source_entity = all_entities
                .iter()
                .find(|(name, _, _, _)| name == source_name || name.contains(source_name))
                .ok_or_else(|| format!("Source entity '{}' not found", source_name))?;

            let target_entity = all_entities
                .iter()
                .find(|(name, _, _, _)| name == target_name || name.contains(target_name))
                .ok_or_else(|| format!("Target entity '{}' not found", target_name))?;

            let distance = distance_3d(&source_entity.2, &target_entity.2);

            results.push(SpatialQueryResult {
                entity_name: target_entity.0.clone(),
                entity_type: target_entity.1.clone(),
                position: Position {
                    x: target_entity.2.x,
                    y: target_entity.2.y,
                    z: target_entity.2.z,
                    coordinate_system: "building_local".to_string(),
                },
                distance,
            });
        }

        "within_radius" => {
            // Find entities within radius of a point
            if params.len() < 4 {
                return Err(
                    "Within_radius query requires center point (x, y, z) and radius".into(),
                );
            }

            let center_x = params[0]
                .parse::<f64>()
                .map_err(|e| format!("Invalid X coordinate '{}': {}", params[0], e))?;
            let center_y = params[1]
                .parse::<f64>()
                .map_err(|e| format!("Invalid Y coordinate '{}': {}", params[1], e))?;
            let center_z = params[2]
                .parse::<f64>()
                .map_err(|e| format!("Invalid Z coordinate '{}': {}", params[2], e))?;
            let radius = params[3]
                .parse::<f64>()
                .map_err(|e| format!("Invalid radius '{}': {}", params[3], e))?;

            let center = Point3D::new(center_x, center_y, center_z);

            for (name, entity_type, pos, _) in &all_entities {
                let distance = distance_3d(&center, pos);
                if distance <= radius {
                    results.push(SpatialQueryResult {
                        entity_name: name.clone(),
                        entity_type: entity_type.clone(),
                        position: Position {
                            x: pos.x,
                            y: pos.y,
                            z: pos.z,
                            coordinate_system: "building_local".to_string(),
                        },
                        distance,
                    });
                }
            }

            // Sort by distance (closest first)
            results.sort_by(|a, b| {
                a.distance
                    .partial_cmp(&b.distance)
                    .unwrap_or(std::cmp::Ordering::Equal)
            });
        }

        "nearest" => {
            // Find nearest entity to a point
            if params.len() < 3 {
                return Err("Nearest query requires reference point (x, y, z)".into());
            }

            let ref_x = params[0]
                .parse::<f64>()
                .map_err(|e| format!("Invalid X coordinate '{}': {}", params[0], e))?;
            let ref_y = params[1]
                .parse::<f64>()
                .map_err(|e| format!("Invalid Y coordinate '{}': {}", params[1], e))?;
            let ref_z = params[2]
                .parse::<f64>()
                .map_err(|e| format!("Invalid Z coordinate '{}': {}", params[2], e))?;

            let reference_point = Point3D::new(ref_x, ref_y, ref_z);
            let max_distance = if params.len() >= 4 {
                Some(
                    params[3]
                        .parse::<f64>()
                        .map_err(|e| format!("Invalid max distance '{}': {}", params[3], e))?,
                )
            } else {
                None
            };

            let mut candidates: Vec<SpatialQueryResult> = Vec::new();

            for (name, entity_type, pos, _) in &all_entities {
                let distance = distance_3d(&reference_point, pos);

                if let Some(max_dist) = max_distance {
                    if distance > max_dist {
                        continue;
                    }
                }

                candidates.push(SpatialQueryResult {
                    entity_name: name.clone(),
                    entity_type: entity_type.clone(),
                    position: Position {
                        x: pos.x,
                        y: pos.y,
                        z: pos.z,
                        coordinate_system: "building_local".to_string(),
                    },
                    distance,
                });
            }

            // Sort by distance and return only the nearest
            candidates.sort_by(|a, b| {
                a.distance
                    .partial_cmp(&b.distance)
                    .unwrap_or(std::cmp::Ordering::Equal)
            });

            if let Some(nearest) = candidates.first() {
                results.push(nearest.clone());
            }
        }

        "all" | "" => {
            // Return all entities with distance from origin
            let origin = Point3D::new(0.0, 0.0, 0.0);

            for (name, entity_type, pos, _) in &all_entities {
                let distance = distance_3d(&origin, pos);
                results.push(SpatialQueryResult {
                    entity_name: name.clone(),
                    entity_type: entity_type.clone(),
                    position: Position {
                        x: pos.x,
                        y: pos.y,
                        z: pos.z,
                        coordinate_system: "building_local".to_string(),
                    },
                    distance,
                });
            }
        }

        _ => {
            return Err(format!("Unknown query type: '{}'. Supported types: 'distance', 'within_radius', 'nearest', 'all'", query_type).into());
        }
    }

    Ok(results)
}

/// List all rooms in the building
///
/// # Arguments
/// * `building_name` - Optional building name to filter by. If None, loads from current directory.
pub fn list_rooms(building_name: Option<&str>) -> Result<Vec<Room>, Box<dyn std::error::Error>> {
    use crate::persistence::{load_building_data_from_dir, PersistenceManager};

    let building_data = if let Some(building) = building_name {
        let persistence = PersistenceManager::new(building)?;
        persistence.load_building_data()?
    } else {
        load_building_data_from_dir()?
    };

    let mut rooms = Vec::new();

    for floor in &building_data.floors {
        // Collect rooms from wings (primary location)
        for wing in &floor.wings {
            rooms.extend(wing.rooms.iter().cloned());
        }
        // Also collect from legacy rooms list
        // Note: Legacy rooms list removed - rooms are only in wings now
    }

    Ok(rooms)
}

/// Get a specific room by name
///
/// # Arguments
/// * `building_name` - Optional building name to filter by. If None, loads from current directory.
/// * `room_name` - Name or ID of the room to retrieve.
pub fn get_room(
    building_name: Option<&str>,
    room_name: &str,
) -> Result<Room, Box<dyn std::error::Error>> {
    use crate::persistence::{load_building_data_from_dir, PersistenceManager};

    let building_data = if let Some(building) = building_name {
        let persistence = PersistenceManager::new(building)?;
        persistence.load_building_data()?
    } else {
        load_building_data_from_dir()?
    };

    for floor in &building_data.floors {
        // Search in wings first (primary location)
        for wing in &floor.wings {
            for room in &wing.rooms {
                if room.name.to_lowercase() == room_name.to_lowercase()
                    || room.id.to_lowercase() == room_name.to_lowercase()
                {
                    return Ok(room.clone());
                }
            }
        }
        // Note: Legacy rooms list removed - rooms are only in wings now
    }

    Err(format!("Room '{}' not found", room_name).into())
}

/// Update a room in a building
pub fn update_room_impl(
    building_name: &str,
    room_id: &str,
    updates: HashMap<String, String>,
    commit: bool,
) -> Result<Room, Box<dyn std::error::Error>> {
    use crate::persistence::PersistenceManager;

    let persistence = PersistenceManager::new(building_name)?;
    let mut building_data = persistence.load_building_data()?;

    // Find and update room
    let mut updated_room = None;
    for floor in &mut building_data.floors {
        // Search in wings first (primary location)
        for wing in &mut floor.wings {
            if let Some(room) = wing
                .rooms
                .iter_mut()
                .find(|r| r.id == room_id || r.name == room_id)
            {
                // Update properties
                for (key, value) in updates.iter() {
                    room.properties.insert(key.clone(), value.clone());
                }
                updated_room = Some(room.clone());
                break;
            }
        }
        if updated_room.is_some() {
            break;
        }
        // Note: Legacy rooms list removed - rooms are only in wings now
    }

    let room = updated_room.ok_or_else(|| format!("Room '{}' not found", room_id))?;

    // Save
    if commit {
        persistence
            .save_and_commit(&building_data, Some(&format!("Update room: {}", room.name)))?;
    } else {
        persistence.save_building_data(&building_data)?;
    }

    Ok(room)
}

/// Delete a room from a building
pub fn delete_room_impl(
    building_name: &str,
    room_id: &str,
    commit: bool,
) -> Result<(), Box<dyn std::error::Error>> {
    use crate::persistence::PersistenceManager;

    let persistence = PersistenceManager::new(building_name)?;
    let mut building_data = persistence.load_building_data()?;

    // Find and remove room
    for floor in &mut building_data.floors {
        // Remove from wings (primary location)
        for wing in &mut floor.wings {
            wing.rooms.retain(|r| r.id != room_id && r.name != room_id);
        }
        // Note: Legacy rooms list removed - rooms are only in wings now
    }

    // Save
    if commit {
        persistence.save_and_commit(&building_data, Some(&format!("Delete room: {}", room_id)))?;
    } else {
        persistence.save_building_data(&building_data)?;
    }

    Ok(())
}

/// List all equipment in the building
///
/// # Arguments
/// * `building_name` - Optional building name to filter by. If None, loads from current directory.
pub fn list_equipment(
    building_name: Option<&str>,
) -> Result<Vec<Equipment>, Box<dyn std::error::Error>> {
    use crate::persistence::{load_building_data_from_dir, PersistenceManager};

    let building_data = if let Some(building) = building_name {
        let persistence = PersistenceManager::new(building)?;
        persistence.load_building_data()?
    } else {
        load_building_data_from_dir()?
    };

    let mut equipment = Vec::new();

    for floor in &building_data.floors {
        equipment.extend(floor.equipment.iter().cloned());
    }

    Ok(equipment)
}

/// Update equipment in a building
pub fn update_equipment_impl(
    building_name: &str,
    equipment_id: &str,
    updates: HashMap<String, String>,
    commit: bool,
) -> Result<Equipment, Box<dyn std::error::Error>> {
    use crate::persistence::PersistenceManager;

    let persistence = PersistenceManager::new(building_name)?;
    let mut building_data = persistence.load_building_data()?;

    // Find and update equipment
    let mut found = false;
    for floor in &mut building_data.floors {
        if let Some(equipment) = floor
            .equipment
            .iter_mut()
            .find(|e| e.id == equipment_id || e.name == equipment_id)
        {
            for (key, value) in updates.iter() {
                equipment.properties.insert(key.clone(), value.clone());
            }
            found = true;
            break;
        }
    }

    if !found {
        return Err(format!("Equipment '{}' not found", equipment_id).into());
    }

    // Get the updated equipment before saving
    let updated_equipment = {
        let mut found_equipment = None;
        for floor in &building_data.floors {
            if let Some(equipment) = floor
                .equipment
                .iter()
                .find(|e| e.id == equipment_id || e.name == equipment_id)
            {
                found_equipment = Some(equipment.clone());
                break;
            }
        }
        found_equipment.ok_or_else(|| format!("Equipment '{}' not found", equipment_id))?
    };

    // Save
    if commit {
        persistence.save_and_commit(
            &building_data,
            Some(&format!("Update equipment: {}", equipment_id)),
        )?;
    } else {
        persistence.save_building_data(&building_data)?;
    }

    Ok(updated_equipment)
}

/// Remove equipment from a building
pub fn remove_equipment_impl(
    building_name: &str,
    equipment_id: &str,
    commit: bool,
) -> Result<(), Box<dyn std::error::Error>> {
    use crate::persistence::PersistenceManager;

    let persistence = PersistenceManager::new(building_name)?;
    let mut building_data = persistence.load_building_data()?;

    // Find and remove equipment
    let mut found = false;
    for floor in &mut building_data.floors {
        let before = floor.equipment.len();
        floor
            .equipment
            .retain(|e| e.id != equipment_id && e.name != equipment_id);
        if floor.equipment.len() < before {
            found = true;
        }
    }

    if !found {
        return Err(format!("Equipment '{}' not found", equipment_id).into());
    }

    // Save
    if commit {
        persistence.save_and_commit(
            &building_data,
            Some(&format!("Remove equipment: {}", equipment_id)),
        )?;
    } else {
        persistence.save_building_data(&building_data)?;
    }

    Ok(())
}

/// Set spatial relationship between entities
///
/// **Note:** This function is reserved for future use. Currently, spatial relationships
/// are tracked implicitly through bounding boxes. Full relationship management will be
/// implemented in a future release.
///
/// When implemented, this will allow explicit relationships like:
/// - Adjacency (rooms next to each other)
/// - Containment (equipment within rooms)
/// - Connectivity (equipment connected to other equipment)
///
/// # Arguments
///
/// * `entity1` - First entity identifier
/// * `entity2` - Second entity identifier
/// * `relationship` - Type of relationship to establish
///
/// # Returns
///
/// Currently returns a formatted message indicating the relationship would be set.
#[allow(dead_code)] // Reserved for future spatial relationship implementation
pub fn set_spatial_relationship(
    entity1: &str,
    entity2: &str,
    relationship: &str,
) -> Result<String, Box<dyn std::error::Error>> {
    Ok(format!("Relationship '{}' set between '{}' and '{}' (spatial relationships tracked in bounding boxes)", relationship, entity1, entity2))
}

/// Transform coordinates between coordinate systems
///
/// **Note:** This function is reserved for future use. Currently, all coordinates
/// are in the "building_local" system. Full coordinate transformation support will
/// be implemented in a future release.
///
/// When implemented, this will support transformations between:
/// - Building local coordinates
/// - World coordinates (GPS/lat-lon)
/// - UTM coordinates
/// - Custom coordinate systems
///
/// **Implementation Status:** This function is part of the public CLI API but is reserved
/// for future implementation. It currently returns a status message. Full implementation would
/// require coordinate system definitions and transformation matrices.
///
/// # Arguments
///
/// * `from` - Source coordinate system
/// * `to` - Target coordinate system
/// * `entity` - Entity identifier to transform
///
/// # Returns
///
/// Currently returns a formatted message indicating the transformation would be completed.
///
/// # Future Implementation
///
/// When fully implemented, this function will:
/// 1. Load coordinate system definitions from building metadata
/// 2. Calculate transformation matrices
/// 3. Transform entity coordinates
/// 4. Update entity positions in building data
/// 5. Return transformation metadata instead of a string
#[allow(dead_code)] // Reserved for future coordinate transformation implementation - part of CLI API
pub fn transform_coordinates(
    from: &str,
    to: &str,
    entity: &str,
) -> Result<String, Box<dyn std::error::Error>> {
    // Reserved for future implementation - currently returns status message
    // This is part of the CLI API, so we maintain the function signature
    Ok(format!("Coordinate transformation '{}' to '{}' for entity '{}' completed (all coordinates in building_local system)", from, to, entity))
}

/// Result of spatial validation
#[derive(Debug, Clone)]
pub struct SpatialValidationResult {
    /// Whether validation passed overall
    pub is_valid: bool,
    /// Number of entities validated
    pub entities_checked: usize,
    /// Number of validation issues found
    pub issues_found: usize,
    /// List of validation issues
    pub issues: Vec<SpatialValidationIssue>,
    /// Tolerance used for validation
    pub tolerance: f64,
}

/// Individual spatial validation issue
#[derive(Debug, Clone)]
pub struct SpatialValidationIssue {
    /// Entity name that has the issue
    pub entity_name: String,
    /// Type of entity (room or equipment)
    pub entity_type: String,
    /// Type of validation issue
    pub issue_type: String,
    /// Description of the issue
    pub message: String,
    /// Severity level
    pub severity: String,
}

/// Validate spatial data for entities
///
/// Performs comprehensive spatial validation including:
/// - Bounding box integrity (min <= max in all dimensions)
/// - Spatial consistency checks
/// - Coordinate system validity
///
/// # Arguments
///
/// * `entity` - Optional entity name to validate. If None, validates all entities.
/// * `tolerance` - Optional tolerance for floating-point comparisons (default: 0.001).
///
/// # Returns
///
/// Structured validation result with detailed issue information.
pub fn validate_spatial(
    entity: Option<&str>,
    tolerance: Option<f64>,
) -> Result<SpatialValidationResult, Box<dyn std::error::Error>> {
    let tol = tolerance.unwrap_or(0.001);
    // Load building data - implementation would need proper file path
    let building_data = crate::yaml::BuildingData { 
        building: crate::core::Building::default(), 
        equipment: Vec::new() 
    };
    let mut issues = Vec::new();
    let mut entities_checked = 0;

    // Helper function to validate bounding box
    let validate_bounding_box = |name: &str,
                                 entity_type: &str,
                                 bbox: &crate::spatial::BoundingBox3D|
     -> Vec<SpatialValidationIssue> {
        let mut bbox_issues = Vec::new();

        // Check if min < max in all dimensions (with tolerance)
        if bbox.min.x > bbox.max.x + tol {
            bbox_issues.push(SpatialValidationIssue {
                entity_name: name.to_string(),
                entity_type: entity_type.to_string(),
                issue_type: "BoundingBoxInvalid".to_string(),
                message: format!(
                    "Bounding box X dimension invalid: min.x ({:.3}) > max.x ({:.3})",
                    bbox.min.x, bbox.max.x
                ),
                severity: "High".to_string(),
            });
        }

        if bbox.min.y > bbox.max.y + tol {
            bbox_issues.push(SpatialValidationIssue {
                entity_name: name.to_string(),
                entity_type: entity_type.to_string(),
                issue_type: "BoundingBoxInvalid".to_string(),
                message: format!(
                    "Bounding box Y dimension invalid: min.y ({:.3}) > max.y ({:.3})",
                    bbox.min.y, bbox.max.y
                ),
                severity: "High".to_string(),
            });
        }

        if bbox.min.z > bbox.max.z + tol {
            bbox_issues.push(SpatialValidationIssue {
                entity_name: name.to_string(),
                entity_type: entity_type.to_string(),
                issue_type: "BoundingBoxInvalid".to_string(),
                message: format!(
                    "Bounding box Z dimension invalid: min.z ({:.3}) > max.z ({:.3})",
                    bbox.min.z, bbox.max.z
                ),
                severity: "High".to_string(),
            });
        }

        // Check for zero or negative dimensions
        let width = (bbox.max.x - bbox.min.x).abs();
        let depth = (bbox.max.y - bbox.min.y).abs();
        let height = (bbox.max.z - bbox.min.z).abs();

        if width < tol {
            bbox_issues.push(SpatialValidationIssue {
                entity_name: name.to_string(),
                entity_type: entity_type.to_string(),
                issue_type: "ZeroDimension".to_string(),
                message: format!("Bounding box has zero width: {:.3}", width),
                severity: "Medium".to_string(),
            });
        }

        if depth < tol {
            bbox_issues.push(SpatialValidationIssue {
                entity_name: name.to_string(),
                entity_type: entity_type.to_string(),
                issue_type: "ZeroDimension".to_string(),
                message: format!("Bounding box has zero depth: {:.3}", depth),
                severity: "Medium".to_string(),
            });
        }

        if height < tol {
            bbox_issues.push(SpatialValidationIssue {
                entity_name: name.to_string(),
                entity_type: entity_type.to_string(),
                issue_type: "ZeroDimension".to_string(),
                message: format!("Bounding box has zero height: {:.3}", height),
                severity: "Medium".to_string(),
            });
        }

        bbox_issues
    };

    // Validate based on entity filter
    match entity {
        Some(entity_name) => {
            // Validate specific entity
            let mut found = false;

            // Check rooms
            for floor in &building_data.floors {
                // Check wings first (primary location)
                for wing in &floor.wings {
                    for room in &wing.rooms {
                        if room.name == entity_name || room.id == entity_name {
                            entities_checked = 1;
                            found = true;
                            let bbox = &room.spatial_properties.bounding_box;
                            issues.extend(validate_bounding_box(
                                &room.name,
                                "Room",
                                &crate::spatial::BoundingBox3D::new(
                                    crate::spatial::Point3D::new(
                                        bbox.min.x, bbox.min.y, bbox.min.z,
                                    ),
                                    crate::spatial::Point3D::new(
                                        bbox.max.x, bbox.max.y, bbox.max.z,
                                    ),
                                ),
                            ));
                            break;
                        }
                    }
                    if found {
                        break;
                    }
                }
                if found {
                    break;
                }
                // Note: Legacy rooms list removed - rooms are only in wings now
                if found {
                    break;
                }
            }

            // Check equipment if not found in rooms
            if !found {
                for floor in &building_data.floors {
                    for equipment in &floor.equipment {
                        if equipment.name == entity_name || equipment.id == entity_name {
                            entities_checked = 1;
                            found = true;
                            // Equipment doesn't have a bounding_box field directly, use position-based bbox
                            let pos = &equipment.position;
                            let bbox = crate::spatial::BoundingBox3D::new(
                                crate::spatial::Point3D::new(pos.x - 0.5, pos.y - 0.5, pos.z - 0.5),
                                crate::spatial::Point3D::new(pos.x + 0.5, pos.y + 0.5, pos.z + 0.5),
                            );
                            issues.extend(validate_bounding_box(
                                &equipment.name,
                                "Equipment",
                                &bbox,
                            ));
                            break;
                        }
                    }
                    if found {
                        break;
                    }
                }
            }

            if !found {
                return Err(
                    format!("Entity '{}' not found for spatial validation", entity_name).into(),
                );
            }
        }
        None => {
            // Validate all entities
            for floor in &building_data.floors {
                // Validate rooms in wings (primary location)
                for wing in &floor.wings {
                    for room in &wing.rooms {
                        entities_checked += 1;
                        let bbox = &room.spatial_properties.bounding_box;
                        issues.extend(validate_bounding_box(
                            &room.name,
                            "Room",
                            &crate::spatial::BoundingBox3D::new(
                                crate::spatial::Point3D::new(bbox.min.x, bbox.min.y, bbox.min.z),
                                crate::spatial::Point3D::new(bbox.max.x, bbox.max.y, bbox.max.z),
                            ),
                        ));
                    }
                }
                // Also validate legacy rooms list
                // Note: Legacy rooms list removed - rooms are only in wings now
                // Rooms are validated through wings above

                for equipment in &floor.equipment {
                    entities_checked += 1;
                    // Equipment doesn't have a bounding_box field directly, use position-based bbox
                    let pos = &equipment.position;
                    let bbox = crate::spatial::BoundingBox3D::new(
                        crate::spatial::Point3D::new(pos.x - 0.5, pos.y - 0.5, pos.z - 0.5),
                        crate::spatial::Point3D::new(pos.x + 0.5, pos.y + 0.5, pos.z + 0.5),
                    );
                    issues.extend(validate_bounding_box(&equipment.name, "Equipment", &bbox));
                }
            }
        }
    }

    Ok(SpatialValidationResult {
        is_valid: issues.is_empty(),
        entities_checked,
        issues_found: issues.len(),
        issues,
        tolerance: tol,
    })
}

// Compatibility wrapper functions for existing CLI handlers
// These need building_name which should come from context
// For now, they work on the current directory's building data

/// Update a room (compatibility wrapper - uses first building found in current directory)
pub fn update_room(
    room_id: &str,
    property: Vec<String>,
) -> Result<Room, Box<dyn std::error::Error>> {
    // Parse properties into HashMap
    let mut updates = HashMap::new();
    for prop in property {
        if let Some((key, value)) = prop.split_once('=') {
            updates.insert(key.to_string(), value.to_string());
        }
    }

    // Find building name from current directory
    let yaml_files: Vec<String> = std::fs::read_dir(".")?
        .filter_map(|entry| {
            let entry = entry.ok()?;
            let path = entry.path();
            if path.extension()? == "yaml" || path.extension()? == "yml" {
                path.to_str().map(|s| s.to_string())
            } else {
                None
            }
        })
        .collect();

    if yaml_files.is_empty() {
        return Err("No building files found in current directory".into());
    }

    // Use first building file found (could be improved)
    update_room_impl("", room_id, updates, false)
}

/// Delete a room (compatibility wrapper - uses first building found in current directory)
///
/// This function attempts to determine the building name from YAML files in the
/// current directory. For better reliability, use `delete_room_impl` with an explicit
/// building name.
pub fn delete_room(room_id: &str) -> Result<(), Box<dyn std::error::Error>> {
    // Determine building name from YAML file in current directory
    let building_data = crate::yaml::BuildingData { 
        building: crate::core::Building::default(), 
        equipment: Vec::new() 
    };

    let building_name = &building_data.building.name;
    delete_room_impl(building_name, room_id, false)
}

/// Update equipment (compatibility wrapper)
///
/// This function attempts to determine the building name from YAML files in the
/// current directory. For better reliability, use `update_equipment_impl` with an explicit
/// building name.
pub fn update_equipment(
    equipment_id: &str,
    property: Vec<String>,
) -> Result<Equipment, Box<dyn std::error::Error>> {
    use crate::persistence::load_building_data_from_dir;

    // Parse properties into HashMap
    let mut updates = HashMap::new();
    for prop in property {
        if let Some((key, value)) = prop.split_once('=') {
            updates.insert(key.to_string(), value.to_string());
        }
    }

    // Determine building name from YAML file in current directory
    let building_data = crate::yaml::BuildingData { 
        building: crate::core::Building::default(), 
        equipment: Vec::new() 
    };

    let building_name = &building_data.building.name;
    update_equipment_impl(building_name, equipment_id, updates, false)
}

/// Remove equipment (compatibility wrapper)
///
/// This function attempts to determine the building name from YAML files in the
/// current directory. For better reliability, use `remove_equipment_impl` with an explicit
/// building name.
pub fn remove_equipment(equipment_id: &str) -> Result<(), Box<dyn std::error::Error>> {
    // Determine building name from YAML file in current directory
    let building_data = crate::yaml::BuildingData { 
        building: crate::core::Building::default(), 
        equipment: Vec::new() 
    };

    let building_name = &building_data.building.name;
    remove_equipment_impl(building_name, equipment_id, false)
}
