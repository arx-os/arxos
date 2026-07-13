//! Query command: match equipment by durable `ArxAddress` glob patterns.

use super::Command;
use crate::cli::args::{QueryArgs, SearchArgs};
use crate::core::Equipment;
use crate::persistence::load_building_data_from_dir;
use std::error::Error;

/// Search building data command (text search; see `Cli::handle_search` for live path).
pub struct SearchCommand {
    pub args: SearchArgs,
}

impl Command for SearchCommand {
    fn execute(&self) -> Result<(), Box<dyn Error>> {
        // Primary path is `Commands::Search` → `Cli::handle_search`.
        // This type remains for args packaging / tests.
        println!("🔍 Searching for: \"{}\"", self.args.query);
        Ok(())
    }

    fn name(&self) -> &'static str {
        "search"
    }
}

/// Query equipment by ArxAddress glob pattern against durable Building SSOT.
pub struct QueryCommand {
    pub args: QueryArgs,
}

impl Command for QueryCommand {
    fn execute(&self) -> Result<(), Box<dyn Error>> {
        self.validate()?;
        run_address_query(&self.args.pattern, &self.args.format, self.args.verbose)
    }

    fn name(&self) -> &'static str {
        "query"
    }

    fn validate(&self) -> Result<(), Box<dyn Error>> {
        if !self.args.pattern.starts_with('/') {
            return Err("ArxAddress pattern must start with '/'".into());
        }
        match self.args.format.as_str() {
            "table" | "json" | "yaml" => Ok(()),
            _ => Err(format!(
                "Invalid format: {}. Must be table, json, or yaml",
                self.args.format
            )
            .into()),
        }
    }
}

/// Load Building and return equipment whose durable `address` matches `pattern`.
pub fn query_equipment_by_address(pattern: &str) -> Result<Vec<Equipment>, Box<dyn Error>> {
    let building = load_building_data_from_dir()?;
    let mut matches = Vec::new();

    for item in building.get_all_equipment() {
        if let Some(addr) = &item.address {
            if addr.matches_glob(pattern) {
                matches.push(item.clone());
            }
        }
    }

    Ok(matches)
}

/// Run address query and print results.
pub fn run_address_query(pattern: &str, format: &str, verbose: bool) -> Result<(), Box<dyn Error>> {
    println!("🔍 Query pattern: {}", pattern);
    println!();

    // Segment count check (allow * wildcards as segments)
    let parts: Vec<&str> = pattern.trim_start_matches('/').split('/').collect();
    if parts.len() != 7 {
        return Err(format!(
            "Invalid ArxAddress pattern. Expected 7 parts, got {}.\nFormat: /country/state/city/building/floor/room/fixture",
            parts.len()
        )
        .into());
    }

    // Validate glob syntax
    if glob::Pattern::new(pattern).is_err() {
        return Err(format!("Invalid glob pattern: {}", pattern).into());
    }

    let matches = query_equipment_by_address(pattern)?;

    if matches.is_empty() {
        println!("❌ No equipment found matching pattern");
        println!("   (equipment must have a durable `address` field in building.yaml)");
        return Ok(());
    }

    match format {
        "json" => {
            println!("{}", serde_json::to_string_pretty(&matches)?);
        }
        "yaml" => {
            println!("{}", serde_yaml::to_string(&matches)?);
        }
        _ => {
            println!("📦 Equipment ({} found):", matches.len());
            println!();
            println!("  {:<28} {:<12} {:<50}", "Name", "Type", "Address");
            println!("  {}", "-".repeat(92));

            for item in &matches {
                let eq_type = format!("{:?}", item.equipment_type);
                let name = truncate(&item.name, 26);
                let addr = item
                    .address
                    .as_ref()
                    .map(|a| a.path.as_str())
                    .unwrap_or("-");
                let addr_disp = truncate(addr, 48);
                println!(
                    "  {:<28} {:<12} {:<50}",
                    name,
                    truncate(&eq_type, 10),
                    addr_disp
                );

                if verbose {
                    println!("     id: {}", item.id);
                    if !item.properties.is_empty() {
                        for (key, value) in item.properties.iter().take(5) {
                            println!("       {}: {}", key, value);
                        }
                    }
                    println!();
                }
            }

            println!();
            println!("✅ Total: {} result(s)", matches.len());
        }
    }

    Ok(())
}

fn truncate(s: &str, max: usize) -> String {
    if s.len() > max {
        format!("{}...", &s[..max.saturating_sub(3)])
    } else {
        s.to_string()
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::core::domain::ArxAddress;
    use crate::core::{Building, Equipment, EquipmentType, Floor, Room, RoomType, Wing};
    use crate::persistence::{save_building_at, BUILDING_YAML};
    use serial_test::serial;
    use std::env;
    use std::path::PathBuf;
    use tempfile::tempdir;

    #[test]
    #[serial]
    fn test_query_matches_durable_address() {
        let tmp = tempdir().unwrap();
        let dir = tmp.path();

        let mut building = Building::new("Query HQ".into(), "/q".into());
        let mut eq = Equipment::new("Boiler-01".into(), String::new(), EquipmentType::HVAC);
        let addr = ArxAddress::new(
            "usa",
            "ny",
            "brooklyn",
            "ps-118",
            "floor-02",
            "mech",
            "boiler-01",
        );
        eq.address = Some(addr);
        let mut room = Room::new("mech".into(), RoomType::Mechanical);
        eq.set_room(room.id.clone());
        room.add_equipment(eq);
        let mut wing = Wing::new("Main".into());
        wing.add_room(room);
        let mut floor = Floor::new("Floor 2".into(), 2);
        floor.add_wing(wing);
        building.add_floor(floor);

        save_building_at(dir, &building).unwrap();

        let original = env::current_dir().unwrap_or_else(|_| PathBuf::from("."));
        env::set_current_dir(dir).unwrap();

        let matches = query_equipment_by_address("/usa/ny/*/floor-*/mech/boiler-*").expect("query");
        assert_eq!(matches.len(), 1);
        assert_eq!(matches[0].name, "Boiler-01");

        let none = query_equipment_by_address("/usa/ca/*/floor-*/mech/*").expect("query");
        assert!(none.is_empty());

        assert!(dir.join(BUILDING_YAML).exists());
        env::set_current_dir(original).unwrap();
    }
}
