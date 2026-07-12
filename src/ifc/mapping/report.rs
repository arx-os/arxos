//! Loss / fidelity reporting for IFC import and export (Phase 5).

use serde::{Deserialize, Serialize};

/// Highest fidelity tier achieved or targeted for a mapping operation.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize, Default)]
pub enum FidelityLevel {
    /// Identity & hierarchy only
    L0,
    /// + typed Arx semantics (LiDAR, clean properties)
    L1,
    /// + geometry (position / dims / mesh subset)
    #[default]
    L2,
}

impl std::fmt::Display for FidelityLevel {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            FidelityLevel::L0 => write!(f, "L0"),
            FidelityLevel::L1 => write!(f, "L1"),
            FidelityLevel::L2 => write!(f, "L2"),
        }
    }
}

/// A non-fatal mapping note (import or export).
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct MappingWarning {
    /// Short machine-oriented code (e.g. `no_placement`, `merge_unmatched`)
    pub code: String,
    /// Human-readable message
    pub message: String,
    /// Optional entity label (name, GlobalId, path)
    pub entity: Option<String>,
}

impl MappingWarning {
    pub fn new(code: impl Into<String>, message: impl Into<String>) -> Self {
        Self {
            code: code.into(),
            message: message.into(),
            entity: None,
        }
    }

    pub fn with_entity(mut self, entity: impl Into<String>) -> Self {
        self.entity = Some(entity.into());
        self
    }
}

/// Statistics from re-import merge against an existing building.
#[derive(Debug, Clone, Default, PartialEq, Eq, Serialize, Deserialize)]
pub struct MergeStats {
    pub floors_matched: usize,
    pub floors_added: usize,
    pub rooms_matched: usize,
    pub rooms_added: usize,
    pub equipment_matched: usize,
    pub equipment_added: usize,
    /// Existing rooms not present in the incoming model (left out of result)
    pub existing_rooms_not_in_incoming: usize,
    /// Existing equipment not present in the incoming model
    pub existing_equipment_not_in_incoming: usize,
}

/// Aggregated result of an IFC import/export mapping operation.
#[derive(Debug, Clone, Default, Serialize, Deserialize)]
pub struct LossReport {
    pub level_achieved: FidelityLevel,
    pub warnings: Vec<MappingWarning>,
    pub merge: Option<MergeStats>,
}

impl LossReport {
    pub fn new(level: FidelityLevel) -> Self {
        Self {
            level_achieved: level,
            warnings: Vec::new(),
            merge: None,
        }
    }

    pub fn warn(&mut self, code: impl Into<String>, message: impl Into<String>) {
        self.warnings.push(MappingWarning::new(code, message));
    }

    pub fn warn_entity(
        &mut self,
        code: impl Into<String>,
        message: impl Into<String>,
        entity: impl Into<String>,
    ) {
        self.warnings
            .push(MappingWarning::new(code, message).with_entity(entity));
    }

    pub fn is_clean(&self) -> bool {
        self.warnings.is_empty()
    }

    /// Short multi-line summary for CLI / agent logs.
    pub fn summary_lines(&self) -> Vec<String> {
        let mut lines = vec![format!("Fidelity: {}", self.level_achieved)];
        if let Some(m) = &self.merge {
            lines.push(format!(
                "Merge: rooms {} matched / {} added, equipment {} matched / {} added",
                m.rooms_matched, m.rooms_added, m.equipment_matched, m.equipment_added
            ));
            if m.existing_rooms_not_in_incoming > 0 || m.existing_equipment_not_in_incoming > 0 {
                lines.push(format!(
                    "Existing not in IFC: {} rooms, {} equipment (not carried into result)",
                    m.existing_rooms_not_in_incoming, m.existing_equipment_not_in_incoming
                ));
            }
        }
        if self.warnings.is_empty() {
            lines.push("Warnings: none".to_string());
        } else {
            lines.push(format!("Warnings ({}):", self.warnings.len()));
            for w in &self.warnings {
                if let Some(ref e) = w.entity {
                    lines.push(format!("  - [{}] {} ({})", w.code, w.message, e));
                } else {
                    lines.push(format!("  - [{}] {}", w.code, w.message));
                }
            }
        }
        lines
    }
}

/// Full outcome of mapping IFC → domain (or reverse with notes).
#[derive(Debug, Clone)]
pub struct MappingResult {
    pub building: crate::core::Building,
    pub report: LossReport,
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn summary_includes_merge_and_warnings() {
        let mut r = LossReport::new(FidelityLevel::L2);
        r.merge = Some(MergeStats {
            rooms_matched: 2,
            rooms_added: 1,
            equipment_matched: 3,
            equipment_added: 0,
            ..Default::default()
        });
        r.warn("demo", "something dropped");
        let s = r.summary_lines().join("\n");
        assert!(s.contains("L2"));
        assert!(s.contains("rooms 2 matched"));
        assert!(s.contains("demo"));
    }
}
