//! Domain layer for ArxOS business logic
//!
//! This module contains core domain concepts like addresses, fixtures, and other
//! building-related entities.

pub mod address;
pub mod economy;
pub mod elec;
pub mod postal;

pub use address::{ArxAddress, RESERVED_SYSTEMS};
pub use economy::{BuildingValuation, ContributionRecord, EconomySnapshot, Money, RevenuePayout};
pub use elec::{
    build_elec_address, ckt_segment, elec_kind_from_ifc, elec_leaf_segment, elec_root,
    is_elec_path, jbox_segment, ltg_segment, panel_segment, rec_segment, sw_segment,
    try_elec_address_from_import, ElecKind, ELEC_ROOT,
};
pub use postal::{
    derive_building_root_from_str, derive_building_root_string, parse_postal_string,
    postal_building_root, postal_building_root_fields, postal_building_root_from_str,
    resolve_building_root_from_options, PostalAddress,
};
