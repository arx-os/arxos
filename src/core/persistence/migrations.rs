//! Database Migration System
//! 
//! Manages schema versioning and migrations with:
//! - Automatic migration detection and execution
//! - Rollback support for failed migrations
//! - Version tracking in database

use crate::error::ArxError;

type Result<T> = std::result::Result<T, ArxError>;
use super::connection_pool::ConnectionPool;

/// Migration manager for schema versioning
pub struct MigrationManager {
    migrations: Vec<Migration>,
}

/// A single migration
struct Migration {
    version: u32,
    name: &'static str,
    up_sql: &'static str,
    down_sql: Option<&'static str>,
}

impl MigrationManager {
    /// Create a new migration manager
    pub fn new() -> Self {
        Self {
            migrations: Self::get_migrations(),
        }
    }
    
    /// Run all pending migrations
    pub fn migrate(&self, pool: &ConnectionPool) -> Result<()> {
        let conn = pool.get()?;
        
        // Ensure migrations table exists
        conn.execute(
            "CREATE TABLE IF NOT EXISTS schema_migrations (
                version INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )",
            [],
        )?;
        
        // Get current version
        let current_version = self.get_current_version(&conn)?;
        
        // Apply pending migrations
        for migration in &self.migrations {
            if migration.version > current_version {
                self.apply_migration(&conn, migration)?;
            }
        }
        
        Ok(())
    }
    
    /// Rollback to a specific version
    pub fn rollback_to(&self, pool: &ConnectionPool, target_version: u32) -> Result<()> {
        let conn = pool.get()?;
        
        let current_version = self.get_current_version(&conn)?;
        
        if target_version >= current_version {
            return Ok(()); // Nothing to rollback
        }
        
        // Rollback migrations in reverse order
        for migration in self.migrations.iter().rev() {
            if migration.version > target_version && migration.version <= current_version {
                self.rollback_migration(&conn, migration)?;
            }
        }
        
        Ok(())
    }
    
    /// Get current schema version
    fn get_current_version(&self, conn: &super::connection_pool::PooledConnection) -> Result<u32> {
        let version: Result<i64> = conn.query_row(
            "SELECT COALESCE(MAX(version), 0) FROM schema_migrations",
            [],
            |row| row.get(0),
        );
        
        match version {
            Ok(v) => Ok(v as u32),
            Err(_) => Ok(0), // Table doesn't exist yet
        }
    }
    
    /// Apply a single migration
    fn apply_migration(&self, conn: &super::connection_pool::PooledConnection, migration: &Migration) -> Result<()> {
        println!("Applying migration {}: {}", migration.version, migration.name);
        
        // Start transaction
        conn.execute("BEGIN IMMEDIATE", [])?;
        
        // Apply migration
        if let Err(e) = conn.execute_batch(migration.up_sql) {
            conn.execute("ROLLBACK", [])?;
            return Err(ArxError::InvalidInput(
                format!("Migration {} failed: {}", migration.version, e)
            ));
        }
        
        // Record migration
        if let Err(e) = conn.execute(
            "INSERT INTO schema_migrations (version, name) VALUES (?1, ?2)",
            rusqlite::params![migration.version, migration.name],
        ) {
            conn.execute("ROLLBACK", [])?;
            return Err(ArxError::InvalidInput(
                format!("Failed to record migration {}: {}", migration.version, e)
            ));
        }
        
        // Commit
        conn.execute("COMMIT", [])?;
        
        Ok(())
    }
    
    /// Rollback a single migration
    fn rollback_migration(&self, conn: &super::connection_pool::PooledConnection, migration: &Migration) -> Result<()> {
        if migration.down_sql.is_none() {
            return Err(ArxError::InvalidInput(
                format!("Migration {} cannot be rolled back", migration.version)
            ));
        }
        
        println!("Rolling back migration {}: {}", migration.version, migration.name);
        
        // Start transaction
        conn.execute("BEGIN IMMEDIATE", [])?;
        
        // Rollback migration
        if let Err(e) = conn.execute_batch(migration.down_sql.unwrap()) {
            conn.execute("ROLLBACK", [])?;
            return Err(ArxError::InvalidInput(
                format!("Rollback of migration {} failed: {}", migration.version, e)
            ));
        }
        
        // Remove migration record
        if let Err(e) = conn.execute(
            "DELETE FROM schema_migrations WHERE version = ?1",
            rusqlite::params![migration.version],
        ) {
            conn.execute("ROLLBACK", [])?;
            return Err(ArxError::InvalidInput(
                format!("Failed to remove migration record {}: {}", migration.version, e)
            ));
        }
        
        // Commit
        conn.execute("COMMIT", [])?;
        
        Ok(())
    }
    
    /// Get all defined migrations
    fn get_migrations() -> Vec<Migration> {
        vec![
            Migration {
                version: 1,
                name: "Initial schema",
                up_sql: super::schema::SCHEMA,
                down_sql: Some(
                    "DROP TABLE IF EXISTS cluster_members;
                     DROP TABLE IF EXISTS consciousness_clusters;
                     DROP TABLE IF EXISTS entanglement_network;
                     DROP TABLE IF EXISTS temporal_states;
                     DROP TABLE IF EXISTS spatial_index;
                     DROP TABLE IF EXISTS consciousness_fields;
                     DROP TABLE IF EXISTS quantum_states;
                     DROP TABLE IF EXISTS arxobjects;
                     DROP TABLE IF EXISTS reality_cache;
                     DROP TABLE IF EXISTS db_metadata;"
                ),
            },
            Migration {
                version: 2,
                name: "Add performance indexes",
                up_sql: "
                    CREATE INDEX IF NOT EXISTS idx_arxobjects_composite 
                    ON arxobjects(building_id, object_type, x, y, z);
                    
                    CREATE INDEX IF NOT EXISTS idx_quantum_states_type 
                    ON quantum_states(state_type);
                    
                    CREATE INDEX IF NOT EXISTS idx_consciousness_fields_composite 
                    ON consciousness_fields(arxobject_id, phi);
                    
                    ANALYZE;
                ",
                down_sql: Some(
                    "DROP INDEX IF EXISTS idx_arxobjects_composite;
                     DROP INDEX IF EXISTS idx_quantum_states_type;
                     DROP INDEX IF EXISTS idx_consciousness_fields_composite;"
                ),
            },
            Migration {
                version: 3,
                name: "Add observer tracking",
                up_sql: "
                    CREATE TABLE IF NOT EXISTS observer_sessions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        observer_role TEXT NOT NULL,
                        session_id TEXT UNIQUE NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_active_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        observation_count INTEGER DEFAULT 0
                    );
                    
                    CREATE TABLE IF NOT EXISTS observations (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        session_id INTEGER NOT NULL,
                        arxobject_id INTEGER NOT NULL,
                        scale REAL NOT NULL,
                        observed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        
                        FOREIGN KEY (session_id) REFERENCES observer_sessions(id) ON DELETE CASCADE,
                        FOREIGN KEY (arxobject_id) REFERENCES arxobjects(id) ON DELETE CASCADE
                    );
                    
                    CREATE INDEX idx_observations_session ON observations(session_id);
                    CREATE INDEX idx_observations_arxobject ON observations(arxobject_id);
                ",
                down_sql: Some(
                    "DROP TABLE IF EXISTS observations;
                     DROP TABLE IF EXISTS observer_sessions;"
                ),
            },
        ]
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use tempfile::tempdir;
    
    #[test]
    fn test_migrations() -> Result<()> {
        let dir = tempdir().unwrap();
        let db_path = dir.path().join("test.db");
        
        let pool = ConnectionPool::new(&db_path, 5)?;
        let manager = MigrationManager::new();
        
        // Run migrations
        manager.migrate(&pool)?;
        
        // Check version
        let conn = pool.get()?;
        let version = manager.get_current_version(&conn)?;
        assert_eq!(version, 3); // We have 3 migrations defined
        
        // Check tables exist
        let count: i64 = conn.query_row(
            "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='arxobjects'",
            [],
            |row| row.get(0),
        )?;
        assert_eq!(count, 1);
        
        Ok(())
    }
    
    #[test]
    fn test_rollback() -> Result<()> {
        let dir = tempdir().unwrap();
        let db_path = dir.path().join("test.db");
        
        let pool = ConnectionPool::new(&db_path, 5)?;
        let manager = MigrationManager::new();
        
        // Run migrations
        manager.migrate(&pool)?;
        
        // Rollback to version 1
        manager.rollback_to(&pool, 1)?;
        
        // Check version
        let conn = pool.get()?;
        let version = manager.get_current_version(&conn)?;
        assert_eq!(version, 1);
        
        // Check that observer tables don't exist
        let count: i64 = conn.query_row(
            "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='observer_sessions'",
            [],
            |row| row.get(0),
        )?;
        assert_eq!(count, 0);
        
        Ok(())
    }
}