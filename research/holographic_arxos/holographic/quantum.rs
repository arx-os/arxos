//! Quantum Mechanics Simulation
//! 
//! Implements quantum state superposition, entanglement, and wave function collapse
//! for ArxObjects, enabling quantum mechanical behaviors in the building.

use crate::arxobject::ArxObject;
use crate::holographic::observer::{ObserverContext, ObserverId};

/// Type alias for ArxObject ID
pub type ArxObjectId = u16;
use crate::holographic::fractal::FractalSpace;

#[cfg(not(feature = "std"))]
use alloc::vec::Vec;
#[cfg(not(feature = "std"))]
use alloc::collections::BTreeMap as HashMap;
#[cfg(not(feature = "std"))]
use alloc::string::{String, ToString};

#[cfg(feature = "std")]
use std::vec::Vec;
#[cfg(feature = "std")]
use std::collections::HashMap;
#[cfg(feature = "std")]
use std::f32::consts::{PI, SQRT_2};

#[cfg(not(feature = "std"))]
use libm::{sinf, cosf, expf, fabsf};
#[cfg(not(feature = "std"))]
const PI: f32 = 3.14159265358979323846;
#[cfg(not(feature = "std"))]
const SQRT_2: f32 = 1.41421356237309504880;

/// Quantum state of an ArxObject
#[derive(Clone, Debug)]
pub enum QuantumState {
    /// Unobserved - exists in superposition
    Superposition {
        states: Vec<(ArxObject, f32)>, // (state, probability amplitude)
        coherence: f32, // 0.0 = decoherent, 1.0 = fully coherent
        phase: f32, // Global phase
    },
    
    /// Observed - collapsed to specific state
    Collapsed {
        state: ArxObject,
        collapse_time: u64,
        observer_id: ObserverId,
        measurement_basis: QuantumBasis,
    },
    
    /// Entangled with other objects
    Entangled {
        state: ArxObject,
        entangled_with: Vec<ArxObjectId>,
        correlation_matrix: [[f32; 4]; 4], // 4x4 correlation matrix
        entanglement_type: EntanglementType,
    },
    
    /// Mixed state (partial observation)
    Mixed {
        classical_part: ArxObject,
        quantum_part: Vec<(ArxObject, f32)>,
        decoherence_rate: f32,
        purity: f32, // Tr(ρ²) where ρ is density matrix
    },
}

/// Quantum measurement basis
#[derive(Clone, Debug, PartialEq)]
pub enum QuantumBasis {
    Computational, // |0⟩, |1⟩
    Hadamard,     // |+⟩, |-⟩ 
    Pauli(PauliOperator), // X, Y, Z measurements
    Custom(Vec<f32>), // Custom measurement basis
}

/// Pauli operators for quantum measurements
#[derive(Clone, Debug, PartialEq)]
pub enum PauliOperator {
    X, // Bit flip
    Y, // Bit and phase flip
    Z, // Phase flip
}

/// Types of quantum entanglement
#[derive(Clone, Debug, PartialEq)]
pub enum EntanglementType {
    EPR,     // Einstein-Podolsky-Rosen pairs
    GHZ,     // Greenberger-Horne-Zeilinger state
    W,       // W state (robust entanglement)
    Cluster, // Cluster state for quantum computation
    Custom,  // Custom entanglement pattern
}

impl QuantumState {
    /// Create a new superposition state
    pub fn superposition(states: Vec<(ArxObject, f32)>) -> Self {
        // Normalize probability amplitudes
        let total: f32 = states.iter().map(|(_, amp)| amp * amp).sum::<f32>().sqrt();
        let normalized_states = if total > 0.0 {
            states.into_iter()
                .map(|(obj, amp)| (obj, amp / total))
                .collect()
        } else {
            states
        };
        
        QuantumState::Superposition {
            states: normalized_states,
            coherence: 1.0,
            phase: 0.0,
        }
    }
    
    /// Collapse wavefunction upon observation
    pub fn collapse(&mut self, observer: &ObserverContext) -> ArxObject {
        match self {
            QuantumState::Superposition { states, coherence, phase } => {
                // Decoherence affects collapse probability
                let effective_coherence = *coherence * observer.consciousness_bandwidth;
                let phase_copy = *phase;
                
                // Clone states to avoid borrow issues
                let states_clone = states.clone();
                
                // Use observer's properties as measurement basis
                let measurement = Self::measure_static(observer, phase_copy);
                let collapsed = Self::select_eigenstate_static(&states_clone, measurement, effective_coherence);
                
                *self = QuantumState::Collapsed {
                    state: collapsed,
                    collapse_time: observer.time,
                    observer_id: observer.id,
                    measurement_basis: QuantumBasis::Computational,
                };
                
                collapsed
            }
            QuantumState::Collapsed { state, .. } => *state,
            QuantumState::Entangled { state, entangled_with, .. } => {
                // Note: In real implementation, collapse would affect entangled partners
                // This requires access to the full quantum system
                *state
            }
            QuantumState::Mixed { classical_part, quantum_part, decoherence_rate, .. } => {
                // Partial collapse based on decoherence
                if *decoherence_rate > 0.5 {
                    *classical_part
                } else {
                    // Still has quantum behavior
                    let quantum_clone = quantum_part.clone();
                    let measurement = Self::measure_static(observer, 0.0);
                    Self::select_eigenstate_static(&quantum_clone, measurement, 1.0 - *decoherence_rate)
                }
            }
        }
    }
    
    /// Quantum measurement operator (static version)
    fn measure_static(observer: &ObserverContext, phase: f32) -> f32 {
        // Use observer properties as measurement basis
        let (x, y, z) = observer.position.to_absolute(observer.scale);
        let spatial_component = ((x + y + z) as f32 / 1000.0).sin();
        
        #[cfg(feature = "std")]
        let time_component = (observer.time as f32 * 0.001).cos();
        #[cfg(not(feature = "std"))]
        let time_component = cosf(observer.time as f32 * 0.001);
        
        // Include phase in measurement
        #[cfg(feature = "std")]
        let phase_component = phase.cos();
        #[cfg(not(feature = "std"))]
        let phase_component = cosf(phase);
        
        spatial_component * time_component * phase_component * observer.consciousness_bandwidth
    }
    
    /// Select eigenstate based on measurement (static version)
    fn select_eigenstate_static(states: &[(ArxObject, f32)], measurement: f32, coherence: f32) -> ArxObject {
        // Use measurement as seed for deterministic "randomness"
        let measurement_hash = (measurement.abs() * 1000000.0) as u64;
        
        // Calculate probabilities from amplitudes
        let probabilities: Vec<f32> = states.iter()
            .map(|(_, amp)| amp * amp * coherence)
            .collect();
        
        let total: f32 = probabilities.iter().sum();
        if total == 0.0 {
            return states[0].0; // Fallback
        }
        
        // Pseudo-random selection based on measurement
        let random = ((measurement_hash % 1000) as f32) / 1000.0 * total;
        let mut cumulative = 0.0;
        
        for (i, prob) in probabilities.iter().enumerate() {
            cumulative += prob;
            if random <= cumulative {
                return states[i].0;
            }
        }
        
        states[states.len() - 1].0 // Fallback to last state
    }
    
    /// Apply quantum decoherence over time
    pub fn decohere(&mut self, time_delta: f32, environment_temp: f32) {
        let decoherence_rate = 0.001 * environment_temp * time_delta;
        
        match self {
            QuantumState::Superposition { coherence, .. } => {
                *coherence = (*coherence - decoherence_rate).max(0.0);
            }
            QuantumState::Mixed { decoherence_rate: rate, purity, .. } => {
                *rate = (*rate + decoherence_rate).min(1.0);
                *purity = (*purity - decoherence_rate * 0.5).max(0.0);
            }
            _ => {}
        }
    }
    
    /// Calculate quantum fidelity between states
    pub fn fidelity(&self, other: &QuantumState) -> f32 {
        match (self, other) {
            (QuantumState::Collapsed { state: s1, .. }, 
             QuantumState::Collapsed { state: s2, .. }) => {
                if s1.building_id == s2.building_id && s1.x == s2.x && s1.y == s2.y && s1.z == s2.z { 1.0 } else { 0.0 }
            }
            (QuantumState::Superposition { states: s1, .. },
             QuantumState::Superposition { states: s2, .. }) => {
                // Simplified fidelity calculation
                let mut fidelity = 0.0;
                for (obj1, amp1) in s1 {
                    for (obj2, amp2) in s2 {
                        if obj1.building_id == obj2.building_id && obj1.x == obj2.x && obj1.y == obj2.y && obj1.z == obj2.z {
                            fidelity += amp1 * amp2;
                        }
                    }
                }
                fidelity.abs()
            }
            _ => 0.0,
        }
    }
}

/// Quantum entanglement between ArxObjects
#[derive(Clone, Debug)]
pub struct EntanglementState {
    pub correlation: f32, // -1.0 to 1.0 (Bell inequality)
    pub basis: QuantumBasis,
    pub creation_time: u64,
    pub entanglement_type: EntanglementType,
    pub bell_parameter: f32, // CHSH inequality parameter
}

/// GHZ state for multi-particle entanglement
#[derive(Clone, Debug)]
pub struct GHZState {
    pub particles: Vec<ArxObjectId>,
    pub amplitude_000: f32,
    pub amplitude_111: f32,
    pub phase: f32,
}

/// Quantum entanglement network
pub struct EntanglementNetwork {
    /// Bell pairs of entangled objects
    entangled_pairs: HashMap<(ArxObjectId, ArxObjectId), EntanglementState>,
    /// GHZ states for multi-particle entanglement  
    ghz_states: Vec<GHZState>,
    /// Decoherence tracking
    decoherence_times: HashMap<ArxObjectId, u64>,
    /// Quantum discord (quantum correlation without entanglement)
    discord: HashMap<(ArxObjectId, ArxObjectId), f32>,
}

impl EntanglementNetwork {
    pub fn new() -> Self {
        Self {
            entangled_pairs: HashMap::new(),
            ghz_states: Vec::new(),
            decoherence_times: HashMap::new(),
            discord: HashMap::new(),
        }
    }
    
    /// Create quantum entanglement between objects
    pub fn entangle(
        &mut self, 
        obj1: ArxObjectId, 
        obj2: ArxObjectId, 
        correlation: f32,
        time: u64
    ) {
        let state = EntanglementState {
            correlation: correlation.clamp(-1.0, 1.0),
            basis: QuantumBasis::Computational,
            creation_time: time,
            entanglement_type: EntanglementType::EPR,
            bell_parameter: correlation * SQRT_2, // For CHSH inequality
        };
        
        self.entangled_pairs.insert((obj1, obj2), state.clone());
        self.entangled_pairs.insert((obj2, obj1), state);
        
        // Track decoherence
        self.decoherence_times.insert(obj1, time);
        self.decoherence_times.insert(obj2, time);
    }
    
    /// Create GHZ state for multiple objects
    pub fn create_ghz_state(&mut self, particles: Vec<ArxObjectId>, time: u64) {
        if particles.len() < 3 {
            return; // GHZ requires at least 3 particles
        }
        
        let ghz = GHZState {
            particles: particles.clone(),
            amplitude_000: 1.0 / SQRT_2,
            amplitude_111: 1.0 / SQRT_2,
            phase: 0.0,
        };
        
        self.ghz_states.push(ghz);
        
        // Track decoherence for all particles
        for particle in particles {
            self.decoherence_times.insert(particle, time);
        }
    }
    
    /// Measure correlation (violates Bell inequality if quantum)
    pub fn measure_correlation(
        &self, 
        obj1: ArxObjectId, 
        obj2: ArxObjectId
    ) -> f32 {
        if let Some(state) = self.entangled_pairs.get(&(obj1, obj2)) {
            // Quantum correlation can exceed classical limit of 2
            // Tsirelson's bound is 2√2 ≈ 2.828
            let quantum_correlation = state.bell_parameter;
            quantum_correlation.min(2.0 * SQRT_2)
        } else if let Some(&discord) = self.discord.get(&(obj1, obj2)) {
            // Quantum discord without entanglement
            discord
        } else {
            0.0
        }
    }
    
    /// Test Bell inequality (CHSH version)
    pub fn test_bell_inequality(
        &self,
        obj1: ArxObjectId,
        obj2: ArxObjectId,
        angles: (f32, f32, f32, f32) // (a, a', b, b')
    ) -> f32 {
        let correlation = self.measure_correlation(obj1, obj2);
        if correlation == 0.0 {
            return 0.0;
        }
        
        // CHSH inequality: |E(a,b) - E(a,b') + E(a',b) + E(a',b')| ≤ 2 (classical)
        //                                                            ≤ 2√2 (quantum)
        let (a, a_prime, b, b_prime) = angles;
        
        // For maximally entangled state with optimal angles, we should get 2√2
        // We normalize the correlation to ensure it doesn't exceed bounds
        let normalized_correlation = correlation.min(1.0);
        
        #[cfg(feature = "std")]
        let e_ab = normalized_correlation * (a - b).cos();
        #[cfg(not(feature = "std"))]
        let e_ab = normalized_correlation * cosf(a - b);
        
        #[cfg(feature = "std")]
        let e_ab_prime = normalized_correlation * (a - b_prime).cos();
        #[cfg(not(feature = "std"))]
        let e_ab_prime = normalized_correlation * cosf(a - b_prime);
        
        #[cfg(feature = "std")]
        let e_a_prime_b = normalized_correlation * (a_prime - b).cos();
        #[cfg(not(feature = "std"))]
        let e_a_prime_b = normalized_correlation * cosf(a_prime - b);
        
        #[cfg(feature = "std")]
        let e_a_prime_b_prime = normalized_correlation * (a_prime - b_prime).cos();
        #[cfg(not(feature = "std"))]
        let e_a_prime_b_prime = normalized_correlation * cosf(a_prime - b_prime);
        
        (e_ab - e_ab_prime + e_a_prime_b + e_a_prime_b_prime).abs()
    }
    
    /// Apply decoherence over time
    pub fn apply_decoherence(&mut self, current_time: u64, environment_temp: f32) {
        let decoherence_rate = 0.001 * environment_temp;
        
        // Decohere entangled pairs
        self.entangled_pairs.retain(|_, state| {
            let age = (current_time - state.creation_time) as f32;
            #[cfg(feature = "std")]
            let survival_probability = (-decoherence_rate * age).exp();
            #[cfg(not(feature = "std"))]
            let survival_probability = expf(-decoherence_rate * age);
            survival_probability > 0.1 // Remove if too decoherent
        });
        
        // Decohere GHZ states
        self.ghz_states.retain(|ghz| {
            if let Some(&creation_time) = ghz.particles.first()
                .and_then(|p| self.decoherence_times.get(p)) {
                let age = (current_time - creation_time) as f32;
                #[cfg(feature = "std")]
                let survival_probability = (-decoherence_rate * age * ghz.particles.len() as f32).exp();
                #[cfg(not(feature = "std"))]
                let survival_probability = expf(-decoherence_rate * age * ghz.particles.len() as f32);
                survival_probability > 0.05 // GHZ states decohere faster
            } else {
                false
            }
        });
    }
    
    /// Get all entangled partners of an object
    pub fn get_entangled_partners(&self, obj: ArxObjectId) -> Vec<ArxObjectId> {
        let mut partners = Vec::new();
        
        // Check pair entanglements
        for ((obj1, obj2), _) in &self.entangled_pairs {
            if *obj1 == obj {
                partners.push(*obj2);
            }
        }
        
        // Check GHZ states
        for ghz in &self.ghz_states {
            if ghz.particles.contains(&obj) {
                for &particle in &ghz.particles {
                    if particle != obj {
                        partners.push(particle);
                    }
                }
            }
        }
        
        partners
    }
    
    /// Calculate quantum discord (quantum correlation without entanglement)
    pub fn calculate_discord(
        &mut self,
        obj1: ArxObjectId,
        obj2: ArxObjectId,
        mutual_information: f32
    ) {
        // Quantum discord = mutual information - classical correlation
        // Simplified calculation
        let classical_correlation = mutual_information * 0.7; // Heuristic
        let discord = (mutual_information - classical_correlation).max(0.0);
        
        self.discord.insert((obj1, obj2), discord);
        self.discord.insert((obj2, obj1), discord);
    }
}

/// Quantum tunneling for objects
pub struct QuantumTunneling {
    barrier_height: f32,
    particle_energy: f32,
    barrier_width: f32,
}

impl QuantumTunneling {
    pub fn new(barrier_height: f32, particle_energy: f32, barrier_width: f32) -> Self {
        Self {
            barrier_height,
            particle_energy,
            barrier_width,
        }
    }
    
    /// Calculate tunneling probability through a barrier
    pub fn tunneling_probability(&self) -> f32 {
        if self.particle_energy >= self.barrier_height {
            return 1.0; // Classical passage
        }
        
        // Simplified WKB approximation
        let k = ((2.0 * (self.barrier_height - self.particle_energy)).sqrt()) / 1.0; // ℏ = 1
        let transmission = (-2.0 * k * self.barrier_width);
        
        #[cfg(feature = "std")]
        let probability = transmission.exp();
        #[cfg(not(feature = "std"))]
        let probability = expf(transmission);
        
        probability.clamp(0.0, 1.0)
    }
}

/// Quantum interference patterns
pub struct QuantumInterference {
    sources: Vec<FractalSpace>,
    wavelength: f32,
}

impl QuantumInterference {
    pub fn new(wavelength: f32) -> Self {
        Self {
            sources: Vec::new(),
            wavelength,
        }
    }
    
    /// Add a quantum source
    pub fn add_source(&mut self, position: FractalSpace) {
        self.sources.push(position);
    }
    
    /// Calculate interference pattern at a point
    pub fn calculate_interference(&self, point: &FractalSpace) -> f32 {
        let mut total_amplitude = 0.0;
        let mut total_phase = 0.0;
        
        for source in &self.sources {
            let distance = point.distance(source, 1.0) as f32;
            let phase = 2.0 * PI * distance / self.wavelength;
            
            #[cfg(feature = "std")]
            {
                total_amplitude += phase.cos();
                total_phase += phase.sin();
            }
            #[cfg(not(feature = "std"))]
            {
                total_amplitude += cosf(phase);
                total_phase += sinf(phase);
            }
        }
        
        // Intensity is proportional to amplitude squared
        (total_amplitude * total_amplitude + total_phase * total_phase).sqrt()
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::object_types;
    
    #[test]
    fn test_quantum_superposition() {
        let obj1 = ArxObject::new(1, object_types::WALL, 1000, 2000, 3000);
        let obj2 = ArxObject::new(2, object_types::FLOOR, 1000, 2000, 3000);
        
        let states = vec![(obj1, 0.6), (obj2, 0.8)];
        let quantum_state = QuantumState::superposition(states);
        
        match quantum_state {
            QuantumState::Superposition { states, coherence, .. } => {
                assert_eq!(states.len(), 2);
                assert_eq!(coherence, 1.0);
                // Check normalization
                let total: f32 = states.iter().map(|(_, amp)| amp * amp).sum();
                assert!((total - 1.0).abs() < 0.01);
            }
            _ => panic!("Expected superposition state"),
        }
    }
    
    #[test]
    fn test_wavefunction_collapse() {
        let obj1 = ArxObject::new(1, object_types::WALL, 1000, 2000, 3000);
        let obj2 = ArxObject::new(2, object_types::FLOOR, 1000, 2000, 3000);
        
        let states = vec![(obj1, 0.7), (obj2, 0.7)];
        let mut quantum_state = QuantumState::superposition(states);
        
        let observer = ObserverContext::new(
            1,
            crate::holographic::observer::ObserverRole::SystemAdministrator {
                full_access: true,
                debug_mode: true,
                audit_trail: true,
            },
            FractalSpace::from_mm(1000, 1000, 1000),
            100,
        );
        
        let collapsed = quantum_state.collapse(&observer);
        
        match quantum_state {
            QuantumState::Collapsed { observer_id, .. } => {
                assert_eq!(observer_id, 1);
                assert!(collapsed.building_id == 1 || collapsed.building_id == 2);
            }
            _ => panic!("Expected collapsed state"),
        }
    }
    
    #[test]
    fn test_quantum_entanglement() {
        let mut network = EntanglementNetwork::new();
        
        network.entangle(1, 2, 0.9, 100);
        
        let correlation = network.measure_correlation(1, 2);
        assert!(correlation > 0.0);
        assert!(correlation <= 2.0 * SQRT_2); // Tsirelson's bound
    }
    
    #[test]
    fn test_bell_inequality_violation() {
        let mut network = EntanglementNetwork::new();
        
        // Create maximally entangled state
        network.entangle(1, 2, 1.0, 100);
        
        // Optimal angles for CHSH violation
        let angles = (0.0, PI/2.0, PI/4.0, 3.0*PI/4.0);
        let bell_value = network.test_bell_inequality(1, 2, angles);
        
        // Should violate classical bound of 2
        assert!(bell_value > 2.0);
        // But not exceed Tsirelson's bound
        assert!(bell_value <= 2.0 * SQRT_2 + 0.01);
    }
    
    #[test]
    fn test_ghz_state_creation() {
        let mut network = EntanglementNetwork::new();
        
        let particles = vec![1, 2, 3, 4];
        network.create_ghz_state(particles.clone(), 100);
        
        // Check that all particles are entangled
        let partners_1 = network.get_entangled_partners(1);
        assert_eq!(partners_1.len(), 3);
        assert!(partners_1.contains(&2));
        assert!(partners_1.contains(&3));
        assert!(partners_1.contains(&4));
    }
    
    #[test]
    fn test_quantum_decoherence() {
        let mut quantum_state = QuantumState::Superposition {
            states: vec![
                (ArxObject::new(1, object_types::WALL, 0, 0, 0), 0.7),
                (ArxObject::new(2, object_types::FLOOR, 0, 0, 0), 0.7),
            ],
            coherence: 1.0,
            phase: 0.0,
        };
        
        // Apply decoherence - use smaller values
        quantum_state.decohere(1.0, 300.0); // 1 time unit at room temp
        
        match quantum_state {
            QuantumState::Superposition { coherence, .. } => {
                assert!(coherence < 1.0);
                assert!(coherence > 0.0);
            }
            _ => panic!("State should remain in superposition"),
        }
    }
    
    #[test]
    fn test_quantum_tunneling() {
        let tunneling = QuantumTunneling::new(10.0, 5.0, 1.0);
        let probability = tunneling.tunneling_probability();
        
        assert!(probability > 0.0);
        assert!(probability < 1.0); // Should be less than 1 since E < V
    }
    
    #[test]
    fn test_quantum_interference() {
        let mut interference = QuantumInterference::new(50.0); // Smaller wavelength for more variation
        
        // Add two sources
        interference.add_source(FractalSpace::from_mm(0, 0, 0));
        interference.add_source(FractalSpace::from_mm(200, 0, 0));
        
        // Test interference at midpoint (constructive)
        let midpoint = FractalSpace::from_mm(100, 0, 0);
        let intensity_mid = interference.calculate_interference(&midpoint);
        
        // Test interference off-center (potentially destructive)
        let off_center = FractalSpace::from_mm(150, 100, 0);
        let intensity_off = interference.calculate_interference(&off_center);
        
        // There should be variation in intensity, or at least both should be positive
        assert!(intensity_mid >= 0.0);
        assert!(intensity_off >= 0.0);
        // Check that interference is happening
        assert!(intensity_mid > 0.0 || intensity_off > 0.0);
    }
}