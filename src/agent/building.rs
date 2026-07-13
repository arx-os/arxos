//! Read-only building snapshot for PWA review (Batch B1).
//!
//! Thin wrapper around `load_building_at` + `summarize_review` — no IFC spine changes.

use std::path::Path;

use anyhow::{anyhow, Result};
use serde::Serialize;

use crate::core::review::{equipment_review_status, room_review_status, ReviewStatus};
use crate::core::{summarize_review, Building};
use crate::persistence::{load_building_at, BUILDING_YAML};

/// JSON result for `building.get`.
#[derive(Debug, Serialize)]
pub struct BuildingGetResult {
    pub building: Building,
    pub yaml_path: String,
    /// Human-readable review warning lines (proposed / rejected LiDAR autos).
    pub review_warnings: Vec<String>,
    pub proposed_rooms: usize,
    pub proposed_equipment: usize,
    pub floors: usize,
    pub rooms: usize,
    pub equipment: usize,
}

/// Load durable `building.yaml` and attach review summary for the phone Review UI.
pub fn get_building(repo_root: &Path) -> Result<BuildingGetResult> {
    let building = load_building_at(repo_root)
        .map_err(|e| anyhow!("Failed to load {}: {}", BUILDING_YAML, e))?;

    let summary = summarize_review(&building);
    let proposed_rooms = building
        .get_all_rooms()
        .iter()
        .filter(|r| room_review_status(r) == Some(ReviewStatus::Proposed))
        .count();
    let proposed_equipment = building
        .get_all_equipment()
        .iter()
        .filter(|e| equipment_review_status(e) == Some(ReviewStatus::Proposed))
        .count();
    let rooms = building.get_all_rooms().len();
    let equipment = building.get_all_equipment().len();
    let floors = building.floors.len();
    let review_warnings = summary.warning_lines();

    Ok(BuildingGetResult {
        building,
        yaml_path: BUILDING_YAML.to_string(),
        review_warnings,
        proposed_rooms,
        proposed_equipment,
        floors,
        rooms,
        equipment,
    })
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::core::{mark_proposed, Building, Floor, Room, RoomType, Wing};
    use crate::persistence::save_building_at;
    use tempfile::tempdir;

    #[test]
    fn get_building_counts_proposed() {
        let dir = tempdir().unwrap();
        let mut b = Building::new("Pilot".into(), "/pilot".into());
        let mut floor = Floor::new("L1".into(), 0);
        let mut wing = Wing::new("A".into());
        let mut room = Room::new("Scan Room".into(), RoomType::Office);
        mark_proposed(&mut room.properties);
        wing.add_room(room);
        floor.add_wing(wing);
        b.add_floor(floor);
        save_building_at(dir.path(), &b).unwrap();

        let got = get_building(dir.path()).unwrap();
        assert_eq!(got.proposed_rooms, 1);
        assert_eq!(got.rooms, 1);
        assert_eq!(got.building.name, "Pilot");
        assert!(!got.review_warnings.is_empty());
    }
}
