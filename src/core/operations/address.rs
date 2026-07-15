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

    // 1. Backfill Building address
    if building.address.is_none() {
        if let Ok(addr) = ArxAddress::from_path(&format!("/local/local/local/{}", building_slug)) {
            building.address = Some(addr);
        }
    }
    let bldg_addr_prefix = building.address.as_ref().map(|a| a.path.clone())
        .unwrap_or_else(|| format!("/local/local/local/{}", building_slug));

    // 2. Backfill Building-level anchors
    for anchor in &mut building.anchors {
        if anchor.address.is_none() {
            let anchor_slug = slug(&anchor.name);
            if let Ok(addr) = ArxAddress::from_path(&format!("{}/{}", bldg_addr_prefix, anchor_slug)) {
                anchor.address = Some(addr);
            }
        }
    }

    for floor in &mut building.floors {
        let floor_slug = if floor.name.trim().is_empty() {
            format!("floor-{}", floor.level)
        } else {
            slug(&floor.name)
        };

        // Backfill Floor address
        if floor.address.is_none() {
            if let Ok(addr) = ArxAddress::from_path(&format!("{}/{}", bldg_addr_prefix, floor_slug)) {
                floor.address = Some(addr);
            }
        }
        let floor_addr_prefix = floor.address.as_ref().map(|a| a.path.clone())
            .unwrap_or_else(|| format!("{}/{}", bldg_addr_prefix, floor_slug));

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

        // Floor-level anchors
        for anchor in &mut floor.anchors {
            if anchor.address.is_none() {
                let anchor_slug = slug(&anchor.name);
                if let Ok(addr) = ArxAddress::from_path(&format!("{}/{}", floor_addr_prefix, anchor_slug)) {
                    anchor.address = Some(addr);
                }
            }
        }

        for wing in &mut floor.wings {
            let wing_slug = slug(&wing.name);

            // Backfill Wing address
            if wing.address.is_none() {
                if let Ok(addr) = ArxAddress::from_path(&format!("{}/{}", floor_addr_prefix, wing_slug)) {
                    wing.address = Some(addr);
                }
            }
            let wing_addr_prefix = wing.address.as_ref().map(|a| a.path.clone())
                .unwrap_or_else(|| format!("{}/{}", floor_addr_prefix, wing_slug));

            for eq in &mut wing.equipment {
                if eq.address.is_some() {
                    continue;
                }
                if let Some(addr) = make_address(&building_slug, &floor_slug, &wing_slug, &eq.name)
                {
                    eq.path = addr.path.clone();
                    eq.address = Some(addr);
                    count += 1;
                }
            }

            for anchor in &mut wing.anchors {
                if anchor.address.is_none() {
                    let anchor_slug = slug(&anchor.name);
                    if let Ok(addr) = ArxAddress::from_path(&format!("{}/{}", wing_addr_prefix, anchor_slug)) {
                        anchor.address = Some(addr);
                    }
                }
            }

            for room in &mut wing.rooms {
                let room_slug = slug(&room.name);

                // Backfill Room address
                if room.address.is_none() {
                    if let Ok(addr) = ArxAddress::from_path(&format!("{}/{}", wing_addr_prefix, room_slug)) {
                        room.address = Some(addr);
                    }
                }
                let room_addr_prefix = room.address.as_ref().map(|a| a.path.clone())
                    .unwrap_or_else(|| format!("{}/{}", wing_addr_prefix, room_slug));

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

                for anchor in &mut room.anchors {
                    if anchor.address.is_none() {
                        let anchor_slug = slug(&anchor.name);
                        if let Ok(addr) = ArxAddress::from_path(&format!("{}/{}", room_addr_prefix, anchor_slug)) {
                            anchor.address = Some(addr);
                        }
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
