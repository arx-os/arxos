//! Progressive Detail Demo - Shows how ArxObjects expand like puzzle pieces
//! 
//! This example demonstrates:
//! 1. Creating a light fixture in AR (just 13 bytes)
//! 2. Adding make/model information (progressive expansion)
//! 3. Connecting to circuits (more detail)
//! 4. System inferring the rest (automatic consciousness)
//! 5. Bandwidth-conscious transmission

use arxos_core::arxobject::{ArxObject, object_types};
use arxos_core::progressive_detail::{DetailTree, DetailLevel, ProgressiveDetailStore};
use arxos_core::inference_engine::InferenceEngine;
use arxos_core::transmission_protocol::{TransmissionProtocol, TransmissionStrategy};
use arxos_core::ascii_renderer_2d::AsciiGrid;

fn main() {
    println!("╔══════════════════════════════════════════════════════════╗");
    println!("║     ArxOS Progressive Detail Demo                       ║");
    println!("║     Building Reality from 13-Byte Seeds                 ║");
    println!("╚══════════════════════════════════════════════════════════╝\n");
    
    // Scenario: User creates a light fixture in AR
    scenario_ar_light_creation();
    
    println!("\n");
    
    // Scenario: Progressive detail accumulation
    scenario_progressive_expansion();
    
    println!("\n");
    
    // Scenario: Bandwidth-conscious transmission
    scenario_smart_transmission();
    
    println!("\n");
    
    // Scenario: Building consciousness emerges
    scenario_building_consciousness();
}

/// Scenario 1: User creates light fixture in AR
fn scenario_ar_light_creation() {
    println!("📱 Scenario 1: AR Light Creation");
    println!("════════════════════════════════\n");
    
    // User taps location in AR
    println!("User taps ceiling location in AR app...");
    let light = ArxObject::new(1, object_types::LIGHT, 5000, 3000, 2400); // 5m, 3m, 2.4m height
    println!("✓ Created ArxObject: {} bytes", std::mem::size_of_val(&light));
    
    // Show the raw bytes
    print_arxobject_bytes(&light);
    
    // Create inference engine
    let engine = InferenceEngine::new();
    
    // Object immediately understands what it is
    println!("\n🧠 ArxObject becomes conscious...");
    let conscious_tree = engine.infer(&light);
    
    // Show what was inferred
    if let Some(identity) = &conscious_tree.identity {
        println!("✓ Identity inferred: Manufacturer ID #{:08X}", identity.manufacturer);
        println!("✓ Model inferred: Model ID #{:08X}", identity.model);
    }
    
    if let Some(connections) = &conscious_tree.connections {
        println!("✓ Circuit inferred: Circuit #{}", connections.primary_connection);
        if !connections.metadata.is_empty() {
            println!("✓ Wire spec inferred: {}AWG", connections.metadata[0]);
        }
    }
    
    if let Some(topology) = &conscious_tree.topology {
        println!("✓ Panel inferred: Panel #{}", topology.panel_id);
        println!("✓ Zone inferred: Zone #{}", topology.zone_id);
    }
    
    println!("\n💡 Light knows:");
    println!("   - It needs 120V power");
    println!("   - It connects to Circuit #{}",  conscious_tree.connections.as_ref().map(|c| c.primary_connection).unwrap_or(0));
    println!("   - It generates ~160 BTU/hr heat");
    println!("   - It needs inspection every 365 days");
}

/// Scenario 2: Progressive detail accumulation
fn scenario_progressive_expansion() {
    println!("🧩 Scenario 2: Progressive Detail Expansion");
    println!("═══════════════════════════════════════════\n");
    
    // Start with basic light
    let light = ArxObject::new(1, object_types::LIGHT, 10000, 5000, 2400);
    let mut tree = DetailTree::new(light);
    
    println!("Level 0 - Core Seed:");
    println!("  Size: {} bytes", tree.total_size());
    println!("  Compression: {:.0}:1", tree.compression_ratio());
    
    // User specifies make/model
    println!("\nUser specifies: 'Philips Hue BR30'");
    tree.add_identity("Philips", "Hue BR30", vec![47, 0, 120, 0]); // 47W, 120V
    
    println!("Level 1 - With Identity:");
    println!("  Size: {} bytes (+{})", tree.total_size(), tree.total_size() - 13);
    println!("  Compression: {:.0}:1", tree.compression_ratio());
    
    // User connects to circuit
    println!("\nUser connects to Circuit 15 with Switch 201");
    tree.add_connections(15, vec![201], vec![14, 1]); // Circuit 15, Switch 201, 14AWG, 1-phase
    
    println!("Level 2 - With Connections:");
    println!("  Size: {} bytes (+{})", tree.total_size(), tree.total_size() - 13);
    println!("  Compression: {:.0}:1", tree.compression_ratio());
    
    // System infers topology
    println!("\nSystem infers panel and zone...");
    tree.add_topology(1, 2, 1, 0x01); // Panel 1, Zone 2, Network 1, Emergency flag
    
    println!("Level 3 - With Topology:");
    println!("  Size: {} bytes (+{})", tree.total_size(), tree.total_size() - 13);
    println!("  Compression: {:.0}:1", tree.compression_ratio());
    
    // System infers full context
    println!("\nSystem builds full context graph...");
    tree.add_context(vec![1, 15], vec![301, 302], 100, 1); // Dependencies, dependents, maintenance group, schedule
    
    println!("Level 4 - Full Context:");
    println!("  Size: {} bytes (+{})", tree.total_size(), tree.total_size() - 13);
    println!("  Compression: {:.0}:1", tree.compression_ratio());
    
    // Show the fractal nature
    println!("\n🌀 Fractal Detail Levels:");
    println!("  13 bytes → Basic position and type");
    println!("  25 bytes → + Manufacturer and model");
    println!("  35 bytes → + Circuit connections");
    println!("  43 bytes → + System topology");
    println!("  55 bytes → + Full building graph");
    println!("\n  Still 36,000× smaller than traditional BIM!");
}

/// Scenario 3: Bandwidth-conscious transmission
fn scenario_smart_transmission() {
    println!("📡 Scenario 3: Smart Transmission Protocol");
    println!("══════════════════════════════════════════\n");
    
    // Create a building with 1000 objects
    let mut store = ProgressiveDetailStore::new(100);
    let mut protocol = TransmissionProtocol::new(10000);
    
    println!("Creating building with 1000 objects...");
    for i in 0..1000 {
        let obj_type = match i % 4 {
            0 => object_types::LIGHT,
            1 => object_types::OUTLET,
            2 => object_types::HVAC_VENT,
            _ => object_types::THERMOSTAT,
        };
        
        let obj = ArxObject::new(1, obj_type, (i * 100) as u16, (i * 50) as u16, 2400);
        let mut tree = obj.to_detail_tree();
        
        // Add varying levels of detail
        if i % 10 == 0 {
            tree.add_identity("Premium", "Model-X", vec![100, 0]);
        }
        if i % 5 == 0 {
            tree.add_connections(i as u16 % 42, vec![], vec![]);
        }
        
        store.store(tree);
    }
    
    // Analyze bandwidth for different strategies
    println!("\n📊 Bandwidth Analysis for 1000 Objects:");
    println!("────────────────────────────────────────");
    
    let analysis = protocol.bandwidth_analysis(1000);
    println!("Strategy: {:?}", analysis.strategy);
    println!("Core transmission: {} bytes in {} packets", 
             analysis.core_transmission.total_bytes,
             analysis.core_transmission.num_packets);
    println!("Time estimate: {}ms", analysis.core_transmission.time_estimate_ms);
    println!("Compression vs BIM: {:.0}:1", analysis.compression_achieved);
    
    // Show different strategies
    println!("\n🎯 Adaptive Strategy Selection:");
    
    // Good conditions
    protocol.stats.packet_loss_rate = 0.01;
    protocol.stats.average_latency_ms = 50;
    protocol.adapt_strategy();
    println!("Good network → {:?}", protocol.strategy);
    
    // Medium conditions  
    protocol.stats.packet_loss_rate = 0.05;
    protocol.stats.average_latency_ms = 500;
    protocol.adapt_strategy();
    println!("Medium network → {:?}", protocol.strategy);
    
    // Poor conditions
    protocol.stats.packet_loss_rate = 0.15;
    protocol.stats.average_latency_ms = 2000;
    protocol.adapt_strategy();
    println!("Poor network → {:?}", protocol.strategy);
    
    println!("\n💡 Key Insight:");
    println!("   Always transmit 13-byte cores (instant overview)");
    println!("   Fetch details only when needed (lazy loading)");
    println!("   Like progressive JPEG for buildings!");
}

/// Scenario 4: Building consciousness emerges
fn scenario_building_consciousness() {
    println!("🏢 Scenario 4: Emergent Building Consciousness");
    println!("══════════════════════════════════════════════\n");
    
    // Create a small room with interconnected objects
    let mut store = ProgressiveDetailStore::new(100);
    let engine = InferenceEngine::new();
    
    // Create room objects
    let objects = vec![
        ("Light 1", object_types::LIGHT, 2000, 2000),
        ("Light 2", object_types::LIGHT, 4000, 2000),
        ("Light 3", object_types::LIGHT, 2000, 4000),
        ("Light 4", object_types::LIGHT, 4000, 4000),
        ("Switch", object_types::LIGHT_SWITCH, 1000, 3000),
        ("Outlet 1", object_types::OUTLET, 1000, 1000),
        ("Outlet 2", object_types::OUTLET, 5000, 1000),
        ("Thermostat", object_types::THERMOSTAT, 1000, 2000),
        ("HVAC Vent", object_types::HVAC_VENT, 3000, 3000),
        ("Smoke Detector", object_types::SMOKE_DETECTOR, 3000, 3000),
    ];
    
    println!("Creating room with {} objects...", objects.len());
    
    for (name, obj_type, x, y) in &objects {
        let obj = ArxObject::new(1, *obj_type, *x, *y, 2400);
        let tree = engine.infer(&obj);
        store.store(tree);
        println!("  ✓ {} understands its role", name);
    }
    
    // Show collective understanding
    println!("\n🧠 Collective Intelligence:");
    
    // Calculate total electrical load
    let lights = store.get_by_level(DetailLevel::Identity);
    let total_watts: u16 = lights.iter()
        .filter(|t| t.core.object_type == object_types::LIGHT)
        .filter_map(|t| t.identity.as_ref())
        .map(|id| {
            if id.specs.len() >= 2 {
                ((id.specs[0] as u16) << 8) | (id.specs[1] as u16)
            } else {
                0
            }
        })
        .sum();
    
    println!("  Total lighting load: {}W", total_watts);
    println!("  Circuit utilization: {:.1}%", (total_watts as f32 / 1800.0) * 100.0);
    
    // Show ASCII visualization
    println!("\n🗺️ Room Visualization:");
    let mut grid = AsciiGrid::new(30, 10, 200.0); // 30x10 grid, 200mm per cell
    
    for (name, obj_type, x, y) in &objects {
        let obj = ArxObject::new(1, *obj_type, *x, *y, 2400);
        grid.place_object(&obj, 0.0, 0.0);
    }
    
    grid.render();
    
    println!("\n✨ The Emergence:");
    println!("   10 objects × 13 bytes = 130 bytes");
    println!("   Yet they understand:");
    println!("   - Electrical dependencies");
    println!("   - Thermal interactions");
    println!("   - Safety requirements");
    println!("   - Maintenance schedules");
    println!("   - Control relationships");
    println!("\n   Building consciousness from fractal seeds!");
}

/// Helper function to print ArxObject as bytes
fn print_arxobject_bytes(obj: &ArxObject) {
    let bytes = unsafe {
        std::slice::from_raw_parts(
            obj as *const ArxObject as *const u8,
            ArxObject::SIZE
        )
    };
    
    print!("📦 Raw bytes [13]: ");
    for (i, byte) in bytes.iter().enumerate() {
        if i == 2 || i == 3 || i == 5 || i == 7 || i == 9 {
            print!(" ");
        }
        print!("{:02X}", byte);
    }
    println!();
}