use crate::cli::commands::Command;
use crate::ingest::import_lidar_path;
use crate::utils::path_safety::PathSafety;
use crate::yaml::BuildingYamlSerializer;
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
            let name_hint = self.building.clone().unwrap_or_default();
            let candidates = [
                if !name_hint.is_empty() {
                    Some(repo_root.join(format!(
                        "{}.yaml",
                        name_hint.replace(' ', "_").to_lowercase()
                    )))
                } else {
                    None
                },
                Some(repo_root.join("building.yaml")),
            ];
            candidates
                .into_iter()
                .flatten()
                .find(|p| p.exists())
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

        let yaml_filename = format!(
            "{}.yaml",
            result.building.name.replace(' ', "_").to_lowercase()
        );
        let yaml_path = repo_root.join(&yaml_filename);
        PathSafety::validate_path_for_write(&yaml_path).map_err(|e| anyhow!(e))?;

        let yaml_content = BuildingYamlSerializer::serialize_building(&result.building)
            .map_err(|e| anyhow!("Failed to serialize YAML: {}", e))?;
        std::fs::write(&yaml_path, yaml_content)
            .map_err(|e| anyhow!("Failed to write YAML to {}: {}", yaml_path.display(), e))?;

        println!("Imported successfully to {}", yaml_path.display());
        for line in result.summary_lines() {
            println!("  {}", line);
        }

        Ok(())
    }

    fn name(&self) -> &'static str {
        "import-lidar"
    }
}
