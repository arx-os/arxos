//! Contribution spine: Building → validated commitment package (reward path).
//!
//! On-chain oracle submit remains a follow-on under `--features blockchain` + Anvil.

use arxos::contribution::{build_contribution_package, commit_building, PackageOptions};
use arxos::core::{Building, Floor, Room, RoomType, Wing};
use arxos::persistence::{load_building_at, save_building_at, BUILDING_YAML};
use arxos::validation::validate_building;
use serial_test::serial;
use std::env;
use std::path::PathBuf;
use tempfile::tempdir;

#[test]
#[serial]
fn building_to_contribution_package_round_trip() {
    let tmp = tempdir().expect("tmp");
    let dir = tmp.path();

    let mut building = Building::new("Reward HQ".into(), "/reward-hq".into());
    let mut floor = Floor::new("Ground".into(), 0);
    let mut wing = Wing::new("Main".into());
    wing.add_room(Room::new("Lobby".into(), RoomType::Hallway));
    floor.add_wing(wing);
    building.add_floor(floor);

    assert!(!validate_building(&building).has_errors());
    save_building_at(dir, &building).expect("save");

    let original = env::current_dir().unwrap_or_else(|_| PathBuf::from("."));
    env::set_current_dir(dir).expect("chdir");

    let loaded = load_building_at(".").expect("load");
    let c1 = commit_building(&loaded).expect("commit");
    let c2 = commit_building(&loaded).expect("commit again");
    assert_eq!(c1.merkle_root, c2.merkle_root);

    let pkg = build_contribution_package(
        &loaded,
        PackageOptions {
            latitude: 40.7128,
            longitude: -74.0060,
            git_commit: Some("deadbeef".into()),
            require_clean_validation: true,
        },
    )
    .expect("package");

    assert_eq!(pkg.building_id, loaded.id);
    assert_eq!(pkg.merkle_root_hex.len(), 64);
    assert_eq!(pkg.git_commit.as_deref(), Some("deadbeef"));
    assert!(pkg.accuracy > 0);
    assert!(pkg.completeness > 0);
    assert!(pkg.location_hash_hex.is_some());

    let json = serde_json::to_string_pretty(&pkg).expect("json");
    std::fs::write(dir.join("contribution.json"), &json).expect("write");
    assert!(dir.join("contribution.json").exists());
    assert!(dir.join(BUILDING_YAML).exists());

    env::set_current_dir(original).ok();
}
