-- Webhook subscriptions table
CREATE TABLE IF NOT EXISTS webhooks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    url TEXT NOT NULL,
    secret VARCHAR(255), -- For HMAC signature verification
    active BOOLEAN DEFAULT true,
    
    -- Event filtering
    event_types TEXT[], -- Array of event types to subscribe to
    path_pattern TEXT, -- Optional path filter
    object_type VARCHAR(50), -- Optional object type filter
    building_id UUID REFERENCES buildings(id) ON DELETE CASCADE,
    
    -- Delivery configuration
    retry_count INTEGER DEFAULT 3,
    timeout_seconds INTEGER DEFAULT 30,
    
    -- Headers to include in webhook calls
    custom_headers JSONB DEFAULT '{}',
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_triggered_at TIMESTAMP,
    
    -- Statistics
    total_deliveries INTEGER DEFAULT 0,
    successful_deliveries INTEGER DEFAULT 0,
    failed_deliveries INTEGER DEFAULT 0
);

-- Index for active webhooks
CREATE INDEX idx_webhooks_active ON webhooks(active) WHERE active = true;

-- Webhook delivery log
CREATE TABLE IF NOT EXISTS webhook_deliveries (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    webhook_id UUID NOT NULL REFERENCES webhooks(id) ON DELETE CASCADE,
    event_id UUID NOT NULL,
    
    -- Delivery details
    url TEXT NOT NULL,
    method VARCHAR(10) DEFAULT 'POST',
    headers JSONB,
    payload JSONB NOT NULL,
    
    -- Response details
    status_code INTEGER,
    response_body TEXT,
    response_headers JSONB,
    
    -- Delivery status
    delivered BOOLEAN DEFAULT false,
    error_message TEXT,
    attempt_number INTEGER DEFAULT 1,
    
    -- Timing
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    delivered_at TIMESTAMP,
    duration_ms INTEGER
);

-- Index for finding pending deliveries
CREATE INDEX idx_webhook_deliveries_pending 
    ON webhook_deliveries(delivered, created_at) 
    WHERE delivered = false;

-- Index for webhook history
CREATE INDEX idx_webhook_deliveries_webhook 
    ON webhook_deliveries(webhook_id, created_at DESC);

-- Function to update webhook statistics
CREATE OR REPLACE FUNCTION update_webhook_stats()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.delivered = true AND (OLD.delivered = false OR OLD.delivered IS NULL) THEN
        UPDATE webhooks 
        SET successful_deliveries = successful_deliveries + 1,
            total_deliveries = total_deliveries + 1,
            last_triggered_at = NEW.delivered_at
        WHERE id = NEW.webhook_id;
    ELSIF NEW.delivered = false AND NEW.attempt_number >= 3 THEN
        UPDATE webhooks 
        SET failed_deliveries = failed_deliveries + 1,
            total_deliveries = total_deliveries + 1
        WHERE id = NEW.webhook_id;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to update webhook stats
CREATE TRIGGER webhook_delivery_stats
    AFTER UPDATE OF delivered ON webhook_deliveries
    FOR EACH ROW
    EXECUTE FUNCTION update_webhook_stats();