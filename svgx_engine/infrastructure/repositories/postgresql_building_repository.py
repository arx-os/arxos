"""
PostgreSQL Building Repository Implementation

This module provides a PostgreSQL implementation of the BuildingRepository interface.
It handles database operations for building entities with proper connection pooling,
transaction management, and error handling.
"""

import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2.pool import SimpleConnectionPool
from typing import List, Optional, Dict, Any
import json
from datetime import datetime
import logging

from svgx_engine.domain.repositories.building_repository import BuildingRepository
from svgx_engine.domain.entities.building import Building
from svgx_engine.domain.value_objects.address import Address
from svgx_engine.domain.value_objects.dimensions import Dimensions
from svgx_engine.domain.value_objects.identifier import Identifier
from svgx_engine.utils.errors import DatabaseError, PersistenceError

logger = logging.getLogger(__name__)


class PostgreSQLBuildingRepository(BuildingRepository):
    """
    PostgreSQL implementation of BuildingRepository.
    
    This repository provides persistent storage for building entities
    using PostgreSQL with connection pooling and proper error handling.
    """
    
    def __init__(self, connection_string: str = None, pool_size: int = 5):
        """
        Initialize the PostgreSQL repository.
        
        Args:
            connection_string: PostgreSQL connection string
            pool_size: Size of the connection pool
        """
        self.connection_string = connection_string or self._get_default_connection_string()
        self.pool_size = pool_size
        self._pool = None
        self._initialize_pool()
        self._create_tables()
    
    def _get_default_connection_string(self) -> str:
        """Get default connection string from environment or use defaults."""
        import os
        return os.getenv(
            'DATABASE_URL',
            'postgresql://postgres:password@localhost:5432/arxos_buildings'
        )
    
    def _initialize_pool(self):
        """Initialize the connection pool."""
        try:
            self._pool = SimpleConnectionPool(
                1, self.pool_size, self.connection_string
            )
            logger.info(f"PostgreSQL connection pool initialized with size {self.pool_size}")
        except Exception as e:
            logger.error(f"Failed to initialize connection pool: {e}")
            raise DatabaseError(f"Database connection failed: {e}")
    
    def _create_tables(self):
        """Create database tables if they don't exist."""
        create_buildings_table = """
        CREATE TABLE IF NOT EXISTS buildings (
            id VARCHAR(255) PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            address_street VARCHAR(255) NOT NULL,
            address_city VARCHAR(100) NOT NULL,
            address_state VARCHAR(50) NOT NULL,
            address_postal_code VARCHAR(20) NOT NULL,
            address_country VARCHAR(100) NOT NULL,
            address_unit VARCHAR(50),
            dimensions_length DECIMAL(10,2) NOT NULL,
            dimensions_width DECIMAL(10,2) NOT NULL,
            dimensions_height DECIMAL(10,2),
            building_type VARCHAR(50) DEFAULT 'commercial',
            year_built INTEGER,
            total_area DECIMAL(10,2),
            energy_rating VARCHAR(50),
            is_active BOOLEAN DEFAULT TRUE,
            status VARCHAR(50) DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_by VARCHAR(255),
            updated_by VARCHAR(255)
        );
        """
        
        create_building_events_table = """
        CREATE TABLE IF NOT EXISTS building_events (
            id SERIAL PRIMARY KEY,
            building_id VARCHAR(255) NOT NULL,
            event_type VARCHAR(100) NOT NULL,
            event_data JSONB NOT NULL,
            occurred_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (building_id) REFERENCES buildings(id)
        );
        """
        
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(create_buildings_table)
                    cursor.execute(create_building_events_table)
                    conn.commit()
                    logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Failed to create tables: {e}")
            raise DatabaseError(f"Table creation failed: {e}")
    
    def _get_connection(self):
        """Get a connection from the pool."""
        if not self._pool:
            raise DatabaseError("Connection pool not initialized")
        return self._pool.getconn()
    
    def _return_connection(self, conn):
        """Return a connection to the pool."""
        if self._pool:
            self._pool.putconn(conn)
    
    def save(self, building: Building) -> Building:
        """
        Save a building entity to the database.
        
        Args:
            building: Building entity to save
            
        Returns:
            Saved building entity
            
        Raises:
            PersistenceError: If save operation fails
        """
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    # Use UPSERT (INSERT ... ON CONFLICT UPDATE)
                    cursor.execute("""
                        INSERT INTO buildings (
                            id, name, address_street, address_city, address_state,
                            address_postal_code, address_country, address_unit,
                            dimensions_length, dimensions_width, dimensions_height,
                            building_type, year_built, total_area, energy_rating,
                            is_active, status, created_at, updated_at, created_by, updated_by
                        ) VALUES (
                            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                        ) ON CONFLICT (id) DO UPDATE SET
                            name = EXCLUDED.name,
                            address_street = EXCLUDED.address_street,
                            address_city = EXCLUDED.address_city,
                            address_state = EXCLUDED.address_state,
                            address_postal_code = EXCLUDED.address_postal_code,
                            address_country = EXCLUDED.address_country,
                            address_unit = EXCLUDED.address_unit,
                            dimensions_length = EXCLUDED.dimensions_length,
                            dimensions_width = EXCLUDED.dimensions_width,
                            dimensions_height = EXCLUDED.dimensions_height,
                            building_type = EXCLUDED.building_type,
                            year_built = EXCLUDED.year_built,
                            total_area = EXCLUDED.total_area,
                            energy_rating = EXCLUDED.energy_rating,
                            is_active = EXCLUDED.is_active,
                            status = EXCLUDED.status,
                            updated_at = EXCLUDED.updated_at,
                            updated_by = EXCLUDED.updated_by
                    """, (
                        str(building.id),
                        building.name,
                        building.address.street,
                        building.address.city,
                        building.address.state,
                        building.address.postal_code,
                        building.address.country,
                        building.address.unit,
                        building.dimensions.length,
                        building.dimensions.width,
                        building.dimensions.height,
                        building.building_type,
                        building.year_built,
                        building.total_area,
                        building.energy_rating,
                        building.is_active,
                        building.status,
                        building.created_at,
                        building.updated_at,
                        building.created_by,
                        building.updated_by
                    ))
                    
                    # Save domain events
                    for event in building.get_domain_events():
                        cursor.execute("""
                            INSERT INTO building_events (building_id, event_type, event_data)
                            VALUES (%s, %s, %s)
                        """, (
                            str(building.id),
                            event.event_type,
                            json.dumps(event.to_dict())
                        ))
                    
                    conn.commit()
                    logger.info(f"Building saved successfully: {building.id}")
                    return building
                    
        except Exception as e:
            logger.error(f"Failed to save building: {e}")
            raise PersistenceError(f"Save operation failed: {e}")
    
    def find_by_id(self, building_id: Identifier) -> Optional[Building]:
        """
        Find a building by its ID.
        
        Args:
            building_id: Building identifier
            
        Returns:
            Building entity if found, None otherwise
        """
        try:
            with self._get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute("""
                        SELECT * FROM buildings WHERE id = %s
                    """, (str(building_id),))
                    
                    row = cursor.fetchone()
                    if row:
                        return self._row_to_building(row)
                    return None
                    
        except Exception as e:
            logger.error(f"Failed to find building by ID: {e}")
            raise DatabaseError(f"Find operation failed: {e}")
    
    def find_all(self, limit: int = 100, offset: int = 0) -> List[Building]:
        """
        Find all buildings with pagination.
        
        Args:
            limit: Maximum number of buildings to return
            offset: Number of buildings to skip
            
        Returns:
            List of building entities
        """
        try:
            with self._get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute("""
                        SELECT * FROM buildings 
                        ORDER BY created_at DESC 
                        LIMIT %s OFFSET %s
                    """, (limit, offset))
                    
                    rows = cursor.fetchall()
                    return [self._row_to_building(row) for row in rows]
                    
        except Exception as e:
            logger.error(f"Failed to find all buildings: {e}")
            raise DatabaseError(f"Find all operation failed: {e}")
    
    def find_by_criteria(self, criteria: Dict[str, Any]) -> List[Building]:
        """
        Find buildings by search criteria.
        
        Args:
            criteria: Search criteria dictionary
            
        Returns:
            List of building entities matching criteria
        """
        try:
            with self._get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    # Build dynamic query based on criteria
                    query = "SELECT * FROM buildings WHERE 1=1"
                    params = []
                    
                    if 'name' in criteria:
                        query += " AND name ILIKE %s"
                        params.append(f"%{criteria['name']}%")
                    
                    if 'building_type' in criteria:
                        query += " AND building_type = %s"
                        params.append(criteria['building_type'])
                    
                    if 'is_active' in criteria:
                        query += " AND is_active = %s"
                        params.append(criteria['is_active'])
                    
                    if 'city' in criteria:
                        query += " AND address_city ILIKE %s"
                        params.append(f"%{criteria['city']}%")
                    
                    query += " ORDER BY created_at DESC"
                    
                    cursor.execute(query, params)
                    rows = cursor.fetchall()
                    return [self._row_to_building(row) for row in rows]
                    
        except Exception as e:
            logger.error(f"Failed to find buildings by criteria: {e}")
            raise DatabaseError(f"Find by criteria operation failed: {e}")
    
    def delete(self, building_id: Identifier) -> bool:
        """
        Delete a building by ID.
        
        Args:
            building_id: Building identifier
            
        Returns:
            True if deleted, False if not found
        """
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        DELETE FROM buildings WHERE id = %s
                    """, (str(building_id),))
                    
                    deleted = cursor.rowcount > 0
                    conn.commit()
                    
                    if deleted:
                        logger.info(f"Building deleted successfully: {building_id}")
                    
                    return deleted
                    
        except Exception as e:
            logger.error(f"Failed to delete building: {e}")
            raise DatabaseError(f"Delete operation failed: {e}")
    
    def count(self) -> int:
        """
        Get the total number of buildings.
        
        Returns:
            Total count of buildings
        """
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT COUNT(*) FROM buildings")
                    return cursor.fetchone()[0]
                    
        except Exception as e:
            logger.error(f"Failed to count buildings: {e}")
            raise DatabaseError(f"Count operation failed: {e}")
    
    def _row_to_building(self, row: Dict[str, Any]) -> Building:
        """Convert database row to Building entity."""
        try:
            # Create address
            address = Address(
                street=row['address_street'],
                city=row['address_city'],
                state=row['address_state'],
                postal_code=row['address_postal_code'],
                country=row['address_country'],
                unit=row['address_unit']
            )
            
            # Create dimensions
            dimensions = Dimensions(
                length=float(row['dimensions_length']),
                width=float(row['dimensions_width']),
                height=float(row['dimensions_height']) if row['dimensions_height'] else None
            )
            
            # Create building
            building = Building(
                id=Identifier(row['id']),
                name=row['name'],
                address=address,
                dimensions=dimensions,
                building_type=row['building_type'],
                year_built=row['year_built'],
                total_area=float(row['total_area']) if row['total_area'] else None,
                energy_rating=row['energy_rating'],
                is_active=row['is_active'],
                status=row['status'],
                created_at=row['created_at'],
                updated_at=row['updated_at'],
                created_by=row['created_by'],
                updated_by=row['updated_by']
            )
            
            return building
            
        except Exception as e:
            logger.error(f"Failed to convert row to building: {e}")
            raise DatabaseError(f"Row conversion failed: {e}")
    
    def close(self):
        """Close the connection pool."""
        if self._pool:
            self._pool.closeall()
            logger.info("PostgreSQL connection pool closed") 