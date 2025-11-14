//! Merge conflict resolution command

use crate::tui::merge_tool::MergeTool;
use clap::Args;
use std::path::PathBuf;

/// Resolve merge conflicts interactively
#[derive(Debug, Args)]
pub struct MergeCommand {
    /// File to resolve conflicts in (if not specified, finds all conflicted files)
    #[arg(value_name = "FILE")]
    file: Option<PathBuf>,

    /// List conflicted files without launching viewer
    #[arg(short, long)]
    list: bool,
}

impl MergeCommand {
    pub fn execute(&self) -> Result<(), Box<dyn std::error::Error>> {
        if self.list {
            return self.list_conflicts();
        }

        if let Some(ref file_path) = self.file {
            // Resolve specific file
            self.resolve_file(file_path)?;
        } else {
            // Find and resolve all conflicted files
            self.resolve_all()?;
        }

        Ok(())
    }

    fn list_conflicts(&self) -> Result<(), Box<dyn std::error::Error>> {
        let files = MergeTool::find_conflicted_files()?;

        if files.is_empty() {
            println!("No merge conflicts found.");
            return Ok(());
        }

        println!("Files with merge conflicts:");
        for file in files {
            println!("  {}", file.display());
        }
        println!("\nRun 'arx merge <file>' to resolve conflicts.");

        Ok(())
    }

    fn resolve_file(&self, file_path: &PathBuf) -> Result<(), Box<dyn std::error::Error>> {
        if !file_path.exists() {
            return Err(format!("File not found: {}", file_path.display()).into());
        }

        println!("Resolving conflicts in: {}", file_path.display());

        let mut tool = MergeTool::new(file_path.clone())?;
        tool.run_interactive()?;

        println!("✓ Conflicts resolved in {}", file_path.display());

        Ok(())
    }

    fn resolve_all(&self) -> Result<(), Box<dyn std::error::Error>> {
        let files = MergeTool::find_conflicted_files()?;

        if files.is_empty() {
            println!("No merge conflicts found.");
            return Ok(());
        }

        println!("Found {} file(s) with conflicts", files.len());

        for file in &files {
            println!("\n=== Resolving: {} ===", file.display());

            match MergeTool::new(file.clone()) {
                Ok(mut tool) => {
                    if let Err(e) = tool.run_interactive() {
                        eprintln!("Error resolving {}: {}", file.display(), e);
                        eprintln!("Skipping to next file...");
                        continue;
                    }
                    println!("✓ Resolved: {}", file.display());
                }
                Err(e) => {
                    eprintln!("Error loading {}: {}", file.display(), e);
                    eprintln!("Skipping to next file...");
                }
            }
        }

        println!("\n✓ All conflicts resolved!");
        println!("Don't forget to:");
        println!("  1. Review the changes");
        println!("  2. Run tests if applicable");
        println!("  3. git add <files>");
        println!("  4. git commit");

        Ok(())
    }
}
