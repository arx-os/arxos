-- Migration 007: Ecosystem Tiers and Three-Tier Architecture
-- This migration adds support for the three-tier ecosystem architecture:
-- Layer 1 (Core): FREE - Basic building management
-- Layer 2 (Hardware): FREEMIUM - Device management and marketplace
-- Layer 3 (Workflow): PAID - Advanced automation and analytics

-- Create ecosystem tiers table
CREATE TABLE IF NOT EXISTS ecosystem_tiers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    description TEXT,
    price VARCHAR(20) NOT NULL,
    features JSONB,
    limits JSONB,
    api_endpoints JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Insert default tiers
INSERT INTO ecosystem_tiers (name, description, price, features, limits, api_endpoints) VALUES
('core', 'ArxOS Core - The "Git" of buildings', 'FREE', 
 '["building_management", "equipment_management", "spatial_queries", "import_export", "basic_cli", "version_control", "hardware_designs", "partner_support"]',
 '{"buildings": -1, "users": 5, "api_calls": 1000, "storage_gb": 10, "support": "community"}',
 '["/api/v1/core/buildings", "/api/v1/core/equipment", "/api/v1/core/spatial", "/api/v1/core/import", "/api/v1/core/export"]'),
 
('hardware', 'Hardware Platform - The "GitHub Free"', 'FREEMIUM',
 '["device_management", "gateway_deployment", "device_templates", "firmware_updates", "protocol_translation", "basic_automation", "certified_marketplace", "hardware_support"]',
 '{"certified_devices": 10, "marketplace_sales": 5, "support": "community", "commission": "5-10%"}',
 '["/api/v1/hardware/devices", "/api/v1/hardware/templates", "/api/v1/hardware/gateway", "/api/v1/hardware/marketplace"]'),
 
('workflow', 'Workflow Automation - The "GitHub Pro"', 'PAID',
 '["visual_workflows", "workflow_automation", "cmmc_features", "work_order_management", "maintenance_scheduling", "predictive_analytics", "enterprise_integrations", "advanced_reporting", "professional_support", "unlimited_resources"]',
 '{"buildings": -1, "users": -1, "workflows": -1, "integrations": 400, "api_calls": -1, "storage_gb": -1, "support": "professional", "sla": "99.9%"}',
 '["/api/v1/workflow/workflows", "/api/v1/workflow/cmmc", "/api/v1/workflow/automation", "/api/v1/workflow/analytics", "/api/v1/workflow/integrations"]');

-- Add tier column to existing tables
ALTER TABLE buildings ADD COLUMN IF NOT EXISTS tier VARCHAR(20) DEFAULT 'core';
ALTER TABLE equipment ADD COLUMN IF NOT EXISTS tier VARCHAR(20) DEFAULT 'core';

-- Create user tiers table for tier management
CREATE TABLE IF NOT EXISTS user_tiers (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    tier VARCHAR(20) NOT NULL,
    organization_id VARCHAR(255),
    subscription_id VARCHAR(255),
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE,
    status VARCHAR(20) DEFAULT 'active',
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, tier)
);

-- Create tier usage tracking table
CREATE TABLE IF NOT EXISTS tier_usage (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    tier VARCHAR(20) NOT NULL,
    resource VARCHAR(100) NOT NULL,
    usage_count INTEGER DEFAULT 0,
    usage_limit INTEGER DEFAULT -1,
    period_start TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    period_end TIMESTAMP WITH TIME ZONE,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, tier, resource, period_start)
);

-- Create hardware devices table (Layer 2)
CREATE TABLE IF NOT EXISTS hardware_devices (
    id VARCHAR(255) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    type VARCHAR(100) NOT NULL,
    template_id VARCHAR(255),
    status VARCHAR(50) DEFAULT 'active',
    config JSONB,
    firmware JSONB,
    location JSONB,
    user_id VARCHAR(255) NOT NULL,
    tier VARCHAR(20) DEFAULT 'hardware',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create device templates table
CREATE TABLE IF NOT EXISTS device_templates (
    id VARCHAR(255) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    type VARCHAR(100) NOT NULL,
    description TEXT,
    schema JSONB,
    firmware BYTEA,
    sdk JSONB,
    certification JSONB,
    tier VARCHAR(20) DEFAULT 'hardware',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create gateways table
CREATE TABLE IF NOT EXISTS gateways (
    id VARCHAR(255) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    type VARCHAR(100) NOT NULL,
    status VARCHAR(50) DEFAULT 'active',
    config JSONB,
    devices JSONB,
    location JSONB,
    user_id VARCHAR(255) NOT NULL,
    tier VARCHAR(20) DEFAULT 'hardware',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create certified devices marketplace table
CREATE TABLE IF NOT EXISTS certified_devices (
    id VARCHAR(255) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    type VARCHAR(100) NOT NULL,
    price DECIMAL(10,2),
    certification VARCHAR(100),
    description TEXT,
    features JSONB,
    specifications JSONB,
    availability VARCHAR(50) DEFAULT 'available',
    tier VARCHAR(20) DEFAULT 'hardware',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create marketplace orders table
CREATE TABLE IF NOT EXISTS marketplace_orders (
    id VARCHAR(255) PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    device_id VARCHAR(255) NOT NULL,
    quantity INTEGER DEFAULT 1,
    status VARCHAR(50) DEFAULT 'pending',
    total_price DECIMAL(10,2),
    shipping JSONB,
    payment JSONB,
    tier VARCHAR(20) DEFAULT 'hardware',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create workflows table (Layer 3)
CREATE TABLE IF NOT EXISTS workflows (
    id VARCHAR(255) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    definition JSONB,
    status VARCHAR(50) DEFAULT 'active',
    version VARCHAR(20) DEFAULT '1.0.0',
    n8n_workflow_id VARCHAR(255),
    user_id VARCHAR(255) NOT NULL,
    tier VARCHAR(20) DEFAULT 'workflow',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create workflow executions table
CREATE TABLE IF NOT EXISTS workflow_executions (
    id VARCHAR(255) PRIMARY KEY,
    workflow_id VARCHAR(255) NOT NULL,
    n8n_execution_id VARCHAR(255),
    status VARCHAR(50) DEFAULT 'running',
    input JSONB,
    output JSONB,
    duration_ms BIGINT,
    error TEXT,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    tier VARCHAR(20) DEFAULT 'workflow'
);

-- Create work orders table (CMMS)
CREATE TABLE IF NOT EXISTS work_orders (
    id VARCHAR(255) PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    priority VARCHAR(50) DEFAULT 'medium',
    status VARCHAR(50) DEFAULT 'open',
    equipment_id VARCHAR(255),
    assigned_to VARCHAR(255),
    due_date TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    metadata JSONB,
    user_id VARCHAR(255) NOT NULL,
    tier VARCHAR(20) DEFAULT 'workflow',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create maintenance schedules table
CREATE TABLE IF NOT EXISTS maintenance_schedules (
    id VARCHAR(255) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    type VARCHAR(100) NOT NULL,
    schedule JSONB,
    tasks JSONB,
    status VARCHAR(50) DEFAULT 'active',
    user_id VARCHAR(255) NOT NULL,
    tier VARCHAR(20) DEFAULT 'workflow',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create maintenance schedule equipment relationships table
CREATE TABLE IF NOT EXISTS maintenance_schedule_equipment (
    id SERIAL PRIMARY KEY,
    schedule_id VARCHAR(255) NOT NULL,
    equipment_id VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(schedule_id, equipment_id)
);

-- Create maintenance executions table
CREATE TABLE IF NOT EXISTS maintenance_executions (
    id VARCHAR(255) PRIMARY KEY,
    schedule_id VARCHAR(255) NOT NULL,
    status VARCHAR(50) DEFAULT 'running',
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    tasks JSONB,
    results JSONB,
    tier VARCHAR(20) DEFAULT 'workflow'
);

-- Create reports table
CREATE TABLE IF NOT EXISTS reports (
    id VARCHAR(255) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    type VARCHAR(100) NOT NULL,
    data JSONB,
    format VARCHAR(50) DEFAULT 'json',
    generated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    user_id VARCHAR(255) NOT NULL,
    size_bytes BIGINT,
    tier VARCHAR(20) DEFAULT 'workflow'
);

-- Create automations table
CREATE TABLE IF NOT EXISTS automations (
    id VARCHAR(255) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    trigger JSONB,
    actions JSONB,
    conditions JSONB,
    status VARCHAR(50) DEFAULT 'active',
    user_id VARCHAR(255) NOT NULL,
    tier VARCHAR(20) DEFAULT 'workflow',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create automation status table
CREATE TABLE IF NOT EXISTS automation_status (
    id SERIAL PRIMARY KEY,
    automation_id VARCHAR(255) NOT NULL,
    status VARCHAR(50) DEFAULT 'active',
    last_triggered TIMESTAMP WITH TIME ZONE,
    trigger_count INTEGER DEFAULT 0,
    success_count INTEGER DEFAULT 0,
    error_count INTEGER DEFAULT 0,
    last_error TEXT,
    next_schedule TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(automation_id)
);

-- Create analytics results table
CREATE TABLE IF NOT EXISTS analytics_results (
    id VARCHAR(255) PRIMARY KEY,
    type VARCHAR(100) NOT NULL,
    data JSONB,
    summary JSONB,
    generated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    tier VARCHAR(20) DEFAULT 'workflow'
);

-- Create predictive insights table
CREATE TABLE IF NOT EXISTS predictive_insights (
    id VARCHAR(255) PRIMARY KEY,
    type VARCHAR(100) NOT NULL,
    insights JSONB,
    confidence DECIMAL(5,4),
    generated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    tier VARCHAR(20) DEFAULT 'workflow'
);

-- Create dashboards table
CREATE TABLE IF NOT EXISTS dashboards (
    id VARCHAR(255) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    type VARCHAR(100) NOT NULL,
    widgets JSONB,
    layout JSONB,
    user_id VARCHAR(255) NOT NULL,
    tier VARCHAR(20) DEFAULT 'workflow',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create integrations table
CREATE TABLE IF NOT EXISTS integrations (
    id VARCHAR(255) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    type VARCHAR(100) NOT NULL,
    status VARCHAR(50) DEFAULT 'active',
    config JSONB,
    credentials JSONB,
    user_id VARCHAR(255) NOT NULL,
    tier VARCHAR(20) DEFAULT 'workflow',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create integration status table
CREATE TABLE IF NOT EXISTS integration_status (
    id SERIAL PRIMARY KEY,
    integration_id VARCHAR(255) NOT NULL,
    status VARCHAR(50) DEFAULT 'active',
    last_sync TIMESTAMP WITH TIME ZONE,
    sync_count INTEGER DEFAULT 0,
    error_count INTEGER DEFAULT 0,
    last_error TEXT,
    next_sync TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(integration_id)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_user_tiers_user_id ON user_tiers(user_id);
CREATE INDEX IF NOT EXISTS idx_user_tiers_tier ON user_tiers(tier);
CREATE INDEX IF NOT EXISTS idx_user_tiers_status ON user_tiers(status);

CREATE INDEX IF NOT EXISTS idx_tier_usage_user_id ON tier_usage(user_id);
CREATE INDEX IF NOT EXISTS idx_tier_usage_tier ON tier_usage(tier);
CREATE INDEX IF NOT EXISTS idx_tier_usage_resource ON tier_usage(resource);

CREATE INDEX IF NOT EXISTS idx_hardware_devices_user_id ON hardware_devices(user_id);
CREATE INDEX IF NOT EXISTS idx_hardware_devices_type ON hardware_devices(type);
CREATE INDEX IF NOT EXISTS idx_hardware_devices_status ON hardware_devices(status);

CREATE INDEX IF NOT EXISTS idx_device_templates_type ON device_templates(type);

CREATE INDEX IF NOT EXISTS idx_gateways_user_id ON gateways(user_id);
CREATE INDEX IF NOT EXISTS idx_gateways_status ON gateways(status);

CREATE INDEX IF NOT EXISTS idx_certified_devices_type ON certified_devices(type);
CREATE INDEX IF NOT EXISTS idx_certified_devices_availability ON certified_devices(availability);

CREATE INDEX IF NOT EXISTS idx_marketplace_orders_user_id ON marketplace_orders(user_id);
CREATE INDEX IF NOT EXISTS idx_marketplace_orders_status ON marketplace_orders(status);

CREATE INDEX IF NOT EXISTS idx_workflows_user_id ON workflows(user_id);
CREATE INDEX IF NOT EXISTS idx_workflows_status ON workflows(status);

CREATE INDEX IF NOT EXISTS idx_workflow_executions_workflow_id ON workflow_executions(workflow_id);
CREATE INDEX IF NOT EXISTS idx_workflow_executions_status ON workflow_executions(status);

CREATE INDEX IF NOT EXISTS idx_work_orders_user_id ON work_orders(user_id);
CREATE INDEX IF NOT EXISTS idx_work_orders_status ON work_orders(status);
CREATE INDEX IF NOT EXISTS idx_work_orders_equipment_id ON work_orders(equipment_id);

CREATE INDEX IF NOT EXISTS idx_maintenance_schedules_user_id ON maintenance_schedules(user_id);
CREATE INDEX IF NOT EXISTS idx_maintenance_schedules_status ON maintenance_schedules(status);

CREATE INDEX IF NOT EXISTS idx_maintenance_executions_schedule_id ON maintenance_executions(schedule_id);
CREATE INDEX IF NOT EXISTS idx_maintenance_executions_status ON maintenance_executions(status);

CREATE INDEX IF NOT EXISTS idx_reports_user_id ON reports(user_id);
CREATE INDEX IF NOT EXISTS idx_reports_type ON reports(type);

CREATE INDEX IF NOT EXISTS idx_automations_user_id ON automations(user_id);
CREATE INDEX IF NOT EXISTS idx_automations_status ON automations(status);

CREATE INDEX IF NOT EXISTS idx_automation_status_automation_id ON automation_status(automation_id);

CREATE INDEX IF NOT EXISTS idx_analytics_results_type ON analytics_results(type);

CREATE INDEX IF NOT EXISTS idx_predictive_insights_type ON predictive_insights(type);

CREATE INDEX IF NOT EXISTS idx_dashboards_user_id ON dashboards(user_id);
CREATE INDEX IF NOT EXISTS idx_dashboards_type ON dashboards(type);

CREATE INDEX IF NOT EXISTS idx_integrations_user_id ON integrations(user_id);
CREATE INDEX IF NOT EXISTS idx_integrations_status ON integrations(status);

CREATE INDEX IF NOT EXISTS idx_integration_status_integration_id ON integration_status(integration_id);

-- Create spatial indexes for location-based queries
CREATE INDEX IF NOT EXISTS idx_hardware_devices_location ON hardware_devices USING GIST ((location::geometry));
CREATE INDEX IF NOT EXISTS idx_gateways_location ON gateways USING GIST ((location::geometry));

-- Create updated_at triggers for all tables
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply triggers to tables with updated_at columns
CREATE TRIGGER update_ecosystem_tiers_updated_at BEFORE UPDATE ON ecosystem_tiers FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_user_tiers_updated_at BEFORE UPDATE ON user_tiers FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_tier_usage_updated_at BEFORE UPDATE ON tier_usage FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_hardware_devices_updated_at BEFORE UPDATE ON hardware_devices FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_device_templates_updated_at BEFORE UPDATE ON device_templates FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_gateways_updated_at BEFORE UPDATE ON gateways FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_marketplace_orders_updated_at BEFORE UPDATE ON marketplace_orders FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_workflows_updated_at BEFORE UPDATE ON workflows FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_work_orders_updated_at BEFORE UPDATE ON work_orders FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_maintenance_schedules_updated_at BEFORE UPDATE ON maintenance_schedules FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_automations_updated_at BEFORE UPDATE ON automations FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_automation_status_updated_at BEFORE UPDATE ON automation_status FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_dashboards_updated_at BEFORE UPDATE ON dashboards FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_integrations_updated_at BEFORE UPDATE ON integrations FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_integration_status_updated_at BEFORE UPDATE ON integration_status FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Create views for tier management
CREATE OR REPLACE VIEW user_tier_summary AS
SELECT 
    ut.user_id,
    ut.tier,
    et.name as tier_name,
    et.description as tier_description,
    et.price as tier_price,
    et.features as tier_features,
    et.limits as tier_limits,
    ut.status,
    ut.started_at,
    ut.expires_at,
    ut.metadata
FROM user_tiers ut
JOIN ecosystem_tiers et ON ut.tier = et.name
WHERE ut.status = 'active';

-- Create view for usage tracking
CREATE OR REPLACE VIEW user_usage_summary AS
SELECT 
    tu.user_id,
    tu.tier,
    tu.resource,
    tu.usage_count,
    tu.usage_limit,
    et.limits->tu.resource as tier_limit,
    CASE 
        WHEN tu.usage_limit = -1 THEN true
        WHEN et.limits->tu.resource = '-1' THEN true
        WHEN tu.usage_count < COALESCE(tu.usage_limit, (et.limits->tu.resource)::int) THEN true
        ELSE false
    END as within_limit
FROM tier_usage tu
JOIN ecosystem_tiers et ON tu.tier = et.name;

-- Grant permissions
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO arxos_user;
GRANT SELECT ON ALL SEQUENCES IN SCHEMA public TO arxos_user;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO arxos_user;

-- Add comments for documentation
COMMENT ON TABLE ecosystem_tiers IS 'Defines the three-tier ecosystem architecture: core (free), hardware (freemium), workflow (paid)';
COMMENT ON TABLE user_tiers IS 'Tracks user tier subscriptions and access levels';
COMMENT ON TABLE tier_usage IS 'Monitors resource usage against tier limits for rate limiting and quota management';
COMMENT ON TABLE hardware_devices IS 'Manages IoT devices and sensors (Layer 2 - Hardware Platform)';
COMMENT ON TABLE device_templates IS 'Stores device templates and SDK information for hardware development';
COMMENT ON TABLE gateways IS 'Manages gateway devices for protocol translation and device communication';
COMMENT ON TABLE certified_devices IS 'Marketplace catalog of certified hardware devices';
COMMENT ON TABLE marketplace_orders IS 'Tracks hardware device purchases and orders';
COMMENT ON TABLE workflows IS 'Visual workflow definitions and automation (Layer 3 - Workflow Platform)';
COMMENT ON TABLE workflow_executions IS 'Tracks workflow execution history and results';
COMMENT ON TABLE work_orders IS 'CMMS work order management system';
COMMENT ON TABLE maintenance_schedules IS 'Preventive maintenance scheduling and task management';
COMMENT ON TABLE maintenance_executions IS 'Tracks maintenance task execution and completion';
COMMENT ON TABLE reports IS 'Generated reports and analytics outputs';
COMMENT ON TABLE automations IS 'Building automation rules and triggers';
COMMENT ON TABLE automation_status IS 'Tracks automation execution status and metrics';
COMMENT ON TABLE analytics_results IS 'Stores analytics computation results and insights';
COMMENT ON TABLE predictive_insights IS 'AI/ML predictive maintenance and optimization insights';
COMMENT ON TABLE dashboards IS 'User dashboard configurations and layouts';
COMMENT ON TABLE integrations IS 'Enterprise system integrations and connectors';
COMMENT ON TABLE integration_status IS 'Tracks integration sync status and health';
