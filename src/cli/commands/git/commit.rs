use crate::cli::commands::Command;
use crate::git::manager::{BuildingGitManager, GitConfigManager};
use std::error::Error;

pub struct CommitCommand {
    pub message: String,
}

impl Command for CommitCommand {
    fn execute(&self) -> Result<(), Box<dyn Error>> {
        let config = GitConfigManager::load_from_arx_config_or_env();
        let mut manager = BuildingGitManager::new(".", "current", config)?;

        let commit_id = manager.commit_staged(&self.message)?;
        let short_id = if commit_id.len() >= 8 { &commit_id[..8] } else { &commit_id };
        println!("✅ Committed: {}", short_id);
        println!("📝 Message: {}", self.message);

        Ok(())
    }

    fn name(&self) -> &'static str {
        "git commit"
    }
}
