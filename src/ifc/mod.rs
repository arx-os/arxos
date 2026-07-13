//! IFC processing for ArxOS (native STEP parser only).
//!
//! External IFC bytes become a `core::Building` via `parse_native` /
//! `parse_native_content`. Production imports must continue through
//! `ingest::import_ifc_path` so merge + validation finalize the model.

use log::info;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::path::Path;

mod error;
mod geometry;
mod hierarchy;
mod identifiers;
pub mod mapping;
pub mod parser;
pub mod spatial;

pub use error::{IFCError, IFCResult};
pub use hierarchy::{HierarchyBuilder, IFCEntity};
pub use mapping::{
    assign_missing_global_ids, merge_building, merge_building_with_policy, merge_into_report,
    merge_into_report_with_policy, report_export_losses, resolve_product_global_id, FidelityLevel,
    HierarchyBase, LossReport, MappingResult, MergePolicy, MergeResult, MergeSource, MergeStats,
};
pub use spatial::{SpatialIndex, SpatialQueryResult, SpatialRelationship};

/// IFC (Industry Foundation Classes) file processor.
///
/// Canonical construction path: native STEP lexer/registry/resolver → `Building`.
pub struct IFCProcessor;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct EntityStats {
    pub total_entities: usize,
    pub class_counts: HashMap<String, usize>,
    pub spatial_entities: usize,
}

#[derive(Debug, Clone)]
pub struct ParsingResult {
    pub building: crate::core::Building,
    pub stats: EntityStats,
    /// Structured fidelity / loss report.
    pub report: mapping::LossReport,
    /// Flattened warning messages (derived from `report` for simple consumers).
    pub warnings: Vec<String>,
}

impl Default for IFCProcessor {
    fn default() -> Self {
        Self::new()
    }
}

impl IFCProcessor {
    pub fn new() -> Self {
        Self
    }

    /// Parse IFC file using the native STEP parser into a `Building`.
    pub fn parse_native(
        &self,
        file_path: &str,
        validate_strict: bool,
    ) -> anyhow::Result<ParsingResult> {
        info!(
            "Processing IFC file (Native, strict={}): {}",
            validate_strict, file_path
        );
        if !Path::new(file_path).exists() {
            return Err(anyhow::anyhow!("IFC file not found: {}", file_path));
        }
        let content = std::fs::read_to_string(file_path)?;
        self.parse_native_content(&content, validate_strict)
    }

    /// Parse IFC from an in-memory STEP string (CLI / WASM / ingest shared path).
    pub fn parse_native_content(
        &self,
        content: &str,
        validate_strict: bool,
    ) -> anyhow::Result<ParsingResult> {
        let lexer = parser::StepLexer::new(content);
        let mut registry = parser::EntityRegistry::new();
        registry.populate_from_lexer(lexer);

        let stats = registry.get_stats();

        if validate_strict && stats.spatial_entities == 0 {
            return Err(anyhow::anyhow!(
                "Strict validation failed: No spatial entities found (IFC contains no Site/Building/Storey)"
            ));
        }

        let mut resolver = parser::IfcResolver::new(&mut registry);
        let (building, report) = resolver.resolve_all()?;
        let warnings = report
            .warnings
            .iter()
            .map(|w| {
                if let Some(ref e) = w.entity {
                    format!("[{}] {} ({})", w.code, w.message, e)
                } else {
                    format!("[{}] {}", w.code, w.message)
                }
            })
            .collect();

        Ok(ParsingResult {
            building,
            stats,
            report,
            warnings,
        })
    }

    /// Extract hierarchical building data from an IFC file.
    pub fn extract_hierarchy(&self, file_path: &str) -> anyhow::Result<crate::core::Building> {
        Ok(self.parse_native(file_path, false)?.building)
    }

    pub fn validate_ifc_file(&self, file_path: &str) -> IFCResult<bool> {
        info!("Validating IFC file: {}", file_path);

        if !Path::new(file_path).exists() {
            return Err(IFCError::FileNotFound {
                path: file_path.to_string(),
            });
        }

        if !file_path.to_lowercase().ends_with(".ifc") {
            return Err(IFCError::InvalidFormat {
                reason: "File must have .ifc extension".to_string(),
            });
        }

        let metadata = std::fs::metadata(file_path)?;
        if metadata.len() == 0 {
            return Err(IFCError::InvalidFormat {
                reason: "File is empty".to_string(),
            });
        }

        use crate::utils::path_safety::PathSafety;
        let base_dir = std::env::current_dir().map_err(|e| IFCError::FileNotFound {
            path: format!("Failed to get current directory: {}", e),
        })?;

        let content = PathSafety::read_file_safely(std::path::Path::new(file_path), &base_dir)
            .map_err(|e| IFCError::FileNotFound {
                path: format!("Failed to read IFC file '{}': {}", file_path, e),
            })?;

        self.validate_ifc_structure(&content)?;

        info!("IFC file validation passed");
        Ok(true)
    }

    fn validate_ifc_structure(&self, content: &str) -> IFCResult<()> {
        let lines: Vec<&str> = content.lines().collect();

        if lines.is_empty() {
            return Err(IFCError::InvalidFormat {
                reason: "File contains no content".to_string(),
            });
        }

        if !lines[0].starts_with("ISO-10303-21;") {
            return Err(IFCError::InvalidFormat {
                reason: "Missing ISO-10303-21 header".to_string(),
            });
        }

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

        if !content.trim_end().ends_with("END-ISO-10303-21;") {
            return Err(IFCError::InvalidFormat {
                reason: "Missing END-ISO-10303-21 footer".to_string(),
            });
        }

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
