-- Migration: Enhance Audit Logs for Asset and Export Tracking
-- Date: 2024-01-XX
-- Description: Add enhanced fields to audit_logs table for detailed asset and export change tracking

-- Add new columns to audit_logs table
ALTER TABLE audit_logs
ADD COLUMN ip_address VARCHAR(45), -- IPv6 compatible
ADD COLUMN user_agent TEXT,
ADD COLUMN session_id VARCHAR(255),
ADD COLUMN building_id INTEGER REFERENCES buildings(id),
ADD COLUMN floor_id INTEGER REFERENCES floors(id),
ADD COLUMN asset_id VARCHAR(255),
ADD COLUMN export_id INTEGER,
ADD COLUMN field_changes JSONB,
ADD COLUMN context JSONB;

-- Create indexes for better query performance
CREATE INDEX idx_audit_logs_asset_id ON audit_logs(asset_id);
CREATE INDEX idx_audit_logs_building_id ON audit_logs(building_id);
CREATE INDEX idx_audit_logs_floor_id ON audit_logs(floor_id);
CREATE INDEX idx_audit_logs_export_id ON audit_logs(export_id);
CREATE INDEX idx_audit_logs_ip_address ON audit_logs(ip_address);
CREATE INDEX idx_audit_logs_created_at ON audit_logs(created_at DESC);

-- Create composite indexes for common query patterns
CREATE INDEX idx_audit_logs_asset_user_date ON audit_logs(asset_id, user_id, created_at DESC);
CREATE INDEX idx_audit_logs_building_date ON audit_logs(building_id, created_at DESC);
CREATE INDEX idx_audit_logs_object_type_date ON audit_logs(object_type, created_at DESC);

-- Add comments for documentation
COMMENT ON COLUMN audit_logs.ip_address IS 'Client IP address for security tracking';
COMMENT ON COLUMN audit_logs.user_agent IS 'User agent string for request context';
COMMENT ON COLUMN audit_logs.session_id IS 'Session identifier for request grouping';
COMMENT ON COLUMN audit_logs.building_id IS 'Building context for asset operations';
COMMENT ON COLUMN audit_logs.floor_id IS 'Floor context for asset operations';
COMMENT ON COLUMN audit_logs.asset_id IS 'Asset identifier for asset-specific operations';
COMMENT ON COLUMN audit_logs.export_id IS 'Export identifier for export operations';
COMMENT ON COLUMN audit_logs.field_changes IS 'JSON object tracking field-level changes';
COMMENT ON COLUMN audit_logs.context IS 'Additional context metadata for the operation';
