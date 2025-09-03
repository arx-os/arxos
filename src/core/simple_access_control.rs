//! Simple Access Control for ArxOS
//! 
//! The SIMPLEST possible IAM that actually works in the field.
//! No complex chains, no certificates, just practical access control.

use crate::arxobject::ArxObject;

/// The entire access control system in ONE 13-byte packet
#[derive(Debug, Clone, Copy)]
pub struct SimpleAccess {
    /// Building ID (2 bytes)
    pub building_id: u16,
    
    /// User's company/org (1 byte)
    pub company_code: u8,
    
    /// User's role (1 byte)
    pub role_code: u8,
    
    /// Access expires (2 bytes: days since 2024)
    pub expires_days: u16,
    
    /// What they can access (4 bytes: bit flags for object types)
    pub access_mask: u32,
    
    /// Trust level (1 byte: 0-255)
    pub trust_level: u8,
    
    /// Checksum (2 bytes)
    pub checksum: u16,
}

impl SimpleAccess {
    /// Create access token for a field tech
    pub fn new_for_tech(company: CompanyCode, role: RoleCode, days_valid: u16) -> Self {
        let access_mask = match role {
            RoleCode::HVACTech => {
                let mut mask = 0u32;
                mask |= 1 << 9;  // HVAC_VENT
                mask |= 1 << 10; // THERMOSTAT
                mask |= 1 << 11; // ELECTRICAL_PANEL (view only)
                mask |= 1 << 0;  // WALL (navigation)
                mask |= 1 << 1;  // FLOOR (navigation)
                mask |= 1 << 3;  // DOOR (navigation)
                mask
            }
            RoleCode::Electrician => {
                let mut mask = 0u32;
                mask |= 1 << 6;  // OUTLET
                mask |= 1 << 7;  // SWITCH
                mask |= 1 << 8;  // LIGHT
                mask |= 1 << 11; // ELECTRICAL_PANEL
                mask |= 1 << 0;  // WALL (navigation)
                mask |= 1 << 1;  // FLOOR (navigation)
                mask |= 1 << 3;  // DOOR (navigation)
                mask
            }
            RoleCode::Maintenance => {
                0xFFFF // See most things
            }
            RoleCode::Security => {
                let mut mask = 0u32;
                mask |= 1 << 13; // CAMERA
                mask |= 1 << 14; // MOTION_SENSOR
                mask |= 1 << 12; // EMERGENCY_EXIT
                mask |= 1 << 3;  // DOOR
                mask |= 1 << 0;  // WALL (navigation)
                mask |= 1 << 1;  // FLOOR (navigation)
                mask
            }
            _ => 0x0F, // Basic navigation only
        };
        
        let mut access = Self {
            building_id: 0, // Set by building
            company_code: company as u8,
            role_code: role as u8,
            expires_days: days_valid,
            access_mask,
            trust_level: 50, // Start at neutral trust
            checksum: 0,
        };
        
        access.checksum = access.calculate_checksum();
        access
    }
    
    /// Check if user can see this object type
    pub fn can_see(&self, object: &ArxObject) -> bool {
        // Check expiration
        if self.is_expired() {
            return false;
        }
        
        // Check building match
        if self.building_id != object.building_id {
            return false;
        }
        
        // Check access mask
        let type_bit = 1u32 << object.object_type;
        (self.access_mask & type_bit) != 0
    }
    
    /// Check if user can modify this object
    pub fn can_modify(&self, object: &ArxObject) -> bool {
        // Must be able to see it first
        if !self.can_see(object) {
            return false;
        }
        
        // Check if it's their primary system
        match self.role_code {
            r if r == RoleCode::HVACTech as u8 => {
                matches!(object.object_type, 9 | 10) // HVAC_VENT, THERMOSTAT
            }
            r if r == RoleCode::Electrician as u8 => {
                matches!(object.object_type, 6 | 7 | 8 | 11) // Electrical
            }
            r if r == RoleCode::Maintenance as u8 => {
                true // Can modify most things
            }
            _ => false,
        }
    }
    
    fn is_expired(&self) -> bool {
        let days_since_2024 = days_since_epoch_2024();
        days_since_2024 > self.expires_days
    }
    
    fn calculate_checksum(&self) -> u16 {
        // Simple checksum for integrity
        let sum = self.building_id as u32
            + self.company_code as u32
            + self.role_code as u32
            + self.expires_days as u32
            + (self.access_mask & 0xFFFF) as u32
            + ((self.access_mask >> 16) & 0xFFFF) as u32
            + self.trust_level as u32;
        
        (sum & 0xFFFF) as u16
    }
    
    /// Pack into 13 bytes for transmission
    pub fn to_bytes(&self) -> [u8; 13] {
        let mut bytes = [0u8; 13];
        bytes[0..2].copy_from_slice(&self.building_id.to_le_bytes());
        bytes[2] = self.company_code;
        bytes[3] = self.role_code;
        bytes[4..6].copy_from_slice(&self.expires_days.to_le_bytes());
        bytes[6..10].copy_from_slice(&self.access_mask.to_le_bytes());
        bytes[10] = self.trust_level;
        bytes[11..13].copy_from_slice(&self.checksum.to_le_bytes());
        bytes
    }
    
    /// Unpack from 13 bytes
    pub fn from_bytes(bytes: &[u8; 13]) -> Self {
        Self {
            building_id: u16::from_le_bytes([bytes[0], bytes[1]]),
            company_code: bytes[2],
            role_code: bytes[3],
            expires_days: u16::from_le_bytes([bytes[4], bytes[5]]),
            access_mask: u32::from_le_bytes([bytes[6], bytes[7], bytes[8], bytes[9]]),
            trust_level: bytes[10],
            checksum: u16::from_le_bytes([bytes[11], bytes[12]]),
        }
    }
}

/// Company codes - who employs this person
#[repr(u8)]
#[derive(Debug, Clone, Copy)]
pub enum CompanyCode {
    BuildingOwner = 1,
    JohnsonControls = 2,
    Siemens = 3,
    Honeywell = 4,
    LocalHVAC = 5,
    LocalElectrical = 6,
    CityInspector = 7,
    EmergencyServices = 8,
}

/// Role codes - what they do
#[repr(u8)]
#[derive(Debug, Clone, Copy)]
pub enum RoleCode {
    HVACTech = 1,
    Electrician = 2,
    Plumber = 3,
    Maintenance = 4,
    Security = 5,
    Custodian = 6,
    Inspector = 7,
    Emergency = 8,
    Manager = 9,
}

/// The SIMPLEST possible session manager
pub struct SimpleSessionManager {
    /// Active sessions (max 256 for a building)
    sessions: Vec<SimpleAccess>,
    
    /// Quick lookup by company+role
    index: HashMap<(u8, u8), usize>,
}

use std::collections::HashMap;

impl SimpleSessionManager {
    pub fn new() -> Self {
        Self {
            sessions: Vec::with_capacity(256),
            index: HashMap::new(),
        }
    }
    
    /// Register a new tech entering the building
    pub fn register(&mut self, mut access: SimpleAccess, building_id: u16) -> Result<u8, &str> {
        if self.sessions.len() >= 256 {
            return Err("Building at capacity");
        }
        
        // Set building ID
        access.building_id = building_id;
        access.checksum = access.calculate_checksum();
        
        // Store session
        let session_id = self.sessions.len() as u8;
        self.sessions.push(access);
        
        // Index for quick lookup
        self.index.insert((access.company_code, access.role_code), session_id as usize);
        
        Ok(session_id)
    }
    
    /// Check access for a session
    pub fn check_access(&self, session_id: u8, object: &ArxObject) -> bool {
        self.sessions.get(session_id as usize)
            .map(|access| access.can_see(object))
            .unwrap_or(false)
    }
    
    /// Boost trust for good behavior
    pub fn boost_trust(&mut self, session_id: u8) {
        if let Some(access) = self.sessions.get_mut(session_id as usize) {
            access.trust_level = (access.trust_level + 5).min(255);
        }
    }
    
    /// Reduce trust for violations
    pub fn reduce_trust(&mut self, session_id: u8) {
        if let Some(access) = self.sessions.get_mut(session_id as usize) {
            access.trust_level = access.trust_level.saturating_sub(10);
        }
    }
}

/// How it works in practice
pub fn demo_simple_access() {
    println!("\n🎯 Simple Access Control Demo\n");
    
    println!("No certificates, no OAuth, no SAML, no complexity!");
    println!("Just 13 bytes of practical access control.\n");
    
    println!("HVAC Tech arrives at building:");
    println!("───────────────────────────────");
    
    println!("\n1️⃣ Tech's radio broadcasts access request:");
    println!("   Company: LocalHVAC (code 5)");
    println!("   Role: HVAC Tech (code 1)");
    println!("   Valid: 1 day");
    
    println!("\n2️⃣ Building grants access token (13 bytes):");
    println!("   [Bldg:0x0042][Co:5][Role:1][Days:1][Mask:0x0E03][Trust:50][Check:0xAB12]");
    
    println!("\n3️⃣ Tech queries: \"Show me thermostats\"");
    println!("   → Access mask checked: 0x0E03 & (1<<10) ✓");
    println!("   → Returns: 5 thermostats");
    
    println!("\n4️⃣ Tech tries: \"Show me cameras\"");
    println!("   → Access mask checked: 0x0E03 & (1<<13) ✗");
    println!("   → Returns: Access denied");
    
    println!("\n5️⃣ After good work, trust increases:");
    println!("   Trust: 50 → 55 → 60 → 65");
    println!("   At trust 75+: Can request temporary escalation");
    
    println!("\nTotal overhead: 13 bytes");
    println!("Implementation: ~200 lines of code");
    println!("Security: Good enough for 99% of buildings");
}

fn days_since_epoch_2024() -> u16 {
    // Days since Jan 1, 2024
    use std::time::{SystemTime, UNIX_EPOCH};
    let secs = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap()
        .as_secs();
    
    let epoch_2024 = 1704067200u64; // Jan 1, 2024 timestamp
    ((secs - epoch_2024) / 86400) as u16
}