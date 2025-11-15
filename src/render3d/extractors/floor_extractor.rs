//! Floor data extraction for 3D rendering
//!
//! Converts building floor data into 3D floor representations with
//! proper elevations, bounding boxes, and entity references.

use crate::render3d::types::Floor3D;
use crate::core::spatial::{BoundingBox3D, Point3D};
use crate::yaml::BuildingData;
use std::sync::Arc;

/// Extract 3D floor representations from building data
///
/// Converts building floor data into optimized 3D representations
/// with proper elevation and bounding boxes.
///
/// # Arguments
///
/// * `building_data` - Source building data containing floors
///
/// # Returns
///
/// Vector of Floor3D objects with computed elevations and bounding boxes
///
/// # Elevation Calculation
///
/// - Uses explicit floor.elevation if available
/// - Otherwise calculates as floor.level * 3.0 meters
///
/// # Bounding Box
///
/// - Uses floor.bounding_box if available
/// - Otherwise creates default 100x100m box at floor elevation
pub fn extract_floors_3d(building_data: &BuildingData) -> Vec<Floor3D> {
    building_data
        .building
        .floors
        .iter()
        .map(|floor| {
            let elevation = floor.elevation.unwrap_or(floor.level as f64 * 3.0);
            let bounding_box = floor.bounding_box.clone().unwrap_or_else(|| BoundingBox3D {
                min: Point3D {
                    x: 0.0,
                    y: 0.0,
                    z: elevation,
                },
                max: Point3D {
                    x: 100.0,
                    y: 100.0,
                    z: elevation + 3.0,
                },
            });

            // Collect room IDs from all wings
            let rooms = floor
                .wings
                .iter()
                .flat_map(|w| w.rooms.iter())
                .map(|r| Arc::new(r.id.clone()))
                .collect();

            // Collect equipment IDs from floor level
            let equipment = floor
                .equipment
                .iter()
                .map(|e| Arc::new(e.id.clone()))
                .collect();

            Floor3D {
                id: Arc::new(floor.id.clone()),
                name: Arc::new(floor.name.clone()),
                level: floor.level,
                elevation,
                bounding_box,
                rooms,
                equipment,
            }
        })
        .collect()
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::core::{Building, Floor, Wing, Room};

    #[test]
    fn test_extract_floors_3d() {
        let mut building = Building::default();
        building.name = "Test Building".to_string();

        let mut floor = Floor::new("Floor 1".to_string(), 0);
        floor.elevation = Some(0.0);

        let wing = Wing::new("Wing A".to_string());
        floor.wings.push(wing);
        building.add_floor(floor);

        let building_data = crate::yaml::BuildingData {
            building,
            equipment: Vec::new(),
        };

        let floors = extract_floors_3d(&building_data);

        assert_eq!(floors.len(), 1);
        assert_eq!(*floors[0].name, "Floor 1");
        assert_eq!(floors[0].level, 0);
        assert_eq!(floors[0].elevation, 0.0);
    }

    #[test]
    fn test_floor_elevation_calculation() {
        let mut building = Building::default();

        // Floor without explicit elevation
        let floor1 = Floor::new("Floor 1".to_string(), 0);
        let floor2 = Floor::new("Floor 2".to_string(), 1);

        building.add_floor(floor1);
        building.add_floor(floor2);

        let building_data = crate::yaml::BuildingData {
            building,
            equipment: Vec::new(),
        };

        let floors = extract_floors_3d(&building_data);

        // Should calculate elevation as level * 3.0
        assert_eq!(floors[0].elevation, 0.0);
        assert_eq!(floors[1].elevation, 3.0);
    }

    #[test]
    fn test_floor_default_bounding_box() {
        let mut building = Building::default();
        let floor = Floor::new("Floor 1".to_string(), 0);
        building.add_floor(floor);

        let building_data = crate::yaml::BuildingData {
            building,
            equipment: Vec::new(),
        };

        let floors = extract_floors_3d(&building_data);

        // Should have default 100x100m bounding box
        assert_eq!(floors[0].bounding_box.min.x, 0.0);
        assert_eq!(floors[0].bounding_box.min.y, 0.0);
        assert_eq!(floors[0].bounding_box.max.x, 100.0);
        assert_eq!(floors[0].bounding_box.max.y, 100.0);
    }
}
