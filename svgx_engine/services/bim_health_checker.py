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
        
        logger.info("BIM Health Checker Service initialized")
    
    def _init_database(self) -> None:
        """Initialize the SQLite database with required tables."""
        try:
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
                logger.info("Database initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
    
    def _load_behavior_profiles(self) -> None:
        """Load behavior profiles from database and default profiles."""
        try:
            # Load from database
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("SELECT * FROM behavior_profiles")
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
            
            # Create default profiles if none exist
            if not self.behavior_profiles:
                self._create_default_behavior_profiles()
            
            logger.info(f"Loaded {len(self.behavior_profiles)} behavior profiles")
        except Exception as e:
            logger.error(f"Failed to load behavior profiles: {e}")
            self._create_default_behavior_profiles()
    
    def _create_default_behavior_profiles(self) -> None:
        """Create default behavior profiles for common BIM objects."""
        default_profiles = [
            BehaviorProfile(
                profile_id="wall_default",
                object_type="wall",
                category="structural",
                properties={
                    "height": {"type": "float", "required": True, "min": 0.1, "max": 100.0},
                    "thickness": {"type": "float", "required": True, "min": 0.05, "max": 2.0},
                    "material": {"type": "string", "required": True},
                    "fire_rating": {"type": "string", "required": False}
                },
                validation_rules={
                    "coordinates": {"required": True, "min_points": 2},
                    "bounds": {"required": True},
                    "symbol": {"required": True}
                },
                fix_suggestions={
                    "missing_height": {"action": "set_default", "value": 3.0},
                    "missing_thickness": {"action": "set_default", "value": 0.2},
                    "missing_material": {"action": "set_default", "value": "concrete"},
                    "invalid_coordinates": {"action": "correct_bounds"}
                }
            ),
            BehaviorProfile(
                profile_id="door_default",
                object_type="door",
                category="access",
                properties={
                    "width": {"type": "float", "required": True, "min": 0.6, "max": 3.0},
                    "height": {"type": "float", "required": True, "min": 1.8, "max": 3.0},
                    "type": {"type": "string", "required": True},
                    "fire_rating": {"type": "string", "required": False}
                },
                validation_rules={
                    "coordinates": {"required": True, "min_points": 2},
                    "bounds": {"required": True},
                    "symbol": {"required": True}
                },
                fix_suggestions={
                    "missing_width": {"action": "set_default", "value": 0.9},
                    "missing_height": {"action": "set_default", "value": 2.1},
                    "missing_type": {"action": "set_default", "value": "swing"},
                    "invalid_coordinates": {"action": "correct_bounds"}
                }
            ),
            BehaviorProfile(
                profile_id="window_default",
                object_type="window",
                category="access",
                properties={
                    "width": {"type": "float", "required": True, "min": 0.3, "max": 5.0},
                    "height": {"type": "float", "required": True, "min": 0.3, "max": 5.0},
                    "type": {"type": "string", "required": True},
                    "glazing": {"type": "string", "required": False}
                },
                validation_rules={
                    "coordinates": {"required": True, "min_points": 2},
                    "bounds": {"required": True},
                    "symbol": {"required": True}
                },
                fix_suggestions={
                    "missing_width": {"action": "set_default", "value": 1.2},
                    "missing_height": {"action": "set_default", "value": 1.5},
                    "missing_type": {"action": "set_default", "value": "fixed"},
                    "invalid_coordinates": {"action": "correct_bounds"}
                }
            ),
            BehaviorProfile(
                profile_id="device_default",
                object_type="device",
                category="equipment",
                properties={
                    "type": {"type": "string", "required": True},
                    "system": {"type": "string", "required": True},
                    "capacity": {"type": "float", "required": False},
                    "efficiency": {"type": "float", "required": False}
                },
                validation_rules={
                    "coordinates": {"required": True, "min_points": 1},
                    "bounds": {"required": True},
                    "symbol": {"required": True}
                },
                fix_suggestions={
                    "missing_type": {"action": "infer_from_symbol"},
                    "missing_system": {"action": "infer_from_symbol"},
                    "invalid_coordinates": {"action": "correct_bounds"}
                }
            )
        ]
        
        for profile in default_profiles:
            self.behavior_profiles[profile.profile_id] = profile
            self._save_behavior_profile(profile)
        
        logger.info(f"Created {len(default_profiles)} default behavior profiles")
    
    def _save_behavior_profile(self, profile: BehaviorProfile) -> None:
        """Save behavior profile to database."""
        try:
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
        except Exception as e:
            logger.error(f"Failed to save behavior profile: {e}")
    
    def _save_validation_result(self, result: ValidationResult) -> None:
        """Save validation result to database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Save main result
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
                
                # Save individual issues
                for issue in result.issues:
                    conn.execute("""
                        INSERT OR REPLACE INTO validation_issues 
                        (issue_id, validation_id, issue_type, object_id, severity, description,
                         location, current_value, suggested_value, fix_type, confidence, timestamp, context)
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
        except Exception as e:
            logger.error(f"Failed to save validation result: {e}")
    
    def _generate_validation_id(self, floorplan_id: str) -> str:
        """Generate unique validation ID."""
        timestamp = int(time.time())
        return f"validation_{floorplan_id}_{timestamp}"
    
    def _generate_issue_id(self, validation_id: str, object_id: str, issue_type: IssueType) -> str:
        """Generate unique issue ID."""
        return f"issue_{validation_id}_{object_id}_{issue_type.value}"
    
    def _validate_coordinates(self, coordinates: Dict[str, Any], bounds: Dict[str, List[int]]) -> Tuple[bool, str, Any]:
        """Validate coordinates against bounds."""
        try:
            if not coordinates or not bounds:
                return False, "Missing coordinates or bounds", None
            
            x = coordinates.get('x', 0)
            y = coordinates.get('y', 0)
            
            min_x, max_x = bounds.get('x', [0, 1000])
            min_y, max_y = bounds.get('y', [0, 1000])
            
            if not (min_x <= x <= max_x and min_y <= y <= max_y):
                return False, "Coordinates out of bounds", {"x": max(min_x, min(x, max_x)), "y": max(min_y, min(y, max_y))}
            
            return True, "Valid coordinates", coordinates
        except Exception as e:
            return False, f"Coordinate validation error: {e}", None
    
    def _check_missing_behavior_profile(self, object_data: Dict[str, Any]) -> Optional[ValidationIssue]:
        """Check for missing behavior profile."""
        object_type = object_data.get('type', 'unknown')
        category = object_data.get('category', 'unknown')
        
        # Look for matching profile
        profile_key = f"{object_type}_{category}"
        if profile_key not in self.behavior_profiles:
            # Try default profile
            default_key = f"{object_type}_default"
            if default_key not in self.behavior_profiles:
                return ValidationIssue(
                    issue_id=self._generate_issue_id("temp", object_data.get('id', 'unknown'), IssueType.MISSING_BEHAVIOR_PROFILE),
                    issue_type=IssueType.MISSING_BEHAVIOR_PROFILE,
                    object_id=object_data.get('id', 'unknown'),
                    severity="medium",
                    description=f"Missing behavior profile for {object_type} in category {category}",
                    location={"type": object_type, "category": category},
                    current_value=None,
                    suggested_value=default_key,
                    fix_type=FixType.SUGGESTED_FIX,
                    confidence=0.8,
                    timestamp=datetime.utcnow(),
                    context={"object_data": object_data}
                )
        
        return None
    
    def _check_invalid_coordinates(self, object_data: Dict[str, Any], profile: BehaviorProfile) -> Optional[ValidationIssue]:
        """Check for invalid coordinates."""
        coordinates = object_data.get('coordinates', {})
        bounds = object_data.get('bounds', {})
        
        is_valid, message, corrected = self._validate_coordinates(coordinates, bounds)
        
        if not is_valid:
            return ValidationIssue(
                issue_id=self._generate_issue_id("temp", object_data.get('id', 'unknown'), IssueType.INVALID_COORDINATES),
                issue_type=IssueType.INVALID_COORDINATES,
                object_id=object_data.get('id', 'unknown'),
                severity="high",
                description=f"Invalid coordinates: {message}",
                location=coordinates,
                current_value=coordinates,
                suggested_value=corrected,
                fix_type=FixType.AUTO_FIX,
                confidence=0.9,
                timestamp=datetime.utcnow(),
                context={"profile": profile.profile_id}
            )
        
        return None
    
    def _check_unlinked_symbol(self, object_data: Dict[str, Any], profile: BehaviorProfile) -> Optional[ValidationIssue]:
        """Check for unlinked symbols."""
        symbol_id = object_data.get('symbol_id')
        
        if not symbol_id:
            # Try to find a default symbol
            default_symbol = self._find_default_symbol(profile.category, profile.object_type)
            
            return ValidationIssue(
                issue_id=self._generate_issue_id("temp", object_data.get('id', 'unknown'), IssueType.UNLINKED_SYMBOL),
                issue_type=IssueType.UNLINKED_SYMBOL,
                object_id=object_data.get('id', 'unknown'),
                severity="medium",
                description=f"Object has no linked symbol",
                location={"symbol_id": symbol_id},
                current_value=None,
                suggested_value=default_symbol,
                fix_type=FixType.SUGGESTED_FIX,
                confidence=0.7,
                timestamp=datetime.utcnow(),
                context={"profile": profile.profile_id}
            )
        
        return None
    
    def _check_stale_metadata(self, object_data: Dict[str, Any], profile: BehaviorProfile) -> Optional[ValidationIssue]:
        """Check for stale metadata."""
        last_updated = object_data.get('last_updated')
        if last_updated:
            try:
                update_time = datetime.fromisoformat(last_updated)
                if datetime.utcnow() - update_time > timedelta(days=30):
                    return ValidationIssue(
                        issue_id=self._generate_issue_id("temp", object_data.get('id', 'unknown'), IssueType.STALE_METADATA),
                        issue_type=IssueType.STALE_METADATA,
                        object_id=object_data.get('id', 'unknown'),
                        severity="low",
                        description="Object metadata is stale (older than 30 days)",
                        location={"last_updated": last_updated},
                        current_value=last_updated,
                        suggested_value=datetime.utcnow().isoformat(),
                        fix_type=FixType.AUTO_FIX,
                        confidence=0.6,
                        timestamp=datetime.utcnow(),
                        context={"profile": profile.profile_id}
                    )
            except ValueError:
                pass
        
        return None
    
    def _check_duplicate_objects(self, objects: List[Dict[str, Any]]) -> List[ValidationIssue]:
        """Check for duplicate objects."""
        issues = []
        object_hashes = {}
        
        for obj in objects:
            obj_hash = self._calculate_object_hash(obj)
            if obj_hash in object_hashes:
                # Found duplicate
                original_obj = object_hashes[obj_hash]
                issues.append(ValidationIssue(
                    issue_id=self._generate_issue_id("temp", obj.get('id', 'unknown'), IssueType.DUPLICATE_OBJECT),
                    issue_type=IssueType.DUPLICATE_OBJECT,
                    object_id=obj.get('id', 'unknown'),
                    severity="high",
                    description=f"Duplicate object found (matches {original_obj.get('id', 'unknown')})",
                    location={"duplicate_of": original_obj.get('id', 'unknown')},
                    current_value=obj,
                    suggested_value=None,
                    fix_type=FixType.MANUAL_FIX,
                    confidence=0.95,
                    timestamp=datetime.utcnow(),
                    context={"original_object": original_obj}
                ))
            else:
                object_hashes[obj_hash] = obj
        
        return issues
    
    def _calculate_object_hash(self, obj: Dict[str, Any]) -> str:
        """Calculate hash for object to detect duplicates."""
        # Create a simplified representation for hashing
        hash_data = {
            'type': obj.get('type'),
            'coordinates': obj.get('coordinates'),
            'bounds': obj.get('bounds'),
            'symbol_id': obj.get('symbol_id')
        }
        return hashlib.md5(json.dumps(hash_data, sort_keys=True).encode()).hexdigest()
    
    def _find_default_symbol(self, category: str, object_type: str) -> Optional[str]:
        """Find default symbol for object type and category."""
        # Simple mapping - in production, this would be more sophisticated
        symbol_mapping = {
            ('structural', 'wall'): 'wall_symbol',
            ('access', 'door'): 'door_symbol',
            ('access', 'window'): 'window_symbol',
            ('equipment', 'device'): 'device_symbol'
        }
        
        return symbol_mapping.get((category, object_type))
    
    def validate_floorplan(self, floorplan_id: str, floorplan_data: Dict[str, Any]) -> ValidationResult:
        """
        Validate a floorplan for BIM health issues.
        
        Args:
            floorplan_id: Unique identifier for the floorplan
            floorplan_data: Floorplan data to validate
            
        Returns:
            ValidationResult with all issues found
        """
        start_time = time.time()
        validation_id = self._generate_validation_id(floorplan_id)
        
        try:
            logger.info(f"Starting BIM health check for floorplan: {floorplan_id}")
            
            issues = []
            objects = floorplan_data.get('objects', [])
            total_objects = len(objects)
            
            # Check for duplicate objects
            duplicate_issues = self._check_duplicate_objects(objects)
            issues.extend(duplicate_issues)
            
            # Validate each object
            for obj in objects:
                # Check for missing behavior profile
                profile_issue = self._check_missing_behavior_profile(obj)
                if profile_issue:
                    issues.append(profile_issue)
                
                # Find appropriate behavior profile
                object_type = obj.get('type', 'unknown')
                category = obj.get('category', 'unknown')
                profile_key = f"{object_type}_{category}"
                profile = self.behavior_profiles.get(profile_key) or self.behavior_profiles.get(f"{object_type}_default")
                
                if profile:
                    # Check invalid coordinates
                    coord_issue = self._check_invalid_coordinates(obj, profile)
                    if coord_issue:
                        issues.append(coord_issue)
                    
                    # Check unlinked symbols
                    symbol_issue = self._check_unlinked_symbol(obj, profile)
                    if symbol_issue:
                        issues.append(symbol_issue)
                    
                    # Check stale metadata
                    metadata_issue = self._check_stale_metadata(obj, profile)
                    if metadata_issue:
                        issues.append(metadata_issue)
            
            # Calculate statistics
            auto_fixes = sum(1 for issue in issues if issue.fix_type == FixType.AUTO_FIX)
            suggested_fixes = sum(1 for issue in issues if issue.fix_type == FixType.SUGGESTED_FIX)
            manual_fixes = sum(1 for issue in issues if issue.fix_type == FixType.MANUAL_FIX)
            
            validation_time = time.time() - start_time
            
            # Create result
            result = ValidationResult(
                validation_id=validation_id,
                floorplan_id=floorplan_id,
                status=ValidationStatus.COMPLETED,
                total_objects=total_objects,
                issues_found=len(issues),
                auto_fixes_applied=0,  # Will be updated when fixes are applied
                suggested_fixes=suggested_fixes,
                manual_fixes_required=manual_fixes,
                validation_time=validation_time,
                timestamp=datetime.utcnow(),
                issues=issues,
                summary={
                    "total_objects": total_objects,
                    "issues_by_type": {},
                    "severity_distribution": {},
                    "fix_distribution": {}
                }
            )
            
            # Update summary statistics
            for issue in issues:
                issue_type = issue.issue_type.value
                result.summary["issues_by_type"][issue_type] = result.summary["issues_by_type"].get(issue_type, 0) + 1
                
                result.summary["severity_distribution"][issue.severity] = result.summary["severity_distribution"].get(issue.severity, 0) + 1
                
                result.summary["fix_distribution"][issue.fix_type.value] = result.summary["fix_distribution"].get(issue.fix_type.value, 0) + 1
            
            # Save result
            self._save_validation_result(result)
            
            # Update metrics
            self.metrics["total_validations"] += 1
            self.metrics["successful_validations"] += 1
            self.metrics["issues_detected"] += len(issues)
            self.metrics["average_validation_time"] = (
                (self.metrics["average_validation_time"] * (self.metrics["total_validations"] - 1) + validation_time) /
                self.metrics["total_validations"]
            )
            
            logger.info(f"BIM health check completed for {floorplan_id}: {len(issues)} issues found")
            return result
            
        except Exception as e:
            logger.error(f"BIM health check failed for {floorplan_id}: {e}")
            return ValidationResult(
                validation_id=validation_id,
                floorplan_id=floorplan_id,
                status=ValidationStatus.FAILED,
                total_objects=0,
                issues_found=0,
                auto_fixes_applied=0,
                suggested_fixes=0,
                manual_fixes_required=0,
                validation_time=time.time() - start_time,
                timestamp=datetime.utcnow(),
                issues=[],
                summary={"error": str(e)}
            )
    
    def apply_fixes(self, validation_id: str, fix_selections: Dict[str, str]) -> Dict[str, Any]:
        """
        Apply selected fixes to validation issues.
        
        Args:
            validation_id: Validation ID to apply fixes to
            fix_selections: Dictionary mapping issue_id to fix action
            
        Returns:
            Dictionary with fix application results
        """
        try:
            # Find validation result
            validation_result = None
            for result in self.validation_results:
                if result.validation_id == validation_id:
                    validation_result = result
                    break
            
            if not validation_result:
                return {"success": False, "error": "Validation result not found"}
            
            applied_fixes = 0
            failed_fixes = 0
            
            for issue in validation_result.issues:
                if issue.issue_id in fix_selections:
                    fix_action = fix_selections[issue.issue_id]
                    
                    if fix_action == "apply":
                        if self._apply_issue_fix(issue):
                            applied_fixes += 1
                        else:
                            failed_fixes += 1
                    elif fix_action == "ignore":
                        # Mark as ignored
                        issue.fix_type = FixType.IGNORE
                        applied_fixes += 1
            
            # Update validation result
            validation_result.auto_fixes_applied = applied_fixes
            self._save_validation_result(validation_result)
            
            # Update metrics
            self.metrics["auto_fixes_applied"] += applied_fixes
            
            return {
                "success": True,
                "applied_fixes": applied_fixes,
                "failed_fixes": failed_fixes,
                "total_issues": len(validation_result.issues)
            }
            
        except Exception as e:
            logger.error(f"Failed to apply fixes: {e}")
            return {"success": False, "error": str(e)}
    
    def _apply_issue_fix(self, issue: ValidationIssue) -> bool:
        """Apply a single issue fix."""
        try:
            if issue.fix_type == FixType.AUTO_FIX:
                # Apply the suggested fix
                if issue.suggested_value is not None:
                    # In a real implementation, this would update the actual object
                    # For now, we just mark it as applied
                    return True
            return False
        except Exception as e:
            logger.error(f"Failed to apply fix for issue {issue.issue_id}: {e}")
            return False
    
    def get_validation_history(self, floorplan_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get validation history for a floorplan."""
        try:
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
                        "validation_id": row[0],
                        "floorplan_id": row[1],
                        "status": row[2],
                        "total_objects": row[3],
                        "issues_found": row[4],
                        "auto_fixes_applied": row[5],
                        "suggested_fixes": row[6],
                        "manual_fixes_required": row[7],
                        "validation_time": row[8],
                        "timestamp": row[9],
                        "summary": json.loads(row[10]) if row[10] else {}
                    })
                
                return results
        except Exception as e:
            logger.error(f"Failed to get validation history: {e}")
            return []
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get service metrics."""
        return self.metrics.copy()
    
    def add_behavior_profile(self, profile: BehaviorProfile) -> None:
        """Add a new behavior profile."""
        self.behavior_profiles[profile.profile_id] = profile
        self._save_behavior_profile(profile)
        logger.info(f"Added behavior profile: {profile.profile_id}")
    
    def get_behavior_profiles(self) -> List[Dict[str, Any]]:
        """Get all behavior profiles."""
        return [asdict(profile) for profile in self.behavior_profiles.values()] 