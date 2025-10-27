//! Enhanced IFC parser with partial parsing and error recovery

use crate::core::Building;
use crate::spatial::{SpatialEntity, CoordinateSystem, Point3D, BoundingBox3D};
use crate::progress::ProgressContext;
use crate::error::{ArxError, ArxResult};
use log::{info, warn};
use std::fs::File;
use std::io::Write;
use std::collections::HashMap;

/// Types of equipment relationships
#[derive(Debug, Clone, PartialEq)]
pub enum RelationshipType {
    FlowConnection,
    ControlConnection,
    SpatialConnection,
    ElectricalConnection,
    MechanicalConnection,
}

/// Equipment relationship data structure
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

/// Enhanced IFC parser with error recovery capabilities
pub struct EnhancedIFCParser {
    error_threshold: usize,
    continue_on_error: bool,
    collected_errors: Vec<ArxError>,
    parse_stats: ParseStats,
}

/// Result of IFC parsing with error recovery
#[derive(Debug)]
pub struct ParseResult {
    pub building: Building,
    pub spatial_entities: Vec<SpatialEntity>,
    pub parse_stats: ParseStats,
    pub errors: Vec<ArxError>,
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

/// Individual IFC entity parsed from file
#[derive(Debug, Clone)]
pub struct IFCEntity {
    pub id: String,
    pub entity_type: String,
    pub parameters: Vec<String>,
    pub line_number: usize,
}

impl EnhancedIFCParser {
    /// Create a new enhanced IFC parser
    pub fn new() -> Self {
        Self {
            error_threshold: 10, // Stop after 10 errors
            continue_on_error: true,
            collected_errors: Vec::new(),
            parse_stats: ParseStats::new(),
        }
    }
    
    /// Create parser with custom error threshold
    pub fn with_error_threshold(mut self, threshold: usize) -> Self {
        self.error_threshold = threshold;
        self
    }
    
    /// Enable or disable continuing on errors
    pub fn with_error_continuation(mut self, continue_on_error: bool) -> Self {
        self.continue_on_error = continue_on_error;
        self
    }
    
    /// Parse IFC file with partial parsing and error recovery
    pub fn parse_with_recovery(&mut self, file_path: &str) -> ArxResult<ParseResult> {
        let start_time = std::time::Instant::now();
        
        info!("Starting enhanced IFC parsing with error recovery: {}", file_path);
        
        // Read file content with error handling
        let content = self.read_file_safely(file_path)?;
        let lines: Vec<&str> = content.lines().collect();
        self.parse_stats.total_lines = lines.len();
        
        info!("Processing {} lines with error recovery", lines.len());
        
        let mut building = Building::default();
        let mut spatial_entities = Vec::new();
        
        // Parse entities with error recovery
        for (line_num, line) in lines.iter().enumerate() {
            if self.collected_errors.len() >= self.error_threshold {
                warn!("Error threshold reached ({}), stopping parsing", self.error_threshold);
                break;
            }
            
            match self.parse_entity_line_safe(line, line_num) {
                Ok(Some(entity)) => {
                    self.parse_stats.successful_entities += 1;
                    
                    // Try to extract building information
                    if self.is_building_entity(&entity.entity_type) {
                        if let Some(building_name) = self.extract_building_name(&entity) {
                            building = Building::new(entity.id.clone(), building_name);
                        }
                    }
                    
                    // Try to extract spatial data
                    if self.is_spatial_entity(&entity.entity_type) {
                        match self.extract_spatial_data_safe(&entity) {
                            Ok(Some(spatial_entity)) => {
                                spatial_entities.push(spatial_entity);
                            }
                            Ok(None) => {
                                // No spatial data extracted, continue
                            }
                            Err(e) => {
                                self.parse_stats.failed_spatial_extractions += 1;
                                warn!("Failed to extract spatial data for entity {}: {}", entity.id, e);
                                self.collected_errors.push(e);
                            }
                        }
                    }
                }
                Ok(None) => {
                    // Not an entity line, continue
                }
                Err(e) => {
                    self.parse_stats.failed_parses += 1;
                    warn!("Failed to parse line {}: {}", line_num + 1, e);
                    self.collected_errors.push(e);
                }
            }
        }
        
        self.parse_stats.processing_time_ms = start_time.elapsed().as_millis() as u64;
        
        let result = ParseResult {
            building,
            spatial_entities,
            parse_stats: self.parse_stats.clone(),
            errors: std::mem::take(&mut self.collected_errors),
        };
        
        info!("Parsing completed: {} entities, {} errors, {:.1}% success rate", 
              result.parse_stats.successful_entities,
              result.errors.len(),
              result.parse_stats.success_rate() * 100.0);
        
        Ok(result)
    }
    
    /// Parse IFC file with progress reporting and error recovery
    pub fn parse_with_progress_and_recovery(&mut self, file_path: &str, progress: ProgressContext) -> ArxResult<ParseResult> {
        let start_time = std::time::Instant::now();
        
        progress.update(10, "Reading IFC file...");
        
        // Read file content with error handling
        let content = self.read_file_safely(file_path)?;
        let lines: Vec<&str> = content.lines().collect();
        self.parse_stats.total_lines = lines.len();
        
        progress.update(20, "Parsing entities with error recovery...");
        
        let mut building = Building::default();
        let mut spatial_entities = Vec::new();
        
        // Parse entities with error recovery and progress updates
        for (line_num, line) in lines.iter().enumerate() {
            if self.collected_errors.len() >= self.error_threshold {
                warn!("Error threshold reached ({}), stopping parsing", self.error_threshold);
                break;
            }
            
            // Update progress every 100 lines
            if line_num % 100 == 0 {
                let progress_percent = 20 + ((line_num as f64 / lines.len() as f64) * 70.0) as u32;
                progress.update(progress_percent, &format!("Processing line {}/{}", line_num + 1, lines.len()));
            }
            
            match self.parse_entity_line_safe(line, line_num) {
                Ok(Some(entity)) => {
                    self.parse_stats.successful_entities += 1;
                    
                    // Try to extract building information
                    if self.is_building_entity(&entity.entity_type) {
                        if let Some(building_name) = self.extract_building_name(&entity) {
                            building = Building::new(entity.id.clone(), building_name);
                        }
                    }
                    
                    // Try to extract spatial data
                    if self.is_spatial_entity(&entity.entity_type) {
                        match self.extract_spatial_data_safe(&entity) {
                            Ok(Some(spatial_entity)) => {
                                spatial_entities.push(spatial_entity);
                            }
                            Ok(None) => {
                                // No spatial data extracted, continue
                            }
                            Err(e) => {
                                self.parse_stats.failed_spatial_extractions += 1;
                                self.collected_errors.push(e);
                            }
                        }
                    }
                }
                Ok(None) => {
                    // Not an entity line, continue
                }
                Err(e) => {
                    self.parse_stats.failed_parses += 1;
                    self.collected_errors.push(e);
                }
            }
        }
        
        progress.update(90, "Finalizing results...");
        
        self.parse_stats.processing_time_ms = start_time.elapsed().as_millis() as u64;
        
        let result = ParseResult {
            building,
            spatial_entities,
            parse_stats: self.parse_stats.clone(),
            errors: std::mem::take(&mut self.collected_errors),
        };
        
        progress.update(100, "Parsing completed");
        
        info!("Parsing with progress completed: {} entities, {} errors, {:.1}% success rate", 
              result.parse_stats.successful_entities,
              result.errors.len(),
              result.parse_stats.success_rate() * 100.0);
        
        Ok(result)
    }
    
    /// Safely read file content with comprehensive error handling
    fn read_file_safely(&self, file_path: &str) -> ArxResult<String> {
        use std::fs;
        use std::path::Path;
        
        // Check if file exists
        if !Path::new(file_path).exists() {
            return Err(ArxError::io_error("IFC file not found")
                .with_file_path(file_path)
                .with_suggestions(vec![
                    "Check if the file path is correct".to_string(),
                    "Verify the file exists and is accessible".to_string(),
                ])
                .with_recovery(vec![
                    "Use absolute path instead of relative path".to_string(),
                    "Check file permissions".to_string(),
                ]));
        }
        
        // Check file extension
        if !file_path.to_lowercase().ends_with(".ifc") {
            warn!("File does not have .ifc extension: {}", file_path);
        }
        
        // Read file content
        match fs::read_to_string(file_path) {
            Ok(content) => {
                if content.is_empty() {
                    return Err(ArxError::io_error("IFC file is empty")
                        .with_file_path(file_path)
                        .with_suggestions(vec![
                            "Check if the file was properly exported".to_string(),
                            "Verify the file is not corrupted".to_string(),
                        ])
                        .with_recovery(vec![
                            "Re-export the IFC file from your BIM software".to_string(),
                            "Check file size and integrity".to_string(),
                        ]));
                }
                Ok(content)
            }
            Err(e) => {
                Err(ArxError::io_error("Failed to read IFC file")
                    .with_file_path(file_path)
                    .with_debug_info(format!("IO Error: {}", e))
                    .with_suggestions(vec![
                        "Check file permissions".to_string(),
                        "Verify the file is not locked by another process".to_string(),
                    ])
                    .with_recovery(vec![
                        "Run with appropriate permissions".to_string(),
                        "Close any applications using the file".to_string(),
                    ]))
            }
        }
    }
    
    /// Safely parse an entity line with error recovery
    fn parse_entity_line_safe(&self, line: &str, line_num: usize) -> ArxResult<Option<IFCEntity>> {
        if !line.starts_with("#") || !line.contains("=") {
            return Ok(None);
        }
        
        // Try to parse the entity
        match self.parse_entity_line(line) {
            Some(entity) => Ok(Some(entity)),
            None => {
                // Log the parsing failure but continue
                Err(ArxError::ifc_processing("Failed to parse entity line")
                    .with_file_path("IFC file")
                    .with_line_number(line_num + 1)
                    .with_debug_info(format!("Line content: {}", line))
                    .with_suggestions(vec![
                        "Check IFC file format compliance".to_string(),
                        "Verify entity syntax is correct".to_string(),
                    ])
                    .with_recovery(vec![
                        "Skipping malformed line".to_string(),
                        "Continuing with next entity".to_string(),
                    ]))
            }
        }
    }
    
    /// Parse a single entity line
    fn parse_entity_line(&self, line: &str) -> Option<IFCEntity> {
        // Remove leading # and trailing ;
        let line = line.trim_start_matches('#').trim_end_matches(';');
        
        // Split by = to get ID and parameters
        let parts: Vec<&str> = line.splitn(2, '=').collect();
        if parts.len() != 2 {
            return None;
        }
        
        let id = parts[0].trim().to_string();
        let param_str = parts[1].trim();
        
        // Parse IFC entity format: ENTITYTYPE(param1,param2,...)
        let entity_type = if param_str.contains('(') {
            // Extract entity type before the first parenthesis
            param_str.split('(').next().unwrap_or("").trim().to_string()
        } else {
            // No parameters, just entity type
            param_str.to_string()
        };
        
        // Parse parameters (everything inside parentheses)
        let parameters = if param_str.contains('(') && param_str.contains(')') {
            let start = param_str.find('(').unwrap() + 1;
            let end = param_str.rfind(')').unwrap();
            let param_content = &param_str[start..end];
            
            // Split by comma, but be careful with quoted strings
            let mut params = Vec::new();
            let mut current_param = String::new();
            let mut in_quotes = false;
            let mut quote_char = '\0';
            
            for ch in param_content.chars() {
                match ch {
                    '\'' | '"' => {
                        if !in_quotes {
                            in_quotes = true;
                            quote_char = ch;
                        } else if ch == quote_char {
                            in_quotes = false;
                        }
                        current_param.push(ch);
                    }
                    ',' => {
                        if !in_quotes {
                            params.push(current_param.trim().to_string());
                            current_param.clear();
                        } else {
                            current_param.push(ch);
                        }
                    }
                    _ => current_param.push(ch),
                }
            }
            
            if !current_param.is_empty() {
                params.push(current_param.trim().to_string());
            }
            
            params
        } else {
            vec![param_str.to_string()]
        };
        
        if parameters.is_empty() {
            return None;
        }
        
        Some(IFCEntity {
            id,
            entity_type,
            parameters,
            line_number: 0, // Will be set by caller
        })
    }
    
    /// Check if entity type is a building entity
    fn is_building_entity(&self, entity_type: &str) -> bool {
        matches!(entity_type.to_uppercase().as_str(), "IFCBUILDING" | "IFCSITE" | "IFCPROJECT")
    }
    
    /// Check if entity type is a spatial entity
    fn is_spatial_entity(&self, entity_type: &str) -> bool {
        matches!(entity_type.to_uppercase().as_str(), 
                 // Building spaces
                 "IFCSPACE" | "IFCROOM" | "IFCZONE" | 
                 // Structural elements
                 "IFCWALL" | "IFCDOOR" | "IFCWINDOW" | "IFCCOLUMN" | "IFCSLAB" | "IFCBEAM" |
                 // HVAC equipment
                 "IFCFLOWTERMINAL" | "IFCFLOWFITTING" | "IFCFLOWSEGMENT" | "IFCFLOWCONTROLLER" |
                 "IFCAIRTERMINAL" | "IFCDUCTFITTING" | "IFCDUCTSEGMENT" | "IFCAIRHANDLINGUNIT" |
                 "IFCFAN" | "IFCPUMP" | "IFCBOILER" | "IFCCHILLER" | "IFCCOOLINGTOWER" |
                 // Electrical equipment
                 "IFCDISTRIBUTIONELEMENT" | "IFCELECTRICDISTRIBUTIONBOARD" | "IFCELECTRICMOTOR" |
                 "IFCLIGHTFIXTURE" | "IFCSWITCHINGDEVICE" | "IFCELECTRICGENERATOR" |
                 // Plumbing equipment
                 "IFCPIPE" | "IFCPIPEFITTING" | "IFCPIPESEGMENT" | "IFCTANK" | "IFCJUNCTIONBOX" |
                 // Fire safety equipment
                 "IFCFIREALARM" | "IFCFIREDETECTOR" | "IFCFIREEXTINGUISHER" | "IFCFIREPUMP" |
                 // Security equipment
                 "IFCSECURITYDEVICE" | "IFCCAMERA" | "IFCACCESSDEVICE" |
                 // Other building equipment
                 "IFCELEVATOR" | "IFCESCALATOR" | "IFCMOVINGWALKWAY" | "IFCCRANE" | "IFCLIFTINGDEVICE")
    }
    
    /// Check if entity type represents a building storey (floor)
    fn is_storey_entity(&self, entity_type: &str) -> bool {
        matches!(entity_type.to_uppercase().as_str(),
            "IFCBUILDINGSTOREY" | "IFCBUILDINGFLOOR" | "IFCLEVEL"
        )
    }
    
    /// Check if entity type represents equipment (non-structural)
    fn is_equipment_entity(&self, entity_type: &str) -> bool {
        matches!(entity_type.to_uppercase().as_str(),
            "IFCFLOWTERMINAL" | "IFCAIRTERMINAL" | "IFCLIGHTFIXTURE" |
            "IFCDISTRIBUTIONELEMENT" | "IFCFAN" | "IFCPUMP" | "IFCFIREALARM" |
            "IFCFIREDETECTOR" | "IFCSWITCHINGDEVICE" | "IFCELEVATOR" | "IFCESCALATOR"
        )
    }
    
    /// Extract building name from entity
    fn extract_building_name(&self, entity: &IFCEntity) -> Option<String> {
        if entity.parameters.len() > 1 {
            Some(entity.parameters[1].clone())
        } else {
            None
        }
    }
    
    /// Safely extract spatial data from entity
    fn extract_spatial_data_safe(&self, entity: &IFCEntity) -> ArxResult<Option<SpatialEntity>> {
        match self.extract_spatial_data(entity) {
            Ok(spatial_entity) => Ok(Some(spatial_entity)),
            Err(e) => {
                warn!("Failed to extract spatial data for entity {}: {}", entity.id, e);
                Err(ArxError::spatial_data("Failed to extract spatial data")
                    .with_file_path("IFC file")
                    .with_line_number(entity.line_number)
                    .with_debug_info(format!("Entity: {} ({})", entity.id, entity.entity_type))
                    .with_suggestions(vec![
                        "Check if entity has valid placement data".to_string(),
                        "Verify coordinate system is properly defined".to_string(),
                    ])
                    .with_recovery(vec![
                        "Skipping entity with invalid spatial data".to_string(),
                        "Continuing with next entity".to_string(),
                    ]))
            }
        }
    }
    
    /// Extract spatial data from entity (enhanced implementation)
    fn extract_spatial_data(&self, entity: &IFCEntity) -> Result<SpatialEntity, Box<dyn std::error::Error>> {
        // Parse placement and geometry data from IFC entity
        let position = self.parse_entity_placement(entity)?;
        let bounding_box = self.calculate_entity_bounds(entity, &position)?;
        
        Ok(SpatialEntity {
            id: entity.id.clone(),
            name: entity.id.clone(), // Use ID as name since name field doesn't exist
            entity_type: entity.entity_type.clone(),
            position,
            bounding_box,
            coordinate_system: Some(crate::spatial::types::CoordinateSystem::new(
                "IFC_COORDINATE_SYSTEM".to_string(),
                crate::spatial::types::Point3D::origin()
            )),
        })
    }
    
    /// Parse entity placement from IFC data
    fn parse_entity_placement(&self, entity: &IFCEntity) -> Result<Point3D, Box<dyn std::error::Error>> {
        // Try to extract placement information from entity parameters
        if let Some(placement_data) = entity.parameters.get(0) {
            return self.parse_placement_data(placement_data);
        }
        
        // Try to extract from geometry data
        if let Some(geometry_data) = entity.parameters.get(1) {
            return self.parse_geometry_placement(geometry_data);
        }
        
        // Fallback to deterministic positioning based on entity type
        self.generate_deterministic_position(entity)
    }
    
    /// Parse placement data from IFC ObjectPlacement (enhanced)
    fn parse_placement_data(&self, placement_data: &str) -> Result<Point3D, Box<dyn std::error::Error>> {
        // Handle different IFC placement formats
        
        // 1. Direct coordinate format: (1.0, 2.0, 3.0)
        if placement_data.starts_with('(') && placement_data.ends_with(')') {
            return self.parse_direct_coordinates(placement_data);
        }
        
        // 2. Reference format: #12345 (reference to another entity)
        if placement_data.starts_with('#') {
            return self.parse_placement_reference(placement_data);
        }
        
        // 3. IFCLOCALPLACEMENT format: IFCLOCALPLACEMENT(#12346,#12347)
        if placement_data.contains("IFCLOCALPLACEMENT") {
            return self.parse_local_placement(placement_data);
        }
        
        // 4. IFCAXIS2PLACEMENT3D format: IFCAXIS2PLACEMENT3D(#12346,#12347,#12348)
        if placement_data.contains("IFCAXIS2PLACEMENT3D") {
            return self.parse_axis2_placement_3d(placement_data);
        }
        
        // 5. Try to parse as direct coordinates without parentheses
        if let Ok(coords) = self.parse_coordinate_string(placement_data) {
            return Ok(coords);
        }
        
        Err(format!("Unsupported placement data format: {}", placement_data).into())
    }
    
    /// Parse direct coordinate format: (x, y, z)
    fn parse_direct_coordinates(&self, coord_str: &str) -> Result<Point3D, Box<dyn std::error::Error>> {
        let coords_str = coord_str.trim_start_matches('(').trim_end_matches(')');
                let coords: Vec<&str> = coords_str.split(',').collect();
                
                if coords.len() >= 3 {
                    let x = coords[0].trim().parse::<f64>().unwrap_or(0.0);
                    let y = coords[1].trim().parse::<f64>().unwrap_or(0.0);
                    let z = coords[2].trim().parse::<f64>().unwrap_or(0.0);
                    return Ok(Point3D::new(x, y, z));
                }
        
        Err("Invalid coordinate format".into())
    }
    
    /// Parse placement reference: #12345
    fn parse_placement_reference(&self, ref_str: &str) -> Result<Point3D, Box<dyn std::error::Error>> {
        // For now, return origin - in a full implementation, we would resolve the reference
        // This would require maintaining a reference table during parsing
        warn!("Placement reference not resolved: {}", ref_str);
        Ok(Point3D::origin())
    }
    
    /// Parse IFCLOCALPLACEMENT: IFCLOCALPLACEMENT(#12346,#12347)
    fn parse_local_placement(&self, placement_str: &str) -> Result<Point3D, Box<dyn std::error::Error>> {
        // Extract parameters from IFCLOCALPLACEMENT(#ref1,#ref2)
        if let Some(start) = placement_str.find('(') {
            if let Some(end) = placement_str.find(')') {
                let params_str = &placement_str[start+1..end];
                let params: Vec<&str> = params_str.split(',').collect();
                
                // First parameter is usually the location (IFCCARTESIANPOINT)
                if let Some(location_ref) = params.get(0) {
                    return self.parse_placement_reference(location_ref.trim());
                }
            }
        }
        
        Err("Invalid IFCLOCALPLACEMENT format".into())
    }
    
    /// Parse IFCAXIS2PLACEMENT3D: IFCAXIS2PLACEMENT3D(#ref1,#ref2,#ref3)
    fn parse_axis2_placement_3d(&self, placement_str: &str) -> Result<Point3D, Box<dyn std::error::Error>> {
        // Extract parameters from IFCAXIS2PLACEMENT3D(#location,#axis,#ref_direction)
        if let Some(start) = placement_str.find('(') {
            if let Some(end) = placement_str.find(')') {
                let params_str = &placement_str[start+1..end];
                let params: Vec<&str> = params_str.split(',').collect();
                
                // First parameter is the location (IFCCARTESIANPOINT)
                if let Some(location_ref) = params.get(0) {
                    return self.parse_placement_reference(location_ref.trim());
                }
            }
        }
        
        Err("Invalid IFCAXIS2PLACEMENT3D format".into())
    }
    
    /// Parse coordinate string without parentheses
    fn parse_coordinate_string(&self, coord_str: &str) -> Result<Point3D, Box<dyn std::error::Error>> {
        let coords: Vec<&str> = coord_str.split(',').collect();
        
        if coords.len() >= 3 {
            let x = coords[0].trim().parse::<f64>().unwrap_or(0.0);
            let y = coords[1].trim().parse::<f64>().unwrap_or(0.0);
            let z = coords[2].trim().parse::<f64>().unwrap_or(0.0);
            return Ok(Point3D::new(x, y, z));
        }
        
        Err("Invalid coordinate string format".into())
    }
    
    /// Parse geometry placement from IFC Representation (enhanced)
    fn parse_geometry_placement(&self, geometry_data: &str) -> Result<Point3D, Box<dyn std::error::Error>> {
        // Handle different IFC geometry formats
        
        // 1. Try to parse as placement reference first
        if geometry_data.starts_with('#') {
            return self.parse_placement_reference(geometry_data);
        }
        
        // 2. Try to parse as IFCSHAPEREPRESENTATION or similar
        if geometry_data.contains("IFCSHAPEREPRESENTATION") || 
           geometry_data.contains("IFCGEOMETRICREPRESENTATIONCONTEXT") {
            return self.parse_shape_representation(geometry_data);
        }
        
        // 3. Try to extract coordinates from geometry data
        let coordinates = self.extract_coordinates_from_geometry(geometry_data)?;
        
        if coordinates.len() >= 3 {
            // Calculate centroid of all coordinates
            let mut x_sum = 0.0;
            let mut y_sum = 0.0;
            let mut z_sum = 0.0;
            
            for coord in &coordinates {
                x_sum += coord.x;
                y_sum += coord.y;
                z_sum += coord.z;
            }
            
            let count = coordinates.len() as f64;
            Ok(Point3D::new(
                x_sum / count,
                y_sum / count,
                z_sum / count,
            ))
        } else {
            Err("Insufficient coordinates found in geometry data".into())
        }
    }
    
    /// Parse IFCSHAPEREPRESENTATION or similar geometry representation
    fn parse_shape_representation(&self, shape_data: &str) -> Result<Point3D, Box<dyn std::error::Error>> {
        // Extract parameters from shape representation
        if let Some(start) = shape_data.find('(') {
            if let Some(end) = shape_data.find(')') {
                let params_str = &shape_data[start+1..end];
                let params: Vec<&str> = params_str.split(',').collect();
                
                // Look for coordinate references in parameters
                for param in params {
                    let param = param.trim();
                    if param.starts_with('#') {
                        // Try to resolve the reference
                        return self.parse_placement_reference(param);
                    }
                }
            }
        }
        
        Err("No valid geometry reference found".into())
    }
    
    /// Extract coordinates from geometry data string
    fn extract_coordinates_from_geometry(&self, geometry_data: &str) -> Result<Vec<Point3D>, Box<dyn std::error::Error>> {
        let mut coordinates = Vec::new();
        
        // Split by common IFC delimiters and whitespace
        let tokens: Vec<&str> = geometry_data.split(|c| c == ',' || c == ' ' || c == '\t' || c == '\n')
            .filter(|s| !s.is_empty())
            .collect();
        
        let mut i = 0;
        while i + 2 < tokens.len() {
            // Try to parse three consecutive tokens as coordinates
            if let (Ok(x), Ok(y), Ok(z)) = (
                tokens[i].parse::<f64>(),
                tokens[i + 1].parse::<f64>(),
                tokens[i + 2].parse::<f64>()
            ) {
                coordinates.push(Point3D::new(x, y, z));
                i += 3;
            } else {
                i += 1;
            }
        }
        
        if coordinates.is_empty() {
            Err("No valid coordinates found in geometry data".into())
        } else {
            Ok(coordinates)
        }
    }
    
    // ============================================================================
    // IFC WRITING CAPABILITIES - Terminal 3D → IFC Sync
    // ============================================================================
    
    /// Helper function to handle IO errors consistently
    fn write_line(&self, file: &mut File, line: &str) -> ArxResult<()> {
        writeln!(file, "{}", line)
            .map_err(|e| ArxError::io_error("Failed to write IFC data").with_debug_info(format!("IO Error: {}", e)))
    }
    
    // ============================================================================
    // COORDINATE SYSTEM TRANSFORMATIONS
    // ============================================================================
    
    /// Transform a point from one coordinate system to another
    pub fn transform_point(&self, point: &Point3D, from_system: &CoordinateSystem, to_system: &CoordinateSystem) -> Point3D {
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
    pub fn parse_coordinate_system(&self, entity_data: &str) -> Result<CoordinateSystem, Box<dyn std::error::Error>> {
        // Handle different IFC coordinate system formats
        
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
        Ok(CoordinateSystem::new("DEFAULT".to_string(), Point3D::origin()))
    }
    
    /// Parse IFCCARTESIANPOINT coordinate system
    fn parse_cartesian_point_system(&self, data: &str) -> Result<CoordinateSystem, Box<dyn std::error::Error>> {
        // Extract coordinates from IFCCARTESIANPOINT((x,y,z))
        // Need to find the nested parentheses: IFCCARTESIANPOINT((x,y,z))
        if let Some(start) = data.find("((") {
            if let Some(end) = data.find("))") {
                let coords_str = &data[start+2..end]; // Skip the double opening parentheses
                let coords: Vec<&str> = coords_str.split(',').collect();
                
                if coords.len() >= 3 {
                    let x = coords[0].trim().parse::<f64>().unwrap_or(0.0);
                    let y = coords[1].trim().parse::<f64>().unwrap_or(0.0);
                    let z = coords[2].trim().parse::<f64>().unwrap_or(0.0);
                    
                    return Ok(CoordinateSystem::new(
                        "CARTESIAN".to_string(),
                        Point3D::new(x, y, z)
                    ));
                }
            }
        }
        
        Err("Invalid IFCCARTESIANPOINT format".into())
    }
    
    /// Parse IFCAXIS2PLACEMENT3D coordinate system
    fn parse_axis2_placement_system(&self, data: &str) -> Result<CoordinateSystem, Box<dyn std::error::Error>> {
        // Extract location from IFCAXIS2PLACEMENT3D(#location,#axis,#ref_direction)
        if let Some(start) = data.find('(') {
            if let Some(end) = data.find(')') {
                let params_str = &data[start+1..end];
                let params: Vec<&str> = params_str.split(',').collect();
                
                // First parameter is the location reference
                if let Some(location_ref) = params.get(0) {
                    let _location_ref = location_ref.trim();
                    
                    // For now, return a coordinate system with origin
                    // In a full implementation, we would resolve the reference
                    return Ok(CoordinateSystem::new(
                        "AXIS2_PLACEMENT".to_string(),
                        Point3D::origin()
                    ));
                }
            }
        }
        
        Err("Invalid IFCAXIS2PLACEMENT3D format".into())
    }
    
    /// Parse IFCLOCALPLACEMENT coordinate system
    fn parse_local_placement_system(&self, data: &str) -> Result<CoordinateSystem, Box<dyn std::error::Error>> {
        // Extract placement from IFCLOCALPLACEMENT(#relative_placement,#placement)
        if let Some(start) = data.find('(') {
            if let Some(end) = data.find(')') {
                let params_str = &data[start+1..end];
                let params: Vec<&str> = params_str.split(',').collect();
                
                // Second parameter is usually the placement
                if let Some(placement_ref) = params.get(1) {
                    let _placement_ref = placement_ref.trim();
                    
                    // For now, return a coordinate system with origin
                    // In a full implementation, we would resolve the reference
                    return Ok(CoordinateSystem::new(
                        "LOCAL_PLACEMENT".to_string(),
                        Point3D::origin()
                    ));
                }
            }
        }
        
        Err("Invalid IFCLOCALPLACEMENT format".into())
    }
    
    /// Convert between different IFC coordinate systems
    pub fn convert_coordinate_system(&self, point: &Point3D, from_system_name: &str, to_system_name: &str) -> Result<Point3D, Box<dyn std::error::Error>> {
        // Create coordinate systems based on names
        let from_system = self.create_coordinate_system_by_name(from_system_name)?;
        let to_system = self.create_coordinate_system_by_name(to_system_name)?;
        
        // Transform the point
        Ok(self.transform_point(point, &from_system, &to_system))
    }
    
    /// Create coordinate system by name
    fn create_coordinate_system_by_name(&self, name: &str) -> Result<CoordinateSystem, Box<dyn std::error::Error>> {
        match name.to_uppercase().as_str() {
            "IFC_COORDINATE_SYSTEM" | "GLOBAL" => {
                Ok(CoordinateSystem::new("GLOBAL".to_string(), Point3D::origin()))
            },
            "BUILDING_COORDINATE_SYSTEM" | "BUILDING" => {
                Ok(CoordinateSystem::new("BUILDING".to_string(), Point3D::new(0.0, 0.0, 0.0)))
            },
            "FLOOR_COORDINATE_SYSTEM" | "FLOOR" => {
                Ok(CoordinateSystem::new("FLOOR".to_string(), Point3D::new(0.0, 0.0, 0.0)))
            },
            "ROOM_COORDINATE_SYSTEM" | "ROOM" => {
                Ok(CoordinateSystem::new("ROOM".to_string(), Point3D::new(0.0, 0.0, 0.0)))
            },
            _ => {
                Err(format!("Unknown coordinate system: {}", name).into())
            }
        }
    }
    
    /// Normalize coordinates to a standard coordinate system
    pub fn normalize_coordinates(&self, entities: &mut [SpatialEntity], target_system: &str) -> ArxResult<()> {
        let target_coord_system = self.create_coordinate_system_by_name(target_system)
            .map_err(|e| ArxError::spatial_data("Failed to create target coordinate system")
                .with_debug_info(format!("Error: {}", e)))?;
        
        for entity in entities.iter_mut() {
            if let Some(ref current_system) = entity.coordinate_system {
                // Transform entity position to target coordinate system
                entity.position = self.transform_point(&entity.position, current_system, &target_coord_system);
                
                // Update coordinate system reference
                entity.coordinate_system = Some(target_coord_system.clone());
            }
        }
        
        info!("Normalized {} entities to coordinate system: {}", entities.len(), target_system);
        Ok(())
    }
    
    // ============================================================================
    // EQUIPMENT RELATIONSHIP PARSING
    // ============================================================================
    
    /// Parse equipment relationships from IFC data
    pub fn parse_equipment_relationships(&self, entities: &[SpatialEntity]) -> Vec<EquipmentRelationship> {
        let mut relationships = Vec::new();
        
        for entity in entities {
            // Parse different types of relationships based on entity type
            match entity.entity_type.as_str() {
                "IFCDUCTSEGMENT" | "IFCPIPESEGMENT" => {
                    self.parse_flow_segment_relationships(entity, &mut relationships);
                },
                "IFCDUCTFITTING" | "IFCPIPEFITTING" => {
                    self.parse_fitting_relationships(entity, &mut relationships);
                },
                "IFCFLOWTERMINAL" | "IFCAIRTERMINAL" => {
                    self.parse_terminal_relationships(entity, &mut relationships);
                },
                "IFCFLOWCONTROLLER" => {
                    self.parse_controller_relationships(entity, &mut relationships);
                },
                _ => {
                    // For other equipment types, look for generic connections
                    self.parse_generic_relationships(entity, &mut relationships);
                }
            }
        }
        
        info!("Parsed {} equipment relationships", relationships.len());
        relationships
    }
    
    /// Parse flow segment relationships (ducts, pipes)
    fn parse_flow_segment_relationships(&self, entity: &SpatialEntity, relationships: &mut Vec<EquipmentRelationship>) {
        // Flow segments typically connect to fittings and other segments
        // For now, we'll create proximity-based relationships
        // In a full implementation, we would parse IFC connection data
        
        // Create relationship to nearby equipment
        let relationship = EquipmentRelationship {
            from_entity_id: entity.id.clone(),
            to_entity_id: format!("{}_CONNECTION", entity.id),
            relationship_type: RelationshipType::FlowConnection,
            connection_type: Some("DUCT_SEGMENT".to_string()),
            properties: vec![
                ("length".to_string(), "estimated".to_string()),
                ("diameter".to_string(), "standard".to_string()),
            ],
        };
        
        relationships.push(relationship);
    }
    
    /// Parse fitting relationships (elbows, tees, reducers)
    fn parse_fitting_relationships(&self, entity: &SpatialEntity, relationships: &mut Vec<EquipmentRelationship>) {
        // Fittings connect multiple flow segments
        let relationship = EquipmentRelationship {
            from_entity_id: entity.id.clone(),
            to_entity_id: format!("{}_INLET", entity.id),
            relationship_type: RelationshipType::FlowConnection,
            connection_type: Some("FITTING".to_string()),
            properties: vec![
                ("fitting_type".to_string(), "elbow".to_string()),
                ("angle".to_string(), "90_degrees".to_string()),
            ],
        };
        
        relationships.push(relationship);
        
        // Add outlet connection
        let outlet_relationship = EquipmentRelationship {
            from_entity_id: entity.id.clone(),
            to_entity_id: format!("{}_OUTLET", entity.id),
            relationship_type: RelationshipType::FlowConnection,
            connection_type: Some("FITTING".to_string()),
            properties: vec![
                ("fitting_type".to_string(), "elbow".to_string()),
                ("angle".to_string(), "90_degrees".to_string()),
            ],
        };
        
        relationships.push(outlet_relationship);
    }
    
    /// Parse terminal relationships (air terminals, outlets)
    fn parse_terminal_relationships(&self, entity: &SpatialEntity, relationships: &mut Vec<EquipmentRelationship>) {
        // Terminals connect to supply/return systems
        let relationship = EquipmentRelationship {
            from_entity_id: entity.id.clone(),
            to_entity_id: format!("{}_SUPPLY", entity.id),
            relationship_type: RelationshipType::FlowConnection,
            connection_type: Some("TERMINAL".to_string()),
            properties: vec![
                ("flow_rate".to_string(), "variable".to_string()),
                ("pressure".to_string(), "low".to_string()),
            ],
        };
        
        relationships.push(relationship);
    }
    
    /// Parse controller relationships (valves, dampers)
    fn parse_controller_relationships(&self, entity: &SpatialEntity, relationships: &mut Vec<EquipmentRelationship>) {
        // Controllers regulate flow in systems
        let relationship = EquipmentRelationship {
            from_entity_id: entity.id.clone(),
            to_entity_id: format!("{}_CONTROL", entity.id),
            relationship_type: RelationshipType::ControlConnection,
            connection_type: Some("CONTROLLER".to_string()),
            properties: vec![
                ("control_type".to_string(), "modulating".to_string()),
                ("position".to_string(), "variable".to_string()),
            ],
        };
        
        relationships.push(relationship);
    }
    
    /// Parse generic equipment relationships
    fn parse_generic_relationships(&self, entity: &SpatialEntity, relationships: &mut Vec<EquipmentRelationship>) {
        // For generic equipment, create spatial relationships
        let relationship = EquipmentRelationship {
            from_entity_id: entity.id.clone(),
            to_entity_id: format!("{}_SPATIAL", entity.id),
            relationship_type: RelationshipType::SpatialConnection,
            connection_type: Some("GENERIC".to_string()),
            properties: vec![
                ("spatial_type".to_string(), "proximity".to_string()),
                ("distance".to_string(), "calculated".to_string()),
            ],
        };
        
        relationships.push(relationship);
    }
    
    /// Find equipment connected to a specific entity
    pub fn find_connected_equipment<'a>(&self, entity_id: &str, relationships: &'a [EquipmentRelationship]) -> Vec<&'a EquipmentRelationship> {
        relationships.iter()
            .filter(|rel| rel.from_entity_id == entity_id || rel.to_entity_id == entity_id)
            .collect()
    }
    
    /// Get equipment network (all connected equipment)
    pub fn get_equipment_network(&self, start_entity_id: &str, relationships: &[EquipmentRelationship]) -> Vec<String> {
        let mut network = Vec::new();
        let mut visited = std::collections::HashSet::new();
        let mut to_visit = vec![start_entity_id.to_string()];
        
        while let Some(current_id) = to_visit.pop() {
            if visited.contains(&current_id) {
                continue;
            }
            
            visited.insert(current_id.clone());
            network.push(current_id.clone());
            
            // Find all connected equipment
            for rel in relationships {
                if rel.from_entity_id == current_id && !visited.contains(&rel.to_entity_id) {
                    to_visit.push(rel.to_entity_id.clone());
                } else if rel.to_entity_id == current_id && !visited.contains(&rel.from_entity_id) {
                    to_visit.push(rel.from_entity_id.clone());
                }
            }
        }
        
        network
    }
    
    /// Calculate equipment system efficiency
    pub fn calculate_system_efficiency(&self, relationships: &[EquipmentRelationship]) -> f64 {
        let total_relationships = relationships.len() as f64;
        if total_relationships == 0.0 {
            return 0.0;
        }
        
        // Count different types of connections
        let flow_connections = relationships.iter()
            .filter(|rel| rel.relationship_type == RelationshipType::FlowConnection)
            .count() as f64;
        
        let control_connections = relationships.iter()
            .filter(|rel| rel.relationship_type == RelationshipType::ControlConnection)
            .count() as f64;
        
        // Calculate efficiency based on connection types
        let flow_efficiency = flow_connections / total_relationships;
        let control_efficiency = control_connections / total_relationships;
        
        // Weighted average (flow connections are more important)
        0.7 * flow_efficiency + 0.3 * control_efficiency
    }
    
    /// Build spatial index from spatial entities
    pub fn build_spatial_index(&self, entities: &[SpatialEntity]) -> SpatialIndex {
        let mut room_index = HashMap::new();
        let mut floor_index = HashMap::new();
        let mut entity_cache = HashMap::new();
        
        // Build room and floor indices
        for entity in entities {
            entity_cache.insert(entity.id.clone(), entity.clone());
            
            // For now, we'll use the entity name as room identifier
            // This will be enhanced when we have proper room/floor data
            let room_id = format!("ROOM_{}", entity.name.replace(" ", "_"));
            room_index.entry(room_id.clone())
                .or_insert_with(Vec::new)
                .push(entity.id.clone());
            
            // For now, use a default floor based on Z coordinate
            let floor = (entity.position.z / 10.0) as i32;
            floor_index.entry(floor)
                .or_insert_with(Vec::new)
                .push(entity.id.clone());
        }
        
        // Build R-Tree
        let rtree = RTreeNode::new(entities);
        
        SpatialIndex {
            rtree,
            room_index,
            floor_index,
            entity_cache,
            query_times: Vec::new(),
            cache_hits: 0,
            cache_misses: 0,
        }
    }
    
    /// Write IFC entities from SpatialEntity data (for terminal 3D → IFC sync)
    pub fn write_spatial_entities_to_ifc(&self, entities: &[SpatialEntity], output_path: &str) -> ArxResult<()> {
        
        let mut file = File::create(output_path)
            .map_err(|e| ArxError::io_error("Failed to create IFC output file")
                .with_file_path(output_path)
                .with_debug_info(format!("IO Error: {}", e)))?;
        
        // Write IFC header
        self.write_ifc_header(&mut file)?;
        
        // Write coordinate system definitions
        self.write_coordinate_systems(&mut file)?;
        
        // Write spatial entities
        for entity in entities {
            self.write_spatial_entity(&mut file, entity)?;
        }
        
        // Write IFC footer
        self.write_ifc_footer(&mut file)?;
        
        info!("Successfully wrote {} spatial entities to IFC file: {}", entities.len(), output_path);
        Ok(())
    }
    
    /// Write IFC file header
    fn write_ifc_header(&self, file: &mut File) -> ArxResult<()> {
        self.write_line(file, "ISO-10303-21;")?;
        self.write_line(file, "HEADER;")?;
        self.write_line(file, "FILE_DESCRIPTION(('ArxOS Generated IFC File'),'2;1');")?;
        self.write_line(file, "FILE_NAME('arxos_generated.ifc','2024-01-01T00:00:00',('ArxOS'),('ArxOS Terminal 3D Sync'),'ArxOS','ArxOS','');")?;
        self.write_line(file, "FILE_SCHEMA(('IFC4'));")?;
        self.write_line(file, "ENDSEC;")?;
        self.write_line(file, "")?;
        self.write_line(file, "DATA;")?;
        Ok(())
    }
    
    /// Write coordinate system definitions
    fn write_coordinate_systems(&self, file: &mut File) -> ArxResult<()> {
        // Write global coordinate system
        self.write_line(file, "#1=IFCCARTESIANPOINT((0.,0.,0.));")?;
        self.write_line(file, "#2=IFCDIRECTION((0.,0.,1.));")?;
        self.write_line(file, "#3=IFCDIRECTION((1.,0.,0.));")?;
        self.write_line(file, "#4=IFCAXIS2PLACEMENT3D(#1,#2,#3);")?;
        self.write_line(file, "#5=IFCLOCALPLACEMENT($,#4);")?;
        self.write_line(file, "")?;
        Ok(())
    }
    
    /// Write a single spatial entity to IFC format
    fn write_spatial_entity(&self, file: &mut File, entity: &SpatialEntity) -> ArxResult<()> {
        // Generate unique ID for this entity
        let entity_id = self.generate_entity_id(&entity.id);
        
        // Write coordinate point
        let point_id = entity_id + 1;
        self.write_line(file, &format!("#{}={}(({:.3},{:.3},{:.3}));", 
                 point_id, "IFCCARTESIANPOINT", 
                 entity.position.x, entity.position.y, entity.position.z))?;
        
        // Write local placement
        let placement_id = entity_id + 2;
        self.write_line(file, &format!("#{}={}(#{});", 
                 placement_id, "IFCLOCALPLACEMENT", point_id))?;
        
        // Write entity based on type
        match entity.entity_type.as_str() {
            "IFCSPACE" => self.write_ifc_space(file, entity, entity_id, placement_id)?,
            "IFCROOM" => self.write_ifc_room(file, entity, entity_id, placement_id)?,
            "IFCAIRTERMINAL" => self.write_ifc_air_terminal(file, entity, entity_id, placement_id)?,
            "IFCLIGHTFIXTURE" => self.write_ifc_light_fixture(file, entity, entity_id, placement_id)?,
            "IFCFAN" => self.write_ifc_fan(file, entity, entity_id, placement_id)?,
            "IFCPUMP" => self.write_ifc_pump(file, entity, entity_id, placement_id)?,
            _ => self.write_generic_equipment(file, entity, entity_id, placement_id)?,
        }
        
        self.write_line(file, "")?;
        Ok(())
    }
    
    /// Generate unique entity ID from string hash
    fn generate_entity_id(&self, id_str: &str) -> u32 {
        let hash = self.hash_string(id_str);
        (hash % 1000000) as u32 + 1000 // Start from 1000 to avoid conflicts
    }
    
    /// Write IFCSPACE entity
    fn write_ifc_space(&self, file: &mut File, entity: &SpatialEntity, entity_id: u32, placement_id: u32) -> ArxResult<()> {
        self.write_line(file, &format!("#{}={}('{}','{}',$,#{});", 
                 entity_id, "IFCSPACE", entity.id, entity.name, placement_id))?;
        Ok(())
    }
    
    /// Write IFCROOM entity
    fn write_ifc_room(&self, file: &mut File, entity: &SpatialEntity, entity_id: u32, placement_id: u32) -> ArxResult<()> {
        self.write_line(file, &format!("#{}={}('{}','{}',$,#{});", 
                 entity_id, "IFCROOM", entity.id, entity.name, placement_id))?;
        Ok(())
    }
    
    /// Write IFCAIRTERMINAL entity
    fn write_ifc_air_terminal(&self, file: &mut File, entity: &SpatialEntity, entity_id: u32, placement_id: u32) -> ArxResult<()> {
        self.write_line(file, &format!("#{}={}('{}','{}',$,#{});", 
                 entity_id, "IFCAIRTERMINAL", entity.id, entity.name, placement_id))?;
        Ok(())
    }
    
    /// Write IFCLIGHTFIXTURE entity
    fn write_ifc_light_fixture(&self, file: &mut File, entity: &SpatialEntity, entity_id: u32, placement_id: u32) -> ArxResult<()> {
        self.write_line(file, &format!("#{}={}('{}','{}',$,#{});", 
                 entity_id, "IFCLIGHTFIXTURE", entity.id, entity.name, placement_id))?;
        Ok(())
    }
    
    /// Write IFCFAN entity
    fn write_ifc_fan(&self, file: &mut File, entity: &SpatialEntity, entity_id: u32, placement_id: u32) -> ArxResult<()> {
        self.write_line(file, &format!("#{}={}('{}','{}',$,#{});", 
                 entity_id, "IFCFAN", entity.id, entity.name, placement_id))?;
        Ok(())
    }
    
    /// Write IFCPUMP entity
    fn write_ifc_pump(&self, file: &mut File, entity: &SpatialEntity, entity_id: u32, placement_id: u32) -> ArxResult<()> {
        self.write_line(file, &format!("#{}={}('{}','{}',$,#{});", 
                 entity_id, "IFCPUMP", entity.id, entity.name, placement_id))?;
        Ok(())
    }
    
    /// Write generic equipment entity
    fn write_generic_equipment(&self, file: &mut File, entity: &SpatialEntity, entity_id: u32, placement_id: u32) -> ArxResult<()> {
        self.write_line(file, &format!("#{}={}('{}','{}',$,#{});", 
                 entity_id, "IFCDISTRIBUTIONELEMENT", entity.id, entity.name, placement_id))?;
        Ok(())
    }
    
    /// Write IFC file footer
    fn write_ifc_footer(&self, file: &mut File) -> ArxResult<()> {
        self.write_line(file, "ENDSEC;")?;
        self.write_line(file, "END-ISO-10303-21;")?;
        Ok(())
    }
    
    /// Generate deterministic position based on entity properties
    fn generate_deterministic_position(&self, entity: &IFCEntity) -> Result<Point3D, Box<dyn std::error::Error>> {
        // Use entity ID hash for deterministic positioning
        let id_hash = self.hash_string(&entity.id);
        let name_hash = self.hash_string(&entity.id);
        
        // Generate coordinates based on entity type and properties
        let position = match entity.entity_type.as_str() {
            // Building spaces
            "IFCSPACE" | "IFCROOM" | "IFCZONE" => {
                // Spaces are distributed across floors
                let floor_height = 3.0; // Standard floor height
                let floor = (id_hash % 5) as f64; // 0-4 floors
                Point3D::new(
                    (id_hash % 1000) as f64 / 10.0, // X: 0-100m
                    (name_hash % 800) as f64 / 10.0, // Y: 0-80m  
                    floor * floor_height + 0.1,     // Z: Floor level
                )
            },
            
            // Structural elements
            "IFCWALL" => {
                // Walls span across spaces
                let floor_height = 3.0;
                let floor = (id_hash % 5) as f64;
                Point3D::new(
                    (id_hash % 1000) as f64 / 10.0,
                    (name_hash % 800) as f64 / 10.0,
                    floor * floor_height + 1.5, // Wall center height
                )
            },
            "IFCDOOR" => {
                // Doors are typically at floor level
                let floor_height = 3.0;
                let floor = (id_hash % 5) as f64;
                Point3D::new(
                    (id_hash % 1000) as f64 / 10.0,
                    (name_hash % 800) as f64 / 10.0,
                    floor * floor_height + 0.9, // Door handle height
                )
            },
            "IFCWINDOW" => {
                // Windows are typically above floor level
                let floor_height = 3.0;
                let floor = (id_hash % 5) as f64;
                Point3D::new(
                    (id_hash % 1000) as f64 / 10.0,
                    (name_hash % 800) as f64 / 10.0,
                    floor * floor_height + 1.2, // Window sill height
                )
            },
            "IFCCOLUMN" => {
                // Columns span floor to ceiling
                let floor_height = 3.0;
                let floor = (id_hash % 5) as f64;
                Point3D::new(
                    (id_hash % 1000) as f64 / 10.0,
                    (name_hash % 800) as f64 / 10.0,
                    floor * floor_height + 1.5, // Column center height
                )
            },
            "IFCSLAB" => {
                // Slabs are at floor level
                let floor_height = 3.0;
                let floor = (id_hash % 5) as f64;
                Point3D::new(
                    (id_hash % 1000) as f64 / 10.0,
                    (name_hash % 800) as f64 / 10.0,
                    floor * floor_height, // Floor level
                )
            },
            "IFCBEAM" => {
                // Beams are typically at ceiling level
                let floor_height = 3.0;
                let floor = (id_hash % 5) as f64;
                Point3D::new(
                    (id_hash % 1000) as f64 / 10.0,
                    (name_hash % 800) as f64 / 10.0,
                    floor * floor_height + 2.7, // Near ceiling
                )
            },
            
            // HVAC equipment
            "IFCFLOWTERMINAL" | "IFCAIRTERMINAL" => {
                // Flow terminals are typically wall-mounted
                let floor_height = 3.0;
                let floor = (id_hash % 5) as f64;
                Point3D::new(
                    (id_hash % 1000) as f64 / 10.0,
                    (name_hash % 800) as f64 / 10.0,
                    floor * floor_height + 1.5, // Wall-mounted height
                )
            },
            "IFCFLOWFITTING" | "IFCDUCTFITTING" | "IFCPIPEFITTING" => {
                // Fittings are typically at ceiling level
                let floor_height = 3.0;
                let floor = (id_hash % 5) as f64;
                Point3D::new(
                    (id_hash % 1000) as f64 / 10.0,
                    (name_hash % 800) as f64 / 10.0,
                    floor * floor_height + 2.5, // Near ceiling
                )
            },
            "IFCFLOWSEGMENT" | "IFCDUCTSEGMENT" | "IFCPIPESEGMENT" => {
                // Segments run horizontally
                let floor_height = 3.0;
                let floor = (id_hash % 5) as f64;
                Point3D::new(
                    (id_hash % 1000) as f64 / 10.0,
                    (name_hash % 800) as f64 / 10.0,
                    floor * floor_height + 2.3, // Above ceiling
                )
            },
            "IFCFLOWCONTROLLER" => {
                // Controllers (valves, dampers) are typically wall-mounted
                let floor_height = 3.0;
                let floor = (id_hash % 5) as f64;
                Point3D::new(
                    (id_hash % 1000) as f64 / 10.0,
                    (name_hash % 800) as f64 / 10.0,
                    floor * floor_height + 1.2, // Wall-mounted height
                )
            },
            "IFCAIRHANDLINGUNIT" | "IFCBOILER" | "IFCCHILLER" | "IFCCOOLINGTOWER" => {
                // Large HVAC equipment is typically in mechanical rooms
                let floor_height = 3.0;
                let floor = (id_hash % 5) as f64;
                Point3D::new(
                    (id_hash % 1000) as f64 / 10.0,
                    (name_hash % 800) as f64 / 10.0,
                    floor * floor_height + 0.5, // Floor-mounted
                )
            },
            "IFCFAN" | "IFCPUMP" => {
                // Fans and pumps are typically floor-mounted
                let floor_height = 3.0;
                let floor = (id_hash % 5) as f64;
                Point3D::new(
                    (id_hash % 1000) as f64 / 10.0,
                    (name_hash % 800) as f64 / 10.0,
                    floor * floor_height + 0.3, // Floor-mounted
                )
            },
            
            // Electrical equipment
            "IFCDISTRIBUTIONELEMENT" | "IFCELECTRICDISTRIBUTIONBOARD" => {
                // Electrical panels are typically wall-mounted
                let floor_height = 3.0;
                let floor = (id_hash % 5) as f64;
                Point3D::new(
                    (id_hash % 1000) as f64 / 10.0,
                    (name_hash % 800) as f64 / 10.0,
                    floor * floor_height + 1.4, // Panel height
                )
            },
            "IFCLIGHTFIXTURE" => {
                // Light fixtures are typically ceiling-mounted
                let floor_height = 3.0;
                let floor = (id_hash % 5) as f64;
                Point3D::new(
                    (id_hash % 1000) as f64 / 10.0,
                    (name_hash % 800) as f64 / 10.0,
                    floor * floor_height + 2.8, // Near ceiling
                )
            },
            "IFCELECTRICMOTOR" | "IFCELECTRICGENERATOR" => {
                // Motors and generators are typically floor-mounted
                let floor_height = 3.0;
                let floor = (id_hash % 5) as f64;
                Point3D::new(
                    (id_hash % 1000) as f64 / 10.0,
                    (name_hash % 800) as f64 / 10.0,
                    floor * floor_height + 0.4, // Floor-mounted
                )
            },
            "IFCSWITCHINGDEVICE" => {
                // Switches are typically wall-mounted
                let floor_height = 3.0;
                let floor = (id_hash % 5) as f64;
                Point3D::new(
                    (id_hash % 1000) as f64 / 10.0,
                    (name_hash % 800) as f64 / 10.0,
                    floor * floor_height + 1.1, // Switch height
                )
            },
            
            // Plumbing equipment
            "IFCPIPE" => {
                // Pipes run horizontally
                let floor_height = 3.0;
                let floor = (id_hash % 5) as f64;
                Point3D::new(
                    (id_hash % 1000) as f64 / 10.0,
                    (name_hash % 800) as f64 / 10.0,
                    floor * floor_height + 2.2, // Above ceiling
                )
            },
            "IFCTANK" => {
                // Tanks are typically floor-mounted
                let floor_height = 3.0;
                let floor = (id_hash % 5) as f64;
                Point3D::new(
                    (id_hash % 1000) as f64 / 10.0,
                    (name_hash % 800) as f64 / 10.0,
                    floor * floor_height + 0.6, // Floor-mounted
                )
            },
            "IFCJUNCTIONBOX" => {
                // Junction boxes are typically wall-mounted
                let floor_height = 3.0;
                let floor = (id_hash % 5) as f64;
                Point3D::new(
                    (id_hash % 1000) as f64 / 10.0,
                    (name_hash % 800) as f64 / 10.0,
                    floor * floor_height + 1.8, // Wall-mounted height
                )
            },
            
            // Fire safety equipment
            "IFCFIREALARM" | "IFCFIREDETECTOR" => {
                // Fire alarms and detectors are typically ceiling-mounted
                let floor_height = 3.0;
                let floor = (id_hash % 5) as f64;
                Point3D::new(
                    (id_hash % 1000) as f64 / 10.0,
                    (name_hash % 800) as f64 / 10.0,
                    floor * floor_height + 2.6, // Near ceiling
                )
            },
            "IFCFIREEXTINGUISHER" => {
                // Fire extinguishers are typically wall-mounted
                let floor_height = 3.0;
                let floor = (id_hash % 5) as f64;
                Point3D::new(
                    (id_hash % 1000) as f64 / 10.0,
                    (name_hash % 800) as f64 / 10.0,
                    floor * floor_height + 1.0, // Wall-mounted height
                )
            },
            "IFCFIREPUMP" => {
                // Fire pumps are typically floor-mounted
                let floor_height = 3.0;
                let floor = (id_hash % 5) as f64;
                Point3D::new(
                    (id_hash % 1000) as f64 / 10.0,
                    (name_hash % 800) as f64 / 10.0,
                    floor * floor_height + 0.3, // Floor-mounted
                )
            },
            
            // Security equipment
            "IFCSECURITYDEVICE" | "IFCCAMERA" => {
                // Security devices are typically ceiling-mounted
                let floor_height = 3.0;
                let floor = (id_hash % 5) as f64;
                Point3D::new(
                    (id_hash % 1000) as f64 / 10.0,
                    (name_hash % 800) as f64 / 10.0,
                    floor * floor_height + 2.7, // Near ceiling
                )
            },
            "IFCACCESSDEVICE" => {
                // Access devices (card readers) are typically wall-mounted
                let floor_height = 3.0;
                let floor = (id_hash % 5) as f64;
                Point3D::new(
                    (id_hash % 1000) as f64 / 10.0,
                    (name_hash % 800) as f64 / 10.0,
                    floor * floor_height + 1.2, // Wall-mounted height
                )
            },
            
            // Other building equipment
            "IFCELEVATOR" | "IFCESCALATOR" | "IFCMOVINGWALKWAY" => {
                // Vertical transportation is typically floor-to-floor
                let floor_height = 3.0;
                let floor = (id_hash % 5) as f64;
                Point3D::new(
                    (id_hash % 1000) as f64 / 10.0,
                    (name_hash % 800) as f64 / 10.0,
                    floor * floor_height + 1.5, // Center height
                )
            },
            "IFCCRANE" | "IFCLIFTINGDEVICE" => {
                // Cranes and lifting devices are typically ceiling-mounted
                let floor_height = 3.0;
                let floor = (id_hash % 5) as f64;
                Point3D::new(
                    (id_hash % 1000) as f64 / 10.0,
                    (name_hash % 800) as f64 / 10.0,
                    floor * floor_height + 2.9, // Near ceiling
                )
            },
            
            _ => {
                // Default positioning for unknown entity types
                let floor_height = 3.0;
                let floor = (id_hash % 5) as f64;
                Point3D::new(
                    (id_hash % 1000) as f64 / 10.0,
                    (name_hash % 800) as f64 / 10.0,
                    floor * floor_height + 1.0, // Default height
                )
            }
        };
        
        Ok(position)
    }
    
    /// Calculate entity bounds based on type and position
    fn calculate_entity_bounds(&self, entity: &IFCEntity, position: &Point3D) -> Result<BoundingBox3D, Box<dyn std::error::Error>> {
        // Calculate bounding box based on entity type and typical dimensions
        let (width, height, depth) = match entity.entity_type.as_str() {
            // Building spaces
            "IFCSPACE" | "IFCROOM" | "IFCZONE" => (10.0, 3.0, 8.0),        // Typical room size
            
            // Structural elements
            "IFCWALL" => (0.2, 3.0, 5.0),          // Wall dimensions
            "IFCDOOR" => (0.9, 2.1, 0.1),          // Door dimensions
            "IFCWINDOW" => (1.5, 1.2, 0.1),        // Window dimensions
            "IFCCOLUMN" => (0.4, 3.0, 0.4),        // Column dimensions
            "IFCSLAB" => (10.0, 0.2, 8.0),         // Slab dimensions
            "IFCBEAM" => (8.0, 0.3, 0.3),          // Beam dimensions
            
            // HVAC equipment
            "IFCFLOWTERMINAL" | "IFCAIRTERMINAL" => (0.3, 0.3, 0.1),   // Small terminal
            "IFCFLOWFITTING" | "IFCDUCTFITTING" | "IFCPIPEFITTING" => (0.5, 0.5, 0.3), // Fittings
            "IFCFLOWSEGMENT" | "IFCDUCTSEGMENT" | "IFCPIPESEGMENT" => (2.0, 0.3, 0.3), // Segments
            "IFCFLOWCONTROLLER" => (0.4, 0.4, 0.2), // Controllers (valves, dampers)
            "IFCAIRHANDLINGUNIT" => (3.0, 2.0, 2.0), // Large AHU
            "IFCBOILER" => (1.5, 1.5, 1.0),         // Boiler
            "IFCCHILLER" => (2.0, 1.5, 1.5),        // Chiller
            "IFCCOOLINGTOWER" => (2.5, 2.5, 2.0),   // Cooling tower
            "IFCFAN" => (0.8, 0.8, 0.8),            // Fan
            "IFCPUMP" => (0.6, 0.6, 0.4),           // Pump
            
            // Electrical equipment
            "IFCDISTRIBUTIONELEMENT" | "IFCELECTRICDISTRIBUTIONBOARD" => (0.6, 1.2, 0.2), // Panel
            "IFCLIGHTFIXTURE" => (0.6, 0.6, 0.1),   // Light fixture
            "IFCELECTRICMOTOR" => (0.5, 0.5, 0.5),  // Motor
            "IFCELECTRICGENERATOR" => (1.0, 1.0, 0.8), // Generator
            "IFCSWITCHINGDEVICE" => (0.1, 0.1, 0.05), // Switch
            
            // Plumbing equipment
            "IFCPIPE" => (1.0, 0.1, 0.1),           // Pipe
            "IFCTANK" => (1.5, 1.5, 1.0),           // Tank
            "IFCJUNCTIONBOX" => (0.3, 0.3, 0.2),    // Junction box
            
            // Fire safety equipment
            "IFCFIREALARM" | "IFCFIREDETECTOR" => (0.2, 0.2, 0.1), // Fire alarm/detector
            "IFCFIREEXTINGUISHER" => (0.3, 0.6, 0.2), // Fire extinguisher
            "IFCFIREPUMP" => (0.8, 0.8, 0.6),       // Fire pump
            
            // Security equipment
            "IFCSECURITYDEVICE" | "IFCCAMERA" => (0.2, 0.2, 0.1), // Security device/camera
            "IFCACCESSDEVICE" => (0.1, 0.1, 0.05),  // Access device
            
            // Other building equipment
            "IFCELEVATOR" => (2.0, 2.0, 3.0),       // Elevator
            "IFCESCALATOR" => (1.5, 1.5, 3.0),      // Escalator
            "IFCMOVINGWALKWAY" => (2.0, 1.0, 3.0),   // Moving walkway
            "IFCCRANE" | "IFCLIFTINGDEVICE" => (1.0, 1.0, 0.5), // Crane/lifting device
            
            _ => (1.0, 1.0, 1.0),                  // Default dimensions
        };
        
        let min_point = Point3D::new(
            position.x - width / 2.0,
            position.y - height / 2.0,
            position.z - depth / 2.0,
        );
        
        let max_point = Point3D::new(
            position.x + width / 2.0,
            position.y + height / 2.0,
            position.z + depth / 2.0,
        );
        
        Ok(BoundingBox3D::new(min_point, max_point))
    }
    
    /// Generate a simple hash from a string for deterministic positioning
    fn hash_string(&self, s: &str) -> u64 {
        let mut hash = 5381u64;
        for byte in s.bytes() {
            hash = hash.wrapping_mul(33).wrapping_add(byte as u64);
        }
        hash
    }
}

impl RTreeNode {
    /// Create a new R-Tree node
    pub fn new(entities: &[SpatialEntity]) -> Self {
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
        
        RTreeNode {
            bounds,
            children: Vec::new(),
            entities: entities.to_vec(),
            is_leaf: true,
            max_entities: 10,
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
            let entity_bounds = &entity.bounding_box;
            min_x = min_x.min(entity_bounds.min.x);
            min_y = min_y.min(entity_bounds.min.y);
            min_z = min_z.min(entity_bounds.min.z);
            max_x = max_x.max(entity_bounds.max.x);
            max_y = max_y.max(entity_bounds.max.y);
            max_z = max_z.max(entity_bounds.max.z);
        }
        
        BoundingBox3D {
            min: Point3D { x: min_x, y: min_y, z: min_z },
            max: Point3D { x: max_x, y: max_y, z: max_z },
        }
    }
    
    /// Check if this node intersects with a bounding box
    pub fn intersects(&self, bbox: &BoundingBox3D) -> bool {
        self.bounds.min.x <= bbox.max.x &&
        self.bounds.max.x >= bbox.min.x &&
        self.bounds.min.y <= bbox.max.y &&
        self.bounds.max.y >= bbox.min.y &&
        self.bounds.min.z <= bbox.max.z &&
        self.bounds.max.z >= bbox.min.z
    }
    
    /// Check if this node contains a point
    pub fn contains_point(&self, point: &Point3D) -> bool {
        point.x >= self.bounds.min.x && point.x <= self.bounds.max.x &&
        point.y >= self.bounds.min.y && point.y <= self.bounds.max.y &&
        point.z >= self.bounds.min.z && point.z <= self.bounds.max.z
    }
    
    /// Search for entities within a bounding box
    pub fn search_within_bounds(&self, bbox: &BoundingBox3D) -> Vec<SpatialEntity> {
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

impl SpatialIndex {
    /// Create a new spatial index
    pub fn new() -> Self {
        SpatialIndex {
            rtree: RTreeNode::new(&[]),
            room_index: HashMap::new(),
            floor_index: HashMap::new(),
            entity_cache: HashMap::new(),
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
            min: Point3D {
                x: center.x - radius,
                y: center.y - radius,
                z: center.z - radius,
            },
            max: Point3D {
                x: center.x + radius,
                y: center.y + radius,
                z: center.z + radius,
            },
        };
        
        // Search R-Tree
        let entities = self.rtree.search_within_bounds(&search_bbox);
        
        // Filter by actual distance and create results
        for entity in entities {
            let distance = self.calculate_distance(&center, &entity.position);
            if distance <= radius {
                results.push(SpatialQueryResult {
                    entity,
                    distance,
                    relationship_type: SpatialRelationship::Within,
                    intersection_points: Vec::new(),
                });
            }
        }
        
        // Sort by distance
        results.sort_by(|a, b| a.distance.partial_cmp(&b.distance).unwrap());
        results
    }
    
    /// Find entities within a bounding box
    pub fn find_within_bounding_box(&self, bbox: BoundingBox3D) -> Vec<SpatialQueryResult> {
        let entities = self.rtree.search_within_bounds(&bbox);
        
        entities.into_iter().map(|entity| {
            SpatialQueryResult {
                entity,
                distance: 0.0, // Distance not applicable for bounding box queries
                relationship_type: SpatialRelationship::Within,
                intersection_points: Vec::new(),
            }
        }).collect()
    }
    
    /// Find entities in a specific room
    pub fn find_in_room(&self, room_id: &str) -> Vec<SpatialEntity> {
        if let Some(entity_ids) = self.room_index.get(room_id) {
            entity_ids.iter()
                .filter_map(|id| self.entity_cache.get(id))
                .cloned()
                .collect()
        } else {
            Vec::new()
        }
    }
    
    /// Find entities on a specific floor
    pub fn find_in_floor(&self, floor: i32) -> Vec<SpatialEntity> {
        if let Some(entity_ids) = self.floor_index.get(&floor) {
            entity_ids.iter()
                .filter_map(|id| self.entity_cache.get(id))
                .cloned()
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
            let distance = self.calculate_distance(&point, &entity.position);
            if distance < min_distance {
                min_distance = distance;
                nearest = Some(SpatialQueryResult {
                    entity: entity.clone(),
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
        
        entities.into_iter().map(|entity| {
            let intersection_points = self.calculate_intersection_points(&entity.bounding_box, &bbox);
            SpatialQueryResult {
                entity,
                distance: 0.0, // Distance not applicable for intersection queries
                relationship_type: SpatialRelationship::Intersects,
                intersection_points,
            }
        }).collect()
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
            if self.point_in_bounding_box(&point, &entity.bounding_box) {
                results.push(SpatialQueryResult {
                    entity: entity.clone(),
                    distance: self.calculate_distance(&point, &entity.position),
                    relationship_type: SpatialRelationship::Contains,
                    intersection_points: vec![point.clone()],
                });
            }
        }
        
        results
    }
    
    /// Find entities within a specific volume (3D bounding box)
    pub fn find_within_volume(&self, bbox: BoundingBox3D) -> Vec<SpatialQueryResult> {
        let entities = self.rtree.search_within_bounds(&bbox);
        
        entities.into_iter().filter_map(|entity| {
            // Check if entity is fully contained within the volume
            if self.bounding_box_contained(&entity.bounding_box, &bbox) {
                Some(SpatialQueryResult {
                    entity,
                    distance: 0.0,
                    relationship_type: SpatialRelationship::Within,
                    intersection_points: Vec::new(),
                })
            } else {
                None
            }
        }).collect()
    }
    
    /// Find entities that span across multiple floors
    pub fn find_cross_floor_entities(&self, min_floor: i32, max_floor: i32) -> Vec<SpatialEntity> {
        let mut results = Vec::new();
        
        for entity in self.entity_cache.values() {
            let entity_floor_min = (entity.bounding_box.min.z / 10.0) as i32;
            let entity_floor_max = (entity.bounding_box.max.z / 10.0) as i32;
            
            // Check if entity spans across the specified floor range
            if entity_floor_min < min_floor || entity_floor_max > max_floor {
                results.push(entity.clone());
            }
        }
        
        results
    }
    
    /// Find equipment by system type within a radius
    pub fn find_equipment_by_system(&self, system_type: &str, center: Point3D, radius: f64) -> Vec<SpatialQueryResult> {
        self.find_within_radius(center, radius)
            .into_iter()
            .filter(|result| {
                result.entity.entity_type.to_uppercase().contains(&system_type.to_uppercase())
            })
            .collect()
    }
    
    /// Find equipment clusters (groups of nearby equipment)
    pub fn find_equipment_clusters(&self, cluster_radius: f64, min_cluster_size: usize) -> Vec<Vec<SpatialEntity>> {
        let mut clusters = Vec::new();
        let mut processed = std::collections::HashSet::new();
        
        for entity in self.entity_cache.values() {
            if processed.contains(&entity.id) {
                continue;
            }
            
            // Find all entities within cluster radius
            let nearby_entities = self.find_within_radius(entity.position.clone(), cluster_radius);
            let cluster: Vec<SpatialEntity> = nearby_entities
                .into_iter()
                .map(|result| result.entity)
                .collect();
            
            if cluster.len() >= min_cluster_size {
                // Mark all entities in this cluster as processed
                for cluster_entity in &cluster {
                    processed.insert(cluster_entity.id.clone());
                }
                clusters.push(cluster);
            }
        }
        
        clusters
    }
    
    /// Calculate intersection points between two bounding boxes
    fn calculate_intersection_points(&self, bbox1: &BoundingBox3D, bbox2: &BoundingBox3D) -> Vec<Point3D> {
        let mut points = Vec::new();
        
        // Calculate intersection bounding box
        let intersection_min = Point3D {
            x: bbox1.min.x.max(bbox2.min.x),
            y: bbox1.min.y.max(bbox2.min.y),
            z: bbox1.min.z.max(bbox2.min.z),
        };
        
        let intersection_max = Point3D {
            x: bbox1.max.x.min(bbox2.max.x),
            y: bbox1.max.y.min(bbox2.max.y),
            z: bbox1.max.z.min(bbox2.max.z),
        };
        
        // Check if there's a valid intersection
        if intersection_min.x <= intersection_max.x &&
           intersection_min.y <= intersection_max.y &&
           intersection_min.z <= intersection_max.z {
            
            // Add corner points of intersection
            points.push(intersection_min.clone());
            points.push(intersection_max.clone());
            points.push(Point3D {
                x: intersection_min.x,
                y: intersection_min.y,
                z: intersection_max.z,
            });
            points.push(Point3D {
                x: intersection_max.x,
                y: intersection_min.y,
                z: intersection_min.z,
            });
        }
        
        points
    }
    
    /// Check if a point is inside a bounding box
    fn point_in_bounding_box(&self, point: &Point3D, bbox: &BoundingBox3D) -> bool {
        point.x >= bbox.min.x && point.x <= bbox.max.x &&
        point.y >= bbox.min.y && point.y <= bbox.max.y &&
        point.z >= bbox.min.z && point.z <= bbox.max.z
    }
    
    /// Check if one bounding box is contained within another
    fn bounding_box_contained(&self, inner: &BoundingBox3D, outer: &BoundingBox3D) -> bool {
        inner.min.x >= outer.min.x && inner.max.x <= outer.max.x &&
        inner.min.y >= outer.min.y && inner.max.y <= outer.max.y &&
        inner.min.z >= outer.min.z && inner.max.z <= outer.max.z
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
    pub fn calculate_intersection_volume(&self, bbox1: &BoundingBox3D, bbox2: &BoundingBox3D) -> f64 {
        let intersection_min_x = bbox1.min.x.max(bbox2.min.x);
        let intersection_max_x = bbox1.max.x.min(bbox2.max.x);
        let intersection_min_y = bbox1.min.y.max(bbox2.min.y);
        let intersection_max_y = bbox1.max.y.min(bbox2.max.y);
        let intersection_min_z = bbox1.min.z.max(bbox2.min.z);
        let intersection_max_z = bbox1.max.z.min(bbox2.max.z);
        
        if intersection_min_x <= intersection_max_x &&
           intersection_min_y <= intersection_max_y &&
           intersection_min_z <= intersection_max_z {
            (intersection_max_x - intersection_min_x) * 
            (intersection_max_y - intersection_min_y) * 
            (intersection_max_z - intersection_min_z)
        } else {
            0.0
        }
    }
    
    /// Calculate overlap percentage between two bounding boxes
    pub fn calculate_overlap_percentage(&self, bbox1: &BoundingBox3D, bbox2: &BoundingBox3D) -> f64 {
        let intersection_volume = self.calculate_intersection_volume(bbox1, bbox2);
        let union_volume = bbox1.volume() + bbox2.volume() - intersection_volume;
        
        if union_volume > 0.0 {
            intersection_volume / union_volume
        } else {
            0.0
        }
    }
    
    /// Analyze spatial relationships between two entities
    pub fn analyze_spatial_relationships(&self, entity1: &SpatialEntity, entity2: &SpatialEntity) -> SpatialRelationship {
        let bbox1 = &entity1.bounding_box;
        let bbox2 = &entity2.bounding_box;
        
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
        let distance = self.calculate_distance(&entity1.position, &entity2.position);
        let max_dimension = (bbox1.volume().powf(1.0/3.0) + bbox2.volume().powf(1.0/3.0)) / 2.0;
        
        if distance <= max_dimension * 2.0 {
            return SpatialRelationship::Adjacent;
        }
        
        SpatialRelationship::Overlaps
    }
    
    /// Calculate geometric similarity between two entities
    pub fn calculate_geometric_similarity(&self, entity1: &SpatialEntity, entity2: &SpatialEntity) -> f64 {
        let volume1 = entity1.bounding_box.volume();
        let volume2 = entity2.bounding_box.volume();
        
        // Volume similarity
        let volume_similarity = 1.0 - (volume1 - volume2).abs() / (volume1 + volume2).max(1.0);
        
        // Position similarity
        let distance = self.calculate_distance(&entity1.position, &entity2.position);
        let max_distance = 100.0; // Maximum expected distance for similarity
        let position_similarity = 1.0 - (distance / max_distance).min(1.0);
        
        // Shape similarity (aspect ratio)
        let aspect1 = self.calculate_aspect_ratio(&entity1.bounding_box);
        let aspect2 = self.calculate_aspect_ratio(&entity2.bounding_box);
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
                
                let intersection_volume = self.calculate_intersection_volume(&entity1.bounding_box, &entity2.bounding_box);
                let distance = self.calculate_distance(&entity1.position, &entity2.position);
                
                // Check for overlap conflicts
                if intersection_volume > 0.0 {
                    let severity = if intersection_volume > entity1.bounding_box.volume() * 0.5 {
                        ConflictSeverity::Critical
                    } else if intersection_volume > entity1.bounding_box.volume() * 0.1 {
                        ConflictSeverity::High
                    } else {
                        ConflictSeverity::Medium
                    };
                    
                    conflicts.push(GeometricConflict {
                        entity1_id: entity1.id.clone(),
                        entity2_id: entity2.id.clone(),
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
                        entity1_id: entity1.id.clone(),
                        entity2_id: entity2.id.clone(),
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
        let base_clearance = match (entity1.entity_type.as_str(), entity2.entity_type.as_str()) {
            (t1, t2) if t1.contains("ELECTRIC") && t2.contains("ELECTRIC") => 0.3,
            (t1, t2) if t1.contains("FIRE") || t2.contains("FIRE") => 1.0,
            (t1, t2) if t1.contains("HVAC") && t2.contains("HVAC") => 0.5,
            _ => 0.2, // Default clearance
        };
        
        // Add size-based clearance
        let size_factor = (entity1.bounding_box.volume() + entity2.bounding_box.volume()).powf(1.0/3.0) * 0.1;
        
        base_clearance + size_factor
    }
    
    /// Optimize spatial index for better performance
    pub fn optimize_spatial_index(&mut self) -> ArxResult<()> {
        // Rebuild the R-Tree with optimized parameters
        let entities: Vec<SpatialEntity> = self.entity_cache.values().cloned().collect();
        self.rtree = RTreeNode::new(&entities);
        
        // Optimize room and floor indices
        self.room_index.clear();
        self.floor_index.clear();
        
        for entity in &entities {
            let room_id = format!("ROOM_{}", entity.name.replace(" ", "_"));
            self.room_index.entry(room_id.clone())
                .or_insert_with(Vec::new)
                .push(entity.id.clone());
            
            let floor = (entity.position.z / 10.0) as i32;
            self.floor_index.entry(floor)
                .or_insert_with(Vec::new)
                .push(entity.id.clone());
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
        let _entity_count = self.entity_cache.len();
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

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_enhanced_parser_creation() {
        let parser = EnhancedIFCParser::new();
        assert_eq!(parser.error_threshold, 10);
        assert!(parser.continue_on_error);
    }
    
    #[test]
    fn test_parser_with_custom_threshold() {
        let parser = EnhancedIFCParser::new().with_error_threshold(5);
        assert_eq!(parser.error_threshold, 5);
    }
    
    #[test]
    fn test_parse_stats_calculations() {
        let mut stats = ParseStats::new();
        stats.successful_entities = 80;
        stats.failed_parses = 10;
        stats.failed_spatial_extractions = 5;
        stats.total_lines = 100;
        stats.processing_time_ms = 1000;
        
        assert_eq!(stats.success_rate(), 0.8);
        assert_eq!(stats.error_rate(), 0.15);
        assert_eq!(stats.processing_speed(), 100.0);
    }
    
    #[test]
    fn test_entity_line_parsing() {
        let parser = EnhancedIFCParser::new();
        let line = "#123=IFCBUILDING('Building-1','Office Building',$,$,$,$,$,$,$);";
        
        let entity = parser.parse_entity_line(line).unwrap();
        assert_eq!(entity.id, "123");
        assert_eq!(entity.entity_type, "IFCBUILDING");
        assert!(!entity.parameters.is_empty());
    }
    
    #[test]
    fn test_spatial_entity_detection() {
        let parser = EnhancedIFCParser::new();
        
        assert!(parser.is_spatial_entity("IFCSPACE"));
        assert!(parser.is_spatial_entity("IFCFLOWTERMINAL"));
        assert!(!parser.is_spatial_entity("IFCBUILDING"));
    }
    
    #[test]
    fn test_enhanced_equipment_type_support() {
        let parser = EnhancedIFCParser::new();
        
        // Test HVAC equipment
        assert!(parser.is_spatial_entity("IFCAIRTERMINAL"));
        assert!(parser.is_spatial_entity("IFCDUCTFITTING"));
        assert!(parser.is_spatial_entity("IFCFLOWCONTROLLER"));
        assert!(parser.is_spatial_entity("IFCAIRHANDLINGUNIT"));
        assert!(parser.is_spatial_entity("IFCFAN"));
        assert!(parser.is_spatial_entity("IFCPUMP"));
        
        // Test electrical equipment
        assert!(parser.is_spatial_entity("IFCELECTRICDISTRIBUTIONBOARD"));
        assert!(parser.is_spatial_entity("IFCLIGHTFIXTURE"));
        assert!(parser.is_spatial_entity("IFCELECTRICMOTOR"));
        assert!(parser.is_spatial_entity("IFCSWITCHINGDEVICE"));
        
        // Test plumbing equipment
        assert!(parser.is_spatial_entity("IFCPIPE"));
        assert!(parser.is_spatial_entity("IFCTANK"));
        assert!(parser.is_spatial_entity("IFCJUNCTIONBOX"));
        
        // Test fire safety equipment
        assert!(parser.is_spatial_entity("IFCFIREALARM"));
        assert!(parser.is_spatial_entity("IFCFIREDETECTOR"));
        assert!(parser.is_spatial_entity("IFCFIREEXTINGUISHER"));
        
        // Test security equipment
        assert!(parser.is_spatial_entity("IFCSECURITYDEVICE"));
        assert!(parser.is_spatial_entity("IFCCAMERA"));
        assert!(parser.is_spatial_entity("IFCACCESSDEVICE"));
        
        // Test other building equipment
        assert!(parser.is_spatial_entity("IFCELEVATOR"));
        assert!(parser.is_spatial_entity("IFCESCALATOR"));
        assert!(parser.is_spatial_entity("IFCCRANE"));
    }
    
    #[test]
    fn test_equipment_positioning_logic() {
        let parser = EnhancedIFCParser::new();
        
        // Test HVAC equipment positioning
        let hvac_entity = IFCEntity {
            id: "123".to_string(),
            entity_type: "IFCAIRTERMINAL".to_string(),
            parameters: vec!["test".to_string()],
            line_number: 1,
        };
        
        let position = parser.generate_deterministic_position(&hvac_entity).unwrap();
        
        // HVAC terminals should be wall-mounted (around 1.5m height)
        // With floor_height = 3.0 and floor = (id_hash % 5), z = floor * 3.0 + 1.5
        let id_hash = parser.hash_string("123");
        let floor = (id_hash % 5) as f64;
        let expected_z = floor * 3.0 + 1.5;
        assert!((position.z - expected_z).abs() < 0.1);
        
        // Test electrical equipment positioning
        let elec_entity = IFCEntity {
            id: "456".to_string(),
            entity_type: "IFCLIGHTFIXTURE".to_string(),
            parameters: vec!["test".to_string()],
            line_number: 1,
        };
        
        let position = parser.generate_deterministic_position(&elec_entity).unwrap();
        
        // Light fixtures should be ceiling-mounted (around 2.8m height)
        let id_hash = parser.hash_string("456");
        let floor = (id_hash % 5) as f64;
        let expected_z = floor * 3.0 + 2.8;
        assert!((position.z - expected_z).abs() < 0.1);
        
        // Test that different equipment types have different heights
        let pump_entity = IFCEntity {
            id: "789".to_string(),
            entity_type: "IFCPUMP".to_string(),
            parameters: vec!["test".to_string()],
            line_number: 1,
        };
        
        let pump_position = parser.generate_deterministic_position(&pump_entity).unwrap();
        
        // Pumps should be floor-mounted (around 0.3m height)
        let id_hash = parser.hash_string("789");
        let floor = (id_hash % 5) as f64;
        let expected_z = floor * 3.0 + 0.3;
        assert!((pump_position.z - expected_z).abs() < 0.1);
        
        // Verify that different equipment types have different positioning logic
        assert_ne!(position.z, pump_position.z);
    }
    
    #[test]
    fn test_equipment_bounding_boxes() {
        let parser = EnhancedIFCParser::new();
        
        // Test HVAC equipment bounding boxes
        let hvac_entity = IFCEntity {
            id: "123".to_string(),
            entity_type: "IFCAIRTERMINAL".to_string(),
            parameters: vec!["test".to_string()],
            line_number: 1,
        };
        
        let position = Point3D::new(10.0, 10.0, 1.5);
        let bounds = parser.calculate_entity_bounds(&hvac_entity, &position).unwrap();
        
        // Air terminals should be small (0.3 x 0.3 x 0.1)
        let width = bounds.max.x - bounds.min.x;
        let height = bounds.max.y - bounds.min.y;
        let depth = bounds.max.z - bounds.min.z;
        
        assert!((width - 0.3).abs() < 0.01);
        assert!((height - 0.3).abs() < 0.01);
        assert!((depth - 0.1).abs() < 0.01);
        
        // Test large equipment bounding boxes
        let large_entity = IFCEntity {
            id: "789".to_string(),
            entity_type: "IFCAIRHANDLINGUNIT".to_string(),
            parameters: vec!["test".to_string()],
            line_number: 1,
        };
        
        let bounds = parser.calculate_entity_bounds(&large_entity, &position).unwrap();
        let width = bounds.max.x - bounds.min.x;
        
        // AHU should be large (3.0 x 2.0 x 2.0)
        assert!((width - 3.0).abs() < 0.01);
    }
    
    #[test]
    fn test_coordinate_extraction_formats() {
        let parser = EnhancedIFCParser::new();
        
        // Test direct coordinate format: (x, y, z)
        let direct_coords = parser.parse_direct_coordinates("(1.5, 2.3, 3.7)").unwrap();
        assert_eq!(direct_coords.x, 1.5);
        assert_eq!(direct_coords.y, 2.3);
        assert_eq!(direct_coords.z, 3.7);
        
        // Test coordinate string without parentheses
        let coord_string = parser.parse_coordinate_string("4.1, 5.2, 6.3").unwrap();
        assert_eq!(coord_string.x, 4.1);
        assert_eq!(coord_string.y, 5.2);
        assert_eq!(coord_string.z, 6.3);
        
        // Test placement reference (should return origin for now)
        let ref_coords = parser.parse_placement_reference("#12345").unwrap();
        assert_eq!(ref_coords.x, 0.0);
        assert_eq!(ref_coords.y, 0.0);
        assert_eq!(ref_coords.z, 0.0);
    }
    
    #[test]
    fn test_ifc_placement_formats() {
        let parser = EnhancedIFCParser::new();
        
        // Test IFCLOCALPLACEMENT format
        let local_placement = parser.parse_local_placement("IFCLOCALPLACEMENT(#12346,#12347)").unwrap();
        // Should return origin since reference resolution is not implemented yet
        assert_eq!(local_placement.x, 0.0);
        assert_eq!(local_placement.y, 0.0);
        assert_eq!(local_placement.z, 0.0);
        
        // Test IFCAXIS2PLACEMENT3D format
        let axis_placement = parser.parse_axis2_placement_3d("IFCAXIS2PLACEMENT3D(#12346,#12347,#12348)").unwrap();
        // Should return origin since reference resolution is not implemented yet
        assert_eq!(axis_placement.x, 0.0);
        assert_eq!(axis_placement.y, 0.0);
        assert_eq!(axis_placement.z, 0.0);
    }
    
    #[test]
    fn test_geometry_coordinate_extraction() {
        let parser = EnhancedIFCParser::new();
        
        // Test coordinate extraction from geometry data
        let geometry_data = "1.0 2.0 3.0 4.0 5.0 6.0 7.0 8.0 9.0";
        let coordinates = parser.extract_coordinates_from_geometry(geometry_data).unwrap();
        
        assert_eq!(coordinates.len(), 3);
        assert_eq!(coordinates[0], Point3D::new(1.0, 2.0, 3.0));
        assert_eq!(coordinates[1], Point3D::new(4.0, 5.0, 6.0));
        assert_eq!(coordinates[2], Point3D::new(7.0, 8.0, 9.0));
        
        // Test geometry placement with coordinate centroid calculation
        let geometry_placement = parser.parse_geometry_placement(geometry_data).unwrap();
        // Centroid should be (4.0, 5.0, 6.0)
        assert_eq!(geometry_placement.x, 4.0);
        assert_eq!(geometry_placement.y, 5.0);
        assert_eq!(geometry_placement.z, 6.0);
    }
    
    #[test]
    fn test_enhanced_placement_data_parsing() {
        let parser = EnhancedIFCParser::new();
        
        // Test direct coordinates
        let direct = parser.parse_placement_data("(10.5, 20.3, 30.7)").unwrap();
        assert_eq!(direct.x, 10.5);
        assert_eq!(direct.y, 20.3);
        assert_eq!(direct.z, 30.7);
        
        // Test coordinate string
        let coord_str = parser.parse_placement_data("40.1, 50.2, 60.3").unwrap();
        assert_eq!(coord_str.x, 40.1);
        assert_eq!(coord_str.y, 50.2);
        assert_eq!(coord_str.z, 60.3);
        
        // Test reference (should return origin)
        let reference = parser.parse_placement_data("#12345").unwrap();
        assert_eq!(reference.x, 0.0);
        assert_eq!(reference.y, 0.0);
        assert_eq!(reference.z, 0.0);
        
        // Test IFCLOCALPLACEMENT
        let local = parser.parse_placement_data("IFCLOCALPLACEMENT(#12346,#12347)").unwrap();
        assert_eq!(local.x, 0.0);
        assert_eq!(local.y, 0.0);
        assert_eq!(local.z, 0.0);
        
        // Test IFCAXIS2PLACEMENT3D
        let axis = parser.parse_placement_data("IFCAXIS2PLACEMENT3D(#12346,#12347,#12348)").unwrap();
        assert_eq!(axis.x, 0.0);
        assert_eq!(axis.y, 0.0);
        assert_eq!(axis.z, 0.0);
    }
    
    #[test]
    fn test_ifc_writing_capabilities() {
        let parser = EnhancedIFCParser::new();
        
        // Create test spatial entities
        let entities = vec![
            SpatialEntity {
                id: "SPACE_001".to_string(),
                name: "Conference Room A".to_string(),
                entity_type: "IFCSPACE".to_string(),
                position: Point3D::new(10.0, 20.0, 0.0),
                bounding_box: BoundingBox3D {
                    min: Point3D::new(9.0, 19.0, 0.0),
                    max: Point3D::new(11.0, 21.0, 3.0),
                },
                coordinate_system: Some(crate::spatial::types::CoordinateSystem::new(
                    "IFC_COORDINATE_SYSTEM".to_string(),
                    Point3D::origin()
                )),
            },
            SpatialEntity {
                id: "AIR_TERMINAL_001".to_string(),
                name: "Supply Air Terminal".to_string(),
                entity_type: "IFCAIRTERMINAL".to_string(),
                position: Point3D::new(10.5, 20.5, 1.5),
                bounding_box: BoundingBox3D {
                    min: Point3D::new(10.2, 20.2, 1.2),
                    max: Point3D::new(10.8, 20.8, 1.8),
                },
                coordinate_system: Some(crate::spatial::types::CoordinateSystem::new(
                    "IFC_COORDINATE_SYSTEM".to_string(),
                    Point3D::origin()
                )),
            },
            SpatialEntity {
                id: "LIGHT_001".to_string(),
                name: "LED Light Fixture".to_string(),
                entity_type: "IFCLIGHTFIXTURE".to_string(),
                position: Point3D::new(10.0, 20.0, 2.8),
                bounding_box: BoundingBox3D {
                    min: Point3D::new(9.8, 19.8, 2.6),
                    max: Point3D::new(10.2, 20.2, 3.0),
                },
                coordinate_system: Some(crate::spatial::types::CoordinateSystem::new(
                    "IFC_COORDINATE_SYSTEM".to_string(),
                    Point3D::origin()
                )),
            },
        ];
        
        // Test writing to temporary file
        let temp_path = "test_output.ifc";
        let result = parser.write_spatial_entities_to_ifc(&entities, temp_path);
        
        // Verify the operation succeeded
        assert!(result.is_ok());
        
        // Verify the file was created and contains expected content
        let content = std::fs::read_to_string(temp_path).unwrap();
        
        // Check for IFC header
        assert!(content.contains("ISO-10303-21"));
        assert!(content.contains("FILE_DESCRIPTION"));
        assert!(content.contains("ArxOS Generated IFC File"));
        
        // Check for coordinate system definitions
        assert!(content.contains("IFCCARTESIANPOINT"));
        assert!(content.contains("IFCLOCALPLACEMENT"));
        
        // Check for spatial entities
        assert!(content.contains("IFCSPACE"));
        assert!(content.contains("IFCAIRTERMINAL"));
        assert!(content.contains("IFCLIGHTFIXTURE"));
        
        // Check for specific coordinates
        assert!(content.contains("10.000,20.000,0.000"));
        assert!(content.contains("10.500,20.500,1.500"));
        assert!(content.contains("10.000,20.000,2.800"));
        
        // Check for IFC footer
        assert!(content.contains("ENDSEC"));
        assert!(content.contains("END-ISO-10303-21"));
        
        // Clean up test file
        std::fs::remove_file(temp_path).unwrap();
    }
    
    #[test]
    fn test_entity_id_generation() {
        let parser = EnhancedIFCParser::new();
        
        // Test that different IDs generate different entity IDs
        let id1 = parser.generate_entity_id("ENTITY_001");
        let id2 = parser.generate_entity_id("ENTITY_002");
        let id3 = parser.generate_entity_id("ENTITY_001"); // Same as id1
        
        // Different entities should have different IDs
        assert_ne!(id1, id2);
        
        // Same entity should have same ID (deterministic)
        assert_eq!(id1, id3);
        
        // IDs should be in reasonable range (1000+)
        assert!(id1 >= 1000);
        assert!(id2 >= 1000);
        assert!(id3 >= 1000);
    }
    
    #[test]
    fn test_ifc_entity_writing_formats() {
        let parser = EnhancedIFCParser::new();
        
        // Test different entity types
        let test_cases = vec![
            ("IFCSPACE", "Space Entity"),
            ("IFCROOM", "Room Entity"),
            ("IFCAIRTERMINAL", "Air Terminal"),
            ("IFCLIGHTFIXTURE", "Light Fixture"),
            ("IFCFAN", "Fan Unit"),
            ("IFCPUMP", "Pump Unit"),
            ("UNKNOWN_TYPE", "Generic Equipment"),
        ];
        
        for (entity_type, expected_name) in test_cases {
            let entity = SpatialEntity {
                id: format!("TEST_{}", entity_type),
                name: expected_name.to_string(),
                entity_type: entity_type.to_string(),
                position: Point3D::new(1.0, 2.0, 3.0),
                bounding_box: BoundingBox3D {
                    min: Point3D::new(0.5, 1.5, 2.5),
                    max: Point3D::new(1.5, 2.5, 3.5),
                },
                coordinate_system: Some(crate::spatial::types::CoordinateSystem::new(
                    "IFC_COORDINATE_SYSTEM".to_string(),
                    Point3D::origin()
                )),
            };
            
            // Test that writing doesn't panic
            let temp_path = format!("test_{}.ifc", entity_type);
            let result = parser.write_spatial_entities_to_ifc(&[entity], &temp_path);
            assert!(result.is_ok());
            
            // Verify file content
            let content = std::fs::read_to_string(&temp_path).unwrap();
            assert!(content.contains(entity_type));
            assert!(content.contains(expected_name));
            assert!(content.contains("1.000,2.000,3.000"));
            
            // Clean up
            std::fs::remove_file(&temp_path).unwrap();
        }
    }
    
    #[test]
    fn test_coordinate_system_parsing() {
        let parser = EnhancedIFCParser::new();
        
        // Test IFCCARTESIANPOINT parsing
        let cartesian_data = "IFCCARTESIANPOINT((10.5, 20.3, 30.7))";
        let coord_system = parser.parse_coordinate_system(cartesian_data).unwrap();
        assert_eq!(coord_system.name, "CARTESIAN");
        assert_eq!(coord_system.origin.x, 10.5);
        assert_eq!(coord_system.origin.y, 20.3);
        assert_eq!(coord_system.origin.z, 30.7);
        
        // Test IFCAXIS2PLACEMENT3D parsing
        let axis_data = "IFCAXIS2PLACEMENT3D(#12346,#12347,#12348)";
        let coord_system = parser.parse_coordinate_system(axis_data).unwrap();
        assert_eq!(coord_system.name, "AXIS2_PLACEMENT");
        assert_eq!(coord_system.origin.x, 0.0);
        assert_eq!(coord_system.origin.y, 0.0);
        assert_eq!(coord_system.origin.z, 0.0);
        
        // Test IFCLOCALPLACEMENT parsing
        let local_data = "IFCLOCALPLACEMENT(#12346,#12347)";
        let coord_system = parser.parse_coordinate_system(local_data).unwrap();
        assert_eq!(coord_system.name, "LOCAL_PLACEMENT");
        assert_eq!(coord_system.origin.x, 0.0);
        assert_eq!(coord_system.origin.y, 0.0);
        assert_eq!(coord_system.origin.z, 0.0);
        
        // Test unknown format (should return default)
        let unknown_data = "UNKNOWN_FORMAT";
        let coord_system = parser.parse_coordinate_system(unknown_data).unwrap();
        assert_eq!(coord_system.name, "DEFAULT");
        assert_eq!(coord_system.origin.x, 0.0);
        assert_eq!(coord_system.origin.y, 0.0);
        assert_eq!(coord_system.origin.z, 0.0);
    }
    
    #[test]
    fn test_point_transformation() {
        let parser = EnhancedIFCParser::new();
        
        // Create source and target coordinate systems
        let source_system = CoordinateSystem::new("SOURCE".to_string(), Point3D::new(5.0, 10.0, 15.0));
        let target_system = CoordinateSystem::new("TARGET".to_string(), Point3D::new(2.0, 3.0, 4.0));
        
        // Test point transformation
        let original_point = Point3D::new(10.0, 20.0, 30.0);
        let transformed_point = parser.transform_point(&original_point, &source_system, &target_system);
        
        // Expected: (10-5+2, 20-10+3, 30-15+4) = (7, 13, 19)
        assert_eq!(transformed_point.x, 7.0);
        assert_eq!(transformed_point.y, 13.0);
        assert_eq!(transformed_point.z, 19.0);
        
        // Test inverse transformation
        let back_transformed = parser.transform_point(&transformed_point, &target_system, &source_system);
        assert_eq!(back_transformed.x, original_point.x);
        assert_eq!(back_transformed.y, original_point.y);
        assert_eq!(back_transformed.z, original_point.z);
    }
    
    #[test]
    fn test_coordinate_system_conversion() {
        let parser = EnhancedIFCParser::new();
        
        // Test conversion between named coordinate systems
        let point = Point3D::new(100.0, 200.0, 300.0);
        
        // Convert from GLOBAL to BUILDING coordinate system
        let converted = parser.convert_coordinate_system(&point, "GLOBAL", "BUILDING").unwrap();
        assert_eq!(converted.x, 100.0);
        assert_eq!(converted.y, 200.0);
        assert_eq!(converted.z, 300.0);
        
        // Test unknown coordinate system
        let result = parser.convert_coordinate_system(&point, "UNKNOWN", "GLOBAL");
        assert!(result.is_err());
    }
    
    #[test]
    fn test_coordinate_normalization() {
        let parser = EnhancedIFCParser::new();
        
        // Create test entities with different coordinate systems
        let mut entities = vec![
            SpatialEntity {
                id: "ENTITY_001".to_string(),
                name: "Test Entity 1".to_string(),
                entity_type: "IFCSPACE".to_string(),
                position: Point3D::new(10.0, 20.0, 30.0),
                bounding_box: BoundingBox3D {
                    min: Point3D::new(9.0, 19.0, 29.0),
                    max: Point3D::new(11.0, 21.0, 31.0),
                },
                coordinate_system: Some(CoordinateSystem::new("BUILDING".to_string(), Point3D::new(5.0, 10.0, 15.0))),
            },
            SpatialEntity {
                id: "ENTITY_002".to_string(),
                name: "Test Entity 2".to_string(),
                entity_type: "IFCAIRTERMINAL".to_string(),
                position: Point3D::new(50.0, 60.0, 70.0),
                bounding_box: BoundingBox3D {
                    min: Point3D::new(49.0, 59.0, 69.0),
                    max: Point3D::new(51.0, 61.0, 71.0),
                },
                coordinate_system: Some(CoordinateSystem::new("FLOOR".to_string(), Point3D::new(2.0, 3.0, 4.0))),
            },
        ];
        
        // Normalize to GLOBAL coordinate system
        let result = parser.normalize_coordinates(&mut entities, "GLOBAL");
        assert!(result.is_ok());
        
        // Verify that all entities now have GLOBAL coordinate system
        for entity in &entities {
            assert!(entity.coordinate_system.is_some());
            assert_eq!(entity.coordinate_system.as_ref().unwrap().name, "GLOBAL");
        }
        
        // Verify positions were transformed
        // Entity 1: (10-5+0, 20-10+0, 30-15+0) = (5, 10, 15)
        assert_eq!(entities[0].position.x, 5.0);
        assert_eq!(entities[0].position.y, 10.0);
        assert_eq!(entities[0].position.z, 15.0);
        
        // Entity 2: (50-2+0, 60-3+0, 70-4+0) = (48, 57, 66)
        assert_eq!(entities[1].position.x, 48.0);
        assert_eq!(entities[1].position.y, 57.0);
        assert_eq!(entities[1].position.z, 66.0);
    }
    
    #[test]
    fn test_cartesian_point_parsing() {
        let parser = EnhancedIFCParser::new();
        
        // Test valid IFCCARTESIANPOINT
        let valid_data = "IFCCARTESIANPOINT((1.5, 2.3, 3.7))";
        let coord_system = parser.parse_cartesian_point_system(valid_data).unwrap();
        assert_eq!(coord_system.name, "CARTESIAN");
        assert_eq!(coord_system.origin.x, 1.5);
        assert_eq!(coord_system.origin.y, 2.3);
        assert_eq!(coord_system.origin.z, 3.7);
        
        // Test invalid format
        let invalid_data = "INVALID_FORMAT";
        let result = parser.parse_cartesian_point_system(invalid_data);
        assert!(result.is_err());
        
        // Test malformed coordinates
        let malformed_data = "IFCCARTESIANPOINT((1.5,2.3))"; // Missing z coordinate
        let result = parser.parse_cartesian_point_system(malformed_data);
        assert!(result.is_err());
    }
    
    #[test]
    fn test_coordinate_system_creation() {
        let parser = EnhancedIFCParser::new();
        
        // Test known coordinate systems
        let global = parser.create_coordinate_system_by_name("GLOBAL").unwrap();
        assert_eq!(global.name, "GLOBAL");
        assert_eq!(global.origin.x, 0.0);
        assert_eq!(global.origin.y, 0.0);
        assert_eq!(global.origin.z, 0.0);
        
        let building = parser.create_coordinate_system_by_name("BUILDING_COORDINATE_SYSTEM").unwrap();
        assert_eq!(building.name, "BUILDING");
        assert_eq!(building.origin.x, 0.0);
        assert_eq!(building.origin.y, 0.0);
        assert_eq!(building.origin.z, 0.0);
        
        let floor = parser.create_coordinate_system_by_name("FLOOR_COORDINATE_SYSTEM").unwrap();
        assert_eq!(floor.name, "FLOOR");
        assert_eq!(floor.origin.x, 0.0);
        assert_eq!(floor.origin.y, 0.0);
        assert_eq!(floor.origin.z, 0.0);
        
        let room = parser.create_coordinate_system_by_name("ROOM_COORDINATE_SYSTEM").unwrap();
        assert_eq!(room.name, "ROOM");
        assert_eq!(room.origin.x, 0.0);
        assert_eq!(room.origin.y, 0.0);
        assert_eq!(room.origin.z, 0.0);
        
        // Test unknown coordinate system
        let result = parser.create_coordinate_system_by_name("UNKNOWN_SYSTEM");
        assert!(result.is_err());
    }
    
    #[test]
    fn test_equipment_relationship_parsing() {
        let parser = EnhancedIFCParser::new();
        
        // Create test entities with different equipment types
        let entities = vec![
            SpatialEntity {
                id: "DUCT_001".to_string(),
                name: "Supply Duct Segment".to_string(),
                entity_type: "IFCDUCTSEGMENT".to_string(),
                position: Point3D::new(10.0, 20.0, 3.0),
                bounding_box: BoundingBox3D {
                    min: Point3D::new(9.0, 19.0, 2.5),
                    max: Point3D::new(11.0, 21.0, 3.5),
                },
                coordinate_system: Some(CoordinateSystem::new("GLOBAL".to_string(), Point3D::origin())),
            },
            SpatialEntity {
                id: "FITTING_001".to_string(),
                name: "90 Degree Elbow".to_string(),
                entity_type: "IFCDUCTFITTING".to_string(),
                position: Point3D::new(15.0, 20.0, 3.0),
                bounding_box: BoundingBox3D {
                    min: Point3D::new(14.0, 19.0, 2.5),
                    max: Point3D::new(16.0, 21.0, 3.5),
                },
                coordinate_system: Some(CoordinateSystem::new("GLOBAL".to_string(), Point3D::origin())),
            },
            SpatialEntity {
                id: "TERMINAL_001".to_string(),
                name: "Supply Air Terminal".to_string(),
                entity_type: "IFCAIRTERMINAL".to_string(),
                position: Point3D::new(20.0, 20.0, 1.5),
                bounding_box: BoundingBox3D {
                    min: Point3D::new(19.5, 19.5, 1.0),
                    max: Point3D::new(20.5, 20.5, 2.0),
                },
                coordinate_system: Some(CoordinateSystem::new("GLOBAL".to_string(), Point3D::origin())),
            },
            SpatialEntity {
                id: "VALVE_001".to_string(),
                name: "Control Valve".to_string(),
                entity_type: "IFCFLOWCONTROLLER".to_string(),
                position: Point3D::new(12.0, 20.0, 3.0),
                bounding_box: BoundingBox3D {
                    min: Point3D::new(11.5, 19.5, 2.5),
                    max: Point3D::new(12.5, 20.5, 3.5),
                },
                coordinate_system: Some(CoordinateSystem::new("GLOBAL".to_string(), Point3D::origin())),
            },
        ];
        
        // Parse equipment relationships
        let relationships = parser.parse_equipment_relationships(&entities);
        
        // Verify relationships were created
        assert_eq!(relationships.len(), 5); // 1 duct + 2 fittings + 1 terminal + 1 valve
        
        // Verify relationship types
        let flow_connections = relationships.iter()
            .filter(|rel| rel.relationship_type == RelationshipType::FlowConnection)
            .count();
        assert_eq!(flow_connections, 4);
        
        let control_connections = relationships.iter()
            .filter(|rel| rel.relationship_type == RelationshipType::ControlConnection)
            .count();
        assert_eq!(control_connections, 1);
        
        // Verify specific relationships
        let duct_relationship = relationships.iter()
            .find(|rel| rel.from_entity_id == "DUCT_001")
            .unwrap();
        assert_eq!(duct_relationship.relationship_type, RelationshipType::FlowConnection);
        assert_eq!(duct_relationship.connection_type, Some("DUCT_SEGMENT".to_string()));
        
        let fitting_relationships = relationships.iter()
            .filter(|rel| rel.from_entity_id == "FITTING_001")
            .collect::<Vec<_>>();
        assert_eq!(fitting_relationships.len(), 2); // Inlet and outlet
        
        let terminal_relationship = relationships.iter()
            .find(|rel| rel.from_entity_id == "TERMINAL_001")
            .unwrap();
        assert_eq!(terminal_relationship.relationship_type, RelationshipType::FlowConnection);
        assert_eq!(terminal_relationship.connection_type, Some("TERMINAL".to_string()));
        
        let valve_relationship = relationships.iter()
            .find(|rel| rel.from_entity_id == "VALVE_001")
            .unwrap();
        assert_eq!(valve_relationship.relationship_type, RelationshipType::ControlConnection);
        assert_eq!(valve_relationship.connection_type, Some("CONTROLLER".to_string()));
    }
    
    #[test]
    fn test_connected_equipment_finding() {
        let parser = EnhancedIFCParser::new();
        
        // Create test relationships
        let relationships = vec![
            EquipmentRelationship {
                from_entity_id: "EQUIPMENT_001".to_string(),
                to_entity_id: "EQUIPMENT_002".to_string(),
                relationship_type: RelationshipType::FlowConnection,
                connection_type: Some("DUCT".to_string()),
                properties: vec![("length".to_string(), "10.0".to_string())],
            },
            EquipmentRelationship {
                from_entity_id: "EQUIPMENT_002".to_string(),
                to_entity_id: "EQUIPMENT_003".to_string(),
                relationship_type: RelationshipType::FlowConnection,
                connection_type: Some("FITTING".to_string()),
                properties: vec![("type".to_string(), "elbow".to_string())],
            },
            EquipmentRelationship {
                from_entity_id: "EQUIPMENT_001".to_string(),
                to_entity_id: "EQUIPMENT_004".to_string(),
                relationship_type: RelationshipType::ControlConnection,
                connection_type: Some("VALVE".to_string()),
                properties: vec![("position".to_string(), "open".to_string())],
            },
        ];
        
        // Find equipment connected to EQUIPMENT_001
        let connected = parser.find_connected_equipment("EQUIPMENT_001", &relationships);
        assert_eq!(connected.len(), 2); // EQUIPMENT_002 and EQUIPMENT_004
        
        // Find equipment connected to EQUIPMENT_002
        let connected = parser.find_connected_equipment("EQUIPMENT_002", &relationships);
        assert_eq!(connected.len(), 2); // EQUIPMENT_001 and EQUIPMENT_003
        
        // Find equipment connected to EQUIPMENT_003
        let connected = parser.find_connected_equipment("EQUIPMENT_003", &relationships);
        assert_eq!(connected.len(), 1); // EQUIPMENT_002
    }
    
    #[test]
    fn test_equipment_network_traversal() {
        let parser = EnhancedIFCParser::new();
        
        // Create a network: 001 -> 002 -> 003 -> 004
        //                  001 -> 005
        let relationships = vec![
            EquipmentRelationship {
                from_entity_id: "EQUIPMENT_001".to_string(),
                to_entity_id: "EQUIPMENT_002".to_string(),
                relationship_type: RelationshipType::FlowConnection,
                connection_type: Some("DUCT".to_string()),
                properties: vec![],
            },
            EquipmentRelationship {
                from_entity_id: "EQUIPMENT_002".to_string(),
                to_entity_id: "EQUIPMENT_003".to_string(),
                relationship_type: RelationshipType::FlowConnection,
                connection_type: Some("DUCT".to_string()),
                properties: vec![],
            },
            EquipmentRelationship {
                from_entity_id: "EQUIPMENT_003".to_string(),
                to_entity_id: "EQUIPMENT_004".to_string(),
                relationship_type: RelationshipType::FlowConnection,
                connection_type: Some("DUCT".to_string()),
                properties: vec![],
            },
            EquipmentRelationship {
                from_entity_id: "EQUIPMENT_001".to_string(),
                to_entity_id: "EQUIPMENT_005".to_string(),
                relationship_type: RelationshipType::FlowConnection,
                connection_type: Some("DUCT".to_string()),
                properties: vec![],
            },
        ];
        
        // Get network starting from EQUIPMENT_001
        let network = parser.get_equipment_network("EQUIPMENT_001", &relationships);
        assert_eq!(network.len(), 5); // All 5 equipment items
        
        // Verify all equipment is in the network
        assert!(network.contains(&"EQUIPMENT_001".to_string()));
        assert!(network.contains(&"EQUIPMENT_002".to_string()));
        assert!(network.contains(&"EQUIPMENT_003".to_string()));
        assert!(network.contains(&"EQUIPMENT_004".to_string()));
        assert!(network.contains(&"EQUIPMENT_005".to_string()));
        
        // Get network starting from EQUIPMENT_003
        let network = parser.get_equipment_network("EQUIPMENT_003", &relationships);
        assert_eq!(network.len(), 5); // All equipment items are connected through the network
        
        // Verify network contents
        assert!(network.contains(&"EQUIPMENT_001".to_string()));
        assert!(network.contains(&"EQUIPMENT_002".to_string()));
        assert!(network.contains(&"EQUIPMENT_003".to_string()));
        assert!(network.contains(&"EQUIPMENT_004".to_string()));
        assert!(network.contains(&"EQUIPMENT_005".to_string()));
    }
    
    #[test]
    fn test_system_efficiency_calculation() {
        let parser = EnhancedIFCParser::new();
        
        // Test with mixed relationship types
        let relationships = vec![
            EquipmentRelationship {
                from_entity_id: "EQUIPMENT_001".to_string(),
                to_entity_id: "EQUIPMENT_002".to_string(),
                relationship_type: RelationshipType::FlowConnection,
                connection_type: Some("DUCT".to_string()),
                properties: vec![],
            },
            EquipmentRelationship {
                from_entity_id: "EQUIPMENT_002".to_string(),
                to_entity_id: "EQUIPMENT_003".to_string(),
                relationship_type: RelationshipType::FlowConnection,
                connection_type: Some("DUCT".to_string()),
                properties: vec![],
            },
            EquipmentRelationship {
                from_entity_id: "EQUIPMENT_001".to_string(),
                to_entity_id: "EQUIPMENT_004".to_string(),
                relationship_type: RelationshipType::ControlConnection,
                connection_type: Some("VALVE".to_string()),
                properties: vec![],
            },
            EquipmentRelationship {
                from_entity_id: "EQUIPMENT_005".to_string(),
                to_entity_id: "EQUIPMENT_006".to_string(),
                relationship_type: RelationshipType::SpatialConnection,
                connection_type: Some("PROXIMITY".to_string()),
                properties: vec![],
            },
        ];
        
        let efficiency = parser.calculate_system_efficiency(&relationships);
        
        // Expected: 2 flow connections, 1 control connection, 1 spatial connection
        // Flow efficiency: 2/4 = 0.5
        // Control efficiency: 1/4 = 0.25
        // Weighted: 0.7 * 0.5 + 0.3 * 0.25 = 0.35 + 0.075 = 0.425
        assert!((efficiency - 0.425).abs() < 0.001);
        
        // Test with no relationships
        let empty_relationships = vec![];
        let efficiency = parser.calculate_system_efficiency(&empty_relationships);
        assert_eq!(efficiency, 0.0);
        
        // Test with only flow connections
        let flow_only_relationships = vec![
            EquipmentRelationship {
                from_entity_id: "EQUIPMENT_001".to_string(),
                to_entity_id: "EQUIPMENT_002".to_string(),
                relationship_type: RelationshipType::FlowConnection,
                connection_type: Some("DUCT".to_string()),
                properties: vec![],
            },
            EquipmentRelationship {
                from_entity_id: "EQUIPMENT_002".to_string(),
                to_entity_id: "EQUIPMENT_003".to_string(),
                relationship_type: RelationshipType::FlowConnection,
                connection_type: Some("DUCT".to_string()),
                properties: vec![],
            },
        ];
        
        let efficiency = parser.calculate_system_efficiency(&flow_only_relationships);
        // Expected: 2 flow connections, 0 control connections
        // Flow efficiency: 2/2 = 1.0
        // Control efficiency: 0/2 = 0.0
        // Weighted: 0.7 * 1.0 + 0.3 * 0.0 = 0.7
        assert!((efficiency - 0.7).abs() < 0.001);
    }
    
    #[test]
    fn test_spatial_index_creation() {
        let parser = EnhancedIFCParser::new();
        
        let entities = vec![
            SpatialEntity {
                id: "EQUIPMENT_001".to_string(),
                name: "Air Terminal 001".to_string(),
                entity_type: "IFCAIRTERMINAL".to_string(),
                position: Point3D { x: 10.0, y: 20.0, z: 30.0 },
                bounding_box: BoundingBox3D {
                    min: Point3D { x: 8.0, y: 18.0, z: 28.0 },
                    max: Point3D { x: 12.0, y: 22.0, z: 32.0 },
                },
                coordinate_system: None,
            },
            SpatialEntity {
                id: "EQUIPMENT_002".to_string(),
                name: "Light Fixture 002".to_string(),
                entity_type: "IFCLIGHTFIXTURE".to_string(),
                position: Point3D { x: 15.0, y: 25.0, z: 35.0 },
                bounding_box: BoundingBox3D {
                    min: Point3D { x: 13.0, y: 23.0, z: 33.0 },
                    max: Point3D { x: 17.0, y: 27.0, z: 37.0 },
                },
                coordinate_system: None,
            },
        ];
        
        let spatial_index = parser.build_spatial_index(&entities);
        
        // Verify room index
        assert_eq!(spatial_index.room_index.len(), 2); // Two different rooms based on names
        assert!(spatial_index.room_index.contains_key("ROOM_Air_Terminal_001"));
        assert!(spatial_index.room_index.contains_key("ROOM_Light_Fixture_002"));
        
        // Verify floor index (Z coordinates 30.0 and 35.0 / 10.0 = floors 3 and 3)
        assert_eq!(spatial_index.floor_index.len(), 1);
        assert!(spatial_index.floor_index.contains_key(&3));
        assert_eq!(spatial_index.floor_index[&3].len(), 2);
        
        // Verify entity cache
        assert_eq!(spatial_index.entity_cache.len(), 2);
        assert!(spatial_index.entity_cache.contains_key("EQUIPMENT_001"));
        assert!(spatial_index.entity_cache.contains_key("EQUIPMENT_002"));
    }
    
    #[test]
    fn test_rtree_bounds_calculation() {
        let entities = vec![
            SpatialEntity {
                id: "EQUIPMENT_001".to_string(),
                name: "Air Terminal 001".to_string(),
                entity_type: "IFCAIRTERMINAL".to_string(),
                position: Point3D { x: 10.0, y: 20.0, z: 30.0 },
                bounding_box: BoundingBox3D {
                    min: Point3D { x: 8.0, y: 18.0, z: 28.0 },
                    max: Point3D { x: 12.0, y: 22.0, z: 32.0 },
                },
                coordinate_system: None,
            },
            SpatialEntity {
                id: "EQUIPMENT_002".to_string(),
                name: "Light Fixture 002".to_string(),
                entity_type: "IFCLIGHTFIXTURE".to_string(),
                position: Point3D { x: 15.0, y: 25.0, z: 35.0 },
                bounding_box: BoundingBox3D {
                    min: Point3D { x: 13.0, y: 23.0, z: 33.0 },
                    max: Point3D { x: 17.0, y: 27.0, z: 37.0 },
                },
                coordinate_system: None,
            },
        ];
        
        let rtree = RTreeNode::new(&entities);
        
        // Verify bounding box calculation
        assert_eq!(rtree.bounds.min.x, 8.0);
        assert_eq!(rtree.bounds.min.y, 18.0);
        assert_eq!(rtree.bounds.min.z, 28.0);
        assert_eq!(rtree.bounds.max.x, 17.0);
        assert_eq!(rtree.bounds.max.y, 27.0);
        assert_eq!(rtree.bounds.max.z, 37.0);
        
        // Verify leaf node properties
        assert!(rtree.is_leaf);
        assert_eq!(rtree.entities.len(), 2);
    }
    
    #[test]
    fn test_spatial_queries() {
        let parser = EnhancedIFCParser::new();
        
        let entities = vec![
            SpatialEntity {
                id: "EQUIPMENT_001".to_string(),
                name: "Air Terminal 001".to_string(),
                entity_type: "IFCAIRTERMINAL".to_string(),
                position: Point3D { x: 10.0, y: 20.0, z: 30.0 },
                bounding_box: BoundingBox3D {
                    min: Point3D { x: 8.0, y: 18.0, z: 28.0 },
                    max: Point3D { x: 12.0, y: 22.0, z: 32.0 },
                },
                coordinate_system: None,
            },
            SpatialEntity {
                id: "EQUIPMENT_002".to_string(),
                name: "Light Fixture 002".to_string(),
                entity_type: "IFCLIGHTFIXTURE".to_string(),
                position: Point3D { x: 15.0, y: 25.0, z: 35.0 },
                bounding_box: BoundingBox3D {
                    min: Point3D { x: 13.0, y: 23.0, z: 33.0 },
                    max: Point3D { x: 17.0, y: 27.0, z: 37.0 },
                },
                coordinate_system: None,
            },
        ];
        
        let spatial_index = parser.build_spatial_index(&entities);
        
        // Test room query
        let room_entities = spatial_index.find_in_room("ROOM_Air_Terminal_001");
        assert_eq!(room_entities.len(), 1);
        
        // Test floor query (Z coordinates 30.0 and 35.0 / 10.0 = floors 3 and 3)
        let floor_entities = spatial_index.find_in_floor(3);
        assert_eq!(floor_entities.len(), 2);
        
        // Test nearest query
        let nearest = spatial_index.find_nearest(Point3D { x: 10.0, y: 20.0, z: 30.0 });
        assert!(nearest.is_some());
        assert_eq!(nearest.unwrap().entity.id, "EQUIPMENT_001");
        
        // Test radius query
        let radius_results = spatial_index.find_within_radius(Point3D { x: 10.0, y: 20.0, z: 30.0 }, 10.0);
        assert_eq!(radius_results.len(), 2);
        
        // Test bounding box query
        let bbox = BoundingBox3D {
            min: Point3D { x: 5.0, y: 15.0, z: 25.0 },
            max: Point3D { x: 20.0, y: 30.0, z: 40.0 },
        };
        let bbox_results = spatial_index.find_within_bounding_box(bbox);
        assert_eq!(bbox_results.len(), 2);
    }
    
    #[test]
    fn test_distance_calculations() {
        let spatial_index = SpatialIndex::new();
        
        let point1 = Point3D { x: 0.0, y: 0.0, z: 0.0 };
        let point2 = Point3D { x: 3.0, y: 4.0, z: 0.0 };
        
        let distance = spatial_index.calculate_distance(&point1, &point2);
        assert!((distance - 5.0).abs() < 0.001); // 3-4-5 triangle
        
        let point3 = Point3D { x: 1.0, y: 1.0, z: 1.0 };
        let distance3d = spatial_index.calculate_distance(&point1, &point3);
        assert!((distance3d - 1.732).abs() < 0.001); // sqrt(3) ≈ 1.732
    }
    
    #[test]
    fn test_rtree_intersection() {
        let entities = vec![
            SpatialEntity {
                id: "EQUIPMENT_001".to_string(),
                name: "Air Terminal 001".to_string(),
                entity_type: "IFCAIRTERMINAL".to_string(),
                position: Point3D { x: 10.0, y: 20.0, z: 30.0 },
                bounding_box: BoundingBox3D {
                    min: Point3D { x: 8.0, y: 18.0, z: 28.0 },
                    max: Point3D { x: 12.0, y: 22.0, z: 32.0 },
                },
                coordinate_system: None,
            },
        ];
        
        let rtree = RTreeNode::new(&entities);
        
        // Test intersection with overlapping bounding box
        let overlapping_bbox = BoundingBox3D {
            min: Point3D { x: 9.0, y: 19.0, z: 29.0 },
            max: Point3D { x: 11.0, y: 21.0, z: 31.0 },
        };
        assert!(rtree.intersects(&overlapping_bbox));
        
        // Test intersection with non-overlapping bounding box
        let non_overlapping_bbox = BoundingBox3D {
            min: Point3D { x: 20.0, y: 30.0, z: 40.0 },
            max: Point3D { x: 25.0, y: 35.0, z: 45.0 },
        };
        assert!(!rtree.intersects(&non_overlapping_bbox));
        
        // Test point containment
        let contained_point = Point3D { x: 10.0, y: 20.0, z: 30.0 };
        assert!(rtree.contains_point(&contained_point));
        
        let outside_point = Point3D { x: 20.0, y: 30.0, z: 40.0 };
        assert!(!rtree.contains_point(&outside_point));
    }
    
    #[test]
    fn test_intersection_queries() {
        let parser = EnhancedIFCParser::new();
        
        let entities = vec![
            SpatialEntity {
                id: "EQUIPMENT_001".to_string(),
                name: "Air Terminal 001".to_string(),
                entity_type: "IFCAIRTERMINAL".to_string(),
                position: Point3D { x: 10.0, y: 20.0, z: 30.0 },
                bounding_box: BoundingBox3D {
                    min: Point3D { x: 8.0, y: 18.0, z: 28.0 },
                    max: Point3D { x: 12.0, y: 22.0, z: 32.0 },
                },
                coordinate_system: None,
            },
            SpatialEntity {
                id: "EQUIPMENT_002".to_string(),
                name: "Light Fixture 002".to_string(),
                entity_type: "IFCLIGHTFIXTURE".to_string(),
                position: Point3D { x: 15.0, y: 25.0, z: 35.0 },
                bounding_box: BoundingBox3D {
                    min: Point3D { x: 13.0, y: 23.0, z: 33.0 },
                    max: Point3D { x: 17.0, y: 27.0, z: 37.0 },
                },
                coordinate_system: None,
            },
        ];
        
        let spatial_index = parser.build_spatial_index(&entities);
        
        // Test intersection query
        let intersecting_bbox = BoundingBox3D {
            min: Point3D { x: 9.0, y: 19.0, z: 29.0 },
            max: Point3D { x: 11.0, y: 21.0, z: 31.0 },
        };
        let intersection_results = spatial_index.find_intersecting(intersecting_bbox);
        assert_eq!(intersection_results.len(), 1);
        assert_eq!(intersection_results[0].entity.id, "EQUIPMENT_001");
        assert_eq!(intersection_results[0].relationship_type, SpatialRelationship::Intersects);
        
        // Test volume containment query
        let volume_bbox = BoundingBox3D {
            min: Point3D { x: 5.0, y: 15.0, z: 25.0 },
            max: Point3D { x: 20.0, y: 30.0, z: 40.0 },
        };
        let volume_results = spatial_index.find_within_volume(volume_bbox);
        assert_eq!(volume_results.len(), 2);
        
        // Test point containment query
        let contained_point = Point3D { x: 10.0, y: 20.0, z: 30.0 };
        let containing_results = spatial_index.find_containing(contained_point);
        assert_eq!(containing_results.len(), 1);
        assert_eq!(containing_results[0].entity.id, "EQUIPMENT_001");
        assert_eq!(containing_results[0].relationship_type, SpatialRelationship::Contains);
    }
    
    #[test]
    fn test_adjacent_queries() {
        let parser = EnhancedIFCParser::new();
        
        let entities = vec![
            SpatialEntity {
                id: "EQUIPMENT_001".to_string(),
                name: "Air Terminal 001".to_string(),
                entity_type: "IFCAIRTERMINAL".to_string(),
                position: Point3D { x: 10.0, y: 20.0, z: 30.0 },
                bounding_box: BoundingBox3D {
                    min: Point3D { x: 8.0, y: 18.0, z: 28.0 },
                    max: Point3D { x: 12.0, y: 22.0, z: 32.0 },
                },
                coordinate_system: None,
            },
            SpatialEntity {
                id: "EQUIPMENT_002".to_string(),
                name: "Light Fixture 002".to_string(),
                entity_type: "IFCLIGHTFIXTURE".to_string(),
                position: Point3D { x: 15.0, y: 25.0, z: 35.0 },
                bounding_box: BoundingBox3D {
                    min: Point3D { x: 13.0, y: 23.0, z: 33.0 },
                    max: Point3D { x: 17.0, y: 27.0, z: 37.0 },
                },
                coordinate_system: None,
            },
        ];
        
        let spatial_index = parser.build_spatial_index(&entities);
        
        // Test adjacent queries
        let adjacent_results = spatial_index.find_adjacent(Point3D { x: 10.0, y: 20.0, z: 30.0 }, 10.0);
        assert_eq!(adjacent_results.len(), 2);
        assert_eq!(adjacent_results[0].relationship_type, SpatialRelationship::Adjacent);
    }
    
    #[test]
    fn test_equipment_clustering() {
        let parser = EnhancedIFCParser::new();
        
        let entities = vec![
            SpatialEntity {
                id: "EQUIPMENT_001".to_string(),
                name: "Air Terminal 001".to_string(),
                entity_type: "IFCAIRTERMINAL".to_string(),
                position: Point3D { x: 10.0, y: 20.0, z: 30.0 },
                bounding_box: BoundingBox3D {
                    min: Point3D { x: 8.0, y: 18.0, z: 28.0 },
                    max: Point3D { x: 12.0, y: 22.0, z: 32.0 },
                },
                coordinate_system: None,
            },
            SpatialEntity {
                id: "EQUIPMENT_002".to_string(),
                name: "Light Fixture 002".to_string(),
                entity_type: "IFCLIGHTFIXTURE".to_string(),
                position: Point3D { x: 11.0, y: 21.0, z: 31.0 },
                bounding_box: BoundingBox3D {
                    min: Point3D { x: 9.0, y: 19.0, z: 29.0 },
                    max: Point3D { x: 13.0, y: 23.0, z: 33.0 },
                },
                coordinate_system: None,
            },
            SpatialEntity {
                id: "EQUIPMENT_003".to_string(),
                name: "Light Fixture 003".to_string(),
                entity_type: "IFCLIGHTFIXTURE".to_string(),
                position: Point3D { x: 50.0, y: 60.0, z: 70.0 },
                bounding_box: BoundingBox3D {
                    min: Point3D { x: 48.0, y: 58.0, z: 68.0 },
                    max: Point3D { x: 52.0, y: 62.0, z: 72.0 },
                },
                coordinate_system: None,
            },
        ];
        
        let spatial_index = parser.build_spatial_index(&entities);
        
        // Test equipment clustering with a very large radius to ensure we find the cluster
        let clusters = spatial_index.find_equipment_clusters(20.0, 2);
        assert_eq!(clusters.len(), 1); // Should find one cluster with 2 equipment items
        
        // Verify the cluster contains the expected equipment
        assert_eq!(clusters[0].len(), 2);
        let cluster_ids: Vec<String> = clusters[0].iter().map(|e| e.id.clone()).collect();
        assert!(cluster_ids.contains(&"EQUIPMENT_001".to_string()));
        assert!(cluster_ids.contains(&"EQUIPMENT_002".to_string()));
        
        // Test system-specific queries
        let hvac_equipment = spatial_index.find_equipment_by_system("AIR", Point3D { x: 10.0, y: 20.0, z: 30.0 }, 10.0);
        assert_eq!(hvac_equipment.len(), 1);
        assert_eq!(hvac_equipment[0].entity.entity_type, "IFCAIRTERMINAL");
        
        let light_equipment = spatial_index.find_equipment_by_system("LIGHT", Point3D { x: 10.0, y: 20.0, z: 30.0 }, 10.0);
        assert_eq!(light_equipment.len(), 1);
        assert_eq!(light_equipment[0].entity.entity_type, "IFCLIGHTFIXTURE");
    }
    
    #[test]
    fn test_cross_floor_queries() {
        let parser = EnhancedIFCParser::new();
        
        let entities = vec![
            SpatialEntity {
                id: "EQUIPMENT_001".to_string(),
                name: "Air Terminal 001".to_string(),
                entity_type: "IFCAIRTERMINAL".to_string(),
                position: Point3D { x: 10.0, y: 20.0, z: 30.0 },
                bounding_box: BoundingBox3D {
                    min: Point3D { x: 8.0, y: 18.0, z: 28.0 },
                    max: Point3D { x: 12.0, y: 22.0, z: 32.0 },
                },
                coordinate_system: None,
            },
            SpatialEntity {
                id: "EQUIPMENT_002".to_string(),
                name: "Vertical Duct 002".to_string(),
                entity_type: "IFCDUCTSEGMENT".to_string(),
                position: Point3D { x: 15.0, y: 25.0, z: 50.0 },
                bounding_box: BoundingBox3D {
                    min: Point3D { x: 13.0, y: 23.0, z: 10.0 }, // Spans from floor 1 to floor 5
                    max: Point3D { x: 17.0, y: 27.0, z: 55.0 },
                },
                coordinate_system: None,
            },
        ];
        
        let spatial_index = parser.build_spatial_index(&entities);
        
        // Test cross-floor entity detection
        let cross_floor_entities = spatial_index.find_cross_floor_entities(2, 4);
        assert_eq!(cross_floor_entities.len(), 1);
        assert_eq!(cross_floor_entities[0].id, "EQUIPMENT_002");
    }
    
    #[test]
    fn test_intersection_point_calculation() {
        let spatial_index = SpatialIndex::new();
        
        let bbox1 = BoundingBox3D {
            min: Point3D { x: 0.0, y: 0.0, z: 0.0 },
            max: Point3D { x: 10.0, y: 10.0, z: 10.0 },
        };
        
        let bbox2 = BoundingBox3D {
            min: Point3D { x: 5.0, y: 5.0, z: 5.0 },
            max: Point3D { x: 15.0, y: 15.0, z: 15.0 },
        };
        
        let intersection_points = spatial_index.calculate_intersection_points(&bbox1, &bbox2);
        assert_eq!(intersection_points.len(), 4); // Should have 4 corner points
        
        // Test non-intersecting bounding boxes
        let bbox3 = BoundingBox3D {
            min: Point3D { x: 20.0, y: 20.0, z: 20.0 },
            max: Point3D { x: 30.0, y: 30.0, z: 30.0 },
        };
        
        let no_intersection = spatial_index.calculate_intersection_points(&bbox1, &bbox3);
        assert_eq!(no_intersection.len(), 0); // Should have no intersection points
    }
    
    #[test]
    fn test_advanced_geometric_calculations() {
        let spatial_index = SpatialIndex::new();
        
        let bbox1 = BoundingBox3D {
            min: Point3D { x: 0.0, y: 0.0, z: 0.0 },
            max: Point3D { x: 10.0, y: 10.0, z: 10.0 },
        };
        
        let bbox2 = BoundingBox3D {
            min: Point3D { x: 5.0, y: 5.0, z: 5.0 },
            max: Point3D { x: 15.0, y: 15.0, z: 15.0 },
        };
        
        // Test intersection area calculation
        let intersection_area = spatial_index.calculate_intersection_area(&bbox1, &bbox2);
        assert!((intersection_area - 25.0).abs() < 0.001); // 5x5 intersection area
        
        // Test intersection volume calculation
        let intersection_volume = spatial_index.calculate_intersection_volume(&bbox1, &bbox2);
        assert!((intersection_volume - 125.0).abs() < 0.001); // 5x5x5 intersection volume
        
        // Test overlap percentage calculation
        let overlap_percentage = spatial_index.calculate_overlap_percentage(&bbox1, &bbox2);
        assert!(overlap_percentage > 0.0 && overlap_percentage < 1.0);
        
        // Test non-intersecting bounding boxes
        let bbox3 = BoundingBox3D {
            min: Point3D { x: 20.0, y: 20.0, z: 20.0 },
            max: Point3D { x: 30.0, y: 30.0, z: 30.0 },
        };
        
        let no_intersection_area = spatial_index.calculate_intersection_area(&bbox1, &bbox3);
        assert_eq!(no_intersection_area, 0.0);
        
        let no_intersection_volume = spatial_index.calculate_intersection_volume(&bbox1, &bbox3);
        assert_eq!(no_intersection_volume, 0.0);
    }
    
    #[test]
    fn test_spatial_relationship_analysis() {
        let spatial_index = SpatialIndex::new();
        
        let entity1 = SpatialEntity {
            id: "ENTITY_001".to_string(),
            name: "Entity 1".to_string(),
            entity_type: "IFCAIRTERMINAL".to_string(),
            position: Point3D { x: 10.0, y: 10.0, z: 10.0 },
            bounding_box: BoundingBox3D {
                min: Point3D { x: 8.0, y: 8.0, z: 8.0 },
                max: Point3D { x: 12.0, y: 12.0, z: 12.0 },
            },
            coordinate_system: None,
        };
        
        let entity2 = SpatialEntity {
            id: "ENTITY_002".to_string(),
            name: "Entity 2".to_string(),
            entity_type: "IFCLIGHTFIXTURE".to_string(),
            position: Point3D { x: 11.0, y: 11.0, z: 11.0 },
            bounding_box: BoundingBox3D {
                min: Point3D { x: 9.0, y: 9.0, z: 9.0 },
                max: Point3D { x: 13.0, y: 13.0, z: 13.0 },
            },
            coordinate_system: None,
        };
        
        let entity3 = SpatialEntity {
            id: "ENTITY_003".to_string(),
            name: "Entity 3".to_string(),
            entity_type: "IFCFAN".to_string(),
            position: Point3D { x: 50.0, y: 50.0, z: 50.0 },
            bounding_box: BoundingBox3D {
                min: Point3D { x: 48.0, y: 48.0, z: 48.0 },
                max: Point3D { x: 52.0, y: 52.0, z: 52.0 },
            },
            coordinate_system: None,
        };
        
        // Test intersecting entities
        let relationship1 = spatial_index.analyze_spatial_relationships(&entity1, &entity2);
        assert_eq!(relationship1, SpatialRelationship::Intersects);
        
        // Test non-intersecting entities
        let relationship2 = spatial_index.analyze_spatial_relationships(&entity1, &entity3);
        assert_eq!(relationship2, SpatialRelationship::Overlaps);
        
        // Test geometric similarity
        let similarity = spatial_index.calculate_geometric_similarity(&entity1, &entity2);
        assert!(similarity > 0.0 && similarity <= 1.0);
        
        let low_similarity = spatial_index.calculate_geometric_similarity(&entity1, &entity3);
        assert!(low_similarity < similarity); // Should be less similar
    }
    
    #[test]
    fn test_geometric_conflict_detection() {
        let spatial_index = SpatialIndex::new();
        
        let entities = vec![
            SpatialEntity {
                id: "ENTITY_001".to_string(),
                name: "Entity 1".to_string(),
                entity_type: "IFCAIRTERMINAL".to_string(),
                position: Point3D { x: 10.0, y: 10.0, z: 10.0 },
                bounding_box: BoundingBox3D {
                    min: Point3D { x: 8.0, y: 8.0, z: 8.0 },
                    max: Point3D { x: 12.0, y: 12.0, z: 12.0 },
                },
                coordinate_system: None,
            },
            SpatialEntity {
                id: "ENTITY_002".to_string(),
                name: "Entity 2".to_string(),
                entity_type: "IFCLIGHTFIXTURE".to_string(),
                position: Point3D { x: 11.0, y: 11.0, z: 11.0 },
                bounding_box: BoundingBox3D {
                    min: Point3D { x: 9.0, y: 9.0, z: 9.0 },
                    max: Point3D { x: 13.0, y: 13.0, z: 13.0 },
                },
                coordinate_system: None,
            },
        ];
        
        let conflicts = spatial_index.detect_geometric_conflicts(&entities);
        
        // Should detect overlap conflict
        assert!(!conflicts.is_empty());
        assert_eq!(conflicts[0].conflict_type, ConflictType::Overlap);
        assert_eq!(conflicts[0].entity1_id, "ENTITY_001");
        assert_eq!(conflicts[0].entity2_id, "ENTITY_002");
        assert!(conflicts[0].intersection_volume > 0.0);
        assert!(!conflicts[0].resolution_suggestions.is_empty());
    }
    
    #[test]
    fn test_spatial_index_optimization() {
        let entities = vec![
            SpatialEntity {
                id: "ENTITY_001".to_string(),
                name: "Entity 1".to_string(),
                entity_type: "IFCAIRTERMINAL".to_string(),
                position: Point3D { x: 10.0, y: 10.0, z: 10.0 },
                bounding_box: BoundingBox3D {
                    min: Point3D { x: 8.0, y: 8.0, z: 8.0 },
                    max: Point3D { x: 12.0, y: 12.0, z: 12.0 },
                },
                coordinate_system: None,
            },
        ];
        
        // Build initial spatial index
        let mut spatial_index = EnhancedIFCParser::new().build_spatial_index(&entities);
        
        // Optimize the spatial index
        let result = spatial_index.optimize_spatial_index();
        assert!(result.is_ok());
        
        // Verify the optimization worked
        let metrics = spatial_index.calculate_query_performance_metrics();
        assert!(metrics.memory_usage_mb >= 0.0);
        assert!(metrics.spatial_index_size_bytes > 0);
    }
    
    #[test]
    fn test_aspect_ratio_calculation() {
        let spatial_index = SpatialIndex::new();
        
        // Test cubic bounding box
        let cubic_bbox = BoundingBox3D {
            min: Point3D { x: 0.0, y: 0.0, z: 0.0 },
            max: Point3D { x: 10.0, y: 10.0, z: 10.0 },
        };
        let cubic_aspect = spatial_index.calculate_aspect_ratio(&cubic_bbox);
        assert!((cubic_aspect - 1.0).abs() < 0.001); // Should be 1.0 for a cube
        
        // Test rectangular bounding box
        let rectangular_bbox = BoundingBox3D {
            min: Point3D { x: 0.0, y: 0.0, z: 0.0 },
            max: Point3D { x: 20.0, y: 5.0, z: 5.0 },
        };
        let rectangular_aspect = spatial_index.calculate_aspect_ratio(&rectangular_bbox);
        assert!(rectangular_aspect > 1.0); // Should be greater than 1.0 for a rectangle
    }
    
    #[test]
    fn test_minimum_clearance_calculation() {
        let spatial_index = SpatialIndex::new();
        
        let entity1 = SpatialEntity {
            id: "ENTITY_001".to_string(),
            name: "Entity 1".to_string(),
            entity_type: "IFCELECTRICMOTOR".to_string(),
            position: Point3D { x: 10.0, y: 10.0, z: 10.0 },
            bounding_box: BoundingBox3D {
                min: Point3D { x: 8.0, y: 8.0, z: 8.0 },
                max: Point3D { x: 12.0, y: 12.0, z: 12.0 },
            },
            coordinate_system: None,
        };
        
        let entity2 = SpatialEntity {
            id: "ENTITY_002".to_string(),
            name: "Entity 2".to_string(),
            entity_type: "IFCELECTRICGENERATOR".to_string(),
            position: Point3D { x: 15.0, y: 15.0, z: 15.0 },
            bounding_box: BoundingBox3D {
                min: Point3D { x: 13.0, y: 13.0, z: 13.0 },
                max: Point3D { x: 17.0, y: 17.0, z: 17.0 },
            },
            coordinate_system: None,
        };
        
        let clearance = spatial_index.calculate_minimum_clearance(&entity1, &entity2);
        assert!(clearance > 0.0);
        assert!(clearance >= 0.3); // Should be at least the base clearance for electrical equipment
    }
}
