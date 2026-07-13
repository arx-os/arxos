//! Unified building merge for multi-source ingest (IFC, LiDAR, …).
//!
//! Match priority for rooms and equipment:
//! 1. `ifc_global_id` (both present and equal)
//! 2. Arx `id`
//! 3. Hierarchical name path (floor / wing / room / equipment)
//! 4. Optional spatial proximity (LiDAR re-scan)
//!
//! # Hierarchy base
//!
//! - **Incoming** (IFC): result structure follows the incoming model; unmatched
//!   existing entities are omitted (counted in stats).
//! - **Existing** (LiDAR): result starts from existing; unmatched existing kept;
//!   new entities from the scan are added.

use std::collections::{HashMap, HashSet};

use crate::core::{Building, Equipment, EquipmentType, Floor, Position, Room};

use super::prefer_existing_lidar;
use super::report::{LossReport, MappingWarning, MergeStats};

/// Which ingest source is driving the merge (affects match heuristics).
#[derive(Debug, Clone, Copy, PartialEq, Eq, Default)]
pub enum MergeSource {
    #[default]
    Ifc,
    Lidar,
}

/// Whether the result hierarchy is rooted in existing or incoming.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Default)]
pub enum HierarchyBase {
    /// Full replace structure from incoming (IFC re-import).
    #[default]
    Incoming,
    /// Incremental update of existing (LiDAR re-scan).
    Existing,
}

/// Configurable merge policy for ingest adapters.
#[derive(Debug, Clone)]
pub struct MergePolicy {
    pub source: MergeSource,
    pub hierarchy: HierarchyBase,
    /// When set, rooms on the same floor match if centroids are within this distance (m).
    pub room_match_radius_m: Option<f64>,
    /// When set, equipment matches if same type and within this distance (m).
    pub equipment_match_radius_m: Option<f64>,
}

impl MergePolicy {
    /// Default IFC re-import policy.
    pub fn ifc() -> Self {
        Self {
            source: MergeSource::Ifc,
            hierarchy: HierarchyBase::Incoming,
            room_match_radius_m: None,
            equipment_match_radius_m: None,
        }
    }

    /// LiDAR incremental re-scan policy (preserve existing, spatial match).
    pub fn lidar() -> Self {
        Self {
            source: MergeSource::Lidar,
            hierarchy: HierarchyBase::Existing,
            room_match_radius_m: Some(2.0),
            equipment_match_radius_m: Some(1.5),
        }
    }
}

/// Result of merging an existing Arx building with an incoming model.
#[derive(Debug, Clone)]
pub struct MergeResult {
    pub building: Building,
    pub stats: MergeStats,
    pub warnings: Vec<MappingWarning>,
}

/// Merge with the default IFC policy.
pub fn merge_building(existing: &Building, incoming: Building) -> MergeResult {
    merge_building_with_policy(existing, incoming, &MergePolicy::ifc())
}

/// Merge with an explicit policy (IFC, LiDAR, or custom).
pub fn merge_building_with_policy(
    existing: &Building,
    incoming: Building,
    policy: &MergePolicy,
) -> MergeResult {
    match policy.hierarchy {
        HierarchyBase::Incoming => merge_incoming_base(existing, incoming, policy),
        HierarchyBase::Existing => merge_existing_base(existing, incoming, policy),
    }
}

/// Apply merge into a loss report (convenience for import pipelines).
pub fn merge_into_report(
    existing: &Building,
    incoming: Building,
    report: &mut LossReport,
) -> Building {
    merge_into_report_with_policy(existing, incoming, report, &MergePolicy::ifc())
}

/// Apply merge with policy into a loss report.
pub fn merge_into_report_with_policy(
    existing: &Building,
    incoming: Building,
    report: &mut LossReport,
    policy: &MergePolicy,
) -> Building {
    let result = merge_building_with_policy(existing, incoming, policy);
    report.merge = Some(result.stats);
    report.warnings.extend(result.warnings);
    result.building
}

// ---------------------------------------------------------------------------
// Incoming base (IFC)
// ---------------------------------------------------------------------------

fn merge_incoming_base(
    existing: &Building,
    incoming: Building,
    policy: &MergePolicy,
) -> MergeResult {
    let mut stats = MergeStats::default();
    let mut warnings = Vec::new();
    let mut building = incoming;

    if building.ifc_global_id.is_none() {
        building.ifc_global_id = existing.ifc_global_id.clone();
    }
    if ids_match(
        existing.ifc_global_id.as_deref(),
        building.ifc_global_id.as_deref(),
    ) || existing.name == building.name
        || existing.id == building.id
    {
        building.id = existing.id.clone();
        building.created_at = existing.created_at;
        if building.path.is_empty() {
            building.path = existing.path.clone();
        }
    }

    merge_building_metadata(&mut building, existing);

    let (existing_floors, existing_rooms, existing_equipment) = index_existing(existing);
    let mut matched_room_keys: HashSet<String> = HashSet::new();
    let mut matched_eq_keys: HashSet<String> = HashSet::new();

    for floor in &mut building.floors {
        let floor_path = floor.name.clone();
        if let Some(old_floor) = find_floor(&existing_floors, floor) {
            stats.floors_matched += 1;
            apply_floor_identity(floor, old_floor);
        } else {
            stats.floors_added += 1;
        }

        // Spatial room candidates from existing floor (clone positions for matching)
        let spatial_room_candidates: Vec<(String, Position)> = existing
            .floors
            .iter()
            .filter(|f| f.level == floor.level || f.name == floor.name || f.id == floor.id)
            .flat_map(|f| {
                f.wings.iter().flat_map(|w| {
                    w.rooms
                        .iter()
                        .map(|r| (r.id.clone(), r.spatial_properties.position.clone()))
                })
            })
            .collect();

        for eq in &mut floor.equipment {
            let path = format!("{}/{}", floor_path, eq.name);
            match find_equipment(&existing_equipment, eq, &path, policy, &[]) {
                Some((key, old_eq)) => {
                    stats.equipment_matched += 1;
                    matched_eq_keys.insert(key);
                    merge_equipment_fields(eq, old_eq, policy);
                }
                None => stats.equipment_added += 1,
            }
        }

        for wing in &mut floor.wings {
            let wing_path = format!("{}/{}", floor_path, wing.name);
            for eq in &mut wing.equipment {
                let path = format!("{}/{}", wing_path, eq.name);
                match find_equipment(&existing_equipment, eq, &path, policy, &[]) {
                    Some((key, old_eq)) => {
                        stats.equipment_matched += 1;
                        matched_eq_keys.insert(key);
                        merge_equipment_fields(eq, old_eq, policy);
                    }
                    None => stats.equipment_added += 1,
                }
            }

            for room in &mut wing.rooms {
                let room_path = format!("{}/{}", floor_path, room.name);
                let room_path_wing = format!("{}/{}/{}", floor_path, wing.name, room.name);
                match find_room(
                    &existing_rooms,
                    room,
                    &room_path,
                    &room_path_wing,
                    policy,
                    &spatial_room_candidates,
                ) {
                    Some((key, old_room)) => {
                        stats.rooms_matched += 1;
                        matched_room_keys.insert(key);
                        merge_room_fields(room, old_room, policy);
                    }
                    None => stats.rooms_added += 1,
                }

                // Equipment spatial candidates from matched old room (by id)
                let room_id_for_eq = room.id.clone();
                let spatial_eq: Vec<(String, Position, EquipmentType)> = existing_rooms
                    .get(&format!("id:{}", room_id_for_eq))
                    .map(|r| {
                        r.equipment
                            .iter()
                            .map(|e| (e.id.clone(), e.position.clone(), e.equipment_type.clone()))
                            .collect()
                    })
                    .unwrap_or_default();

                for eq in &mut room.equipment {
                    let path = format!("{}/{}/{}", wing_path, room.name, eq.name);
                    match find_equipment(&existing_equipment, eq, &path, policy, &spatial_eq) {
                        Some((key, old_eq)) => {
                            stats.equipment_matched += 1;
                            matched_eq_keys.insert(key);
                            merge_equipment_fields(eq, old_eq, policy);
                            eq.room_id = Some(room.id.clone());
                        }
                        None => {
                            stats.equipment_added += 1;
                            eq.room_id = Some(room.id.clone());
                        }
                    }
                }
            }
        }
    }

    finish_orphan_stats(
        &mut stats,
        &mut warnings,
        existing_rooms.len(),
        matched_room_keys.len(),
        existing_equipment.len(),
        matched_eq_keys.len(),
        policy,
    );

    MergeResult {
        building,
        stats,
        warnings,
    }
}

// ---------------------------------------------------------------------------
// Existing base (LiDAR incremental)
// ---------------------------------------------------------------------------

fn merge_existing_base(
    existing: &Building,
    incoming: Building,
    policy: &MergePolicy,
) -> MergeResult {
    let mut stats = MergeStats::default();
    let warnings = Vec::new();
    let mut building = existing.clone();

    // Fold scan metadata into existing
    merge_building_metadata_from_incoming(&mut building, &incoming);
    if building.name.is_empty() {
        building.name = incoming.name.clone();
    }

    for incoming_floor in incoming.floors {
        let floor_idx = building
            .floors
            .iter()
            .position(|f| f.level == incoming_floor.level || f.name == incoming_floor.name);

        let floor_idx = match floor_idx {
            Some(i) => {
                stats.floors_matched += 1;
                if building.floors[i].elevation.is_none() {
                    building.floors[i].elevation = incoming_floor.elevation;
                }
                for (k, v) in &incoming_floor.properties {
                    building.floors[i]
                        .properties
                        .entry(k.clone())
                        .or_insert_with(|| v.clone());
                }
                i
            }
            None => {
                stats.floors_added += 1;
                building.add_floor(incoming_floor);
                continue;
            }
        };

        // Work on a clone of wings to avoid borrow issues, then write back
        let floor_name = building.floors[floor_idx].name.clone();
        let mut wings = building.floors[floor_idx].wings.clone();

        for incoming_wing in incoming_floor.wings {
            let wing_idx = wings.iter().position(|w| w.name == incoming_wing.name);
            let wing_idx = match wing_idx {
                Some(i) => i,
                None => {
                    wings.push(incoming_wing);
                    // count rooms/equipment as added
                    let w = wings.last().unwrap();
                    stats.rooms_added += w.rooms.len();
                    stats.equipment_added +=
                        w.rooms.iter().map(|r| r.equipment.len()).sum::<usize>()
                            + w.equipment.len();
                    continue;
                }
            };

            for mut incoming_room in incoming_wing.rooms {
                let room_path = format!("{}/{}", floor_name, incoming_room.name);
                let room_path_wing = format!(
                    "{}/{}/{}",
                    floor_name, wings[wing_idx].name, incoming_room.name
                );

                // Build temporary index of current wing rooms for matching
                let room_match = {
                    let rooms_ref: Vec<&Room> = wings[wing_idx].rooms.iter().collect();
                    find_room_in_list(
                        &rooms_ref,
                        &incoming_room,
                        &room_path,
                        &room_path_wing,
                        policy,
                    )
                };

                match room_match {
                    Some(ri) => {
                        stats.rooms_matched += 1;
                        let old_room = wings[wing_idx].rooms[ri].clone();
                        merge_room_fields(&mut incoming_room, &old_room, policy);
                        // Keep name from existing when spatial match used different names? Prefer incoming name for scan labels
                        // Preserve id from old (done in merge_room_fields)

                        // Merge equipment into the matched room
                        let mut merged_eq = old_room.equipment.clone();
                        for mut inc_eq in incoming_room.equipment.drain(..) {
                            let eq_path = format!(
                                "{}/{}/{}/{}",
                                floor_name, wings[wing_idx].name, old_room.name, inc_eq.name
                            );
                            let eq_match = find_equipment_in_list(
                                &merged_eq.iter().collect::<Vec<_>>(),
                                &inc_eq,
                                &eq_path,
                                policy,
                            );
                            match eq_match {
                                Some(ei) => {
                                    stats.equipment_matched += 1;
                                    let old_eq = merged_eq[ei].clone();
                                    merge_equipment_fields(&mut inc_eq, &old_eq, policy);
                                    inc_eq.room_id = Some(incoming_room.id.clone());
                                    merged_eq[ei] = inc_eq;
                                }
                                None => {
                                    stats.equipment_added += 1;
                                    inc_eq.room_id = Some(incoming_room.id.clone());
                                    merged_eq.push(inc_eq);
                                }
                            }
                        }
                        incoming_room.equipment = merged_eq;
                        wings[wing_idx].rooms[ri] = incoming_room;
                    }
                    None => {
                        stats.rooms_added += 1;
                        stats.equipment_added += incoming_room.equipment.len();
                        for eq in &mut incoming_room.equipment {
                            eq.room_id = Some(incoming_room.id.clone());
                        }
                        wings[wing_idx].rooms.push(incoming_room);
                    }
                }
            }

            // Wing-level equipment
            for mut inc_eq in incoming_wing.equipment {
                let eq_path = format!("{}/{}/{}", floor_name, wings[wing_idx].name, inc_eq.name);
                let eq_match = find_equipment_in_list(
                    &wings[wing_idx].equipment.iter().collect::<Vec<_>>(),
                    &inc_eq,
                    &eq_path,
                    policy,
                );
                match eq_match {
                    Some(ei) => {
                        stats.equipment_matched += 1;
                        let old_eq = wings[wing_idx].equipment[ei].clone();
                        merge_equipment_fields(&mut inc_eq, &old_eq, policy);
                        wings[wing_idx].equipment[ei] = inc_eq;
                    }
                    None => {
                        stats.equipment_added += 1;
                        wings[wing_idx].equipment.push(inc_eq);
                    }
                }
            }
        }

        // Floor-level equipment from incoming
        for mut inc_eq in incoming_floor.equipment {
            let eq_path = format!("{}/{}", floor_name, inc_eq.name);
            let eq_match = find_equipment_in_list(
                &building.floors[floor_idx]
                    .equipment
                    .iter()
                    .collect::<Vec<_>>(),
                &inc_eq,
                &eq_path,
                policy,
            );
            match eq_match {
                Some(ei) => {
                    stats.equipment_matched += 1;
                    let old_eq = building.floors[floor_idx].equipment[ei].clone();
                    merge_equipment_fields(&mut inc_eq, &old_eq, policy);
                    building.floors[floor_idx].equipment[ei] = inc_eq;
                }
                None => {
                    stats.equipment_added += 1;
                    building.floors[floor_idx].equipment.push(inc_eq);
                }
            }
        }

        building.floors[floor_idx].wings = wings;
    }

    // Existing base keeps unmatched existing; zero orphan counts
    stats.existing_rooms_not_in_incoming = 0;
    stats.existing_equipment_not_in_incoming = 0;

    MergeResult {
        building,
        stats,
        warnings,
    }
}

// ---------------------------------------------------------------------------
// Field merge
// ---------------------------------------------------------------------------

fn apply_floor_identity(floor: &mut Floor, old: &Floor) {
    if floor.ifc_global_id.is_none() {
        floor.ifc_global_id = old.ifc_global_id.clone();
    }
    floor.id = old.id.clone();
    if floor.elevation.is_none() {
        floor.elevation = old.elevation;
    }
    for (k, v) in &old.properties {
        floor
            .properties
            .entry(k.clone())
            .or_insert_with(|| v.clone());
    }
}

fn merge_building_metadata(building: &mut Building, existing: &Building) {
    if let Some(old_meta) = &existing.metadata {
        if let Some(new_meta) = &mut building.metadata {
            for tag in &old_meta.tags {
                if !new_meta.tags.contains(tag) {
                    new_meta.tags.push(tag.clone());
                }
            }
            for (k, v) in &old_meta.properties {
                new_meta
                    .properties
                    .entry(k.clone())
                    .or_insert_with(|| v.clone());
            }
            if new_meta.source_file.is_none() {
                new_meta.source_file = old_meta.source_file.clone();
            }
        } else {
            building.metadata = Some(old_meta.clone());
        }
    }
}

fn merge_building_metadata_from_incoming(building: &mut Building, incoming: &Building) {
    if let Some(inc_meta) = &incoming.metadata {
        if let Some(meta) = &mut building.metadata {
            for tag in &inc_meta.tags {
                if !meta.tags.contains(tag) {
                    meta.tags.push(tag.clone());
                }
            }
            for (k, v) in &inc_meta.properties {
                meta.properties.insert(k.clone(), v.clone());
            }
            meta.source_file = inc_meta.source_file.clone().or(meta.source_file.clone());
            meta.total_entities = inc_meta.total_entities;
            meta.spatial_entities = inc_meta.spatial_entities;
        } else {
            building.metadata = Some(inc_meta.clone());
        }
    }
}

fn merge_room_fields(room: &mut Room, old: &Room, _policy: &MergePolicy) {
    room.id = old.id.clone();
    room.created_at = old.created_at;
    // Geometry already on `room` (incoming). Enrichment: prefer incoming when Some.
    room.lidar_enrichment = prefer_existing_lidar(&old.lidar_enrichment, &room.lidar_enrichment);
    if room.ifc_global_id.is_none() {
        room.ifc_global_id = old.ifc_global_id.clone();
    }
    for (k, v) in &old.properties {
        room.properties
            .entry(k.clone())
            .or_insert_with(|| v.clone());
    }
}

fn merge_equipment_fields(eq: &mut Equipment, old: &Equipment, _policy: &MergePolicy) {
    eq.id = old.id.clone();
    eq.status = old.status;
    eq.health_status = old.health_status;
    if eq.sensor_mappings.is_none() {
        eq.sensor_mappings = old.sensor_mappings.clone();
    }
    eq.lidar_enrichment = prefer_existing_lidar(&old.lidar_enrichment, &eq.lidar_enrichment);
    if eq.ifc_global_id.is_none() {
        eq.ifc_global_id = old.ifc_global_id.clone();
    }
    // Incoming properties win on collision; fill gaps from existing
    let mut merged = old.properties.clone();
    for (k, v) in eq.properties.drain() {
        merged.insert(k, v);
    }
    eq.properties = merged;
}

fn finish_orphan_stats(
    stats: &mut MergeStats,
    warnings: &mut Vec<MappingWarning>,
    existing_rooms: usize,
    matched_rooms: usize,
    existing_eq: usize,
    matched_eq: usize,
    policy: &MergePolicy,
) {
    if policy.hierarchy != HierarchyBase::Incoming {
        return;
    }
    stats.existing_rooms_not_in_incoming = existing_rooms.saturating_sub(matched_rooms);
    stats.existing_equipment_not_in_incoming = existing_eq.saturating_sub(matched_eq);

    if stats.existing_rooms_not_in_incoming > 0 {
        warnings.push(MappingWarning::new(
            "merge_existing_rooms_omitted",
            format!(
                "{} room(s) present in existing model but not in incoming were not carried forward",
                stats.existing_rooms_not_in_incoming
            ),
        ));
    }
    if stats.existing_equipment_not_in_incoming > 0 {
        warnings.push(MappingWarning::new(
            "merge_existing_equipment_omitted",
            format!(
                "{} equipment present in existing model but not in incoming were not carried forward",
                stats.existing_equipment_not_in_incoming
            ),
        ));
    }
}

// ---------------------------------------------------------------------------
// Indexing & matching
// ---------------------------------------------------------------------------

fn ids_match(a: Option<&str>, b: Option<&str>) -> bool {
    matches!((a, b), (Some(x), Some(y)) if !x.is_empty() && x == y)
}

fn distance(p1: &Position, p2: &Position) -> f64 {
    ((p1.x - p2.x).powi(2) + (p1.y - p2.y).powi(2) + (p1.z - p2.z).powi(2)).sqrt()
}

type FloorIndex<'a> = Vec<&'a Floor>;
type RoomIndex<'a> = HashMap<String, &'a Room>;
type EquipmentIndex<'a> = HashMap<String, &'a Equipment>;

fn index_existing(existing: &Building) -> (FloorIndex<'_>, RoomIndex<'_>, EquipmentIndex<'_>) {
    let mut floors = Vec::new();
    let mut rooms = HashMap::new();
    let mut equipment = HashMap::new();

    for floor in &existing.floors {
        floors.push(floor);
        for eq in &floor.equipment {
            insert_equipment_keys(&mut equipment, eq, &format!("{}/{}", floor.name, eq.name));
        }
        for wing in &floor.wings {
            for eq in &wing.equipment {
                insert_equipment_keys(
                    &mut equipment,
                    eq,
                    &format!("{}/{}/{}", floor.name, wing.name, eq.name),
                );
            }
            for room in &wing.rooms {
                let path = format!("{}/{}", floor.name, room.name);
                let path_wing = format!("{}/{}/{}", floor.name, wing.name, room.name);
                insert_room_keys(&mut rooms, room, &path);
                insert_room_keys(&mut rooms, room, &path_wing);
                for eq in &room.equipment {
                    insert_equipment_keys(
                        &mut equipment,
                        eq,
                        &format!("{}/{}/{}/{}", floor.name, wing.name, room.name, eq.name),
                    );
                }
            }
        }
    }

    (floors, rooms, equipment)
}

fn insert_room_keys<'a>(index: &mut RoomIndex<'a>, room: &'a Room, path: &str) {
    if let Some(ref gid) = room.ifc_global_id {
        if !gid.is_empty() {
            index.entry(format!("gid:{}", gid)).or_insert(room);
        }
    }
    index.entry(format!("id:{}", room.id)).or_insert(room);
    index.entry(format!("path:{}", path)).or_insert(room);
}

fn insert_equipment_keys<'a>(index: &mut EquipmentIndex<'a>, eq: &'a Equipment, path: &str) {
    if let Some(ref gid) = eq.ifc_global_id {
        if !gid.is_empty() {
            index.entry(format!("gid:{}", gid)).or_insert(eq);
        }
    }
    index.entry(format!("id:{}", eq.id)).or_insert(eq);
    index.entry(format!("path:{}", path)).or_insert(eq);
}

fn find_floor<'a>(floors: &FloorIndex<'a>, floor: &Floor) -> Option<&'a Floor> {
    if let Some(ref gid) = floor.ifc_global_id {
        if !gid.is_empty() {
            if let Some(f) = floors
                .iter()
                .find(|f| f.ifc_global_id.as_deref() == Some(gid.as_str()))
            {
                return Some(*f);
            }
        }
    }
    if let Some(f) = floors.iter().find(|f| f.id == floor.id) {
        return Some(*f);
    }
    if let Some(f) = floors.iter().find(|f| f.level == floor.level) {
        return Some(*f);
    }
    floors.iter().find(|f| f.name == floor.name).copied()
}

fn find_room<'a>(
    index: &RoomIndex<'a>,
    room: &Room,
    path: &str,
    path_wing: &str,
    policy: &MergePolicy,
    spatial_candidates: &[(String, Position)],
) -> Option<(String, &'a Room)> {
    if let Some(ref gid) = room.ifc_global_id {
        let key = format!("gid:{}", gid);
        if let Some(r) = index.get(&key) {
            return Some((key, *r));
        }
    }
    let id_key = format!("id:{}", room.id);
    if let Some(r) = index.get(&id_key) {
        return Some((id_key, *r));
    }
    let p1 = format!("path:{}", path);
    if let Some(r) = index.get(&p1) {
        return Some((p1, *r));
    }
    let p2 = format!("path:{}", path_wing);
    if let Some(r) = index.get(&p2) {
        return Some((p2, *r));
    }

    // Spatial fallback (LiDAR) — candidates are (room_id, position)
    if let Some(radius) = policy.room_match_radius_m {
        let mut best: Option<(&str, f64)> = None;
        for (id, pos) in spatial_candidates {
            let d = distance(&room.spatial_properties.position, pos);
            if d < radius && best.map(|(_, bd)| d < bd).unwrap_or(true) {
                best = Some((id.as_str(), d));
            }
        }
        if let Some((id, _)) = best {
            let key = format!("id:{}", id);
            if let Some(r) = index.get(&key) {
                return Some((key, *r));
            }
        }
    }
    None
}

fn find_room_in_list(
    rooms: &[&Room],
    room: &Room,
    path: &str,
    path_wing: &str,
    policy: &MergePolicy,
) -> Option<usize> {
    if let Some(ref gid) = room.ifc_global_id {
        if let Some(i) = rooms
            .iter()
            .position(|r| r.ifc_global_id.as_deref() == Some(gid.as_str()))
        {
            return Some(i);
        }
    }
    if let Some(i) = rooms.iter().position(|r| r.id == room.id) {
        return Some(i);
    }
    if let Some(i) = rooms.iter().position(|r| r.name == room.name) {
        // path-ish match by name
        let _ = (path, path_wing);
        return Some(i);
    }
    if let Some(radius) = policy.room_match_radius_m {
        let mut best: Option<(usize, f64)> = None;
        for (i, r) in rooms.iter().enumerate() {
            let d = distance(
                &room.spatial_properties.position,
                &r.spatial_properties.position,
            );
            if d < radius && best.map(|(_, bd)| d < bd).unwrap_or(true) {
                best = Some((i, d));
            }
        }
        return best.map(|(i, _)| i);
    }
    None
}

fn find_equipment<'a>(
    index: &EquipmentIndex<'a>,
    eq: &Equipment,
    path: &str,
    policy: &MergePolicy,
    spatial_candidates: &[(String, Position, EquipmentType)],
) -> Option<(String, &'a Equipment)> {
    if let Some(ref gid) = eq.ifc_global_id {
        let key = format!("gid:{}", gid);
        if let Some(e) = index.get(&key) {
            return Some((key, *e));
        }
    }
    let id_key = format!("id:{}", eq.id);
    if let Some(e) = index.get(&id_key) {
        return Some((id_key, *e));
    }
    let p = format!("path:{}", path);
    if let Some(e) = index.get(&p) {
        return Some((p, *e));
    }

    if let Some(radius) = policy.equipment_match_radius_m {
        let mut best: Option<(&str, f64)> = None;
        for (id, pos, ty) in spatial_candidates {
            if !equipment_types_compatible(ty, &eq.equipment_type) {
                continue;
            }
            let d = distance(&eq.position, pos);
            if d < radius && best.map(|(_, bd)| d < bd).unwrap_or(true) {
                best = Some((id.as_str(), d));
            }
        }
        if let Some((id, _)) = best {
            let key = format!("id:{}", id);
            if let Some(e) = index.get(&key) {
                return Some((key, *e));
            }
        }
    }
    None
}

fn find_equipment_in_list(
    list: &[&Equipment],
    eq: &Equipment,
    path: &str,
    policy: &MergePolicy,
) -> Option<usize> {
    let _ = path;
    if let Some(ref gid) = eq.ifc_global_id {
        if let Some(i) = list
            .iter()
            .position(|e| e.ifc_global_id.as_deref() == Some(gid.as_str()))
        {
            return Some(i);
        }
    }
    if let Some(i) = list.iter().position(|e| e.id == eq.id) {
        return Some(i);
    }
    if let Some(i) = list.iter().position(|e| e.name == eq.name) {
        return Some(i);
    }
    if let Some(radius) = policy.equipment_match_radius_m {
        let mut best: Option<(usize, f64)> = None;
        for (i, e) in list.iter().enumerate() {
            if !equipment_types_compatible(&e.equipment_type, &eq.equipment_type) {
                continue;
            }
            let d = distance(&eq.position, &e.position);
            if d < radius && best.map(|(_, bd)| d < bd).unwrap_or(true) {
                best = Some((i, d));
            }
        }
        return best.map(|(i, _)| i);
    }
    None
}

fn equipment_types_compatible(a: &EquipmentType, b: &EquipmentType) -> bool {
    a == b
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::core::{
        EquipmentStatus, EquipmentType, Floor, LidarEnrichment, Position, Room, RoomType, Wing,
    };

    fn sample_building() -> Building {
        let mut b = Building::new("HQ".into(), "/hq".into());
        let mut floor = Floor::new("F1".into(), 1);
        let mut wing = Wing::new("Main".into());
        let mut room = Room::new("R1".into(), RoomType::Office);
        room.ifc_global_id = Some("RoomGid001".into());
        room.lidar_enrichment = Some(LidarEnrichment {
            point_count: 100,
            confidence_score: 0.9,
            last_scan_timestamp: None,
            classification_heuristic: Some("v1".into()),
        });
        room.properties
            .insert("custom_arx".into(), "keep-me".into());

        let mut eq = Equipment::new("eq1".into(), "".into(), EquipmentType::HVAC);
        eq.ifc_global_id = Some("EqGid001".into());
        eq.status = EquipmentStatus::Maintenance;
        eq.position = Position {
            x: 1.0,
            y: 2.0,
            z: 0.5,
            coordinate_system: "building_local".into(),
        };
        room.add_equipment(eq);
        wing.add_room(room);
        floor.add_wing(wing);
        b.add_floor(floor);
        b
    }

    #[test]
    fn merge_matches_by_global_id_preserves_arx_state() {
        let existing = sample_building();
        let old_room_id = existing.floors[0].wings[0].rooms[0].id.clone();
        let old_eq_id = existing.floors[0].wings[0].rooms[0].equipment[0].id.clone();

        let mut incoming = Building::new("HQ".into(), "/hq".into());
        let mut floor = Floor::new("F1".into(), 1);
        let mut wing = Wing::new("Main".into());
        let mut room = Room::new("R1-renamed".into(), RoomType::Office);
        room.ifc_global_id = Some("RoomGid001".into());
        room.lidar_enrichment = None;
        room.spatial_properties.position.x = 99.0;

        let mut eq = Equipment::new("eq1".into(), "".into(), EquipmentType::HVAC);
        eq.ifc_global_id = Some("EqGid001".into());
        eq.status = EquipmentStatus::Active;
        eq.position.x = 50.0;
        room.add_equipment(eq);
        wing.add_room(room);
        floor.add_wing(wing);
        incoming.add_floor(floor);

        let result = merge_building(&existing, incoming);
        assert_eq!(result.stats.rooms_matched, 1);
        assert_eq!(result.stats.equipment_matched, 1);

        let room = &result.building.floors[0].wings[0].rooms[0];
        assert_eq!(room.id, old_room_id);
        assert_eq!(room.name, "R1-renamed");
        assert!((room.spatial_properties.position.x - 99.0).abs() < 1e-9);
        assert_eq!(
            room.lidar_enrichment.as_ref().map(|e| e.point_count),
            Some(100),
        );
        assert_eq!(
            room.properties.get("custom_arx").map(String::as_str),
            Some("keep-me")
        );

        let eq = &room.equipment[0];
        assert_eq!(eq.id, old_eq_id);
        assert_eq!(eq.status, EquipmentStatus::Maintenance);
        assert!((eq.position.x - 50.0).abs() < 1e-9);
    }

    #[test]
    fn merge_path_fallback_when_no_global_id() {
        let mut existing = Building::new("HQ".into(), "/hq".into());
        let mut floor = Floor::new("F1".into(), 1);
        let mut wing = Wing::new("Main".into());
        let mut room = Room::new("Office".into(), RoomType::Office);
        room.properties.insert("note".into(), "old".into());
        wing.add_room(room);
        floor.add_wing(wing);
        existing.add_floor(floor);

        let mut incoming = Building::new("HQ".into(), "/hq".into());
        let mut floor = Floor::new("F1".into(), 1);
        let mut wing = Wing::new("Main".into());
        let room = Room::new("Office".into(), RoomType::Office);
        wing.add_room(room);
        floor.add_wing(wing);
        incoming.add_floor(floor);

        let result = merge_building(&existing, incoming);
        assert_eq!(result.stats.rooms_matched, 1);
        let room = &result.building.floors[0].wings[0].rooms[0];
        assert_eq!(room.properties.get("note").map(String::as_str), Some("old"));
    }

    #[test]
    fn lidar_merge_updates_enrichment_and_preserves_ids() {
        let mut existing = Building::new("Scan".into(), "/s".into());
        let mut floor = Floor::new("Floor 1".into(), 0);
        let mut wing = Wing::new("Main".into());
        let mut room = Room::new("Room 1".into(), RoomType::Office);
        room.spatial_properties.position = Position {
            x: 2.0,
            y: 2.0,
            z: 0.0,
            coordinate_system: "building_local".into(),
        };
        room.lidar_enrichment = Some(LidarEnrichment {
            point_count: 10,
            confidence_score: 0.5,
            last_scan_timestamp: None,
            classification_heuristic: Some("old".into()),
        });
        let room_id = room.id.clone();
        let mut eq = Equipment::new("HVAC Item 1".into(), "".into(), EquipmentType::HVAC);
        eq.position = Position {
            x: 2.2,
            y: 2.2,
            z: 0.5,
            coordinate_system: "building_local".into(),
        };
        let eq_id = eq.id.clone();
        room.add_equipment(eq);
        wing.add_room(room);
        floor.add_wing(wing);
        existing.add_floor(floor);

        let mut incoming = Building::new("Scan".into(), "/s".into());
        let mut floor = Floor::new("Floor 1".into(), 0);
        let mut wing = Wing::new("Main".into());
        let mut room = Room::new("Room 1".into(), RoomType::Office);
        room.spatial_properties.position = Position {
            x: 2.1,
            y: 2.1,
            z: 0.0,
            coordinate_system: "building_local".into(),
        };
        room.lidar_enrichment = Some(LidarEnrichment {
            point_count: 5000,
            confidence_score: 0.95,
            last_scan_timestamp: None,
            classification_heuristic: Some("new_scan".into()),
        });
        let mut eq = Equipment::new("HVAC Item 1".into(), "".into(), EquipmentType::HVAC);
        eq.position = Position {
            x: 2.25,
            y: 2.25,
            z: 0.5,
            coordinate_system: "building_local".into(),
        };
        eq.lidar_enrichment = Some(LidarEnrichment {
            point_count: 80,
            confidence_score: 0.8,
            last_scan_timestamp: None,
            classification_heuristic: Some("eq_scan".into()),
        });
        room.add_equipment(eq);
        wing.add_room(room);
        floor.add_wing(wing);
        incoming.add_floor(floor);

        let result = merge_building_with_policy(&existing, incoming, &MergePolicy::lidar());
        assert_eq!(result.stats.rooms_matched, 1);
        assert_eq!(result.stats.equipment_matched, 1);

        let r = &result.building.floors[0].wings[0].rooms[0];
        assert_eq!(r.id, room_id);
        assert_eq!(
            r.lidar_enrichment.as_ref().map(|e| e.point_count),
            Some(5000),
            "incoming scan enrichment must win"
        );
        assert!((r.spatial_properties.position.x - 2.1).abs() < 1e-9);
        let e = &r.equipment[0];
        assert_eq!(e.id, eq_id);
        assert_eq!(e.lidar_enrichment.as_ref().map(|e| e.point_count), Some(80));
        assert!((e.position.x - 2.25).abs() < 1e-9);
    }
}
