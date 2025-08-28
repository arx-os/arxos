-- GitOps Features Tables for BIaC
-- Enables pull request workflows and collaborative building configuration management

-- Pull requests table: Main PR tracking
CREATE TABLE IF NOT EXISTS pull_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pr_number SERIAL UNIQUE NOT NULL,  -- Sequential PR number for easy reference
    building_id VARCHAR(36) NOT NULL REFERENCES pdf_buildings(id) ON DELETE CASCADE,
    
    -- Branch information
    source_branch VARCHAR(100) NOT NULL,
    target_branch VARCHAR(100) NOT NULL,
    base_state_id UUID REFERENCES building_states(id),  -- Common ancestor state
    source_state_id UUID REFERENCES building_states(id),  -- Latest state in source branch
    target_state_id UUID REFERENCES building_states(id),  -- Latest state in target branch
    merge_state_id UUID REFERENCES building_states(id),  -- Created after merge
    
    -- PR metadata
    title VARCHAR(500) NOT NULL,
    description TEXT,
    pr_type VARCHAR(50) DEFAULT 'standard',  -- standard, hotfix, release
    priority VARCHAR(20) DEFAULT 'normal',  -- low, normal, high, critical
    
    -- Status tracking
    status VARCHAR(50) NOT NULL DEFAULT 'draft' CHECK (status IN (
        'draft', 'open', 'review_required', 'changes_requested', 
        'approved', 'merged', 'closed', 'locked'
    )),
    
    -- Conflict detection
    has_conflicts BOOLEAN DEFAULT FALSE,
    conflict_details JSONB,
    auto_mergeable BOOLEAN DEFAULT TRUE,
    
    -- Review requirements
    required_approvals INTEGER DEFAULT 1,
    require_all_reviewers BOOLEAN DEFAULT FALSE,
    require_status_checks BOOLEAN DEFAULT TRUE,
    status_checks JSONB,  -- Required checks and their status
    
    -- Ownership
    author_id VARCHAR(36) NOT NULL,
    author_name VARCHAR(255) NOT NULL,
    merger_id VARCHAR(36),
    merger_name VARCHAR(255),
    
    -- Timestamps
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    ready_for_review_at TIMESTAMP,
    first_reviewed_at TIMESTAMP,
    approved_at TIMESTAMP,
    merged_at TIMESTAMP,
    closed_at TIMESTAMP,
    
    -- Metrics
    lines_added INTEGER DEFAULT 0,
    lines_removed INTEGER DEFAULT 0,
    files_changed INTEGER DEFAULT 0,
    comments_count INTEGER DEFAULT 0,
    commits_count INTEGER DEFAULT 0,
    review_time_hours FLOAT,
    
    -- Additional metadata
    labels TEXT[],
    milestone VARCHAR(100),
    metadata JSONB,
    
    UNIQUE(building_id, pr_number)
);

-- PR reviews table: Track review activities
CREATE TABLE IF NOT EXISTS pr_reviews (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pr_id UUID NOT NULL REFERENCES pull_requests(id) ON DELETE CASCADE,
    
    -- Reviewer information
    reviewer_id VARCHAR(36) NOT NULL,
    reviewer_name VARCHAR(255) NOT NULL,
    reviewer_role VARCHAR(50),  -- owner, maintainer, contributor, viewer
    
    -- Review decision
    status VARCHAR(50) NOT NULL CHECK (status IN (
        'pending', 'commented', 'approved', 'changes_requested', 'dismissed'
    )),
    
    -- Review content
    body TEXT,
    commit_id UUID REFERENCES building_states(id),  -- State at time of review
    
    -- Timestamps
    submitted_at TIMESTAMP NOT NULL DEFAULT NOW(),
    dismissed_at TIMESTAMP,
    dismissed_by VARCHAR(36),
    dismiss_reason TEXT,
    
    metadata JSONB
);

-- PR comments table: Discussion threads
CREATE TABLE IF NOT EXISTS pr_comments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pr_id UUID NOT NULL REFERENCES pull_requests(id) ON DELETE CASCADE,
    parent_comment_id UUID REFERENCES pr_comments(id),  -- For threaded discussions
    
    -- Comment metadata
    comment_type VARCHAR(50) DEFAULT 'general',  -- general, code, system
    line_number INTEGER,  -- For inline comments
    file_path TEXT,  -- For file-specific comments
    
    -- Content
    body TEXT NOT NULL,
    
    -- Author
    author_id VARCHAR(36) NOT NULL,
    author_name VARCHAR(255) NOT NULL,
    
    -- Status
    is_resolved BOOLEAN DEFAULT FALSE,
    resolved_by VARCHAR(36),
    resolved_at TIMESTAMP,
    
    -- Timestamps
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMP,  -- Soft delete
    
    -- Reactions
    reactions JSONB,  -- {"+1": ["user1", "user2"], "-1": ["user3"]}
    
    metadata JSONB
);

-- PR commits table: Track commits in a PR
CREATE TABLE IF NOT EXISTS pr_commits (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pr_id UUID NOT NULL REFERENCES pull_requests(id) ON DELETE CASCADE,
    state_id UUID NOT NULL REFERENCES building_states(id),
    
    -- Commit information
    commit_message TEXT NOT NULL,
    commit_order INTEGER NOT NULL,
    
    -- Changes summary
    objects_added INTEGER DEFAULT 0,
    objects_modified INTEGER DEFAULT 0,
    objects_removed INTEGER DEFAULT 0,
    systems_changed TEXT[],
    
    -- Author
    author_id VARCHAR(36) NOT NULL,
    author_name VARCHAR(255) NOT NULL,
    committed_at TIMESTAMP NOT NULL DEFAULT NOW(),
    
    metadata JSONB,
    
    UNIQUE(pr_id, commit_order)
);

-- Merge conflicts table: Track and resolve conflicts
CREATE TABLE IF NOT EXISTS merge_conflicts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pr_id UUID NOT NULL REFERENCES pull_requests(id) ON DELETE CASCADE,
    
    -- Conflict location
    conflict_type VARCHAR(50) NOT NULL,  -- arxobject, system, metadata
    object_id VARCHAR(100),  -- ID of conflicting object/system
    
    -- Conflict details
    base_value JSONB,  -- Value in base branch
    source_value JSONB,  -- Value in source branch
    target_value JSONB,  -- Value in target branch
    
    -- Resolution
    resolution_strategy VARCHAR(50),  -- ours, theirs, manual, auto
    resolved_value JSONB,
    resolved_by VARCHAR(36),
    resolved_at TIMESTAMP,
    
    -- Status
    status VARCHAR(50) DEFAULT 'unresolved',  -- unresolved, resolved, ignored
    
    metadata JSONB
);

-- PR templates table: Reusable PR templates
CREATE TABLE IF NOT EXISTS pr_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL UNIQUE,
    template_type VARCHAR(50) NOT NULL,  -- feature, bugfix, hotfix, release
    
    -- Template content
    title_template TEXT,
    description_template TEXT,
    
    -- Default settings
    default_reviewers TEXT[],
    default_labels TEXT[],
    required_status_checks TEXT[],
    auto_merge_enabled BOOLEAN DEFAULT FALSE,
    
    -- Usage
    is_active BOOLEAN DEFAULT TRUE,
    usage_count INTEGER DEFAULT 0,
    last_used_at TIMESTAMP,
    
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    metadata JSONB
);

-- PR status checks table: Track automated checks
CREATE TABLE IF NOT EXISTS pr_status_checks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pr_id UUID NOT NULL REFERENCES pull_requests(id) ON DELETE CASCADE,
    
    -- Check information
    check_name VARCHAR(255) NOT NULL,
    check_type VARCHAR(50) NOT NULL,  -- validation, test, build, security
    
    -- Status
    status VARCHAR(50) NOT NULL CHECK (status IN (
        'pending', 'running', 'success', 'failure', 'error', 'cancelled', 'skipped'
    )),
    
    -- Results
    conclusion VARCHAR(50),
    output JSONB,
    details_url TEXT,
    
    -- Timing
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    
    -- Context
    commit_id UUID REFERENCES building_states(id),
    external_id VARCHAR(255),  -- ID from external system
    
    metadata JSONB,
    
    UNIQUE(pr_id, check_name, commit_id)
);

-- Branch protection rules table
CREATE TABLE IF NOT EXISTS branch_protection_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    building_id VARCHAR(36) NOT NULL REFERENCES pdf_buildings(id) ON DELETE CASCADE,
    branch_pattern VARCHAR(255) NOT NULL,  -- Can use wildcards like 'release/*'
    
    -- Protection settings
    require_pr BOOLEAN DEFAULT TRUE,
    require_approvals INTEGER DEFAULT 1,
    dismiss_stale_reviews BOOLEAN DEFAULT TRUE,
    require_status_checks BOOLEAN DEFAULT TRUE,
    required_status_check_names TEXT[],
    require_up_to_date BOOLEAN DEFAULT TRUE,
    
    -- Restrictions
    restrict_push BOOLEAN DEFAULT FALSE,
    push_allowlist TEXT[],  -- User IDs who can push
    restrict_merge BOOLEAN DEFAULT FALSE,
    merge_allowlist TEXT[],  -- User IDs who can merge
    allow_force_push BOOLEAN DEFAULT FALSE,
    allow_deletions BOOLEAN DEFAULT FALSE,
    
    -- Enforcement
    enforce_admins BOOLEAN DEFAULT FALSE,
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    metadata JSONB,
    
    UNIQUE(building_id, branch_pattern)
);

-- Merge queue table: Manage merge order
CREATE TABLE IF NOT EXISTS merge_queue (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pr_id UUID NOT NULL REFERENCES pull_requests(id) ON DELETE CASCADE,
    
    -- Queue position
    position INTEGER NOT NULL,
    priority INTEGER DEFAULT 0,  -- Higher priority merges first
    
    -- Status
    status VARCHAR(50) NOT NULL DEFAULT 'waiting' CHECK (status IN (
        'waiting', 'checking', 'merging', 'merged', 'failed', 'cancelled'
    )),
    
    -- Timing
    enqueued_at TIMESTAMP NOT NULL DEFAULT NOW(),
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    
    -- Results
    merge_commit_id UUID REFERENCES building_states(id),
    failure_reason TEXT,
    
    metadata JSONB,
    
    UNIQUE(pr_id)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_pull_requests_building ON pull_requests(building_id);
CREATE INDEX IF NOT EXISTS idx_pull_requests_status ON pull_requests(status);
CREATE INDEX IF NOT EXISTS idx_pull_requests_author ON pull_requests(author_id);
CREATE INDEX IF NOT EXISTS idx_pull_requests_created ON pull_requests(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_pull_requests_number ON pull_requests(pr_number);

CREATE INDEX IF NOT EXISTS idx_pr_reviews_pr ON pr_reviews(pr_id);
CREATE INDEX IF NOT EXISTS idx_pr_reviews_reviewer ON pr_reviews(reviewer_id);
CREATE INDEX IF NOT EXISTS idx_pr_reviews_status ON pr_reviews(status);

CREATE INDEX IF NOT EXISTS idx_pr_comments_pr ON pr_comments(pr_id);
CREATE INDEX IF NOT EXISTS idx_pr_comments_parent ON pr_comments(parent_comment_id);
CREATE INDEX IF NOT EXISTS idx_pr_comments_author ON pr_comments(author_id);

CREATE INDEX IF NOT EXISTS idx_pr_commits_pr ON pr_commits(pr_id);
CREATE INDEX IF NOT EXISTS idx_pr_commits_state ON pr_commits(state_id);

CREATE INDEX IF NOT EXISTS idx_merge_conflicts_pr ON merge_conflicts(pr_id);
CREATE INDEX IF NOT EXISTS idx_merge_conflicts_status ON merge_conflicts(status);

CREATE INDEX IF NOT EXISTS idx_pr_status_checks_pr ON pr_status_checks(pr_id);
CREATE INDEX IF NOT EXISTS idx_pr_status_checks_status ON pr_status_checks(status);

CREATE INDEX IF NOT EXISTS idx_branch_protection_building ON branch_protection_rules(building_id);
CREATE INDEX IF NOT EXISTS idx_branch_protection_active ON branch_protection_rules(is_active);

CREATE INDEX IF NOT EXISTS idx_merge_queue_position ON merge_queue(position);
CREATE INDEX IF NOT EXISTS idx_merge_queue_status ON merge_queue(status);

-- Add comments
COMMENT ON TABLE pull_requests IS 'Pull requests for collaborative building configuration changes';
COMMENT ON TABLE pr_reviews IS 'Review activities on pull requests';
COMMENT ON TABLE pr_comments IS 'Discussion threads on pull requests';
COMMENT ON TABLE pr_commits IS 'Building state commits within a pull request';
COMMENT ON TABLE merge_conflicts IS 'Conflicts detected during merge attempts';
COMMENT ON TABLE pr_templates IS 'Reusable templates for creating pull requests';
COMMENT ON TABLE pr_status_checks IS 'Automated checks run on pull requests';
COMMENT ON TABLE branch_protection_rules IS 'Rules protecting branches from direct changes';
COMMENT ON TABLE merge_queue IS 'Queue for managing merge order and preventing conflicts';

COMMENT ON COLUMN pull_requests.pr_number IS 'Sequential number for easy reference (e.g., PR #123)';
COMMENT ON COLUMN pull_requests.base_state_id IS 'Common ancestor state for three-way merge';
COMMENT ON COLUMN merge_conflicts.resolution_strategy IS 'Strategy used to resolve conflict: ours (source wins), theirs (target wins), manual, auto';

-- Grant permissions
GRANT SELECT, INSERT, UPDATE, DELETE ON pull_requests TO arxos_api_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON pr_reviews TO arxos_api_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON pr_comments TO arxos_api_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON pr_commits TO arxos_api_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON merge_conflicts TO arxos_api_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON pr_templates TO arxos_api_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON pr_status_checks TO arxos_api_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON branch_protection_rules TO arxos_api_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON merge_queue TO arxos_api_user;

-- Grant usage on sequences
GRANT USAGE, SELECT ON SEQUENCE pull_requests_pr_number_seq TO arxos_api_user;

-- Insert default PR templates
INSERT INTO pr_templates (name, template_type, title_template, description_template, is_active) VALUES
('feature_template', 'feature', '[FEATURE] ', '## Description\nDescribe the new feature\n\n## Changes\n- \n\n## Testing\n- [ ] Tested locally\n- [ ] All checks pass', true),
('bugfix_template', 'bugfix', '[FIX] ', '## Issue\nDescribe the bug\n\n## Solution\nHow it was fixed\n\n## Testing\n- [ ] Bug is resolved\n- [ ] No regressions', true),
('hotfix_template', 'hotfix', '[HOTFIX] ', '## Critical Issue\n\n## Immediate Fix\n\n## Impact\n\n## Rollback Plan\n', true)
ON CONFLICT (name) DO NOTHING;