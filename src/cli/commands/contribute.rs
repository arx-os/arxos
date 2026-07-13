//! Build a contribution package from validated building.yaml (reward path).
//!
//! Does not submit on-chain by default — writes `contribution.json` for oracle
//! operators / later `blockchain` submit. Software remains free; this packages labor.

use super::Command;
use crate::contribution::{build_contribution_package, PackageOptions};
use crate::persistence::{load_building_at, BUILDING_YAML};
use std::error::Error;
use std::path::{Path, PathBuf};

pub struct ContributeCommand {
    pub output: PathBuf,
    pub latitude: Option<f64>,
    pub longitude: Option<f64>,
    pub git_commit: Option<String>,
    pub allow_invalid: bool,
    pub dry_run: bool,
}

impl Command for ContributeCommand {
    fn execute(&self) -> Result<(), Box<dyn Error>> {
        let repo_root = Path::new(".");
        let building = load_building_at(repo_root)
            .map_err(|e| format!("load {}: {}", BUILDING_YAML, e))?;

        let git_commit = self.git_commit.clone().or_else(detect_head_commit);

        let opts = PackageOptions {
            latitude: self.latitude.unwrap_or(0.0),
            longitude: self.longitude.unwrap_or(0.0),
            git_commit,
            require_clean_validation: !self.allow_invalid,
        };

        let package = build_contribution_package(&building, opts)
            .map_err(|e| -> Box<dyn Error> { e.into() })?;

        println!("📦 Contribution package (building data labor)");
        println!("  {}", package.summary);
        println!("  building_id:  {}", package.building_id);
        println!("  merkle_root:  {}", package.merkle_root_hex);
        println!("  content_hash: {}", package.content_hash_hex);
        println!(
            "  quality:      accuracy={} completeness={}",
            package.accuracy, package.completeness
        );
        if let Some(ref c) = package.git_commit {
            println!("  git_commit:   {}", c);
        }
        println!(
            "  algorithm:    {} (on-chain submit may re-encode with keccak under --features blockchain)",
            package.hash_algorithm
        );

        if self.dry_run {
            println!("Dry run — not writing {}", self.output.display());
            return Ok(());
        }

        let json = serde_json::to_string_pretty(&package)?;
        std::fs::write(&self.output, json)?;
        println!("✅ Wrote {}", self.output.display());
        println!("   Next: oracle operators verify package + submit EIP-712 proof (Track F wiring).");
        Ok(())
    }

    fn name(&self) -> &'static str {
        "contribute"
    }
}

fn detect_head_commit() -> Option<String> {
    let repo = git2::Repository::open(".").ok()?;
    let head = repo.head().ok()?;
    let oid = head.peel_to_commit().ok()?.id();
    Some(oid.to_string())
}
