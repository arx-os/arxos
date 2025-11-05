//! Grid to Address mapping utilities
//!
//! Provides functions to infer room names from grid coordinates and generate
//! addresses automatically from building context.

use crate::domain::ArxAddress;
use anyhow::{bail, Result};
use std::collections::HashMap;

/// Infer room name from grid coordinate
///
/// This is a simple mapping that can be extended with site-specific data.
/// In production, this would likely load from building configuration or
/// spatial database.
///
/// # Arguments
/// * `grid` - Grid coordinate string (e.g., "D-4", "C-8")
///
/// # Returns
/// * Room name string (e.g., "mech", "kitchen")
pub fn infer_room_from_grid(grid: &str) -> Result<String> {
    // Example mapping – replace with real site data or configuration
    // In production, this would load from building metadata or spatial database
    let mapping: HashMap<&str, &str> = [
        ("D-4", "mech"),
        ("C-8", "kitchen"),
        ("A-1", "lobby"),
        ("B-2", "office"),
        ("E-5", "bathroom"),
    ]
    .iter()
    .cloned()
    .collect();

    Ok(mapping
        .get(grid.to_uppercase().as_str())
        .copied()
        .unwrap_or("unknown")
        .to_string())
}

/// Get next available ID for a fixture in a room
///
/// Returns a simple incremental ID. In production, this would load from
/// persistent counter file (.arxos/counters.toml) and track counters per
/// room/type combination.
///
/// # Arguments
/// * `room` - Room name
/// * `typ` - Equipment type (e.g., "boiler", "ahu")
///
/// # Returns
/// * Next available ID number
pub fn next_id(_room: &str, _typ: &str) -> Result<u32> {
    // Simple implementation: returns 1 for now
    // Future enhancement: load from persistent counter storage
    Ok(1)
}

/// Generate address from building context and grid
///
/// # Arguments
/// * `country` - Country code (defaults to "usa" if None)
/// * `state` - State code (defaults to "ny" if None)
/// * `city` - City name (defaults to "brooklyn" if None)
/// * `building` - Building identifier
/// * `floor` - Floor identifier
/// * `grid` - Grid coordinate (optional)
/// * `room` - Room name (optional, inferred from grid if not provided)
/// * `equipment_type` - Equipment type string
///
/// # Returns
/// * Generated ArxAddress
pub fn generate_address_from_context(
    country: Option<&str>,
    state: Option<&str>,
    city: Option<&str>,
    building: &str,
    floor: &str,
    grid: Option<&str>,
    room: Option<&str>,
    equipment_type: &str,
) -> Result<ArxAddress> {
    let country = country.unwrap_or("usa");
    let state = state.unwrap_or("ny");
    let city = city.unwrap_or("brooklyn");

    let room = if let Some(r) = room {
        r.to_string()
    } else if let Some(g) = grid {
        infer_room_from_grid(g)?
    } else {
        bail!("Either room or grid must be provided");
    };

    let id = next_id(&room, equipment_type)?;
    let fixture = format!("{}-{:02}", equipment_type.to_lowercase(), id);

    Ok(ArxAddress::new(country, state, city, building, floor, &room, &fixture))
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_infer_room_from_grid() {
        assert_eq!(infer_room_from_grid("D-4").unwrap(), "mech");
        assert_eq!(infer_room_from_grid("C-8").unwrap(), "kitchen");
        assert_eq!(infer_room_from_grid("UNKNOWN").unwrap(), "unknown");
    }

    #[test]
    fn test_generate_address_from_context() {
        let addr = generate_address_from_context(
            None,
            None,
            None,
            "ps-118",
            "floor-02",
            Some("D-4"),
            None,
            "boiler",
        )
        .unwrap();
        assert!(addr.path.contains("mech"));
        assert!(addr.path.contains("boiler-01"));
    }

    #[test]
    fn test_generate_address_with_room() {
        let addr = generate_address_from_context(
            Some("usa"),
            Some("ca"),
            Some("san-francisco"),
            "office-building",
            "floor-01",
            None,
            Some("kitchen"),
            "fridge",
        )
        .unwrap();
        assert_eq!(addr.path, "/usa/ca/san-francisco/office-building/floor-01/kitchen/fridge-01");
    }
}

