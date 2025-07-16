"""
SVGX Engine Symbol Schema Validation Service.

Implements comprehensive schema validation for SVGX symbols:
- SVGX schema validation with versioning support
- Custom validation rules and constraints
- Performance-optimized validation engine
- Real-time validation feedback
- Schema evolution and migration support
- SVGX-specific validation enhancements
- Validation caching and optimization
"""

import logging
import json
import re
import hashlib
import time
from typing import Dict, List, Any, Optional, Tuple, Union, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
import sqlite3
import xml.etree.ElementTree as ET
from xml.schema import XMLSchema
import jsonschema
from concurrent.futures import ThreadPoolExecutor
import threading
from collections import defaultdict, deque
import pickle
import zlib

try:
    from ..utils.performance import PerformanceMonitor
except ImportError:
    # Fallback for direct execution
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from utils.performance import PerformanceMonitor

try:
    from ..utils.errors import (
        ValidationError, SchemaError, SVGXError, PerformanceError
    )
except ImportError:
    # Fallback for direct execution
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from utils.errors import (
        ValidationError, SchemaError, SVGXError, PerformanceError
    )

from ..models.svgx import SVGXElement, SVGXDocument


@dataclass
class ValidationRule:
    """Represents a validation rule for SVGX symbols."""
    rule_id: str
    name: str
    description: str
    rule_type: str  # 'xml_schema', 'json_schema', 'custom', 'regex'
    schema_content: str
    severity: str  # 'error', 'warning', 'info'
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ValidationResult:
    """Result of a validation operation."""
    symbol_id: str
    is_valid: bool
    errors: List[Dict[str, Any]]
    warnings: List[Dict[str, Any]]
    info: List[Dict[str, Any]]
    validation_time: float
    schema_version: str
    applied_rules: List[str]
    metadata: Dict[str, Any]


@dataclass
class SchemaVersion:
    """Represents a schema version."""
    version: str
    description: str
    schema_content: str
    rules: List[ValidationRule]
    is_default: bool = False
    created_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ValidationCache:
    """Cache for validation results."""
    symbol_hash: str
    schema_version: str
    validation_result: ValidationResult
    cached_at: datetime
    expires_at: datetime


class SVGXSymbolSchemaValidationService:
    """
    SVGX Engine Symbol Schema Validation Service.
    
    Provides comprehensive schema validation for SVGX symbols with advanced features:
    - Multi-format schema validation (XML, JSON, custom)
    - Schema versioning and migration
    - Performance-optimized validation engine
    - Real-time validation feedback
    - Validation caching and optimization
    - SVGX-specific validation enhancements
    """
    
    def __init__(self, options: Optional[Dict[str, Any]] = None):
        """
        Initialize the Symbol Schema Validation Service.
        
        Args:
            options: Configuration options
        """
        self.options = {
            'enable_caching': True,
            'cache_ttl_seconds': 3600,  # 1 hour
            'max_cache_size': 1000,
            'enable_performance_monitoring': True,
            'validation_timeout_seconds': 30,
            'max_concurrent_validations': 10,
            'enable_schema_versioning': True,
            'default_schema_version': '1.0.0',
            'svgx_validation_enabled': True,
            'custom_rules_enabled': True,
            'performance_optimization': True,
        }
        if options:
            self.options.update(options)
        
        self.logger = logging.getLogger(__name__)
        self.performance_monitor = PerformanceMonitor()
        
        # Initialize databases
        self._init_databases()
        
        # Schema management
        self.schemas: Dict[str, SchemaVersion] = {}
        self.active_rules: Dict[str, ValidationRule] = {}
        self.validation_cache: Dict[str, ValidationCache] = {}
        self.cache_lock = threading.Lock()
        
        # Performance tracking
        self.validation_stats = {
            'total_validations': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'average_validation_time': 0.0,
            'error_count': 0,
            'warning_count': 0,
        }
        
        # Initialize default schemas
        self._initialize_default_schemas()
        
        self.logger.info("symbol_schema_validation_service_initialized",
                        options=self.options)
    
    def _init_databases(self):
        """Initialize validation databases."""
        self.validation_db_path = "data/validation.db"
        self.schema_db_path = "data/schema.db"
        self.cache_db_path = "data/validation_cache.db"
        
        # Create directories if they don't exist
        for db_path in [self.validation_db_path, self.schema_db_path, self.cache_db_path]:
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize validation database
        with sqlite3.connect(self.validation_db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS validation_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol_id TEXT NOT NULL,
                    symbol_hash TEXT NOT NULL,
                    schema_version TEXT NOT NULL,
                    is_valid BOOLEAN NOT NULL,
                    errors TEXT,
                    warnings TEXT,
                    info TEXT,
                    validation_time REAL,
                    applied_rules TEXT,
                    metadata TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_validation_symbol_id 
                ON validation_results(symbol_id)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_validation_hash 
                ON validation_results(symbol_hash)
            """)
        
        # Initialize schema database
        with sqlite3.connect(self.schema_db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS schemas (
                    version TEXT PRIMARY KEY,
                    description TEXT,
                    schema_content TEXT NOT NULL,
                    is_default BOOLEAN DEFAULT FALSE,
                    metadata TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS validation_rules (
                    rule_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    rule_type TEXT NOT NULL,
                    schema_content TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    is_active BOOLEAN DEFAULT TRUE,
                    metadata TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
        
        # Initialize cache database
        with sqlite3.connect(self.cache_db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS validation_cache (
                    symbol_hash TEXT PRIMARY KEY,
                    schema_version TEXT NOT NULL,
                    validation_result TEXT NOT NULL,
                    cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP NOT NULL
                )
            """)
    
    def _initialize_default_schemas(self):
        """Initialize default SVGX schemas."""
        self.logger.info("initializing_default_schemas")
        
        # Default SVGX XML Schema
        default_xml_schema = '''<?xml version="1.0" encoding="UTF-8"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"
           xmlns:svgx="http://www.svgx.org/schema/1.0"
           targetNamespace="http://www.svgx.org/schema/1.0"
           elementFormDefault="qualified">
    
    <xs:element name="svgx" type="svgx:SVGXType"/>
    
    <xs:complexType name="SVGXType">
        <xs:sequence>
            <xs:element name="metadata" type="svgx:MetadataType" minOccurs="0"/>
            <xs:element name="geometry" type="svgx:GeometryType" minOccurs="0"/>
            <xs:element name="behaviors" type="svgx:BehaviorsType" minOccurs="0"/>
            <xs:element name="physics" type="svgx:PhysicsType" minOccurs="0"/>
        </xs:sequence>
    </xs:complexType>
    
    <xs:complexType name="MetadataType">
        <xs:sequence>
            <xs:element name="name" type="xs:string"/>
            <xs:element name="description" type="xs:string" minOccurs="0"/>
            <xs:element name="version" type="xs:string"/>
            <xs:element name="author" type="xs:string"/>
            <xs:element name="tags" type="xs:string" minOccurs="0"/>
        </xs:sequence>
    </xs:complexType>
    
    <xs:complexType name="GeometryType">
        <xs:choice maxOccurs="unbounded">
            <xs:element name="rect" type="svgx:RectType"/>
            <xs:element name="circle" type="svgx:CircleType"/>
            <xs:element name="path" type="svgx:PathType"/>
            <xs:element name="group" type="svgx:GroupType"/>
        </xs:choice>
    </xs:complexType>
    
    <xs:complexType name="RectType">
        <xs:attribute name="x" type="xs:double" use="required"/>
        <xs:attribute name="y" type="xs:double" use="required"/>
        <xs:attribute name="width" type="xs:double" use="required"/>
        <xs:attribute name="height" type="xs:double" use="required"/>
        <xs:attribute name="fill" type="xs:string"/>
        <xs:attribute name="stroke" type="xs:string"/>
        <xs:attribute name="stroke-width" type="xs:double"/>
    </xs:complexType>
    
    <xs:complexType name="CircleType">
        <xs:attribute name="cx" type="xs:double" use="required"/>
        <xs:attribute name="cy" type="xs:double" use="required"/>
        <xs:attribute name="r" type="xs:double" use="required"/>
        <xs:attribute name="fill" type="xs:string"/>
        <xs:attribute name="stroke" type="xs:string"/>
        <xs:attribute name="stroke-width" type="xs:double"/>
    </xs:complexType>
    
    <xs:complexType name="PathType">
        <xs:attribute name="d" type="xs:string" use="required"/>
        <xs:attribute name="fill" type="xs:string"/>
        <xs:attribute name="stroke" type="xs:string"/>
        <xs:attribute name="stroke-width" type="xs:double"/>
    </xs:complexType>
    
    <xs:complexType name="GroupType">
        <xs:choice maxOccurs="unbounded">
            <xs:element name="rect" type="svgx:RectType"/>
            <xs:element name="circle" type="svgx:CircleType"/>
            <xs:element name="path" type="svgx:PathType"/>
            <xs:element name="group" type="svgx:GroupType"/>
        </xs:choice>
    </xs:complexType>
    
    <xs:complexType name="BehaviorsType">
        <xs:sequence>
            <xs:element name="behavior" type="svgx:BehaviorType" maxOccurs="unbounded"/>
        </xs:sequence>
    </xs:complexType>
    
    <xs:complexType name="BehaviorType">
        <xs:sequence>
            <xs:element name="action" type="xs:string"/>
        </xs:sequence>
        <xs:attribute name="name" type="xs:string" use="required"/>
        <xs:attribute name="type" type="xs:string" use="required"/>
    </xs:complexType>
    
    <xs:complexType name="PhysicsType">
        <xs:sequence>
            <xs:element name="mass" type="xs:double" minOccurs="0"/>
            <xs:element name="friction" type="xs:double" minOccurs="0"/>
            <xs:element name="elasticity" type="xs:double" minOccurs="0"/>
        </xs:sequence>
    </xs:complexType>
    
</xs:schema>'''
        
        # Default JSON Schema for SVGX
        default_json_schema = {
            "type": "object",
            "properties": {
                "metadata": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "description": {"type": "string"},
                        "version": {"type": "string"},
                        "author": {"type": "string"},
                        "tags": {"type": "string"}
                    },
                    "required": ["name", "version", "author"]
                },
                "geometry": {
                    "type": "object",
                    "properties": {
                        "elements": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "type": {"type": "string"},
                                    "attributes": {"type": "object"}
                                },
                                "required": ["type"]
                            }
                        }
                    }
                },
                "behaviors": {
                    "type": "object",
                    "properties": {
                        "actions": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "name": {"type": "string"},
                                    "type": {"type": "string"},
                                    "action": {"type": "string"}
                                },
                                "required": ["name", "type", "action"]
                            }
                        }
                    }
                },
                "physics": {
                    "type": "object",
                    "properties": {
                        "mass": {"type": "number"},
                        "friction": {"type": "number"},
                        "elasticity": {"type": "number"}
                    }
                }
            },
            "required": ["metadata"]
        }
        
        # Create default schema version
        default_schema = SchemaVersion(
            version=self.options['default_schema_version'],
            description="Default SVGX schema with comprehensive validation",
            schema_content=default_xml_schema,
            rules=[],
            is_default=True,
            metadata={
                'json_schema': default_json_schema,
                'supports_xml': True,
                'supports_json': True,
                'svgx_features': ['geometry', 'behaviors', 'physics', 'metadata']
            }
        )
        
        self.schemas[default_schema.version] = default_schema
        self._save_schema_version(default_schema)
        
        # Add default validation rules
        self._add_default_validation_rules()
    
    def _add_default_validation_rules(self):
        """Add default validation rules."""
        rules = [
            ValidationRule(
                rule_id="svgx_metadata_required",
                name="SVGX Metadata Required",
                description="Ensures SVGX symbols have required metadata",
                rule_type="custom",
                schema_content="metadata.name and metadata.version and metadata.author",
                severity="error"
            ),
            ValidationRule(
                rule_id="svgx_geometry_valid",
                name="SVGX Geometry Validation",
                description="Validates SVGX geometry elements",
                rule_type="custom",
                schema_content="geometry.elements or geometry.rect or geometry.circle or geometry.path",
                severity="warning"
            ),
            ValidationRule(
                rule_id="svgx_behavior_valid",
                name="SVGX Behavior Validation",
                description="Validates SVGX behavior definitions",
                rule_type="custom",
                schema_content="behaviors.actions or behaviors.behavior",
                severity="info"
            ),
            ValidationRule(
                rule_id="svgx_physics_valid",
                name="SVGX Physics Validation",
                description="Validates SVGX physics properties",
                rule_type="custom",
                schema_content="physics.mass >= 0 and physics.friction >= 0 and physics.friction <= 1",
                severity="warning"
            )
        ]
        
        for rule in rules:
            self.add_validation_rule(rule)
    
    def validate_symbol(self, symbol_id: str, content: str, 
                       schema_version: str = None, 
                       custom_rules: List[ValidationRule] = None) -> ValidationResult:
        """
        Validate an SVGX symbol against schemas and rules.
        
        Args:
            symbol_id: Unique identifier for the symbol
            content: SVGX symbol content (XML or JSON)
            schema_version: Schema version to use for validation
            custom_rules: Additional custom validation rules
            
        Returns:
            ValidationResult with validation results
        """
        start_time = time.time()
        
        try:
            # Use default schema version if not specified
            if schema_version is None:
                schema_version = self.options['default_schema_version']
            
            # Check cache first
            symbol_hash = self._generate_symbol_hash(content)
            cached_result = self._get_cached_validation(symbol_hash, schema_version)
            if cached_result:
                self.validation_stats['cache_hits'] += 1
                return cached_result
            
            self.validation_stats['cache_misses'] += 1
            
            # Initialize result
            errors = []
            warnings = []
            info = []
            applied_rules = []
            
            # Get schema for validation
            schema = self.schemas.get(schema_version)
            if not schema:
                raise SchemaError(f"Schema version {schema_version} not found")
            
            # Validate against XML schema
            if self._is_xml_content(content):
                xml_errors, xml_warnings, xml_info = self._validate_xml_schema(
                    content, schema, custom_rules
                )
                errors.extend(xml_errors)
                warnings.extend(xml_warnings)
                info.extend(xml_info)
                applied_rules.append("xml_schema_validation")
            
            # Validate against JSON schema
            elif self._is_json_content(content):
                json_errors, json_warnings, json_info = self._validate_json_schema(
                    content, schema, custom_rules
                )
                errors.extend(json_errors)
                warnings.extend(json_warnings)
                info.extend(json_info)
                applied_rules.append("json_schema_validation")
            
            # Apply custom validation rules
            custom_errors, custom_warnings, custom_info = self._apply_custom_rules(
                content, custom_rules or []
            )
            errors.extend(custom_errors)
            warnings.extend(custom_warnings)
            info.extend(custom_info)
            applied_rules.append("custom_rules")
            
            # Apply SVGX-specific validations
            if self.options['svgx_validation_enabled']:
                svgx_errors, svgx_warnings, svgx_info = self._validate_svgx_specific(
                    content
                )
                errors.extend(svgx_errors)
                warnings.extend(svgx_warnings)
                info.extend(svgx_info)
                applied_rules.append("svgx_specific_validation")
            
            # Create validation result
            validation_time = time.time() - start_time
            result = ValidationResult(
                symbol_id=symbol_id,
                is_valid=len(errors) == 0,
                errors=errors,
                warnings=warnings,
                info=info,
                validation_time=validation_time,
                schema_version=schema_version,
                applied_rules=applied_rules,
                metadata={
                    'symbol_hash': symbol_hash,
                    'content_type': 'xml' if self._is_xml_content(content) else 'json',
                    'performance_optimized': self.options['performance_optimization']
                }
            )
            
            # Cache the result
            if self.options['enable_caching']:
                self._cache_validation_result(symbol_hash, schema_version, result)
            
            # Update statistics
            self.validation_stats['total_validations'] += 1
            self.validation_stats['error_count'] += len(errors)
            self.validation_stats['warning_count'] += len(warnings)
            
            # Update average validation time
            total_validations = self.validation_stats['total_validations']
            current_avg = self.validation_stats['average_validation_time']
            self.validation_stats['average_validation_time'] = (
                (current_avg * (total_validations - 1) + validation_time) / total_validations
            )
            
            # Save validation result to database
            self._save_validation_result(result)
            
            return result
            
        except Exception as e:
            self.logger.error("validation_error", 
                            symbol_id=symbol_id, 
                            error=str(e))
            raise ValidationError(f"Validation failed: {str(e)}")
    
    def _validate_xml_schema(self, content: str, schema: SchemaVersion, 
                            custom_rules: List[ValidationRule]) -> Tuple[List, List, List]:
        """Validate XML content against schema."""
        errors = []
        warnings = []
        info = []
        
        try:
            # Parse XML content
            root = ET.fromstring(content)
            
            # Validate against XML schema
            schema_doc = ET.fromstring(schema.schema_content)
            xml_schema = XMLSchema(schema_doc)
            
            # Validate the document
            xml_schema.validate(root)
            
            # Apply custom rules for XML
            for rule in custom_rules:
                if rule.rule_type == 'xml_custom':
                    rule_result = self._apply_xml_custom_rule(root, rule)
                    if rule_result['is_error']:
                        errors.append(rule_result)
                    elif rule_result['is_warning']:
                        warnings.append(rule_result)
                    else:
                        info.append(rule_result)
            
        except ET.ParseError as e:
            errors.append({
                'rule_id': 'xml_parse_error',
                'message': f"XML parsing error: {str(e)}",
                'location': 'document',
                'severity': 'error'
            })
        except Exception as e:
            errors.append({
                'rule_id': 'xml_schema_error',
                'message': f"XML schema validation error: {str(e)}",
                'location': 'document',
                'severity': 'error'
            })
        
        return errors, warnings, info
    
    def _validate_json_schema(self, content: str, schema: SchemaVersion, 
                             custom_rules: List[ValidationRule]) -> Tuple[List, List, List]:
        """Validate JSON content against schema."""
        errors = []
        warnings = []
        info = []
        
        try:
            # Parse JSON content
            data = json.loads(content)
            
            # Get JSON schema from metadata
            json_schema = schema.metadata.get('json_schema')
            if json_schema:
                # Validate against JSON schema
                jsonschema.validate(data, json_schema)
            
            # Apply custom rules for JSON
            for rule in custom_rules:
                if rule.rule_type == 'json_custom':
                    rule_result = self._apply_json_custom_rule(data, rule)
                    if rule_result['is_error']:
                        errors.append(rule_result)
                    elif rule_result['is_warning']:
                        warnings.append(rule_result)
                    else:
                        info.append(rule_result)
            
        except json.JSONDecodeError as e:
            errors.append({
                'rule_id': 'json_parse_error',
                'message': f"JSON parsing error: {str(e)}",
                'location': 'document',
                'severity': 'error'
            })
        except jsonschema.ValidationError as e:
            errors.append({
                'rule_id': 'json_schema_error',
                'message': f"JSON schema validation error: {str(e)}",
                'path': str(e.path),
                'severity': 'error'
            })
        except Exception as e:
            errors.append({
                'rule_id': 'json_validation_error',
                'message': f"JSON validation error: {str(e)}",
                'location': 'document',
                'severity': 'error'
            })
        
        return errors, warnings, info
    
    def _apply_custom_rules(self, content: str, custom_rules: List[ValidationRule]) -> Tuple[List, List, List]:
        """Apply custom validation rules."""
        errors = []
        warnings = []
        info = []
        
        for rule in custom_rules:
            if not rule.is_active:
                continue
                
            try:
                if rule.rule_type == 'regex':
                    result = self._apply_regex_rule(content, rule)
                elif rule.rule_type == 'custom':
                    result = self._apply_custom_rule(content, rule)
                else:
                    continue
                
                if result['is_error']:
                    errors.append(result)
                elif result['is_warning']:
                    warnings.append(result)
                else:
                    info.append(result)
                    
            except Exception as e:
                self.logger.warning("custom_rule_error", 
                                  rule_id=rule.rule_id, 
                                  error=str(e))
        
        return errors, warnings, info
    
    def _validate_svgx_specific(self, content: str) -> Tuple[List, List, List]:
        """Apply SVGX-specific validations."""
        errors = []
        warnings = []
        info = []
        
        # Check for required SVGX elements
        if '<svgx' not in content:
            errors.append({
                'rule_id': 'svgx_root_element',
                'message': "Missing SVGX root element",
                'severity': 'error'
            })
        
        # Check for metadata
        if '<metadata>' not in content:
            warnings.append({
                'rule_id': 'svgx_metadata',
                'message': "Missing metadata section",
                'severity': 'warning'
            })
        
        # Check for geometry
        if '<geometry>' not in content:
            warnings.append({
                'rule_id': 'svgx_geometry',
                'message': "Missing geometry section",
                'severity': 'warning'
            })
        
        # Check for behaviors
        if '<behaviors>' in content:
            info.append({
                'rule_id': 'svgx_behaviors',
                'message': "Behaviors section found",
                'severity': 'info'
            })
        
        # Check for physics
        if '<physics>' in content:
            info.append({
                'rule_id': 'svgx_physics',
                'message': "Physics section found",
                'severity': 'info'
            })
        
        return errors, warnings, info
    
    def add_validation_rule(self, rule: ValidationRule) -> bool:
        """Add a new validation rule."""
        try:
            self.active_rules[rule.rule_id] = rule
            self._save_validation_rule(rule)
            self.logger.info("validation_rule_added", rule_id=rule.rule_id)
            return True
        except Exception as e:
            self.logger.error("add_validation_rule_error", 
                            rule_id=rule.rule_id, 
                            error=str(e))
            return False
    
    def remove_validation_rule(self, rule_id: str) -> bool:
        """Remove a validation rule."""
        try:
            if rule_id in self.active_rules:
                del self.active_rules[rule_id]
                self._delete_validation_rule(rule_id)
                self.logger.info("validation_rule_removed", rule_id=rule_id)
                return True
            return False
        except Exception as e:
            self.logger.error("remove_validation_rule_error", 
                            rule_id=rule_id, 
                            error=str(e))
            return False
    
    def add_schema_version(self, schema: SchemaVersion) -> bool:
        """Add a new schema version."""
        try:
            self.schemas[schema.version] = schema
            self._save_schema_version(schema)
            self.logger.info("schema_version_added", version=schema.version)
            return True
        except Exception as e:
            self.logger.error("add_schema_version_error", 
                            version=schema.version, 
                            error=str(e))
            return False
    
    def get_schema_version(self, version: str) -> Optional[SchemaVersion]:
        """Get a schema version."""
        return self.schemas.get(version)
    
    def get_validation_statistics(self) -> Dict[str, Any]:
        """Get validation statistics."""
        return {
            **self.validation_stats,
            'cache_size': len(self.validation_cache),
            'active_rules_count': len(self.active_rules),
            'schema_versions_count': len(self.schemas),
            'performance_metrics': self.performance_monitor.get_metrics()
        }
    
    def clear_cache(self) -> bool:
        """Clear validation cache."""
        try:
            with self.cache_lock:
                self.validation_cache.clear()
            
            # Clear cache database
            with sqlite3.connect(self.cache_db_path) as conn:
                conn.execute("DELETE FROM validation_cache")
            
            self.logger.info("validation_cache_cleared")
            return True
        except Exception as e:
            self.logger.error("clear_cache_error", error=str(e))
            return False
    
    def _generate_symbol_hash(self, content: str) -> str:
        """Generate hash for symbol content."""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
    
    def _is_xml_content(self, content: str) -> bool:
        """Check if content is XML."""
        return content.strip().startswith('<?xml') or content.strip().startswith('<')
    
    def _is_json_content(self, content: str) -> bool:
        """Check if content is JSON."""
        try:
            json.loads(content)
            return True
        except:
            return False
    
    def _get_cached_validation(self, symbol_hash: str, schema_version: str) -> Optional[ValidationResult]:
        """Get cached validation result."""
        if not self.options['enable_caching']:
            return None
        
        cache_key = f"{symbol_hash}_{schema_version}"
        
        with self.cache_lock:
            cached = self.validation_cache.get(cache_key)
            if cached and cached.expires_at > datetime.now():
                return cached.validation_result
        
        return None
    
    def _cache_validation_result(self, symbol_hash: str, schema_version: str, result: ValidationResult):
        """Cache validation result."""
        if not self.options['enable_caching']:
            return
        
        cache_key = f"{symbol_hash}_{schema_version}"
        expires_at = datetime.now() + timedelta(seconds=self.options['cache_ttl_seconds'])
        
        cache_entry = ValidationCache(
            symbol_hash=symbol_hash,
            schema_version=schema_version,
            validation_result=result,
            cached_at=datetime.now(),
            expires_at=expires_at
        )
        
        with self.cache_lock:
            # Implement LRU cache eviction
            if len(self.validation_cache) >= self.options['max_cache_size']:
                oldest_key = min(self.validation_cache.keys(), 
                               key=lambda k: self.validation_cache[k].cached_at)
                del self.validation_cache[oldest_key]
            
            self.validation_cache[cache_key] = cache_entry
        
        # Save to database
        with sqlite3.connect(self.cache_db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO validation_cache 
                (symbol_hash, schema_version, validation_result, cached_at, expires_at)
                VALUES (?, ?, ?, ?, ?)
            """, (
                symbol_hash,
                schema_version,
                pickle.dumps(result),
                cache_entry.cached_at.isoformat(),
                cache_entry.expires_at.isoformat()
            ))
    
    def _save_validation_result(self, result: ValidationResult):
        """Save validation result to database."""
        with sqlite3.connect(self.validation_db_path) as conn:
            conn.execute("""
                INSERT INTO validation_results 
                (symbol_id, symbol_hash, schema_version, is_valid, errors, warnings, info,
                 validation_time, applied_rules, metadata, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                result.symbol_id,
                result.metadata.get('symbol_hash', ''),
                result.schema_version,
                result.is_valid,
                json.dumps(result.errors),
                json.dumps(result.warnings),
                json.dumps(result.info),
                result.validation_time,
                json.dumps(result.applied_rules),
                json.dumps(result.metadata),
                datetime.now().isoformat()
            ))
    
    def _save_schema_version(self, schema: SchemaVersion):
        """Save schema version to database."""
        with sqlite3.connect(self.schema_db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO schemas 
                (version, description, schema_content, is_default, metadata, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                schema.version,
                schema.description,
                schema.schema_content,
                schema.is_default,
                json.dumps(schema.metadata),
                schema.created_at.isoformat()
            ))
    
    def _save_validation_rule(self, rule: ValidationRule):
        """Save validation rule to database."""
        with sqlite3.connect(self.schema_db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO validation_rules 
                (rule_id, name, description, rule_type, schema_content, severity, 
                 is_active, metadata, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                rule.rule_id,
                rule.name,
                rule.description,
                rule.rule_type,
                rule.schema_content,
                rule.severity,
                rule.is_active,
                json.dumps(rule.metadata),
                rule.created_at.isoformat()
            ))
    
    def _delete_validation_rule(self, rule_id: str):
        """Delete validation rule from database."""
        with sqlite3.connect(self.schema_db_path) as conn:
            conn.execute("DELETE FROM validation_rules WHERE rule_id = ?", (rule_id,))
    
    def _apply_xml_custom_rule(self, root: ET.Element, rule: ValidationRule) -> Dict[str, Any]:
        """Apply custom rule to XML content."""
        # Implementation would depend on the specific rule
        return {
            'rule_id': rule.rule_id,
            'message': f"Custom XML rule applied: {rule.name}",
            'severity': rule.severity,
            'is_error': rule.severity == 'error',
            'is_warning': rule.severity == 'warning'
        }
    
    def _apply_json_custom_rule(self, data: Dict, rule: ValidationRule) -> Dict[str, Any]:
        """Apply custom rule to JSON content."""
        # Implementation would depend on the specific rule
        return {
            'rule_id': rule.rule_id,
            'message': f"Custom JSON rule applied: {rule.name}",
            'severity': rule.severity,
            'is_error': rule.severity == 'error',
            'is_warning': rule.severity == 'warning'
        }
    
    def _apply_regex_rule(self, content: str, rule: ValidationRule) -> Dict[str, Any]:
        """Apply regex rule to content."""
        try:
            pattern = re.compile(rule.schema_content)
            if pattern.search(content):
                return {
                    'rule_id': rule.rule_id,
                    'message': f"Regex rule matched: {rule.name}",
                    'severity': rule.severity,
                    'is_error': rule.severity == 'error',
                    'is_warning': rule.severity == 'warning'
                }
            else:
                return {
                    'rule_id': rule.rule_id,
                    'message': f"Regex rule failed: {rule.name}",
                    'severity': rule.severity,
                    'is_error': rule.severity == 'error',
                    'is_warning': rule.severity == 'warning'
                }
        except Exception as e:
            return {
                'rule_id': rule.rule_id,
                'message': f"Regex rule error: {str(e)}",
                'severity': 'error',
                'is_error': True,
                'is_warning': False
            }
    
    def _apply_custom_rule(self, content: str, rule: ValidationRule) -> Dict[str, Any]:
        """Apply custom rule to content."""
        # Implementation would depend on the specific rule
        return {
            'rule_id': rule.rule_id,
            'message': f"Custom rule applied: {rule.name}",
            'severity': rule.severity,
            'is_error': rule.severity == 'error',
            'is_warning': rule.severity == 'warning'
        }
    
    def cleanup(self):
        """Cleanup resources."""
        try:
            # Clear expired cache entries
            with self.cache_lock:
                current_time = datetime.now()
                expired_keys = [
                    key for key, cache_entry in self.validation_cache.items()
                    if cache_entry.expires_at <= current_time
                ]
                for key in expired_keys:
                    del self.validation_cache[key]
            
            self.logger.info("symbol_schema_validation_cleanup_completed")
        except Exception as e:
            self.logger.error("cleanup_error", error=str(e))


def create_symbol_schema_validation_service(options: Optional[Dict[str, Any]] = None) -> SVGXSymbolSchemaValidationService:
    """
    Create a Symbol Schema Validation Service instance.
    
    Args:
        options: Configuration options
        
    Returns:
        SVGXSymbolSchemaValidationService instance
    """
    return SVGXSymbolSchemaValidationService(options) 