-- Migration 016: Pull Request System
-- Description: Implement GitHub-style pull requests for building repository collaboration
-- This enables CMMS/work order workflows using Git PR model
-- Author: ArxOS Team
-- Date: 2025-01-15

-- ============================================================================
-- Pull Requests Table
-- ============================================================================
-- Represents pull requests (work orders, contractor projects, issue fixes)
CREATE TABLE IF NOT EXISTS pull_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    repository_id UUID NOT NULL REFERENCES building_repositories(id) ON DELETE CASCADE,
    
    -- PR identification
    number SERIAL, -- Auto-incrementing PR number per repository
    title TEXT NOT NULL,
    description TEXT,
    
    -- Branch information
    source_branch_id UUID NOT NULL REFERENCES repository_branches(id) ON DELETE CASCADE,
    target_branch_id UUID NOT NULL REFERENCES repository_branches(id) ON DELETE CASCADE,
    
    -- PR metadata
    pr_type TEXT CHECK (pr_type IN (
        'work_order',      -- Regular work order/maintenance
        'contractor_work', -- Contractor project
        'vendor_service',  -- Vendor maintenance
        'equipment_upgrade', -- Equipment installation/upgrade
        'bas_integration', -- BAS system changes
        'scan_upload',     -- LiDAR scan from mobile
        'issue_fix',       -- Fix for reported issue
        'feature',         -- New feature/capability
        'other'            -- General changes
    )),
    
    -- Status
    status TEXT NOT NULL DEFAULT 'open' CHECK (status IN (
        'open',            -- Newly created, awaiting review
        'in_review',       -- Under review
        'changes_requested', -- Reviewer requested changes
        'approved',        -- Approved, ready to merge
        'merged',          -- Successfully merged
        'closed',          -- Closed without merging
        'draft'            -- Work in progress, not ready for review
    )),
    
    -- Review requirements
    requires_review BOOLEAN NOT NULL DEFAULT true,
    required_reviewers INTEGER NOT NULL DEFAULT 1,
    approved_count INTEGER NOT NULL DEFAULT 0,
    
    -- Assignment
    assigned_to TEXT REFERENCES users(id) ON DELETE SET NULL,
    assigned_team TEXT, -- 'electricians', 'hvac-contractors', etc.
    auto_assigned BOOLEAN NOT NULL DEFAULT false,
    
    -- Priority (like issue priority)
    priority TEXT NOT NULL DEFAULT 'normal' CHECK (priority IN ('low', 'normal', 'high', 'urgent', 'emergency')),
    
    -- Work tracking
    estimated_hours NUMERIC(5,2),
    actual_hours NUMERIC(5,2),
    budget_amount NUMERIC(10,2),
    actual_cost NUMERIC(10,2),
    
    -- Due date
    due_date TIMESTAMPTZ,
    
    -- Labels
    labels TEXT[], -- ['hvac', 'floor-3', 'major-project']
    
    -- Metadata
    metadata JSONB DEFAULT '{}',
    
    -- Author
    created_by TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Audit trail
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    closed_at TIMESTAMPTZ,
    merged_at TIMESTAMPTZ,
    merged_by TEXT REFERENCES users(id) ON DELETE SET NULL
);

CREATE UNIQUE INDEX idx_pull_requests_number ON pull_requests(repository_id, number);
CREATE INDEX idx_pull_requests_repo ON pull_requests(repository_id);
CREATE INDEX idx_pull_requests_source_branch ON pull_requests(source_branch_id);
CREATE INDEX idx_pull_requests_target_branch ON pull_requests(target_branch_id);
CREATE INDEX idx_pull_requests_status ON pull_requests(status) WHERE status IN ('open', 'in_review', 'approved');
CREATE INDEX idx_pull_requests_assigned ON pull_requests(assigned_to) WHERE assigned_to IS NOT NULL;
CREATE INDEX idx_pull_requests_type ON pull_requests(pr_type);
CREATE INDEX idx_pull_requests_priority ON pull_requests(priority) WHERE priority IN ('high', 'urgent', 'emergency');
CREATE INDEX idx_pull_requests_labels ON pull_requests USING GIN(labels);
CREATE INDEX idx_pull_requests_created_by ON pull_requests(created_by);

COMMENT ON TABLE pull_requests IS 'Pull requests for collaborative building changes (work orders, contractor projects, etc.)';
COMMENT ON COLUMN pull_requests.pr_type IS 'Type of work: work_order, contractor_work, issue_fix, etc.';
COMMENT ON COLUMN pull_requests.auto_assigned IS 'Whether PR was auto-assigned based on equipment type or rules';

-- ============================================================================
-- PR Reviewers Table
-- ============================================================================
-- Tracks who needs to review each PR
CREATE TABLE IF NOT EXISTS pr_reviewers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pr_id UUID NOT NULL REFERENCES pull_requests(id) ON DELETE CASCADE,
    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Review status
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN (
        'pending',          -- Not yet reviewed
        'approved',         -- Approved
        'changes_requested', -- Requested changes
        'commented'         -- Commented without approval
    )),
    
    -- Review metadata
    required BOOLEAN NOT NULL DEFAULT false, -- Is this reviewer required?
    reviewed_at TIMESTAMPTZ,
    
    -- Audit
    added_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    added_by TEXT REFERENCES users(id) ON DELETE SET NULL,
    
    CONSTRAINT pr_reviewers_unique UNIQUE(pr_id, user_id)
);

CREATE INDEX idx_pr_reviewers_pr ON pr_reviewers(pr_id);
CREATE INDEX idx_pr_reviewers_user ON pr_reviewers(user_id);
CREATE INDEX idx_pr_reviewers_status ON pr_reviewers(status);
CREATE INDEX idx_pr_reviewers_pending ON pr_reviewers(pr_id, status) WHERE status = 'pending';

COMMENT ON TABLE pr_reviewers IS 'Reviewers assigned to pull requests';

-- ============================================================================
-- PR Reviews Table
-- ============================================================================
-- Individual review submissions
CREATE TABLE IF NOT EXISTS pr_reviews (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pr_id UUID NOT NULL REFERENCES pull_requests(id) ON DELETE CASCADE,
    reviewer_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Review decision
    decision TEXT NOT NULL CHECK (decision IN ('approve', 'request_changes', 'comment')),
    
    -- Review content
    summary TEXT, -- Overall review summary
    body TEXT, -- Detailed review comments
    
    -- Review metadata
    reviewed_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_pr_reviews_pr ON pr_reviews(pr_id, reviewed_at DESC);
CREATE INDEX idx_pr_reviews_reviewer ON pr_reviews(reviewer_id);
CREATE INDEX idx_pr_reviews_decision ON pr_reviews(decision);

COMMENT ON TABLE pr_reviews IS 'Individual review submissions for pull requests';

-- ============================================================================
-- PR Comments Table
-- ============================================================================
-- Comments and discussion on pull requests
CREATE TABLE IF NOT EXISTS pr_comments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pr_id UUID NOT NULL REFERENCES pull_requests(id) ON DELETE CASCADE,
    
    -- Comment metadata
    comment_type TEXT NOT NULL DEFAULT 'general' CHECK (comment_type IN (
        'general',      -- General comment
        'review',       -- Part of review
        'change_request', -- Specific change request
        'approval',     -- Approval comment
        'status_update' -- Status change comment
    )),
    
    -- Comment content
    body TEXT NOT NULL,
    
    -- Threading
    parent_comment_id UUID REFERENCES pr_comments(id) ON DELETE CASCADE,
    thread_resolved BOOLEAN NOT NULL DEFAULT false,
    
    -- Entity reference (commenting on specific change)
    entity_type TEXT,
    entity_id UUID,
    
    -- Author
    author_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Reactions (like GitHub reactions)
    reactions JSONB DEFAULT '{}', -- {thumbs_up: 5, heart: 2, etc.}
    
    -- Audit
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    edited BOOLEAN NOT NULL DEFAULT false
);

CREATE INDEX idx_pr_comments_pr ON pr_comments(pr_id, created_at);
CREATE INDEX idx_pr_comments_author ON pr_comments(author_id);
CREATE INDEX idx_pr_comments_parent ON pr_comments(parent_comment_id) WHERE parent_comment_id IS NOT NULL;
CREATE INDEX idx_pr_comments_unresolved ON pr_comments(pr_id, thread_resolved) WHERE thread_resolved = false;

COMMENT ON TABLE pr_comments IS 'Comments and discussion on pull requests';

-- ============================================================================
-- PR Attached Files Table
-- ============================================================================
-- Files attached to PRs (reports, photos, documents)
CREATE TABLE IF NOT EXISTS pr_files (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pr_id UUID NOT NULL REFERENCES pull_requests(id) ON DELETE CASCADE,
    
    -- File metadata
    filename TEXT NOT NULL,
    file_path TEXT NOT NULL, -- Storage path
    file_size BIGINT NOT NULL,
    file_type TEXT, -- pdf, jpg, csv, etc.
    mime_type TEXT,
    
    -- File categorization
    file_category TEXT CHECK (file_category IN (
        'commissioning_report',
        'test_results',
        'as_built_drawing',
        'photo',
        'invoice',
        'warranty',
        'manual',
        'other'
    )),
    
    -- Upload metadata
    uploaded_by TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    uploaded_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- Description
    description TEXT
);

CREATE INDEX idx_pr_files_pr ON pr_files(pr_id);
CREATE INDEX idx_pr_files_uploaded_by ON pr_files(uploaded_by);
CREATE INDEX idx_pr_files_category ON pr_files(file_category);

COMMENT ON TABLE pr_files IS 'Files attached to pull requests (reports, photos, documents)';

-- ============================================================================
-- PR Assignment Rules Table
-- ============================================================================
-- Rules for automatic PR assignment based on equipment type, location, etc.
CREATE TABLE IF NOT EXISTS pr_assignment_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    repository_id UUID NOT NULL REFERENCES building_repositories(id) ON DELETE CASCADE,
    
    -- Rule identification
    name TEXT NOT NULL,
    description TEXT,
    enabled BOOLEAN NOT NULL DEFAULT true,
    priority INTEGER NOT NULL DEFAULT 0, -- Higher priority rules checked first
    
    -- Matching criteria
    equipment_type TEXT, -- 'hvac', 'electrical', 'plumbing', etc.
    room_type TEXT,
    floor_number INTEGER,
    pr_type TEXT,
    priority_level TEXT,
    
    -- Assignment action
    assign_to_user TEXT REFERENCES users(id) ON DELETE SET NULL,
    assign_to_team TEXT,
    notify_users UUID[], -- Additional users to notify
    
    -- Rule metadata
    metadata JSONB DEFAULT '{}',
    
    -- Audit
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by TEXT REFERENCES users(id) ON DELETE SET NULL
);

CREATE INDEX idx_pr_assignment_rules_repo ON pr_assignment_rules(repository_id);
CREATE INDEX idx_pr_assignment_rules_enabled ON pr_assignment_rules(enabled) WHERE enabled = true;
CREATE INDEX idx_pr_assignment_rules_equipment ON pr_assignment_rules(equipment_type) WHERE equipment_type IS NOT NULL;
CREATE INDEX idx_pr_assignment_rules_priority ON pr_assignment_rules(priority DESC);

COMMENT ON TABLE pr_assignment_rules IS 'Auto-assignment rules for pull requests based on equipment type, location, etc.';

-- ============================================================================
-- PR Activity Log Table
-- ============================================================================
-- Activity feed for PRs (status changes, assignments, merges)
CREATE TABLE IF NOT EXISTS pr_activity_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pr_id UUID NOT NULL REFERENCES pull_requests(id) ON DELETE CASCADE,
    
    -- Activity type
    activity_type TEXT NOT NULL CHECK (activity_type IN (
        'created',
        'assigned',
        'review_requested',
        'reviewed',
        'approved',
        'changes_requested',
        'commented',
        'status_changed',
        'merged',
        'closed',
        'reopened',
        'labeled',
        'unlabeled',
        'file_attached'
    )),
    
    -- Activity details
    details TEXT,
    metadata JSONB DEFAULT '{}',
    
    -- Actor
    actor_id TEXT REFERENCES users(id) ON DELETE SET NULL,
    
    -- Timestamp
    occurred_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_pr_activity_pr ON pr_activity_log(pr_id, occurred_at DESC);
CREATE INDEX idx_pr_activity_actor ON pr_activity_log(actor_id) WHERE actor_id IS NOT NULL;
CREATE INDEX idx_pr_activity_type ON pr_activity_log(activity_type);

COMMENT ON TABLE pr_activity_log IS 'Activity feed for pull requests (like GitHub activity timeline)';

-- ============================================================================
-- Update triggers
-- ============================================================================
CREATE OR REPLACE FUNCTION update_pr_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER pull_requests_updated_at
    BEFORE UPDATE ON pull_requests
    FOR EACH ROW
    EXECUTE FUNCTION update_pr_updated_at();

CREATE TRIGGER pr_comments_updated_at
    BEFORE UPDATE ON pr_comments
    FOR EACH ROW
    EXECUTE FUNCTION update_pr_updated_at();

-- ============================================================================
-- Trigger: Log PR activity on status changes
-- ============================================================================
CREATE OR REPLACE FUNCTION log_pr_status_change()
RETURNS TRIGGER AS $$
BEGIN
    IF (TG_OP = 'UPDATE' AND OLD.status != NEW.status) THEN
        INSERT INTO pr_activity_log (pr_id, activity_type, details, metadata)
        VALUES (
            NEW.id,
            'status_changed',
            format('Status changed from %s to %s', OLD.status, NEW.status),
            jsonb_build_object('old_status', OLD.status, 'new_status', NEW.status)
        );
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER pull_requests_status_change
    AFTER UPDATE ON pull_requests
    FOR EACH ROW
    EXECUTE FUNCTION log_pr_status_change();

-- ============================================================================
-- Views for common queries
-- ============================================================================

-- Open PRs with reviewer status
CREATE OR REPLACE VIEW v_open_pull_requests AS
SELECT 
    pr.id,
    pr.number,
    pr.title,
    pr.pr_type,
    pr.priority,
    pr.status,
    pr.assigned_to,
    pr.created_by,
    pr.created_at,
    pr.due_date,
    sb.name as source_branch_name,
    tb.name as target_branch_name,
    COUNT(DISTINCT prr.user_id) as total_reviewers,
    COUNT(DISTINCT CASE WHEN prr.status = 'approved' THEN prr.user_id END) as approved_count,
    COUNT(DISTINCT CASE WHEN prr.status = 'changes_requested' THEN prr.user_id END) as changes_requested_count
FROM pull_requests pr
JOIN repository_branches sb ON sb.id = pr.source_branch_id
JOIN repository_branches tb ON tb.id = pr.target_branch_id
LEFT JOIN pr_reviewers prr ON prr.pr_id = pr.id
WHERE pr.status IN ('open', 'in_review', 'approved')
GROUP BY pr.id, sb.name, tb.name;

COMMENT ON VIEW v_open_pull_requests IS 'Open PRs with review status summary';

-- PR dashboard view
CREATE OR REPLACE VIEW v_pr_dashboard AS
SELECT 
    pr.repository_id,
    COUNT(*) FILTER (WHERE pr.status = 'open') as open_count,
    COUNT(*) FILTER (WHERE pr.status = 'approved') as approved_count,
    COUNT(*) FILTER (WHERE pr.status = 'in_review') as in_review_count,
    COUNT(*) FILTER (WHERE pr.priority IN ('urgent', 'emergency')) as urgent_count,
    COUNT(*) FILTER (WHERE pr.due_date < NOW() AND pr.status NOT IN ('merged', 'closed')) as overdue_count
FROM pull_requests pr
GROUP BY pr.repository_id;

COMMENT ON VIEW v_pr_dashboard IS 'PR statistics dashboard by repository';

-- ============================================================================
-- Schema documentation
-- ============================================================================
COMMENT ON SCHEMA public IS 'ArxOS spatial database schema - Migration 016 applied (Pull Requests)';

