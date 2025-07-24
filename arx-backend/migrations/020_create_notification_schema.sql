-- 020_create_notification_schema.sql
-- Migration: Create comprehensive notification system schema

-- Enable UUID extension for external IDs
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- NOTIFICATION CHANNELS
-- Configuration for different notification channels (email, slack, sms, webhook, etc.)
CREATE TABLE notification_channels (
    id SERIAL PRIMARY KEY,
    channel VARCHAR(50) UNIQUE NOT NULL, -- email, slack, sms, webhook, push, in_app
    name VARCHAR(255) NOT NULL,
    description TEXT,
    is_enabled BOOLEAN DEFAULT true,
    config JSONB, -- Channel-specific configuration (SMTP settings, webhook URLs, etc.)
    rate_limit INTEGER DEFAULT 100, -- messages per minute
    timeout INTEGER DEFAULT 30, -- seconds
    retry_limit INTEGER DEFAULT 3,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP
);

-- NOTIFICATION TEMPLATES
-- Reusable notification templates with variables
CREATE TABLE notification_templates (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,
    description TEXT,
    type VARCHAR(50) NOT NULL, -- system, user, maintenance, alert, reminder, update, security
    channels JSONB, -- Array of channel types this template supports
    subject VARCHAR(500),
    body TEXT NOT NULL,
    html_body TEXT,
    variables JSONB, -- Template variables and their types
    is_active BOOLEAN DEFAULT true,
    created_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP
);

-- NOTIFICATION CONFIGURATIONS
-- System-wide notification configurations
CREATE TABLE notification_configs (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,
    description TEXT,
    channels JSONB, -- Array of channel types
    priority VARCHAR(20) DEFAULT 'normal', -- low, normal, high, urgent
    retry_attempts INTEGER DEFAULT 3,
    retry_delay INTEGER DEFAULT 60, -- seconds
    timeout INTEGER DEFAULT 30, -- seconds
    template_id INTEGER REFERENCES notification_templates(id) ON DELETE SET NULL,
    template_data JSONB, -- Template variables data
    is_active BOOLEAN DEFAULT true,
    created_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP
);

-- NOTIFICATIONS (Enhanced)
-- Main notification records
CREATE TABLE notifications (
    id SERIAL PRIMARY KEY,
    title VARCHAR(500) NOT NULL,
    message TEXT NOT NULL,
    type VARCHAR(50) NOT NULL, -- system, user, maintenance, alert, reminder, update, security
    channels JSONB, -- Array of channel types for this notification
    priority VARCHAR(20) DEFAULT 'normal', -- low, normal, high, urgent
    status VARCHAR(20) DEFAULT 'pending', -- pending, sending, sent, delivered, failed, rate_limited, cancelled
    config_id INTEGER REFERENCES notification_configs(id) ON DELETE SET NULL,
    template_id INTEGER REFERENCES notification_templates(id) ON DELETE SET NULL,
    template_data JSONB, -- Template variables data
    recipient_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    sender_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    building_id INTEGER REFERENCES buildings(id) ON DELETE SET NULL,
    asset_id VARCHAR(64), -- References BuildingAsset.id
    related_object_id VARCHAR(64), -- Generic object reference
    related_object_type VARCHAR(100), -- Type of related object
    metadata JSONB, -- Additional metadata
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP
);

-- NOTIFICATION DELIVERIES
-- Individual delivery attempts for each channel
CREATE TABLE notification_deliveries (
    id SERIAL PRIMARY KEY,
    notification_id INTEGER REFERENCES notifications(id) ON DELETE CASCADE,
    channel VARCHAR(50) NOT NULL, -- email, slack, sms, webhook, push, in_app
    status VARCHAR(20) DEFAULT 'pending', -- pending, sending, sent, delivered, failed, rate_limited, cancelled
    attempt_number INTEGER DEFAULT 1,
    sent_at TIMESTAMP,
    delivered_at TIMESTAMP,
    failed_at TIMESTAMP,
    error_message TEXT,
    response_code INTEGER,
    response_body TEXT,
    external_id VARCHAR(255), -- External service ID (email message ID, Slack timestamp, etc.)
    metadata JSONB, -- Additional delivery metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- NOTIFICATION PREFERENCES
-- User preferences for notification channels and types
CREATE TABLE notification_preferences (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    channel VARCHAR(50) NOT NULL, -- email, slack, sms, webhook, push, in_app
    type VARCHAR(50) NOT NULL, -- system, user, maintenance, alert, reminder, update, security
    is_enabled BOOLEAN DEFAULT true,
    priority VARCHAR(20) DEFAULT 'normal', -- low, normal, high, urgent
    frequency VARCHAR(20) DEFAULT 'immediate', -- immediate, daily, weekly, never
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, channel, type)
);

-- NOTIFICATION LOGS
-- Audit trail for notification events
CREATE TABLE notification_logs (
    id SERIAL PRIMARY KEY,
    notification_id INTEGER REFERENCES notifications(id) ON DELETE CASCADE,
    delivery_id INTEGER REFERENCES notification_deliveries(id) ON DELETE SET NULL,
    action VARCHAR(50) NOT NULL, -- created, sent, delivered, failed, retry, cancelled, etc.
    status VARCHAR(20) NOT NULL, -- pending, sending, sent, delivered, failed, rate_limited, cancelled
    message TEXT,
    metadata JSONB, -- Additional log metadata
    ip_address VARCHAR(45),
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- NOTIFICATION STATISTICS
-- Aggregated statistics for reporting
CREATE TABLE notification_statistics (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    channel VARCHAR(50) NOT NULL, -- email, slack, sms, webhook, push, in_app
    type VARCHAR(50) NOT NULL, -- system, user, maintenance, alert, reminder, update, security
    total_sent INTEGER DEFAULT 0,
    total_delivered INTEGER DEFAULT 0,
    total_failed INTEGER DEFAULT 0,
    total_rate_limited INTEGER DEFAULT 0,
    avg_delivery_time DECIMAL(10,3), -- in seconds
    success_rate DECIMAL(5,2), -- percentage
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(date, channel, type)
);

-- NOTIFICATION QUEUE
-- Queue for background processing
CREATE TABLE notification_queue (
    id SERIAL PRIMARY KEY,
    notification_id INTEGER REFERENCES notifications(id) ON DELETE CASCADE,
    priority VARCHAR(20) NOT NULL, -- low, normal, high, urgent
    status VARCHAR(20) DEFAULT 'queued', -- queued, processing, completed, failed
    attempt_count INTEGER DEFAULT 0,
    max_attempts INTEGER DEFAULT 3,
    scheduled_at TIMESTAMP NOT NULL,
    processed_at TIMESTAMP,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- NOTIFICATION SCHEDULES
-- Scheduled and recurring notifications
CREATE TABLE notification_schedules (
    id SERIAL PRIMARY KEY,
    notification_id INTEGER REFERENCES notifications(id) ON DELETE CASCADE,
    schedule_type VARCHAR(20) NOT NULL, -- one_time, recurring, interval
    cron_expression VARCHAR(100), -- For recurring schedules
    interval_seconds INTEGER, -- For interval schedules
    next_run_at TIMESTAMP NOT NULL,
    last_run_at TIMESTAMP,
    is_active BOOLEAN DEFAULT true,
    max_runs INTEGER, -- NULL for unlimited
    run_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- NOTIFICATION GROUPS
-- Group notifications for batch processing
CREATE TABLE notification_groups (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    template_id INTEGER REFERENCES notification_templates(id) ON DELETE SET NULL,
    config_id INTEGER REFERENCES notification_configs(id) ON DELETE SET NULL,
    is_active BOOLEAN DEFAULT true,
    created_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP
);

-- NOTIFICATION GROUP MEMBERS
-- Users in notification groups
CREATE TABLE notification_group_members (
    id SERIAL PRIMARY KEY,
    group_id INTEGER REFERENCES notification_groups(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(group_id, user_id)
);

-- NOTIFICATION WEBHOOKS
-- External webhook configurations
CREATE TABLE notification_webhooks (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    url VARCHAR(500) NOT NULL,
    method VARCHAR(10) DEFAULT 'POST',
    headers JSONB, -- Custom headers
    auth_type VARCHAR(20), -- basic, bearer, none
    auth_credentials JSONB, -- Encrypted credentials
    is_active BOOLEAN DEFAULT true,
    created_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP
);

-- NOTIFICATION WEBHOOK EVENTS
-- Webhook delivery events
CREATE TABLE notification_webhook_events (
    id SERIAL PRIMARY KEY,
    webhook_id INTEGER REFERENCES notification_webhooks(id) ON DELETE CASCADE,
    delivery_id INTEGER REFERENCES notification_deliveries(id) ON DELETE CASCADE,
    event_type VARCHAR(50) NOT NULL, -- sent, delivered, failed, retry
    payload JSONB, -- Webhook payload
    response_code INTEGER,
    response_body TEXT,
    response_time INTEGER, -- milliseconds
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX idx_notifications_recipient_id ON notifications(recipient_id);
CREATE INDEX idx_notifications_sender_id ON notifications(sender_id);
CREATE INDEX idx_notifications_status ON notifications(status);
CREATE INDEX idx_notifications_type ON notifications(type);
CREATE INDEX idx_notifications_priority ON notifications(priority);
CREATE INDEX idx_notifications_created_at ON notifications(created_at);
CREATE INDEX idx_notifications_building_id ON notifications(building_id);
CREATE INDEX idx_notifications_asset_id ON notifications(asset_id);

CREATE INDEX idx_notification_deliveries_notification_id ON notification_deliveries(notification_id);
CREATE INDEX idx_notification_deliveries_channel ON notification_deliveries(channel);
CREATE INDEX idx_notification_deliveries_status ON notification_deliveries(status);
CREATE INDEX idx_notification_deliveries_created_at ON notification_deliveries(created_at);

CREATE INDEX idx_notification_preferences_user_id ON notification_preferences(user_id);
CREATE INDEX idx_notification_preferences_channel ON notification_preferences(channel);
CREATE INDEX idx_notification_preferences_type ON notification_preferences(type);

CREATE INDEX idx_notification_logs_notification_id ON notification_logs(notification_id);
CREATE INDEX idx_notification_logs_delivery_id ON notification_logs(delivery_id);
CREATE INDEX idx_notification_logs_action ON notification_logs(action);
CREATE INDEX idx_notification_logs_created_at ON notification_logs(created_at);

CREATE INDEX idx_notification_statistics_date ON notification_statistics(date);
CREATE INDEX idx_notification_statistics_channel ON notification_statistics(channel);
CREATE INDEX idx_notification_statistics_type ON notification_statistics(type);

CREATE INDEX idx_notification_queue_status ON notification_queue(status);
CREATE INDEX idx_notification_queue_priority ON notification_queue(priority);
CREATE INDEX idx_notification_queue_scheduled_at ON notification_queue(scheduled_at);

CREATE INDEX idx_notification_schedules_next_run_at ON notification_schedules(next_run_at);
CREATE INDEX idx_notification_schedules_is_active ON notification_schedules(is_active);

CREATE INDEX idx_notification_templates_type ON notification_templates(type);
CREATE INDEX idx_notification_templates_is_active ON notification_templates(is_active);

CREATE INDEX idx_notification_configs_is_active ON notification_configs(is_active);

CREATE INDEX idx_notification_channels_channel ON notification_channels(channel);
CREATE INDEX idx_notification_channels_is_enabled ON notification_channels(is_enabled);

-- Triggers for updated_at timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_notification_channels_updated_at BEFORE UPDATE ON notification_channels
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_notification_templates_updated_at BEFORE UPDATE ON notification_templates
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_notification_configs_updated_at BEFORE UPDATE ON notification_configs
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_notifications_updated_at BEFORE UPDATE ON notifications
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_notification_deliveries_updated_at BEFORE UPDATE ON notification_deliveries
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_notification_preferences_updated_at BEFORE UPDATE ON notification_preferences
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_notification_statistics_updated_at BEFORE UPDATE ON notification_statistics
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_notification_queue_updated_at BEFORE UPDATE ON notification_queue
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_notification_schedules_updated_at BEFORE UPDATE ON notification_schedules
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_notification_groups_updated_at BEFORE UPDATE ON notification_groups
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_notification_webhooks_updated_at BEFORE UPDATE ON notification_webhooks
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert default notification channels
INSERT INTO notification_channels (channel, name, description, config) VALUES
('email', 'Email', 'Email notifications via SMTP', '{"smtp_host": "", "smtp_port": 587, "smtp_username": "", "smtp_password": "", "from_email": "", "from_name": ""}'),
('slack', 'Slack', 'Slack notifications via webhook', '{"webhook_url": "", "channel": "", "username": "", "icon_emoji": ""}'),
('sms', 'SMS', 'SMS notifications via Twilio', '{"account_sid": "", "auth_token": "", "from_number": ""}'),
('webhook', 'Webhook', 'Custom webhook notifications', '{"url": "", "method": "POST", "headers": {}}'),
('push', 'Push', 'Mobile push notifications', '{"fcm_server_key": "", "ios_cert_path": ""}'),
('in_app', 'In-App', 'In-app notifications', '{}');

-- Insert default notification templates
INSERT INTO notification_templates (name, description, type, channels, subject, body, variables, created_by) VALUES
('system_maintenance', 'System maintenance notification', 'maintenance', '["email", "slack"]', 'System Maintenance: {{title}}', 'Hello {{user_name}},\n\n{{message}}\n\nMaintenance Type: {{maintenance_type}}\nScheduled Date: {{scheduled_date}}\n\nBest regards,\nArxos Team', '{"user_name": "string", "maintenance_type": "string", "scheduled_date": "datetime"}', 1),
('asset_alert', 'Asset alert notification', 'alert', '["email", "slack", "sms"]', 'Asset Alert: {{asset_name}}', 'Alert for asset {{asset_name}}:\n\n{{message}}\n\nAsset ID: {{asset_id}}\nLocation: {{location}}\nPriority: {{priority}}\n\nPlease take immediate action.', '{"asset_name": "string", "asset_id": "string", "location": "string", "priority": "string"}', 1),
('user_welcome', 'Welcome notification for new users', 'user', '["email"]', 'Welcome to Arxos!', 'Hello {{user_name}},\n\nWelcome to Arxos! We''re excited to have you on board.\n\nYour account has been successfully created and you can now access all features.\n\nIf you have any questions, please don''t hesitate to contact our support team.\n\nBest regards,\nArxos Team', '{"user_name": "string"}', 1);

-- Insert default notification configurations
INSERT INTO notification_configs (name, description, channels, priority, template_id, created_by) VALUES
('default_maintenance', 'Default maintenance notification configuration', '["email", "slack"]', 'normal', 1, 1),
('critical_alerts', 'Critical asset alert configuration', '["email", "slack", "sms"]', 'urgent', 2, 1),
('user_notifications', 'Default user notification configuration', '["email"]', 'normal', 3, 1); 