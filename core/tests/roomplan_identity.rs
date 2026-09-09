//! Two `map_roomplan` calls with identical UUIDs share EntityId.

use arxos_core::capture::roomplan::{
    identity_transform, map_roomplan, RoomPlanGeometry, RoomPlanSurface,
};
use arxos_core::entity::entity_id_of;

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
    assert_ne!(
        a.surfaces[0].cid().unwrap(),
        b.surfaces[0].cid().unwrap(),
        "second ingest must mint a new CID"
    );
}
