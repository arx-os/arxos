//! Integration: postal-derived building roots on init/import path.

use arxos::core::domain::{
    derive_building_root_from_str, postal_building_root_from_str, resolve_building_root_from_options,
};
use arxos::core::operations::address_nav::{list_children, resolve};
use arxos::ifc::IFCProcessor;
use arxos::persistence::{load_building_at, save_building_at};
use serial_test::serial;
use std::path::PathBuf;
use tempfile::tempdir;

const DALE_MABRY: &str = "143677 N. Dale Mabry Hwy, Suite 2, Tampa, FL, 33622";
const EXPECTED_ROOT: &str = "bldg.us.fl.tampa.dale-mabry.143677.s2";

#[test]
fn dale_mabry_root_string() {
    assert_eq!(
        derive_building_root_from_str(DALE_MABRY).unwrap(),
        EXPECTED_ROOT
    );
}

#[test]
#[serial]
fn import_with_postal_roots_hierarchy() {
    let fixture = PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .join("tests/fixtures/ifc/simple.ifc");
    if !fixture.exists() {
        eprintln!("skip: simple.ifc missing");
        return;
    }

    let root = postal_building_root_from_str(DALE_MABRY).unwrap();
    assert_eq!(root.path, format!("/{}", EXPECTED_ROOT));

    let processor = IFCProcessor::new();
    let parsed = processor
        .parse_native_with_root(fixture.to_str().unwrap(), false, Some(root.clone()))
        .expect("parse with postal root");

    let b = &parsed.building;
    assert_eq!(
        b.address.as_ref().map(|a| a.path.as_str()),
        Some(root.path.as_str())
    );

    // Floors under postal root
    for floor in &b.floors {
        if let Some(ref a) = floor.address {
            assert!(
                a.path.starts_with(&format!("{}/", root.path)),
                "floor address {} not under {}",
                a.path,
                root.path
            );
        }
    }

    // Resolve / ls via address_nav
    let entity = resolve(b, &root.path).expect("show building");
    assert_eq!(entity.kind.as_str(), "building");
    let kids = list_children(b, &root.path).expect("ls root");
    assert!(!kids.is_empty(), "expected floors under postal root");

    // Persist and reload
    let tmp = tempdir().unwrap();
    save_building_at(tmp.path(), b).unwrap();
    let loaded = load_building_at(tmp.path()).unwrap();
    assert_eq!(
        loaded.address.as_ref().unwrap().path,
        format!("/{}", EXPECTED_ROOT)
    );
}

#[test]
fn resolve_options_freeform_and_structured() {
    let a = resolve_building_root_from_options(
        Some(DALE_MABRY),
        None,
        None,
        None,
        None,
        None,
        None,
    )
    .unwrap()
    .unwrap();
    assert_eq!(a.path, format!("/{}", EXPECTED_ROOT));

    let b = resolve_building_root_from_options(
        None,
        Some("us"),
        Some("fl"),
        Some("tampa"),
        Some("Dale Mabry"),
        Some("143677"),
        Some("s2"),
    )
    .unwrap()
    .unwrap();
    assert_eq!(b.path, format!("/{}", EXPECTED_ROOT));

    let none = resolve_building_root_from_options(None, None, None, None, None, None, None)
        .unwrap();
    assert!(none.is_none());
}

#[test]
fn lab_root_still_default_without_postal() {
    let root = arxos::core::domain::ArxAddress::lab_building_root("duplex");
    assert!(root.path.starts_with("/bldg.lab.local.sample."));
}
