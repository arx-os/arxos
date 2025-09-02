//! Observer Context System
//! 
//! Implements observer-dependent reality manifestation where ArxObjects
//! generate different realities based on who's observing them.

use crate::arxobject::{ArxObject, object_types};
use crate::holographic::fractal::{FractalCoordinate, FractalSpace};
use core::f32;

#[cfg(not(feature = "std"))]
use alloc::vec::Vec;
#[cfg(not(feature = "std"))]
use alloc::collections::VecDeque;

#[cfg(feature = "std")]
use std::vec::Vec;
#[cfg(feature = "std")]
use std::collections::VecDeque;

/// Observer identifier
pub type ObserverId = u32;

/// Maintenance specializations
#[derive(Clone, Debug, PartialEq)]
pub enum MaintenanceType {
    Electrical,
    HVAC,
    Plumbing,
    Structural,
    Janitorial,
    General,
}

/// Security clearance levels
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub enum SecurityClearance {
    Public = 0,
    Restricted = 1,
    Confidential = 2,
    Secret = 3,
    TopSecret = 4,
}

/// Department types for facility managers
#[derive(Clone, Debug, PartialEq)]
pub enum Department {
    Operations,
    Maintenance,
    Security,
    IT,
    Finance,
    HR,
    Safety,
}

/// Emergency response types
#[derive(Clone, Debug, PartialEq)]
pub enum EmergencyType {
    Fire,
    Medical,
    Security,
    HazMat,
    Structural,
    Evacuation,
}

/// System types that can be visible
#[derive(Clone, Debug, PartialEq)]
pub enum SystemType {
    Electrical,
    HVAC,
    Plumbing,
    Network,
    Security,
    Fire,
    Structural,
    All,
}

/// Visitor interests for guided experiences
#[derive(Clone, Debug, PartialEq)]
pub enum Interest {
    Architecture,
    History,
    Technology,
    Art,
    Engineering,
    Sustainability,
}

/// Game player classes
#[derive(Clone, Debug, PartialEq)]
pub enum PlayerClass {
    Engineer,
    Security,
    Hacker,
    Explorer,
    Speedrunner,
    Completionist,
}

/// Quest state for game context
#[derive(Clone, Debug)]
pub struct QuestState {
    pub quest_id: u32,
    pub objectives_complete: u8,
    pub objectives_total: u8,
    pub current_target: Option<u16>,
}

/// Observer role determines reality manifestation
#[derive(Clone, Debug)]
pub enum ObserverRole {
    MaintenanceWorker {
        specialization: MaintenanceType,
        access_level: u8,
        years_experience: u8,
    },
    SecurityGuard {
        clearance: SecurityClearance,
        patrol_route: Vec<u16>,
        alert_radius: f32,
    },
    FacilityManager {
        departments: Vec<Department>,
        budget_view: bool,
        management_level: u8,
    },
    EmergencyResponder {
        response_type: EmergencyType,
        priority_systems: Vec<SystemType>,
        response_code: u8,
    },
    Visitor {
        guide_level: u8,
        interests: Vec<Interest>,
        time_limit: Option<u32>,
    },
    GamePlayer {
        level: u32,
        experience: u32,
        class: PlayerClass,
        quest_context: Option<QuestState>,
        abilities_unlocked: Vec<u8>,
    },
    SystemAdministrator {
        full_access: bool,
        debug_mode: bool,
        audit_trail: bool,
    },
    AIAgent {
        agent_type: u8,
        processing_power: f32,
        memory_limit: usize,
    },
}

impl ObserverRole {
    /// Get base access level for this role
    pub fn access_level(&self) -> u8 {
        match self {
            ObserverRole::MaintenanceWorker { access_level, .. } => *access_level,
            ObserverRole::SecurityGuard { clearance, .. } => clearance.clone() as u8 * 2,
            ObserverRole::FacilityManager { management_level, .. } => *management_level * 3,
            ObserverRole::EmergencyResponder { .. } => 10, // High priority access
            ObserverRole::Visitor { guide_level, .. } => *guide_level,
            ObserverRole::GamePlayer { level, .. } => (*level / 10).min(10) as u8,
            ObserverRole::SystemAdministrator { .. } => 255, // Maximum access
            ObserverRole::AIAgent { .. } => 5, // Limited access
        }
    }
    
    /// Check if this role can see a specific system type
    pub fn can_see_system(&self, system: &SystemType) -> bool {
        match self {
            ObserverRole::MaintenanceWorker { specialization, .. } => {
                match (specialization, system) {
                    (MaintenanceType::Electrical, SystemType::Electrical) => true,
                    (MaintenanceType::HVAC, SystemType::HVAC) => true,
                    (MaintenanceType::Plumbing, SystemType::Plumbing) => true,
                    (MaintenanceType::General, _) => true,
                    _ => false,
                }
            }
            ObserverRole::EmergencyResponder { priority_systems, .. } => {
                priority_systems.contains(system) || priority_systems.contains(&SystemType::All)
            }
            ObserverRole::FacilityManager { .. } => true,
            ObserverRole::SystemAdministrator { .. } => true,
            ObserverRole::GamePlayer { level, abilities_unlocked, .. } => {
                // Unlock systems as player progresses
                match system {
                    SystemType::Electrical => *level >= 5 || abilities_unlocked.contains(&1),
                    SystemType::Network => *level >= 10 || abilities_unlocked.contains(&2),
                    SystemType::Security => *level >= 15 || abilities_unlocked.contains(&3),
                    _ => *level >= 20,
                }
            }
            _ => false,
        }
    }
}

/// Historical observation for context
#[derive(Clone, Debug)]
pub struct Observation {
    pub time: u64,
    pub object_id: u16,
    pub action: ObservationAction,
}

#[derive(Clone, Debug)]
pub enum ObservationAction {
    Viewed,
    Interacted,
    Modified,
    Created,
    Destroyed,
}

/// Complete observer context for reality generation
#[derive(Clone, Debug)]
pub struct ObserverContext {
    pub id: ObserverId,
    pub role: ObserverRole,
    pub position: FractalSpace,
    pub scale: f32, // 0.001 (atomic) to 1000.0 (city)
    pub time: u64, // Unix timestamp
    pub observation_depth: u8, // How deep to recurse
    pub consciousness_bandwidth: f32, // 0.0-1.0 reality detail
    pub entangled_observers: Vec<ObserverId>, // Shared reality
    pub observation_history: VecDeque<Observation>,
    pub energy_level: f32, // Observer's energy/attention (0.0-1.0)
    pub focus_point: Option<FractalSpace>, // Where attention is focused
}

impl ObserverContext {
    /// Create a new observer context
    pub fn new(id: ObserverId, role: ObserverRole, position: FractalSpace, time: u64) -> Self {
        // Set consciousness bandwidth based on role
        let consciousness_bandwidth = match &role {
            ObserverRole::GamePlayer { .. } => 1.0, // Full bandwidth for immersive experience
            ObserverRole::SystemAdministrator { .. } => 1.0, // Full bandwidth for debugging
            ObserverRole::AIAgent { processing_power, .. } => *processing_power,
            _ => 0.5, // Default for other roles
        };
        
        Self {
            id,
            role,
            position,
            scale: 1.0,
            time,
            observation_depth: 3,
            consciousness_bandwidth,
            entangled_observers: Vec::new(),
            observation_history: VecDeque::with_capacity(100),
            energy_level: 1.0,
            focus_point: None,
        }
    }
    
    /// Add an observation to history
    pub fn observe(&mut self, object_id: u16, action: ObservationAction) {
        let observation = Observation {
            time: self.time,
            object_id,
            action,
        };
        
        self.observation_history.push_back(observation);
        
        // Keep history limited
        if self.observation_history.len() > 100 {
            self.observation_history.pop_front();
        }
    }
    
    /// Calculate reality manifestation parameters
    pub fn manifestation_params(&self) -> ManifestationParams {
        ManifestationParams {
            detail_level: self.calculate_detail_level(),
            visible_systems: self.get_visible_systems(),
            interaction_modes: self.get_available_interactions(),
            time_evolution_rate: self.get_time_rate(),
            quantum_collapse_radius: self.consciousness_bandwidth * 10.0,
            perception_filter: self.get_perception_filter(),
            render_distance: self.calculate_render_distance(),
        }
    }
    
    /// Calculate appropriate detail level based on role and context
    fn calculate_detail_level(&self) -> DetailLevel {
        let base_detail = match &self.role {
            ObserverRole::MaintenanceWorker { years_experience, .. } => {
                DetailLevel {
                    geometric: 0.6 + (*years_experience as f32 * 0.02),
                    material: 0.9, // High material detail for maintenance
                    systems: 1.0,   // Full system visibility
                    aesthetic: 0.3,
                    quantum: 0.1,
                    temporal: 0.5,
                }
            }
            ObserverRole::SecurityGuard { clearance, .. } => {
                let clearance_bonus = clearance.clone() as u8 as f32 * 0.1;
                DetailLevel {
                    geometric: 0.7,
                    material: 0.4,
                    systems: 0.3 + clearance_bonus,
                    aesthetic: 0.2,
                    quantum: 0.0,
                    temporal: 0.8, // High temporal awareness
                }
            }
            ObserverRole::FacilityManager { management_level, .. } => {
                DetailLevel {
                    geometric: 0.5,
                    material: 0.5,
                    systems: 0.8 + (*management_level as f32 * 0.05),
                    aesthetic: 0.6,
                    quantum: 0.2,
                    temporal: 0.7,
                }
            }
            ObserverRole::EmergencyResponder { response_code, .. } => {
                let urgency = (*response_code as f32 / 10.0).min(1.0);
                DetailLevel {
                    geometric: 0.8,
                    material: 0.3,
                    systems: urgency,
                    aesthetic: 0.0, // No time for aesthetics
                    quantum: 0.0,
                    temporal: 1.0 - urgency, // Less time awareness when urgent
                }
            }
            ObserverRole::Visitor { guide_level, .. } => {
                DetailLevel {
                    geometric: 0.7,
                    material: 0.3,
                    systems: 0.1 * *guide_level as f32,
                    aesthetic: 0.9, // High aesthetic for visitors
                    quantum: 0.0,
                    temporal: 0.3,
                }
            }
            ObserverRole::GamePlayer { level, class, .. } => {
                let level_factor = (*level as f32 / 100.0).min(1.0);
                let class_bonus = match class {
                    PlayerClass::Engineer => 0.2,
                    PlayerClass::Hacker => 0.3,
                    _ => 0.0,
                };
                DetailLevel {
                    geometric: 0.8,
                    material: 0.4 + level_factor * 0.2,
                    systems: level_factor * 0.8 + class_bonus,
                    aesthetic: 0.9, // High for game enjoyment
                    quantum: (level_factor * 0.5).min(1.0),
                    temporal: 0.5,
                }
            }
            ObserverRole::SystemAdministrator { debug_mode, .. } => {
                if *debug_mode {
                    DetailLevel::maximum()
                } else {
                    DetailLevel::balanced()
                }
            }
            ObserverRole::AIAgent { processing_power, .. } => {
                DetailLevel {
                    geometric: processing_power.min(1.0),
                    material: processing_power * 0.5,
                    systems: processing_power * 0.8,
                    aesthetic: 0.0, // AI doesn't need aesthetics
                    quantum: processing_power.min(1.0),
                    temporal: 1.0,
                }
            }
        };
        
        // Adjust for energy level and consciousness bandwidth
        base_detail.scale(self.energy_level * self.consciousness_bandwidth)
    }
    
    /// Get list of visible systems for this observer
    fn get_visible_systems(&self) -> Vec<SystemType> {
        let mut systems = Vec::new();
        
        for system_type in &[
            SystemType::Electrical,
            SystemType::HVAC,
            SystemType::Plumbing,
            SystemType::Network,
            SystemType::Security,
            SystemType::Fire,
            SystemType::Structural,
        ] {
            if self.role.can_see_system(system_type) {
                systems.push(system_type.clone());
            }
        }
        
        systems
    }
    
    /// Get available interaction modes
    fn get_available_interactions(&self) -> Vec<InteractionMode> {
        let mut modes = vec![InteractionMode::View];
        
        match &self.role {
            ObserverRole::MaintenanceWorker { .. } => {
                modes.extend(vec![
                    InteractionMode::Inspect,
                    InteractionMode::Repair,
                    InteractionMode::Replace,
                    InteractionMode::Calibrate,
                ]);
            }
            ObserverRole::SecurityGuard { .. } => {
                modes.extend(vec![
                    InteractionMode::Inspect,
                    InteractionMode::Lock,
                    InteractionMode::Alarm,
                    InteractionMode::Report,
                ]);
            }
            ObserverRole::FacilityManager { .. } => {
                modes.extend(vec![
                    InteractionMode::Inspect,
                    InteractionMode::Configure,
                    InteractionMode::Schedule,
                    InteractionMode::Report,
                ]);
            }
            ObserverRole::EmergencyResponder { .. } => {
                modes.extend(vec![
                    InteractionMode::Inspect,
                    InteractionMode::Override,
                    InteractionMode::Evacuate,
                    InteractionMode::Contain,
                ]);
            }
            ObserverRole::GamePlayer { abilities_unlocked, .. } => {
                modes.push(InteractionMode::Interact);
                if abilities_unlocked.contains(&10) {
                    modes.push(InteractionMode::Hack);
                }
                if abilities_unlocked.contains(&15) {
                    modes.push(InteractionMode::Modify);
                }
            }
            ObserverRole::SystemAdministrator { .. } => {
                modes.extend(vec![
                    InteractionMode::Inspect,
                    InteractionMode::Configure,
                    InteractionMode::Override,
                    InteractionMode::Debug,
                    InteractionMode::Modify,
                ]);
            }
            _ => {}
        }
        
        modes
    }
    
    /// Get time evolution rate based on role
    fn get_time_rate(&self) -> f32 {
        match &self.role {
            ObserverRole::EmergencyResponder { response_code, .. } => {
                // Time slows down in emergencies
                1.0 / (1.0 + *response_code as f32 * 0.2)
            }
            ObserverRole::GamePlayer { class, .. } => {
                match class {
                    PlayerClass::Speedrunner => 2.0, // Faster time
                    _ => 1.0,
                }
            }
            ObserverRole::AIAgent { processing_power, .. } => {
                // AI can process faster
                1.0 + processing_power * 5.0
            }
            _ => 1.0,
        }
    }
    
    /// Get perception filter based on role
    fn get_perception_filter(&self) -> PerceptionFilter {
        match &self.role {
            ObserverRole::MaintenanceWorker { specialization, .. } => {
                PerceptionFilter::Technical(specialization.clone())
            }
            ObserverRole::SecurityGuard { .. } => PerceptionFilter::Threat,
            ObserverRole::Visitor { .. } => PerceptionFilter::Aesthetic,
            ObserverRole::GamePlayer { .. } => PerceptionFilter::Interactive,
            ObserverRole::EmergencyResponder { .. } => PerceptionFilter::Hazard,
            _ => PerceptionFilter::Standard,
        }
    }
    
    /// Calculate render distance based on context
    fn calculate_render_distance(&self) -> f32 {
        let base_distance = match &self.role {
            ObserverRole::SecurityGuard { alert_radius, .. } => *alert_radius,
            ObserverRole::GamePlayer { level, .. } => 10.0 + (*level as f32),
            ObserverRole::SystemAdministrator { .. } => 1000.0,
            _ => 50.0,
        };
        
        // Adjust for scale and energy
        base_distance * self.scale * self.energy_level
    }
}

/// Detail levels for different aspects of reality
#[derive(Clone, Debug)]
pub struct DetailLevel {
    pub geometric: f32,    // Shape and form detail (0.0-1.0)
    pub material: f32,     // Material properties detail
    pub systems: f32,      // Internal systems visibility
    pub aesthetic: f32,    // Visual beauty and style
    pub quantum: f32,      // Quantum effects visibility
    pub temporal: f32,     // Time-based changes visibility
}

impl DetailLevel {
    /// Create maximum detail level
    pub fn maximum() -> Self {
        Self {
            geometric: 1.0,
            material: 1.0,
            systems: 1.0,
            aesthetic: 1.0,
            quantum: 1.0,
            temporal: 1.0,
        }
    }
    
    /// Create balanced detail level
    pub fn balanced() -> Self {
        Self {
            geometric: 0.7,
            material: 0.6,
            systems: 0.5,
            aesthetic: 0.5,
            quantum: 0.3,
            temporal: 0.5,
        }
    }
    
    /// Scale all detail levels by a factor
    pub fn scale(&self, factor: f32) -> Self {
        Self {
            geometric: (self.geometric * factor).min(1.0),
            material: (self.material * factor).min(1.0),
            systems: (self.systems * factor).min(1.0),
            aesthetic: (self.aesthetic * factor).min(1.0),
            quantum: (self.quantum * factor).min(1.0),
            temporal: (self.temporal * factor).min(1.0),
        }
    }
}

/// Interaction modes available to observers
#[derive(Clone, Debug, PartialEq)]
pub enum InteractionMode {
    View,
    Inspect,
    Interact,
    Repair,
    Replace,
    Configure,
    Override,
    Lock,
    Unlock,
    Alarm,
    Report,
    Schedule,
    Calibrate,
    Hack,
    Modify,
    Debug,
    Evacuate,
    Contain,
}

/// Perception filters that affect what's visible
#[derive(Clone, Debug)]
pub enum PerceptionFilter {
    Standard,
    Technical(MaintenanceType),
    Threat,
    Aesthetic,
    Interactive,
    Hazard,
    Historical,
    Predictive,
}

/// Parameters for reality manifestation
#[derive(Clone, Debug)]
pub struct ManifestationParams {
    pub detail_level: DetailLevel,
    pub visible_systems: Vec<SystemType>,
    pub interaction_modes: Vec<InteractionMode>,
    pub time_evolution_rate: f32,
    pub quantum_collapse_radius: f32,
    pub perception_filter: PerceptionFilter,
    pub render_distance: f32,
}

impl ManifestationParams {
    /// Check if a specific object type should be visible
    pub fn should_render_type(&self, object_type: u8) -> bool {
        // Check if object type belongs to visible systems
        let system = object_type_to_system(object_type);
        
        if let Some(sys) = system {
            self.visible_systems.contains(&sys) || self.visible_systems.contains(&SystemType::All)
        } else {
            // Always show structural elements
            matches!(object_type, 
                x if x == object_types::WALL || 
                x == object_types::FLOOR || 
                x == object_types::DOOR ||
                x == object_types::WINDOW)
        }
    }
    
    /// Get render priority for an object
    pub fn render_priority(&self, object: &ArxObject) -> f32 {
        let type_priority = match object.object_type {
            x if x == object_types::FIRE_ALARM => 10.0,
            x if x == object_types::EMERGENCY_EXIT => 9.0,
            x if x == object_types::DOOR => 8.0,
            x if x == object_types::WALL => 7.0,
            _ => 5.0,
        };
        
        // Adjust based on perception filter
        let filter_modifier = match &self.perception_filter {
            PerceptionFilter::Threat => {
                if object.object_type == object_types::CAMERA { 2.0 } else { 1.0 }
            }
            PerceptionFilter::Hazard => {
                if object.object_type == object_types::FIRE_ALARM { 3.0 } else { 1.0 }
            }
            _ => 1.0,
        };
        
        type_priority * filter_modifier * self.detail_level.geometric
    }
}

/// Convert object type to system type
fn object_type_to_system(object_type: u8) -> Option<SystemType> {
    match object_type {
        x if x >= 0x10 && x < 0x20 => Some(SystemType::Electrical),
        x if x >= 0x20 && x < 0x30 => Some(SystemType::HVAC),
        x if x >= 0x60 && x < 0x70 => Some(SystemType::Plumbing),
        x if x >= 0x70 && x < 0x80 => Some(SystemType::Network),
        x if x >= 0x40 && x < 0x50 => Some(SystemType::Security),
        x if x == object_types::FIRE_ALARM || x == object_types::SPRINKLER => Some(SystemType::Fire),
        x if x >= 0x50 && x < 0x60 => Some(SystemType::Structural),
        _ => None,
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_observer_role_access_levels() {
        let maintenance = ObserverRole::MaintenanceWorker {
            specialization: MaintenanceType::Electrical,
            access_level: 3,
            years_experience: 5,
        };
        assert_eq!(maintenance.access_level(), 3);
        
        let admin = ObserverRole::SystemAdministrator {
            full_access: true,
            debug_mode: false,
            audit_trail: true,
        };
        assert_eq!(admin.access_level(), 255);
    }
    
    #[test]
    fn test_system_visibility() {
        let electrician = ObserverRole::MaintenanceWorker {
            specialization: MaintenanceType::Electrical,
            access_level: 2,
            years_experience: 3,
        };
        
        assert!(electrician.can_see_system(&SystemType::Electrical));
        assert!(!electrician.can_see_system(&SystemType::Plumbing));
        
        let general = ObserverRole::MaintenanceWorker {
            specialization: MaintenanceType::General,
            access_level: 3,
            years_experience: 10,
        };
        
        assert!(general.can_see_system(&SystemType::Electrical));
        assert!(general.can_see_system(&SystemType::Plumbing));
    }
    
    #[test]
    fn test_detail_level_calculation() {
        let context = ObserverContext::new(
            1,
            ObserverRole::GamePlayer {
                level: 50,
                experience: 10000,
                class: PlayerClass::Engineer,
                quest_context: None,
                abilities_unlocked: vec![1, 2, 3],
            },
            FractalSpace::from_mm(5000, 5000, 1500),
            1234567890,
        );
        
        let params = context.manifestation_params();
        assert!(params.detail_level.systems > 0.5);
        assert!(params.detail_level.aesthetic > 0.8);
    }
    
    #[test]
    fn test_interaction_modes() {
        let worker = ObserverContext::new(
            2,
            ObserverRole::MaintenanceWorker {
                specialization: MaintenanceType::HVAC,
                access_level: 3,
                years_experience: 5,
            },
            FractalSpace::from_mm(1000, 1000, 1000),
            0,
        );
        
        let params = worker.manifestation_params();
        assert!(params.interaction_modes.contains(&InteractionMode::Repair));
        assert!(params.interaction_modes.contains(&InteractionMode::Inspect));
    }
    
    #[test]
    fn test_observation_history() {
        let mut context = ObserverContext::new(
            3,
            ObserverRole::Visitor {
                guide_level: 2,
                interests: vec![Interest::Architecture, Interest::Technology],
                time_limit: Some(3600),
            },
            FractalSpace::from_mm(0, 0, 0),
            0,
        );
        
        context.observe(100, ObservationAction::Viewed);
        context.observe(101, ObservationAction::Interacted);
        
        assert_eq!(context.observation_history.len(), 2);
    }
}