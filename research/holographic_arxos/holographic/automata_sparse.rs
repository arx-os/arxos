//! Sparse Cellular Automata Implementation
//! 
//! Memory-efficient cellular automata using sparse grids

use std::collections::{HashMap, HashSet};
use crate::holographic::sparse::SparseGrid3D;
use crate::holographic::automata::{AutomatonRules, CellState, NeighborhoodType};
use crate::holographic::error::Result;
use crate::arxobject::{ArxObject, object_types};

/// Sparse 3D cellular automaton
pub struct SparseCellularAutomaton3D {
    rules: AutomatonRules,
    grid: SparseGrid3D<CellState>,
    generation: u64,
    seed: u64,
    active_cells: HashSet<(usize, usize, usize)>,
}

impl SparseCellularAutomaton3D {
    /// Create new sparse automaton
    pub fn new(width: usize, height: usize, depth: usize, rules: AutomatonRules, seed: u64) -> Result<Self> {
        Ok(Self {
            rules,
            grid: SparseGrid3D::new(width, height, depth),
            generation: 0,
            seed,
            active_cells: HashSet::new(),
        })
    }
    
    /// Set a cell and track as active
    pub fn set_cell(&mut self, x: usize, y: usize, z: usize, state: CellState) -> Result<()> {
        self.grid.set(x, y, z, state)?;
        if state != CellState::Dead {
            self.active_cells.insert((x, y, z));
            // Also track neighbors as potentially active
            self.track_neighbors(x, y, z);
        } else {
            self.active_cells.remove(&(x, y, z));
        }
        Ok(())
    }
    
    /// Track neighbors of active cells
    fn track_neighbors(&mut self, x: usize, y: usize, z: usize) {
        let (width, height, depth) = self.grid.dimensions();
        
        match self.rules.neighborhood {
            NeighborhoodType::VonNeumann => {
                // 6 face neighbors
                let neighbors = [
                    (x.wrapping_sub(1), y, z),
                    (x + 1, y, z),
                    (x, y.wrapping_sub(1), z),
                    (x, y + 1, z),
                    (x, y, z.wrapping_sub(1)),
                    (x, y, z + 1),
                ];
                
                for (nx, ny, nz) in neighbors {
                    if nx < width && ny < height && nz < depth {
                        self.active_cells.insert((nx, ny, nz));
                    }
                }
            }
            NeighborhoodType::Moore => {
                // 26 neighbors (all adjacent cells)
                for dx in -1i32..=1 {
                    for dy in -1i32..=1 {
                        for dz in -1i32..=1 {
                            if dx == 0 && dy == 0 && dz == 0 {
                                continue;
                            }
                            
                            let nx = (x as i32 + dx) as usize;
                            let ny = (y as i32 + dy) as usize;
                            let nz = (z as i32 + dz) as usize;
                            
                            if nx < width && ny < height && nz < depth {
                                self.active_cells.insert((nx, ny, nz));
                            }
                        }
                    }
                }
            }
            NeighborhoodType::Extended => {
                // Extended neighborhood - 2 cells away
                for dx in -2i32..=2 {
                    for dy in -2i32..=2 {
                        for dz in -2i32..=2 {
                            if dx.abs() + dy.abs() + dz.abs() > 4 {
                                continue;
                            }
                            
                            let nx = (x as i32 + dx) as usize;
                            let ny = (y as i32 + dy) as usize;
                            let nz = (z as i32 + dz) as usize;
                            
                            if nx < width && ny < height && nz < depth {
                                self.active_cells.insert((nx, ny, nz));
                            }
                        }
                    }
                }
            }
        }
    }
    
    /// Count live neighbors efficiently
    fn count_neighbors(&self, x: usize, y: usize, z: usize) -> u8 {
        let (width, height, depth) = self.grid.dimensions();
        let mut count = 0;
        
        match self.rules.neighborhood {
            NeighborhoodType::VonNeumann => {
                let neighbors = [
                    (x.wrapping_sub(1), y, z),
                    (x + 1, y, z),
                    (x, y.wrapping_sub(1), z),
                    (x, y + 1, z),
                    (x, y, z.wrapping_sub(1)),
                    (x, y, z + 1),
                ];
                
                for (nx, ny, nz) in neighbors {
                    if nx < width && ny < height && nz < depth {
                        if matches!(self.grid.get(nx, ny, nz), CellState::Alive(_)) {
                            count += 1;
                        }
                    }
                }
            }
            NeighborhoodType::Moore => {
                for dx in -1i32..=1 {
                    for dy in -1i32..=1 {
                        for dz in -1i32..=1 {
                            if dx == 0 && dy == 0 && dz == 0 {
                                continue;
                            }
                            
                            let nx = (x as i32 + dx) as usize;
                            let ny = (y as i32 + dy) as usize;
                            let nz = (z as i32 + dz) as usize;
                            
                            if nx < width && ny < height && nz < depth {
                                if matches!(self.grid.get(nx, ny, nz), CellState::Alive(_)) {
                                    count += 1;
                                }
                            }
                        }
                    }
                }
            }
            NeighborhoodType::Extended => {
                for dx in -2i32..=2 {
                    for dy in -2i32..=2 {
                        for dz in -2i32..=2 {
                            if dx == 0 && dy == 0 && dz == 0 {
                                continue;
                            }
                            if dx.abs() + dy.abs() + dz.abs() > 4 {
                                continue;
                            }
                            
                            let nx = (x as i32 + dx) as usize;
                            let ny = (y as i32 + dy) as usize;
                            let nz = (z as i32 + dz) as usize;
                            
                            if nx < width && ny < height && nz < depth {
                                if matches!(self.grid.get(nx, ny, nz), CellState::Alive(_)) {
                                    count += 1;
                                }
                            }
                        }
                    }
                }
            }
        }
        
        count
    }
    
    /// Perform one generation step - optimized for sparse grids
    pub fn step(&mut self) {
        let mut next_grid = SparseGrid3D::new(
            self.grid.dimensions().0,
            self.grid.dimensions().1,
            self.grid.dimensions().2,
        );
        let mut next_active = HashSet::new();
        
        // Only process active cells and their neighbors
        for &(x, y, z) in &self.active_cells {
            let current = self.grid.get(x, y, z).clone();
            let neighbors = self.count_neighbors(x, y, z);
            
            let next_state = match current {
                CellState::Dead => {
                    if self.rules.should_birth(neighbors) {
                        CellState::Alive(self.rules.states - 1)
                    } else {
                        CellState::Dead
                    }
                }
                CellState::Alive(age) => {
                    if self.rules.should_survive(neighbors) {
                        if self.rules.states > 2 && age > 0 {
                            CellState::Alive(age - 1)
                        } else {
                            CellState::Alive(age)
                        }
                    } else if self.rules.decay_rate > 0.0 && age > 0 {
                        let decay_chance = (self.seed as f32 % 100.0) / 100.0;
                        if decay_chance < self.rules.decay_rate {
                            CellState::Alive(age - 1)
                        } else {
                            CellState::Dead
                        }
                    } else {
                        CellState::Dead
                    }
                }
            };
            
            if next_state != CellState::Dead {
                next_grid.set(x, y, z, next_state).ok();
                next_active.insert((x, y, z));
                
                // Track neighbors for next generation
                for dx in -1i32..=1 {
                    for dy in -1i32..=1 {
                        for dz in -1i32..=1 {
                            let nx = (x as i32 + dx) as usize;
                            let ny = (y as i32 + dy) as usize;
                            let nz = (z as i32 + dz) as usize;
                            
                            if nx < self.grid.dimensions().0 && 
                               ny < self.grid.dimensions().1 && 
                               nz < self.grid.dimensions().2 {
                                next_active.insert((nx, ny, nz));
                            }
                        }
                    }
                }
            }
        }
        
        self.grid = next_grid;
        self.active_cells = next_active;
        self.generation += 1;
    }
    
    /// Get current generation
    pub fn generation(&self) -> u64 {
        self.generation
    }
    
    /// Get population count efficiently
    pub fn population(&self) -> usize {
        self.grid.non_default_count()
    }
    
    /// Get memory efficiency
    pub fn memory_efficiency(&self) -> f32 {
        self.grid.sparsity()
    }
    
    /// Convert to ArxObjects for visualization
    pub fn to_arxobjects(&self, building_id: u16) -> Vec<ArxObject> {
        let mut objects = Vec::new();
        
        for ((x, y, z), state) in self.grid.iter() {
            if matches!(state, CellState::Alive(_)) {
                objects.push(ArxObject::new(
                    building_id,
                    object_types::LIGHT, // Use light to represent active cells
                    x as u16,
                    y as u16,
                    z as u16,
                ));
            }
        }
        
        objects
    }
    
    /// Clear the automaton
    pub fn clear(&mut self) {
        self.grid.clear();
        self.active_cells.clear();
        self.generation = 0;
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_sparse_automaton() {
        let rules = AutomatonRules::conway_3d();
        let mut ca = SparseCellularAutomaton3D::new(100, 100, 100, rules, 42).unwrap();
        
        // Set some initial cells
        ca.set_cell(50, 50, 50, CellState::Alive(1)).unwrap();
        ca.set_cell(51, 50, 50, CellState::Alive(1)).unwrap();
        ca.set_cell(50, 51, 50, CellState::Alive(1)).unwrap();
        ca.set_cell(50, 50, 51, CellState::Alive(1)).unwrap();
        
        let initial_pop = ca.population();
        assert_eq!(initial_pop, 4);
        
        // Memory should be very efficient
        let efficiency = ca.memory_efficiency();
        assert!(efficiency < 0.001); // Less than 0.1% of full grid
        
        // Run a step
        ca.step();
        assert!(ca.generation() == 1);
        
        // Population should change based on rules
        let new_pop = ca.population();
        assert!(new_pop > 0);
    }
    
    #[test]
    fn test_sparse_memory_savings() {
        let rules = AutomatonRules::conway_3d();
        
        // Large grid with few active cells
        let mut ca = SparseCellularAutomaton3D::new(1000, 1000, 1000, rules, 42).unwrap();
        
        // Add only 100 cells to a billion-cell grid
        for i in 0..10 {
            for j in 0..10 {
                ca.set_cell(i * 10, j * 10, 50, CellState::Alive(1)).unwrap();
            }
        }
        
        assert_eq!(ca.population(), 100);
        
        // Memory efficiency should be extremely good
        let efficiency = ca.memory_efficiency();
        assert!(efficiency < 0.0001); // Less than 0.01% of full grid
        
        // Active cells tracking should be reasonable
        assert!(ca.active_cells.len() < 10000); // Much less than billion cells
    }
}