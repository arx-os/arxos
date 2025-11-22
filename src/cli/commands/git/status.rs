use crate::cli::commands::Command;
use crate::git::manager::{BuildingGitManager, GitConfigManager};
use std::error::Error;

pub struct StatusCommand {
    pub verbose: bool,
    pub interactive: bool,
}

impl Command for StatusCommand {
    fn execute(&self) -> Result<(), Box<dyn Error>> {
        if self.interactive {
            #[cfg(feature = "tui")]
            {
                let dashboard = crate::tui::dashboard::Dashboard::new()?;
                dashboard.run()?;
                return Ok(());
            }
            #[cfg(not(feature = "tui"))]
            {
                println!("⚠️  Interactive dashboard requires --features tui");
                return Ok(());
            }
        }

        // Get git manager for current directory
        let config = GitConfigManager::load_from_arx_config_or_env();
        let manager = BuildingGitManager::new(".", "current", config)?;

        let status = manager.get_status()?;

        println!("📊 Repository Status");
        println!();
        println!("Branch: {}", status.current_branch);
        println!("Last commit: {}", if status.last_commit.is_empty() { "(none)" } else { &status.last_commit[..8.min(status.last_commit.len())] });
        println!("Message: {}", status.last_commit_message);
        println!();

        if self.verbose {
            println!("💡 Use 'arx stage <file>' to stage changes");
            println!("💡 Use 'arx commit <message>' to commit staged changes");
            println!("💡 Use 'arx diff' to see changes");
        }

        Ok(())
    }

    fn name(&self) -> &'static str {
        "git status"
    }
}
