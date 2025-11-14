//! Conflict resolution engine
//!
//! Tracks user choices for each conflict and builds the final merged content.

use super::conflict::Conflict;
use std::collections::HashMap;
use std::fs;
use std::path::Path;

/// User's choice for resolving a conflict
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ResolutionChoice {
    /// Use "ours" version
    Ours,
    /// Use "theirs" version
    Theirs,
    /// Use both (ours then theirs)
    Both,
    /// Use both (theirs then ours)
    BothReversed,
    /// Skip this conflict (leave markers)
    Skip,
    /// Custom resolution (manually edited)
    Custom,
}

/// A resolution for a single conflict
#[derive(Debug, Clone)]
pub struct Resolution {
    /// Index of the conflict being resolved
    pub conflict_index: usize,
    /// User's choice
    pub choice: ResolutionChoice,
    /// Custom content (if choice is Custom)
    pub custom_content: Option<Vec<String>>,
}

/// Engine for building merged content from resolutions
pub struct ResolutionEngine {
    conflicts: Vec<Conflict>,
    resolutions: HashMap<usize, Resolution>,
    original_content: Vec<String>,
}

impl ResolutionEngine {
    /// Create a new resolution engine
    pub fn new(conflicts: Vec<Conflict>) -> Self {
        Self {
            conflicts,
            resolutions: HashMap::new(),
            original_content: Vec::new(),
        }
    }

    /// Create resolution engine from a file
    pub fn from_file(
        conflicts: Vec<Conflict>,
        file_path: &Path,
    ) -> Result<Self, Box<dyn std::error::Error>> {
        let content = fs::read_to_string(file_path)?;
        let original_content: Vec<String> = content.lines().map(String::from).collect();

        Ok(Self {
            conflicts,
            resolutions: HashMap::new(),
            original_content,
        })
    }

    /// Apply a list of resolutions
    pub fn apply_resolutions(&mut self, resolutions: &[Resolution]) {
        for resolution in resolutions {
            self.resolutions
                .insert(resolution.conflict_index, resolution.clone());
        }
    }

    /// Apply a single resolution
    pub fn apply_resolution(&mut self, resolution: Resolution) {
        self.resolutions
            .insert(resolution.conflict_index, resolution);
    }

    /// Build the merged file content
    pub fn build_merged_content(&self) -> String {
        let mut result = Vec::new();
        let mut last_end = 0;

        for (idx, conflict) in self.conflicts.iter().enumerate() {
            // Add lines before this conflict
            if !self.original_content.is_empty() {
                for i in last_end..conflict.start_line {
                    if i < self.original_content.len() {
                        result.push(self.original_content[i].clone());
                    }
                }
            } else {
                // If we don't have original content, add context
                result.extend(conflict.context_before.clone());
            }

            // Add resolved conflict content
            if let Some(resolution) = self.resolutions.get(&idx) {
                result.extend(self.resolve_conflict(conflict, resolution));
            } else {
                // No resolution yet - leave conflict markers
                result.extend(self.render_conflict_markers(conflict));
            }

            last_end = conflict.end_line + 1;
        }

        // Add remaining lines after last conflict
        if !self.original_content.is_empty() {
            for i in last_end..self.original_content.len() {
                result.push(self.original_content[i].clone());
            }
        }

        result.join("\n")
    }

    /// Resolve a single conflict based on user choice
    fn resolve_conflict(&self, conflict: &Conflict, resolution: &Resolution) -> Vec<String> {
        match resolution.choice {
            ResolutionChoice::Ours => conflict.sections.ours.lines.clone(),
            ResolutionChoice::Theirs => conflict.sections.theirs.lines.clone(),
            ResolutionChoice::Both => {
                let mut lines = conflict.sections.ours.lines.clone();
                lines.extend(conflict.sections.theirs.lines.clone());
                lines
            }
            ResolutionChoice::BothReversed => {
                let mut lines = conflict.sections.theirs.lines.clone();
                lines.extend(conflict.sections.ours.lines.clone());
                lines
            }
            ResolutionChoice::Custom => resolution
                .custom_content
                .as_ref()
                .cloned()
                .unwrap_or_default(),
            ResolutionChoice::Skip => self.render_conflict_markers(conflict),
        }
    }

    /// Render conflict with markers (for unresolved conflicts)
    fn render_conflict_markers(&self, conflict: &Conflict) -> Vec<String> {
        let mut lines = Vec::new();

        // Opening marker
        lines.push(format!("<<<<<<< {}", conflict.sections.ours.label));

        // Ours section
        lines.extend(conflict.sections.ours.lines.clone());

        // Base section (if present)
        if let Some(ref base) = conflict.sections.base {
            lines.push(format!("||||||| {}", base.label));
            lines.extend(base.lines.clone());
        }

        // Separator
        lines.push("=======".to_string());

        // Theirs section
        lines.extend(conflict.sections.theirs.lines.clone());

        // Closing marker
        lines.push(format!(">>>>>>> {}", conflict.sections.theirs.label));

        lines
    }

    /// Save merged content to file
    pub fn save_to_file(&self, path: &Path) -> Result<(), Box<dyn std::error::Error>> {
        let content = self.build_merged_content();
        fs::write(path, content)?;
        Ok(())
    }

    /// Get resolution for a specific conflict
    pub fn get_resolution(&self, conflict_index: usize) -> Option<&Resolution> {
        self.resolutions.get(&conflict_index)
    }

    /// Check if all conflicts are resolved
    pub fn all_resolved(&self) -> bool {
        self.conflicts.len() == self.resolutions.len()
            && self
                .resolutions
                .values()
                .all(|r| r.choice != ResolutionChoice::Skip)
    }

    /// Get number of resolved conflicts
    pub fn resolved_count(&self) -> usize {
        self.resolutions
            .values()
            .filter(|r| r.choice != ResolutionChoice::Skip)
            .count()
    }

    /// Get total number of conflicts
    pub fn total_conflicts(&self) -> usize {
        self.conflicts.len()
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::tui::merge_tool::conflict::ConflictSection;

    fn create_test_conflict() -> Conflict {
        Conflict {
            start_line: 0,
            end_line: 6,
            sections: ConflictSections {
                ours: ConflictSection {
                    lines: vec!["our line 1".to_string(), "our line 2".to_string()],
                    label: "HEAD".to_string(),
                },
                base: None,
                theirs: ConflictSection {
                    lines: vec!["their line 1".to_string()],
                    label: "feature".to_string(),
                },
            },
            context_before: vec![],
            context_after: vec![],
        }
    }

    #[test]
    fn test_resolve_ours() {
        let conflict = create_test_conflict();
        let engine = ResolutionEngine::new(vec![conflict.clone()]);

        let resolution = Resolution {
            conflict_index: 0,
            choice: ResolutionChoice::Ours,
            custom_content: None,
        };

        let resolved = engine.resolve_conflict(&conflict, &resolution);
        assert_eq!(resolved, vec!["our line 1", "our line 2"]);
    }

    #[test]
    fn test_resolve_theirs() {
        let conflict = create_test_conflict();
        let engine = ResolutionEngine::new(vec![conflict.clone()]);

        let resolution = Resolution {
            conflict_index: 0,
            choice: ResolutionChoice::Theirs,
            custom_content: None,
        };

        let resolved = engine.resolve_conflict(&conflict, &resolution);
        assert_eq!(resolved, vec!["their line 1"]);
    }

    #[test]
    fn test_resolve_both() {
        let conflict = create_test_conflict();
        let engine = ResolutionEngine::new(vec![conflict.clone()]);

        let resolution = Resolution {
            conflict_index: 0,
            choice: ResolutionChoice::Both,
            custom_content: None,
        };

        let resolved = engine.resolve_conflict(&conflict, &resolution);
        assert_eq!(resolved, vec!["our line 1", "our line 2", "their line 1"]);
    }

    #[test]
    fn test_all_resolved() {
        let mut engine = ResolutionEngine::new(vec![create_test_conflict()]);

        assert!(!engine.all_resolved());

        engine.apply_resolution(Resolution {
            conflict_index: 0,
            choice: ResolutionChoice::Ours,
            custom_content: None,
        });

        assert!(engine.all_resolved());
    }
}
