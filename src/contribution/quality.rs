//! Quality metrics for contribution proofs (0–100), derived from the Building model.
//!
//! Not probabilistic ML confidence. Rule-based from validation + human review.

use crate::core::review::{equipment_review_status, room_review_status, ReviewStatus};
use crate::core::Building;
use crate::validation::validate_building;

/// Scores matching Solidity `QualityMetrics` (uint8 accuracy, completeness).
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct QualityScores {
    pub accuracy: u8,
    pub completeness: u8,
}

/// Derive quality from validation report + LiDAR review coverage.
///
/// | Signal | Effect |
/// | :--- | :--- |
/// | Validation errors | accuracy = 0 |
/// | Validation warnings only | accuracy capped at 70 |
/// | Clean validation | accuracy base 100 |
/// | LiDAR entities still `proposed` | accuracy reduced by unreviewed fraction |
/// | Completeness | floors/rooms present + equipment address fill rate |
pub fn quality_from_building(building: &Building) -> QualityScores {
    let report = validate_building(building);

    let mut accuracy: u16 = if report.has_errors() {
        0
    } else if report.warnings().count() > 0 {
        70
    } else {
        100
    };

    let (lidar_total, lidar_accepted, lidar_proposed) = lidar_review_counts(building);
    if lidar_total > 0 && accuracy > 0 {
        // Unreviewed (proposed) auto structure pulls accuracy down.
        let reviewed_ok = lidar_total.saturating_sub(lidar_proposed);
        let ratio = (reviewed_ok as f64) / (lidar_total as f64);
        accuracy = ((accuracy as f64) * (0.5 + 0.5 * ratio)).round() as u16;
        // Accepted-only bonus already in ratio; rejected counts as reviewed (not proposed).
        let _ = lidar_accepted;
    }

    let completeness = completeness_score(building);

    QualityScores {
        accuracy: accuracy.min(100) as u8,
        completeness,
    }
}

fn lidar_review_counts(building: &Building) -> (usize, usize, usize) {
    let mut total = 0;
    let mut accepted = 0;
    let mut proposed = 0;

    for floor in &building.floors {
        for eq in &floor.equipment {
            tally_equipment(eq, &mut total, &mut accepted, &mut proposed);
        }
        for wing in &floor.wings {
            for room in &wing.rooms {
                tally_room(room, &mut total, &mut accepted, &mut proposed);
                for eq in &room.equipment {
                    tally_equipment(eq, &mut total, &mut accepted, &mut proposed);
                }
            }
            for eq in &wing.equipment {
                tally_equipment(eq, &mut total, &mut accepted, &mut proposed);
            }
        }
    }

    (total, accepted, proposed)
}

fn tally_room(
    room: &crate::core::Room,
    total: &mut usize,
    accepted: &mut usize,
    proposed: &mut usize,
) {
    if room.lidar_enrichment.is_none() && room_review_status(room).is_none() {
        return;
    }
    *total += 1;
    match room_review_status(room) {
        Some(ReviewStatus::Accepted) => *accepted += 1,
        Some(ReviewStatus::Proposed) => *proposed += 1,
        Some(ReviewStatus::Rejected) => {}
        None if room.lidar_enrichment.is_some() => *proposed += 1,
        None => {}
    }
}

fn tally_equipment(
    eq: &crate::core::Equipment,
    total: &mut usize,
    accepted: &mut usize,
    proposed: &mut usize,
) {
    if eq.lidar_enrichment.is_none() && equipment_review_status(eq).is_none() {
        return;
    }
    *total += 1;
    match equipment_review_status(eq) {
        Some(ReviewStatus::Accepted) => *accepted += 1,
        Some(ReviewStatus::Proposed) => *proposed += 1,
        Some(ReviewStatus::Rejected) => {}
        None if eq.lidar_enrichment.is_some() => *proposed += 1,
        None => {}
    }
}

fn completeness_score(building: &Building) -> u8 {
    if building.name.trim().is_empty() || building.id.trim().is_empty() {
        return 0;
    }
    if building.floors.is_empty() {
        return 20;
    }

    let mut room_count = 0usize;
    let mut equip_count = 0usize;
    let mut addressed = 0usize;

    for floor in &building.floors {
        equip_count += floor.equipment.len();
        addressed += floor.equipment.iter().filter(|e| e.address.is_some()).count();
        for wing in &floor.wings {
            room_count += wing.rooms.len();
            equip_count += wing.equipment.len();
            addressed += wing.equipment.iter().filter(|e| e.address.is_some()).count();
            for room in &wing.rooms {
                equip_count += room.equipment.len();
                addressed += room.equipment.iter().filter(|e| e.address.is_some()).count();
            }
        }
    }

    let mut score: u16 = 40; // has floors
    if room_count > 0 {
        score += 30;
    }
    if equip_count == 0 {
        score += 30; // empty equipment is complete for structure-only
    } else {
        let fill = (addressed as f64) / (equip_count as f64);
        score += (30.0 * fill).round() as u16;
    }

    score.min(100) as u8
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::core::review::mark_proposed;
    use crate::core::{Floor, LidarEnrichment, Room, RoomType, Wing};

    #[test]
    fn clean_minimal_building_has_nonzero_quality() {
        let mut b = Building::new("Q".into(), "/q".into());
        b.add_floor(Floor::new("G".into(), 0));
        let q = quality_from_building(&b);
        assert!(q.completeness >= 40);
        assert!(q.accuracy > 0);
    }

    #[test]
    fn proposed_lidar_lowers_accuracy() {
        let mut b = Building::new("Q".into(), "/q".into());
        let mut floor = Floor::new("G".into(), 0);
        let mut wing = Wing::new("M".into());
        let mut room = Room::new("Auto".into(), RoomType::Office);
        room.lidar_enrichment = Some(LidarEnrichment {
            point_count: 10,
            confidence_score: 0.9,
            last_scan_timestamp: None,
            classification_heuristic: Some("rule".into()),
        });
        mark_proposed(&mut room.properties);
        wing.add_room(room);
        floor.add_wing(wing);
        b.add_floor(floor);

        let q = quality_from_building(&b);
        // base may be 70 (empty floor warning) or 100; proposed pulls toward 0.5x
        assert!(q.accuracy < 100);
    }
}
