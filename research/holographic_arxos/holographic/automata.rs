//! Cellular Automata System
//! 
//! Implements 3D cellular automata for dynamic building systems
//! simulation using Conway-like rules extended to three dimensions.

use crate::arxobject::{ArxObject, object_types};
use crate::holographic::error::{Result, validation};
use core::ops::{Index, IndexMut};

#[cfg(not(feature = "std"))]
use alloc::vec::Vec;

#[cfg(feature = "std")]
use std::vec::Vec;

/// Cell state for cellular automata
#[derive(Clone, Copy, Debug, PartialEq, Default)]
pub enum CellState {
    #[default]
    Dead,
    Alive(u8), // Age or state value
}

/// 3D cellular automaton rules
#[derive(Clone, Debug)]
pub struct AutomatonRules {
    /// Neighbor counts that cause birth of new cell
    pub birth: Vec<u8>,
    
    /// Neighbor counts that allow survival
    pub survival: Vec<u8>,
    
    /// Number of possible states (2 for binary, more for multi-state)
    pub states: u8,
    
    /// Decay rate for multi-state automata
    pub decay_rate: f32,
    
    /// Neighborhood type
    pub neighborhood: NeighborhoodType,
}

impl AutomatonRules {
    /// Classic 3D Conway's Game of Life rules (B5/S45)
    pub fn conway_3d() -> Self {
        Self {
            birth: vec![5],
            survival: vec![4, 5],
            states: 2,
            decay_rate: 0.0,
            neighborhood: NeighborhoodType::Moore,
        }
    }
    
    /// 3D growth pattern (B4/S234)
    pub fn growth_3d() -> Self {
        Self {
            birth: vec![4],
            survival: vec![2, 3, 4],
            states: 2,
            decay_rate: 0.0,
            neighborhood: NeighborhoodType::Moore,
        }
    }
    
    /// Crystal formation pattern
    pub fn crystal() -> Self {
        Self {
            birth: vec![1, 3],
            survival: vec![1, 2, 3, 4, 5, 6],
            states: 2,
            decay_rate: 0.0,
            neighborhood: NeighborhoodType::VonNeumann,
        }
    }
    
    /// Multi-state decay automaton
    pub fn decay(states: u8, decay_rate: f32) -> Self {
        Self {
            birth: vec![3, 6],
            survival: vec![2, 3, 4, 5],
            states,
            decay_rate: decay_rate.clamp(0.0, 1.0),
            neighborhood: NeighborhoodType::Moore,
        }
    }
    
    /// Check if cell should be born
    pub fn should_birth(&self, neighbors: u8) -> bool {
        self.birth.contains(&neighbors)
    }
    
    /// Check if cell should survive
    pub fn should_survive(&self, neighbors: u8) -> bool {
        self.survival.contains(&neighbors)
    }
}

/// Neighborhood types for cellular automata
#[derive(Clone, Copy, Debug, PartialEq)]
pub enum NeighborhoodType {
    /// 6 neighbors (faces only)
    VonNeumann,
    
    /// 26 neighbors (faces, edges, corners)
    Moore,
    
    /// 18 neighbors (faces and edges, no corners)
    Extended,
}

impl NeighborhoodType {
    /// Get neighbor offsets for this neighborhood type
    pub fn offsets(&self) -> Vec<(i32, i32, i32)> {
        match self {
            NeighborhoodType::VonNeumann => vec![
                (-1, 0, 0), (1, 0, 0),
                (0, -1, 0), (0, 1, 0),
                (0, 0, -1), (0, 0, 1),
            ],
            NeighborhoodType::Moore => {
                let mut offsets = Vec::with_capacity(26);
                for dx in -1..=1 {
                    for dy in -1..=1 {
                        for dz in -1..=1 {
                            if dx != 0 || dy != 0 || dz != 0 {
                                offsets.push((dx, dy, dz));
                            }
                        }
                    }
                }
                offsets
            }
            NeighborhoodType::Extended => {
                let mut offsets = Vec::with_capacity(18);
                // Faces
                offsets.extend(&[
                    (-1, 0, 0), (1, 0, 0),
                    (0, -1, 0), (0, 1, 0),
                    (0, 0, -1), (0, 0, 1),
                ]);
                // Edges
                for dx in -1..=1 {
                    for dy in -1..=1 {
                        if dx != 0 && dy != 0 {
                            offsets.push((dx, dy, 0));
                        }
                    }
                }
                for dx in -1..=1 {
                    for dz in -1..=1 {
                        if dx != 0 && dz != 0 {
                            offsets.push((dx, 0, dz));
                        }
                    }
                }
                for dy in -1..=1 {
                    for dz in -1..=1 {
                        if dy != 0 && dz != 0 {
                            offsets.push((0, dy, dz));
                        }
                    }
                }
                offsets
            }
        }
    }
    
    /// Get maximum neighbor count for this neighborhood
    pub fn max_neighbors(&self) -> u8 {
        match self {
            NeighborhoodType::VonNeumann => 6,
            NeighborhoodType::Moore => 26,
            NeighborhoodType::Extended => 18,
        }
    }
}

/// 3D grid for cellular automaton
#[derive(Clone, Debug)]
pub struct Grid3D {
    data: Vec<u8>,
    width: usize,
    height: usize,
    depth: usize,
}

impl Grid3D {
    /// Create new empty grid
    pub fn new(width: usize, height: usize, depth: usize) -> Self {
        Self {
            data: vec![0; width * height * depth],
            width,
            height,
            depth,
        }
    }
    
    /// Create grid with random initial state
    pub fn random(width: usize, height: usize, depth: usize, density: f32, seed: u64) -> Self {
        let mut grid = Self::new(width, height, depth);
        let threshold = (density * 1000.0) as u64;
        
        for x in 0..width {
            for y in 0..height {
                for z in 0..depth {
                    let hash = Self::hash(seed, x as u64, y as u64, z as u64);
                    if hash % 1000 < threshold {
                        grid[(x, y, z)] = 1;
                    }
                }
            }
        }
        
        grid
    }
    
    /// Simple hash for randomness
    fn hash(seed: u64, x: u64, y: u64, z: u64) -> u64 {
        let mut h = seed;
        h ^= x.wrapping_mul(0x9e3779b97f4a7c15);
        h ^= y.wrapping_mul(0x94d049bb133111eb);
        h ^= z.wrapping_mul(0xbf58476d1ce4e5b9);
        h = h.wrapping_mul(0x94d049bb133111eb);
        h ^= h >> 30;
        h
    }
    
    /// Get value at position with boundary checking
    pub fn get(&self, x: i32, y: i32, z: i32) -> u8 {
        if x < 0 || y < 0 || z < 0 {
            return 0;
        }
        let (x, y, z) = (x as usize, y as usize, z as usize);
        if x >= self.width || y >= self.height || z >= self.depth {
            return 0;
        }
        self.data[x + y * self.width + z * self.width * self.height]
    }
    
    /// Set value at position with boundary checking
    pub fn set(&mut self, x: i32, y: i32, z: i32, value: u8) {
        if x < 0 || y < 0 || z < 0 {
            return;
        }
        let (x, y, z) = (x as usize, y as usize, z as usize);
        if x >= self.width || y >= self.height || z >= self.depth {
            return;
        }
        self.data[x + y * self.width + z * self.width * self.height] = value;
    }
    
    /// Count living cells
    pub fn population(&self) -> usize {
        self.data.iter().filter(|&&c| c > 0).count()
    }
    
    /// Get dimensions
    pub fn dimensions(&self) -> (usize, usize, usize) {
        (self.width, self.height, self.depth)
    }
}

impl Index<(usize, usize, usize)> for Grid3D {
    type Output = u8;
    
    fn index(&self, (x, y, z): (usize, usize, usize)) -> &Self::Output {
        &self.data[x + y * self.width + z * self.width * self.height]
    }
}

impl IndexMut<(usize, usize, usize)> for Grid3D {
    fn index_mut(&mut self, (x, y, z): (usize, usize, usize)) -> &mut Self::Output {
        &mut self.data[x + y * self.width + z * self.width * self.height]
    }
}

/// 3D cellular automaton for building systems
pub struct CellularAutomaton3D {
    rules: AutomatonRules,
    grid: Grid3D,
    generation: u64,
    seed: u64,
}

impl CellularAutomaton3D {
    /// Create new automaton
    pub fn new(width: usize, height: usize, depth: usize, rules: AutomatonRules, seed: u64) -> Result<Self> {
        validation::validate_grid_dimensions(width, height, depth)?;
        Ok(Self {
            rules,
            grid: Grid3D::new(width, height, depth),
            generation: 0,
            seed,
        })
    }
    
    /// Create with random initial state
    pub fn random(
        width: usize,
        height: usize,
        depth: usize,
        rules: AutomatonRules,
        density: f32,
        seed: u64,
    ) -> Result<Self> {
        validation::validate_grid_dimensions(width, height, depth)?;
        validation::validate_probability(density, "density")?;
        Ok(Self {
            rules,
            grid: Grid3D::random(width, height, depth, density, seed),
            generation: 0,
            seed,
        })
    }
    
    /// Perform one generation step
    pub fn step(&mut self) {
        let (width, height, depth) = self.grid.dimensions();
        let mut new_grid = Grid3D::new(width, height, depth);
        
        for x in 0..width {
            for y in 0..height {
                for z in 0..depth {
                    let current = self.grid[(x, y, z)];
                    let neighbors = self.count_neighbors(x as i32, y as i32, z as i32);
                    
                    let new_value = if self.rules.states == 2 {
                        // Binary automaton
                        if current > 0 {
                            if self.rules.should_survive(neighbors) { 1 } else { 0 }
                        } else {
                            if self.rules.should_birth(neighbors) { 1 } else { 0 }
                        }
                    } else {
                        // Multi-state automaton
                        self.calculate_multistate(current, neighbors)
                    };
                    
                    new_grid[(x, y, z)] = new_value;
                }
            }
        }
        
        self.grid = new_grid;
        self.generation += 1;
    }
    
    /// Count living neighbors
    fn count_neighbors(&self, x: i32, y: i32, z: i32) -> u8 {
        let mut count = 0;
        
        for (dx, dy, dz) in self.rules.neighborhood.offsets() {
            let value = self.grid.get(x + dx, y + dy, z + dz);
            if value > 0 {
                count += 1;
            }
        }
        
        count
    }
    
    /// Calculate next state for multi-state automaton
    fn calculate_multistate(&self, current: u8, neighbors: u8) -> u8 {
        if current == 0 {
            // Dead cell - check for birth
            if self.rules.should_birth(neighbors) {
                self.rules.states - 1 // Born at maximum state
            } else {
                0
            }
        } else if current == self.rules.states - 1 {
            // Living cell at max state
            if self.rules.should_survive(neighbors) {
                current
            } else {
                ((current as f32) * (1.0 - self.rules.decay_rate)) as u8
            }
        } else {
            // Decaying cell
            ((current as f32) * (1.0 - self.rules.decay_rate)).max(0.0) as u8
        }
    }
    
    /// Run for multiple generations
    pub fn evolve(&mut self, generations: u32) {
        for _ in 0..generations {
            self.step();
        }
    }
    
    /// Convert current state to ArxObjects
    pub fn to_arxobjects(&self, building_id: u16, base_position: (u16, u16, u16), scale: u16) -> Vec<ArxObject> {
        let mut objects = Vec::new();
        let (width, height, depth) = self.grid.dimensions();
        
        for x in 0..width {
            for y in 0..height {
                for z in 0..depth {
                    let value = self.grid[(x, y, z)];
                    if value > 0 {
                        let obj = ArxObject::new(
                            building_id,
                            self.cell_to_object_type(value, z),
                            base_position.0 + (x as u16 * scale),
                            base_position.1 + (y as u16 * scale),
                            base_position.2 + (z as u16 * scale),
                        );
                        objects.push(obj);
                    }
                }
            }
        }
        
        objects
    }
    
    /// Map cell state to object type
    fn cell_to_object_type(&self, state: u8, z: usize) -> u8 {
        if self.rules.states == 2 {
            // Binary - use height to determine type
            if z == 0 {
                object_types::FOUNDATION
            } else if z < 3 {
                object_types::WALL
            } else {
                object_types::FLOOR
            }
        } else {
            // Multi-state - map state to different materials
            match state {
                0 => object_types::AIR_VENT,
                1..=3 => object_types::DRYWALL,
                4..=6 => object_types::CONCRETE,
                7..=9 => object_types::STEEL_BEAM,
                _ => object_types::GLASS,
            }
        }
    }
    
    /// Get current grid state
    pub fn grid(&self) -> &Grid3D {
        &self.grid
    }
    
    /// Get current generation
    pub fn generation(&self) -> u64 {
        self.generation
    }
    
    /// Set a region of cells
    pub fn set_region(&mut self, x: i32, y: i32, z: i32, w: i32, h: i32, d: i32, value: u8) {
        for dx in 0..w {
            for dy in 0..h {
                for dz in 0..d {
                    self.grid.set(x + dx, y + dy, z + dz, value);
                }
            }
        }
    }
    
    /// Create a glider pattern (if applicable to rules)
    pub fn add_glider(&mut self, x: i32, y: i32, z: i32) {
        // 3D glider pattern
        self.grid.set(x, y, z, 1);
        self.grid.set(x + 1, y, z, 1);
        self.grid.set(x + 2, y, z, 1);
        self.grid.set(x + 2, y + 1, z, 1);
        self.grid.set(x + 1, y + 2, z, 1);
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_neighborhood_offsets() {
        let von = NeighborhoodType::VonNeumann;
        assert_eq!(von.offsets().len(), 6);
        assert_eq!(von.max_neighbors(), 6);
        
        let moore = NeighborhoodType::Moore;
        assert_eq!(moore.offsets().len(), 26);
        assert_eq!(moore.max_neighbors(), 26);
        
        let extended = NeighborhoodType::Extended;
        assert_eq!(extended.offsets().len(), 18);
        assert_eq!(extended.max_neighbors(), 18);
    }
    
    #[test]
    fn test_grid_3d() {
        let mut grid = Grid3D::new(10, 10, 10);
        assert_eq!(grid.population(), 0);
        
        grid[(5, 5, 5)] = 1;
        assert_eq!(grid.population(), 1);
        assert_eq!(grid.get(5, 5, 5), 1);
        
        // Test boundary checking
        assert_eq!(grid.get(-1, 5, 5), 0);
        assert_eq!(grid.get(10, 5, 5), 0);
    }
    
    #[test]
    fn test_cellular_automaton() {
        let rules = AutomatonRules::conway_3d();
        let mut ca = CellularAutomaton3D::random(10, 10, 10, rules, 0.3, 42).unwrap();
        
        let initial_pop = ca.grid().population();
        ca.step();
        let new_pop = ca.grid().population();
        
        // Population should change
        assert_ne!(initial_pop, new_pop);
        assert_eq!(ca.generation(), 1);
    }
    
    #[test]
    fn test_to_arxobjects() {
        let rules = AutomatonRules::growth_3d();
        let mut ca = CellularAutomaton3D::new(5, 5, 5, rules, 42).unwrap();
        
        // Create a simple pattern
        ca.set_region(1, 1, 1, 3, 3, 1, 1);
        
        let objects = ca.to_arxobjects(1, (1000, 1000, 1000), 100);
        assert_eq!(objects.len(), 9); // 3x3x1 region
        
        // Check positions are correct (copy values to avoid packed struct alignment issues)
        let x0 = objects[0].x;
        let y0 = objects[0].y;
        let z0 = objects[0].z;
        assert_eq!(x0, 1100);
        assert_eq!(y0, 1100);
        assert_eq!(z0, 1100);
    }
}