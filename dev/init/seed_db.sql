-- Arxos Database Initialization Script
-- This script sets up the PostgreSQL database with PostGIS extension
-- and initial tables for the Arxos platform

-- Enable PostGIS extension
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;

-- Create GUS-related tables
CREATE TABLE IF NOT EXISTS gus_sessions (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    session_id VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    conversation_history JSONB DEFAULT '[]',
    context JSONB DEFAULT '{}',
    preferences JSONB DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS gus_knowledge_base (
    id SERIAL PRIMARY KEY,
    topic VARCHAR(255) NOT NULL,
    category VARCHAR(100) NOT NULL,
    title VARCHAR(500) NOT NULL,
    content TEXT NOT NULL,
    source VARCHAR(255),
    citation TEXT,
    relevance_tags TEXT[],
    embedding_vector VECTOR(1536),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS gus_interactions (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(255) NOT NULL,
    user_id VARCHAR(255) NOT NULL,
    query TEXT NOT NULL,
    response TEXT NOT NULL,
    intent VARCHAR(100),
    confidence FLOAT,
    entities JSONB,
    processing_time_ms INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS gus_learning_data (
    id SERIAL PRIMARY KEY,
    interaction_id INTEGER REFERENCES gus_interactions(id),
    user_feedback INTEGER CHECK (user_feedback >= 1 AND user_feedback <= 5),
    feedback_text TEXT,
    model_performance_metrics JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_gus_sessions_user_id ON gus_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_gus_sessions_created_at ON gus_sessions(created_at);
CREATE INDEX IF NOT EXISTS idx_gus_knowledge_topic ON gus_knowledge_base(topic);
CREATE INDEX IF NOT EXISTS idx_gus_knowledge_category ON gus_knowledge_base(category);
CREATE INDEX IF NOT EXISTS idx_gus_knowledge_tags ON gus_knowledge_base USING GIN(relevance_tags);
CREATE INDEX IF NOT EXISTS idx_gus_interactions_session_id ON gus_interactions(session_id);
CREATE INDEX IF NOT EXISTS idx_gus_interactions_created_at ON gus_interactions(created_at);
CREATE INDEX IF NOT EXISTS idx_gus_interactions_intent ON gus_interactions(intent);

-- Insert initial knowledge base data (Tier 1 standards)
INSERT INTO gus_knowledge_base (topic, category, title, content, source, citation, relevance_tags) VALUES
-- IBC 2024
('structural_requirements', 'building_codes', 'IBC 2024 - Structural Requirements',
'International Building Code 2024 structural requirements for buildings including load calculations, material specifications, and safety factors.',
'IBC 2024', 'International Building Code 2024, Chapter 16',
ARRAY['structural', 'building_codes', 'IBC', 'safety', 'loads']),

('architectural_requirements', 'building_codes', 'IBC 2024 - Architectural Requirements',
'International Building Code 2024 architectural requirements including egress, accessibility, and building envelope specifications.',
'IBC 2024', 'International Building Code 2024, Chapter 10',
ARRAY['architectural', 'building_codes', 'IBC', 'egress', 'accessibility']),

-- NEC 2023
('electrical_systems', 'electrical_codes', 'NEC 2023 - Electrical System Requirements',
'National Electrical Code 2023 requirements for electrical systems including wiring, grounding, and safety measures.',
'NEC 2023', 'National Electrical Code 2023, Article 250',
ARRAY['electrical', 'NEC', 'wiring', 'grounding', 'safety']),

('electrical_outlets', 'electrical_codes', 'NEC 2023 - Electrical Outlet Requirements',
'National Electrical Code 2023 requirements for electrical outlets including spacing, types, and installation.',
'NEC 2023', 'National Electrical Code 2023, Article 210',
ARRAY['electrical', 'outlets', 'NEC', 'spacing', 'installation']),

-- ASHRAE 90.1
('hvac_energy', 'hvac_standards', 'ASHRAE 90.1 - HVAC Energy Standards',
'ASHRAE 90.1 energy standards for HVAC systems including efficiency requirements and energy conservation measures.',
'ASHRAE 90.1', 'ASHRAE Standard 90.1-2022, Section 6',
ARRAY['HVAC', 'energy', 'ASHRAE', 'efficiency', 'conservation']),

-- NFPA 101
('life_safety', 'fire_safety', 'NFPA 101 - Life Safety Code',
'NFPA 101 Life Safety Code requirements for multi-floor buildings including egress, fire protection, and emergency systems.',
'NFPA 101', 'NFPA 101 Life Safety Code 2021, Chapter 7',
ARRAY['life_safety', 'fire_safety', 'NFPA', 'egress', 'emergency']),

-- ADA
('accessibility', 'accessibility_standards', 'ADA - Accessibility Requirements',
'Americans with Disabilities Act requirements for building accessibility including ramps, doorways, and facilities.',
'ADA', 'ADA Standards for Accessible Design 2010',
ARRAY['accessibility', 'ADA', 'ramps', 'doorways', 'facilities']);

-- Create spatial tables for CAD data
CREATE TABLE IF NOT EXISTS cad_objects (
    id SERIAL PRIMARY KEY,
    object_id VARCHAR(255) UNIQUE NOT NULL,
    object_type VARCHAR(100) NOT NULL,
    name VARCHAR(255),
    geometry GEOMETRY(POINT, 4326),
    properties JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS cad_constraints (
    id SERIAL PRIMARY KEY,
    constraint_id VARCHAR(255) UNIQUE NOT NULL,
    constraint_type VARCHAR(100) NOT NULL,
    object_ids VARCHAR(255)[] NOT NULL,
    parameters JSONB DEFAULT '{}',
    status VARCHAR(50) DEFAULT 'active',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create spatial indexes
CREATE INDEX IF NOT EXISTS idx_cad_objects_geometry ON cad_objects USING GIST (geometry);
CREATE INDEX IF NOT EXISTS idx_cad_objects_type ON cad_objects(object_type);
CREATE INDEX IF NOT EXISTS idx_cad_constraints_type ON cad_constraints(constraint_type);

-- Create functions for GUS integration
CREATE OR REPLACE FUNCTION update_gus_session_context(
    p_session_id VARCHAR(255),
    p_context JSONB
) RETURNS VOID AS $$
BEGIN
    UPDATE gus_sessions
    SET context = p_context, updated_at = CURRENT_TIMESTAMP
    WHERE session_id = p_session_id;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION get_gus_session_history(
    p_session_id VARCHAR(255)
) RETURNS JSONB AS $$
BEGIN
    RETURN (
        SELECT conversation_history
        FROM gus_sessions
        WHERE session_id = p_session_id
    );
END;
$$ LANGUAGE plpgsql;

-- Grant permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO arxos_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO arxos_user;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO arxos_user;
