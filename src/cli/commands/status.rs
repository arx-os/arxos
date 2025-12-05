use anyhow::{Context, Result};
use clap::Parser;
use std::path::PathBuf;

/// Show YAML vs IFC sync status
#[derive(Parser, Debug)]
pub struct StatusCommand {
    /// Repository directory (defaults to current directory)
    #[arg(default_value = ".")]
    pub directory: PathBuf,

    /// Show detailed information
    #[arg(short, long)]
    pub verbose: bool,
}

impl StatusCommand {
    pub fn execute(&self) -> Result<()> {
        use crate::export::ifc::IFCSyncState;
        use std::fs;
        use std::time::SystemTime;

        let dir = &self.directory;
        
        // Check for building.yaml
        let yaml_path = dir.join("building.yaml");
        if !yaml_path.exists() {
            anyhow::bail!("No building.yaml found in {}. Run 'arx init' to create one.", dir.display());
        }

        // Get YAML modification time
        let yaml_metadata = fs::metadata(&yaml_path)?;
        let yaml_modified = yaml_metadata.modified()?;

        // Check for IFC sync state
        let sync_state_path = dir.join(".ifc_sync_state.json");
        let sync_state = IFCSyncState::load(&sync_state_path);

        // Check for IFC file
        let exports_dir = dir.join("exports");
        let ifc_files: Vec<_> = if exports_dir.exists() {
            fs::read_dir(&exports_dir)?
                .filter_map(|e| e.ok())
                .filter(|e| {
                    e.path()
                        .extension()
                        .and_then(|ext| ext.to_str())
                        .map(|ext| ext.eq_ignore_ascii_case("ifc"))
                        .unwrap_or(false)
                })
                .collect()
        } else {
            Vec::new()
        };

        println!("📊 ArxOS Repository Status\n");
        println!("📁 Directory: {}", dir.display());
        println!("📄 YAML: {}", if yaml_path.exists() { "✅ Found" } else { "❌ Missing" });

        if let Some(sync_state) = sync_state {
            let last_export = sync_state.last_export_timestamp;
            let is_outdated = yaml_modified > last_export.into();

            println!("🔄 Last Export: {}", last_export.format("%Y-%m-%d %H:%M:%S"));
            
            if is_outdated {
                println!("⚠️  Status: OUT OF DATE (YAML modified after last export)");
                println!("\n💡 Run 'arx export --format ifc' to regenerate IFC");
            } else {
                println!("✅ Status: UP TO DATE");
            }

            if self.verbose {
                println!("\n📦 Tracked Entities:");
                println!("   Equipment: {}", sync_state.equipment_paths.len());
                println!("   Rooms: {}", sync_state.rooms_paths.len());
            }
        } else {
            println!("🔄 Last Export: Never");
            println!("⚠️  Status: NO IFC EXPORTED YET");
            println!("\n💡 Run 'arx export --format ifc' to create initial IFC");
        }

        if !ifc_files.is_empty() {
            println!("\n📂 IFC Files in exports/:");
            for file in &ifc_files {
                let path = file.path();
                let metadata = fs::metadata(&path)?;
                let size = metadata.len();
                let modified = metadata.modified()?;
                
                println!("   • {} ({} KB, modified: {})", 
                    path.file_name().unwrap().to_string_lossy(),
                    size / 1024,
                    format_system_time(modified)
                );
            }
        } else {
            println!("\n📂 IFC Files: None");
        }

        // Show Git status if in a Git repo
        if dir.join(".git").exists() {
            if let Ok(git_status) = get_git_status(dir) {
                println!("\n🔧 Git Status:");
                println!("   Branch: {}", git_status.branch);
                if git_status.uncommitted_changes > 0 {
                    println!("   ⚠️  {} uncommitted change(s)", git_status.uncommitted_changes);
                } else {
                    println!("   ✅ Working tree clean");
                }
            }
        }

        Ok(())
    }
}

fn format_system_time(time: SystemTime) -> String {
    use chrono::{DateTime, Utc};
    let datetime: DateTime<Utc> = time.into();
    datetime.format("%Y-%m-%d %H:%M:%S").to_string()
}

struct GitStatus {
    branch: String,
    uncommitted_changes: usize,
}

fn get_git_status(dir: &std::path::Path) -> Result<GitStatus> {
    use crate::git::manager::{BuildingGitManager, GitConfigManager};
    
    let config = GitConfigManager::load_from_arx_config_or_env();
    let dir_str = dir.to_str().ok_or_else(|| anyhow::anyhow!("Invalid path"))?;
    let manager = BuildingGitManager::new(dir_str, "current", config)?;
    let status = manager.get_status()?;
    
    Ok(GitStatus {
        branch: status.current_branch,
        uncommitted_changes: status.modified_files.len() + status.new_files.len(),
    })
}
