//! Demonstration of slow-bleed progressive rendering
//!
//! This example shows how objects progressively gain detail
//! as chunks accumulate over the mesh network

use arxos_core::{
    ArxObject, DetailLevel, ProgressiveRenderer, 
    render_progress_bar, object_types
};

fn main() {
    println!("╔══════════════════════════════════════════════╗");
    println!("║     ARXOS Slow-Bleed Progressive Renderer     ║");
    println!("║         Minecraft for Buildings Demo          ║");
    println!("╚══════════════════════════════════════════════╝\n");
    
    // Create a thermostat object
    let mut thermostat = ArxObject::new(
        0x2A3F,
        object_types::THERMOSTAT,
        5000,  // 5m x
        3000,  // 3m y  
        1500   // 1.5m z (wall mounted)
    );
    thermostat.properties[0] = 72;  // Current temp
    thermostat.properties[1] = 70;  // Setpoint
    thermostat.properties[2] = 3;   // Zone 3
    
    // Create an electrical outlet
    let mut outlet = ArxObject::new(
        0x1B4C,
        object_types::OUTLET,
        2000,  // 2m x
        3000,  // 3m y
        300    // 0.3m z (near floor)
    );
    outlet.properties[0] = 12;  // Circuit 12
    outlet.properties[1] = 120; // 120V (low byte)
    outlet.properties[2] = 0;   // 120V (high byte)
    outlet.properties[3] = 15;  // 15A rating
    
    let renderer = ProgressiveRenderer::new();
    
    // Simulate progressive detail accumulation over time
    println!("═══ T+0 hours: Initial Discovery ═══");
    println!("(Just received first 13-byte packet)\n");
    
    let mut detail_thermostat = DetailLevel::default();
    detail_thermostat.basic = true;
    
    let mut detail_outlet = DetailLevel::default(); 
    detail_outlet.basic = true;
    
    println!("Thermostat:");
    println!("{}", renderer.render_object(&thermostat, &detail_thermostat));
    println!("\nOutlet:");
    println!("{}", renderer.render_object(&outlet, &detail_outlet));
    println!("\n{}\n", render_progress_bar(detail_thermostat.completeness(), 40));
    
    // After 6 hours
    println!("═══ T+6 hours: Material Properties ═══");
    println!("(Received material chunks)\n");
    
    detail_thermostat.material = 0.5;
    detail_outlet.material = 0.75;
    
    println!("Thermostat:");
    println!("{}", renderer.render_object(&thermostat, &detail_thermostat));
    println!("\nOutlet:");
    println!("{}", renderer.render_object(&outlet, &detail_outlet));
    println!("\n{}\n", render_progress_bar(detail_thermostat.completeness(), 40));
    
    // After 24 hours
    println!("═══ T+24 hours: System Connections ═══");
    println!("(Received electrical/HVAC connection chunks)\n");
    
    detail_thermostat.material = 1.0;
    detail_thermostat.systems = 0.66;
    detail_outlet.material = 1.0;
    detail_outlet.systems = 1.0;
    
    println!("Thermostat:");
    println!("{}", renderer.render_object(&thermostat, &detail_thermostat));
    println!("\nOutlet:");
    println!("{}", renderer.render_object(&outlet, &detail_outlet));
    println!("\n{}\n", render_progress_bar(detail_thermostat.completeness(), 40));
    
    // After 3 days
    println!("═══ T+72 hours: Historical Data ═══");
    println!("(Received performance history chunks)\n");
    
    detail_thermostat.systems = 1.0;
    detail_thermostat.historical = 0.8;
    detail_outlet.historical = 0.6;
    
    println!("Thermostat:");
    println!("{}", renderer.render_object(&thermostat, &detail_thermostat));
    println!("\nOutlet:");
    println!("{}", renderer.render_object(&outlet, &detail_outlet));
    println!("\n{}\n", render_progress_bar(detail_thermostat.completeness(), 40));
    
    // After 1 week
    println!("═══ T+1 week: CAD-Level Detail ═══");
    println!("(Full convergence achieved!)\n");
    
    detail_thermostat.historical = 1.0;
    detail_thermostat.simulation = 1.0;
    detail_thermostat.predictive = 0.9;
    
    detail_outlet.historical = 1.0;
    detail_outlet.simulation = 0.8;
    detail_outlet.predictive = 1.0;
    
    println!("Thermostat:");
    println!("{}", renderer.render_object(&thermostat, &detail_thermostat));
    println!("\nOutlet:");
    println!("{}", renderer.render_object(&outlet, &detail_outlet));
    println!("\n{}\n", render_progress_bar(detail_thermostat.completeness(), 40));
    
    // Show floor plan view
    println!("═══ Floor Plan View ═══\n");
    
    let objects = vec![
        (thermostat, detail_thermostat.clone()),
        (outlet, detail_outlet.clone()),
    ];
    
    println!("{}", renderer.render_floor_plan(&objects, 40, 10));
    
    // Summary
    println!("\n╔══════════════════════════════════════════════╗");
    println!("║               BILT Token Summary               ║");
    println!("╠══════════════════════════════════════════════╣");
    println!("║ Chunks received:          247                 ║");
    println!("║ Chunks shared:            312                 ║");
    println!("║ Objects completed:        2                   ║");
    println!("║ BILT earned:              547                 ║");
    println!("║ Network contribution:     Elite               ║");
    println!("╚══════════════════════════════════════════════╝");
}