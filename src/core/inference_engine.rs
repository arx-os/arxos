//! Inference Engine for Progressive ArxObject Details
//! 
//! This module implements the "consciousness" that allows ArxObjects to
//! understand their context and automatically generate implied properties.
//! Like how a LEGO brick "knows" it can connect to others, each object
//! understands its role in the building's nervous system.

use crate::arxobject::{ArxObject, object_types};
use crate::progressive_detail::DetailTree;
use std::collections::HashMap;

/// The Inference Engine that gives ArxObjects consciousness
pub struct InferenceEngine {
    /// Knowledge base of object type implications
    type_knowledge: HashMap<u8, ObjectKnowledge>,
    
    /// Spatial reasoning for automatic connections
    spatial_index: SpatialIndex,
    
    /// System topology understanding
    topology_map: TopologyMap,
    
    /// Building codes and requirements
    code_requirements: CodeRequirements,
}

/// Knowledge about what each object type implies
#[derive(Debug, Clone)]
pub struct ObjectKnowledge {
    pub category: SystemCategory,
    pub typical_specs: TypicalSpecs,
    pub required_connections: Vec<ConnectionType>,
    pub implied_systems: Vec<SystemType>,
    pub maintenance_schedule: MaintenanceSchedule,
}

/// Categories of building systems
#[derive(Debug, Clone, PartialEq)]
pub enum SystemCategory {
    Electrical,
    HVAC,
    Plumbing,
    Lighting,
    Security,
    Fire,
    Data,
    Structural,
}

/// Types of connections objects can have
#[derive(Debug, Clone)]
pub enum ConnectionType {
    ElectricalCircuit(ElectricalSpec),
    DataNetwork(NetworkSpec),
    HVACDuct(AirflowSpec),
    PlumbingPipe(FluidSpec),
    ControlWire(ControlSpec),
    Mechanical(MountingSpec),
}

/// Electrical specifications that are implied
#[derive(Debug, Clone)]
pub struct ElectricalSpec {
    pub voltage: u16,        // 120V, 208V, 277V, 480V
    pub amperage: u16,       // Circuit amperage
    pub phase: u8,          // 1 or 3 phase
    pub wire_gauge: u8,     // AWG size
}

/// Typical specifications for object types
#[derive(Debug, Clone)]
pub struct TypicalSpecs {
    pub power_consumption: Option<u16>,  // Watts
    pub heat_output: Option<u16>,        // BTU/hr
    pub airflow: Option<u16>,            // CFM
    pub water_flow: Option<u16>,         // GPM
    pub data_bandwidth: Option<u32>,     // Mbps
    pub weight: Option<u16>,             // Pounds
}

/// System types that objects participate in
#[derive(Debug, Clone, PartialEq)]
pub enum SystemType {
    PowerDistribution,
    LightingControl,
    HVACControl,
    FireAlarm,
    SecurityMonitoring,
    DataCommunication,
    EmergencyPower,
    BuildingAutomation,
}

/// Maintenance requirements
#[derive(Debug, Clone)]
pub struct MaintenanceSchedule {
    pub inspection_days: u32,
    pub replacement_days: u32,
    pub cleaning_days: u32,
    pub testing_days: u32,
}

/// Spatial index for finding nearby objects
pub struct SpatialIndex {
    grid: HashMap<(u16, u16, u16), Vec<ArxObject>>,
    resolution: u16, // Grid cell size in mm
}

/// Building topology understanding
pub struct TopologyMap {
    circuits_to_panels: HashMap<u16, u16>,
    panels_to_transformers: HashMap<u16, u16>,
    zones_to_systems: HashMap<u16, Vec<SystemType>>,
}

/// Building code requirements
pub struct CodeRequirements {
    nec_2020: HashMap<u8, Vec<CodeRule>>,
    ashrae_90_1: HashMap<u8, Vec<CodeRule>>,
    nfpa_72: HashMap<u8, Vec<CodeRule>>,
}

#[derive(Debug, Clone)]
pub struct CodeRule {
    pub rule_id: String,
    pub description: String,
    pub requirement: String,
}

/// Network specifications
#[derive(Debug, Clone)]
pub struct NetworkSpec {
    pub protocol: String,
    pub bandwidth: u32,
    pub vlan: Option<u16>,
}

/// Airflow specifications
#[derive(Debug, Clone)]
pub struct AirflowSpec {
    pub cfm: u16,
    pub static_pressure: f32,
}

/// Fluid specifications
#[derive(Debug, Clone)]
pub struct FluidSpec {
    pub gpm: u16,
    pub pressure_psi: u16,
}

/// Control specifications
#[derive(Debug, Clone)]
pub struct ControlSpec {
    pub protocol: String,
    pub voltage: u8,
}

/// Mounting specifications
#[derive(Debug, Clone)]
pub struct MountingSpec {
    pub mount_type: String,
    pub weight_capacity: u16,
}

impl InferenceEngine {
    /// Create a new inference engine with building knowledge
    pub fn new() -> Self {
        let mut engine = Self {
            type_knowledge: HashMap::new(),
            spatial_index: SpatialIndex::new(1000), // 1 meter grid
            topology_map: TopologyMap::new(),
            code_requirements: CodeRequirements::new(),
        };
        
        // Initialize knowledge base
        engine.initialize_knowledge();
        engine
    }
    
    /// Initialize the knowledge base with object type implications
    fn initialize_knowledge(&mut self) {
        // Light fixture knowledge
        self.type_knowledge.insert(object_types::LIGHT, ObjectKnowledge {
            category: SystemCategory::Lighting,
            typical_specs: TypicalSpecs {
                power_consumption: Some(47),  // 47W LED typical
                heat_output: Some(160),       // ~160 BTU/hr
                airflow: None,
                water_flow: None,
                data_bandwidth: Some(10),     // For smart lights
                weight: Some(3),              // 3 lbs typical
            },
            required_connections: vec![
                ConnectionType::ElectricalCircuit(ElectricalSpec {
                    voltage: 120,
                    amperage: 15,
                    phase: 1,
                    wire_gauge: 14,
                }),
                ConnectionType::ControlWire(ControlSpec {
                    protocol: "0-10V".to_string(),
                    voltage: 10,
                }),
            ],
            implied_systems: vec![
                SystemType::PowerDistribution,
                SystemType::LightingControl,
                SystemType::EmergencyPower,
            ],
            maintenance_schedule: MaintenanceSchedule {
                inspection_days: 365,
                replacement_days: 3650,  // 10 years
                cleaning_days: 180,
                testing_days: 30,
            },
        });
        
        // Outlet knowledge
        self.type_knowledge.insert(object_types::OUTLET, ObjectKnowledge {
            category: SystemCategory::Electrical,
            typical_specs: TypicalSpecs {
                power_consumption: None,  // Depends on load
                heat_output: None,
                airflow: None,
                water_flow: None,
                data_bandwidth: None,
                weight: Some(1),
            },
            required_connections: vec![
                ConnectionType::ElectricalCircuit(ElectricalSpec {
                    voltage: 120,
                    amperage: 20,
                    phase: 1,
                    wire_gauge: 12,
                }),
            ],
            implied_systems: vec![
                SystemType::PowerDistribution,
            ],
            maintenance_schedule: MaintenanceSchedule {
                inspection_days: 365,
                replacement_days: 7300,  // 20 years
                cleaning_days: 0,
                testing_days: 365,
            },
        });
        
        // HVAC Vent knowledge
        self.type_knowledge.insert(object_types::HVAC_VENT, ObjectKnowledge {
            category: SystemCategory::HVAC,
            typical_specs: TypicalSpecs {
                power_consumption: None,
                heat_output: None,
                airflow: Some(400),  // 400 CFM typical
                water_flow: None,
                data_bandwidth: None,
                weight: Some(5),
            },
            required_connections: vec![
                ConnectionType::HVACDuct(AirflowSpec {
                    cfm: 400,
                    static_pressure: 0.5,
                }),
                ConnectionType::ControlWire(ControlSpec {
                    protocol: "24VAC".to_string(),
                    voltage: 24,
                }),
            ],
            implied_systems: vec![
                SystemType::HVACControl,
                SystemType::BuildingAutomation,
            ],
            maintenance_schedule: MaintenanceSchedule {
                inspection_days: 90,
                replacement_days: 5475,  // 15 years
                cleaning_days: 180,
                testing_days: 90,
            },
        });
        
        // Add more object types...
    }
    
    /// Infer details for an ArxObject based on its type and context
    pub fn infer(&self, obj: &ArxObject) -> DetailTree {
        let mut tree = DetailTree::new(*obj);
        
        // Get knowledge for this object type
        if let Some(knowledge) = self.type_knowledge.get(&obj.object_type) {
            // Infer identity
            self.infer_identity(&mut tree, knowledge);
            
            // Infer connections based on spatial context
            self.infer_connections(&mut tree, obj, knowledge);
            
            // Infer topology
            self.infer_topology(&mut tree, knowledge);
            
            // Infer full context
            self.infer_context(&mut tree, obj, knowledge);
        }
        
        tree
    }
    
    /// Infer identity information
    fn infer_identity(&self, tree: &mut DetailTree, knowledge: &ObjectKnowledge) {
        // Generate typical manufacturer and model based on object type
        let (manufacturer, model) = match tree.core.object_type {
            object_types::LIGHT => ("Philips", "BR30-LED"),
            object_types::OUTLET => ("Leviton", "5-20R"),
            object_types::HVAC_VENT => ("Titus", "TMR-AA"),
            object_types::THERMOSTAT => ("Honeywell", "T6-Pro"),
            _ => ("Generic", "Standard"),
        };
        
        // Encode specifications
        let mut specs = Vec::new();
        if let Some(power) = knowledge.typical_specs.power_consumption {
            specs.push((power >> 8) as u8);
            specs.push((power & 0xFF) as u8);
        }
        
        tree.add_identity(manufacturer, model, specs);
    }
    
    /// Infer connections based on spatial proximity
    fn infer_connections(&self, tree: &mut DetailTree, obj: &ArxObject, knowledge: &ObjectKnowledge) {
        // Find nearby objects of compatible types
        let nearby = self.spatial_index.find_nearby(obj, 5000); // 5 meter radius
        
        // Determine primary connection (usually circuit for electrical)
        let primary = match knowledge.category {
            SystemCategory::Electrical | SystemCategory::Lighting => {
                // Circuit ID based on spatial hashing
                self.hash_to_circuit(obj.x, obj.y, obj.z)
            }
            SystemCategory::HVAC => {
                // Zone ID based on floor
                (obj.z / 3000) as u16 // Floor-based zoning
            }
            _ => 0,
        };
        
        // Find secondary connections (switches, controllers)
        let mut secondary = Vec::new();
        for nearby_obj in nearby {
            if self.can_connect(obj, &nearby_obj) {
                secondary.push(nearby_obj.to_id() as u16);
            }
        }
        
        // Encode metadata about connection requirements
        let mut metadata = Vec::new();
        for conn_type in &knowledge.required_connections {
            match conn_type {
                ConnectionType::ElectricalCircuit(spec) => {
                    metadata.push(spec.wire_gauge);
                    metadata.push(spec.phase);
                }
                _ => {}
            }
        }
        
        tree.add_connections(primary, secondary, metadata);
    }
    
    /// Infer system topology
    fn infer_topology(&self, tree: &mut DetailTree, knowledge: &ObjectKnowledge) {
        if let Some(connections) = &tree.connections {
            // Infer panel from circuit
            let panel_id = self.topology_map.circuit_to_panel(connections.primary_connection);
            
            // Infer zone from position
            let zone_id = tree.core.z / 3000; // Floor-based
            
            // Infer network segment
            let network_segment = match knowledge.category {
                SystemCategory::Security => 100, // Security VLAN
                SystemCategory::Data => 200,     // Data VLAN
                _ => 1,                          // Default
            };
            
            // Set system flags
            let mut flags = 0u16;
            if knowledge.implied_systems.contains(&SystemType::EmergencyPower) {
                flags |= 0x01; // Emergency circuit flag
            }
            if knowledge.implied_systems.contains(&SystemType::SecurityMonitoring) {
                flags |= 0x02; // Security monitored flag
            }
            
            tree.add_topology(panel_id, zone_id, network_segment, flags);
        }
    }
    
    /// Infer full building context
    fn infer_context(&self, tree: &mut DetailTree, obj: &ArxObject, knowledge: &ObjectKnowledge) {
        // Find dependencies (what this object needs)
        let mut dependencies = Vec::new();
        if knowledge.category == SystemCategory::Electrical {
            // Depends on panel
            if let Some(topo) = &tree.topology {
                dependencies.push(topo.panel_id);
            }
        }
        
        // Find dependents (what needs this object)
        let dependents = self.spatial_index.find_dependents(obj);
        
        // Maintenance group based on type and location
        let maintenance_group = (obj.object_type as u16) * 100 + (obj.z / 3000) as u16;
        
        // Schedule ID based on object type
        let schedule_id = match knowledge.category {
            SystemCategory::Lighting => 1,  // Lighting schedule
            SystemCategory::HVAC => 2,      // HVAC schedule
            _ => 0,                         // Default schedule
        };
        
        tree.add_context(dependencies, dependents, maintenance_group, schedule_id);
    }
    
    /// Hash position to circuit ID
    fn hash_to_circuit(&self, x: u16, y: u16, z: u16) -> u16 {
        // Simple spatial hashing for demo
        let hash = ((x / 5000) + (y / 5000) * 10 + (z / 3000) * 100) as u16;
        hash % 42 + 1 // Circuits 1-42
    }
    
    /// Check if two objects can connect
    fn can_connect(&self, obj1: &ArxObject, obj2: &ArxObject) -> bool {
        // Lights can connect to switches
        if obj1.object_type == object_types::LIGHT && obj2.object_type == object_types::LIGHT_SWITCH {
            return true;
        }
        
        // Thermostats can connect to HVAC vents
        if obj1.object_type == object_types::THERMOSTAT && obj2.object_type == object_types::HVAC_VENT {
            return true;
        }
        
        false
    }
}

impl SpatialIndex {
    pub fn new(resolution: u16) -> Self {
        Self {
            grid: HashMap::new(),
            resolution,
        }
    }
    
    pub fn find_nearby(&self, _obj: &ArxObject, _radius: u16) -> Vec<ArxObject> {
        // Simplified - would use proper spatial indexing
        Vec::new()
    }
    
    pub fn find_dependents(&self, _obj: &ArxObject) -> Vec<u16> {
        // Find objects that depend on this one
        Vec::new()
    }
}

impl TopologyMap {
    pub fn new() -> Self {
        Self {
            circuits_to_panels: HashMap::new(),
            panels_to_transformers: HashMap::new(),
            zones_to_systems: HashMap::new(),
        }
    }
    
    pub fn circuit_to_panel(&self, circuit_id: u16) -> u16 {
        // Simple mapping for demo
        (circuit_id - 1) / 42 + 1 // 42 circuits per panel
    }
}

impl CodeRequirements {
    pub fn new() -> Self {
        Self {
            nec_2020: HashMap::new(),
            ashrae_90_1: HashMap::new(),
            nfpa_72: HashMap::new(),
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_light_inference() {
        let engine = InferenceEngine::new();
        
        // Create a light fixture
        let light = ArxObject::new(1, object_types::LIGHT, 5000, 3000, 1200);
        
        // Let the engine infer everything
        let tree = engine.infer(&light);
        
        // Verify identity was inferred
        assert!(tree.identity.is_some());
        let identity = tree.identity.unwrap();
        assert_eq!(identity.manufacturer, super::super::progressive_detail::hash_string("Philips"));
        
        // Verify connections were inferred
        assert!(tree.connections.is_some());
        
        // Verify topology was inferred
        assert!(tree.topology.is_some());
    }
}