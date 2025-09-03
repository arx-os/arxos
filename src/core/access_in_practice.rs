//! Access Control In Practice - How it Actually Works
//! 
//! Forget complex IAM architectures. Here's how access REALLY works
//! in buildings with ArxOS over mesh networks.

use crate::arxobject::ArxObject;
use crate::simple_access_control::{SimpleAccess, CompanyCode, RoleCode};

/// How access actually flows in the field
pub struct FieldAccessFlow;

impl FieldAccessFlow {
    pub fn demonstrate() {
        println!("\n🏢 How Access Actually Works in ArxOS\n");
        
        Self::morning_arrival();
        Self::cross_system_work();
        Self::emergency_override();
        Self::trust_building();
        Self::the_simple_truth();
    }
    
    fn morning_arrival() {
        println!("📅 Monday Morning - HVAC Tech Arrives");
        println!("══════════════════════════════════════\n");
        
        println!("Tech's radio automatically broadcasts:");
        println!("  \"Johnson Controls HVAC tech requesting access\"");
        println!();
        
        println!("Building's mesh node receives and checks:");
        println!("  ✓ Johnson Controls is approved vendor");
        println!("  ✓ Monday is scheduled maintenance day");
        println!("  ✓ Tech's ID matches work order");
        println!();
        
        println!("Building responds (13 bytes):");
        println!("  📡 Access granted for 8 hours");
        println!("  📡 Can see: HVAC + Electrical panels + Navigation");
        println!("  📡 Can modify: HVAC only");
        println!("  📡 Session ID: 42");
        println!();
    }
    
    fn cross_system_work() {
        println!("🔧 Real Work - Troubleshooting No Heat");
        println!("═══════════════════════════════════════\n");
        
        println!("Tech: \"Show me room 203's thermostat\"");
        println!("ArxOS: ✓ [Returns thermostat data]");
        println!();
        
        println!("Tech: \"Show me the electrical panel for this zone\"");
        println!("ArxOS: ✓ [Returns panel data - READ ONLY]");
        println!("       Note: Tech sees it's tripped");
        println!();
        
        println!("Tech: \"Reset breaker 14\"");
        println!("ArxOS: ❌ \"Cannot modify electrical. Flagging for electrician.\"");
        println!();
        
        println!("Tech: \"Add note: Breaker 14 tripped, needs electrical check\"");
        println!("ArxOS: ✓ [Annotation added, electrician notified]");
        println!();
        
        println!("This is GOOD! Tech found root cause without");
        println!("needing to modify systems outside expertise.");
        println!();
    }
    
    fn emergency_override() {
        println!("🚨 Emergency - Fire Alarm");
        println!("═════════════════════════\n");
        
        println!("Fire Marshal's radio broadcasts:");
        println!("  \"EMERGENCY OVERRIDE - FIRE MARSHAL\"");
        println!();
        
        println!("Building immediately grants:");
        println!("  🔴 Access Level: EMERGENCY");
        println!("  🔴 Can see: EVERYTHING");
        println!("  🔴 Can modify: Doors, Power, HVAC");
        println!("  🔴 Duration: Until all-clear");
        println!();
        
        println!("Fire Marshal: \"Kill power to zone 3\"");
        println!("ArxOS: ✓ [Power disconnected]");
        println!();
        
        println!("Fire Marshal: \"Open all exits\"");
        println!("ArxOS: ✓ [All exits unlocked]");
        println!();
        
        println!("No authentication delays. No permission checks.");
        println!("Emergency = Full access. Period.");
        println!();
    }
    
    fn trust_building() {
        println!("📈 Trust Over Time");
        println!("═══════════════════\n");
        
        println!("New tech (Day 1):");
        println!("  Trust: 50/255");
        println!("  Access: Basic only");
        println!("  Supervision: Required");
        println!();
        
        println!("After 10 successful visits:");
        println!("  Trust: 100/255");
        println!("  Access: Can request escalation");
        println!("  Supervision: Not required");
        println!();
        
        println!("After 6 months:");
        println!("  Trust: 200/255");
        println!("  Access: Extended by default");
        println!("  Privileges: Can train others");
        println!();
        
        println!("Trust is earned through:");
        println!("  ✓ Completing work properly");
        println!("  ✓ Not attempting unauthorized access");
        println!("  ✓ Helping identify issues");
        println!("  ✓ Time and consistency");
        println!();
    }
    
    fn the_simple_truth() {
        println!("💡 The Simple Truth About IAM");
        println!("════════════════════════════════\n");
        
        println!("Complex IAM systems assume:");
        println!("  ❌ Constant internet");
        println!("  ❌ Certificate infrastructure");
        println!("  ❌ Directory services");
        println!("  ❌ IT staff on-site");
        println!();
        
        println!("ArxOS assumes reality:");
        println!("  ✅ Internet might be down");
        println!("  ✅ It's just a building");
        println!("  ✅ Radios always work");
        println!("  ✅ 13 bytes is enough");
        println!();
        
        println!("Our entire IAM:");
        println!("┌─────────────────────────────┐");
        println!("│ 1. Who are you?   (2 bytes)│");
        println!("│ 2. Why here?      (2 bytes)│");
        println!("│ 3. What can see?  (4 bytes)│");
        println!("│ 4. How trusted?   (1 byte) │");
        println!("│ 5. When expires?  (2 bytes)│");
        println!("│ 6. Checksum       (2 bytes)│");
        println!("└─────────────────────────────┘");
        println!("         Total: 13 bytes");
        println!();
    }
}

/// Common access patterns we see in real buildings
pub struct CommonPatterns;

impl CommonPatterns {
    pub fn hvac_needs_electrical() -> SimpleAccess {
        let mut access = SimpleAccess::new_for_tech(
            CompanyCode::LocalHVAC,
            RoleCode::HVACTech,
            1, // 1 day
        );
        
        // HVAC tech ALWAYS needs to see electrical
        access.access_mask |= 1 << 11; // ELECTRICAL_PANEL
        access.access_mask |= 1 << 6;  // OUTLET (for tools)
        
        access
    }
    
    pub fn electrician_needs_structure() -> SimpleAccess {
        let mut access = SimpleAccess::new_for_tech(
            CompanyCode::LocalElectrical,
            RoleCode::Electrician,
            1,
        );
        
        // Electrician needs to understand building structure
        access.access_mask |= 1 << 0; // WALL (conduit routing)
        access.access_mask |= 1 << 2; // CEILING (fixture mounting)
        access.access_mask |= 1 << 5; // COLUMN (avoid structural)
        
        access
    }
    
    pub fn maintenance_sees_all() -> SimpleAccess {
        SimpleAccess::new_for_tech(
            CompanyCode::BuildingOwner,
            RoleCode::Maintenance,
            365, // Year-round access
        )
        // Already has 0xFFFF mask (sees everything)
    }
}

/// The permission check that happens 1000x per day
pub fn fast_permission_check(
    session: &SimpleAccess,
    object: &ArxObject,
) -> bool {
    // This ENTIRE permission check is just bit operations!
    
    // 1. Compare building IDs (2-byte comparison)
    if session.building_id != object.building_id {
        return false;
    }
    
    // 2. Check expiration (2-byte comparison)
    if session.expires_days < days_since_2024() {
        return false;
    }
    
    // 3. Check access mask (1 bit shift + AND)
    let allowed = (session.access_mask & (1 << object.object_type)) != 0;
    
    allowed
    
    // That's it! 3 integer operations.
    // No database lookups, no network calls, no certificates.
}

/// Why this works in practice
pub fn why_this_works() {
    println!("\n🎯 Why Simple Access Works\n");
    
    println!("1️⃣ Buildings are not banks");
    println!("   • Physical security already exists");
    println!("   • Cameras watch everything");
    println!("   • Humans verify identity");
    println!();
    
    println!("2️⃣ Perfect security < Working system");
    println!("   • During emergencies, access > security");
    println!("   • Broken AC needs fixing NOW");
    println!("   • Complex IAM = nobody can work");
    println!();
    
    println!("3️⃣ Trust is human, not cryptographic");
    println!("   • Same HVAC tech for 5 years");
    println!("   • Building manager knows them");
    println!("   • Reputation matters more than certificates");
    println!();
    
    println!("4️⃣ 13 bytes handles 99% of cases");
    println!("   • 256 companies");
    println!("   • 256 roles");  
    println!("   • 32 object types");
    println!("   • 65,535 day expiration");
    println!("   • That's... everything you need!");
}

fn days_since_2024() -> u16 {
    // Simplified for demo
    100
}