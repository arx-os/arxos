//! Serve-owned apply: control socket while the flock is held.
#![cfg(unix)]

use arxos_core::capture::roomplan::{hall_four_walls, map_roomplan};
use arxos_core::ctl::{ctl_send, spawn_serve_ctl, wake_ctl, CtlRequest};
use arxos_core::object::ObjectType;
use arxos_core::repository::BuildingRepository;
use arxos_core::state::BuildingState;
use arxos_core::store::ObjectStore;
use arxos_core::{inbox, Keypair};
use std::os::unix::fs::PermissionsExt;
use tempfile::tempdir;

#[test]
fn ctl_apply_while_flock_held() {
    let dir = tempdir().unwrap();
    let kp = Keypair::generate();
    let mut repo = BuildingRepository::init(
        dir.path(),
        Some("Hall".into()),
        Some(Keypair::from_seed(*kp.seed())),
    )
    .unwrap();
    let bid = repo.building_id().clone();
    let mut mapped = map_roomplan(&hall_four_walls([0.0, 0.0, 0.0], 40.0), 10).unwrap();
    mapped.set_sigma_mm(40.0);
    repo.ingest_mapped_roomplan(mapped).unwrap();
    repo.commit(Some("v1".into())).unwrap();
    let head_before = repo.head_root();
    drop(repo);

    // Contributor facts in a scratch store, then copy bytes into official CAS.
    let dir_b = tempdir().unwrap();
    let mut scratch =
        BuildingRepository::open_or_follow(dir_b.path(), &bid, Some("scratch".into())).unwrap();
    let mut mapped2 = map_roomplan(&hall_four_walls([0.05, 0.0, 0.0], 20.0), 20).unwrap();
    mapped2.set_sigma_mm(20.0);
    let staged = scratch.ingest_mapped_roomplan(mapped2).unwrap();
    let payloads: Vec<_> = staged
        .surfaces
        .iter()
        .map(|c| (*c, scratch.get_object_bytes(c).unwrap()))
        .collect();
    drop(scratch);

    // Serve-like: hold flock, bind sock. Second open must fail.
    let store = ObjectStore::open(dir.path()).unwrap();
    let _lock = store.try_lock_exclusive().unwrap();
    assert!(
        BuildingRepository::open(dir.path(), &bid).is_err(),
        "second open must fail while serve holds flock"
    );

    let path = arxos_core::serve_sock_path(dir.path());
    let (guard, stop, handle) = spawn_serve_ctl(dir.path()).unwrap();
    let meta = std::fs::metadata(&path).unwrap();
    assert_eq!(meta.permissions().mode() & 0o777, 0o600);

    for (cid, bytes) in &payloads {
        store.put_bytes(bytes).unwrap();
        inbox::inbox_add(dir.path(), &bid, cid, "ed25519:contrib").unwrap();
    }

    let reply = ctl_send(
        dir.path(),
        &CtlRequest {
            op: "inbox_apply".into(),
            building_id: Some(bid.to_string()),
            cids: None,
        },
    )
    .unwrap();
    assert!(reply.ok, "{:?}", reply.error);
    assert!(reply.root_cid.is_some());
    assert_ne!(reply.root_cid.as_deref(), head_before.map(|c| c.to_string()).as_deref());

    // Still holding flock.
    assert!(BuildingRepository::open(dir.path(), &bid).is_err());

    let read = BuildingRepository::open_read(dir.path(), &bid).unwrap();
    let head = read.head_root().unwrap();
    let root_obj = read.get_object(&head).unwrap();
    let root = arxos_core::root::RootBody::from_object(&root_obj).unwrap();
    let state = BuildingState::from_root(&read, root).unwrap();
    let walls: Vec<_> = state
        .facts()
        .filter(|(_, o)| o.header.object_type == ObjectType::Surface)
        .collect();
    assert_eq!(walls.len(), 4);
    assert!(walls.iter().all(|(_, w)| w.effective_support_count() == 2));
    drop(read);

    stop.store(true, std::sync::atomic::Ordering::Relaxed);
    wake_ctl(dir.path());
    let _ = handle.join();
    drop(guard);
    drop(_lock);
}

#[test]
fn ctl_apply_without_serve_is_local_path() {
    // Serve down: in-process apply still works (covered by inbox_apply tests).
    // This asserts sock is absent so CLI would take the local path.
    let dir = tempdir().unwrap();
    let _repo = BuildingRepository::init(dir.path(), Some("X".into()), None).unwrap();
    assert!(!arxos_core::serve_ctl_path_exists(dir.path()));
}
