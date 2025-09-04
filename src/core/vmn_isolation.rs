use std::collections::{HashMap, HashSet};

/// Virtual Mesh Network (VMN) - Like VLANs but for mesh networks
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub struct VMN {
    pub id: u8,
    pub priority: Priority,
    pub service_type: ServiceType,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Priority {
    Critical = 0,  // Emergency services
    High = 1,      // Administrative
    Medium = 2,    // Educational
    Low = 3,       // Commercial
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ServiceType {
    Emergency,
    ArxOSCore,
    DistrictAdmin,
    StudentData,
    Educational,
    Facilities,
    Municipal,
    Commercial,
    Guest,
}

/// VMN Isolation Policy - Controls traffic between virtual networks
pub struct VMNIsolationPolicy {
    pub vmn_id: u8,
    pub service_type: ServiceType,
    pub allowed_destinations: HashSet<u8>,
    pub denied_sources: HashSet<u8>,
    pub inter_vmn_routing: bool,
    pub encryption_required: bool,
    pub bandwidth_guarantee_kbps: u32,
    pub bandwidth_max_kbps: u32,
}

/// District-level VMN management
pub struct DistrictVMNManager {
    pub district_id: String,
    pub allocated_range: (u8, u8),  // e.g., 0x20-0x2F for HCPS
    pub vmn_configs: HashMap<u8, VMNConfig>,
    pub isolation_matrix: IsolationMatrix,
    pub bandwidth_allocations: HashMap<u8, BandwidthAllocation>,
}

#[derive(Clone)]
pub struct VMNConfig {
    pub vmn_id: u8,
    pub name: String,
    pub vlan_type: ServiceType,
    pub encryption: EncryptionLevel,
    pub priority: Priority,
    pub allowed_devices: HashSet<DeviceType>,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub enum DeviceType {
    EmergencyResponder,
    SchoolAdministrator,
    Teacher,
    Student,
    Contractor,
    IoTSensor,
    Guest,
}

#[derive(Clone, Copy)]
pub enum EncryptionLevel {
    None,
    Basic,
    Strong,
    Military,
}

/// Isolation Matrix - Defines which VMNs can communicate
pub struct IsolationMatrix {
    //[source][destination] = allowed
    matrix: Vec<Vec<bool>>,
}

impl IsolationMatrix {
    pub fn new(size: usize) -> Self {
        Self {
            matrix: vec![vec![false; size]; size],
        }
    }

    pub fn allow(&mut self, source: u8, dest: u8) {
        self.matrix[source as usize][dest as usize] = true;
    }

    pub fn deny(&mut self, source: u8, dest: u8) {
        self.matrix[source as usize][dest as usize] = false;
    }

    pub fn is_allowed(&self, source: u8, dest: u8) -> bool {
        self.matrix[source as usize][dest as usize]
    }
}

/// Bandwidth allocation per VMN
pub struct BandwidthAllocation {
    pub vmn_id: u8,
    pub guaranteed_kbps: u32,
    pub maximum_kbps: u32,
    pub current_usage_kbps: u32,
    pub priority: Priority,
}

/// Dynamic VMN Assignment - Like 802.1X for mesh
pub struct DynamicVMNAssignment {
    pub device_mac: [u8; 6],
    pub device_type: DeviceType,
    pub authentication_result: AuthResult,
    pub location: MeshLocation,
    pub bilt_balance: u32,
}

pub enum AuthResult {
    Unauthenticated,
    BILTVerified(u32),  // BILT balance
    DistrictAuth(String),  // District ID
    EmergencyAuth,
    CommercialAuth(String),  // Company ID
}

pub struct MeshLocation {
    pub district_id: String,
    pub school_id: Option<String>,
    pub building_id: String,
    pub room_id: Option<String>,
}

impl DynamicVMNAssignment {
    pub fn assign_vmn(&self) -> u8 {
        match (&self.device_type, &self.authentication_result) {
            (DeviceType::EmergencyResponder, AuthResult::EmergencyAuth) => 0x00,
            (DeviceType::SchoolAdministrator, AuthResult::DistrictAuth(_)) => 0x20,
            (DeviceType::Teacher, AuthResult::DistrictAuth(_)) => 0x22,
            (DeviceType::Student, AuthResult::DistrictAuth(_)) => 0x21,
            (DeviceType::Contractor, AuthResult::BILTVerified(balance)) if *balance > 100 => 0x23,
            (DeviceType::IoTSensor, AuthResult::CommercialAuth(_)) => 0x26,
            _ => 0x25, // Guest network
        }
    }
}

/// VMN-aware packet structure
pub struct MeshPacket {
    pub preamble: [u8; 2],
    pub vmn_tag: VMNTag,
    pub source: [u8; 4],
    pub destination: [u8; 4],
    pub payload: Vec<u8>,
    pub checksum: u16,
}

/// VMN Tag structure (8 bits total)
#[derive(Debug, Clone, Copy)]
pub struct VMNTag {
    pub priority: u8,      // 2 bits
    pub service_id: u8,    // 3 bits  
    pub district_id: u8,   // 3 bits
}

impl VMNTag {
    pub fn new(priority: Priority, service: u8, district: u8) -> Self {
        Self {
            priority: priority as u8,
            service_id: service & 0x07,
            district_id: district & 0x07,
        }
    }

    pub fn to_byte(&self) -> u8 {
        (self.priority << 6) | (self.service_id << 3) | self.district_id
    }

    pub fn from_byte(byte: u8) -> Self {
        Self {
            priority: byte >> 6,
            service_id: (byte >> 3) & 0x07,
            district_id: byte & 0x07,
        }
    }
}

/// Mesh Spanning Tree Protocol - Prevent loops in mesh topology
pub struct MeshSpanningTree {
    pub root_node_id: [u8; 4],
    pub local_node_id: [u8; 4],
    pub port_states: HashMap<u8, PortState>,
    pub path_costs: HashMap<[u8; 4], u32>,
}

#[derive(Debug, Clone, Copy)]
pub enum PortState {
    Forwarding,
    Blocking,
    Learning,
    Disabled,
}

impl MeshSpanningTree {
    pub fn calculate_spanning_tree(&mut self) {
        // Identify root node (usually district HQ)
        self.identify_root();
        
        // Calculate path costs to root
        self.calculate_path_costs();
        
        // Block redundant paths
        self.block_redundant_paths();
        
        // Keep backup routes ready
        self.maintain_backup_routes();
    }

    fn identify_root(&mut self) {
        // Root selection based on priority and ID
    }

    fn calculate_path_costs(&mut self) {
        // Distance vector calculation
    }

    fn block_redundant_paths(&mut self) {
        // Block ports that create loops
    }

    fn maintain_backup_routes(&mut self) {
        // Keep alternate paths in learning state
    }
}

/// HCPS-specific VMN configuration
pub fn create_hcps_vmn_config() -> DistrictVMNManager {
    let mut manager = DistrictVMNManager {
        district_id: "HCPS".to_string(),
        allocated_range: (0x20, 0x2F),
        vmn_configs: HashMap::new(),
        isolation_matrix: IsolationMatrix::new(256),
        bandwidth_allocations: HashMap::new(),
    };

    // Configure default HCPS VMNs
    manager.vmn_configs.insert(0x20, VMNConfig {
        vmn_id: 0x20,
        name: "District Administration".to_string(),
        vlan_type: ServiceType::DistrictAdmin,
        encryption: EncryptionLevel::Strong,
        priority: Priority::High,
        allowed_devices: HashSet::from([
            DeviceType::SchoolAdministrator,
        ]),
    });

    manager.vmn_configs.insert(0x21, VMNConfig {
        vmn_id: 0x21,
        name: "Student Data (FERPA)".to_string(),
        vlan_type: ServiceType::StudentData,
        encryption: EncryptionLevel::Strong,
        priority: Priority::High,
        allowed_devices: HashSet::from([
            DeviceType::Teacher,
            DeviceType::SchoolAdministrator,
        ]),
    });

    manager.vmn_configs.insert(0x22, VMNConfig {
        vmn_id: 0x22,
        name: "Staff Communications".to_string(),
        vlan_type: ServiceType::Educational,
        encryption: EncryptionLevel::Basic,
        priority: Priority::Medium,
        allowed_devices: HashSet::from([
            DeviceType::Teacher,
            DeviceType::SchoolAdministrator,
        ]),
    });

    manager.vmn_configs.insert(0x23, VMNConfig {
        vmn_id: 0x23,
        name: "Facilities & ArxOS".to_string(),
        vlan_type: ServiceType::Facilities,
        encryption: EncryptionLevel::Basic,
        priority: Priority::Medium,
        allowed_devices: HashSet::from([
            DeviceType::Contractor,
            DeviceType::IoTSensor,
        ]),
    });

    // Set up isolation rules
    // Admin can talk to everything
    for dest in 0x20..=0x2F {
        manager.isolation_matrix.allow(0x20, dest);
    }
    
    // Student data is highly isolated
    manager.isolation_matrix.allow(0x21, 0x21); // Only to itself
    manager.isolation_matrix.allow(0x21, 0x20); // And to admin
    
    // Contractors only access facilities
    manager.isolation_matrix.allow(0x23, 0x23);
    manager.isolation_matrix.deny(0x23, 0x21); // No student data access

    manager
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_vmn_tag_encoding() {
        let tag = VMNTag::new(Priority::High, 0x04, 0x02);
        let byte = tag.to_byte();
        let decoded = VMNTag::from_byte(byte);
        
        assert_eq!(tag.priority, decoded.priority);
        assert_eq!(tag.service_id, decoded.service_id);
        assert_eq!(tag.district_id, decoded.district_id);
    }

    #[test]
    fn test_isolation_matrix() {
        let mut matrix = IsolationMatrix::new(256);
        matrix.allow(0x20, 0x21);
        matrix.deny(0x23, 0x21);
        
        assert!(matrix.is_allowed(0x20, 0x21));
        assert!(!matrix.is_allowed(0x23, 0x21));
    }

    #[test]
    fn test_dynamic_vmn_assignment() {
        let assignment = DynamicVMNAssignment {
            device_mac: [0xAA; 6],
            device_type: DeviceType::Contractor,
            authentication_result: AuthResult::BILTVerified(500),
            location: MeshLocation {
                district_id: "HCPS".to_string(),
                school_id: None,
                building_id: "BLDG001".to_string(),
                room_id: None,
            },
            bilt_balance: 500,
        };

        let vmn = assignment.assign_vmn();
        assert_eq!(vmn, 0x23); // Should get facilities VMN
    }
}