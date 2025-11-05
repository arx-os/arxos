//! Main parser implementation for enhanced IFC parsing

use super::types::{EnhancedIFCParser, ParseStats, ParseResult, IFCEntity};
use crate::core::Building;
use crate::spatial::SpatialEntity;
use crate::utils::progress::ProgressContext;
use crate::error::{ArxError, ArxResult};
use log::{info, warn};

impl Default for EnhancedIFCParser {
    fn default() -> Self {
        Self::new()
    }
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
    
    /// Validate IFC file size before processing
    fn validate_file_size(&self, file_path: &str) -> ArxResult<()> {
        use std::fs::metadata;
        
        let metadata = metadata(file_path)
            .map_err(|e| ArxError::io_error(format!("Cannot read file metadata: {}", e))
                .with_file_path(file_path))?;
        
        let file_size_bytes = metadata.len();
        let file_size_mb = file_size_bytes / (1024 * 1024);
        
        const MAX_FILE_SIZE_MB: u64 = 500;
        const WARNING_THRESHOLD_MB: u64 = 100;
        
        if file_size_mb > MAX_FILE_SIZE_MB {
            return Err(ArxError::ifc_processing(format!(
                "IFC file too large: {}MB exceeds maximum of {}MB",
                file_size_mb, MAX_FILE_SIZE_MB
            ))
            .with_file_path(file_path)
            .with_suggestions(vec![
                format!("File size: {}MB (max: {}MB)", file_size_mb, MAX_FILE_SIZE_MB),
                "Consider using a streaming parser for large files".to_string(),
                "Reduce file size by exporting fewer elements from BIM software".to_string(),
            ])
            .with_recovery(vec![
                "Use IFC file optimization tools".to_string(),
                "Export only required building elements".to_string(),
                "Contact support for streaming parser feature (future)".to_string(),
            ]));
        }
        
        if file_size_mb > WARNING_THRESHOLD_MB {
            info!("Warning: Large IFC file detected ({}MB). Processing may take longer.", file_size_mb);
        }
        
        Ok(())
    }
    
    /// Safely read file content with comprehensive error handling
    fn read_file_safely(&self, file_path: &str) -> ArxResult<String> {
        use crate::utils::path_safety::PathSafety;
        use std::path::Path;
        
        // Validate file path with path safety first
        let current_dir = std::env::current_dir()
            .map_err(|e| ArxError::io_error(format!("Cannot get current directory: {}", e)))?;
        let file_path_buf = Path::new(file_path);
        let validated_path = if file_path_buf.is_absolute() {
            PathSafety::canonicalize_and_validate(file_path_buf, &current_dir)
                .map_err(|e| ArxError::io_error(format!("Path validation failed: {}", e))
                    .with_file_path(file_path))?
        } else {
            let joined = current_dir.join(file_path_buf);
            PathSafety::canonicalize_and_validate(&joined, &current_dir)
                .map_err(|e| ArxError::io_error(format!("Path validation failed: {}", e))
                    .with_file_path(file_path))?
        };
        
        // Check if file exists
        if !validated_path.exists() {
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
        if !validated_path.to_string_lossy().to_lowercase().ends_with(".ifc") {
            warn!("File does not have .ifc extension: {}", validated_path.display());
        }
        
        // Validate file size before reading
        self.validate_file_size(validated_path.to_str()
            .ok_or_else(|| ArxError::io_error("Invalid file path encoding")
                .with_file_path(file_path))?)?;
        
        // Read file content using path-safe method
        match PathSafety::read_file_safely(&validated_path, &current_dir) {
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
                Err(ArxError::io_error(format!("Failed to read IFC file: {}", e))
                    .with_file_path(file_path)
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
            Some(mut entity) => {
                entity.line_number = line_num;
                Ok(Some(entity))
            }
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
            let start = match param_str.find('(') {
                Some(pos) => pos + 1,
                None => {
                    warn!("Missing opening parenthesis in parameter: {}", param_str);
                    return None;
                }
            };
            let end = match param_str.rfind(')') {
                Some(pos) => pos,
                None => {
                    warn!("Missing closing parenthesis in parameter: {}", param_str);
                    return None;
                }
            };
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
        use super::positioning;
        
        match positioning::extract_spatial_data(self, entity) {
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
    
    /// Build spatial index from spatial entities
    pub fn build_spatial_index(&self, entities: &[SpatialEntity]) -> super::types::SpatialIndex {
        use std::collections::HashMap;
        
        // Pre-allocate HashMaps with estimated capacity for better performance
        let entity_count = entities.len();
        let mut entity_cache = HashMap::with_capacity(entity_count);
        let mut room_index = HashMap::with_capacity(entity_count / 10); // Estimate: ~10 entities per room
        let mut floor_index = HashMap::with_capacity(10); // Estimate: few floors
        
        // Build room and floor indices
        for entity in entities {
            // Clone entity once (needed for cache)
            let entity_id = entity.id.clone();
            entity_cache.insert(entity_id.clone(), entity.clone());
            
            // Build room_id efficiently - pre-allocate capacity
            let mut room_id = String::with_capacity(entity.name.len() + 6); // "ROOM_" + name
            room_id.push_str("ROOM_");
            room_id.push_str(&entity.name.replace(" ", "_"));
            
            // Use entry API efficiently - move room_id instead of cloning
            room_index.entry(room_id)
                .or_insert_with(Vec::new)
                .push(entity_id.clone());
            
            // For now, use a default floor based on Z coordinate
            let floor = (entity.position.z / 10.0) as i32;
            floor_index.entry(floor)
                .or_insert_with(Vec::new)
                .push(entity_id); // Single clone per entity
        }
        
        // Build R-Tree
        use super::types::RTreeNode;
        let rtree = RTreeNode::new(entities);
        
        super::types::SpatialIndex {
            rtree,
            room_index,
            floor_index,
            entity_cache,
            query_times: Vec::new(),
            cache_hits: 0,
            cache_misses: 0,
        }
    }
    
    /// Generate a simple hash from a string for deterministic positioning
    pub fn hash_string(&self, s: &str) -> u64 {
        let mut hash = 5381u64;
        for byte in s.bytes() {
            hash = hash.wrapping_mul(33).wrapping_add(byte as u64);
        }
        hash
    }
}
