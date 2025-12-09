use std::fs;
use std::path::PathBuf;

use arx::ifc::IFCProcessor;
use arx::yaml::BuildingYamlSerializer;
use arxos::render::BuildingRenderer;
use arxos::export::ar::gltf::GLTFExporter;
use tempfile::tempdir;

fn load_fixture_path(relative: &str) -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR")).join(relative)
}

fn building_data_from_fixture() -> arx::yaml::BuildingData {
    let ifc_path = load_fixture_path("tests/fixtures/ifc/simple.ifc");
    let processor = IFCProcessor::new();
    let (building, _floors) = processor
        .extract_hierarchy(ifc_path.to_str().unwrap())
        .expect("failed to extract hierarchy");

    BuildingYamlSerializer::new()
        .serialize_building(&building, &[], None)
        .expect("failed to serialize building data")
}

#[test]
fn gltf_export_contains_expected_nodes() {
    let building_data = building_data_from_fixture();
    let exporter = GLTFExporter::new(&building_data);
    let dir = tempdir().unwrap();
    let gltf_path = dir.path().join("simple.gltf");

    exporter
        .export(&gltf_path)
        .expect("GLTF export should succeed");

    let gltf_output = fs::read_to_string(&gltf_path).expect("failed to read glTF output");
    assert!(
        gltf_output.contains("\"name\": \"VAV-301\""),
        "exported glTF should contain equipment node"
    );
    assert!(
        gltf_output.contains("\"nodes\""),
        "exported glTF should define nodes section"
    );
}

#[test]
fn building_renderer_renders_floor_without_error() {
    let building_data = building_data_from_fixture();
    let renderer = BuildingRenderer::new(building_data.clone());
    let first_floor_level = building_data
        .floors
        .first()
        .map(|floor| floor.level)
        .expect("fixture should contain at least one floor");

    renderer
        .render_floor(first_floor_level)
        .expect("rendering should succeed");
}

