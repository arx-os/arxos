//! Address-based navigation over a loaded `Building` (ADR 0001).
//!
//! Pure helpers used by `arx show` / `arx ls` / `arx tree`. Resolution keys on
//! durable `address` fields only — never on internal UUIDs.

use crate::core::domain::ArxAddress;
use crate::core::{Building, Equipment, Floor, Room, Wing};
use anyhow::{anyhow, Result};

/// Kind of domain entity resolved by address.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum EntityKind {
    Building,
    Floor,
    Wing,
    Room,
    Equipment,
    /// Virtual intermediate node derived from address prefixes (e.g. `…/elec`, `…/elec/panel.l1`).
    System,
}

impl EntityKind {
    pub fn as_str(self) -> &'static str {
        match self {
            EntityKind::Building => "building",
            EntityKind::Floor => "floor",
            EntityKind::Wing => "wing",
            EntityKind::Room => "room",
            EntityKind::Equipment => "equipment",
            EntityKind::System => "system",
        }
    }
}

/// A resolved entity reference with display metadata (no internal UUID).
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct EntityRef {
    pub kind: EntityKind,
    pub name: String,
    pub address: ArxAddress,
    pub ifc_global_id: Option<String>,
    /// Short type label (room_type / equipment_type / storey name already in `name`).
    pub type_label: Option<String>,
    pub child_count: usize,
    /// Selected property pairs (stable key order when populated).
    pub properties: Vec<(String, String)>,
}

/// One row for `ls` / tree listing.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ChildEntry {
    pub kind: EntityKind,
    pub name: String,
    pub address: ArxAddress,
}

/// Tree node for hierarchical print.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct TreeNode {
    pub entry: ChildEntry,
    pub children: Vec<TreeNode>,
}

/// Normalize a user-supplied path to a canonical `ArxAddress`.
pub fn parse_address(path: &str) -> Result<ArxAddress> {
    ArxAddress::from_path(path.trim()).map_err(|e| anyhow!("{}", e))
}

/// True when `child` is a direct (one-segment) descendant of `parent`.
pub fn is_direct_child(parent: &ArxAddress, child: &ArxAddress) -> bool {
    if child.path == parent.path {
        return false;
    }
    let p = parent.path.trim_end_matches('/');
    let prefix = format!("{}/", p);
    if !child.path.starts_with(&prefix) {
        return false;
    }
    let rest = &child.path[prefix.len()..];
    !rest.is_empty() && !rest.contains('/')
}

/// Resolve an address to a single entity in the building.
///
/// Intermediate system paths (e.g. `…/elec`, `…/elec/panel.l1`) that appear only
/// as prefixes of equipment addresses resolve as virtual [`EntityKind::System`] nodes.
pub fn resolve(building: &Building, path: &str) -> Result<EntityRef> {
    let target = parse_address(path)?;
    let mut hits: Vec<EntityRef> = Vec::new();

    if let Some(ref a) = building.address {
        if a.path == target.path {
            hits.push(entity_ref_building(building));
        }
    }

    for floor in &building.floors {
        if let Some(ref a) = floor.address {
            if a.path == target.path {
                hits.push(entity_ref_floor(floor));
            }
        }
        for eq in &floor.equipment {
            if let Some(ref a) = eq.address {
                if a.path == target.path {
                    hits.push(entity_ref_equipment(eq));
                }
            }
        }
        for wing in &floor.wings {
            if let Some(ref a) = wing.address {
                if a.path == target.path {
                    hits.push(entity_ref_wing(wing));
                }
            }
            for eq in &wing.equipment {
                if let Some(ref a) = eq.address {
                    if a.path == target.path {
                        hits.push(entity_ref_equipment(eq));
                    }
                }
            }
            for room in &wing.rooms {
                if let Some(ref a) = room.address {
                    if a.path == target.path {
                        hits.push(entity_ref_room(room));
                    }
                }
                for eq in &room.equipment {
                    if let Some(ref a) = eq.address {
                        if a.path == target.path {
                            hits.push(entity_ref_equipment(eq));
                        }
                    }
                }
            }
        }
    }

    match hits.len() {
        0 => {
            // Virtual system / intermediate node if any addressed entity lives under this path
            if path_has_descendants(building, &target) {
                let leaf = target
                    .path
                    .rsplit('/')
                    .next()
                    .unwrap_or("system")
                    .to_string();
                let child_count = list_children_unverified(building, &target).len();
                return Ok(EntityRef {
                    kind: EntityKind::System,
                    name: leaf,
                    address: target,
                    ifc_global_id: None,
                    type_label: Some("virtual".into()),
                    child_count,
                    properties: Vec::new(),
                });
            }
            Err(anyhow!("No entity found at address '{}'", target.path))
        }
        1 => Ok(hits.remove(0)),
        n => Err(anyhow!(
            "Ambiguous address '{}': {} entities share this path",
            target.path,
            n
        )),
    }
}

/// List direct children of an address (deterministic order by address path).
pub fn list_children(building: &Building, path: &str) -> Result<Vec<ChildEntry>> {
    let parent = parse_address(path)?;
    // Parent must exist as real entity or virtual prefix
    let _ = resolve(building, &parent.path)?;
    Ok(list_children_unverified(building, &parent))
}

fn list_children_unverified(building: &Building, parent: &ArxAddress) -> Vec<ChildEntry> {
    let mut children = collect_all_addressed(building)
        .into_iter()
        .filter(|c| is_direct_child(parent, &c.address))
        .collect::<Vec<_>>();

    // Virtual intermediate children: unique next path segments under parent
    // that are not already exact entity paths.
    let existing: std::collections::HashSet<String> =
        children.iter().map(|c| c.address.path.clone()).collect();
    let p = parent.path.trim_end_matches('/');
    let prefix = format!("{}/", p);
    let mut virtuals: std::collections::BTreeMap<String, String> = std::collections::BTreeMap::new();
    for entry in collect_all_addressed(building) {
        if !entry.address.path.starts_with(&prefix) {
            continue;
        }
        let rest = &entry.address.path[prefix.len()..];
        let next = rest.split('/').next().unwrap_or("");
        if next.is_empty() {
            continue;
        }
        let child_path = format!("{}/{}", p, next);
        if existing.contains(&child_path) {
            continue;
        }
        // Virtual intermediate only when a deeper descendant exists under this segment
        if rest.contains('/') {
            virtuals
                .entry(child_path.clone())
                .or_insert_with(|| next.to_string());
        }
    }
    for (path, name) in virtuals {
        if let Ok(addr) = ArxAddress::from_path(&path) {
            children.push(ChildEntry {
                kind: EntityKind::System,
                name,
                address: addr,
            });
        }
    }

    children.sort_by(|a, b| a.address.path.cmp(&b.address.path));
    children.dedup_by(|a, b| a.address.path == b.address.path);
    children
}

fn path_has_descendants(building: &Building, parent: &ArxAddress) -> bool {
    let p = parent.path.trim_end_matches('/');
    let prefix = format!("{}/", p);
    collect_all_addressed(building)
        .iter()
        .any(|c| c.address.path.starts_with(&prefix))
}

/// Build a tree rooted at `path` with maximum depth (`depth == 0` means only the root).
pub fn build_tree(building: &Building, path: &str, depth: usize) -> Result<TreeNode> {
    let root_ref = resolve(building, path)?;
    let root = TreeNode {
        entry: ChildEntry {
            kind: root_ref.kind,
            name: root_ref.name.clone(),
            address: root_ref.address.clone(),
        },
        children: Vec::new(),
    };
    Ok(fill_tree(building, root, depth))
}

fn fill_tree(building: &Building, mut node: TreeNode, depth: usize) -> TreeNode {
    if depth == 0 {
        return node;
    }
    let children = match list_children(building, &node.entry.address.path) {
        Ok(c) => c,
        Err(_) => return node,
    };
    for child in children {
        let child_node = TreeNode {
            entry: child,
            children: Vec::new(),
        };
        node.children
            .push(fill_tree(building, child_node, depth - 1));
    }
    node
}

/// Format `show` output (stable line keys for tests).
pub fn format_show(entity: &EntityRef) -> String {
    let mut lines = Vec::new();
    lines.push(format!("type: {}", entity.kind.as_str()));
    lines.push(format!("name: {}", entity.name));
    lines.push(format!("address: {}", entity.address.path));
    if let Some(ref t) = entity.type_label {
        lines.push(format!("type_label: {}", t));
    }
    match &entity.ifc_global_id {
        Some(g) if !g.is_empty() => lines.push(format!("ifc_global_id: {}", g)),
        _ => lines.push("ifc_global_id: (none)".into()),
    }
    lines.push(format!("children: {}", entity.child_count));
    if !entity.properties.is_empty() {
        lines.push("properties:".into());
        for (k, v) in &entity.properties {
            lines.push(format!("  {}: {}", k, v));
        }
    }
    lines.join("\n")
}

/// Format `ls` output.
pub fn format_ls(children: &[ChildEntry]) -> String {
    if children.is_empty() {
        return "(no children)".to_string();
    }
    let mut lines = Vec::with_capacity(children.len());
    for c in children {
        lines.push(format!(
            "{:<10}  {:<24}  {}",
            c.kind.as_str(),
            truncate(&c.name, 24),
            c.address.path
        ));
    }
    lines.join("\n")
}

/// Format tree output (Unicode box drawing, stable).
pub fn format_tree(node: &TreeNode) -> String {
    let mut lines = Vec::new();
    lines.push(format!(
        "{}  {}  ({})",
        node.entry.address.path,
        node.entry.name,
        node.entry.kind.as_str()
    ));
    let n = node.children.len();
    for (i, child) in node.children.iter().enumerate() {
        format_tree_rec(child, "", i + 1 == n, &mut lines);
    }
    lines.join("\n")
}

fn format_tree_rec(node: &TreeNode, prefix: &str, is_last: bool, lines: &mut Vec<String>) {
    let branch = if is_last { "└── " } else { "├── " };
    lines.push(format!(
        "{}{}{}  ({})",
        prefix,
        branch,
        node.entry.name,
        node.entry.kind.as_str()
    ));
    // Second line with address for clarity at each node
    let cont = if is_last { "    " } else { "│   " };
    lines.push(format!("{}{}    {}", prefix, cont, node.entry.address.path));

    let child_prefix = format!("{}{}", prefix, cont);
    let n = node.children.len();
    for (i, child) in node.children.iter().enumerate() {
        format_tree_rec(child, &child_prefix, i + 1 == n, lines);
    }
}

fn truncate(s: &str, max: usize) -> String {
    if s.chars().count() <= max {
        return s.to_string();
    }
    let mut out: String = s.chars().take(max.saturating_sub(1)).collect();
    out.push('…');
    out
}

/// All entities that currently carry an address (for mutation / allocation).
pub fn collect_all_addressed(building: &Building) -> Vec<ChildEntry> {
    let mut out = Vec::new();
    if let Some(ref a) = building.address {
        out.push(ChildEntry {
            kind: EntityKind::Building,
            name: building.name.clone(),
            address: a.clone(),
        });
    }
    for floor in &building.floors {
        if let Some(ref a) = floor.address {
            out.push(ChildEntry {
                kind: EntityKind::Floor,
                name: floor.name.clone(),
                address: a.clone(),
            });
        }
        for eq in &floor.equipment {
            push_eq(&mut out, eq);
        }
        for wing in &floor.wings {
            if let Some(ref a) = wing.address {
                out.push(ChildEntry {
                    kind: EntityKind::Wing,
                    name: wing.name.clone(),
                    address: a.clone(),
                });
            }
            for eq in &wing.equipment {
                push_eq(&mut out, eq);
            }
            for room in &wing.rooms {
                if let Some(ref a) = room.address {
                    out.push(ChildEntry {
                        kind: EntityKind::Room,
                        name: room.name.clone(),
                        address: a.clone(),
                    });
                }
                for eq in &room.equipment {
                    push_eq(&mut out, eq);
                }
            }
        }
    }
    out
}

fn push_eq(out: &mut Vec<ChildEntry>, eq: &Equipment) {
    if let Some(ref a) = eq.address {
        out.push(ChildEntry {
            kind: EntityKind::Equipment,
            name: eq.name.clone(),
            address: a.clone(),
        });
    }
}

fn entity_ref_building(b: &Building) -> EntityRef {
    let child_count = b.floors.len();
    EntityRef {
        kind: EntityKind::Building,
        name: b.name.clone(),
        address: b.address.clone().expect("checked"),
        ifc_global_id: b.ifc_global_id.clone(),
        type_label: None,
        child_count,
        properties: Vec::new(),
    }
}

fn entity_ref_floor(f: &Floor) -> EntityRef {
    let rooms: usize = f.wings.iter().map(|w| w.rooms.len()).sum();
    let child_count = f.wings.len() + f.equipment.len() + rooms;
    // Direct children for display count: wings + floor equipment + rooms under wings
    // More accurate: use same as list_children would — approximate with wings+equip+rooms
    EntityRef {
        kind: EntityKind::Floor,
        name: f.name.clone(),
        address: f.address.clone().expect("checked"),
        ifc_global_id: f.ifc_global_id.clone(),
        type_label: Some(format!("level={}", f.level)),
        child_count,
        properties: sorted_props(&f.properties),
    }
}

fn entity_ref_wing(w: &Wing) -> EntityRef {
    EntityRef {
        kind: EntityKind::Wing,
        name: w.name.clone(),
        address: w.address.clone().expect("checked"),
        ifc_global_id: None,
        type_label: None,
        child_count: w.rooms.len() + w.equipment.len(),
        properties: sorted_props(&w.properties),
    }
}

fn entity_ref_room(r: &Room) -> EntityRef {
    EntityRef {
        kind: EntityKind::Room,
        name: r.name.clone(),
        address: r.address.clone().expect("checked"),
        ifc_global_id: r.ifc_global_id.clone(),
        type_label: Some(format!("{:?}", r.room_type)),
        child_count: r.equipment.len(),
        properties: sorted_props(&r.properties),
    }
}

fn entity_ref_equipment(e: &Equipment) -> EntityRef {
    EntityRef {
        kind: EntityKind::Equipment,
        name: e.name.clone(),
        address: e.address.clone().expect("checked"),
        ifc_global_id: e.ifc_global_id.clone(),
        type_label: Some(format!("{:?}", e.equipment_type)),
        child_count: 0,
        properties: sorted_props(&e.properties),
    }
}

fn sorted_props(map: &std::collections::HashMap<String, String>) -> Vec<(String, String)> {
    let mut keys: Vec<_> = map.keys().cloned().collect();
    keys.sort();
    keys.into_iter()
        .filter_map(|k| {
            // Cap noise: skip very long values
            let v = map.get(&k)?;
            if v.len() > 120 {
                Some((k, format!("{}…", &v[..117])))
            } else {
                Some((k, v.clone()))
            }
        })
        .take(12)
        .collect()
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::core::domain::ArxAddress;
    use crate::core::{Building, Equipment, EquipmentType, Floor, Room, RoomType, Wing};

    fn sample_building() -> Building {
        let root = ArxAddress::lab_building_root("duplex");
        let mut b = Building::new("Duplex".into(), "/duplex".into());
        b.address = Some(root.clone());
        b.ifc_global_id = Some("AbcGlobalId01234567890".into());

        let fl1 = root.join("fl.1").unwrap();
        let fl2 = root.join("fl.2").unwrap();
        let mut floor1 = Floor::new("Level 1".into(), 1);
        floor1.address = Some(fl1.clone());
        floor1.ifc_global_id = Some("FloorGid0000000000001".into());

        let mut wing = Wing::new("Main".into());
        // Wing intentionally without address so rooms sit under floor

        let mut room = Room::new("A101".into(), RoomType::Office);
        room.address = Some(fl1.join("rm.a101").unwrap());
        room.ifc_global_id = Some("RoomGid00000000000001".into());
        room.properties
            .insert("occupancy".into(), "office".into());

        let mut eq = Equipment::new("Sensor-A".into(), String::new(), EquipmentType::Other("sensor".into()));
        eq.address = Some(room.address.as_ref().unwrap().join("sensor-a").unwrap());
        room.add_equipment(eq);

        let mut room2 = Room::new("A102".into(), RoomType::Office);
        room2.address = Some(fl1.join("rm.a102").unwrap());

        wing.add_room(room);
        wing.add_room(room2);
        floor1.add_wing(wing);

        let mut floor2 = Floor::new("Level 2".into(), 2);
        floor2.address = Some(fl2);

        b.add_floor(floor1);
        b.add_floor(floor2);
        b
    }

    #[test]
    fn resolve_building_with_and_without_slash() {
        let b = sample_building();
        let root = b.address.as_ref().unwrap().path.clone();
        let bare = root.trim_start_matches('/').to_string();
        let r1 = resolve(&b, &root).unwrap();
        let r2 = resolve(&b, &bare).unwrap();
        assert_eq!(r1.kind, EntityKind::Building);
        assert_eq!(r1.address.path, r2.address.path);
        assert_eq!(r1.name, "Duplex");
        assert!(r1.ifc_global_id.is_some());
    }

    #[test]
    fn resolve_room_and_equipment() {
        let b = sample_building();
        let room_path = format!(
            "{}/fl.1/rm.a101",
            b.address.as_ref().unwrap().path
        );
        let r = resolve(&b, &room_path).unwrap();
        assert_eq!(r.kind, EntityKind::Room);
        assert_eq!(r.name, "A101");
        assert_eq!(r.child_count, 1);

        let eq_path = format!("{}/sensor-a", room_path);
        let e = resolve(&b, &eq_path).unwrap();
        assert_eq!(e.kind, EntityKind::Equipment);
        assert_eq!(e.name, "Sensor-A");
    }

    #[test]
    fn resolve_missing_is_error() {
        let b = sample_building();
        let err = resolve(&b, "/bldg.lab.local.sample.nope/fl.9").unwrap_err();
        assert!(err.to_string().contains("No entity found"));
    }

    #[test]
    fn ls_floor_lists_rooms_sorted() {
        let b = sample_building();
        let fl = format!("{}/fl.1", b.address.as_ref().unwrap().path);
        let kids = list_children(&b, &fl).unwrap();
        assert_eq!(kids.len(), 2);
        assert_eq!(kids[0].name, "A101");
        assert_eq!(kids[1].name, "A102");
        assert!(kids[0].address.path < kids[1].address.path);
    }

    #[test]
    fn ls_building_lists_floors() {
        let b = sample_building();
        let root = b.address.as_ref().unwrap().path.clone();
        let kids = list_children(&b, &root).unwrap();
        assert_eq!(kids.len(), 2);
        assert_eq!(kids[0].kind, EntityKind::Floor);
        assert!(kids[0].address.path.ends_with("/fl.1"));
        assert!(kids[1].address.path.ends_with("/fl.2"));
    }

    #[test]
    fn tree_depth_limits() {
        let b = sample_building();
        let root = b.address.as_ref().unwrap().path.clone();
        let t0 = build_tree(&b, &root, 0).unwrap();
        assert!(t0.children.is_empty());
        let t1 = build_tree(&b, &root, 1).unwrap();
        assert_eq!(t1.children.len(), 2);
        assert!(t1.children[0].children.is_empty());
        let t2 = build_tree(&b, &root, 2).unwrap();
        assert!(!t2.children[0].children.is_empty());
    }

    #[test]
    fn show_format_stable_keys() {
        let b = sample_building();
        let root = b.address.as_ref().unwrap().path.clone();
        let entity = resolve(&b, &root).unwrap();
        let out = format_show(&entity);
        assert!(out.starts_with("type: building\n"));
        assert!(out.contains("name: Duplex\n"));
        assert!(out.contains(&format!("address: {}\n", root)));
        assert!(out.contains("ifc_global_id:"));
        // Do not surface internal UUID as a primary field
        assert!(!out.lines().any(|l| l.starts_with("id:")));
        assert!(!out.lines().any(|l| l.starts_with("uuid:")));
        assert!(out.contains("children:"));
    }

    #[test]
    fn is_direct_child_logic() {
        let p = ArxAddress::from_path("/bldg.lab.local.sample.x").unwrap();
        let c = ArxAddress::from_path("/bldg.lab.local.sample.x/fl.1").unwrap();
        let g = ArxAddress::from_path("/bldg.lab.local.sample.x/fl.1/rm.a").unwrap();
        assert!(is_direct_child(&p, &c));
        assert!(!is_direct_child(&p, &g));
        assert!(!is_direct_child(&p, &p));
    }

    fn sample_with_elec() -> Building {
        let mut b = sample_building();
        let root = b.address.as_ref().unwrap().clone();
        let mut eq = Equipment::new(
            "Rec-7".into(),
            String::new(),
            EquipmentType::Electrical,
        );
        eq.address = Some(
            crate::core::domain::build_elec_address(
                &root,
                &["panel.l1", "ckt.14", "rec.7"],
            )
            .unwrap(),
        );
        eq.ifc_global_id = Some("ElecGid00000000000001".into());
        // Place under first room for graph containment
        b.floors[0].wings[0].rooms[0].equipment.push(eq);
        b
    }

    #[test]
    fn resolve_elec_leaf_and_virtual_intermediates() {
        let b = sample_with_elec();
        let root = b.address.as_ref().unwrap().path.clone();
        let rec = format!("{}/elec/panel.l1/ckt.14/rec.7", root);
        let entity = resolve(&b, &rec).unwrap();
        assert_eq!(entity.kind, EntityKind::Equipment);
        assert_eq!(entity.name, "Rec-7");
        assert_eq!(entity.ifc_global_id.as_deref(), Some("ElecGid00000000000001"));

        let elec = format!("{}/elec", root);
        let sys = resolve(&b, &elec).unwrap();
        assert_eq!(sys.kind, EntityKind::System);
        assert_eq!(sys.name, "elec");

        let panel = format!("{}/elec/panel.l1", root);
        let p = resolve(&b, &panel).unwrap();
        assert_eq!(p.kind, EntityKind::System);
        assert!(p.name.starts_with("panel"));
    }

    #[test]
    fn ls_and_tree_elec_subtree() {
        let b = sample_with_elec();
        let root = b.address.as_ref().unwrap().path.clone();
        let elec = format!("{}/elec", root);
        let kids = list_children(&b, &elec).unwrap();
        assert_eq!(kids.len(), 1);
        assert!(kids[0].address.path.ends_with("/elec/panel.l1"));

        let tree = build_tree(&b, &elec, 4).unwrap();
        let out = format_tree(&tree);
        assert!(out.contains("elec"));
        assert!(out.contains("panel.l1") || out.contains("panel"));
        assert!(out.contains("Rec-7") || out.contains("rec.7"));
    }

    #[test]
    fn spatial_addresses_still_resolve() {
        let b = sample_with_elec();
        let room_path = format!(
            "{}/fl.1/rm.a101",
            b.address.as_ref().unwrap().path
        );
        let r = resolve(&b, &room_path).unwrap();
        assert_eq!(r.kind, EntityKind::Room);
    }
}
