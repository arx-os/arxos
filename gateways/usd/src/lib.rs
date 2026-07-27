//! # arxos-usd
//!
//! Projection of the Arxos object graph to **OpenUSD ASCII (USDA)**.
//!
//! Phase 4 ships a **narrow, correct subset**:
//! - Hierarchy: Building → Floor → Space → Annotation / PointCloud / Equipment
//! - Identity custom properties: `arxos:cid`, `arxos:type`, `arxos:buildingId`
//! - Poses as `xformOp:transform` (translate + identity rotation for Phase 4)
//! - Bounds as `extent` on geom prims
//! - Point clouds as `UsdGeomPoints`
//!
//! Full OpenUSD C++/Rust bindings can replace the USDA writer later without
//! changing the projection model. Geometry remains **data only** — Arxos does
//! not render.

#![allow(missing_docs)]

mod error;
mod export;
mod import;
mod model;

pub use error::{Result, UsdError};
pub use export::{export_building_usda, export_root_usda, ExportOptions};
pub use import::{import_usda, ImportResult};
pub use model::{UsdPrim, UsdStage, UsdValue};

/// Crate version.
pub fn version() -> &'static str {
    env!("CARGO_PKG_VERSION")
}
