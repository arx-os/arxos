use super::*;
use crate::capture::{AnnotationCapture, PointCloudCapture, SpaceCapture};
use crate::entity::{entity_id_of, EntityId};
use crate::object::{BuildingId, Object, ObjectBody, Pose};
use crate::root::{RootBody, RootBuilder};
use crate::Error;
use std::collections::BTreeMap;
use std::str::FromStr;
use tempfile::tempdir;

#[test]
fn entity_replace_on_commit_drops_old_version() {
    let dir = tempdir().unwrap();
    let path = dir.path();
    let mut repo = BuildingRepository::init(path, Some("E".into()), None).unwrap();
    let eid = EntityId::from("01ENTITYREPLACE0000000000".to_string());

    let r1 = repo
        .capture_space(&SpaceCapture {
            entity_id: Some(eid.clone()),
            name: Some("v1".into()),
            pose: Pose {
                position: [0.0, 0.0, 0.0],
                orientation: [0.0, 0.0, 0.0, 1.0],
            },
            bounds: None,
            floor: None,
            properties: BTreeMap::new(),
        })
        .unwrap();
    repo.commit(Some("add v1".into())).unwrap();
    assert!(repo.active_objects.contains(&r1.cid));

    let r2 = repo
        .capture_space(&SpaceCapture {
            entity_id: Some(eid.clone()),
            name: Some("v2".into()),
            pose: Pose {
                position: [1.0, 0.0, 0.0],
                orientation: [0.0, 0.0, 0.0, 1.0],
            },
            bounds: None,
            floor: None,
            properties: BTreeMap::new(),
        })
        .unwrap();
    let commit = repo.commit(Some("replace v1".into())).unwrap();
    assert!(repo.active_objects.contains(&r2.cid));
    assert!(!repo.active_objects.contains(&r1.cid));

    // Root delta records the removal.
    let head = repo.load_head_root().unwrap().unwrap();
    if head.objects.is_none() {
        assert!(head.removed.contains(&r1.cid));
        assert!(head.added.contains(&r2.cid));
    }
    let _ = commit;
    // Entity id preserved on the new head object.
    let obj = repo.get_object(&r2.cid).unwrap();
    assert_eq!(entity_id_of(&obj).map(|e| e.as_str()), Some(eid.as_str()));
}

#[test]
fn entity_remove_without_replace() {
    let dir = tempdir().unwrap();
    let path = dir.path();
    let mut repo = BuildingRepository::init(path, Some("R".into()), None).unwrap();
    let eid = EntityId::from("01ENTITYREMOVE00000000000".to_string());
    let r = repo
        .capture_space(&SpaceCapture {
            entity_id: Some(eid.clone()),
            name: Some("gone".into()),
            pose: Pose::default(),
            bounds: None,
            floor: None,
            properties: BTreeMap::new(),
        })
        .unwrap();
    repo.commit(Some("add".into())).unwrap();
    let n = repo.remove_entity(&eid).unwrap();
    assert_eq!(n, 1);
    repo.commit(Some("remove".into())).unwrap();
    assert!(!repo.active_objects.contains(&r.cid));
}

#[test]
fn open_read_skips_exclusive_lock_and_rejects_writes() {
    if std::env::var_os("ARXOS_OPEN_READ_CHILD").is_some() {
        let path = std::env::var("ARXOS_LOCK_PATH").expect("ARXOS_LOCK_PATH");
        let bid = BuildingId::from_str(&std::env::var("ARXOS_BID").expect("ARXOS_BID")).unwrap();
        let read_ok = BuildingRepository::open_read(&path, &bid).is_ok();
        let write_blocked = BuildingRepository::open(&path, &bid).is_err();
        std::process::exit(if read_ok && write_blocked { 0 } else { 1 });
    }

    let dir = tempdir().unwrap();
    let path = dir.path();
    let mut writer = BuildingRepository::init(path, Some("RO".into()), None).unwrap();
    let bid = writer.building_id().clone();
    writer
        .capture_annotation(&AnnotationCapture::new("n", Pose::default()))
        .unwrap();
    writer.commit(Some("c".into())).unwrap();

    // Same-process readers must not take or wait on the exclusive flock.
    let ro_while_writer = BuildingRepository::open_read(path, &bid).unwrap();
    assert!(ro_while_writer.is_read_only());
    assert!(ro_while_writer.head_root().is_some());

    let exe = std::env::current_exe().expect("current_exe");
    let status = std::process::Command::new(exe)
        .arg("--exact")
        .arg("repository::tests::open_read_skips_exclusive_lock_and_rejects_writes")
        .env("ARXOS_OPEN_READ_CHILD", "1")
        .env("ARXOS_LOCK_PATH", path)
        .env("ARXOS_BID", bid.to_string())
        .status()
        .expect("spawn open_read probe");
    assert!(
            status.success(),
            "open_read must succeed and exclusive open must fail while a writer holds store.lock; {status}"
        );

    drop(writer);
    let ro = BuildingRepository::open_read(path, &bid).unwrap();
    assert!(ro.is_read_only());
    assert!(ro.head_root().is_some());
    let obj = Object::new_with_created(
        ObjectBody::Blob(crate::object::BlobBody {
            content_type: None,
            data: b"x".to_vec(),
            properties: BTreeMap::new(),
        }),
        1,
    );
    let err = ro.put_object(&obj).unwrap_err();
    assert!(
        matches!(err, Error::Store(ref m) if m.contains("read-only")),
        "{err:?}"
    );
    let commit_err = {
        let mut ro_mut = BuildingRepository::open_read(path, &bid).unwrap();
        ro_mut.commit(Some("should fail".into())).unwrap_err()
    };
    assert!(
        matches!(commit_err, Error::Store(ref m) if m.contains("read-only")),
        "{commit_err:?}"
    );

    let ro2 = BuildingRepository::open_read(path, &bid).unwrap();
    let mut w2 = BuildingRepository::open(path, &bid).unwrap();
    assert!(!w2.is_read_only());
    w2.capture_annotation(&AnnotationCapture::new("n2", Pose::default()))
        .unwrap();
    let _ = ro2.get_object(&ro2.record().building_object.unwrap());
}

#[test]
fn init_capture_commit_reload() {
    let dir = tempdir().unwrap();
    let path = dir.path();

    let mut repo = BuildingRepository::init(path, Some("Hall".into()), None).unwrap();
    let bid = repo.building_id().clone();
    let head0 = repo.head_root().unwrap();

    repo.capture_space(&SpaceCapture {
        entity_id: None,
        name: Some("Mech Room".into()),
        pose: Pose {
            position: [2.0, 0.0, 1.0],
            orientation: [0.0, 0.0, 0.0, 1.0],
        },
        bounds: None,
        floor: None,
        properties: BTreeMap::new(),
    })
    .unwrap();

    let pts = [
        [0.0f32, 0.0, 0.0],
        [1.0, 0.0, 0.0],
        [1.0, 0.0, 1.0],
        [0.0, 0.0, 1.0],
    ];
    repo.capture_point_cloud(&PointCloudCapture::from_xyz(&pts, Pose::default(), None))
        .unwrap();

    repo.capture_annotation(&AnnotationCapture::new(
        "disconnect switch",
        Pose {
            position: [2.1, 1.2, 1.0],
            orientation: [0.0, 0.0, 0.0, 1.0],
        },
    ))
    .unwrap();

    let commit = repo.commit(Some("first scan".into())).unwrap();
    assert_ne!(commit.root_cid, head0);
    assert_eq!(commit.previous_root, Some(head0));
    assert!(commit.object_count >= 4);
    drop(repo); // release exclusive store lock before re-open

    // Reload same building on "same device"
    let mut repo2 = BuildingRepository::open(path, &bid).unwrap();
    assert_eq!(repo2.head_root(), Some(commit.root_cid));
    let root = repo2.load_head_root().unwrap().unwrap();
    assert_eq!(root.message.as_deref(), Some("first scan"));
    root.verify_authors().unwrap();

    let hits = repo2
        .annotations_near(
            &Pose {
                position: [2.0, 1.0, 1.0],
                orientation: [0.0, 0.0, 0.0, 1.0],
            },
            5.0,
        )
        .unwrap();
    assert_eq!(hits.len(), 1);
    assert_eq!(hits[0].text, "disconnect switch");

    let listed = BuildingRepository::list_buildings(path).unwrap();
    assert_eq!(listed.len(), 1);
    assert_eq!(listed[0].building_id, bid);
}

#[test]
fn pending_survives_reopen_then_commit() {
    let dir = tempdir().unwrap();
    let path = dir.path();
    let mut repo = BuildingRepository::init(path, Some("Pending".into()), None).unwrap();
    let bid = repo.building_id().clone();
    let head0 = repo.head_root().unwrap();

    repo.capture_annotation(&AnnotationCapture::new(
        "staged offline",
        Pose {
            position: [0.0, 1.0, 0.0],
            orientation: [0.0, 0.0, 0.0, 1.0],
        },
    ))
    .unwrap();
    assert_eq!(repo.record().pending.len(), 1);
    drop(repo);

    // Simulate UniFFI: new process opens building; pending must restore.
    let mut repo2 = BuildingRepository::open(path, &bid).unwrap();
    assert_eq!(repo2.record().pending.len(), 1);
    assert_eq!(repo2.working_set().staged_len(), 1);

    let commit = repo2.commit(Some("after reopen".into())).unwrap();
    assert_ne!(commit.root_cid, head0);
    assert!(repo2.record().pending.is_empty());

    let hits = repo2
        .annotations_near(
            &Pose {
                position: [0.0, 1.0, 0.0],
                orientation: [0.0, 0.0, 0.0, 1.0],
            },
            1.0,
        )
        .unwrap();
    assert_eq!(hits.len(), 1);
    assert_eq!(hits[0].text, "staged offline");
}

#[test]
fn test_adopt_root_validation() {
    let dir = tempdir().unwrap();
    let path = dir.path();
    let mut repo = BuildingRepository::init(path, Some("AdoptTest".into()), None).unwrap();
    let bid = repo.building_id().clone();
    let controller = repo.keypair().unwrap();
    let outsider = Keypair::generate();

    // 1. Authorized controller signs a fast-forward root — adopt succeeds.
    let local_head = repo.head_root().unwrap();
    let mut objects = BTreeSet::new();
    objects.insert(repo.record().building_object.unwrap());
    let (root_obj, signed_root_cid) = RootBuilder::new(bid.clone(), 100)
        .objects(objects.clone())
        .previous_root(local_head)
        .message("signed commit")
        .build_signed(controller)
        .unwrap();
    repo.put_object(&root_obj).unwrap();
    assert!(repo.adopt_root(signed_root_cid).is_ok());

    // 2. Valid signature from a non-controller — rejected under default options.
    let (bad_obj, bad_cid) = RootBuilder::new(bid.clone(), 101)
        .objects(objects.clone())
        .previous_root(signed_root_cid)
        .message("outsider")
        .build_signed(&outsider)
        .unwrap();
    repo.put_object(&bad_obj).unwrap();
    let err = repo.adopt_root(bad_cid).unwrap_err();
    assert!(
        matches!(err, Error::Authorization(_)),
        "expected Authorization, got {err:?}"
    );

    // 3. Unsigned root — rejected by default.
    let body = RootBody::new(bid.clone(), Some(signed_root_cid), objects, 102);
    let obj = body.into_object(102);
    let unsigned_root_cid = repo.put_object(&obj).unwrap();
    let err = repo.adopt_root(unsigned_root_cid);
    assert!(err.is_err());
    assert!(matches!(err.unwrap_err(), Error::Signature(_)));

    // 4. allow_untrusted escape hatch accepts unauthorized / unsigned roots.
    let res = repo.adopt_root_with_options(
        unsigned_root_cid,
        &AdoptOptions {
            allow_untrusted: true,
            ..Default::default()
        },
    );
    assert!(res.is_ok());
}

#[test]
fn adopt_incomplete_closure_fails_by_default() {
    let dir = tempdir().unwrap();
    let path = dir.path();
    let mut repo = BuildingRepository::init(path, Some("Partial".into()), None).unwrap();
    let bid = repo.building_id().clone();
    let controller = repo.keypair().unwrap();
    let building_cid = repo.record().building_object.unwrap();

    // Phantom CID listed as active but never stored.
    let ghost = Cid::from_canonical_bytes(b"ghost-object-not-in-store");
    let mut objects = BTreeSet::new();
    objects.insert(building_cid);
    objects.insert(ghost);
    let local_head = repo.head_root().unwrap();
    let (root_obj, root_cid) = RootBuilder::new(bid, 200)
        .objects(objects)
        .previous_root(local_head)
        .message("incomplete")
        .build_signed(controller)
        .unwrap();
    repo.put_object(&root_obj).unwrap();

    let err = repo.adopt_root(root_cid).unwrap_err();
    assert!(
        matches!(err, Error::NotFound(_)),
        "expected NotFound for incomplete adopt, got {err:?}"
    );

    // allow_partial must not install an incomplete head.
    let err = repo
        .adopt_root_with_options(
            root_cid,
            &AdoptOptions {
                allow_untrusted: false,
                allow_partial: true,
                ..Default::default()
            },
        )
        .unwrap_err();
    assert!(
        matches!(err, Error::Validation(_)),
        "expected Validation refusing allow_partial head, got {err:?}"
    );
    assert_eq!(repo.head_root(), Some(local_head));
}

#[test]
fn add_controller_key_allows_second_device_commit() {
    let dir = tempdir().unwrap();
    let path = dir.path();
    let mut repo = BuildingRepository::init(path, Some("Multi".into()), None).unwrap();
    let bid = repo.building_id().clone();
    let first_pk = repo.keypair().unwrap().public_key();
    let second = Keypair::generate();
    let second_pk = second.public_key();

    repo.add_controller_key(second_pk).unwrap();
    let commit = repo.commit(Some("add device B".into())).unwrap();
    assert!(commit.object_count >= 1);
    drop(repo);

    // Device B: write its seed and open; can commit as new controller.
    BuildingRepository::write_seed(path, &second).unwrap();
    let mut repo_b = BuildingRepository::open(path, &bid).unwrap();
    repo_b
        .capture_annotation(&AnnotationCapture::new(
            "from B",
            Pose {
                position: [0.0, 0.0, 0.0],
                orientation: [0.0, 0.0, 0.0, 1.0],
            },
        ))
        .unwrap();
    let c2 = repo_b.commit(Some("B scan".into())).unwrap();
    assert_eq!(c2.previous_root, Some(commit.root_cid));

    let (_, body) = repo_b.current_building_body().unwrap();
    assert_eq!(body.controller_keys.len(), 2);
    assert!(body.controller_keys.contains(&second_pk));
    assert!(body.controller_keys.contains(&first_pk));
}

#[test]
fn remove_controller_key_success_and_remaining_can_commit() {
    let dir = tempdir().unwrap();
    let path = dir.path();
    let mut repo = BuildingRepository::init(path, Some("Rm".into()), None).unwrap();
    let bid = repo.building_id().clone();
    let first_pk = repo.keypair().unwrap().public_key();
    let first = Keypair::from_seed(*repo.keypair().unwrap().seed());
    let second = Keypair::generate();
    repo.add_controller_key(second.public_key()).unwrap();
    repo.commit(Some("add B".into())).unwrap();
    drop(repo);

    BuildingRepository::write_seed(path, &first).unwrap();
    let mut repo = BuildingRepository::open(path, &bid).unwrap();
    repo.remove_controller_key(second.public_key()).unwrap();
    let c = repo.commit(Some("remove B".into())).unwrap();
    assert_eq!(repo.controller_keys().unwrap().len(), 1);
    assert!(repo.controller_keys().unwrap().contains(&first_pk));
    drop(repo);

    // Remaining controller can still author.
    BuildingRepository::write_seed(path, &first).unwrap();
    let mut repo = BuildingRepository::open(path, &bid).unwrap();
    repo.capture_annotation(&AnnotationCapture::new("still here", Pose::default()))
        .unwrap();
    let c2 = repo.commit(Some("after remove".into())).unwrap();
    assert_eq!(c2.previous_root, Some(c.root_cid));
}

#[test]
fn remove_last_controller_rejected() {
    let dir = tempdir().unwrap();
    let path = dir.path();
    let mut repo = BuildingRepository::init(path, Some("Last".into()), None).unwrap();
    let only = repo.keypair().unwrap().public_key();
    let err = repo.remove_controller_key(only).unwrap_err();
    assert!(
        matches!(err, Error::Authorization(_)),
        "expected Authorization, got {err:?}"
    );
}

#[test]
fn remove_unknown_controller_rejected() {
    let dir = tempdir().unwrap();
    let path = dir.path();
    let mut repo = BuildingRepository::init(path, Some("Unk".into()), None).unwrap();
    let stranger = Keypair::generate().public_key();
    let err = repo.remove_controller_key(stranger).unwrap_err();
    assert!(
        matches!(err, Error::Validation(_)),
        "expected Validation, got {err:?}"
    );
}

#[test]
fn removed_controller_cannot_author() {
    let dir = tempdir().unwrap();
    let path = dir.path();
    let mut repo = BuildingRepository::init(path, Some("Authz".into()), None).unwrap();
    let bid = repo.building_id().clone();
    let second = Keypair::generate();
    repo.add_controller_key(second.public_key()).unwrap();
    repo.commit(Some("add B".into())).unwrap();
    // First removes second.
    repo.remove_controller_key(second.public_key()).unwrap();
    repo.commit(Some("drop B".into())).unwrap();
    drop(repo);

    BuildingRepository::write_seed(path, &second).unwrap();
    let mut repo = BuildingRepository::open(path, &bid).unwrap();
    repo.capture_annotation(&AnnotationCapture::new("nope", Pose::default()))
        .unwrap();
    let err = repo.commit(Some("should fail".into())).unwrap_err();
    assert!(
        matches!(err, Error::Authorization(_)),
        "expected Authorization, got {err:?}"
    );
}

#[test]
fn commit_requires_controller_keypair() {
    let dir = tempdir().unwrap();
    let path = dir.path();
    // Init with known controller, then replace seed with an outsider key.
    let repo = BuildingRepository::init(path, Some("Ctrl".into()), None).unwrap();
    let bid = repo.building_id().clone();
    let outsider = Keypair::generate();
    BuildingRepository::write_seed(path, &outsider).unwrap();
    drop(repo); // release exclusive store lock before re-open

    let mut repo = BuildingRepository::open(path, &bid).unwrap();
    repo.capture_annotation(&AnnotationCapture::new(
        "x",
        Pose {
            position: [0.0, 0.0, 0.0],
            orientation: [0.0, 0.0, 0.0, 1.0],
        },
    ))
    .unwrap();
    let err = repo.commit(Some("should fail".into())).unwrap_err();
    assert!(
        matches!(err, Error::Authorization(_)),
        "expected Authorization, got {err:?}"
    );
}

#[test]
fn init_ephemeral_does_not_write_device_seed() {
    let dir = tempdir().unwrap();
    let kp = Keypair::generate();
    let repo = BuildingRepository::init_ephemeral(dir.path(), Some("Eph".into()), kp).unwrap();
    assert!(!dir.path().join("keys").join("device.seed").exists());
    assert!(repo.keypair().is_some());
    assert!(repo.head_root().is_some());
}

#[test]
fn init_writes_device_seed_owner_rw_only() {
    let dir = tempdir().unwrap();
    let _repo = BuildingRepository::init(dir.path(), Some("Keys".into()), None).unwrap();
    let path = dir.path().join("keys").join("device.seed");
    assert!(path.exists());
    #[cfg(unix)]
    {
        use std::os::unix::fs::PermissionsExt;
        let mode = std::fs::metadata(&path).unwrap().permissions().mode() & 0o777;
        assert_eq!(mode, 0o600, "device.seed must be 0o600, got {mode:#o}");
    }
    let kp = BuildingRepository::read_seed(dir.path()).unwrap();
    assert_eq!(kp.public_key(), _repo.keypair().unwrap().public_key());
}
