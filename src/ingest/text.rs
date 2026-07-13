//! Text / AR command script → building mutations.
//!
//! A small deterministic DSL (one command per line) for edits from CLI, agents,
//! AR apps, or chat. After applying, always run [`crate::ingest::finalize_ingest`].
//!
//! # Grammar (case-insensitive keywords)
//!
//! ```text
//! add room <name> floor=<n|name> [wing=<name>] [type=<room_type>] [pos=x,y,z] [dims=WxDxH]
//! add equipment <name> room=<room_name> [type=<eq_type>] [pos=x,y,z]
//! set room <name> <key>=<value> [...]
//! set equipment <name> status=<status> | <key>=<value>
//! rename room <old_name> <new_name>
//! # comment
//! ```

use std::collections::HashMap;

use anyhow::{anyhow, bail, Context, Result};

use crate::core::{
    Building, Dimensions, Equipment, EquipmentStatus, EquipmentType, Floor, Position, Room,
    RoomType, Wing,
};
use crate::ifc::mapping::spatial_from_position_dims;
use crate::ifc::mapping::COORD_BUILDING_LOCAL;

/// One parsed edit operation.
#[derive(Debug, Clone)]
pub enum TextEdit {
    AddRoom {
        name: String,
        floor: String,
        wing: Option<String>,
        room_type: RoomType,
        position: Option<Position>,
        dimensions: Option<Dimensions>,
    },
    AddEquipment {
        name: String,
        room: String,
        equipment_type: EquipmentType,
        position: Option<Position>,
    },
    SetRoomProps {
        name: String,
        props: HashMap<String, String>,
    },
    SetEquipment {
        name: String,
        status: Option<EquipmentStatus>,
        props: HashMap<String, String>,
    },
    RenameRoom {
        old_name: String,
        new_name: String,
    },
}

/// Summary of applied text edits.
#[derive(Debug, Clone, Default)]
pub struct TextEditReport {
    pub applied: usize,
    pub messages: Vec<String>,
}

/// Parse a multi-line script into edits (blank lines and `#` comments skipped).
pub fn parse_text_script(script: &str) -> Result<Vec<TextEdit>> {
    let mut edits = Vec::new();
    for (i, raw) in script.lines().enumerate() {
        let line = raw.trim();
        if line.is_empty() || line.starts_with('#') {
            continue;
        }
        let edit = parse_text_line(line).with_context(|| format!("line {}: {}", i + 1, line))?;
        edits.push(edit);
    }
    Ok(edits)
}

/// Parse a single command line.
pub fn parse_text_line(line: &str) -> Result<TextEdit> {
    let line = line.trim();
    let lower = line.to_ascii_lowercase();

    if lower.starts_with("add room ") {
        return parse_add_room(&line[9..]);
    }
    if lower.starts_with("add equipment ") {
        return parse_add_equipment(&line[14..]);
    }
    if lower.starts_with("set room ") {
        return parse_set_room(&line[9..]);
    }
    if lower.starts_with("set equipment ") {
        return parse_set_equipment(&line[14..]);
    }
    if lower.starts_with("rename room ") {
        return parse_rename_room(&line[12..]);
    }

    bail!("unknown command (expected add room|add equipment|set room|set equipment|rename room)");
}

/// Apply edits to `building` in order.
pub fn apply_text_edits(building: &mut Building, edits: &[TextEdit]) -> Result<TextEditReport> {
    let mut report = TextEditReport::default();
    for edit in edits {
        apply_one(building, edit, &mut report)?;
        report.applied += 1;
    }
    Ok(report)
}

/// Parse script, apply to building, return edit report.
pub fn apply_text_script(building: &mut Building, script: &str) -> Result<TextEditReport> {
    let edits = parse_text_script(script)?;
    apply_text_edits(building, &edits)
}

fn apply_one(building: &mut Building, edit: &TextEdit, report: &mut TextEditReport) -> Result<()> {
    match edit {
        TextEdit::AddRoom {
            name,
            floor,
            wing,
            room_type,
            position,
            dimensions,
        } => {
            let floor_ref = ensure_floor(building, floor)?;
            let wing_name = wing.clone().unwrap_or_else(|| "Main".to_string());
            if !floor_ref.wings.iter().any(|w| w.name == wing_name) {
                floor_ref.add_wing(Wing::new(wing_name.clone()));
            }
            let wing_ref = floor_ref
                .wings
                .iter_mut()
                .find(|w| w.name == wing_name)
                .unwrap();
            if wing_ref.rooms.iter().any(|r| r.name == *name) {
                bail!("room '{}' already exists on floor '{}'", name, floor);
            }
            let mut room = Room::new(name.clone(), room_type.clone());
            if let (Some(pos), Some(dims)) = (position, dimensions) {
                room.spatial_properties = spatial_from_position_dims(pos.clone(), dims.clone());
            } else if let Some(pos) = position {
                room.spatial_properties.position = pos.clone();
                room.spatial_properties.coordinate_system = COORD_BUILDING_LOCAL.to_string();
            } else if let Some(dims) = dimensions {
                let pos = room.spatial_properties.position.clone();
                room.spatial_properties = spatial_from_position_dims(pos, dims.clone());
            }
            wing_ref.add_room(room);
            report
                .messages
                .push(format!("added room '{}' on floor '{}'", name, floor));
        }
        TextEdit::AddEquipment {
            name,
            room,
            equipment_type,
            position,
        } => {
            let room_ref = find_room_mut(building, room)
                .ok_or_else(|| anyhow!("room '{}' not found", room))?;
            if room_ref.equipment.iter().any(|e| e.name == *name) {
                bail!("equipment '{}' already in room '{}'", name, room);
            }
            let mut eq = Equipment::new(name.clone(), String::new(), equipment_type.clone());
            if let Some(pos) = position {
                eq.position = pos.clone();
            }
            eq.room_id = Some(room_ref.id.clone());
            room_ref.add_equipment(eq);
            report
                .messages
                .push(format!("added equipment '{}' in room '{}'", name, room));
        }
        TextEdit::SetRoomProps { name, props } => {
            let room = find_room_mut(building, name)
                .ok_or_else(|| anyhow!("room '{}' not found", name))?;
            for (k, v) in props {
                match k.as_str() {
                    "type" => {
                        room.room_type = parse_room_type(v)?;
                    }
                    "pos" | "position" => {
                        room.spatial_properties.position = parse_position(v, COORD_BUILDING_LOCAL)?;
                    }
                    "dims" | "dimensions" => {
                        let dims = parse_dimensions(v)?;
                        let pos = room.spatial_properties.position.clone();
                        room.spatial_properties = spatial_from_position_dims(pos, dims);
                    }
                    _ => {
                        room.properties.insert(k.clone(), v.clone());
                    }
                }
            }
            report.messages.push(format!("updated room '{}'", name));
        }
        TextEdit::SetEquipment {
            name,
            status,
            props,
        } => {
            let eq = find_equipment_mut(building, name)
                .ok_or_else(|| anyhow!("equipment '{}' not found", name))?;
            if let Some(s) = status {
                eq.status = *s;
            }
            for (k, v) in props {
                match k.as_str() {
                    "status" => eq.status = parse_status(v)?,
                    "pos" | "position" => {
                        eq.position = parse_position(v, COORD_BUILDING_LOCAL)?;
                    }
                    "type" => eq.equipment_type = parse_eq_type(v)?,
                    _ => {
                        eq.properties.insert(k.clone(), v.clone());
                    }
                }
            }
            report
                .messages
                .push(format!("updated equipment '{}'", name));
        }
        TextEdit::RenameRoom { old_name, new_name } => {
            let room = find_room_mut(building, old_name)
                .ok_or_else(|| anyhow!("room '{}' not found", old_name))?;
            room.name = new_name.clone();
            report
                .messages
                .push(format!("renamed room '{}' → '{}'", old_name, new_name));
        }
    }
    Ok(())
}

fn ensure_floor<'a>(building: &'a mut Building, floor_key: &str) -> Result<&'a mut Floor> {
    if let Ok(level) = floor_key.parse::<i32>() {
        if let Some(i) = building.floors.iter().position(|f| f.level == level) {
            return Ok(&mut building.floors[i]);
        }
        let mut f = Floor::new(format!("Floor {}", level), level);
        f.level = level;
        building.add_floor(f);
        return Ok(building.floors.last_mut().unwrap());
    }
    if let Some(i) = building.floors.iter().position(|f| f.name == floor_key) {
        return Ok(&mut building.floors[i]);
    }
    // Create by name with next level
    let level = building
        .floors
        .iter()
        .map(|f| f.level)
        .max()
        .map(|l| l + 1)
        .unwrap_or(0);
    building.add_floor(Floor::new(floor_key.to_string(), level));
    Ok(building.floors.last_mut().unwrap())
}

fn find_room_mut<'a>(building: &'a mut Building, name: &str) -> Option<&'a mut Room> {
    for floor in &mut building.floors {
        for wing in &mut floor.wings {
            if let Some(r) = wing.rooms.iter_mut().find(|r| r.name == name) {
                return Some(r);
            }
        }
    }
    None
}

fn find_equipment_mut<'a>(building: &'a mut Building, name: &str) -> Option<&'a mut Equipment> {
    for floor in &mut building.floors {
        if let Some(e) = floor.equipment.iter_mut().find(|e| e.name == name) {
            return Some(e);
        }
        for wing in &mut floor.wings {
            if let Some(e) = wing.equipment.iter_mut().find(|e| e.name == name) {
                return Some(e);
            }
            for room in &mut wing.rooms {
                if let Some(e) = room.equipment.iter_mut().find(|e| e.name == name) {
                    return Some(e);
                }
            }
        }
    }
    None
}

// --- parsing helpers ---

fn parse_add_room(rest: &str) -> Result<TextEdit> {
    let (name, kvs) = split_name_and_kvs(rest)?;
    let floor = kvs
        .get("floor")
        .cloned()
        .ok_or_else(|| anyhow!("add room requires floor=<n|name>"))?;
    let wing = kvs.get("wing").cloned();
    let room_type = kvs
        .get("type")
        .map(|s| parse_room_type(s))
        .transpose()?
        .unwrap_or(RoomType::Office);
    let position = kvs
        .get("pos")
        .or_else(|| kvs.get("position"))
        .map(|s| parse_position(s, COORD_BUILDING_LOCAL))
        .transpose()?;
    let dimensions = kvs
        .get("dims")
        .or_else(|| kvs.get("dimensions"))
        .map(|s| parse_dimensions(s))
        .transpose()?;
    Ok(TextEdit::AddRoom {
        name,
        floor,
        wing,
        room_type,
        position,
        dimensions,
    })
}

fn parse_add_equipment(rest: &str) -> Result<TextEdit> {
    let (name, kvs) = split_name_and_kvs(rest)?;
    let room = kvs
        .get("room")
        .cloned()
        .ok_or_else(|| anyhow!("add equipment requires room=<name>"))?;
    let equipment_type = kvs
        .get("type")
        .map(|s| parse_eq_type(s))
        .transpose()?
        .unwrap_or(EquipmentType::Other("Unknown".into()));
    let position = kvs
        .get("pos")
        .or_else(|| kvs.get("position"))
        .map(|s| parse_position(s, COORD_BUILDING_LOCAL))
        .transpose()?;
    Ok(TextEdit::AddEquipment {
        name,
        room,
        equipment_type,
        position,
    })
}

fn parse_set_room(rest: &str) -> Result<TextEdit> {
    let (name, kvs) = split_name_and_kvs(rest)?;
    if kvs.is_empty() {
        bail!("set room requires at least one key=value");
    }
    Ok(TextEdit::SetRoomProps { name, props: kvs })
}

fn parse_set_equipment(rest: &str) -> Result<TextEdit> {
    let (name, kvs) = split_name_and_kvs(rest)?;
    let status = kvs.get("status").map(|s| parse_status(s)).transpose()?;
    Ok(TextEdit::SetEquipment {
        name,
        status,
        props: kvs,
    })
}

fn parse_rename_room(rest: &str) -> Result<TextEdit> {
    let parts: Vec<&str> = rest.split_whitespace().collect();
    if parts.len() < 2 {
        bail!("rename room requires <old_name> <new_name>");
    }
    // Support quoted multi-word: "Old Name" "New Name"
    let tokens = tokenize(rest);
    if tokens.len() != 2 {
        bail!("rename room requires exactly two names (quote multi-word names)");
    }
    Ok(TextEdit::RenameRoom {
        old_name: tokens[0].clone(),
        new_name: tokens[1].clone(),
    })
}

fn split_name_and_kvs(rest: &str) -> Result<(String, HashMap<String, String>)> {
    let tokens = tokenize(rest);
    if tokens.is_empty() {
        bail!("missing name");
    }
    let mut name_parts = Vec::new();
    let mut kvs = HashMap::new();
    let mut seen_kv = false;
    for t in tokens {
        if let Some((k, v)) = t.split_once('=') {
            seen_kv = true;
            kvs.insert(k.trim().to_ascii_lowercase(), v.trim().to_string());
        } else if !seen_kv {
            name_parts.push(t);
        } else {
            bail!("positional token '{}' after key=value", t);
        }
    }
    if name_parts.is_empty() {
        bail!("missing name");
    }
    Ok((name_parts.join(" "), kvs))
}

/// Split on whitespace respecting simple double quotes.
fn tokenize(s: &str) -> Vec<String> {
    let mut out = Vec::new();
    let mut cur = String::new();
    let mut in_quotes = false;
    for c in s.chars() {
        match c {
            '"' => in_quotes = !in_quotes,
            c if c.is_whitespace() && !in_quotes => {
                if !cur.is_empty() {
                    out.push(std::mem::take(&mut cur));
                }
            }
            _ => cur.push(c),
        }
    }
    if !cur.is_empty() {
        out.push(cur);
    }
    out
}

fn parse_position(input: &str, coordinate_system: &str) -> Result<Position> {
    let parts: Vec<&str> = input
        .split([',', ' '])
        .filter(|s| !s.is_empty())
        .collect();
    if parts.len() != 3 {
        bail!("position must be x,y,z");
    }
    Ok(Position {
        x: parts[0].parse()?,
        y: parts[1].parse()?,
        z: parts[2].parse()?,
        coordinate_system: coordinate_system.to_string(),
    })
}

fn parse_dimensions(input: &str) -> Result<Dimensions> {
    let cleaned = input.replace('X', "x");
    let parts: Vec<&str> = cleaned.split('x').collect();
    if parts.len() != 3 {
        bail!("dimensions must be WxDxH");
    }
    Ok(Dimensions {
        width: parts[0].trim().parse()?,
        depth: parts[1].trim().parse()?,
        height: parts[2].trim().parse()?,
    })
}

fn parse_room_type(s: &str) -> Result<RoomType> {
    Ok(match s.trim().to_ascii_lowercase().as_str() {
        "office" => RoomType::Office,
        "classroom" => RoomType::Classroom,
        "laboratory" | "lab" => RoomType::Laboratory,
        "corridor" | "hallway" => RoomType::Hallway,
        "restroom" | "bathroom" => RoomType::Restroom,
        "storage" => RoomType::Storage,
        "mechanical" => RoomType::Mechanical,
        other => RoomType::Other(other.to_string()),
    })
}

fn parse_eq_type(s: &str) -> Result<EquipmentType> {
    Ok(match s.trim().to_ascii_lowercase().as_str() {
        "hvac" => EquipmentType::HVAC,
        "electrical" => EquipmentType::Electrical,
        "av" => EquipmentType::AV,
        "furniture" => EquipmentType::Furniture,
        "safety" => EquipmentType::Safety,
        "plumbing" => EquipmentType::Plumbing,
        "network" => EquipmentType::Network,
        other => EquipmentType::Other(other.to_string()),
    })
}

fn parse_status(s: &str) -> Result<EquipmentStatus> {
    Ok(match s.trim().to_ascii_lowercase().as_str() {
        "active" => EquipmentStatus::Active,
        "inactive" => EquipmentStatus::Inactive,
        "maintenance" => EquipmentStatus::Maintenance,
        "outoforder" | "out_of_order" | "out-of-order" => EquipmentStatus::OutOfOrder,
        "unknown" => EquipmentStatus::Unknown,
        other => bail!("unknown status '{}'", other),
    })
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn parse_add_room_and_equipment() {
        let edits = parse_text_script(
            r#"
            # setup
            add room "Studio A" floor=0 type=office pos=1,2,0 dims=4x5x3
            add equipment cam-1 room="Studio A" type=av pos=1.5,2.5,2
            set room "Studio A" finish=epoxy
            set equipment cam-1 status=maintenance brand=Sony
            "#,
        )
        .unwrap();
        assert_eq!(edits.len(), 4);

        let mut b = Building::new("HQ".into(), "/hq".into());
        let report = apply_text_edits(&mut b, &edits).unwrap();
        assert_eq!(report.applied, 4);
        assert_eq!(b.floors.len(), 1);
        let room = &b.floors[0].wings[0].rooms[0];
        assert_eq!(room.name, "Studio A");
        assert!((room.spatial_properties.dimensions.width - 4.0).abs() < 1e-9);
        assert_eq!(
            room.properties.get("finish").map(String::as_str),
            Some("epoxy")
        );
        assert_eq!(room.equipment[0].name, "cam-1");
        assert_eq!(room.equipment[0].status, EquipmentStatus::Maintenance);
    }

    #[test]
    fn rename_room() {
        let mut b = Building::new("HQ".into(), "/hq".into());
        let mut floor = Floor::new("F0".into(), 0);
        let mut wing = Wing::new("Main".into());
        wing.add_room(Room::new("Old".into(), RoomType::Office));
        floor.add_wing(wing);
        b.add_floor(floor);
        apply_text_script(&mut b, "rename room Old New").unwrap();
        assert_eq!(b.floors[0].wings[0].rooms[0].name, "New");
    }
}
