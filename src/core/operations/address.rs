//! Backfill durable `ArxAddress` values on Building equipment.

use crate::core::domain::ArxAddress;
use crate::core::Building;

/// Assign `address` (and `path`) to equipment that lack one, using hierarchy context.
///
/// Layout: `/local/local/local/{building}/{floor}/{room}/{fixture}`
/// where fixture is derived from the equipment name. Room segments that would
/// fail reserved-system validation fall back to `items`.
///
/// Returns the number of equipment items updated.
pub fn backfill_equipment_addresses(building: &mut Building) -> usize {
    let building_slug = slug(&building.name);
    let mut count = 0;

    for floor in &mut building.floors {
        let floor_slug = if floor.name.trim().is_empty() {
            format!("floor-{}", floor.level)
        } else {
            slug(&floor.name)
        };

        // Floor-level equipment (no room)
        for eq in &mut floor.equipment {
            if eq.address.is_some() {
                continue;
            }
            if let Some(addr) = make_address(&building_slug, &floor_slug, "common", &eq.name) {
                eq.path = addr.path.clone();
                eq.address = Some(addr);
                count += 1;
            }
        }

        for wing in &mut floor.wings {
            for eq in &mut wing.equipment {
                if eq.address.is_some() {
                    continue;
                }
                let room_slug = slug(&wing.name);
                if let Some(addr) = make_address(&building_slug, &floor_slug, &room_slug, &eq.name)
                {
                    eq.path = addr.path.clone();
                    eq.address = Some(addr);
                    count += 1;
                }
            }

            for room in &mut wing.rooms {
                let room_slug = slug(&room.name);
                for eq in &mut room.equipment {
                    if eq.address.is_some() {
                        continue;
                    }
                    if let Some(addr) =
                        make_address(&building_slug, &floor_slug, &room_slug, &eq.name)
                    {
                        eq.path = addr.path.clone();
                        eq.address = Some(addr);
                        count += 1;
                    }
                }
            }
        }
    }

    count
}

fn slug(s: &str) -> String {
    let s = s.trim().to_lowercase();
    if s.is_empty() {
        return "unknown".into();
    }
    s.chars()
        .map(|c| {
            if c.is_ascii_alphanumeric() || c == '-' || c == '_' {
                c
            } else {
                '-'
            }
        })
        .collect::<String>()
        .split('-')
        .filter(|p| !p.is_empty())
        .collect::<Vec<_>>()
        .join("-")
}

fn make_address(building: &str, floor: &str, room: &str, fixture: &str) -> Option<ArxAddress> {
    let fixture = slug(fixture);
    let room = slug(room);
    let floor = slug(floor);
    let building = slug(building);

    let candidates = [
        ArxAddress::new(
            "local", "local", "local", &building, &floor, &room, &fixture,
        ),
        // Reserved-system rooms may reject arbitrary fixture names — use open bucket.
        ArxAddress::new(
            "local", "local", "local", &building, &floor, "items", &fixture,
        ),
    ];

    candidates.into_iter().find(|addr| addr.validate().is_ok())
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::core::{Equipment, EquipmentType, Floor, Room, RoomType, Wing};

    #[test]
    fn backfill_assigns_missing_addresses_only() {
        let mut b = Building::new("PS 118".into(), "/ps".into());
        let mut floor = Floor::new("Floor 2".into(), 2);
        let mut wing = Wing::new("Main".into());
        let mut room = Room::new("Mech".into(), RoomType::Mechanical);

        let eq = Equipment::new("Boiler 01".into(), String::new(), EquipmentType::HVAC);
        assert!(eq.address.is_none());
        room.add_equipment(eq);

        let mut already = Equipment::new("Panel".into(), String::new(), EquipmentType::Electrical);
        already.address = Some(ArxAddress::new(
            "usa", "ny", "brooklyn", "ps-118", "floor-02", "elec", "panel-01",
        ));
        room.add_equipment(already);

        wing.add_room(room);
        floor.add_wing(wing);
        b.add_floor(floor);

        let n = backfill_equipment_addresses(&mut b);
        assert_eq!(n, 1, "only missing address should be filled");

        let all = b.get_all_equipment();
        let boiler = all.iter().find(|e| e.name == "Boiler 01").unwrap();
        assert!(boiler.address.is_some());
        assert!(boiler.address.as_ref().unwrap().path.contains("boiler-01"));

        let panel = all.iter().find(|e| e.name == "Panel").unwrap();
        assert_eq!(
            panel.address.as_ref().unwrap().path,
            "/usa/ny/brooklyn/ps-118/floor-02/elec/panel-01"
        );
    }
}
