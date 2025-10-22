// IFC processing for ArxOS using custom STEP parser
use crate::core::Building;
use std::path::Path;
use log::{info, warn};

mod error;
mod fallback;
pub use error::{IFCError, IFCResult};
pub use fallback::FallbackIFCParser;

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
    
    fn fallback_parsing(&self, file_path: &str) -> IFCResult<(Building, Vec<crate::spatial::SpatialEntity>)> {
        info!("Using custom STEP parser");
        let parser = FallbackIFCParser::new();
        parser.parse_ifc_file(file_path).map_err(|e| IFCError::ParsingError {
            message: e.to_string()
        })
    }
    
    pub fn extract_spatial_data(&self, _ifc_data: &[u8]) -> IFCResult<Vec<crate::spatial::SpatialEntity>> {
        info!("Extracting spatial data from IFC");
        // TODO: Extract spatial data from IFC
        // This will use custom STEP parser to parse entities and extract coordinates
        Ok(vec![])
    }
    
    pub fn validate_ifc_file(&self, file_path: &str) -> IFCResult<bool> {
        info!("Validating IFC file: {}", file_path);
        
        if !Path::new(file_path).exists() {
            return Err(IFCError::FileNotFound { 
                path: file_path.to_string() 
            });
        }
        
        // TODO: Implement real IFC validation
        // For now, just check if file exists and has content
        let metadata = std::fs::metadata(file_path)?;
        if metadata.len() == 0 {
            return Err(IFCError::InvalidFormat { 
                reason: "File is empty".to_string() 
            });
        }
        
        info!("IFC file validation passed");
        Ok(true)
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
