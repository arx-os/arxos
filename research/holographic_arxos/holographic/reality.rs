//! Reality Manifestation System
//!
//! Core system that generates observer-specific reality from ArxObjects
//! by combining all holographic subsystems.

use crate::arxobject::{ArxObject, object_types};
use crate::holographic::{
    fractal::{FractalSpace, FractalCoordinate},
    noise::fractal_noise_3d,
    observer::{
        ObserverContext, ObserverRole, ManifestationParams, DetailLevel, InteractionMode,
        MaintenanceType, PlayerClass, Interest,
    },
    temporal::{TemporalEvolution, EnvironmentalFactors},
};

#[cfg(not(feature = "std"))]
use alloc::vec::Vec;
#[cfg(not(feature = "std"))]
use alloc::string::String;
#[cfg(not(feature = "std"))]
use alloc::collections::BTreeMap as HashMap;

#[cfg(feature = "std")]
use std::vec::Vec;
#[cfg(feature = "std")]
use std::string::String;
#[cfg(feature = "std")]
use std::collections::HashMap;

/// Manifested reality for a specific observer
#[derive(Clone, Debug)]
pub struct ManifestedReality {
    /// Geometric representation
    pub geometry: Geometry,
    
    /// Active systems
    pub systems: Vec<SystemState>,
    
    /// Available interactions
    pub interactions: Vec<ObjectInteraction>,
    
    /// Quantum state (if observable)
    pub quantum_state: Option<QuantumManifest>,
    
    /// Metadata specific to observer role
    pub metadata: ObserverMetadata,
    
    /// Temporal state
    pub temporal_state: TemporalState,
}

/// Geometric representation at current detail level
#[derive(Clone, Debug)]
pub struct Geometry {
    /// Vertices in observer space
    pub vertices: Vec<(f32, f32, f32)>,
    
    /// Faces (if detail level sufficient)
    pub faces: Option<Vec<(usize, usize, usize)>>,
    
    /// Level of detail (0.0-1.0)
    pub lod: f32,
    
    /// Material properties
    pub material: MaterialProperties,
    
    /// Bounding box
    pub bounds: BoundingBox,
}

/// Material properties based on observer detail level
#[derive(Clone, Debug)]
pub struct MaterialProperties {
    pub color: (f32, f32, f32),
    pub roughness: f32,
    pub metallic: f32,
    pub emission: f32,
    pub transparency: f32,
    pub texture_id: Option<u32>,
}

/// Bounding box in observer space
#[derive(Clone, Debug)]
pub struct BoundingBox {
    pub min: (f32, f32, f32),
    pub max: (f32, f32, f32),
}

/// System state visible to observer
#[derive(Clone, Debug)]
pub struct SystemState {
    pub system_type: SystemType,
    pub operational: bool,
    pub efficiency: f32,
    pub alerts: Vec<SystemAlert>,
    pub metrics: HashMap<String, f32>,
}

#[derive(Clone, Debug)]
pub enum SystemType {
    Electrical,
    HVAC,
    Plumbing,
    Network,
    Security,
    Fire,
}

#[derive(Clone, Debug)]
pub struct SystemAlert {
    pub severity: AlertSeverity,
    pub message: String,
    pub time: u64,
}

#[derive(Clone, Debug, PartialOrd, PartialEq)]
pub enum AlertSeverity {
    Info = 0,
    Warning = 1,
    Error = 2,
    Critical = 3,
}

/// Interaction available to observer
#[derive(Clone, Debug)]
pub struct ObjectInteraction {
    pub mode: InteractionMode,
    pub enabled: bool,
    pub cost: f32, // Energy/resource cost
    pub description: String,
    pub hotkey: Option<char>,
}

/// Quantum manifestation (Phase 3 placeholder)
#[derive(Clone, Debug)]
pub struct QuantumManifest {
    pub superposition: bool,
    pub entangled_with: Vec<u16>,
    pub collapse_probability: f32,
}

/// Temporal state of manifested object
#[derive(Clone, Debug)]
pub struct TemporalState {
    pub age: u64,
    pub wear_level: f32,
    pub last_maintenance: Option<u64>,
    pub predicted_failure: Option<u64>,
    pub evolution_rate: f32,
}

/// Observer-specific metadata
#[derive(Clone, Debug)]
pub enum ObserverMetadata {
    Maintenance {
        last_service: u64,
        next_service: u64,
        wear_level: f32,
        replacement_parts: Vec<String>,
        service_history: Vec<ServiceRecord>,
    },
    Security {
        last_accessed: u64,
        access_log: Vec<AccessRecord>,
        threat_level: f32,
        vulnerabilities: Vec<String>,
    },
    Game {
        interaction_prompt: String,
        loot_table: Vec<LootItem>,
        experience_value: u32,
        quest_relevance: f32,
        discovered: bool,
    },
    Facility {
        cost_per_month: f32,
        efficiency_rating: f32,
        compliance_status: Vec<ComplianceItem>,
        scheduled_tasks: Vec<ScheduledTask>,
    },
    Emergency {
        hazard_level: f32,
        evacuation_priority: u8,
        containment_status: String,
        response_checklist: Vec<ChecklistItem>,
    },
    Visitor {
        description: String,
        historical_significance: Option<String>,
        photo_opportunity: bool,
        accessibility: AccessibilityInfo,
    },
}

#[derive(Clone, Debug)]
pub struct ServiceRecord {
    pub date: u64,
    pub technician: String,
    pub work_performed: String,
}

#[derive(Clone, Debug)]
pub struct AccessRecord {
    pub time: u64,
    pub user_id: u32,
    pub action: String,
}

#[derive(Clone, Debug)]
pub struct LootItem {
    pub name: String,
    pub rarity: f32,
    pub value: u32,
}

#[derive(Clone, Debug)]
pub struct ComplianceItem {
    pub regulation: String,
    pub compliant: bool,
    pub next_inspection: u64,
}

#[derive(Clone, Debug)]
pub struct ScheduledTask {
    pub task: String,
    pub due_date: u64,
    pub assigned_to: Option<String>,
}

#[derive(Clone, Debug)]
pub struct ChecklistItem {
    pub item: String,
    pub completed: bool,
    pub critical: bool,
}

#[derive(Clone, Debug)]
pub struct AccessibilityInfo {
    pub wheelchair_accessible: bool,
    pub audio_description: Option<String>,
    pub braille_available: bool,
}

/// Reality manifestation engine
pub struct RealityManifester {
    temporal_evolution: TemporalEvolution,
    detail_cache: HashMap<(u16, u8), Geometry>,
}

impl RealityManifester {
    pub fn new(base_time: u64) -> Self {
        Self {
            temporal_evolution: TemporalEvolution::new(base_time, 1.0),
            detail_cache: HashMap::new(),
        }
    }
    
    /// Manifest reality for an ArxObject based on observer context
    pub fn manifest(
        &mut self,
        object: &ArxObject,
        observer: &ObserverContext,
    ) -> ManifestedReality {
        let params = observer.manifestation_params();
        
        // Check if object should be visible
        if !params.should_render_type(object.object_type) {
            return self.create_hidden_reality();
        }
        
        // Check render distance
        let distance = self.calculate_distance(object, observer);
        if distance > params.render_distance {
            return self.create_distant_reality(object, distance);
        }
        
        // Apply temporal evolution
        let evolved = self.temporal_evolution.evolve(object, observer.time);
        
        // Generate geometry based on detail level
        let geometry = self.generate_geometry(&evolved, &params.detail_level, distance);
        
        // Generate visible systems
        let systems = self.generate_systems(&evolved, &params);
        
        // Generate available interactions
        let interactions = self.generate_interactions(&evolved, &params, observer);
        
        // Generate quantum state (Phase 3 placeholder)
        let quantum_state = if params.detail_level.quantum > 0.0 {
            Some(self.generate_quantum_state(&evolved))
        } else {
            None
        };
        
        // Generate role-specific metadata
        let metadata = self.generate_metadata(&evolved, observer);
        
        // Generate temporal state
        let temporal_state = self.generate_temporal_state(&evolved);
        
        ManifestedReality {
            geometry,
            systems,
            interactions,
            quantum_state,
            metadata,
            temporal_state,
        }
    }
    
    /// Calculate distance between object and observer
    fn calculate_distance(&self, object: &ArxObject, observer: &ObserverContext) -> f32 {
        let obj_pos = FractalSpace::from_mm(object.x, object.y, object.z);
        obj_pos.distance(&observer.position, observer.scale) as f32
    }
    
    /// Create hidden reality (object not visible)
    fn create_hidden_reality(&self) -> ManifestedReality {
        ManifestedReality {
            geometry: Geometry {
                vertices: Vec::new(),
                faces: None,
                lod: 0.0,
                material: MaterialProperties {
                    color: (0.0, 0.0, 0.0),
                    roughness: 1.0,
                    metallic: 0.0,
                    emission: 0.0,
                    transparency: 1.0,
                    texture_id: None,
                },
                bounds: BoundingBox {
                    min: (0.0, 0.0, 0.0),
                    max: (0.0, 0.0, 0.0),
                },
            },
            systems: Vec::new(),
            interactions: Vec::new(),
            quantum_state: None,
            metadata: ObserverMetadata::Visitor {
                description: "Hidden".to_string(),
                historical_significance: None,
                photo_opportunity: false,
                accessibility: AccessibilityInfo {
                    wheelchair_accessible: false,
                    audio_description: None,
                    braille_available: false,
                },
            },
            temporal_state: TemporalState {
                age: 0,
                wear_level: 0.0,
                last_maintenance: None,
                predicted_failure: None,
                evolution_rate: 0.0,
            },
        }
    }
    
    /// Create distant reality (low detail)
    fn create_distant_reality(&self, object: &ArxObject, distance: f32) -> ManifestedReality {
        let lod = (1.0 - distance / 1000.0).max(0.0);
        
        ManifestedReality {
            geometry: Geometry {
                vertices: vec![
                    (object.x as f32 / 1000.0, object.y as f32 / 1000.0, object.z as f32 / 1000.0)
                ],
                faces: None,
                lod,
                material: self.get_basic_material(object.object_type),
                bounds: BoundingBox {
                    min: (object.x as f32 / 1000.0 - 0.5, 
                          object.y as f32 / 1000.0 - 0.5,
                          object.z as f32 / 1000.0 - 0.5),
                    max: (object.x as f32 / 1000.0 + 0.5,
                          object.y as f32 / 1000.0 + 0.5,
                          object.z as f32 / 1000.0 + 0.5),
                },
            },
            systems: Vec::new(),
            interactions: vec![ObjectInteraction {
                mode: InteractionMode::View,
                enabled: true,
                cost: 0.0,
                description: "View from distance".to_string(),
                hotkey: Some('v'),
            }],
            quantum_state: None,
            metadata: ObserverMetadata::Visitor {
                description: "Distant object".to_string(),
                historical_significance: None,
                photo_opportunity: false,
                accessibility: AccessibilityInfo {
                    wheelchair_accessible: false,
                    audio_description: None,
                    braille_available: false,
                },
            },
            temporal_state: TemporalState {
                age: 0,
                wear_level: 0.0,
                last_maintenance: None,
                predicted_failure: None,
                evolution_rate: 0.0,
            },
        }
    }
    
    /// Generate geometry based on detail level
    fn generate_geometry(
        &mut self,
        object: &ArxObject,
        detail: &DetailLevel,
        distance: f32,
    ) -> Geometry {
        // Check cache
        let cache_key = (object.building_id, object.object_type);
        if let Some(cached) = self.detail_cache.get(&cache_key) {
            return cached.clone();
        }
        
        let lod = detail.geometric * (1.0 - distance / 100.0).max(0.0);
        
        // Generate vertices based on object type and LOD
        let (vertices, faces) = self.generate_mesh(object, lod);
        
        let geometry = Geometry {
            vertices,
            faces,
            lod,
            material: self.generate_material(object, detail.material),
            bounds: self.calculate_bounds(object),
        };
        
        // Cache if high detail
        if lod > 0.8 {
            self.detail_cache.insert(cache_key, geometry.clone());
        }
        
        geometry
    }
    
    /// Generate mesh vertices and faces
    fn generate_mesh(&self, object: &ArxObject, lod: f32) -> (Vec<(f32, f32, f32)>, Option<Vec<(usize, usize, usize)>>) {
        let base_x = object.x as f32 / 1000.0;
        let base_y = object.y as f32 / 1000.0;
        let base_z = object.z as f32 / 1000.0;
        
        // Use procedural generation based on object type
        match object.object_type {
            x if x == object_types::WALL => {
                self.generate_wall_mesh(base_x, base_y, base_z, lod)
            }
            x if x == object_types::DOOR => {
                self.generate_door_mesh(base_x, base_y, base_z, lod)
            }
            x if x == object_types::OUTLET => {
                self.generate_outlet_mesh(base_x, base_y, base_z, lod)
            }
            _ => {
                // Default cube mesh
                self.generate_cube_mesh(base_x, base_y, base_z, 0.5, lod)
            }
        }
    }
    
    /// Generate cube mesh
    fn generate_cube_mesh(
        &self,
        x: f32,
        y: f32,
        z: f32,
        size: f32,
        lod: f32,
    ) -> (Vec<(f32, f32, f32)>, Option<Vec<(usize, usize, usize)>>) {
        let vertices = vec![
            (x - size, y - size, z - size),
            (x + size, y - size, z - size),
            (x + size, y + size, z - size),
            (x - size, y + size, z - size),
            (x - size, y - size, z + size),
            (x + size, y - size, z + size),
            (x + size, y + size, z + size),
            (x - size, y + size, z + size),
        ];
        
        let faces = if lod > 0.3 {
            Some(vec![
                (0, 1, 2), (0, 2, 3), // Front
                (4, 5, 6), (4, 6, 7), // Back
                (0, 1, 5), (0, 5, 4), // Bottom
                (2, 3, 7), (2, 7, 6), // Top
                (0, 3, 7), (0, 7, 4), // Left
                (1, 2, 6), (1, 6, 5), // Right
            ])
        } else {
            None
        };
        
        (vertices, faces)
    }
    
    /// Generate wall mesh
    fn generate_wall_mesh(
        &self,
        x: f32,
        y: f32,
        z: f32,
        lod: f32,
    ) -> (Vec<(f32, f32, f32)>, Option<Vec<(usize, usize, usize)>>) {
        let width = 3.0;
        let height = 3.0;
        let thickness = 0.2;
        
        let vertices = vec![
            (x, y - thickness, z),
            (x + width, y - thickness, z),
            (x + width, y + thickness, z),
            (x, y + thickness, z),
            (x, y - thickness, z + height),
            (x + width, y - thickness, z + height),
            (x + width, y + thickness, z + height),
            (x, y + thickness, z + height),
        ];
        
        let faces = if lod > 0.2 {
            Some(vec![
                (0, 1, 5), (0, 5, 4),
                (2, 3, 7), (2, 7, 6),
                (0, 3, 7), (0, 7, 4),
                (1, 2, 6), (1, 6, 5),
            ])
        } else {
            None
        };
        
        (vertices, faces)
    }
    
    /// Generate door mesh
    fn generate_door_mesh(
        &self,
        x: f32,
        y: f32,
        z: f32,
        lod: f32,
    ) -> (Vec<(f32, f32, f32)>, Option<Vec<(usize, usize, usize)>>) {
        let width = 1.0;
        let height = 2.1;
        let thickness = 0.05;
        
        // Add door frame if high detail
        if lod > 0.7 {
            let mut vertices = Vec::new();
            let mut faces = Vec::new();
            
            // Door panel
            vertices.extend(&[
                (x, y - thickness, z),
                (x + width, y - thickness, z),
                (x + width, y + thickness, z),
                (x, y + thickness, z),
                (x, y - thickness, z + height),
                (x + width, y - thickness, z + height),
                (x + width, y + thickness, z + height),
                (x, y + thickness, z + height),
            ]);
            
            // Door handle (if very high detail)
            if lod > 0.9 {
                let handle_x = x + width * 0.85;
                let handle_z = z + height * 0.5;
                vertices.extend(&[
                    (handle_x - 0.05, y - 0.05, handle_z - 0.05),
                    (handle_x + 0.05, y - 0.05, handle_z - 0.05),
                    (handle_x + 0.05, y + 0.05, handle_z - 0.05),
                    (handle_x - 0.05, y + 0.05, handle_z - 0.05),
                ]);
            }
            
            (vertices, Some(faces))
        } else {
            self.generate_cube_mesh(x + width/2.0, y, z + height/2.0, width/2.0, lod)
        }
    }
    
    /// Generate outlet mesh
    fn generate_outlet_mesh(
        &self,
        x: f32,
        y: f32,
        z: f32,
        lod: f32,
    ) -> (Vec<(f32, f32, f32)>, Option<Vec<(usize, usize, usize)>>) {
        if lod > 0.8 {
            // Detailed outlet with receptacles
            let mut vertices = Vec::new();
            
            // Faceplate
            vertices.extend(&[
                (x - 0.05, y - 0.01, z - 0.08),
                (x + 0.05, y - 0.01, z - 0.08),
                (x + 0.05, y + 0.01, z - 0.08),
                (x - 0.05, y + 0.01, z - 0.08),
                (x - 0.05, y - 0.01, z + 0.08),
                (x + 0.05, y - 0.01, z + 0.08),
                (x + 0.05, y + 0.01, z + 0.08),
                (x - 0.05, y + 0.01, z + 0.08),
            ]);
            
            // Receptacle holes (simplified)
            if lod > 0.95 {
                vertices.extend(&[
                    (x - 0.02, y, z - 0.03),
                    (x + 0.02, y, z - 0.03),
                    (x - 0.02, y, z + 0.03),
                    (x + 0.02, y, z + 0.03),
                ]);
            }
            
            (vertices, None)
        } else {
            self.generate_cube_mesh(x, y, z, 0.05, lod)
        }
    }
    
    /// Get basic material for object type
    fn get_basic_material(&self, object_type: u8) -> MaterialProperties {
        match object_type {
            x if x == object_types::WALL => MaterialProperties {
                color: (0.9, 0.9, 0.9),
                roughness: 0.8,
                metallic: 0.0,
                emission: 0.0,
                transparency: 0.0,
                texture_id: Some(1),
            },
            x if x == object_types::DOOR => MaterialProperties {
                color: (0.6, 0.4, 0.2),
                roughness: 0.6,
                metallic: 0.1,
                emission: 0.0,
                transparency: 0.0,
                texture_id: Some(2),
            },
            x if x == object_types::WINDOW => MaterialProperties {
                color: (0.8, 0.9, 1.0),
                roughness: 0.1,
                metallic: 0.0,
                emission: 0.0,
                transparency: 0.8,
                texture_id: Some(3),
            },
            x if x == object_types::LIGHT => MaterialProperties {
                color: (1.0, 1.0, 0.9),
                roughness: 0.3,
                metallic: 0.0,
                emission: 0.8,
                transparency: 0.0,
                texture_id: None,
            },
            _ => MaterialProperties {
                color: (0.5, 0.5, 0.5),
                roughness: 0.5,
                metallic: 0.0,
                emission: 0.0,
                transparency: 0.0,
                texture_id: None,
            },
        }
    }
    
    /// Generate material properties
    fn generate_material(&self, object: &ArxObject, detail_level: f32) -> MaterialProperties {
        let mut material = self.get_basic_material(object.object_type);
        
        // Add wear effects
        let wear = 1.0 - (object.properties[0] as f32 / 255.0);
        material.roughness = (material.roughness + wear * 0.3).min(1.0);
        material.color.0 *= 1.0 - wear * 0.2;
        material.color.1 *= 1.0 - wear * 0.2;
        material.color.2 *= 1.0 - wear * 0.2;
        
        // Add procedural variation using noise
        if detail_level > 0.7 {
            let noise = fractal_noise_3d(
                object.building_id as u64,
                object.x as f32 * 0.01,
                object.y as f32 * 0.01,
                object.z as f32 * 0.01,
                2,
                0.5,
                2.0,
            );
            
            material.roughness = (material.roughness + noise * 0.1).clamp(0.0, 1.0);
        }
        
        material
    }
    
    /// Calculate bounding box
    fn calculate_bounds(&self, object: &ArxObject) -> BoundingBox {
        let x = object.x as f32 / 1000.0;
        let y = object.y as f32 / 1000.0;
        let z = object.z as f32 / 1000.0;
        
        // Size based on object type
        let (width, height, depth) = match object.object_type {
            x if x == object_types::WALL => (3.0, 0.2, 3.0),
            x if x == object_types::DOOR => (1.0, 0.1, 2.1),
            x if x == object_types::OUTLET => (0.1, 0.05, 0.15),
            _ => (0.5, 0.5, 0.5),
        };
        
        BoundingBox {
            min: (x - width/2.0, y - depth/2.0, z),
            max: (x + width/2.0, y + depth/2.0, z + height),
        }
    }
    
    /// Generate visible systems
    fn generate_systems(&self, object: &ArxObject, params: &ManifestationParams) -> Vec<SystemState> {
        let mut systems = Vec::new();
        
        // Determine which system this object belongs to
        let system_type = match object.object_type {
            x if x >= 0x10 && x < 0x20 => Some(SystemType::Electrical),
            x if x >= 0x20 && x < 0x30 => Some(SystemType::HVAC),
            x if x >= 0x60 && x < 0x70 => Some(SystemType::Plumbing),
            x if x >= 0x70 && x < 0x80 => Some(SystemType::Network),
            x if x >= 0x40 && x < 0x50 => Some(SystemType::Security),
            _ => None,
        };
        
        if let Some(sys_type) = system_type {
            let operational = object.properties[0] > 50;
            let efficiency = object.properties[0] as f32 / 255.0;
            
            let mut alerts = Vec::new();
            if object.properties[0] < 30 {
                alerts.push(SystemAlert {
                    severity: AlertSeverity::Critical,
                    message: "System failure imminent".to_string(),
                    time: 0,
                });
            } else if object.properties[0] < 100 {
                alerts.push(SystemAlert {
                    severity: AlertSeverity::Warning,
                    message: "Maintenance required".to_string(),
                    time: 0,
                });
            }
            
            let mut metrics = HashMap::new();
            metrics.insert("health".to_string(), object.properties[0] as f32);
            metrics.insert("temperature".to_string(), object.properties[1] as f32);
            metrics.insert("usage".to_string(), object.properties[2] as f32);
            
            systems.push(SystemState {
                system_type: sys_type,
                operational,
                efficiency,
                alerts,
                metrics,
            });
        }
        
        systems
    }
    
    /// Generate available interactions
    fn generate_interactions(
        &self,
        object: &ArxObject,
        params: &ManifestationParams,
        observer: &ObserverContext,
    ) -> Vec<ObjectInteraction> {
        let mut interactions = Vec::new();
        
        for mode in &params.interaction_modes {
            let enabled = self.is_interaction_enabled(object, mode, observer);
            let cost = self.calculate_interaction_cost(mode, observer);
            let description = self.get_interaction_description(mode, object);
            let hotkey = self.get_interaction_hotkey(mode);
            
            interactions.push(ObjectInteraction {
                mode: mode.clone(),
                enabled,
                cost,
                description,
                hotkey,
            });
        }
        
        interactions
    }
    
    /// Check if interaction is enabled
    fn is_interaction_enabled(
        &self,
        object: &ArxObject,
        mode: &InteractionMode,
        observer: &ObserverContext,
    ) -> bool {
        match mode {
            InteractionMode::Repair => object.properties[0] < 200,
            InteractionMode::Lock => matches!(object.object_type, x if x == object_types::DOOR),
            InteractionMode::Configure => object.properties[3] & 0x01 == 0, // Not locked
            _ => true,
        }
    }
    
    /// Calculate interaction cost
    fn calculate_interaction_cost(
        &self,
        mode: &InteractionMode,
        observer: &ObserverContext,
    ) -> f32 {
        let base_cost = match mode {
            InteractionMode::View => 0.0,
            InteractionMode::Inspect => 0.1,
            InteractionMode::Interact => 0.2,
            InteractionMode::Repair => 0.5,
            InteractionMode::Replace => 1.0,
            InteractionMode::Configure => 0.3,
            InteractionMode::Override => 0.8,
            _ => 0.2,
        };
        
        base_cost * (2.0 - observer.energy_level)
    }
    
    /// Get interaction description
    fn get_interaction_description(&self, mode: &InteractionMode, object: &ArxObject) -> String {
        match mode {
            InteractionMode::View => "Examine object".to_string(),
            InteractionMode::Inspect => "Detailed inspection".to_string(),
            InteractionMode::Repair => format!("Repair ({}% health)", object.properties[0] * 100 / 255),
            InteractionMode::Configure => "Adjust settings".to_string(),
            _ => format!("{:?}", mode),
        }
    }
    
    /// Get interaction hotkey
    fn get_interaction_hotkey(&self, mode: &InteractionMode) -> Option<char> {
        match mode {
            InteractionMode::View => Some('v'),
            InteractionMode::Inspect => Some('i'),
            InteractionMode::Interact => Some('e'),
            InteractionMode::Repair => Some('r'),
            InteractionMode::Configure => Some('c'),
            _ => None,
        }
    }
    
    /// Generate quantum state (placeholder)
    fn generate_quantum_state(&self, object: &ArxObject) -> QuantumManifest {
        QuantumManifest {
            superposition: object.properties[3] & 0x02 != 0,
            entangled_with: Vec::new(),
            collapse_probability: 0.5,
        }
    }
    
    /// Generate role-specific metadata
    fn generate_metadata(&self, object: &ArxObject, observer: &ObserverContext) -> ObserverMetadata {
        match &observer.role {
            ObserverRole::MaintenanceWorker { .. } => {
                ObserverMetadata::Maintenance {
                    last_service: observer.time.saturating_sub(86400 * 30), // 30 days ago
                    next_service: observer.time.saturating_add(86400 * 60), // 60 days
                    wear_level: 1.0 - (object.properties[0] as f32 / 255.0),
                    replacement_parts: vec![
                        "Filter".to_string(),
                        "Gasket".to_string(),
                    ],
                    service_history: vec![
                        ServiceRecord {
                            date: observer.time.saturating_sub(86400 * 90),
                            technician: "Tech A".to_string(),
                            work_performed: "Routine maintenance".to_string(),
                        },
                    ],
                }
            }
            ObserverRole::GamePlayer { level, .. } => {
                ObserverMetadata::Game {
                    interaction_prompt: "Press E to interact".to_string(),
                    loot_table: vec![
                        LootItem {
                            name: "Scrap Metal".to_string(),
                            rarity: 0.1,
                            value: 10,
                        },
                    ],
                    experience_value: 50,
                    quest_relevance: 0.3,
                    discovered: *level > 10,
                }
            }
            _ => ObserverMetadata::Visitor {
                description: "Building component".to_string(),
                historical_significance: None,
                photo_opportunity: false,
                accessibility: AccessibilityInfo {
                    wheelchair_accessible: true,
                    audio_description: None,
                    braille_available: false,
                },
            },
        }
    }
    
    /// Generate temporal state
    fn generate_temporal_state(&self, object: &ArxObject) -> TemporalState {
        let age = self.temporal_evolution.base_time;
        let wear_level = 1.0 - (object.properties[0] as f32 / 255.0);
        let evolution_rate = self.temporal_evolution.get_evolution_rate(object);
        
        let predicted_failure = if object.properties[0] < 100 {
            Some(self.temporal_evolution.base_time + 86400 * 30)
        } else {
            None
        };
        
        TemporalState {
            age,
            wear_level,
            last_maintenance: if object.properties[3] & 0x08 != 0 {
                Some(self.temporal_evolution.base_time - 86400 * 7)
            } else {
                None
            },
            predicted_failure,
            evolution_rate,
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::holographic::observer::{MaintenanceType, PlayerClass};
    
    #[test]
    fn test_reality_manifestation() {
        let mut manifester = RealityManifester::new(0);
        
        let outlet = ArxObject::new(1, object_types::OUTLET, 5000, 3000, 1500);
        
        let observer = ObserverContext::new(
            1,
            ObserverRole::MaintenanceWorker {
                specialization: MaintenanceType::Electrical,
                access_level: 3,
                years_experience: 5,
            },
            FractalSpace::from_mm(5000, 3000, 1500),
            1000,
        );
        
        let reality = manifester.manifest(&outlet, &observer);
        
        // Should have geometry
        assert!(!reality.geometry.vertices.is_empty());
        
        // Should have electrical system visible
        assert!(!reality.systems.is_empty());
        
        // Should have maintenance metadata
        matches!(reality.metadata, ObserverMetadata::Maintenance { .. });
    }
    
    #[test]
    fn test_distance_culling() {
        let mut manifester = RealityManifester::new(0);
        
        let far_object = ArxObject::new(1, object_types::WALL, 50000, 50000, 0);
        
        let mut observer = ObserverContext::new(
            1,
            ObserverRole::Visitor {
                guide_level: 1,
                interests: vec![],
                time_limit: None,
            },
            FractalSpace::from_mm(0, 0, 0),
            0,
        );
        
        observer.scale = 1.0;
        
        let reality = manifester.manifest(&far_object, &observer);
        
        // Far object should have minimal detail
        assert!(reality.geometry.lod < 0.1);
    }
    
    #[test]
    fn test_role_specific_systems() {
        let mut manifester = RealityManifester::new(0);
        
        let hvac = ArxObject::new(1, object_types::AIR_VENT, 1000, 1000, 2000);
        
        // HVAC worker should see HVAC systems
        let hvac_worker = ObserverContext::new(
            1,
            ObserverRole::MaintenanceWorker {
                specialization: MaintenanceType::HVAC,
                access_level: 3,
                years_experience: 5,
            },
            FractalSpace::from_mm(1000, 1000, 2000),
            0,
        );
        
        let reality = manifester.manifest(&hvac, &hvac_worker);
        assert!(!reality.systems.is_empty());
        
        // Visitor shouldn't see internal systems
        let visitor = ObserverContext::new(
            2,
            ObserverRole::Visitor {
                guide_level: 1,
                interests: vec![],
                time_limit: None,
            },
            FractalSpace::from_mm(1000, 1000, 2000),
            0,
        );
        
        let visitor_reality = manifester.manifest(&hvac, &visitor);
        assert!(visitor_reality.systems.is_empty());
    }
}