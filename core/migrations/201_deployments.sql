-- Deployment Engine Tables for BIaC
-- Enables configuration deployment across building portfolios

-- Deployments table: Main deployment tracking
CREATE TABLE IF NOT EXISTS deployments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    
    -- Source configuration
    source_state_id UUID REFERENCES building_states(id),
    template_id UUID,  -- Reference to configuration template (future)
    config JSONB NOT NULL,  -- Deployment configuration
    
    -- Target selection
    target_query TEXT,  -- AQL query to select target buildings
    target_buildings UUID[] NOT NULL,  -- Resolved target building IDs
    target_count INTEGER NOT NULL DEFAULT 0,
    
    -- Deployment strategy
    strategy VARCHAR(50) NOT NULL CHECK (strategy IN ('immediate', 'canary', 'rolling', 'blue_green')),
    strategy_config JSONB,  -- Strategy-specific configuration
    
    -- Scheduling
    scheduled_at TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    
    -- Status tracking
    status VARCHAR(50) NOT NULL DEFAULT 'draft' CHECK (status IN (
        'draft', 'scheduled', 'pending_approval', 'approved', 
        'in_progress', 'paused', 'completed', 'failed', 'cancelled', 'rolled_back'
    )),
    
    -- Progress tracking
    progress_percentage INTEGER DEFAULT 0 CHECK (progress_percentage >= 0 AND progress_percentage <= 100),
    successful_count INTEGER DEFAULT 0,
    failed_count INTEGER DEFAULT 0,
    pending_count INTEGER DEFAULT 0,
    
    -- Rollback information
    rollback_enabled BOOLEAN DEFAULT TRUE,
    rollback_state_id UUID REFERENCES building_states(id),
    rolled_back_at TIMESTAMP,
    rollback_reason TEXT,
    
    -- Health checks
    health_check_enabled BOOLEAN DEFAULT TRUE,
    health_check_config JSONB,
    health_status VARCHAR(50),
    
    -- Ownership and audit
    created_by VARCHAR(36) NOT NULL,
    created_by_name VARCHAR(255),
    approved_by VARCHAR(36),
    approved_by_name VARCHAR(255),
    approved_at TIMESTAMP,
    
    -- Metrics and monitoring
    metrics JSONB,  -- Performance metrics during deployment
    logs TEXT[],    -- Deployment logs
    
    -- Timestamps
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    
    -- Additional metadata
    tags TEXT[],
    metadata JSONB
);

-- Deployment targets table: Track individual building deployments
CREATE TABLE IF NOT EXISTS deployment_targets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    deployment_id UUID NOT NULL REFERENCES deployments(id) ON DELETE CASCADE,
    building_id VARCHAR(36) NOT NULL REFERENCES pdf_buildings(id),
    
    -- Deployment order (for rolling deployments)
    deployment_order INTEGER NOT NULL DEFAULT 0,
    deployment_wave INTEGER DEFAULT 0,  -- For canary/blue-green
    
    -- State tracking
    previous_state_id UUID REFERENCES building_states(id),
    deployed_state_id UUID REFERENCES building_states(id),
    
    -- Status for this specific target
    status VARCHAR(50) NOT NULL DEFAULT 'pending' CHECK (status IN (
        'pending', 'queued', 'in_progress', 'validating', 
        'completed', 'failed', 'rolled_back', 'skipped'
    )),
    
    -- Timing
    queued_at TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    duration_ms INTEGER,
    
    -- Health check results
    pre_deployment_health JSONB,
    post_deployment_health JSONB,
    health_check_passed BOOLEAN,
    
    -- Validation results
    validation_results JSONB,
    validation_passed BOOLEAN,
    
    -- Error tracking
    error_code VARCHAR(100),
    error_message TEXT,
    error_details JSONB,
    retry_count INTEGER DEFAULT 0,
    
    -- Metrics
    metrics JSONB,
    
    -- Metadata
    metadata JSONB,
    
    UNIQUE(deployment_id, building_id)
);

-- Deployment strategies configuration
CREATE TABLE IF NOT EXISTS deployment_strategies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL UNIQUE,
    strategy_type VARCHAR(50) NOT NULL,
    description TEXT,
    
    -- Default configuration for this strategy
    default_config JSONB NOT NULL,
    
    -- Validation rules
    validation_rules JSONB,
    
    -- Health check requirements
    health_check_requirements JSONB,
    
    -- Rollback policy
    rollback_policy JSONB,
    
    -- Usage tracking
    usage_count INTEGER DEFAULT 0,
    last_used_at TIMESTAMP,
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    is_default BOOLEAN DEFAULT FALSE,
    
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    metadata JSONB
);

-- Deployment approvals table: Track approval workflow
CREATE TABLE IF NOT EXISTS deployment_approvals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    deployment_id UUID NOT NULL REFERENCES deployments(id) ON DELETE CASCADE,
    
    -- Approval requirements
    required_approvers TEXT[],
    minimum_approvals INTEGER DEFAULT 1,
    
    -- Actual approvals
    approvals JSONB[],  -- Array of {approver_id, approver_name, approved_at, comments}
    rejections JSONB[],  -- Array of {rejector_id, rejector_name, rejected_at, reason}
    
    -- Status
    status VARCHAR(50) NOT NULL DEFAULT 'pending' CHECK (status IN (
        'pending', 'partially_approved', 'approved', 'rejected', 'expired'
    )),
    
    -- Timing
    requested_at TIMESTAMP NOT NULL DEFAULT NOW(),
    deadline_at TIMESTAMP,
    completed_at TIMESTAMP,
    
    -- Notifications
    notifications_sent JSONB,
    reminder_count INTEGER DEFAULT 0,
    
    metadata JSONB
);

-- Deployment health checks table: Health check definitions and results
CREATE TABLE IF NOT EXISTS deployment_health_checks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    deployment_id UUID REFERENCES deployments(id) ON DELETE CASCADE,
    target_id UUID REFERENCES deployment_targets(id) ON DELETE CASCADE,
    
    -- Check definition
    check_name VARCHAR(255) NOT NULL,
    check_type VARCHAR(50) NOT NULL,  -- system, performance, compliance, custom
    check_config JSONB NOT NULL,
    
    -- Execution
    executed_at TIMESTAMP NOT NULL DEFAULT NOW(),
    duration_ms INTEGER,
    
    -- Results
    status VARCHAR(50) NOT NULL CHECK (status IN ('passed', 'failed', 'warning', 'skipped')),
    score DECIMAL(5,2),  -- 0-100 health score
    
    -- Details
    metrics JSONB,
    issues JSONB[],
    recommendations TEXT[],
    
    -- Thresholds
    expected_values JSONB,
    actual_values JSONB,
    threshold_config JSONB,
    
    metadata JSONB
);

-- Deployment rollback history
CREATE TABLE IF NOT EXISTS deployment_rollbacks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    deployment_id UUID NOT NULL REFERENCES deployments(id),
    
    -- Rollback trigger
    triggered_by VARCHAR(50) NOT NULL,  -- automatic, manual, health_check_failure
    triggered_by_user VARCHAR(36),
    triggered_by_name VARCHAR(255),
    triggered_at TIMESTAMP NOT NULL DEFAULT NOW(),
    
    -- Rollback scope
    scope VARCHAR(50) NOT NULL,  -- full, partial, single_building
    affected_buildings UUID[],
    
    -- Rollback execution
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    duration_ms INTEGER,
    
    -- Results
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    successful_count INTEGER DEFAULT 0,
    failed_count INTEGER DEFAULT 0,
    
    -- Reason and details
    reason TEXT NOT NULL,
    details JSONB,
    error_log TEXT[],
    
    metadata JSONB
);

-- Deployment templates table: Reusable deployment configurations
CREATE TABLE IF NOT EXISTS deployment_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    category VARCHAR(100),
    description TEXT,
    
    -- Template content
    template_type VARCHAR(50) NOT NULL,  -- full_config, partial_config, strategy_only
    template_content JSONB NOT NULL,
    
    -- Variables that can be substituted
    variables JSONB,
    required_variables TEXT[],
    
    -- Validation schema
    validation_schema JSONB,
    
    -- Usage tracking
    usage_count INTEGER DEFAULT 0,
    last_used_at TIMESTAMP,
    
    -- Version control
    version VARCHAR(20) NOT NULL DEFAULT '1.0.0',
    is_latest BOOLEAN DEFAULT TRUE,
    parent_template_id UUID REFERENCES deployment_templates(id),
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    is_public BOOLEAN DEFAULT FALSE,
    
    -- Ownership
    created_by VARCHAR(36),
    created_by_name VARCHAR(255),
    
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    tags TEXT[],
    metadata JSONB,
    
    UNIQUE(name, version)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_deployments_status ON deployments(status);
CREATE INDEX IF NOT EXISTS idx_deployments_strategy ON deployments(strategy);
CREATE INDEX IF NOT EXISTS idx_deployments_created ON deployments(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_deployments_scheduled ON deployments(scheduled_at) WHERE scheduled_at IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_deployments_source_state ON deployments(source_state_id);

CREATE INDEX IF NOT EXISTS idx_deployment_targets_deployment ON deployment_targets(deployment_id);
CREATE INDEX IF NOT EXISTS idx_deployment_targets_building ON deployment_targets(building_id);
CREATE INDEX IF NOT EXISTS idx_deployment_targets_status ON deployment_targets(status);
CREATE INDEX IF NOT EXISTS idx_deployment_targets_order ON deployment_targets(deployment_id, deployment_order);

CREATE INDEX IF NOT EXISTS idx_deployment_approvals_deployment ON deployment_approvals(deployment_id);
CREATE INDEX IF NOT EXISTS idx_deployment_approvals_status ON deployment_approvals(status);

CREATE INDEX IF NOT EXISTS idx_deployment_health_checks_deployment ON deployment_health_checks(deployment_id);
CREATE INDEX IF NOT EXISTS idx_deployment_health_checks_target ON deployment_health_checks(target_id);
CREATE INDEX IF NOT EXISTS idx_deployment_health_checks_status ON deployment_health_checks(status);

CREATE INDEX IF NOT EXISTS idx_deployment_rollbacks_deployment ON deployment_rollbacks(deployment_id);
CREATE INDEX IF NOT EXISTS idx_deployment_rollbacks_triggered ON deployment_rollbacks(triggered_at DESC);

CREATE INDEX IF NOT EXISTS idx_deployment_templates_name ON deployment_templates(name);
CREATE INDEX IF NOT EXISTS idx_deployment_templates_active ON deployment_templates(is_active, is_public);

-- Add comments
COMMENT ON TABLE deployments IS 'Main deployment tracking for pushing configurations to building portfolios';
COMMENT ON TABLE deployment_targets IS 'Individual building deployment status within a deployment';
COMMENT ON TABLE deployment_strategies IS 'Reusable deployment strategy configurations';
COMMENT ON TABLE deployment_approvals IS 'Approval workflow tracking for deployments';
COMMENT ON TABLE deployment_health_checks IS 'Health check execution and results';
COMMENT ON TABLE deployment_rollbacks IS 'Rollback history and tracking';
COMMENT ON TABLE deployment_templates IS 'Reusable deployment configuration templates';

COMMENT ON COLUMN deployments.strategy IS 'Deployment strategy: immediate (all at once), canary (small percentage first), rolling (gradual), blue_green (parallel with switch)';
COMMENT ON COLUMN deployments.target_query IS 'AQL query to dynamically select target buildings';
COMMENT ON COLUMN deployment_targets.deployment_wave IS 'Wave number for staged deployments (canary, blue-green)';

-- Grant permissions
GRANT SELECT, INSERT, UPDATE, DELETE ON deployments TO arxos_api_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON deployment_targets TO arxos_api_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON deployment_strategies TO arxos_api_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON deployment_approvals TO arxos_api_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON deployment_health_checks TO arxos_api_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON deployment_rollbacks TO arxos_api_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON deployment_templates TO arxos_api_user;

-- Insert default deployment strategies
INSERT INTO deployment_strategies (name, strategy_type, description, default_config) VALUES
('immediate_default', 'immediate', 'Deploy to all targets simultaneously', 
 '{"parallel_execution": true, "max_parallel": 10, "timeout_minutes": 30}'::jsonb),

('canary_10_percent', 'canary', 'Deploy to 10% of targets first, wait for validation',
 '{"canary_percentage": 10, "validation_period_minutes": 60, "auto_promote": false}'::jsonb),

('rolling_25_percent', 'rolling', 'Deploy in waves of 25% of targets',
 '{"wave_size_percentage": 25, "wave_delay_minutes": 15, "stop_on_failure": true}'::jsonb),

('blue_green_standard', 'blue_green', 'Deploy to parallel environment and switch',
 '{"validation_period_minutes": 120, "traffic_shift_percentage": [0, 50, 100], "rollback_window_hours": 24}'::jsonb)

ON CONFLICT (name) DO NOTHING;