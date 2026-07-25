//! `arx add <parent> <kind>` — create equipment under an address (ADR 0001).

use crate::core::operations::address_mutate::{add_under_address, AddKind};
use crate::ingest::persist_building_at;
use crate::persistence::{load_building_at, BUILDING_YAML};
use anyhow::{anyhow, Result};
use std::path::PathBuf;

/// `arx add <parent-address> <kind> [--name NAME] [--path DIR]`
pub fn run_add(
    parent: &str,
    kind_str: &str,
    name: Option<&str>,
    path: Option<&str>,
) -> Result<()> {
    let kind = AddKind::parse(kind_str).map_err(|e| anyhow!("{}", e))?;
    let base = path
        .map(PathBuf::from)
        .unwrap_or_else(|| PathBuf::from("."));

    let mut building = load_building_at(&base).map_err(|e| {
        anyhow!(
            "Failed to load {} under {}: {}",
            BUILDING_YAML,
            base.display(),
            e
        )
    })?;

    let result = add_under_address(&mut building, parent, kind, name)
        .map_err(|e| anyhow!("{}", e))?;

    persist_building_at(
        &base,
        building,
        false,
        Some(&format!("add {} at {}", kind.as_str(), result.address.path)),
    )
    .map_err(|e| anyhow!("Failed to save {}: {}", BUILDING_YAML, e))?;

    // Browse-style success output (address primary, no internal UUID)
    println!("type: equipment");
    println!("kind: {}", result.kind.as_str());
    println!("name: {}", result.name);
    println!("address: {}", result.address.path);
    println!("ifc_global_id: (none)");
    println!("status: added");
    Ok(())
}
