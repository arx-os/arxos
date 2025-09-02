//! Temporal Evolution System
//! 
//! Implements time-based evolution of ArxObjects, allowing them to change
//! over time based on environmental factors, wear, and observer interactions.

use crate::arxobject::{ArxObject, object_types, properties};
use crate::holographic::observer::{ObserverContext, ObserverRole};
use crate::holographic::fractal::FractalSpace;
use core::f32::consts::E;

#[cfg(not(feature = "std"))]
use alloc::vec::Vec;
#[cfg(not(feature = "std"))]
use alloc::collections::BTreeMap as HashMap;

#[cfg(feature = "std")]
use std::vec::Vec;
#[cfg(feature = "std")]
use std::collections::HashMap;

/// Time-based evolution of ArxObjects
#[derive(Clone, Debug)]
pub struct TemporalEvolution {
    /// Base time for evolution calculations
    pub base_time: u64,
    
    /// Reality time multiplier
    pub time_scale: f32,
    
    /// Evolution rules for different object types
    pub evolution_rules: Vec<EvolutionRule>,
    
    /// Environmental factors affecting evolution
    pub environment: EnvironmentalFactors,
    
    /// Cache of evolved states
    evolution_cache: HashMap<(u16, u64), ArxObject>,
}

/// Environmental factors that affect evolution
#[derive(Clone, Debug)]
pub struct EnvironmentalFactors {
    pub temperature: f32,      // Celsius
    pub humidity: f32,         // 0.0-1.0
    pub air_quality: f32,      // 0.0-1.0 (1.0 = perfect)
    pub vibration: f32,        // 0.0-1.0 intensity
    pub light_level: f32,      // 0.0-1.0
    pub occupancy: f32,        // 0.0-1.0
    pub maintenance_quality: f32, // 0.0-1.0
}

impl Default for EnvironmentalFactors {
    fn default() -> Self {
        Self {
            temperature: 20.0,
            humidity: 0.5,
            air_quality: 0.9,
            vibration: 0.1,
            light_level: 0.7,
            occupancy: 0.3,
            maintenance_quality: 0.8,
        }
    }
}

/// Rule for how objects evolve over time
#[derive(Clone, Debug)]
pub struct EvolutionRule {
    /// Object types this rule applies to
    pub applicable_types: Vec<u8>,
    
    /// Evolution function
    pub evolution_type: EvolutionType,
    
    /// Rate of change (per second)
    pub rate: f32,
    
    /// Priority for rule application
    pub priority: u8,
}

/// Types of evolution behaviors
#[derive(Clone, Debug)]
pub enum EvolutionType {
    /// Gradual wear and degradation
    Wear {
        wear_factor: f32,
        critical_threshold: f32,
    },
    
    /// Temperature-based changes
    Thermal {
        target_temp: f32,
        thermal_mass: f32,
    },
    
    /// Cyclic patterns (e.g., HVAC cycles)
    Cyclic {
        period: f32,  // Seconds
        amplitude: f32,
        phase: f32,
    },
    
    /// Growth/accumulation (e.g., dust, wear)
    Accumulation {
        max_value: f32,
        accumulation_rate: f32,
    },
    
    /// Decay/consumption (e.g., battery, fuel)
    Decay {
        half_life: f32,
        min_value: f32,
    },
    
    /// State machine transitions
    StateTransition {
        states: Vec<u8>,
        transition_probabilities: Vec<f32>,
    },
    
    /// Maintenance effects
    Maintenance {
        degradation_rate: f32,
        maintenance_boost: f32,
    },
}

impl TemporalEvolution {
    /// Create new temporal evolution system
    pub fn new(base_time: u64, time_scale: f32) -> Self {
        Self {
            base_time,
            time_scale,
            evolution_rules: Self::default_rules(),
            environment: EnvironmentalFactors::default(),
            evolution_cache: HashMap::new(),
        }
    }
    
    /// Get default evolution rules
    fn default_rules() -> Vec<EvolutionRule> {
        vec![
            // Electrical equipment wear
            EvolutionRule {
                applicable_types: vec![
                    object_types::OUTLET,
                    object_types::LIGHT_SWITCH,
                    object_types::CIRCUIT_BREAKER,
                ],
                evolution_type: EvolutionType::Wear {
                    wear_factor: 0.00001,
                    critical_threshold: 0.2,
                },
                rate: 1.0,
                priority: 5,
            },
            
            // HVAC temperature cycling
            EvolutionRule {
                applicable_types: vec![
                    object_types::THERMOSTAT,
                    object_types::AIR_VENT,
                ],
                evolution_type: EvolutionType::Cyclic {
                    period: 1800.0, // 30 minutes
                    amplitude: 2.0,
                    phase: 0.0,
                },
                rate: 1.0,
                priority: 3,
            },
            
            // Battery decay
            EvolutionRule {
                applicable_types: vec![
                    object_types::SMOKE_DETECTOR,
                    object_types::MOTION_SENSOR,
                    object_types::UPS,
                ],
                evolution_type: EvolutionType::Decay {
                    half_life: 15552000.0, // 6 months in seconds
                    min_value: 0.0,
                },
                rate: 1.0,
                priority: 4,
            },
            
            // Dust accumulation
            EvolutionRule {
                applicable_types: vec![
                    object_types::AIR_VENT,
                    object_types::LIGHT,
                    object_types::SMOKE_DETECTOR,
                ],
                evolution_type: EvolutionType::Accumulation {
                    max_value: 100.0,
                    accumulation_rate: 0.00001,
                },
                rate: 1.0,
                priority: 2,
            },
            
            // Thermal equilibrium
            EvolutionRule {
                applicable_types: vec![
                    object_types::ROOM,
                    object_types::WALL,
                    object_types::FLOOR,
                ],
                evolution_type: EvolutionType::Thermal {
                    target_temp: 20.0,
                    thermal_mass: 1000.0,
                },
                rate: 0.1,
                priority: 1,
            },
        ]
    }
    
    /// Evolve an object to a specific time
    pub fn evolve(&mut self, object: &ArxObject, current_time: u64) -> ArxObject {
        // Check cache first
        let cache_key = (object.building_id, current_time / 60); // Cache per minute
        if let Some(cached) = self.evolution_cache.get(&cache_key) {
            return *cached;
        }
        
        let delta_t = (current_time.saturating_sub(self.base_time)) as f32 * self.time_scale;
        
        let mut evolved = *object;
        
        // Apply evolution rules in priority order
        let mut rules = self.evolution_rules.clone();
        rules.sort_by_key(|r| 255 - r.priority);
        
        for rule in &rules {
            if rule.applicable_types.contains(&object.object_type) {
                evolved = self.apply_evolution_rule(&evolved, &rule, delta_t);
            }
        }
        
        // Apply environmental factors
        evolved = self.apply_environmental_effects(&evolved, delta_t);
        
        // Cache the result
        self.evolution_cache.insert(cache_key, evolved);
        
        // Limit cache size
        if self.evolution_cache.len() > 1000 {
            self.evolution_cache.clear();
        }
        
        evolved
    }
    
    /// Apply a specific evolution rule
    fn apply_evolution_rule(&self, object: &ArxObject, rule: &EvolutionRule, delta_t: f32) -> ArxObject {
        let mut evolved = *object;
        
        match &rule.evolution_type {
            EvolutionType::Wear { wear_factor, critical_threshold } => {
                // Calculate wear based on time and environment
                let wear_rate = wear_factor * rule.rate * (2.0 - self.environment.maintenance_quality);
                let total_wear = (wear_rate * delta_t * 255.0) as u8;
                
                // Apply wear to first property byte (health/condition)
                let current_health = evolved.properties[0];
                evolved.properties[0] = current_health.saturating_sub(total_wear);
                
                // Mark as critical if below threshold
                if evolved.properties[0] < (critical_threshold * 255.0) as u8 {
                    evolved.properties[3] |= 0x80; // Set critical flag
                }
            }
            
            EvolutionType::Thermal { target_temp, thermal_mass } => {
                // Newton's law of cooling
                let current_temp = properties::decode_temperature(evolved.properties[1]);
                let temp_diff = self.environment.temperature - current_temp;
                let cooling_rate = rule.rate / thermal_mass;
                let new_temp = current_temp + temp_diff * (1.0 - E.powf(-cooling_rate * delta_t));
                
                evolved.properties[1] = properties::encode_temperature(new_temp);
            }
            
            EvolutionType::Cyclic { period, amplitude, phase } => {
                // Sinusoidal variation
                let omega = 2.0 * core::f32::consts::PI / period;
                let value = amplitude * (omega * delta_t + phase).sin();
                
                // Store in second property byte
                evolved.properties[1] = ((value + amplitude) * 127.0 / amplitude) as u8;
            }
            
            EvolutionType::Accumulation { max_value, accumulation_rate } => {
                // Linear accumulation with cap
                let current = evolved.properties[2] as f32;
                let accumulated = (current + accumulation_rate * rule.rate * delta_t * 255.0)
                    .min(*max_value);
                
                evolved.properties[2] = accumulated as u8;
            }
            
            EvolutionType::Decay { half_life, min_value } => {
                // Exponential decay
                let decay_constant = 0.693 / half_life; // ln(2) / half_life
                let current = evolved.properties[0] as f32;
                let decayed = current * E.powf(-decay_constant * rule.rate * delta_t);
                
                evolved.properties[0] = decayed.max(*min_value) as u8;
            }
            
            EvolutionType::StateTransition { states, transition_probabilities } => {
                // Probabilistic state transition
                let current_state = evolved.properties[3] & 0x0F; // Lower 4 bits for state
                
                if let Some(state_idx) = states.iter().position(|&s| s == current_state) {
                    // Check if transition should occur
                    let prob = transition_probabilities.get(state_idx).unwrap_or(&0.0);
                    let threshold = prob * delta_t;
                    
                    // Simple deterministic "random" based on time
                    let should_transition = ((delta_t * 1000.0) as u32 % 1000) < (threshold * 1000.0) as u32;
                    
                    if should_transition {
                        let next_idx = (state_idx + 1) % states.len();
                        let next_state = states[next_idx];
                        evolved.properties[3] = (evolved.properties[3] & 0xF0) | (next_state & 0x0F);
                    }
                }
            }
            
            EvolutionType::Maintenance { degradation_rate, maintenance_boost } => {
                // Maintenance affects degradation rate
                let maintenance_factor = self.environment.maintenance_quality;
                let effective_rate = degradation_rate * (1.0 - maintenance_factor) * rule.rate;
                
                let current_condition = evolved.properties[0] as f32;
                let new_condition = if maintenance_factor > 0.8 {
                    // Good maintenance can improve condition
                    (current_condition + maintenance_boost * delta_t).min(255.0)
                } else {
                    // Poor maintenance accelerates degradation
                    (current_condition - effective_rate * delta_t * 255.0).max(0.0)
                };
                
                evolved.properties[0] = new_condition as u8;
            }
        }
        
        evolved
    }
    
    /// Apply environmental effects to object
    fn apply_environmental_effects(&self, object: &ArxObject, delta_t: f32) -> ArxObject {
        let mut evolved = *object;
        
        // Temperature stress on electronics
        if matches!(object.object_type, 
            x if x >= 0x10 && x < 0x20 || // Electrical
                 x >= 0x70 && x < 0x80)    // Network
        {
            let temp_stress = ((self.environment.temperature - 20.0).abs() / 30.0).min(1.0);
            let stress_damage = (temp_stress * 0.0001 * delta_t * 255.0) as u8;
            evolved.properties[0] = evolved.properties[0].saturating_sub(stress_damage);
        }
        
        // Humidity effects on certain materials
        if matches!(object.object_type,
            x if x == object_types::DRYWALL ||
                 x == object_types::CEILING)
        {
            if self.environment.humidity > 0.7 {
                let humidity_damage = ((self.environment.humidity - 0.7) * 0.001 * delta_t * 255.0) as u8;
                evolved.properties[0] = evolved.properties[0].saturating_sub(humidity_damage);
            }
        }
        
        // Vibration effects on mechanical systems
        if matches!(object.object_type,
            x if x == object_types::PUMP ||
                 x == object_types::FAN ||
                 x == object_types::AIR_HANDLER)
        {
            let vibration_wear = (self.environment.vibration * 0.0002 * delta_t * 255.0) as u8;
            evolved.properties[0] = evolved.properties[0].saturating_sub(vibration_wear);
        }
        
        // Occupancy affects HVAC and lighting
        if matches!(object.object_type,
            x if x == object_types::LIGHT ||
                 x == object_types::THERMOSTAT)
        {
            // Store occupancy level in property
            evolved.properties[2] = (self.environment.occupancy * 255.0) as u8;
        }
        
        evolved
    }
    
    /// Predict future state of an object
    pub fn predict(&self, object: &ArxObject, future_time: u64) -> ArxObject {
        let mut temp_evolution = self.clone();
        temp_evolution.evolve(object, future_time)
    }
    
    /// Apply observer-triggered evolution
    pub fn evolve_from_observation(
        &mut self,
        object: &ArxObject,
        observer: &ObserverContext,
    ) -> ArxObject {
        let mut evolved = *object;
        
        // Different observers cause different evolutionary effects
        match &observer.role {
            ObserverRole::MaintenanceWorker { .. } => {
                // Maintenance observation can improve condition
                if evolved.properties[0] < 200 {
                    evolved.properties[0] = evolved.properties[0].saturating_add(10);
                }
                // Reset wear indicators
                evolved.properties[3] &= 0x7F; // Clear critical flag
            }
            
            ObserverRole::GamePlayer { level, .. } => {
                // Game interaction can "activate" objects
                evolved.properties[3] |= 0x40; // Set active flag
                
                // Higher level players reveal more properties
                if *level > 20 {
                    evolved.properties[3] |= 0x20; // Set discovered flag
                }
            }
            
            ObserverRole::EmergencyResponder { .. } => {
                // Emergency observation marks objects as checked
                evolved.properties[3] |= 0x10; // Set emergency-checked flag
            }
            
            _ => {}
        }
        
        // Update last observation time (encoded in properties)
        let time_marker = ((observer.time / 3600) % 256) as u8; // Hour marker
        evolved.properties[2] = time_marker;
        
        evolved
    }
    
    /// Get evolution rate for a specific object
    pub fn get_evolution_rate(&self, object: &ArxObject) -> f32 {
        let mut total_rate = 0.0;
        
        for rule in &self.evolution_rules {
            if rule.applicable_types.contains(&object.object_type) {
                total_rate += rule.rate;
            }
        }
        
        total_rate * self.time_scale
    }
    
    /// Check if an object needs maintenance
    pub fn needs_maintenance(&self, object: &ArxObject) -> bool {
        // Check health/condition
        if object.properties[0] < 50 {
            return true;
        }
        
        // Check critical flag
        if object.properties[3] & 0x80 != 0 {
            return true;
        }
        
        // Check accumulation levels (dust, etc.)
        if object.properties[2] > 200 {
            return true;
        }
        
        false
    }
    
    /// Calculate time until next maintenance needed
    pub fn time_to_maintenance(&self, object: &ArxObject) -> Option<u64> {
        let current_health = object.properties[0] as f32 / 255.0;
        
        if current_health < 0.2 {
            return Some(0); // Needs immediate maintenance
        }
        
        // Find applicable wear rule
        for rule in &self.evolution_rules {
            if !rule.applicable_types.contains(&object.object_type) {
                continue;
            }
            
            if let EvolutionType::Wear { wear_factor, critical_threshold } = &rule.evolution_type {
                let wear_rate = wear_factor * rule.rate * (2.0 - self.environment.maintenance_quality);
                let health_to_lose = current_health - critical_threshold;
                
                if health_to_lose > 0.0 && wear_rate > 0.0 {
                    let time_seconds = health_to_lose / wear_rate;
                    return Some((time_seconds / self.time_scale) as u64);
                }
            }
        }
        
        None
    }
}

/// History of an object's evolution
#[derive(Clone, Debug)]
pub struct EvolutionHistory {
    pub object_id: u16,
    pub snapshots: Vec<(u64, ArxObject)>,
    pub events: Vec<EvolutionEvent>,
}

/// Significant events in object evolution
#[derive(Clone, Debug)]
pub enum EvolutionEvent {
    MaintenancePerformed { time: u64, improvement: u8 },
    FailureOccurred { time: u64, failure_type: u8 },
    StateChanged { time: u64, from: u8, to: u8 },
    ThresholdCrossed { time: u64, property: u8, value: u8 },
}

impl EvolutionHistory {
    pub fn new(object_id: u16) -> Self {
        Self {
            object_id,
            snapshots: Vec::new(),
            events: Vec::new(),
        }
    }
    
    /// Add a snapshot to history
    pub fn add_snapshot(&mut self, time: u64, object: ArxObject) {
        self.snapshots.push((time, object));
        
        // Keep history limited
        if self.snapshots.len() > 100 {
            self.snapshots.remove(0);
        }
    }
    
    /// Record an event
    pub fn record_event(&mut self, event: EvolutionEvent) {
        self.events.push(event);
        
        // Keep events limited
        if self.events.len() > 50 {
            self.events.remove(0);
        }
    }
    
    /// Get state at specific time
    pub fn state_at(&self, time: u64) -> Option<ArxObject> {
        // Find closest snapshot
        let mut closest = None;
        let mut min_diff = u64::MAX;
        
        for (snap_time, object) in &self.snapshots {
            let diff = time.abs_diff(*snap_time);
            if diff < min_diff {
                min_diff = diff;
                closest = Some(*object);
            }
        }
        
        closest
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::holographic::observer::MaintenanceType;
    
    #[test]
    fn test_wear_evolution() {
        let mut evolution = TemporalEvolution::new(0, 1.0);
        
        let outlet = ArxObject::with_properties(
            1,
            object_types::OUTLET,
            1000, 2000, 1500,
            [255, 128, 0, 0], // Full health
        );
        
        // Evolve for 1 year (31536000 seconds)
        let aged_outlet = evolution.evolve(&outlet, 31536000);
        
        // Health should have decreased
        assert!(aged_outlet.properties[0] < 255);
    }
    
    #[test]
    fn test_thermal_evolution() {
        let mut evolution = TemporalEvolution::new(0, 1.0);
        evolution.environment.temperature = 25.0;
        
        let room = ArxObject::with_properties(
            1,
            object_types::ROOM,
            0, 0, 0,
            [255, properties::encode_temperature(15.0), 0, 0],
        );
        
        // Evolve for 1 hour
        let warmed_room = evolution.evolve(&room, 3600);
        
        // Temperature should have increased toward ambient
        let new_temp = properties::decode_temperature(warmed_room.properties[1]);
        assert!(new_temp > 15.0);
        assert!(new_temp < 25.0);
    }
    
    #[test]
    fn test_maintenance_check() {
        let evolution = TemporalEvolution::new(0, 1.0);
        
        let worn_outlet = ArxObject::with_properties(
            1,
            object_types::OUTLET,
            1000, 2000, 1500,
            [40, 0, 0, 0], // Low health
        );
        
        assert!(evolution.needs_maintenance(&worn_outlet));
        
        let healthy_outlet = ArxObject::with_properties(
            1,
            object_types::OUTLET,
            1000, 2000, 1500,
            [200, 0, 0, 0], // Good health
        );
        
        assert!(!evolution.needs_maintenance(&healthy_outlet));
    }
    
    #[test]
    fn test_observer_evolution() {
        let mut evolution = TemporalEvolution::new(0, 1.0);
        
        let outlet = ArxObject::with_properties(
            1,
            object_types::OUTLET,
            1000, 2000, 1500,
            [150, 0, 0, 0],
        );
        
        let observer = ObserverContext::new(
            1,
            ObserverRole::MaintenanceWorker {
                specialization: MaintenanceType::Electrical,
                access_level: 3,
                years_experience: 5,
            },
            FractalSpace::from_mm(1000, 2000, 1500),
            1000,
        );
        
        let maintained = evolution.evolve_from_observation(&outlet, &observer);
        
        // Maintenance should improve condition
        assert!(maintained.properties[0] > outlet.properties[0]);
    }
    
    #[test]
    fn test_evolution_history() {
        let mut history = EvolutionHistory::new(123);
        
        let obj1 = ArxObject::new(1, object_types::OUTLET, 0, 0, 0);
        let obj2 = ArxObject::new(1, object_types::OUTLET, 0, 0, 0);
        
        history.add_snapshot(0, obj1);
        history.add_snapshot(3600, obj2);
        
        history.record_event(EvolutionEvent::MaintenancePerformed {
            time: 1800,
            improvement: 50,
        });
        
        assert_eq!(history.snapshots.len(), 2);
        assert_eq!(history.events.len(), 1);
        
        // Should find closest snapshot
        let state = history.state_at(1800);
        assert!(state.is_some());
    }
}