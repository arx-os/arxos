//! Backfill durable ArxAddress values (ADR 0001).

use crate::core::domain::ArxAddress;
use crate::core::Building;

/// Rewrite all entity addresses that sit under `old_root` to use `new_root`.
///
/// Used when applying a postal-derived root to a building that already has
/// lab-style (or other) addresses. Returns the number of entities updated.
pub fn reroot_addresses(building: &mut Building, new_root: &ArxAddress) -> usize {
    let old_root = match building.address.clone() {
        Some(r) => r,
        None => {
            building.address = Some(new_root.clone());
            return 1 + backfill_equipment_addresses(building);
        }
    };
    if old_root.path == new_root.path {
        return 0;
    }
    let mut count = 0usize;
    let mut rewrite = |addr: &mut Option<ArxAddress>| {
        if let Some(a) = addr {
            if let Some(rewritten) = rewrite_path_prefix(&a.path, &old_root.path, &new_root.path) {
                if let Ok(na) = ArxAddress::from_path(&rewritten) {
                    *a = na;
                    count += 1;
                }
            }
        }
    };

    rewrite(&mut building.address);
    for anchor in &mut building.anchors {
        rewrite(&mut anchor.address);
    }
    for floor in &mut building.floors {
        rewrite(&mut floor.address);
        for anchor in &mut floor.anchors {
            rewrite(&mut anchor.address);
        }
        for eq in &mut floor.equipment {
            rewrite(&mut eq.address);
            if let Some(ref a) = eq.address {
                eq.path = a.path.clone();
            }
        }
        for wing in &mut floor.wings {
            rewrite(&mut wing.address);
            for eq in &mut wing.equipment {
                rewrite(&mut eq.address);
                if let Some(ref a) = eq.address {
                    eq.path = a.path.clone();
                }
            }
            for room in &mut wing.rooms {
                rewrite(&mut room.address);
                for eq in &mut room.equipment {
                    rewrite(&mut eq.address);
                    if let Some(ref a) = eq.address {
                        eq.path = a.path.clone();
                    }
                }
                for anchor in &mut room.anchors {
                    rewrite(&mut anchor.address);
                }
            }
        }
    }
    count
}

fn rewrite_path_prefix(path: &str, old_root: &str, new_root: &str) -> Option<String> {
    let old = old_root.trim_end_matches('/');
    let new = new_root.trim_end_matches('/');
    if path == old {
        return Some(new.to_string());
    }
    let prefix = format!("{}/", old);
    if let Some(rest) = path.strip_prefix(&prefix) {
        return Some(format!("{}/{}", new, rest));
    }
    None
}

/// Assign `address` to entities that lack one, using hierarchy context.
///
/// Target layout:
/// `bldg.lab.local.sample.<building-slug>/fl.<n>/rm.<slug>/<equipment-slug>`
///
/// Returns the number of **entities** updated (building, floors, wings, rooms, equipment, anchors).
pub fn backfill_equipment_addresses(building: &mut Building) -> usize {
    let mut count = 0;

    // Building root
    if building.address.is_none() {
        building.address = Some(ArxAddress::lab_building_root(&building.name));
        count += 1;
    }
    let bldg = building
        .address
        .clone()
        .unwrap_or_else(|| ArxAddress::lab_building_root(&building.name));

    for (fi, floor) in building.floors.iter_mut().enumerate() {
        if floor.address.is_none() {
            let seg = ArxAddress::floor_segment(&floor.name, fi);
            if let Ok(addr) = bldg.join(&seg) {
                floor.address = Some(addr);
                count += 1;
            }
        }
        let floor_addr = floor
            .address
            .clone()
            .unwrap_or_else(|| bldg.join(&format!("fl.{}", fi)).expect("fl segment"));

        for anchor in &mut floor.anchors {
            if anchor.address.is_none() {
                let seg = ArxAddress::stable_slug(&anchor.name);
                if let Ok(addr) = floor_addr.join(&seg) {
                    anchor.address = Some(addr);
                    count += 1;
                }
            }
        }

        for eq in &mut floor.equipment {
            if eq.address.is_none() {
                let leaf = ArxAddress::equipment_segment(&eq.name);
                if let Ok(addr) = floor_addr.join(&leaf) {
                    eq.path = addr.path.clone();
                    eq.address = Some(addr);
                    count += 1;
                }
            }
        }

        for wing in &mut floor.wings {
            // Wings are organizational; address optional but fill for navigation
            if wing.address.is_none() {
                let seg = format!("wing.{}", ArxAddress::stable_slug(&wing.name));
                if let Ok(addr) = floor_addr.join(&seg) {
                    wing.address = Some(addr);
                    count += 1;
                }
            }

            for eq in &mut wing.equipment {
                if eq.address.is_none() {
                    let leaf = ArxAddress::equipment_segment(&eq.name);
                    if let Ok(addr) = floor_addr.join(&leaf) {
                        eq.path = addr.path.clone();
                        eq.address = Some(addr);
                        count += 1;
                    }
                }
            }

            for room in &mut wing.rooms {
                if room.address.is_none() {
                    let seg = ArxAddress::room_segment(&room.name);
                    if let Ok(addr) = floor_addr.join(&seg) {
                        room.address = Some(addr);
                        count += 1;
                    }
                }
                let room_addr = room.address.clone().unwrap_or_else(|| {
                    floor_addr
                        .join(&ArxAddress::room_segment(&room.name))
                        .unwrap_or_else(|_| floor_addr.clone())
                });

                for eq in &mut room.equipment {
                    if eq.address.is_none() {
                        let leaf = ArxAddress::equipment_segment(&eq.name);
                        if let Ok(addr) = room_addr.join(&leaf) {
                            eq.path = addr.path.clone();
                            eq.address = Some(addr);
                            count += 1;
                        }
                    }
                }

                for anchor in &mut room.anchors {
                    if anchor.address.is_none() {
                        let seg = ArxAddress::stable_slug(&anchor.name);
                        if let Ok(addr) = room_addr.join(&seg) {
                            anchor.address = Some(addr);
                            count += 1;
                        }
                    }
                }
            }
        }
    }

    // Building-level anchors
    for anchor in &mut building.anchors {
        if anchor.address.is_none() {
            let seg = ArxAddress::stable_slug(&anchor.name);
            if let Ok(addr) = bldg.join(&seg) {
                anchor.address = Some(addr);
                count += 1;
            }
        }
    }

    count
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::core::domain::ArxAddress;
    use crate::core::{Building, Equipment, EquipmentType, Floor, Room, RoomType, Wing};

    #[test]
    fn backfill_assigns_missing_addresses_only() {
        let mut b = Building::new("HQ".into(), "/hq".into());
        let mut floor = Floor::new("Level 1".into(), 0);
        let mut wing = Wing::new("Main".into());
        let mut room = Room::new("A101".into(), RoomType::Office);
        let mut already = Equipment::new("Boiler".into(), String::new(), EquipmentType::HVAC);
        already.address = Some(
            ArxAddress::from_path("bldg.lab.local.sample.hq/fl.1/rm.a101/keep-me").unwrap(),
        );
        room.add_equipment(already);
        room.add_equipment(Equipment::new(
            "Pump".into(),
            String::new(),
            EquipmentType::Plumbing,
        ));
        wing.add_room(room);
        floor.add_wing(wing);
        b.add_floor(floor);

        let n = backfill_equipment_addresses(&mut b);
        assert!(n >= 1);
        assert!(b.address.is_some());
        assert!(b.address.as_ref().unwrap().path.starts_with("/bldg.lab.local.sample."));
        let room = &b.floors[0].wings[0].rooms[0];
        assert!(room.address.is_some());
        assert!(room.address.as_ref().unwrap().path.contains("/rm."));
        // Preserved existing
        assert_eq!(
            room.equipment[0].address.as_ref().unwrap().path,
            "/bldg.lab.local.sample.hq/fl.1/rm.a101/keep-me"
        );
        // Filled missing
        assert!(room.equipment[1].address.is_some());
    }

    #[test]
    fn reroot_lab_to_postal() {
        use crate::core::domain::postal_building_root_from_str;
        let mut b = Building::new("HQ".into(), "/hq".into());
        let lab = ArxAddress::lab_building_root("hq");
        b.address = Some(lab.clone());
        let mut floor = Floor::new("Level 1".into(), 1);
        floor.address = Some(lab.join("fl.1").unwrap());
        let mut wing = Wing::new("Main".into());
        let mut room = Room::new("A101".into(), RoomType::Office);
        room.address = Some(floor.address.as_ref().unwrap().join("rm.a101").unwrap());
        wing.add_room(room);
        floor.add_wing(wing);
        b.add_floor(floor);

        let postal = postal_building_root_from_str(
            "143677 N. Dale Mabry Hwy, Suite 2, Tampa, FL, 33622",
        )
        .unwrap();
        let n = reroot_addresses(&mut b, &postal);
        assert!(n >= 3);
        assert_eq!(
            b.address.as_ref().unwrap().path,
            "/bldg.us.fl.tampa.dale-mabry.143677.s2"
        );
        assert_eq!(
            b.floors[0].address.as_ref().unwrap().path,
            "/bldg.us.fl.tampa.dale-mabry.143677.s2/fl.1"
        );
        assert_eq!(
            b.floors[0].wings[0].rooms[0]
                .address
                .as_ref()
                .unwrap()
                .path,
            "/bldg.us.fl.tampa.dale-mabry.143677.s2/fl.1/rm.a101"
        );
    }
}
