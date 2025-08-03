"""
SVGX Engine - Database Integration

Comprehensive database integration with connection pooling,
query optimization, and transaction management.
"""

import sqlite3
import threading
import time
import json
import logging
from typing import Dict, Any, Optional, List, Union, Tuple
from dataclasses import dataclass
from datetime import datetime
from contextlib import contextmanager
from enum import Enum
import queue

logger = logging.getLogger(__name__)


class DatabaseType(Enum):
    """Database types."""
    SQLITE = "sqlite"
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"


class ConnectionState(Enum):
    """Connection states."""
    IDLE = "idle"
    IN_USE = "in_use"
    ERROR = "error"
    CLOSED = "closed"


@dataclass
class DatabaseConfig:
    """Database configuration."""
    db_type: DatabaseType = DatabaseType.SQLITE
    host: Optional[str] = None
    port: Optional[int] = None
    database: str = "svgx_engine.db"
    username: Optional[str] = None
    password: Optional[str] = None
    max_connections: int = 10
    connection_timeout: int = 30
    query_timeout: int = 60
    enable_logging: bool = True
    enable_metrics: bool = True


@dataclass
class QueryResult:
    """Query result structure."""
    success: bool
    data: Optional[List[Dict[str, Any]]] = None
    error: Optional[str] = None
    rows_affected: int = 0
    execution_time_ms: float = 0.0


class DatabaseConnection:
    """Database connection wrapper."""
    
    def __init__(self, config: DatabaseConfig):
    """
    Perform __init__ operation

Args:
        config: Description of config

Returns:
        Description of return value

Raises:
        Exception: Description of exception

Example:
        result = __init__(param)
        print(result)
    """
        self.config = config
        self.connection = None
        self.state = ConnectionState.IDLE
        self.last_used = None
        self.query_count = 0
        self.error_count = 0
        self._lock = threading.Lock()
    
    def connect(self) -> bool:
        """Establish database connection."""
        try:
            if self.config.db_type == DatabaseType.SQLITE:
                self.connection = sqlite3.connect(
                    self.config.database,
                    timeout=self.config.connection_timeout,
                    check_same_thread=False
                )
                # Enable foreign keys
                self.connection.execute("PRAGMA foreign_keys = ON")
                # Enable WAL mode for better concurrency
                self.connection.execute("PRAGMA journal_mode = WAL")
            else:
                # Placeholder for other database types
                logger.warning(f"Database type {self.config.db_type} not implemented")
                return False
            
            self.state = ConnectionState.IDLE
            self.last_used = datetime.now()
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            self.state = ConnectionState.ERROR
            return False
    
    def disconnect(self):
        """Close database connection."""
        try:
            if self.connection:
                self.connection.close()
            self.state = ConnectionState.CLOSED
        except Exception as e:
            logger.error(f"Error disconnecting from database: {e}")
    
    def execute(self, query: str, params: Optional[Tuple] = None) -> QueryResult:
        """Execute a query."""
        start_time = time.time()
        
        try:
            if not self.connection:
                return QueryResult(success=False, error="No database connection")
            
            cursor = self.connection.cursor()
            
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            # Get results
            if query.strip().upper().startswith('SELECT'):
                columns = [description[0] for description in cursor.description]
                rows = cursor.fetchall()
                data = [dict(zip(columns, row)) for row in rows]
            else:
                data = None
                self.connection.commit()
            
            execution_time = (time.time() - start_time) * 1000
            
            # Update stats
            with self._lock:
                self.query_count += 1
                self.last_used = datetime.now()
            
            return QueryResult(
                success=True,
                data=data,
                rows_affected=cursor.rowcount,
                execution_time_ms=execution_time
            )
            
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            logger.error(f"Query execution failed: {e}")
            
            with self._lock:
                self.error_count += 1
                self.state = ConnectionState.ERROR
            
            return QueryResult(
                success=False,
                error=str(e),
                execution_time_ms=execution_time
            )
    
    def is_healthy(self) -> bool:
        """Check if connection is healthy."""
        if not self.connection:
            return False
        
        try:
            # Simple health check query
            cursor = self.connection.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            return True
        except Exception:
            return False


class ConnectionPool:
    """
    Perform __init__ operation

Args:
        config: Description of config

Returns:
        Description of return value

Raises:
        Exception: Description of exception

Example:
        result = __init__(param)
        print(result)
    """
    """Database connection pool."""
    
    def __init__(self, config: DatabaseConfig):
        self.config = config
        self.connections: List[DatabaseConnection] = []
        self.available_connections: queue.Queue = queue.Queue()
        self.in_use_connections: set = set()
        self._lock = threading.RLock()
        self._initialize_pool()
    
    def _initialize_pool(self):
        """Initialize connection pool."""
        for _ in range(self.config.max_connections):
            conn = DatabaseConnection(self.config)
            if conn.connect():
                self.connections.append(conn)
                self.available_connections.put(conn)
    
    def get_connection(self, timeout: int = 30) -> Optional[DatabaseConnection]:
        """Get a connection from the pool."""
        try:
            # Try to get an available connection
            conn = self.available_connections.get(timeout=timeout)
            
            with self._lock:
                if conn in self.in_use_connections:
                    # Connection already in use, try again
                    self.available_connections.put(conn)
                    return self.get_connection(timeout)
                
                # Check if connection is healthy
                if not conn.is_healthy():
                    # Replace unhealthy connection
                    self._replace_connection(conn)
                    return self.get_connection(timeout)
                
                conn.state = ConnectionState.IN_USE
                self.in_use_connections.add(conn)
                return conn
                
        except queue.Empty:
            logger.error("No available database connections")
            return None
    
    def return_connection(self, conn: DatabaseConnection):
        """Return a connection to the pool."""
        with self._lock:
            if conn in self.in_use_connections:
                self.in_use_connections.remove(conn)
                conn.state = ConnectionState.IDLE
                self.available_connections.put(conn)
    
    def _replace_connection(self, conn: DatabaseConnection):
        """Replace an unhealthy connection."""
        try:
            conn.disconnect()
            self.connections.remove(conn)
            
            # Create new connection
            new_conn = DatabaseConnection(self.config)
            if new_conn.connect():
                self.connections.append(new_conn)
                self.available_connections.put(new_conn)
            else:
                logger.error("Failed to create replacement connection")
                
        except Exception as e:
            logger.error(f"Error replacing connection: {e}")
    
    def close_all(self):
        """Close all connections."""
        with self._lock:
            for conn in self.connections:
                conn.disconnect()
            self.connections.clear()
            while not self.available_connections.empty():
                try:
                    self.available_connections.get_nowait()
                except queue.Empty:
                    break
    
    def get_stats(self) -> Dict[str, Any]:
        """Get connection pool statistics."""
        with self._lock:
            total_queries = sum(conn.query_count for conn in self.connections)
            total_errors = sum(conn.error_count for conn in self.connections)
            
            return {
                'total_connections': len(self.connections),
                'available_connections': self.available_connections.qsize(),
                'in_use_connections': len(self.in_use_connections),
                'total_queries': total_queries,
                'total_errors': total_errors,
                'error_rate': total_errors / max(total_queries, 1)
            }


class DatabaseManager:
    """Database manager for SVGX Engine."""
    
    def __init__(self, config: Optional[DatabaseConfig] = None):
        self.config = config or DatabaseConfig()
        self.pool = ConnectionPool(self.config)
        self._initialize_database()
    
    def _initialize_database(self):
        """Initialize database schema."""
        try:
            with self.get_connection() as conn:
                if conn:
                    # Create tables if they don't exist
                    self._create_tables(conn)
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
    
    def _create_tables(self, conn: DatabaseConnection):
        """Create database tables."""
        tables = [
            """
            CREATE TABLE IF NOT EXISTS svgx_documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                metadata TEXT,
                user_id TEXT,
                version INTEGER DEFAULT 1
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS svgx_elements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_id INTEGER,
                element_type TEXT NOT NULL,
                element_data TEXT NOT NULL,
                position_x REAL,
                position_y REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (document_id) REFERENCES svgx_documents (id)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS svgx_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT UNIQUE NOT NULL,
                user_id TEXT,
                data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS svgx_cache (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                ttl INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                accessed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS svgx_telemetry (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT NOT NULL,
                event_data TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                user_id TEXT,
                session_id TEXT
            )
            """
        ]
        
        for table_sql in tables:
            result = conn.execute(table_sql)
            if not result.success:
                logger.error(f"Failed to create table: {result.error}")
    
    @contextmanager
    def get_connection(self):
        """Get a database connection with context manager."""
        conn = self.pool.get_connection()
        try:
            yield conn
        finally:
            if conn:
                self.pool.return_connection(conn)
    
    def execute_query(self, query: str, params: Optional[Tuple] = None) -> QueryResult:
        """Execute a database query."""
        with self.get_connection() as conn:
            if conn:
                return conn.execute(query, params)
            else:
                return QueryResult(success=False, error="No database connection available")
    
    def insert_document(self, name: str, content: str, user_id: Optional[str] = None,
                       metadata: Optional[Dict[str, Any]] = None) -> QueryResult:
        """Insert a new SVGX document."""
        query = """
        INSERT INTO svgx_documents (name, content, user_id, metadata)
        VALUES (?, ?, ?, ?)
        """
        metadata_json = json.dumps(metadata) if metadata else None
        params = (name, content, user_id, metadata_json)
        return self.execute_query(query, params)
    
    def get_document(self, document_id: int) -> QueryResult:
        """Get a document by ID."""
        query = "SELECT * FROM svgx_documents WHERE id = ?"
        return self.execute_query(query, (document_id,))
    
    def update_document(self, document_id: int, content: str, metadata: Optional[Dict[str, Any]] = None) -> QueryResult:
        """Update a document."""
        query = """
        UPDATE svgx_documents 
        SET content = ?, metadata = ?, updated_at = CURRENT_TIMESTAMP, version = version + 1
        WHERE id = ?
        """
        metadata_json = json.dumps(metadata) if metadata else None
        params = (content, metadata_json, document_id)
        return self.execute_query(query, params)
    
    def delete_document(self, document_id: int) -> QueryResult:
        """Delete a document."""
        query = "DELETE FROM svgx_documents WHERE id = ?"
        return self.execute_query(query, (document_id,))
    
    def list_documents(self, user_id: Optional[str] = None, limit: int = 100) -> QueryResult:
        """List documents."""
        if user_id:
            query = "SELECT * FROM svgx_documents WHERE user_id = ? ORDER BY updated_at DESC LIMIT ?"
            params = (user_id, limit)
        else:
            query = "SELECT * FROM svgx_documents ORDER BY updated_at DESC LIMIT ?"
            params = (limit,)
        return self.execute_query(query, params)
    
    def insert_element(self, document_id: int, element_type: str, element_data: str,
                      position_x: Optional[float] = None, position_y: Optional[float] = None) -> QueryResult:
        """Insert a new element."""
        query = """
        INSERT INTO svgx_elements (document_id, element_type, element_data, position_x, position_y)
        VALUES (?, ?, ?, ?, ?)
        """
        params = (document_id, element_type, element_data, position_x, position_y)
        return self.execute_query(query, params)
    
    def get_document_elements(self, document_id: int) -> QueryResult:
        """Get all elements for a document."""
        query = "SELECT * FROM svgx_elements WHERE document_id = ? ORDER BY id"
        return self.execute_query(query, (document_id,))
    
    def set_session_data(self, session_id: str, data: Dict[str, Any], user_id: Optional[str] = None) -> QueryResult:
        """Set session data."""
        query = """
        INSERT OR REPLACE INTO svgx_sessions (session_id, user_id, data, updated_at)
        VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        """
        data_json = json.dumps(data)
        params = (session_id, user_id, data_json)
        return self.execute_query(query, params)
    
    def get_session_data(self, session_id: str) -> QueryResult:
        """Get session data."""
        query = "SELECT * FROM svgx_sessions WHERE session_id = ?"
        return self.execute_query(query, (session_id,))
    
    def delete_session(self, session_id: str) -> QueryResult:
        """Delete session data."""
        query = "DELETE FROM svgx_sessions WHERE session_id = ?"
        return self.execute_query(query, (session_id,))
    
    def log_telemetry(self, event_type: str, event_data: Optional[Dict[str, Any]] = None,
                      user_id: Optional[str] = None, session_id: Optional[str] = None) -> QueryResult:
        """Log telemetry event."""
        query = """
        INSERT INTO svgx_telemetry (event_type, event_data, user_id, session_id)
        VALUES (?, ?, ?, ?)
        """
        event_data_json = json.dumps(event_data) if event_data else None
        params = (event_type, event_data_json, user_id, session_id)
        return self.execute_query(query, params)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get database statistics."""
        pool_stats = self.pool.get_stats()
        
        # Get table statistics
        stats_query = """
        SELECT 
            (SELECT COUNT(*) FROM svgx_documents) as document_count,
            (SELECT COUNT(*) FROM svgx_elements) as element_count,
            (SELECT COUNT(*) FROM svgx_sessions) as session_count,
            (SELECT COUNT(*) FROM svgx_telemetry) as telemetry_count
        """
        result = self.execute_query(stats_query)
        
        if result.success and result.data:
            table_stats = result.data[0]
        else:
            table_stats = {}
        
        return {
            'pool_stats': pool_stats,
            'table_stats': table_stats
        }
    
    def close(self):
        """Close database manager."""
        self.pool.close_all()


# Global database manager instance
_db_manager = None


def get_database_manager() -> DatabaseManager:
    """Get the global database manager."""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager


def setup_database(config: DatabaseConfig):
    """Setup database with custom configuration."""
    global _db_manager
    if _db_manager:
        _db_manager.close()
    _db_manager = DatabaseManager(config)


def execute_query(query: str, params: Optional[Tuple] = None) -> QueryResult:
    """Execute a database query."""
    manager = get_database_manager()
    return manager.execute_query(query, params)


def insert_document(name: str, content: str, user_id: Optional[str] = None,
                   metadata: Optional[Dict[str, Any]] = None) -> QueryResult:
    """Insert a new SVGX document."""
    manager = get_database_manager()
    return manager.insert_document(name, content, user_id, metadata)


def get_document(document_id: int) -> QueryResult:
    """Get a document by ID."""
    manager = get_database_manager()
    return manager.get_document(document_id)


def update_document(document_id: int, content: str, metadata: Optional[Dict[str, Any]] = None) -> QueryResult:
    """Update a document."""
    manager = get_database_manager()
    return manager.update_document(document_id, content, metadata)


def delete_document(document_id: int) -> QueryResult:
    """Delete a document."""
    manager = get_database_manager()
    return manager.delete_document(document_id)


def list_documents(user_id: Optional[str] = None, limit: int = 100) -> QueryResult:
    """List documents."""
    manager = get_database_manager()
    return manager.list_documents(user_id, limit)


def set_session_data(session_id: str, data: Dict[str, Any], user_id: Optional[str] = None) -> QueryResult:
    """Set session data."""
    manager = get_database_manager()
    return manager.set_session_data(session_id, data, user_id)


def get_session_data(session_id: str) -> QueryResult:
    """Get session data."""
    manager = get_database_manager()
    return manager.get_session_data(session_id)


def delete_session(session_id: str) -> QueryResult:
    """Delete session data."""
    manager = get_database_manager()
    return manager.delete_session(session_id)


def log_telemetry(event_type: str, event_data: Optional[Dict[str, Any]] = None,
                  user_id: Optional[str] = None, session_id: Optional[str] = None) -> QueryResult:
    """Log telemetry event."""
    manager = get_database_manager()
    return manager.log_telemetry(event_type, event_data, user_id, session_id)


def get_database_stats() -> Dict[str, Any]:
    """Get database statistics."""
    manager = get_database_manager()
    return manager.get_stats()


def close_database():
    """Close database connections."""
    global _db_manager
    if _db_manager:
        _db_manager.close()
        _db_manager = None 