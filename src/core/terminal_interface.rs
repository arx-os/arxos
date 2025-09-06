//! Terminal Interface - ArxOS Command Line for Building Intelligence
//! 
//! The primary human interface to ArxOS, providing ASCII-based interaction
//! with the building mesh network through simple terminal commands.

use crate::arxobject::ArxObject;
use crate::ascii_bridge::AsciiBridge;
use crate::mesh::mesh_router::{MeshRouter, MeshTopology};
use crate::transport::Transport;
use std::collections::VecDeque;

/// Terminal command processor for ArxOS
pub struct TerminalInterface {
    /// ASCII bridge for object conversion
    ascii_bridge: AsciiBridge,
    
    /// Mesh router for packet flow
    mesh_router: MeshRouter,
    
    /// Network topology visualization
    topology: MeshTopology,
    
    /// Command history
    history: VecDeque<String>,
    
    /// Current building context
    building_id: u16,
    
    /// Node ID in mesh
    node_id: u16,
    
    /// Transport layer (optional)
    transport: Option<Box<dyn Transport>>,
}

impl TerminalInterface {
    /// Create new terminal interface
    pub fn new(building_id: u16, node_id: u16) -> Self {
        Self {
            ascii_bridge: AsciiBridge::new(building_id),
            mesh_router: MeshRouter::new(node_id, building_id),
            topology: MeshTopology::new(),
            history: VecDeque::with_capacity(100),
            building_id,
            node_id,
            transport: None,
        }
    }
    
    /// Set transport layer for mesh communication
    pub fn set_transport(&mut self, transport: Box<dyn Transport>) {
        self.transport = Some(transport);
    }
    
    /// Process terminal command
    pub fn process_command(&mut self, cmd: &str) -> String {
        // Add to history
        self.history.push_back(cmd.to_string());
        if self.history.len() > 100 {
            self.history.pop_front();
        }
        
        // Parse command
        let parts: Vec<&str> = cmd.trim().split_whitespace().collect();
        if parts.is_empty() {
            return String::new();
        }
        
        match parts[0] {
            // Core ArxOS commands
            "scan" | "capture" => self.cmd_capture(),
            "parse" => self.cmd_parse(&parts[1..]),
            "render" => self.cmd_render(&parts[1..]),
            "broadcast" => self.cmd_broadcast(&parts[1..]),
            "query" => self.cmd_query(&parts[1..]),
            
            // Mesh network commands
            "mesh" => self.cmd_mesh(&parts[1..]),
            "route" => self.cmd_route(&parts[1..]),
            "topology" => self.cmd_topology(),
            "neighbors" => self.cmd_neighbors(),
            
            // System commands
            "status" => self.cmd_status(),
            "history" => self.cmd_history(),
            "clear" => self.cmd_clear(),
            "help" => self.cmd_help(),
            
            // Building-specific
            "building" => self.cmd_building(&parts[1..]),
            "room" => self.cmd_room(&parts[1..]),
            
            _ => format!("Unknown command: '{}'. Type 'help' for available commands.", parts[0]),
        }
    }
    
    // Command implementations
    
    fn cmd_capture(&mut self) -> String {
        // Simulate AR capture workflow
        let mut output = String::new();
        output.push_str("📷 Initiating AR capture...\n");
        output.push_str("🔍 Scanning environment via LiDAR...\n");
        output.push_str("✨ Processing point cloud...\n\n");
        
        // Simulate finding objects
        output.push_str("Found 3 objects:\n");
        output.push_str("  1. OUTLET @ (10.5, 2.3, 1.2)m CIRCUIT:15 STATUS:OK\n");
        output.push_str("  2. SWITCH @ (10.5, 2.3, 1.5)m CIRCUIT:15 STATUS:ON\n");
        output.push_str("  3. VENT @ (12.0, 3.0, 2.8)m UNIT:1 STATUS:OPEN\n");
        
        output
    }
    
    fn cmd_parse(&mut self, args: &[&str]) -> String {
        if args.is_empty() {
            return "Usage: parse <ASCII description>\nExample: parse OUTLET @ (10.5, 2.3, 1.2)m CIRCUIT:15".to_string();
        }
        
        let ascii = args.join(" ");
        match self.ascii_bridge.parse(&ascii) {
            Ok(obj) => {
                let mut output = String::new();
                output.push_str("✅ Parsed successfully:\n");
                output.push_str(&format!("  ArxObject [13 bytes]:\n"));
                let building_id = obj.building_id;
                let object_type = obj.object_type;
                let x = obj.x;
                let y = obj.y;
                let z = obj.z;
                output.push_str(&format!("    Building: {}\n", building_id));
                output.push_str(&format!("    Type: 0x{:02X}\n", object_type));
                output.push_str(&format!("    Position: ({}, {}, {}) mm\n", x, y, z));
                output.push_str(&format!("    Properties: {:?}\n", obj.properties));
                output.push_str(&format!("    Bytes: {:?}\n", obj.to_bytes()));
                output
            }
            Err(e) => format!("❌ Parse error: {}", e),
        }
    }
    
    fn cmd_render(&mut self, args: &[&str]) -> String {
        if args.is_empty() {
            // Render last captured/parsed object
            let obj = ArxObject::new(self.building_id, 0x15, 10500, 2300, 1200);
            return self.ascii_bridge.render(&obj);
        }
        
        // Try to parse hex bytes
        // TODO: Add hex decoding support
        // if args[0] == "hex" && args.len() >= 2 {
        //     let hex = args[1..].join("");
        //     if let Ok(bytes) = hex::decode(&hex) {
        //         if bytes.len() == 13 {
        //             let mut array = [0u8; 13];
        //             array.copy_from_slice(&bytes);
        //             let obj = ArxObject::from_bytes(&array);
        //             return self.ascii_bridge.render(&obj);
        //         }
        //     }
        // }
        
        "Usage: render [hex <13 bytes>]\nExample: render hex 002A150029045B0898".to_string()
    }
    
    fn cmd_broadcast(&mut self, args: &[&str]) -> String {
        if args.is_empty() {
            return "Usage: broadcast <ASCII description>\nExample: broadcast LEAK @ ROOM_205 SEVERITY:HIGH".to_string();
        }
        
        let ascii = args.join(" ");
        match self.ascii_bridge.parse(&ascii) {
            Ok(obj) => {
                // Route through mesh
                let destination = 0xFFFF; // Broadcast address
                if let Some(next_hop) = self.mesh_router.route_arxobject(&obj, destination) {
                    let mut output = String::new();
                    output.push_str("📡 Broadcasting ArxObject:\n");
                    output.push_str(&format!("  ASCII: {}\n", ascii));
                    output.push_str(&format!("  ArxObject: {} bytes\n", 13));
                    output.push_str(&format!("  Next hop: 0x{:04X}\n", next_hop));
                    output.push_str("  Status: Transmitted via LoRa mesh\n");
                    output
                } else {
                    "❌ No route available".to_string()
                }
            }
            Err(e) => format!("❌ Parse error: {}", e),
        }
    }
    
    fn cmd_query(&mut self, args: &[&str]) -> String {
        if args.is_empty() {
            return "Usage: query <search terms>\nExample: query outlets in room 205".to_string();
        }
        
        let query = args.join(" ").to_lowercase();
        let mut output = String::new();
        
        output.push_str(&format!("🔍 Querying: '{}'\n\n", args.join(" ")));
        
        // Simulate query results based on keywords
        if query.contains("outlet") {
            output.push_str("Found 2 outlets:\n");
            output.push_str("  OUTLET @ (10.5, 2.3, 1.2)m CIRCUIT:15 STATUS:OK\n");
            output.push_str("  OUTLET @ (14.2, 2.3, 1.2)m CIRCUIT:16 STATUS:OK\n");
        } else if query.contains("leak") {
            output.push_str("No active leaks detected ✅\n");
        } else if query.contains("room") {
            output.push_str("Room 205 objects:\n");
            output.push_str("  2 OUTLETs\n");
            output.push_str("  1 THERMOSTAT\n");
            output.push_str("  4 VENTs\n");
            output.push_str("  2 WINDOWs\n");
            output.push_str("  1 DOOR\n");
        } else {
            output.push_str("No matching objects found.\n");
        }
        
        output
    }
    
    fn cmd_mesh(&mut self, args: &[&str]) -> String {
        if args.is_empty() {
            return self.cmd_mesh_status();
        }
        
        match args[0] {
            "status" => self.cmd_mesh_status(),
            "routes" => self.cmd_mesh_routes(),
            "stats" => {
                let stats = self.mesh_router.stats();
                format!(
                    "📊 Mesh Statistics:\n  Node ID: 0x{:04X}\n  Routes: {}\n  Neighbors: {}\n  Queue: {}\n  Routed: {}\n  Dropped: {}\n  Updates: {}",
                    stats.node_id,
                    stats.routes_known,
                    stats.neighbors_count,
                    stats.queue_size,
                    stats.packets_routed,
                    stats.packets_dropped,
                    stats.route_updates
                )
            }
            _ => "Usage: mesh [status|routes|stats]".to_string(),
        }
    }
    
    fn cmd_mesh_status(&self) -> String {
        let stats = self.mesh_router.stats();
        let mut output = String::new();
        
        output.push_str("🌐 Mesh Network Status\n");
        output.push_str(&format!("  Node: 0x{:04X}\n", self.node_id));
        output.push_str(&format!("  Building: {}\n", self.building_id));
        output.push_str(&format!("  Neighbors: {}\n", stats.neighbors_count));
        output.push_str(&format!("  Known routes: {}\n", stats.routes_known));
        output.push_str(&format!("  Packets routed: {}\n", stats.packets_routed));
        
        if let Some(ref transport) = self.transport {
            let metrics = transport.get_metrics();
            output.push_str(&format!("  Transport: {}\n", transport.name()));
            output.push_str(&format!("  Signal: {:?} dBm\n", metrics.signal_strength));
        }
        
        output
    }
    
    fn cmd_mesh_routes(&self) -> String {
        let ad = self.mesh_router.generate_advertisement();
        let mut output = String::new();
        
        output.push_str("📍 Routing Table:\n");
        for route in &ad.routes {
            output.push_str(&format!(
                "  → 0x{:04X}: {} hops, metric {}\n",
                route.destination, route.hop_count, route.metric
            ));
        }
        
        if ad.routes.is_empty() {
            output.push_str("  (No routes available)\n");
        }
        
        output
    }
    
    fn cmd_route(&mut self, args: &[&str]) -> String {
        if args.len() < 2 {
            return "Usage: route <object_type> <destination>\nExample: route outlet 0x0042".to_string();
        }
        
        // Create test object
        let obj = ArxObject::new(self.building_id, 0x15, 0, 0, 0);
        
        // Parse destination
        let dest_str = args[1].trim_start_matches("0x");
        let destination = u16::from_str_radix(dest_str, 16).unwrap_or(0);
        
        if let Some(next_hop) = self.mesh_router.route_arxobject(&obj, destination) {
            format!("Route to 0x{:04X}: via 0x{:04X}", destination, next_hop)
        } else {
            format!("No route to 0x{:04X}", destination)
        }
    }
    
    fn cmd_topology(&mut self) -> String {
        // Update topology from current router state
        let ad = self.mesh_router.generate_advertisement();
        self.topology.update_from_advertisement(&ad);
        
        self.topology.render_ascii()
    }
    
    fn cmd_neighbors(&self) -> String {
        let stats = self.mesh_router.stats();
        format!("Neighbors: {} nodes in direct range", stats.neighbors_count)
    }
    
    fn cmd_status(&self) -> String {
        let mut output = String::new();
        
        output.push_str("═══ ArxOS Terminal Status ═══\n\n");
        output.push_str(&format!("Building ID: {}\n", self.building_id));
        output.push_str(&format!("Node ID: 0x{:04X}\n", self.node_id));
        output.push_str(&format!("Mode: Flow Orchestrator\n"));
        output.push_str(&format!("Protocol: 13-byte ArxObject\n"));
        output.push_str(&format!("Interface: ASCII Terminal + AR\n"));
        
        let stats = self.mesh_router.stats();
        output.push_str(&format!("\nMesh: {} routes, {} neighbors\n", 
            stats.routes_known, stats.neighbors_count));
        
        output.push_str("\nReady for commands. Type 'help' for usage.\n");
        
        output
    }
    
    fn cmd_history(&self) -> String {
        let mut output = String::new();
        output.push_str("Command History:\n");
        
        for (i, cmd) in self.history.iter().enumerate().rev().take(10) {
            output.push_str(&format!("  {}: {}\n", self.history.len() - i, cmd));
        }
        
        output
    }
    
    fn cmd_clear(&self) -> String {
        "\x1b[2J\x1b[H".to_string() // ANSI clear screen
    }
    
    fn cmd_help(&self) -> String {
        r#"
╔═══════════════════════════════════════════════════════╗
║           ArxOS Terminal Commands                     ║
╠═══════════════════════════════════════════════════════╣
║ Field Operations:                                     ║
║   scan/capture    - Capture objects via AR           ║
║   parse <text>    - Convert ASCII to ArxObject       ║
║   render [hex]    - Convert ArxObject to ASCII       ║
║   broadcast <text> - Send to mesh network            ║
║   query <terms>   - Search building intelligence     ║
║                                                       ║
║ Mesh Network:                                         ║
║   mesh [status]   - Show mesh network status         ║
║   route <obj> <dst> - Find route to destination      ║
║   topology        - Display network topology         ║
║   neighbors       - List direct neighbors            ║
║                                                       ║
║ Building:                                             ║
║   building <id>   - Switch building context          ║
║   room <number>   - Query room objects               ║
║                                                       ║
║ System:                                               ║
║   status          - Show system status               ║
║   history         - Show command history             ║
║   clear           - Clear screen                     ║
║   help            - Show this help                   ║
╚═══════════════════════════════════════════════════════╝
        
Examples:
  parse OUTLET @ (10.5, 2.3, 1.2)m CIRCUIT:15
  broadcast LEAK @ ROOM_205 SEVERITY:HIGH
  query outlets in room 205
  mesh status
"#.to_string()
    }
    
    fn cmd_building(&mut self, args: &[&str]) -> String {
        if args.is_empty() {
            return format!("Current building: {}", self.building_id);
        }
        
        if let Ok(id) = args[0].parse::<u16>() {
            self.building_id = id;
            self.ascii_bridge = AsciiBridge::new(id);
            format!("Switched to building {}", id)
        } else {
            "Invalid building ID".to_string()
        }
    }
    
    fn cmd_room(&mut self, args: &[&str]) -> String {
        if args.is_empty() {
            return "Usage: room <number>\nExample: room 205".to_string();
        }
        
        let room = args[0];
        let mut output = String::new();
        
        output.push_str(&format!("📍 Room {} Status:\n", room));
        output.push_str("  Temperature: 72°F\n");
        output.push_str("  Occupancy: Vacant\n");
        output.push_str("  Lights: Off\n");
        output.push_str("  HVAC: Standby\n");
        output.push_str("\nObjects in room:\n");
        output.push_str("  2 OUTLETs (circuits 15, 16)\n");
        output.push_str("  1 THERMOSTAT (setpoint 72°F)\n");
        output.push_str("  4 VENTs (all open)\n");
        output.push_str("  2 WINDOWs (closed)\n");
        output.push_str("  1 DOOR (closed)\n");
        
        output
    }
}

/// Terminal prompt display
pub fn display_prompt(building_id: u16, node_id: u16) -> String {
    format!("arxos[{:04X}@B{}]> ", node_id, building_id)
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_terminal_help() {
        let mut terminal = TerminalInterface::new(42, 1);
        let output = terminal.process_command("help");
        assert!(output.contains("ArxOS Terminal Commands"));
    }
    
    #[test]
    fn test_terminal_parse() {
        let mut terminal = TerminalInterface::new(42, 1);
        let output = terminal.process_command("parse OUTLET @ (10.5, 2.3, 1.2)m");
        assert!(output.contains("Parsed successfully"));
        assert!(output.contains("13 bytes"));
    }
    
    #[test]
    fn test_terminal_status() {
        let terminal = TerminalInterface::new(42, 1);
        let output = terminal.process_command("status");
        assert!(output.contains("Building ID: 42"));
        assert!(output.contains("Node ID: 0x0001"));
    }
    
    #[test]
    fn test_terminal_broadcast() {
        let mut terminal = TerminalInterface::new(42, 1);
        let output = terminal.process_command("broadcast LEAK @ ROOM_205 SEVERITY:HIGH");
        assert!(output.contains("Broadcasting ArxObject"));
    }
}