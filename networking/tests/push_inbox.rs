//! Push Facts into a peer inbox without moving head_root.

use arxos_core::capture::roomplan::{hall_four_walls, map_roomplan};
use arxos_core::object::ObjectType;
use arxos_core::repository::BuildingRepository;
use arxos_core::state::BuildingState;
use arxos_core::Keypair;
use arxos_networking::memory::MemoryMesh;
use arxos_networking::sync::{building_ads_from_store, push_facts};
use arxos_networking::ObjectTransport;
use tempfile::tempdir;

#[tokio::test]
async fn push_does_not_move_head_apply_fuses() {
    let mesh = MemoryMesh::new();
    let dir_a = tempdir().unwrap();
    let dir_b = tempdir().unwrap();
    let kp = Keypair::generate();

    let mut official = BuildingRepository::init(
        dir_a.path(),
        Some("Hall".into()),
        Some(Keypair::from_seed(*kp.seed())),
    )
    .unwrap();
    let bid = official.building_id().clone();
    let g1 = hall_four_walls([0.0, 0.0, 0.0], 40.0);
    let mut m1 = map_roomplan(&g1, 10).unwrap();
    m1.set_sigma_mm(40.0);
    official.ingest_mapped_roomplan(m1).unwrap();
    official.commit(Some("v1".into())).unwrap();
    let head_before = official.head_root();
    drop(official);

    let mut scratch = BuildingRepository::open_or_follow(dir_b.path(), &bid, Some("scratch".into()))
        .unwrap();
    let g2 = hall_four_walls([0.05, 0.0, 0.0], 20.0);
    let mut m2 = map_roomplan(&g2, 20).unwrap();
    m2.set_sigma_mm(20.0);
    let staged = scratch.ingest_mapped_roomplan(m2).unwrap();
    let mut objects = Vec::new();
    let mut leaves = Vec::new();
    for cid in &staged.surfaces {
        objects.push((cid.to_string(), scratch.get_object_bytes(cid).unwrap()));
        leaves.push(cid.to_string());
    }
    drop(scratch);

    let ads = building_ads_from_store(dir_a.path()).unwrap();
    let node_a = mesh.attach(dir_a.path(), ads).unwrap();
    let node_b = mesh.attach(dir_b.path(), vec![]).unwrap();

    let pushed = push_facts(
        &node_b,
        node_a.peer_id(),
        bid.as_str(),
        &objects,
        &leaves,
        "ed25519:contrib",
    )
    .await
    .unwrap();
    assert_eq!(pushed.accepted.len(), 4);
    assert!(pushed.rejected.is_empty());

    let official = BuildingRepository::open_read(dir_a.path(), &bid).unwrap();
    assert_eq!(official.head_root(), head_before, "push must not adopt");
    assert_eq!(official.inbox_list().unwrap().pending.len(), 4);
    drop(official);

    let mut official = BuildingRepository::open(dir_a.path(), &bid).unwrap();
    official.set_keypair(Keypair::from_seed(*kp.seed()));
    official.inbox_apply(None).unwrap();
    let head = official.head_root().unwrap();
    let root_obj = official.get_object(&head).unwrap();
    let root = arxos_core::root::RootBody::from_object(&root_obj).unwrap();
    let state = BuildingState::from_root(&official, root).unwrap();
    let walls: Vec<_> = state
        .facts()
        .filter(|(_, o)| o.header.object_type == ObjectType::Surface)
        .collect();
    assert_eq!(walls.len(), 4);
    assert!(walls.iter().all(|(_, w)| w.effective_support_count() == 2));
}

#[tokio::test]
async fn put_object_cid_mismatch_rejected() {
    let mesh = MemoryMesh::new();
    let dir = tempdir().unwrap();
    let repo = BuildingRepository::init(dir.path(), Some("X".into()), None).unwrap();
    let bid = repo.building_id().clone();
    drop(repo);
    let node = mesh.attach(dir.path(), vec![]).unwrap();
    let peer = node.peer_id().to_string();
    let resp = node
        .put_object(&peer, "b3:0000000000000000000000000000000000000000000000000000000000000000", &[1, 2, 3])
        .await
        .unwrap();
    match resp {
        arxos_networking::Message::PutObjectReject { .. } => {}
        other => panic!("expected reject, got {other:?}"),
    }
    let _ = bid;
}

#[tokio::test]
async fn push_root_rejected() {
    let mesh = MemoryMesh::new();
    let dir = tempdir().unwrap();
    let mut repo = BuildingRepository::init(dir.path(), Some("X".into()), None).unwrap();
    let bid = repo.building_id().clone();
    repo.ingest_mapped_roomplan(map_roomplan(&hall_four_walls([0.0, 0.0, 0.0], 40.0), 1).unwrap())
        .unwrap();
    let commit = repo.commit(Some("r".into())).unwrap();
    let root_cid = commit.root_cid;
    let bytes = repo.get_object_bytes(&root_cid).unwrap();
    drop(repo);

    let ads = building_ads_from_store(dir.path()).unwrap();
    let node = mesh.attach(dir.path(), ads).unwrap();
    let peer = node.peer_id().to_string();
    let put = node
        .put_object(&peer, &root_cid.to_string(), &bytes)
        .await
        .unwrap();
    assert!(matches!(put, arxos_networking::Message::PutObjectOk { .. }));
    let pushed = push_facts(
        &node,
        &peer,
        bid.as_str(),
        &[],
        &[root_cid.to_string()],
        "",
    )
    .await
    .unwrap();
    assert_eq!(pushed.accepted.len(), 0);
    assert_eq!(pushed.rejected.len(), 1);
    assert!(
        pushed.rejected[0].reason.to_lowercase().contains("root"),
        "{}",
        pushed.rejected[0].reason
    );
}
