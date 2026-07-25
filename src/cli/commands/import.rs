use crate::cli::commands::Command;
use crate::core::domain::{resolve_building_root_from_options, ArxAddress};
use crate::ingest::import_ifc_path_with_root;
use crate::persistence::{save_building_at, BUILDING_YAML};
use anyhow::anyhow;
use std::error::Error;
use std::path::Path;

pub struct ImportCommand {
    pub ifc_file: String,
    pub repo: Option<String>,
    pub dry_run: bool,
    pub strict: bool,
    pub postal: Option<String>,
    pub country: Option<String>,
    pub region: Option<String>,
    pub city: Option<String>,
    pub street: Option<String>,
    pub number: Option<String>,
    pub unit: Option<String>,
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

        let building_root: Option<ArxAddress> = resolve_building_root_from_options(
            self.postal.as_deref(),
            self.country.as_deref(),
            self.region.as_deref(),
            self.city.as_deref(),
            self.street.as_deref(),
            self.number.as_deref(),
            self.unit.as_deref(),
        )
        .map_err(|e| format!("postal root: {}", e))?;
        if let Some(ref root) = building_root {
            println!("  Building root (postal): {}", root.path);
        }

        let repo_root = Path::new(".");
        let ifc_path = Path::new(&self.ifc_file);

        let building_yaml = repo_root.join(BUILDING_YAML);
        let existing = if building_yaml.exists() {
            Some(building_yaml.as_path())
        } else {
            None
        };

        let result = import_ifc_path_with_root(ifc_path, existing, self.strict, true, building_root)
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
