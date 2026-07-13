//! Human review status for auto-detected (LiDAR) structure.
//!
//! Track C1/C2: auto entities start as `proposed`; pilot teams accept/reject
//! via text DSL (`set room X review_status=accepted`) before approved IFC export.

use std::collections::HashMap;

use crate::core::{Building, Equipment, Room};

/// Property key on room/equipment free-form bags.
pub const PROP_REVIEW_STATUS: &str = "review_status";

/// Review lifecycle for automated structure.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ReviewStatus {
    /// Auto-detected; not yet human-approved.
    Proposed,
    /// Human accepted for export / pilot handoff.
    Accepted,
    /// Human rejected; strip under `--approved-only`.
    Rejected,
}

impl ReviewStatus {
    pub fn as_str(self) -> &'static str {
        match self {
            ReviewStatus::Proposed => "proposed",
            ReviewStatus::Accepted => "accepted",
            ReviewStatus::Rejected => "rejected",
        }
    }

    pub fn parse(s: &str) -> Option<Self> {
        match s.trim().to_ascii_lowercase().as_str() {
            "proposed" | "proposal" | "auto" => Some(ReviewStatus::Proposed),
            "accepted" | "approved" | "ok" => Some(ReviewStatus::Accepted),
            "rejected" | "reject" | "no" => Some(ReviewStatus::Rejected),
            _ => None,
        }
    }
}

/// Read review status from a properties bag.
pub fn review_status_from_props(props: &HashMap<String, String>) -> Option<ReviewStatus> {
    props
        .get(PROP_REVIEW_STATUS)
        .and_then(|s| ReviewStatus::parse(s))
}

/// Mark entity as auto-proposed (call when LiDAR creates structure).
pub fn mark_proposed(props: &mut HashMap<String, String>) {
    props.insert(
        PROP_REVIEW_STATUS.to_string(),
        ReviewStatus::Proposed.as_str().to_string(),
    );
}

/// Whether this room needs human review before "approved" IFC (has LiDAR signal).
pub fn room_needs_review(room: &Room) -> bool {
    room.lidar_enrichment.is_some()
        || review_status_from_props(&room.properties) == Some(ReviewStatus::Proposed)
}

/// Whether this equipment needs human review.
pub fn equipment_needs_review(eq: &Equipment) -> bool {
    eq.lidar_enrichment.is_some()
        || review_status_from_props(&eq.properties) == Some(ReviewStatus::Proposed)
}

/// Effective review status for a LiDAR-touched room (defaults to proposed if enrichment present).
pub fn room_review_status(room: &Room) -> Option<ReviewStatus> {
    if let Some(s) = review_status_from_props(&room.properties) {
        return Some(s);
    }
    if room.lidar_enrichment.is_some() {
        return Some(ReviewStatus::Proposed);
    }
    None
}

/// Effective review status for equipment.
pub fn equipment_review_status(eq: &Equipment) -> Option<ReviewStatus> {
    if let Some(s) = review_status_from_props(&eq.properties) {
        return Some(s);
    }
    if eq.lidar_enrichment.is_some() {
        return Some(ReviewStatus::Proposed);
    }
    None
}

/// Summary of unreviewed / rejected auto structure in a building.
#[derive(Debug, Clone, Default)]
pub struct ReviewSummary {
    pub proposed_rooms: Vec<String>,
    pub proposed_equipment: Vec<String>,
    pub rejected_rooms: Vec<String>,
    pub rejected_equipment: Vec<String>,
}

impl ReviewSummary {
    pub fn has_unreviewed(&self) -> bool {
        !self.proposed_rooms.is_empty() || !self.proposed_equipment.is_empty()
    }

    pub fn has_rejected(&self) -> bool {
        !self.rejected_rooms.is_empty() || !self.rejected_equipment.is_empty()
    }

    pub fn warning_lines(&self) -> Vec<String> {
        let mut lines = Vec::new();
        for n in &self.proposed_rooms {
            lines.push(format!(
                "warn: room '{}' has LiDAR auto-structure with review_status=proposed (accept/reject before pilot handoff)",
                n
            ));
        }
        for n in &self.proposed_equipment {
            lines.push(format!(
                "warn: equipment '{}' has LiDAR auto-structure with review_status=proposed",
                n
            ));
        }
        for n in &self.rejected_rooms {
            lines.push(format!(
                "info: room '{}' is review_status=rejected (excluded under --approved-only)",
                n
            ));
        }
        for n in &self.rejected_equipment {
            lines.push(format!(
                "info: equipment '{}' is review_status=rejected (excluded under --approved-only)",
                n
            ));
        }
        lines
    }
}

/// Scan building for review-related entities.
pub fn summarize_review(building: &Building) -> ReviewSummary {
    let mut s = ReviewSummary::default();
    for floor in &building.floors {
        for eq in &floor.equipment {
            match equipment_review_status(eq) {
                Some(ReviewStatus::Proposed) => s.proposed_equipment.push(eq.name.clone()),
                Some(ReviewStatus::Rejected) => s.rejected_equipment.push(eq.name.clone()),
                _ => {}
            }
        }
        for wing in &floor.wings {
            for eq in &wing.equipment {
                match equipment_review_status(eq) {
                    Some(ReviewStatus::Proposed) => s.proposed_equipment.push(eq.name.clone()),
                    Some(ReviewStatus::Rejected) => s.rejected_equipment.push(eq.name.clone()),
                    _ => {}
                }
            }
            for room in &wing.rooms {
                match room_review_status(room) {
                    Some(ReviewStatus::Proposed) => s.proposed_rooms.push(room.name.clone()),
                    Some(ReviewStatus::Rejected) => s.rejected_rooms.push(room.name.clone()),
                    _ => {}
                }
                for eq in &room.equipment {
                    match equipment_review_status(eq) {
                        Some(ReviewStatus::Proposed) => s.proposed_equipment.push(eq.name.clone()),
                        Some(ReviewStatus::Rejected) => s.rejected_equipment.push(eq.name.clone()),
                        _ => {}
                    }
                }
            }
        }
    }
    s
}

fn keep_equipment(eq: &Equipment, approved_only: bool) -> bool {
    match equipment_review_status(eq) {
        Some(ReviewStatus::Rejected) => false,
        Some(ReviewStatus::Proposed) if approved_only => false,
        _ => true,
    }
}

fn keep_room(room: &Room, approved_only: bool) -> bool {
    match room_review_status(room) {
        Some(ReviewStatus::Rejected) => false,
        Some(ReviewStatus::Proposed) if approved_only => false,
        _ => true,
    }
}

/// Filter a building for IFC export.
///
/// - Always drops `rejected` LiDAR/auto entities.
/// - When `approved_only`, also drops `proposed` (unreviewed) auto entities.
/// - Entities without LiDAR/review tags are always kept.
pub fn filter_building_for_export(building: &Building, approved_only: bool) -> Building {
    let mut out = building.clone();
    for floor in &mut out.floors {
        floor
            .equipment
            .retain(|eq| keep_equipment(eq, approved_only));
        for wing in &mut floor.wings {
            wing.equipment
                .retain(|eq| keep_equipment(eq, approved_only));
            wing.rooms.retain(|room| keep_room(room, approved_only));
            for room in &mut wing.rooms {
                room.equipment
                    .retain(|eq| keep_equipment(eq, approved_only));
            }
        }
    }
    out
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::core::{Floor, LidarEnrichment, RoomType, Wing};

    #[test]
    fn mark_and_parse_review_status() {
        let mut props = HashMap::new();
        mark_proposed(&mut props);
        assert_eq!(
            review_status_from_props(&props),
            Some(ReviewStatus::Proposed)
        );
        props.insert(PROP_REVIEW_STATUS.into(), "accepted".into());
        assert_eq!(
            review_status_from_props(&props),
            Some(ReviewStatus::Accepted)
        );
    }

    #[test]
    fn filter_drops_rejected_and_optional_proposed() {
        let mut building = Building::new("R".into(), "/r".into());
        let mut floor = Floor::new("G".into(), 0);
        let mut wing = Wing::new("M".into());

        let mut proposed = Room::new("AutoRoom".into(), RoomType::Office);
        proposed.lidar_enrichment = Some(LidarEnrichment {
            point_count: 10,
            confidence_score: 0.9,
            last_scan_timestamp: None,
            classification_heuristic: Some("rule".into()),
        });
        mark_proposed(&mut proposed.properties);

        let mut rejected = Room::new("BadRoom".into(), RoomType::Storage);
        rejected
            .properties
            .insert(PROP_REVIEW_STATUS.into(), "rejected".into());

        let ok = Room::new("ManualRoom".into(), RoomType::Office);

        wing.add_room(proposed);
        wing.add_room(rejected);
        wing.add_room(ok);
        floor.add_wing(wing);
        building.add_floor(floor);

        let default_export = filter_building_for_export(&building, false);
        let names: Vec<_> = default_export.floors[0].wings[0]
            .rooms
            .iter()
            .map(|r| r.name.as_str())
            .collect();
        assert!(names.contains(&"AutoRoom"));
        assert!(names.contains(&"ManualRoom"));
        assert!(!names.contains(&"BadRoom"));

        let approved = filter_building_for_export(&building, true);
        let names: Vec<_> = approved.floors[0].wings[0]
            .rooms
            .iter()
            .map(|r| r.name.as_str())
            .collect();
        assert!(!names.contains(&"AutoRoom"));
        assert!(names.contains(&"ManualRoom"));
        assert!(!names.contains(&"BadRoom"));
    }

    #[test]
    fn summarize_finds_proposed() {
        let mut building = Building::new("R".into(), "/r".into());
        let mut floor = Floor::new("G".into(), 0);
        let mut wing = Wing::new("M".into());
        let mut room = Room::new("ScanRoom".into(), RoomType::Office);
        room.lidar_enrichment = Some(LidarEnrichment {
            point_count: 1,
            confidence_score: 0.5,
            last_scan_timestamp: None,
            classification_heuristic: None,
        });
        wing.add_room(room);
        floor.add_wing(wing);
        building.add_floor(floor);

        let s = summarize_review(&building);
        assert!(s.has_unreviewed());
        assert_eq!(s.proposed_rooms, vec!["ScanRoom".to_string()]);
    }
}
