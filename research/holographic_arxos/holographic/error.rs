//! Error types for the Holographic ArxObject System
//!
//! Comprehensive error handling for security, validation, and resource management.

use thiserror::Error;

// Re-export for convenience
pub type Result<T> = std::result::Result<T, HolographicError>;

/// Maximum allowed fractal depth to prevent integer overflow
pub const MAX_FRACTAL_DEPTH: i8 = 20;

/// Maximum conscious objects to prevent memory exhaustion
pub const MAX_CONSCIOUS_OBJECTS: usize = 10_000;

/// Maximum grid dimension for cellular automata
pub const MAX_GRID_DIMENSION: usize = 1000;

/// Maximum observation history size
pub const MAX_OBSERVATION_HISTORY: usize = 1000;

/// Maximum cache size for temporal evolution
pub const MAX_EVOLUTION_CACHE: usize = 1000;

/// Maximum entangled objects in quantum system
pub const MAX_ENTANGLED_OBJECTS: usize = 1000;

/// Main error type for the holographic system
#[derive(Debug, Error)]
pub enum HolographicError {
    #[error("Fractal error: {0}")]
    Fractal(#[from] FractalError),
    
    #[error("Consciousness error: {0}")]
    Consciousness(#[from] ConsciousnessError),
    
    #[error("Quantum error: {0}")]
    Quantum(#[from] QuantumError),
    
    #[error("Temporal error: {0}")]
    Temporal(#[from] TemporalError),
    
    #[error("Automaton error: {0}")]
    Automaton(#[from] AutomatonError),
    
    #[error("Observer error: {0}")]
    Observer(#[from] ObserverError),
    
    #[error("Reality manifestation error: {0}")]
    Reality(#[from] RealityError),
    
    #[error("Validation error: {0}")]
    Validation(#[from] ValidationError),
    
    #[error("Resource exhausted: {0}")]
    ResourceExhausted(String),
    
    #[error("Invalid input: {0}")]
    InvalidInput(String),
    
    #[cfg(feature = "std")]
    #[error("Database error: {0}")]
    Database(String),
}

// Add From implementation for rusqlite::Error when std feature is enabled
#[cfg(feature = "std")]
impl From<rusqlite::Error> for HolographicError {
    fn from(err: rusqlite::Error) -> Self {
        HolographicError::Database(err.to_string())
    }
}

/// Fractal coordinate system errors
#[derive(Debug, Error)]
pub enum FractalError {
    #[error("Depth {0} exceeds maximum depth {}", MAX_FRACTAL_DEPTH)]
    DepthOverflow(i8),
    
    #[error("Coordinate out of bounds: ({x}, {y}, {z})")]
    CoordinateOutOfBounds { x: u16, y: u16, z: u16 },
    
    #[error("Integer overflow in scale calculation")]
    ScaleOverflow,
    
    #[error("Division by zero in voxel calculation")]
    DivisionByZero,
    
    #[error("Invalid sub-position: {0} (must be 0.0-1.0)")]
    InvalidSubPosition(f32),
}

/// Consciousness field errors
#[derive(Debug, Error)]
pub enum ConsciousnessError {
    #[error("Too many conscious objects: {count} (max: {})", MAX_CONSCIOUS_OBJECTS)]
    TooManyObjects { count: usize },
    
    #[error("Phi calculation failed: {reason}")]
    PhiCalculationError { reason: String },
    
    #[error("Invalid consciousness field: phi={phi}")]
    InvalidField { phi: f32 },
    
    #[error("Memory consolidation failed")]
    MemoryConsolidationError,
    
    #[error("Pattern detection failed")]
    PatternDetectionError,
}

/// Quantum mechanics errors
#[derive(Debug, Error)]
pub enum QuantumError {
    #[error("Invalid superposition: probabilities sum to {0}, expected 1.0")]
    InvalidSuperposition(f32),
    
    #[error("Entanglement limit exceeded: {count} (max: {})", MAX_ENTANGLED_OBJECTS)]
    TooManyEntanglements { count: usize },
    
    #[error("Wave function collapse failed")]
    CollapseFailed,
    
    #[error("Invalid quantum state")]
    InvalidState,
    
    #[error("Decoherence rate out of bounds: {0}")]
    InvalidDecoherence(f32),
}

/// Temporal evolution errors
#[derive(Debug, Error)]
pub enum TemporalError {
    #[error("Evolution cache overflow: {size} (max: {})", MAX_EVOLUTION_CACHE)]
    CacheOverflow { size: usize },
    
    #[error("Invalid time delta: {0}")]
    InvalidTimeDelta(f32),
    
    #[error("Evolution rule conflict")]
    RuleConflict,
    
    #[error("State transition failed")]
    TransitionFailed,
}

/// Cellular automaton errors
#[derive(Debug, Error)]
pub enum AutomatonError {
    #[error("Grid dimension too large: {dim} (max: {})", MAX_GRID_DIMENSION)]
    DimensionTooLarge { dim: usize },
    
    #[error("Zero dimension not allowed")]
    ZeroDimension,
    
    #[error("Invalid cell state")]
    InvalidCellState,
    
    #[error("Grid allocation failed: {width}x{height}x{depth}")]
    AllocationFailed { width: usize, height: usize, depth: usize },
}

/// Observer system errors
#[derive(Debug, Error)]
pub enum ObserverError {
    #[error("Observation history overflow: {size} (max: {})", MAX_OBSERVATION_HISTORY)]
    HistoryOverflow { size: usize },
    
    #[error("Invalid observer role")]
    InvalidRole,
    
    #[error("Access denied for role")]
    AccessDenied,
    
    #[error("Invalid consciousness bandwidth: {0}")]
    InvalidBandwidth(f32),
}

/// Reality manifestation errors
#[derive(Debug, Error)]
pub enum RealityError {
    #[error("Manifestation failed: {reason}")]
    ManifestationFailed { reason: String },
    
    #[error("Invalid geometry")]
    InvalidGeometry,
    
    #[error("System generation failed")]
    SystemGenerationFailed,
}

/// Input validation errors
#[derive(Debug, Error)]
pub enum ValidationError {
    #[error("Value {value} out of range [{min}, {max}]")]
    OutOfRange { value: f64, min: f64, max: f64 },
    
    #[error("Invalid dimension: {0}")]
    InvalidDimension(String),
    
    #[error("NaN or infinite value encountered")]
    NotFinite,
    
    #[error("Negative value not allowed: {0}")]
    NegativeValue(f64),
}

/// Validation utilities
pub mod validation {
    use super::*;
    
    /// Validate that a value is finite (not NaN or infinite)
    pub fn validate_finite(value: f32, name: &str) -> Result<()> {
        if !value.is_finite() {
            return Err(ValidationError::NotFinite.into());
        }
        Ok(())
    }
    
    /// Validate that a value is within range
    pub fn validate_range<T: PartialOrd + Into<f64> + Copy>(
        value: T, 
        min: T, 
        max: T, 
        name: &str
    ) -> Result<()> {
        if value < min || value > max {
            return Err(ValidationError::OutOfRange {
                value: value.into(),
                min: min.into(),
                max: max.into(),
            }.into());
        }
        Ok(())
    }
    
    /// Validate grid dimensions
    pub fn validate_grid_dimensions(
        width: usize, 
        height: usize, 
        depth: usize
    ) -> Result<()> {
        if width == 0 || height == 0 || depth == 0 {
            return Err(AutomatonError::ZeroDimension.into());
        }
        
        if width > MAX_GRID_DIMENSION {
            return Err(AutomatonError::DimensionTooLarge { dim: width }.into());
        }
        if height > MAX_GRID_DIMENSION {
            return Err(AutomatonError::DimensionTooLarge { dim: height }.into());
        }
        if depth > MAX_GRID_DIMENSION {
            return Err(AutomatonError::DimensionTooLarge { dim: depth }.into());
        }
        
        // Check for allocation overflow
        let total_cells = width.saturating_mul(height).saturating_mul(depth);
        if total_cells > MAX_GRID_DIMENSION * MAX_GRID_DIMENSION * MAX_GRID_DIMENSION {
            return Err(AutomatonError::AllocationFailed { width, height, depth }.into());
        }
        
        Ok(())
    }
    
    /// Validate fractal depth
    pub fn validate_depth(depth: i8) -> Result<()> {
        if depth.abs() > MAX_FRACTAL_DEPTH {
            return Err(FractalError::DepthOverflow(depth).into());
        }
        Ok(())
    }
    
    /// Validate probability (0.0 to 1.0)
    pub fn validate_probability(prob: f32, name: &str) -> Result<()> {
        validate_finite(prob, name)?;
        validate_range(prob, 0.0, 1.0, name)?;
        Ok(())
    }
    
    /// Validate collection size limit
    pub fn validate_collection_size<T>(
        collection: &[T], 
        max_size: usize, 
        name: &str
    ) -> Result<()> {
        if collection.len() > max_size {
            return Err(HolographicError::ResourceExhausted(
                format!("{} size {} exceeds maximum {}", name, collection.len(), max_size)
            ));
        }
        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use super::validation::*;
    
    #[test]
    fn test_validate_finite() {
        assert!(validate_finite(1.0, "test").is_ok());
        assert!(validate_finite(f32::NAN, "test").is_err());
        assert!(validate_finite(f32::INFINITY, "test").is_err());
    }
    
    #[test]
    fn test_validate_range() {
        assert!(validate_range(5, 0, 10, "test").is_ok());
        assert!(validate_range(11, 0, 10, "test").is_err());
        assert!(validate_range(-1, 0, 10, "test").is_err());
    }
    
    #[test]
    fn test_validate_grid_dimensions() {
        assert!(validate_grid_dimensions(10, 10, 10).is_ok());
        assert!(validate_grid_dimensions(0, 10, 10).is_err());
        assert!(validate_grid_dimensions(10000, 10, 10).is_err());
    }
    
    #[test]
    fn test_validate_depth() {
        assert!(validate_depth(10).is_ok());
        assert!(validate_depth(-10).is_ok());
        assert!(validate_depth(21).is_err());
        assert!(validate_depth(-21).is_err());
    }
    
    #[test]
    fn test_validate_probability() {
        assert!(validate_probability(0.5, "test").is_ok());
        assert!(validate_probability(0.0, "test").is_ok());
        assert!(validate_probability(1.0, "test").is_ok());
        assert!(validate_probability(1.1, "test").is_err());
        assert!(validate_probability(-0.1, "test").is_err());
    }
}