//! Inbox apply fuses a second Fact of the same EntityId into official S.

use std::collections::BTreeSet;

use arxos_core::capture::roomplan::{hall_four_walls, map_roomplan};
use arxos_core::entity::entity_id_of;
use arxos_core::object::ObjectType;
use arxos_core::repository::BuildingRepository;
use arxos_core::state::BuildingState;
use arxos_core::{inbox, Cid, Keypair};
use tempfile::tempdir;

#[test]
fn inbox_apply_fuses_second_walk() {
    let dir_a = tempdir().unwrap();
    let kp = Keypair::generate();
    let mut official = BuildingRepository::init(
        dir_a.path(),
        Some("Hall".into()),
        Some(Keypair::from_seed(*kp.seed())),
    )
    .unwrap();
    let bid = official.building_id().clone();

    let g1 = hall_four_walls([0.0, 0.0, 0.0], 40.0);
    let mut mapped = map_roomplan(&g1, 10).unwrap();
    mapped.set_sigma_mm(40.0);
    official.ingest_mapped_roomplan(mapped).unwrap();
    official.commit(Some("v1".into())).unwrap();
    let head_before = official.head_root();
    drop(official);

    // Contributor scratch: same Apple UUIDs, translated, tighter σ.
    let dir_b = tempdir().unwrap();
    let mut scratch = BuildingRepository::open_or_follow(dir_b.path(), &bid, Some("scratch".into()))
        .unwrap();
    let g2 = hall_four_walls([0.05, 0.0, 0.0], 20.0);
    let mut mapped2 = map_roomplan(&g2, 20).unwrap();
    mapped2.set_sigma_mm(20.0);
    let staged = scratch.ingest_mapped_roomplan(mapped2).unwrap();
    let wall_cids = staged.surfaces.clone();
    let mut payloads = Vec::new();
    for cid in &wall_cids {
        payloads.push((*cid, scratch.get_object_bytes(cid).unwrap()));
    }
    drop(scratch);

    // Simulate push: CAS ingest + inbox_add. Head must not move.
    let mut official = BuildingRepository::open(dir_a.path(), &bid).unwrap();
    official.set_keypair(Keypair::from_seed(*kp.seed()));
    assert_eq!(official.head_root(), head_before);
    for (cid, bytes) in &payloads {
        let stored = official.put_object_bytes(bytes).unwrap();
        assert_eq!(stored, *cid);
        official.inbox_add(*cid, "ed25519:contrib").unwrap();
    }
    assert_eq!(official.head_root(), head_before, "push must not move head");
    let listed = official.inbox_list().unwrap();
    assert_eq!(listed.pending.len(), 4);

    // Second add of same CID is idempotent.
    official.inbox_add(wall_cids[0], "ed25519:contrib").unwrap();
    assert_eq!(official.inbox_list().unwrap().pending.len(), 4);

    let apply = official.inbox_apply(None).unwrap();
    assert_ne!(Some(apply.commit.root_cid), head_before);
    assert!(official.inbox_list().unwrap().pending.is_empty());

    let head = official.head_root().unwrap();
    let root_obj = official.get_object(&head).unwrap();
    let root = arxos_core::root::RootBody::from_object(&root_obj).unwrap();
    let state = BuildingState::from_root(&official, root).unwrap();
    let walls: Vec<_> = state
        .facts()
        .filter(|(_, o)| o.header.object_type == ObjectType::Surface)
        .collect();
    assert_eq!(walls.len(), 4, "second apply must not stack walls");
    for (_, w) in &walls {
        assert_eq!(w.effective_support_count(), 2);
        let x = w.pose().unwrap().position[0];
        // Original x is 0 or 2 or 4; +0.05 at σ=20 vs σ=40 → pulled toward +0.05
        // Weights 1/1600 and 1/400; delta 0.05 → mean offset 0.04
        let _ = entity_id_of(w);
        let _ = x;
    }
    // South wall center was x=2.0; after fuse with 2.05 @ 20mm: 2.04
    let south = walls
        .iter()
        .find(|(id, _)| id.as_str().ends_with("000000000001"))
        .map(|(_, o)| o.pose().unwrap().position[0])
        .expect("south wall");
    assert!(
        (south - 2.04).abs() < 1e-6,
        "pose should move toward tighter σ, got {south}"
    );
}

#[test]
fn inbox_apply_without_controller_key_fails() {
    let dir = tempdir().unwrap();
    let mut repo = BuildingRepository::init(dir.path(), Some("X".into()), None).unwrap();
    let bid = repo.building_id().clone();
    let g = hall_four_walls([0.0, 0.0, 0.0], 40.0);
    let mapped = map_roomplan(&g, 1).unwrap();
    let staged = repo.ingest_mapped_roomplan(mapped).unwrap();
    let cid = staged.surfaces[0];
    let bytes = repo.get_object_bytes(&cid).unwrap();
    drop(repo);

    std::fs::remove_file(dir.path().join("keys").join("device.seed")).unwrap();
    let repo = BuildingRepository::open(dir.path(), &bid).unwrap();
    repo.put_object_bytes(&bytes).unwrap();
    // put_object_bytes requires write — open() has lock. Good.
    drop(repo);
    let mut repo = BuildingRepository::open(dir.path(), &bid).unwrap();
    repo.inbox_add(cid, "").unwrap();
    let err = repo.inbox_apply(None).unwrap_err();
    let s = err.to_string();
    assert!(
        s.contains("keypair") || s.contains("crypto") || s.contains("signing"),
        "{s}"
    );
}

#[test]
fn inbox_rejects_root_cid() {
    let dir = tempdir().unwrap();
    let mut repo = BuildingRepository::init(dir.path(), Some("R".into()), None).unwrap();
    let bid = repo.building_id().clone();
    repo.ingest_mapped_roomplan(map_roomplan(&hall_four_walls([0.0, 0.0, 0.0], 40.0), 1).unwrap())
        .unwrap();
    let commit = repo.commit(Some("root".into())).unwrap();
    let root_cid = commit.root_cid;
    let err = repo.inbox_add(root_cid, "").unwrap_err();
    assert!(
        err.to_string().to_lowercase().contains("root"),
        "{}",
        err
    );
    let _ = bid;
    let _ = Cid::from_canonical_bytes(b"x");
    let _ = BTreeSet::<Cid>::new();
    let _ = inbox::InboxAdd::Added;
}
