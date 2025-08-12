"""
ArxObject Repository - Database Persistence Layer

This module provides database persistence for ArxObjects using PostgreSQL with PostGIS
for spatial operations and JSONB for flexible property storage.
"""

import json
import asyncio
from typing import Dict, List, Any, Optional, Set, Tuple
from datetime import datetime, timezone
import asyncpg
from asyncpg.pool import Pool
import logging

from core.spatial.arxobject_core import (
    ArxObject, ArxObjectType, ArxObjectGeometry, ArxObjectPrecision
)
from core.arxobject.engine import (
    ArxObjectRelationship, ArxObjectConstraint, RelationshipType
)

logger = logging.getLogger(__name__)


class ArxObjectRepository:
    """
    Repository for persisting ArxObjects to PostgreSQL database.
    
    Features:
    - Efficient JSONB storage for flexible properties
    - PostGIS for spatial indexing and queries
    - Batch operations for performance
    - Transaction support
    - Query optimization with prepared statements
    """
    
    def __init__(self, db_pool: Pool):
        """
        Initialize repository with database connection pool.
        
        Args:
            db_pool: AsyncPG connection pool
        """
        self.db_pool = db_pool
        self.prepared_statements: Dict[str, str] = {}
        
        logger.info("Initialized ArxObjectRepository")
    
    async def initialize_schema(self) -> None:
        """Create necessary database tables and indices"""
        async with self.db_pool.acquire() as conn:
            # Enable PostGIS extension
            await conn.execute("CREATE EXTENSION IF NOT EXISTS postgis;")
            await conn.execute("CREATE EXTENSION IF NOT EXISTS btree_gist;")
            
            # Create ArxObjects table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS arxobjects (
                    id UUID PRIMARY KEY,
                    object_type VARCHAR(100) NOT NULL,
                    properties JSONB NOT NULL DEFAULT '{}',
                    geometry JSONB NOT NULL,
                    spatial_geom GEOMETRY(PointZ, 4326),
                    bbox_3d BOX3D,
                    precision VARCHAR(20) NOT NULL DEFAULT 'standard',
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    created_by VARCHAR(255),
                    version INTEGER NOT NULL DEFAULT 1,
                    metadata JSONB DEFAULT '{}',
                    tags TEXT[] DEFAULT '{}',
                    active BOOLEAN DEFAULT TRUE
                );
            """)
            
            # Create relationships table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS arxobject_relationships (
                    id UUID PRIMARY KEY,
                    source_id UUID NOT NULL REFERENCES arxobjects(id) ON DELETE CASCADE,
                    target_id UUID NOT NULL REFERENCES arxobjects(id) ON DELETE CASCADE,
                    relationship_type VARCHAR(50) NOT NULL,
                    properties JSONB DEFAULT '{}',
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    metadata JSONB DEFAULT '{}'
                );
            """)
            
            # Create constraints table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS arxobject_constraints (
                    id UUID PRIMARY KEY,
                    object_id UUID NOT NULL REFERENCES arxobjects(id) ON DELETE CASCADE,
                    constraint_type VARCHAR(100) NOT NULL,
                    expression TEXT NOT NULL,
                    parameters JSONB DEFAULT '{}',
                    severity VARCHAR(20) NOT NULL DEFAULT 'error',
                    active BOOLEAN DEFAULT TRUE,
                    metadata JSONB DEFAULT '{}'
                );
            """)
            
            # Create history table for audit trail
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS arxobject_history (
                    id SERIAL PRIMARY KEY,
                    object_id UUID NOT NULL,
                    operation VARCHAR(20) NOT NULL,
                    old_values JSONB,
                    new_values JSONB,
                    changed_by VARCHAR(255),
                    changed_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );
            """)
            
            # Create indices for performance
            await conn.execute("""
                -- Object type index
                CREATE INDEX IF NOT EXISTS idx_arxobjects_type 
                ON arxobjects(object_type);
                
                -- JSONB property indices
                CREATE INDEX IF NOT EXISTS idx_arxobjects_properties 
                ON arxobjects USING GIN(properties);
                
                -- Spatial index
                CREATE INDEX IF NOT EXISTS idx_arxobjects_spatial 
                ON arxobjects USING GIST(spatial_geom);
                
                -- 3D bounding box index
                CREATE INDEX IF NOT EXISTS idx_arxobjects_bbox3d 
                ON arxobjects USING GIST(bbox_3d);
                
                -- Timestamp indices
                CREATE INDEX IF NOT EXISTS idx_arxobjects_created 
                ON arxobjects(created_at DESC);
                
                CREATE INDEX IF NOT EXISTS idx_arxobjects_updated 
                ON arxobjects(updated_at DESC);
                
                -- Tag index
                CREATE INDEX IF NOT EXISTS idx_arxobjects_tags 
                ON arxobjects USING GIN(tags);
                
                -- Relationship indices
                CREATE INDEX IF NOT EXISTS idx_relationships_source 
                ON arxobject_relationships(source_id);
                
                CREATE INDEX IF NOT EXISTS idx_relationships_target 
                ON arxobject_relationships(target_id);
                
                CREATE INDEX IF NOT EXISTS idx_relationships_type 
                ON arxobject_relationships(relationship_type);
                
                -- Constraint indices
                CREATE INDEX IF NOT EXISTS idx_constraints_object 
                ON arxobject_constraints(object_id);
                
                CREATE INDEX IF NOT EXISTS idx_constraints_type 
                ON arxobject_constraints(constraint_type);
                
                -- History index
                CREATE INDEX IF NOT EXISTS idx_history_object 
                ON arxobject_history(object_id, changed_at DESC);
            """)
            
            logger.info("Database schema initialized")
    
    # ==========================================
    # Object CRUD Operations
    # ==========================================
    
    async def create_object(self, obj: ArxObject, user_id: Optional[str] = None) -> bool:
        """
        Create a new ArxObject in the database.
        
        Args:
            obj: ArxObject to create
            user_id: Optional user ID for audit
            
        Returns:
            True if created successfully
        """
        async with self.db_pool.acquire() as conn:
            try:
                # Convert geometry to PostGIS format
                spatial_geom = f"POINT Z({obj.geometry.x} {obj.geometry.y} {obj.geometry.z})"
                bbox_3d = self._geometry_to_box3d(obj.geometry)
                
                await conn.execute("""
                    INSERT INTO arxobjects (
                        id, object_type, properties, geometry, spatial_geom, 
                        bbox_3d, precision, created_at, updated_at, created_by, 
                        version, metadata, tags, active
                    ) VALUES (
                        $1, $2, $3, $4, ST_GeomFromText($5, 4326),
                        $6::box3d, $7, $8, $9, $10,
                        $11, $12, $13, $14
                    )
                """,
                    obj.id,
                    obj.object_type.value,
                    json.dumps(obj.properties),
                    json.dumps(self._geometry_to_dict(obj.geometry)),
                    spatial_geom,
                    bbox_3d,
                    obj.precision.value,
                    obj.created_at,
                    obj.updated_at,
                    user_id,
                    obj.version,
                    json.dumps(obj.metadata),
                    obj.tags,
                    True
                )
                
                # Record in history
                await self._record_history(
                    conn, obj.id, "CREATE", None, 
                    {"id": obj.id, "type": obj.object_type.value},
                    user_id
                )
                
                logger.debug(f"Created ArxObject {obj.id} in database")
                return True
                
            except Exception as e:
                logger.error(f"Error creating ArxObject: {e}")
                raise
    
    async def get_object(self, object_id: str) -> Optional[ArxObject]:
        """
        Retrieve an ArxObject from the database.
        
        Args:
            object_id: Object identifier
            
        Returns:
            ArxObject or None if not found
        """
        async with self.db_pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT * FROM arxobjects WHERE id = $1 AND active = TRUE
            """, object_id)
            
            if not row:
                return None
            
            return self._row_to_arxobject(row)
    
    async def update_object(
        self,
        obj: ArxObject,
        user_id: Optional[str] = None
    ) -> bool:
        """
        Update an ArxObject in the database.
        
        Args:
            obj: ArxObject to update
            user_id: Optional user ID for audit
            
        Returns:
            True if updated successfully
        """
        async with self.db_pool.acquire() as conn:
            # Get current state for history
            current = await conn.fetchrow(
                "SELECT properties, geometry FROM arxobjects WHERE id = $1",
                obj.id
            )
            
            if not current:
                return False
            
            # Update object
            spatial_geom = f"POINT Z({obj.geometry.x} {obj.geometry.y} {obj.geometry.z})"
            bbox_3d = self._geometry_to_box3d(obj.geometry)
            
            result = await conn.execute("""
                UPDATE arxobjects SET
                    properties = $2,
                    geometry = $3,
                    spatial_geom = ST_GeomFromText($4, 4326),
                    bbox_3d = $5::box3d,
                    updated_at = $6,
                    version = version + 1,
                    metadata = $7
                WHERE id = $1 AND active = TRUE
            """,
                obj.id,
                json.dumps(obj.properties),
                json.dumps(self._geometry_to_dict(obj.geometry)),
                spatial_geom,
                bbox_3d,
                datetime.now(timezone.utc),
                json.dumps(obj.metadata)
            )
            
            if result == "UPDATE 1":
                # Record in history
                await self._record_history(
                    conn, obj.id, "UPDATE",
                    {"properties": current['properties'], "geometry": current['geometry']},
                    {"properties": obj.properties, "geometry": self._geometry_to_dict(obj.geometry)},
                    user_id
                )
                
                logger.debug(f"Updated ArxObject {obj.id} in database")
                return True
            
            return False
    
    async def delete_object(
        self,
        object_id: str,
        soft_delete: bool = True,
        user_id: Optional[str] = None
    ) -> bool:
        """
        Delete an ArxObject from the database.
        
        Args:
            object_id: Object identifier
            soft_delete: If True, mark as inactive; if False, physically delete
            user_id: Optional user ID for audit
            
        Returns:
            True if deleted successfully
        """
        async with self.db_pool.acquire() as conn:
            if soft_delete:
                result = await conn.execute("""
                    UPDATE arxobjects SET active = FALSE, updated_at = NOW()
                    WHERE id = $1 AND active = TRUE
                """, object_id)
                
                if result == "UPDATE 1":
                    await self._record_history(
                        conn, object_id, "SOFT_DELETE", None, None, user_id
                    )
                    return True
            else:
                result = await conn.execute("""
                    DELETE FROM arxobjects WHERE id = $1
                """, object_id)
                
                if result == "DELETE 1":
                    await self._record_history(
                        conn, object_id, "HARD_DELETE", None, None, user_id
                    )
                    return True
            
            return False
    
    # ==========================================
    # Batch Operations
    # ==========================================
    
    async def create_objects_batch(
        self,
        objects: List[ArxObject],
        user_id: Optional[str] = None
    ) -> int:
        """
        Create multiple ArxObjects in a single transaction.
        
        Args:
            objects: List of ArxObjects to create
            user_id: Optional user ID for audit
            
        Returns:
            Number of objects created
        """
        async with self.db_pool.acquire() as conn:
            async with conn.transaction():
                created = 0
                for obj in objects:
                    try:
                        spatial_geom = f"POINT Z({obj.geometry.x} {obj.geometry.y} {obj.geometry.z})"
                        bbox_3d = self._geometry_to_box3d(obj.geometry)
                        
                        await conn.execute("""
                            INSERT INTO arxobjects (
                                id, object_type, properties, geometry, spatial_geom,
                                bbox_3d, precision, created_at, updated_at, created_by
                            ) VALUES (
                                $1, $2, $3, $4, ST_GeomFromText($5, 4326),
                                $6::box3d, $7, $8, $9, $10
                            )
                        """,
                            obj.id, obj.object_type.value,
                            json.dumps(obj.properties),
                            json.dumps(self._geometry_to_dict(obj.geometry)),
                            spatial_geom, bbox_3d,
                            obj.precision.value,
                            obj.created_at, obj.updated_at,
                            user_id
                        )
                        created += 1
                    except Exception as e:
                        logger.error(f"Error in batch create for object {obj.id}: {e}")
                
                logger.info(f"Batch created {created} ArxObjects")
                return created
    
    # ==========================================
    # Query Operations
    # ==========================================
    
    async def find_by_type(
        self,
        object_type: ArxObjectType,
        limit: int = 100,
        offset: int = 0
    ) -> List[ArxObject]:
        """
        Find ArxObjects by type.
        
        Args:
            object_type: Type of objects to find
            limit: Maximum number of results
            offset: Result offset for pagination
            
        Returns:
            List of ArxObjects
        """
        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT * FROM arxobjects 
                WHERE object_type = $1 AND active = TRUE
                ORDER BY created_at DESC
                LIMIT $2 OFFSET $3
            """, object_type.value, limit, offset)
            
            return [self._row_to_arxobject(row) for row in rows]
    
    async def find_by_properties(
        self,
        property_filters: Dict[str, Any],
        limit: int = 100
    ) -> List[ArxObject]:
        """
        Find ArxObjects by property values using JSONB queries.
        
        Args:
            property_filters: Property key-value pairs to match
            limit: Maximum number of results
            
        Returns:
            List of ArxObjects
        """
        async with self.db_pool.acquire() as conn:
            # Build JSONB query
            conditions = []
            params = []
            param_count = 1
            
            for key, value in property_filters.items():
                conditions.append(f"properties @> ${param_count}::jsonb")
                params.append(json.dumps({key: value}))
                param_count += 1
            
            where_clause = " AND ".join(conditions)
            params.append(limit)
            
            query = f"""
                SELECT * FROM arxobjects 
                WHERE {where_clause} AND active = TRUE
                LIMIT ${param_count}
            """
            
            rows = await conn.fetch(query, *params)
            return [self._row_to_arxobject(row) for row in rows]
    
    async def find_in_region(
        self,
        min_x: float, min_y: float, min_z: float,
        max_x: float, max_y: float, max_z: float,
        object_types: Optional[List[ArxObjectType]] = None
    ) -> List[ArxObject]:
        """
        Find ArxObjects within a 3D region using PostGIS.
        
        Args:
            min_x, min_y, min_z: Minimum coordinates
            max_x, max_y, max_z: Maximum coordinates
            object_types: Optional filter by types
            
        Returns:
            List of ArxObjects in region
        """
        async with self.db_pool.acquire() as conn:
            # Build query with spatial filter
            query = """
                SELECT * FROM arxobjects 
                WHERE bbox_3d && BOX3D(ST_MakePoint($1, $2, $3), ST_MakePoint($4, $5, $6))
                AND active = TRUE
            """
            params = [min_x, min_y, min_z, max_x, max_y, max_z]
            
            if object_types:
                type_values = [t.value for t in object_types]
                query += f" AND object_type = ANY(${len(params) + 1})"
                params.append(type_values)
            
            rows = await conn.fetch(query, *params)
            return [self._row_to_arxobject(row) for row in rows]
    
    async def find_nearest(
        self,
        x: float, y: float, z: float,
        radius: float,
        limit: int = 10,
        object_types: Optional[List[ArxObjectType]] = None
    ) -> List[Tuple[ArxObject, float]]:
        """
        Find nearest ArxObjects to a point within radius.
        
        Args:
            x, y, z: Point coordinates
            radius: Search radius
            limit: Maximum number of results
            object_types: Optional filter by types
            
        Returns:
            List of (ArxObject, distance) tuples
        """
        async with self.db_pool.acquire() as conn:
            query = """
                SELECT *, 
                       ST_3DDistance(spatial_geom, ST_MakePoint($1, $2, $3)::geometry) as distance
                FROM arxobjects 
                WHERE ST_3DDWithin(spatial_geom, ST_MakePoint($1, $2, $3)::geometry, $4)
                AND active = TRUE
            """
            params = [x, y, z, radius]
            
            if object_types:
                type_values = [t.value for t in object_types]
                query += f" AND object_type = ANY(${len(params) + 1})"
                params.append(type_values)
            
            query += f" ORDER BY distance LIMIT ${len(params) + 1}"
            params.append(limit)
            
            rows = await conn.fetch(query, *params)
            
            results = []
            for row in rows:
                obj = self._row_to_arxobject(row)
                distance = float(row['distance'])
                results.append((obj, distance))
            
            return results
    
    # ==========================================
    # Relationship Operations
    # ==========================================
    
    async def create_relationship(
        self,
        relationship: ArxObjectRelationship
    ) -> bool:
        """Create a relationship between ArxObjects"""
        async with self.db_pool.acquire() as conn:
            try:
                await conn.execute("""
                    INSERT INTO arxobject_relationships 
                    (id, source_id, target_id, relationship_type, properties, created_at, metadata)
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                """,
                    relationship.id,
                    relationship.source_id,
                    relationship.target_id,
                    relationship.relationship_type.value,
                    json.dumps(relationship.properties),
                    relationship.created_at,
                    json.dumps(relationship.metadata)
                )
                return True
            except Exception as e:
                logger.error(f"Error creating relationship: {e}")
                return False
    
    async def get_relationships(
        self,
        object_id: str,
        relationship_type: Optional[RelationshipType] = None
    ) -> List[ArxObjectRelationship]:
        """Get relationships for an object"""
        async with self.db_pool.acquire() as conn:
            query = """
                SELECT * FROM arxobject_relationships 
                WHERE (source_id = $1 OR target_id = $1)
            """
            params = [object_id]
            
            if relationship_type:
                query += f" AND relationship_type = ${len(params) + 1}"
                params.append(relationship_type.value)
            
            rows = await conn.fetch(query, *params)
            
            relationships = []
            for row in rows:
                rel = ArxObjectRelationship(
                    id=str(row['id']),
                    source_id=str(row['source_id']),
                    target_id=str(row['target_id']),
                    relationship_type=RelationshipType(row['relationship_type']),
                    properties=json.loads(row['properties']),
                    created_at=row['created_at'],
                    metadata=json.loads(row['metadata'])
                )
                relationships.append(rel)
            
            return relationships
    
    # ==========================================
    # Constraint Operations
    # ==========================================
    
    async def create_constraint(
        self,
        constraint: ArxObjectConstraint
    ) -> bool:
        """Create a constraint for an ArxObject"""
        async with self.db_pool.acquire() as conn:
            try:
                await conn.execute("""
                    INSERT INTO arxobject_constraints 
                    (id, object_id, constraint_type, expression, parameters, severity, active, metadata)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                """,
                    constraint.id,
                    constraint.object_id,
                    constraint.constraint_type,
                    constraint.expression,
                    json.dumps(constraint.parameters),
                    constraint.severity,
                    constraint.active,
                    json.dumps(constraint.metadata)
                )
                return True
            except Exception as e:
                logger.error(f"Error creating constraint: {e}")
                return False
    
    async def get_constraints(
        self,
        object_id: str,
        active_only: bool = True
    ) -> List[ArxObjectConstraint]:
        """Get constraints for an object"""
        async with self.db_pool.acquire() as conn:
            query = "SELECT * FROM arxobject_constraints WHERE object_id = $1"
            params = [object_id]
            
            if active_only:
                query += " AND active = TRUE"
            
            rows = await conn.fetch(query, *params)
            
            constraints = []
            for row in rows:
                const = ArxObjectConstraint(
                    id=str(row['id']),
                    object_id=str(row['object_id']),
                    constraint_type=row['constraint_type'],
                    expression=row['expression'],
                    parameters=json.loads(row['parameters']),
                    severity=row['severity'],
                    active=row['active'],
                    metadata=json.loads(row['metadata'])
                )
                constraints.append(const)
            
            return constraints
    
    # ==========================================
    # Helper Methods
    # ==========================================
    
    def _row_to_arxobject(self, row: asyncpg.Record) -> ArxObject:
        """Convert database row to ArxObject"""
        geometry_data = json.loads(row['geometry'])
        geometry = ArxObjectGeometry(**geometry_data)
        
        obj = ArxObject(
            object_type=ArxObjectType(row['object_type']),
            properties=json.loads(row['properties']),
            geometry=geometry,
            precision=ArxObjectPrecision(row['precision'])
        )
        
        # Set additional fields
        obj.id = str(row['id'])
        obj.created_at = row['created_at']
        obj.updated_at = row['updated_at']
        obj.version = row['version']
        obj.metadata = json.loads(row['metadata'])
        obj.tags = row['tags']
        
        return obj
    
    def _geometry_to_dict(self, geometry: ArxObjectGeometry) -> Dict[str, Any]:
        """Convert ArxObjectGeometry to dictionary"""
        return {
            'x': geometry.x,
            'y': geometry.y,
            'z': geometry.z,
            'length': geometry.length,
            'width': geometry.width,
            'height': geometry.height,
            'rotation_x': geometry.rotation_x,
            'rotation_y': geometry.rotation_y,
            'rotation_z': geometry.rotation_z,
            'shape_type': geometry.shape_type,
            'custom_geometry': geometry.custom_geometry
        }
    
    def _geometry_to_box3d(self, geometry: ArxObjectGeometry) -> str:
        """Convert geometry to PostGIS BOX3D format"""
        half_length = geometry.length / 2
        half_width = geometry.width / 2
        half_height = geometry.height / 2
        
        min_x = geometry.x - half_length
        min_y = geometry.y - half_width
        min_z = geometry.z - half_height
        max_x = geometry.x + half_length
        max_y = geometry.y + half_width
        max_z = geometry.z + half_height
        
        return f"BOX3D({min_x} {min_y} {min_z}, {max_x} {max_y} {max_z})"
    
    async def _record_history(
        self,
        conn: asyncpg.Connection,
        object_id: str,
        operation: str,
        old_values: Optional[Dict],
        new_values: Optional[Dict],
        user_id: Optional[str]
    ) -> None:
        """Record operation in history table"""
        await conn.execute("""
            INSERT INTO arxobject_history 
            (object_id, operation, old_values, new_values, changed_by, changed_at)
            VALUES ($1, $2, $3, $4, $5, NOW())
        """,
            object_id,
            operation,
            json.dumps(old_values) if old_values else None,
            json.dumps(new_values) if new_values else None,
            user_id
        )