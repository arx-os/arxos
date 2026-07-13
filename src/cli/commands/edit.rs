//! Apply text / AR command scripts to a building model.

use crate::cli::commands::Command;
use crate::ingest::ingest_text_script;
use crate::persistence::{load_building_at, save_building_at, BUILDING_YAML};
use anyhow::anyhow;
use std::error::Error;
use std::fs;
use std::path::{Path, PathBuf};

pub struct EditCommand {
    /// Path to script file, or "-" for stdin
    pub script: String,
    /// Building YAML path (default: building.yaml)
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

        let (base, yaml_path) = resolve_building_base(self.building.as_deref())?;
        let building =
            load_building_at(&base).map_err(|e| format!("load {}: {}", yaml_path.display(), e))?;

        let result = ingest_text_script(building, &script_body, true)
            .map_err(|e| format!("text edit failed: {}", e))?;

        println!("Text edits applied to {}", yaml_path.display());
        for line in result.summary_lines() {
            println!("  {}", line);
        }

        if result.validation.has_errors() {
            return Err("Edit validation failed; refusing to write building.yaml".into());
        }

        if self.dry_run {
            println!("Dry run — not writing YAML");
            return Ok(());
        }

        save_building_at(&base, &result.building)
            .map_err(|e| anyhow!("save {}: {}", yaml_path.display(), e))?;
        println!("Saved {}", yaml_path.display());
        Ok(())
    }

    fn name(&self) -> &'static str {
        "edit"
    }
}

/// Resolve project base directory and expected `building.yaml` path.
fn resolve_building_base(explicit: Option<&str>) -> Result<(PathBuf, PathBuf), Box<dyn Error>> {
    if let Some(p) = explicit {
        let path = Path::new(p);
        if path.is_dir() {
            let yaml = path.join(BUILDING_YAML);
            if yaml.exists() {
                return Ok((path.to_path_buf(), yaml));
            }
            return Err(format!("no {} in {}", BUILDING_YAML, path.display()).into());
        }
        if path.exists()
            && path
                .file_name()
                .and_then(|n| n.to_str())
                .map(|n| n.eq_ignore_ascii_case(BUILDING_YAML))
                .unwrap_or(false)
        {
            let base = path
                .parent()
                .map(|p| p.to_path_buf())
                .unwrap_or_else(|| PathBuf::from("."));
            return Ok((base, path.to_path_buf()));
        }
        return Err(format!("building SSOT must be {} (got {})", BUILDING_YAML, p).into());
    }

    let base = PathBuf::from(".");
    let yaml = base.join(BUILDING_YAML);
    if !yaml.exists() {
        return Err(format!("no {} found in current directory", BUILDING_YAML).into());
    }
    Ok((base, yaml))
}
