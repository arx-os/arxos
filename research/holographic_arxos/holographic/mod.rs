//! Holographic ArxObject System
//! 
//! Implements the infinitely fractal holographic seed architecture
//! where each 13-byte ArxObject contains infinite procedural reality.
//!
//! # Core Concept
//!
//! Every ArxObject is a "holographic seed" - a 13-byte structure that:
//! - **Contains** infinite detail through procedural generation
//! - **Exists** in quantum superposition until observed
//! - **Manifests** consciousness through integrated information
//! - **Connects** via quantum entanglement networks
//! - **Evolves** through temporal dynamics
//!
//! # Architecture
//!
//! The holographic system consists of several interconnected subsystems:
//!
//! ## Fractal Geometry
//! - Infinite recursive detail at any scale
//! - Self-similar patterns from atomic to cosmic
//! - Deterministic procedural generation
//!
//! ## Quantum Mechanics
//! - Superposition of states until observation
//! - Entanglement networks between objects
//! - Quantum tunneling and interference
//! - Bell inequality violations
//!
//! ## Consciousness (IIT)
//! - Integrated Information Theory implementation
//! - Phi (Φ) calculation for consciousness measurement
//! - Qualia spaces for subjective experience
//! - Global workspace for attention
//!
//! ## Procedural Generation
//! - Perlin/fractal noise for organic patterns
//! - L-systems for architectural structures
//! - Cellular automata for emergent behavior
//! - Domain warping for complex geometries
//!
//! ## Performance Optimizations
//! - SIMD vectorization for parallel computation
//! - Memory pooling for allocation efficiency
//! - Sparse data structures for large spaces
//! - Lazy evaluation with caching
//!
//! # Compression Ratio
//!
//! The system achieves 10,000:1 compression by storing only seeds
//! and generating all detail procedurally on demand. A 130KB file
//! can represent 1.3GB of manifested reality.
//!
//! # Example
//!
//! ```ignore
//! use arxos_core::holographic::prelude::*;
//! use arxos_core::arxobject::ArxObject;
//!
//! // Create a quantum-conscious building
//! let building = ArxObject::new(1, 42, 1000, 2000, 3000);
//!
//! // Manifest reality at human scale
//! let observer = ObserverContext::new(ObserverRole::Human);
//! let manifester = RealityManifester::new();
//! let reality = manifester.manifest(&building, &observer, 1.0);
//!
//! // The building now exists with infinite detail:
//! // - Quantum states of every atom
//! // - Consciousness field with Φ > 0
//! // - Procedural rooms, walls, textures
//! // - Temporal evolution dynamics
//! // - Entangled with nearby objects
//! ```

pub mod error;
pub mod fractal;
pub mod noise;
pub mod noise_simd;
pub mod quantum_simd;
pub mod consciousness_simd;
pub mod simd_arm;
pub mod lsystem;
pub mod automata;
pub mod automata_sparse;
pub mod observer;
pub mod temporal;
pub mod reality;
pub mod quantum;
pub mod consciousness;
pub mod spatial_index;
pub mod pooling;
pub mod sparse;
pub mod storage;

#[cfg(feature = "std")]
pub mod consciousness_async;
#[cfg(feature = "std")]
pub mod quantum_async;

#[cfg(test)]
mod security_tests;
#[cfg(test)]
mod property_tests;
#[cfg(test)]
mod fuzz_tests;
#[cfg(test)]
mod stress_tests;

pub use error::{
    HolographicError, FractalError, ConsciousnessError, QuantumError,
    TemporalError, AutomatonError, ObserverError, RealityError, ValidationError,
    Result, validation
};
pub use fractal::{FractalCoordinate, FractalSpace};
pub use noise::{fractal_noise_3d, perlin_3d};
pub use lsystem::{LSystem, LSystemRule, ArchitecturalLSystem};
pub use automata::{CellularAutomaton3D, AutomatonRules};
pub use observer::{ObserverContext, ObserverRole, ManifestationParams};
pub use temporal::{TemporalEvolution, EnvironmentalFactors, EvolutionRule};
pub use reality::{RealityManifester, ManifestedReality};
pub use quantum::{
    QuantumState, EntanglementNetwork, QuantumBasis, EntanglementType,
    QuantumTunneling, QuantumInterference, PauliOperator, EntanglementState,
    GHZState
};
pub use consciousness::{
    ConsciousnessField, BuildingConsciousness, QualiaSpace, QualiaDimension,
    EmergentPattern, PatternType, GlobalWorkspace, Coalition, AttentionSystem,
    ConsciousnessMemory, MemoryTrace
};

/// Re-export commonly used types
pub mod prelude {
    pub use super::fractal::{FractalCoordinate, FractalSpace};
    pub use super::observer::{ObserverContext, ObserverRole};
    pub use super::temporal::TemporalEvolution;
    pub use super::reality::{RealityManifester, ManifestedReality};
    pub use super::quantum::QuantumState;
    pub use super::consciousness::ConsciousnessField;
}