//! Enhanced IFC parser with partial parsing and error recovery
//!
//! This module is split into logical components:
//! - types: All type definitions
//! - parser: Main parser implementation
//! - coordinates: Coordinate system transformations
//! - relationships: Equipment relationship parsing
//! - spatial_index: R-Tree and spatial queries
//! - writer: IFC file writing
//! - positioning: Deterministic position generation

mod coordinates;
mod parser;
mod positioning;
mod relationships;
mod spatial_index;
mod types;
mod writer;

// Re-export public types (already includes SpatialIndex, RTreeNode, etc.)
pub use types::*;
// Parser, coordinates, relationships, spatial_index, writer, and positioning
// modules contain impl blocks that are automatically associated with types
