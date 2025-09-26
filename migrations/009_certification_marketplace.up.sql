-- Create certification requests table
CREATE TABLE IF NOT EXISTS certification_requests (
    id VARCHAR(255) PRIMARY KEY,
    device_id VARCHAR(255) NOT NULL,
    device_name VARCHAR(255) NOT NULL,
    device_type VARCHAR(100) NOT NULL,
    manufacturer VARCHAR(255) NOT NULL,
    model VARCHAR(255) NOT NULL,
    specifications JSONB,
    documentation JSONB,
    test_results JSONB,
    compliance_docs JSONB,
    certification_level VARCHAR(50) DEFAULT 'Basic',
    requested_by VARCHAR(255) NOT NULL,
    notes TEXT,
    status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create certification standards table
CREATE TABLE IF NOT EXISTS certification_standards (
    id VARCHAR(255) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    version VARCHAR(50) NOT NULL,
    description TEXT,
    requirements JSONB,
    test_suite JSONB,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create certification results table
CREATE TABLE IF NOT EXISTS certification_results (
    id VARCHAR(255) PRIMARY KEY,
    device_id VARCHAR(255) NOT NULL,
    certification_request_id VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL,
    certification_level VARCHAR(50) NOT NULL,
    certification_number VARCHAR(255) NOT NULL,
    valid_from TIMESTAMP WITH TIME ZONE NOT NULL,
    valid_until TIMESTAMP WITH TIME ZONE NOT NULL,
    test_results JSONB,
    compliance_score DECIMAL(3,2),
    issued_by VARCHAR(255) NOT NULL,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    FOREIGN KEY (certification_request_id) REFERENCES certification_requests(id)
);

-- Create marketplace vendors table
CREATE TABLE IF NOT EXISTS marketplace_vendors (
    id VARCHAR(255) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL,
    website VARCHAR(255),
    description TEXT,
    contact_info JSONB,
    status VARCHAR(50) DEFAULT 'active',
    rating DECIMAL(2,1) DEFAULT 0.0,
    total_sales INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create marketplace reviews table
CREATE TABLE IF NOT EXISTS marketplace_reviews (
    id VARCHAR(255) PRIMARY KEY,
    device_id VARCHAR(255) NOT NULL,
    user_id VARCHAR(255) NOT NULL,
    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
    title VARCHAR(255),
    review_text TEXT,
    helpful_count INTEGER DEFAULT 0,
    verified_purchase BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    FOREIGN KEY (device_id) REFERENCES certified_devices(id)
);

-- Create marketplace analytics table
CREATE TABLE IF NOT EXISTS marketplace_analytics (
    id VARCHAR(255) PRIMARY KEY,
    device_id VARCHAR(255) NOT NULL,
    event_type VARCHAR(100) NOT NULL,
    event_data JSONB,
    user_id VARCHAR(255),
    session_id VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    FOREIGN KEY (device_id) REFERENCES certified_devices(id)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_certification_requests_status ON certification_requests(status);
CREATE INDEX IF NOT EXISTS idx_certification_requests_device_type ON certification_requests(device_type);
CREATE INDEX IF NOT EXISTS idx_certification_requests_requested_by ON certification_requests(requested_by);

CREATE INDEX IF NOT EXISTS idx_certification_standards_name ON certification_standards(name);
CREATE INDEX IF NOT EXISTS idx_certification_standards_is_active ON certification_standards(is_active);

CREATE INDEX IF NOT EXISTS idx_certification_results_device_id ON certification_results(device_id);
CREATE INDEX IF NOT EXISTS idx_certification_results_status ON certification_results(status);
CREATE INDEX IF NOT EXISTS idx_certification_results_valid_until ON certification_results(valid_until);

CREATE INDEX IF NOT EXISTS idx_marketplace_vendors_status ON marketplace_vendors(status);
CREATE INDEX IF NOT EXISTS idx_marketplace_vendors_rating ON marketplace_vendors(rating);

CREATE INDEX IF NOT EXISTS idx_marketplace_reviews_device_id ON marketplace_reviews(device_id);
CREATE INDEX IF NOT EXISTS idx_marketplace_reviews_user_id ON marketplace_reviews(user_id);
CREATE INDEX IF NOT EXISTS idx_marketplace_reviews_rating ON marketplace_reviews(rating);

CREATE INDEX IF NOT EXISTS idx_marketplace_analytics_device_id ON marketplace_analytics(device_id);
CREATE INDEX IF NOT EXISTS idx_marketplace_analytics_event_type ON marketplace_analytics(event_type);
CREATE INDEX IF NOT EXISTS idx_marketplace_analytics_created_at ON marketplace_analytics(created_at);

-- Create updated_at triggers
CREATE TRIGGER update_certification_requests_updated_at 
    BEFORE UPDATE ON certification_requests 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_certification_standards_updated_at 
    BEFORE UPDATE ON certification_standards 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_certification_results_updated_at 
    BEFORE UPDATE ON certification_results 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_marketplace_vendors_updated_at 
    BEFORE UPDATE ON marketplace_vendors 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_marketplace_reviews_updated_at 
    BEFORE UPDATE ON marketplace_reviews 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert default certification standards
INSERT INTO certification_standards (id, name, version, description, requirements, test_suite, is_active) VALUES
('arx_basic', 'ArxOS Basic Certification', '1.0', 'Basic certification for ArxOS compatibility', 
 '{"safety": true, "performance": true, "compatibility": true}', 
 '["safety_tests", "basic_performance", "compatibility_checks"]', true),
 
('arx_standard', 'ArxOS Standard Certification', '1.0', 'Standard certification with enhanced testing', 
 '{"safety": true, "performance": true, "compatibility": true, "security": true}', 
 '["safety_tests", "performance_tests", "security_tests", "compatibility_checks"]', true),
 
('arx_premium', 'ArxOS Premium Certification', '1.0', 'Premium certification with comprehensive testing', 
 '{"safety": true, "performance": true, "compatibility": true, "security": true, "reliability": true}', 
 '["safety_tests", "performance_tests", "security_tests", "compatibility_checks", "reliability_tests"]', true);

-- Insert default marketplace vendor (ArxOS)
INSERT INTO marketplace_vendors (id, name, email, website, description, contact_info, status, rating) VALUES
('arxos_official', 'ArxOS Official', 'marketplace@arxos.dev', 'https://arxos.dev', 
 'Official ArxOS marketplace vendor', 
 '{"phone": "+1-555-ARXOS", "address": "ArxOS HQ", "support_email": "support@arxos.dev"}', 
 'active', 5.0);

-- Add comments
COMMENT ON TABLE certification_requests IS 'Manages device certification requests and submissions';
COMMENT ON TABLE certification_standards IS 'Defines certification standards and requirements';
COMMENT ON TABLE certification_results IS 'Stores certification results and validity periods';
COMMENT ON TABLE marketplace_vendors IS 'Manages marketplace vendors and their information';
COMMENT ON TABLE marketplace_reviews IS 'Stores device reviews and ratings from users';
COMMENT ON TABLE marketplace_analytics IS 'Tracks marketplace analytics and user behavior';
