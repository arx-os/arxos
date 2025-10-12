-- Migration 007: Ecosystem Tiers and Three-Tier Architecture (ROLLBACK)
-- This migration removes the three-tier ecosystem architecture tables and data

-- Drop views first
DROP VIEW IF EXISTS user_usage_summary;
DROP VIEW IF EXISTS user_tier_summary;

-- Drop triggers
DROP TRIGGER IF EXISTS update_integration_status_updated_at ON integration_status;
DROP TRIGGER IF EXISTS update_integrations_updated_at ON integrations;
DROP TRIGGER IF EXISTS update_dashboards_updated_at ON dashboards;
DROP TRIGGER IF EXISTS update_automation_status_updated_at ON automation_status;
DROP TRIGGER IF EXISTS update_automations_updated_at ON automations;
DROP TRIGGER IF EXISTS update_maintenance_schedules_updated_at ON maintenance_schedules;
DROP TRIGGER IF EXISTS update_work_orders_updated_at ON work_orders;
DROP TRIGGER IF EXISTS update_workflows_updated_at ON workflows;
DROP TRIGGER IF EXISTS update_marketplace_orders_updated_at ON marketplace_orders;
DROP TRIGGER IF EXISTS update_gateways_updated_at ON gateways;
DROP TRIGGER IF EXISTS update_device_templates_updated_at ON device_templates;
DROP TRIGGER IF EXISTS update_hardware_devices_updated_at ON hardware_devices;
DROP TRIGGER IF EXISTS update_tier_usage_updated_at ON tier_usage;
DROP TRIGGER IF EXISTS update_user_tiers_updated_at ON user_tiers;
DROP TRIGGER IF EXISTS update_ecosystem_tiers_updated_at ON ecosystem_tiers;

-- Drop function
DROP FUNCTION IF EXISTS update_updated_at_column();

-- Drop tables in reverse order (due to foreign key constraints)
DROP TABLE IF EXISTS integration_status;
DROP TABLE IF EXISTS integrations;
DROP TABLE IF EXISTS dashboards;
DROP TABLE IF EXISTS predictive_insights;
DROP TABLE IF EXISTS analytics_results;
DROP TABLE IF EXISTS automation_status;
DROP TABLE IF EXISTS automations;
DROP TABLE IF EXISTS reports;
DROP TABLE IF EXISTS maintenance_executions;
DROP TABLE IF EXISTS maintenance_schedule_equipment;
DROP TABLE IF EXISTS maintenance_schedules;
DROP TABLE IF EXISTS work_orders;
DROP TABLE IF EXISTS workflow_executions;
DROP TABLE IF EXISTS workflows;
DROP TABLE IF EXISTS marketplace_orders;
DROP TABLE IF EXISTS certified_devices;
DROP TABLE IF EXISTS gateways;
DROP TABLE IF EXISTS device_templates;
DROP TABLE IF EXISTS hardware_devices;
DROP TABLE IF EXISTS tier_usage;
DROP TABLE IF EXISTS user_tiers;
DROP TABLE IF EXISTS ecosystem_tiers;

-- Remove tier columns from existing tables
ALTER TABLE equipment DROP COLUMN IF EXISTS tier;
ALTER TABLE buildings DROP COLUMN IF EXISTS tier;
