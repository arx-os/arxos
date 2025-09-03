//! Lightweight Persistence Layer for ArxOS
//! 
//! Simple SQLite storage for routing tables and ArxObjects.
//! No heavy processing - just basic storage and retrieval.

pub mod schema;
pub mod arxobject_store;
pub mod connection_pool;
pub mod migrations;

pub use arxobject_store::ArxObjectStore;
pub use connection_pool::{ConnectionPool, PooledConnection};
pub use migrations::MigrationManager;

/// Pool statistics
#[derive(Debug, Clone)]
pub struct PoolStats {
    pub total_connections: usize,
    pub active_connections: usize,
    pub idle_connections: usize,
    pub wait_count: usize,
    pub wait_time_ms: u64,
}

use std::path::Path;

/// Lightweight persistence manager for ArxOS routing data
pub struct PersistenceManager {
    pool: ConnectionPool,
    arxobject_store: ArxObjectStore,
}

impl PersistenceManager {
    /// Create a new persistence manager with database at given path
    pub fn new<P: AsRef<Path>>(db_path: P) -> Result<Self, Box<dyn std::error::Error>> {
        let pool = ConnectionPool::new(db_path.as_ref(), 10)?;
        
        // Run migrations to ensure schema is up to date
        let migration_manager = MigrationManager::new();
        migration_manager.migrate(&pool)?;
        
        Ok(Self {
            arxobject_store: ArxObjectStore::new(pool.clone()),
            pool,
        })
    }
    
    /// Get the ArxObject store for basic storage operations
    pub fn arxobjects(&self) -> &ArxObjectStore {
        &self.arxobject_store
    }
    
    /// Get connection pool for custom queries
    pub fn pool(&self) -> &ConnectionPool {
        &self.pool
    }
}

/// Simple routing table entry
#[derive(Debug, Clone)]
pub struct RouteEntry {
    pub destination: u16,
    pub next_hop: u16,
    pub metric: u16,
    pub timestamp: i64,
}

/// Store for mesh routing tables (lightweight)
pub struct RoutingStore {
    pool: ConnectionPool,
}

impl RoutingStore {
    pub fn new(pool: ConnectionPool) -> Self {
        Self { pool }
    }
    
    /// Store a route entry
    pub fn store_route(&self, _route: &RouteEntry) -> Result<(), Box<dyn std::error::Error>> {
        // Simple SQL insert for routing table
        Ok(())
    }
    
    /// Get route to destination
    pub fn get_route(&self, _destination: u16) -> Result<Option<RouteEntry>, Box<dyn std::error::Error>> {
        // Simple SQL query for route
        Ok(None)
    }
}