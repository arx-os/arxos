use crate::cli::commands::Command;
use crate::git::manager::{BuildingGitManager, GitConfigManager};
use std::error::Error;

pub struct UnstageCommand {
    pub all: bool,
    pub file: Option<String>,
}

impl Command for UnstageCommand {
    fn execute(&self) -> Result<(), Box<dyn Error>> {
        let config = GitConfigManager::load_from_arx_config_or_env();
        let mut manager = BuildingGitManager::new(".", "current", config)?;

        if self.all || self.file.is_none() {
            let count = manager.unstage_all()?;
            println!("✅ Unstaged {} file(s)", count);
        } else if let Some(path) = &self.file {
            manager.unstage_file(path)?;
            println!("✅ Unstaged: {}", path);
        }

        Ok(())
    }

    fn name(&self) -> &'static str {
        "git unstage"
    }
}
