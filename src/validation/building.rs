//! Post-ingest validation of the canonical `Building` model.

use crate::core::Building;
use crate::ifc::mapping::COORD_BUILDING_LOCAL;

use super::rules::{ValidationResult, ValidationSeverity};

/// Aggregated validation outcome for a building after ingest.
#[derive(Debug, Clone, Default)]
pub struct BuildingValidationReport {
    pub results: Vec<ValidationResult>,
}

impl BuildingValidationReport {
    pub fn errors(&self) -> impl Iterator<Item = &ValidationResult> {
        self.results
            .iter()
            .filter(|r| r.severity == ValidationSeverity::Error)
    }

    pub fn warnings(&self) -> impl Iterator<Item = &ValidationResult> {
        self.results
            .iter()
            .filter(|r| r.severity == ValidationSeverity::Warning)
    }

    pub fn has_errors(&self) -> bool {
        self.errors().next().is_some()
    }

    pub fn is_clean(&self) -> bool {
        self.results.is_empty()
    }

    pub fn summary_lines(&self) -> Vec<String> {
        if self.results.is_empty() {
            return vec!["Validation: ok".to_string()];
        }
        let mut lines = vec![format!(
            "Validation: {} error(s), {} warning(s)",
            self.errors().count(),
            self.warnings().count()
        )];
        for r in &self.results {
            let sev = match r.severity {
                ValidationSeverity::Error => "error",
                ValidationSeverity::Warning => "warn",
                ValidationSeverity::Info => "info",
            };
            if let Some(ref f) = r.field {
                lines.push(format!("  - [{}] {} ({})", sev, r.message, f));
            } else {
                lines.push(format!("  - [{}] {}", sev, r.message));
            }
        }
        lines
    }
}

/// Validate structural and semantic invariants of a building after any ingest path.
pub fn validate_building(building: &Building) -> BuildingValidationReport {
    let mut report = BuildingValidationReport::default();

    if building.name.trim().is_empty() {
        report.results.push(ValidationResult {
            rule_id: "building.name.required".into(),
            message: "Building name must not be empty".into(),
            severity: ValidationSeverity::Error,
            field: Some("name".into()),
        });
    }

    if building.id.trim().is_empty() {
        report.results.push(ValidationResult {
            rule_id: "building.id.required".into(),
            message: "Building id must not be empty".into(),
            severity: ValidationSeverity::Error,
            field: Some("id".into()),
        });
    }

    if let Some(ref meta) = building.metadata {
        if !meta.coordinate_system.is_empty()
            && meta.coordinate_system != COORD_BUILDING_LOCAL
            && meta.coordinate_system != "World"
            && meta.coordinate_system != "LOCAL"
        {
            report.results.push(ValidationResult {
                rule_id: "building.coords.unknown".into(),
                message: format!(
                    "Unusual coordinate_system '{}' (expected {})",
                    meta.coordinate_system, COORD_BUILDING_LOCAL
                ),
                severity: ValidationSeverity::Warning,
                field: Some("metadata.coordinate_system".into()),
            });
        }
    }

    if building.floors.is_empty() {
        report.results.push(ValidationResult {
            rule_id: "building.floors.empty".into(),
            message: "Building has no floors".into(),
            severity: ValidationSeverity::Warning,
            field: Some("floors".into()),
        });
    }

    let mut seen_room_ids = std::collections::HashSet::new();
    let mut seen_eq_ids = std::collections::HashSet::new();

    for floor in &building.floors {
        if floor.name.trim().is_empty() {
            report.results.push(ValidationResult {
                rule_id: "floor.name.required".into(),
                message: "Floor name must not be empty".into(),
                severity: ValidationSeverity::Error,
                field: Some(format!("floor[{}].name", floor.level)),
            });
        }

        if floor.wings.is_empty() && floor.equipment.is_empty() {
            report.results.push(ValidationResult {
                rule_id: "floor.empty".into(),
                message: format!("Floor '{}' has no wings or equipment", floor.name),
                severity: ValidationSeverity::Info,
                field: Some(format!("floor[{}]", floor.name)),
            });
        }

        for wing in &floor.wings {
            for room in &wing.rooms {
                if room.name.trim().is_empty() {
                    report.results.push(ValidationResult {
                        rule_id: "room.name.required".into(),
                        message: "Room name must not be empty".into(),
                        severity: ValidationSeverity::Error,
                        field: Some(format!("{}/{}/room", floor.name, wing.name)),
                    });
                }

                if !seen_room_ids.insert(room.id.clone()) {
                    report.results.push(ValidationResult {
                        rule_id: "room.id.duplicate".into(),
                        message: format!("Duplicate room id {}", room.id),
                        severity: ValidationSeverity::Error,
                        field: Some(room.id.clone()),
                    });
                }

                if let Some(ref gid) = room.ifc_global_id {
                    if !(gid.len() == 22 || gid.is_empty()) {
                        // 22-char IFC compressed GUID, or empty/absent
                        if gid.len() != 22 {
                            report.results.push(ValidationResult {
                                rule_id: "room.ifc_global_id.format".into(),
                                message: format!(
                                    "Room '{}' ifc_global_id length {} (expected 22 for IFC GlobalId)",
                                    room.name,
                                    gid.len()
                                ),
                                severity: ValidationSeverity::Warning,
                                field: Some(format!("room[{}].ifc_global_id", room.name)),
                            });
                        }
                    }
                }

                let d = &room.spatial_properties.dimensions;
                if d.width < 0.0 || d.depth < 0.0 || d.height < 0.0 {
                    report.results.push(ValidationResult {
                        rule_id: "room.dimensions.negative".into(),
                        message: format!("Room '{}' has negative dimensions", room.name),
                        severity: ValidationSeverity::Error,
                        field: Some(format!("room[{}].dimensions", room.name)),
                    });
                }

                if !room.spatial_properties.bounding_box.is_valid() {
                    report.results.push(ValidationResult {
                        rule_id: "room.bbox.invalid".into(),
                        message: format!(
                            "Room '{}' has invalid bounding box (min > max)",
                            room.name
                        ),
                        severity: ValidationSeverity::Warning,
                        field: Some(format!("room[{}].bounding_box", room.name)),
                    });
                }

                if let Some(ref enr) = room.lidar_enrichment {
                    validate_enrichment(
                        &mut report,
                        &format!("room[{}]", room.name),
                        enr.confidence_score,
                        enr.point_count,
                    );
                }

                // Double-prefixed property keys (should have been normalized)
                for k in room.properties.keys() {
                    if k.contains("Pset_Arx") && k.matches("Pset_").count() > 1 {
                        report.results.push(ValidationResult {
                            rule_id: "props.double_prefix".into(),
                            message: format!(
                                "Room '{}' has double-prefixed property key '{}'",
                                room.name, k
                            ),
                            severity: ValidationSeverity::Warning,
                            field: Some(k.clone()),
                        });
                    }
                }

                for eq in &room.equipment {
                    validate_equipment(&mut report, eq, &mut seen_eq_ids, &room.name);
                }
            }
            for eq in &wing.equipment {
                validate_equipment(&mut report, eq, &mut seen_eq_ids, &wing.name);
            }
        }
        for eq in &floor.equipment {
            validate_equipment(&mut report, eq, &mut seen_eq_ids, &floor.name);
        }
    }

    report
}

fn validate_equipment(
    report: &mut BuildingValidationReport,
    eq: &crate::core::Equipment,
    seen_eq_ids: &mut std::collections::HashSet<String>,
    context: &str,
) {
    if eq.name.trim().is_empty() {
        report.results.push(ValidationResult {
            rule_id: "equipment.name.required".into(),
            message: format!("Equipment under '{}' has empty name", context),
            severity: ValidationSeverity::Error,
            field: Some(format!("{}/equipment", context)),
        });
    }
    if !seen_eq_ids.insert(eq.id.clone()) {
        report.results.push(ValidationResult {
            rule_id: "equipment.id.duplicate".into(),
            message: format!("Duplicate equipment id {}", eq.id),
            severity: ValidationSeverity::Error,
            field: Some(eq.id.clone()),
        });
    }
    if let Some(ref enr) = eq.lidar_enrichment {
        validate_enrichment(
            report,
            &format!("equipment[{}]", eq.name),
            enr.confidence_score,
            enr.point_count,
        );
    }
}

fn validate_enrichment(
    report: &mut BuildingValidationReport,
    field_prefix: &str,
    confidence: f64,
    point_count: usize,
) {
    if !(0.0..=1.0).contains(&confidence) {
        report.results.push(ValidationResult {
            rule_id: "lidar.confidence.range".into(),
            message: format!(
                "{} confidence_score {} outside [0, 1]",
                field_prefix, confidence
            ),
            severity: ValidationSeverity::Warning,
            field: Some(format!(
                "{}.lidar_enrichment.confidence_score",
                field_prefix
            )),
        });
    }
    // point_count is usize — always non-negative; nothing to check beyond presence
    let _ = point_count;
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::core::{Building, Floor, LidarEnrichment, Room, RoomType, Wing};

    #[test]
    fn accepts_minimal_valid_building() {
        let mut b = Building::new("HQ".into(), "/hq".into());
        let mut floor = Floor::new("F1".into(), 0);
        let mut wing = Wing::new("Main".into());
        wing.add_room(Room::new("R1".into(), RoomType::Office));
        floor.add_wing(wing);
        b.add_floor(floor);
        let report = validate_building(&b);
        assert!(!report.has_errors());
    }

    #[test]
    fn flags_empty_name_and_bad_confidence() {
        let mut b = Building::new("".into(), "/hq".into());
        let mut floor = Floor::new("F1".into(), 0);
        let mut wing = Wing::new("Main".into());
        let mut room = Room::new("R1".into(), RoomType::Office);
        room.lidar_enrichment = Some(LidarEnrichment {
            point_count: 1,
            confidence_score: 1.5,
            last_scan_timestamp: None,
            classification_heuristic: None,
        });
        wing.add_room(room);
        floor.add_wing(wing);
        b.add_floor(floor);
        let report = validate_building(&b);
        assert!(report.has_errors());
        assert!(report
            .warnings()
            .any(|w| w.rule_id == "lidar.confidence.range"));
    }
}
