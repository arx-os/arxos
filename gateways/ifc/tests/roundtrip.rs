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
    let mut repo = BuildingRepository::init(
        path,
        Some("IFC Hall".into()),
        Some(Keypair::from_seed(*kp.seed())),
    )
    .unwrap();
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
    assert!(ifc.contains("ViewDefinition [ArxosAsBuiltView]"));
    assert!(!ifc.contains("CoordinationView"));
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
    assert!(
        found_source,
        "expected arxos_source_cid on imported objects"
    );
}

#[test]
fn ifc_unsigned_import_refused() {
    let dir = tempdir().unwrap();
    let path = dir.path();
    let mut repo = BuildingRepository::init(path, Some("IFC Hall".into()), None).unwrap();
    let bid = repo.building_id().clone();
    repo.capture_annotation(&AnnotationCapture::new("note", Pose::default()))
        .unwrap();
    let _ = repo.commit(Some("src".into())).unwrap();
    drop(repo);

    let ifc = export_building_ifc(path, &bid, &ExportOptions::default()).unwrap();
    let dir2 = tempdir().unwrap();
    let err = import_ifc(dir2.path(), &ifc, None).unwrap_err();
    assert!(
        err.to_string().contains("unsigned") || err.to_string().contains("device key"),
        "expected unsigned import refusal, got {err}"
    );
}

#[test]
fn ifc_wall_fact_emits_ifcwall() {
    use arxos_core::entity::EntityId;
    use arxos_core::object::{Object, ObjectBody, SurfaceBody};

    let dir = tempdir().unwrap();
    let path = dir.path();
    let kp = Keypair::generate();
    let mut repo = BuildingRepository::init(
        path,
        Some("Wall Hall".into()),
        Some(Keypair::from_seed(*kp.seed())),
    )
    .unwrap();
    let bid = repo.building_id().clone();
    let eid = EntityId::from("rp:wall-export-1".to_string());
    let wall = Object::new_with_created(
        ObjectBody::Surface(SurfaceBody {
            entity_id: Some(eid.clone()),
            pose: Some(Pose {
                position: [2.0, 1.25, 0.0],
                orientation: [0.0, 0.0, 0.0, 1.0],
            }),
            surface_kind: Some("wall".into()),
            extent: Some([4.0, 2.5, 0.15]),
            sigma_mm: Some(40.0),
            support_count: 1,
            ..Default::default()
        }),
        1,
    );
    repo.stage_captured_object(wall).unwrap();
    repo.commit(Some("one wall".into())).unwrap();
    drop(repo);

    let ifc = export_building_ifc(path, &bid, &ExportOptions::default()).unwrap();
    assert!(
        ifc.contains("IFCWALL") || ifc.contains("IFCWALLSTANDARDCASE"),
        "expected IFCWALL in export, got:\n{}",
        &ifc[..ifc.len().min(2000)]
    );
    assert!(ifc.contains("Pset_ArxosIdentity"));
    assert!(ifc.contains("EntityId") || ifc.contains("rp:wall-export-1"));
    assert!(ifc.contains("Pset_ArxosMeasure"));
    assert!(ifc.contains("IFCEXTRUDEDAREASOLID"));
}

#[test]
fn ifc_hall_door_emits_void_relationship() {
    use arxos_core::capture::roomplan::{hall_four_walls_with_door, map_roomplan};

    let dir = tempdir().unwrap();
    let path = dir.path();
    let kp = Keypair::generate();
    let mut repo = BuildingRepository::init(
        path,
        Some("Hall".into()),
        Some(Keypair::from_seed(*kp.seed())),
    )
    .unwrap();
    let bid = repo.building_id().clone();
    let mapped = map_roomplan(&hall_four_walls_with_door([0.0, 0.0, 0.0], 40.0), 1).unwrap();
    repo.ingest_mapped_roomplan(mapped).unwrap();
    repo.commit(Some("hall+door".into())).unwrap();
    drop(repo);

    let ifc = export_building_ifc(path, &bid, &ExportOptions::default()).unwrap();
    assert!(ifc.contains("ViewDefinition [ArxosAsBuiltView]"));
    assert!(!ifc.contains("CoordinationView"));
    assert!(
        ifc.contains("IFCWALL"),
        "missing IFCWALL:\n{}",
        &ifc[..ifc.len().min(1500)]
    );
    assert!(
        ifc.contains("IFCDOOR") || ifc.contains("IFCOPENINGELEMENT"),
        "missing door/opening:\n{}",
        &ifc[..ifc.len().min(2000)]
    );
    assert!(
        ifc.contains("IFCRELVOIDSELEMENT"),
        "missing void relationship:\n{}",
        &ifc[..ifc.len().min(2500)]
    );
    assert!(ifc.contains("EntityId") || ifc.contains("rp:"));
}
