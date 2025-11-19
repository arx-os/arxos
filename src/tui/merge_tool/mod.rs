//! Three-way merge conflict resolution tool
//!
//! Provides an interactive TUI for resolving Git merge conflicts in building data files.
//! Supports both Git conflict markers and git merge-tree output.

pub mod conflict;
pub mod diff_viewer;
pub mod resolver;

pub use conflict::{Conflict, ConflictParser};
pub use diff_viewer::MergeViewer;
pub use resolver::ResolutionEngine;

use std::path::PathBuf;

/// Main entry point for merge conflict resolution
pub struct MergeTool {
    file_path: PathBuf,
    conflicts: Vec<Conflict>,
    resolver: ResolutionEngine,
}

impl MergeTool {
    /// Create a new merge tool for a file with conflicts
    pub fn new(file_path: PathBuf) -> Result<Self, Box<dyn std::error::Error>> {
        let parser = ConflictParser::new();
        let conflicts = parser.parse_file(&file_path)?;

        Ok(Self {
            file_path,
            conflicts: conflicts.clone(),
            resolver: ResolutionEngine::new(conflicts),
        })
    }

    /// Launch interactive merge viewer
    pub fn run_interactive(&mut self) -> Result<(), Box<dyn std::error::Error>> {
        let mut viewer = MergeViewer::new(&self.conflicts, &self.file_path)?;

        // Run the viewer and get resolutions
        let resolutions = viewer.run()?;

        // Apply resolutions
        self.resolver.apply_resolutions(&resolutions);

        // Preview and confirm before saving
        self.preview_and_save()?;

        Ok(())
    }

    /// Preview merged result and save if confirmed
    fn preview_and_save(&self) -> Result<(), Box<dyn std::error::Error>> {
        let merged_content = self.resolver.build_merged_content();

        // Show preview (would use TUI in real implementation)
        println!("=== PREVIEW OF MERGED FILE ===");
        println!("{}", merged_content);
        println!("==============================");

        // In full implementation, this would be a TUI confirmation dialog
        // For now, just save directly
        self.resolver.save_to_file(&self.file_path)?;

        Ok(())
    }

    /// Get list of files with conflicts in the repository
    pub fn find_conflicted_files() -> Result<Vec<PathBuf>, Box<dyn std::error::Error>> {
        use std::process::Command;

        let output = Command::new("git")
            .args(["diff", "--name-only", "--diff-filter=U"])
            .output()?;

        let files = String::from_utf8(output.stdout)?
            .lines()
            .map(PathBuf::from)
            .collect();

        Ok(files)
    }
}
