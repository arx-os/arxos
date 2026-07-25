//! Electrical system addresses (ADR 0001 — first system tree).
//!
//! Root segment: `elec`
//!
//! Example:
//! `bldg.us.fl.tampa.dale-mabry.143677.s2/elec/panel.l1/ckt.14/rec.7`
//!
//! Honesty rule: only build deeper panel/circuit structure when source data
//! supplies those identifiers. Never invent panels or circuits.

use super::address::ArxAddress;
use crate::core::EquipmentType;
use std::collections::HashMap;

/// Official short root for the electrical system tree.
pub const ELEC_ROOT: &str = "elec";

/// Leaf / node kinds under `elec`.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ElecKind {
    Panel,
    Circuit,
    Jbox,
    Rec,
    Ltg,
    Sw,
    /// Generic electrical device when class is electrical but not a known leaf.
    Device,
}

impl ElecKind {
    pub fn prefix(self) -> &'static str {
        match self {
            ElecKind::Panel => "panel",
            ElecKind::Circuit => "ckt",
            ElecKind::Jbox => "jbox",
            ElecKind::Rec => "rec",
            ElecKind::Ltg => "ltg",
            ElecKind::Sw => "sw",
            ElecKind::Device => "dev",
        }
    }

    pub fn as_str(self) -> &'static str {
        self.prefix()
    }
}

/// `panel.<id>`
pub fn panel_segment(id: &str) -> String {
    format!("panel.{}", ArxAddress::stable_slug(id))
}

/// `ckt.<n>` — circuit number or identifier.
pub fn ckt_segment(id: &str) -> String {
    format!("ckt.{}", ArxAddress::stable_slug(id))
}

/// `jbox.<id>`
pub fn jbox_segment(id: &str) -> String {
    format!("jbox.{}", ArxAddress::stable_slug(id))
}

/// `rec.<id>` receptacle
pub fn rec_segment(id: &str) -> String {
    format!("rec.{}", ArxAddress::stable_slug(id))
}

/// `ltg.<id>` lighting
pub fn ltg_segment(id: &str) -> String {
    format!("ltg.{}", ArxAddress::stable_slug(id))
}

/// `sw.<id>` switch
pub fn sw_segment(id: &str) -> String {
    format!("sw.{}", ArxAddress::stable_slug(id))
}

/// `dev.<id>` generic device
pub fn dev_segment(id: &str) -> String {
    format!("dev.{}", ArxAddress::stable_slug(id))
}

/// Segment for a leaf kind + name slug.
pub fn elec_leaf_segment(kind: ElecKind, name: &str) -> String {
    format!("{}.{}", kind.prefix(), ArxAddress::stable_slug(name))
}

/// Building root + `/elec`.
pub fn elec_root(building_root: &ArxAddress) -> Result<ArxAddress, anyhow::Error> {
    building_root.join(ELEC_ROOT)
}

/// Build a full electrical address under `building_root`.
///
/// Segments after `elec` are joined in order (panel → ckt → jbox → leaf).
pub fn build_elec_address(
    building_root: &ArxAddress,
    segments: &[&str],
) -> Result<ArxAddress, anyhow::Error> {
    let mut addr = elec_root(building_root)?;
    for seg in segments {
        addr = addr.join(seg)?;
    }
    Ok(addr)
}

/// Map IFC class / equipment type to an electrical leaf kind when clear.
///
/// Returns `None` when the object should **not** be forced into the elec tree.
pub fn elec_kind_from_ifc(class: &str, eq_type: &EquipmentType) -> Option<ElecKind> {
    let c = class.to_ascii_uppercase();
    match c.as_str() {
        "IFCOUTLET" => Some(ElecKind::Rec),
        "IFCLIGHTFIXTURE" | "IFCLAMP" => Some(ElecKind::Ltg),
        "IFCSWITCHINGDEVICE" => Some(ElecKind::Sw),
        "IFCELECTRICDISTRIBUTIONBOARD"
        | "IFCELECTRICDISTRIBUTIONPOINT"
        | "IFCDISTRIBUTIONBOARDELEMENT" => Some(ElecKind::Panel),
        "IFCJUNCTIONBOX" => Some(ElecKind::Jbox),
        "IFCPROTECTIVEDEVICE" | "IFCCABLECARRIERSEGMENT" => Some(ElecKind::Device),
        _ => match eq_type {
            EquipmentType::Electrical => Some(ElecKind::Device),
            EquipmentType::Other(s) if s.eq_ignore_ascii_case("Lighting") => Some(ElecKind::Ltg),
            _ => None,
        },
    }
}

/// Look up first matching property (case-insensitive key).
pub fn prop_ci<'a>(props: &'a HashMap<String, String>, keys: &[&str]) -> Option<&'a str> {
    for want in keys {
        let w = want.to_ascii_lowercase();
        for (k, v) in props {
            if k.to_ascii_lowercase() == w && !v.trim().is_empty() {
                return Some(v.trim());
            }
            // Pset_Foo:Bar style — match suffix after ':'
            if let Some((_, suffix)) = k.rsplit_once(':') {
                if suffix.to_ascii_lowercase() == w && !v.trim().is_empty() {
                    return Some(v.trim());
                }
            }
        }
    }
    None
}

/// Try to construct an electrical address from IFC class, name, and properties.
///
/// - With panel + circuit properties → `…/elec/panel.x/ckt.y/<leaf>.slug`
/// - With panel only → `…/elec/panel.x/<leaf>.slug`
/// - With clear electrical class only → `…/elec/<leaf>.slug` (no invented panel/ckt)
/// - Returns `None` when the class is not electrical (caller keeps spatial address).
pub fn try_elec_address_from_import(
    building_root: &ArxAddress,
    class: &str,
    name: &str,
    eq_type: &EquipmentType,
    properties: &HashMap<String, String>,
) -> Option<ArxAddress> {
    let kind = elec_kind_from_ifc(class, eq_type)?;
    let leaf = elec_leaf_segment(kind, name);

    // Panel objects themselves
    if kind == ElecKind::Panel {
        return build_elec_address(building_root, &[&panel_segment(name)]).ok();
    }

    let panel = prop_ci(
        properties,
        &[
            "PanelName",
            "Panel",
            "PanelNumber",
            "DistributionBoard",
            "Panel ID",
            "PanelID",
        ],
    );
    let circuit = prop_ci(
        properties,
        &[
            "CircuitNumber",
            "Circuit",
            "CircuitNo",
            "BranchCircuit",
            "Circuit ID",
            "CircuitID",
        ],
    );

    match (panel, circuit) {
        (Some(p), Some(c)) => {
            build_elec_address(building_root, &[&panel_segment(p), &ckt_segment(c), &leaf]).ok()
        }
        (Some(p), None) => build_elec_address(building_root, &[&panel_segment(p), &leaf]).ok(),
        (None, Some(c)) => {
            // Circuit without panel — still honest: attach under elec/ckt only
            build_elec_address(building_root, &[&ckt_segment(c), &leaf]).ok()
        }
        (None, None) => {
            // Clear electrical type, no topology → shallow elec leaf only
            build_elec_address(building_root, &[&leaf]).ok()
        }
    }
}

/// True if path contains a `/elec` or `/elec/` system root segment.
pub fn is_elec_path(path: &str) -> bool {
    let p = path.trim_start_matches('/');
    p == ELEC_ROOT
        || p.starts_with("elec/")
        || p.contains("/elec/")
        || p.ends_with("/elec")
}

#[cfg(test)]
mod tests {
    use super::*;

    fn root() -> ArxAddress {
        ArxAddress::from_path("bldg.us.fl.tampa.dale-mabry.143677.s2").unwrap()
    }

    #[test]
    fn segment_helpers() {
        assert_eq!(panel_segment("L1"), "panel.l1");
        assert_eq!(ckt_segment("14"), "ckt.14");
        assert_eq!(rec_segment("7"), "rec.7");
        assert_eq!(ltg_segment("Hall-1"), "ltg.hall-1");
        assert_eq!(sw_segment("SW-A"), "sw.sw-a");
    }

    #[test]
    fn full_path_construction() {
        let addr = build_elec_address(
            &root(),
            &["panel.l1", "ckt.14", "rec.7"],
        )
        .unwrap();
        assert_eq!(
            addr.path,
            "/bldg.us.fl.tampa.dale-mabry.143677.s2/elec/panel.l1/ckt.14/rec.7"
        );
        assert!(addr.validate().is_ok());
        assert!(is_elec_path(&addr.path));
    }

    #[test]
    fn shallow_leaf_without_invented_panel() {
        let mut props = HashMap::new();
        let addr = try_elec_address_from_import(
            &root(),
            "IFCOUTLET",
            "Outlet-7",
            &EquipmentType::Electrical,
            &props,
        )
        .unwrap();
        assert_eq!(
            addr.path,
            "/bldg.us.fl.tampa.dale-mabry.143677.s2/elec/rec.outlet-7"
        );
        // no invented panel/ckt
        assert!(!addr.path.contains("panel."));
        assert!(!addr.path.contains("ckt."));
        let _ = &mut props;
    }

    #[test]
    fn panel_and_circuit_from_properties() {
        let mut props = HashMap::new();
        props.insert("PanelName".into(), "L1".into());
        props.insert("CircuitNumber".into(), "14".into());
        let addr = try_elec_address_from_import(
            &root(),
            "IFCOUTLET",
            "Rec-7",
            &EquipmentType::Electrical,
            &props,
        )
        .unwrap();
        assert_eq!(
            addr.path,
            "/bldg.us.fl.tampa.dale-mabry.143677.s2/elec/panel.l1/ckt.14/rec.rec-7"
        );
    }

    #[test]
    fn non_electrical_returns_none() {
        let props = HashMap::new();
        assert!(try_elec_address_from_import(
            &root(),
            "IFCBOILER",
            "B-1",
            &EquipmentType::HVAC,
            &props,
        )
        .is_none());
    }

    #[test]
    fn lighting_maps_to_ltg() {
        let props = HashMap::new();
        let addr = try_elec_address_from_import(
            &root(),
            "IFCLIGHTFIXTURE",
            "Hall Light",
            &EquipmentType::Other("Lighting".into()),
            &props,
        )
        .unwrap();
        assert!(addr.path.ends_with("/elec/ltg.hall-light"));
    }
}
