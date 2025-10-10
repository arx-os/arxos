-- Migration 015: Git Workflow Enhancement
-- Description: Add branches, enhanced commits, and repository state management for Git-like collaboration
-- Author: ArxOS Team
-- Date: 2025-01-15

-- ============================================================================
-- Repository Branches Table
-- ============================================================================
-- Implements Git-like branches for isolated work on building repositories
CREATE TABLE IF NOT EXISTS repository_branches (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    repository_id UUID NOT NULL REFERENCES building_repositories(id) ON DELETE CASCADE,
    
    -- Branch identification
    name TEXT NOT NULL,
    display_name TEXT,
    description TEXT,
    
    -- Branch metadata
    base_commit UUID REFERENCES versions(id) ON DELETE SET NULL, -- What this branched from
    head_commit UUID REFERENCES versions(id) ON DELETE SET NULL, -- Current tip of branch
    
    -- Branch type (for workflows)
    branch_type TEXT CHECK (branch_type IN (
        'main',           -- Main/production branch
        'development',    -- Development branch
        'feature',        -- Feature branch
        'bugfix',         -- Bug fix branch
        'release',        -- Release branch
        'hotfix',         -- Hotfix branch
        'contractor',     -- Contractor work branch
        'vendor',         -- Vendor maintenance branch
        'issue',          -- Auto-created from issue
        'scan'            -- Auto-created from mobile scan
    )),
    
    -- Branch protection
    protected BOOLEAN NOT NULL DEFAULT false,
    requires_review BOOLEAN NOT NULL DEFAULT false,
    auto_delete_on_merge BOOLEAN NOT NULL DEFAULT false,
    
    -- Branch state
    status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'stale', 'merged', 'closed')),
    is_default BOOLEAN NOT NULL DEFAULT false,
    
    -- Branch ownership
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,
    owned_by UUID REFERENCES users(id) ON DELETE SET NULL, -- Current owner
    
    -- Audit
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    merged_at TIMESTAMPTZ,
    merged_by UUID REFERENCES users(id) ON DELETE SET NULL,
    
    -- Unique constraint: One branch name per repository
    CONSTRAINT repository_branches_unique_name UNIQUE(repository_id, name)
);

CREATE INDEX idx_repository_branches_repo ON repository_branches(repository_id);
CREATE INDEX idx_repository_branches_status ON repository_branches(status) WHERE status = 'active';
CREATE INDEX idx_repository_branches_type ON repository_branches(branch_type);
CREATE INDEX idx_repository_branches_owner ON repository_branches(owned_by) WHERE owned_by IS NOT NULL;
CREATE INDEX idx_repository_branches_default ON repository_branches(repository_id, is_default) WHERE is_default = true;

COMMENT ON TABLE repository_branches IS 'Git-like branches for isolated work on building repositories';
COMMENT ON COLUMN repository_branches.protected IS 'Protected branches require PR to merge (like GitHub main branch)';
COMMENT ON COLUMN repository_branches.branch_type IS 'Type of branch for workflow routing (contractor, vendor, issue, etc.)';

-- ============================================================================
-- Repository Commits Table (Enhanced)
-- ============================================================================
-- Enhanced commit tracking with detailed changesets
CREATE TABLE IF NOT EXISTS repository_commits (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    repository_id UUID NOT NULL REFERENCES building_repositories(id) ON DELETE CASCADE,
    branch_id UUID NOT NULL REFERENCES repository_branches(id) ON DELETE CASCADE,
    version_id UUID NOT NULL REFERENCES versions(id) ON DELETE CASCADE,
    
    -- Commit identification
    commit_hash TEXT UNIQUE NOT NULL,
    short_hash TEXT NOT NULL, -- First 7 chars of hash
    
    -- Commit metadata
    message TEXT NOT NULL,
    description TEXT, -- Extended commit message
    
    -- Author information
    author_name TEXT NOT NULL,
    author_email TEXT NOT NULL,
    author_id UUID REFERENCES users(id) ON DELETE SET NULL,
    
    -- Commit relationships
    parent_commits UUID[], -- Array of parent commit IDs (for merges)
    merge_commit BOOLEAN NOT NULL DEFAULT false,
    
    -- Changes summary
    changes_summary JSONB NOT NULL DEFAULT '{}', -- {buildings_added: 0, rooms_modified: 3, etc.}
    files_changed INTEGER NOT NULL DEFAULT 0,
    lines_added INTEGER NOT NULL DEFAULT 0,
    lines_deleted INTEGER NOT NULL DEFAULT 0,
    
    -- Commit tags
    tags TEXT[], -- ['v1.0', 'production', 'milestone-1']
    
    -- Audit
    committed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- Metadata
    metadata JSONB DEFAULT '{}'
);

CREATE INDEX idx_repository_commits_repo ON repository_commits(repository_id, committed_at DESC);
CREATE INDEX idx_repository_commits_branch ON repository_commits(branch_id, committed_at DESC);
CREATE INDEX idx_repository_commits_author ON repository_commits(author_id) WHERE author_id IS NOT NULL;
CREATE INDEX idx_repository_commits_hash ON repository_commits(commit_hash);
CREATE INDEX idx_repository_commits_tags ON repository_commits USING GIN(tags);
CREATE INDEX idx_repository_commits_merge ON repository_commits(merge_commit) WHERE merge_commit = true;

COMMENT ON TABLE repository_commits IS 'Enhanced commit tracking with changesets and branch relationships';
COMMENT ON COLUMN repository_commits.parent_commits IS 'Array of parent UUIDs - single for regular commit, multiple for merge';

-- ============================================================================
-- Commit Changes Table
-- ============================================================================
-- Detailed per-entity changes for each commit
CREATE TABLE IF NOT EXISTS commit_changes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    commit_id UUID NOT NULL REFERENCES repository_commits(id) ON DELETE CASCADE,
    
    -- Change identification
    entity_type TEXT NOT NULL CHECK (entity_type IN (
        'building', 'floor', 'room', 'equipment', 
        'bas_point', 'bas_system',
        'component', 'spatial_anchor', 'point_cloud'
    )),
    entity_id UUID NOT NULL,
    entity_path TEXT, -- ArxOS path like /building/3/room-301
    
    -- Change type
    change_type TEXT NOT NULL CHECK (change_type IN ('added', 'modified', 'deleted', 'renamed', 'moved')),
    
    -- Change details
    field_name TEXT, -- Which field changed (for 'modified')
    old_value TEXT,
    new_value TEXT,
    
    -- Diff
    diff JSONB, -- Structured diff data
    
    -- Metadata
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_commit_changes_commit ON commit_changes(commit_id);
CREATE INDEX idx_commit_changes_entity ON commit_changes(entity_type, entity_id);
CREATE INDEX idx_commit_changes_type ON commit_changes(change_type);
CREATE INDEX idx_commit_changes_path ON commit_changes(entity_path);

COMMENT ON TABLE commit_changes IS 'Detailed entity-level changes for each commit (like git diff)';

-- ============================================================================
-- Repository State Table
-- ============================================================================
-- Current state of each branch (cached for performance)
CREATE TABLE IF NOT EXISTS repository_branch_states (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    repository_id UUID NOT NULL REFERENCES building_repositories(id) ON DELETE CASCADE,
    branch_id UUID NOT NULL REFERENCES repository_branches(id) ON DELETE CASCADE,
    
    -- State summary
    buildings_count INTEGER NOT NULL DEFAULT 0,
    floors_count INTEGER NOT NULL DEFAULT 0,
    rooms_count INTEGER NOT NULL DEFAULT 0,
    equipment_count INTEGER NOT NULL DEFAULT 0,
    bas_points_count INTEGER NOT NULL DEFAULT 0,
    
    -- Uncommitted changes
    has_uncommitted_changes BOOLEAN NOT NULL DEFAULT false,
    uncommitted_changes_count INTEGER NOT NULL DEFAULT 0,
    
    -- State hash (for quick comparison)
    state_hash TEXT NOT NULL,
    
    -- Last updated
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    CONSTRAINT repository_branch_states_unique UNIQUE(repository_id, branch_id)
);

CREATE INDEX idx_repository_branch_states_repo ON repository_branch_states(repository_id);
CREATE INDEX idx_repository_branch_states_branch ON repository_branch_states(branch_id);
CREATE INDEX idx_repository_branch_states_uncommitted ON repository_branch_states(has_uncommitted_changes) 
    WHERE has_uncommitted_changes = true;

COMMENT ON TABLE repository_branch_states IS 'Cached state summary for each branch (performance optimization)';

-- ============================================================================
-- Working Directory Table
-- ============================================================================
-- Tracks working directory state per user (like git status)
CREATE TABLE IF NOT EXISTS working_directories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    repository_id UUID NOT NULL REFERENCES building_repositories(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Current checkout
    current_branch_id UUID NOT NULL REFERENCES repository_branches(id) ON DELETE CASCADE,
    current_commit_id UUID REFERENCES repository_commits(id) ON DELETE SET NULL,
    
    -- Working state
    has_uncommitted_changes BOOLEAN NOT NULL DEFAULT false,
    staged_changes JSONB DEFAULT '[]', -- Array of entity changes staged for commit
    
    -- Last activity
    last_checkout_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_commit_at TIMESTAMPTZ,
    
    -- Metadata
    metadata JSONB DEFAULT '{}',
    
    CONSTRAINT working_directories_unique_user_repo UNIQUE(repository_id, user_id)
);

CREATE INDEX idx_working_directories_user ON working_directories(user_id);
CREATE INDEX idx_working_directories_repo ON working_directories(repository_id);
CREATE INDEX idx_working_directories_branch ON working_directories(current_branch_id);

COMMENT ON TABLE working_directories IS 'User working directory state (current branch, uncommitted changes)';

-- ============================================================================
-- Merge Conflicts Table
-- ============================================================================
-- Track merge conflicts for resolution
CREATE TABLE IF NOT EXISTS merge_conflicts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    repository_id UUID NOT NULL REFERENCES building_repositories(id) ON DELETE CASCADE,
    
    -- Merge details
    source_branch_id UUID NOT NULL REFERENCES repository_branches(id) ON DELETE CASCADE,
    target_branch_id UUID NOT NULL REFERENCES repository_branches(id) ON DELETE CASCADE,
    
    -- Conflict details
    entity_type TEXT NOT NULL,
    entity_id UUID NOT NULL,
    entity_path TEXT,
    
    -- Conflicting changes
    source_value TEXT,
    target_value TEXT,
    base_value TEXT, -- Common ancestor value
    
    -- Resolution
    resolved BOOLEAN NOT NULL DEFAULT false,
    resolution_value TEXT,
    resolved_by UUID REFERENCES users(id) ON DELETE SET NULL,
    resolved_at TIMESTAMPTZ,
    resolution_strategy TEXT CHECK (resolution_strategy IN ('ours', 'theirs', 'manual', 'auto', NULL)),
    
    -- Metadata
    conflict_type TEXT CHECK (conflict_type IN ('content', 'delete', 'rename', 'move')),
    metadata JSONB DEFAULT '{}',
    
    -- Audit
    detected_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_merge_conflicts_repo ON merge_conflicts(repository_id);
CREATE INDEX idx_merge_conflicts_source ON merge_conflicts(source_branch_id);
CREATE INDEX idx_merge_conflicts_target ON merge_conflicts(target_branch_id);
CREATE INDEX idx_merge_conflicts_unresolved ON merge_conflicts(resolved) WHERE resolved = false;
CREATE INDEX idx_merge_conflicts_entity ON merge_conflicts(entity_type, entity_id);

COMMENT ON TABLE merge_conflicts IS 'Merge conflicts detected during branch merges (like git merge conflicts)';

-- ============================================================================
-- Initial Data: Create default main branch for existing repositories
-- ============================================================================
-- For any existing building repositories, create a default main branch
INSERT INTO repository_branches (repository_id, name, display_name, branch_type, protected, is_default, status, created_at)
SELECT 
    id as repository_id,
    'main' as name,
    'Main' as display_name,
    'main' as branch_type,
    true as protected,
    true as is_default,
    'active' as status,
    NOW() as created_at
FROM building_repositories
WHERE id NOT IN (
    SELECT repository_id FROM repository_branches WHERE name = 'main'
)
ON CONFLICT DO NOTHING;

-- ============================================================================
-- Update triggers for updated_at timestamps
-- ============================================================================
CREATE OR REPLACE FUNCTION update_repository_workflow_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER repository_branches_updated_at
    BEFORE UPDATE ON repository_branches
    FOR EACH ROW
    EXECUTE FUNCTION update_repository_workflow_updated_at();

CREATE TRIGGER repository_branch_states_updated_at
    BEFORE UPDATE ON repository_branch_states
    FOR EACH ROW
    EXECUTE FUNCTION update_repository_workflow_updated_at();

-- ============================================================================
-- Views for common queries
-- ============================================================================
-- Active branches with commit counts
CREATE OR REPLACE VIEW v_active_branches AS
SELECT 
    b.id,
    b.repository_id,
    b.name,
    b.display_name,
    b.branch_type,
    b.protected,
    b.status,
    b.created_by,
    b.owned_by,
    b.created_at,
    b.updated_at,
    COUNT(c.id) as commit_count,
    MAX(c.committed_at) as last_commit_at
FROM repository_branches b
LEFT JOIN repository_commits c ON c.branch_id = b.id
WHERE b.status = 'active'
GROUP BY b.id;

COMMENT ON VIEW v_active_branches IS 'Active branches with commit statistics';

-- Unresolved conflicts summary
CREATE OR REPLACE VIEW v_unresolved_conflicts AS
SELECT 
    repository_id,
    source_branch_id,
    target_branch_id,
    COUNT(*) as conflict_count,
    array_agg(DISTINCT entity_type) as affected_entity_types
FROM merge_conflicts
WHERE resolved = false
GROUP BY repository_id, source_branch_id, target_branch_id;

COMMENT ON VIEW v_unresolved_conflicts IS 'Summary of unresolved merge conflicts by branch pair';

-- ============================================================================
-- Schema documentation
-- ============================================================================
COMMENT ON SCHEMA public IS 'ArxOS spatial database schema - Migration 015 applied (Git Workflow)';

