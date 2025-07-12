-- Migration: Add missing data vendor tables and enhancements
-- Date: 2024-01-15

-- Ensure api_key_usage table exists (in case it wasn't created in security migration)
CREATE TABLE IF NOT EXISTS api_key_usage (
    id BIGSERIAL PRIMARY KEY,
    api_key_id BIGINT NOT NULL,
    endpoint VARCHAR(255) NOT NULL,
    method VARCHAR(10) NOT NULL,
    status INTEGER NOT NULL,
    response_time INTEGER, -- in milliseconds
    request_size BIGINT,   -- in bytes
    response_size BIGINT,  -- in bytes
    ip_address INET,
    user_agent TEXT,
    error_code VARCHAR(50),
    error_message TEXT,
    rate_limit_hit BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (api_key_id) REFERENCES data_vendor_api_keys(id) ON DELETE CASCADE
);

-- Create indexes for api_key_usage if they don't exist
CREATE INDEX IF NOT EXISTS idx_api_key_usage_api_key_id ON api_key_usage(api_key_id);
CREATE INDEX IF NOT EXISTS idx_api_key_usage_endpoint ON api_key_usage(endpoint);
CREATE INDEX IF NOT EXISTS idx_api_key_usage_status ON api_key_usage(status);
CREATE INDEX IF NOT EXISTS idx_api_key_usage_ip_address ON api_key_usage(ip_address);
CREATE INDEX IF NOT EXISTS idx_api_key_usage_created_at ON api_key_usage(created_at);

-- Add missing columns to data_vendor_api_keys if they don't exist
ALTER TABLE data_vendor_api_keys 
ADD COLUMN IF NOT EXISTS last_used TIMESTAMP NULL,
ADD COLUMN IF NOT EXISTS last_used_at TIMESTAMP NULL,
ADD COLUMN IF NOT EXISTS failed_attempts INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS locked_until TIMESTAMP NULL,
ADD COLUMN IF NOT EXISTS allowed_ips INET[],
ADD COLUMN IF NOT EXISTS allowed_user_agents TEXT[],
ADD COLUMN IF NOT EXISTS security_level VARCHAR(20) DEFAULT 'standard';

-- Create indexes for new columns if they don't exist
CREATE INDEX IF NOT EXISTS idx_data_vendor_api_keys_last_used ON data_vendor_api_keys(last_used);
CREATE INDEX IF NOT EXISTS idx_data_vendor_api_keys_last_used_at ON data_vendor_api_keys(last_used_at);
CREATE INDEX IF NOT EXISTS idx_data_vendor_api_keys_locked_until ON data_vendor_api_keys(locked_until);

-- Add access_level column to buildings table if it doesn't exist
ALTER TABLE buildings 
ADD COLUMN IF NOT EXISTS access_level VARCHAR(50) DEFAULT 'public';

-- Create index for buildings access_level
CREATE INDEX IF NOT EXISTS idx_buildings_access_level ON buildings(access_level);

-- Add missing columns to industry_benchmarks if they don't exist
ALTER TABLE industry_benchmarks 
ADD COLUMN IF NOT EXISTS region VARCHAR(100) DEFAULT 'Global',
ADD COLUMN IF NOT EXISTS building_type VARCHAR(100),
ADD COLUMN IF NOT EXISTS confidence_level DECIMAL(3,2) DEFAULT 0.95,
ADD COLUMN IF NOT EXISTS sample_size INTEGER,
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP;

-- Create indexes for new industry_benchmarks columns
CREATE INDEX IF NOT EXISTS idx_industry_benchmarks_region ON industry_benchmarks(region);
CREATE INDEX IF NOT EXISTS idx_industry_benchmarks_building_type ON industry_benchmarks(building_type);
CREATE INDEX IF NOT EXISTS idx_industry_benchmarks_confidence_level ON industry_benchmarks(confidence_level);

-- Create function to update last_used timestamp for API keys
CREATE OR REPLACE FUNCTION update_api_key_last_used()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE data_vendor_api_keys 
    SET last_used = CURRENT_TIMESTAMP,
        last_used_at = CURRENT_TIMESTAMP
    WHERE id = NEW.api_key_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for api_key_usage
DROP TRIGGER IF EXISTS update_api_key_last_used_trigger ON api_key_usage;
CREATE TRIGGER update_api_key_last_used_trigger
    AFTER INSERT ON api_key_usage
    FOR EACH ROW EXECUTE FUNCTION update_api_key_last_used();

-- Create view for data vendor usage analytics
CREATE OR REPLACE VIEW data_vendor_usage_analytics AS
SELECT 
    dvak.id as api_key_id,
    dvak.vendor_name,
    dvak.access_level,
    dvak.is_active,
    COUNT(aku.id) as total_requests,
    COUNT(CASE WHEN aku.status >= 200 AND aku.status < 300 THEN 1 END) as successful_requests,
    COUNT(CASE WHEN aku.status >= 400 THEN 1 END) as failed_requests,
    COUNT(CASE WHEN aku.rate_limit_hit = true THEN 1 END) as rate_limit_hits,
    AVG(aku.response_time) as avg_response_time,
    MAX(aku.created_at) as last_request_at,
    dvak.created_at as key_created_at
FROM data_vendor_api_keys dvak
LEFT JOIN api_key_usage aku ON dvak.id = aku.api_key_id
GROUP BY dvak.id, dvak.vendor_name, dvak.access_level, dvak.is_active, dvak.created_at;

-- Create view for billing calculations
CREATE OR REPLACE VIEW data_vendor_billing AS
SELECT 
    dvak.id as api_key_id,
    dvak.vendor_name,
    dvak.access_level,
    dvak.is_active,
    CASE 
        WHEN dvak.access_level = 'basic' THEN 50.0
        WHEN dvak.access_level = 'premium' THEN 150.0
        WHEN dvak.access_level = 'enterprise' THEN 500.0
        ELSE 0.0
    END as monthly_base_rate,
    COUNT(aku.id) as requests_this_month,
    CASE 
        WHEN COUNT(aku.id) > 10000 THEN (COUNT(aku.id) - 10000) * 0.005
        ELSE 0.0
    END as overage_charges,
    CASE 
        WHEN dvak.access_level = 'basic' THEN 50.0
        WHEN dvak.access_level = 'premium' THEN 150.0
        WHEN dvak.access_level = 'enterprise' THEN 500.0
        ELSE 0.0
    END + CASE 
        WHEN COUNT(aku.id) > 10000 THEN (COUNT(aku.id) - 10000) * 0.005
        ELSE 0.0
    END as total_monthly_charge
FROM data_vendor_api_keys dvak
LEFT JOIN api_key_usage aku ON dvak.id = aku.api_key_id 
    AND aku.created_at >= DATE_TRUNC('month', CURRENT_DATE)
WHERE dvak.is_active = true
GROUP BY dvak.id, dvak.vendor_name, dvak.access_level, dvak.is_active;

-- Add comments to tables for documentation
COMMENT ON TABLE data_vendor_api_keys IS 'API keys for external data vendors with access control and rate limiting';
COMMENT ON TABLE api_key_usage IS 'Log of all API requests from data vendors for billing and monitoring';
COMMENT ON TABLE industry_benchmarks IS 'Industry benchmark data for equipment and systems';
COMMENT ON VIEW data_vendor_usage_analytics IS 'Analytics view for data vendor API usage';
COMMENT ON VIEW data_vendor_billing IS 'Billing calculations for data vendor API usage'; 