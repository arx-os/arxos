//! Query engine for ArxOS Address glob patterns
//!
//! Provides glob pattern matching on ArxAddress paths for finding equipment
//! and rooms that match hierarchical path patterns.
//!
//! # Examples
//!
//! ```rust
//! use arxos::query::query_addresses;
//! use arxos::yaml::BuildingData;
//!
//! let building_data = /* ... */;
//! let results = query_addresses(&building_data, "/usa/ny/*/floor-*/mech/boiler-*")?;
//! ```

use crate::yaml::BuildingData;
use glob::Pattern;
use serde::{Serialize, Deserialize};

/// Query result containing equipment matching the address pattern
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct QueryResult {
    /// Equipment name
    pub name: String,
    /// Full address path
    pub address: String,
    /// Equipment type
    pub equipment_type: String,
    /// Floor level (if determinable)
    pub floor: Option<i32>,
    /// Room name (if determinable)
    pub room: Option<String>,
}

/// Query building data using an ArxAddress glob pattern
///
/// # Arguments
///
/// * `building_data` - Building data to search
/// * `pattern` - Glob pattern for address paths (e.g., "/usa/ny/*/floor-*/mech/boiler-*")
///
/// # Returns
///
/// * `Result<Vec<QueryResult>>` - Matching equipment items
///
/// # Examples
///
/// ```rust
/// # use arxos::query::query_addresses;
/// # use arxos::yaml::{BuildingData, BuildingInfo, BuildingMetadata};
/// # use chrono::Utc;
/// # let building_data = BuildingData {
/// #     building: BuildingInfo {
/// #         id: "test".to_string(),
/// #         name: "Test".to_string(),
/// #         description: None,
/// #         created_at: Utc::now(),
/// #         updated_at: Utc::now(),
/// #         version: "1.0".to_string(),
/// #         global_bounding_box: None,
/// #     },
/// #     metadata: BuildingMetadata {
/// #         source_file: None,
/// #         parser_version: "1.0".to_string(),
/// #         total_entities: 0,
/// #         spatial_entities: 0,
/// #         coordinate_system: "LOCAL".to_string(),
/// #         units: "meters".to_string(),
/// #         tags: vec![],
/// #     },
/// #     floors: vec![],
/// #     coordinate_systems: vec![],
/// # };
/// let results = query_addresses(&building_data, "/usa/ny/*/floor-*/mech/boiler-*")?;
/// ```
pub fn query_addresses(building_data: &BuildingData, pattern: &str) -> Result<Vec<QueryResult>, Box<dyn std::error::Error>> {
    // Normalize pattern: ensure it starts with /
    let normalized_pattern = if pattern.starts_with('/') {
        pattern.to_string()
    } else {
        format!("/{}", pattern)
    };

    // Compile glob pattern
    let glob_pattern = Pattern::new(&normalized_pattern)?;

    let mut results = Vec::new();

    // Search through all equipment
    for floor in &building_data.floors {
        for equipment in &floor.equipment {
            // Get equipment path (prefer address, fallback to path)
            let path = equipment.address.as_ref()
                .map(|addr| addr.path.clone())
                .filter(|p| !p.is_empty())
                .unwrap_or_else(|| equipment.path.clone());

            // Skip empty paths
            if path.is_empty() {
                continue;
            }

            // Match pattern
            if glob_pattern.matches(&path) {
                let (floor_num, room_name) = extract_location_from_path(&path);
                
                results.push(QueryResult {
                    name: equipment.name.clone(),
                    address: path,
                    equipment_type: format!("{:?}", equipment.equipment_type),
                    floor: floor_num,
                    room: room_name,
                });
            }
        }
    }

    Ok(results)
}

/// Extract floor and room from address path
///
/// Supports both ArxAddress format (/country/state/city/building/floor/room/fixture)
/// and legacy universal_path format.
fn extract_location_from_path(path: &str) -> (Option<i32>, Option<String>) {
    let parts: Vec<&str> = path.split('/').filter(|p| !p.is_empty()).collect();
    
    // Try ArxAddress format first: /country/state/city/building/floor/room/fixture
    if parts.len() == 7 {
        let floor_str = parts[4]; // 5th part (0-indexed)
        let room = parts[5].to_string(); // 6th part
        
        // Extract floor number from "floor-02" format
        let floor = if let Some(floor_num_str) = floor_str.strip_prefix("floor-") {
            floor_num_str.parse::<i32>().ok()
        } else if let Ok(floor_num) = floor_str.parse::<i32>() {
            Some(floor_num)
        } else {
            None
        };
        
        return (floor, Some(room));
    }
    
    // Fall back to universal path format
    let mut floor: Option<i32> = None;
    let mut room: Option<String> = None;
    
    for (i, part) in parts.iter().enumerate() {
        if *part == "FLOOR" && i + 1 < parts.len() {
            if let Ok(floor_num) = parts[i + 1].parse::<i32>() {
                floor = Some(floor_num);
            }
        }
        if let Some(floor_str) = part.strip_prefix("FLOOR-") {
            if let Ok(floor_num) = floor_str.parse::<i32>() {
                floor = Some(floor_num);
            }
        }
        if *part == "ROOM" && i + 1 < parts.len() {
            room = Some(parts[i + 1].to_string());
        }
    }
    
    (floor, room)
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::yaml::{BuildingData, BuildingInfo, BuildingMetadata, FloorData, EquipmentData};
    use crate::domain::ArxAddress;
    use crate::spatial::Point3D;
    use chrono::Utc;

    fn create_test_building_data() -> BuildingData {
        BuildingData {
            building: BuildingInfo {
                id: "test-building".to_string(),
                name: "Test Building".to_string(),
                description: None,
                created_at: Utc::now(),
                updated_at: Utc::now(),
                version: "1.0".to_string(),
                global_bounding_box: None,
            },
            metadata: BuildingMetadata {
                source_file: None,
                parser_version: "1.0".to_string(),
                total_entities: 2,
                spatial_entities: 2,
                coordinate_system: "LOCAL".to_string(),
                units: "meters".to_string(),
                tags: vec![],
            },
            floors: vec![
                FloorData {
                    id: "floor-1".to_string(),
                    name: "Floor 1".to_string(),
                    level: 1,
                    elevation: 0.0,
                    wings: vec![],
                    rooms: vec![],
                    equipment: vec![
                        EquipmentData {
                            id: "equipment-1".to_string(),
                            name: "Boiler 01".to_string(),
                            equipment_type: "HVAC".to_string(),
                            system_type: "HVAC".to_string(),
                            position: Point3D::new(0.0, 0.0, 0.0),
                            bounding_box: crate::spatial::BoundingBox3D::new(
                                Point3D::new(-0.5, -0.5, -0.5),
                                Point3D::new(0.5, 0.5, 0.5),
                            ),
                            status: crate::yaml::EquipmentStatus::Healthy,
                            properties: std::collections::HashMap::new(),
                            universal_path: String::new(),
                            address: Some(ArxAddress::from_path("/usa/ny/brooklyn/ps-118/floor-02/mech/boiler-01").unwrap()),
                            sensor_mappings: None,
                        },
                        EquipmentData {
                            id: "equipment-2".to_string(),
                            name: "Boiler 02".to_string(),
                            equipment_type: "HVAC".to_string(),
                            system_type: "HVAC".to_string(),
                            position: Point3D::new(1.0, 1.0, 1.0),
                            bounding_box: crate::spatial::BoundingBox3D::new(
                                Point3D::new(0.5, 0.5, 0.5),
                                Point3D::new(1.5, 1.5, 1.5),
                            ),
                            status: crate::yaml::EquipmentStatus::Healthy,
                            properties: std::collections::HashMap::new(),
                            universal_path: String::new(),
                            address: Some(ArxAddress::from_path("/usa/ny/brooklyn/ps-118/floor-02/mech/boiler-02").unwrap()),
                            sensor_mappings: None,
                        },
                        EquipmentData {
                            id: "equipment-3".to_string(),
                            name: "Valve 01".to_string(),
                            equipment_type: "Plumbing".to_string(),
                            system_type: "Plumbing".to_string(),
                            position: Point3D::new(2.0, 2.0, 2.0),
                            bounding_box: crate::spatial::BoundingBox3D::new(
                                Point3D::new(1.5, 1.5, 1.5),
                                Point3D::new(2.5, 2.5, 2.5),
                            ),
                            status: crate::yaml::EquipmentStatus::Healthy,
                            properties: std::collections::HashMap::new(),
                            universal_path: String::new(),
                            address: Some(ArxAddress::from_path("/usa/ny/brooklyn/ps-118/floor-02/plumbing/valve-01").unwrap()),
                            sensor_mappings: None,
                        },
                    ],
                    bounding_box: None,
                },
            ],
            coordinate_systems: vec![],
        }
    }

    #[test]
    fn test_query_exact_match() {
        let building_data = create_test_building_data();
        let results = query_addresses(&building_data, "/usa/ny/brooklyn/ps-118/floor-02/mech/boiler-01").unwrap();
        assert_eq!(results.len(), 1);
        assert_eq!(results[0].name, "Boiler 01");
    }

    #[test]
    fn test_query_wildcard_room() {
        let building_data = create_test_building_data();
        let results = query_addresses(&building_data, "/usa/ny/brooklyn/ps-118/floor-02/mech/boiler-*").unwrap();
        assert_eq!(results.len(), 2);
        assert!(results.iter().all(|r| r.name.starts_with("Boiler")));
    }

    #[test]
    fn test_query_wildcard_city() {
        let building_data = create_test_building_data();
        let results = query_addresses(&building_data, "/usa/ny/*/ps-118/floor-02/mech/boiler-*").unwrap();
        assert_eq!(results.len(), 2);
    }

    #[test]
    fn test_query_wildcard_floor() {
        let building_data = create_test_building_data();
        let results = query_addresses(&building_data, "/usa/ny/brooklyn/ps-118/floor-*/mech/boiler-*").unwrap();
        assert_eq!(results.len(), 2);
    }

    #[test]
    fn test_query_no_match() {
        let building_data = create_test_building_data();
        let results = query_addresses(&building_data, "/usa/ny/brooklyn/ps-118/floor-02/kitchen/*").unwrap();
        assert_eq!(results.len(), 0);
    }

    #[test]
    fn test_query_different_system() {
        let building_data = create_test_building_data();
        let results = query_addresses(&building_data, "/usa/ny/brooklyn/ps-118/floor-02/plumbing/*").unwrap();
        assert_eq!(results.len(), 1);
        assert_eq!(results[0].name, "Valve 01");
    }
}

