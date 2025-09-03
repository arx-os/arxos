//! Database to Mesh Network Bridge
//! 
//! This enables field technicians to query the building database
//! through the mesh network using simple text commands.

use crate::database_impl::ArxDatabase;
use crate::arxobject::ArxObject;
use crate::mesh_network::MeshNode;
use crate::error::Result;

/// Bridge between database and mesh network
pub struct DatabaseMeshBridge {
    database: ArxDatabase,
    mesh_node: MeshNode,
    building_id: u16,
}

impl DatabaseMeshBridge {
    pub fn new(database: ArxDatabase, mesh_node: MeshNode, building_id: u16) -> Self {
        Self {
            database,
            mesh_node,
            building_id,
        }
    }
    
    /// Process text query from field tech
    pub async fn process_query(&self, query: &str, sender_id: u32) -> Result<String> {
        // Parse natural language query
        let query_lower = query.to_lowercase();
        
        let response = if query_lower.contains("room") {
            // "What's in room 127?"
            self.query_room(&query_lower).await
        } else if query_lower.contains("outlet") {
            // "Find outlets"
            self.query_outlets().await
        } else if query_lower.contains("floor") {
            // "Second floor equipment"
            self.query_floor(&query_lower).await
        } else if query_lower.contains("maintenance") {
            // "What needs maintenance?"
            self.query_maintenance().await
        } else if query_lower.contains("near") {
            // "What's near me?"
            self.query_nearby(sender_id).await
        } else {
            Ok(format!("Unknown query: '{}'. Try: 'room 127', 'outlets', 'maintenance'", query))
        };
        
        response
    }
    
    /// Query room contents
    async fn query_room(&self, query: &str) -> Result<String> {
        // Extract room number
        let room_number = query
            .split_whitespace()
            .find_map(|word| word.parse::<u32>().ok())
            .unwrap_or(0);
        
        // Approximate room bounds (would be more sophisticated in production)
        let room_x = (room_number % 10) as f32 * 5000.0; // 5m grid
        let room_y = (room_number / 10) as f32 * 5000.0;
        
        let objects = self.database.find_in_bounds(
            room_x,
            room_x + 5000.0,
            room_y,
            room_y + 5000.0,
            0.0,
            3000.0,
        )?;
        
        self.format_objects_response(&objects, &format!("Room {}", room_number))
    }
    
    /// Query all outlets
    async fn query_outlets(&self) -> Result<String> {
        let outlets = self.database.query(
            "SELECT * FROM arxobjects WHERE object_type = ?1 AND building_id = ?2",
            params![crate::arxobject::object_types::OUTLET, self.building_id],
        )?;
        
        self.format_objects_response(&outlets, "Outlets")
    }
    
    /// Query floor contents
    async fn query_floor(&self, query: &str) -> Result<String> {
        let floor_num = if query.contains("second") || query.contains("2nd") {
            2
        } else if query.contains("third") || query.contains("3rd") {
            3
        } else {
            1
        };
        
        let min_z = (floor_num - 1) as f32 * 3000.0;
        let max_z = floor_num as f32 * 3000.0;
        
        let objects = self.database.query(
            "SELECT * FROM arxobjects 
             WHERE z >= ?1 AND z <= ?2 AND building_id = ?3",
            params![min_z as u16, max_z as u16, self.building_id],
        )?;
        
        self.format_objects_response(&objects, &format!("Floor {}", floor_num))
    }
    
    /// Query maintenance needs
    async fn query_maintenance(&self) -> Result<String> {
        let needs_maintenance = self.database.query(
            "SELECT * FROM arxobjects 
             WHERE building_id = ?1
             AND object_type IN (?2, ?3, ?4)
             AND (properties[0] > 200 OR properties[1] > 180)",
            params![
                self.building_id,
                crate::arxobject::object_types::HVAC_VENT,
                crate::arxobject::object_types::ELECTRICAL_PANEL,
                crate::arxobject::object_types::LIGHT,
            ],
        )?;
        
        if needs_maintenance.is_empty() {
            Ok("✅ No equipment needs immediate maintenance".to_string())
        } else {
            let mut response = format!("⚠️ {} items need maintenance:\n", needs_maintenance.len());
            for obj in needs_maintenance.iter().take(5) {
                response.push_str(&format!(
                    "  • {} at ({:.1}m, {:.1}m, {:.1}m)\n",
                    self.object_type_name(obj.object_type),
                    obj.x as f32 / 1000.0,
                    obj.y as f32 / 1000.0,
                    obj.z as f32 / 1000.0,
                ));
            }
            Ok(response)
        }
    }
    
    /// Query objects near the sender
    async fn query_nearby(&self, sender_id: u32) -> Result<String> {
        // Get sender's last known position from mesh network
        // For demo, use center of building
        let x = 5000.0;
        let y = 5000.0;
        let z = 1500.0;
        
        let nearby = self.database.find_within_radius(x, y, z, 2000.0)?; // 2m radius
        
        self.format_objects_response(&nearby, "Nearby objects")
    }
    
    /// Format objects into readable response
    fn format_objects_response(&self, objects: &[ArxObject], context: &str) -> Result<String> {
        if objects.is_empty() {
            return Ok(format!("No objects found for: {}", context));
        }
        
        let mut response = format!("{} ({}  objects):\n", context, objects.len());
        
        // Group by type
        use std::collections::HashMap;
        let mut type_counts: HashMap<u8, usize> = HashMap::new();
        
        for obj in objects {
            *type_counts.entry(obj.object_type).or_insert(0) += 1;
        }
        
        for (obj_type, count) in type_counts {
            response.push_str(&format!(
                "  • {} {}\n",
                count,
                self.object_type_name(obj_type)
            ));
        }
        
        // Add compression note
        response.push_str(&format!(
            "\n📊 {} ArxObjects = {} bytes transmitted",
            objects.len(),
            objects.len() * 13
        ));
        
        Ok(response)
    }
    
    /// Get human-readable name for object type
    fn object_type_name(&self, obj_type: u8) -> &str {
        use crate::arxobject::object_types::*;
        match obj_type {
            WALL => "Wall",
            FLOOR => "Floor",
            CEILING => "Ceiling",
            DOOR => "Door",
            WINDOW => "Window",
            COLUMN => "Column",
            OUTLET => "Outlet",
            SWITCH => "Switch",
            LIGHT => "Light",
            HVAC_VENT => "HVAC Vent",
            THERMOSTAT => "Thermostat",
            ELECTRICAL_PANEL => "Electrical Panel",
            EMERGENCY_EXIT => "Emergency Exit",
            CAMERA => "Camera",
            MOTION_SENSOR => "Motion Sensor",
            _ => "Object",
        }
    }
}

/// Example usage showing the complete flow
pub async fn demo_database_flow() {
    println!("\n📡 Database → Mesh Network Demo\n");
    
    println!("Field Tech: 'What's in room 127?'");
    println!("  ↓ (text over radio)");
    println!("Mesh Node receives query");
    println!("  ↓");
    println!("Database queries spatial index");
    println!("  ↓");
    println!("Results compressed to ArxObjects");
    println!("  ↓ (13 bytes each)");
    println!("Tech receives: '5 outlets, 2 lights, 1 thermostat'");
    println!("\n✨ Total data transmitted: 104 bytes");
    println!("   vs traditional: ~50KB of JSON");
    println!("   Compression: 500:1");
}

// Import params macro
use rusqlite::params;