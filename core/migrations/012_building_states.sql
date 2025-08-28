-- Building State Management Tables for BIaC
-- Enables version control and state tracking for buildings

-- Building states table: Core versioning system
CREATE TABLE IF NOT EXISTS building_states (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    building_id VARCHAR(36) NOT NULL REFERENCES pdf_buildings(id) ON DELETE CASCADE,
    version VARCHAR(20) NOT NULL,  -- Semantic versioning (e.g., 1.2.3)
    state_hash VARCHAR(64) NOT NULL,  -- SHA-256 hash of complete state
    merkle_root VARCHAR(64),  -- Root of Merkle tree for efficient comparison
    parent_state_id UUID REFERENCES building_states(id),
    branch_name VARCHAR(100) NOT NULL DEFAULT 'main',
    
    -- State data
    arxobject_snapshot JSONB NOT NULL,  -- Compressed snapshot of all ArxObjects
    systems_state JSONB NOT NULL,  -- HVAC, electrical, plumbing states
    performance_metrics JSONB,  -- Energy usage, occupancy, etc.
    compliance_status JSONB,  -- Regulatory compliance state
    
    -- Metadata
    author_id VARCHAR(36),
    author_name VARCHAR(255),
    message TEXT,  -- Commit message
    tags TEXT[],  -- Version tags
    arxobject_count INTEGER NOT NULL DEFAULT 0,
    total_size_bytes BIGINT,
    
    -- Timestamps
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    captured_at TIMESTAMP NOT NULL DEFAULT NOW(),
    
    -- Additional metadata
    metadata JSONB,
    
    -- Unique constraint on building + version + branch
    UNIQUE(building_id, version, branch_name)
);

-- State transitions table: Track all state changes
CREATE TABLE IF NOT EXISTS state_transitions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    building_id VARCHAR(36) NOT NULL REFERENCES pdf_buildings(id) ON DELETE CASCADE,
    from_state_id UUID REFERENCES building_states(id),
    to_state_id UUID NOT NULL REFERENCES building_states(id),
    transition_type VARCHAR(50) NOT NULL,  -- capture, restore, merge, rollback
    initiated_by VARCHAR(36),
    initiated_by_name VARCHAR(255),
    reason TEXT,
    
    -- Transition details
    changes_summary JSONB,  -- Summary of what changed
    affected_systems TEXT[],  -- Which systems were affected
    validation_results JSONB,  -- Any validation performed
    
    -- Timing
    initiated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMP,
    duration_ms INTEGER,
    
    -- Status
    status VARCHAR(50) NOT NULL DEFAULT 'completed',  -- completed, failed, partial
    error_details TEXT,
    
    metadata JSONB
);

-- State branches table: Git-like branching for buildings
CREATE TABLE IF NOT EXISTS state_branches (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    building_id VARCHAR(36) NOT NULL REFERENCES pdf_buildings(id) ON DELETE CASCADE,
    branch_name VARCHAR(100) NOT NULL,
    base_state_id UUID REFERENCES building_states(id),  -- Where branch was created from
    head_state_id UUID REFERENCES building_states(id),  -- Current HEAD of branch
    
    -- Branch metadata
    description TEXT,
    is_protected BOOLEAN DEFAULT FALSE,
    is_default BOOLEAN DEFAULT FALSE,
    merge_requirements JSONB,  -- Required approvals, checks, etc.
    
    -- Ownership
    created_by VARCHAR(36),
    created_by_name VARCHAR(255),
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    
    -- Statistics
    commits_ahead INTEGER DEFAULT 0,
    commits_behind INTEGER DEFAULT 0,
    last_activity_at TIMESTAMP,
    
    metadata JSONB,
    
    -- Unique constraint
    UNIQUE(building_id, branch_name)
);

-- State comparisons table: Cache diff results
CREATE TABLE IF NOT EXISTS state_comparisons (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    state_a_id UUID NOT NULL REFERENCES building_states(id) ON DELETE CASCADE,
    state_b_id UUID NOT NULL REFERENCES building_states(id) ON DELETE CASCADE,
    
    -- Diff results
    diff_summary JSONB NOT NULL,  -- High-level summary
    arxobjects_added INTEGER DEFAULT 0,
    arxobjects_modified INTEGER DEFAULT 0,
    arxobjects_removed INTEGER DEFAULT 0,
    systems_changed TEXT[],
    
    -- Performance
    comparison_time_ms INTEGER,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    
    -- Cache management
    accessed_count INTEGER DEFAULT 1,
    last_accessed_at TIMESTAMP NOT NULL DEFAULT NOW(),
    
    -- Unique constraint for caching
    UNIQUE(state_a_id, state_b_id)
);

-- State tags table: Named versions (like Git tags)
CREATE TABLE IF NOT EXISTS state_tags (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    building_id VARCHAR(36) NOT NULL REFERENCES pdf_buildings(id) ON DELETE CASCADE,
    state_id UUID NOT NULL REFERENCES building_states(id) ON DELETE CASCADE,
    tag_name VARCHAR(100) NOT NULL,
    tag_type VARCHAR(50) NOT NULL DEFAULT 'lightweight',  -- lightweight, annotated
    
    -- Annotation (for annotated tags)
    message TEXT,
    tagger_id VARCHAR(36),
    tagger_name VARCHAR(255),
    
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    metadata JSONB,
    
    -- Unique constraint
    UNIQUE(building_id, tag_name)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_building_states_building ON building_states(building_id);
CREATE INDEX IF NOT EXISTS idx_building_states_branch ON building_states(branch_name);
CREATE INDEX IF NOT EXISTS idx_building_states_version ON building_states(version);
CREATE INDEX IF NOT EXISTS idx_building_states_hash ON building_states(state_hash);
CREATE INDEX IF NOT EXISTS idx_building_states_parent ON building_states(parent_state_id);
CREATE INDEX IF NOT EXISTS idx_building_states_created ON building_states(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_state_transitions_building ON state_transitions(building_id);
CREATE INDEX IF NOT EXISTS idx_state_transitions_from ON state_transitions(from_state_id);
CREATE INDEX IF NOT EXISTS idx_state_transitions_to ON state_transitions(to_state_id);
CREATE INDEX IF NOT EXISTS idx_state_transitions_initiated ON state_transitions(initiated_at DESC);

CREATE INDEX IF NOT EXISTS idx_state_branches_building ON state_branches(building_id);
CREATE INDEX IF NOT EXISTS idx_state_branches_head ON state_branches(head_state_id);
CREATE INDEX IF NOT EXISTS idx_state_branches_default ON state_branches(building_id, is_default) WHERE is_default = TRUE;

CREATE INDEX IF NOT EXISTS idx_state_comparisons_states ON state_comparisons(state_a_id, state_b_id);
CREATE INDEX IF NOT EXISTS idx_state_comparisons_accessed ON state_comparisons(last_accessed_at DESC);

CREATE INDEX IF NOT EXISTS idx_state_tags_building ON state_tags(building_id);
CREATE INDEX IF NOT EXISTS idx_state_tags_state ON state_tags(state_id);

-- Add comments
COMMENT ON TABLE building_states IS 'Version-controlled snapshots of complete building state';
COMMENT ON TABLE state_transitions IS 'Audit log of all state changes';
COMMENT ON TABLE state_branches IS 'Git-like branches for building configuration management';
COMMENT ON TABLE state_comparisons IS 'Cached diff results between states for performance';
COMMENT ON TABLE state_tags IS 'Named versions for release management';

COMMENT ON COLUMN building_states.state_hash IS 'SHA-256 hash of entire state for integrity verification';
COMMENT ON COLUMN building_states.merkle_root IS 'Root of Merkle tree for efficient state comparison';
COMMENT ON COLUMN building_states.arxobject_snapshot IS 'Complete snapshot of all ArxObjects at this state';
COMMENT ON COLUMN state_branches.is_protected IS 'Prevents direct commits, requires pull requests';

-- Grant permissions
GRANT SELECT, INSERT, UPDATE, DELETE ON building_states TO arxos_api_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON state_transitions TO arxos_api_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON state_branches TO arxos_api_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON state_comparisons TO arxos_api_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON state_tags TO arxos_api_user;