//! One-shot migration: fill missing durable `ArxAddress` / apply postal root.

use super::Command;
use crate::core::domain::resolve_building_root_from_options;
use crate::core::operations::{backfill_equipment_addresses, reroot_addresses};
use crate::ingest::persist_building_at;
use crate::persistence::{load_building_at, BUILDING_YAML};
use std::error::Error;
use std::path::PathBuf;

/// Backfill missing addresses and optionally re-root from postal data.
pub struct MigrateCommand {
    pub dry_run: bool,
    /// Project root containing building.yaml (default: cwd)
    pub path: Option<PathBuf>,
    pub postal: Option<String>,
    pub country: Option<String>,
    pub region: Option<String>,
    pub city: Option<String>,
    pub street: Option<String>,
    pub number: Option<String>,
    pub unit: Option<String>,
}

impl Command for MigrateCommand {
    fn execute(&self) -> Result<(), Box<dyn Error>> {
        let base = self.path.clone().unwrap_or_else(|| PathBuf::from("."));

        let mut building = load_building_at(&base).map_err(|e| {
            format!(
                "Failed to load {} under {}: {}",
                BUILDING_YAML,
                base.display(),
                e
            )
        })?;

        let mut updated = 0usize;

        if let Some(root) = resolve_building_root_from_options(
            self.postal.as_deref(),
            self.country.as_deref(),
            self.region.as_deref(),
            self.city.as_deref(),
            self.street.as_deref(),
            self.number.as_deref(),
            self.unit.as_deref(),
        )
        .map_err(|e| format!("postal root: {}", e))?
        {
            let n = reroot_addresses(&mut building, &root);
            println!("🔄 Postal re-root → {}: {} entities updated", root.path, n);
            updated += n;
        }

        let filled = backfill_equipment_addresses(&mut building);
        println!("🔄 Address backfill: {} entities filled", filled);
        updated += filled;

        if updated == 0 {
            println!("✅ Nothing to migrate — addresses already complete");
            return Ok(());
        }

        if self.dry_run {
            println!("Dry run — not writing {}", BUILDING_YAML);
            if let Some(ref a) = building.address {
                println!("  building root would be {}", a.path);
            }
            return Ok(());
        }

        persist_building_at(
            &base,
            building,
            false,
            Some("migrate: backfill / postal re-root ArxAddress"),
        )?;
        println!("✅ Wrote addresses to {}", BUILDING_YAML);
        Ok(())
    }

    fn name(&self) -> &'static str {
        "migrate"
    }
}
