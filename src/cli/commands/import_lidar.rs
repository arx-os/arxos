use crate::cli::commands::Command;
use crate::spatial::lidar::LidarPipeline;
use crate::spatial::lidar::merger::ModelMerger;
use crate::yaml::BuildingYamlSerializer;
use crate::utils::path_safety::PathSafety;
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
        println!("🏗️  Importing LiDAR file: {}", self.file_path);
        println!("   Voxel Size: {} m", self.voxel_size);
        if self.light {
            println!("   Mode: Light (optimized for resource limits)");
        }
        if self.dry_run {
            println!("🔍 Dry run mode enabled - no changes will be written");
        }

        let pipeline = LidarPipeline::new(self.voxel_size, self.light);
        let incoming_building = pipeline.process(&self.file_path)?;

        let target_building = if self.merge {
            let existing_name = self.building.as_ref().cloned().unwrap_or_else(|| {
                incoming_building.name.clone()
            });

            let yaml_filename = format!("{}.yaml", existing_name.replace(" ", "_").to_lowercase());
            let yaml_path = Path::new(".").join(&yaml_filename);

            if yaml_path.exists() {
                println!("📂 Loading existing building model from: {}", yaml_path.display());
                let yaml_content = std::fs::read_to_string(&yaml_path)
                    .map_err(|e| anyhow!("Failed to read existing building YAML: {}", e))?;
                let existing_building = BuildingYamlSerializer::deserialize_building(&yaml_content)
                    .map_err(|e| anyhow!("Failed to deserialize existing building: {}", e))?;

                ModelMerger::merge(existing_building, incoming_building)
            } else {
                println!("⚠️  Merge enabled but no existing model found at {}. Creating new building.", yaml_path.display());
                incoming_building
            }
        } else {
            incoming_building
        };

        if self.dry_run {
            println!("✅ Parsed successfully (dry-run):");
            println!("  Building: {}", target_building.name);
            if let Some(ref metadata) = target_building.metadata {
                if let Some(total) = metadata.properties.get("total_points") {
                    println!("  Total points: {}", total);
                }
                if let Some(ds) = metadata.properties.get("downsampled_points") {
                    println!("  Downsampled points: {}", ds);
                }
            }
            return Ok(());
        }

        // Write to YAML in repository root
        let repo_root = Path::new(".");
        let yaml_filename = format!("{}.yaml", target_building.name.replace(" ", "_").to_lowercase());
        let yaml_path = repo_root.join(&yaml_filename);

        PathSafety::validate_path_for_write(&yaml_path).map_err(|e| anyhow!(e))?;

        let yaml_content = BuildingYamlSerializer::serialize_building(&target_building)
            .map_err(|e| anyhow!("Failed to serialize YAML: {}", e))?;

        std::fs::write(&yaml_path, yaml_content)
            .map_err(|e| anyhow!("Failed to write YAML to {}: {}", yaml_path.display(), e))?;

        println!("✅ Imported successfully to {}", yaml_path.display());
        Ok(())
    }

    fn name(&self) -> &'static str {
        "import-lidar"
    }
}
