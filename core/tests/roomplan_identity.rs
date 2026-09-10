//! Two `map_roomplan` / `ingest_room_plan` calls with identical Apple UUIDs
//! share EntityId (`rp:` + lowercase uuid). FFI must not mint random ids.

use arxos_core::capture::roomplan::{
    entity_id_from_roomplan_uuid, identity_transform, map_roomplan, RoomPlanGeometry,
    RoomPlanSurface,
};
use arxos_core::entity::entity_id_of;
use arxos_core::repository::BuildingRepository;
use arxos_core::Keypair;
use tempfile::tempdir;

#[test]
fn two_ingests_same_uuid_same_entity_id() {
    let geom = RoomPlanGeometry {
        surfaces: vec![RoomPlanSurface {
            id: "11111111-2222-3333-4444-555555555555".into(),
            category: "wall".into(),
            transform: identity_transform(1.0, 1.25, 0.0),
            dimensions: vec![3.0, 2.5, 0.15],
        }],
        objects: vec![],
    };
    let a = map_roomplan(&geom, 10).unwrap();
    let b = map_roomplan(&geom, 20).unwrap();
    assert_eq!(entity_id_of(&a.surfaces[0]), entity_id_of(&b.surfaces[0]));
    assert_eq!(
        entity_id_of(&a.surfaces[0]).map(|e| e.as_str()),
        Some("rp:11111111-2222-3333-4444-555555555555")
    );
    assert_ne!(
        a.surfaces[0].cid().unwrap(),
        b.surfaces[0].cid().unwrap(),
        "second ingest must mint a new CID"
    );
}

#[test]
fn mixed_case_apple_uuid_lowercases_to_rp_prefix() {
    let id = entity_id_from_roomplan_uuid("AABBCCDD-EEff-0011-2233-445566778899").unwrap();
    assert_eq!(id.as_str(), "rp:aabbccdd-eeff-0011-2233-445566778899");
    let again = entity_id_from_roomplan_uuid("aabbccdd-eeff-0011-2233-445566778899").unwrap();
    assert_eq!(id, again);
}

#[test]
fn repository_ingest_same_uuid_same_entity_id() {
    let dir = tempdir().unwrap();
    let kp = Keypair::generate();
    let mut repo = BuildingRepository::init(
        dir.path(),
        Some("Hall".into()),
        Some(Keypair::from_seed(*kp.seed())),
    )
    .unwrap();

    let uuid = "AAAAAAAA-BBBB-CCCC-DDDD-EEEEEEEEEEEE";
    let geom = RoomPlanGeometry {
        surfaces: vec![RoomPlanSurface {
            id: uuid.into(),
            category: "wall".into(),
            transform: identity_transform(0.0, 1.25, 0.0),
            dimensions: vec![4.0, 2.5, 0.15],
        }],
        objects: vec![],
    };
    let a = repo.ingest_room_plan(&geom).unwrap();
    let b = repo.ingest_room_plan(&geom).unwrap();
    let wall_a = repo.get_object(&a.surfaces[0]).unwrap();
    let wall_b = repo.get_object(&b.surfaces[0]).unwrap();
    assert_eq!(entity_id_of(&wall_a), entity_id_of(&wall_b));
    assert_eq!(
        entity_id_of(&wall_a).map(|e| e.as_str()),
        Some("rp:aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee")
    );
    // Same-second ingest of an identical body may share a CID; EntityId is the
    // identity contract. Distinct `created` stamps (map_roomplan) mint a new CID.
}
