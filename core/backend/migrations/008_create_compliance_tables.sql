-- Migration: Create Compliance and Data Retention Tables
-- Date: 2024-01-XX
-- Description: Add tables for compliance reporting and data retention policies

-- Data Retention Policies table
CREATE TABLE IF NOT EXISTS data_retention_policies (
    id BIGSERIAL PRIMARY KEY,
    object_type VARCHAR(255) NOT NULL,
    retention_period INTEGER NOT NULL, -- in days
    archive_after INTEGER NOT NULL,    -- in days
    delete_after INTEGER NOT NULL,     -- in days
    is_active BOOLEAN DEFAULT true,
    description TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    
    INDEX idx_data_retention_policies_object_type (object_type),
    INDEX idx_data_retention_policies_is_active (is_active)
);

-- Insert default retention policies
INSERT INTO data_retention_policies (object_type, retention_period, archive_after, delete_after, description) VALUES
('audit_log', 2555, 365, 1825, 'Audit logs: 1 year active, 5 years total retention'),
('export_activity', 1095, 90, 365, 'Export activities: 3 months active, 1 year total retention'),
('asset_history', 3650, 730, 5475, 'Asset history: 2 years active, 15 years total retention'),
('maintenance_task', 1825, 365, 3650, 'Maintenance tasks: 1 year active, 10 years total retention'),
('data_vendor_request', 365, 90, 730, 'Data vendor requests: 3 months active, 2 years total retention');

-- Archived Audit Logs table for long-term storage
CREATE TABLE IF NOT EXISTS archived_audit_logs (
    id BIGSERIAL PRIMARY KEY,
    original_id BIGINT NOT NULL,
    user_id BIGINT NOT NULL,
    object_type VARCHAR(255) NOT NULL,
    object_id VARCHAR(255) NOT NULL,
    action VARCHAR(255) NOT NULL,
    payload JSONB,
    ip_address VARCHAR(45),
    user_agent TEXT,
    session_id VARCHAR(255),
    building_id BIGINT,
    floor_id BIGINT,
    asset_id VARCHAR(255),
    export_id BIGINT,
    field_changes JSONB,
    context JSONB,
    created_at TIMESTAMP NOT NULL,
    archived_at TIMESTAMP NOT NULL DEFAULT NOW(),
    
    INDEX idx_archived_audit_logs_original_id (original_id),
    INDEX idx_archived_audit_logs_user_id (user_id),
    INDEX idx_archived_audit_logs_object_type (object_type),
    INDEX idx_archived_audit_logs_created_at (created_at),
    INDEX idx_archived_audit_logs_archived_at (archived_at)
);

-- Compliance Reports table for storing generated compliance reports
CREATE TABLE IF NOT EXISTS compliance_reports (
    id BIGSERIAL PRIMARY KEY,
    report_type VARCHAR(255) NOT NULL, -- data_access, change_history, export_summary, retention_audit
    report_name VARCHAR(255) NOT NULL,
    generated_by BIGINT NOT NULL,
    parameters JSONB, -- Report parameters and filters
    file_path VARCHAR(500), -- Path to generated report file
    file_size BIGINT,
    format VARCHAR(50), -- csv, json, pdf, xlsx
    status VARCHAR(50) DEFAULT 'generating', -- generating, completed, failed
    error_message TEXT,
    expires_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMP,
    
    INDEX idx_compliance_reports_type (report_type),
    INDEX idx_compliance_reports_generated_by (generated_by),
    INDEX idx_compliance_reports_status (status),
    INDEX idx_compliance_reports_created_at (created_at),
    
    CONSTRAINT fk_compliance_reports_generated_by FOREIGN KEY (generated_by) REFERENCES users(id)
);

-- Data Access Logs table for detailed auditor access tracking
CREATE TABLE IF NOT EXISTS data_access_logs (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    action VARCHAR(255) NOT NULL, -- view, export, modify, delete
    object_type VARCHAR(255) NOT NULL,
    object_id VARCHAR(255) NOT NULL,
    ip_address VARCHAR(45),
    user_agent TEXT,
    session_id VARCHAR(255),
    building_id BIGINT,
    floor_id BIGINT,
    asset_id VARCHAR(255),
    export_id BIGINT,
    access_level VARCHAR(50), -- basic, premium, enterprise, admin
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    
    INDEX idx_data_access_logs_user_id (user_id),
    INDEX idx_data_access_logs_action (action),
    INDEX idx_data_access_logs_object_type (object_type),
    INDEX idx_data_access_logs_created_at (created_at),
    INDEX idx_data_access_logs_ip_address (ip_address),
    
    CONSTRAINT fk_data_access_logs_user_id FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Add archived column to existing audit_logs table
ALTER TABLE audit_logs 
ADD COLUMN IF NOT EXISTS archived BOOLEAN DEFAULT false;

-- Create index for archived column
CREATE INDEX IF NOT EXISTS idx_audit_logs_archived ON audit_logs(archived);

-- Add comments for documentation
COMMENT ON TABLE data_retention_policies IS 'Defines retention policies for different object types';
COMMENT ON TABLE archived_audit_logs IS 'Long-term storage for archived audit logs';
COMMENT ON TABLE compliance_reports IS 'Stores generated compliance reports';
COMMENT ON TABLE data_access_logs IS 'Detailed tracking of data access for auditors';
COMMENT ON COLUMN audit_logs.archived IS 'Flag indicating if log has been archived'; 