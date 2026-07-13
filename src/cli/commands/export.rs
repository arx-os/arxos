use crate::cli::commands::Command;
use crate::export::ifc::IFCExporter;
use crate::ifc::mapping::report_export_losses;
use crate::persistence::{load_building_at, BUILDING_YAML};
use crate::utils::path_safety::PathSafety;
use anyhow::anyhow;
use std::error::Error;
use std::path::Path;

pub struct ExportCommand {
    pub format: String,
    pub output: Option<String>,
    pub repo: Option<String>,
    pub delta: bool,
}

impl Command for ExportCommand {
    fn execute(&self) -> Result<(), Box<dyn Error>> {
        if self.delta {
            return Err(
                "export --delta is not implemented (no silent ignore). \
                 Export a full model, or remove --delta."
                    .into(),
            );
        }

        let repo_root = Path::new(".");

        match self.format.as_str() {
            "ifc" => {
                println!("📤 Exporting to IFC format...");

                let building = load_building_at(repo_root)
                    .map_err(|e| format!("No {} to export: {}", BUILDING_YAML, e))?;

                let output_file = self
                    .output
                    .clone()
                    .unwrap_or_else(|| format!("{}.ifc", building.name));
                let output_path = repo_root.join(&output_file);

                PathSafety::validate_path_for_write(&output_path).map_err(|e| anyhow!(e))?;

                let export_notes = report_export_losses(&building);
                let exporter = IFCExporter::new(building);
                exporter.export(&output_path).map_err(|e| anyhow!(e))?;

                println!("Export successful: {}", output_path.display());
                for line in export_notes.summary_lines() {
                    println!("  {}", line);
                }
                Ok(())
            }
            "yaml" => {
                println!("📤 Exporting to YAML format...");
                let output_file = self
                    .output
                    .clone()
                    .unwrap_or_else(|| BUILDING_YAML.to_string());
                let output_path = repo_root.join(&output_file);
                let source_path = repo_root.join(BUILDING_YAML);

                if !source_path.exists() {
                    return Err(format!("No {} found to export", BUILDING_YAML).into());
                }

                if output_file != BUILDING_YAML {
                    std::fs::copy(&source_path, &output_path)?;
                    println!("✅ Export successful: {}", output_file);
                } else {
                    println!("⚠️  Source and destination are the same file");
                }
                Ok(())
            }
            "json" => {
                println!("📤 Exporting to JSON format...");
                let output_file = self
                    .output
                    .clone()
                    .unwrap_or_else(|| "building.json".to_string());
                let output_path = repo_root.join(&output_file);
                let source_path = repo_root.join(BUILDING_YAML);

                if !source_path.exists() {
                    return Err(format!("No {} found to export", BUILDING_YAML).into());
                }

                let yaml_content = std::fs::read_to_string(&source_path)?;
                let yaml_value: serde_yaml::Value = serde_yaml::from_str(&yaml_content)?;
                let json_content = serde_json::to_string_pretty(&yaml_value)?;

                std::fs::write(&output_path, json_content)?;
                println!("✅ Export successful: {}", output_file);
                Ok(())
            }
            _ => Err(format!(
                "Unsupported export format: '{}'. Use: ifc, yaml, json",
                self.format
            )
            .into()),
        }
    }

    fn name(&self) -> &'static str {
        "export"
    }
}
