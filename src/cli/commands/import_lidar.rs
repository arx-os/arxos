use crate::cli::commands::Command;
use crate::ingest::import_lidar_path;
use crate::persistence::{save_building_at, BUILDING_YAML};
use anyhow::anyhow;
use std::error::Error;
use std::path::Path;

pub struct ImportLidarCommand {
    pub file_path: String,
    pub voxel_size: f64,
    pub light: bool,
    pub dry_run: bool,
    pub merge: bool,
    pub building: Option<String>,
}

impl Command for ImportLidarCommand {
    fn execute(&self) -> Result<(), Box<dyn Error>> {
        println!("Importing LiDAR file: {}", self.file_path);
        println!("  Voxel Size: {} m", self.voxel_size);
        if self.light {
            println!("  Mode: Light (optimized for resource limits)");
        }
        if self.dry_run {
            println!("Dry run mode enabled - no changes will be written");
        }

        let repo_root = Path::new(".");
        let lidar_path = Path::new(&self.file_path);

        let existing = if self.merge {
            let building_yaml = repo_root.join(BUILDING_YAML);
            if building_yaml.exists() {
                Some(building_yaml)
            } else {
                None
            }
        } else {
            None
        };

        let result = import_lidar_path(
            lidar_path,
            existing.as_deref(),
            self.voxel_size,
            self.light,
            true,
        )
        .map_err(|e| format!("LiDAR import failed: {}", e))?;

        if result.validation.has_errors() {
            for line in result.summary_lines() {
                println!("  {}", line);
            }
            return Err("LiDAR import validation failed; refusing to write building.yaml".into());
        }

        if self.dry_run {
            println!("Parsed successfully (dry-run):");
            println!("  Building: {}", result.building.name);
            if let Some(ref metadata) = result.building.metadata {
                if let Some(total) = metadata.properties.get("total_points") {
                    println!("  Total points: {}", total);
                }
            }
            for line in result.summary_lines() {
                println!("  {}", line);
            }
            return Ok(());
        }

        save_building_at(repo_root, &result.building)
            .map_err(|e| anyhow!("Failed to write {}: {}", BUILDING_YAML, e))?;

        println!("Imported successfully to {}", BUILDING_YAML);
        for line in result.summary_lines() {
            println!("  {}", line);
        }

        Ok(())
    }

    fn name(&self) -> &'static str {
        "import-lidar"
    }
}
