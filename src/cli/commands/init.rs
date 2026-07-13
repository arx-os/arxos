use anyhow::{Context, Result};
use clap::Parser;
use std::fs;
use std::path::{Path, PathBuf};

/// Initialize a new ArxOS building repository
#[derive(Parser, Debug)]
pub struct InitCommand {
    /// Directory to initialize (defaults to current directory)
    #[arg(default_value = ".")]
    pub directory: PathBuf,

    /// Building name
    #[arg(short, long)]
    pub name: Option<String>,

    /// Install Git hooks for auto-export
    #[arg(long, default_value = "true")]
    pub install_hooks: bool,

    /// Initialize Git repository if not present
    #[arg(long, default_value = "true")]
    pub init_git: bool,
}

impl InitCommand {
    pub fn execute(&self) -> Result<()> {
        let dir = &self.directory;

        // Create directory if it doesn't exist
        if !dir.exists() {
            fs::create_dir_all(dir)
                .context(format!("Failed to create directory: {}", dir.display()))?;
            println!("📁 Created directory: {}", dir.display());
        }

        // Check if already initialized
        let building_yaml = dir.join("building.yaml");
        if building_yaml.exists() {
            anyhow::bail!("Directory already contains building.yaml. Use a different directory or remove the existing file.");
        }

        // Initialize Git repository if requested
        if self.init_git && !dir.join(".git").exists() {
            self.init_git_repo(dir)?;
        }

        // Copy .gitignore template
        self.copy_gitignore(dir)?;

        // Create building.yaml from template
        self.create_building_yaml(dir)?;

        // Install Git hooks if requested
        if self.install_hooks && dir.join(".git").exists() {
            self.install_git_hooks(dir)?;
        }

        // Create exports directory
        let exports_dir = dir.join("exports");
        fs::create_dir_all(&exports_dir).context("Failed to create exports directory")?;
        println!("📂 Created exports directory");

        println!("\n✅ ArxOS repository initialized!");
        println!("\nNext steps:");
        println!("  1. Edit building.yaml to define your building");
        println!("  2. Run 'arx export --format ifc' to generate IFC");
        println!("  3. Commit your changes: git add . && git commit -m 'Initial building'");

        if self.install_hooks {
            println!("\n🔗 Git hooks installed - IFC will auto-export after git pull");
        }

        Ok(())
    }

    fn init_git_repo(&self, dir: &Path) -> Result<()> {
        use std::process::Command;

        let output = Command::new("git")
            .arg("init")
            .current_dir(dir)
            .output()
            .context("Failed to run 'git init'. Is Git installed?")?;

        if output.status.success() {
            println!("🔧 Initialized Git repository");
            Ok(())
        } else {
            anyhow::bail!(
                "Git init failed: {}",
                String::from_utf8_lossy(&output.stderr)
            )
        }
    }

    fn copy_gitignore(&self, dir: &Path) -> Result<()> {
        let template = include_str!("../../../templates/.gitignore");
        let gitignore_path = dir.join(".gitignore");

        if gitignore_path.exists() {
            println!("⚠️  .gitignore already exists, skipping");
        } else {
            fs::write(&gitignore_path, template).context("Failed to write .gitignore")?;
            println!("📝 Created .gitignore");
        }

        Ok(())
    }

    fn create_building_yaml(&self, dir: &Path) -> Result<()> {
        use crate::core::{Building, Floor};

        let name = self
            .name
            .clone()
            .unwrap_or_else(|| "My Building".to_string());
        let path = format!("/{}", name.replace(' ', "-").to_lowercase());
        let mut building = Building::new(name, path);
        building.description = Some("A sample building managed with ArxOS".into());
        building.add_floor(Floor::new("Ground Floor".to_string(), 0));

        crate::persistence::save_building_at(dir, &building)
            .map_err(|e| anyhow::anyhow!("Failed to write building.yaml: {}", e))?;

        println!(
            "📄 Created building.yaml (id={}, 1 floor)",
            building.id
        );
        println!("   Next: arx import ifc|lidar … or arx edit to grow the model");
        Ok(())
    }

    fn install_git_hooks(&self, dir: &Path) -> Result<()> {
        let hooks_dir = dir.join(".git/hooks");
        if !hooks_dir.exists() {
            anyhow::bail!("Git hooks directory not found. Initialize Git first.");
        }

        let template = include_str!("../../../templates/post-merge");
        let hook_path = hooks_dir.join("post-merge");

        fs::write(&hook_path, template).context("Failed to write post-merge hook")?;

        // Make executable (Unix only)
        #[cfg(unix)]
        {
            use std::os::unix::fs::PermissionsExt;
            let mut perms = fs::metadata(&hook_path)?.permissions();
            perms.set_mode(0o755);
            fs::set_permissions(&hook_path, perms)?;
        }

        println!("🪝 Installed Git hooks (post-merge)");
        Ok(())
    }
}
