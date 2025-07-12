-- Maintenance Workflow Schema
-- Migration: 004_create_maintenance_workflow_schema.sql

-- Maintenance Tasks table
CREATE TABLE IF NOT EXISTS maintenance_tasks (
    id SERIAL PRIMARY KEY,
    asset_id INTEGER REFERENCES assets(id) ON DELETE CASCADE,
    schedule_id INTEGER REFERENCES maintenance_schedules(id) ON DELETE SET NULL,
    task_type VARCHAR(50) NOT NULL, -- preventive, corrective, emergency, inspection
    status VARCHAR(50) NOT NULL, -- pending, in_progress, completed, cancelled, overdue
    priority VARCHAR(50) DEFAULT 'medium', -- low, medium, high, critical
    title VARCHAR(255) NOT NULL,
    description TEXT,
    instructions TEXT,
    assigned_to VARCHAR(255),
    estimated_hours DECIMAL(10,2),
    actual_hours DECIMAL(10,2),
    estimated_cost DECIMAL(12,2),
    actual_cost DECIMAL(12,2),
    parts_used TEXT, -- JSON array
    notes TEXT,
    scheduled_date TIMESTAMP NOT NULL,
    started_date TIMESTAMP,
    completed_date TIMESTAMP,
    due_date TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Asset Lifecycle table
CREATE TABLE IF NOT EXISTS asset_lifecycles (
    id SERIAL PRIMARY KEY,
    asset_id INTEGER REFERENCES assets(id) ON DELETE CASCADE UNIQUE,
    install_date TIMESTAMP NOT NULL,
    expected_life INTEGER NOT NULL, -- in months
    end_of_life_date TIMESTAMP NOT NULL,
    replacement_date TIMESTAMP,
    status VARCHAR(50) DEFAULT 'active', -- active, maintenance, replacement_planned, end_of_life, retired
    condition VARCHAR(50) DEFAULT 'good', -- excellent, good, fair, poor, critical
    risk_level VARCHAR(50) DEFAULT 'low', -- low, medium, high, critical
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Warranties table
CREATE TABLE IF NOT EXISTS warranties (
    id SERIAL PRIMARY KEY,
    asset_id INTEGER REFERENCES assets(id) ON DELETE CASCADE,
    warranty_type VARCHAR(50) NOT NULL, -- manufacturer, extended, service
    provider VARCHAR(255) NOT NULL,
    contract_number VARCHAR(255),
    start_date TIMESTAMP NOT NULL,
    end_date TIMESTAMP NOT NULL,
    coverage VARCHAR(50) NOT NULL, -- parts, labor, both
    terms TEXT, -- JSON terms and conditions
    contact_info TEXT, -- JSON contact details
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Replacement Plans table
CREATE TABLE IF NOT EXISTS replacement_plans (
    id SERIAL PRIMARY KEY,
    asset_id INTEGER REFERENCES assets(id) ON DELETE CASCADE,
    plan_type VARCHAR(50) NOT NULL, -- scheduled, emergency, upgrade
    reason TEXT NOT NULL,
    priority VARCHAR(50) DEFAULT 'medium', -- low, medium, high, critical
    estimated_cost DECIMAL(12,2),
    budgeted_amount DECIMAL(12,2),
    planned_date TIMESTAMP NOT NULL,
    actual_date TIMESTAMP,
    status VARCHAR(50) DEFAULT 'planned', -- planned, approved, in_progress, completed, cancelled
    replacement_asset_id INTEGER REFERENCES assets(id) ON DELETE SET NULL,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Maintenance Costs table
CREATE TABLE IF NOT EXISTS maintenance_costs (
    id SERIAL PRIMARY KEY,
    asset_id INTEGER REFERENCES assets(id) ON DELETE CASCADE,
    task_id INTEGER REFERENCES maintenance_tasks(id) ON DELETE SET NULL,
    cost_type VARCHAR(50) NOT NULL, -- labor, parts, materials, external
    description TEXT NOT NULL,
    amount DECIMAL(12,2) NOT NULL,
    currency VARCHAR(10) DEFAULT 'USD', -- USD, EUR, etc.
    date TIMESTAMP NOT NULL,
    invoice_number VARCHAR(255),
    vendor VARCHAR(255),
    approved_by VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Maintenance Notifications table
CREATE TABLE IF NOT EXISTS maintenance_notifications (
    id SERIAL PRIMARY KEY,
    asset_id INTEGER REFERENCES assets(id) ON DELETE CASCADE,
    task_id INTEGER REFERENCES maintenance_tasks(id) ON DELETE SET NULL,
    notification_type VARCHAR(50) NOT NULL, -- due_date, overdue, completion, warranty_expiry, eol
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    priority VARCHAR(50) DEFAULT 'medium', -- low, medium, high, critical
    is_read BOOLEAN DEFAULT false,
    read_by VARCHAR(255),
    read_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX idx_maintenance_tasks_asset_id ON maintenance_tasks(asset_id);
CREATE INDEX idx_maintenance_tasks_status ON maintenance_tasks(status);
CREATE INDEX idx_maintenance_tasks_due_date ON maintenance_tasks(due_date);
CREATE INDEX idx_maintenance_tasks_assigned_to ON maintenance_tasks(assigned_to);
CREATE INDEX idx_asset_lifecycles_status ON asset_lifecycles(status);
CREATE INDEX idx_asset_lifecycles_end_of_life ON asset_lifecycles(end_of_life_date);
CREATE INDEX idx_asset_lifecycles_condition ON asset_lifecycles(condition);
CREATE INDEX idx_warranties_asset_id ON warranties(asset_id);
CREATE INDEX idx_warranties_end_date ON warranties(end_date);
CREATE INDEX idx_warranties_is_active ON warranties(is_active);
CREATE INDEX idx_replacement_plans_asset_id ON replacement_plans(asset_id);
CREATE INDEX idx_replacement_plans_status ON replacement_plans(status);
CREATE INDEX idx_replacement_plans_planned_date ON replacement_plans(planned_date);
CREATE INDEX idx_maintenance_costs_asset_id ON maintenance_costs(asset_id);
CREATE INDEX idx_maintenance_costs_date ON maintenance_costs(date);
CREATE INDEX idx_maintenance_notifications_asset_id ON maintenance_notifications(asset_id);
CREATE INDEX idx_maintenance_notifications_is_read ON maintenance_notifications(is_read);
CREATE INDEX idx_maintenance_notifications_created_at ON maintenance_notifications(created_at);

-- Add maintenance-related columns to assets table
ALTER TABLE assets ADD COLUMN IF NOT EXISTS maintenance_priority VARCHAR(50) DEFAULT 'medium';
ALTER TABLE assets ADD COLUMN IF NOT EXISTS last_maintenance_date TIMESTAMP;
ALTER TABLE assets ADD COLUMN IF NOT EXISTS next_maintenance_date TIMESTAMP;
ALTER TABLE assets ADD COLUMN IF NOT EXISTS total_maintenance_cost DECIMAL(12,2) DEFAULT 0;
ALTER TABLE assets ADD COLUMN IF NOT EXISTS maintenance_notes TEXT; 