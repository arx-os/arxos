//! Vendor / third-party IFC interop goldens (Track B).
//!
//! Uses checked-in samples under `test_data/` as stand-ins until anonymized
//! Revit/ArchiCAD fixtures are licensed. Goal: **no panic**, structure counts,
//! optional re-export when validation is clean.
//!
//! See `docs/ifc-limitations.md`.

use arxos::export::ifc::IFCExporter;
use arxos::ingest::import_ifc_path;
use arxos::persistence::{load_building_at, save_building_at, BUILDING_YAML};
use arxos::validation::validate_building;
use serial_test::serial;
use std::path::{Path, PathBuf};
use tempfile::tempdir;

fn fixture(rel: &str) -> Option<PathBuf> {
    let root = PathBuf::from(env!("CARGO_MANIFEST_DIR"));
    let p = root.join(rel);
    if p.exists() {
        Some(p)
    } else {
        None
    }
}

/// SketchUp IFC-manager export (IFC4) — third-party toolchain stand-in.
#[test]
#[serial]
fn vendor_sketchup_architecture_import_no_panic() {
    let Some(path) = fixture("test_data/Building-Architecture.ifc") else {
        eprintln!("skip: Building-Architecture.ifc missing");
        return;
    };
    run_vendor_import(&path, "sketchup-architecture");
}

/// HVAC sample IFC — systems-oriented third-party-ish fixture.
#[test]
#[serial]
fn vendor_hvac_import_no_panic() {
    let Some(path) = fixture("test_data/Building-Hvac.ifc") else {
        eprintln!("skip: Building-Hvac.ifc missing");
        return;
    };
    run_vendor_import(&path, "hvac-sample");
}

/// Arx-authored minimal sample — always expected to validate + round-trip.
#[test]
#[serial]
fn vendor_arx_sample_full_round_trip() {
    let Some(path) = fixture("test_data/sample_building.ifc") else {
        eprintln!("skip: sample_building.ifc missing");
        return;
    };
    let result = import_ifc_path(&path, None, false, true).expect("import sample");
    assert!(
        !result.validation.has_errors(),
        "Arx sample must validate: {:?}",
        result.summary_lines()
    );
    let tmp = tempdir().expect("tmp");
    save_building_at(tmp.path(), &result.building).expect("save");
    let building = load_building_at(tmp.path()).expect("load");
    assert!(!validate_building(&building).has_errors());
    let out = tmp.path().join("out.ifc");
    IFCExporter::new(building.clone())
        .export(&out)
        .expect("export");
    let re = import_ifc_path(&out, None, false, true).expect("reimport");
    assert!(!re.validation.has_errors());
    assert_eq!(re.building.floors.len(), building.floors.len());
}

fn run_vendor_import(path: &Path, label: &str) {
    let result = import_ifc_path(path, None, false, true)
        .unwrap_or_else(|e| panic!("{} import panicked/failed: {}", label, e));

    // Structure visibility for limitations table / CI logs
    println!(
        "[{}] floors={} validation_errors={} warnings~={}",
        label,
        result.building.floors.len(),
        result.validation.errors().count(),
        result.report.warnings.len()
    );

    // Persist only when clean (mirrors production writers)
    if result.validation.has_errors() {
        println!(
            "[{}] not writing SSOT (validation errors) — still no panic OK",
            label
        );
        return;
    }

    let tmp = tempdir().expect("tmp");
    save_building_at(tmp.path(), &result.building).expect("save building.yaml");
    assert!(tmp.path().join(BUILDING_YAML).exists());

    let out = tmp.path().join(format!("{}.ifc", label));
    IFCExporter::new(result.building.clone())
        .export(&out)
        .expect("export");
    assert!(out.exists());

    let re = import_ifc_path(&out, None, false, true).expect("re-import");
    println!(
        "[{}] re-import floors={} (orig {})",
        label,
        re.building.floors.len(),
        result.building.floors.len()
    );
}
