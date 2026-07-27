//! # arxos-ifc
//!
//! Bidirectional **IFC** projection of the Arxos object graph.
//!
//! Phase 4 ships a **narrow, identity-preserving subset**:
//! - IFC4 STEP physical file (ISO 10303-21)
//! - Hierarchy: IfcProject → IfcSite → IfcBuilding → IfcBuildingStorey → IfcSpace
//! - Annotations as IfcAnnotation with IfcTextLiteral
//! - Identity via property set `Pset_ArxosIdentity` (`Cid`, `BuildingId`, `ObjectType`)
//! - GlobalId derived deterministically from CID (stable re-export)
//!
//! Geometry is minimal (local placement + optional bounding box as
//! IfcBoundingBox). Full BREP/mesh fidelity is intentionally out of scope;
//! use USD for modern geometry interchange.

#![allow(missing_docs)]

mod error;
mod export;
mod global_id;
mod import;
mod parse;

pub use error::{IfcError, Result};
pub use export::{export_building_ifc, export_root_ifc, ExportOptions};
pub use import::{import_ifc, ImportResult};

/// Crate version.
pub fn version() -> &'static str {
    env!("CARGO_PKG_VERSION")
}
