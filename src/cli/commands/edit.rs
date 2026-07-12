//! Apply text / AR command scripts to a building model.

use crate::cli::commands::Command;
use crate::ingest::ingest_text_script;
use crate::utils::path_safety::PathSafety;
use crate::yaml::BuildingYamlSerializer;
use anyhow::anyhow;
use std::error::Error;
use std::fs;
use std::path::Path;

pub struct EditCommand {
    /// Path to script file, or "-" for stdin
    pub script: String,
    /// Building YAML path (default: first building.yaml / named yaml)
    pub building: Option<String>,
    pub dry_run: bool,
}

impl Command for EditCommand {
    fn execute(&self) -> Result<(), Box<dyn Error>> {
        let script_body = if self.script == "-" {
            use std::io::Read;
            let mut buf = String::new();
            std::io::stdin().read_to_string(&mut buf)?;
            buf
        } else {
            fs::read_to_string(&self.script)
                .map_err(|e| format!("read script {}: {}", self.script, e))?
        };

        let yaml_path = resolve_building_yaml(self.building.as_deref())?;
        let yaml = fs::read_to_string(&yaml_path)
            .map_err(|e| format!("read {}: {}", yaml_path.display(), e))?;
        let building = BuildingYamlSerializer::deserialize_building(&yaml)
            .map_err(|e| format!("deserialize building: {}", e))?;

        let result = ingest_text_script(building, &script_body, true)
            .map_err(|e| format!("text edit failed: {}", e))?;

        println!("Text edits applied to {}", yaml_path.display());
        for line in result.summary_lines() {
            println!("  {}", line);
        }

        if self.dry_run {
            println!("Dry run — not writing YAML");
            return Ok(());
        }

        PathSafety::validate_path_for_write(&yaml_path).map_err(|e| anyhow!(e))?;
        let out = BuildingYamlSerializer::serialize_building(&result.building)
            .map_err(|e| anyhow!("serialize: {}", e))?;
        fs::write(&yaml_path, out)?;
        println!("Saved {}", yaml_path.display());
        Ok(())
    }

    fn name(&self) -> &'static str {
        "edit"
    }
}

fn resolve_building_yaml(explicit: Option<&str>) -> Result<std::path::PathBuf, Box<dyn Error>> {
    if let Some(p) = explicit {
        let path = Path::new(p);
        if path.exists() {
            return Ok(path.to_path_buf());
        }
        // Treat as building name
        let candidate = Path::new(".").join(format!(
            "{}.yaml",
            p.replace(' ', "_").to_lowercase()
        ));
        if candidate.exists() {
            return Ok(candidate);
        }
        return Err(format!("building YAML not found: {}", p).into());
    }
    let building_yaml = Path::new("building.yaml");
    if building_yaml.exists() {
        return Ok(building_yaml.to_path_buf());
    }
    // First *.yaml in cwd that deserializes
    for entry in fs::read_dir(".")? {
        let entry = entry?;
        let path = entry.path();
        if path.extension().and_then(|e| e.to_str()) == Some("yaml")
            || path.extension().and_then(|e| e.to_str()) == Some("yml")
        {
            if let Ok(contents) = fs::read_to_string(&path) {
                if BuildingYamlSerializer::deserialize_building(&contents).is_ok() {
                    return Ok(path);
                }
            }
        }
    }
    Err("no building YAML found (pass --building path)".into())
}
