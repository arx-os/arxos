"""
Data API Structuring Service

Provides structured JSON endpoints for system object lists by type, status, 
condition, installation date, and behavior profile with filtering, pagination, 
contributor attribution, and data anonymization.
"""

import json
import sqlite3
import time
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime, timedelta
import logging
from pathlib import Path
import hashlib
import re
from contextlib import contextmanager

# Initialize logger
logger = logging.getLogger(__name__)


class ObjectType(Enum):
    """Object type enumeration."""
    MECHANICAL = "mechanical"
    ELECTRICAL = "electrical"
    PLUMBING = "plumbing"
    HVAC = "hvac"
    SECURITY = "security"
    NETWORK = "network"
    FIRE_ALARM = "fire_alarm"
    BUILDING_CONTROLS = "building_controls"
    STRUCTURAL = "structural"
    GENERAL = "general"


class ObjectStatus(Enum):
    """Object status enumeration."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    MAINTENANCE = "maintenance"
    REPAIR = "repair"
    REPLACEMENT = "replacement"
    DECOMMISSIONED = "decommissioned"


class ObjectCondition(Enum):
    """Object condition enumeration."""
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    CRITICAL = "critical"


class ContributorRole(Enum):
    """Contributor role enumeration."""
    OWNER = "owner"
    CONTRIBUTOR = "contributor"
    VIEWER = "viewer"
    ADMIN = "admin"


@dataclass
class SystemObject:
    """System object data structure."""
    object_id: str
    name: str
    object_type: ObjectType
    status: ObjectStatus
    condition: ObjectCondition
    installation_date: datetime
    last_maintenance_date: Optional[datetime]
    location: Dict[str, Any]
    metadata: Dict[str, Any]
    behavior_profile: Dict[str, Any]
    contributor_id: str
    contributor_name: str
    contributor_role: ContributorRole
    licensing_info: Dict[str, Any]
    created_at: datetime
    updated_at: datetime


@dataclass
class QueryFilter:
    """Query filter structure."""
    object_type: Optional[ObjectType] = None
    status: Optional[ObjectStatus] = None
    condition: Optional[ObjectCondition] = None
    contributor_id: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    location_filter: Optional[Dict[str, Any]] = None
    behavior_profile_filter: Optional[Dict[str, Any]] = None


@dataclass
class PaginationInfo:
    """Pagination information structure."""
    page: int
    page_size: int
    total_count: int
    total_pages: int
    has_next: bool
    has_previous: bool
    next_page: Optional[int]
    previous_page: Optional[int]


@dataclass
class QueryResult:
    """Query result structure."""
    objects: List[SystemObject]
    pagination: PaginationInfo
    filters_applied: Dict[str, Any]
    query_time: float
    anonymized_count: int


class DataAPIStructuringService:
    """
    Data API Structuring service for system object querying and management.
    
    Provides comprehensive object querying with filtering, pagination,
    contributor attribution, and data anonymization capabilities.
    """
    
    def __init__(self, db_path: str = "data_api.db"):
        self.db_path = db_path
        self._initialize_database()
        self._load_sample_data()
    
    def _initialize_database(self):
        """Initialize SQLite database for data API structuring."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # System objects table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS system_objects (
                        object_id TEXT PRIMARY KEY,
                        name TEXT NOT NULL,
                        object_type TEXT NOT NULL,
                        status TEXT NOT NULL,
                        condition TEXT NOT NULL,
                        installation_date TEXT NOT NULL,
                        last_maintenance_date TEXT,
                        location TEXT NOT NULL,
                        metadata TEXT,
                        behavior_profile TEXT,
                        contributor_id TEXT NOT NULL,
                        contributor_name TEXT NOT NULL,
                        contributor_role TEXT NOT NULL,
                        licensing_info TEXT,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL
                    )
                """)
                
                # Contributors table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS contributors (
                        contributor_id TEXT PRIMARY KEY,
                        name TEXT NOT NULL,
                        email TEXT,
                        role TEXT NOT NULL,
                        license_level TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL
                    )
                """)
                
                # Access logs table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS access_logs (
                        log_id TEXT PRIMARY KEY,
                        user_id TEXT NOT NULL,
                        endpoint TEXT NOT NULL,
                        query_params TEXT,
                        response_time REAL,
                        objects_returned INTEGER,
                        objects_anonymized INTEGER,
                        timestamp TEXT NOT NULL
                    )
                """)
                
                # Create indexes for performance
                conn.execute("CREATE INDEX IF NOT EXISTS idx_objects_type ON system_objects (object_type)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_objects_status ON system_objects (status)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_objects_condition ON system_objects (condition)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_objects_contributor ON system_objects (contributor_id)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_objects_installation_date ON system_objects (installation_date)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_objects_created_at ON system_objects (created_at)")
                
                conn.commit()
            logger.info("Data API Structuring database initialized")
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
    
    def _load_sample_data(self):
        """Load sample data for testing and demonstration."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Check if data already exists
                cursor = conn.execute("SELECT COUNT(*) FROM system_objects")
                if cursor.fetchone()[0] > 0:
                    return  # Data already loaded
                
                # Sample contributors
                contributors = [
                    ("contrib_001", "John Smith", "john@example.com", "owner", "full", datetime.now(), datetime.now()),
                    ("contrib_002", "Sarah Johnson", "sarah@example.com", "contributor", "limited", datetime.now(), datetime.now()),
                    ("contrib_003", "Mike Wilson", "mike@example.com", "viewer", "basic", datetime.now(), datetime.now()),
                    ("contrib_004", "Lisa Brown", "lisa@example.com", "admin", "full", datetime.now(), datetime.now())
                ]
                
                for contributor in contributors:
                    conn.execute("""
                        INSERT INTO contributors 
                        (contributor_id, name, email, role, license_level, created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, contributor)
                
                # Sample system objects
                sample_objects = []
                object_types = [ObjectType.MECHANICAL, ObjectType.ELECTRICAL, ObjectType.HVAC, 
                              ObjectType.PLUMBING, ObjectType.SECURITY, ObjectType.NETWORK]
                statuses = [ObjectStatus.ACTIVE, ObjectStatus.MAINTENANCE, ObjectStatus.INACTIVE]
                conditions = [ObjectCondition.EXCELLENT, ObjectCondition.GOOD, ObjectCondition.FAIR]
                
                for i in range(1000):  # Create 1000 sample objects
                    object_id = f"obj_{i+1:04d}"
                    object_type = object_types[i % len(object_types)]
                    status = statuses[i % len(statuses)]
                    condition = conditions[i % len(conditions)]
                    contributor_id = f"contrib_{((i % 4) + 1):03d}"
                    
                    # Generate sample data
                    installation_date = datetime.now() - timedelta(days=i*30)
                    last_maintenance = installation_date + timedelta(days=180) if i % 3 == 0 else None
                    
                    location = {
                        "building": f"Building_{i % 5 + 1}",
                        "floor": f"Floor_{i % 10 + 1}",
                        "room": f"Room_{i % 20 + 1}",
                        "coordinates": {"x": i % 100, "y": i % 100, "z": i % 10}
                    }
                    
                    metadata = {
                        "manufacturer": f"Manufacturer_{i % 10 + 1}",
                        "model": f"Model_{i % 20 + 1}",
                        "serial_number": f"SN{i:06d}",
                        "warranty_expiry": (installation_date + timedelta(days=365)).isoformat()
                    }
                    
                    behavior_profile = {
                        "maintenance_interval": 180,
                        "expected_lifespan": 3600,
                        "critical_thresholds": {"temperature": 85, "pressure": 100},
                        "performance_metrics": {"efficiency": 0.85 + (i % 15) / 100}
                    }
                    
                    licensing_info = {
                        "license_type": "standard" if i % 3 == 0 else "premium",
                        "access_level": "full" if i % 2 == 0 else "limited",
                        "expiry_date": (datetime.now() + timedelta(days=365)).isoformat()
                    }
                    
                    sample_objects.append((
                        object_id,
                        f"{object_type.value.title()} System {i+1}",
                        object_type.value,
                        status.value,
                        condition.value,
                        installation_date.isoformat(),
                        last_maintenance.isoformat() if last_maintenance else None,
                        json.dumps(location),
                        json.dumps(metadata),
                        json.dumps(behavior_profile),
                        contributor_id,
                        contributors[int(contributor_id.split('_')[1]) - 1][1],
                        "owner" if i % 4 == 0 else "contributor",
                        json.dumps(licensing_info),
                        installation_date.isoformat(),
                        datetime.now().isoformat()
                    ))
                
                # Insert sample objects
                conn.executemany("""
                    INSERT INTO system_objects 
                    (object_id, name, object_type, status, condition, installation_date,
                     last_maintenance_date, location, metadata, behavior_profile,
                     contributor_id, contributor_name, contributor_role, licensing_info,
                     created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, sample_objects)
                
                conn.commit()
                logger.info(f"Loaded {len(sample_objects)} sample system objects")
        except Exception as e:
            logger.error(f"Failed to load sample data: {e}")
    
    def query_system_objects(self, 
                           filters: Optional[QueryFilter] = None,
                           page: int = 1,
                           page_size: int = 50,
                           sort_by: str = "created_at",
                           sort_order: str = "desc",
                           user_id: str = None,
                           user_license_level: str = "basic") -> QueryResult:
        """
        Query system objects with filtering, pagination, and anonymization.
        
        Args:
            filters: Query filters to apply
            page: Page number (1-based)
            page_size: Number of objects per page
            sort_by: Field to sort by
            sort_order: Sort order (asc/desc)
            user_id: User ID for access control
            user_license_level: User's license level for anonymization
            
        Returns:
            QueryResult with objects, pagination info, and anonymization details
        """
        try:
            start_time = time.time()
            
            # Build query with filters
            query, params = self._build_query(filters, sort_by, sort_order)
            
            # Get total count
            count_query = f"SELECT COUNT(*) FROM ({query})"
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(count_query, params)
                total_count = cursor.fetchone()[0]
            
            # Calculate pagination
            total_pages = (total_count + page_size - 1) // page_size
            offset = (page - 1) * page_size
            
            # Add pagination to query
            paginated_query = f"{query} LIMIT {page_size} OFFSET {offset}"
            
            # Execute query
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(paginated_query, params)
                rows = cursor.fetchall()
            
            # Convert rows to objects
            objects = []
            anonymized_count = 0
            
            for row in rows:
                obj = self._row_to_object(row)
                
                # Apply anonymization based on user license
                anonymized_obj = self._anonymize_object(obj, user_license_level)
                if anonymized_obj != obj:
                    anonymized_count += 1
                
                objects.append(anonymized_obj)
            
            # Create pagination info
            pagination = PaginationInfo(
                page=page,
                page_size=page_size,
                total_count=total_count,
                total_pages=total_pages,
                has_next=page < total_pages,
                has_previous=page > 1,
                next_page=page + 1 if page < total_pages else None,
                previous_page=page - 1 if page > 1 else None
            )
            
            # Log access
            self._log_access(user_id, "query_system_objects", {
                "filters": filters.__dict__ if filters else None,
                "page": page,
                "page_size": page_size
            }, time.time() - start_time, len(objects), anonymized_count)
            
            return QueryResult(
                objects=objects,
                pagination=pagination,
                filters_applied=filters.__dict__ if filters else {},
                query_time=time.time() - start_time,
                anonymized_count=anonymized_count
            )
            
        except Exception as e:
            logger.error(f"Query system objects failed: {e}")
            raise
    
    def get_system_object(self, object_id: str, user_id: str = None, 
                         user_license_level: str = "basic") -> Optional[SystemObject]:
        """
        Get a specific system object by ID.
        
        Args:
            object_id: Object ID to retrieve
            user_id: User ID for access control
            user_license_level: User's license level for anonymization
            
        Returns:
            SystemObject or None if not found
        """
        try:
            start_time = time.time()
            
            query = """
                SELECT * FROM system_objects WHERE object_id = ?
            """
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(query, (object_id,))
                row = cursor.fetchone()
            
            if not row:
                return None
            
            obj = self._row_to_object(row)
            anonymized_obj = self._anonymize_object(obj, user_license_level)
            
            # Log access
            self._log_access(user_id, "get_system_object", {"object_id": object_id}, 
                           time.time() - start_time, 1, 0 if anonymized_obj == obj else 1)
            
            return anonymized_obj
            
        except Exception as e:
            logger.error(f"Get system object failed: {e}")
            raise
    
    def get_objects_by_contributor(self, contributor_id: str, 
                                  filters: Optional[QueryFilter] = None,
                                  page: int = 1,
                                  page_size: int = 50,
                                  user_id: str = None,
                                  user_license_level: str = "basic") -> QueryResult:
        """
        Get objects by contributor with filtering and pagination.
        
        Args:
            contributor_id: Contributor ID to filter by
            filters: Additional query filters
            page: Page number (1-based)
            page_size: Number of objects per page
            user_id: User ID for access control
            user_license_level: User's license level for anonymization
            
        Returns:
            QueryResult with objects by contributor
        """
        try:
            # Add contributor filter
            if filters is None:
                filters = QueryFilter()
            filters.contributor_id = contributor_id
            
            return self.query_system_objects(
                filters=filters,
                page=page,
                page_size=page_size,
                user_id=user_id,
                user_license_level=user_license_level
            )
            
        except Exception as e:
            logger.error(f"Get objects by contributor failed: {e}")
            raise
    
    def get_system_summary(self, user_id: str = None, 
                          user_license_level: str = "basic") -> Dict[str, Any]:
        """
        Get system summary statistics.
        
        Args:
            user_id: User ID for access control
            user_license_level: User's license level for anonymization
            
        Returns:
            System summary statistics
        """
        try:
            start_time = time.time()
            
            with sqlite3.connect(self.db_path) as conn:
                # Total objects by type
                cursor = conn.execute("""
                    SELECT object_type, COUNT(*) as count 
                    FROM system_objects 
                    GROUP BY object_type
                """)
                objects_by_type = {row[0]: row[1] for row in cursor.fetchall()}
                
                # Total objects by status
                cursor = conn.execute("""
                    SELECT status, COUNT(*) as count 
                    FROM system_objects 
                    GROUP BY status
                """)
                objects_by_status = {row[0]: row[1] for row in cursor.fetchall()}
                
                # Total objects by condition
                cursor = conn.execute("""
                    SELECT condition, COUNT(*) as count 
                    FROM system_objects 
                    GROUP BY condition
                """)
                objects_by_condition = {row[0]: row[1] for row in cursor.fetchall()}
                
                # Total objects by contributor
                cursor = conn.execute("""
                    SELECT contributor_id, COUNT(*) as count 
                    FROM system_objects 
                    GROUP BY contributor_id
                """)
                objects_by_contributor = {row[0]: row[1] for row in cursor.fetchall()}
                
                # Recent installations (last 30 days)
                thirty_days_ago = (datetime.now() - timedelta(days=30)).isoformat()
                cursor = conn.execute("""
                    SELECT COUNT(*) FROM system_objects 
                    WHERE installation_date >= ?
                """, (thirty_days_ago,))
                recent_installations = cursor.fetchone()[0]
                
                # Total count
                cursor = conn.execute("SELECT COUNT(*) FROM system_objects")
                total_objects = cursor.fetchone()[0]
            
            summary = {
                "total_objects": total_objects,
                "objects_by_type": objects_by_type,
                "objects_by_status": objects_by_status,
                "objects_by_condition": objects_by_condition,
                "objects_by_contributor": objects_by_contributor,
                "recent_installations": recent_installations,
                "generated_at": datetime.now().isoformat()
            }
            
            # Log access
            self._log_access(user_id, "get_system_summary", {}, 
                           time.time() - start_time, 1, 0)
            
            return summary
            
        except Exception as e:
            logger.error(f"Get system summary failed: {e}")
            raise
    
    def export_objects(self, filters: Optional[QueryFilter] = None,
                      format: str = "json",
                      user_id: str = None,
                      user_license_level: str = "basic") -> str:
        """
        Export objects in specified format.
        
        Args:
            filters: Query filters to apply
            format: Export format (json, csv)
            user_id: User ID for access control
            user_license_level: User's license level for anonymization
            
        Returns:
            Exported data as string
        """
        try:
            start_time = time.time()
            
            # Get all objects (no pagination for export)
            result = self.query_system_objects(
                filters=filters,
                page=1,
                page_size=10000,  # Large page size for export
                user_id=user_id,
                user_license_level=user_license_level
            )
            
            if format.lower() == "json":
                export_data = {
                    "objects": [asdict(obj) for obj in result.objects],
                    "export_info": {
                        "total_objects": len(result.objects),
                        "anonymized_count": result.anonymized_count,
                        "filters_applied": result.filters_applied,
                        "export_time": datetime.now().isoformat(),
                        "format": "json"
                    }
                }
                return json.dumps(export_data, indent=2, default=str)
            
            elif format.lower() == "csv":
                import csv
                import io
                
                output = io.StringIO()
                writer = csv.writer(output)
                
                # Write header
                if result.objects:
                    writer.writerow(result.objects[0].__dict__.keys())
                
                # Write data
                for obj in result.objects:
                    writer.writerow(obj.__dict__.values())
                
                return output.getvalue()
            
            else:
                raise ValueError(f"Unsupported export format: {format}")
                
        except Exception as e:
            logger.error(f"Export objects failed: {e}")
            raise
    
    def get_access_analytics(self, days: int = 30) -> Dict[str, Any]:
        """
        Get access analytics for the specified period.
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Access analytics data
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            with sqlite3.connect(self.db_path) as conn:
                # Total access count
                cursor = conn.execute("""
                    SELECT COUNT(*) FROM access_logs 
                    WHERE timestamp >= ?
                """, (cutoff_date.isoformat(),))
                total_access = cursor.fetchone()[0]
                
                # Access by endpoint
                cursor = conn.execute("""
                    SELECT endpoint, COUNT(*) as count 
                    FROM access_logs 
                    WHERE timestamp >= ?
                    GROUP BY endpoint
                """, (cutoff_date.isoformat(),))
                access_by_endpoint = {row[0]: row[1] for row in cursor.fetchall()}
                
                # Average response time
                cursor = conn.execute("""
                    SELECT AVG(response_time) FROM access_logs 
                    WHERE timestamp >= ?
                """, (cutoff_date.isoformat(),))
                avg_response_time = cursor.fetchone()[0] or 0
                
                # Total objects returned
                cursor = conn.execute("""
                    SELECT SUM(objects_returned) FROM access_logs 
                    WHERE timestamp >= ?
                """, (cutoff_date.isoformat(),))
                total_objects_returned = cursor.fetchone()[0] or 0
                
                # Total objects anonymized
                cursor = conn.execute("""
                    SELECT SUM(objects_anonymized) FROM access_logs 
                    WHERE timestamp >= ?
                """, (cutoff_date.isoformat(),))
                total_objects_anonymized = cursor.fetchone()[0] or 0
            
            return {
                "period_days": days,
                "total_access": total_access,
                "access_by_endpoint": access_by_endpoint,
                "avg_response_time": avg_response_time,
                "total_objects_returned": total_objects_returned,
                "total_objects_anonymized": total_objects_anonymized,
                "anonymization_rate": total_objects_anonymized / total_objects_returned if total_objects_returned > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Get access analytics failed: {e}")
            raise
    
    # Helper methods
    
    def _build_query(self, filters: Optional[QueryFilter], sort_by: str, sort_order: str) -> Tuple[str, List]:
        """Build SQL query with filters."""
        query = "SELECT * FROM system_objects WHERE 1=1"
        params = []
        
        if filters:
            if filters.object_type:
                query += " AND object_type = ?"
                params.append(filters.object_type.value)
            
            if filters.status:
                query += " AND status = ?"
                params.append(filters.status.value)
            
            if filters.condition:
                query += " AND condition = ?"
                params.append(filters.condition.value)
            
            if filters.contributor_id:
                query += " AND contributor_id = ?"
                params.append(filters.contributor_id)
            
            if filters.date_from:
                query += " AND installation_date >= ?"
                params.append(filters.date_from.isoformat())
            
            if filters.date_to:
                query += " AND installation_date <= ?"
                params.append(filters.date_to.isoformat())
        
        # Add sorting
        query += f" ORDER BY {sort_by} {sort_order.upper()}"
        
        return query, params
    
    def _row_to_object(self, row: Tuple) -> SystemObject:
        """Convert database row to SystemObject."""
        return SystemObject(
            object_id=row[0],
            name=row[1],
            object_type=ObjectType(row[2]),
            status=ObjectStatus(row[3]),
            condition=ObjectCondition(row[4]),
            installation_date=datetime.fromisoformat(row[5]),
            last_maintenance_date=datetime.fromisoformat(row[6]) if row[6] else None,
            location=json.loads(row[7]),
            metadata=json.loads(row[8]) if row[8] else {},
            behavior_profile=json.loads(row[9]) if row[9] else {},
            contributor_id=row[10],
            contributor_name=row[11],
            contributor_role=ContributorRole(row[12]),
            licensing_info=json.loads(row[13]) if row[13] else {},
            created_at=datetime.fromisoformat(row[14]),
            updated_at=datetime.fromisoformat(row[15])
        )
    
    def _anonymize_object(self, obj: SystemObject, user_license_level: str) -> SystemObject:
        """Anonymize object based on user license level."""
        if user_license_level == "full":
            return obj  # No anonymization for full license
        
        # Create anonymized copy
        anonymized_obj = SystemObject(
            object_id=obj.object_id,
            name=obj.name,
            object_type=obj.object_type,
            status=obj.status,
            condition=obj.condition,
            installation_date=obj.installation_date,
            last_maintenance_date=obj.last_maintenance_date,
            location=obj.location,
            metadata=obj.metadata,
            behavior_profile=obj.behavior_profile,
            contributor_id=obj.contributor_id,
            contributor_name=obj.contributor_name,
            contributor_role=obj.contributor_role,
            licensing_info=obj.licensing_info,
            created_at=obj.created_at,
            updated_at=obj.updated_at
        )
        
        if user_license_level == "basic":
            # Anonymize sensitive fields for basic license
            anonymized_obj.contributor_name = "Anonymous"
            anonymized_obj.metadata = {
                "manufacturer": "Unknown",
                "model": "Unknown",
                "serial_number": "***",
                "warranty_expiry": "***"
            }
            anonymized_obj.behavior_profile = {
                "maintenance_interval": anonymized_obj.behavior_profile.get("maintenance_interval"),
                "expected_lifespan": anonymized_obj.behavior_profile.get("expected_lifespan")
            }
        
        elif user_license_level == "limited":
            # Partial anonymization for limited license
            anonymized_obj.contributor_name = f"{obj.contributor_name[0]}***"
            anonymized_obj.metadata["serial_number"] = "***"
            anonymized_obj.behavior_profile["critical_thresholds"] = {}
        
        return anonymized_obj
    
    def _log_access(self, user_id: str, endpoint: str, query_params: Dict[str, Any],
                   response_time: float, objects_returned: int, objects_anonymized: int):
        """Log API access for analytics."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO access_logs 
                    (log_id, user_id, endpoint, query_params, response_time, 
                     objects_returned, objects_anonymized, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    f"log_{int(time.time() * 1000)}",
                    user_id or "anonymous",
                    endpoint,
                    json.dumps(query_params),
                    response_time,
                    objects_returned,
                    objects_anonymized,
                    datetime.now().isoformat()
                ))
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to log access: {e}")
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for the data API service."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Total objects
                cursor = conn.execute("SELECT COUNT(*) FROM system_objects")
                total_objects = cursor.fetchone()[0]
                
                # Objects by type
                cursor = conn.execute("""
                    SELECT object_type, COUNT(*) FROM system_objects 
                    GROUP BY object_type
                """)
                objects_by_type = {row[0]: row[1] for row in cursor.fetchall()}
                
                # Recent access
                cursor = conn.execute("""
                    SELECT COUNT(*) FROM access_logs 
                    WHERE timestamp >= ?
                """, ((datetime.now() - timedelta(hours=1)).isoformat(),))
                recent_access = cursor.fetchone()[0]
                
                # Average response time
                cursor = conn.execute("""
                    SELECT AVG(response_time) FROM access_logs 
                    WHERE timestamp >= ?
                """, ((datetime.now() - timedelta(hours=1)).isoformat(),))
                avg_response_time = cursor.fetchone()[0] or 0
            
            return {
                "total_objects": total_objects,
                "objects_by_type": objects_by_type,
                "recent_access": recent_access,
                "avg_response_time": avg_response_time,
                "database_size": Path(self.db_path).stat().st_size if Path(self.db_path).exists() else 0
            }
        except Exception as e:
            logger.error(f"Failed to get performance metrics: {e}")
            return {"error": str(e)} 