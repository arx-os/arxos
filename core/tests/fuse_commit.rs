//! Repository-level: second walk updates the wall instead of stacking walls.

use arxos_core::capture::roomplan::{
    identity_transform, map_roomplan, RoomPlanGeometry, RoomPlanSurface,
};
use arxos_core::entity::entity_id_of;
use arxos_core::object::{ObjectBody, ObjectType};
use arxos_core::repository::BuildingRepository;
use arxos_core::state::BuildingState;
use arxos_core::Keypair;
use tempfile::tempdir;

#[test]
fn second_commit_fuses_same_entity() {
    let dir = tempdir().unwrap();
    let kp = Keypair::generate();
    let mut repo = BuildingRepository::init(
        dir.path(),
        Some("Hall".into()),
        Some(Keypair::from_seed(*kp.seed())),
    )
    .unwrap();

    let wall_id = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee";
    let geom_a = RoomPlanGeometry {
        surfaces: vec![RoomPlanSurface {
            id: wall_id.into(),
            category: "wall".into(),
            transform: identity_transform(0.0, 1.25, 0.0),
            dimensions: vec![4.0, 2.5, 0.15],
        }],
        objects: vec![],
    };
    repo.ingest_room_plan(&geom_a).unwrap();
    repo.commit(Some("A".into())).unwrap();

    let geom_b = RoomPlanGeometry {
        surfaces: vec![RoomPlanSurface {
            id: wall_id.into(),
            category: "wall".into(),
            transform: identity_transform(0.05, 1.25, 0.0),
            dimensions: vec![4.0, 2.5, 0.15],
        }],
        objects: vec![],
    };
    let mut mapped = map_roomplan(&geom_b, 99).unwrap();
    if let ObjectBody::Surface(ref mut s) = mapped.surfaces[0].body {
        s.sigma_mm = Some(20.0);
        s.support_count = 1;
    }
    repo.stage_captured_object(mapped.surfaces.remove(0)).unwrap();
    repo.commit(Some("A'".into())).unwrap();

    let head = repo.head_root().unwrap();
    let root_obj = repo.get_object(&head).unwrap();
    let root = arxos_core::root::RootBody::from_object(&root_obj).unwrap();
    let state = BuildingState::from_root(&repo, root).unwrap();
    let walls: Vec<_> = state
        .facts()
        .filter(|(_, o)| o.header.object_type == ObjectType::Surface)
        .collect();
    assert_eq!(walls.len(), 1, "second walk must not stack walls");
    let wall = walls[0].1;
    assert_eq!(
        entity_id_of(wall).map(|e| e.as_str()),
        Some("rp:aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee")
    );
    assert_eq!(wall.effective_support_count(), 2);
    let x = wall.pose().unwrap().position[0];
    // Weights 1/1600 and 1/400 → mean = 0.04
    assert!(
        (x - 0.04).abs() < 1e-6,
        "pose should move toward the tighter σ observation, got {x}"
    );
}
