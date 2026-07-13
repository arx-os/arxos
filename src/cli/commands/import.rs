use crate::cli::commands::Command;
use crate::ingest::import_ifc_path;
use crate::persistence::{save_building_at, BUILDING_YAML};
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
        println!("Importing IFC (compiler spine): {}", self.ifc_file);
        println!("  Policy: vendor BIM → clean IFC export → arx (no CAD plugins)");

        if self.dry_run {
            println!("Dry run mode enabled - no changes will be written");
        }
        if self.strict {
            println!("Strict validation enabled");
        }

        let repo_root = Path::new(".");
        let ifc_path = Path::new(&self.ifc_file);

        let building_yaml = repo_root.join(BUILDING_YAML);
        let existing = if building_yaml.exists() {
            Some(building_yaml.as_path())
        } else {
            None
        };

        let result = import_ifc_path(ifc_path, existing, self.strict, true)
            .map_err(|e| format!("IFC import failed: {}", e))?;

        if result.validation.has_errors() {
            for line in result.summary_lines() {
                println!("  {}", line);
            }
            return Err("Import validation failed; refusing to write building.yaml".into());
        }

        if self.dry_run {
            println!("Parsed successfully:");
            println!("  Building: {}", result.building.name);
            println!("  Floors: {}", result.building.floors.len());
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
        "import"
    }
}
