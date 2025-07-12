# Building Regulation Database Schema Design

## 🎯 Overview

This document defines the database schema for storing building regulations, codes, and validation rules. The schema supports multiple jurisdictions, regulation categories, versioning, and complex rule definitions.

## 🏗️ Schema Architecture

### Entity-Relationship Diagram (ERD)

```
┌─────────────────────────────────────────────────────────────────┐
│                    Building Regulations Database                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐        │
│  │ jurisdictions│    │ categories  │    │ regulations │        │
│  │             │    │             │    │             │        │
│  │ id (PK)     │    │ id (PK)     │    │ id (PK)     │        │
│  │ name        │    │ name        │    │ code        │        │
│  │ country     │    │ description │    │ title       │        │
│  │ state       │    │ parent_id   │    │ description │        │
│  │ city        │    │ active      │    │ category_id │        │
│  │ active      │    └─────────────┘    │ jurisdiction│        │
│  └─────────────┘                       │ effective_dt│        │
│                                        │ expires_dt  │        │
│                                        │ active      │        │
│                                        └─────────────┘        │
│                                                │              │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐        │
│  │ versions    │    │ parameters  │    │ rules       │        │
│  │             │    │             │    │             │        │
│  │ id (PK)     │    │ id (PK)     │    │ id (PK)     │        │
│  │ regulation_id│   │ regulation_id│   │ regulation_id│       │
│  │ version     │    │ param_name  │    │ rule_name   │        │
│  │ effective_dt│    │ param_type  │    │ rule_type   │        │
│  │ expires_dt  │    │ param_value │    │ rule_logic  │        │
│  │ content     │    │ units       │    │ conditions  │        │
│  │ active      │    │ required    │    │ actions     │        │
│  └─────────────┘    │ active      │    │ priority    │        │
│                     └─────────────┘    │ active      │        │
│                                        └─────────────┘        │
│                                                                 │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐        │
│  │ validations │    │ violations  │    │ compliance  │        │
│  │             │    │             │    │             │        │
│  │ id (PK)     │    │ id (PK)     │    │ id (PK)     │        │
│  │ building_id │    │ validation_id│   │ building_id │        │
│  │ regulation_id│   │ rule_id     │    │ regulation_id│       │
│  │ status      │    │ severity    │    │ status      │        │
│  │ score       │    │ description │    │ score       │        │
│  │ details     │    │ location    │    │ details     │        │
│  │ created_dt  │    │ created_dt  │    │ created_dt  │        │
│  │ updated_dt  │    │ active      │    │ updated_dt  │        │
│  └─────────────┘    └─────────────┘    └─────────────┘        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## 📋 Table Definitions

### 1. jurisdictions
Stores information about different jurisdictions (countries, states, cities) that have building codes.

```sql
-- PostgreSQL/PostGIS
CREATE TABLE jurisdictions (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    country VARCHAR(100) NOT NULL,
    state VARCHAR(100),
    city VARCHAR(100),
    code VARCHAR(50) UNIQUE NOT NULL,
    description TEXT,
    active BOOLEAN DEFAULT TRUE,
    created_dt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_dt TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- SQLite
CREATE TABLE jurisdictions (
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
);
```

### 2. categories
Stores regulation categories and subcategories for organizing building codes.

```sql
-- PostgreSQL/PostGIS
CREATE TABLE categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    parent_id INTEGER REFERENCES categories(id),
    code VARCHAR(50) UNIQUE NOT NULL,
    active BOOLEAN DEFAULT TRUE,
    created_dt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_dt TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- SQLite
CREATE TABLE categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    parent_id INTEGER REFERENCES categories(id),
    code TEXT UNIQUE NOT NULL,
    active INTEGER DEFAULT 1,
    created_dt DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_dt DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### 3. regulations
Stores the main regulation records with metadata and relationships.

```sql
-- PostgreSQL/PostGIS
CREATE TABLE regulations (
    id SERIAL PRIMARY KEY,
    code VARCHAR(100) NOT NULL,
    title VARCHAR(500) NOT NULL,
    description TEXT,
    category_id INTEGER REFERENCES categories(id),
    jurisdiction_id INTEGER REFERENCES jurisdictions(id),
    regulation_type VARCHAR(50) NOT NULL, -- 'structural', 'fire', 'accessibility', 'energy', etc.
    effective_dt DATE NOT NULL,
    expires_dt DATE,
    version VARCHAR(20) DEFAULT '1.0',
    status VARCHAR(20) DEFAULT 'active', -- 'active', 'draft', 'superseded', 'repealed'
    priority INTEGER DEFAULT 1,
    active BOOLEAN DEFAULT TRUE,
    created_dt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_dt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(code, jurisdiction_id, version)
);

-- SQLite
CREATE TABLE regulations (
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
);
```

### 4. regulation_versions
Stores versioned content and changes for regulations.

```sql
-- PostgreSQL/PostGIS
CREATE TABLE regulation_versions (
    id SERIAL PRIMARY KEY,
    regulation_id INTEGER REFERENCES regulations(id),
    version VARCHAR(20) NOT NULL,
    effective_dt DATE NOT NULL,
    expires_dt DATE,
    content TEXT NOT NULL, -- JSON or XML content
    content_type VARCHAR(20) DEFAULT 'json', -- 'json', 'xml', 'text'
    change_summary TEXT,
    approved_by VARCHAR(255),
    approved_dt TIMESTAMP,
    active BOOLEAN DEFAULT TRUE,
    created_dt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_dt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(regulation_id, version)
);

-- SQLite
CREATE TABLE regulation_versions (
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
);
```

### 5. regulation_parameters
Stores parameters and values used in regulation calculations and validations.

```sql
-- PostgreSQL/PostGIS
CREATE TABLE regulation_parameters (
    id SERIAL PRIMARY KEY,
    regulation_id INTEGER REFERENCES regulations(id),
    param_name VARCHAR(255) NOT NULL,
    param_type VARCHAR(50) NOT NULL, -- 'numeric', 'string', 'boolean', 'date', 'enum'
    param_value TEXT NOT NULL,
    units VARCHAR(50),
    min_value DECIMAL(10,4),
    max_value DECIMAL(10,4),
    enum_values TEXT[], -- For enum types
    required BOOLEAN DEFAULT FALSE,
    description TEXT,
    active BOOLEAN DEFAULT TRUE,
    created_dt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_dt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(regulation_id, param_name)
);

-- SQLite
CREATE TABLE regulation_parameters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    regulation_id INTEGER REFERENCES regulations(id),
    param_name TEXT NOT NULL,
    param_type TEXT NOT NULL,
    param_value TEXT NOT NULL,
    units TEXT,
    min_value REAL,
    max_value REAL,
    enum_values TEXT, -- JSON array for enum types
    required INTEGER DEFAULT 0,
    description TEXT,
    active INTEGER DEFAULT 1,
    created_dt DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_dt DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(regulation_id, param_name)
);
```

### 6. validation_rules
Stores the actual validation rules and logic for each regulation.

```sql
-- PostgreSQL/PostGIS
CREATE TABLE validation_rules (
    id SERIAL PRIMARY KEY,
    regulation_id INTEGER REFERENCES regulations(id),
    rule_name VARCHAR(255) NOT NULL,
    rule_type VARCHAR(50) NOT NULL, -- 'structural', 'fire', 'accessibility', 'energy', 'general'
    rule_logic TEXT NOT NULL, -- JSON or SQL-like logic
    conditions TEXT, -- JSON conditions
    actions TEXT, -- JSON actions to take
    severity VARCHAR(20) DEFAULT 'error', -- 'error', 'warning', 'info'
    priority INTEGER DEFAULT 1,
    description TEXT,
    active BOOLEAN DEFAULT TRUE,
    created_dt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_dt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(regulation_id, rule_name)
);

-- SQLite
CREATE TABLE validation_rules (
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
);
```

### 7. building_validations
Stores validation results for specific buildings.

```sql
-- PostgreSQL/PostGIS
CREATE TABLE building_validations (
    id SERIAL PRIMARY KEY,
    building_id VARCHAR(255) NOT NULL,
    regulation_id INTEGER REFERENCES regulations(id),
    validation_status VARCHAR(20) NOT NULL, -- 'pending', 'passed', 'failed', 'partial'
    compliance_score DECIMAL(5,2), -- 0-100 score
    total_rules INTEGER DEFAULT 0,
    passed_rules INTEGER DEFAULT 0,
    failed_rules INTEGER DEFAULT 0,
    warnings INTEGER DEFAULT 0,
    details TEXT, -- JSON details
    validated_dt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_dt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_dt TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- SQLite
CREATE TABLE building_validations (
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
);
```

### 8. validation_violations
Stores specific violations found during validation.

```sql
-- PostgreSQL/PostGIS
CREATE TABLE validation_violations (
    id SERIAL PRIMARY KEY,
    building_validation_id INTEGER REFERENCES building_validations(id),
    rule_id INTEGER REFERENCES validation_rules(id),
    violation_type VARCHAR(50) NOT NULL, -- 'structural', 'fire', 'accessibility', 'energy', 'general'
    severity VARCHAR(20) NOT NULL, -- 'error', 'warning', 'info'
    description TEXT NOT NULL,
    location TEXT, -- JSON location data
    element_id VARCHAR(255), -- Reference to building element
    current_value TEXT,
    required_value TEXT,
    tolerance DECIMAL(10,4),
    recommendation TEXT,
    created_dt TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- SQLite
CREATE TABLE validation_violations (
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
);
```

## 🔧 Indexes and Performance

### PostgreSQL/PostGIS Indexes
```sql
-- Performance indexes
CREATE INDEX idx_regulations_jurisdiction ON regulations(jurisdiction_id);
CREATE INDEX idx_regulations_category ON regulations(category_id);
CREATE INDEX idx_regulations_type ON regulations(regulation_type);
CREATE INDEX idx_regulations_active ON regulations(active);
CREATE INDEX idx_regulations_effective ON regulations(effective_dt);

CREATE INDEX idx_validation_rules_regulation ON validation_rules(regulation_id);
CREATE INDEX idx_validation_rules_type ON validation_rules(rule_type);
CREATE INDEX idx_validation_rules_active ON validation_rules(active);

CREATE INDEX idx_building_validations_building ON building_validations(building_id);
CREATE INDEX idx_building_validations_regulation ON building_validations(regulation_id);
CREATE INDEX idx_building_validations_status ON building_validations(validation_status);

CREATE INDEX idx_violations_validation ON validation_violations(building_validation_id);
CREATE INDEX idx_violations_rule ON validation_violations(rule_id);
CREATE INDEX idx_violations_severity ON validation_violations(severity);
```

### SQLite Indexes
```sql
-- Performance indexes
CREATE INDEX idx_regulations_jurisdiction ON regulations(jurisdiction_id);
CREATE INDEX idx_regulations_category ON regulations(category_id);
CREATE INDEX idx_regulations_type ON regulations(regulation_type);
CREATE INDEX idx_regulations_active ON regulations(active);
CREATE INDEX idx_regulations_effective ON regulations(effective_dt);

CREATE INDEX idx_validation_rules_regulation ON validation_rules(regulation_id);
CREATE INDEX idx_validation_rules_type ON validation_rules(rule_type);
CREATE INDEX idx_validation_rules_active ON validation_rules(active);

CREATE INDEX idx_building_validations_building ON building_validations(building_id);
CREATE INDEX idx_building_validations_regulation ON building_validations(regulation_id);
CREATE INDEX idx_building_validations_status ON building_validations(validation_status);

CREATE INDEX idx_violations_validation ON validation_violations(building_validation_id);
CREATE INDEX idx_violations_rule ON validation_violations(rule_id);
CREATE INDEX idx_violations_severity ON validation_violations(severity);
```

## 📊 Sample Data

### Jurisdictions
```sql
INSERT INTO jurisdictions (name, country, state, city, code, description) VALUES
('United States - International Building Code', 'USA', NULL, NULL, 'IBC', 'International Building Code'),
('United States - NFPA 101', 'USA', NULL, NULL, 'NFPA101', 'Life Safety Code'),
('United States - ADA Standards', 'USA', NULL, NULL, 'ADA', 'Americans with Disabilities Act'),
('United States - ASHRAE 90.1', 'USA', NULL, NULL, 'ASHRAE90.1', 'Energy Standard for Buildings'),
('Canada - National Building Code', 'Canada', NULL, NULL, 'NBC', 'National Building Code of Canada'),
('United Kingdom - Building Regulations', 'UK', NULL, NULL, 'UKBR', 'Building Regulations England and Wales');
```

### Categories
```sql
INSERT INTO categories (name, description, code) VALUES
('Structural', 'Structural integrity and load-bearing requirements', 'STRUCTURAL'),
('Fire Safety', 'Fire protection, egress, and life safety requirements', 'FIRE_SAFETY'),
('Accessibility', 'Accessibility and universal design requirements', 'ACCESSIBILITY'),
('Energy Efficiency', 'Energy conservation and efficiency requirements', 'ENERGY'),
('Mechanical', 'HVAC and mechanical system requirements', 'MECHANICAL'),
('Electrical', 'Electrical system and safety requirements', 'ELECTRICAL'),
('Plumbing', 'Plumbing and water system requirements', 'PLUMBING'),
('Environmental', 'Environmental and sustainability requirements', 'ENVIRONMENTAL');

-- Subcategories
INSERT INTO categories (name, description, parent_id, code) VALUES
('Load Bearing', 'Load-bearing wall and structural element requirements', 1, 'LOAD_BEARING'),
('Foundation', 'Foundation and soil requirements', 1, 'FOUNDATION'),
('Fire Resistance', 'Fire resistance ratings and materials', 2, 'FIRE_RESISTANCE'),
('Egress', 'Means of egress and exit requirements', 2, 'EGRESS'),
('Wheelchair Access', 'Wheelchair accessibility requirements', 3, 'WHEELCHAIR_ACCESS'),
('Energy Conservation', 'Energy conservation measures', 4, 'ENERGY_CONSERVATION');
```

### Sample Regulations
```sql
INSERT INTO regulations (code, title, description, category_id, jurisdiction_id, regulation_type, effective_dt) VALUES
('IBC-1607.1', 'Live Loads', 'Minimum uniformly distributed live loads and concentrated live loads', 1, 1, 'structural', '2021-01-01'),
('IBC-1003.3.1', 'Ceiling Height', 'Minimum ceiling height requirements for habitable spaces', 3, 1, 'accessibility', '2021-01-01'),
('IBC-1006.2.1', 'Number of Exits', 'Minimum number of exits required based on occupant load', 2, 1, 'fire', '2021-01-01'),
('ADA-403.5.1', 'Clear Width', 'Minimum clear width for accessible routes', 5, 3, 'accessibility', '2010-03-15'),
('ASHRAE-9.4.1.1', 'Building Envelope', 'Building envelope requirements for energy efficiency', 6, 4, 'energy', '2019-01-01');
```

## 🔍 Query Examples

### Get Active Regulations by Category
```sql
SELECT r.code, r.title, c.name as category, j.name as jurisdiction
FROM regulations r
JOIN categories c ON r.category_id = c.id
JOIN jurisdictions j ON r.jurisdiction_id = j.id
WHERE r.active = 1 AND c.active = 1 AND j.active = 1
ORDER BY c.name, r.code;
```

### Get Validation Rules for a Regulation
```sql
SELECT vr.rule_name, vr.rule_type, vr.severity, vr.description
FROM validation_rules vr
WHERE vr.regulation_id = ? AND vr.active = 1
ORDER BY vr.priority DESC, vr.severity;
```

### Get Building Validation Results
```sql
SELECT r.code, r.title, bv.validation_status, bv.compliance_score,
       bv.passed_rules, bv.failed_rules, bv.warnings
FROM building_validations bv
JOIN regulations r ON bv.regulation_id = r.id
WHERE bv.building_id = ?
ORDER BY bv.validated_dt DESC;
```

## 🚀 Implementation Notes

### PostgreSQL/PostGIS Features
- Use JSONB for complex data (conditions, actions, details)
- Leverage PostGIS for spatial queries if needed
- Use triggers for automatic timestamp updates
- Consider partitioning for large datasets

### SQLite Features
- Use JSON functions for complex data (SQLite 3.38+)
- Implement triggers for automatic timestamp updates
- Use WAL mode for better concurrency
- Consider database optimization for large datasets

### Migration Strategy
1. Start with SQLite for development and testing
2. Use schema migration tools for PostgreSQL deployment
3. Implement data migration scripts for production
4. Use connection pooling for production PostgreSQL

---

**Schema Version**: 1.0
**Last Updated**: 2024-01-XX
**Compatibility**: PostgreSQL 12+, SQLite 3.35+ 