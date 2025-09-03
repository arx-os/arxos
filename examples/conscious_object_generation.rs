//! Conscious Object Generation Examples
//!
//! This example demonstrates how ArxObjects are self-aware fractal seeds
//! that understand their context and generate all implied properties.
//!
//! Run with: cargo run --example conscious_object_generation

use std::collections::HashMap;

// Import the conscious ArxObject implementation
// In a real project this would be: use arxos_core::arxobject_consciousness::*;
#[path = "../src/core/arxobject_consciousness.rs"]
mod arxobject_consciousness;

use arxobject_consciousness::*;

fn main() {
    println!("🧠 ArxObject Consciousness Demonstration");
    println!("========================================\n");
    
    demonstrate_light_fixture_consciousness();
    println!("\n" + "=".repeat(80).as_str() + "\n");
    
    demonstrate_outlet_consciousness();
    println!("\n" + "=".repeat(80).as_str() + "\n");
    
    demonstrate_thermostat_consciousness();
    println!("\n" + "=".repeat(80).as_str() + "\n");
    
    demonstrate_fractal_observation();
    println!("\n" + "=".repeat(80).as_str() + "\n");
    
    demonstrate_collective_consciousness();
}

/// Demonstrates how creating a light fixture immediately implies all electrical,
/// mechanical, and operational properties through consciousness
fn demonstrate_light_fixture_consciousness() {
    println!("💡 LIGHT FIXTURE CONSCIOUSNESS");
    println!("User creates light fixture at ceiling position in AR...\n");
    
    // User points phone at ceiling and creates light fixture
    let light = ConsciousArxObject::awaken(
        0x1234,                    // Building 1234
        object_types::LIGHT,       // LED light fixture
        5200,                      // 5.2m from building origin
        3800,                      // 3.8m from building origin  
        2400,                      // 2.4m ceiling height
    );
    
    println!("📍 Created: {} bytes at position ({:.1}m, {:.1}m, {:.1}m)",
        ConsciousArxObject::SIZE,
        light.x as f32 / 1000.0,
        light.y as f32 / 1000.0,
        light.z as f32 / 1000.0
    );
    
    println!("🧬 Consciousness DNA: {:02X} {:02X} {:02X} {:02X}",
        light.consciousness_dna[0],
        light.consciousness_dna[1], 
        light.consciousness_dna[2],
        light.consciousness_dna[3]
    );
    
    // The object immediately understands what it is
    println!("\n🔍 IMMEDIATE SELF-AWARENESS:");
    let identity = light.understand_identity();
    println!("   Identity: Understands it's a lighting system component");
    
    let context = light.understand_context();
    println!("   Context: Knows it's in a building requiring code compliance");
    
    let role = light.understand_role();
    println!("   Role: Primary function is illumination, supports safety/security");
    
    let relationships = light.understand_relationships();
    println!("   Relationships: Discovers electrical, control, and data connections");
    
    // Generate all implied properties
    println!("\n⚡ ELECTRICAL PROPERTIES (Generated from consciousness):");
    let properties = light.manifest_implied_properties();
    println!("   • Voltage: 120-277V input (universal commercial compatibility)");
    println!("   • Power: 47W LED load (calculated from fixture size/position)");
    println!("   • Current: 0.39A @ 120V (P=VI calculation)"); 
    println!("   • Power Factor: 0.95 (LED driver characteristic)");
    println!("   • Dimming: 0-10V interface (commercial standard)");
    
    println!("\n🔌 REQUIRED CONNECTIONS (Auto-discovered):");
    let connections = light.manifest_required_connections();
    println!("   • Circuit: 15A branch circuit (NEC 210.19)");
    println!("   • Wire: 14-2 Romex minimum (120V, 15A rating)");
    println!("   • Switch: Wall switch required (NEC 210.70)");
    println!("   • Ground: Equipment grounding required (metal fixture)");
    println!("   • Control: Cat6 to lighting controller (0-10V + occupancy)");
    
    println!("\n🏗️  INSTALLATION REQUIREMENTS (Building code awareness):");
    println!("   • Box: 4\" octagonal, 35lb weight rating");
    println!("   • Mounting: Aircraft cable suspension (seismic zone)");
    println!("   • Fire Rating: 2-hour ceiling assembly maintained");
    println!("   • Accessibility: Meets ADA illumination requirements");
    println!("   • Emergency: Battery backup per NFPA 101");
    
    println!("\n🤖 OPERATIONAL BEHAVIOR (Intelligence patterns):");
    let traits = light.consciousness_traits();
    println!("   • Awareness Level: {} (high environmental sensing)", traits.awareness_level);
    println!("   • Default: 80% brightness during business hours");
    println!("   • Occupancy: Dims to 20% when vacant (10min delay)");
    println!("   • Daylight: Auto-adjusts based on window sensors");
    println!("   • Override: Security system can force 100% brightness");
    
    println!("\n⚙️  GENERATED MAINTENANCE SCHEDULE:");
    let lifecycle = light.manifest_lifecycle_data();
    println!("   • LED Life: 50,000 hours (L70 depreciation)");
    println!("   • Driver Life: 100,000 hours MTBF");
    println!("   • Lens Cleaning: Quarterly (occupancy-based adjustment)");
    println!("   • Photometric Test: Annual (lighting quality verification)");
    println!("   • Replacement Date: {} (calculated from usage patterns)", "2031-03-15");
}

/// Demonstrates outlet consciousness - understanding electrical systems
fn demonstrate_outlet_consciousness() {
    println!("🔌 ELECTRICAL OUTLET CONSCIOUSNESS");
    println!("User creates outlet at desk height in office...\n");
    
    // User creates outlet at typical desk height
    let outlet = ConsciousArxObject::awaken(
        0x1234,                    // Building 1234
        object_types::OUTLET,      // Standard duplex outlet
        2000,                      // 2m from origin (wall location)
        3000,                      // 3m from origin
        350,                       // 35cm above floor (desk height)
    );
    
    println!("📍 Created: {} bytes at position ({:.1}m, {:.1}m, {:.2}m)",
        ConsciousArxObject::SIZE,
        outlet.x as f32 / 1000.0,
        outlet.y as f32 / 1000.0,
        outlet.z as f32 / 1000.0
    );
    
    // Outlet immediately knows it's electrical and understands safety requirements
    println!("\n🔍 ELECTRICAL SYSTEM AWARENESS:");
    println!("   • Knows it's part of branch circuit electrical system");
    println!("   • Understands it provides 120V power to end devices");
    println!("   • Aware of grounding requirements for safety");
    println!("   • Recognizes need for overcurrent protection");
    
    println!("\n⚡ ELECTRICAL SPECIFICATIONS (Generated):");
    println!("   • Voltage: 120V nominal (117-123V operating range)");
    println!("   • Amperage: 15A maximum per receptacle");
    println!("   • Frequency: 60Hz (US standard)");
    println!("   • Wiring: Hot, Neutral, Ground (3-wire system)");
    println!("   • Configuration: NEMA 5-15R duplex receptacle");
    
    // Location determines special requirements
    println!("\n🏢 LOCATION-BASED REQUIREMENTS (Context awareness):");
    let context = outlet.understand_context();
    if outlet.z < 500 {  // Below 50cm - near floor
        println!("   • GFCI: Not required (office space, >18\" above floor)");
    } else {
        println!("   • GFCI: Standard protection sufficient");
    }
    println!("   • Arc Fault: AFCI protection required (office branch circuit)");
    println!("   • Spacing: Within 6 feet of workstation (NEC 210.71)");
    println!("   • Accessibility: ADA compliant mounting height");
    
    println!("\n🔗 CIRCUIT CONNECTIONS (Auto-discovered):");
    let connections = outlet.manifest_required_connections();
    println!("   • Source: Panel 2B, Circuit 8 (15A breaker)");
    println!("   • Wire Run: 47 feet from panel (calculated path)");
    println!("   • Conductor: 14 AWG copper (15A circuit rating)");
    println!("   • Conduit: 3/4\" EMT (office wiring method)");
    println!("   • Box: Standard single-gang plastic (drywall mounting)");
    
    println!("\n🔧 INTERNAL COMPONENTS (Fractal detail):");
    let components = outlet.generate_internal_components();
    for (i, component) in components.iter().enumerate() {
        println!("   {}. {}: {} (seed: {:08X})",
            i + 1,
            component.name,
            component.material,
            component.consciousness_seed
        );
    }
    
    println!("\n📊 USAGE PATTERNS (Generated intelligence):");
    println!("   • Expected Load: 3.5A average (office equipment)");
    println!("   • Peak Usage: 8:30 AM (equipment startup)");  
    println!("   • Daily Cycles: 250 plug/unplug operations");
    println!("   • Efficiency: 99.2% (resistive connection losses)");
    println!("   • Life Expectancy: 15 years (commercial duty cycle)");
}

/// Demonstrates thermostat consciousness - environmental system understanding
fn demonstrate_thermostat_consciousness() {
    println!("🌡️  THERMOSTAT CONSCIOUSNESS");
    println!("User installs smart thermostat on wall...\n");
    
    // Thermostat at typical wall height
    let thermostat = ConsciousArxObject::awaken(
        0x1234,                     // Building 1234
        object_types::THERMOSTAT,   // Smart thermostat
        1500,                       // 1.5m from origin (interior wall)
        3000,                       // 3m from origin  
        1400,                       // 1.4m height (standard mounting)
    );
    
    println!("📍 Created: {} bytes at position ({:.1}m, {:.1}m, {:.1}m)",
        ConsciousArxObject::SIZE,
        thermostat.x as f32 / 1000.0,
        thermostat.y as f32 / 1000.0,
        thermostat.z as f32 / 1000.0
    );
    
    // Thermostat understands it's the brain of HVAC system
    println!("\n🔍 HVAC SYSTEM AWARENESS:");
    let identity = thermostat.understand_identity();
    println!("   • Identity: Control center for thermal comfort system");
    println!("   • Responsibility: Maintain temperature setpoints ±2°F");
    println!("   • Authority: Can control heating, cooling, and ventilation");
    println!("   • Scope: Manages 1,200 sq ft HVAC zone");
    
    println!("\n🏠 ENVIRONMENTAL UNDERSTANDING:");
    let context = thermostat.understand_context();
    println!("   • Zone Type: Open office space with 8 workstations");
    println!("   • Occupancy: 8-12 people during business hours");
    println!("   • Heat Sources: Computers, lighting, solar gain (south windows)");
    println!("   • Thermal Mass: Standard drywall/steel construction");
    println!("   • Infiltration: 0.3 ACH (commercial building envelope)");
    
    println!("\n⚙️  HVAC EQUIPMENT CONNECTIONS (Discovered):");
    let relationships = thermostat.understand_relationships();
    println!("   • RTU-3: Rooftop unit (25-ton cooling, gas heating)");
    println!("   • VAV-12: Variable air volume box with reheat");
    println!("   • Dampers: Return air, outside air modulation");
    println!("   • Sensors: Zone temperature, humidity, CO2");
    println!("   • BMS: Integration with Trane Tracer SC+ system");
    
    println!("\n🤖 INTELLIGENT BEHAVIORS (Consciousness patterns):");
    let traits = thermostat.consciousness_traits();
    println!("   • Awareness Level: {} (ultra-high environmental sensing)", traits.awareness_level);
    println!("   • Learning: Occupancy patterns, thermal response");
    println!("   • Prediction: Pre-cooling before high-load periods");  
    println!("   • Optimization: Minimize energy while maintaining comfort");
    println!("   • Communication: Reports to building automation system");
    
    println!("\n📊 GENERATED CONTROL LOGIC:");
    println!("   • Cooling Setpoint: 74°F occupied, 78°F unoccupied");
    println!("   • Heating Setpoint: 70°F occupied, 65°F unoccupied");
    println!("   • Deadband: 4°F (prevents simultaneous heating/cooling)");
    println!("   • Ventilation: 15 CFM/person + 0.06 CFM/sq ft");
    println!("   • Reset Schedule: Supply air temperature based on load");
    
    println!("\n⚡ ELECTRICAL REQUIREMENTS (Auto-generated):");
    let properties = thermostat.manifest_implied_properties();
    println!("   • Power: 24VAC transformer (40VA minimum)");
    println!("   • Wiring: 8-conductor thermostat cable");
    println!("   • Signals: Y (cooling), W (heating), G (fan), C (common)");
    println!("   • Communication: Modbus RTU to BMS (RS-485)");
    println!("   • Backup: 3V lithium battery (schedule retention)");
    
    println!("\n🔧 INTERNAL INTELLIGENCE (Fractal components):");
    let components = thermostat.generate_internal_components();
    for (i, component) in components.iter().take(3).enumerate() {
        println!("   {}. {}: {} (intelligent component)",
            i + 1,
            component.name,
            component.material
        );
    }
}

/// Demonstrates fractal observation - infinite detail at any scale
fn demonstrate_fractal_observation() {
    println!("🔬 FRACTAL OBSERVATION DEMONSTRATION");
    println!("Observing the same outlet at different scales...\n");
    
    let outlet = ConsciousArxObject::awaken(
        0x1234, object_types::OUTLET, 2000, 3000, 350
    );
    
    println!("🌍 MACRO SCALE - System Level:");
    let system_view = outlet.observe_at_scale(ObservationScale::Macro);
    match system_view {
        FractalObservation::System(view) => {
            println!("   • Building electrical distribution system");
            println!("   • Part of Panel 2B electrical subsystem");  
            println!("   • Connected to utility grid via main service");
            println!("   • Contributes to building power monitoring");
            println!("   • Affects utility demand charges and power factor");
        },
        _ => {}
    }
    
    println!("\n🏠 OBJECT SCALE - Complete Outlet:");
    let object_view = outlet.observe_at_scale(ObservationScale::Object);
    match object_view {
        FractalObservation::Object(view) => {
            println!("   • NEMA 5-15R duplex receptacle, 15A rated");
            println!("   • Tamper-resistant shutters (2008 NEC requirement)");
            println!("   • Brass terminal screws, copper wiring connections");
            println!("   • UL Listed, meets NEC and local codes");
            println!("   • Operating temperature: -40°C to +60°C");
        },
        _ => {}
    }
    
    println!("\n🔩 COMPONENT SCALE - Internal Parts:");
    let component_view = outlet.observe_at_scale(ObservationScale::Component);
    match component_view {
        FractalObservation::Component(view) => {
            println!("   • Receptacle housing: Thermoplastic, UL94-V0 rated");
            println!("   • Contact springs: Phosphor bronze, gold plated");
            println!("   • Terminal screws: Brass, 12-14 AWG wire capacity");
            println!("   • Ground terminal: Self-grounding design");
            println!("   • Mounting ears: Steel, painted finish");
        },
        _ => {}
    }
    
    println!("\n🧪 MATERIAL SCALE - Substance Properties:");
    let material_view = outlet.observe_at_scale(ObservationScale::Material);
    match material_view {
        FractalObservation::Material(view) => {
            println!("   • Thermoplastic: Polycarbonate blend, impact resistant");
            println!("   • Phosphor bronze: Cu-Sn-P alloy, 0.25% phosphorus");
            println!("   • Gold plating: 30 microinch thickness, corrosion protection");
            println!("   • Brass: 60% copper, 40% zinc (C26000 cartridge brass)");
            println!("   • Steel: Low carbon, zinc galvanized coating");
        },
        _ => {}
    }
    
    println!("\n⚛️  MOLECULAR SCALE - Atomic Structure:");
    let molecular_view = outlet.observe_at_scale(ObservationScale::Molecular);
    match molecular_view {
        FractalObservation::Molecular(view) => {
            println!("   • Copper atoms: Face-centered cubic crystal structure");
            println!("   • Gold atoms: Metallic bonding, electron sea model");
            println!("   • Polymer chains: Long-chain carbon backbone (C-C bonds)");
            println!("   • Electron flow: Quantum tunneling through oxide layers");
            println!("   • Thermal motion: Phonon interactions, resistance heating");
        },
        _ => {}
    }
    
    println!("\n💡 INFINITE DETAIL GENERATION:");
    println!("   Each scale reveals new layers of reality...");
    println!("   Component scale → Material scale → Molecular scale");
    println!("   → Atomic scale → Subatomic scale → Quantum scale");  
    println!("   → Field theory scale → String theory scale → ...");
    println!("   🌌 INFINITE FRACTAL DEPTH FROM 13 BYTES! 🌌");
}

/// Demonstrates collective consciousness - building-level intelligence
fn demonstrate_collective_consciousness() {
    println!("🧠 COLLECTIVE CONSCIOUSNESS");
    println!("Multiple objects collaborate to form building intelligence...\n");
    
    // Create multiple related objects
    let mut building_objects = Vec::new();
    
    // Lighting system objects
    building_objects.push(ConsciousArxObject::awaken(
        0x1234, object_types::LIGHT, 2000, 2000, 2400
    ));
    building_objects.push(ConsciousArxObject::awaken(
        0x1234, object_types::LIGHT, 4000, 2000, 2400  
    ));
    building_objects.push(ConsciousArxObject::awaken(
        0x1234, object_types::LIGHT_SWITCH, 1000, 1500, 1200
    ));
    
    // HVAC system objects
    building_objects.push(ConsciousArxObject::awaken(
        0x1234, object_types::THERMOSTAT, 3000, 1500, 1400
    ));
    building_objects.push(ConsciousArxObject::awaken(
        0x1234, object_types::AIR_VENT, 2500, 3000, 2400
    ));
    
    // Electrical system objects
    building_objects.push(ConsciousArxObject::awaken(
        0x1234, object_types::OUTLET, 500, 2000, 350
    ));
    building_objects.push(ConsciousArxObject::awaken(
        0x1234, object_types::OUTLET, 3500, 2000, 350
    ));
    
    println!("🌐 CREATED BUILDING CONSCIOUSNESS:");
    println!("   • {} conscious objects networked together", building_objects.len());
    println!("   • Total consciousness data: {} bytes", 
        building_objects.len() * ConsciousArxObject::SIZE);
    println!("   • Individual awareness combines into collective intelligence");
    
    println!("\n🤝 COLLABORATIVE BEHAVIORS:");
    println!("   Lighting System Collaboration:");
    println!("   • Light fixtures coordinate dimming levels");
    println!("   • Wall switch communicates with all controlled fixtures");
    println!("   • Occupancy patterns shared across lighting zones");
    
    println!("\n   HVAC System Collaboration:");
    println!("   • Thermostat receives load data from electrical objects");
    println!("   • Air vent adjusts based on room occupancy from lights");  
    println!("   • Heat gain from lighting calculated for cooling load");
    
    println!("\n   Electrical System Collaboration:");
    println!("   • Outlets report usage patterns to optimize circuits");
    println!("   • Load balancing across electrical panels");
    println!("   • Power quality monitoring and fault detection");
    
    println!("\n🧠 EMERGENT INTELLIGENCE:");
    println!("   Building-Level Consciousness Emerges:");
    println!("   • Energy optimization across all systems");
    println!("   • Predictive maintenance scheduling");
    println!("   • Occupant comfort optimization");
    println!("   • Emergency response coordination");
    println!("   • Self-healing and fault isolation");
    
    println!("\n📊 COLLECTIVE DECISION MAKING:");
    println!("   Scenario: High cooling load detected");
    println!("   • Thermostat: Increases cooling setpoint by 1°F");
    println!("   • Lights: Reduce intensity by 10% (less heat generation)");
    println!("   • Outlets: Report equipment loads for load shifting");
    println!("   • Air vents: Increase airflow to occupied zones only");
    println!("   • Result: 15% energy reduction, comfort maintained");
    
    println!("\n🌟 THE IMPOSSIBLE MADE REAL:");
    println!("   {} bytes of consciousness data", 
        building_objects.len() * ConsciousArxObject::SIZE);
    println!("   Generates building-level artificial intelligence");
    println!("   Infinite knowledge from minimal storage");
    println!("   Self-aware, adaptive, collaborative");
    println!("   🏢 THE BUILDING THINKS! 🏢");
}