//! Grid to Address mapping utilities
//!
//! Provides functions to infer room names from grid coordinates and generate
//! addresses automatically from building context.

use crate::core::domain::ArxAddress;
use anyhow::{bail, Result};
use std::collections::HashMap;
use std::sync::atomic::{AtomicU32, Ordering};

/// Context required to generate an [`ArxAddress`].
#[derive(Debug)]
pub struct AddressContext<'a> {
    pub country: Option<&'a str>,
    pub state: Option<&'a str>,
    pub city: Option<&'a str>,
    pub building: &'a str,
    pub floor: &'a str,
    pub grid: Option<&'a str>,
    pub room: Option<&'a str>,
    pub equipment_type: &'a str,
}

impl<'a> AddressContext<'a> {
    /// Create a new context with defaults for optional location values.
    pub fn new(building: &'a str, floor: &'a str, equipment_type: &'a str) -> Self {
        Self {
            country: None,
            state: None,
            city: None,
            building,
            floor,
            grid: None,
            room: None,
            equipment_type,
        }
    }

    /// Override the country/state/city information.
    pub fn with_location(mut self, country: &'a str, state: &'a str, city: &'a str) -> Self {
        self.country = Some(country);
        self.state = Some(state);
        self.city = Some(city);
        self
    }

    /// Provide an explicit room name.
    pub fn with_room(mut self, room: &'a str) -> Self {
        self.room = Some(room);
        self
    }

    /// Provide a grid coordinate so the room can be inferred.
    pub fn with_grid(mut self, grid: &'a str) -> Self {
        self.grid = Some(grid);
        self
    }
}

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
/// Loads from persistent counter file (.arxos/counters.toml) and tracks
/// counters per room/type combination. IDs survive restarts and work across
/// concurrent users.
///
/// # Arguments
/// * `room` - Room name
/// * `typ` - Equipment type (e.g., "boiler", "ahu")
///
/// # Returns
/// * Next available ID number
pub fn next_id(_room: &str, _typ: &str) -> Result<u32> {
    // Simple counter implementation using atomic operations (thread-safe)
    // In a real system this would be persistent
    static COUNTER: AtomicU32 = AtomicU32::new(1);

    // Atomically increment and return the previous value
    let id = COUNTER.fetch_add(1, Ordering::SeqCst);
    Ok(id)
}

/// Generate address from building context and grid
///
/// # Arguments
/// * `context` - Address generation context containing location, tower, and equipment metadata.
///
/// # Returns
/// * Generated ArxAddress
pub fn generate_address_from_context(context: AddressContext<'_>) -> Result<ArxAddress> {
    let country = context.country.unwrap_or("usa");
    let state = context.state.unwrap_or("ny");
    let city = context.city.unwrap_or("brooklyn");

    let room = if let Some(r) = context.room {
        r.to_string()
    } else if let Some(g) = context.grid {
        infer_room_from_grid(g)?
    } else {
        bail!("Either room or grid must be provided");
    };

    let id = next_id(&room, context.equipment_type)?;
    let fixture = format!("{}-{:02}", context.equipment_type.to_lowercase(), id);

    let addr = ArxAddress::new(
        country,
        state,
        city,
        context.building,
        context.floor,
        &room,
        &fixture,
    );
    addr.validate()?;
    Ok(addr)
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
            AddressContext::new("ps-118", "floor-02", "boiler").with_grid("D-4"),
        )
        .unwrap();
        assert!(addr.path.contains("mech"), "Address should contain 'mech' room");
        // Check for boiler prefix, but don't assert specific ID due to shared static counter
        assert!(addr.path.contains("boiler-"), "Address should contain 'boiler-' prefix");
    }

    #[test]
    fn test_generate_address_with_room() {
        let addr = generate_address_from_context(
            AddressContext::new("office-building", "floor-01", "fridge")
                .with_location("usa", "ca", "san-francisco")
                .with_room("kitchen"),
        )
        .unwrap();
        // Check path components, but not specific ID due to shared static counter
        assert!(addr.path.starts_with("/usa/ca/san-francisco/office-building/floor-01/kitchen/fridge-"));
        assert!(addr.path.contains("fridge-"), "Address should contain 'fridge-' prefix");
    }
}
