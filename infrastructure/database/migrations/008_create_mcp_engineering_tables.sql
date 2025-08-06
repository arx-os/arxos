-- Migration: Create MCP-Engineering Tables
-- Description: Creates all database tables for MCP-Engineering functionality
-- Date: 2024-01-XX
-- Author: MCP-Engineering Integration Team

-- Create enum types for MCP-Engineering
CREATE TYPE issue_severity AS ENUM ('critical', 'high', 'medium', 'low', 'info');
CREATE TYPE suggestion_type AS ENUM ('optimization', 'compliance', 'safety', 'efficiency', 'cost_saving');
CREATE TYPE validation_type AS ENUM ('structural', 'electrical', 'mechanical', 'plumbing', 'fire', 'accessibility', 'energy');
CREATE TYPE validation_status AS ENUM ('pass', 'fail', 'warning', 'pending', 'error');
CREATE TYPE report_type AS ENUM ('comprehensive', 'summary', 'technical');
CREATE TYPE report_format AS ENUM ('pdf', 'html', 'json');

-- Create MCP Building Data table
CREATE TABLE mcp_building_data (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    area FLOAT NOT NULL,
    height FLOAT NOT NULL,
    building_type VARCHAR(100) NOT NULL,
    occupancy VARCHAR(100),
    floors INTEGER,
    jurisdiction VARCHAR(100),
    address TEXT,
    construction_type VARCHAR(100),
    year_built INTEGER,
    renovation_year INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create MCP Validation Sessions table
CREATE TABLE mcp_validation_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(100) NOT NULL,
    validation_type validation_type NOT NULL,
    project_id VARCHAR(100),
    status validation_status DEFAULT 'pending',
    include_suggestions BOOLEAN DEFAULT TRUE,
    confidence_threshold FLOAT DEFAULT 0.7,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    processing_time FLOAT,
    building_data_id UUID NOT NULL REFERENCES mcp_building_data(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create MCP Validation Results table
CREATE TABLE mcp_validation_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    validation_type validation_type NOT NULL,
    status validation_status NOT NULL,
    confidence_score FLOAT DEFAULT 0.0,
    processing_time FLOAT DEFAULT 0.0,
    model_version VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    building_data_id UUID NOT NULL REFERENCES mcp_building_data(id) ON DELETE CASCADE,
    validation_session_id UUID REFERENCES mcp_validation_sessions(id) ON DELETE SET NULL
);

-- Create MCP Compliance Issues table
CREATE TABLE mcp_compliance_issues (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code_reference VARCHAR(200) NOT NULL,
    severity issue_severity NOT NULL,
    description TEXT NOT NULL,
    resolution TEXT NOT NULL,
    affected_systems JSONB,
    estimated_cost FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    validation_result_id UUID REFERENCES mcp_validation_results(id) ON DELETE CASCADE
);

-- Create MCP AI Recommendations table
CREATE TABLE mcp_ai_recommendations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    type suggestion_type NOT NULL,
    description TEXT NOT NULL,
    confidence FLOAT NOT NULL,
    impact_score FLOAT NOT NULL,
    implementation_cost FLOAT,
    estimated_savings FLOAT,
    affected_systems JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    validation_result_id UUID REFERENCES mcp_validation_results(id) ON DELETE CASCADE
);

-- Create MCP Knowledge Search Results table
CREATE TABLE mcp_knowledge_search_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code_reference VARCHAR(200) NOT NULL,
    title VARCHAR(500) NOT NULL,
    content TEXT NOT NULL,
    code_standard VARCHAR(100) NOT NULL,
    relevance_score FLOAT NOT NULL,
    section_number VARCHAR(50),
    subsection VARCHAR(100),
    jurisdiction VARCHAR(100),
    effective_date TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create MCP ML Predictions table
CREATE TABLE mcp_ml_predictions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    prediction_type VARCHAR(100) NOT NULL,
    prediction_value VARCHAR(500) NOT NULL,
    confidence FLOAT NOT NULL,
    model_version VARCHAR(100) NOT NULL,
    model_name VARCHAR(100) NOT NULL,
    features JSONB,
    processing_time FLOAT DEFAULT 0.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create MCP Compliance Reports table
CREATE TABLE mcp_compliance_reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    report_type report_type NOT NULL,
    format report_format NOT NULL,
    user_id VARCHAR(100) NOT NULL,
    project_id VARCHAR(100),
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    download_url TEXT,
    file_size INTEGER,
    checksum VARCHAR(64),
    building_data_id UUID NOT NULL REFERENCES mcp_building_data(id) ON DELETE CASCADE
);

-- Create association table for reports and validation results
CREATE TABLE mcp_report_validation_results (
    report_id UUID REFERENCES mcp_compliance_reports(id) ON DELETE CASCADE,
    validation_result_id UUID REFERENCES mcp_validation_results(id) ON DELETE CASCADE,
    PRIMARY KEY (report_id, validation_result_id)
);

-- Create MCP Validation Statistics table
CREATE TABLE mcp_validation_statistics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    total_validations INTEGER DEFAULT 0,
    successful_validations INTEGER DEFAULT 0,
    failed_validations INTEGER DEFAULT 0,
    average_processing_time FLOAT DEFAULT 0.0,
    total_processing_time FLOAT DEFAULT 0.0,
    average_confidence_score FLOAT DEFAULT 0.0,
    total_issues_found INTEGER DEFAULT 0,
    total_suggestions_generated INTEGER DEFAULT 0,
    most_common_validation_type VARCHAR(100),
    last_validation_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX idx_mcp_building_data_building_type ON mcp_building_data(building_type);
CREATE INDEX idx_mcp_building_data_jurisdiction ON mcp_building_data(jurisdiction);
CREATE INDEX idx_mcp_validation_sessions_user_id ON mcp_validation_sessions(user_id);
CREATE INDEX idx_mcp_validation_sessions_status ON mcp_validation_sessions(status);
CREATE INDEX idx_mcp_validation_sessions_validation_type ON mcp_validation_sessions(validation_type);
CREATE INDEX idx_mcp_validation_results_status ON mcp_validation_results(status);
CREATE INDEX idx_mcp_validation_results_validation_type ON mcp_validation_results(validation_type);
CREATE INDEX idx_mcp_validation_results_created_at ON mcp_validation_results(created_at);
CREATE INDEX idx_mcp_compliance_issues_severity ON mcp_compliance_issues(severity);
CREATE INDEX idx_mcp_compliance_issues_code_reference ON mcp_compliance_issues(code_reference);
CREATE INDEX idx_mcp_ai_recommendations_type ON mcp_ai_recommendations(type);
CREATE INDEX idx_mcp_ai_recommendations_confidence ON mcp_ai_recommendations(confidence);
CREATE INDEX idx_mcp_knowledge_search_results_code_reference ON mcp_knowledge_search_results(code_reference);
CREATE INDEX idx_mcp_knowledge_search_results_relevance_score ON mcp_knowledge_search_results(relevance_score);
CREATE INDEX idx_mcp_ml_predictions_prediction_type ON mcp_ml_predictions(prediction_type);
CREATE INDEX idx_mcp_ml_predictions_model_name ON mcp_ml_predictions(model_name);
CREATE INDEX idx_mcp_compliance_reports_user_id ON mcp_compliance_reports(user_id);
CREATE INDEX idx_mcp_compliance_reports_report_type ON mcp_compliance_reports(report_type);
CREATE INDEX idx_mcp_compliance_reports_generated_at ON mcp_compliance_reports(generated_at);

-- Create composite indexes for common query patterns
CREATE INDEX idx_mcp_validation_sessions_user_status ON mcp_validation_sessions(user_id, status);
CREATE INDEX idx_mcp_validation_results_building_status ON mcp_validation_results(building_data_id, status);
CREATE INDEX idx_mcp_compliance_issues_result_severity ON mcp_compliance_issues(validation_result_id, severity);

-- Create GIN indexes for JSONB columns
CREATE INDEX idx_mcp_compliance_issues_affected_systems ON mcp_compliance_issues USING GIN (affected_systems);
CREATE INDEX idx_mcp_ai_recommendations_affected_systems ON mcp_ai_recommendations USING GIN (affected_systems);
CREATE INDEX idx_mcp_ml_predictions_features ON mcp_ml_predictions USING GIN (features);

-- Add constraints
ALTER TABLE mcp_building_data ADD CONSTRAINT chk_area_positive CHECK (area > 0);
ALTER TABLE mcp_building_data ADD CONSTRAINT chk_height_positive CHECK (height > 0);
ALTER TABLE mcp_building_data ADD CONSTRAINT chk_floors_positive CHECK (floors IS NULL OR floors > 0);
ALTER TABLE mcp_validation_sessions ADD CONSTRAINT chk_confidence_threshold CHECK (confidence_threshold >= 0 AND confidence_threshold <= 1);
ALTER TABLE mcp_validation_results ADD CONSTRAINT chk_confidence_score CHECK (confidence_score >= 0 AND confidence_score <= 1);
ALTER TABLE mcp_validation_results ADD CONSTRAINT chk_processing_time CHECK (processing_time >= 0);
ALTER TABLE mcp_compliance_issues ADD CONSTRAINT chk_estimated_cost CHECK (estimated_cost IS NULL OR estimated_cost >= 0);
ALTER TABLE mcp_ai_recommendations ADD CONSTRAINT chk_confidence CHECK (confidence >= 0 AND confidence <= 1);
ALTER TABLE mcp_ai_recommendations ADD CONSTRAINT chk_impact_score CHECK (impact_score >= 0 AND impact_score <= 1);
ALTER TABLE mcp_ai_recommendations ADD CONSTRAINT chk_implementation_cost CHECK (implementation_cost IS NULL OR implementation_cost >= 0);
ALTER TABLE mcp_ai_recommendations ADD CONSTRAINT chk_estimated_savings CHECK (estimated_savings IS NULL OR estimated_savings >= 0);
ALTER TABLE mcp_knowledge_search_results ADD CONSTRAINT chk_relevance_score CHECK (relevance_score >= 0 AND relevance_score <= 1);
ALTER TABLE mcp_ml_predictions ADD CONSTRAINT chk_confidence_ml CHECK (confidence >= 0 AND confidence <= 1);
ALTER TABLE mcp_ml_predictions ADD CONSTRAINT chk_processing_time_ml CHECK (processing_time >= 0);
ALTER TABLE mcp_validation_statistics ADD CONSTRAINT chk_total_validations CHECK (total_validations >= 0);
ALTER TABLE mcp_validation_statistics ADD CONSTRAINT chk_successful_validations CHECK (successful_validations >= 0);
ALTER TABLE mcp_validation_statistics ADD CONSTRAINT chk_failed_validations CHECK (failed_validations >= 0);
ALTER TABLE mcp_validation_statistics ADD CONSTRAINT chk_average_processing_time CHECK (average_processing_time >= 0);
ALTER TABLE mcp_validation_statistics ADD CONSTRAINT chk_total_processing_time CHECK (total_processing_time >= 0);
ALTER TABLE mcp_validation_statistics ADD CONSTRAINT chk_average_confidence_score CHECK (average_confidence_score >= 0 AND average_confidence_score <= 1);
ALTER TABLE mcp_validation_statistics ADD CONSTRAINT chk_total_issues_found CHECK (total_issues_found >= 0);
ALTER TABLE mcp_validation_statistics ADD CONSTRAINT chk_total_suggestions_generated CHECK (total_suggestions_generated >= 0);

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at columns
CREATE TRIGGER update_mcp_building_data_updated_at BEFORE UPDATE ON mcp_building_data FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_mcp_validation_sessions_updated_at BEFORE UPDATE ON mcp_validation_sessions FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_mcp_compliance_issues_updated_at BEFORE UPDATE ON mcp_compliance_issues FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_mcp_ai_recommendations_updated_at BEFORE UPDATE ON mcp_ai_recommendations FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_mcp_validation_statistics_updated_at BEFORE UPDATE ON mcp_validation_statistics FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert initial validation statistics record
INSERT INTO mcp_validation_statistics (id, total_validations, successful_validations, failed_validations)
VALUES (gen_random_uuid(), 0, 0, 0);

-- Add comments to tables
COMMENT ON TABLE mcp_building_data IS 'Stores building data for MCP-Engineering validation operations';
COMMENT ON TABLE mcp_validation_sessions IS 'Tracks validation sessions and their status';
COMMENT ON TABLE mcp_validation_results IS 'Stores validation results with issues and recommendations';
COMMENT ON TABLE mcp_compliance_issues IS 'Stores compliance issues found during validation';
COMMENT ON TABLE mcp_ai_recommendations IS 'Stores AI-generated recommendations for building improvements';
COMMENT ON TABLE mcp_knowledge_search_results IS 'Stores knowledge base search results for code references';
COMMENT ON TABLE mcp_ml_predictions IS 'Stores machine learning predictions for building analysis';
COMMENT ON TABLE mcp_compliance_reports IS 'Stores generated compliance reports';
COMMENT ON TABLE mcp_report_validation_results IS 'Association table linking reports to validation results';
COMMENT ON TABLE mcp_validation_statistics IS 'Stores aggregated validation statistics for analytics';

-- Grant permissions (adjust as needed for your environment)
-- GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO arxos_user;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO arxos_user; 