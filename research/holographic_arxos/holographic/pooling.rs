//! Object Pooling System for Memory Efficiency
//! 
//! Implements object pools to reduce allocation overhead and improve
//! cache locality for frequently created/destroyed objects.

use std::sync::{Arc, Mutex, MutexGuard};
use std::collections::VecDeque;
use crate::holographic::error::{Result, HolographicError};

/// Trait for objects that can be pooled
pub trait Poolable: Default + Send {
    /// Reset the object to its initial state
    fn reset(&mut self);
}

/// Generic object pool for reusable objects
pub struct ObjectPool<T: Poolable> {
    available: Arc<Mutex<VecDeque<T>>>,
    max_size: usize,
    created_count: usize,
}

impl<T: Poolable> ObjectPool<T> {
    /// Create a new object pool with a maximum size
    pub fn new(max_size: usize) -> Self {
        Self {
            available: Arc::new(Mutex::new(VecDeque::with_capacity(max_size))),
            max_size,
            created_count: 0,
        }
    }
    
    /// Create a new pool with pre-allocated objects
    pub fn with_capacity(capacity: usize, max_size: usize) -> Result<Self> {
        let mut pool = Self::new(max_size);
        let mut available = pool.available.lock()
            .map_err(|_| HolographicError::InvalidInput("Pool mutex poisoned".to_string()))?;
        
        for _ in 0..capacity {
            available.push_back(T::default());
            pool.created_count += 1;
        }
        
        drop(available);
        Ok(pool)
    }
    
    /// Get an object from the pool
    pub fn get(&mut self) -> Result<PooledObject<T>> {
        let mut available = self.available.lock()
            .map_err(|_| HolographicError::InvalidInput("Pool mutex poisoned".to_string()))?;
        
        let obj = if let Some(mut obj) = available.pop_front() {
            obj.reset();
            obj
        } else {
            self.created_count += 1;
            T::default()
        };
        
        Ok(PooledObject {
            inner: Some(obj),
            pool: Arc::clone(&self.available),
            max_size: self.max_size,
        })
    }
    
    /// Get current number of available objects
    pub fn available_count(&self) -> Result<usize> {
        Ok(self.available.lock()
            .map_err(|_| HolographicError::InvalidInput("Pool mutex poisoned".to_string()))?
            .len())
    }
    
    /// Get total number of objects created
    pub fn created_count(&self) -> usize {
        self.created_count
    }
    
    /// Clear all objects from the pool
    pub fn clear(&mut self) -> Result<()> {
        self.available.lock()
            .map_err(|_| HolographicError::InvalidInput("Pool mutex poisoned".to_string()))?
            .clear();
        Ok(())
    }
}

/// RAII wrapper for pooled objects
pub struct PooledObject<T: Poolable> {
    inner: Option<T>,
    pool: Arc<Mutex<VecDeque<T>>>,
    max_size: usize,
}

impl<T: Poolable> PooledObject<T> {
    /// Take ownership of the inner object
    pub fn take(mut self) -> Result<T> {
        self.inner.take()
            .ok_or_else(|| HolographicError::InvalidInput("PooledObject already taken".to_string()))
    }
}

impl<T: Poolable> std::ops::Deref for PooledObject<T> {
    type Target = T;
    
    fn deref(&self) -> &Self::Target {
        self.inner.as_ref()
            .expect("PooledObject inner value should not be None during deref")
    }
}

impl<T: Poolable> std::ops::DerefMut for PooledObject<T> {
    fn deref_mut(&mut self) -> &mut Self::Target {
        self.inner.as_mut()
            .expect("PooledObject inner value should not be None during deref_mut")
    }
}

impl<T: Poolable> Drop for PooledObject<T> {
    fn drop(&mut self) {
        if let Some(mut obj) = self.inner.take() {
            // Best effort - ignore errors in drop
            if let Ok(mut pool) = self.pool.lock() {
                // Only return to pool if under max size
                if pool.len() < self.max_size {
                    obj.reset();
                    pool.push_back(obj);
                }
            }
        }
    }
}

/// Specialized pool for Vec<T> to reuse allocations
pub struct VecPool<T> {
    available: Arc<Mutex<Vec<Vec<T>>>>,
    max_size: usize,
    max_vec_capacity: usize,
}

impl<T> VecPool<T> {
    pub fn new(max_size: usize, max_vec_capacity: usize) -> Self {
        Self {
            available: Arc::new(Mutex::new(Vec::with_capacity(max_size))),
            max_size,
            max_vec_capacity,
        }
    }
    
    pub fn get(&self) -> Result<PooledVec<T>> {
        let mut available = self.available.lock()
            .map_err(|_| HolographicError::InvalidInput("VecPool mutex poisoned".to_string()))?;
        
        let vec = available.pop().unwrap_or_else(|| Vec::with_capacity(16));
        
        Ok(PooledVec {
            inner: Some(vec),
            pool: Arc::clone(&self.available),
            max_size: self.max_size,
            max_capacity: self.max_vec_capacity,
        })
    }
}

pub struct PooledVec<T> {
    inner: Option<Vec<T>>,
    pool: Arc<Mutex<Vec<Vec<T>>>>,
    max_size: usize,
    max_capacity: usize,
}

impl<T> std::ops::Deref for PooledVec<T> {
    type Target = Vec<T>;
    
    fn deref(&self) -> &Self::Target {
        self.inner.as_ref()
            .expect("PooledVec inner value should not be None during deref")
    }
}

impl<T> std::ops::DerefMut for PooledVec<T> {
    fn deref_mut(&mut self) -> &mut Self::Target {
        self.inner.as_mut()
            .expect("PooledVec inner value should not be None during deref_mut")
    }
}

impl<T> Drop for PooledVec<T> {
    fn drop(&mut self) {
        if let Some(mut vec) = self.inner.take() {
            // Best effort - ignore errors in drop
            if let Ok(mut pool) = self.pool.lock() {
                // Clear the vec and return to pool if conditions met
                if pool.len() < self.max_size && vec.capacity() <= self.max_capacity {
                    vec.clear();
                    pool.push(vec);
                }
            }
        }
    }
}

/// Pool for frequently used computation results
pub struct ComputationCache<K, V> {
    cache: Arc<Mutex<lru::LruCache<K, V>>>,
}

impl<K: Eq + std::hash::Hash, V: Clone> ComputationCache<K, V> {
    pub fn new(capacity: usize) -> Result<Self> {
        let capacity = std::num::NonZeroUsize::new(capacity)
            .ok_or_else(|| HolographicError::InvalidInput("Cache capacity must be non-zero".to_string()))?;
        
        Ok(Self {
            cache: Arc::new(Mutex::new(lru::LruCache::new(capacity))),
        })
    }
    
    pub fn get_or_compute<F>(&self, key: K, compute: F) -> Result<V>
    where
        F: FnOnce() -> V,
        K: Clone,
    {
        let mut cache = self.cache.lock()
            .map_err(|_| HolographicError::InvalidInput("Cache mutex poisoned".to_string()))?;
        
        if let Some(value) = cache.get(&key) {
            return Ok(value.clone());
        }
        
        let value = compute();
        cache.put(key, value.clone());
        Ok(value)
    }
    
    pub fn clear(&self) -> Result<()> {
        self.cache.lock()
            .map_err(|_| HolographicError::InvalidInput("Cache mutex poisoned".to_string()))?
            .clear();
        Ok(())
    }
}

// Concrete poolable types for the holographic system

/// Poolable mesh vertex buffer
#[derive(Default)]
pub struct VertexBuffer {
    pub vertices: Vec<f32>,
    pub normals: Vec<f32>,
    pub uvs: Vec<f32>,
}

impl Poolable for VertexBuffer {
    fn reset(&mut self) {
        self.vertices.clear();
        self.normals.clear();
        self.uvs.clear();
    }
}

/// Poolable transformation matrix
#[derive(Default)]
pub struct TransformMatrix {
    pub data: [[f32; 4]; 4],
}

impl Poolable for TransformMatrix {
    fn reset(&mut self) {
        self.data = [
            [1.0, 0.0, 0.0, 0.0],
            [0.0, 1.0, 0.0, 0.0],
            [0.0, 0.0, 1.0, 0.0],
            [0.0, 0.0, 0.0, 1.0],
        ];
    }
}

/// Poolable noise computation buffer
#[derive(Default)]
pub struct NoiseBuffer {
    pub samples: Vec<f32>,
    pub octaves: Vec<(f32, f32)>,
}

impl Poolable for NoiseBuffer {
    fn reset(&mut self) {
        self.samples.clear();
        self.octaves.clear();
    }
}

/// Global pools for the holographic system
pub struct GlobalPools {
    pub vertex_buffers: ObjectPool<VertexBuffer>,
    pub transform_matrices: ObjectPool<TransformMatrix>,
    pub noise_buffers: ObjectPool<NoiseBuffer>,
    pub vec_pool_f32: VecPool<f32>,
    pub vec_pool_u16: VecPool<u16>,
}

impl GlobalPools {
    pub fn new() -> Result<Self> {
        Ok(Self {
            vertex_buffers: ObjectPool::with_capacity(32, 128)?,
            transform_matrices: ObjectPool::with_capacity(64, 256)?,
            noise_buffers: ObjectPool::with_capacity(16, 64)?,
            vec_pool_f32: VecPool::new(128, 10000),
            vec_pool_u16: VecPool::new(128, 10000),
        })
    }
}

impl Default for GlobalPools {
    fn default() -> Self {
        Self::new().expect("Failed to create default GlobalPools")
    }
}

// Thread-local storage for pools
thread_local! {
    static POOLS: std::cell::RefCell<Option<Arc<GlobalPools>>> = std::cell::RefCell::new(None);
}

/// Initialize global pools for the current thread
pub fn initialize_pools() -> Result<()> {
    POOLS.with(|p| {
        *p.borrow_mut() = Some(Arc::new(GlobalPools::new()?));
        Ok(())
    })
}

/// Get a reference to the global pools
pub fn with_pools<F, R>(f: F) -> Option<R>
where
    F: FnOnce(&GlobalPools) -> R,
{
    POOLS.with(|p| {
        p.borrow().as_ref().map(|pools| f(pools))
    })
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[derive(Default)]
    struct TestObject {
        value: i32,
        data: Vec<u8>,
    }
    
    impl Poolable for TestObject {
        fn reset(&mut self) {
            self.value = 0;
            self.data.clear();
        }
    }
    
    #[test]
    fn test_object_pool() -> Result<()> {
        let mut pool = ObjectPool::<TestObject>::new(10);
        
        // Get object from pool
        let mut obj1 = pool.get()?;
        obj1.value = 42;
        obj1.data.push(1);
        
        // Drop returns to pool
        drop(obj1);
        
        assert_eq!(pool.available_count()?, 1);
        
        // Get again - should be reset
        let obj2 = pool.get()?;
        assert_eq!(obj2.value, 0);
        assert_eq!(obj2.data.len(), 0);
        
        Ok(())
    }
    
    #[test]
    fn test_vec_pool() -> Result<()> {
        let pool = VecPool::<i32>::new(10, 1000);
        
        let mut vec1 = pool.get()?;
        vec1.extend(&[1, 2, 3, 4, 5]);
        
        let capacity = vec1.capacity();
        drop(vec1);
        
        // Get again - should reuse allocation
        let vec2 = pool.get()?;
        assert!(vec2.capacity() >= capacity);
        assert_eq!(vec2.len(), 0);
        
        Ok(())
    }
    
    #[test]
    fn test_computation_cache() -> Result<()> {
        let cache = ComputationCache::<i32, i32>::new(10)?;
        
        let mut compute_count = 0;
        
        // First call computes
        let result1 = cache.get_or_compute(5, || {
            compute_count += 1;
            5 * 5
        })?;
        assert_eq!(result1, 25);
        assert_eq!(compute_count, 1);
        
        // Second call uses cache
        let result2 = cache.get_or_compute(5, || {
            compute_count += 1;
            5 * 5
        })?;
        assert_eq!(result2, 25);
        assert_eq!(compute_count, 1); // Not computed again
        
        Ok(())
    }
}