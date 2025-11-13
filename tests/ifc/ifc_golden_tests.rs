use std::collections::HashMap;
use std::fs;
use std::path::PathBuf;

use arx::ifc::IFCProcessor;
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
struct EquipmentSummary {
    name: String,
    path: String,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
struct RoomSummary {
    name: String,
    path: String,
    equipment: Vec<EquipmentSummary>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
struct FloorSummary {
    name: String,
    path: String,
    rooms: Vec<RoomSummary>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
struct BuildingSummary {
    building: BuildingHeader,
    floors: Vec<FloorSummary>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
struct BuildingHeader {
    name: String,
    path: String,
}

fn canonical_path(props: &HashMap<String, String>) -> String {
    props
        .get("canonical_path")
        .cloned()
        .expect("entity missing canonical_path")
}

fn load_fixture_path(relative: &str) -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .join(relative)
}

#[test]
fn simple_fixture_matches_golden_outputs() {
    let ifc_path = load_fixture_path("tests/fixtures/ifc/simple.ifc");
    let processor = IFCProcessor::new();
    let (building, _floors) = processor
        .extract_hierarchy(ifc_path.to_str().unwrap())
        .expect("failed to extract hierarchy");

    let building_path = building.path.clone();

    let floor_summaries: Vec<FloorSummary> = building
        .floors
        .iter()
        .map(|floor| {
            let rooms: Vec<RoomSummary> = floor
                .wings
                .iter()
                .flat_map(|wing| wing.rooms.iter())
                .map(|room| {
                    let equipment: Vec<EquipmentSummary> = room
                        .equipment
                        .iter()
                        .map(|equip| EquipmentSummary {
                            name: equip.name.clone(),
                            path: equip.path.clone(),
                        })
                        .collect();

                    RoomSummary {
                        name: room.name.clone(),
                        path: canonical_path(&room.properties),
                        equipment,
                    }
                })
                .collect();

            FloorSummary {
                name: floor.name.clone(),
                path: canonical_path(&floor.properties),
                rooms,
            }
        })
        .collect();

    let summary = BuildingSummary {
        building: BuildingHeader {
            name: building.name.clone(),
            path: building_path,
        },
        floors: floor_summaries,
    };

    let golden_json_path = load_fixture_path("tests/fixtures/golden/simple_building.json");
    let golden_json: BuildingSummary =
        serde_json::from_str(&fs::read_to_string(golden_json_path).unwrap()).unwrap();

    let golden_yaml_path = load_fixture_path("tests/fixtures/golden/simple_building.yaml");
    let golden_yaml: BuildingSummary =
        serde_yaml::from_str(&fs::read_to_string(golden_yaml_path).unwrap()).unwrap();

    assert_eq!(summary, golden_json, "JSON golden mismatch");
    assert_eq!(summary, golden_yaml, "YAML golden mismatch");
}

