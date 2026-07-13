//! One-shot migration: fill missing durable `ArxAddress` on equipment.

use super::Command;
use crate::core::operations::backfill_equipment_addresses;
use crate::ingest::persist_building_at;
use crate::persistence::{load_building_at, BUILDING_YAML};
use std::error::Error;
use std::path::PathBuf;

/// Backfill missing equipment addresses on the Building SSOT.
pub struct MigrateCommand {
    pub dry_run: bool,
    /// Project root containing building.yaml (default: cwd)
    pub path: Option<PathBuf>,
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

        let updated = backfill_equipment_addresses(&mut building);
        println!("🔄 Address backfill: {} equipment updated", updated);

        if updated == 0 {
            println!("✅ Nothing to migrate — all equipment already has addresses");
            return Ok(());
        }

        if self.dry_run {
            println!("Dry run — not writing {}", BUILDING_YAML);
            for eq in building.get_all_equipment() {
                if let Some(addr) = &eq.address {
                    println!("  would keep/set {} → {}", eq.name, addr.path);
                }
            }
            return Ok(());
        }

        // Path-aware persist — does not mutate process cwd (Track I10).
        persist_building_at(
            &base,
            building,
            false,
            Some("migrate: backfill equipment ArxAddress"),
        )?;
        println!("✅ Wrote addresses to {}", BUILDING_YAML);
        Ok(())
    }

    fn name(&self) -> &'static str {
        "migrate"
    }
}
