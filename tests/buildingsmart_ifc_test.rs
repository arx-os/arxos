//! buildingSMART Sample-Test-Files (small ISO RV subset).
//!
//! Checked-in under `tests/fixtures/ifc/buildingsmart/` with attribution README.
//! Goals: **no panic**, import completes, LossReport surfaces unmapped products when present.

use arxos::export::ifc::IFCExporter;
use arxos::ingest::import_ifc_path;
use serial_test::serial;
use std::path::PathBuf;
use tempfile::tempdir;

fn fixture(name: &str) -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .join("tests/fixtures/ifc/buildingsmart")
        .join(name)
}

#[test]
#[serial]
fn buildingsmart_basin_import_no_panic() {
    let path = fixture("basin-tessellation.ifc");
    assert!(path.exists(), "missing fixture {:?}", path);
    let result = import_ifc_path(&path, None, false, true).expect("import basin");
    // May warn about empty floors — must not error fatally for non-strict.
    assert!(
        result
            .report
            .warnings
            .iter()
            .any(|w| w.code == "no_storeys" || w.code == "building.floors.empty")
            || !result.building.floors.is_empty()
            || result.report.warnings.iter().any(|w| w.code == "no_building"),
        "expected empty-hierarchy or no_storeys warning; got {:?}",
        result.report.warnings
    );
}

#[test]
#[serial]
fn buildingsmart_wall_opening_import_reports_unmapped_products() {
    let path = fixture("wall-with-opening-and-window.ifc");
    assert!(path.exists(), "missing fixture {:?}", path);
    let result = import_ifc_path(&path, None, false, true).expect("import wall sample");

    // File contains IFCWALL / opening products — must not claim clean mapping.
    let unmapped = result
        .report
        .warnings
        .iter()
        .find(|w| w.code == "unmapped_products");
    assert!(
        unmapped.is_some(),
        "expected unmapped_products warning for wall sample; warnings={:?}",
        result.report.warnings
    );
    let msg = &unmapped.unwrap().message;
    assert!(
        msg.contains("IFCWALL") || msg.contains("IFCWINDOW") || msg.contains("IFCDOOR"),
        "unmapped message should cite wall/window/door classes: {}",
        msg
    );

    // Export must still succeed (spine health).
    let tmp = tempdir().expect("tmp");
    let out = tmp.path().join("out.ifc");
    IFCExporter::new(result.building)
        .export(&out)
        .expect("export");
    assert!(out.metadata().unwrap().len() > 0);
}

#[test]
#[serial]
fn test_mep_unmapped_loss_reporting() {
    let path = std::path::PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .join("tests/fixtures/ifc/buildingsmart/basin-tessellation.ifc");
    assert!(path.exists());
    let result = import_ifc_path(&path, None, false, true).expect("import basin");
    
    let unmapped = result
        .report
        .warnings
        .iter()
        .find(|w| w.code == "unmapped_products");
    assert!(
        unmapped.is_some(),
        "expected unmapped_products warning; got warnings={:?}",
        result.report.warnings
    );
    let msg = &unmapped.unwrap().message;
    assert!(
        msg.contains("IFCSANITARYTERMINAL"),
        "expected unmapped message to cite IFCSANITARYTERMINAL: {}",
        msg
    );
}
