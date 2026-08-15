//! Multi-device concurrent tip integration (deterministic, no network).
//!
//! Exercises: entity update/remove, concurrent merge (three-way), controller
//! add/remove enforceability after merge, and scoring against collapsed heads.

use std::collections::BTreeMap;

use arxos_core::capture::{AnnotationCapture, SpaceCapture};
use arxos_core::entity::EntityId;
use arxos_core::object::Pose;
use arxos_core::repository::BuildingRepository;
use arxos_core::scoring::score_root;
use arxos_core::Keypair;
use tempfile::tempdir;

/// Copy CAS object bytes only (does not overwrite head pointers).
fn mirror_objects(src: &std::path::Path, dst: &std::path::Path) {
    let s = arxos_core::store::ObjectStore::open(src).unwrap();
    let d = arxos_core::store::ObjectStore::open(dst).unwrap();
    for cid in s.list_cids().unwrap() {
        if !d.contains(&cid) {
            let bytes = s.get_bytes(&cid).unwrap();
            d.put_bytes(&bytes).unwrap();
        }
    }
}

/// Copy CAS + building head records (initial device clone).
fn mirror_store(src: &std::path::Path, dst: &std::path::Path) {
    mirror_objects(src, dst);
    let meta_src = src.join("meta").join("buildings");
    let meta_dst = dst.join("meta").join("buildings");
    if meta_src.exists() {
        std::fs::create_dir_all(&meta_dst).unwrap();
        for ent in std::fs::read_dir(&meta_src).unwrap() {
            let ent = ent.unwrap();
            let to = meta_dst.join(ent.file_name());
            std::fs::copy(ent.path(), to).unwrap();
        }
    }
}

fn write_device_seed(store: &std::path::Path, kp: &Keypair) {
    let path = store.join("keys").join("device.seed");
    let seed = kp.seed();
    arxos_core::write_secret_bytes(&path, seed.as_ref()).unwrap();
}

#[test]
fn concurrent_entity_update_and_remove_merge() {
    let dir_a = tempdir().unwrap();
    let dir_b = tempdir().unwrap();

    // Device A: init + space entity + commit base.
    let mut repo_a = BuildingRepository::init(dir_a.path(), Some("Site".into()), None).unwrap();
    let bid = repo_a.building_id().clone();
    let kp_a = Keypair::from_seed(*repo_a.keypair().unwrap().seed());
    let eid = EntityId::from("01MULTIDEVICEENTITY0000000".to_string());

    let r1 = repo_a
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
    let base = repo_a.commit(Some("base".into())).unwrap();
    drop(repo_a);

    // Seed device B store with A's CAS + follow head.
    mirror_store(dir_a.path(), dir_b.path());
    // Copy device seed for B later; first follow without needing to commit as A.
    std::fs::create_dir_all(dir_b.path().join("keys")).unwrap();
    // Device B uses its own key — but is not yet a controller. For concurrent
    // field work we add B as controller on A first, then re-mirror.
    let kp_b = Keypair::generate();
    {
        write_device_seed(dir_a.path(), &kp_a);
        let mut repo_a = BuildingRepository::open(dir_a.path(), &bid).unwrap();
        repo_a.add_controller_key(kp_b.public_key()).unwrap();
        let _ = repo_a.commit(Some("add B".into())).unwrap();
        drop(repo_a);
    }
    mirror_store(dir_a.path(), dir_b.path());
    write_device_seed(dir_b.path(), &kp_b);

    // Open B at head (after controller add).
    let mut repo_b = BuildingRepository::open(dir_b.path(), &bid).unwrap();
    // B updates the same entity (v2).
    let r2 = repo_b
        .capture_space(&SpaceCapture {
            entity_id: Some(eid.clone()),
            name: Some("v2-from-B".into()),
            pose: Pose {
                position: [1.0, 0.0, 0.0],
                orientation: [0.0, 0.0, 0.0, 1.0],
            },
            bounds: None,
            floor: None,
            properties: BTreeMap::new(),
        })
        .unwrap();
    let tip_b = repo_b.commit(Some("B update entity".into())).unwrap();
    drop(repo_b);

    // A concurrently removes the entity (offline from B).
    write_device_seed(dir_a.path(), &kp_a);
    let mut repo_a = BuildingRepository::open(dir_a.path(), &bid).unwrap();
    let n = repo_a.remove_entity(&eid).unwrap();
    assert!(n >= 1, "expected to stage removal of v1 {r1:?}");
    repo_a
        .capture_annotation(&AnnotationCapture::new(
            "A note while removing",
            Pose::default(),
        ))
        .unwrap();
    let tip_a = repo_a.commit(Some("A remove entity".into())).unwrap();
    drop(repo_a);

    // Bring B's tip objects into A's store (keep A's head pointer).
    mirror_objects(dir_b.path(), dir_a.path());
    write_device_seed(dir_a.path(), &kp_a);
    let mut repo_a = BuildingRepository::open(dir_a.path(), &bid).unwrap();
    assert_eq!(repo_a.head_root(), Some(tip_a.root_cid));
    let merged = repo_a
        .merge_root(tip_b.root_cid, Some("merge A+B".into()))
        .unwrap();
    let heads = repo_a.list_entity_heads().unwrap();
    // Concurrent remove vs update: three-way removes v1 from A path; B adds v2.
    // Result should have v2 (B's update) OR nothing if remove wins over update.
    // Our three-way: base has v1; A removes v1; B removes v1 adds v2.
    // result = base - v1 + v2 = has v2. Update survives when concurrent with remove
    // of the *same* base version (B's add is independent of A's remove of v1).
    // Documented invariant: concurrent remove of old version + add of new version
    // keeps the new version (entity evolves).
    assert!(
        heads.iter().any(|(e, c, _)| e == &eid && *c == r2.cid),
        "expected entity head at B's version after merge; heads={heads:?} merged={merged:?}"
    );
    assert!(!repo_a.head_object_cids().unwrap().contains(&r1.cid));
    // A's annotation kept.
    let active = repo_a.head_object_cids().unwrap();
    assert!(active.len() >= 2);
    let _ = (base, tip_a, merged);
}

#[test]
fn concurrent_remove_only_drops_entity() {
    let dir = tempdir().unwrap();
    let mut repo = BuildingRepository::init(dir.path(), Some("Rm".into()), None).unwrap();
    let kp = Keypair::from_seed(*repo.keypair().unwrap().seed());
    let bid = repo.building_id().clone();
    let eid = EntityId::from("01ONLYREMOVE00000000000000".to_string());

    repo.capture_space(&SpaceCapture {
        entity_id: Some(eid.clone()),
        name: Some("gone".into()),
        pose: Pose::default(),
        bounds: None,
        floor: None,
        properties: BTreeMap::new(),
    })
    .unwrap();
    let base = repo.commit(Some("with space".into())).unwrap();
    drop(repo);

    // Branch A: remove entity
    let mut repo_a = BuildingRepository::open(dir.path(), &bid).unwrap();
    repo_a.remove_entity(&eid).unwrap();
    let tip_a = repo_a.commit(Some("remove".into())).unwrap();
    let root_a = tip_a.root_cid;
    drop(repo_a);

    // Branch B: fork from base — need separate store with only base head
    // Simulate by opening a second store mirrored at base time... simpler:
    // use two roots from same store where B was created before A's remove.
    // Rebuild: second device path.
    let dir_b = tempdir().unwrap();
    // Mirror full store then reset B's head to base by adopt.
    mirror_store(dir.path(), dir_b.path());
    write_device_seed(dir_b.path(), &kp);
    // B still has base as head if we never pulled tip_a — but mirror copied tip_a objects.
    // Force B head to base:
    {
        let mut repo_b = BuildingRepository::open(dir_b.path(), &bid).unwrap();
        // If head is tip_a, adopt base (allow if tip_a is head).
        if repo_b.head_root() != Some(base.root_cid) {
            repo_b.adopt_root(base.root_cid).unwrap();
        }
        // B adds annotation only (keeps entity)
        repo_b
            .capture_annotation(&AnnotationCapture::new("keep room", Pose::default()))
            .unwrap();
        let tip_b = repo_b.commit(Some("ann".into())).unwrap();
        drop(repo_b);

        // Merge on A side: A has tip_a (entity removed), import tip_b objects only
        mirror_objects(dir_b.path(), dir.path());
        let mut repo_a = BuildingRepository::open(dir.path(), &bid).unwrap();
        assert_eq!(repo_a.head_root(), Some(root_a));
        let merged = repo_a.merge_root(tip_b.root_cid, Some("merge".into())).unwrap();
        let heads = repo_a.list_entity_heads().unwrap();
        assert!(
            !heads.iter().any(|(e, _, _)| e == &eid),
            "entity must stay removed after merge with tip that kept it; heads={heads:?}"
        );
        // Annotation from B should be present
        let report = score_root(repo_a.store(), &merged.root_cid, &Default::default()).unwrap();
        assert!(report.total_objects >= 2);
    }
}

#[test]
fn controller_add_survives_sync_and_enforce() {
    let dir_a = tempdir().unwrap();
    let dir_b = tempdir().unwrap();

    let mut repo_a = BuildingRepository::init(dir_a.path(), Some("Ctrl".into()), None).unwrap();
    let bid = repo_a.building_id().clone();
    let kp_a = Keypair::from_seed(*repo_a.keypair().unwrap().seed());
    let kp_b = Keypair::generate();
    repo_a.add_controller_key(kp_b.public_key()).unwrap();
    let _ = repo_a.commit(Some("add B".into())).unwrap();
    drop(repo_a);

    mirror_store(dir_a.path(), dir_b.path());
    write_device_seed(dir_b.path(), &kp_b);
    let mut repo_b = BuildingRepository::open(dir_b.path(), &bid).unwrap();
    assert_eq!(repo_b.controller_keys().unwrap().len(), 2);
    repo_b
        .capture_annotation(&AnnotationCapture::new("from B", Pose::default()))
        .unwrap();
    let tip_b = repo_b.commit(Some("B works".into())).unwrap();
    drop(repo_b);

    // A removes B
    write_device_seed(dir_a.path(), &kp_a);
    let mut repo_a = BuildingRepository::open(dir_a.path(), &bid).unwrap();
    repo_a.remove_controller_key(kp_b.public_key()).unwrap();
    let tip_a = repo_a.commit(Some("drop B".into())).unwrap();
    drop(repo_a);

    // Merge: A dropped B as controller; B authored while still controller.
    // LCA is "add B"; tip_a has Building[A]; tip_b has Building[A,B]+ann.
    // Three-way + building collapse → Building[A] + ann; B cannot author after.
    mirror_objects(dir_b.path(), dir_a.path());
    write_device_seed(dir_a.path(), &kp_a);
    let mut repo_a = BuildingRepository::open(dir_a.path(), &bid).unwrap();
    assert_eq!(repo_a.head_root(), Some(tip_a.root_cid));
    let merged = repo_a
        .merge_root(tip_b.root_cid, Some("merge ctrl".into()))
        .unwrap();
    let keys = repo_a.controller_keys().unwrap();
    assert_eq!(keys.len(), 1);
    assert!(keys.contains(&kp_a.public_key()));
    assert!(!keys.contains(&kp_b.public_key()));

    // B cannot author against merged head
    mirror_objects(dir_a.path(), dir_b.path());
    write_device_seed(dir_b.path(), &kp_b);
    let mut repo_b = BuildingRepository::open(dir_b.path(), &bid).unwrap();
    repo_b.adopt_root(merged.root_cid).unwrap();
    repo_b
        .capture_annotation(&AnnotationCapture::new("nope", Pose::default()))
        .unwrap();
    let err = repo_b.commit(Some("should fail".into())).unwrap_err();
    assert!(
        matches!(err, arxos_core::Error::Authorization(_)),
        "got {err:?}"
    );
}

#[test]
fn scoring_ignores_removed_and_superseded_entity_versions() {
    let dir = tempdir().unwrap();
    let mut repo = BuildingRepository::init(dir.path(), Some("Score".into()), None).unwrap();
    let eid = EntityId::from("01SCORESUPERSEDE0000000000".to_string());

    repo.capture_space(&SpaceCapture {
        entity_id: Some(eid.clone()),
        name: Some("v1".into()),
        pose: Pose::default(),
        bounds: None,
        floor: None,
        properties: BTreeMap::new(),
    })
    .unwrap();
    let c1 = repo.commit(Some("v1".into())).unwrap();
    let score1 = score_root(repo.store(), &c1.root_cid, &Default::default()).unwrap();

    repo.capture_space(&SpaceCapture {
        entity_id: Some(eid.clone()),
        name: Some("v2".into()),
        pose: Pose {
            position: [2.0, 0.0, 0.0],
            orientation: [0.0, 0.0, 0.0, 1.0],
        },
        bounds: None,
        floor: None,
        properties: BTreeMap::new(),
    })
    .unwrap();
    let c2 = repo.commit(Some("v2".into())).unwrap();
    let score2 = score_root(repo.store(), &c2.root_cid, &Default::default()).unwrap();
    // Same space count (one entity head), not double.
    assert_eq!(
        score1.contributors.iter().map(|c| c.spaces).sum::<u64>(),
        score2.contributors.iter().map(|c| c.spaces).sum::<u64>()
    );

    repo.remove_entity(&eid).unwrap();
    let c3 = repo.commit(Some("rm".into())).unwrap();
    let score3 = score_root(repo.store(), &c3.root_cid, &Default::default()).unwrap();
    assert_eq!(
        score3.contributors.iter().map(|c| c.spaces).sum::<u64>(),
        0,
        "removed entity must not contribute space score"
    );
}

#[test]
fn scoring_after_merge_matches_active_set() {
    let dir = tempdir().unwrap();
    let mut repo = BuildingRepository::init(dir.path(), Some("MScore".into()), None).unwrap();
    let bid = repo.building_id().clone();
    let kp = Keypair::from_seed(*repo.keypair().unwrap().seed());
    let eid = EntityId::from("01MERGESCORE00000000000000".to_string());

    repo.capture_space(&SpaceCapture {
        entity_id: Some(eid.clone()),
        name: Some("s".into()),
        pose: Pose::default(),
        bounds: None,
        floor: None,
        properties: BTreeMap::new(),
    })
    .unwrap();
    let base = repo.commit(Some("base".into())).unwrap();
    drop(repo);

    // Two branches from base with different annotations
    let dir2 = tempdir().unwrap();
    mirror_store(dir.path(), dir2.path());
    write_device_seed(dir.path(), &kp);
    write_device_seed(dir2.path(), &kp);

    let mut ra = BuildingRepository::open(dir.path(), &bid).unwrap();
    if ra.head_root() != Some(base.root_cid) {
        ra.adopt_root(base.root_cid).unwrap();
    }
    ra.capture_annotation(&AnnotationCapture::new("left", Pose::default()))
        .unwrap();
    let tip_a = ra.commit(Some("a".into())).unwrap();
    drop(ra);

    let mut rb = BuildingRepository::open(dir2.path(), &bid).unwrap();
    if rb.head_root() != Some(base.root_cid) {
        rb.adopt_root(base.root_cid).unwrap();
    }
    rb.capture_annotation(&AnnotationCapture::new("right", Pose {
        position: [5.0, 0.0, 0.0],
        orientation: [0.0, 0.0, 0.0, 1.0],
    }))
    .unwrap();
    let tip_b = rb.commit(Some("b".into())).unwrap();
    drop(rb);

    mirror_objects(dir2.path(), dir.path());
    let mut ra = BuildingRepository::open(dir.path(), &bid).unwrap();
    assert_eq!(ra.head_root(), Some(tip_a.root_cid));
    let merged = ra.merge_root(tip_b.root_cid, Some("m".into())).unwrap();
    let report = score_root(ra.store(), &merged.root_cid, &Default::default()).unwrap();
    let anns: u64 = report.contributors.iter().map(|c| c.annotations).sum();
    assert_eq!(anns, 2, "both concurrent annotations scored once each");
    let spaces: u64 = report.contributors.iter().map(|c| c.spaces).sum();
    assert_eq!(spaces, 1, "one entity head space");
}
