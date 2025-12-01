// IFC processing for ArxOS using custom STEP parser
use crate::core::{Building, Floor};
use crate::utils::progress::ProgressContext;
use log::{info, warn};
use std::path::Path;

mod error;
mod geometry;
mod identifiers;
mod hierarchy;
mod bim_parser;

pub use error::{IFCError, IFCResult};
pub use hierarchy::HierarchyBuilder;
pub use bim_parser::BimParser;

/// IFC (Industry Foundation Classes) file processor
///
/// Handles parsing and processing of IFC files to extract building data.
/// Uses a custom STEP parser to convert IFC entities into ArxOS building models.
pub struct IFCProcessor {
    // Custom STEP parser implementation
}

impl Default for IFCProcessor {
    fn default() -> Self {
        Self::new()
    }
}

impl IFCProcessor {
    pub fn new() -> Self {
        Self {}
    }


    pub fn process_file(
        &self,
        file_path: &str,
    ) -> IFCResult<(Building, Vec<crate::core::spatial::SpatialEntity>)> {
        info!("Processing IFC file: {}", file_path);

        // Check if file exists
        if !Path::new(file_path).exists() {
            return Err(IFCError::FileNotFound {
                path: file_path.to_string(),
            });
        }

        // Check file extension
        if !file_path.to_lowercase().ends_with(".ifc") {
            warn!("File does not have .ifc extension: {}", file_path);
        }

        // Use bim crate parser
        let parser = BimParser::new();
        match parser.parse_ifc_file(file_path) {
            Ok((building, spatial_entities)) => {
                info!("Successfully parsed with bim crate");
                Ok((building, spatial_entities))
            }
            Err(e) => {
                warn!("bim crate parsing failed: {}", e);
                Err(IFCError::ParsingError {
                    message: e.to_string(),
                })
            }
        }
    }

    /// Process IFC file with parallel processing and progress reporting
    pub fn process_file_parallel(
        &self,
        file_path: &str,
    ) -> IFCResult<(Building, Vec<crate::core::spatial::SpatialEntity>)> {
        info!(
            "Processing IFC file with parallel processing: {}",
            file_path
        );

        // Check if file exists
        if !Path::new(file_path).exists() {
            return Err(IFCError::FileNotFound {
                path: file_path.to_string(),
            });
        }

        // Check file extension
        if !file_path.to_lowercase().ends_with(".ifc") {
            warn!("File does not have .ifc extension: {}", file_path);
        }

        // Note: bim crate doesn't have explicit parallel mode, but it's efficient
        let parser = BimParser::new();
        match parser.parse_ifc_file(file_path) {
            Ok((building, spatial_entities)) => {
                info!("Successfully parsed with bim crate");
                Ok((building, spatial_entities))
            }
            Err(e) => {
                warn!("bim crate parsing failed: {}", e);
                Err(IFCError::ParsingError {
                    message: e.to_string(),
                })
            }
        }
    }

    /// Process IFC file with progress reporting
    pub fn process_file_with_progress(
        &self,
        file_path: &str,
        mut progress: ProgressContext,
    ) -> IFCResult<(Building, Vec<crate::core::spatial::SpatialEntity>)> {
        info!("Processing IFC file with progress reporting: {}", file_path);

        progress.update(10, "Reading IFC file...");

        // Check if file exists
        if !Path::new(file_path).exists() {
            progress.finish_error("IFC file not found");
            return Err(IFCError::FileNotFound {
                path: file_path.to_string(),
            });
        }

        // Check file extension
        if !file_path.to_lowercase().ends_with(".ifc") {
            warn!("File does not have .ifc extension: {}", file_path);
        }

        progress.update(20, "Parsing IFC entities...");

        // Use bim crate parser with progress
        let parser = BimParser::new();
        match parser.parse_ifc_file_with_progress(file_path, progress) {
            Ok((building, spatial_entities)) => {
                info!("Successfully parsed with bim crate");
                Ok((building, spatial_entities))
            }
            Err(e) => {
                warn!("bim crate parsing failed: {}", e);
                Err(IFCError::ParsingError {
                    message: e.to_string(),
                })
            }
        }
    }


    pub fn validate_ifc_file(&self, file_path: &str) -> IFCResult<bool> {
        info!("Validating IFC file: {}", file_path);

        if !Path::new(file_path).exists() {
            return Err(IFCError::FileNotFound {
                path: file_path.to_string(),
            });
        }

        // Check file extension
        if !file_path.to_lowercase().ends_with(".ifc") {
            return Err(IFCError::InvalidFormat {
                reason: "File must have .ifc extension".to_string(),
            });
        }

        // Check file size
        let metadata = std::fs::metadata(file_path)?;
        if metadata.len() == 0 {
            return Err(IFCError::InvalidFormat {
                reason: "File is empty".to_string(),
            });
        }

        // Read file content for format validation with path safety
        use crate::utils::path_safety::PathSafety;
        let base_dir = std::env::current_dir().map_err(|e| IFCError::FileNotFound {
            path: format!("Failed to get current directory: {}", e),
        })?;

        let content = PathSafety::read_file_safely(std::path::Path::new(file_path), &base_dir)
            .map_err(|e| IFCError::FileNotFound {
                path: format!("Failed to read IFC file '{}': {}", file_path, e),
            })?;

        // Validate IFC file structure
        self.validate_ifc_structure(&content)?;

        info!("IFC file validation passed");
        Ok(true)
    }


    /// Validate IFC file structure and format
    fn validate_ifc_structure(&self, content: &str) -> IFCResult<()> {
        let lines: Vec<&str> = content.lines().collect();

        if lines.is_empty() {
            return Err(IFCError::InvalidFormat {
                reason: "File contains no content".to_string(),
            });
        }

        // Check for ISO-10303-21 header
        if !lines[0].starts_with("ISO-10303-21;") {
            return Err(IFCError::InvalidFormat {
                reason: "Missing ISO-10303-21 header".to_string(),
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
                reason: "Missing HEADER section".to_string(),
            });
        }

        if !has_data {
            return Err(IFCError::InvalidFormat {
                reason: "Missing DATA section".to_string(),
            });
        }

        if !has_endsec {
            return Err(IFCError::InvalidFormat {
                reason: "Missing ENDSEC section".to_string(),
            });
        }

        // Check for proper ending
        if !content.trim_end().ends_with("END-ISO-10303-21;") {
            return Err(IFCError::InvalidFormat {
                reason: "Missing END-ISO-10303-21 footer".to_string(),
            });
        }

        // Check for at least one entity definition
        let has_entities = lines
            .iter()
            .any(|line| line.starts_with("#") && line.contains("="));
        if !has_entities {
            return Err(IFCError::InvalidFormat {
                reason: "No entity definitions found".to_string(),
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
