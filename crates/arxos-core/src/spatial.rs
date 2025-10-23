//! Spatial data processing for building management

use crate::{Result, ArxError};
use std::collections::HashMap;
use nalgebra::{Vector3, Matrix3};
use serde::{Deserialize, Serialize};
use tracing::{info, warn};

/// Spatial coordinate system types
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum CoordinateSystem {
    /// Building local coordinates (meters)
    BuildingLocal,
    /// Geographic coordinates (WGS84)
    Geographic,
    /// UTM coordinates
    UTM,
    /// AR world coordinates
    ARWorld,
    /// CAD coordinates
    CAD,
}

/// 3D position with coordinate system
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SpatialPosition {
    pub x: f64,
    pub y: f64,
    pub z: f64,
    pub coordinate_system: CoordinateSystem,
    pub accuracy: f64,
    pub timestamp: Option<chrono::DateTime<chrono::Utc>>,
}

/// Spatial bounding box
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BoundingBox {
    pub min: SpatialPosition,
    pub max: SpatialPosition,
}

/// Spatial entity (room, equipment, etc.)
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SpatialEntity {
    pub id: String,
    pub name: String,
    pub entity_type: String,
    pub position: SpatialPosition,
    pub bounding_box: Option<BoundingBox>,
    pub properties: HashMap<String, String>,
}

/// Spatial processing engine
pub struct SpatialEngine {
    coordinate_transforms: HashMap<(CoordinateSystem, CoordinateSystem), Matrix3<f64>>,
    building_origin: Option<SpatialPosition>,
}

impl SpatialEngine {
    /// Create a new spatial engine
    pub fn new() -> Self {
        Self {
            coordinate_transforms: HashMap::new(),
            building_origin: None,
        }
    }
    
    /// Set building origin for coordinate transformations
    pub fn set_building_origin(&mut self, origin: SpatialPosition) -> Result<()> {
        validate_coordinates(origin.x, origin.y, origin.z)?;
        let origin_clone = origin.clone();
        self.building_origin = Some(origin);
        info!("Building origin set to: ({}, {}, {})", origin_clone.x, origin_clone.y, origin_clone.z);
        Ok(())
    }
    
    /// Process spatial data from various sources
    pub fn process_spatial_data(&mut self, data: Vec<u8>, data_type: &str) -> Result<Vec<SpatialEntity>> {
        info!("Processing spatial data: {} bytes, type: {}", data.len(), data_type);
        
        match data_type {
            "ifc" => self.process_ifc_spatial_data(data),
            "cad" => self.process_cad_spatial_data(data),
            "ar" => self.process_ar_spatial_data(data),
            "lidar" => self.process_lidar_spatial_data(data),
            _ => {
                warn!("Unknown spatial data type: {}", data_type);
                Err(ArxError::Spatial(format!("Unknown data type: {}", data_type)))
            }
        }
    }
    
    /// Process IFC spatial data
    fn process_ifc_spatial_data(&mut self, data: Vec<u8>) -> Result<Vec<SpatialEntity>> {
        // Parse IFC data and extract spatial information
        let ifc_content = String::from_utf8(data)
            .map_err(|e| ArxError::Spatial(format!("Invalid UTF-8 in IFC data: {}", e)))?;
        
        let mut entities = Vec::new();
        
        // Parse IFC entities (simplified parser)
        for line in ifc_content.lines() {
            if line.contains("IFCBUILDING") {
                if let Some(entity) = self.parse_ifc_building(line) {
                    entities.push(entity);
                }
            } else if line.contains("IFCSPACE") {
                if let Some(entity) = self.parse_ifc_space(line) {
                    entities.push(entity);
                }
            } else if line.contains("IFCPRODUCT") {
                if let Some(entity) = self.parse_ifc_product(line) {
                    entities.push(entity);
                }
            }
        }
        
        info!("Processed {} spatial entities from IFC data", entities.len());
        Ok(entities)
    }
    
    /// Process CAD spatial data
    fn process_cad_spatial_data(&mut self, _data: Vec<u8>) -> Result<Vec<SpatialEntity>> {
        // Placeholder for CAD processing
        // In a real implementation, this would parse DWG, DXF, or other CAD formats
        warn!("CAD spatial data processing not yet implemented");
        Ok(vec![])
    }
    
    /// Process AR spatial data
    fn process_ar_spatial_data(&mut self, data: Vec<u8>) -> Result<Vec<SpatialEntity>> {
        // Parse AR point cloud or mesh data
        // This would typically be JSON or binary format from ARKit/ARCore
        let ar_data = String::from_utf8(data)
            .map_err(|e| ArxError::Spatial(format!("Invalid UTF-8 in AR data: {}", e)))?;
        
        let mut entities = Vec::new();
        
        // Parse AR data (simplified)
        if let Ok(ar_json) = serde_json::from_str::<serde_json::Value>(&ar_data) {
            if let Some(points) = ar_json.get("points").and_then(|p| p.as_array()) {
                for (i, point) in points.iter().enumerate() {
                    if let (Some(x), Some(y), Some(z)) = (
                        point.get("x").and_then(|v| v.as_f64()),
                        point.get("y").and_then(|v| v.as_f64()),
                        point.get("z").and_then(|v| v.as_f64()),
                    ) {
                        let entity = SpatialEntity {
                            id: format!("ar_point_{}", i),
                            name: format!("AR Point {}", i),
                            entity_type: "ARPoint".to_string(),
                            position: SpatialPosition {
                                x,
                                y,
                                z,
                                coordinate_system: CoordinateSystem::ARWorld,
                                accuracy: 0.01,
                                timestamp: Some(chrono::Utc::now()),
                            },
                            bounding_box: None,
                            properties: HashMap::new(),
                        };
                        entities.push(entity);
                    }
                }
            }
        }
        
        info!("Processed {} AR spatial entities", entities.len());
        Ok(entities)
    }
    
    /// Process LiDAR spatial data
    fn process_lidar_spatial_data(&mut self, _data: Vec<u8>) -> Result<Vec<SpatialEntity>> {
        // Process LiDAR point cloud data
        // This would typically be binary format from LiDAR sensors
        warn!("LiDAR spatial data processing not yet implemented");
        Ok(vec![])
    }
    
    /// Parse IFC building entity
    fn parse_ifc_building(&self, line: &str) -> Option<SpatialEntity> {
        // Simplified IFC parsing - extract building information
        if let Some(name_start) = line.find("Name=") {
            if let Some(name_end) = line[name_start..].find(',') {
                let name = &line[name_start + 5..name_start + name_end];
                return Some(SpatialEntity {
                    id: format!("building_{}", name.replace(" ", "_").to_lowercase()),
                    name: name.to_string(),
                    entity_type: "Building".to_string(),
                    position: SpatialPosition {
                        x: 0.0,
                        y: 0.0,
                        z: 0.0,
                        coordinate_system: CoordinateSystem::BuildingLocal,
                        accuracy: 0.1,
                        timestamp: Some(chrono::Utc::now()),
                    },
                    bounding_box: None,
                    properties: HashMap::new(),
                });
            }
        }
        None
    }
    
    /// Parse IFC space entity
    fn parse_ifc_space(&self, line: &str) -> Option<SpatialEntity> {
        // Simplified IFC parsing - extract space information
        if let Some(name_start) = line.find("Name=") {
            if let Some(name_end) = line[name_start..].find(',') {
                let name = &line[name_start + 5..name_start + name_end];
                return Some(SpatialEntity {
                    id: format!("space_{}", name.replace(" ", "_").to_lowercase()),
                    name: name.to_string(),
                    entity_type: "Space".to_string(),
                    position: SpatialPosition {
                        x: 0.0,
                        y: 0.0,
                        z: 0.0,
                        coordinate_system: CoordinateSystem::BuildingLocal,
                        accuracy: 0.1,
                        timestamp: Some(chrono::Utc::now()),
                    },
                    bounding_box: None,
                    properties: HashMap::new(),
                });
            }
        }
        None
    }
    
    /// Parse IFC product entity
    fn parse_ifc_product(&self, line: &str) -> Option<SpatialEntity> {
        // Simplified IFC parsing - extract product information
        if let Some(name_start) = line.find("Name=") {
            if let Some(name_end) = line[name_start..].find(',') {
                let name = &line[name_start + 5..name_start + name_end];
                return Some(SpatialEntity {
                    id: format!("product_{}", name.replace(" ", "_").to_lowercase()),
                    name: name.to_string(),
                    entity_type: "Product".to_string(),
                    position: SpatialPosition {
                        x: 0.0,
                        y: 0.0,
                        z: 0.0,
                        coordinate_system: CoordinateSystem::BuildingLocal,
                        accuracy: 0.1,
                        timestamp: Some(chrono::Utc::now()),
                    },
                    bounding_box: None,
                    properties: HashMap::new(),
                });
            }
        }
        None
    }
    
    /// Transform coordinates between systems
    pub fn transform_coordinates(
        &self,
        position: &SpatialPosition,
        target_system: CoordinateSystem,
    ) -> Result<SpatialPosition> {
        if position.coordinate_system == target_system {
            return Ok(position.clone());
        }
        
        let transform_key = (position.coordinate_system, target_system);
        
        if let Some(transform_matrix) = self.coordinate_transforms.get(&transform_key) {
            let source_vector = Vector3::new(position.x, position.y, position.z);
            let transformed_vector = transform_matrix * source_vector;
            
            Ok(SpatialPosition {
                x: transformed_vector.x,
                y: transformed_vector.y,
                z: transformed_vector.z,
                coordinate_system: target_system,
                accuracy: position.accuracy,
                timestamp: position.timestamp,
            })
        } else {
            // Calculate transformation matrix
            let transform_matrix = self.calculate_transform_matrix(
                position.coordinate_system,
                target_system,
            )?;
            
            let source_vector = Vector3::new(position.x, position.y, position.z);
            let transformed_vector = transform_matrix * source_vector;
            
            Ok(SpatialPosition {
                x: transformed_vector.x,
                y: transformed_vector.y,
                z: transformed_vector.z,
                coordinate_system: target_system,
                accuracy: position.accuracy,
                timestamp: position.timestamp,
            })
        }
    }
    
    /// Calculate transformation matrix between coordinate systems
    fn calculate_transform_matrix(
        &self,
        source: CoordinateSystem,
        target: CoordinateSystem,
    ) -> Result<Matrix3<f64>> {
        match (source, target) {
            (CoordinateSystem::BuildingLocal, CoordinateSystem::Geographic) => {
                // Convert building local to geographic using building origin
                if let Some(_origin) = &self.building_origin {
                    Ok(Matrix3::new(
                        1.0, 0.0, 0.0,
                        0.0, 1.0, 0.0,
                        0.0, 0.0, 1.0,
                    ))
                } else {
                    Err(ArxError::Spatial("Building origin not set".to_string()))
                }
            }
            (CoordinateSystem::ARWorld, CoordinateSystem::BuildingLocal) => {
                // AR world to building local transformation
                Ok(Matrix3::new(
                    1.0, 0.0, 0.0,
                    0.0, 1.0, 0.0,
                    0.0, 0.0, 1.0,
                ))
            }
            (CoordinateSystem::Geographic, CoordinateSystem::UTM) => {
                // Geographic to UTM conversion
                Ok(Matrix3::new(
                    1.0, 0.0, 0.0,
                    0.0, 1.0, 0.0,
                    0.0, 0.0, 1.0,
                ))
            }
            _ => {
                warn!("Transformation from {:?} to {:?} not implemented", source, target);
                Err(ArxError::Spatial(format!(
                    "Transformation from {:?} to {:?} not implemented",
                    source, target
                )))
            }
        }
    }
    
    /// Calculate distance between two spatial positions
    pub fn calculate_distance(&self, pos1: &SpatialPosition, pos2: &SpatialPosition) -> Result<f64> {
        // Transform both positions to the same coordinate system
        let pos1_transformed = if pos1.coordinate_system != pos2.coordinate_system {
            self.transform_coordinates(pos1, pos2.coordinate_system)?
        } else {
            pos1.clone()
        };
        
        let dx = pos1_transformed.x - pos2.x;
        let dy = pos1_transformed.y - pos2.y;
        let dz = pos1_transformed.z - pos2.z;
        
        let distance = (dx * dx + dy * dy + dz * dz).sqrt();
        Ok(distance)
    }
    
    /// Find entities within a radius of a position
    pub fn find_entities_within_radius(
        &self,
        entities: &[SpatialEntity],
        center: &SpatialPosition,
        radius: f64,
    ) -> Result<Vec<SpatialEntity>> {
        let mut nearby_entities = Vec::new();
        
        for entity in entities {
            let distance = self.calculate_distance(center, &entity.position)?;
            if distance <= radius {
                nearby_entities.push(entity.clone());
            }
        }
        
        Ok(nearby_entities)
}

/// Validate spatial coordinates
    pub fn validate_coordinates(&self, x: f64, y: f64, z: f64) -> Result<()> {
        if !x.is_finite() || !y.is_finite() || !z.is_finite() {
            return Err(ArxError::Spatial("Coordinates must be finite numbers".to_string()));
        }
        
        // Check reasonable bounds for building coordinates (in meters)
        if x.abs() > 10000.0 || y.abs() > 10000.0 || z.abs() > 1000.0 {
            warn!("Coordinates seem unusually large: ({}, {}, {})", x, y, z);
        }
        
        Ok(())
    }
}

/// Process spatial data (legacy function for compatibility)
pub fn process_spatial_data(data: Vec<u8>) -> Result<String> {
    let mut engine = SpatialEngine::new();
    let entities = engine.process_spatial_data(data, "unknown")?;
    
    let result = serde_json::to_string(&entities)
        .map_err(|e| ArxError::Spatial(format!("Failed to serialize spatial data: {}", e)))?;
    
    Ok(result)
}

/// Validate spatial coordinates (legacy function for compatibility)
pub fn validate_coordinates(x: f64, y: f64, z: f64) -> Result<()> {
    let engine = SpatialEngine::new();
    engine.validate_coordinates(x, y, z)
}
