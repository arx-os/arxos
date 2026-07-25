//! Address-native mutations (ADR 0001) — add entities under a parent address.

use crate::core::domain::address::ArxAddress;
use crate::core::domain::elec::{
    ckt_segment, elec_leaf_segment, jbox_segment, panel_segment, ElecKind, ELEC_ROOT,
};
use crate::core::operations::address_nav::{
    collect_all_addressed, is_direct_child, parse_address, resolve, EntityKind,
};
use crate::core::{Building, Equipment, EquipmentType, Position};
use anyhow::{bail, Result};

/// Kinds accepted by `arx add`.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum AddKind {
    Outlet,
    Light,
    Switch,
    Jbox,
    Circuit,
    Panel,
}

impl AddKind {
    pub fn parse(s: &str) -> Result<Self> {
        match s.trim().to_ascii_lowercase().as_str() {
            "outlet" | "rec" | "receptacle" => Ok(AddKind::Outlet),
            "light" | "ltg" | "lighting" | "lamp" => Ok(AddKind::Light),
            "switch" | "sw" => Ok(AddKind::Switch),
            "jbox" | "junction" | "junction-box" => Ok(AddKind::Jbox),
            "ckt" | "circuit" => Ok(AddKind::Circuit),
            "panel" => Ok(AddKind::Panel),
            other => bail!(
                "Unknown kind '{}'. Supported: outlet|rec, light|ltg, switch|sw, jbox, ckt|circuit, panel",
                other
            ),
        }
    }

    pub fn as_str(self) -> &'static str {
        match self {
            AddKind::Outlet => "outlet",
            AddKind::Light => "light",
            AddKind::Switch => "switch",
            AddKind::Jbox => "jbox",
            AddKind::Circuit => "circuit",
            AddKind::Panel => "panel",
        }
    }

    fn elec_kind(self) -> ElecKind {
        match self {
            AddKind::Outlet => ElecKind::Rec,
            AddKind::Light => ElecKind::Ltg,
            AddKind::Switch => ElecKind::Sw,
            AddKind::Jbox => ElecKind::Jbox,
            AddKind::Circuit => ElecKind::Circuit,
            AddKind::Panel => ElecKind::Panel,
        }
    }

    fn equipment_type(self) -> EquipmentType {
        match self {
            AddKind::Outlet | AddKind::Switch | AddKind::Panel | AddKind::Circuit | AddKind::Jbox => {
                EquipmentType::Electrical
            }
            AddKind::Light => EquipmentType::Other("Lighting".into()),
        }
    }

    fn default_display_name(self, leaf_id: &str) -> String {
        match self {
            AddKind::Outlet => format!("Outlet {}", leaf_id),
            AddKind::Light => format!("Light {}", leaf_id),
            AddKind::Switch => format!("Switch {}", leaf_id),
            AddKind::Jbox => format!("JBox {}", leaf_id),
            AddKind::Circuit => format!("Circuit {}", leaf_id),
            AddKind::Panel => format!("Panel {}", leaf_id),
        }
    }
}

/// Result of a successful add.
#[derive(Debug, Clone)]
pub struct AddResult {
    pub address: ArxAddress,
    pub name: String,
    pub kind: AddKind,
}

/// Allocate a deterministic child leaf segment under `parent` for `kind`.
///
/// - With `name`: `prefix.slug` — error on collision
/// - Without name: `prefix.N` where N is the next free positive integer
pub fn allocate_child_address(
    building: &Building,
    parent: &ArxAddress,
    kind: AddKind,
    name: Option<&str>,
) -> Result<ArxAddress> {
    let prefix = kind.elec_kind().prefix();
    let segment = if let Some(n) = name.map(str::trim).filter(|s| !s.is_empty()) {
        let seg = match kind {
            AddKind::Panel => panel_segment(n),
            AddKind::Circuit => ckt_segment(n),
            AddKind::Jbox => jbox_segment(n),
            _ => elec_leaf_segment(kind.elec_kind(), n),
        };
        // Collision check
        let candidate = parent.join(&seg)?;
        if address_exists(building, &candidate) {
            bail!(
                "Address collision: '{}' already exists",
                candidate.path
            );
        }
        seg
    } else {
        let next = next_numeric_id(building, parent, prefix);
        format!("{}.{}", prefix, next)
    };
    let addr = parent.join(&segment)?;
    if address_exists(building, &addr) {
        bail!("Address collision: '{}' already exists", addr.path);
    }
    Ok(addr)
}

/// Next free numeric suffix for `prefix.` under direct children of `parent` (1-based).
pub fn next_numeric_id(building: &Building, parent: &ArxAddress, prefix: &str) -> u32 {
    let mut max = 0u32;
    let head = format!("{}.", prefix);
    for entry in all_addresses(building) {
        if !is_direct_child(parent, &entry) {
            continue;
        }
        let leaf = entry.path.rsplit('/').next().unwrap_or("");
        if let Some(rest) = leaf.strip_prefix(&head) {
            if let Ok(n) = rest.parse::<u32>() {
                max = max.max(n);
            }
        }
    }
    max + 1
}

fn address_exists(building: &Building, addr: &ArxAddress) -> bool {
    all_addresses(building).iter().any(|a| a.path == addr.path)
}

fn all_addresses(building: &Building) -> Vec<ArxAddress> {
    collect_all_addressed(building)
        .into_iter()
        .map(|c| c.address)
        .collect()
}

/// Validate parent context for the kind (light rules; honesty over invention).
pub fn validate_parent_for_kind(parent: &ArxAddress, kind: AddKind) -> Result<()> {
    let path = parent.path.as_str();
    let under_elec = path.contains(&format!("/{}/", ELEC_ROOT))
        || path.ends_with(&format!("/{}", ELEC_ROOT))
        || path.rsplit('/').next() == Some(ELEC_ROOT);

    match kind {
        AddKind::Panel => {
            // Prefer under …/elec
            if !under_elec && !path.contains("/elec") {
                // Allow under building root too (will create …/elec/panel.N if parent is root?)
                // Strict: parent last segment is "elec" or parent is building (user can add under elec)
                let leaf = path.rsplit('/').next().unwrap_or("");
                if leaf != ELEC_ROOT {
                    bail!(
                        "Invalid parent for panel: expected parent under '/elec' (got '{}')",
                        parent.path
                    );
                }
            }
        }
        AddKind::Circuit => {
            let leaf = path.rsplit('/').next().unwrap_or("");
            if !leaf.starts_with("panel.") && !under_elec {
                bail!(
                    "Invalid parent for circuit: expected a panel.* address (got '{}')",
                    parent.path
                );
            }
        }
        AddKind::Outlet | AddKind::Light | AddKind::Switch | AddKind::Jbox => {
            // Allowed under elec tree or spatial room/floor
            let leaf = path.rsplit('/').next().unwrap_or("");
            let ok = under_elec
                || leaf.starts_with("rm.")
                || leaf.starts_with("fl.")
                || leaf.starts_with("ckt.")
                || leaf.starts_with("panel.")
                || leaf.starts_with("jbox.");
            if !ok {
                // Still allow if parent resolves as room/floor/building
                // Caller checks resolve; soft allow building root
            }
        }
    }
    Ok(())
}

/// Add a new equipment entity under `parent_path`. Mutates `building` in memory.
pub fn add_under_address(
    building: &mut Building,
    parent_path: &str,
    kind: AddKind,
    name: Option<&str>,
) -> Result<AddResult> {
    let parent_in = parse_address(parent_path)?;
    // Parent must resolve (real entity or virtual system prefix)
    let parent_ref = resolve(building, &parent_in.path)?;

    // Building root + panel → create under …/elec (bootstrap electrical tree)
    let parent = if kind == AddKind::Panel && parent_ref.kind == EntityKind::Building {
        parent_in.join(ELEC_ROOT)?
    } else {
        parent_in.clone()
    };

    validate_parent_for_kind(&parent, kind)?;

    // Stricter: panel parent for circuit
    if kind == AddKind::Circuit {
        let leaf = parent.path.rsplit('/').next().unwrap_or("");
        if !leaf.starts_with("panel.") {
            bail!(
                "Invalid parent for circuit: expected panel.* (got '{}')",
                parent.path
            );
        }
    }
    if kind == AddKind::Panel {
        let leaf = parent.path.rsplit('/').next().unwrap_or("");
        if leaf != ELEC_ROOT {
            bail!(
                "Invalid parent for panel: expected …/elec or building root (got '{}')",
                parent.path
            );
        }
    }

    let addr = allocate_child_address(building, &parent, kind, name)?;
    let leaf_id = addr
        .path
        .rsplit('/')
        .next()
        .and_then(|s| s.split_once('.').map(|(_, id)| id))
        .unwrap_or("1");
    let display_name = name
        .map(str::trim)
        .filter(|s| !s.is_empty())
        .map(|s| s.to_string())
        .unwrap_or_else(|| kind.default_display_name(leaf_id));

    let mut eq = Equipment::new(display_name.clone(), String::new(), kind.equipment_type());
    eq.address = Some(addr.clone());
    eq.path = addr.path.clone();
    eq.ifc_global_id = None; // Arxos-native; GlobalId on export later
    eq.position = Position {
        x: 0.0,
        y: 0.0,
        z: 0.0,
        coordinate_system: "building_local".into(),
    };

    place_equipment(building, &parent_ref.kind, &parent, &mut eq)?;

    Ok(AddResult {
        address: addr,
        name: display_name,
        kind,
    })
}

fn place_equipment(
    building: &mut Building,
    parent_kind: &EntityKind,
    parent: &ArxAddress,
    eq: &mut Equipment,
) -> Result<()> {
    // Prefer explicit room parent
    if *parent_kind == EntityKind::Room {
        for floor in &mut building.floors {
            for wing in &mut floor.wings {
                if let Some(room) = wing.rooms.iter_mut().find(|r| {
                    r.address
                        .as_ref()
                        .map(|a| a.path == parent.path)
                        .unwrap_or(false)
                }) {
                    eq.set_room(room.id.clone());
                    room.equipment.push(eq.clone());
                    return Ok(());
                }
            }
        }
    }

    // Floor parent → floor equipment
    if *parent_kind == EntityKind::Floor {
        if let Some(floor) = building.floors.iter_mut().find(|f| {
            f.address
                .as_ref()
                .map(|a| a.path == parent.path)
                .unwrap_or(false)
        }) {
            floor.equipment.push(eq.clone());
            return Ok(());
        }
    }

    // Electrical / virtual / building: attach to first room if any, else first floor
    if let Some(floor) = building.floors.first_mut() {
        if let Some(wing) = floor.wings.first_mut() {
            if let Some(room) = wing.rooms.first_mut() {
                eq.set_room(room.id.clone());
                room.equipment.push(eq.clone());
                return Ok(());
            }
        }
        floor.equipment.push(eq.clone());
        return Ok(());
    }

    bail!("Building has no floors to attach equipment");
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::core::domain::ArxAddress;
    use crate::core::{Building, Floor, Room, RoomType, Wing};

    fn sample() -> Building {
        let root = ArxAddress::from_path("bldg.us.fl.tampa.dale-mabry.143677.s2").unwrap();
        let mut b = Building::new("HQ".into(), "/hq".into());
        b.address = Some(root.clone());
        let mut floor = Floor::new("Level 1".into(), 1);
        floor.address = Some(root.join("fl.1").unwrap());
        let mut wing = Wing::new("Main".into());
        let mut room = Room::new("A101".into(), RoomType::Office);
        room.address = Some(floor.address.as_ref().unwrap().join("rm.a101").unwrap());
        // Seed one existing outlet so next is rec.2
        let mut existing = Equipment::new("Outlet 1".into(), String::new(), EquipmentType::Electrical);
        existing.address = Some(
            root.join("elec")
                .unwrap()
                .join("panel.l1")
                .unwrap()
                .join("ckt.14")
                .unwrap()
                .join("rec.1")
                .unwrap(),
        );
        room.add_equipment(existing);
        wing.add_room(room);
        floor.add_wing(wing);
        b.add_floor(floor);
        b
    }

    #[test]
    fn next_numeric_deterministic() {
        let b = sample();
        let parent = ArxAddress::from_path(
            "bldg.us.fl.tampa.dale-mabry.143677.s2/elec/panel.l1/ckt.14",
        )
        .unwrap();
        // Parent is virtual — seed addresses only via equipment
        assert_eq!(next_numeric_id(&b, &parent, "rec"), 2);
        assert_eq!(next_numeric_id(&b, &parent, "ltg"), 1);
    }

    #[test]
    fn add_outlet_under_circuit() {
        let mut b = sample();
        // Ensure virtual parent path has a descendant so resolve works
        let r = add_under_address(
            &mut b,
            "bldg.us.fl.tampa.dale-mabry.143677.s2/elec/panel.l1/ckt.14",
            AddKind::Outlet,
            None,
        )
        .unwrap();
        assert_eq!(
            r.address.path,
            "/bldg.us.fl.tampa.dale-mabry.143677.s2/elec/panel.l1/ckt.14/rec.2"
        );
        assert!(r.address.validate().is_ok());
        // No GlobalId on native entity
        let eq = b
            .get_all_equipment()
            .into_iter()
            .find(|e| e.address.as_ref().map(|a| a.path.as_str()) == Some(r.address.path.as_str()))
            .unwrap();
        assert!(eq.ifc_global_id.is_none());

        // Second add → rec.3
        let r2 = add_under_address(
            &mut b,
            "/bldg.us.fl.tampa.dale-mabry.143677.s2/elec/panel.l1/ckt.14",
            AddKind::Outlet,
            None,
        )
        .unwrap();
        assert!(r2.address.path.ends_with("/rec.3"));
    }

    #[test]
    fn add_with_name_and_collision() {
        let mut b = sample();
        let r = add_under_address(
            &mut b,
            "bldg.us.fl.tampa.dale-mabry.143677.s2/elec/panel.l1/ckt.14",
            AddKind::Outlet,
            Some("Kitchen-Island"),
        )
        .unwrap();
        assert!(r.address.path.ends_with("/rec.kitchen-island"));
        let err = add_under_address(
            &mut b,
            "bldg.us.fl.tampa.dale-mabry.143677.s2/elec/panel.l1/ckt.14",
            AddKind::Outlet,
            Some("Kitchen-Island"),
        );
        assert!(err.is_err());
        assert!(err.unwrap_err().to_string().contains("collision"));
    }

    #[test]
    fn add_under_spatial_room() {
        let mut b = sample();
        let r = add_under_address(
            &mut b,
            "bldg.us.fl.tampa.dale-mabry.143677.s2/fl.1/rm.a101",
            AddKind::Light,
            None,
        )
        .unwrap();
        assert!(r.address.path.contains("/rm.a101/ltg.1"));
        let room = &b.floors[0].wings[0].rooms[0];
        assert!(room.equipment.iter().any(|e| {
            e.address.as_ref().map(|a| a.path.as_str()) == Some(r.address.path.as_str())
        }));
    }

    #[test]
    fn reject_bad_parent_and_kind() {
        let mut b = sample();
        assert!(AddKind::parse("boiler").is_err());
        let err = add_under_address(
            &mut b,
            "bldg.us.fl.tampa.dale-mabry.143677.s2/nope",
            AddKind::Outlet,
            None,
        );
        assert!(err.is_err());
        let err = add_under_address(
            &mut b,
            "bldg.us.fl.tampa.dale-mabry.143677.s2/fl.1",
            AddKind::Circuit,
            None,
        );
        assert!(err.unwrap_err().to_string().contains("panel"));
    }

    #[test]
    fn add_panel_under_elec() {
        let mut b = sample();
        // Existing rec creates …/elec/… so elec resolves
        let r = add_under_address(
            &mut b,
            "bldg.us.fl.tampa.dale-mabry.143677.s2/elec",
            AddKind::Panel,
            Some("L2"),
        )
        .unwrap();
        assert_eq!(
            r.address.path,
            "/bldg.us.fl.tampa.dale-mabry.143677.s2/elec/panel.l2"
        );
    }

    #[test]
    fn add_panel_under_building_bootstraps_elec() {
        let mut b = sample();
        // Remove all equipment so /elec has no descendants — panel under building still works
        b.floors[0].wings[0].rooms[0].equipment.clear();
        let r = add_under_address(
            &mut b,
            "bldg.us.fl.tampa.dale-mabry.143677.s2",
            AddKind::Panel,
            Some("L1"),
        )
        .unwrap();
        assert_eq!(
            r.address.path,
            "/bldg.us.fl.tampa.dale-mabry.143677.s2/elec/panel.l1"
        );
    }
}
