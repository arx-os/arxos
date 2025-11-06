//! Building documentation generation
//!
//! Generates HTML documentation from building data, similar to rustdoc for code.
//! Produces self-contained HTML files that can be shared and viewed offline.

use crate::yaml::BuildingData;
use crate::core::Equipment;
use crate::utils::loading::load_building_data;
use std::path::Path;
use std::fs;

/// Generate HTML documentation for a building
///
/// # Parameters
///
/// * `building_name` - Name of the building to document
/// * `output_path` - Optional path for output file (default: `./docs/{building}.html`)
///
/// # Returns
///
/// Returns a `Result` indicating success or failure.
///
/// # Errors
///
/// This function can return errors for:
/// * Building data not found
/// * Invalid building data
/// * File system errors (permissions, disk space, etc.)
pub fn generate_building_docs(
    building_name: &str,
    output_path: Option<&str>,
) -> Result<String, Box<dyn std::error::Error>> {
    let building_data = load_building_data(building_name)?;
    
    let html = generate_html(&building_data)?;
    
    let output = output_path.map(String::from).unwrap_or_else(|| {
        let filename = sanitize_filename(building_name);
        format!("./docs/{}.html", filename)
    });
    
    if let Some(parent) = Path::new(&output).parent() {
        fs::create_dir_all(parent)?;
    }
    
    fs::write(&output, &html)?;
    
    Ok(output)
}

/// Generate HTML content from building data
fn generate_html(data: &BuildingData) -> Result<String, Box<dyn std::error::Error>> {
    // Rooms are now in wings
    let room_count: usize = data.floors.iter()
        .flat_map(|f| &f.wings)
        .map(|w| w.rooms.len())
        .sum();
    let room_equipment_count: usize = data.floors.iter()
        .flat_map(|f| &f.wings)
        .flat_map(|w| &w.rooms)
        .map(|r| r.equipment.len())
        .sum();
    let floor_equipment_count: usize = data.floors.iter()
        .map(|f| f.equipment.len())
        .sum();
    let equipment_count = room_equipment_count + floor_equipment_count;
    
    let floors_html = generate_floors_section(data);
    let rooms_html = generate_rooms_section(data);
    let equipment_html = generate_equipment_section(data);
    let ascii_render = generate_ascii_visualization(data);
    
    Ok(format!(r#"<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{name} - Building Documentation</title>
    <style>
        {css}
    </style>
</head>
<body>
    <div class="container">
        <h1>{name}</h1>
        
        <div class="summary">
            <h2>Building Summary</h2>
            <ul>
                <li><strong>Building ID:</strong> {id}</li>
                <li><strong>Floors:</strong> {floor_count}</li>
                <li><strong>Rooms:</strong> {room_count}</li>
                <li><strong>Equipment:</strong> {equipment_count}</li>
                <li><strong>Last Updated:</strong> {updated_at}</li>
                <li><strong>Version:</strong> {version}</li>
            </ul>
        </div>
        
        {description_html}
        
        <div class="section">
            <h2>Floors</h2>
            {floors_html}
        </div>
        
        <div class="section">
            <h2>Rooms</h2>
            {rooms_html}
        </div>
        
        <div class="section">
            <h2>Equipment</h2>
            {equipment_html}
        </div>
        
        <div class="section">
            <h2>Building Visualization</h2>
            <pre class="ascii-render">{ascii_render}</pre>
        </div>
    </div>
</body>
</html>
"#,
        name = html_escape(&data.building.name),
        id = html_escape(&data.building.id),
        floor_count = data.floors.len(),
        room_count = room_count,
        equipment_count = equipment_count,
        updated_at = data.building.updated_at.format("%Y-%m-%d %H:%M:%S UTC"),
        version = html_escape(&data.building.version),
        description_html = if let Some(ref desc) = data.building.description {
            format!(r#"<div class="description"><p>{}</p></div>"#, html_escape(desc))
        } else {
            String::new()
        },
        floors_html = floors_html,
        rooms_html = rooms_html,
        equipment_html = equipment_html,
        ascii_render = html_escape(&ascii_render),
        css = get_css(),
    ))
}

fn generate_floors_section(data: &BuildingData) -> String {
    if data.floors.is_empty() {
        return "<p>No floors defined.</p>".to_string();
    }
    
    data.floors.iter()
        .map(|floor| {
            // Rooms are now in wings
            let room_count: usize = floor.wings.iter()
                .map(|w| w.rooms.len())
                .sum();
            let equipment_count = floor.equipment.len() + floor.wings.iter()
                .flat_map(|w| &w.rooms)
                .map(|r| r.equipment.len())
                .sum::<usize>();
            
            format!(
                r#"<div class="floor-item">
                    <h3>Floor {level}: {name}</h3>
                    <div class="floor-details">
                        <p><strong>Elevation:</strong> {elevation:.2}m</p>
                        <p><strong>Rooms:</strong> {rooms}</p>
                        <p><strong>Equipment:</strong> {equipment}</p>
                    </div>
                </div>"#,
                level = floor.level,
                name = html_escape(&floor.name),
                elevation = floor.elevation.unwrap_or(floor.level as f64 * 3.0),
                rooms = room_count,
                equipment = equipment_count,
            )
        })
        .collect::<Vec<_>>()
        .join("\n")
}

fn generate_rooms_section(data: &BuildingData) -> String {
    // Rooms are now in wings
    let all_rooms: Vec<_> = data.floors.iter()
        .flat_map(|floor| {
            floor.wings.iter()
                .flat_map(|wing| wing.rooms.iter().map(move |room| (floor.level, room)))
        })
        .collect();
    
    if all_rooms.is_empty() {
        return "<p>No rooms defined.</p>".to_string();
    }
    
    all_rooms.iter()
        .map(|(floor_level, room)| {
            // Calculate area and volume from dimensions
            let area = room.spatial_properties.dimensions.width * room.spatial_properties.dimensions.depth;
            let volume = area * room.spatial_properties.dimensions.height;
            let area_str = format!("{:.2}m²", area);
            let volume_str = format!("{:.2}m³", volume);
            let position_str = format!("({:.2}, {:.2}, {:.2})", 
                room.spatial_properties.position.x, 
                room.spatial_properties.position.y, 
                room.spatial_properties.position.z);
            
            format!(
                r#"<div class="room-item">
                    <h4>{name} (Floor {floor})</h4>
                    <div class="room-details">
                        <p><strong>Type:</strong> {type}</p>
                        <p><strong>Area:</strong> {area}</p>
                        <p><strong>Volume:</strong> {volume}</p>
                        <p><strong>Position:</strong> {position}</p>
                        <p><strong>Equipment Count:</strong> {equipment_count}</p>
                    </div>
                </div>"#,
                name = html_escape(&room.name),
                floor = floor_level,
                type = html_escape(&format!("{:?}", room.room_type)),
                area = area_str,
                volume = volume_str,
                position = position_str,
                equipment_count = room.equipment.len(),
            )
        })
        .collect::<Vec<_>>()
        .join("\n")
}

fn generate_equipment_section(data: &BuildingData) -> String {
    let mut all_equipment: Vec<(i32, Option<String>, &Equipment)> = Vec::new();
    
    for floor in &data.floors {
        for eq in &floor.equipment {
            all_equipment.push((floor.level, None, eq));
        }
        
        // Rooms are now in wings
        for wing in &floor.wings {
            for room in &wing.rooms {
                // Room.equipment is now Vec<Equipment>, not Vec<String>
                for eq in &room.equipment {
                    all_equipment.push((floor.level, Some(room.name.clone()), eq));
                }
            }
        }
    }
    
    if all_equipment.is_empty() {
        return "<p>No equipment defined.</p>".to_string();
    }
    
    all_equipment.iter()
        .map(|(floor_level, room_name, eq)| {
            let location = if let Some(room) = room_name {
                format!("Floor {}, Room {}", floor_level, html_escape(room))
            } else {
                format!("Floor {}", floor_level)
            };
            use crate::core::{EquipmentStatus, EquipmentHealthStatus};
            let position_str = format!("({:.2}, {:.2}, {:.2})", eq.position.x, eq.position.y, eq.position.z);
            
            // Use health_status if available, otherwise fall back to status
            let (status_class, status_text) = if let Some(health_status) = &eq.health_status {
                match health_status {
                    EquipmentHealthStatus::Healthy => ("status-healthy", "Healthy"),
                    EquipmentHealthStatus::Warning => ("status-warning", "Warning"),
                    EquipmentHealthStatus::Critical => ("status-critical", "Critical"),
                    EquipmentHealthStatus::Unknown => ("status-unknown", "Unknown"),
                }
            } else {
                match eq.status {
                    EquipmentStatus::Active => ("status-healthy", "Active"),
                    EquipmentStatus::Inactive => ("status-unknown", "Inactive"),
                    EquipmentStatus::Maintenance => ("status-warning", "Maintenance"),
                    EquipmentStatus::OutOfOrder => ("status-critical", "Out of Order"),
                    EquipmentStatus::Unknown => ("status-unknown", "Unknown"),
                }
            };
            
            format!(
                r#"<div class="equipment-item {status_class}">
                    <h4>{name}</h4>
                    <div class="equipment-details">
                        <p><strong>Type:</strong> {type}</p>
                        <p><strong>System:</strong> {system}</p>
                        <p><strong>Status:</strong> <span class="{status_class}">{status}</span></p>
                        <p><strong>Location:</strong> {location}</p>
                        <p><strong>Position:</strong> {position}</p>
                        <p><strong>Path:</strong> <code>{path}</code></p>
                    </div>
                </div>"#,
                name = html_escape(&eq.name),
                type = html_escape(&format!("{:?}", eq.equipment_type)),
                system = html_escape(&eq.system_type()),
                status = status_text,
                location = location,
                position = position_str,
                path = html_escape(&eq.path),
                status_class = status_class,
            )
        })
        .collect::<Vec<_>>()
        .join("\n")
}

fn generate_ascii_visualization(data: &BuildingData) -> String {
    let mut output = String::new();
    
    if data.floors.is_empty() {
        return "No building data available for visualization.".to_string();
    }
    
    for floor in &data.floors {
        output.push_str(&format!("Floor {}: {}\n", floor.level, floor.name));
        output.push_str(&format!("  Elevation: {:.2}m\n", floor.elevation.unwrap_or(floor.level as f64 * 3.0)));
        
        // Rooms are now in wings
        let has_rooms = floor.wings.iter().any(|w| !w.rooms.is_empty());
        if has_rooms {
            output.push_str("  Rooms:\n");
            for wing in &floor.wings {
                for room in &wing.rooms {
                    output.push_str(&format!("    - {} ({:?})\n", room.name, room.room_type));
                    if !room.equipment.is_empty() {
                        for eq in &room.equipment {
                            output.push_str(&format!("      Equipment: {} ({:?})\n", eq.name, eq.equipment_type));
                        }
                    }
                }
            }
        }
        
        if !floor.equipment.is_empty() {
            output.push_str("  Floor Equipment:\n");
            use crate::core::{EquipmentStatus, EquipmentHealthStatus};
            for eq in &floor.equipment {
                let status_str = if let Some(health_status) = &eq.health_status {
                    match health_status {
                        EquipmentHealthStatus::Healthy => "Healthy",
                        EquipmentHealthStatus::Warning => "Warning",
                        EquipmentHealthStatus::Critical => "Critical",
                        EquipmentHealthStatus::Unknown => "Unknown",
                    }
                } else {
                    match eq.status {
                        EquipmentStatus::Active => "Active",
                        EquipmentStatus::Inactive => "Inactive",
                        EquipmentStatus::Maintenance => "Maintenance",
                        EquipmentStatus::OutOfOrder => "Out of Order",
                        EquipmentStatus::Unknown => "Unknown",
                    }
                };
                output.push_str(&format!("    - {} ({:?}) - {}\n", 
                    eq.name, 
                    eq.equipment_type,
                    status_str
                ));
            }
        }
        
        output.push('\n');
    }
    
    output
}

fn html_escape(text: &str) -> String {
    text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace("\"", "&quot;")
        .replace("'", "&#x27;")
}

fn sanitize_filename(name: &str) -> String {
    name.chars()
        .map(|c| if c.is_alphanumeric() || c == '-' || c == '_' {
            c.to_lowercase().collect::<String>()
        } else if c == ' ' {
            "-".to_string()
        } else {
            String::new()
        })
        .collect::<String>()
        .trim_matches('-')
        .to_string()
}

fn get_css() -> &'static str {
    r#"
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: #fff;
        }
        h1 {
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
            margin-bottom: 20px;
        }
        h2 {
            color: #34495e;
            margin-top: 40px;
            margin-bottom: 20px;
        }
        h3 {
            color: #555;
            margin-top: 20px;
        }
        h4 {
            color: #666;
            margin-top: 15px;
        }
        .summary {
            background: #ecf0f1;
            padding: 20px;
            border-radius: 5px;
            margin: 20px 0;
        }
        .summary ul {
            list-style: none;
            padding: 0;
        }
        .summary li {
            padding: 5px 0;
        }
        .description {
            background: #f8f9fa;
            padding: 15px;
            border-left: 4px solid #3498db;
            margin: 20px 0;
            border-radius: 3px;
        }
        .section {
            margin: 30px 0;
        }
        .floor-item, .room-item, .equipment-item {
            background: #f8f9fa;
            padding: 15px;
            margin: 10px 0;
            border-left: 4px solid #3498db;
            border-radius: 3px;
        }
        .floor-details, .room-details, .equipment-details {
            margin-top: 10px;
        }
        .floor-details p, .room-details p, .equipment-details p {
            margin: 5px 0;
        }
        .status-healthy {
            color: #27ae60;
            font-weight: bold;
        }
        .status-warning {
            color: #f39c12;
            font-weight: bold;
        }
        .status-critical {
            color: #e74c3c;
            font-weight: bold;
        }
        .status-unknown {
            color: #7f8c8d;
            font-weight: bold;
        }
        .equipment-item.status-healthy {
            border-left-color: #27ae60;
        }
        .equipment-item.status-warning {
            border-left-color: #f39c12;
        }
        .equipment-item.status-critical {
            border-left-color: #e74c3c;
        }
        .equipment-item.status-unknown {
            border-left-color: #7f8c8d;
        }
        .ascii-render {
            background: #2c3e50;
            color: #ecf0f1;
            padding: 20px;
            border-radius: 5px;
            overflow-x: auto;
            font-family: 'Courier New', 'Monaco', 'Menlo', monospace;
            font-size: 12px;
            line-height: 1.4;
            white-space: pre-wrap;
        }
        pre {
            margin: 0;
        }
        code {
            background: #f4f4f4;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: 'Courier New', monospace;
            font-size: 0.9em;
        }
    "#
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::yaml::{BuildingInfo, BuildingMetadata};
    use chrono::Utc;
    
    fn create_test_building_data() -> BuildingData {
        BuildingData {
            building: BuildingInfo {
                id: "test-building-1".to_string(),
                name: "Test Building".to_string(),
                description: Some("A test building for documentation".to_string()),
                created_at: Utc::now(),
                updated_at: Utc::now(),
                version: "1.0.0".to_string(),
                global_bounding_box: None,
            },
            metadata: BuildingMetadata {
                source_file: None,
                parser_version: "1.0".to_string(),
                total_entities: 0,
                spatial_entities: 0,
                coordinate_system: "WGS84".to_string(),
                units: "meters".to_string(),
                tags: vec![],
            },
            floors: vec![],
            coordinate_systems: vec![],
        }
    }
    
    #[test]
    fn test_html_escape() {
        assert_eq!(html_escape("test"), "test");
        assert_eq!(html_escape("<script>"), "&lt;script&gt;");
        assert_eq!(html_escape("&amp;"), "&amp;amp;");
        assert_eq!(html_escape("\"quote\""), "&quot;quote&quot;");
    }
    
    #[test]
    fn test_sanitize_filename() {
        assert_eq!(sanitize_filename("Test Building"), "test-building");
        assert_eq!(sanitize_filename("Building_123"), "building_123");
        assert_eq!(sanitize_filename("Test@Building#1"), "testbuilding1");
        assert_eq!(sanitize_filename("  Test  "), "test");
    }
    
    #[test]
    fn test_generate_html_empty_building() {
        let data = create_test_building_data();
        let html = generate_html(&data).unwrap();
        
        assert!(html.contains("Test Building"));
        assert!(html.contains("test-building-1"));
        assert!(html.contains("No floors defined"));
        assert!(html.contains("No rooms defined"));
        assert!(html.contains("No equipment defined"));
    }
    
    #[test]
    fn test_generate_floors_section_empty() {
        let data = create_test_building_data();
        let result = generate_floors_section(&data);
        assert_eq!(result, "<p>No floors defined.</p>");
    }
    
    #[test]
    fn test_generate_rooms_section_empty() {
        let data = create_test_building_data();
        let result = generate_rooms_section(&data);
        assert_eq!(result, "<p>No rooms defined.</p>");
    }
    
    #[test]
    fn test_generate_equipment_section_empty() {
        let data = create_test_building_data();
        let result = generate_equipment_section(&data);
        assert_eq!(result, "<p>No equipment defined.</p>");
    }
}

