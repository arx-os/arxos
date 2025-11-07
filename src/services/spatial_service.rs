//! Spatial service for spatial query operations
//!
//! Provides high-level operations for spatial queries and relationships,
//! decoupled from persistence concerns. Uses R-Tree spatial indexing for
//! efficient queries on large datasets.

use super::repository::RepositoryRef;
use crate::core::SpatialQueryResult;
use crate::spatial::{SpatialEntity, Point3D, BoundingBox3D};
use std::sync::{Arc, RwLock};
use std::collections::HashMap;

/// Service for spatial operations with built-in spatial indexing
pub struct SpatialService {
    repository: RepositoryRef,
    // Cache spatial indices per building to avoid rebuilding
    indices: Arc<RwLock<HashMap<String, SpatialIndex>>>,
}

/// Internal spatial index using R-Tree for efficient queries
#[derive(Clone)]
struct SpatialIndex {
    #[allow(dead_code)]
    entities: Vec<SpatialEntity>,
    rtree: RTreeNode,
}

/// R-Tree node for spatial indexing
#[derive(Clone)]
#[allow(dead_code)]
struct RTreeNode {
    bounds: BoundingBox3D,
    children: Vec<RTreeNode>,
    entities: Vec<SpatialEntity>,
    is_leaf: bool,
    max_entities: usize,
}

impl SpatialService {
    /// Create a new spatial service with the given repository
    pub fn new(repository: RepositoryRef) -> Self {
        Self {
            repository,
            indices: Arc::new(RwLock::new(HashMap::new())),
        }
    }
    
    /// Create a spatial service with file-based repository (production)
    pub fn with_file_repository() -> Self {
        use super::repository::FileRepository;
        Self::new(Arc::new(FileRepository::new()))
    }
    
    /// Create a spatial service with in-memory repository (testing)
    pub fn with_memory_repository() -> Self {
        use super::repository::InMemoryRepository;
        Self::new(Arc::new(InMemoryRepository::new()))
    }
    
    /// Build or get cached spatial index for a building
    fn get_or_build_index(
        &self,
        building_name: &str,
    ) -> Result<SpatialIndex, Box<dyn std::error::Error + Send + Sync>> {
        // Check cache first
        {
            let indices = self.indices.read().unwrap();
            if let Some(index) = indices.get(building_name) {
                return Ok(index.clone());
            }
        }
        
        // Build new index
        let building_data = self.repository.load(building_name)?;
        let spatial_entities = self.extract_spatial_entities(&building_data);
        let index = SpatialIndex::new(spatial_entities);
        
        // Cache it
        {
            let mut indices = self.indices.write().unwrap();
            indices.insert(building_name.to_string(), index.clone());
        }
        
        Ok(index)
    }
    
    /// Invalidate cached index for a building (call after data changes)
    pub fn invalidate_index(&self, building_name: &str) {
        let mut indices = self.indices.write().unwrap();
        indices.remove(building_name);
    }
    
    /// Query entities near a point using spatial index
    pub fn query_near(
        &self,
        building_name: &str,
        point: Point3D,
        radius: f64,
    ) -> Result<Vec<SpatialQueryResult>, Box<dyn std::error::Error + Send + Sync>> {
        let index = self.get_or_build_index(building_name)?;
        
        // Create bounding box for radius search
        let search_bbox = BoundingBox3D {
            min: Point3D {
                x: point.x - radius,
                y: point.y - radius,
                z: point.z - radius,
            },
            max: Point3D {
                x: point.x + radius,
                y: point.y + radius,
                z: point.z + radius,
            },
        };
        
        // Use R-Tree to find candidate entities
        let candidates = index.rtree.search_within_bounds(&search_bbox);
        
        // Filter by actual distance and create results
        let mut results = Vec::new();
        for entity in candidates {
            let distance = self.calculate_distance(&point, &entity.position);
            if distance <= radius {
                results.push(SpatialQueryResult {
                    entity_name: entity.name.clone(),
                    entity_type: entity.entity_type.clone(),
                    position: crate::core::Position {
                        x: entity.position.x,
                        y: entity.position.y,
                        z: entity.position.z,
                        coordinate_system: "building_local".to_string(),
                    },
                    distance,
                });
            }
        }
        
        // Sort by distance
        results.sort_by(|a, b| a.distance.partial_cmp(&b.distance).unwrap_or(std::cmp::Ordering::Equal));
        
        Ok(results)
    }
    
    /// Query entities within a bounding box using spatial index
    pub fn query_within_bbox(
        &self,
        building_name: &str,
        bbox: BoundingBox3D,
    ) -> Result<Vec<SpatialQueryResult>, Box<dyn std::error::Error + Send + Sync>> {
        let index = self.get_or_build_index(building_name)?;
        
        // Use R-Tree to find entities
        let entities = index.rtree.search_within_bounds(&bbox);
        
        // Convert to results
        let results = entities.into_iter().map(|entity| {
            SpatialQueryResult {
                entity_name: entity.name.clone(),
                entity_type: entity.entity_type.clone(),
                position: crate::core::Position {
                    x: entity.position.x,
                    y: entity.position.y,
                    z: entity.position.z,
                    coordinate_system: "building_local".to_string(),
                },
                distance: 0.0, // Distance not applicable for bbox queries
            }
        }).collect();
        
        Ok(results)
    }
    
    /// Find the nearest entity to a point using spatial index
    pub fn find_nearest(
        &self,
        building_name: &str,
        point: Point3D,
    ) -> Result<Option<SpatialQueryResult>, Box<dyn std::error::Error + Send + Sync>> {
        let index = self.get_or_build_index(building_name)?;
        
        // Start with a small radius and expand if needed
        let mut radius = 10.0;
        
        // Try progressively larger radii until we find at least one entity
        for _ in 0..5 {
            let search_bbox = BoundingBox3D {
                min: Point3D {
                    x: point.x - radius,
                    y: point.y - radius,
                    z: point.z - radius,
                },
                max: Point3D {
                    x: point.x + radius,
                    y: point.y + radius,
                    z: point.z + radius,
                },
            };
            
            let candidates = index.rtree.search_within_bounds(&search_bbox);
            if !candidates.is_empty() {
                // Find the nearest among candidates
                let mut nearest: Option<(SpatialEntity, f64)> = None;
                for entity in candidates {
                    let distance = self.calculate_distance(&point, &entity.position);
                    if nearest.is_none() || distance < nearest.as_ref().unwrap().1 {
                        nearest = Some((entity, distance));
                    }
                }
                
                if let Some((entity, distance)) = nearest {
                    return Ok(Some(SpatialQueryResult {
                        entity_name: entity.name.clone(),
                        entity_type: entity.entity_type.clone(),
                        position: crate::core::Position {
                            x: entity.position.x,
                            y: entity.position.y,
                            z: entity.position.z,
                            coordinate_system: "building_local".to_string(),
                        },
                        distance,
                    }));
                }
            }
            
            radius *= 2.0; // Expand search radius
        }
        
        Ok(None)
    }
    
    /// Extract spatial entities from building data
    fn extract_spatial_entities(&self, building_data: &crate::yaml::BuildingData) -> Vec<SpatialEntity> {
        let mut entities = Vec::new();
        
        for floor in &building_data.floors {
            // Add rooms as spatial entities (rooms are now in wings)
            for wing in &floor.wings {
                for room in &wing.rooms {
                    // Convert core::Position to spatial::Point3D
                    use crate::spatial::Point3D;
                    let position = Point3D {
                        x: room.spatial_properties.position.x,
                        y: room.spatial_properties.position.y,
                        z: room.spatial_properties.position.z,
                    };
                    // Convert core::BoundingBox to spatial::BoundingBox3D
                    use crate::spatial::BoundingBox3D;
                    let bbox = &room.spatial_properties.bounding_box;
                    let bounding_box = BoundingBox3D {
                        min: Point3D {
                            x: bbox.min.x,
                            y: bbox.min.y,
                            z: bbox.min.z,
                        },
                        max: Point3D {
                            x: bbox.max.x,
                            y: bbox.max.y,
                            z: bbox.max.z,
                        },
                    };
                    entities.push(SpatialEntity::new(
                        room.id.clone(),
                        room.name.clone(),
                        "Room".to_string(),
                        position,
                    ).with_bounding_box(bounding_box));
                }
            }
            
            // Add equipment as spatial entities
            for equipment in &floor.equipment {
                // Convert core::Position to spatial::Point3D
                use crate::spatial::Point3D;
                let position = Point3D {
                    x: equipment.position.x,
                    y: equipment.position.y,
                    z: equipment.position.z,
                };
                // Equipment doesn't have a direct bounding_box, so create a default one
                use crate::spatial::BoundingBox3D;
                let bounding_box = BoundingBox3D::new(
                    Point3D::new(position.x - 0.5, position.y - 0.5, position.z - 0.5),
                    Point3D::new(position.x + 0.5, position.y + 0.5, position.z + 0.5),
                );
                entities.push(SpatialEntity::new(
                    equipment.id.clone(),
                    equipment.name.clone(),
                    format!("{:?}", equipment.equipment_type),
                    position,
                ).with_bounding_box(bounding_box));
            }
        }
        
        entities
    }
    
    /// Calculate distance between two points
    fn calculate_distance(&self, p1: &Point3D, p2: &Point3D) -> f64 {
        let dx = p1.x - p2.x;
        let dy = p1.y - p2.y;
        let dz = p1.z - p2.z;
        (dx * dx + dy * dy + dz * dz).sqrt()
    }
}

impl SpatialIndex {
    /// Create a new spatial index from entities
    fn new(entities: Vec<SpatialEntity>) -> Self {
        let rtree = RTreeNode::new(&entities);
        Self { entities, rtree }
    }
}

impl RTreeNode {
    /// Create a new R-Tree node from entities
    fn new(entities: &[SpatialEntity]) -> Self {
        if entities.is_empty() {
            return RTreeNode {
                bounds: BoundingBox3D {
                    min: Point3D { x: 0.0, y: 0.0, z: 0.0 },
                    max: Point3D { x: 0.0, y: 0.0, z: 0.0 },
                },
                children: Vec::new(),
                entities: Vec::new(),
                is_leaf: true,
                max_entities: 10,
            };
        }
        
        // Calculate bounding box for all entities
        let bounds = Self::calculate_bounds(entities);
        
        // Simple implementation: if we have few entities, store them directly
        // For larger sets, we could implement proper R-Tree splitting
        if entities.len() <= 10 {
            RTreeNode {
                bounds,
                children: Vec::new(),
                entities: entities.to_vec(),
                is_leaf: true,
                max_entities: 10,
            }
        } else {
            // For larger sets, create a simple grid-based partitioning
            // This is a simplified R-Tree - a full implementation would use
            // proper splitting algorithms (e.g., quadratic split)
            let mut children = Vec::new();
            let chunk_size = (entities.len() / 4).max(1);
            
            for chunk in entities.chunks(chunk_size) {
                children.push(RTreeNode::new(chunk));
            }
            
            RTreeNode {
                bounds,
                children,
                entities: Vec::new(),
                is_leaf: false,
                max_entities: 10,
            }
        }
    }
    
    /// Calculate bounding box for a set of entities
    fn calculate_bounds(entities: &[SpatialEntity]) -> BoundingBox3D {
        if entities.is_empty() {
            return BoundingBox3D {
                min: Point3D { x: 0.0, y: 0.0, z: 0.0 },
                max: Point3D { x: 0.0, y: 0.0, z: 0.0 },
            };
        }
        
        let mut min_x = f64::INFINITY;
        let mut min_y = f64::INFINITY;
        let mut min_z = f64::INFINITY;
        let mut max_x = f64::NEG_INFINITY;
        let mut max_y = f64::NEG_INFINITY;
        let mut max_z = f64::NEG_INFINITY;
        
        for entity in entities {
            min_x = min_x.min(entity.bounding_box.min.x);
            min_y = min_y.min(entity.bounding_box.min.y);
            min_z = min_z.min(entity.bounding_box.min.z);
            max_x = max_x.max(entity.bounding_box.max.x);
            max_y = max_y.max(entity.bounding_box.max.y);
            max_z = max_z.max(entity.bounding_box.max.z);
        }
        
        BoundingBox3D {
            min: Point3D { x: min_x, y: min_y, z: min_z },
            max: Point3D { x: max_x, y: max_y, z: max_z },
        }
    }
    
    /// Check if this node intersects with a bounding box
    fn intersects(&self, bbox: &BoundingBox3D) -> bool {
        self.bounds.min.x <= bbox.max.x &&
        self.bounds.max.x >= bbox.min.x &&
        self.bounds.min.y <= bbox.max.y &&
        self.bounds.max.y >= bbox.min.y &&
        self.bounds.min.z <= bbox.max.z &&
        self.bounds.max.z >= bbox.min.z
    }
    
    /// Search for entities within a bounding box
    fn search_within_bounds(&self, bbox: &BoundingBox3D) -> Vec<SpatialEntity> {
        let mut results = Vec::new();
        
        if !self.intersects(bbox) {
            return results;
        }
        
        if self.is_leaf {
            // Check each entity in this leaf node
            for entity in &self.entities {
                if Self::entity_intersects_bbox(entity, bbox) {
                    results.push(entity.clone());
                }
            }
        } else {
            // Search child nodes
            for child in &self.children {
                results.extend(child.search_within_bounds(bbox));
            }
        }
        
        results
    }
    
    /// Check if an entity intersects with a bounding box
    fn entity_intersects_bbox(entity: &SpatialEntity, bbox: &BoundingBox3D) -> bool {
        entity.bounding_box.min.x <= bbox.max.x &&
        entity.bounding_box.max.x >= bbox.min.x &&
        entity.bounding_box.min.y <= bbox.max.y &&
        entity.bounding_box.max.y >= bbox.min.y &&
        entity.bounding_box.min.z <= bbox.max.z &&
        entity.bounding_box.max.z >= bbox.min.z
    }
}

impl Default for SpatialService {
    fn default() -> Self {
        Self::with_file_repository()
    }
}

