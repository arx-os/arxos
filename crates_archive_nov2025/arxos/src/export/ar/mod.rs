//! AR export functionality for ArxOS
//!
//! This module provides AR format export capabilities including glTF and USDZ.

pub mod anchor;
pub mod gltf;
pub mod usdz;

// Re-export types
pub use anchor::{export_anchors_to_json, import_anchors_from_json, SpatialAnchor};
pub use gltf::GLTFExporter;
pub use usdz::USDZExporter;

use crate::yaml::BuildingData;
use std::path::Path;

/// AR export format options
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ARFormat {
    /// glTF 2.0 format (universal 3D standard)
    GLTF,
    /// USDZ format (Apple ARKit preferred)
    USDZ,
}

impl std::fmt::Display for ARFormat {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            ARFormat::GLTF => write!(f, "gltf"),
            ARFormat::USDZ => write!(f, "usdz"),
        }
    }
}

impl std::str::FromStr for ARFormat {
    type Err = String;

    fn from_str(s: &str) -> Result<Self, Self::Err> {
        match s.to_lowercase().as_str() {
            "gltf" => Ok(ARFormat::GLTF),
            "usdz" => Ok(ARFormat::USDZ),
            _ => Err(format!("Unknown AR format: {}. Supported: gltf, usdz", s)),
        }
    }
}

/// AR exporter for building data
pub struct ARExporter {
    building_data: BuildingData,
}

impl ARExporter {
    /// Create a new AR exporter from building data
    pub fn new(building_data: BuildingData) -> Self {
        Self { building_data }
    }

    /// Export building to AR format
    pub fn export(
        &self,
        format: ARFormat,
        output: &Path,
    ) -> Result<(), Box<dyn std::error::Error>> {
        match format {
            ARFormat::GLTF => {
                let exporter = GLTFExporter::new(&self.building_data);
                exporter.export(output)
            }
            ARFormat::USDZ => {
                let exporter = USDZExporter::new(&self.building_data);
                exporter.export(output)
            }
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_ar_format_display() {
        assert_eq!(ARFormat::GLTF.to_string(), "gltf");
        assert_eq!(ARFormat::USDZ.to_string(), "usdz");
    }

    #[test]
    fn test_ar_format_from_str() {
        assert_eq!("gltf".parse::<ARFormat>(), Ok(ARFormat::GLTF));
        assert_eq!("usdz".parse::<ARFormat>(), Ok(ARFormat::USDZ));
        assert!("invalid".parse::<ARFormat>().is_err());
    }
}
