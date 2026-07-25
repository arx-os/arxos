//! Address-native browse commands: `show`, `ls`, `tree` (ADR 0001).

use crate::core::operations::address_nav::{
    build_tree, format_ls, format_show, format_tree, list_children, resolve,
};
use crate::persistence::{load_building_at, BUILDING_YAML};
use anyhow::{anyhow, Result};
use std::path::PathBuf;

fn load_cwd_building(path: Option<&str>) -> Result<crate::core::Building> {
    let base = path
        .map(PathBuf::from)
        .unwrap_or_else(|| PathBuf::from("."));
    load_building_at(&base).map_err(|e| {
        anyhow!(
            "Failed to load {} under {}: {}",
            BUILDING_YAML,
            base.display(),
            e
        )
    })
}

/// `arx show <address>`
pub fn run_show(address: &str, path: Option<&str>) -> Result<()> {
    let building = load_cwd_building(path)?;
    let entity = resolve(&building, address)?;
    println!("{}", format_show(&entity));
    Ok(())
}

/// `arx ls <address>`
pub fn run_ls(address: &str, path: Option<&str>) -> Result<()> {
    let building = load_cwd_building(path)?;
    let children = list_children(&building, address)?;
    println!("{}", format_ls(&children));
    Ok(())
}

/// `arx tree <address> [--depth N]`
pub fn run_tree(address: &str, depth: usize, path: Option<&str>) -> Result<()> {
    let building = load_cwd_building(path)?;
    let tree = build_tree(&building, address, depth)?;
    println!("{}", format_tree(&tree));
    Ok(())
}
