//! Connection Pool for SQLite
//! 
//! Provides efficient connection pooling with:
//! - Configurable pool size
//! - Automatic connection recycling
//! - Health checks and recovery
//! - Async-friendly blocking with timeout

use std::path::{Path, PathBuf};
use std::sync::{Arc, Mutex, Condvar};
use std::time::{Duration, Instant};
use std::collections::VecDeque;
use rusqlite::{Connection, OpenFlags};
use crate::error::ArxError;

type Result<T> = std::result::Result<T, ArxError>;

/// A pooled database connection
pub struct PooledConnection<'a> {
    conn: Option<Connection>,
    pool: &'a ConnectionPool,
}

impl<'a> PooledConnection<'a> {
    /// Execute a SQL statement
    pub fn execute<P: rusqlite::Params>(&self, sql: &str, params: P) -> Result<usize> {
        self.conn
            .as_ref()
            .ok_or_else(|| ArxError::InvalidArxObject("Connection already returned".to_string()))?
            .execute(sql, params)
            .map_err(|e| ArxError::InvalidArxObject(format!("SQL error: {}", e)))
    }
    
    /// Prepare a SQL statement
    pub fn prepare(&self, sql: &str) -> Result<rusqlite::Statement> {
        self.conn
            .as_ref()
            .ok_or_else(|| ArxError::InvalidArxObject("Connection already returned".to_string()))?
            .prepare(sql)
            .map_err(|e| ArxError::InvalidArxObject(format!("SQL error: {}", e)))
    }
    
    /// Query a single row
    pub fn query_row<T, P, F>(&self, sql: &str, params: P, f: F) -> Result<T>
    where
        P: rusqlite::Params,
        F: FnOnce(&rusqlite::Row<'_>) -> rusqlite::Result<T>,
    {
        self.conn
            .as_ref()
            .ok_or_else(|| ArxError::InvalidArxObject("Connection already returned".to_string()))?
            .query_row(sql, params, f)
            .map_err(|e| ArxError::InvalidArxObject(format!("SQL error: {}", e)))
    }
    
    /// Get the last insert row ID
    pub fn last_insert_rowid(&self) -> i64 {
        self.conn
            .as_ref()
            .map(|c| c.last_insert_rowid())
            .unwrap_or(0)
    }
}

impl<'a> Drop for PooledConnection<'a> {
    fn drop(&mut self) {
        if let Some(conn) = self.conn.take() {
            self.pool.return_connection(conn);
        }
    }
}

impl<'a> std::ops::Deref for PooledConnection<'a> {
    type Target = Connection;
    
    fn deref(&self) -> &Self::Target {
        self.conn.as_ref().expect("Connection already returned")
    }
}

/// Thread-safe connection pool
pub struct ConnectionPool {
    inner: Arc<ConnectionPoolInner>,
}

impl Clone for ConnectionPool {
    fn clone(&self) -> Self {
        Self {
            inner: Arc::clone(&self.inner),
        }
    }
}

struct ConnectionPoolInner {
    path: PathBuf,
    connections: Mutex<VecDeque<Connection>>,
    condvar: Condvar,
    max_connections: usize,
    active_connections: Mutex<usize>,
    wait_timeout: Duration,
}

impl ConnectionPool {
    /// Create a new connection pool
    pub fn new<P: AsRef<Path>>(path: P, max_connections: usize) -> Result<Self> {
        let path = path.as_ref().to_path_buf();
        
        // Pre-create one connection to ensure database is accessible
        let test_conn = Self::create_connection(&path)?;
        
        // Run initialization pragmas
        test_conn.execute_batch(crate::persistence::schema::ENABLE_FOREIGN_KEYS)?;
        test_conn.execute_batch(crate::persistence::schema::SET_WAL_MODE)?;
        test_conn.execute_batch(crate::persistence::schema::SET_SYNCHRONOUS)?;
        test_conn.execute_batch(crate::persistence::schema::SET_CACHE_SIZE)?;
        test_conn.execute_batch(crate::persistence::schema::SET_TEMP_STORE)?;
        
        let mut connections = VecDeque::with_capacity(max_connections);
        connections.push_back(test_conn);
        
        Ok(Self {
            inner: Arc::new(ConnectionPoolInner {
                path,
                connections: Mutex::new(connections),
                condvar: Condvar::new(),
                max_connections,
                active_connections: Mutex::new(0),
                wait_timeout: Duration::from_secs(30),
            }),
        })
    }
    
    /// Get a connection from the pool
    pub fn get(&self) -> Result<PooledConnection> {
        let deadline = Instant::now() + self.inner.wait_timeout;
        
        loop {
            // Try to get an existing connection
            {
                let mut connections = self.inner.connections
                    .lock()
                    .map_err(|_| ArxError::InvalidArxObject("Pool mutex poisoned".to_string()))?;
                
                if let Some(conn) = connections.pop_front() {
                    // Verify connection is still valid
                    if Self::check_connection(&conn) {
                        let mut active = self.inner.active_connections
                            .lock()
                            .map_err(|_| ArxError::InvalidArxObject("Active count mutex poisoned".to_string()))?;
                        *active += 1;
                        
                        return Ok(PooledConnection {
                            conn: Some(conn),
                            pool: self,
                        });
                    }
                    // Connection is bad, don't return it to pool
                }
            }
            
            // Try to create a new connection if under limit
            {
                let active = self.inner.active_connections
                    .lock()
                    .map_err(|_| ArxError::InvalidArxObject("Active count mutex poisoned".to_string()))?;
                
                if *active < self.inner.max_connections {
                    drop(active); // Release lock before creating connection
                    
                    let conn = Self::create_connection(&self.inner.path)?;
                    
                    let mut active = self.inner.active_connections
                        .lock()
                        .map_err(|_| ArxError::InvalidArxObject("Active count mutex poisoned".to_string()))?;
                    *active += 1;
                    
                    return Ok(PooledConnection {
                        conn: Some(conn),
                        pool: self,
                    });
                }
            }
            
            // Wait for a connection to be returned
            let now = Instant::now();
            if now >= deadline {
                return Err(ArxError::InvalidArxObject(
                    "Timeout waiting for database connection".to_string()
                ));
            }
            
            let timeout = deadline - now;
            let (connections, timeout_result) = self.inner.condvar
                .wait_timeout(
                    self.inner.connections.lock()
                        .map_err(|_| ArxError::InvalidArxObject("Pool mutex poisoned".to_string()))?,
                    timeout
                )
                .map_err(|_| ArxError::InvalidArxObject("Condvar wait failed".to_string()))?;
            
            drop(connections); // Release lock before next iteration
            
            if timeout_result.timed_out() {
                return Err(ArxError::InvalidArxObject(
                    "Timeout waiting for database connection".to_string()
                ));
            }
        }
    }
    
    /// Return a connection to the pool
    fn return_connection(&self, conn: Connection) {
        // Check if connection is still good before returning
        if !Self::check_connection(&conn) {
            // Connection is bad, don't return it
            if let Ok(mut active) = self.inner.active_connections.lock() {
                *active = active.saturating_sub(1);
            }
            return;
        }
        
        if let Ok(mut connections) = self.inner.connections.lock() {
            connections.push_back(conn);
            if let Ok(mut active) = self.inner.active_connections.lock() {
                *active = active.saturating_sub(1);
            }
            self.inner.condvar.notify_one();
        }
    }
    
    /// Create a new database connection
    fn create_connection(path: &Path) -> Result<Connection> {
        let conn = Connection::open_with_flags(
            path,
            OpenFlags::SQLITE_OPEN_READ_WRITE 
                | OpenFlags::SQLITE_OPEN_CREATE
                | OpenFlags::SQLITE_OPEN_NO_MUTEX
                | OpenFlags::SQLITE_OPEN_URI
        ).map_err(|e| ArxError::InvalidArxObject(format!("Failed to open database: {}", e)))?;
        
        // Set connection-specific pragmas
        conn.execute_batch(crate::persistence::schema::ENABLE_FOREIGN_KEYS)?;
        conn.busy_timeout(Duration::from_secs(5))?;
        
        Ok(conn)
    }
    
    /// Check if a connection is still valid
    fn check_connection(conn: &Connection) -> bool {
        conn.execute("SELECT 1", []).is_ok()
    }
    
    /// Get pool statistics
    pub fn stats(&self) -> super::PoolStats {
        let available = self.inner.connections
            .lock()
            .map(|c| c.len())
            .unwrap_or(0);
        
        let active = self.inner.active_connections
            .lock()
            .map(|a| *a)
            .unwrap_or(0);
        
        super::PoolStats {
            total_connections: active + available,
            available_connections: available,
            waiting_tasks: 0, // Would need to track this separately
        }
    }
    
    /// Clear all connections from the pool
    pub fn clear(&self) -> Result<()> {
        let mut connections = self.inner.connections
            .lock()
            .map_err(|_| ArxError::InvalidArxObject("Pool mutex poisoned".to_string()))?;
        
        connections.clear();
        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use tempfile::tempdir;
    
    #[test]
    fn test_connection_pool() -> Result<()> {
        let dir = tempdir().unwrap();
        let db_path = dir.path().join("test.db");
        
        let pool = ConnectionPool::new(&db_path, 5)?;
        
        // Get multiple connections
        let conn1 = pool.get()?;
        let conn2 = pool.get()?;
        
        // Use connections
        conn1.execute("CREATE TABLE test (id INTEGER)", [])?;
        conn2.execute("INSERT INTO test VALUES (1)", [])?;
        
        // Return connections
        drop(conn1);
        drop(conn2);
        
        // Get connection again (should reuse)
        let conn3 = pool.get()?;
        let count: i64 = conn3.query_row(
            "SELECT COUNT(*) FROM test",
            [],
            |row| row.get(0)
        )?;
        
        assert_eq!(count, 1);
        
        Ok(())
    }
    
    #[test]
    fn test_pool_limits() -> Result<()> {
        let dir = tempdir().unwrap();
        let db_path = dir.path().join("test.db");
        
        let pool = ConnectionPool::new(&db_path, 2)?;
        
        // Get max connections
        let conn1 = pool.get()?;
        let conn2 = pool.get()?;
        
        // Try to get another (should wait/timeout)
        let pool_clone = pool.clone();
        let handle = std::thread::spawn(move || {
            std::thread::sleep(Duration::from_millis(100));
            pool_clone.get()
        });
        
        // Return one connection
        drop(conn1);
        
        // Thread should now get a connection
        let result = handle.join().unwrap();
        assert!(result.is_ok());
        
        Ok(())
    }
}