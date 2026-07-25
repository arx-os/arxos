//! Product GlobalId ↔ Arx UUID identity helpers.

use std::collections::HashMap;

use uuid::Uuid;

use crate::core::{Building, Equipment, Floor, Room};

use super::{pset_prop_key, PROP_ARX_ID, PSET_ARX_IDENTITY};

/// IFC compressed-GUID alphabet (22-char GlobalId).
const IFC_GUID_CHARS: &[u8; 64] =
    b"0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz_$";

/// Encode a UUID as a 22-character IFC GlobalId.
pub fn ifc_global_id_from_uuid(uuid: &Uuid) -> String {
    let bytes = uuid.as_bytes();
    let mut result = String::with_capacity(22);

    let to_b64 = |b1: u8, b2: u8, b3: u8, len: usize| -> String {
        let mut num = ((b1 as u32) << 16) + ((b2 as u32) << 8) + (b3 as u32);
        let mut s = String::new();
        for _ in 0..len {
            s.insert(0, IFC_GUID_CHARS[(num % 64) as usize] as char);
            num /= 64;
        }
        s
    };

    result.push_str(&to_b64(bytes[0], bytes[1], bytes[2], 4));
    result.push_str(&to_b64(bytes[3], bytes[4], bytes[5], 4));
    result.push_str(&to_b64(bytes[6], bytes[7], bytes[8], 4));
    result.push_str(&to_b64(bytes[9], bytes[10], bytes[11], 4));
    result.push_str(&to_b64(bytes[12], bytes[13], bytes[14], 4));

    let mut num = bytes[15] as u32;
    let mut s = String::new();
    for _ in 0..2 {
        s.insert(0, IFC_GUID_CHARS[(num % 64) as usize] as char);
        num /= 64;
    }
    result.push_str(&s);
    result
}

/// Parse an Arx id string as a UUID when possible.
pub fn uuid_from_arx_id(arx_id: &str) -> Option<Uuid> {
    Uuid::parse_str(arx_id).ok()
}

/// True when `ifc_global_id` is present and non-empty (IFC-origin / already assigned).
pub fn has_ifc_global_id(ifc_global_id: &Option<String>) -> bool {
    ifc_global_id
        .as_ref()
        .map(|g| !g.trim().is_empty())
        .unwrap_or(false)
}

/// Resolve the product GlobalId to write for an entity.
///
/// Prefers a stored non-empty `ifc_global_id`; otherwise derives from Arx UUID when
/// parseable (deterministic for Arxos-native entities that use UUID ids);
/// otherwise mints a new UUID-based GlobalId.
pub fn resolve_product_global_id(ifc_global_id: &Option<String>, arx_id: &str) -> String {
    if let Some(g) = ifc_global_id {
        let trimmed = g.trim();
        if !trimmed.is_empty() {
            return trimmed.to_string();
        }
    }
    if let Some(uuid) = uuid_from_arx_id(arx_id) {
        return ifc_global_id_from_uuid(&uuid);
    }
    ifc_global_id_from_uuid(&Uuid::new_v4())
}

/// Stats from [`assign_missing_global_ids`] (export identity bookkeeping).
#[derive(Debug, Clone, Default, PartialEq, Eq)]
pub struct GlobalIdAssignStats {
    /// Entities that already had a non-empty `ifc_global_id` (preserved).
    pub preserved: usize,
    /// Entities that received a newly assigned GlobalId (Arxos-native → first export).
    pub assigned: usize,
}

impl GlobalIdAssignStats {
    pub fn summary_lines(&self) -> Vec<String> {
        vec![
            format!(
                "Identity: {} GlobalId(s) preserved (IFC-origin / prior export)",
                self.preserved
            ),
            format!(
                "Identity: {} new GlobalId(s) assigned (Arxos-native)",
                self.assigned
            ),
        ]
    }
}

/// Assign `ifc_global_id` on all product entities that lack one.
///
/// Call before IFC export so the written GlobalIds match values persisted on
/// the model (and subsequent exports stay stable). Returns counts of preserved
/// vs newly assigned IDs.
pub fn assign_missing_global_ids(building: &mut Building) -> GlobalIdAssignStats {
    let mut stats = GlobalIdAssignStats::default();
    assign_slot(&mut building.ifc_global_id, &building.id, &mut stats);

    for floor in &mut building.floors {
        assign_floor_ids(floor, &mut stats);
    }
    stats
}

fn assign_slot(slot: &mut Option<String>, arx_id: &str, stats: &mut GlobalIdAssignStats) {
    if has_ifc_global_id(slot) {
        stats.preserved += 1;
        return;
    }
    *slot = Some(resolve_product_global_id(&None, arx_id));
    stats.assigned += 1;
}

fn assign_floor_ids(floor: &mut Floor, stats: &mut GlobalIdAssignStats) {
    assign_slot(&mut floor.ifc_global_id, &floor.id, stats);
    for eq in &mut floor.equipment {
        assign_equipment_ids(eq, stats);
    }
    for wing in &mut floor.wings {
        for eq in &mut wing.equipment {
            assign_equipment_ids(eq, stats);
        }
        for room in &mut wing.rooms {
            assign_room_ids(room, stats);
        }
    }
}

fn assign_room_ids(room: &mut Room, stats: &mut GlobalIdAssignStats) {
    assign_slot(&mut room.ifc_global_id, &room.id, stats);
    for eq in &mut room.equipment {
        assign_equipment_ids(eq, stats);
    }
}

fn assign_equipment_ids(eq: &mut Equipment, stats: &mut GlobalIdAssignStats) {
    assign_slot(&mut eq.ifc_global_id, &eq.id, stats);
}

/// Apply IFC product GlobalId and optional `Pset_ArxIdentity` onto domain fields.
///
/// - Sets `ifc_global_id` from the IFC GlobalId when present.
/// - Overwrites Arx `id` when `Pset_ArxIdentity:ArxId` is present.
pub fn apply_identity_on_import(
    arx_id: &mut String,
    ifc_global_id: &mut Option<String>,
    global_id_from_ifc: Option<String>,
    properties: &HashMap<String, String>,
) {
    if let Some(gid) = global_id_from_ifc {
        let trimmed = gid.trim().to_string();
        if !trimmed.is_empty() {
            *ifc_global_id = Some(trimmed);
        }
    }

    let key = pset_prop_key(PSET_ARX_IDENTITY, PROP_ARX_ID);
    if let Some(id) = properties.get(&key) {
        let trimmed = id.trim();
        if !trimmed.is_empty() {
            *arx_id = trimmed.to_string();
        }
    }
}

/// Build the property map for `Pset_ArxIdentity`.
pub fn identity_property_map(arx_id: &str, kind: &str) -> HashMap<String, String> {
    let mut map = HashMap::new();
    map.insert(PROP_ARX_ID.to_string(), arx_id.to_string());
    map.insert(super::PROP_ENTITY_KIND.to_string(), kind.to_string());
    map
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn global_id_is_22_chars() {
        let uuid = Uuid::parse_str("550e8400-e29b-41d4-a716-446655440000").unwrap();
        let gid = ifc_global_id_from_uuid(&uuid);
        assert_eq!(gid.len(), 22);
        assert!(gid.chars().all(|c| IFC_GUID_CHARS.contains(&(c as u8))));
    }

    #[test]
    fn global_id_is_deterministic() {
        let uuid = Uuid::parse_str("550e8400-e29b-41d4-a716-446655440000").unwrap();
        assert_eq!(
            ifc_global_id_from_uuid(&uuid),
            ifc_global_id_from_uuid(&uuid)
        );
    }

    #[test]
    fn resolve_prefers_stored_global_id() {
        let stored = Some("0123456789012345678901".to_string());
        assert_eq!(
            resolve_product_global_id(&stored, "not-a-uuid"),
            "0123456789012345678901"
        );
    }

    #[test]
    fn resolve_derives_from_arx_uuid() {
        let arx = "550e8400-e29b-41d4-a716-446655440000";
        let expected = ifc_global_id_from_uuid(&Uuid::parse_str(arx).unwrap());
        assert_eq!(resolve_product_global_id(&None, arx), expected);
    }

    #[test]
    fn assign_missing_preserves_and_assigns() {
        use crate::core::{Building, Equipment, EquipmentType, Floor, Room, RoomType, Wing};

        let mut b = Building::new("HQ".into(), "/hq".into());
        b.ifc_global_id = Some("StoredBuildingGid000001".into());
        let mut floor = Floor::new("F1".into(), 1);
        floor.ifc_global_id = Some("StoredFloorGid000000001".into());
        let mut wing = Wing::new("Main".into());
        let mut room = Room::new("R1".into(), RoomType::Office);
        room.ifc_global_id = Some("StoredRoomGid0000000001".into());
        let mut native =
            Equipment::new("Outlet".into(), String::new(), EquipmentType::Electrical);
        // Arxos-native: no GlobalId
        native.ifc_global_id = None;
        let mut imported =
            Equipment::new("Imported".into(), String::new(), EquipmentType::Electrical);
        imported.ifc_global_id = Some("StoredEquipGid000000001".into());
        room.add_equipment(native);
        room.add_equipment(imported);
        wing.add_room(room);
        floor.add_wing(wing);
        b.add_floor(floor);

        let stats = assign_missing_global_ids(&mut b);
        assert_eq!(stats.preserved, 4); // building, floor, room, imported equip
        assert_eq!(stats.assigned, 1); // native outlet

        let eqs = b.get_all_equipment();
        let native_eq = eqs.iter().find(|e| e.name == "Outlet").unwrap();
        let imported_eq = eqs.iter().find(|e| e.name == "Imported").unwrap();
        assert!(has_ifc_global_id(&native_eq.ifc_global_id));
        let expected = resolve_product_global_id(&None, &native_eq.id);
        assert_eq!(native_eq.ifc_global_id.as_deref(), Some(expected.as_str()));
        assert_eq!(
            imported_eq.ifc_global_id.as_deref(),
            Some("StoredEquipGid000000001")
        );

        // Second assign: all preserved, no churn
        let g1 = native_eq.ifc_global_id.clone();
        let stats2 = assign_missing_global_ids(&mut b);
        assert_eq!(stats2.assigned, 0);
        assert_eq!(stats2.preserved, 5);
        let g2 = b
            .get_all_equipment()
            .into_iter()
            .find(|e| e.name == "Outlet")
            .unwrap()
            .ifc_global_id
            .clone();
        assert_eq!(g1, g2);
    }

    #[test]
    fn empty_global_id_treated_as_missing() {
        assert!(!has_ifc_global_id(&None));
        assert!(!has_ifc_global_id(&Some("".into())));
        assert!(!has_ifc_global_id(&Some("   ".into())));
        assert!(has_ifc_global_id(&Some("0123456789012345678901".into())));
    }

    #[test]
    fn apply_identity_restores_arx_id_and_global_id() {
        let mut arx_id = "generated".to_string();
        let mut ifc_gid = None;
        let mut props = HashMap::new();
        props.insert(
            pset_prop_key(PSET_ARX_IDENTITY, PROP_ARX_ID),
            "550e8400-e29b-41d4-a716-446655440000".to_string(),
        );
        apply_identity_on_import(
            &mut arx_id,
            &mut ifc_gid,
            Some("AbCdEfGhIjKlMnOpQrStUv".to_string()),
            &props,
        );
        assert_eq!(arx_id, "550e8400-e29b-41d4-a716-446655440000");
        assert_eq!(ifc_gid.as_deref(), Some("AbCdEfGhIjKlMnOpQrStUv"));
    }
}
