use crate::cli::commands::Command;
use crate::ingest::import_ifc_path;
use crate::utils::path_safety::PathSafety;
use crate::yaml::BuildingYamlSerializer;
use anyhow::anyhow;
use std::error::Error;
use std::path::Path;

pub struct ImportCommand {
    pub ifc_file: String,
    pub repo: Option<String>,
    pub dry_run: bool,
    pub strict: bool,
}

impl Command for ImportCommand {
    fn execute(&self) -> Result<(), Box<dyn Error>> {
        println!("Importing IFC file: {}", self.ifc_file);

        if self.dry_run {
            println!("Dry run mode enabled - no changes will be written");
        }
        if self.strict {
            println!("Strict validation enabled");
        }

        let repo_root = Path::new(".");
        let ifc_path = Path::new(&self.ifc_file);

        // Candidate existing YAML for merge (name not known until parse — try building.yaml + stem)
        let stem_yaml = ifc_path
            .file_stem()
            .and_then(|s| s.to_str())
            .map(|s| {
                repo_root.join(format!(
                    "{}.yaml",
                    s.replace(' ', "_").to_lowercase()
                ))
            });
        let building_yaml = repo_root.join("building.yaml");
        let existing = if building_yaml.exists() {
            Some(building_yaml.as_path())
        } else {
            stem_yaml.as_ref().map(|p| p.as_path())
        };

        let result = import_ifc_path(ifc_path, existing, self.strict, true)
            .map_err(|e| format!("IFC import failed: {}", e))?;

        if self.dry_run {
            println!("Parsed successfully:");
            println!("  Building: {}", result.building.name);
            println!("  Floors: {}", result.building.floors.len());
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
        "import"
    }
}
