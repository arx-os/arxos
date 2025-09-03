//! Complete Access Management Demo
//! 
//! Shows how Hypori-inspired concepts + SMS onboarding + simple IAM
//! combine into a practical field-ready system.

use arxos_core::simple_access_control::{SimpleAccess, CompanyCode, RoleCode};
use arxos_core::sms_access_token::SMSAccessToken;
use arxos_core::arxobject::ArxObject;

fn main() {
    println!("\n");
    println!("╔══════════════════════════════════════════════════╗");
    println!("║        ArxOS Complete Access System Demo         ║");
    println!("║                                                  ║");
    println!("║  Hypori Concepts + SMS + Simple IAM = Success   ║");
    println!("╚══════════════════════════════════════════════════╝");
    println!();
    
    morning_arrival();
    cross_system_visibility();
    sms_flow();
    mesh_transmission();
    complete_picture();
}

fn morning_arrival() {
    println!("📅 8:00 AM - HVAC Tech Arrives Unexpectedly");
    println!("═══════════════════════════════════════════\n");
    
    println!("Tech: \"I'm here to check the units\"");
    println!("Manager: \"Let me grant you access...\"\n");
    
    println!("Manager's Terminal:");
    println!("┌─────────────────────────────────────┐");
    println!("│ $ grant 555-0100 hvac 8h            │");
    println!("│ ✅ SMS sent to 555-0100             │");
    println!("└─────────────────────────────────────┘");
    println!();
    
    std::thread::sleep(std::time::Duration::from_secs(1));
}

fn cross_system_visibility() {
    println!("🔧 8:05 AM - Tech Working");
    println!("═══════════════════════════════\n");
    
    println!("Tech (via app): \"Show room 203\"");
    println!("ArxOS returns:");
    println!("  • 2 HVAC vents (can modify)");
    println!("  • 1 Thermostat (can modify)");
    println!("  • 1 Electrical panel (READ ONLY)");
    println!("  • 4 Outlets (READ ONLY)");
    println!();
    
    println!("Tech: \"Thermostat set to 72°F\"");
    println!("ArxOS: ✅ Modified");
    println!();
    
    println!("Tech: \"Why no heat?\"");
    println!("Tech: \"Show electrical panel\"");
    println!("ArxOS: Panel shows breaker 14 tripped");
    println!();
    
    println!("Tech: \"Reset breaker 14\"");
    println!("ArxOS: ❌ Cannot modify electrical");
    println!("ArxOS: 📝 Flagging for electrician");
    println!();
    
    std::thread::sleep(std::time::Duration::from_secs(1));
}

fn sms_flow() {
    println!("📱 8:10 AM - Tech Calls Electrician Partner");
    println!("════════════════════════════════════════════\n");
    
    println!("HVAC Tech: \"Need electrical help in room 203\"");
    println!("Electrician: \"On my way\"\n");
    
    println!("HVAC Tech shares access:");
    println!("┌─────────────────────────────────────┐");
    println!("│ $ arx -share 555-0200 --role=elec   │");
    println!("└─────────────────────────────────────┘");
    println!();
    
    println!("Electrician receives SMS:");
    println!("┌─────────────────────────────────────┐");
    println!("│ Jim shared West High access         │");
    println!("│ Code: B7K4M2                        │");
    println!("│ Role: Electrical                     │");
    println!("│ Tap: arxos://access/0042/B7K4M2     │");
    println!("└─────────────────────────────────────┘");
    println!();
    
    // Show the token conversion
    let token = SMSAccessToken::from_sms_code("B7K4M2", "555-0200", 0x0042);
    let access = token.to_simple_access();
    
    println!("Token → Access: {} hours, trust level {}", 
        token.hours_remaining, access.trust_level);
    println!();
    
    std::thread::sleep(std::time::Duration::from_secs(1));
}

fn mesh_transmission() {
    println!("📡 How It Works Over Mesh");
    println!("════════════════════════\n");
    
    // Create access token as ArxObject
    let token = SMSAccessToken::from_sms_code("K7M3X9", "555-0100", 0x0042);
    let arx = token.to_arxobject();
    let bytes = arx.to_bytes();
    
    println!("1️⃣ SMS Token: 'K7M3X9' (6 chars)");
    println!("     ↓");
    println!("2️⃣ ArxObject: {} bytes", bytes.len());
    println!("   Building: 0x{:04X}", arx.building_id);
    println!("   Type: 0xFE (Access Token)");
    println!("   Data: {:02X?}", &bytes[0..8]);
    println!("     ↓");
    println!("3️⃣ LoRa Packet: 900MHz transmission");
    println!("     ↓");
    println!("4️⃣ Building receives & validates");
    println!("     ↓");
    println!("5️⃣ Access granted for {} hours!", token.hours_remaining);
    println!();
    
    // Show permission check
    let simple = SimpleAccess::new_for_tech(
        CompanyCode::LocalHVAC,
        RoleCode::HVACTech,
        8,
    );
    
    println!("Permission Check (3 CPU ops):");
    println!("  if building_id != obj.building {{ return false }}");
    println!("  if expired {{ return false }}");
    println!("  return (mask & (1 << type)) != 0");
    println!();
    println!("That's it! No database, no network, no certificates.");
    println!();
    
    std::thread::sleep(std::time::Duration::from_secs(1));
}

fn complete_picture() {
    println!("🎯 The Complete Picture");
    println!("═══════════════════════\n");
    
    println!("What we borrowed from Hypori:");
    println!("  • Virtual workspaces → Virtual Building Spaces");
    println!("  • Pixel streaming → ASCII streaming (7500:1 smaller)");
    println!("  • Zero-trust → Every packet signed");
    println!();
    
    println!("What we added:");
    println!("  • SMS onboarding (30 seconds)");
    println!("  • Offline-first (no internet required)");
    println!("  • Cross-system visibility (HVAC sees electrical)");
    println!("  • 13-byte everything");
    println!();
    
    println!("The Result:");
    println!("┌────────────────────────────────────────┐");
    println!("│                                        │");
    println!("│  Complex enterprise IAM problem        │");
    println!("│              ↓                         │");
    println!("│  grant 555-0100 hvac 8h                │");
    println!("│              ↓                         │");
    println!("│  Problem solved                        │");
    println!("│                                        │");
    println!("└────────────────────────────────────────┘");
    println!();
    
    println!("Why it works:");
    println!("  ✅ Every contractor has a phone");
    println!("  ✅ SMS works everywhere");
    println!("  ✅ No app required");
    println!("  ✅ No internet required");
    println!("  ✅ No IT staff required");
    println!("  ✅ 13 bytes over mesh");
    println!();
    
    println!("Perfect for K-12 schools:");
    println!("  • Limited IT resources");
    println!("  • Contractors arrive unexpectedly");
    println!("  • Need cross-system visibility");
    println!("  • Must work during emergencies");
    println!("  • Budget constraints");
    println!();
    
    println!("                    🏢");
    println!("            The building has a");
    println!("              phone number.");
    println!("              Text it for");
    println!("               access.");
    println!();
}