//! Sparse Data Structures for Memory Efficiency
//! 
//! Implements sparse representations of 3D grids and matrices to reduce
//! memory usage for data with many zero/default values.

use std::collections::HashMap;
use std::hash::Hash;
use crate::holographic::error::{Result, HolographicError};

/// Sparse 3D grid that only stores non-default values
#[derive(Clone, Debug)]
pub struct SparseGrid3D<T: Clone + Default + PartialEq> {
    cells: HashMap<(usize, usize, usize), T>,
    dimensions: (usize, usize, usize),
    default_value: T,
}

impl<T: Clone + Default + PartialEq> SparseGrid3D<T> {
    /// Create a new sparse grid with specified dimensions
    pub fn new(width: usize, height: usize, depth: usize) -> Self {
        Self {
            cells: HashMap::new(),
            dimensions: (width, height, depth),
            default_value: T::default(),
        }
    }
    
    /// Create with a custom default value
    pub fn with_default(width: usize, height: usize, depth: usize, default: T) -> Self {
        Self {
            cells: HashMap::new(),
            dimensions: (width, height, depth),
            default_value: default,
        }
    }
    
    /// Get value at position
    pub fn get(&self, x: usize, y: usize, z: usize) -> &T {
        self.cells.get(&(x, y, z)).unwrap_or(&self.default_value)
    }
    
    /// Set value at position
    pub fn set(&mut self, x: usize, y: usize, z: usize, value: T) -> Result<()> {
        if x >= self.dimensions.0 || y >= self.dimensions.1 || z >= self.dimensions.2 {
            return Err(HolographicError::InvalidInput(
                format!("Position ({}, {}, {}) out of bounds", x, y, z)
            ));
        }
        
        if value == self.default_value {
            // Remove from storage if setting to default
            self.cells.remove(&(x, y, z));
        } else {
            self.cells.insert((x, y, z), value);
        }
        Ok(())
    }
    
    /// Get mutable reference to value at position
    pub fn get_mut(&mut self, x: usize, y: usize, z: usize) -> &mut T {
        if !self.cells.contains_key(&(x, y, z)) {
            self.cells.insert((x, y, z), self.default_value.clone());
        }
        self.cells.get_mut(&(x, y, z)).unwrap()
    }
    
    /// Iterate over all non-default cells
    pub fn iter(&self) -> impl Iterator<Item = ((usize, usize, usize), &T)> {
        self.cells.iter().map(|(k, v)| (*k, v))
    }
    
    /// Count of non-default cells
    pub fn non_default_count(&self) -> usize {
        self.cells.len()
    }
    
    /// Total capacity if fully populated
    pub fn capacity(&self) -> usize {
        self.dimensions.0 * self.dimensions.1 * self.dimensions.2
    }
    
    /// Memory efficiency ratio (0.0 to 1.0, lower is better)
    pub fn sparsity(&self) -> f32 {
        self.cells.len() as f32 / self.capacity() as f32
    }
    
    /// Clear all non-default values
    pub fn clear(&mut self) {
        self.cells.clear();
    }
    
    /// Get dimensions
    pub fn dimensions(&self) -> (usize, usize, usize) {
        self.dimensions
    }
    
    /// Apply a function to all non-default cells
    pub fn map_inplace<F>(&mut self, mut f: F) 
    where
        F: FnMut(&T) -> T,
    {
        let mut updates = Vec::new();
        for (coord, value) in &self.cells {
            let new_value = f(value);
            if new_value != self.default_value {
                updates.push((*coord, new_value));
            }
        }
        
        for (coord, value) in updates {
            if value == self.default_value {
                self.cells.remove(&coord);
            } else {
                self.cells.insert(coord, value);
            }
        }
    }
    
    /// Get all cells in a region
    pub fn get_region(&self, 
        x_min: usize, y_min: usize, z_min: usize,
        x_max: usize, y_max: usize, z_max: usize
    ) -> Vec<((usize, usize, usize), T)> {
        let mut result = Vec::new();
        for x in x_min..=x_max.min(self.dimensions.0 - 1) {
            for y in y_min..=y_max.min(self.dimensions.1 - 1) {
                for z in z_min..=z_max.min(self.dimensions.2 - 1) {
                    let value = self.get(x, y, z).clone();
                    if value != self.default_value {
                        result.push(((x, y, z), value));
                    }
                }
            }
        }
        result
    }
}

/// Sparse matrix for 2D data
#[derive(Clone, Debug)]
pub struct SparseMatrix<T: Clone + Default + PartialEq> {
    entries: HashMap<(usize, usize), T>,
    rows: usize,
    cols: usize,
    default_value: T,
}

impl<T: Clone + Default + PartialEq> SparseMatrix<T> {
    pub fn new(rows: usize, cols: usize) -> Self {
        Self {
            entries: HashMap::new(),
            rows,
            cols,
            default_value: T::default(),
        }
    }
    
    pub fn get(&self, row: usize, col: usize) -> &T {
        self.entries.get(&(row, col)).unwrap_or(&self.default_value)
    }
    
    pub fn set(&mut self, row: usize, col: usize, value: T) -> Result<()> {
        if row >= self.rows || col >= self.cols {
            return Err(HolographicError::InvalidInput(
                format!("Position ({}, {}) out of bounds", row, col)
            ));
        }
        
        if value == self.default_value {
            self.entries.remove(&(row, col));
        } else {
            self.entries.insert((row, col), value);
        }
        Ok(())
    }
    
    pub fn non_zero_count(&self) -> usize {
        self.entries.len()
    }
    
    pub fn sparsity(&self) -> f32 {
        self.entries.len() as f32 / (self.rows * self.cols) as f32
    }
}

/// Bounded collections with automatic eviction
#[derive(Clone, Debug)]
pub struct BoundedVecDeque<T> {
    inner: std::collections::VecDeque<T>,
    max_size: usize,
}

impl<T> BoundedVecDeque<T> {
    pub fn new(max_size: usize) -> Self {
        Self {
            inner: std::collections::VecDeque::with_capacity(max_size),
            max_size,
        }
    }
    
    pub fn push_back(&mut self, item: T) {
        if self.inner.len() >= self.max_size {
            self.inner.pop_front(); // Remove oldest
        }
        self.inner.push_back(item);
    }
    
    pub fn push_front(&mut self, item: T) {
        if self.inner.len() >= self.max_size {
            self.inner.pop_back(); // Remove newest
        }
        self.inner.push_front(item);
    }
    
    pub fn len(&self) -> usize {
        self.inner.len()
    }
    
    pub fn is_empty(&self) -> bool {
        self.inner.is_empty()
    }
    
    pub fn clear(&mut self) {
        self.inner.clear();
    }
    
    pub fn iter(&self) -> impl Iterator<Item = &T> {
        self.inner.iter()
    }
}

/// Bounded HashMap with LRU eviction
pub struct BoundedHashMap<K: Hash + Eq + Clone, V: Clone> {
    map: HashMap<K, V>,
    access_order: std::collections::VecDeque<K>,
    max_size: usize,
}

impl<K: Hash + Eq + Clone, V: Clone> BoundedHashMap<K, V> {
    pub fn new(max_size: usize) -> Self {
        Self {
            map: HashMap::with_capacity(max_size),
            access_order: std::collections::VecDeque::with_capacity(max_size),
            max_size,
        }
    }
    
    pub fn insert(&mut self, key: K, value: V) -> Option<V> {
        // Remove from access order if exists
        if let Some(pos) = self.access_order.iter().position(|k| k == &key) {
            self.access_order.remove(pos);
        }
        
        // Evict LRU if at capacity
        if self.map.len() >= self.max_size && !self.map.contains_key(&key) {
            if let Some(lru_key) = self.access_order.pop_front() {
                self.map.remove(&lru_key);
            }
        }
        
        self.access_order.push_back(key.clone());
        self.map.insert(key, value)
    }
    
    pub fn get(&mut self, key: &K) -> Option<&V> {
        if self.map.contains_key(key) {
            // Update access order
            if let Some(pos) = self.access_order.iter().position(|k| k == key) {
                self.access_order.remove(pos);
            }
            self.access_order.push_back(key.clone());
            self.map.get(key)
        } else {
            None
        }
    }
    
    pub fn len(&self) -> usize {
        self.map.len()
    }
    
    pub fn clear(&mut self) {
        self.map.clear();
        self.access_order.clear();
    }
}

/// Compressed bit vector for boolean grids
pub struct BitGrid3D {
    bits: Vec<u64>,
    dimensions: (usize, usize, usize),
}

impl BitGrid3D {
    pub fn new(width: usize, height: usize, depth: usize) -> Self {
        let total_bits = width * height * depth;
        let words_needed = (total_bits + 63) / 64;
        Self {
            bits: vec![0u64; words_needed],
            dimensions: (width, height, depth),
        }
    }
    
    fn index(&self, x: usize, y: usize, z: usize) -> usize {
        x + y * self.dimensions.0 + z * self.dimensions.0 * self.dimensions.1
    }
    
    pub fn get(&self, x: usize, y: usize, z: usize) -> bool {
        let bit_index = self.index(x, y, z);
        let word_index = bit_index / 64;
        let bit_offset = bit_index % 64;
        
        if word_index >= self.bits.len() {
            return false;
        }
        
        (self.bits[word_index] & (1u64 << bit_offset)) != 0
    }
    
    pub fn set(&mut self, x: usize, y: usize, z: usize, value: bool) {
        let bit_index = self.index(x, y, z);
        let word_index = bit_index / 64;
        let bit_offset = bit_index % 64;
        
        if word_index >= self.bits.len() {
            return;
        }
        
        if value {
            self.bits[word_index] |= 1u64 << bit_offset;
        } else {
            self.bits[word_index] &= !(1u64 << bit_offset);
        }
    }
    
    pub fn count_set(&self) -> usize {
        self.bits.iter().map(|word| word.count_ones() as usize).sum()
    }
    
    pub fn memory_usage_bytes(&self) -> usize {
        self.bits.len() * 8
    }
    
    pub fn clear(&mut self) {
        for word in &mut self.bits {
            *word = 0;
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_sparse_grid() {
        let mut grid = SparseGrid3D::<i32>::new(100, 100, 100);
        
        // Initially empty
        assert_eq!(grid.non_default_count(), 0);
        assert_eq!(*grid.get(50, 50, 50), 0);
        
        // Set some values
        grid.set(10, 10, 10, 42).unwrap();
        grid.set(20, 20, 20, 100).unwrap();
        
        assert_eq!(*grid.get(10, 10, 10), 42);
        assert_eq!(*grid.get(20, 20, 20), 100);
        assert_eq!(grid.non_default_count(), 2);
        
        // Setting to default removes from storage
        grid.set(10, 10, 10, 0).unwrap();
        assert_eq!(grid.non_default_count(), 1);
        
        // Check sparsity
        let sparsity = grid.sparsity();
        assert!(sparsity < 0.001); // Very sparse
    }
    
    #[test]
    fn test_bounded_vec_deque() {
        let mut deque = BoundedVecDeque::new(3);
        
        deque.push_back(1);
        deque.push_back(2);
        deque.push_back(3);
        deque.push_back(4); // Should evict 1
        
        let values: Vec<_> = deque.iter().copied().collect();
        assert_eq!(values, vec![2, 3, 4]);
    }
    
    #[test]
    fn test_bounded_hashmap() {
        let mut map = BoundedHashMap::new(3);
        
        map.insert("a", 1);
        map.insert("b", 2);
        map.insert("c", 3);
        
        // Access "a" to make it recently used
        assert_eq!(map.get(&"a"), Some(&1));
        
        // Insert "d" should evict "b" (least recently used)
        map.insert("d", 4);
        
        assert_eq!(map.len(), 3);
        assert!(map.get(&"b").is_none());
    }
    
    #[test]
    fn test_bit_grid() {
        let mut grid = BitGrid3D::new(64, 64, 64);
        
        grid.set(10, 10, 10, true);
        grid.set(20, 20, 20, true);
        grid.set(30, 30, 30, true);
        
        assert!(grid.get(10, 10, 10));
        assert!(grid.get(20, 20, 20));
        assert!(!grid.get(15, 15, 15));
        
        assert_eq!(grid.count_set(), 3);
        
        // Memory efficiency: 64x64x64 = 262,144 bits = 32,768 bytes for full array
        // BitGrid uses: 4,096 bytes (8x more efficient)
        assert!(grid.memory_usage_bytes() < 5000);
    }
}