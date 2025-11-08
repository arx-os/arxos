//! IFC export functionality for ArxOS
//!
//! This module provides IFC format export capabilities for building data,
//! including delta tracking and continuous synchronization.

pub mod delta;
pub mod exporter;
pub mod mapper;
pub mod sync_state;

// Re-export public types
pub use delta::ExportDelta;
pub use exporter::IFCExporter;
pub use mapper::{address_to_ifc_entity_id, universal_path_to_ifc_entity_id};
pub use sync_state::IFCSyncState;
