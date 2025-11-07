//! Type definitions for enhanced IFC parsing

use crate::error::ArxError;
use crate::spatial::{BoundingBox3D, Point3D, SpatialEntity};
use std::collections::HashMap;

/// Types of equipment relationships
#[allow(dead_code)] // Used in relationships module (to be migrated)
#[derive(Debug, Clone, PartialEq)]
pub enum RelationshipType {
    FlowConnection,
    ControlConnection,
    SpatialConnection,
    ElectricalConnection,
    MechanicalConnection,
}

/// Equipment relationship data structure
#[allow(dead_code)] // Used in relationships module (to be migrated)
#[derive(Debug, Clone)]
pub struct EquipmentRelationship {
    pub from_entity_id: String,
    pub to_entity_id: String,
    pub relationship_type: RelationshipType,
    pub connection_type: Option<String>,
    pub properties: Vec<(String, String)>,
}

/// Spatial relationship types for queries
#[derive(Debug, Clone, PartialEq)]
pub enum SpatialRelationship {
    Contains,
    Intersects,
    Adjacent,
    Within,
    Spans,
    Overlaps,
}

/// Geometric conflict types
#[derive(Debug, Clone, PartialEq)]
pub enum ConflictType {
    Overlap,
    InsufficientClearance,
    AccessibilityViolation,
    CodeViolation,
    StructuralInterference,
}

/// Conflict severity levels
#[derive(Debug, Clone, PartialEq)]
pub enum ConflictSeverity {
    Low,
    Medium,
    High,
    Critical,
}

/// Query performance metrics
#[derive(Debug, Clone)]
pub struct QueryPerformanceMetrics {
    pub average_query_time_ms: f64,
    pub spatial_index_size_bytes: usize,
    pub cache_hit_rate: f64,
    pub memory_usage_mb: f64,
    pub total_queries: usize,
    pub query_times: Vec<f64>,
    pub cache_hits: usize,
    pub cache_misses: usize,
}

/// Geometric conflict detection result
#[derive(Debug, Clone)]
pub struct GeometricConflict {
    pub entity1_id: String,
    pub entity2_id: String,
    pub conflict_type: ConflictType,
    pub severity: ConflictSeverity,
    pub intersection_volume: f64,
    pub clearance_distance: f64,
    pub resolution_suggestions: Vec<String>,
}

/// Spatial query types for batch processing
#[derive(Debug, Clone)]
#[allow(dead_code)] // Future use for batch query processing
pub enum QueryType {
    Proximity,
    Intersection,
    Containment,
    SystemSpecific,
    Clustering,
}

/// Query parameters for batch processing
#[derive(Debug, Clone)]
#[allow(dead_code)] // Future use for batch query processing
pub struct QueryParameters {
    pub center: Option<Point3D>,
    pub radius: Option<f64>,
    pub bounding_box: Option<BoundingBox3D>,
    pub system_type: Option<String>,
    pub min_cluster_size: Option<usize>,
}

/// Query priority levels
#[derive(Debug, Clone, PartialEq)]
#[allow(dead_code)] // Future use for batch query processing
pub enum QueryPriority {
    Low,
    Normal,
    High,
    Critical,
}

/// Batch spatial query
#[derive(Debug, Clone)]
#[allow(dead_code)] // Future use for batch query processing
pub struct SpatialQuery {
    pub query_type: QueryType,
    pub parameters: QueryParameters,
    pub priority: QueryPriority,
}

/// Query result with detailed spatial information
#[derive(Debug, Clone, PartialEq)]
pub struct SpatialQueryResult {
    pub entity: SpatialEntity,
    pub distance: f64,
    pub relationship_type: SpatialRelationship,
    pub intersection_points: Vec<Point3D>,
}

/// R-Tree node for spatial indexing
#[derive(Debug, Clone)]
pub struct RTreeNode {
    pub bounds: BoundingBox3D,
    pub children: Vec<RTreeNode>,
    pub entities: Vec<SpatialEntity>,
    pub is_leaf: bool,
    pub max_entities: usize,
}

/// Spatial index with R-Tree for efficient spatial queries
#[derive(Debug, Clone)]
pub struct SpatialIndex {
    pub rtree: RTreeNode,
    pub room_index: HashMap<String, Vec<String>>, // room_id -> equipment_ids
    pub floor_index: HashMap<i32, Vec<String>>,   // floor -> equipment_ids
    pub entity_cache: HashMap<String, SpatialEntity>, // entity_id -> entity
    pub query_times: Vec<f64>,
    pub cache_hits: usize,
    pub cache_misses: usize,
}

/// Statistics about the parsing process
#[derive(Debug, Clone)]
pub struct ParseStats {
    pub successful_entities: usize,
    pub failed_parses: usize,
    pub failed_spatial_extractions: usize,
    pub total_lines: usize,
    pub processing_time_ms: u64,
}

impl ParseStats {
    /// Create new parse statistics
    pub fn new() -> Self {
        Self {
            successful_entities: 0,
            failed_parses: 0,
            failed_spatial_extractions: 0,
            total_lines: 0,
            processing_time_ms: 0,
        }
    }

    /// Calculate success rate
    pub fn success_rate(&self) -> f64 {
        if self.total_lines == 0 {
            0.0
        } else {
            self.successful_entities as f64 / self.total_lines as f64
        }
    }

    /// Calculate error rate
    pub fn error_rate(&self) -> f64 {
        let total_errors = self.failed_parses + self.failed_spatial_extractions;
        if self.total_lines == 0 {
            0.0
        } else {
            total_errors as f64 / self.total_lines as f64
        }
    }

    /// Get processing speed (lines per second)
    pub fn processing_speed(&self) -> f64 {
        if self.processing_time_ms == 0 {
            0.0
        } else {
            self.total_lines as f64 / (self.processing_time_ms as f64 / 1000.0)
        }
    }
}

impl Default for ParseStats {
    fn default() -> Self {
        Self::new()
    }
}

/// Individual IFC entity parsed from file
#[derive(Debug, Clone)]
pub struct IFCEntity {
    pub id: String,
    pub entity_type: String,
    pub parameters: Vec<String>,
    pub line_number: usize,
}

/// Enhanced IFC parser with error recovery capabilities
pub struct EnhancedIFCParser {
    pub(crate) error_threshold: usize,
    pub(crate) continue_on_error: bool,
    pub(crate) collected_errors: Vec<ArxError>,
    pub(crate) parse_stats: ParseStats,
}

/// Result of IFC parsing with error recovery
#[derive(Debug)]
pub struct ParseResult {
    pub building: crate::core::Building,
    pub spatial_entities: Vec<SpatialEntity>,
    pub parse_stats: ParseStats,
    pub errors: Vec<ArxError>,
}
