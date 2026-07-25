//! Integration: `add_under_address` + persist + resolve.

use arxos::core::domain::ArxAddress;
use arxos::core::operations::address_mutate::{add_under_address, AddKind};
use arxos::core::operations::address_nav::{list_children, resolve};
use arxos::core::{Building, Equipment, EquipmentType, Floor, Room, RoomType, Wing};
use arxos::ingest::persist_building_at;
use arxos::persistence::load_building_at;
use serial_test::serial;
use tempfile::tempdir;

fn seeded_building() -> Building {
    let root = ArxAddress::from_path("bldg.us.fl.tampa.dale-mabry.143677.s2").unwrap();
    let mut b = Building::new("HQ".into(), "/hq".into());
    b.address = Some(root.clone());
    let mut floor = Floor::new("Level 1".into(), 1);
    floor.address = Some(root.join("fl.1").unwrap());
    let mut wing = Wing::new("Main".into());
    let mut room = Room::new("A101".into(), RoomType::Office);
    room.address = Some(floor.address.as_ref().unwrap().join("rm.a101").unwrap());
    let mut existing =
        Equipment::new("Outlet 1".into(), String::new(), EquipmentType::Electrical);
    existing.address = Some(
        root.join("elec")
            .unwrap()
            .join("panel.l1")
            .unwrap()
            .join("ckt.14")
            .unwrap()
            .join("rec.1")
            .unwrap(),
    );
    existing.ifc_global_id = Some("ExistingGid00000000001".into());
    room.add_equipment(existing);
    wing.add_room(room);
    floor.add_wing(wing);
    b.add_floor(floor);
    b
}

#[test]
#[serial]
fn add_outlet_persists_and_browse_sees_it() {
    let tmp = tempdir().unwrap();
    let mut b = seeded_building();
    let r = add_under_address(
        &mut b,
        "bldg.us.fl.tampa.dale-mabry.143677.s2/elec/panel.l1/ckt.14",
        AddKind::Outlet,
        None,
    )
    .unwrap();
    assert!(r.address.path.ends_with("/rec.2"));

    persist_building_at(tmp.path(), b, false, Some("test add")).unwrap();
    let loaded = load_building_at(tmp.path()).unwrap();

    let entity = resolve(&loaded, &r.address.path).unwrap();
    assert_eq!(entity.kind.as_str(), "equipment");
    assert!(entity.ifc_global_id.is_none() || entity.ifc_global_id.as_deref() == Some(""));

    // Pre-existing keeps GlobalId
    let old = resolve(
        &loaded,
        "bldg.us.fl.tampa.dale-mabry.143677.s2/elec/panel.l1/ckt.14/rec.1",
    )
    .unwrap();
    assert_eq!(old.ifc_global_id.as_deref(), Some("ExistingGid00000000001"));

    let kids = list_children(
        &loaded,
        "bldg.us.fl.tampa.dale-mabry.143677.s2/elec/panel.l1/ckt.14",
    )
    .unwrap();
    assert!(kids.iter().any(|c| c.address.path.ends_with("/rec.2")));
}

#[test]
fn reject_unknown_parent() {
    let mut b = seeded_building();
    let err = add_under_address(&mut b, "bldg.us.fl.tampa.nope/elec", AddKind::Outlet, None);
    assert!(err.is_err());
}
