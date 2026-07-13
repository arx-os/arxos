//! IFC ↔ core data model mapping policy (identity, Psets, fidelity).
//!
//! The core `Building` graph is canonical. This module owns constants and pure
//! helpers so import and export stay consistent. See `docs/ifc-limitations.md` and `docs/identity.md`.

mod export_report;
mod geometry;
mod identity;
mod lidar;
mod merge;
mod properties;
mod report;

pub use export_report::report_export_losses;
pub use geometry::{
    approx_eq, bounding_box_from_position_dims, dimensions_approx_eq, dimensions_from_mesh_aabb,
    mesh_to_local, position_from_origin, positions_approx_eq, spatial_from_position_dims,
    COORD_BUILDING_LOCAL, GEOMETRY_EPSILON,
};
pub use identity::{
    apply_identity_on_import, assign_missing_global_ids, identity_property_map,
    ifc_global_id_from_uuid, resolve_product_global_id, uuid_from_arx_id,
};
pub use lidar::{
    apply_lidar_on_import, lidar_enrichment_to_pset, prefer_existing_lidar,
    take_lidar_enrichment_from_properties, PROP_CLASSIFICATION_HEURISTIC, PROP_CONFIDENCE_SCORE,
    PROP_LAST_SCAN_TIMESTAMP, PROP_POINT_COUNT,
};
pub use merge::{
    merge_building, merge_building_with_policy, merge_into_report, merge_into_report_with_policy,
    HierarchyBase, MergePolicy, MergeResult, MergeSource,
};
pub use properties::{
    normalize_imported_properties, properties_for_export, wing_name_from_properties, PROP_ARX_WING,
    PROP_WING,
};
pub use report::{FidelityLevel, LossReport, MappingResult, MappingWarning, MergeStats};

/// Property set carrying Arx identity across the IFC boundary.
pub const PSET_ARX_IDENTITY: &str = "Pset_ArxIdentity";

/// Property set for LiDAR enrichments (L1).
pub const PSET_ARX_LIDAR: &str = "Pset_ArxLidarEnrichment";

/// Existing Arx room free-form properties Pset.
pub const PSET_ARX_ROOM: &str = "Pset_ArxRoomProperties";

/// Existing Arx equipment free-form properties Pset.
pub const PSET_ARX_EQUIPMENT: &str = "Pset_ArxEquipmentProperties";

/// Existing Arx floor free-form properties Pset.
pub const PSET_ARX_FLOOR: &str = "Pset_ArxFloorProperties";

/// Existing Arx building metadata Pset.
pub const PSET_ARX_BUILDING: &str = "Pset_ArxBuildingMetadata";

/// `Pset_ArxIdentity` property: Arx UUID string.
pub const PROP_ARX_ID: &str = "ArxId";

/// `Pset_ArxIdentity` property: domain kind label.
pub const PROP_ENTITY_KIND: &str = "EntityKind";

/// Entity kind labels written into `Pset_ArxIdentity`.
pub mod entity_kind {
    pub const BUILDING: &str = "Building";
    pub const FLOOR: &str = "Floor";
    pub const ROOM: &str = "Room";
    pub const EQUIPMENT: &str = "Equipment";
}

/// Prefixed property key as stored after native IFC import
/// (`PsetName:PropertyName`).
pub fn pset_prop_key(pset: &str, prop: &str) -> String {
    format!("{}:{}", pset, prop)
}
