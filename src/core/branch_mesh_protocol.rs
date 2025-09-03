//! Branch Mesh Protocol - How branches work over 900MHz mesh
//! 
//! Contractors work in isolated branches transmitted as ArxObjects.
//! All changes are proposed, not directly applied.

use crate::arxobject::{ArxObject, object_types};
use crate::building_repository::{BuildingBranch, BuildingChange, Severity};
use crate::simple_access_control::SimpleAccess;

/// Branch identifier that fits in ArxObject
#[derive(Debug, Clone, Copy)]
pub struct BranchID {
    /// Building (2 bytes)
    pub building_id: u16,
    
    /// Branch number (2 bytes) 
    pub branch_num: u16,
    
    /// Owner's session ID (1 byte)
    pub session_id: u8,
    
    /// Branch type (1 byte)
    pub branch_type: BranchType,
    
    /// Expires in hours (1 byte)
    pub expires_hours: u8,
}

#[repr(u8)]
#[derive(Debug, Clone, Copy)]
pub enum BranchType {
    Main = 0,           // Production branch
    Contractor = 1,     // Temporary contractor branch
    Inspector = 2,      // Read-only inspection branch
    Emergency = 3,      // Emergency override branch
    Maintenance = 4,    // Scheduled maintenance branch
}

impl BranchID {
    /// Encode branch ID into ArxObject for mesh transmission
    pub fn to_arxobject(&self) -> ArxObject {
        ArxObject {
            building_id: self.building_id,
            object_type: 0xFD, // Special type for branch metadata
            x: self.branch_num,
            y: u16::from_le_bytes([self.session_id, self.branch_type as u8]),
            z: self.expires_hours as u16,
            properties: [0; 4], // Reserved for future use
        }
    }
    
    /// Decode from ArxObject
    pub fn from_arxobject(obj: &ArxObject) -> Option<Self> {
        if obj.object_type != 0xFD {
            return None;
        }
        
        Some(Self {
            building_id: obj.building_id,
            branch_num: obj.x,
            session_id: (obj.y & 0xFF) as u8,
            branch_type: unsafe { std::mem::transmute((obj.y >> 8) as u8) },
            expires_hours: obj.z as u8,
        })
    }
}

/// Change proposal that fits in ArxObject
#[derive(Debug, Clone, Copy)]
pub struct ChangeProposal {
    /// Object being changed
    pub object_id: u16,
    
    /// Type of change
    pub change_type: ChangeType,
    
    /// New value (interpretation depends on change_type)
    pub new_value: [u8; 4],
    
    /// Reason code
    pub reason_code: ReasonCode,
    
    /// Severity if annotation
    pub severity: u8,
}

#[repr(u8)]
#[derive(Debug, Clone, Copy)]
pub enum ChangeType {
    Add = 1,
    Modify = 2,
    Remove = 3,
    Annotate = 4,
    Replace = 5,
    Inspect = 6,
}

#[repr(u8)]
#[derive(Debug, Clone, Copy)]
pub enum ReasonCode {
    Repair = 1,
    Replace = 2,
    Maintenance = 3,
    Inspection = 4,
    Upgrade = 5,
    Safety = 6,
    Efficiency = 7,
    Compliance = 8,
    Emergency = 9,
}

impl ChangeProposal {
    /// Encode as ArxObject for mesh transmission
    pub fn to_arxobject(&self, building_id: u16) -> ArxObject {
        ArxObject {
            building_id,
            object_type: 0xFC, // Special type for change proposals
            x: self.object_id,
            y: u16::from_le_bytes([self.change_type as u8, self.reason_code as u8]),
            z: self.severity as u16,
            properties: self.new_value,
        }
    }
    
    /// Decode from ArxObject
    pub fn from_arxobject(obj: &ArxObject) -> Option<Self> {
        if obj.object_type != 0xFC {
            return None;
        }
        
        Some(Self {
            object_id: obj.x,
            change_type: unsafe { std::mem::transmute((obj.y & 0xFF) as u8) },
            new_value: obj.properties,
            reason_code: unsafe { std::mem::transmute((obj.y >> 8) as u8) },
            severity: obj.z as u8,
        })
    }
}

/// Branch operations over mesh network
pub struct BranchMeshOps {
    /// Current branch context
    pub branch_id: BranchID,
    
    /// Cached branch objects
    pub branch_objects: Vec<ArxObject>,
    
    /// Pending changes
    pub pending_changes: Vec<ChangeProposal>,
}

impl BranchMeshOps {
    /// Query objects in branch context
    pub fn query_branch(&self, query: &[u8; 13]) -> Vec<ArxObject> {
        // Parse query
        let query_obj = ArxObject::from_bytes(query);
        
        // Filter objects based on branch view
        self.branch_objects.iter()
            .filter(|obj| {
                // Check if object matches query criteria
                obj.object_type == query_obj.object_type
                    || obj.x == query_obj.x
                    || obj.y == query_obj.y
            })
            .cloned()
            .collect()
    }
    
    /// Propose a change in branch
    pub fn propose_change(&mut self, change: ChangeProposal) -> Result<(), &'static str> {
        // Check if branch is main
        if self.branch_id.branch_type as u8 == BranchType::Main as u8 {
            return Err("Cannot modify main branch directly");
        }
        
        // Check if branch is expired
        if self.branch_id.expires_hours == 0 {
            return Err("Branch expired");
        }
        
        // Add to pending changes
        self.pending_changes.push(change);
        
        // Apply locally to branch view
        self.apply_local_change(&change);
        
        Ok(())
    }
    
    /// Apply change locally (in branch only)
    fn apply_local_change(&mut self, change: &ChangeProposal) {
        match change.change_type {
            ChangeType::Modify => {
                // Find and modify object
                for obj in &mut self.branch_objects {
                    if obj.building_id == change.object_id {
                        obj.properties = change.new_value;
                        break;
                    }
                }
            }
            ChangeType::Remove => {
                // Remove from local view
                self.branch_objects.retain(|obj| obj.building_id != change.object_id);
            }
            ChangeType::Add => {
                // Add placeholder object
                let new_obj = ArxObject {
                    building_id: change.object_id,
                    object_type: change.new_value[0],
                    x: u16::from_le_bytes([change.new_value[1], change.new_value[2]]),
                    y: 0,
                    z: 0,
                    properties: [0; 4],
                };
                self.branch_objects.push(new_obj);
            }
            _ => {}
        }
    }
    
    /// Create merge request packet
    pub fn create_merge_request(&self) -> Vec<ArxObject> {
        let mut packets = Vec::new();
        
        // First packet: branch metadata
        packets.push(self.branch_id.to_arxobject());
        
        // Following packets: changes
        for change in &self.pending_changes {
            packets.push(change.to_arxobject(self.branch_id.building_id));
        }
        
        packets
    }
}

/// How contractors interact with branches
pub fn demo_contractor_branch_interaction() {
    println!("\n📡 Branch Over Mesh Demo\n");
    
    println!("HVAC Tech's radio interaction:");
    println!("═══════════════════════════════\n");
    
    println!("1️⃣ Tech connects with branch access:");
    let branch = BranchID {
        building_id: 0x0042,
        branch_num: 17,
        session_id: 42,
        branch_type: BranchType::Contractor,
        expires_hours: 8,
    };
    
    let branch_packet = branch.to_arxobject();
    println!("   Branch packet: {:02X?}", branch_packet.to_bytes());
    println!("   → Building: 0x{:04X}", branch.building_id);
    println!("   → Branch: #{}", branch.branch_num);
    println!("   → Type: Contractor");
    println!("   → Expires: {} hours", branch.expires_hours);
    println!();
    
    println!("2️⃣ Tech queries: 'Show thermostats'");
    println!("   Mesh returns objects FROM BRANCH VIEW");
    println!("   (Not production data!)");
    println!();
    
    println!("3️⃣ Tech proposes change:");
    let change = ChangeProposal {
        object_id: 0x0203, // Thermostat in room 203
        change_type: ChangeType::Replace,
        new_value: [72, 0, 0, 0], // Set to 72°F
        reason_code: ReasonCode::Repair,
        severity: 2, // Warning level
    };
    
    let change_packet = change.to_arxobject(0x0042);
    println!("   Change packet: {:02X?}", change_packet.to_bytes());
    println!("   → Object: Thermostat-203");
    println!("   → Action: Replace");
    println!("   → Reason: Repair");
    println!();
    
    println!("4️⃣ Changes accumulate in branch:");
    println!("   Branch changes: 3 pending");
    println!("   Main branch: Unchanged");
    println!("   Other contractors: Don't see these changes");
    println!();
    
    println!("5️⃣ Tech submits merge request:");
    println!("   13-byte packets × 4 = 52 bytes total");
    println!("   [Branch ID][Change 1][Change 2][Change 3]");
    println!();
    
    println!("Key insight:");
    println!("   All branch operations fit in 13-byte ArxObjects!");
    println!("   Git-like version control over 900MHz mesh!");
}

/// Show isolation between branches
pub fn demo_branch_isolation() {
    println!("\n🔐 Branch Isolation Demo\n");
    
    println!("Three contractors working simultaneously:");
    println!("══════════════════════════════════════════\n");
    
    println!("Building Main Branch (Truth):");
    println!("  • 500 ArxObjects");
    println!("  • All equipment in working state");
    println!("  • Last updated: Yesterday 5pm");
    println!();
    
    println!("HVAC Tech (Branch #17):");
    println!("  • Sees: 500 objects (copy of main)");
    println!("  • Changes: Thermostat-203 → needs replacement");
    println!("  • Others see: No changes (isolated)");
    println!();
    
    println!("Electrician (Branch #18):");
    println!("  • Sees: 500 objects (copy of main)");
    println!("  • Changes: Panel-2 → add 20A breaker");
    println!("  • Others see: No changes (isolated)");
    println!();
    
    println!("Inspector (Branch #19 - Read Only):");
    println!("  • Sees: 500 objects (copy of main)");
    println!("  • Changes: ❌ Cannot modify (inspection only)");
    println!("  • Can annotate: Fire extinguisher needs service");
    println!();
    
    println!("After all submit merge requests:");
    println!("┌─────────────────────────────────────────┐");
    println!("│ Pending Merge Requests:                │");
    println!("│                                         │");
    println!("│ MR-17: HVAC - Replace thermostat       │");
    println!("│ MR-18: Electrical - Add breaker        │");
    println!("│ MR-19: Inspection - Service notes      │");
    println!("│                                         │");
    println!("│ Manager reviews each independently     │");
    println!("│ Approves/merges in order               │");
    println!("│ Conflicts resolved by human            │");
    println!("└─────────────────────────────────────────┘");
}

/// Emergency branch override
pub fn demo_emergency_override() {
    println!("\n🚨 Emergency Branch Override\n");
    
    println!("Fire alarm triggered!");
    println!("══════════════════════\n");
    
    println!("Normal branches: Read-only or limited write");
    println!("Emergency branch: Full write to main!");
    println!();
    
    let emergency_branch = BranchID {
        building_id: 0x0042,
        branch_num: 911,
        session_id: 0xFF,
        branch_type: BranchType::Emergency,
        expires_hours: 1, // Auto-expires quickly
    };
    
    println!("Emergency responder gets:");
    println!("  • Branch type: EMERGENCY");
    println!("  • Permissions: Override everything");
    println!("  • Changes: Applied immediately to main");
    println!("  • Audit: Full log maintained");
    println!();
    
    println!("Actions taken:");
    println!("  1. Unlock all doors → Immediate");
    println!("  2. Kill HVAC zones → Immediate");
    println!("  3. Activate emergency lights → Immediate");
    println!();
    
    println!("After emergency:");
    println!("  • Branch expires");
    println!("  • Full audit log available");
    println!("  • Can review all changes");
    println!("  • Can rollback if needed");
}