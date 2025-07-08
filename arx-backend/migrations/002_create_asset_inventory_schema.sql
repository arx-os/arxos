-- Migration: Create Asset Inventory Schema
-- This migration adds comprehensive asset inventory tracking capabilities

-- Building Assets table
CREATE TABLE building_assets (
    id VARCHAR(255) PRIMARY KEY,
    building_id BIGINT UNSIGNED NOT NULL,
    floor_id BIGINT UNSIGNED,
    room_id VARCHAR(255),
    symbol_id VARCHAR(255) NOT NULL,
    asset_type VARCHAR(255) NOT NULL,
    system VARCHAR(255) NOT NULL,
    subsystem VARCHAR(255),
    
    -- Location details
    location_floor VARCHAR(255),
    location_room VARCHAR(255),
    location_area VARCHAR(255),
    location_x DOUBLE,
    location_y DOUBLE,
    location_coordinates VARCHAR(255),
    
    -- Specifications and metadata
    specifications JSON,
    metadata JSON,
    
    -- Calculated fields
    age INT,
    efficiency_rating VARCHAR(255),
    lifecycle_stage VARCHAR(255),
    
    -- Valuation
    estimated_value DOUBLE,
    replacement_cost DOUBLE,
    
    -- Status and tracking
    status VARCHAR(255) DEFAULT 'active',
    created_by BIGINT UNSIGNED NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP NULL,
    
    INDEX idx_building_assets_building_id (building_id),
    INDEX idx_building_assets_floor_id (floor_id),
    INDEX idx_building_assets_room_id (room_id),
    INDEX idx_building_assets_symbol_id (symbol_id),
    INDEX idx_building_assets_asset_type (asset_type),
    INDEX idx_building_assets_system (system),
    INDEX idx_building_assets_status (status),
    INDEX idx_building_assets_created_by (created_by),
    INDEX idx_building_assets_deleted_at (deleted_at),
    
    FOREIGN KEY (building_id) REFERENCES buildings(id) ON DELETE CASCADE,
    FOREIGN KEY (floor_id) REFERENCES floors(id) ON DELETE SET NULL,
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE CASCADE
);

-- Asset History table
CREATE TABLE asset_history (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    asset_id VARCHAR(255) NOT NULL,
    event_type VARCHAR(255) NOT NULL,
    event_date TIMESTAMP NOT NULL,
    description TEXT,
    cost DOUBLE,
    contractor VARCHAR(255),
    warranty VARCHAR(255),
    documents JSON,
    created_by BIGINT UNSIGNED NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_asset_history_asset_id (asset_id),
    INDEX idx_asset_history_event_type (event_type),
    INDEX idx_asset_history_event_date (event_date),
    INDEX idx_asset_history_created_by (created_by),
    
    FOREIGN KEY (asset_id) REFERENCES building_assets(id) ON DELETE CASCADE,
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE CASCADE
);

-- Asset Maintenance table
CREATE TABLE asset_maintenance (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    asset_id VARCHAR(255) NOT NULL,
    maintenance_type VARCHAR(255) NOT NULL,
    status VARCHAR(255) NOT NULL,
    scheduled_date TIMESTAMP NOT NULL,
    completed_date TIMESTAMP NULL,
    description TEXT,
    cost DOUBLE,
    technician VARCHAR(255),
    parts JSON,
    notes TEXT,
    created_by BIGINT UNSIGNED NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_asset_maintenance_asset_id (asset_id),
    INDEX idx_asset_maintenance_maintenance_type (maintenance_type),
    INDEX idx_asset_maintenance_status (status),
    INDEX idx_asset_maintenance_scheduled_date (scheduled_date),
    INDEX idx_asset_maintenance_created_by (created_by),
    
    FOREIGN KEY (asset_id) REFERENCES building_assets(id) ON DELETE CASCADE,
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE CASCADE
);

-- Asset Valuation table
CREATE TABLE asset_valuations (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    asset_id VARCHAR(255) NOT NULL,
    valuation_date TIMESTAMP NOT NULL,
    valuation_type VARCHAR(255) NOT NULL,
    value DOUBLE NOT NULL,
    currency VARCHAR(10) DEFAULT 'USD',
    valuation_method VARCHAR(255),
    notes TEXT,
    created_by BIGINT UNSIGNED NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_asset_valuations_asset_id (asset_id),
    INDEX idx_asset_valuations_valuation_type (valuation_type),
    INDEX idx_asset_valuations_valuation_date (valuation_date),
    INDEX idx_asset_valuations_created_by (created_by),
    
    FOREIGN KEY (asset_id) REFERENCES building_assets(id) ON DELETE CASCADE,
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE CASCADE
);

-- Building Asset Inventory table
CREATE TABLE building_asset_inventories (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    building_id BIGINT UNSIGNED NOT NULL,
    inventory_date TIMESTAMP NOT NULL,
    total_assets INT NOT NULL,
    systems JSON,
    export_format VARCHAR(50),
    export_data JSON,
    created_by BIGINT UNSIGNED NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_building_asset_inventories_building_id (building_id),
    INDEX idx_building_asset_inventories_inventory_date (inventory_date),
    INDEX idx_building_asset_inventories_created_by (created_by),
    
    FOREIGN KEY (building_id) REFERENCES buildings(id) ON DELETE CASCADE,
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE CASCADE
);

-- Industry Benchmarks table
CREATE TABLE industry_benchmarks (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    equipment_type VARCHAR(255) NOT NULL,
    system VARCHAR(255) NOT NULL,
    metric VARCHAR(255) NOT NULL,
    value DOUBLE NOT NULL,
    unit VARCHAR(100),
    source VARCHAR(255),
    year INT,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_industry_benchmarks_equipment_type (equipment_type),
    INDEX idx_industry_benchmarks_system (system),
    INDEX idx_industry_benchmarks_metric (metric),
    INDEX idx_industry_benchmarks_source (source),
    INDEX idx_industry_benchmarks_year (year)
);

-- Insert some initial industry benchmarks
INSERT INTO industry_benchmarks (equipment_type, system, metric, value, unit, source, year, description) VALUES
('HVAC', 'HVAC', 'efficiency', 85.0, 'percent', 'ASHRAE', 2023, 'Typical HVAC system efficiency rating'),
('Lighting', 'Electrical', 'efficiency', 90.0, 'percent', 'IES', 2023, 'LED lighting efficiency'),
('Pump', 'Plumbing', 'efficiency', 75.0, 'percent', 'Hydraulic Institute', 2023, 'Centrifugal pump efficiency'),
('Motor', 'Mechanical', 'efficiency', 92.0, 'percent', 'NEMA', 2023, 'Premium efficiency motor'),
('Chiller', 'HVAC', 'efficiency', 0.6, 'kW/ton', 'ASHRAE', 2023, 'Water-cooled chiller efficiency'),
('Boiler', 'HVAC', 'efficiency', 88.0, 'percent', 'ASHRAE', 2023, 'Gas-fired boiler efficiency'),
('Fan', 'HVAC', 'efficiency', 70.0, 'percent', 'AMCA', 2023, 'Air handling unit fan efficiency'),
('Transformer', 'Electrical', 'efficiency', 98.5, 'percent', 'IEEE', 2023, 'Distribution transformer efficiency');

-- Data Vendor API tables
CREATE TABLE data_vendor_api_keys (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    `key` VARCHAR(255) UNIQUE NOT NULL,
    vendor_name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL,
    access_level VARCHAR(50) DEFAULT 'basic',
    rate_limit INT DEFAULT 1000,
    is_active BOOLEAN DEFAULT TRUE,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_data_vendor_api_keys_key (`key`),
    INDEX idx_data_vendor_api_keys_vendor_name (vendor_name),
    INDEX idx_data_vendor_api_keys_access_level (access_level),
    INDEX idx_data_vendor_api_keys_is_active (is_active),
    INDEX idx_data_vendor_api_keys_expires_at (expires_at)
);

CREATE TABLE data_vendor_requests (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    api_key_id BIGINT UNSIGNED NOT NULL,
    request_type VARCHAR(255) NOT NULL,
    building_id BIGINT UNSIGNED,
    format VARCHAR(50) DEFAULT 'json',
    filters TEXT,
    ip_address VARCHAR(45),
    user_agent TEXT,
    status VARCHAR(50) DEFAULT 'completed',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_data_vendor_requests_api_key_id (api_key_id),
    INDEX idx_data_vendor_requests_request_type (request_type),
    INDEX idx_data_vendor_requests_building_id (building_id),
    INDEX idx_data_vendor_requests_created_at (created_at),
    
    FOREIGN KEY (api_key_id) REFERENCES data_vendor_api_keys(id) ON DELETE CASCADE,
    FOREIGN KEY (building_id) REFERENCES buildings(id) ON DELETE SET NULL
); 