// IFC processing for ArxOS using custom STEP parser
use crate::core::Building;
use crate::progress::ProgressContext;
use std::path::Path;
use log::{info, warn};

mod error;
mod fallback;
mod enhanced;
pub use error::{IFCError, IFCResult};
pub use fallback::FallbackIFCParser;
pub use enhanced::{EnhancedIFCParser, ParseResult, ParseStats};

pub struct IFCProcessor {
    // Custom STEP parser implementation
}

impl IFCProcessor {
    pub fn new() -> Self {
        Self {}
    }
    
    pub fn process_file(&self, file_path: &str) -> IFCResult<(Building, Vec<crate::spatial::SpatialEntity>)> {
        info!("Processing IFC file: {}", file_path);

        // Check if file exists
        if !Path::new(file_path).exists() {
            return Err(IFCError::FileNotFound {
                path: file_path.to_string()
            });
        }

        // Check file extension
        if !file_path.to_lowercase().ends_with(".ifc") {
            warn!("File does not have .ifc extension: {}", file_path);
        }
        
        // Use custom STEP parser
        match self.fallback_parsing(file_path) {
            Ok((building, spatial_entities)) => {
                info!("Successfully parsed with custom STEP parser");
                Ok((building, spatial_entities))
            }
            Err(e) => {
                warn!("Custom STEP parsing failed: {}", e);
                Err(e)
            }
        }
    }
    
    /// Process IFC file with parallel processing and progress reporting
    pub fn process_file_parallel(&self, file_path: &str) -> IFCResult<(Building, Vec<crate::spatial::SpatialEntity>)> {
        info!("Processing IFC file with parallel processing: {}", file_path);

        // Check if file exists
        if !Path::new(file_path).exists() {
            return Err(IFCError::FileNotFound {
                path: file_path.to_string()
            });
        }

        // Check file extension
        if !file_path.to_lowercase().ends_with(".ifc") {
            warn!("File does not have .ifc extension: {}", file_path);
        }
        
        // Use parallel custom STEP parser
        match self.fallback_parsing_parallel(file_path) {
            Ok((building, spatial_entities)) => {
                info!("Successfully parsed with parallel custom STEP parser");
                Ok((building, spatial_entities))
            }
            Err(e) => {
                warn!("Parallel custom STEP parsing failed: {}", e);
                Err(e)
            }
        }
    }
    
    /// Process IFC file with progress reporting
    pub fn process_file_with_progress(&self, file_path: &str, progress: ProgressContext) -> IFCResult<(Building, Vec<crate::spatial::SpatialEntity>)> {
        info!("Processing IFC file with progress reporting: {}", file_path);
        
        progress.update(10, "Reading IFC file...");
        
        // Check if file exists
        if !Path::new(file_path).exists() {
            progress.finish_error("IFC file not found");
            return Err(IFCError::FileNotFound {
                path: file_path.to_string()
            });
        }

        // Check file extension
        if !file_path.to_lowercase().ends_with(".ifc") {
            warn!("File does not have .ifc extension: {}", file_path);
        }
        
        progress.update(20, "Parsing IFC entities...");
        
        // Use custom STEP parser with progress
        match self.fallback_parsing_with_progress(file_path, progress) {
            Ok((building, spatial_entities)) => {
                info!("Successfully parsed with custom STEP parser");
                Ok((building, spatial_entities))
            }
            Err(e) => {
                warn!("Custom STEP parsing failed: {}", e);
                Err(e)
            }
        }
    }
    
    fn fallback_parsing(&self, file_path: &str) -> IFCResult<(Building, Vec<crate::spatial::SpatialEntity>)> {
        info!("Using custom STEP parser");
        let parser = FallbackIFCParser::new();
        parser.parse_ifc_file(file_path).map_err(|e| IFCError::ParsingError {
            message: e.to_string()
        })
    }
    
    fn fallback_parsing_parallel(&self, file_path: &str) -> IFCResult<(Building, Vec<crate::spatial::SpatialEntity>)> {
        info!("Using parallel custom STEP parser");
        let parser = FallbackIFCParser::new();
        parser.parse_ifc_file_parallel(file_path).map_err(|e| IFCError::ParsingError {
            message: e.to_string()
        })
    }
    
    fn fallback_parsing_with_progress(&self, file_path: &str, progress: ProgressContext) -> IFCResult<(Building, Vec<crate::spatial::SpatialEntity>)> {
        info!("Using custom STEP parser with progress");
        let parser = FallbackIFCParser::new();
        
        progress.update(30, "Initializing parser...");
        
        // Parse with progress updates
        let result = parser.parse_ifc_file_with_progress(file_path, progress);
        
        match result {
            Ok((building, spatial_entities)) => {
                info!("Successfully parsed with progress reporting");
                Ok((building, spatial_entities))
            }
            Err(e) => {
                warn!("Parsing with progress failed: {}", e);
                Err(IFCError::ParsingError {
                    message: e.to_string()
                })
            }
        }
    }
    
    pub fn validate_ifc_file(&self, file_path: &str) -> IFCResult<bool> {
        info!("Validating IFC file: {}", file_path);
        
        if !Path::new(file_path).exists() {
            return Err(IFCError::FileNotFound { 
                path: file_path.to_string() 
            });
        }
        
        // Check file extension
        if !file_path.to_lowercase().ends_with(".ifc") {
            return Err(IFCError::InvalidFormat { 
                reason: "File must have .ifc extension".to_string() 
            });
        }
        
        // Check file size
        let metadata = std::fs::metadata(file_path)?;
        if metadata.len() == 0 {
            return Err(IFCError::InvalidFormat { 
                reason: "File is empty".to_string() 
            });
        }
        
        // Read file content for format validation
        let content = std::fs::read_to_string(file_path)?;
        
        // Validate IFC file structure
        self.validate_ifc_structure(&content)?;
        
        info!("IFC file validation passed");
        Ok(true)
    }
    
    /// Process IFC file with enhanced error recovery
    pub fn process_file_with_recovery(&self, file_path: &str) -> Result<ParseResult, Box<dyn std::error::Error>> {
        info!("Processing IFC file with enhanced error recovery: {}", file_path);
        
        let mut parser = EnhancedIFCParser::new();
        parser.parse_with_recovery(file_path).map_err(|e| e.into())
    }
    
    /// Process IFC file with progress and error recovery
    pub fn process_file_with_progress_and_recovery(&self, file_path: &str, progress: ProgressContext) -> Result<ParseResult, Box<dyn std::error::Error>> {
        info!("Processing IFC file with progress and error recovery: {}", file_path);
        
        let mut parser = EnhancedIFCParser::new();
        parser.parse_with_progress_and_recovery(file_path, progress).map_err(|e| e.into())
    }
    
    /// Validate IFC file structure and format
    fn validate_ifc_structure(&self, content: &str) -> IFCResult<()> {
        let lines: Vec<&str> = content.lines().collect();
        
        if lines.is_empty() {
            return Err(IFCError::InvalidFormat { 
                reason: "File contains no content".to_string() 
            });
        }
        
        // Check for ISO-10303-21 header
        if !lines[0].starts_with("ISO-10303-21;") {
            return Err(IFCError::InvalidFormat { 
                reason: "Missing ISO-10303-21 header".to_string() 
            });
        }
        
        // Check for required sections
        let mut has_header = false;
        let mut has_data = false;
        let mut has_endsec = false;
        
        for line in lines.iter() {
            let line = line.trim();
            if line == "HEADER;" {
                has_header = true;
            } else if line == "DATA;" {
                has_data = true;
            } else if line == "ENDSEC;" {
                has_endsec = true;
            }
        }
        
        if !has_header {
            return Err(IFCError::InvalidFormat { 
                reason: "Missing HEADER section".to_string() 
            });
        }
        
        if !has_data {
            return Err(IFCError::InvalidFormat { 
                reason: "Missing DATA section".to_string() 
            });
        }
        
        if !has_endsec {
            return Err(IFCError::InvalidFormat { 
                reason: "Missing ENDSEC section".to_string() 
            });
        }
        
        // Check for proper ending
        if !content.trim_end().ends_with("END-ISO-10303-21;") {
            return Err(IFCError::InvalidFormat { 
                reason: "Missing END-ISO-10303-21 footer".to_string() 
            });
        }
        
        // Check for at least one entity definition
        let has_entities = lines.iter().any(|line| line.starts_with("#") && line.contains("="));
        if !has_entities {
            return Err(IFCError::InvalidFormat { 
                reason: "No entity definitions found".to_string() 
            });
        }
        
        Ok(())
    }
}

#[derive(Debug, Clone)]
pub struct BoundingBox {
    pub min_x: f64,
    pub min_y: f64,
    pub min_z: f64,
    pub max_x: f64,
    pub max_y: f64,
    pub max_z: f64,
}
