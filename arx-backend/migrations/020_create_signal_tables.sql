-- Migration: Create Signal Propagation Tables
-- Description: Creates tables for signal propagation analysis, antenna analysis, interference analysis, and signal projects

-- Create signal_projects table
CREATE TABLE IF NOT EXISTS signal_projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    status VARCHAR(50) DEFAULT 'active',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_signal_projects_user_id FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Create index on signal_projects
CREATE INDEX IF NOT EXISTS idx_signal_projects_user_id ON signal_projects(user_id);
CREATE INDEX IF NOT EXISTS idx_signal_projects_status ON signal_projects(status);
CREATE INDEX IF NOT EXISTS idx_signal_projects_created_at ON signal_projects(created_at);

-- Create signal_analyses table
CREATE TABLE IF NOT EXISTS signal_analyses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    project_id UUID,
    request_data JSONB NOT NULL,
    result_data JSONB,
    status VARCHAR(50) DEFAULT 'pending',
    analysis_type VARCHAR(100) NOT NULL,
    propagation_model VARCHAR(100),
    environment_type VARCHAR(100),
    frequency DOUBLE PRECISION,
    power DOUBLE PRECISION,
    distance DOUBLE PRECISION,
    path_loss DOUBLE PRECISION,
    received_power DOUBLE PRECISION,
    signal_strength DOUBLE PRECISION,
    snr DOUBLE PRECISION,
    interference_level DOUBLE PRECISION,
    analysis_time DOUBLE PRECISION,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE,
    error TEXT,
    CONSTRAINT fk_signal_analyses_user_id FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_signal_analyses_project_id FOREIGN KEY (project_id) REFERENCES signal_projects(id) ON DELETE SET NULL
);

-- Create indexes on signal_analyses
CREATE INDEX IF NOT EXISTS idx_signal_analyses_user_id ON signal_analyses(user_id);
CREATE INDEX IF NOT EXISTS idx_signal_analyses_project_id ON signal_analyses(project_id);
CREATE INDEX IF NOT EXISTS idx_signal_analyses_status ON signal_analyses(status);
CREATE INDEX IF NOT EXISTS idx_signal_analyses_analysis_type ON signal_analyses(analysis_type);
CREATE INDEX IF NOT EXISTS idx_signal_analyses_propagation_model ON signal_analyses(propagation_model);
CREATE INDEX IF NOT EXISTS idx_signal_analyses_created_at ON signal_analyses(created_at);
CREATE INDEX IF NOT EXISTS idx_signal_analyses_frequency ON signal_analyses(frequency);

-- Create antenna_analyses table
CREATE TABLE IF NOT EXISTS antenna_analyses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    project_id UUID,
    request_data JSONB NOT NULL,
    result_data JSONB,
    status VARCHAR(50) DEFAULT 'pending',
    analysis_type VARCHAR(100) NOT NULL,
    antenna_type VARCHAR(100) NOT NULL,
    frequency DOUBLE PRECISION NOT NULL,
    max_gain DOUBLE PRECISION,
    directivity DOUBLE PRECISION,
    efficiency DOUBLE PRECISION,
    bandwidth DOUBLE PRECISION,
    vswr DOUBLE PRECISION,
    beamwidth_h DOUBLE PRECISION,
    beamwidth_v DOUBLE PRECISION,
    front_to_back_ratio DOUBLE PRECISION,
    side_lobe_level DOUBLE PRECISION,
    analysis_time DOUBLE PRECISION,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE,
    error TEXT,
    CONSTRAINT fk_antenna_analyses_user_id FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_antenna_analyses_project_id FOREIGN KEY (project_id) REFERENCES signal_projects(id) ON DELETE SET NULL
);

-- Create indexes on antenna_analyses
CREATE INDEX IF NOT EXISTS idx_antenna_analyses_user_id ON antenna_analyses(user_id);
CREATE INDEX IF NOT EXISTS idx_antenna_analyses_project_id ON antenna_analyses(project_id);
CREATE INDEX IF NOT EXISTS idx_antenna_analyses_status ON antenna_analyses(status);
CREATE INDEX IF NOT EXISTS idx_antenna_analyses_analysis_type ON antenna_analyses(analysis_type);
CREATE INDEX IF NOT EXISTS idx_antenna_analyses_antenna_type ON antenna_analyses(antenna_type);
CREATE INDEX IF NOT EXISTS idx_antenna_analyses_created_at ON antenna_analyses(created_at);
CREATE INDEX IF NOT EXISTS idx_antenna_analyses_frequency ON antenna_analyses(frequency);

-- Create interference_analyses table
CREATE TABLE IF NOT EXISTS interference_analyses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    project_id UUID,
    request_data JSONB NOT NULL,
    result_data JSONB,
    status VARCHAR(50) DEFAULT 'pending',
    analysis_type VARCHAR(100) NOT NULL,
    interference_type VARCHAR(100),
    severity VARCHAR(50),
    interference_level DOUBLE PRECISION,
    signal_to_interference_ratio DOUBLE PRECISION,
    carrier_to_interference_ratio DOUBLE PRECISION,
    interference_power DOUBLE PRECISION,
    analysis_time DOUBLE PRECISION,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE,
    error TEXT,
    CONSTRAINT fk_interference_analyses_user_id FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_interference_analyses_project_id FOREIGN KEY (project_id) REFERENCES signal_projects(id) ON DELETE SET NULL
);

-- Create indexes on interference_analyses
CREATE INDEX IF NOT EXISTS idx_interference_analyses_user_id ON interference_analyses(user_id);
CREATE INDEX IF NOT EXISTS idx_interference_analyses_project_id ON interference_analyses(project_id);
CREATE INDEX IF NOT EXISTS idx_interference_analyses_status ON interference_analyses(status);
CREATE INDEX IF NOT EXISTS idx_interference_analyses_analysis_type ON interference_analyses(analysis_type);
CREATE INDEX IF NOT EXISTS idx_interference_analyses_interference_type ON interference_analyses(interference_type);
CREATE INDEX IF NOT EXISTS idx_interference_analyses_severity ON interference_analyses(severity);
CREATE INDEX IF NOT EXISTS idx_interference_analyses_created_at ON interference_analyses(created_at);

-- Create signal_analysis_results table for detailed results
CREATE TABLE IF NOT EXISTS signal_analysis_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    analysis_id UUID NOT NULL,
    result_type VARCHAR(100) NOT NULL,
    result_data JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_signal_analysis_results_analysis_id FOREIGN KEY (analysis_id) REFERENCES signal_analyses(id) ON DELETE CASCADE
);

-- Create indexes on signal_analysis_results
CREATE INDEX IF NOT EXISTS idx_signal_analysis_results_analysis_id ON signal_analysis_results(analysis_id);
CREATE INDEX IF NOT EXISTS idx_signal_analysis_results_result_type ON signal_analysis_results(result_type);

-- Create antenna_analysis_results table for detailed results
CREATE TABLE IF NOT EXISTS antenna_analysis_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    analysis_id UUID NOT NULL,
    result_type VARCHAR(100) NOT NULL,
    result_data JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_antenna_analysis_results_analysis_id FOREIGN KEY (analysis_id) REFERENCES antenna_analyses(id) ON DELETE CASCADE
);

-- Create indexes on antenna_analysis_results
CREATE INDEX IF NOT EXISTS idx_antenna_analysis_results_analysis_id ON antenna_analysis_results(analysis_id);
CREATE INDEX IF NOT EXISTS idx_antenna_analysis_results_result_type ON antenna_analysis_results(result_type);

-- Create interference_analysis_results table for detailed results
CREATE TABLE IF NOT EXISTS interference_analysis_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    analysis_id UUID NOT NULL,
    result_type VARCHAR(100) NOT NULL,
    result_data JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_interference_analysis_results_analysis_id FOREIGN KEY (analysis_id) REFERENCES interference_analyses(id) ON DELETE CASCADE
);

-- Create indexes on interference_analysis_results
CREATE INDEX IF NOT EXISTS idx_interference_analysis_results_analysis_id ON interference_analysis_results(analysis_id);
CREATE INDEX IF NOT EXISTS idx_interference_analysis_results_result_type ON interference_analysis_results(result_type);

-- Create signal_analysis_logs table for audit trail
CREATE TABLE IF NOT EXISTS signal_analysis_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    analysis_id UUID NOT NULL,
    analysis_type VARCHAR(100) NOT NULL,
    user_id UUID NOT NULL,
    action VARCHAR(100) NOT NULL,
    details JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_signal_analysis_logs_user_id FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Create indexes on signal_analysis_logs
CREATE INDEX IF NOT EXISTS idx_signal_analysis_logs_analysis_id ON signal_analysis_logs(analysis_id);
CREATE INDEX IF NOT EXISTS idx_signal_analysis_logs_analysis_type ON signal_analysis_logs(analysis_type);
CREATE INDEX IF NOT EXISTS idx_signal_analysis_logs_user_id ON signal_analysis_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_signal_analysis_logs_action ON signal_analysis_logs(action);
CREATE INDEX IF NOT EXISTS idx_signal_analysis_logs_created_at ON signal_analysis_logs(created_at);

-- Create signal_analysis_performance table for performance metrics
CREATE TABLE IF NOT EXISTS signal_analysis_performance (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    analysis_id UUID NOT NULL,
    analysis_type VARCHAR(100) NOT NULL,
    execution_time DOUBLE PRECISION NOT NULL,
    memory_usage DOUBLE PRECISION,
    cpu_usage DOUBLE PRECISION,
    cache_hit BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes on signal_analysis_performance
CREATE INDEX IF NOT EXISTS idx_signal_analysis_performance_analysis_id ON signal_analysis_performance(analysis_id);
CREATE INDEX IF NOT EXISTS idx_signal_analysis_performance_analysis_type ON signal_analysis_performance(analysis_type);
CREATE INDEX IF NOT EXISTS idx_signal_analysis_performance_execution_time ON signal_analysis_performance(execution_time);
CREATE INDEX IF NOT EXISTS idx_signal_analysis_performance_created_at ON signal_analysis_performance(created_at);

-- Create signal_analysis_cache table for caching results
CREATE TABLE IF NOT EXISTS signal_analysis_cache (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cache_key VARCHAR(255) UNIQUE NOT NULL,
    cache_data JSONB NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    accessed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes on signal_analysis_cache
CREATE INDEX IF NOT EXISTS idx_signal_analysis_cache_cache_key ON signal_analysis_cache(cache_key);
CREATE INDEX IF NOT EXISTS idx_signal_analysis_cache_expires_at ON signal_analysis_cache(expires_at);
CREATE INDEX IF NOT EXISTS idx_signal_analysis_cache_accessed_at ON signal_analysis_cache(accessed_at);

-- Create signal_analysis_templates table for reusable analysis templates
CREATE TABLE IF NOT EXISTS signal_analysis_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    template_type VARCHAR(100) NOT NULL,
    template_data JSONB NOT NULL,
    is_public BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_signal_analysis_templates_user_id FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Create indexes on signal_analysis_templates
CREATE INDEX IF NOT EXISTS idx_signal_analysis_templates_user_id ON signal_analysis_templates(user_id);
CREATE INDEX IF NOT EXISTS idx_signal_analysis_templates_template_type ON signal_analysis_templates(template_type);
CREATE INDEX IF NOT EXISTS idx_signal_analysis_templates_is_public ON signal_analysis_templates(is_public);
CREATE INDEX IF NOT EXISTS idx_signal_analysis_templates_created_at ON signal_analysis_templates(created_at);

-- Create signal_analysis_shares table for sharing analysis results
CREATE TABLE IF NOT EXISTS signal_analysis_shares (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    analysis_id UUID NOT NULL,
    analysis_type VARCHAR(100) NOT NULL,
    shared_by UUID NOT NULL,
    shared_with UUID NOT NULL,
    permissions JSONB DEFAULT '{"read": true, "write": false, "delete": false}',
    expires_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_signal_analysis_shares_shared_by FOREIGN KEY (shared_by) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_signal_analysis_shares_shared_with FOREIGN KEY (shared_with) REFERENCES users(id) ON DELETE CASCADE
);

-- Create indexes on signal_analysis_shares
CREATE INDEX IF NOT EXISTS idx_signal_analysis_shares_analysis_id ON signal_analysis_shares(analysis_id);
CREATE INDEX IF NOT EXISTS idx_signal_analysis_shares_analysis_type ON signal_analysis_shares(analysis_type);
CREATE INDEX IF NOT EXISTS idx_signal_analysis_shares_shared_by ON signal_analysis_shares(shared_by);
CREATE INDEX IF NOT EXISTS idx_signal_analysis_shares_shared_with ON signal_analysis_shares(shared_with);
CREATE INDEX IF NOT EXISTS idx_signal_analysis_shares_expires_at ON signal_analysis_shares(expires_at);

-- Create triggers for updated_at timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for signal_projects
CREATE TRIGGER update_signal_projects_updated_at 
    BEFORE UPDATE ON signal_projects 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Create triggers for signal_analyses
CREATE TRIGGER update_signal_analyses_updated_at 
    BEFORE UPDATE ON signal_analyses 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Create triggers for antenna_analyses
CREATE TRIGGER update_antenna_analyses_updated_at 
    BEFORE UPDATE ON antenna_analyses 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Create triggers for interference_analyses
CREATE TRIGGER update_interference_analyses_updated_at 
    BEFORE UPDATE ON interference_analyses 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Create triggers for signal_analysis_templates
CREATE TRIGGER update_signal_analysis_templates_updated_at 
    BEFORE UPDATE ON signal_analysis_templates 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Create function to clean up expired cache entries
CREATE OR REPLACE FUNCTION cleanup_expired_cache()
RETURNS void AS $$
BEGIN
    DELETE FROM signal_analysis_cache WHERE expires_at < CURRENT_TIMESTAMP;
END;
$$ LANGUAGE plpgsql;

-- Create function to update cache access time
CREATE OR REPLACE FUNCTION update_cache_access_time()
RETURNS TRIGGER AS $$
BEGIN
    NEW.accessed_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for cache access time
CREATE TRIGGER update_signal_analysis_cache_accessed_at 
    BEFORE UPDATE ON signal_analysis_cache 
    FOR EACH ROW EXECUTE FUNCTION update_cache_access_time();

-- Insert initial data for signal analysis types
INSERT INTO signal_analysis_templates (id, user_id, name, description, template_type, template_data, is_public) VALUES
(
    gen_random_uuid(),
    (SELECT id FROM users LIMIT 1),
    'Basic Signal Propagation',
    'Basic signal propagation analysis with free space model',
    'signal_propagation',
    '{"propagation_model": "free_space", "environment_type": "urban", "frequency": 2.4e9, "power": 20}',
    true
),
(
    gen_random_uuid(),
    (SELECT id FROM users LIMIT 1),
    'Dipole Antenna Analysis',
    'Basic dipole antenna analysis',
    'antenna_analysis',
    '{"antenna_type": "dipole", "frequency": 2.4e9, "length": 0.0625}',
    true
),
(
    gen_random_uuid(),
    (SELECT id FROM users LIMIT 1),
    'Co-channel Interference Analysis',
    'Basic co-channel interference analysis',
    'interference_analysis',
    '{"interference_type": "co_channel", "severity": "moderate"}',
    true
);

-- Create views for common queries
CREATE OR REPLACE VIEW signal_analysis_summary AS
SELECT 
    sa.id,
    sa.user_id,
    sa.project_id,
    sp.name as project_name,
    sa.analysis_type,
    sa.propagation_model,
    sa.environment_type,
    sa.frequency,
    sa.power,
    sa.path_loss,
    sa.received_power,
    sa.signal_strength,
    sa.snr,
    sa.status,
    sa.created_at,
    sa.completed_at,
    sa.analysis_time
FROM signal_analyses sa
LEFT JOIN signal_projects sp ON sa.project_id = sp.id;

CREATE OR REPLACE VIEW antenna_analysis_summary AS
SELECT 
    aa.id,
    aa.user_id,
    aa.project_id,
    sp.name as project_name,
    aa.analysis_type,
    aa.antenna_type,
    aa.frequency,
    aa.max_gain,
    aa.directivity,
    aa.efficiency,
    aa.bandwidth,
    aa.vswr,
    aa.status,
    aa.created_at,
    aa.completed_at,
    aa.analysis_time
FROM antenna_analyses aa
LEFT JOIN signal_projects sp ON aa.project_id = sp.id;

CREATE OR REPLACE VIEW interference_analysis_summary AS
SELECT 
    ia.id,
    ia.user_id,
    ia.project_id,
    sp.name as project_name,
    ia.analysis_type,
    ia.interference_type,
    ia.severity,
    ia.interference_level,
    ia.signal_to_interference_ratio,
    ia.carrier_to_interference_ratio,
    ia.status,
    ia.created_at,
    ia.completed_at,
    ia.analysis_time
FROM interference_analyses ia
LEFT JOIN signal_projects sp ON ia.project_id = sp.id;

-- Create view for performance metrics
CREATE OR REPLACE VIEW signal_analysis_performance_summary AS
SELECT 
    sap.analysis_type,
    COUNT(*) as total_analyses,
    AVG(sap.execution_time) as avg_execution_time,
    MAX(sap.execution_time) as max_execution_time,
    MIN(sap.execution_time) as min_execution_time,
    AVG(sap.memory_usage) as avg_memory_usage,
    AVG(sap.cpu_usage) as avg_cpu_usage,
    COUNT(CASE WHEN sap.cache_hit THEN 1 END) as cache_hits,
    COUNT(CASE WHEN NOT sap.cache_hit THEN 1 END) as cache_misses
FROM signal_analysis_performance sap
GROUP BY sap.analysis_type;

-- Grant permissions
GRANT SELECT, INSERT, UPDATE, DELETE ON signal_projects TO arxos_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON signal_analyses TO arxos_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON antenna_analyses TO arxos_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON interference_analyses TO arxos_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON signal_analysis_results TO arxos_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON antenna_analysis_results TO arxos_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON interference_analysis_results TO arxos_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON signal_analysis_logs TO arxos_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON signal_analysis_performance TO arxos_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON signal_analysis_cache TO arxos_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON signal_analysis_templates TO arxos_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON signal_analysis_shares TO arxos_user;

GRANT SELECT ON signal_analysis_summary TO arxos_user;
GRANT SELECT ON antenna_analysis_summary TO arxos_user;
GRANT SELECT ON interference_analysis_summary TO arxos_user;
GRANT SELECT ON signal_analysis_performance_summary TO arxos_user;

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_signal_analyses_request_data_gin ON signal_analyses USING GIN (request_data);
CREATE INDEX IF NOT EXISTS idx_signal_analyses_result_data_gin ON signal_analyses USING GIN (result_data);
CREATE INDEX IF NOT EXISTS idx_antenna_analyses_request_data_gin ON antenna_analyses USING GIN (request_data);
CREATE INDEX IF NOT EXISTS idx_antenna_analyses_result_data_gin ON antenna_analyses USING GIN (result_data);
CREATE INDEX IF NOT EXISTS idx_interference_analyses_request_data_gin ON interference_analyses USING GIN (request_data);
CREATE INDEX IF NOT EXISTS idx_interference_analyses_result_data_gin ON interference_analyses USING GIN (result_data);
CREATE INDEX IF NOT EXISTS idx_signal_analysis_cache_cache_data_gin ON signal_analysis_cache USING GIN (cache_data);
CREATE INDEX IF NOT EXISTS idx_signal_analysis_templates_template_data_gin ON signal_analysis_templates USING GIN (template_data); 