//! Golden IFC compiler path: native parse → finalize → SSOT → validate → export.
//!
//! Uses `test_data/sample_building.ifc` when present.

use arxos::export::ifc::IFCExporter;
use arxos::ingest::import_ifc_path;
use arxos::persistence::{load_building_at, save_building_at, BUILDING_YAML};
use arxos::validation::validate_building;
use serial_test::serial;
use std::env;
use std::path::{Path, PathBuf};
use tempfile::tempdir;

fn sample_ifc() -> Option<PathBuf> {
    let candidates = [
        PathBuf::from("test_data/sample_building.ifc"),
        PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("test_data/sample_building.ifc"),
    ];
    candidates.into_iter().find(|p| p.exists())
}

#[test]
#[serial]
fn ifc_import_persist_validate_export_round_trip() {
    let Some(ifc_path) = sample_ifc() else {
        eprintln!("skip: test_data/sample_building.ifc not found");
        return;
    };

    let tmp = tempdir().expect("tempdir");
    let dir = tmp.path();

    // --- Import through ingest (native parse + finalize + validate report) ---
    let result = import_ifc_path(&ifc_path, None, false, true).expect("import_ifc_path");
    assert!(
        !result.building.floors.is_empty() || !result.validation.has_errors(),
        "expected floors or validation context; floors={} report={:?}",
        result.building.floors.len(),
        result.summary_lines()
    );

    // Hard gate: do not write invalid buildings
    if result.validation.has_errors() {
        // Sample fixture should be valid; fail loudly if not
        panic!("sample IFC failed validation: {:?}", result.summary_lines());
    }

    save_building_at(dir, &result.building).expect("write building.yaml");
    assert!(dir.join(BUILDING_YAML).exists());

    // --- Reload SSOT ---
    let building = load_building_at(dir).expect("reload building.yaml");
    let report = validate_building(&building);
    assert!(
        !report.has_errors(),
        "reloaded Building invalid: {:?}",
        report.summary_lines()
    );

    // --- Export IFC projection ---
    let out_ifc = dir.join("roundtrip.ifc");
    IFCExporter::new(building.clone())
        .export(&out_ifc)
        .expect("export ifc");
    assert!(out_ifc.exists());
    let content = std::fs::read_to_string(&out_ifc).expect("read export");
    assert!(content.contains("ISO-10303-21"));
    assert!(content.contains("END-ISO-10303-21"));

    // --- Re-import exported IFC (semantic, not byte-identical) ---
    let reimport = import_ifc_path(Path::new(&out_ifc), None, false, true).expect("re-import");
    assert!(
        !reimport.validation.has_errors(),
        "re-import validation failed: {:?}",
        reimport.summary_lines()
    );
    assert_eq!(
        reimport.building.floors.len(),
        building.floors.len(),
        "floor count should survive export→import"
    );
}

#[test]
#[serial]
fn ifc_import_writes_only_building_yaml_layout() {
    let Some(ifc_path) = sample_ifc() else {
        eprintln!("skip: test_data/sample_building.ifc not found");
        return;
    };
    // Absolute path before chdir (import reads the IFC file from disk)
    let ifc_path = ifc_path.canonicalize().unwrap_or(ifc_path);

    let tmp = tempdir().expect("tempdir");
    let dir = tmp.path();
    let original = env::current_dir().unwrap_or_else(|_| PathBuf::from("."));
    env::set_current_dir(dir).expect("chdir");

    let result = import_ifc_path(&ifc_path, None, false, true).expect("import");
    if result.validation.has_errors() {
        env::set_current_dir(original).ok();
        panic!("validation failed: {:?}", result.summary_lines());
    }

    arxos::persistence::save_building_at(".", &result.building).expect("save");

    // Single SSOT file — no multi-file floor/equipment shards
    let yaml_files: Vec<_> = std::fs::read_dir(".")
        .unwrap()
        .filter_map(|e| e.ok())
        .filter(|e| {
            e.path()
                .extension()
                .and_then(|x| x.to_str())
                .map(|x| x == "yaml" || x == "yml")
                .unwrap_or(false)
        })
        .map(|e| e.file_name().to_string_lossy().into_owned())
        .collect();

    assert_eq!(
        yaml_files,
        vec![BUILDING_YAML.to_string()],
        "expected only building.yaml, found {:?}",
        yaml_files
    );
    assert!(!Path::new("floors").exists(), "no sharded floors/ tree");

    env::set_current_dir(original).ok();
}
