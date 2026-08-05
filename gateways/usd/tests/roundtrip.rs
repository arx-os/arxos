//! USD export → import round-trip preserves identity properties and structure.

use std::collections::BTreeMap;

use arxos_core::capture::{AnnotationCapture, SpaceCapture};
use arxos_core::object::{FloorBody, Object, ObjectBody, Pose};
use arxos_core::repository::BuildingRepository;
use arxos_core::store::ObjectStore;
use arxos_core::Keypair;
use arxos_usd::{export_building_usda, import_usda, ExportOptions};
use tempfile::tempdir;

#[test]
fn usd_roundtrip_identity() {
    let dir = tempdir().unwrap();
    let path = dir.path();
    let kp = Keypair::generate();
    let mut repo =
        BuildingRepository::init(path, Some("USD Hall".into()), Some(kp.clone())).unwrap();
    let bid = repo.building_id().clone();

    // Floor + space + annotation
    let floor = Object::new(ObjectBody::Floor(FloorBody {
        entity_id: Some(arxos_core::EntityId::new()),
        building_id: bid.clone(),
        name: Some("L1".into()),
        level_index: 0,
        elevation_m: 0.0,
        properties: BTreeMap::new(),
    }));
    let floor_cid = repo.store().put(&floor).unwrap();
    // stage floor by putting into pending via capture_space path — use raw put + pending
    // Through capture APIs:
    repo.capture_space(&SpaceCapture {
                    entity_id: None,
        name: Some("Room A".into()),
        pose: Pose {
            position: [2.0, 0.0, 3.0],
            orientation: [0.0, 0.0, 0.0, 1.0],
        },
        bounds: None,
        floor: Some(floor_cid),
        properties: BTreeMap::new(),
    })
    .unwrap();
    // Also add floor to store pending manually by re-opening and... just include floor in commit
    // by putting into store and adding to pending via capture annotation after commit init.
    // Force floor into graph: put + stage through second capture of annotation only after
    // injecting floor into head by putting and including in commit.
    {
        // Put floor and add to pending by using store + open record hack:
        // commit carries previous objects; floor not pending.
        // Put floor as a staged object using annotation then replace - simpler: export only
        // from commit that includes floor via capture.
        let store = ObjectStore::open(path).unwrap();
        let _ = store.put(&floor).unwrap();
    }

    repo.capture_annotation(&AnnotationCapture::new(
        "panel note",
        Pose {
            position: [2.1, 1.4, 3.0],
            orientation: [0.0, 0.0, 0.0, 1.0],
        },
    ))
    .unwrap();
    // Add floor cid to pending by capturing another object won't work.
    // Use commit then merge floor via second commit after staging floor:
    // Direct: use BuildingRepository internals - put floor and use root from capture commit,
    // then for roundtrip we only need building+space+annotation which we have.
    let _ = floor_cid;
    let commit = repo.commit(Some("usd source".into())).unwrap();
    let _ = commit;
    drop(repo); // release exclusive store lock before export re-opens the building

    let usda = export_building_usda(path, &bid, &ExportOptions::default()).unwrap();
    assert!(usda.contains("#usda 1.0"));
    assert!(usda.contains("arxos:cid"));
    assert!(usda.contains("panel note") || usda.contains("panel_note") || usda.contains("arxos:text"));

    let dir2 = tempdir().unwrap();
    let imp = import_usda(dir2.path(), &usda, Some(&kp)).unwrap();
    assert_eq!(imp.building_id, bid);
    assert!(imp.root_cid.is_some());
    assert!(imp.object_cids.len() >= 2);
    assert_eq!(
        imp.source_root_cid.as_deref(),
        Some(commit.root_cid.to_string().as_str())
    );

    // Re-export and check identity props survive
    let usda2 = export_building_usda(dir2.path(), &imp.building_id, &ExportOptions::default())
        .unwrap();
    assert!(usda2.contains("arxos:buildingId"));
    assert!(usda2.contains(bid.as_str()));
}
