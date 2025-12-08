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
            #[cfg(all(feature = "tui", feature = "agent"))]
            {
                use crate::agent::auth::TokenState;
                // Dummy state for consistency with CLI dashboard command
                let repo_root = std::path::PathBuf::from(".");
                let token_state = TokenState::new("dummy".to_string(), vec![]);
                let hardware = crate::hardware::HardwareManager::new();
                
                let state = std::sync::Arc::new(crate::agent::dispatcher::AgentState {
                    repo_root,
                    token: std::sync::Arc::new(std::sync::Mutex::new(token_state)),
                    hardware: std::sync::Arc::new(hardware),
                });
                
                let rt = tokio::runtime::Runtime::new()?;
                rt.block_on(crate::tui::dashboard::run_dashboard(state))?;
                return Ok(());
            }
            #[cfg(all(feature = "tui", not(feature = "agent")))]
            {
                println!("⚠️  Interactive dashboard requires --features agent");
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
