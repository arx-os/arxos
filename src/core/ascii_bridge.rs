//! ASCII Bridge - The Universal Building Protocol Interface
//! 
//! Converts between human-readable ASCII descriptions and 13-byte ArxObjects.
//! This is the critical interface between field operations and the mesh network.

use crate::arxobject::ArxObject;
use std::collections::HashMap;
use regex::Regex;

/// Object type mappings for building systems
#[derive(Debug, Clone, Copy, PartialEq)]
pub enum BuildingObjectType {
    // Electrical
    Outlet = 0x15,
    Switch = 0x16,
    Panel = 0x17,
    Breaker = 0x18,
    
    // HVAC
    Vent = 0x20,
    Thermostat = 0x21,
    Unit = 0x22,
    Filter = 0x23,
    
    // Plumbing
    Pipe = 0x30,
    Valve = 0x31,
    Leak = 0x32,
    Drain = 0x33,
    
    // Structural
    Wall = 0x40,
    Door = 0x41,
    Window = 0x42,
    Room = 0x43,
    
    // Safety
    Alarm = 0x50,
    Sensor = 0x51,
    Camera = 0x52,
    Exit = 0x53,
    
    // Maintenance
    Issue = 0x60,
    WorkOrder = 0x61,
    Inspection = 0x62,
    Alert = 0x63,
}

/// ASCII to ArxObject converter
pub struct AsciiBridge {
    building_id: u16,
    object_registry: HashMap<String, BuildingObjectType>,
    location_cache: HashMap<String, (i16, i16, i16)>,
}

impl AsciiBridge {
    /// Create a new ASCII bridge for a building
    pub fn new(building_id: u16) -> Self {
        let mut registry = HashMap::new();
        
        // Register object type keywords
        registry.insert("outlet".to_string(), BuildingObjectType::Outlet);
        registry.insert("switch".to_string(), BuildingObjectType::Switch);
        registry.insert("panel".to_string(), BuildingObjectType::Panel);
        registry.insert("breaker".to_string(), BuildingObjectType::Breaker);
        
        registry.insert("vent".to_string(), BuildingObjectType::Vent);
        registry.insert("thermostat".to_string(), BuildingObjectType::Thermostat);
        registry.insert("unit".to_string(), BuildingObjectType::Unit);
        registry.insert("hvac".to_string(), BuildingObjectType::Unit);
        registry.insert("filter".to_string(), BuildingObjectType::Filter);
        
        registry.insert("pipe".to_string(), BuildingObjectType::Pipe);
        registry.insert("valve".to_string(), BuildingObjectType::Valve);
        registry.insert("leak".to_string(), BuildingObjectType::Leak);
        registry.insert("drain".to_string(), BuildingObjectType::Drain);
        
        registry.insert("wall".to_string(), BuildingObjectType::Wall);
        registry.insert("door".to_string(), BuildingObjectType::Door);
        registry.insert("window".to_string(), BuildingObjectType::Window);
        registry.insert("room".to_string(), BuildingObjectType::Room);
        
        registry.insert("alarm".to_string(), BuildingObjectType::Alarm);
        registry.insert("sensor".to_string(), BuildingObjectType::Sensor);
        registry.insert("camera".to_string(), BuildingObjectType::Camera);
        registry.insert("exit".to_string(), BuildingObjectType::Exit);
        
        registry.insert("issue".to_string(), BuildingObjectType::Issue);
        registry.insert("work_order".to_string(), BuildingObjectType::WorkOrder);
        registry.insert("inspection".to_string(), BuildingObjectType::Inspection);
        registry.insert("alert".to_string(), BuildingObjectType::Alert);
        
        Self {
            building_id,
            object_registry: registry,
            location_cache: HashMap::new(),
        }
    }
    
    /// Parse ASCII description to ArxObject
    /// Format: "OBJECT_TYPE @ (X, Y, Z) PROPERTY:VALUE"
    /// Example: "OUTLET @ (10.5, 2.3, 1.2)m STATUS:OK CIRCUIT:15"
    pub fn parse(&mut self, ascii: &str) -> Result<ArxObject, String> {
        let ascii_lower = ascii.to_lowercase();
        
        // Find object type
        let object_type = self.identify_object_type(&ascii_lower)?;
        
        // Extract position
        let (x, y, z) = self.extract_position(&ascii_lower)?;
        
        // Extract properties
        let properties = self.extract_properties(&ascii_lower, object_type);
        
        Ok(ArxObject::with_properties(
            self.building_id,
            object_type as u8,
            x,
            y,
            z,
            properties,
        ))
    }
    
    /// Convert ArxObject to ASCII description
    pub fn render(&self, obj: &ArxObject) -> String {
        let type_name = self.object_type_name(obj.object_type);
        
        // Convert mm to meters for display
        let x_m = obj.x as f32 / 1000.0;
        let y_m = obj.y as f32 / 1000.0;
        let z_m = obj.z as f32 / 1000.0;
        
        // Base description
        let mut ascii = format!("{} @ ({:.1}, {:.1}, {:.1})m", 
                                type_name.to_uppercase(), x_m, y_m, z_m);
        
        // Add properties based on type
        match obj.object_type {
            0x15 => { // Outlet
                if obj.properties[0] > 0 {
                    ascii.push_str(&format!(" CIRCUIT:{}", obj.properties[0]));
                }
                if obj.properties[1] > 0 {
                    ascii.push_str(&format!(" VOLTAGE:{}V", obj.properties[1]));
                }
            }
            0x32 => { // Leak
                let severity = match obj.properties[1] {
                    3 => "HIGH",
                    2 => "MEDIUM",
                    1 => "LOW",
                    _ => "UNKNOWN",
                };
                ascii.push_str(&format!(" SEVERITY:{}", severity));
            }
            0x22 => { // HVAC Unit
                if obj.properties[0] > 0 {
                    ascii.push_str(&format!(" UNIT:{}", obj.properties[0]));
                }
                let status = if obj.properties[1] > 0 { "ON" } else { "OFF" };
                ascii.push_str(&format!(" STATUS:{}", status));
            }
            _ => {
                // Generic property display
                if obj.properties[0] > 0 {
                    ascii.push_str(&format!(" ID:{}", obj.properties[0]));
                }
            }
        }
        
        ascii
    }
    
    /// Generate ASCII art visualization
    pub fn render_ascii_art(&self, obj: &ArxObject) -> String {
        match obj.object_type {
            0x15 => { // Outlet
                "  ___\n |o o|\n |___|\n".to_string()
            }
            0x16 => { // Switch
                "  ___\n | / |\n |___|\n".to_string()
            }
            0x41 => { // Door
                " ____\n|    |\n| [] |\n|    |\n|____|\n".to_string()
            }
            0x42 => { // Window
                " ____\n|----|\n|----|\n|____|\n".to_string()
            }
            0x32 => { // Leak
                "  ~~\n ~~~~\n~~~~~~\n".to_string()
            }
            0x22 => { // HVAC Unit
                " [====]\n |HVAC|\n [====]\n".to_string()
            }
            _ => {
                " [?]\n".to_string()
            }
        }
    }
    
    /// Parse batch ASCII input (multiple objects)
    pub fn parse_batch(&mut self, ascii: &str) -> Vec<ArxObject> {
        ascii.lines()
            .filter(|line| !line.trim().is_empty())
            .filter_map(|line| self.parse(line).ok())
            .collect()
    }
    
    /// Render multiple ArxObjects as ASCII report
    pub fn render_report(&self, objects: &[ArxObject]) -> String {
        let mut report = String::new();
        report.push_str("=== BUILDING INTELLIGENCE REPORT ===\n");
        report.push_str(&format!("Building ID: {}\n", self.building_id));
        report.push_str(&format!("Objects: {}\n", objects.len()));
        report.push_str("====================================\n\n");
        
        for obj in objects {
            report.push_str(&self.render(obj));
            report.push('\n');
        }
        
        report
    }
    
    // Helper methods
    
    fn identify_object_type(&self, text: &str) -> Result<BuildingObjectType, String> {
        for (keyword, obj_type) in &self.object_registry {
            if text.contains(keyword) {
                return Ok(*obj_type);
            }
        }
        Err(format!("Unknown object type in: {}", text))
    }
    
    fn extract_position(&mut self, text: &str) -> Result<(i16, i16, i16), String> {
        // Try coordinates: @ (x, y, z)
        let coord_regex = Regex::new(r"@\s*\(?\s*([\d.-]+)\s*,\s*([\d.-]+)\s*,\s*([\d.-]+)\s*\)?").unwrap();
        if let Some(caps) = coord_regex.captures(text) {
            let x = caps[1].parse::<f32>().unwrap_or(0.0) * 1000.0; // Convert to mm
            let y = caps[2].parse::<f32>().unwrap_or(0.0) * 1000.0;
            let z = caps[3].parse::<f32>().unwrap_or(0.0) * 1000.0;
            return Ok((
                x.max(-32768.0).min(32767.0) as i16,
                y.max(-32768.0).min(32767.0) as i16,
                z.max(-32768.0).min(32767.0) as i16
            ));
        }
        
        // Try named location: @ ROOM_205
        let location_regex = Regex::new(r"@\s*(\w+)").unwrap();
        if let Some(caps) = location_regex.captures(text) {
            let location = &caps[1];
            if let Some(&pos) = self.location_cache.get(location) {
                return Ok(pos);
            }
            
            // Generate position from room number
            if location.starts_with("room_") || location.starts_with("ROOM_") {
                let room_num: u16 = location[5..].parse().unwrap_or(0);
                let floor = (room_num / 100) as i16;
                let x = ((room_num % 100) * 100) as i16;
                let y = 5000i16; // Default middle of building
                let z = floor * 3000; // 3m per floor
                
                let pos = (x, y, z);
                self.location_cache.insert(location.to_string(), pos);
                return Ok(pos);
            }
        }
        
        // Default position
        Ok((0, 0, 0))
    }
    
    fn extract_properties(&self, text: &str, obj_type: BuildingObjectType) -> [u8; 4] {
        let mut props = [0u8; 4];
        
        // Extract property:value pairs
        let prop_regex = Regex::new(r"(\w+):(\w+)").unwrap();
        let properties: HashMap<String, String> = prop_regex
            .captures_iter(text)
            .map(|cap| (cap[1].to_lowercase(), cap[2].to_lowercase()))
            .collect();
        
        // Parse based on object type
        match obj_type {
            BuildingObjectType::Outlet => {
                if let Some(circuit) = properties.get("circuit") {
                    props[0] = circuit.parse().unwrap_or(0);
                }
                if let Some(voltage) = properties.get("voltage") {
                    props[1] = voltage.replace("v", "").parse().unwrap_or(120);
                }
            }
            BuildingObjectType::Leak => {
                if let Some(severity) = properties.get("severity") {
                    props[1] = match severity.as_str() {
                        "high" => 3,
                        "medium" => 2,
                        "low" => 1,
                        _ => 0,
                    };
                }
            }
            BuildingObjectType::Unit => {
                if let Some(unit) = properties.get("unit") {
                    props[0] = unit.parse().unwrap_or(0);
                }
                if let Some(status) = properties.get("status") {
                    props[1] = if status == "on" { 1 } else { 0 };
                }
            }
            _ => {
                // Generic ID property
                if let Some(id) = properties.get("id") {
                    props[0] = id.parse().unwrap_or(0);
                }
            }
        }
        
        props
    }
    
    fn object_type_name(&self, type_id: u8) -> &str {
        match type_id {
            0x15 => "outlet",
            0x16 => "switch",
            0x17 => "panel",
            0x18 => "breaker",
            0x20 => "vent",
            0x21 => "thermostat",
            0x22 => "unit",
            0x23 => "filter",
            0x30 => "pipe",
            0x31 => "valve",
            0x32 => "leak",
            0x33 => "drain",
            0x40 => "wall",
            0x41 => "door",
            0x42 => "window",
            0x43 => "room",
            0x50 => "alarm",
            0x51 => "sensor",
            0x52 => "camera",
            0x53 => "exit",
            0x60 => "issue",
            0x61 => "work_order",
            0x62 => "inspection",
            0x63 => "alert",
            _ => "unknown",
        }
    }
}

/// Terminal interface for ArxOS
pub struct TerminalInterface {
    bridge: AsciiBridge,
    history: Vec<String>,
}

impl TerminalInterface {
    pub fn new(building_id: u16) -> Self {
        Self {
            bridge: AsciiBridge::new(building_id),
            history: Vec::new(),
        }
    }
    
    /// Process terminal command
    pub fn process_command(&mut self, cmd: &str) -> String {
        self.history.push(cmd.to_string());
        
        let parts: Vec<&str> = cmd.split_whitespace().collect();
        if parts.is_empty() {
            return "Error: Empty command".to_string();
        }
        
        match parts[0] {
            "scan" | "capture" => {
                // Simulate AR capture
                "Scanning via AR...\nFound: OUTLET @ (10.5, 2.3, 1.2)m STATUS:OK".to_string()
            }
            "parse" => {
                if parts.len() < 2 {
                    return "Usage: parse <ascii description>".to_string();
                }
                let ascii = parts[1..].join(" ");
                match self.bridge.parse(&ascii) {
                    Ok(obj) => format!("ArxObject: {:?}", obj),
                    Err(e) => format!("Parse error: {}", e),
                }
            }
            "render" => {
                // Would render last captured object
                "OUTLET @ (10.5, 2.3, 1.2)m CIRCUIT:15 VOLTAGE:120V".to_string()
            }
            "help" => {
                "Commands:\n  scan - Capture from AR\n  parse <text> - Convert ASCII to ArxObject\n  render - Show as ASCII\n  help - Show this help".to_string()
            }
            _ => format!("Unknown command: {}", parts[0]),
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_ascii_to_arxobject() {
        let mut bridge = AsciiBridge::new(42);
        
        // Test outlet parsing
        let ascii = "OUTLET @ (10.5, 2.3, 1.2)m CIRCUIT:15";
        let obj = bridge.parse(ascii).unwrap();
        
        // Use local variables to avoid packed struct alignment issues
        let building_id = obj.building_id;
        let object_type = obj.object_type;
        let x = obj.x;
        let y = obj.y;
        let z = obj.z;
        let prop0 = obj.properties[0];
        
        assert_eq!(building_id, 42);
        assert_eq!(object_type, BuildingObjectType::Outlet as u8);
        assert_eq!(x, 10500);
        assert_eq!(y, 2300);
        assert_eq!(z, 1200);
        assert_eq!(prop0, 15); // Circuit number
    }
    
    #[test]
    fn test_arxobject_to_ascii() {
        let bridge = AsciiBridge::new(42);
        
        let obj = ArxObject::with_properties(
            42,
            BuildingObjectType::Leak as u8,
            5000,
            3000,
            1000,
            [0, 3, 0, 0], // High severity
        );
        
        let ascii = bridge.render(&obj);
        assert!(ascii.contains("LEAK"));
        assert!(ascii.contains("@ (5.0, 3.0, 1.0)m"));
        assert!(ascii.contains("SEVERITY:HIGH"));
    }
    
    #[test]
    fn test_room_location() {
        let mut bridge = AsciiBridge::new(42);
        
        let ascii = "THERMOSTAT @ ROOM_205";
        let obj = bridge.parse(ascii).unwrap();
        
        // Use local variables to avoid packed struct alignment issues
        let object_type = obj.object_type;
        let z = obj.z;
        
        assert_eq!(object_type, BuildingObjectType::Thermostat as u8);
        assert_eq!(z, 6000); // Floor 2 = 6m
    }
}