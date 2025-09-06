//! ArxOS Flow Orchestrator Demo
//! 
//! Demonstrates the complete flow:
//! AR Capture → ASCII → ArxObject (13 bytes) → Mesh Network → Systems

use arxos_core::ascii_bridge::{AsciiBridge, TerminalInterface};
use arxos_core::mesh_router::{MeshRouter, MeshTopology};
use arxos_core::arxobject::ArxObject;

fn main() {
    println!("╔═══════════════════════════════════════════════════════╗");
    println!("║     ArxOS - Building Intelligence Flow Orchestrator    ║");
    println!("╚═══════════════════════════════════════════════════════╝");
    println!();
    
    // Initialize components for Building 42, Node 1
    let building_id = 42;
    let node_id = 1;
    
    let mut ascii_bridge = AsciiBridge::new(building_id);
    let mut mesh_router = MeshRouter::new(node_id, building_id);
    let mut terminal = TerminalInterface::new(building_id);
    
    // Simulate the complete flow
    println!("═══ 1. FIELD LAYER - AR Capture ═══");
    println!("📱 Maintenance tech uses iPhone AR to scan room...");
    println!("🔍 LiDAR captures 3D point cloud");
    println!("✨ External processor converts to ASCII\n");
    
    // Simulate AR capture results
    let ar_captures = vec![
        "OUTLET @ (10.5, 2.3, 1.2)m CIRCUIT:15 STATUS:OK",
        "LEAK @ (5.0, 3.0, 1.0)m SEVERITY:HIGH",
        "THERMOSTAT @ ROOM_205 STATUS:72F",
    ];
    
    println!("═══ 2. INTERFACE LAYER - ASCII Description ═══");
    for capture in &ar_captures {
        println!("📝 {}", capture);
    }
    println!();
    
    println!("═══ 3. PROTOCOL LAYER - ArxObject Conversion ═══");
    for capture in &ar_captures {
        match ascii_bridge.parse(capture) {
            Ok(obj) => {
                println!("✅ Parsed: {}", capture);
                println!("   → ArxObject [13 bytes]: {:?}", obj.to_bytes());
                println!("   → Compression: ~100 chars → 13 bytes (7.7:1)");
                
                // Route through mesh
                if let Some(next_hop) = mesh_router.route_arxobject(&obj, 0xFFFF) {
                    println!("   → Routing: Next hop 0x{:04X}", next_hop);
                }
            }
            Err(e) => {
                println!("❌ Parse error: {}", e);
            }
        }
        println!();
    }
    
    println!("═══ 4. TRANSPORT LAYER - LoRa Mesh ═══");
    println!("📡 Transmitting via 915MHz packet radio");
    println!("   • Packet size: 255 bytes");
    println!("   • ArxObjects per packet: 19");
    println!("   • Range: 2-10 km");
    println!("   • Power: <100mW");
    println!();
    
    println!("═══ 5. INTEGRATION LAYER - System Bridges ═══");
    println!("🏢 Revit/CAD: Updates building model");
    println!("🌡️  Honeywell BAS: Adjusts HVAC for leak");
    println!("📱 IoT Sensors: Correlate with leak detection");
    println!("🤖 Automation: Dispatch maintenance crew");
    println!();
    
    // Show mesh topology
    println!("═══ MESH TOPOLOGY ═══");
    let mut topology = MeshTopology::new();
    let ad = mesh_router.generate_advertisement();
    topology.update_from_advertisement(&ad);
    println!("{}", topology.render_ascii());
    
    // Show router statistics
    let stats = mesh_router.stats();
    println!("═══ ROUTER STATISTICS ═══");
    println!("Node ID: 0x{:04X}", stats.node_id);
    println!("Building: {}", building_id);
    println!("Packets routed: {}", stats.packets_routed);
    println!("Routes known: {}", stats.routes_known);
    println!();
    
    // Terminal interaction demo
    println!("═══ TERMINAL INTERFACE ═══");
    println!("arxos[0001@B42]> scan");
    let output = terminal.process_command("scan");
    for line in output.lines() {
        println!("  {}", line);
    }
    println!();
    
    println!("arxos[0001@B42]> broadcast LEAK @ ROOM_205 SEVERITY:HIGH");
    let output = terminal.process_command("broadcast LEAK @ ROOM_205 SEVERITY:HIGH");
    for line in output.lines() {
        println!("  {}", line);
    }
    println!();
    
    // Summary
    println!("═══ SUMMARY ═══");
    println!("✅ ArxOS Flow Complete:");
    println!("   • Point cloud (1GB) → ASCII (100B) → ArxObject (13B)");
    println!("   • Compression ratio: 10,000,000:1");
    println!("   • Binary size: <5MB");
    println!("   • Runs on: Raspberry Pi ($35)");
    println!("   • Network: LoRa mesh (no internet required)");
    println!("   • Interface: Terminal + AR");
    println!();
    println!("🎯 Mission: Route building intelligence, not process it.");
}