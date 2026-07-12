use crate::core::{Building, Position};

pub struct ModelMerger;

impl ModelMerger {
    pub fn merge(mut existing: Building, incoming: Building) -> Building {
        println!("🔄 Merging new scan into building: {}", existing.name);

        let mut merged_floors_count = 0;
        let mut merged_rooms_count = 0;
        let mut merged_equipment_count = 0;
        let mut added_floors_count = 0;
        let mut added_rooms_count = 0;
        let mut added_equipment_count = 0;

        for incoming_floor in incoming.floors {
            // Find existing floor matching level
            let matched_floor = existing.floors.iter_mut().find(|f| f.level == incoming_floor.level);

            match matched_floor {
                Some(existing_floor) => {
                    merged_floors_count += 1;
                    
                    // Merge wings and rooms
                    for incoming_wing in incoming_floor.wings.clone() {
                        let existing_wing = existing_floor.wings.iter_mut().find(|w| w.name == incoming_wing.name);
                        
                        match existing_wing {
                            Some(w_existing) => {
                                // Merge rooms in this wing
                                for incoming_room in incoming_wing.rooms {
                                    // A room matches if centroids are close (< 2.0 meters)
                                    let matched_room = w_existing.rooms.iter_mut().find(|r| {
                                        let dist = Self::distance(&incoming_room.spatial_properties.position, &r.spatial_properties.position);
                                        dist < 2.0
                                    });

                                    match matched_room {
                                        Some(r_existing) => {
                                            merged_rooms_count += 1;
                                            
                                            // Preserve existing room name/ID, but update spatial geometry to latest scan
                                            r_existing.spatial_properties = incoming_room.spatial_properties;

                                            // Merge equipment
                                            for incoming_eq in incoming_room.equipment {
                                                let matched_eq = r_existing.equipment.iter_mut().find(|e| {
                                                    e.equipment_type == incoming_eq.equipment_type &&
                                                    Self::distance(&e.position, &incoming_eq.position) < 1.5
                                                });

                                                match matched_eq {
                                                    Some(eq_existing) => {
                                                        merged_equipment_count += 1;
                                                        
                                                        // Update existing equipment position & properties
                                                        eq_existing.position = incoming_eq.position;
                                                        eq_existing.properties = incoming_eq.properties;
                                                    }
                                                    None => {
                                                        added_equipment_count += 1;
                                                        
                                                        // Add new equipment to room, keeping its parent room ID reference
                                                        let mut eq_new = incoming_eq.clone();
                                                        eq_new.room_id = Some(r_existing.id.clone());
                                                        r_existing.add_equipment(eq_new);
                                                    }
                                                }
                                            }
                                        }
                                        None => {
                                            added_rooms_count += 1;
                                            w_existing.add_room(incoming_room);
                                        }
                                    }
                                }
                            }
                            None => {
                                // Wing doesn't exist, add the whole wing
                                existing_floor.add_wing(incoming_wing);
                            }
                        }
                    }
                }
                None => {
                    added_floors_count += 1;
                    existing.add_floor(incoming_floor);
                }
            }
        }

        println!("📝 Merge summary:");
        println!("  Floors   : {} matched, {} added", merged_floors_count, added_floors_count);
        println!("  Rooms    : {} matched, {} added", merged_rooms_count, added_rooms_count);
        println!("  Equipment: {} matched, {} added", merged_equipment_count, added_equipment_count);

        existing
    }

    fn distance(p1: &Position, p2: &Position) -> f64 {
        ((p1.x - p2.x).powi(2) + (p1.y - p2.y).powi(2) + (p1.z - p2.z).powi(2)).sqrt()
    }
}
