//! Virtual Building Space (VBS) - Isolated workspace layers over mesh network
//! 
//! Inspired by Hypori's isolation model but adapted for RF mesh networks.
//! Each VBS is a logical view of the building with role-based filtering.

use crate::arxobject::ArxObject;
use crate::mesh_network::MeshNode;
use crate::crypto::{Ed25519PublicKey, Ed25519Signature};
use std::collections::HashMap;

/// Virtual Building Space - an isolated view of building data
#[derive(Debug, Clone)]
pub struct VirtualBuildingSpace {
    /// Unique identifier for this VBS
    pub space_id: u16,
    
    /// Owner/tenant of this space (e.g., maintenance contractor, security firm)
    pub owner_id: u32,
    
    /// Access control list - who can enter this VBS
    pub authorized_users: Vec<Ed25519PublicKey>,
    
    /// Object visibility filter - which ArxObjects are visible
    pub visibility_mask: ObjectVisibilityMask,
    
    /// Encrypted overlay data - additional info only visible in this VBS
    pub overlay_objects: HashMap<u16, EncryptedOverlay>,
    
    /// Temporal access - when this VBS is active
    pub access_schedule: AccessSchedule,
}

/// Controls which objects are visible in a VBS
#[derive(Debug, Clone)]
pub struct ObjectVisibilityMask {
    /// Object types visible (e.g., only HVAC for HVAC contractor)
    pub allowed_types: Vec<u8>,
    
    /// Spatial bounds (e.g., only Floor 2 for floor-specific contractor)
    pub spatial_filter: Option<SpatialBounds>,
    
    /// Property filters (e.g., only objects needing maintenance)
    pub property_filters: Vec<PropertyFilter>,
}

/// Encrypted overlay data for a specific object
#[derive(Debug, Clone)]
pub struct EncryptedOverlay {
    /// Encrypted 13-byte ArxObject with additional properties
    pub encrypted_data: [u8; 13],
    
    /// Signature proving this overlay is authorized
    pub signature: Ed25519Signature,
    
    /// Expiration time for this overlay
    pub expires_at: u64,
}

/// Time-based access control
#[derive(Debug, Clone)]
pub struct AccessSchedule {
    /// Working hours (e.g., 8am-6pm M-F for contractors)
    pub active_hours: Vec<TimeWindow>,
    
    /// Expiration date for entire VBS
    pub expires_on: u64,
    
    /// Emergency override capability
    pub emergency_access: bool,
}

/// Spatial boundaries for a VBS
#[derive(Debug, Clone)]
pub struct SpatialBounds {
    pub min_x: u16,
    pub max_x: u16,
    pub min_y: u16,
    pub max_y: u16,
    pub min_z: u16,
    pub max_z: u16,
}

/// Property-based filtering
#[derive(Debug, Clone)]
pub struct PropertyFilter {
    pub property_index: usize,
    pub min_value: u8,
    pub max_value: u8,
}

/// Time window for access
#[derive(Debug, Clone)]
pub struct TimeWindow {
    pub day_of_week: u8, // 0=Sunday, 6=Saturday
    pub start_hour: u8,
    pub start_minute: u8,
    pub end_hour: u8,
    pub end_minute: u8,
}

impl VirtualBuildingSpace {
    /// Create a new VBS for a specific role
    pub fn new_for_role(role: BuildingRole, owner_id: u32) -> Self {
        let visibility_mask = match role {
            BuildingRole::HVACContractor => ObjectVisibilityMask {
                allowed_types: vec![
                    crate::arxobject::object_types::HVAC_VENT,
                    crate::arxobject::object_types::THERMOSTAT,
                ],
                spatial_filter: None,
                property_filters: vec![],
            },
            BuildingRole::ElectricalContractor => ObjectVisibilityMask {
                allowed_types: vec![
                    crate::arxobject::object_types::OUTLET,
                    crate::arxobject::object_types::SWITCH,
                    crate::arxobject::object_types::ELECTRICAL_PANEL,
                    crate::arxobject::object_types::LIGHT,
                ],
                spatial_filter: None,
                property_filters: vec![],
            },
            BuildingRole::SecurityTeam => ObjectVisibilityMask {
                allowed_types: vec![
                    crate::arxobject::object_types::CAMERA,
                    crate::arxobject::object_types::MOTION_SENSOR,
                    crate::arxobject::object_types::DOOR,
                    crate::arxobject::object_types::EMERGENCY_EXIT,
                ],
                spatial_filter: None,
                property_filters: vec![],
            },
            BuildingRole::MaintenanceStaff => ObjectVisibilityMask {
                allowed_types: vec![], // See everything
                spatial_filter: None,
                property_filters: vec![
                    PropertyFilter {
                        property_index: 0, // Maintenance urgency
                        min_value: 128,    // Only high-priority items
                        max_value: 255,
                    },
                ],
            },
            BuildingRole::Custodial => ObjectVisibilityMask {
                allowed_types: vec![
                    crate::arxobject::object_types::FLOOR,
                    crate::arxobject::object_types::DOOR,
                ],
                spatial_filter: None,
                property_filters: vec![],
            },
        };
        
        Self {
            space_id: (role as u16) << 8 | (owner_id as u16 & 0xFF),
            owner_id,
            authorized_users: vec![],
            visibility_mask,
            overlay_objects: HashMap::new(),
            access_schedule: AccessSchedule {
                active_hours: vec![
                    TimeWindow {
                        day_of_week: 1, // Monday
                        start_hour: 8,
                        start_minute: 0,
                        end_hour: 18,
                        end_minute: 0,
                    },
                    // ... Tuesday through Friday
                ],
                expires_on: u64::MAX, // No expiration by default
                emergency_access: false,
            },
        }
    }
    
    /// Filter ArxObjects based on VBS visibility rules
    pub fn filter_objects(&self, objects: &[ArxObject]) -> Vec<ArxObject> {
        objects.iter()
            .filter(|obj| self.is_visible(obj))
            .cloned()
            .collect()
    }
    
    /// Check if an object is visible in this VBS
    fn is_visible(&self, obj: &ArxObject) -> bool {
        // Check type filter
        if !self.visibility_mask.allowed_types.is_empty() 
            && !self.visibility_mask.allowed_types.contains(&obj.object_type) {
            return false;
        }
        
        // Check spatial bounds
        if let Some(ref bounds) = self.visibility_mask.spatial_filter {
            if obj.x < bounds.min_x || obj.x > bounds.max_x
                || obj.y < bounds.min_y || obj.y > bounds.max_y
                || obj.z < bounds.min_z || obj.z > bounds.max_z {
                return false;
            }
        }
        
        // Check property filters
        for filter in &self.visibility_mask.property_filters {
            let value = obj.properties[filter.property_index];
            if value < filter.min_value || value > filter.max_value {
                return false;
            }
        }
        
        true
    }
    
    /// Apply encrypted overlays to visible objects
    pub fn apply_overlays(&self, objects: &mut [ArxObject]) {
        for obj in objects {
            if let Some(overlay) = self.overlay_objects.get(&obj.building_id) {
                // In real implementation, decrypt and merge overlay data
                // For now, just mark that overlay exists
                obj.properties[3] |= 0x80; // Set high bit to indicate overlay
            }
        }
    }
}

/// Predefined building roles
#[repr(u8)]
#[derive(Debug, Clone, Copy)]
pub enum BuildingRole {
    HVACContractor = 1,
    ElectricalContractor = 2,
    SecurityTeam = 3,
    MaintenanceStaff = 4,
    Custodial = 5,
}

/// VBS Manager - handles multiple virtual spaces over the mesh
pub struct VBSManager {
    /// All active virtual building spaces
    spaces: HashMap<u16, VirtualBuildingSpace>,
    
    /// User to VBS mappings
    user_spaces: HashMap<Ed25519PublicKey, Vec<u16>>,
    
    /// Mesh node for communication
    mesh_node: MeshNode,
}

impl VBSManager {
    pub fn new(mesh_node: MeshNode) -> Self {
        Self {
            spaces: HashMap::new(),
            user_spaces: HashMap::new(),
            mesh_node,
        }
    }
    
    /// Create a new VBS for a contractor/service provider
    pub fn create_space(&mut self, role: BuildingRole, owner_id: u32) -> u16 {
        let vbs = VirtualBuildingSpace::new_for_role(role, owner_id);
        let space_id = vbs.space_id;
        self.spaces.insert(space_id, vbs);
        space_id
    }
    
    /// Query objects visible to a specific user
    pub fn query_for_user(
        &self, 
        user_key: &Ed25519PublicKey,
        all_objects: &[ArxObject],
    ) -> Vec<ArxObject> {
        // Get user's VBS spaces
        let user_spaces = self.user_spaces.get(user_key)
            .map(|s| s.as_slice())
            .unwrap_or(&[]);
        
        // Combine visibility from all user's spaces
        let mut visible_objects = Vec::new();
        for space_id in user_spaces {
            if let Some(vbs) = self.spaces.get(space_id) {
                let filtered = vbs.filter_objects(all_objects);
                visible_objects.extend(filtered);
            }
        }
        
        // Deduplicate
        visible_objects.sort_by_key(|o| (o.building_id, o.x, o.y, o.z));
        visible_objects.dedup();
        
        visible_objects
    }
}

/// Example: HVAC contractor queries building
pub fn demo_vbs_isolation() {
    println!("\n🏢 Virtual Building Space Demo\n");
    
    println!("Scenario: HVAC contractor accessing building");
    println!("─────────────────────────────────────────");
    
    println!("\n1️⃣ Building has 500 ArxObjects total");
    println!("   • 200 walls/floors");
    println!("   • 150 electrical components");
    println!("   • 50 HVAC components");
    println!("   • 100 other objects");
    
    println!("\n2️⃣ HVAC Contractor's VBS filters to:");
    println!("   • ✅ 50 HVAC components visible");
    println!("   • ❌ 450 other objects hidden");
    
    println!("\n3️⃣ Data transmitted over mesh:");
    println!("   • Only 50 × 13 bytes = 650 bytes");
    println!("   • Instead of 500 × 13 = 6,500 bytes");
    println!("   • 90% bandwidth saved!");
    
    println!("\n4️⃣ Security benefits:");
    println!("   • Contractor never sees electrical layout");
    println!("   • No access to security camera positions");
    println!("   • Can't map full building structure");
}