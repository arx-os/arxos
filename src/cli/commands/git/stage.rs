use crate::cli::commands::Command;
use crate::git::manager::{BuildingGitManager, GitConfigManager};
use std::error::Error;

pub struct StageCommand {
    pub all: bool,
    pub file: Option<String>,
}

impl Command for StageCommand {
    fn execute(&self) -> Result<(), Box<dyn Error>> {
        let config = GitConfigManager::load_from_arx_config_or_env();
        let mut manager = BuildingGitManager::new(".", "current", config)?;

        if self.all || self.file.is_none() {
            let count = manager.stage_all()?;
            println!("✅ Staged {} file(s)", count);
        } else if let Some(path) = &self.file {
            manager.stage_file(path)?;
            println!("✅ Staged: {}", path);
        }

        Ok(())
    }

    fn name(&self) -> &'static str {
        "git stage"
    }
}
