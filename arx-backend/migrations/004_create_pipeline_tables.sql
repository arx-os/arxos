-- Migration: Create Pipeline Tables
-- Description: Creates tables for tracking pipeline executions and steps
-- Created: 2024-12-19

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Pipeline Executions Table
CREATE TABLE pipeline_executions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    system VARCHAR(100) NOT NULL,
    object_type VARCHAR(100),
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    error_message TEXT,
    metadata JSONB DEFAULT '{}',
    created_by VARCHAR(100),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Pipeline Steps Table
CREATE TABLE pipeline_steps (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    execution_id UUID NOT NULL REFERENCES pipeline_executions(id) ON DELETE CASCADE,
    step_name VARCHAR(100) NOT NULL,
    step_order INTEGER NOT NULL,
    orchestrator VARCHAR(20) NOT NULL CHECK (orchestrator IN ('go', 'python', 'hybrid')),
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    error_message TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Pipeline Configurations Table
CREATE TABLE pipeline_configurations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    system VARCHAR(100) NOT NULL,
    config_name VARCHAR(100) NOT NULL,
    config_type VARCHAR(50) NOT NULL CHECK (config_type IN ('schema', 'symbol', 'behavior', 'compliance')),
    config_data JSONB NOT NULL,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by VARCHAR(100),
    UNIQUE(system, config_name, config_type)
);

-- Pipeline Quality Gates Table
CREATE TABLE pipeline_quality_gates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    gate_name VARCHAR(100) NOT NULL,
    gate_type VARCHAR(50) NOT NULL CHECK (gate_type IN ('validation', 'security', 'performance', 'compliance')),
    gate_config JSONB NOT NULL,
    is_required BOOLEAN DEFAULT true,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Pipeline Audit Log Table
CREATE TABLE pipeline_audit_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    execution_id UUID REFERENCES pipeline_executions(id) ON DELETE CASCADE,
    step_id UUID REFERENCES pipeline_steps(id) ON DELETE CASCADE,
    action VARCHAR(100) NOT NULL,
    action_type VARCHAR(50) NOT NULL CHECK (action_type IN ('create', 'update', 'delete', 'validate', 'execute', 'rollback')),
    details JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by VARCHAR(100)
);

-- Indexes for performance
CREATE INDEX idx_pipeline_executions_system ON pipeline_executions(system);
CREATE INDEX idx_pipeline_executions_status ON pipeline_executions(status);
CREATE INDEX idx_pipeline_executions_created_at ON pipeline_executions(created_at);
CREATE INDEX idx_pipeline_steps_execution_id ON pipeline_steps(execution_id);
CREATE INDEX idx_pipeline_steps_status ON pipeline_steps(status);
CREATE INDEX idx_pipeline_configurations_system ON pipeline_configurations(system);
CREATE INDEX idx_pipeline_configurations_active ON pipeline_configurations(is_active);
CREATE INDEX idx_pipeline_audit_log_execution_id ON pipeline_audit_log(execution_id);
CREATE INDEX idx_pipeline_audit_log_created_at ON pipeline_audit_log(created_at);

-- Triggers for updated_at timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_pipeline_executions_updated_at 
    BEFORE UPDATE ON pipeline_executions 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_pipeline_steps_updated_at 
    BEFORE UPDATE ON pipeline_steps 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_pipeline_configurations_updated_at 
    BEFORE UPDATE ON pipeline_configurations 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_pipeline_quality_gates_updated_at 
    BEFORE UPDATE ON pipeline_quality_gates 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert default quality gates
INSERT INTO pipeline_quality_gates (gate_name, gate_type, gate_config, is_required) VALUES
('schema_validation', 'validation', '{"required_fields": ["system", "objects"], "max_file_size": 1048576}', true),
('symbol_validation', 'validation', '{"required_fields": ["id", "name", "system", "svg"], "max_symbols_per_system": 100}', true),
('behavior_validation', 'validation', '{"required_methods": ["validate_object", "simulate_behavior"], "max_complexity": 10}', true),
('security_scan', 'security', '{"tools": ["bandit", "safety"], "max_vulnerabilities": 0}', true),
('performance_check', 'performance', '{"max_execution_time": 300, "max_memory_usage": 512}', false),
('compliance_check', 'compliance', '{"standards": ["OWASP", "SOC2"], "required_checks": ["input_validation", "error_handling"]}', true);

-- Insert default pipeline configurations for common systems
INSERT INTO pipeline_configurations (system, config_name, config_type, config_data, created_by) VALUES
('electrical', 'default_schema', 'schema', '{"system": "electrical", "objects": {"panel": {"properties": {}, "relationships": {}, "behavior_profile": "electrical_panel"}}}', 'system'),
('mechanical', 'default_schema', 'schema', '{"system": "mechanical", "objects": {"hvac": {"properties": {}, "relationships": {}, "behavior_profile": "hvac_system"}}}', 'system'),
('plumbing', 'default_schema', 'schema', '{"system": "plumbing", "objects": {"pump": {"properties": {}, "relationships": {}, "behavior_profile": "plumbing_pump"}}}', 'system'),
('fire_alarm', 'default_schema', 'schema', '{"system": "fire_alarm", "objects": {"detector": {"properties": {}, "relationships": {}, "behavior_profile": "fire_detector"}}}', 'system');

-- Create view for pipeline execution summary
CREATE VIEW pipeline_execution_summary AS
SELECT 
    pe.id,
    pe.system,
    pe.object_type,
    pe.status,
    pe.created_at,
    pe.completed_at,
    pe.error_message,
    COUNT(ps.id) as total_steps,
    COUNT(CASE WHEN ps.status = 'completed' THEN 1 END) as completed_steps,
    COUNT(CASE WHEN ps.status = 'failed' THEN 1 END) as failed_steps,
    AVG(EXTRACT(EPOCH FROM (ps.completed_at - ps.started_at))) as avg_step_duration
FROM pipeline_executions pe
LEFT JOIN pipeline_steps ps ON pe.id = ps.execution_id
GROUP BY pe.id, pe.system, pe.object_type, pe.status, pe.created_at, pe.completed_at, pe.error_message;

-- Create view for pipeline quality metrics
CREATE VIEW pipeline_quality_metrics AS
SELECT 
    pe.system,
    COUNT(pe.id) as total_executions,
    COUNT(CASE WHEN pe.status = 'completed' THEN 1 END) as successful_executions,
    COUNT(CASE WHEN pe.status = 'failed' THEN 1 END) as failed_executions,
    AVG(EXTRACT(EPOCH FROM (pe.completed_at - pe.started_at))) as avg_execution_time,
    MAX(pe.created_at) as last_execution
FROM pipeline_executions pe
GROUP BY pe.system; 