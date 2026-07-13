//! Golden-path Building compiler spine.
//!
//! init-like seed → mutate → persist (finalize+validate) → query address → export IFC

use arxos::core::domain::ArxAddress;
use arxos::core::operations::backfill_equipment_addresses;
use arxos::core::{Building, Equipment, EquipmentType, Floor, Room, RoomType, Wing};
use arxos::export::ifc::IFCExporter;
use arxos::ingest::persist_building;
use arxos::persistence::{load_building_at, save_building_at, BUILDING_YAML};
use arxos::validation::validate_building;
use serial_test::serial;
use std::env;
use std::path::PathBuf;
use tempfile::tempdir;

#[test]
#[serial]
fn compiler_spine_seed_mutate_query_export() {
    let tmp = tempdir().expect("tempdir");
    let dir = tmp.path().to_path_buf();

    // --- Seed Building (equivalent to init + minimal model) ---
    let mut building = Building::new("Spine HQ".into(), "/spine-hq".into());
    let mut floor = Floor::new("Floor 1".into(), 1);
    let mut wing = Wing::new("Main".into());
    let mut room = Room::new("Office".into(), RoomType::Office);

    let mut eq = Equipment::new(
        "Sensor-A".into(),
        String::new(),
        EquipmentType::Other("sensor".into()),
    );
    // Intentionally no address yet — migrate will fill
    eq.set_room(room.id.clone());
    room.add_equipment(eq);
    wing.add_room(room);
    floor.add_wing(wing);
    building.add_floor(floor);

    save_building_at(&dir, &building).expect("seed building.yaml");
    assert!(dir.join(BUILDING_YAML).exists());

    // --- Work in project dir for persist_building / query ---
    let original = env::current_dir().unwrap_or_else(|_| PathBuf::from("."));
    env::set_current_dir(&dir).expect("chdir");

    // --- Backfill addresses + persist through finalize gate ---
    let mut building = load_building_at(".").expect("load");
    let filled = backfill_equipment_addresses(&mut building);
    assert_eq!(filled, 1);
    let building = persist_building(building, false, Some("spine: backfill")).expect("persist");

    let report = validate_building(&building);
    assert!(
        !report.has_errors(),
        "validation errors: {:?}",
        report.summary_lines()
    );

    // --- Query by durable address glob ---
    let matches = arxos::cli::commands::query::query_equipment_by_address(
        "/local/local/local/*/floor-1/*/sensor-a",
    )
    .expect("query");
    // floor slug may be "floor-1" from name "Floor 1"
    let matches2 = arxos::cli::commands::query::query_equipment_by_address(
        "/local/local/local/*/*/*/sensor-a",
    )
    .expect("query wildcard");
    assert!(
        !matches2.is_empty() || !matches.is_empty(),
        "expected query hit on durable address; equipment={:?}",
        building
            .get_all_equipment()
            .iter()
            .map(|e| e.address.as_ref().map(|a| a.path.clone()))
            .collect::<Vec<_>>()
    );

    // Explicit path from assigned address
    let path = building
        .get_all_equipment()
        .first()
        .and_then(|e| e.address.as_ref())
        .map(|a| a.path.clone())
        .expect("address present");
    let exact = arxos::cli::commands::query::query_equipment_by_address(&path).expect("exact");
    assert_eq!(exact.len(), 1);
    assert_eq!(exact[0].name, "Sensor-A");

    // --- IFC export projection ---
    let ifc_out = dir.join("spine.ifc");
    IFCExporter::new(building.clone())
        .export(&ifc_out)
        .expect("ifc export");
    assert!(ifc_out.exists());
    let ifc_text = std::fs::read_to_string(&ifc_out).expect("read ifc");
    assert!(ifc_text.contains("ISO-10303-21"), "IFC header");
    assert!(ifc_text.contains("IFC"), "IFC entities");

    // Round-trip address type API
    let addr = ArxAddress::from_path(&path).expect("parse path");
    assert!(addr.matches_glob("/local/local/local/*/*/*"));

    env::set_current_dir(original).ok();
}
