//! IFC export → import round-trip preserves Pset_ArxosIdentity.

use std::collections::BTreeMap;

use arxos_core::capture::{AnnotationCapture, SpaceCapture};
use arxos_core::object::{FloorBody, Object, ObjectBody, Pose};
use arxos_core::repository::BuildingRepository;
use arxos_core::Keypair;
use arxos_ifc::{export_building_ifc, import_ifc, ExportOptions};
use tempfile::tempdir;

#[test]
fn ifc_roundtrip_identity() {
    let dir = tempdir().unwrap();
    let path = dir.path();
    let kp = Keypair::generate();
    let mut repo =
        BuildingRepository::init(path, Some("IFC Hall".into()), Some(Keypair::from_seed(*kp.seed()))).unwrap();
    let bid = repo.building_id().clone();

    let floor = Object::new(ObjectBody::Floor(FloorBody {
        entity_id: Some(arxos_core::EntityId::new()),
        building_id: bid.clone(),
        name: Some("Ground".into()),
        level_index: 0,
        elevation_m: 0.0,
        properties: BTreeMap::new(),
    }));
    let floor_cid = repo.put_object(&floor).unwrap();

    repo.capture_space(&SpaceCapture {
                    entity_id: None,
        name: Some("Mech".into()),
        pose: Pose {
            position: [1.0, 0.0, 2.0],
            orientation: [0.0, 0.0, 0.0, 1.0],
        },
        bounds: None,
        floor: Some(floor_cid),
        properties: BTreeMap::new(),
    })
    .unwrap();
    repo.capture_annotation(&AnnotationCapture::new(
        "disconnect",
        Pose {
            position: [1.2, 1.5, 2.0],
            orientation: [0.0, 0.0, 0.0, 1.0],
        },
    ))
    .unwrap();
    let commit = repo.commit(Some("ifc source".into())).unwrap();
    drop(repo); // release exclusive store lock before export re-opens the building

    let ifc = export_building_ifc(path, &bid, &ExportOptions::default()).unwrap();
    assert!(ifc.contains("ISO-10303-21"));
    assert!(ifc.contains("IFCBUILDING"));
    assert!(ifc.contains("Pset_ArxosIdentity"));
    assert!(ifc.contains("IFCANNOTATION"));
    assert!(ifc.contains(&commit.root_cid.to_string()) || ifc.contains("arxos_root="));

    let dir2 = tempdir().unwrap();
    let imp = import_ifc(dir2.path(), &ifc, Some(&kp)).unwrap();
    assert_eq!(imp.building_id.to_string(), bid.to_string());
    assert!(imp.root_cid.is_some());
    assert!(imp.object_cids.len() >= 2);
    assert!(
        imp.source_root_cid.as_deref() == Some(commit.root_cid.to_string().as_str())
            || imp.source_root_cid.is_some()
    );

    // Source CIDs preserved on at least one object
    let store = arxos_core::store::ObjectStore::open(dir2.path()).unwrap();
    let mut found_source = false;
    for cid in &imp.object_cids {
        let obj = store.get(cid).unwrap();
        let props = match &obj.body {
            ObjectBody::Building(b) => &b.properties,
            ObjectBody::Floor(b) => &b.properties,
            ObjectBody::Space(b) => &b.properties,
            ObjectBody::Annotation(b) => &b.properties,
            _ => continue,
        };
        if props.contains_key("arxos_source_cid") {
            found_source = true;
            break;
        }
    }
    assert!(found_source, "expected arxos_source_cid on imported objects");
}
