//! Conflict parsing and data structures
//!
//! Parses Git conflict markers and git merge-tree output to extract
//! base, ours, and theirs versions for three-way merge.

use std::fs;
use std::path::Path;

/// Represents a single merge conflict in a file
#[derive(Debug, Clone)]
pub struct Conflict {
    /// Line number where conflict starts (0-indexed)
    pub start_line: usize,
    /// Line number where conflict ends (0-indexed)
    pub end_line: usize,
    /// Conflict sections (ours, base, theirs)
    pub sections: ConflictSections,
    /// Context lines before the conflict
    pub context_before: Vec<String>,
    /// Context lines after the conflict
    pub context_after: Vec<String>,
}

/// The three versions in a conflict
#[derive(Debug, Clone)]
pub struct ConflictSections {
    pub ours: ConflictSection,
    pub base: Option<ConflictSection>,
    pub theirs: ConflictSection,
}

/// A section of conflicting content
#[derive(Debug, Clone)]
pub struct ConflictSection {
    pub lines: Vec<String>,
    pub label: String, // e.g., "HEAD", "main", "feature-branch"
}

/// Individual hunk of a conflict (for display)
#[derive(Debug, Clone)]
pub struct ConflictHunk {
    pub line_number: usize,
    pub content: String,
    pub source: HunkSource,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum HunkSource {
    Ours,
    Base,
    Theirs,
    Context,
}

/// Parser for extracting conflicts from files
pub struct ConflictParser {
    context_lines: usize,
}

impl ConflictParser {
    pub fn new() -> Self {
        Self { context_lines: 3 }
    }

    /// Parse conflicts from a file with Git conflict markers
    ///
    /// Format:
    /// ```text
    /// <<<<<<< HEAD (or branch name)
    /// our changes
    /// ||||||| base (optional)
    /// base version
    /// =======
    /// their changes
    /// >>>>>>> branch-name
    /// ```
    pub fn parse_file(&self, path: &Path) -> Result<Vec<Conflict>, Box<dyn std::error::Error>> {
        let content = fs::read_to_string(path)?;
        self.parse_content(&content)
    }

    /// Parse conflicts from file content
    pub fn parse_content(&self, content: &str) -> Result<Vec<Conflict>, Box<dyn std::error::Error>> {
        let lines: Vec<String> = content.lines().map(String::from).collect();
        let mut conflicts = Vec::new();
        let mut i = 0;

        while i < lines.len() {
            if lines[i].starts_with("<<<<<<<") {
                if let Some((conflict, end_idx)) = self.parse_conflict(&lines, i)? {
                    conflicts.push(conflict);
                    i = end_idx + 1;
                } else {
                    i += 1;
                }
            } else {
                i += 1;
            }
        }

        Ok(conflicts)
    }

    /// Parse a single conflict starting at the given index
    fn parse_conflict(
        &self,
        lines: &[String],
        start: usize,
    ) -> Result<Option<(Conflict, usize)>, Box<dyn std::error::Error>> {
        // Extract label from <<<<<<< marker
        let ours_label = lines[start]
            .strip_prefix("<<<<<<<")
            .unwrap_or("")
            .trim()
            .to_string();

        let mut ours_lines = Vec::new();
        let mut base_lines = None;
        let mut theirs_lines = Vec::new();
        let mut theirs_label = String::new();

        let mut i = start + 1;
        let mut in_ours = true;
        let mut in_base = false;
        let mut in_theirs = false;

        // Parse the conflict sections
        while i < lines.len() {
            if lines[i].starts_with("|||||||") {
                // Base section (optional)
                in_ours = false;
                in_base = true;
                base_lines = Some(Vec::new());
            } else if lines[i].starts_with("=======") {
                // Switch to theirs section
                in_ours = false;
                in_base = false;
                in_theirs = true;
            } else if lines[i].starts_with(">>>>>>>") {
                // End of conflict
                theirs_label = lines[i]
                    .strip_prefix(">>>>>>>")
                    .unwrap_or("")
                    .trim()
                    .to_string();
                break;
            } else {
                // Add line to appropriate section
                if in_ours {
                    ours_lines.push(lines[i].clone());
                } else if in_base {
                    if let Some(ref mut base) = base_lines {
                        base.push(lines[i].clone());
                    }
                } else if in_theirs {
                    theirs_lines.push(lines[i].clone());
                }
            }
            i += 1;
        }

        // Extract context
        let context_before = self.extract_context(lines, start, true);
        let context_after = self.extract_context(lines, i, false);

        let conflict = Conflict {
            start_line: start,
            end_line: i,
            sections: ConflictSections {
                ours: ConflictSection {
                    lines: ours_lines,
                    label: ours_label,
                },
                base: base_lines.map(|lines| ConflictSection {
                    lines,
                    label: "base".to_string(),
                }),
                theirs: ConflictSection {
                    lines: theirs_lines,
                    label: theirs_label,
                },
            },
            context_before,
            context_after,
        };

        Ok(Some((conflict, i)))
    }

    /// Extract context lines before or after a conflict
    fn extract_context(&self, lines: &[String], index: usize, before: bool) -> Vec<String> {
        let mut context = Vec::new();

        if before {
            let start = index.saturating_sub(self.context_lines);
            for i in start..index {
                context.push(lines[i].clone());
            }
        } else {
            let end = (index + 1 + self.context_lines).min(lines.len());
            for i in (index + 1)..end {
                context.push(lines[i].clone());
            }
        }

        context
    }
}

impl Default for ConflictParser {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_parse_simple_conflict() {
        let content = r#"
normal line
<<<<<<< HEAD
our changes
=======
their changes
>>>>>>> feature-branch
more normal lines
"#;

        let parser = ConflictParser::new();
        let conflicts = parser.parse_content(content).unwrap();

        assert_eq!(conflicts.len(), 1);
        assert_eq!(conflicts[0].sections.ours.lines, vec!["our changes"]);
        assert_eq!(conflicts[0].sections.theirs.lines, vec!["their changes"]);
    }

    #[test]
    fn test_parse_conflict_with_base() {
        let content = r#"
<<<<<<< HEAD
our changes
||||||| base
base version
=======
their changes
>>>>>>> feature
"#;

        let parser = ConflictParser::new();
        let conflicts = parser.parse_content(content).unwrap();

        assert_eq!(conflicts.len(), 1);
        assert!(conflicts[0].sections.base.is_some());
        assert_eq!(
            conflicts[0].sections.base.as_ref().unwrap().lines,
            vec!["base version"]
        );
    }
}
