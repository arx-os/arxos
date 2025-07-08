"""
Building Regulations Database Models

This module provides database models and schema for storing building regulations,
validation rules, and compliance data. Supports both PostgreSQL and SQLite.
"""

import json
import sqlite3
from datetime import datetime, date
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class RegulationType(Enum):
    """Types of building regulations"""
    STRUCTURAL = "structural"
    FIRE_SAFETY = "fire_safety"
    ACCESSIBILITY = "accessibility"
    ENERGY = "energy"
    MECHANICAL = "mechanical"
    ELECTRICAL = "electrical"
    PLUMBING = "plumbing"
    ENVIRONMENTAL = "environmental"
    GENERAL = "general"


class ValidationStatus(Enum):
    """Validation status values"""
    PENDING = "pending"
    PASSED = "passed"
    FAILED = "failed"
    PARTIAL = "partial"


class ViolationSeverity(Enum):
    """Violation severity levels"""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class Jurisdiction:
    """Jurisdiction information"""
    id: Optional[int] = None
    name: str = ""
    country: str = ""
    state: Optional[str] = None
    city: Optional[str] = None
    code: str = ""
    description: Optional[str] = None
    active: bool = True
    created_dt: Optional[datetime] = None
    updated_dt: Optional[datetime] = None


@dataclass
class Category:
    """Regulation category"""
    id: Optional[int] = None
    name: str = ""
    description: Optional[str] = None
    parent_id: Optional[int] = None
    code: str = ""
    active: bool = True
    created_dt: Optional[datetime] = None
    updated_dt: Optional[datetime] = None


@dataclass
class Regulation:
    """Building regulation"""
    id: Optional[int] = None
    code: str = ""
    title: str = ""
    description: Optional[str] = None
    category_id: Optional[int] = None
    jurisdiction_id: Optional[int] = None
    regulation_type: str = ""
    effective_dt: Optional[date] = None
    expires_dt: Optional[date] = None
    version: str = "1.0"
    status: str = "active"
    priority: int = 1
    active: bool = True
    created_dt: Optional[datetime] = None
    updated_dt: Optional[datetime] = None


@dataclass
class RegulationVersion:
    """Versioned regulation content"""
    id: Optional[int] = None
    regulation_id: Optional[int] = None
    version: str = ""
    effective_dt: Optional[date] = None
    expires_dt: Optional[date] = None
    content: str = ""
    content_type: str = "json"
    change_summary: Optional[str] = None
    approved_by: Optional[str] = None
    approved_dt: Optional[datetime] = None
    active: bool = True
    created_dt: Optional[datetime] = None
    updated_dt: Optional[datetime] = None


@dataclass
class RegulationParameter:
    """Regulation parameter"""
    id: Optional[int] = None
    regulation_id: Optional[int] = None
    param_name: str = ""
    param_type: str = ""
    param_value: str = ""
    units: Optional[str] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    enum_values: Optional[List[str]] = None
    required: bool = False
    description: Optional[str] = None
    active: bool = True
    created_dt: Optional[datetime] = None
    updated_dt: Optional[datetime] = None


@dataclass
class ValidationRule:
    """Validation rule"""
    id: Optional[int] = None
    regulation_id: Optional[int] = None
    rule_name: str = ""
    rule_type: str = ""
    rule_logic: str = ""
    conditions: Optional[str] = None
    actions: Optional[str] = None
    severity: str = "error"
    priority: int = 1
    description: Optional[str] = None
    active: bool = True
    created_dt: Optional[datetime] = None
    updated_dt: Optional[datetime] = None


@dataclass
class BuildingValidation:
    """Building validation result"""
    id: Optional[int] = None
    building_id: str = ""
    regulation_id: Optional[int] = None
    validation_status: str = ""
    compliance_score: Optional[float] = None
    total_rules: int = 0
    passed_rules: int = 0
    failed_rules: int = 0
    warnings: int = 0
    details: Optional[str] = None
    validated_dt: Optional[datetime] = None
    created_dt: Optional[datetime] = None
    updated_dt: Optional[datetime] = None


@dataclass
class ValidationViolation:
    """Validation violation"""
    id: Optional[int] = None
    building_validation_id: Optional[int] = None
    rule_id: Optional[int] = None
    violation_type: str = ""
    severity: str = ""
    description: str = ""
    location: Optional[str] = None
    element_id: Optional[str] = None
    current_value: Optional[str] = None
    required_value: Optional[str] = None
    tolerance: Optional[float] = None
    recommendation: Optional[str] = None
    created_dt: Optional[datetime] = None


class BuildingRegulationsDB:
    """Database manager for building regulations"""
    
    def __init__(self, db_path: str = "building_regulations.db"):
        """Initialize database connection"""
        self.db_path = db_path
        self.conn = None
        self.init_database()
    
    def init_database(self):
        """Initialize database schema"""
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row
            self.create_tables()
            self.create_indexes()
            self.insert_sample_data()
            logger.info(f"Building regulations database initialized: {self.db_path}")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
    
    def create_tables(self):
        """Create database tables"""
        cursor = self.conn.cursor()
        
        # Jurisdictions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS jurisdictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                country TEXT NOT NULL,
                state TEXT,
                city TEXT,
                code TEXT UNIQUE NOT NULL,
                description TEXT,
                active INTEGER DEFAULT 1,
                created_dt DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_dt DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Categories table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                parent_id INTEGER REFERENCES categories(id),
                code TEXT UNIQUE NOT NULL,
                active INTEGER DEFAULT 1,
                created_dt DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_dt DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Regulations table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS regulations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                category_id INTEGER REFERENCES categories(id),
                jurisdiction_id INTEGER REFERENCES jurisdictions(id),
                regulation_type TEXT NOT NULL,
                effective_dt DATE NOT NULL,
                expires_dt DATE,
                version TEXT DEFAULT '1.0',
                status TEXT DEFAULT 'active',
                priority INTEGER DEFAULT 1,
                active INTEGER DEFAULT 1,
                created_dt DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_dt DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(code, jurisdiction_id, version)
            )
        """)
        
        # Regulation versions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS regulation_versions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                regulation_id INTEGER REFERENCES regulations(id),
                version TEXT NOT NULL,
                effective_dt DATE NOT NULL,
                expires_dt DATE,
                content TEXT NOT NULL,
                content_type TEXT DEFAULT 'json',
                change_summary TEXT,
                approved_by TEXT,
                approved_dt DATETIME,
                active INTEGER DEFAULT 1,
                created_dt DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_dt DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(regulation_id, version)
            )
        """)
        
        # Regulation parameters table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS regulation_parameters (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                regulation_id INTEGER REFERENCES regulations(id),
                param_name TEXT NOT NULL,
                param_type TEXT NOT NULL,
                param_value TEXT NOT NULL,
                units TEXT,
                min_value REAL,
                max_value REAL,
                enum_values TEXT,
                required INTEGER DEFAULT 0,
                description TEXT,
                active INTEGER DEFAULT 1,
                created_dt DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_dt DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(regulation_id, param_name)
            )
        """)
        
        # Validation rules table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS validation_rules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                regulation_id INTEGER REFERENCES regulations(id),
                rule_name TEXT NOT NULL,
                rule_type TEXT NOT NULL,
                rule_logic TEXT NOT NULL,
                conditions TEXT,
                actions TEXT,
                severity TEXT DEFAULT 'error',
                priority INTEGER DEFAULT 1,
                description TEXT,
                active INTEGER DEFAULT 1,
                created_dt DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_dt DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(regulation_id, rule_name)
            )
        """)
        
        # Building validations table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS building_validations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                building_id TEXT NOT NULL,
                regulation_id INTEGER REFERENCES regulations(id),
                validation_status TEXT NOT NULL,
                compliance_score REAL,
                total_rules INTEGER DEFAULT 0,
                passed_rules INTEGER DEFAULT 0,
                failed_rules INTEGER DEFAULT 0,
                warnings INTEGER DEFAULT 0,
                details TEXT,
                validated_dt DATETIME DEFAULT CURRENT_TIMESTAMP,
                created_dt DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_dt DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Validation violations table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS validation_violations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                building_validation_id INTEGER REFERENCES building_validations(id),
                rule_id INTEGER REFERENCES validation_rules(id),
                violation_type TEXT NOT NULL,
                severity TEXT NOT NULL,
                description TEXT NOT NULL,
                location TEXT,
                element_id TEXT,
                current_value TEXT,
                required_value TEXT,
                tolerance REAL,
                recommendation TEXT,
                created_dt DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        self.conn.commit()
        logger.info("Database tables created successfully")
    
    def create_indexes(self):
        """Create database indexes for performance"""
        cursor = self.conn.cursor()
        
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_regulations_jurisdiction ON regulations(jurisdiction_id)",
            "CREATE INDEX IF NOT EXISTS idx_regulations_category ON regulations(category_id)",
            "CREATE INDEX IF NOT EXISTS idx_regulations_type ON regulations(regulation_type)",
            "CREATE INDEX IF NOT EXISTS idx_regulations_active ON regulations(active)",
            "CREATE INDEX IF NOT EXISTS idx_regulations_effective ON regulations(effective_dt)",
            "CREATE INDEX IF NOT EXISTS idx_validation_rules_regulation ON validation_rules(regulation_id)",
            "CREATE INDEX IF NOT EXISTS idx_validation_rules_type ON validation_rules(rule_type)",
            "CREATE INDEX IF NOT EXISTS idx_validation_rules_active ON validation_rules(active)",
            "CREATE INDEX IF NOT EXISTS idx_building_validations_building ON building_validations(building_id)",
            "CREATE INDEX IF NOT EXISTS idx_building_validations_regulation ON building_validations(regulation_id)",
            "CREATE INDEX IF NOT EXISTS idx_building_validations_status ON building_validations(validation_status)",
            "CREATE INDEX IF NOT EXISTS idx_violations_validation ON validation_violations(building_validation_id)",
            "CREATE INDEX IF NOT EXISTS idx_violations_rule ON validation_violations(rule_id)",
            "CREATE INDEX IF NOT EXISTS idx_violations_severity ON validation_violations(severity)"
        ]
        
        for index_sql in indexes:
            cursor.execute(index_sql)
        
        self.conn.commit()
        logger.info("Database indexes created successfully")
    
    def insert_sample_data(self):
        """Insert sample data for testing"""
        cursor = self.conn.cursor()
        
        # Check if data already exists
        cursor.execute("SELECT COUNT(*) FROM jurisdictions")
        if cursor.fetchone()[0] > 0:
            logger.info("Sample data already exists, skipping insertion")
            return
        
        # Insert jurisdictions
        jurisdictions = [
            ('United States - International Building Code', 'USA', None, None, 'IBC', 'International Building Code'),
            ('United States - NFPA 101', 'USA', None, None, 'NFPA101', 'Life Safety Code'),
            ('United States - ADA Standards', 'USA', None, None, 'ADA', 'Americans with Disabilities Act'),
            ('United States - ASHRAE 90.1', 'USA', None, None, 'ASHRAE90.1', 'Energy Standard for Buildings'),
            ('Canada - National Building Code', 'Canada', None, None, 'NBC', 'National Building Code of Canada'),
            ('United Kingdom - Building Regulations', 'UK', None, None, 'UKBR', 'Building Regulations England and Wales')
        ]
        
        cursor.executemany("""
            INSERT INTO jurisdictions (name, country, state, city, code, description)
            VALUES (?, ?, ?, ?, ?, ?)
        """, jurisdictions)
        
        # Insert categories
        categories = [
            ('Structural', 'Structural integrity and load-bearing requirements', None, 'STRUCTURAL'),
            ('Fire Safety', 'Fire protection, egress, and life safety requirements', None, 'FIRE_SAFETY'),
            ('Accessibility', 'Accessibility and universal design requirements', None, 'ACCESSIBILITY'),
            ('Energy Efficiency', 'Energy conservation and efficiency requirements', None, 'ENERGY'),
            ('Mechanical', 'HVAC and mechanical system requirements', None, 'MECHANICAL'),
            ('Electrical', 'Electrical system and safety requirements', None, 'ELECTRICAL'),
            ('Plumbing', 'Plumbing and water system requirements', None, 'PLUMBING'),
            ('Environmental', 'Environmental and sustainability requirements', None, 'ENVIRONMENTAL')
        ]
        
        cursor.executemany("""
            INSERT INTO categories (name, description, parent_id, code)
            VALUES (?, ?, ?, ?)
        """, categories)
        
        # Get category IDs for subcategories
        cursor.execute("SELECT id FROM categories WHERE code = 'STRUCTURAL'")
        structural_id = cursor.fetchone()[0]
        
        cursor.execute("SELECT id FROM categories WHERE code = 'FIRE_SAFETY'")
        fire_id = cursor.fetchone()[0]
        
        cursor.execute("SELECT id FROM categories WHERE code = 'ACCESSIBILITY'")
        accessibility_id = cursor.fetchone()[0]
        
        cursor.execute("SELECT id FROM categories WHERE code = 'ENERGY'")
        energy_id = cursor.fetchone()[0]
        
        # Insert subcategories
        subcategories = [
            ('Load Bearing', 'Load-bearing wall and structural element requirements', structural_id, 'LOAD_BEARING'),
            ('Foundation', 'Foundation and soil requirements', structural_id, 'FOUNDATION'),
            ('Fire Resistance', 'Fire resistance ratings and materials', fire_id, 'FIRE_RESISTANCE'),
            ('Egress', 'Means of egress and exit requirements', fire_id, 'EGRESS'),
            ('Wheelchair Access', 'Wheelchair accessibility requirements', accessibility_id, 'WHEELCHAIR_ACCESS'),
            ('Energy Conservation', 'Energy conservation measures', energy_id, 'ENERGY_CONSERVATION')
        ]
        
        cursor.executemany("""
            INSERT INTO categories (name, description, parent_id, code)
            VALUES (?, ?, ?, ?)
        """, subcategories)
        
        # Get jurisdiction and category IDs for regulations
        cursor.execute("SELECT id FROM jurisdictions WHERE code = 'IBC'")
        ibc_id = cursor.fetchone()[0]
        
        cursor.execute("SELECT id FROM jurisdictions WHERE code = 'ADA'")
        ada_id = cursor.fetchone()[0]
        
        cursor.execute("SELECT id FROM categories WHERE code = 'STRUCTURAL'")
        structural_cat_id = cursor.fetchone()[0]
        
        cursor.execute("SELECT id FROM categories WHERE code = 'ACCESSIBILITY'")
        accessibility_cat_id = cursor.fetchone()[0]
        
        cursor.execute("SELECT id FROM categories WHERE code = 'FIRE_SAFETY'")
        fire_cat_id = cursor.fetchone()[0]
        
        cursor.execute("SELECT id FROM categories WHERE code = 'ENERGY'")
        energy_cat_id = cursor.fetchone()[0]
        
        # Insert sample regulations
        regulations = [
            ('IBC-1607.1', 'Live Loads', 'Minimum uniformly distributed live loads and concentrated live loads', 
             structural_cat_id, ibc_id, 'structural', '2021-01-01'),
            ('IBC-1003.3.1', 'Ceiling Height', 'Minimum ceiling height requirements for habitable spaces', 
             accessibility_cat_id, ibc_id, 'accessibility', '2021-01-01'),
            ('IBC-1006.2.1', 'Number of Exits', 'Minimum number of exits required based on occupant load', 
             fire_cat_id, ibc_id, 'fire', '2021-01-01'),
            ('ADA-403.5.1', 'Clear Width', 'Minimum clear width for accessible routes', 
             accessibility_cat_id, ada_id, 'accessibility', '2010-03-15'),
            ('ASHRAE-9.4.1.1', 'Building Envelope', 'Building envelope requirements for energy efficiency', 
             energy_cat_id, ada_id, 'energy', '2019-01-01')
        ]
        
        cursor.executemany("""
            INSERT INTO regulations (code, title, description, category_id, jurisdiction_id, regulation_type, effective_dt)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, regulations)
        
        self.conn.commit()
        logger.info("Sample data inserted successfully")
    
    def get_jurisdictions(self) -> List[Jurisdiction]:
        """Get all active jurisdictions"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM jurisdictions WHERE active = 1 ORDER BY name
        """)
        
        jurisdictions = []
        for row in cursor.fetchall():
            jurisdiction = Jurisdiction(
                id=row['id'],
                name=row['name'],
                country=row['country'],
                state=row['state'],
                city=row['city'],
                code=row['code'],
                description=row['description'],
                active=bool(row['active']),
                created_dt=datetime.fromisoformat(row['created_dt']) if row['created_dt'] else None,
                updated_dt=datetime.fromisoformat(row['updated_dt']) if row['updated_dt'] else None
            )
            jurisdictions.append(jurisdiction)
        
        return jurisdictions
    
    def get_categories(self, parent_id: Optional[int] = None) -> List[Category]:
        """Get categories, optionally filtered by parent"""
        cursor = self.conn.cursor()
        
        if parent_id is None:
            cursor.execute("""
                SELECT * FROM categories WHERE active = 1 ORDER BY name
            """)
        else:
            cursor.execute("""
                SELECT * FROM categories WHERE active = 1 AND parent_id = ? ORDER BY name
            """, (parent_id,))
        
        categories = []
        for row in cursor.fetchall():
            category = Category(
                id=row['id'],
                name=row['name'],
                description=row['description'],
                parent_id=row['parent_id'],
                code=row['code'],
                active=bool(row['active']),
                created_dt=datetime.fromisoformat(row['created_dt']) if row['created_dt'] else None,
                updated_dt=datetime.fromisoformat(row['updated_dt']) if row['updated_dt'] else None
            )
            categories.append(category)
        
        return categories
    
    def get_regulations(self, category_id: Optional[int] = None, 
                       jurisdiction_id: Optional[int] = None,
                       regulation_type: Optional[str] = None) -> List[Regulation]:
        """Get regulations with optional filtering"""
        cursor = self.conn.cursor()
        
        query = """
            SELECT r.*, c.name as category_name, j.name as jurisdiction_name
            FROM regulations r
            JOIN categories c ON r.category_id = c.id
            JOIN jurisdictions j ON r.jurisdiction_id = j.id
            WHERE r.active = 1
        """
        params = []
        
        if category_id:
            query += " AND r.category_id = ?"
            params.append(category_id)
        
        if jurisdiction_id:
            query += " AND r.jurisdiction_id = ?"
            params.append(jurisdiction_id)
        
        if regulation_type:
            query += " AND r.regulation_type = ?"
            params.append(regulation_type)
        
        query += " ORDER BY r.code"
        
        cursor.execute(query, params)
        
        regulations = []
        for row in cursor.fetchall():
            regulation = Regulation(
                id=row['id'],
                code=row['code'],
                title=row['title'],
                description=row['description'],
                category_id=row['category_id'],
                jurisdiction_id=row['jurisdiction_id'],
                regulation_type=row['regulation_type'],
                effective_dt=date.fromisoformat(row['effective_dt']) if row['effective_dt'] else None,
                expires_dt=date.fromisoformat(row['expires_dt']) if row['expires_dt'] else None,
                version=row['version'],
                status=row['status'],
                priority=row['priority'],
                active=bool(row['active']),
                created_dt=datetime.fromisoformat(row['created_dt']) if row['created_dt'] else None,
                updated_dt=datetime.fromisoformat(row['updated_dt']) if row['updated_dt'] else None
            )
            regulations.append(regulation)
        
        return regulations
    
    def get_validation_rules(self, regulation_id: int) -> List[ValidationRule]:
        """Get validation rules for a regulation"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM validation_rules 
            WHERE regulation_id = ? AND active = 1 
            ORDER BY priority DESC, severity
        """, (regulation_id,))
        
        rules = []
        for row in cursor.fetchall():
            rule = ValidationRule(
                id=row['id'],
                regulation_id=row['regulation_id'],
                rule_name=row['rule_name'],
                rule_type=row['rule_type'],
                rule_logic=row['rule_logic'],
                conditions=row['conditions'],
                actions=row['actions'],
                severity=row['severity'],
                priority=row['priority'],
                description=row['description'],
                active=bool(row['active']),
                created_dt=datetime.fromisoformat(row['created_dt']) if row['created_dt'] else None,
                updated_dt=datetime.fromisoformat(row['updated_dt']) if row['updated_dt'] else None
            )
            rules.append(rule)
        
        return rules
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")


class PostgreSQLBuildingRegulationsDB:
    """PostgreSQL/PostGIS implementation for building regulations"""
    
    def __init__(self, connection_string: str):
        """Initialize PostgreSQL connection"""
        self.connection_string = connection_string
        self.conn = None
        # Implementation for PostgreSQL would go here
        # This is a placeholder for future PostgreSQL implementation
        logger.info("PostgreSQL implementation placeholder - not yet implemented")
    
    def init_database(self):
        """Initialize PostgreSQL database schema"""
        # PostgreSQL-specific implementation
        pass
    
    def create_tables(self):
        """Create PostgreSQL tables"""
        # PostgreSQL-specific implementation
        pass
    
    def close(self):
        """Close PostgreSQL connection"""
        if self.conn:
            self.conn.close()


# Factory function for creating database instances
def create_regulations_db(db_type: str = "sqlite", **kwargs) -> Union[BuildingRegulationsDB, PostgreSQLBuildingRegulationsDB]:
    """Create a database instance based on type"""
    if db_type.lower() == "sqlite":
        db_path = kwargs.get("db_path", "building_regulations.db")
        return BuildingRegulationsDB(db_path)
    elif db_type.lower() == "postgresql":
        connection_string = kwargs.get("connection_string")
        if not connection_string:
            raise ValueError("PostgreSQL connection_string is required")
        return PostgreSQLBuildingRegulationsDB(connection_string)
    else:
        raise ValueError(f"Unsupported database type: {db_type}") 