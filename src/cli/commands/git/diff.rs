use crate::cli::commands::Command;
use crate::git::manager::{BuildingGitManager, GitConfigManager};
use std::error::Error;

pub struct DiffCommand {
    pub commit: Option<String>,
    pub file: Option<String>,
    pub stat: bool,
    pub interactive: bool,
}

impl Command for DiffCommand {
    fn execute(&self) -> Result<(), Box<dyn Error>> {
        if self.interactive {
            #[cfg(feature = "tui")]
            {
                let diff_view = crate::tui::diff_view::DiffView::new()?;
                diff_view.run()?;
                return Ok(());
            }
            #[cfg(not(feature = "tui"))]
            {
                println!("⚠️  Interactive diff viewer requires --features tui");
                return Ok(());
            }
        }

        let config = GitConfigManager::load_from_arx_config_or_env();
        let manager = BuildingGitManager::new(".", "current", config)?;

        if self.stat {
            let stats = manager.get_diff_stats(self.commit.as_deref())?;
            println!("📊 Diff Statistics");
            println!();
            println!("  Files changed: {}", stats.files_changed);
            println!("  Insertions:    {}", stats.insertions);
            println!("  Deletions:     {}", stats.deletions);
        } else {
            let diff_result = manager.get_diff(self.commit.as_deref(), self.file.as_deref())?;
            println!("📊 Diff: {} → {}", diff_result.compare_hash[..8.min(diff_result.compare_hash.len())].to_string(), diff_result.commit_hash[..8.min(diff_result.commit_hash.len())].to_string());
            println!("Files changed: {}", diff_result.files_changed);
            println!();
            for file_diff in &diff_result.file_diffs {
                match file_diff.line_type {
                    crate::git::diff::DiffLineType::Addition => println!("+{}: {}", file_diff.line_number, file_diff.content),
                    crate::git::diff::DiffLineType::Deletion => println!("-{}: {}", file_diff.line_number, file_diff.content),
                    crate::git::diff::DiffLineType::Context => println!(" {}: {}", file_diff.line_number, file_diff.content),
                }
            }
        }

        Ok(())
    }

    fn name(&self) -> &'static str {
        "git diff"
    }
}
