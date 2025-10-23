//! Enhanced IFC parser with partial parsing and error recovery

use crate::core::Building;
use crate::spatial::{Point3D, BoundingBox3D, SpatialEntity};
use crate::progress::ProgressContext;
use crate::error::{ArxError, ArxResult};
use log::{info, warn};

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
                 "IFCSPACE" | "IFCROOM" | "IFCZONE" | 
                 "IFCFLOWTERMINAL" | "IFCFLOWFITTING" | "IFCFLOWSEGMENT" |
                 "IFCDISTRIBUTIONELEMENT" | "IFCFLOWCONTROLLER")
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
    
    /// Parse placement data from IFC ObjectPlacement
    fn parse_placement_data(&self, placement_data: &str) -> Result<Point3D, Box<dyn std::error::Error>> {
        // Parse IFC placement format: #12345=IFCLOCALPLACEMENT(#12346,#12347)
        if let Some(start) = placement_data.find('(') {
            if let Some(end) = placement_data.find(')') {
                let coords_str = &placement_data[start+1..end];
                let coords: Vec<&str> = coords_str.split(',').collect();
                
                if coords.len() >= 3 {
                    let x = coords[0].trim().parse::<f64>().unwrap_or(0.0);
                    let y = coords[1].trim().parse::<f64>().unwrap_or(0.0);
                    let z = coords[2].trim().parse::<f64>().unwrap_or(0.0);
                    return Ok(Point3D::new(x, y, z));
                }
            }
        }
        
        Err("Invalid placement data format".into())
    }
    
    /// Parse geometry placement from IFC Representation
    fn parse_geometry_placement(&self, geometry_data: &str) -> Result<Point3D, Box<dyn std::error::Error>> {
        // Parse IFC geometry format for positioning
        // This is a simplified parser - real implementation would be more complex
        
        // Look for coordinate patterns in the geometry data
        let mut x = 0.0;
        let mut y = 0.0;
        let mut z = 0.0;
        let mut coord_count = 0;
        
        // Extract coordinates using regex-like pattern matching
        let words: Vec<&str> = geometry_data.split_whitespace().collect();
        for (_i, word) in words.iter().enumerate() {
            if let Ok(coord) = word.parse::<f64>() {
                match coord_count % 3 {
                    0 => x += coord,
                    1 => y += coord,
                    2 => z += coord,
                    _ => {}
                }
                coord_count += 1;
            }
        }
        
        if coord_count > 0 {
            Ok(Point3D::new(
                x / (coord_count as f64 / 3.0).ceil(),
                y / (coord_count as f64 / 3.0).ceil(),
                z / (coord_count as f64 / 3.0).ceil(),
            ))
        } else {
            Err("No coordinates found in geometry data".into())
        }
    }
    
    /// Generate deterministic position based on entity properties
    fn generate_deterministic_position(&self, entity: &IFCEntity) -> Result<Point3D, Box<dyn std::error::Error>> {
        // Use entity ID hash for deterministic positioning
        let id_hash = self.hash_string(&entity.id);
        let name_hash = self.hash_string(&entity.id);
        
        // Generate coordinates based on entity type and properties
        let position = match entity.entity_type.as_str() {
            "IFCSPACE" => {
                // Spaces are distributed across floors
                let floor_height = 3.0; // Standard floor height
                let floor = (id_hash % 5) as f64; // 0-4 floors
                Point3D::new(
                    (id_hash % 1000) as f64 / 10.0, // X: 0-100m
                    (name_hash % 800) as f64 / 10.0, // Y: 0-80m  
                    floor * floor_height + 0.1,     // Z: Floor level
                )
            },
            "IFCFLOWTERMINAL" => {
                // Flow terminals are typically wall-mounted
                let floor_height = 3.0;
                let floor = (id_hash % 5) as f64;
                Point3D::new(
                    (id_hash % 1000) as f64 / 10.0,
                    (name_hash % 800) as f64 / 10.0,
                    floor * floor_height + 1.5, // Wall-mounted height
                )
            },
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
            "IFCSPACE" => (10.0, 3.0, 8.0),        // Typical room size
            "IFCFLOWTERMINAL" => (0.3, 0.3, 0.1),   // Small terminal
            "IFCWALL" => (0.2, 3.0, 5.0),          // Wall dimensions
            "IFCDOOR" => (0.9, 2.1, 0.1),          // Door dimensions
            "IFCWINDOW" => (1.5, 1.2, 0.1),        // Window dimensions
            "IFCCOLUMN" => (0.4, 3.0, 0.4),        // Column dimensions
            "IFCSLAB" => (10.0, 0.2, 8.0),         // Slab dimensions
            "IFCBEAM" => (8.0, 0.3, 0.3),          // Beam dimensions
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
    fn test_building_entity_detection() {
        let parser = EnhancedIFCParser::new();
        
        assert!(parser.is_building_entity("IFCBUILDING"));
        assert!(parser.is_building_entity("IFCSITE"));
        assert!(!parser.is_building_entity("IFCSPACE"));
    }
}
