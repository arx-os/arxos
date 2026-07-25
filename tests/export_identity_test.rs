//! Export identity round-trip: preserve IFC GlobalIds; assign for Arxos-native.

use arxos::core::domain::ArxAddress;
use arxos::core::operations::address_mutate::{add_under_address, AddKind};
use arxos::core::{Building, Equipment, EquipmentType, Floor, Room, RoomType, Wing};
use arxos::export::ifc::{ifc_product_type_for_equipment, IFCExporter};
use arxos::ifc::mapping::{
    assign_missing_global_ids, has_ifc_global_id, resolve_product_global_id,
};
use arxos::ingest::persist_building_at;
use arxos::persistence::load_building_at;
use serial_test::serial;
use std::fs;
use tempfile::tempdir;

fn building_with_import_and_native() -> Building {
    let root = ArxAddress::from_path("bldg.us.fl.tampa.dale-mabry.143677.s2").unwrap();
    let mut b = Building::new("HQ".into(), "/hq".into());
    b.address = Some(root.clone());
    b.ifc_global_id = Some("ImportBldgGid0000000001".into());

    let mut floor = Floor::new("Level 1".into(), 1);
    floor.address = Some(root.join("fl.1").unwrap());
    floor.ifc_global_id = Some("ImportFloorGid000000001".into());

    let mut wing = Wing::new("Main".into());
    let mut room = Room::new("A101".into(), RoomType::Office);
    room.address = Some(floor.address.as_ref().unwrap().join("rm.a101").unwrap());
    room.ifc_global_id = Some("ImportRoomGid0000000001".into());

    // IFC-origin equipment
    let mut imported =
        Equipment::new("Imported-Switch".into(), String::new(), EquipmentType::Electrical);
    imported.address = Some(
        root.join("elec")
            .unwrap()
            .join("panel.l1")
            .unwrap()
            .join("sw.old")
            .unwrap(),
    );
    imported.ifc_global_id = Some("ImportEquipGid000000001".into());
    room.add_equipment(imported);

    // Seed circuit path via native panel structure for add_under_address
    let mut panel = Equipment::new("L1".into(), String::new(), EquipmentType::Electrical);
    panel.address = Some(root.join("elec").unwrap().join("panel.l1").unwrap());
    // leave no global id — will be assigned on export
    room.add_equipment(panel);

    wing.add_room(room);
    floor.add_wing(wing);
    b.add_floor(floor);
    b
}

#[test]
fn assign_preserves_import_assigns_native() {
    let mut b = building_with_import_and_native();
    let stats = assign_missing_global_ids(&mut b);
    assert!(stats.preserved >= 3);
    assert!(stats.assigned >= 1);

    let imported = b
        .get_all_equipment()
        .into_iter()
        .find(|e| e.name == "Imported-Switch")
        .unwrap();
    assert_eq!(
        imported.ifc_global_id.as_deref(),
        Some("ImportEquipGid000000001")
    );

    let panel = b
        .get_all_equipment()
        .into_iter()
        .find(|e| e.name == "L1")
        .unwrap();
    assert!(has_ifc_global_id(&panel.ifc_global_id));
    let expected = resolve_product_global_id(&None, &panel.id);
    assert_eq!(panel.ifc_global_id.as_deref(), Some(expected.as_str()));
}

#[test]
#[serial]
fn add_outlet_export_assigns_and_stabilizes_global_id() {
    let tmp = tempdir().unwrap();
    let mut b = building_with_import_and_native();
    // Ensure ckt path exists for parent resolve
    let r = add_under_address(
        &mut b,
        "bldg.us.fl.tampa.dale-mabry.143677.s2/elec/panel.l1",
        AddKind::Circuit,
        Some("14"),
    )
    .unwrap();
    assert!(r.address.path.ends_with("/ckt.14"));

    let outlet = add_under_address(
        &mut b,
        "bldg.us.fl.tampa.dale-mabry.143677.s2/elec/panel.l1/ckt.14",
        AddKind::Outlet,
        None,
    )
    .unwrap();
    assert!(outlet.address.path.ends_with("/rec.1"));
    // No GlobalId yet
    let pre = b
        .get_all_equipment()
        .into_iter()
        .find(|e| e.address.as_ref().map(|a| a.path.as_str()) == Some(outlet.address.path.as_str()))
        .unwrap();
    assert!(!has_ifc_global_id(&pre.ifc_global_id));

    // Export path: assign + write IFC
    let stats = assign_missing_global_ids(&mut b);
    assert!(stats.assigned >= 1);
    let after_assign = b
        .get_all_equipment()
        .into_iter()
        .find(|e| e.address.as_ref().map(|a| a.path.as_str()) == Some(outlet.address.path.as_str()))
        .unwrap()
        .ifc_global_id
        .clone()
        .unwrap();
    assert_eq!(after_assign.len(), 22);

    // Imported unchanged
    let imported = b
        .get_all_equipment()
        .into_iter()
        .find(|e| e.name == "Imported-Switch")
        .unwrap();
    assert_eq!(
        imported.ifc_global_id.as_deref(),
        Some("ImportEquipGid000000001")
    );

    let ifc_path = tmp.path().join("out.ifc");
    IFCExporter::new(b.clone())
        .export(&ifc_path)
        .expect("export");
    let ifc_text = fs::read_to_string(&ifc_path).unwrap();
    assert!(ifc_text.contains("IFCOUTLET"), "expected IFCOUTLET for rec.*");
    assert!(
        ifc_text.contains(&after_assign),
        "export must contain assigned GlobalId"
    );
    assert!(
        ifc_text.contains("ImportEquipGid000000001"),
        "export must preserve imported GlobalId"
    );

    // Second assign: no churn
    let stats2 = assign_missing_global_ids(&mut b);
    assert_eq!(stats2.assigned, 0);
    let again = b
        .get_all_equipment()
        .into_iter()
        .find(|e| e.address.as_ref().map(|a| a.path.as_str()) == Some(outlet.address.path.as_str()))
        .unwrap()
        .ifc_global_id
        .clone()
        .unwrap();
    assert_eq!(again, after_assign);

    // Persist + reload: GlobalId stable
    persist_building_at(tmp.path(), b, false, Some("export identity")).unwrap();
    let loaded = load_building_at(tmp.path()).unwrap();
    let loaded_eq = loaded
        .get_all_equipment()
        .into_iter()
        .find(|e| e.address.as_ref().map(|a| a.path.as_str()) == Some(outlet.address.path.as_str()))
        .unwrap();
    assert_eq!(loaded_eq.ifc_global_id.as_deref(), Some(after_assign.as_str()));
}

#[test]
fn ifc_type_from_address_leaf() {
    let mut eq = Equipment::new("x".into(), String::new(), EquipmentType::Electrical);
    eq.address = Some(
        ArxAddress::from_path("bldg.us.fl.tampa.dale-mabry.143677.s2/elec/panel.l1/ckt.14/rec.1")
            .unwrap(),
    );
    assert_eq!(ifc_product_type_for_equipment(&eq), "IFCOUTLET");
    eq.address = Some(
        ArxAddress::from_path("bldg.us.fl.tampa.dale-mabry.143677.s2/elec/ltg.hall").unwrap(),
    );
    assert_eq!(ifc_product_type_for_equipment(&eq), "IFCLIGHTFIXTURE");
    eq.address = Some(
        ArxAddress::from_path("bldg.us.fl.tampa.dale-mabry.143677.s2/elec/sw.a").unwrap(),
    );
    assert_eq!(ifc_product_type_for_equipment(&eq), "IFCSWITCHINGDEVICE");
}
