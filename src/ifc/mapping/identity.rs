//! Product GlobalId ↔ Arx UUID identity helpers.

use std::collections::HashMap;

use uuid::Uuid;

use crate::core::{Building, Equipment, Floor, Room};

use super::{pset_prop_key, PSET_ARX_IDENTITY, PROP_ARX_ID};

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

/// Resolve the product GlobalId to write for an entity.
///
/// Prefers a stored `ifc_global_id`; otherwise derives from Arx UUID when
/// parseable; otherwise mints a new UUID-based GlobalId.
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

/// Assign `ifc_global_id` on all product entities that lack one.
///
/// Call before IFC export so the written GlobalIds match values persisted on
/// the model (and subsequent exports stay stable).
pub fn assign_missing_global_ids(building: &mut Building) {
    if building.ifc_global_id.is_none() {
        building.ifc_global_id = Some(resolve_product_global_id(&None, &building.id));
    }

    for floor in &mut building.floors {
        assign_floor_ids(floor);
    }
}

fn assign_floor_ids(floor: &mut Floor) {
    if floor.ifc_global_id.is_none() {
        floor.ifc_global_id = Some(resolve_product_global_id(&None, &floor.id));
    }
    for eq in &mut floor.equipment {
        assign_equipment_ids(eq);
    }
    for wing in &mut floor.wings {
        for eq in &mut wing.equipment {
            assign_equipment_ids(eq);
        }
        for room in &mut wing.rooms {
            assign_room_ids(room);
        }
    }
}

fn assign_room_ids(room: &mut Room) {
    if room.ifc_global_id.is_none() {
        room.ifc_global_id = Some(resolve_product_global_id(&None, &room.id));
    }
    for eq in &mut room.equipment {
        assign_equipment_ids(eq);
    }
}

fn assign_equipment_ids(eq: &mut Equipment) {
    if eq.ifc_global_id.is_none() {
        eq.ifc_global_id = Some(resolve_product_global_id(&None, &eq.id));
    }
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
