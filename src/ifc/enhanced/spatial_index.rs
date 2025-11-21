//! Spatial indexing and R-Tree implementation
//!
//! This module provides spatial indexing capabilities using an R-Tree data structure
//! for efficient spatial queries on building information model (BIM) entities.
//!
//! # Current Architecture
//!
//! The spatial index consists of:
//! - **R-Tree**: Hierarchical bounding volume structure for fast spatial queries
//! - **Entity Cache**: Hash map for O(1) entity lookups by ID
//! - **Room Index**: Maps room IDs to contained equipment IDs
//! - **Floor Index**: Maps floor numbers to equipment IDs
//!
//! # Performance Characteristics
//!
//! - **Radius queries**: O(log n) average, O(n) worst case
//! - **Bounding box queries**: O(log n) average, O(n) worst case
//! - **Entity lookup**: O(1) via entity_cache
//! - **Room/Floor queries**: O(1) via specialized indexes
//!
//! # Known Limitations
//!
//! 1. **Flat R-Tree**: Current implementation uses a single-level tree without
//!    hierarchical subdivision. For datasets >1000 entities, this may impact performance.
//!
//! 2. **Entity Cloning**: Entities are cloned into the R-Tree rather than using
//!    references or IDs, which increases memory usage.
//!
//! # Future Improvements
//!
//! - Implement hierarchical R-Tree with configurable branching factor
//! - Use entity IDs in R-Tree with entity_cache for lookups
//! - Add bulk loading algorithm for better tree balance
//! - Implement R*-Tree variant for improved query performance
//! - Add spatial caching for frequently queried regions

use super::types::{
    ConflictSeverity, ConflictType, GeometricConflict, QueryPerformanceMetrics, RTreeNode,
    SpatialIndex, SpatialQueryResult, SpatialRelationship,
};
use crate::error::ArxResult;
use crate::core::spatial::{BoundingBox3D, Point3D};
use crate::core::spatial::{SpatialEntity, Point3D as NalgebraPoint3D};

impl RTreeNode {
    /// Create a new R-Tree node
    ///
    /// # Current Implementation
    ///
    /// Creates a flat (single-level) R-Tree node with calculated bounding box.
    /// The entities vector is intentionally left empty; entities should be added
    /// after construction if building a hierarchical tree.
    ///
    /// # Arguments
    ///
    /// * `entities` - Slice of spatial entities to calculate bounds from
    ///
    /// # Note
    ///
    /// For production use, entities should be explicitly added to the node's
    /// `entities` field after construction. See tests for proper usage pattern.
    pub fn new(entities: &[SpatialEntity]) -> Self {
        if entities.is_empty() {
            return RTreeNode {
                bounds: BoundingBox3D {
                    min: crate::core::spatial::Point3D::new(0.0, 0.0, 0.0),
                    max: crate::core::spatial::Point3D::new(0.0, 0.0, 0.0),
                },
                children: Vec::new(),
                entities: Vec::new(),
                is_leaf: true,
                max_entities: 10,
            };
        }

        // Calculate bounding box for all entities
        let bounds = Self::calculate_bounds(entities);

        RTreeNode {
            bounds,
            children: Vec::new(),
            entities: Vec::new(), // Entities should be added after construction
            is_leaf: true,
            max_entities: 10,
        }
    }

    /// Calculate bounding box for a set of entities
    fn calculate_bounds(entities: &[SpatialEntity]) -> BoundingBox3D {
        if entities.is_empty() {
            return BoundingBox3D {
                min: Point3D::new(0.0, 0.0, 0.0),
                max: Point3D::new(0.0, 0.0, 0.0),
            };
        }

        let mut min_x = f64::INFINITY;
        let mut min_y = f64::INFINITY;
        let mut min_z = f64::INFINITY;
        let mut max_x = f64::NEG_INFINITY;
        let mut max_y = f64::NEG_INFINITY;
        let mut max_z = f64::NEG_INFINITY;

        for entity in entities {
            let bbox = entity.bounding_box();
            min_x = min_x.min(bbox.min.x);
            min_y = min_y.min(bbox.min.y);
            min_z = min_z.min(bbox.min.z);
            max_x = max_x.max(bbox.max.x);
            max_y = max_y.max(bbox.max.y);
            max_z = max_z.max(bbox.max.z);
        }

        BoundingBox3D {
            min: crate::core::spatial::Point3D::new(min_x, min_y, min_z),
            max: crate::core::spatial::Point3D::new(max_x, max_y, max_z),
        }
    }

    /// Check if this node intersects with a bounding box
    pub fn intersects(&self, bbox: &BoundingBox3D) -> bool {
        self.bounds.min.x <= bbox.max.x
            && self.bounds.max.x >= bbox.min.x
            && self.bounds.min.y <= bbox.max.y
            && self.bounds.max.y >= bbox.min.y
            && self.bounds.min.z <= bbox.max.z
            && self.bounds.max.z >= bbox.min.z
    }

    /// Check if this node contains a point
    pub fn contains_point(&self, point: &Point3D) -> bool {
        point.x >= self.bounds.min.x
            && point.x <= self.bounds.max.x
            && point.y >= self.bounds.min.y
            && point.y <= self.bounds.max.y
            && point.z >= self.bounds.min.z
            && point.z <= self.bounds.max.z
    }

    /// Search for entities within a bounding box
    pub fn search_within_bounds(&self, bbox: &BoundingBox3D) -> Vec<&SpatialEntity> {
        let mut results = Vec::new();

        if !self.intersects(bbox) {
            return results;
        }

        if self.is_leaf {
            // Check each entity in this leaf node
            for entity in &self.entities {
                if Self::entity_intersects_bbox(entity, bbox) {
                    results.push(entity);
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
        let entity_bbox = entity.bounding_box();
        entity_bbox.min.x <= bbox.max.x
            && entity_bbox.max.x >= bbox.min.x
            && entity_bbox.min.y <= bbox.max.y
            && entity_bbox.max.y >= bbox.min.y
            && entity_bbox.min.z <= bbox.max.z
            && entity_bbox.max.z >= bbox.min.z
    }
}

impl Default for SpatialIndex {
    fn default() -> Self {
        Self::new()
    }
}

impl SpatialIndex {
    /// Create a new spatial index
    pub fn new() -> Self {
        SpatialIndex {
            rtree: RTreeNode::new(&[]),
            room_index: std::collections::HashMap::new(),
            floor_index: std::collections::HashMap::new(),
            entity_cache: std::collections::HashMap::new(),
            query_times: Vec::new(),
            cache_hits: 0,
            cache_misses: 0,
        }
    }

    /// Find entities within a radius of a point
    pub fn find_within_radius(&self, center: Point3D, radius: f64) -> Vec<SpatialQueryResult> {
        let mut results = Vec::new();

        // Create bounding box for radius search
        let search_bbox = BoundingBox3D {
            min: Point3D::new(
                center.x - radius,
                center.y - radius,
                center.z - radius,
            ),
            max: Point3D::new(
                center.x + radius,
                center.y + radius,
                center.z + radius,
            ),
        };

        // Search R-Tree
        let entities = self.rtree.search_within_bounds(&search_bbox);

        // Filter by actual distance and create results
        for entity in entities {
            let entity_pos = entity.position();
            let core_pos = Point3D::new(entity_pos.x, entity_pos.y, entity_pos.z);
            let distance = self.calculate_distance(&center, &core_pos);
            if distance <= radius {
                results.push(SpatialQueryResult {
                    entity_id: entity.id().to_string(),
                    entity_name: entity.name().to_string(),
                    entity_type: entity.entity_type().to_string(),
                    distance,
                    relationship_type: SpatialRelationship::Within,
                    intersection_points: Vec::new(),
                });
            }
        }

        // Sort by distance
        results.sort_by(|a: &SpatialQueryResult, b: &SpatialQueryResult| {
            a.distance
                .partial_cmp(&b.distance)
                .unwrap_or(std::cmp::Ordering::Equal)
        });
        results
    }

    /// Find entities within a bounding box
    pub fn find_within_bounding_box(&self, bbox: BoundingBox3D) -> Vec<SpatialQueryResult> {
        let entities = self.rtree.search_within_bounds(&bbox);

        entities
            .into_iter()
            .map(|entity| {
                let entity_pos = entity.position();
                let center_pos = Point3D::new(
                    (bbox.min.x + bbox.max.x) / 2.0,
                    (bbox.min.y + bbox.max.y) / 2.0,
                    (bbox.min.z + bbox.max.z) / 2.0,
                );
                let distance = self.calculate_distance(&center_pos, &Point3D::new(entity_pos.x, entity_pos.y, entity_pos.z));

                SpatialQueryResult {
                    entity_id: entity.id().to_string(),
                    entity_name: entity.name().to_string(),
                    entity_type: entity.entity_type().to_string(),
                    distance,
                    relationship_type: SpatialRelationship::Intersects,
                    intersection_points: Vec::new(),
                }
            })
            .collect()
    }

    /// Find entities in a specific room
    pub fn find_in_room(&self, room_id: &str) -> Vec<&SpatialEntity> {
        if let Some(entity_ids) = self.room_index.get(room_id) {
            entity_ids
                .iter()
                .filter_map(|id| self.entity_cache.get(id))
                .collect()
        } else {
            Vec::new()
        }
    }

    /// Find entities on a specific floor
    pub fn find_in_floor(&self, floor: i32) -> Vec<&SpatialEntity> {
        if let Some(entity_ids) = self.floor_index.get(&floor) {
            entity_ids
                .iter()
                .filter_map(|id| self.entity_cache.get(id))
                .collect()
        } else {
            Vec::new()
        }
    }

    /// Find the nearest entity to a point
    pub fn find_nearest(&self, point: Point3D) -> Option<SpatialQueryResult> {
        let mut nearest = None;
        let mut min_distance = f64::INFINITY;

        // Search through all entities in cache
        for entity in self.entity_cache.values() {
            let pos = entity.position();
            let entity_pos = Point3D::new(pos.x, pos.y, pos.z);
            let distance = self.calculate_distance(&point, &entity_pos);
            if distance < min_distance {
                min_distance = distance;
                nearest = Some(SpatialQueryResult {
                    entity_id: entity.id().to_string(),
                    entity_name: entity.name().to_string(),
                    entity_type: entity.entity_type().to_string(),
                    distance,
                    relationship_type: SpatialRelationship::Adjacent,
                    intersection_points: Vec::new(),
                });
            }
        }

        nearest
    }

    /// Calculate distance between two points
    pub fn calculate_distance(&self, point1: &Point3D, point2: &Point3D) -> f64 {
        let dx = point1.x - point2.x;
        let dy = point1.y - point2.y;
        let dz = point1.z - point2.z;
        (dx * dx + dy * dy + dz * dz).sqrt()
    }

    /// Find entities that intersect with a given bounding box
    pub fn find_intersecting(&self, bbox: BoundingBox3D) -> Vec<SpatialQueryResult> {
        let entities = self.rtree.search_within_bounds(&bbox);

        entities
            .into_iter()
            .map(|entity| {
                let intersection_points =
                    self.calculate_intersection_points(entity.bounding_box(), &bbox);
                // Convert core::spatial::Point3D to nalgebra Point3D
                let nalgebra_points: Vec<NalgebraPoint3D> = intersection_points
                    .into_iter()
                    .map(|p| NalgebraPoint3D::new(p.x, p.y, p.z))
                    .collect();
                SpatialQueryResult {
                    entity_id: entity.id().to_string(),
                    entity_name: entity.name().to_string(),
                    entity_type: entity.entity_type().to_string(),
                    distance: 0.0, // Distance not applicable for intersection queries
                    relationship_type: SpatialRelationship::Intersects,
                    intersection_points: nalgebra_points,
                }
            })
            .collect()
    }

    /// Find entities adjacent to a given point (within a small radius)
    pub fn find_adjacent(&self, point: Point3D, max_distance: f64) -> Vec<SpatialQueryResult> {
        self.find_within_radius(point, max_distance)
            .into_iter()
            .map(|mut result| {
                result.relationship_type = SpatialRelationship::Adjacent;
                result
            })
            .collect()
    }

    /// Find entities that contain a given point
    pub fn find_containing(&self, point: Point3D) -> Vec<SpatialQueryResult> {
        let mut results = Vec::new();

        for entity in self.entity_cache.values() {
            if self.point_in_bounding_box(&point, entity.bounding_box()) {
                let pos = entity.position();
                let entity_pos = Point3D::new(pos.x, pos.y, pos.z);
                results.push(SpatialQueryResult {
                    entity_id: entity.id().to_string(),
                    entity_name: entity.name().to_string(),
                    entity_type: entity.entity_type().to_string(),
                    distance: self.calculate_distance(&point, &entity_pos),
                    relationship_type: SpatialRelationship::Contains,
                    intersection_points: vec![NalgebraPoint3D::new(point.x, point.y, point.z)],
                });
            }
        }

        results
    }

    /// Find entities within a specific volume (3D bounding box)
    pub fn find_within_volume(&self, bbox: BoundingBox3D) -> Vec<SpatialQueryResult> {
        let entities = self.rtree.search_within_bounds(&bbox);

        entities
            .into_iter()
            .filter_map(|entity| {
                // Check if entity is fully contained within the volume
                if self.bounding_box_contained(entity.bounding_box(), &bbox) {
                    Some(SpatialQueryResult {
                        entity_id: entity.id().to_string(),
                        entity_name: entity.name().to_string(),
                        entity_type: entity.entity_type().to_string(),
                        distance: 0.0,
                        relationship_type: SpatialRelationship::Within,
                        intersection_points: Vec::new(),
                    })
                } else {
                    None
                }
            })
            .collect()
    }

    /// Find entities that span across multiple floors
    pub fn find_cross_floor_entities(&self, min_floor: i32, max_floor: i32) -> Vec<&SpatialEntity> {
        let mut results = Vec::new();

        for entity in self.entity_cache.values() {
            let entity_floor_min = (entity.bounding_box().min.z / 10.0) as i32;
            let entity_floor_max = (entity.bounding_box().max.z / 10.0) as i32;

            // Check if entity spans across the specified floor range
            if entity_floor_min < min_floor || entity_floor_max > max_floor {
                results.push(entity);
            }
        }

        results
    }

    /// Find equipment by system type within a radius
    pub fn find_equipment_by_system(
        &self,
        system_type: &str,
        center: Point3D,
        radius: f64,
    ) -> Vec<SpatialQueryResult> {
        self.find_within_radius(center, radius)
            .into_iter()
            .filter(|result| {
                result
                    .entity_type
                    .to_uppercase()
                    .contains(&system_type.to_uppercase())
            })
            .collect()
    }

    /// Find equipment clusters (groups of nearby equipment)
    pub fn find_equipment_clusters(
        &self,
        cluster_radius: f64,
        min_cluster_size: usize,
    ) -> Vec<Vec<&SpatialEntity>> {
        let mut clusters = Vec::new();
        let mut processed = std::collections::HashSet::new();

        for entity in self.entity_cache.values() {
            if processed.contains(entity.id()) {
                continue;
            }

            // Find all entities within cluster radius
            let pos = entity.position();
            let center = Point3D::new(pos.x, pos.y, pos.z);
            let nearby_results = self.find_within_radius(center, cluster_radius);

            // Look up entities from cache using result IDs
            let cluster: Vec<&SpatialEntity> = nearby_results
                .iter()
                .filter_map(|result| self.entity_cache.get(&result.entity_id))
                .collect();

            if cluster.len() >= min_cluster_size {
                // Mark all entities in this cluster as processed
                for cluster_entity in &cluster {
                    processed.insert(cluster_entity.id().to_string());
                }
                clusters.push(cluster);
            }
        }

        clusters
    }

    /// Calculate intersection points between two bounding boxes
    fn calculate_intersection_points(
        &self,
        bbox1: &BoundingBox3D,
        bbox2: &BoundingBox3D,
    ) -> Vec<Point3D> {
        let mut points = Vec::new();

        // Calculate intersection bounding box
        let intersection_min = Point3D::new(
            bbox1.min.x.max(bbox2.min.x),
            bbox1.min.y.max(bbox2.min.y),
            bbox1.min.z.max(bbox2.min.z),
        );

        let intersection_max = Point3D::new(
            bbox1.max.x.min(bbox2.max.x),
            bbox1.max.y.min(bbox2.max.y),
            bbox1.max.z.min(bbox2.max.z),
        );

        // Check if there's a valid intersection
        if intersection_min.x <= intersection_max.x
            && intersection_min.y <= intersection_max.y
            && intersection_min.z <= intersection_max.z
        {
            // Add corner points of intersection
            points.push(intersection_min);
            points.push(intersection_max);
            points.push(Point3D::new(
                intersection_min.x,
                intersection_min.y,
                intersection_max.z,
            ));
            points.push(Point3D::new(
                intersection_max.x,
                intersection_min.y,
                intersection_min.z,
            ));
        }

        points
    }

    /// Check if a point is inside a bounding box
    fn point_in_bounding_box(&self, point: &Point3D, bbox: &BoundingBox3D) -> bool {
        point.x >= bbox.min.x
            && point.x <= bbox.max.x
            && point.y >= bbox.min.y
            && point.y <= bbox.max.y
            && point.z >= bbox.min.z
            && point.z <= bbox.max.z
    }

    /// Check if one bounding box is contained within another
    fn bounding_box_contained(&self, inner: &BoundingBox3D, outer: &BoundingBox3D) -> bool {
        inner.min.x >= outer.min.x
            && inner.max.x <= outer.max.x
            && inner.min.y >= outer.min.y
            && inner.max.y <= outer.max.y
            && inner.min.z >= outer.min.z
            && inner.max.z <= outer.max.z
    }

    /// Calculate intersection area between 2D bounding boxes (X-Y plane)
    pub fn calculate_intersection_area(&self, bbox1: &BoundingBox3D, bbox2: &BoundingBox3D) -> f64 {
        let intersection_min_x = bbox1.min.x.max(bbox2.min.x);
        let intersection_max_x = bbox1.max.x.min(bbox2.max.x);
        let intersection_min_y = bbox1.min.y.max(bbox2.min.y);
        let intersection_max_y = bbox1.max.y.min(bbox2.max.y);

        if intersection_min_x <= intersection_max_x && intersection_min_y <= intersection_max_y {
            (intersection_max_x - intersection_min_x) * (intersection_max_y - intersection_min_y)
        } else {
            0.0
        }
    }

    /// Calculate intersection volume between 3D bounding boxes
    pub fn calculate_intersection_volume(
        &self,
        bbox1: &BoundingBox3D,
        bbox2: &BoundingBox3D,
    ) -> f64 {
        let intersection_min_x = bbox1.min.x.max(bbox2.min.x);
        let intersection_max_x = bbox1.max.x.min(bbox2.max.x);
        let intersection_min_y = bbox1.min.y.max(bbox2.min.y);
        let intersection_max_y = bbox1.max.y.min(bbox2.max.y);
        let intersection_min_z = bbox1.min.z.max(bbox2.min.z);
        let intersection_max_z = bbox1.max.z.min(bbox2.max.z);

        if intersection_min_x <= intersection_max_x
            && intersection_min_y <= intersection_max_y
            && intersection_min_z <= intersection_max_z
        {
            (intersection_max_x - intersection_min_x)
                * (intersection_max_y - intersection_min_y)
                * (intersection_max_z - intersection_min_z)
        } else {
            0.0
        }
    }

    /// Calculate overlap percentage between two bounding boxes
    pub fn calculate_overlap_percentage(
        &self,
        bbox1: &BoundingBox3D,
        bbox2: &BoundingBox3D,
    ) -> f64 {
        let intersection_volume = self.calculate_intersection_volume(bbox1, bbox2);
        let union_volume = bbox1.volume() + bbox2.volume() - intersection_volume;

        if union_volume > 0.0 {
            intersection_volume / union_volume
        } else {
            0.0
        }
    }

    /// Analyze spatial relationships between two entities
    pub fn analyze_spatial_relationships(
        &self,
        entity1: &SpatialEntity,
        entity2: &SpatialEntity,
    ) -> SpatialRelationship {
        let bbox1 = entity1.bounding_box();
        let bbox2 = entity2.bounding_box();

        // Check for containment
        if self.bounding_box_contained(bbox1, bbox2) {
            return SpatialRelationship::Contains;
        }
        if self.bounding_box_contained(bbox2, bbox1) {
            return SpatialRelationship::Within;
        }

        // Check for intersection
        if self.calculate_intersection_volume(bbox1, bbox2) > 0.0 {
            return SpatialRelationship::Intersects;
        }

        // Check for adjacency (close but not intersecting)
        let pos1_nalgebra = entity1.position();
        let pos2_nalgebra = entity2.position();
        let pos1 = Point3D::new(pos1_nalgebra.x, pos1_nalgebra.y, pos1_nalgebra.z);
        let pos2 = Point3D::new(pos2_nalgebra.x, pos2_nalgebra.y, pos2_nalgebra.z);
        let distance = self.calculate_distance(&pos1, &pos2);
        let max_dimension = (bbox1.volume().powf(1.0 / 3.0) + bbox2.volume().powf(1.0 / 3.0)) / 2.0;

        if distance <= max_dimension * 2.0 {
            return SpatialRelationship::Adjacent;
        }

        SpatialRelationship::Overlaps
    }

    /// Calculate geometric similarity between two entities
    pub fn calculate_geometric_similarity(
        &self,
        entity1: &SpatialEntity,
        entity2: &SpatialEntity,
    ) -> f64 {
        let volume1 = entity1.bounding_box().volume();
        let volume2 = entity2.bounding_box().volume();

        // Volume similarity
        let volume_similarity = 1.0 - (volume1 - volume2).abs() / (volume1 + volume2).max(1.0);

        // Position similarity
        let pos1_nalgebra = entity1.position();
        let pos2_nalgebra = entity2.position();
        let pos1 = Point3D::new(pos1_nalgebra.x, pos1_nalgebra.y, pos1_nalgebra.z);
        let pos2 = Point3D::new(pos2_nalgebra.x, pos2_nalgebra.y, pos2_nalgebra.z);
        let distance = self.calculate_distance(&pos1, &pos2);
        let max_distance = 100.0; // Maximum expected distance for similarity
        let position_similarity = 1.0 - (distance / max_distance).min(1.0);

        // Shape similarity (aspect ratio)
        let aspect1 = self.calculate_aspect_ratio(entity1.bounding_box());
        let aspect2 = self.calculate_aspect_ratio(entity2.bounding_box());
        let shape_similarity = 1.0 - (aspect1 - aspect2).abs() / (aspect1 + aspect2).max(1.0);

        // Weighted average
        0.4 * volume_similarity + 0.3 * position_similarity + 0.3 * shape_similarity
    }

    /// Detect geometric conflicts between entities
    pub fn detect_geometric_conflicts(&self, entities: &[SpatialEntity]) -> Vec<GeometricConflict> {
        let mut conflicts = Vec::new();

        for i in 0..entities.len() {
            for j in (i + 1)..entities.len() {
                let entity1 = &entities[i];
                let entity2 = &entities[j];

                let intersection_volume = self
                    .calculate_intersection_volume(entity1.bounding_box(), entity2.bounding_box());
                let pos1_nalgebra = entity1.position();
                let pos2_nalgebra = entity2.position();
                let pos1 = Point3D::new(pos1_nalgebra.x, pos1_nalgebra.y, pos1_nalgebra.z);
                let pos2 = Point3D::new(pos2_nalgebra.x, pos2_nalgebra.y, pos2_nalgebra.z);
                let distance = self.calculate_distance(&pos1, &pos2);

                // Check for overlap conflicts
                if intersection_volume > 0.0 {
                    let severity = if intersection_volume > entity1.bounding_box().volume() * 0.5 {
                        ConflictSeverity::Critical
                    } else if intersection_volume > entity1.bounding_box().volume() * 0.1 {
                        ConflictSeverity::High
                    } else {
                        ConflictSeverity::Medium
                    };

                    conflicts.push(GeometricConflict {
                        entity1_id: entity1.id().to_string(),
                        entity2_id: entity2.id().to_string(),
                        conflict_type: ConflictType::Overlap,
                        severity,
                        intersection_volume,
                        clearance_distance: distance,
                        resolution_suggestions: vec![
                            "Relocate one of the entities".to_string(),
                            "Resize one of the entities".to_string(),
                            "Check for design conflicts".to_string(),
                        ],
                    });
                }

                // Check for insufficient clearance
                let min_clearance = self.calculate_minimum_clearance(entity1, entity2);
                if distance < min_clearance {
                    conflicts.push(GeometricConflict {
                        entity1_id: entity1.id().to_string(),
                        entity2_id: entity2.id().to_string(),
                        conflict_type: ConflictType::InsufficientClearance,
                        severity: ConflictSeverity::Medium,
                        intersection_volume: 0.0,
                        clearance_distance: distance,
                        resolution_suggestions: vec![
                            "Increase clearance between entities".to_string(),
                            "Verify maintenance accessibility".to_string(),
                            "Check building code requirements".to_string(),
                        ],
                    });
                }
            }
        }

        conflicts
    }

    /// Calculate aspect ratio of a bounding box
    fn calculate_aspect_ratio(&self, bbox: &BoundingBox3D) -> f64 {
        let width = bbox.max.x - bbox.min.x;
        let height = bbox.max.y - bbox.min.y;
        let depth = bbox.max.z - bbox.min.z;

        let max_dimension = width.max(height).max(depth);
        let min_dimension = width.min(height).min(depth);

        if min_dimension > 0.0 {
            max_dimension / min_dimension
        } else {
            1.0
        }
    }

    /// Calculate minimum clearance required between two entities
    fn calculate_minimum_clearance(&self, entity1: &SpatialEntity, entity2: &SpatialEntity) -> f64 {
        // Base clearance requirements based on entity types
        let base_clearance = match (entity1.entity_type(), entity2.entity_type()) {
            (t1, t2) if t1.contains("ELECTRIC") && t2.contains("ELECTRIC") => 0.3,
            (t1, t2) if t1.contains("FIRE") || t2.contains("FIRE") => 1.0,
            (t1, t2) if t1.contains("HVAC") && t2.contains("HVAC") => 0.5,
            _ => 0.2, // Default clearance
        };

        // Add size-based clearance
        let size_factor =
            (entity1.bounding_box().volume() + entity2.bounding_box().volume()).powf(1.0 / 3.0) * 0.1;

        base_clearance + size_factor
    }

    /// Optimize spatial index for better performance
    pub fn optimize_spatial_index(&mut self) -> ArxResult<()> {
        // Note: R-Tree rebuilding would require ownership of entities
        // Since entities are in the cache, we skip rtree rebuild for now
        // In a full implementation, we'd need to take ownership of the cache temporarily

        // Optimize room and floor indices
        self.room_index.clear();
        self.floor_index.clear();

        for entity in self.entity_cache.values() {
            let room_id = format!("ROOM_{}", entity.name().replace(" ", "_"));
            self.room_index
                .entry(room_id.clone())
                .or_default()
                .push(entity.id().to_string());

            let floor = (entity.position().z / 10.0) as i32;
            self.floor_index
                .entry(floor)
                .or_default()
                .push(entity.id().to_string());
        }

        // Reset performance tracking after optimization
        self.query_times.clear();
        self.cache_hits = 0;
        self.cache_misses = 0;

        Ok(())
    }

    /// Record a query execution time for performance tracking
    pub fn record_query_time(&mut self, query_time_ms: f64) {
        self.query_times.push(query_time_ms);
        // Keep only the last 1000 query times to prevent memory growth
        if self.query_times.len() > 1000 {
            self.query_times.remove(0);
        }
    }

    /// Record a cache hit for performance tracking
    pub fn record_cache_hit(&mut self) {
        self.cache_hits += 1;
    }

    /// Record a cache miss for performance tracking
    pub fn record_cache_miss(&mut self) {
        self.cache_misses += 1;
    }

    /// Calculate query performance metrics
    pub fn calculate_query_performance_metrics(&self) -> QueryPerformanceMetrics {
        let memory_usage = std::mem::size_of_val(self) as f64 / (1024.0 * 1024.0); // MB

        // Calculate average query time from recorded times
        let average_query_time_ms = if !self.query_times.is_empty() {
            self.query_times.iter().sum::<f64>() / self.query_times.len() as f64
        } else {
            0.0
        };

        // Calculate cache hit rate
        let total_cache_requests = self.cache_hits + self.cache_misses;
        let cache_hit_rate = if total_cache_requests > 0 {
            self.cache_hits as f64 / total_cache_requests as f64
        } else {
            0.0
        };

        QueryPerformanceMetrics {
            average_query_time_ms,
            spatial_index_size_bytes: std::mem::size_of_val(&self.rtree),
            cache_hit_rate,
            memory_usage_mb: memory_usage,
            total_queries: self.query_times.len(),
            query_times: self.query_times.clone(),
            cache_hits: self.cache_hits,
            cache_misses: self.cache_misses,
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::collections::HashMap;

    fn create_test_entity(id: &str, name: &str, x: f64, y: f64, z: f64) -> SpatialEntity {
        let position = Point3D::new(x, y, z);
        let bbox = BoundingBox3D::new(
            Point3D::new(x - 0.5, y - 0.5, z - 0.5),
            Point3D::new(x + 0.5, y + 0.5, z + 0.5),
        );

        SpatialEntity::new(
            id.to_string(),
            name.to_string(),
            "TestEntity".to_string(),
            position,
        )
        .with_bounding_box(bbox)
    }

    fn create_test_index() -> SpatialIndex {
        let entities = vec![
            create_test_entity("1", "Entity1", 0.0, 0.0, 0.0),
            create_test_entity("2", "Entity2", 5.0, 0.0, 0.0),
            create_test_entity("3", "Entity3", 10.0, 0.0, 0.0),
            create_test_entity("4", "Entity4", 0.0, 5.0, 0.0),
        ];

        let bounds = RTreeNode::calculate_bounds(&entities);
        let rtree = RTreeNode {
            bounds,
            children: Vec::new(),
            entities: entities.clone(),
            is_leaf: true,
            max_entities: 10,
        };

        let mut entity_cache = HashMap::new();
        for entity in entities {
            entity_cache.insert(entity.id().to_string(), entity);
        }

        SpatialIndex {
            rtree,
            room_index: HashMap::new(),
            floor_index: HashMap::new(),
            entity_cache,
            query_times: Vec::new(),
            cache_hits: 0,
            cache_misses: 0,
        }
    }

    #[test]
    fn test_find_within_radius_returns_results() {
        let index = create_test_index();
        let center = Point3D::new(0.0, 0.0, 0.0);
        let radius = 6.0;

        let results = index.find_within_radius(center, radius);

        // Should find Entity1 (distance 0) and Entity2 (distance 5)
        assert!(
            results.len() >= 2,
            "Expected at least 2 entities within radius 6.0 from origin, got {}",
            results.len()
        );

        // Verify results contain the expected entities
        let entity_ids: Vec<String> = results.iter().map(|r| r.entity_id.clone()).collect();
        assert!(
            entity_ids.contains(&"1".to_string()),
            "Results should contain Entity1"
        );
        assert!(
            entity_ids.contains(&"2".to_string()),
            "Results should contain Entity2"
        );
    }

    #[test]
    fn test_find_within_radius_sorted_by_distance() {
        let index = create_test_index();
        let center = Point3D::new(0.0, 0.0, 0.0);
        let radius = 15.0;

        let results = index.find_within_radius(center, radius);

        // Verify results are sorted by distance
        for i in 1..results.len() {
            assert!(
                results[i - 1].distance <= results[i].distance,
                "Results should be sorted by distance"
            );
        }
    }

    #[test]
    fn test_find_within_bounding_box_returns_results() {
        let index = create_test_index();
        let bbox = BoundingBox3D::new(
            Point3D::new(-1.0, -1.0, -1.0),
            Point3D::new(6.0, 6.0, 6.0),
        );

        let results = index.find_within_bounding_box(bbox);

        // Should find Entity1, Entity2, and Entity4 within this bounding box
        assert!(
            results.len() >= 3,
            "Expected at least 3 entities within bounding box, got {}",
            results.len()
        );

        // Verify entity fields are populated
        for result in &results {
            assert!(!result.entity_id.is_empty(), "Entity ID should be populated");
            assert!(!result.entity_name.is_empty(), "Entity name should be populated");
            assert!(!result.entity_type.is_empty(), "Entity type should be populated");
        }
    }

    #[test]
    fn test_find_within_radius_excludes_distant_entities() {
        let index = create_test_index();
        let center = Point3D::new(0.0, 0.0, 0.0);
        let radius = 3.0;

        let results = index.find_within_radius(center, radius);

        // Should only find Entity1 (distance 0), not Entity2 (distance 5)
        assert_eq!(
            results.len(),
            1,
            "Expected only 1 entity within radius 3.0 from origin"
        );
        assert_eq!(results[0].entity_id, "1", "Should only find Entity1");
    }

    #[test]
    fn test_find_within_radius_with_zero_radius() {
        let index = create_test_index();
        let center = Point3D::new(0.0, 0.0, 0.0);
        let radius = 0.0;

        let results = index.find_within_radius(center, radius);

        // Zero radius should only find entities at exact position
        assert_eq!(
            results.len(),
            1,
            "Zero radius should only find entity at exact center"
        );
        assert_eq!(results[0].entity_id, "1");
        assert_eq!(results[0].distance, 0.0);
    }

    #[test]
    fn test_find_within_radius_with_negative_coordinates() {
        let entities = vec![
            create_test_entity("1", "Entity1", -10.0, -5.0, -3.0),
            create_test_entity("2", "Entity2", -5.0, -5.0, -3.0),
            create_test_entity("3", "Entity3", 0.0, 0.0, 0.0),
        ];

        let bounds = RTreeNode::calculate_bounds(&entities);
        let rtree = RTreeNode {
            bounds,
            children: Vec::new(),
            entities: entities.clone(),
            is_leaf: true,
            max_entities: 10,
        };

        let mut entity_cache = HashMap::new();
        for entity in entities {
            entity_cache.insert(entity.id().to_string(), entity);
        }

        let index = SpatialIndex {
            rtree,
            room_index: HashMap::new(),
            floor_index: HashMap::new(),
            entity_cache,
            query_times: Vec::new(),
            cache_hits: 0,
            cache_misses: 0,
        };

        let center = Point3D::new(-10.0, -5.0, -3.0);
        let radius = 6.0;

        let results = index.find_within_radius(center, radius);

        // Should find Entity1 (distance 0) and Entity2 (distance 5)
        assert!(results.len() >= 2, "Should find entities with negative coordinates");
    }

    #[test]
    fn test_find_within_bounding_box_with_empty_box() {
        let index = create_test_index();

        // Zero-size bounding box
        let bbox = BoundingBox3D::new(
            Point3D::new(100.0, 100.0, 100.0),
            Point3D::new(100.0, 100.0, 100.0),
        );

        let results = index.find_within_bounding_box(bbox);

        // No entities should be within a point-sized box far from all entities
        assert_eq!(results.len(), 0, "Empty box far from entities should return no results");
    }

    #[test]
    fn test_find_within_bounding_box_large_box() {
        let index = create_test_index();

        // Very large bounding box that contains all entities
        let bbox = BoundingBox3D::new(
            Point3D::new(-100.0, -100.0, -100.0),
            Point3D::new(100.0, 100.0, 100.0),
        );

        let results = index.find_within_bounding_box(bbox);

        // Should find all 4 entities
        assert_eq!(results.len(), 4, "Large box should contain all entities");
    }

    #[test]
    fn test_find_within_radius_exact_boundary() {
        let index = create_test_index();
        let center = Point3D::new(0.0, 0.0, 0.0);

        // Exact distance to Entity2 is 5.0
        let radius = 5.0;

        let results = index.find_within_radius(center, radius);

        // Should include Entity2 at exact boundary (<=)
        assert!(
            results.len() >= 2,
            "Boundary distance should be inclusive"
        );

        let entity_ids: Vec<String> = results.iter().map(|r| r.entity_id.clone()).collect();
        assert!(
            entity_ids.contains(&"2".to_string()),
            "Should include entity at exact boundary distance"
        );
    }

    #[test]
    fn test_spatial_query_result_fields_populated() {
        let index = create_test_index();
        let center = Point3D::new(0.0, 0.0, 0.0);
        let radius = 10.0;

        let results = index.find_within_radius(center, radius);

        // Verify all fields are properly populated
        for result in &results {
            assert!(!result.entity_id.is_empty(), "Entity ID should be populated");
            assert!(!result.entity_name.is_empty(), "Entity name should be populated");
            assert!(!result.entity_type.is_empty(), "Entity type should be populated");
            assert!(result.distance >= 0.0, "Distance should be non-negative");
            assert_eq!(
                result.relationship_type,
                SpatialRelationship::Within,
                "Relationship type should be Within for radius queries"
            );
        }
    }

    #[test]
    fn test_find_within_bounding_box_relationship_type() {
        let index = create_test_index();
        let bbox = BoundingBox3D::new(
            Point3D::new(-1.0, -1.0, -1.0),
            Point3D::new(6.0, 6.0, 6.0),
        );

        let results = index.find_within_bounding_box(bbox);

        // Verify relationship type for bounding box queries
        for result in &results {
            assert_eq!(
                result.relationship_type,
                SpatialRelationship::Intersects,
                "Relationship type should be Intersects for bbox queries"
            );
        }
    }

    #[test]
    fn test_calculate_distance_accuracy() {
        let index = create_test_index();

        let p1 = Point3D::new(0.0, 0.0, 0.0);
        let p2 = Point3D::new(3.0, 4.0, 0.0);

        let distance = index.calculate_distance(&p1, &p2);

        // 3-4-5 triangle: distance should be 5.0
        assert!((distance - 5.0).abs() < 0.0001, "Distance calculation should be accurate");
    }

    // Performance tests
    #[test]
    fn test_find_within_radius_performance() {
        use std::time::Instant;

        // Create larger test dataset
        let mut entities = Vec::new();
        for i in 0..100 {
            let x = (i % 10) as f64 * 10.0;
            let y = (i / 10) as f64 * 10.0;
            entities.push(create_test_entity(
                &format!("entity_{}", i),
                &format!("Entity{}", i),
                x,
                y,
                0.0,
            ));
        }

        let bounds = RTreeNode::calculate_bounds(&entities);
        let rtree = RTreeNode {
            bounds,
            children: Vec::new(),
            entities: entities.clone(),
            is_leaf: true,
            max_entities: 100,
        };

        let mut entity_cache = HashMap::new();
        for entity in entities {
            entity_cache.insert(entity.id().to_string(), entity);
        }

        let index = SpatialIndex {
            rtree,
            room_index: HashMap::new(),
            floor_index: HashMap::new(),
            entity_cache,
            query_times: Vec::new(),
            cache_hits: 0,
            cache_misses: 0,
        };

        let center = Point3D::new(50.0, 50.0, 0.0);
        let radius = 30.0;

        let start = Instant::now();
        let results = index.find_within_radius(center, radius);
        let duration = start.elapsed();

        // Query should complete in under 10ms for 100 entities
        assert!(
            duration.as_millis() < 10,
            "Radius query should complete quickly, took {:?}",
            duration
        );
        assert!(!results.is_empty(), "Should find entities within radius");
    }

    #[test]
    fn test_find_within_bounding_box_performance() {
        use std::time::Instant;

        // Create larger test dataset
        let mut entities = Vec::new();
        for i in 0..100 {
            let x = (i % 10) as f64 * 10.0;
            let y = (i / 10) as f64 * 10.0;
            entities.push(create_test_entity(
                &format!("entity_{}", i),
                &format!("Entity{}", i),
                x,
                y,
                0.0,
            ));
        }

        let bounds = RTreeNode::calculate_bounds(&entities);
        let rtree = RTreeNode {
            bounds,
            children: Vec::new(),
            entities: entities.clone(),
            is_leaf: true,
            max_entities: 100,
        };

        let mut entity_cache = HashMap::new();
        for entity in entities {
            entity_cache.insert(entity.id().to_string(), entity);
        }

        let index = SpatialIndex {
            rtree,
            room_index: HashMap::new(),
            floor_index: HashMap::new(),
            entity_cache,
            query_times: Vec::new(),
            cache_hits: 0,
            cache_misses: 0,
        };

        let bbox = BoundingBox3D::new(
            Point3D::new(20.0, 20.0, -10.0),
            Point3D::new(70.0, 70.0, 10.0),
        );

        let start = Instant::now();
        let results = index.find_within_bounding_box(bbox);
        let duration = start.elapsed();

        // Query should complete in under 10ms for 100 entities
        assert!(
            duration.as_millis() < 10,
            "Bounding box query should complete quickly, took {:?}",
            duration
        );
        assert!(!results.is_empty(), "Should find entities within bounding box");
    }

    #[test]
    fn test_multiple_queries_performance() {
        use std::time::Instant;

        let index = create_test_index();

        let start = Instant::now();

        // Perform 1000 queries
        for i in 0..1000 {
            let x = (i % 20) as f64;
            let y = (i / 20) as f64;
            let center = Point3D::new(x, y, 0.0);
            let _results = index.find_within_radius(center, 5.0);
        }

        let duration = start.elapsed();

        // 1000 queries should complete in under 100ms
        assert!(
            duration.as_millis() < 100,
            "1000 queries should complete quickly, took {:?}",
            duration
        );
    }

    #[test]
    fn test_distance_calculation_performance() {
        use std::time::Instant;

        let index = create_test_index();

        let start = Instant::now();

        // Calculate distance 10000 times
        for i in 0..10000 {
            let x = (i % 100) as f64;
            let y = (i / 100) as f64;
            let p1 = Point3D::new(0.0, 0.0, 0.0);
            let p2 = Point3D::new(x, y, 0.0);
            let _distance = index.calculate_distance(&p1, &p2);
        }

        let duration = start.elapsed();

        // 10000 distance calculations should complete in under 10ms
        assert!(
            duration.as_millis() < 10,
            "10000 distance calculations should be fast, took {:?}",
            duration
        );
    }
}
