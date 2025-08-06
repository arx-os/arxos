-- CMMS Service Database Initialization
-- This script creates the necessary tables for the CMMS service

-- Create CMMS connections table
CREATE TABLE IF NOT EXISTS cmms_connections (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    type VARCHAR(50) NOT NULL, -- upkeep, fiix, custom, etc.
    base_url VARCHAR(500) NOT NULL,
    api_key VARCHAR(255),
    username VARCHAR(255),
    password VARCHAR(255),
    oauth2_client_id VARCHAR(255),
    oauth2_secret VARCHAR(255),
    oauth2_token_url VARCHAR(255),
    oauth2_scope VARCHAR(255),
    sync_interval_min INTEGER DEFAULT 60,
    is_active BOOLEAN DEFAULT true,
    last_sync TIMESTAMP,
    last_sync_status VARCHAR(50),
    last_sync_error TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create CMMS field mappings table
CREATE TABLE IF NOT EXISTS cmms_mappings (
    id SERIAL PRIMARY KEY,
    cmms_connection_id INTEGER REFERENCES cmms_connections(id) ON DELETE CASCADE,
    arxos_field VARCHAR(255) NOT NULL,
    cmms_field VARCHAR(255) NOT NULL,
    data_type VARCHAR(50) NOT NULL, -- string, number, date, boolean
    is_required BOOLEAN DEFAULT false,
    default_value TEXT,
    transform_rule TEXT, -- JSON transformation rules
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(cmms_connection_id, arxos_field)
);

-- Create maintenance schedules table
CREATE TABLE IF NOT EXISTS maintenance_schedules (
    id SERIAL PRIMARY KEY,
    asset_id INTEGER,
    cmms_connection_id INTEGER REFERENCES cmms_connections(id) ON DELETE CASCADE,
    cmms_asset_id VARCHAR(255) NOT NULL,
    schedule_type VARCHAR(50) NOT NULL, -- preventive, predictive, corrective
    frequency VARCHAR(50) NOT NULL, -- daily, weekly, monthly, yearly
    interval INTEGER NOT NULL, -- number of frequency units
    description TEXT,
    instructions TEXT,
    estimated_hours DECIMAL(10,2),
    priority VARCHAR(50) DEFAULT 'medium', -- low, medium, high, critical
    is_active BOOLEAN DEFAULT true,
    next_due_date TIMESTAMP NOT NULL,
    last_completed TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(cmms_connection_id, cmms_asset_id, schedule_type)
);

-- Create work orders table
CREATE TABLE IF NOT EXISTS work_orders (
    id SERIAL PRIMARY KEY,
    asset_id INTEGER,
    cmms_connection_id INTEGER REFERENCES cmms_connections(id) ON DELETE CASCADE,
    cmms_work_order_id VARCHAR(255) NOT NULL,
    work_order_number VARCHAR(255) NOT NULL,
    type VARCHAR(50) NOT NULL, -- preventive, corrective, emergency
    status VARCHAR(50) NOT NULL, -- open, in_progress, completed, cancelled
    priority VARCHAR(50) DEFAULT 'medium',
    description TEXT,
    instructions TEXT,
    assigned_to VARCHAR(255),
    estimated_hours DECIMAL(10,2),
    actual_hours DECIMAL(10,2),
    cost DECIMAL(12,2),
    parts_used TEXT, -- JSON array
    created_date TIMESTAMP NOT NULL,
    scheduled_date TIMESTAMP NOT NULL,
    started_date TIMESTAMP,
    completed_date TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(cmms_connection_id, cmms_work_order_id)
);

-- Create equipment specifications table
CREATE TABLE IF NOT EXISTS equipment_specifications (
    id SERIAL PRIMARY KEY,
    asset_id INTEGER,
    cmms_connection_id INTEGER REFERENCES cmms_connections(id) ON DELETE CASCADE,
    cmms_asset_id VARCHAR(255) NOT NULL,
    spec_type VARCHAR(50) NOT NULL, -- technical, operational, maintenance
    spec_name VARCHAR(255) NOT NULL,
    spec_value TEXT NOT NULL,
    unit VARCHAR(50),
    min_value DECIMAL(15,5),
    max_value DECIMAL(15,5),
    is_critical BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(cmms_connection_id, cmms_asset_id, spec_type, spec_name)
);

-- Create CMMS sync logs table
CREATE TABLE IF NOT EXISTS cmms_sync_logs (
    id SERIAL PRIMARY KEY,
    cmms_connection_id INTEGER REFERENCES cmms_connections(id) ON DELETE CASCADE,
    sync_type VARCHAR(50) NOT NULL, -- schedules, work_orders, specs
    status VARCHAR(50) NOT NULL, -- success, partial, failed
    records_processed INTEGER DEFAULT 0,
    records_created INTEGER DEFAULT 0,
    records_updated INTEGER DEFAULT 0,
    records_failed INTEGER DEFAULT 0,
    error_details TEXT,
    started_at TIMESTAMP NOT NULL,
    completed_at TIMESTAMP NOT NULL
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_maintenance_schedules_asset_id ON maintenance_schedules(asset_id);
CREATE INDEX IF NOT EXISTS idx_maintenance_schedules_next_due ON maintenance_schedules(next_due_date);
CREATE INDEX IF NOT EXISTS idx_maintenance_schedules_connection ON maintenance_schedules(cmms_connection_id);
CREATE INDEX IF NOT EXISTS idx_work_orders_asset_id ON work_orders(asset_id);
CREATE INDEX IF NOT EXISTS idx_work_orders_status ON work_orders(status);
CREATE INDEX IF NOT EXISTS idx_work_orders_scheduled_date ON work_orders(scheduled_date);
CREATE INDEX IF NOT EXISTS idx_work_orders_connection ON work_orders(cmms_connection_id);
CREATE INDEX IF NOT EXISTS idx_equipment_specs_asset_id ON equipment_specifications(asset_id);
CREATE INDEX IF NOT EXISTS idx_equipment_specs_connection ON equipment_specifications(cmms_connection_id);
CREATE INDEX IF NOT EXISTS idx_cmms_sync_logs_connection ON cmms_sync_logs(cmms_connection_id);
CREATE INDEX IF NOT EXISTS idx_cmms_sync_logs_started ON cmms_sync_logs(started_at);
CREATE INDEX IF NOT EXISTS idx_cmms_mappings_connection ON cmms_mappings(cmms_connection_id);

-- Insert sample data for testing
INSERT INTO cmms_connections (name, type, base_url, api_key, sync_interval_min, is_active) VALUES
('Upkeep Test Connection', 'upkeep', 'https://api.upkeep.com', 'test-api-key', 60, true),
('Fiix Test Connection', 'fiix', 'https://api.fiix.com', 'test-api-key', 120, true)
ON CONFLICT DO NOTHING;

-- Insert sample field mappings
INSERT INTO cmms_mappings (cmms_connection_id, arxos_field, cmms_field, data_type, is_required) VALUES
(1, 'asset_id', 'equipment_id', 'string', true),
(1, 'schedule_type', 'maintenance_type', 'string', true),
(1, 'frequency', 'interval_type', 'string', true),
(1, 'interval', 'interval_value', 'number', true),
(2, 'asset_id', 'asset_id', 'string', true),
(2, 'schedule_type', 'work_type', 'string', true)
ON CONFLICT DO NOTHING; 