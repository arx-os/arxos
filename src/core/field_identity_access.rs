//! Field Identity & Access Management for ArxOS
//! 
//! Real-world IAM that acknowledges field techs need cross-system visibility.
//! Simple, practical, and fits in 13-byte packets.

use crate::arxobject::{ArxObject, object_types};
use std::collections::HashMap;

/// Field User Identity - who's accessing the building
#[derive(Debug, Clone)]
pub struct FieldIdentity {
    /// Unique ID (fits in 2 bytes)
    pub user_id: u16,
    
    /// Primary role (what they're here to do)
    pub primary_role: FieldRole,
    
    /// Current access level (can escalate based on need)
    pub access_level: AccessLevel,
    
    /// Active session token (rotates every 8 hours)
    pub session_token: u32,
    
    /// Company/organization ID
    pub org_id: u16,
}

/// Field roles - what the person does
#[repr(u8)]
#[derive(Debug, Clone, Copy, PartialEq)]
pub enum FieldRole {
    // Maintenance & Repair
    HVACTech = 1,
    Electrician = 2,
    Plumber = 3,
    GeneralMaintenance = 4,
    
    // Operations
    FacilityManager = 10,
    SecurityGuard = 11,
    Custodian = 12,
    ITSupport = 13,
    
    // Emergency
    FireMarshal = 20,
    EMT = 21,
    PoliceOfficer = 22,
    
    // Inspection
    BuildingInspector = 30,
    SafetyInspector = 31,
    HealthInspector = 32,
    
    // Visitors
    Contractor = 40,
    Vendor = 41,
    Guest = 42,
}

/// Access levels - progressive trust
#[repr(u8)]
#[derive(Debug, Clone, Copy, PartialEq, PartialOrd)]
pub enum AccessLevel {
    /// Can only view public areas
    Public = 0,
    
    /// Can view their primary system + dependencies
    Basic = 1,
    
    /// Can view all systems, modify their primary
    Standard = 2,
    
    /// Can view and modify multiple systems
    Extended = 3,
    
    /// Full building access (facility manager)
    Full = 4,
    
    /// Emergency override (first responders)
    Emergency = 5,
}

/// Simple permission check that fits in mesh packets
#[derive(Debug, Clone, Copy)]
pub struct PermissionCheck {
    /// User requesting access (2 bytes)
    pub user_id: u16,
    
    /// Object they want to access (2 bytes)
    pub object_id: u16,
    
    /// Action they want to perform (1 byte)
    pub action: ActionType,
    
    /// Their current location (6 bytes: x,y,z as u16 each)
    pub location: (u16, u16, u16),
    
    /// Context flags (1 byte)
    pub context: ContextFlags,
    
    /// Timestamp (1 byte: minutes since midnight)
    pub time_stamp: u8,
}

impl PermissionCheck {
    /// Fits perfectly in 13-byte ArxObject!
    pub fn to_bytes(&self) -> [u8; 13] {
        let mut bytes = [0u8; 13];
        bytes[0..2].copy_from_slice(&self.user_id.to_le_bytes());
        bytes[2..4].copy_from_slice(&self.object_id.to_le_bytes());
        bytes[4] = self.action as u8;
        bytes[5..7].copy_from_slice(&self.location.0.to_le_bytes());
        bytes[7..9].copy_from_slice(&self.location.1.to_le_bytes());
        bytes[9..11].copy_from_slice(&self.location.2.to_le_bytes());
        bytes[11] = self.context.bits();
        bytes[12] = self.time_stamp;
        bytes
    }
}

/// Actions users can perform
#[repr(u8)]
#[derive(Debug, Clone, Copy)]
pub enum ActionType {
    View = 0,
    Inspect = 1,
    Modify = 2,
    Replace = 3,
    Delete = 4,
    Annotate = 5,
    Emergency = 6,
}

/// Context flags for permission decisions
#[derive(Debug, Clone, Copy)]
pub struct ContextFlags {
    bits: u8,
}

impl ContextFlags {
    pub fn new() -> Self {
        Self { bits: 0 }
    }
    
    pub fn set_emergency(&mut self) {
        self.bits |= 0x01;
    }
    
    pub fn set_after_hours(&mut self) {
        self.bits |= 0x02;
    }
    
    pub fn set_with_supervisor(&mut self) {
        self.bits |= 0x04;
    }
    
    pub fn set_troubleshooting(&mut self) {
        self.bits |= 0x08;
    }
    
    pub fn bits(&self) -> u8 {
        self.bits
    }
}

/// Access Control Matrix - who can see/modify what
pub struct AccessMatrix {
    /// Role -> Object Type -> Allowed Actions
    permissions: HashMap<FieldRole, HashMap<u8, Vec<ActionType>>>,
    
    /// Cross-system visibility rules
    visibility_rules: HashMap<FieldRole, Vec<u8>>,
}

impl AccessMatrix {
    pub fn new() -> Self {
        let mut matrix = Self {
            permissions: HashMap::new(),
            visibility_rules: HashMap::new(),
        };
        
        // Define real-world access patterns
        matrix.setup_hvac_tech();
        matrix.setup_electrician();
        matrix.setup_facility_manager();
        matrix.setup_emergency_responder();
        
        matrix
    }
    
    fn setup_hvac_tech(&mut self) {
        // HVAC tech PRIMARY access (can modify)
        let mut hvac_primary = HashMap::new();
        hvac_primary.insert(object_types::HVAC_VENT, vec![
            ActionType::View, ActionType::Inspect, ActionType::Modify, ActionType::Replace
        ]);
        hvac_primary.insert(object_types::THERMOSTAT, vec![
            ActionType::View, ActionType::Inspect, ActionType::Modify, ActionType::Replace
        ]);
        
        // HVAC tech NEEDS TO SEE (read-only)
        self.visibility_rules.insert(FieldRole::HVACTech, vec![
            object_types::ELECTRICAL_PANEL,  // Need to verify power
            object_types::OUTLET,             // For portable equipment
            object_types::WALL,               // For duct routing
            object_types::CEILING,            // For vent placement
            object_types::FLOOR,              // For navigation
            object_types::DOOR,               // For access planning
            object_types::WINDOW,             // Affects HVAC load
        ]);
        
        self.permissions.insert(FieldRole::HVACTech, hvac_primary);
    }
    
    fn setup_electrician(&mut self) {
        // Electrician PRIMARY access
        let mut elec_primary = HashMap::new();
        elec_primary.insert(object_types::ELECTRICAL_PANEL, vec![
            ActionType::View, ActionType::Inspect, ActionType::Modify, ActionType::Replace
        ]);
        elec_primary.insert(object_types::OUTLET, vec![
            ActionType::View, ActionType::Inspect, ActionType::Modify, ActionType::Replace
        ]);
        elec_primary.insert(object_types::LIGHT_SWITCH, vec![
            ActionType::View, ActionType::Inspect, ActionType::Modify, ActionType::Replace
        ]);
        elec_primary.insert(object_types::LIGHT, vec![
            ActionType::View, ActionType::Inspect, ActionType::Modify, ActionType::Replace
        ]);
        
        // Electrician NEEDS TO SEE
        self.visibility_rules.insert(FieldRole::Electrician, vec![
            object_types::HVAC_VENT,         // High-power HVAC units
            object_types::WALL,               // For conduit routing
            object_types::FLOOR,              // For navigation
            object_types::CEILING,            // For light fixtures
            object_types::EMERGENCY_EXIT,     // Emergency lighting
        ]);
        
        self.permissions.insert(FieldRole::Electrician, elec_primary);
    }
    
    fn setup_facility_manager(&mut self) {
        // Facility manager sees EVERYTHING
        self.visibility_rules.insert(FieldRole::FacilityManager, vec![
            object_types::WALL,
            object_types::FLOOR,
            object_types::CEILING,
            object_types::DOOR,
            object_types::WINDOW,
            object_types::COLUMN,
            object_types::OUTLET,
            object_types::LIGHT_SWITCH,
            object_types::LIGHT,
            object_types::HVAC_VENT,
            object_types::THERMOSTAT,
            object_types::ELECTRICAL_PANEL,
            object_types::EMERGENCY_EXIT,
            object_types::CAMERA,
            object_types::MOTION_SENSOR,
        ]);
        
        // Can modify most things
        let mut fm_primary = HashMap::new();
        for obj_type in 0..=15 {
            fm_primary.insert(obj_type, vec![
                ActionType::View, ActionType::Inspect, ActionType::Modify, ActionType::Annotate
            ]);
        }
        self.permissions.insert(FieldRole::FacilityManager, fm_primary);
    }
    
    fn setup_emergency_responder(&mut self) {
        // Emergency responders see critical systems
        self.visibility_rules.insert(FieldRole::FireMarshal, vec![
            object_types::EMERGENCY_EXIT,
            object_types::DOOR,
            object_types::ELECTRICAL_PANEL,
            object_types::WALL,               // For understanding layout
            object_types::FLOOR,              // For navigation
            object_types::HVAC_VENT,          // For smoke management
        ]);
        
        // Can override/modify in emergency
        let mut emergency_access = HashMap::new();
        emergency_access.insert(object_types::DOOR, vec![
            ActionType::Emergency  // Force open
        ]);
        emergency_access.insert(object_types::ELECTRICAL_PANEL, vec![
            ActionType::Emergency  // Shut off power
        ]);
        
        self.permissions.insert(FieldRole::FireMarshal, emergency_access);
    }
    
    /// Check if user can perform action
    pub fn check_permission(
        &self,
        user: &FieldIdentity,
        object: &ArxObject,
        action: ActionType,
    ) -> PermissionResult {
        // Emergency override
        if user.access_level == AccessLevel::Emergency {
            return PermissionResult::Allowed;
        }
        
        // Check primary permissions
        if let Some(role_perms) = self.permissions.get(&user.primary_role) {
            if let Some(actions) = role_perms.get(&object.object_type) {
                if actions.contains(&action) {
                    return PermissionResult::Allowed;
                }
            }
        }
        
        // Check visibility permissions (view only)
        if action == ActionType::View {
            if let Some(visible_types) = self.visibility_rules.get(&user.primary_role) {
                if visible_types.contains(&object.object_type) {
                    return PermissionResult::Allowed;
                }
            }
        }
        
        // Check if escalation available
        if user.access_level >= AccessLevel::Extended {
            return PermissionResult::RequiresEscalation;
        }
        
        PermissionResult::Denied
    }
}

#[derive(Debug, PartialEq)]
pub enum PermissionResult {
    Allowed,
    Denied,
    RequiresEscalation,
}

/// Progressive Trust - earn more access through good behavior
pub struct TrustManager {
    /// User trust scores
    trust_scores: HashMap<u16, TrustScore>,
    
    /// Access escalation history
    escalation_log: Vec<EscalationEvent>,
}

#[derive(Debug, Clone)]
pub struct TrustScore {
    /// Base score (0-100)
    pub base_score: u8,
    
    /// Number of successful operations
    pub successful_ops: u32,
    
    /// Number of policy violations
    pub violations: u8,
    
    /// Last access time
    pub last_access: u64,
}

#[derive(Debug)]
pub struct EscalationEvent {
    pub user_id: u16,
    pub from_level: AccessLevel,
    pub to_level: AccessLevel,
    pub reason: String,
    pub timestamp: u64,
}

impl TrustManager {
    pub fn new() -> Self {
        Self {
            trust_scores: HashMap::new(),
            escalation_log: Vec::new(),
        }
    }
    
    /// Grant temporary escalation based on need
    pub fn request_escalation(
        &mut self,
        user: &mut FieldIdentity,
        reason: &str,
    ) -> bool {
        let trust = self.trust_scores.get(&user.user_id);
        
        // Check trust score
        let can_escalate = match trust {
            Some(score) if score.base_score > 70 => true,
            Some(score) if score.base_score > 50 && score.violations == 0 => true,
            _ => false,
        };
        
        if can_escalate {
            let old_level = user.access_level;
            user.access_level = match old_level {
                AccessLevel::Basic => AccessLevel::Standard,
                AccessLevel::Standard => AccessLevel::Extended,
                other => other,
            };
            
            self.escalation_log.push(EscalationEvent {
                user_id: user.user_id,
                from_level: old_level,
                to_level: user.access_level,
                reason: reason.to_string(),
                timestamp: current_timestamp(),
            });
            
            true
        } else {
            false
        }
    }
}

/// Practical IAM flow for field work
pub fn demo_field_iam() {
    println!("\n🔧 Practical Field IAM Demo\n");
    
    println!("Scenario: HVAC tech troubleshooting no-heat complaint");
    println!("────────────────────────────────────────────────────");
    
    println!("\n1️⃣ Tech arrives with Basic access:");
    println!("   ✅ Can see: HVAC vents, thermostats");
    println!("   ✅ Can see: Electrical panels (read-only)");
    println!("   ✅ Can see: Walls, doors (navigation)");
    println!("   ❌ Cannot see: Cameras, motion sensors");
    
    println!("\n2️⃣ Tech finds HVAC unit not getting power:");
    println!("   → Requests escalation: \"Need to check breaker\"");
    println!("   → Trust score: 85 (good history)");
    println!("   → Escalated to Standard access");
    
    println!("\n3️⃣ With Standard access:");
    println!("   ✅ Can now annotate electrical panel");
    println!("   ✅ Can flag circuit for electrician");
    println!("   ✅ Still cannot modify electrical");
    
    println!("\n4️⃣ Permission packet (13 bytes):");
    println!("   [UserID:2][ObjID:2][Action:1][X:2][Y:2][Z:2][Ctx:1][Time:1]");
    println!("   [0x0042][0x1234][View][1000][2000][1500][0x08][142]");
    
    println!("\nKey insights:");
    println!("  • Cross-system visibility by default");
    println!("  • Progressive trust through good behavior");
    println!("  • Emergency override for first responders");
    println!("  • All permissions fit in 13-byte packets");
}

fn current_timestamp() -> u64 {
    use std::time::{SystemTime, UNIX_EPOCH};
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap()
        .as_secs()
}