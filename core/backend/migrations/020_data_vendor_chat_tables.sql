-- Migration: Add Data Vendor Chat Tables
-- Description: Creates tables for data vendor chat sessions and messages
-- Version: 020
-- Date: 2024-12-19

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create data vendor chat sessions table
CREATE TABLE data_vendor_chat_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    vendor_id BIGINT NOT NULL REFERENCES data_vendor_api_keys(id) ON DELETE CASCADE,
    session_id VARCHAR(255) UNIQUE NOT NULL,
    context JSONB DEFAULT '{}',
    history JSONB DEFAULT '[]',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,

    -- Indexes for performance
    INDEX idx_chat_sessions_vendor_id (vendor_id),
    INDEX idx_chat_sessions_session_id (session_id),
    INDEX idx_chat_sessions_expires_at (expires_at),
    INDEX idx_chat_sessions_active (is_active)
);

-- Create data vendor chat messages table
CREATE TABLE data_vendor_chat_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id VARCHAR(255) NOT NULL REFERENCES data_vendor_chat_sessions(session_id) ON DELETE CASCADE,
    role VARCHAR(50) NOT NULL CHECK (role IN ('user', 'assistant')),
    message TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),

    -- Indexes for performance
    INDEX idx_chat_messages_session_id (session_id),
    INDEX idx_chat_messages_role (role),
    INDEX idx_chat_messages_created_at (created_at)
);

-- Create data vendor query analytics table
CREATE TABLE data_vendor_query_analytics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    vendor_id BIGINT NOT NULL REFERENCES data_vendor_api_keys(id) ON DELETE CASCADE,
    query_type VARCHAR(100) NOT NULL,
    query_text TEXT,
    result_count INTEGER,
    processing_time_ms INTEGER,
    confidence_score DECIMAL(3,2),
    nlp_confidence DECIMAL(3,2),
    error_message TEXT,
    created_at TIMESTAMP DEFAULT NOW(),

    -- Indexes for performance
    INDEX idx_query_analytics_vendor_id (vendor_id),
    INDEX idx_query_analytics_query_type (query_type),
    INDEX idx_query_analytics_created_at (created_at),
    INDEX idx_query_analytics_confidence (confidence_score)
);

-- Create data vendor query templates table
CREATE TABLE data_vendor_query_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    vendor_id BIGINT NOT NULL REFERENCES data_vendor_api_keys(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    query_structure JSONB NOT NULL,
    is_public BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    -- Indexes for performance
    INDEX idx_query_templates_vendor_id (vendor_id),
    INDEX idx_query_templates_public (is_public),
    INDEX idx_query_templates_created_at (created_at)
);

-- Create data vendor session analytics table
CREATE TABLE data_vendor_session_analytics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id VARCHAR(255) NOT NULL REFERENCES data_vendor_chat_sessions(session_id) ON DELETE CASCADE,
    vendor_id BIGINT NOT NULL REFERENCES data_vendor_api_keys(id) ON DELETE CASCADE,
    session_duration_seconds INTEGER,
    message_count INTEGER DEFAULT 0,
    avg_response_time_ms INTEGER,
    success_rate DECIMAL(3,2),
    created_at TIMESTAMP DEFAULT NOW(),

    -- Indexes for performance
    INDEX idx_session_analytics_session_id (session_id),
    INDEX idx_session_analytics_vendor_id (vendor_id),
    INDEX idx_session_analytics_created_at (created_at)
);

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at
CREATE TRIGGER update_data_vendor_chat_sessions_updated_at
    BEFORE UPDATE ON data_vendor_chat_sessions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_data_vendor_query_templates_updated_at
    BEFORE UPDATE ON data_vendor_query_templates
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Create function to clean up expired sessions
CREATE OR REPLACE FUNCTION cleanup_expired_chat_sessions()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM data_vendor_chat_sessions
    WHERE expires_at < NOW() AND is_active = TRUE;

    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Create function to get session statistics
CREATE OR REPLACE FUNCTION get_vendor_session_stats(vendor_id_param BIGINT)
RETURNS TABLE(
    total_sessions BIGINT,
    active_sessions BIGINT,
    avg_session_duration INTEGER,
    total_messages BIGINT,
    avg_messages_per_session DECIMAL(5,2)
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        COUNT(DISTINCT cs.id)::BIGINT as total_sessions,
        COUNT(DISTINCT CASE WHEN cs.is_active = TRUE THEN cs.id END)::BIGINT as active_sessions,
        AVG(EXTRACT(EPOCH FROM (cs.updated_at - cs.created_at)))::INTEGER as avg_session_duration,
        COUNT(cm.id)::BIGINT as total_messages,
        ROUND(COUNT(cm.id)::DECIMAL / COUNT(DISTINCT cs.id), 2) as avg_messages_per_session
    FROM data_vendor_chat_sessions cs
    LEFT JOIN data_vendor_chat_messages cm ON cs.session_id = cm.session_id
    WHERE cs.vendor_id = vendor_id_param;
END;
$$ LANGUAGE plpgsql;

-- Create function to get query performance metrics
CREATE OR REPLACE FUNCTION get_vendor_query_metrics(vendor_id_param BIGINT, days_back INTEGER DEFAULT 30)
RETURNS TABLE(
    query_type VARCHAR(100),
    total_queries BIGINT,
    avg_processing_time_ms INTEGER,
    avg_confidence_score DECIMAL(3,2),
    success_rate DECIMAL(3,2)
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        qa.query_type,
        COUNT(*)::BIGINT as total_queries,
        AVG(qa.processing_time_ms)::INTEGER as avg_processing_time_ms,
        AVG(qa.confidence_score)::DECIMAL(3,2) as avg_confidence_score,
        ROUND(
            COUNT(CASE WHEN qa.error_message IS NULL THEN 1 END)::DECIMAL / COUNT(*), 2
        ) as success_rate
    FROM data_vendor_query_analytics qa
    WHERE qa.vendor_id = vendor_id_param
    AND qa.created_at >= NOW() - INTERVAL '1 day' * days_back
    GROUP BY qa.query_type
    ORDER BY total_queries DESC;
END;
$$ LANGUAGE plpgsql;

-- Insert sample data for testing (optional)
-- INSERT INTO data_vendor_chat_sessions (vendor_id, session_id, expires_at)
-- VALUES (1, 'test-session-001', NOW() + INTERVAL '24 hours');

-- Grant permissions (adjust based on your security model)
-- GRANT SELECT, INSERT, UPDATE, DELETE ON data_vendor_chat_sessions TO arxos_app;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON data_vendor_chat_messages TO arxos_app;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON data_vendor_query_analytics TO arxos_app;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON data_vendor_query_templates TO arxos_app;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON data_vendor_session_analytics TO arxos_app;

-- Create view for session summary
CREATE VIEW data_vendor_session_summary AS
SELECT
    cs.vendor_id,
    cs.session_id,
    cs.created_at,
    cs.updated_at,
    cs.expires_at,
    cs.is_active,
    COUNT(cm.id) as message_count,
    COUNT(CASE WHEN cm.role = 'user' THEN 1 END) as user_messages,
    COUNT(CASE WHEN cm.role = 'assistant' THEN 1 END) as assistant_messages,
    EXTRACT(EPOCH FROM (cs.updated_at - cs.created_at))::INTEGER as session_duration_seconds
FROM data_vendor_chat_sessions cs
LEFT JOIN data_vendor_chat_messages cm ON cs.session_id = cm.session_id
GROUP BY cs.id, cs.vendor_id, cs.session_id, cs.created_at, cs.updated_at, cs.expires_at, cs.is_active;

-- Create view for vendor analytics
CREATE VIEW data_vendor_analytics AS
SELECT
    dvak.id as vendor_id,
    dvak.vendor_name,
    dvak.access_level,
    COUNT(DISTINCT cs.id) as total_sessions,
    COUNT(DISTINCT CASE WHEN cs.is_active = TRUE THEN cs.id END) as active_sessions,
    COUNT(cm.id) as total_messages,
    AVG(qa.processing_time_ms) as avg_query_time_ms,
    AVG(qa.confidence_score) as avg_confidence_score
FROM data_vendor_api_keys dvak
LEFT JOIN data_vendor_chat_sessions cs ON dvak.id = cs.vendor_id
LEFT JOIN data_vendor_chat_messages cm ON cs.session_id = cm.session_id
LEFT JOIN data_vendor_query_analytics qa ON dvak.id = qa.vendor_id
WHERE dvak.is_active = TRUE
GROUP BY dvak.id, dvak.vendor_name, dvak.access_level;

-- Add comments for documentation
COMMENT ON TABLE data_vendor_chat_sessions IS 'Stores chat sessions for data vendor API interactions';
COMMENT ON TABLE data_vendor_chat_messages IS 'Stores individual chat messages within sessions';
COMMENT ON TABLE data_vendor_query_analytics IS 'Tracks query performance and analytics for data vendor API';
COMMENT ON TABLE data_vendor_query_templates IS 'Stores reusable query templates for data vendors';
COMMENT ON TABLE data_vendor_session_analytics IS 'Tracks session-level analytics for data vendor chat';

COMMENT ON COLUMN data_vendor_chat_sessions.context IS 'JSON context data for the chat session';
COMMENT ON COLUMN data_vendor_chat_sessions.history IS 'JSON array of message history for the session';
COMMENT ON COLUMN data_vendor_chat_messages.role IS 'Role of the message sender: user or assistant';
COMMENT ON COLUMN data_vendor_chat_messages.metadata IS 'Additional metadata for the message';
COMMENT ON COLUMN data_vendor_query_analytics.confidence_score IS 'Confidence score for the query (0.0 to 1.0)';
COMMENT ON COLUMN data_vendor_query_analytics.nlp_confidence IS 'NLP processing confidence score';
