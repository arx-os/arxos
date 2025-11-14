//! IFC hierarchy building module
//!
//! This module provides functionality for extracting and building the ArxOS
//! building hierarchy (Building → Floor → Room → Equipment) from IFC files.
//!
//! # Module Organization
//!
//! - `types` - IFC entity data structures
//! - `builder` - HierarchyBuilder implementation
//! - `helpers` - Entity classification and property extraction
//! - `utils` - Utility functions (path uniqueness, etc.)
//!
//! # Usage
//!
//! ```ignore
//! use crate::ifc::hierarchy::{IFCEntity, HierarchyBuilder};
//!
//! let entities = vec![/* IFC entities */];
//! let builder = HierarchyBuilder::new(entities);
//! let building = builder.build_hierarchy()?;
//! ```

pub mod builder;
pub mod helpers;
pub mod types;
pub mod utils;

// Re-export main types for convenience
pub use builder::HierarchyBuilder;
pub use types::IFCEntity;

// Re-export helper functions
