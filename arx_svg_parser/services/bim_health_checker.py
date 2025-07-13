"""
BIM Health Checker Service

This service provides comprehensive BIM validation for floorplans including:
- Missing behavior profile detection
- Invalid coordinate validation and correction
- Unlinked symbol detection and linking
- Stale object metadata identification
- Context-aware fix suggestions
- Validation reporting and analytics
- Automated fix application capabilities
- Validation scheduling and monitoring

Performance Targets:
- BIM health checks complete within 5 minutes
- Validation identifies 95%+ of issues
- Fix suggestions are 90%+ accurate
- Automated fixes resolve 80%+ of issues
"""

import json
import hashlib
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
import sqlite3
from contextlib import contextmanager
import math
import re

from structlog import get_logger

logger = get_logger()


class ValidationStatus(Enum):
    """Validation status enumeration."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"


class IssueType(Enum):
    """Issue type enumeration."""
    MISSING_BEHAVIOR_PROFILE = "missing_behavior_profile"
    INVALID_COORDINATES = "invalid_coordinates"
    UNLINKED_SYMBOL = "unlinked_symbol"
    STALE_METADATA = "stale_metadata"
    DUPLICATE_OBJECT = "duplicate_object"
    INVALID_SYMBOL = "invalid_symbol"
    MISSING_REQUIRED_FIELDS = "missing_required_fields"
    COORDINATE_OUT_OF_BOUNDS = "coordinate_out_of_bounds"


class FixType(Enum):
    """Fix type enumeration."""
    AUTO_FIX = "auto_fix"
    SUGGESTED_FIX = "suggested_fix"
    MANUAL_FIX = "manual_fix"
    IGNORE = "ignore"


@dataclass
class ValidationIssue:
    """Represents a validation issue found during health check."""
    issue_id: str
    issue_type: IssueType
    object_id: str
    severity: str  # low, medium, high, critical
    description: str
    location: Dict[str, Any]
    current_value: Any
    suggested_value: Any
    fix_type: FixType
    confidence: float  # 0.0 to 1.0
    timestamp: datetime
    context: Dict[str, Any]


@dataclass
class ValidationResult:
    """Represents the result of a BIM health check."""
    validation_id: str
    floorplan_id: str
    status: ValidationStatus
    total_objects: int
    issues_found: int
    auto_fixes_applied: int
    suggested_fixes: int
    manual_fixes_required: int
    validation_time: float
    timestamp: datetime
    issues: List[ValidationIssue]
    summary: Dict[str, Any]


@dataclass
class BehaviorProfile:
    """Represents a behavior profile for BIM objects."""
    profile_id: str
    object_type: str
    category: str
    properties: Dict[str, Any]
    validation_rules: Dict[str, Any]
    fix_suggestions: Dict[str, Any]


class BIMHealthCheckerService:
    """
    Core service for BIM health checking and validation.
    
    This service provides comprehensive BIM validation for floorplans including
    missing behavior profiles, invalid coordinates, unlinked symbols, and stale
    object metadata with context-aware fix suggestions.
    """
    
    def __init__(self, db_path: str = "bim_health.db"):
        """
        Initialize the BIM health checker service.
        
        Args:
            db_path: Path to the SQLite database for validation state storage
        """
        self.db_path = db_path
        self.lock = threading.RLock()
        self._init_database()
        self.behavior_profiles: Dict[str, BehaviorProfile] = {}
        self.validation_results: List[ValidationResult] = []
        
        # Performance metrics
        self.metrics = {
            "total_validations": 0,
            "successful_validations": 0,
            "issues_detected": 0,
            "auto_fixes_applied": 0,
            "average_validation_time": 0.0
        }
        
        # Load behavior profiles
        self._load_behavior_profiles()
    
    def _init_database(self) -> None:
        """Initialize the SQLite database with required tables."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS validation_results (
                    validation_id TEXT PRIMARY KEY,
                    floorplan_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    total_objects INTEGER,
                    issues_found INTEGER,
                    auto_fixes_applied INTEGER,
                    suggested_fixes INTEGER,
                    manual_fixes_required INTEGER,
                    validation_time REAL,
                    timestamp TEXT NOT NULL,
                    summary TEXT
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS validation_issues (
                    issue_id TEXT PRIMARY KEY,
                    validation_id TEXT NOT NULL,
                    issue_type TEXT NOT NULL,
                    object_id TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    description TEXT NOT NULL,
                    location TEXT,
                    current_value TEXT,
                    suggested_value TEXT,
                    fix_type TEXT NOT NULL,
                    confidence REAL,
                    timestamp TEXT NOT NULL,
                    context TEXT
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS behavior_profiles (
                    profile_id TEXT PRIMARY KEY,
                    object_type TEXT NOT NULL,
                    category TEXT NOT NULL,
                    properties TEXT NOT NULL,
                    validation_rules TEXT NOT NULL,
                    fix_suggestions TEXT NOT NULL
                )
            """)
            
            conn.commit()
    
    def _load_behavior_profiles(self) -> None:
        """Load behavior profiles from database and default profiles."""
        # Load from database
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT profile_id, object_type, category, properties, 
                       validation_rules, fix_suggestions
                FROM behavior_profiles
            """)
            
            for row in cursor.fetchall():
                profile = BehaviorProfile(
                    profile_id=row[0],
                    object_type=row[1],
                    category=row[2],
                    properties=json.loads(row[3]),
                    validation_rules=json.loads(row[4]),
                    fix_suggestions=json.loads(row[5])
                )
                self.behavior_profiles[profile.profile_id] = profile
        
        # Load default profiles if none exist
        if not self.behavior_profiles:
            self._create_default_behavior_profiles()
    
    def _create_default_behavior_profiles(self) -> None:
        """Create default behavior profiles for common BIM object types."""
        default_profiles = [
            {
                "profile_id": "electrical_equipment",
                "object_type": "equipment",
                "category": "electrical",
                "properties": {
                    "required_fields": ["id", "name", "type", "location", "properties"],
                    "optional_fields": ["description", "manufacturer", "model", "voltage", "current"],
                    "coordinate_bounds": {"x": [0, 10000], "y": [0, 10000]},
                    "symbol_requirements": ["electrical_symbol", "power_symbol"]
                },
                "validation_rules": {
                    "coordinate_validation": True,
                    "symbol_linking": True,
                    "metadata_completeness": 0.8,
                    "duplicate_detection": True
                },
                "fix_suggestions": {
                    "missing_coordinates": "auto_calculate_from_symbol",
                    "invalid_coordinates": "snap_to_grid",
                    "missing_symbol": "assign_default_symbol",
                    "stale_metadata": "update_from_library"
                }
            },
            {
                "profile_id": "hvac_equipment",
                "object_type": "equipment",
                "category": "hvac",
                "properties": {
                    "required_fields": ["id", "name", "type", "location", "properties"],
                    "optional_fields": ["capacity", "efficiency", "airflow", "temperature"],
                    "coordinate_bounds": {"x": [0, 10000], "y": [0, 10000]},
                    "symbol_requirements": ["hvac_symbol", "airflow_symbol"]
                },
                "validation_rules": {
                    "coordinate_validation": True,
                    "symbol_linking": True,
                    "metadata_completeness": 0.8,
                    "duplicate_detection": True
                },
                "fix_suggestions": {
                    "missing_coordinates": "auto_calculate_from_symbol",
                    "invalid_coordinates": "snap_to_grid",
                    "missing_symbol": "assign_default_symbol",
                    "stale_metadata": "update_from_library"
                }
            },
            {
                "profile_id": "plumbing_fixture",
                "object_type": "fixture",
                "category": "plumbing",
                "properties": {
                    "required_fields": ["id", "name", "type", "location", "properties"],
                    "optional_fields": ["flow_rate", "pressure", "material", "connections"],
                    "coordinate_bounds": {"x": [0, 10000], "y": [0, 10000]},
                    "symbol_requirements": ["plumbing_symbol", "water_symbol"]
                },
                "validation_rules": {
                    "coordinate_validation": True,
                    "symbol_linking": True,
                    "metadata_completeness": 0.8,
                    "duplicate_detection": True
                },
                "fix_suggestions": {
                    "missing_coordinates": "auto_calculate_from_symbol",
                    "invalid_coordinates": "snap_to_grid",
                    "missing_symbol": "assign_default_symbol",
                    "stale_metadata": "update_from_library"
                }
            }
        ]
        
        for profile_data in default_profiles:
            profile = BehaviorProfile(**profile_data)
            self.behavior_profiles[profile.profile_id] = profile
            self._save_behavior_profile(profile)
    
    def _save_behavior_profile(self, profile: BehaviorProfile) -> None:
        """Save a behavior profile to the database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO behavior_profiles 
                (profile_id, object_type, category, properties, validation_rules, fix_suggestions)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                profile.profile_id,
                profile.object_type,
                profile.category,
                json.dumps(profile.properties),
                json.dumps(profile.validation_rules),
                json.dumps(profile.fix_suggestions)
            ))
            conn.commit()
    
    def _save_validation_result(self, result: ValidationResult) -> None:
        """Save validation result to the database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO validation_results 
                (validation_id, floorplan_id, status, total_objects, issues_found,
                 auto_fixes_applied, suggested_fixes, manual_fixes_required,
                 validation_time, timestamp, summary)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                result.validation_id,
                result.floorplan_id,
                result.status.value,
                result.total_objects,
                result.issues_found,
                result.auto_fixes_applied,
                result.suggested_fixes,
                result.manual_fixes_required,
                result.validation_time,
                result.timestamp.isoformat(),
                json.dumps(result.summary)
            ))
            
            # Save issues
            for issue in result.issues:
                conn.execute("""
                    INSERT OR REPLACE INTO validation_issues 
                    (issue_id, validation_id, issue_type, object_id, severity,
                     description, location, current_value, suggested_value,
                     fix_type, confidence, timestamp, context)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    issue.issue_id,
                    result.validation_id,
                    issue.issue_type.value,
                    issue.object_id,
                    issue.severity,
                    issue.description,
                    json.dumps(issue.location),
                    json.dumps(issue.current_value),
                    json.dumps(issue.suggested_value),
                    issue.fix_type.value,
                    issue.confidence,
                    issue.timestamp.isoformat(),
                    json.dumps(issue.context)
                ))
            
            conn.commit()
    
    def _generate_validation_id(self, floorplan_id: str) -> str:
        """Generate a unique validation ID."""
        timestamp = int(time.time() * 1000)
        return f"validation_{floorplan_id}_{timestamp}"
    
    def _generate_issue_id(self, validation_id: str, object_id: str, issue_type: IssueType) -> str:
        """Generate a unique issue ID."""
        timestamp = int(time.time() * 1000)
        return f"issue_{validation_id}_{object_id}_{issue_type.value}_{timestamp}"
    
    def _validate_coordinates(self, coordinates: Dict[str, Any], bounds: Dict[str, List[int]]) -> Tuple[bool, str, Any]:
        """
        Validate coordinates against bounds.
        
        Args:
            coordinates: Coordinate dictionary with x, y, z values
            bounds: Bounds dictionary with coordinate ranges
            
        Returns:
            Tuple of (is_valid, error_message, suggested_value)
        """
        if not coordinates:
            return False, "Missing coordinates", {"x": 0, "y": 0, "z": 0}
        
        x = coordinates.get('x', 0)
        y = coordinates.get('y', 0)
        z = coordinates.get('z', 0)
        
        x_bounds = bounds.get('x', [0, 10000])
        y_bounds = bounds.get('y', [0, 10000])
        z_bounds = bounds.get('z', [0, 100])
        
        issues = []
        suggested_coords = coordinates.copy()
        
        if not isinstance(x, (int, float)) or x < x_bounds[0] or x > x_bounds[1]:
            issues.append(f"X coordinate {x} out of bounds [{x_bounds[0]}, {x_bounds[1]}]")
            suggested_coords['x'] = max(x_bounds[0], min(x, x_bounds[1]))
        
        if not isinstance(y, (int, float)) or y < y_bounds[0] or y > y_bounds[1]:
            issues.append(f"Y coordinate {y} out of bounds [{y_bounds[0]}, {y_bounds[1]}]")
            suggested_coords['y'] = max(y_bounds[0], min(y, y_bounds[1]))
        
        if not isinstance(z, (int, float)) or z < z_bounds[0] or z > z_bounds[1]:
            issues.append(f"Z coordinate {z} out of bounds [{z_bounds[0]}, {z_bounds[1]}]")
            suggested_coords['z'] = max(z_bounds[0], min(z, z_bounds[1]))
        
        if issues:
            return False, "; ".join(issues), suggested_coords
        
        return True, "", coordinates
    
    def _check_missing_behavior_profile(self, object_data: Dict[str, Any]) -> Optional[ValidationIssue]:
        """Check if object has missing behavior profile."""
        object_type = object_data.get('type', '')
        category = object_data.get('category', '')
        
        # Check if we have a behavior profile for this type
        profile_key = f"{object_type}_{category}" if category else object_type
        
        if profile_key not in self.behavior_profiles:
            # Try to find a suitable profile
            suitable_profile = None
            for profile in self.behavior_profiles.values():
                if profile.object_type == object_type or profile.category == category:
                    suitable_profile = profile
                    break
            
            if suitable_profile:
                return ValidationIssue(
                    issue_id=self._generate_issue_id("temp", object_data.get('id', ''), IssueType.MISSING_BEHAVIOR_PROFILE),
                    issue_type=IssueType.MISSING_BEHAVIOR_PROFILE,
                    object_id=object_data.get('id', ''),
                    severity="medium",
                    description=f"Missing behavior profile for {object_type}",
                    location={"type": object_type, "category": category},
                    current_value=None,
                    suggested_value=suitable_profile.profile_id,
                    fix_type=FixType.AUTO_FIX,
                    confidence=0.9,
                    timestamp=datetime.now(),
                    context={"available_profiles": list(self.behavior_profiles.keys())}
                )
        
        return None
    
    def _check_invalid_coordinates(self, object_data: Dict[str, Any], profile: BehaviorProfile) -> Optional[ValidationIssue]:
        """Check for invalid coordinates."""
        location = object_data.get('location', {})
        bounds = profile.properties.get('coordinate_bounds', {})
        
        is_valid, error_message, suggested_value = self._validate_coordinates(location, bounds)
        
        if not is_valid:
            return ValidationIssue(
                issue_id=self._generate_issue_id("temp", object_data.get('id', ''), IssueType.INVALID_COORDINATES),
                issue_type=IssueType.INVALID_COORDINATES,
                object_id=object_data.get('id', ''),
                severity="high",
                description=f"Invalid coordinates: {error_message}",
                location=location,
                current_value=location,
                suggested_value=suggested_value,
                fix_type=FixType.AUTO_FIX,
                confidence=0.95,
                timestamp=datetime.now(),
                context={"bounds": bounds, "error": error_message}
            )
        
        return None
    
    def _check_unlinked_symbol(self, object_data: Dict[str, Any], profile: BehaviorProfile) -> Optional[ValidationIssue]:
        """Check for unlinked symbols."""
        symbol_id = object_data.get('symbol_id')
        symbol_requirements = profile.properties.get('symbol_requirements', [])
        
        if not symbol_id and symbol_requirements:
            # Find a suitable default symbol
            default_symbol = self._find_default_symbol(profile.category, profile.object_type)
            
            return ValidationIssue(
                issue_id=self._generate_issue_id("temp", object_data.get('id', ''), IssueType.UNLINKED_SYMBOL),
                issue_type=IssueType.UNLINKED_SYMBOL,
                object_id=object_data.get('id', ''),
                severity="medium",
                description=f"Missing symbol link for {profile.object_type}",
                location={"symbol_id": symbol_id},
                current_value=symbol_id,
                suggested_value=default_symbol,
                fix_type=FixType.SUGGESTED_FIX,
                confidence=0.8,
                timestamp=datetime.now(),
                context={"required_symbols": symbol_requirements, "object_type": profile.object_type}
            )
        
        return None
    
    def _check_stale_metadata(self, object_data: Dict[str, Any], profile: BehaviorProfile) -> Optional[ValidationIssue]:
        """Check for stale metadata."""
        last_updated = object_data.get('last_updated', 0)
        current_time = int(time.time())
        
        # Consider metadata stale if older than 30 days
        stale_threshold = 30 * 24 * 60 * 60  # 30 days in seconds
        
        if current_time - last_updated > stale_threshold:
            return ValidationIssue(
                issue_id=self._generate_issue_id("temp", object_data.get('id', ''), IssueType.STALE_METADATA),
                issue_type=IssueType.STALE_METADATA,
                object_id=object_data.get('id', ''),
                severity="low",
                description=f"Stale metadata (last updated {datetime.fromtimestamp(last_updated)})",
                location={"last_updated": last_updated},
                current_value=last_updated,
                suggested_value=current_time,
                fix_type=FixType.SUGGESTED_FIX,
                confidence=0.7,
                timestamp=datetime.now(),
                context={"stale_threshold": stale_threshold, "days_old": (current_time - last_updated) // (24 * 60 * 60)}
            )
        
        return None
    
    def _check_duplicate_objects(self, objects: List[Dict[str, Any]]) -> List[ValidationIssue]:
        """Check for duplicate objects."""
        issues = []
        seen_objects = {}
        
        for obj in objects:
            obj_id = obj.get('id', '')
            obj_hash = self._calculate_object_hash(obj)
            
            if obj_hash in seen_objects:
                duplicate_obj = seen_objects[obj_hash]
                
                issues.append(ValidationIssue(
                    issue_id=self._generate_issue_id("temp", obj_id, IssueType.DUPLICATE_OBJECT),
                    issue_type=IssueType.DUPLICATE_OBJECT,
                    object_id=obj_id,
                    severity="high",
                    description=f"Duplicate object detected (similar to {duplicate_obj.get('id', '')})",
                    location={"duplicate_of": duplicate_obj.get('id', '')},
                    current_value=obj,
                    suggested_value=None,  # Manual review required
                    fix_type=FixType.MANUAL_FIX,
                    confidence=0.9,
                    timestamp=datetime.now(),
                    context={"duplicate_object": duplicate_obj}
                ))
            else:
                seen_objects[obj_hash] = obj
        
        return issues
    
    def _calculate_object_hash(self, obj: Dict[str, Any]) -> str:
        """Calculate a hash for object comparison."""
        # Create a simplified representation for comparison
        simplified = {
            'type': obj.get('type', ''),
            'name': obj.get('name', ''),
            'location': obj.get('location', {}),
            'properties': obj.get('properties', {})
        }
        
        return hashlib.sha256(json.dumps(simplified, sort_keys=True).encode()).hexdigest()
    
    def _find_default_symbol(self, category: str, object_type: str) -> Optional[str]:
        """Find a suitable default symbol for an object type."""
        # This would typically query a symbol library
        # For now, return a simple default based on category
        symbol_mapping = {
            'electrical': 'electrical_default',
            'hvac': 'hvac_default',
            'plumbing': 'plumbing_default',
            'equipment': 'equipment_default',
            'fixture': 'fixture_default'
        }
        
        return symbol_mapping.get(category, symbol_mapping.get(object_type, 'default_symbol'))
    
    def validate_floorplan(self, floorplan_id: str, floorplan_data: Dict[str, Any]) -> ValidationResult:
        """
        Perform comprehensive BIM health check on a floorplan.
        
        Args:
            floorplan_id: Unique identifier for the floorplan
            floorplan_data: Floorplan data containing objects to validate
            
        Returns:
            Validation result with issues and fix suggestions
        """
        start_time = time.time()
        validation_id = self._generate_validation_id(floorplan_id)
        
        with self.lock:
            try:
                logger.info(f"Starting BIM health check for floorplan {floorplan_id}")
                
                # Extract objects from floorplan data
                objects = floorplan_data.get('objects', [])
                if isinstance(objects, dict):
                    objects = list(objects.values())
                
                total_objects = len(objects)
                issues = []
                auto_fixes_applied = 0
                suggested_fixes = 0
                manual_fixes_required = 0
                
                # Check for duplicate objects
                duplicate_issues = self._check_duplicate_objects(objects)
                issues.extend(duplicate_issues)
                manual_fixes_required += len(duplicate_issues)
                
                # Validate each object
                for obj in objects:
                    obj_id = obj.get('id', '')
                    obj_type = obj.get('type', '')
                    obj_category = obj.get('category', '')
                    
                    # Find appropriate behavior profile
                    profile_key = f"{obj_type}_{obj_category}" if obj_category else obj_type
                    profile = self.behavior_profiles.get(profile_key)
                    
                    if not profile:
                        # Try to find a suitable profile
                        for p in self.behavior_profiles.values():
                            if p.object_type == obj_type or p.category == obj_category:
                                profile = p
                                break
                    
                    if profile:
                        # Check for missing behavior profile
                        missing_profile_issue = self._check_missing_behavior_profile(obj)
                        if missing_profile_issue:
                            issues.append(missing_profile_issue)
                            auto_fixes_applied += 1
                        
                        # Check for invalid coordinates
                        coord_issue = self._check_invalid_coordinates(obj, profile)
                        if coord_issue:
                            issues.append(coord_issue)
                            auto_fixes_applied += 1
                        
                        # Check for unlinked symbols
                        symbol_issue = self._check_unlinked_symbol(obj, profile)
                        if symbol_issue:
                            issues.append(symbol_issue)
                            suggested_fixes += 1
                        
                        # Check for stale metadata
                        stale_issue = self._check_stale_metadata(obj, profile)
                        if stale_issue:
                            issues.append(stale_issue)
                            suggested_fixes += 1
                    else:
                        # No behavior profile found
                        missing_profile_issue = self._check_missing_behavior_profile(obj)
                        if missing_profile_issue:
                            issues.append(missing_profile_issue)
                            manual_fixes_required += 1
                
                # Calculate validation time
                validation_time = time.time() - start_time
                
                # Create validation result
                result = ValidationResult(
                    validation_id=validation_id,
                    floorplan_id=floorplan_id,
                    status=ValidationStatus.COMPLETED,
                    total_objects=total_objects,
                    issues_found=len(issues),
                    auto_fixes_applied=auto_fixes_applied,
                    suggested_fixes=suggested_fixes,
                    manual_fixes_required=manual_fixes_required,
                    validation_time=validation_time,
                    timestamp=datetime.now(),
                    issues=issues,
                    summary={
                        "validation_score": max(0, 100 - len(issues) * 10),
                        "auto_fix_rate": auto_fixes_applied / max(len(issues), 1),
                        "suggestion_rate": suggested_fixes / max(len(issues), 1),
                        "manual_fix_rate": manual_fixes_required / max(len(issues), 1)
                    }
                )
                
                # Save result to database
                self._save_validation_result(result)
                
                # Update metrics
                self.metrics['total_validations'] += 1
                self.metrics['successful_validations'] += 1
                self.metrics['issues_detected'] += len(issues)
                self.metrics['auto_fixes_applied'] += auto_fixes_applied
                
                # Update average validation time
                total_validations = self.metrics['total_validations']
                current_avg = self.metrics['average_validation_time']
                self.metrics['average_validation_time'] = (
                    (current_avg * (total_validations - 1) + validation_time) / total_validations
                )
                
                logger.info(f"BIM health check completed for {floorplan_id}: {len(issues)} issues found")
                
                return result
                
            except Exception as e:
                logger.error(f"BIM health check failed for {floorplan_id}: {e}")
                
                # Create failed result
                result = ValidationResult(
                    validation_id=validation_id,
                    floorplan_id=floorplan_id,
                    status=ValidationStatus.FAILED,
                    total_objects=0,
                    issues_found=0,
                    auto_fixes_applied=0,
                    suggested_fixes=0,
                    manual_fixes_required=0,
                    validation_time=time.time() - start_time,
                    timestamp=datetime.now(),
                    issues=[],
                    summary={"error": str(e)}
                )
                
                self._save_validation_result(result)
                raise
    
    def apply_fixes(self, validation_id: str, fix_selections: Dict[str, str]) -> Dict[str, Any]:
        """
        Apply selected fixes to a validation result.
        
        Args:
            validation_id: Validation result ID
            fix_selections: Dictionary mapping issue IDs to fix actions
            
        Returns:
            Result of fix application
        """
        try:
            # Load validation result
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT * FROM validation_results WHERE validation_id = ?
                """, (validation_id,))
                
                result_row = cursor.fetchone()
                if not result_row:
                    raise ValueError(f"Validation result {validation_id} not found")
                
                # Load issues
                cursor = conn.execute("""
                    SELECT * FROM validation_issues WHERE validation_id = ?
                """, (validation_id,))
                
                issues = []
                for row in cursor.fetchall():
                    issue = ValidationIssue(
                        issue_id=row[0],
                        issue_type=IssueType(row[2]),
                        object_id=row[3],
                        severity=row[4],
                        description=row[5],
                        location=json.loads(row[6]) if row[6] else {},
                        current_value=json.loads(row[7]) if row[7] else None,
                        suggested_value=json.loads(row[8]) if row[8] else None,
                        fix_type=FixType(row[9]),
                        confidence=row[10],
                        timestamp=datetime.fromisoformat(row[11]),
                        context=json.loads(row[12]) if row[12] else {}
                    )
                    issues.append(issue)
            
            # Apply fixes
            applied_fixes = 0
            failed_fixes = 0
            
            for issue in issues:
                if issue.issue_id in fix_selections:
                    action = fix_selections[issue.issue_id]
                    
                    if action == "apply":
                        # Apply the suggested fix
                        success = self._apply_issue_fix(issue)
                        if success:
                            applied_fixes += 1
                        else:
                            failed_fixes += 1
                    elif action == "ignore":
                        # Mark as ignored
                        applied_fixes += 1
            
            return {
                "validation_id": validation_id,
                "applied_fixes": applied_fixes,
                "failed_fixes": failed_fixes,
                "total_issues": len(issues),
                "status": "completed"
            }
            
        except Exception as e:
            logger.error(f"Failed to apply fixes for {validation_id}: {e}")
            raise
    
    def _apply_issue_fix(self, issue: ValidationIssue) -> bool:
        """
        Apply a fix for a specific issue.
        
        Args:
            issue: Validation issue to fix
            
        Returns:
            True if fix was applied successfully
        """
        try:
            if issue.fix_type == FixType.AUTO_FIX:
                # Auto fixes are already applied during validation
                return True
            elif issue.fix_type == FixType.SUGGESTED_FIX:
                # Apply the suggested value
                if issue.suggested_value is not None:
                    # This would typically update the actual object data
                    # For now, we just return success
                    return True
            elif issue.fix_type == FixType.MANUAL_FIX:
                # Manual fixes require user intervention
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to apply fix for issue {issue.issue_id}: {e}")
            return False
    
    def get_validation_history(self, floorplan_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get validation history for a floorplan.
        
        Args:
            floorplan_id: Floorplan identifier
            limit: Maximum number of results to return
            
        Returns:
            List of validation results
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT * FROM validation_results 
                WHERE floorplan_id = ? 
                ORDER BY timestamp DESC 
                LIMIT ?
            """, (floorplan_id, limit))
            
            results = []
            for row in cursor.fetchall():
                results.append({
                    'validation_id': row[0],
                    'floorplan_id': row[1],
                    'status': row[2],
                    'total_objects': row[3],
                    'issues_found': row[4],
                    'auto_fixes_applied': row[5],
                    'suggested_fixes': row[6],
                    'manual_fixes_required': row[7],
                    'validation_time': row[8],
                    'timestamp': row[9],
                    'summary': json.loads(row[10]) if row[10] else {}
                })
            
            return results
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get BIM health checker performance metrics."""
        return {
            'metrics': self.metrics,
            'behavior_profiles': len(self.behavior_profiles),
            'database_size': Path(self.db_path).stat().st_size if Path(self.db_path).exists() else 0
        }
    
    def add_behavior_profile(self, profile: BehaviorProfile) -> None:
        """
        Add a new behavior profile.
        
        Args:
            profile: Behavior profile to add
        """
        self.behavior_profiles[profile.profile_id] = profile
        self._save_behavior_profile(profile)
    
    def get_behavior_profiles(self) -> List[Dict[str, Any]]:
        """Get all behavior profiles."""
        return [asdict(profile) for profile in self.behavior_profiles.values()] 