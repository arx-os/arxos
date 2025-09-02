//! Quantum State Persistence
//! 
//! Stores and retrieves quantum states with:
//! - Superposition amplitude arrays
//! - Entanglement relationships
//! - Bell inequality measurements

use crate::holographic::quantum::{QuantumState, ArxObjectId, QuantumBasis, EntanglementType};
use crate::holographic::error::{Result, HolographicError};
use super::connection_pool::ConnectionPool;
use rusqlite::params;

/// Store for quantum state persistence
pub struct QuantumStateStore {
    pool: ConnectionPool,
}

impl QuantumStateStore {
    /// Create a new quantum state store
    pub fn new(pool: ConnectionPool) -> Self {
        Self { pool }
    }
    
    /// Save a quantum state for an ArxObject
    pub fn save_state(&self, arxobject_id: ArxObjectId, state: &QuantumState) -> Result<i64> {
        let conn = self.pool.get()?;
        
        match state {
            QuantumState::Superposition { amplitudes, basis } => {
                // Serialize amplitudes
                let amp_bytes = Self::serialize_amplitudes(amplitudes)?;
                
                let mut stmt = conn.prepare(
                    "INSERT INTO quantum_states 
                     (arxobject_id, state_type, amplitudes, basis) 
                     VALUES (?1, 'superposition', ?2, ?3)"
                )?;
                
                stmt.execute(params![
                    arxobject_id as i64,
                    amp_bytes,
                    Self::basis_to_string(basis),
                ])?;
            }
            QuantumState::Collapsed { state: s, basis } => {
                let mut stmt = conn.prepare(
                    "INSERT INTO quantum_states 
                     (arxobject_id, state_type, amplitudes, basis) 
                     VALUES (?1, 'collapsed', ?2, ?3)"
                )?;
                
                // Store collapsed state as single amplitude
                let amp_bytes = vec![*s];
                
                stmt.execute(params![
                    arxobject_id as i64,
                    amp_bytes,
                    Self::basis_to_string(basis),
                ])?;
            }
            QuantumState::Entangled { state: s, entangled_with, correlation, basis, .. } => {
                // First save the entangled state
                let mut stmt = conn.prepare(
                    "INSERT INTO quantum_states 
                     (arxobject_id, state_type, amplitudes, basis, correlation) 
                     VALUES (?1, 'entangled', ?2, ?3, ?4)"
                )?;
                
                let amp_bytes = vec![*s];
                
                stmt.execute(params![
                    arxobject_id as i64,
                    amp_bytes,
                    Self::basis_to_string(basis),
                    correlation,
                ])?;
                
                let state_id = conn.last_insert_rowid();
                
                // Save entanglement relationship
                if let Some(other_id) = entangled_with {
                    self.save_entanglement(state_id, *other_id as i64, *correlation)?;
                }
                
                return Ok(state_id);
            }
        }
        
        Ok(conn.last_insert_rowid())
    }
    
    /// Load quantum state for an ArxObject
    pub fn load_state(&self, arxobject_id: ArxObjectId) -> Result<Option<QuantumState>> {
        let conn = self.pool.get()?;
        
        let mut stmt = conn.prepare(
            "SELECT id, state_type, amplitudes, basis, entangled_with, correlation 
             FROM quantum_states 
             WHERE arxobject_id = ?1 
             ORDER BY created_at DESC 
             LIMIT 1"
        )?;
        
        let result = stmt.query_row(params![arxobject_id as i64], |row| {
            let state_type: String = row.get(1)?;
            let amp_bytes: Vec<u8> = row.get(2)?;
            let basis_str: String = row.get(3)?;
            let entangled_with: Option<i64> = row.get(4)?;
            let correlation: Option<f32> = row.get(5)?;
            
            let basis = Self::string_to_basis(&basis_str);
            
            let state = match state_type.as_str() {
                "superposition" => {
                    let amplitudes = Self::deserialize_amplitudes(&amp_bytes)?;
                    QuantumState::Superposition { amplitudes, basis }
                }
                "collapsed" => {
                    let state = amp_bytes.first().copied().unwrap_or(0);
                    QuantumState::Collapsed { state, basis }
                }
                "entangled" => {
                    let state = amp_bytes.first().copied().unwrap_or(0);
                    QuantumState::Entangled {
                        state,
                        entangled_with: entangled_with.map(|id| id as ArxObjectId),
                        correlation: correlation.unwrap_or(0.0),
                        basis,
                        entanglement_type: EntanglementType::EPR,
                        bell_parameter: 2.0, // Would be calculated
                    }
                }
                _ => {
                    return Err(rusqlite::Error::InvalidQuery);
                }
            };
            
            Ok(state)
        });
        
        match result {
            Ok(state) => Ok(Some(state)),
            Err(rusqlite::Error::QueryReturnedNoRows) => Ok(None),
            Err(e) => Err(HolographicError::InvalidInput(format!("Query error: {}", e))),
        }
    }
    
    /// Save entanglement relationship
    pub fn save_entanglement(&self, state1_id: i64, state2_id: i64, correlation: f32) -> Result<()> {
        let conn = self.pool.get()?;
        
        // Ensure state1_id < state2_id for uniqueness
        let (s1, s2) = if state1_id < state2_id {
            (state1_id, state2_id)
        } else {
            (state2_id, state1_id)
        };
        
        conn.execute(
            "INSERT OR REPLACE INTO entanglement_network 
             (state1_id, state2_id, correlation) 
             VALUES (?1, ?2, ?3)",
            params![s1, s2, correlation],
        )?;
        
        Ok(())
    }
    
    /// Get entangled partners for a quantum state
    pub fn get_entangled_partners(&self, state_id: i64) -> Result<Vec<(i64, f32)>> {
        let conn = self.pool.get()?;
        
        let mut stmt = conn.prepare(
            "SELECT state2_id, correlation FROM entanglement_network WHERE state1_id = ?1
             UNION
             SELECT state1_id, correlation FROM entanglement_network WHERE state2_id = ?1"
        )?;
        
        let partners = stmt.query_map(params![state_id], |row| {
            let partner_id: i64 = row.get(0)?;
            let correlation: f32 = row.get(1)?;
            Ok((partner_id, correlation))
        })?
        .collect::<Result<Vec<_>, _>>()
        .map_err(|e| HolographicError::InvalidInput(format!("Query error: {}", e)))?;
        
        Ok(partners)
    }
    
    /// Calculate Bell inequality violations for all entangled pairs
    pub fn calculate_bell_violations(&self) -> Result<Vec<(i64, i64, f32)>> {
        let conn = self.pool.get()?;
        
        let mut stmt = conn.prepare(
            "SELECT state1_id, state2_id, correlation 
             FROM entanglement_network 
             WHERE ABS(correlation) > 0.7"
        )?;
        
        let violations = stmt.query_map([], |row| {
            let state1: i64 = row.get(0)?;
            let state2: i64 = row.get(1)?;
            let correlation: f32 = row.get(2)?;
            
            // Simplified Bell parameter calculation
            let bell = 2.0 * correlation.abs().sqrt();
            let violation = (bell - 2.0).abs();
            
            Ok((state1, state2, violation))
        })?
        .collect::<Result<Vec<_>, _>>()
        .map_err(|e| HolographicError::InvalidInput(format!("Query error: {}", e)))?;
        
        Ok(violations)
    }
    
    /// Serialize amplitude array to bytes
    fn serialize_amplitudes(amplitudes: &[f32]) -> Result<Vec<u8>> {
        let mut bytes = Vec::with_capacity(amplitudes.len() * 4);
        for &amp in amplitudes {
            bytes.extend_from_slice(&amp.to_le_bytes());
        }
        Ok(bytes)
    }
    
    /// Deserialize amplitude array from bytes
    fn deserialize_amplitudes(bytes: &[u8]) -> rusqlite::Result<Vec<f32>> {
        let mut amplitudes = Vec::with_capacity(bytes.len() / 4);
        for chunk in bytes.chunks_exact(4) {
            let mut arr = [0u8; 4];
            arr.copy_from_slice(chunk);
            amplitudes.push(f32::from_le_bytes(arr));
        }
        Ok(amplitudes)
    }
    
    /// Convert basis enum to string
    fn basis_to_string(basis: &QuantumBasis) -> &'static str {
        match basis {
            QuantumBasis::Computational => "computational",
            QuantumBasis::Hadamard => "hadamard",
            QuantumBasis::PauliX => "pauli_x",
            QuantumBasis::PauliY => "pauli_y",
            QuantumBasis::PauliZ => "pauli_z",
        }
    }
    
    /// Convert string to basis enum
    fn string_to_basis(s: &str) -> QuantumBasis {
        match s {
            "hadamard" => QuantumBasis::Hadamard,
            "pauli_x" => QuantumBasis::PauliX,
            "pauli_y" => QuantumBasis::PauliY,
            "pauli_z" => QuantumBasis::PauliZ,
            _ => QuantumBasis::Computational,
        }
    }
}