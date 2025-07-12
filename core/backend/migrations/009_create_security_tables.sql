-- Migration: Create security-related tables
-- Date: 2024-01-15

-- Create security_alerts table
CREATE TABLE IF NOT EXISTS security_alerts (
    id BIGSERIAL PRIMARY KEY,
    alert_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL DEFAULT 'medium',
    ip_address INET,
    user_agent TEXT,
    path VARCHAR(255),
    method VARCHAR(10),
    user_id BIGINT REFERENCES users(id) ON DELETE SET NULL,
    session_id VARCHAR(255),
    details JSONB,
    is_resolved BOOLEAN DEFAULT FALSE,
    resolved_by BIGINT REFERENCES users(id) ON DELETE SET NULL,
    resolved_at TIMESTAMP,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for security_alerts
CREATE INDEX IF NOT EXISTS idx_security_alerts_alert_type ON security_alerts(alert_type);
CREATE INDEX IF NOT EXISTS idx_security_alerts_severity ON security_alerts(severity);
CREATE INDEX IF NOT EXISTS idx_security_alerts_ip_address ON security_alerts(ip_address);
CREATE INDEX IF NOT EXISTS idx_security_alerts_user_id ON security_alerts(user_id);
CREATE INDEX IF NOT EXISTS idx_security_alerts_resolved_by ON security_alerts(resolved_by);
CREATE INDEX IF NOT EXISTS idx_security_alerts_created_at ON security_alerts(created_at);

-- Create api_key_usage table
CREATE TABLE IF NOT EXISTS api_key_usage (
    id BIGSERIAL PRIMARY KEY,
    api_key_id BIGINT NOT NULL REFERENCES data_vendor_api_keys(id) ON DELETE CASCADE,
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
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for api_key_usage
CREATE INDEX IF NOT EXISTS idx_api_key_usage_api_key_id ON api_key_usage(api_key_id);
CREATE INDEX IF NOT EXISTS idx_api_key_usage_endpoint ON api_key_usage(endpoint);
CREATE INDEX IF NOT EXISTS idx_api_key_usage_status ON api_key_usage(status);
CREATE INDEX IF NOT EXISTS idx_api_key_usage_ip_address ON api_key_usage(ip_address);
CREATE INDEX IF NOT EXISTS idx_api_key_usage_created_at ON api_key_usage(created_at);

-- Add security-related columns to existing tables

-- Add security fields to data_vendor_api_keys
ALTER TABLE data_vendor_api_keys 
ADD COLUMN IF NOT EXISTS last_used_at TIMESTAMP,
ADD COLUMN IF NOT EXISTS failed_attempts INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS locked_until TIMESTAMP,
ADD COLUMN IF NOT EXISTS allowed_ips INET[],
ADD COLUMN IF NOT EXISTS allowed_user_agents TEXT[],
ADD COLUMN IF NOT EXISTS security_level VARCHAR(20) DEFAULT 'standard'; -- standard, enhanced, strict

-- Add security fields to users table
ALTER TABLE users 
ADD COLUMN IF NOT EXISTS last_login_at TIMESTAMP,
ADD COLUMN IF NOT EXISTS failed_login_attempts INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS locked_until TIMESTAMP,
ADD COLUMN IF NOT EXISTS password_changed_at TIMESTAMP,
ADD COLUMN IF NOT EXISTS require_password_change BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS two_factor_enabled BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS two_factor_secret VARCHAR(255);

-- Create indexes for new security fields
CREATE INDEX IF NOT EXISTS idx_data_vendor_api_keys_last_used_at ON data_vendor_api_keys(last_used_at);
CREATE INDEX IF NOT EXISTS idx_data_vendor_api_keys_locked_until ON data_vendor_api_keys(locked_until);
CREATE INDEX IF NOT EXISTS idx_users_last_login_at ON users(last_login_at);
CREATE INDEX IF NOT EXISTS idx_users_locked_until ON users(locked_until);
CREATE INDEX IF NOT EXISTS idx_users_password_changed_at ON users(password_changed_at);

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger for security_alerts
CREATE TRIGGER update_security_alerts_updated_at 
    BEFORE UPDATE ON security_alerts 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Create function to log API key usage
CREATE OR REPLACE FUNCTION log_api_key_usage(
    p_api_key_id BIGINT,
    p_endpoint VARCHAR(255),
    p_method VARCHAR(10),
    p_status INTEGER,
    p_response_time INTEGER,
    p_request_size BIGINT,
    p_response_size BIGINT,
    p_ip_address INET,
    p_user_agent TEXT,
    p_error_code VARCHAR(50),
    p_error_message TEXT,
    p_rate_limit_hit BOOLEAN
) RETURNS VOID AS $$
BEGIN
    INSERT INTO api_key_usage (
        api_key_id, endpoint, method, status, response_time,
        request_size, response_size, ip_address, user_agent,
        error_code, error_message, rate_limit_hit
    ) VALUES (
        p_api_key_id, p_endpoint, p_method, p_status, p_response_time,
        p_request_size, p_response_size, p_ip_address, p_user_agent,
        p_error_code, p_error_message, p_rate_limit_hit
    );
    
    -- Update last_used_at for the API key
    UPDATE data_vendor_api_keys 
    SET last_used_at = CURRENT_TIMESTAMP 
    WHERE id = p_api_key_id;
END;
$$ LANGUAGE plpgsql;

-- Create function to check and update failed login attempts
CREATE OR REPLACE FUNCTION check_failed_login_attempts(
    p_user_id BIGINT,
    p_success BOOLEAN
) RETURNS BOOLEAN AS $$
DECLARE
    max_attempts INTEGER := 5;
    lock_duration INTERVAL := INTERVAL '15 minutes';
BEGIN
    IF p_success THEN
        -- Reset failed attempts on successful login
        UPDATE users 
        SET failed_login_attempts = 0, 
            locked_until = NULL,
            last_login_at = CURRENT_TIMESTAMP
        WHERE id = p_user_id;
        RETURN TRUE;
    ELSE
        -- Increment failed attempts
        UPDATE users 
        SET failed_login_attempts = failed_login_attempts + 1,
            locked_until = CASE 
                WHEN failed_login_attempts + 1 >= max_attempts 
                THEN CURRENT_TIMESTAMP + lock_duration 
                ELSE locked_until 
            END
        WHERE id = p_user_id;
        
        -- Check if account is now locked
        SELECT locked_until IS NOT NULL AND locked_until > CURRENT_TIMESTAMP
        INTO p_success
        FROM users 
        WHERE id = p_user_id;
        
        RETURN NOT p_success;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Insert default security policies
INSERT INTO data_retention_policies (object_type, retention_period, archive_after, delete_after, is_active, description) VALUES
('security_alerts', 2555, 90, 2555, true, 'Security alerts retained for 7 years with 90-day archive'),
('api_key_usage', 1095, 30, 1095, true, 'API key usage logs retained for 3 years with 30-day archive'),
('audit_logs', 1825, 90, 1825, true, 'Audit logs retained for 5 years with 90-day archive')
ON CONFLICT (object_type) DO NOTHING; 