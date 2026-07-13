use crate::cli::commands::Command;
use crate::core::{filter_building_for_export, summarize_review};
use crate::export::ifc::IFCExporter;
use crate::ifc::mapping::report_export_losses;
use crate::persistence::{load_building_at, BUILDING_YAML};
use crate::utils::path_safety::PathSafety;
use anyhow::anyhow;
use std::error::Error;
use std::path::{Path, PathBuf};

pub struct ExportCommand {
    pub format: String,
    pub output: Option<String>,
    /// Project root with building.yaml (default: cwd)
    pub path: Option<String>,
    pub repo: Option<String>,
    /// When true, drop rejected + proposed LiDAR auto entities from IFC export (Track C2).
    pub approved_only: bool,
    /// Commercial export: require access-receipt.json (N7 host gate).
    pub commercial: bool,
    /// Path to access receipt (default: access-receipt.json).
    pub access_receipt: Option<String>,
}

impl Command for ExportCommand {
    fn execute(&self) -> Result<(), Box<dyn Error>> {
        let _ = &self.repo; // reserved for future remote export

        let repo_root: PathBuf = self
            .path
            .as_ref()
            .map(PathBuf::from)
            .unwrap_or_else(|| PathBuf::from("."));

        match self.format.as_str() {
            "ifc" => {
                println!("📤 Exporting to IFC (compiler spine: export::ifc)...");
                if self.path.is_some() {
                    println!("  Project: {}", repo_root.display());
                }

                let mut building = load_building_at(&repo_root)
                    .map_err(|e| format!("No {} under {}: {}", BUILDING_YAML, repo_root.display(), e))?;

                if self.commercial {
                    let receipt_path = self
                        .access_receipt
                        .as_deref()
                        .unwrap_or(crate::access::DEFAULT_RECEIPT_FILE);
                    // Resolve receipt relative to project root when not absolute
                    let receipt_resolved = {
                        let p = Path::new(receipt_path);
                        if p.is_absolute() {
                            p.to_path_buf()
                        } else {
                            repo_root.join(p)
                        }
                    };
                    let receipt =
                        crate::access::require_access_receipt(&receipt_resolved, &building.id)
                            .map_err(|e| {
                                format!(
                                    "commercial export refused (N7 host gate): {}. \
                                     Buyer must `arx access pay` and write access-receipt.json",
                                    e
                                )
                            })?;
                    println!(
                        "  🔐 commercial: access receipt OK (tx={})",
                        receipt.tx_hash
                    );
                }

                // Deterministic product GlobalIds for stable re-export (docs/identity.md).
                crate::ifc::mapping::assign_missing_global_ids(&mut building);

                let review = summarize_review(&building);
                for line in review.warning_lines() {
                    println!("  {}", line);
                }
                if self.approved_only {
                    println!(
                        "  --approved-only: excluding proposed and rejected LiDAR auto entities"
                    );
                }

                let export_building = filter_building_for_export(&building, self.approved_only);

                let output_file = self
                    .output
                    .clone()
                    .unwrap_or_else(|| format!("{}.ifc", building.name));
                let output_path = {
                    let p = Path::new(&output_file);
                    if p.is_absolute() {
                        p.to_path_buf()
                    } else {
                        repo_root.join(p)
                    }
                };

                PathSafety::validate_path_for_write(&output_path).map_err(|e| anyhow!(e))?;

                if let Some(parent) = output_path.parent() {
                    if !parent.as_os_str().is_empty() && !parent.exists() {
                        std::fs::create_dir_all(parent)?;
                    }
                }

                let export_notes = report_export_losses(&export_building);
                let exporter = IFCExporter::new(export_building);
                exporter.export(&output_path).map_err(|e| anyhow!(e))?;

                println!("Export successful: {}", output_path.display());
                for line in export_notes.summary_lines() {
                    println!("  {}", line);
                }
                Ok(())
            }
            "yaml" => {
                println!("📤 Exporting to YAML format...");
                if self.commercial {
                    let building = load_building_at(&repo_root).map_err(|e| {
                        format!("No {} under {}: {}", BUILDING_YAML, repo_root.display(), e)
                    })?;
                    let receipt_path = self
                        .access_receipt
                        .as_deref()
                        .unwrap_or(crate::access::DEFAULT_RECEIPT_FILE);
                    let receipt_resolved = {
                        let p = Path::new(receipt_path);
                        if p.is_absolute() {
                            p.to_path_buf()
                        } else {
                            repo_root.join(p)
                        }
                    };
                    crate::access::require_access_receipt(&receipt_resolved, &building.id).map_err(
                        |e| format!("commercial export refused (N7 host gate): {}", e),
                    )?;
                    println!("  🔐 commercial: access receipt OK");
                }
                let output_file = self
                    .output
                    .clone()
                    .unwrap_or_else(|| BUILDING_YAML.to_string());
                let output_path = {
                    let p = Path::new(&output_file);
                    if p.is_absolute() {
                        p.to_path_buf()
                    } else {
                        repo_root.join(p)
                    }
                };
                let source_path = repo_root.join(BUILDING_YAML);

                if !source_path.exists() {
                    return Err(format!(
                        "No {} found under {}",
                        BUILDING_YAML,
                        repo_root.display()
                    )
                    .into());
                }

                if output_path.canonicalize().ok() == source_path.canonicalize().ok() {
                    println!("⚠️  Source and destination are the same file");
                } else {
                    if let Some(parent) = output_path.parent() {
                        if !parent.as_os_str().is_empty() && !parent.exists() {
                            std::fs::create_dir_all(parent)?;
                        }
                    }
                    std::fs::copy(&source_path, &output_path)?;
                    println!("✅ Export successful: {}", output_path.display());
                }
                Ok(())
            }
            "json" => {
                println!("📤 Exporting to JSON format...");
                let output_file = self
                    .output
                    .clone()
                    .unwrap_or_else(|| "building.json".to_string());
                let output_path = {
                    let p = Path::new(&output_file);
                    if p.is_absolute() {
                        p.to_path_buf()
                    } else {
                        repo_root.join(p)
                    }
                };
                let source_path = repo_root.join(BUILDING_YAML);

                if !source_path.exists() {
                    return Err(format!(
                        "No {} found under {}",
                        BUILDING_YAML,
                        repo_root.display()
                    )
                    .into());
                }

                let yaml_content = std::fs::read_to_string(&source_path)?;
                let yaml_value: serde_yaml::Value = serde_yaml::from_str(&yaml_content)?;
                let json_content = serde_json::to_string_pretty(&yaml_value)?;

                if let Some(parent) = output_path.parent() {
                    if !parent.as_os_str().is_empty() && !parent.exists() {
                        std::fs::create_dir_all(parent)?;
                    }
                }
                std::fs::write(&output_path, json_content)?;
                println!("✅ Export successful: {}", output_path.display());
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
