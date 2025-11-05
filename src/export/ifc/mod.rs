//! IFC export functionality for ArxOS
//! 
//! This module provides IFC format export capabilities for building data,
//! including delta tracking and continuous synchronization.

pub mod exporter;
pub mod mapper;
pub mod sync_state;
pub mod delta;

// Re-export public types
pub use exporter::IFCExporter;
pub use mapper::{universal_path_to_ifc_entity_id, address_to_ifc_entity_id};
pub use sync_state::IFCSyncState;
pub use delta::ExportDelta;

