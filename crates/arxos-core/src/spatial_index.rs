//! # R-Tree Spatial Indexing for ArxOS
//!
//! This module provides efficient R-Tree spatial indexing for building data,
//! enabling fast spatial queries and operations.

use crate::{Result, Position, BoundingBox, Room, Equipment};
use std::collections::HashMap;
use rstar::{RTree, AABB, RTreeObject, RTreeParams};
use serde::{Deserialize, Serialize};

/// Spatial entity wrapper for R-Tree indexing
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct SpatialEntity {
    pub id: String,
    pub entity_type: SpatialEntityType,
    pub bounding_box: BoundingBox,
    pub properties: HashMap<String, String>,
}

/// Types of spatial entities
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub enum SpatialEntityType {
    Room,
    Equipment,
    Wall,
    Door,
    Window,
    Column,
    Beam,
    Slab,
    Other(String),
}

/// R-Tree parameters for spatial indexing
#[derive(Debug)]
pub struct SpatialRTreeParams;

impl RTreeParams for SpatialRTreeParams {
    const MIN_SIZE: usize = 2;
    const MAX_SIZE: usize = 8;
    const REINSERTION_COUNT: usize = 3;
    type DefaultInsertionStrategy = rstar::RStarInsertionStrategy;
}

/// R-Tree spatial index implementation
#[derive(Debug)]
pub struct SpatialRTree {
    tree: RTree<SpatialEntity, SpatialRTreeParams>,
    entities: HashMap<String, SpatialEntity>,
    entity_types: HashMap<String, usize>,
}

impl SpatialRTree {
    /// Create a new R-Tree spatial index
    pub fn new() -> Self {
        Self {
            tree: RTree::new_with_params(),
            entities: HashMap::new(),
            entity_types: HashMap::new(),
        }
    }
    
    /// Add a spatial entity to the index
    pub fn insert(&mut self, entity: SpatialEntity) -> Result<()> {
        let entity_id = entity.id.clone();
        let entity_type = format!("{:?}", entity.entity_type);
        
        // Update counters
        *self.entity_types.entry(entity_type).or_insert(0) += 1;
        
        // Insert into R-Tree
        self.tree.insert(entity.clone());
        
        // Store in hash map for quick lookup
        self.entities.insert(entity_id, entity);
        
        Ok(())
    }
    
    /// Remove a spatial entity from the index
    pub fn remove(&mut self, entity_id: &str) -> Result<()> {
        if let Some(entity) = self.entities.remove(entity_id) {
            // Remove from R-Tree
            self.tree.remove(&entity);
            
            // Update counters
            let entity_type = format!("{:?}", entity.entity_type);
            if let Some(count) = self.entity_types.get_mut(&entity_type) {
                *count -= 1;
                if *count == 0 {
                    self.entity_types.remove(&entity_type);
                }
            }
        }
        
        Ok(())
    }
    
    /// Query entities within a bounding box
    pub fn query_within(&self, bbox: &BoundingBox) -> Vec<&SpatialEntity> {
        let query_bbox = AABB::from_corners(
            [bbox.min.x, bbox.min.y, bbox.min.z],
            [bbox.max.x, bbox.max.y, bbox.max.z],
        );
        
        self.tree.locate_in_envelope(&query_bbox)
            .collect()
    }
    
    /// Query entities within a specified distance of a point
    pub fn query_nearby(&self, point: &Position, distance: f64) -> Vec<&SpatialEntity> {
        let query_bbox = AABB::from_corners(
            [point.x - distance, point.y - distance, point.z - distance],
            [point.x + distance, point.y + distance, point.z + distance],
        );
        
        self.tree.locate_in_envelope(&query_bbox)
            .filter(|entity| {
                let entity_center = SpatialEntity::center(&entity.bounding_box);
                let dx = entity_center.x - point.x;
                let dy = entity_center.y - point.y;
                let dz = entity_center.z - point.z;
                let actual_distance = (dx * dx + dy * dy + dz * dz).sqrt();
                actual_distance <= distance
            })
            .collect()
    }
    
    /// Query entities that intersect with a given bounding box
    pub fn query_intersects(&self, bbox: &BoundingBox) -> Vec<&SpatialEntity> {
        let query_bbox = AABB::from_corners(
            [bbox.min.x, bbox.min.y, bbox.min.z],
            [bbox.max.x, bbox.max.y, bbox.max.z],
        );
        
        self.tree.locate_in_envelope(&query_bbox)
            .collect()
    }
    
    /// Query entities that contain a given point
    pub fn query_contains(&self, point: &Position) -> Vec<&SpatialEntity> {
        self.tree.locate_in_envelope(&AABB::from_point([point.x, point.y, point.z]))
            .filter(|entity| {
                entity.bounding_box.min.x <= point.x && point.x <= entity.bounding_box.max.x &&
                entity.bounding_box.min.y <= point.y && point.y <= entity.bounding_box.max.y &&
                entity.bounding_box.min.z <= point.z && point.z <= entity.bounding_box.max.z
            })
            .collect()
    }
    
    /// Query entities by type
    pub fn query_by_type(&self, entity_type: &SpatialEntityType) -> Vec<&SpatialEntity> {
        self.entities.values()
            .filter(|entity| &entity.entity_type == entity_type)
            .collect()
    }
    
    /// Get all entities
    pub fn get_all_entities(&self) -> Vec<&SpatialEntity> {
        self.entities.values().collect()
    }
    
    /// Get entity by ID
    pub fn get_entity(&self, entity_id: &str) -> Option<&SpatialEntity> {
        self.entities.get(entity_id)
    }
    
    /// Get entity count by type
    pub fn get_entity_count_by_type(&self) -> HashMap<String, usize> {
        self.entity_types.clone()
    }
    
    /// Get total entity count
    pub fn get_total_count(&self) -> usize {
        self.entities.len()
    }
    
    /// Clear all entities
    pub fn clear(&mut self) {
        self.tree = RTree::new_with_params();
        self.entities.clear();
        self.entity_types.clear();
    }
    
    /// Rebuild the R-Tree index (useful after bulk operations)
    pub fn rebuild(&mut self) {
        let entities: Vec<SpatialEntity> = self.entities.values().cloned().collect();
        self.tree = RTree::bulk_load_with_params(entities);
    }
}

impl SpatialEntity {
    /// Create a new spatial entity
    pub fn new(id: String, entity_type: SpatialEntityType, bounding_box: BoundingBox) -> Self {
        Self {
            id,
            entity_type,
            bounding_box,
            properties: HashMap::new(),
        }
    }
    
    /// Calculate the center point of a bounding box
    pub fn center(bbox: &BoundingBox) -> Position {
        Position {
            x: (bbox.min.x + bbox.max.x) / 2.0,
            y: (bbox.min.y + bbox.max.y) / 2.0,
            z: (bbox.min.z + bbox.max.z) / 2.0,
            coordinate_system: bbox.min.coordinate_system.clone(),
        }
    }
    
    /// Calculate the volume of a bounding box
    pub fn volume(bbox: &BoundingBox) -> f64 {
        let dx = bbox.max.x - bbox.min.x;
        let dy = bbox.max.y - bbox.min.y;
        let dz = bbox.max.z - bbox.min.z;
        dx * dy * dz
    }
    
    /// Calculate the area of a bounding box (projected to XY plane)
    pub fn area(bbox: &BoundingBox) -> f64 {
        let dx = bbox.max.x - bbox.min.x;
        let dy = bbox.max.y - bbox.min.y;
        dx * dy
    }
    
    /// Check if two bounding boxes intersect
    pub fn intersects(&self, other: &BoundingBox) -> bool {
        self.bounding_box.min.x <= other.max.x && self.bounding_box.max.x >= other.min.x &&
        self.bounding_box.min.y <= other.max.y && self.bounding_box.max.y >= other.min.y &&
        self.bounding_box.min.z <= other.max.z && self.bounding_box.max.z >= other.min.z
    }
    
    /// Check if this entity contains a point
    pub fn contains_point(&self, point: &Position) -> bool {
        self.bounding_box.min.x <= point.x && point.x <= self.bounding_box.max.x &&
        self.bounding_box.min.y <= point.y && point.y <= self.bounding_box.max.y &&
        self.bounding_box.min.z <= point.z && point.z <= self.bounding_box.max.z
    }
    
    /// Calculate distance to another entity
    pub fn distance_to(&self, other: &SpatialEntity) -> f64 {
        let self_center = Self::center(&self.bounding_box);
        let other_center = Self::center(&other.bounding_box);
        
        let dx = self_center.x - other_center.x;
        let dy = self_center.y - other_center.y;
        let dz = self_center.z - other_center.z;
        
        (dx * dx + dy * dy + dz * dz).sqrt()
    }
}

// Implement RTreeObject trait for SpatialEntity
impl RTreeObject for SpatialEntity {
    type Envelope = AABB<[f64; 3]>;
    
    fn envelope(&self) -> Self::Envelope {
        AABB::from_corners(
            [self.bounding_box.min.x, self.bounding_box.min.y, self.bounding_box.min.z],
            [self.bounding_box.max.x, self.bounding_box.max.y, self.bounding_box.max.z],
        )
    }
}

/// Convert ArxOS entities to spatial entities
pub fn convert_room_to_spatial(room: &Room) -> SpatialEntity {
    SpatialEntity::new(
        room.id.clone(),
        SpatialEntityType::Room,
        room.spatial_properties.bounding_box.clone(),
    )
}

pub fn convert_equipment_to_spatial(equipment: &Equipment) -> SpatialEntity {
    // Create a small bounding box around the equipment position
    let margin = 0.5; // 0.5 meter margin
    let bbox = BoundingBox {
        min: Position {
            x: equipment.position.x - margin,
            y: equipment.position.y - margin,
            z: equipment.position.z - margin,
            coordinate_system: equipment.position.coordinate_system.clone(),
        },
        max: Position {
            x: equipment.position.x + margin,
            y: equipment.position.y + margin,
            z: equipment.position.z + margin,
            coordinate_system: equipment.position.coordinate_system.clone(),
        },
    };
    
    SpatialEntity::new(
        equipment.id.clone(),
        SpatialEntityType::Equipment,
        bbox,
    )
}

/// Convert spatial entities to query results
pub fn convert_to_query_results(entities: Vec<&SpatialEntity>, reference_point: Option<&Position>) -> Vec<crate::types::SpatialQueryResult> {
    entities.into_iter().map(|entity| {
        let distance = reference_point.map(|point| {
            let entity_center = SpatialEntity::center(&entity.bounding_box);
            let dx = entity_center.x - point.x;
            let dy = entity_center.y - point.y;
            let dz = entity_center.z - point.z;
            (dx * dx + dy * dy + dz * dz).sqrt()
        }).unwrap_or(0.0);
        
        let center = SpatialEntity::center(&entity.bounding_box);
        crate::types::SpatialQueryResult {
            entity_type: format!("{:?}", entity.entity_type),
            entity_name: entity.id.clone(),
            distance,
            position: crate::types::Point3D {
                x: center.x,
                y: center.y,
                z: center.z,
            },
        }
    }).collect()
}

/// Spatial index statistics
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SpatialIndexStats {
    pub total_entities: usize,
    pub entity_types: HashMap<String, usize>,
    pub tree_height: usize,
    pub memory_usage_bytes: usize,
}

impl SpatialRTree {
    /// Get spatial index statistics
    pub fn get_stats(&self) -> SpatialIndexStats {
        SpatialIndexStats {
            total_entities: self.entities.len(),
            entity_types: self.entity_types.clone(),
            tree_height: 0, // R-Tree doesn't expose height in this version
            memory_usage_bytes: std::mem::size_of_val(self) + 
                self.entities.len() * std::mem::size_of::<SpatialEntity>() +
                self.entity_types.len() * std::mem::size_of::<(String, usize)>(),
        }
    }
    
    /// Optimize the spatial index
    pub fn optimize(&mut self) {
        self.rebuild();
    }
    
    /// Batch insert multiple entities efficiently
    pub fn batch_insert(&mut self, entities: Vec<SpatialEntity>) -> Result<()> {
        for entity in entities {
            self.insert(entity)?;
        }
        self.rebuild();
        Ok(())
    }
    
    /// Get entities in a specific floor/level
    pub fn query_by_level(&self, level: f64, tolerance: f64) -> Vec<&SpatialEntity> {
        self.entities.values()
            .filter(|entity| {
                let entity_center = SpatialEntity::center(&entity.bounding_box);
                (entity_center.z - level).abs() <= tolerance
            })
            .collect()
    }
    
    /// Get entities in a specific room (by room ID)
    pub fn query_by_room(&self, room_id: &str) -> Vec<&SpatialEntity> {
        self.entities.values()
            .filter(|entity| {
                entity.properties.get("room_id")
                    .map(|id| id == room_id)
                    .unwrap_or(false)
            })
            .collect()
    }
}
