//! Coordinate system transformations and parsing

use super::types::EnhancedIFCParser;
use crate::error::{ArxError, ArxResult};
use crate::spatial::types::CoordinateSystem;
use crate::spatial::{Point3D, SpatialEntity};
use log::info;

impl EnhancedIFCParser {
    /// Transform a point from one coordinate system to another
    pub fn transform_point(
        &self,
        point: &Point3D,
        from_system: &CoordinateSystem,
        to_system: &CoordinateSystem,
    ) -> Point3D {
        // Apply inverse transformation from source system
        let mut transformed = self.apply_inverse_transformation(point, from_system);

        // Apply transformation to target system
        transformed = self.apply_transformation(&transformed, to_system);

        transformed
    }

    /// Apply transformation matrix to a point
    fn apply_transformation(&self, point: &Point3D, system: &CoordinateSystem) -> Point3D {
        // For now, implement simple translation
        // In a full implementation, this would handle rotation and scaling matrices
        Point3D::new(
            point.x + system.origin.x,
            point.y + system.origin.y,
            point.z + system.origin.z,
        )
    }

    /// Apply inverse transformation matrix to a point
    fn apply_inverse_transformation(&self, point: &Point3D, system: &CoordinateSystem) -> Point3D {
        // For now, implement simple inverse translation
        // In a full implementation, this would handle inverse rotation and scaling matrices
        Point3D::new(
            point.x - system.origin.x,
            point.y - system.origin.y,
            point.z - system.origin.z,
        )
    }

    /// Parse IFC coordinate system from entity data
    pub fn parse_coordinate_system(
        &self,
        entity_data: &str,
    ) -> Result<CoordinateSystem, Box<dyn std::error::Error>> {
        // 1. IFCCARTESIANPOINT format
        if entity_data.contains("IFCCARTESIANPOINT") {
            return self.parse_cartesian_point_system(entity_data);
        }

        // 2. IFCAXIS2PLACEMENT3D format
        if entity_data.contains("IFCAXIS2PLACEMENT3D") {
            return self.parse_axis2_placement_system(entity_data);
        }

        // 3. IFCLOCALPLACEMENT format
        if entity_data.contains("IFCLOCALPLACEMENT") {
            return self.parse_local_placement_system(entity_data);
        }

        // Default to origin coordinate system
        Ok(CoordinateSystem::new(
            "DEFAULT".to_string(),
            Point3D::origin(),
        ))
    }

    /// Parse IFCCARTESIANPOINT coordinate system
    fn parse_cartesian_point_system(
        &self,
        data: &str,
    ) -> Result<CoordinateSystem, Box<dyn std::error::Error>> {
        // Extract coordinates from IFCCARTESIANPOINT((x,y,z))
        // Need to find the nested parentheses: IFCCARTESIANPOINT((x,y,z))
        if let Some(start) = data.find("((") {
            if let Some(end) = data.find("))") {
                let coords_str = &data[start + 2..end]; // Skip the double opening parentheses
                let coords: Vec<&str> = coords_str.split(',').collect();

                if coords.len() >= 3 {
                    let x = coords[0].trim().parse::<f64>().unwrap_or(0.0);
                    let y = coords[1].trim().parse::<f64>().unwrap_or(0.0);
                    let z = coords[2].trim().parse::<f64>().unwrap_or(0.0);

                    return Ok(CoordinateSystem::new(
                        "CARTESIAN".to_string(),
                        Point3D::new(x, y, z),
                    ));
                }
            }
        }

        Err("Invalid IFCCARTESIANPOINT format".into())
    }

    /// Parse IFCAXIS2PLACEMENT3D coordinate system
    fn parse_axis2_placement_system(
        &self,
        data: &str,
    ) -> Result<CoordinateSystem, Box<dyn std::error::Error>> {
        // Extract location from IFCAXIS2PLACEMENT3D(#location,#axis,#ref_direction)
        if let Some(start) = data.find('(') {
            if let Some(end) = data.find(')') {
                let params_str = &data[start + 1..end];
                let params: Vec<&str> = params_str.split(',').collect();

                // First parameter is the location reference
                if let Some(_location_ref) = params.first() {
                    // For now, return a coordinate system with origin
                    // In a full implementation, we would resolve the reference
                    return Ok(CoordinateSystem::new(
                        "AXIS2_PLACEMENT".to_string(),
                        Point3D::origin(),
                    ));
                }
            }
        }

        Err("Invalid IFCAXIS2PLACEMENT3D format".into())
    }

    /// Parse IFCLOCALPLACEMENT coordinate system
    fn parse_local_placement_system(
        &self,
        data: &str,
    ) -> Result<CoordinateSystem, Box<dyn std::error::Error>> {
        // Extract placement from IFCLOCALPLACEMENT(#relative_placement,#placement)
        if let Some(start) = data.find('(') {
            if let Some(end) = data.find(')') {
                let params_str = &data[start + 1..end];
                let params: Vec<&str> = params_str.split(',').collect();

                // Second parameter is usually the placement
                if let Some(_placement_ref) = params.get(1) {
                    // For now, return a coordinate system with origin
                    // In a full implementation, we would resolve the reference
                    return Ok(CoordinateSystem::new(
                        "LOCAL_PLACEMENT".to_string(),
                        Point3D::origin(),
                    ));
                }
            }
        }

        Err("Invalid IFCLOCALPLACEMENT format".into())
    }

    /// Convert between different IFC coordinate systems
    pub fn convert_coordinate_system(
        &self,
        point: &Point3D,
        from_system_name: &str,
        to_system_name: &str,
    ) -> Result<Point3D, Box<dyn std::error::Error>> {
        // Create coordinate systems based on names
        let from_system = self.create_coordinate_system_by_name(from_system_name)?;
        let to_system = self.create_coordinate_system_by_name(to_system_name)?;

        // Transform the point
        Ok(self.transform_point(point, &from_system, &to_system))
    }

    /// Create coordinate system by name
    fn create_coordinate_system_by_name(
        &self,
        name: &str,
    ) -> Result<CoordinateSystem, Box<dyn std::error::Error>> {
        match name.to_uppercase().as_str() {
            "IFC_COORDINATE_SYSTEM" | "GLOBAL" => Ok(CoordinateSystem::new(
                "GLOBAL".to_string(),
                Point3D::origin(),
            )),
            "BUILDING_COORDINATE_SYSTEM" | "BUILDING" => Ok(CoordinateSystem::new(
                "BUILDING".to_string(),
                Point3D::new(0.0, 0.0, 0.0),
            )),
            "FLOOR_COORDINATE_SYSTEM" | "FLOOR" => Ok(CoordinateSystem::new(
                "FLOOR".to_string(),
                Point3D::new(0.0, 0.0, 0.0),
            )),
            "ROOM_COORDINATE_SYSTEM" | "ROOM" => Ok(CoordinateSystem::new(
                "ROOM".to_string(),
                Point3D::new(0.0, 0.0, 0.0),
            )),
            _ => Err(format!("Unknown coordinate system: {}", name).into()),
        }
    }

    /// Normalize coordinates to a standard coordinate system
    pub fn normalize_coordinates(
        &self,
        entities: &mut [Box<dyn SpatialEntity>],
        target_system: &str,
    ) -> ArxResult<()> {
        let target_coord_system = self
            .create_coordinate_system_by_name(target_system)
            .map_err(|e| {
                ArxError::spatial_data("Failed to create target coordinate system")
                    .with_debug_info(format!("Error: {}", e))
            })?;

        for entity in entities.iter_mut() {
            if let Some(ref current_system) = entity.coordinate_system {
                // Transform entity position to target coordinate system
                entity.position =
                    self.transform_point(&entity.position, current_system, &target_coord_system);

                // Update coordinate system reference
                entity.coordinate_system = Some(target_coord_system.clone());
            }
        }

        info!(
            "Normalized {} entities to coordinate system: {}",
            entities.len(),
            target_system
        );
        Ok(())
    }
}
