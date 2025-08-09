-- Migration: Create export activity tracking tables
-- Date: 2024-01-XX

-- ExportActivity table for tracking all export requests and their completion status
CREATE TABLE IF NOT EXISTS export_activities (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    building_id BIGINT,
    export_type VARCHAR(50) NOT NULL,
    format VARCHAR(10) NOT NULL,
    filters TEXT,
    status VARCHAR(20) NOT NULL DEFAULT 'requested',
    file_size BIGINT,
    download_count INTEGER DEFAULT 0,
    processing_time INTEGER,
    error_message TEXT,
    ip_address VARCHAR(45),
    user_agent TEXT,
    requested_at TIMESTAMP NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMP,
    expires_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),

    -- Indexes for performance
    INDEX idx_export_activities_user_id (user_id),
    INDEX idx_export_activities_building_id (building_id),
    INDEX idx_export_activities_export_type (export_type),
    INDEX idx_export_activities_status (status),
    INDEX idx_export_activities_requested_at (requested_at),
    INDEX idx_export_activities_created_at (created_at),

    -- Foreign key constraints
    CONSTRAINT fk_export_activities_user_id FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_export_activities_building_id FOREIGN KEY (building_id) REFERENCES buildings(id) ON DELETE SET NULL
);

-- ExportAnalytics table for aggregated export statistics
CREATE TABLE IF NOT EXISTS export_analytics (
    id BIGSERIAL PRIMARY KEY,
    date DATE NOT NULL,
    period VARCHAR(10) NOT NULL, -- daily, weekly, monthly
    total_exports INTEGER DEFAULT 0,
    total_downloads INTEGER DEFAULT 0,
    total_file_size BIGINT DEFAULT 0,
    avg_processing_time INTEGER DEFAULT 0,

    -- Format breakdown
    csv_count INTEGER DEFAULT 0,
    json_count INTEGER DEFAULT 0,
    xml_count INTEGER DEFAULT 0,
    pdf_count INTEGER DEFAULT 0,

    -- Export type breakdown
    asset_inventory_count INTEGER DEFAULT 0,
    building_data_count INTEGER DEFAULT 0,
    maintenance_count INTEGER DEFAULT 0,
    other_count INTEGER DEFAULT 0,

    -- User activity
    active_users INTEGER DEFAULT 0,
    top_user_id BIGINT,
    top_user_exports INTEGER DEFAULT 0,

    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),

    -- Indexes
    INDEX idx_export_analytics_date (date),
    INDEX idx_export_analytics_period (period),
    UNIQUE INDEX idx_export_analytics_date_period (date, period),

    -- Foreign key constraints
    CONSTRAINT fk_export_analytics_top_user_id FOREIGN KEY (top_user_id) REFERENCES users(id) ON DELETE SET NULL
);

-- DataVendorUsage table for tracking API usage by data vendors
CREATE TABLE IF NOT EXISTS data_vendor_usage (
    id BIGSERIAL PRIMARY KEY,
    api_key_id BIGINT NOT NULL,
    vendor_name VARCHAR(100) NOT NULL,
    request_type VARCHAR(50) NOT NULL,
    building_id BIGINT,
    format VARCHAR(10) NOT NULL,
    file_size BIGINT,
    processing_time INTEGER,
    status VARCHAR(20) NOT NULL DEFAULT 'completed',
    error_code VARCHAR(50),
    error_message TEXT,
    ip_address VARCHAR(45),
    user_agent TEXT,
    rate_limit_hit BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),

    -- Indexes
    INDEX idx_data_vendor_usage_api_key_id (api_key_id),
    INDEX idx_data_vendor_usage_vendor_name (vendor_name),
    INDEX idx_data_vendor_usage_request_type (request_type),
    INDEX idx_data_vendor_usage_building_id (building_id),
    INDEX idx_data_vendor_usage_status (status),
    INDEX idx_data_vendor_usage_created_at (created_at),

    -- Foreign key constraints
    CONSTRAINT fk_data_vendor_usage_api_key_id FOREIGN KEY (api_key_id) REFERENCES data_vendor_api_keys(id) ON DELETE CASCADE,
    CONSTRAINT fk_data_vendor_usage_building_id FOREIGN KEY (building_id) REFERENCES buildings(id) ON DELETE SET NULL
);

-- Add indexes to existing audit_logs table for export tracking
CREATE INDEX IF NOT EXISTS idx_audit_logs_export_id ON audit_logs(export_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_object_type_export ON audit_logs(object_type) WHERE object_type = 'export';

-- Create a view for export dashboard statistics
CREATE OR REPLACE VIEW export_dashboard_stats AS
SELECT
    -- Today's stats
    (SELECT COUNT(*) FROM export_activities WHERE DATE(created_at) = CURRENT_DATE) as today_exports,
    (SELECT COALESCE(SUM(download_count), 0) FROM export_activities WHERE DATE(created_at) = CURRENT_DATE) as today_downloads,
    (SELECT COALESCE(SUM(file_size), 0) FROM export_activities WHERE DATE(created_at) = CURRENT_DATE) as today_file_size,

    -- Week's stats
    (SELECT COUNT(*) FROM export_activities WHERE created_at >= CURRENT_DATE - INTERVAL '7 days') as week_exports,
    (SELECT COALESCE(SUM(download_count), 0) FROM export_activities WHERE created_at >= CURRENT_DATE - INTERVAL '7 days') as week_downloads,

    -- Month's stats
    (SELECT COUNT(*) FROM export_activities WHERE created_at >= CURRENT_DATE - INTERVAL '30 days') as month_exports,
    (SELECT COALESCE(SUM(download_count), 0) FROM export_activities WHERE created_at >= CURRENT_DATE - INTERVAL '30 days') as month_downloads,

    -- Active and failed exports
    (SELECT COUNT(*) FROM export_activities WHERE status IN ('requested', 'processing')) as active_exports,
    (SELECT COUNT(*) FROM export_activities WHERE status = 'failed') as failed_exports,

    -- Average processing time
    (SELECT COALESCE(AVG(processing_time), 0) FROM export_activities WHERE processing_time IS NOT NULL) as avg_processing_time;

-- Create a function to update export analytics
CREATE OR REPLACE FUNCTION update_export_analytics()
RETURNS void AS $$
BEGIN
    -- Insert or update daily analytics
    INSERT INTO export_analytics (
        date, period, total_exports, total_downloads, total_file_size, avg_processing_time,
        csv_count, json_count, xml_count, pdf_count,
        asset_inventory_count, building_data_count, maintenance_count, other_count,
        active_users, top_user_id, top_user_exports
    )
    SELECT
        CURRENT_DATE,
        'daily',
        COUNT(*),
        COALESCE(SUM(download_count), 0),
        COALESCE(SUM(file_size), 0),
        COALESCE(AVG(processing_time), 0),
        COUNT(CASE WHEN format = 'csv' THEN 1 END),
        COUNT(CASE WHEN format = 'json' THEN 1 END),
        COUNT(CASE WHEN format = 'xml' THEN 1 END),
        COUNT(CASE WHEN format = 'pdf' THEN 1 END),
        COUNT(CASE WHEN export_type = 'asset_inventory' THEN 1 END),
        COUNT(CASE WHEN export_type = 'building_data' THEN 1 END),
        COUNT(CASE WHEN export_type = 'maintenance' THEN 1 END),
        COUNT(CASE WHEN export_type NOT IN ('asset_inventory', 'building_data', 'maintenance') THEN 1 END),
        COUNT(DISTINCT user_id),
        (SELECT user_id FROM export_activities WHERE DATE(created_at) = CURRENT_DATE GROUP BY user_id ORDER BY COUNT(*) DESC LIMIT 1),
        (SELECT COUNT(*) FROM export_activities WHERE DATE(created_at) = CURRENT_DATE AND user_id = (
            SELECT user_id FROM export_activities WHERE DATE(created_at) = CURRENT_DATE GROUP BY user_id ORDER BY COUNT(*) DESC LIMIT 1
        ))
    FROM export_activities
    WHERE DATE(created_at) = CURRENT_DATE
    ON CONFLICT (date, period) DO UPDATE SET
        total_exports = EXCLUDED.total_exports,
        total_downloads = EXCLUDED.total_downloads,
        total_file_size = EXCLUDED.total_file_size,
        avg_processing_time = EXCLUDED.avg_processing_time,
        csv_count = EXCLUDED.csv_count,
        json_count = EXCLUDED.json_count,
        xml_count = EXCLUDED.xml_count,
        pdf_count = EXCLUDED.pdf_count,
        asset_inventory_count = EXCLUDED.asset_inventory_count,
        building_data_count = EXCLUDED.building_data_count,
        maintenance_count = EXCLUDED.maintenance_count,
        other_count = EXCLUDED.other_count,
        active_users = EXCLUDED.active_users,
        top_user_id = EXCLUDED.top_user_id,
        top_user_exports = EXCLUDED.top_user_exports,
        updated_at = NOW();
END;
$$ LANGUAGE plpgsql;

-- Create a trigger to automatically update analytics when export activities change
CREATE OR REPLACE FUNCTION trigger_update_export_analytics()
RETURNS TRIGGER AS $$
BEGIN
    PERFORM update_export_analytics();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER export_analytics_trigger
    AFTER INSERT OR UPDATE OR DELETE ON export_activities
    FOR EACH STATEMENT
    EXECUTE FUNCTION trigger_update_export_analytics();
