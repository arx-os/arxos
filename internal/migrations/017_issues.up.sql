-- Migration 017: Issue Tracking System
-- Description: GitHub-style issue tracking that auto-creates branches and PRs
-- Issues represent problems/tasks reported by building staff (especially via mobile AR)
-- Author: ArxOS Team
-- Date: 2025-01-15

-- ============================================================================
-- Issues Table
-- ============================================================================
-- GitHub-style issues for building repositories
CREATE TABLE IF NOT EXISTS issues (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    repository_id UUID NOT NULL REFERENCES building_repositories(id) ON DELETE CASCADE,
    
    -- Issue identification
    number SERIAL, -- Auto-incrementing issue number per repository
    title TEXT NOT NULL,
    body TEXT, -- Issue description
    
    -- Spatial context (WHERE is the problem?)
    building_id UUID REFERENCES buildings(id) ON DELETE SET NULL,
    floor_id UUID REFERENCES floors(id) ON DELETE SET NULL,
    room_id UUID REFERENCES rooms(id) ON DELETE SET NULL,
    equipment_id UUID REFERENCES equipment(id) ON DELETE SET NULL,
    bas_point_id UUID REFERENCES bas_points(id) ON DELETE SET NULL,
    
    -- Spatial location (from AR or manual)
    location GEOMETRY(POINTZ, 4326),
    location_description TEXT, -- "Near west wall", "Above ceiling tile 5", etc.
    
    -- Issue classification
    issue_type TEXT NOT NULL DEFAULT 'problem' CHECK (issue_type IN (
        'problem',        -- Something broken/not working
        'maintenance',    -- Scheduled maintenance needed
        'improvement',    -- Improvement suggestion
        'question',       -- Question about building
        'documentation',  -- Documentation update needed
        'safety',         -- Safety concern
        'emergency'       -- Emergency issue
    )),
    
    -- Status
    status TEXT NOT NULL DEFAULT 'open' CHECK (status IN (
        'open',           -- New issue, no work started
        'in_progress',    -- Work has begun (branch/PR created)
        'resolved',       -- Work complete, PR merged
        'closed',         -- Closed without resolution
        'duplicate',      -- Duplicate of another issue
        'wont_fix'        -- Decided not to fix
    )),
    
    -- Priority (auto-elevated for safety/emergency)
    priority TEXT NOT NULL DEFAULT 'normal' CHECK (priority IN ('low', 'normal', 'high', 'urgent', 'emergency')),
    
    -- Assignment
    assigned_to UUID REFERENCES users(id) ON DELETE SET NULL,
    assigned_team TEXT,
    auto_assigned BOOLEAN NOT NULL DEFAULT false,
    
    -- Git integration
    branch_id UUID REFERENCES repository_branches(id) ON DELETE SET NULL, -- Auto-created branch
    pr_id UUID REFERENCES pull_requests(id) ON DELETE SET NULL, -- Auto-created PR
    
    -- Reporter information
    reported_by UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    reported_via TEXT CHECK (reported_via IN ('mobile_ar', 'mobile_app', 'cli', 'api', 'web', NULL)),
    
    -- Resolution
    resolved_by UUID REFERENCES users(id) ON DELETE SET NULL,
    resolved_at TIMESTAMPTZ,
    resolution_notes TEXT,
    
    -- Verification (reporter confirms fix)
    verified_by_reporter BOOLEAN NOT NULL DEFAULT false,
    verified_at TIMESTAMPTZ,
    
    -- Metadata
    metadata JSONB DEFAULT '{}',
    
    -- Audit
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    closed_at TIMESTAMPTZ
);

CREATE UNIQUE INDEX idx_issues_number ON issues(repository_id, number);
CREATE INDEX idx_issues_repo ON issues(repository_id);
CREATE INDEX idx_issues_building ON issues(building_id) WHERE building_id IS NOT NULL;
CREATE INDEX idx_issues_room ON issues(room_id) WHERE room_id IS NOT NULL;
CREATE INDEX idx_issues_equipment ON issues(equipment_id) WHERE equipment_id IS NOT NULL;
CREATE INDEX idx_issues_bas_point ON issues(bas_point_id) WHERE bas_point_id IS NOT NULL;
CREATE INDEX idx_issues_status ON issues(status) WHERE status IN ('open', 'in_progress');
CREATE INDEX idx_issues_assigned ON issues(assigned_to) WHERE assigned_to IS NOT NULL;
CREATE INDEX idx_issues_priority ON issues(priority) WHERE priority IN ('urgent', 'emergency');
CREATE INDEX idx_issues_type ON issues(issue_type);
CREATE INDEX idx_issues_location ON issues USING GIST(location) WHERE location IS NOT NULL;
CREATE INDEX idx_issues_branch ON issues(branch_id) WHERE branch_id IS NOT NULL;
CREATE INDEX idx_issues_pr ON issues(pr_id) WHERE pr_id IS NOT NULL;
CREATE INDEX idx_issues_reported_by ON issues(reported_by);
CREATE INDEX idx_issues_created ON issues(created_at DESC);

COMMENT ON TABLE issues IS 'GitHub-style issues for building repositories (problems, tasks, questions)';
COMMENT ON COLUMN issues.reported_via IS 'How issue was reported (mobile_ar = pointed phone at equipment)';
COMMENT ON COLUMN issues.verified_by_reporter IS 'Whether original reporter confirmed the fix';

-- ============================================================================
-- Issue Labels Table
-- ============================================================================
-- Labels for categorizing issues (like GitHub labels)
CREATE TABLE IF NOT EXISTS issue_labels (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    repository_id UUID NOT NULL REFERENCES building_repositories(id) ON DELETE CASCADE,
    
    -- Label definition
    name TEXT NOT NULL,
    display_name TEXT,
    description TEXT,
    color TEXT, -- Hex color code for UI
    
    -- Label category
    category TEXT CHECK (category IN ('type', 'priority', 'system', 'location', 'custom', NULL)),
    
    -- Auto-apply rules
    auto_apply_equipment_type TEXT, -- Auto-apply to issues with this equipment type
    auto_apply_issue_type TEXT,
    
    -- Usage stats
    usage_count INTEGER NOT NULL DEFAULT 0,
    
    -- Audit
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,
    
    CONSTRAINT issue_labels_unique_name UNIQUE(repository_id, name)
);

CREATE INDEX idx_issue_labels_repo ON issue_labels(repository_id);
CREATE INDEX idx_issue_labels_category ON issue_labels(category);
CREATE INDEX idx_issue_labels_name ON issue_labels(name);

COMMENT ON TABLE issue_labels IS 'Labels for categorizing issues (electrical, hvac, urgent, etc.)';

-- ============================================================================
-- Issue Label Assignments Table
-- ============================================================================
-- Many-to-many relationship between issues and labels
CREATE TABLE IF NOT EXISTS issue_label_assignments (
    issue_id UUID NOT NULL REFERENCES issues(id) ON DELETE CASCADE,
    label_id UUID NOT NULL REFERENCES issue_labels(id) ON DELETE CASCADE,
    
    -- Auto-applied or manual
    auto_applied BOOLEAN NOT NULL DEFAULT false,
    
    -- Audit
    added_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    added_by UUID REFERENCES users(id) ON DELETE SET NULL,
    
    PRIMARY KEY (issue_id, label_id)
);

CREATE INDEX idx_issue_label_assignments_issue ON issue_label_assignments(issue_id);
CREATE INDEX idx_issue_label_assignments_label ON issue_label_assignments(label_id);

-- ============================================================================
-- Issue Comments Table
-- ============================================================================
-- Comments and discussion on issues
CREATE TABLE IF NOT EXISTS issue_comments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    issue_id UUID NOT NULL REFERENCES issues(id) ON DELETE CASCADE,
    
    -- Comment content
    body TEXT NOT NULL,
    
    -- Comment type
    comment_type TEXT NOT NULL DEFAULT 'comment' CHECK (comment_type IN (
        'comment',        -- Regular comment
        'status_update',  -- Status change comment
        'assignment',     -- Assignment notification
        'resolution',     -- Resolution comment
        'verification'    -- Reporter verification
    )),
    
    -- Author
    author_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Threading
    parent_comment_id UUID REFERENCES issue_comments(id) ON DELETE CASCADE,
    
    -- Reactions
    reactions JSONB DEFAULT '{}',
    
    -- Audit
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    edited BOOLEAN NOT NULL DEFAULT false
);

CREATE INDEX idx_issue_comments_issue ON issue_comments(issue_id, created_at);
CREATE INDEX idx_issue_comments_author ON issue_comments(author_id);
CREATE INDEX idx_issue_comments_parent ON issue_comments(parent_comment_id) WHERE parent_comment_id IS NOT NULL;

COMMENT ON TABLE issue_comments IS 'Comments and discussion on issues';

-- ============================================================================
-- Issue Photos Table
-- ============================================================================
-- Photos attached to issues (especially from mobile AR)
CREATE TABLE IF NOT EXISTS issue_photos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    issue_id UUID NOT NULL REFERENCES issues(id) ON DELETE CASCADE,
    
    -- Photo metadata
    filename TEXT NOT NULL,
    file_path TEXT NOT NULL,
    file_size BIGINT NOT NULL,
    mime_type TEXT,
    
    -- Photo capture metadata (from mobile)
    captured_location GEOMETRY(POINTZ, 4326), -- Where photo was taken
    captured_at TIMESTAMPTZ,
    device_info TEXT, -- Device model/OS
    
    -- Photo content (what does it show?)
    photo_type TEXT CHECK (photo_type IN (
        'problem',        -- Shows the problem
        'before',         -- Before repair
        'during',         -- Work in progress
        'after',          -- After repair
        'context',        -- Context/location
        'equipment_label' -- Equipment nameplate/label
    )),
    
    -- Description
    caption TEXT,
    
    -- Upload metadata
    uploaded_by UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    uploaded_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_issue_photos_issue ON issue_photos(issue_id);
CREATE INDEX idx_issue_photos_type ON issue_photos(photo_type);
CREATE INDEX idx_issue_photos_uploaded_by ON issue_photos(uploaded_by);

COMMENT ON TABLE issue_photos IS 'Photos attached to issues (from mobile AR or manual upload)';

-- ============================================================================
-- Issue Activity Log Table
-- ============================================================================
-- Activity timeline for issues
CREATE TABLE IF NOT EXISTS issue_activity_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    issue_id UUID NOT NULL REFERENCES issues(id) ON DELETE CASCADE,
    
    -- Activity type
    activity_type TEXT NOT NULL CHECK (activity_type IN (
        'created',
        'assigned',
        'status_changed',
        'priority_changed',
        'labeled',
        'unlabeled',
        'commented',
        'branch_created',
        'pr_created',
        'pr_merged',
        'resolved',
        'verified',
        'closed',
        'reopened'
    )),
    
    -- Activity details
    details TEXT,
    metadata JSONB DEFAULT '{}',
    
    -- Actor
    actor_id UUID REFERENCES users(id) ON DELETE SET NULL,
    
    -- Timestamp
    occurred_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_issue_activity_issue ON issue_activity_log(issue_id, occurred_at DESC);
CREATE INDEX idx_issue_activity_type ON issue_activity_log(activity_type);
CREATE INDEX idx_issue_activity_actor ON issue_activity_log(actor_id) WHERE actor_id IS NOT NULL;

COMMENT ON TABLE issue_activity_log IS 'Activity timeline for issues (like GitHub issue timeline)';

-- ============================================================================
-- Create default labels for new repositories
-- ============================================================================
-- Common labels that every repository should have
INSERT INTO issue_labels (repository_id, name, display_name, description, color, category)
SELECT 
    br.id as repository_id,
    unnest(ARRAY['electrical', 'hvac', 'plumbing', 'structural', 'safety', 'urgent']) as name,
    unnest(ARRAY['Electrical', 'HVAC', 'Plumbing', 'Structural', 'Safety', 'Urgent']) as display_name,
    unnest(ARRAY[
        'Electrical system issues',
        'HVAC and climate control',
        'Plumbing and water systems',
        'Structural issues',
        'Safety concerns',
        'Urgent priority'
    ]) as description,
    unnest(ARRAY['#FFD700', '#1E90FF', '#32CD32', '#8B4513', '#FF0000', '#FF4500']) as color,
    unnest(ARRAY['system', 'system', 'system', 'system', 'priority', 'priority']) as category
FROM building_repositories br
WHERE NOT EXISTS (
    SELECT 1 FROM issue_labels il WHERE il.repository_id = br.id AND il.name = 'electrical'
)
ON CONFLICT DO NOTHING;

-- ============================================================================
-- Triggers
-- ============================================================================

-- Auto-update updated_at
CREATE OR REPLACE FUNCTION update_issue_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER issues_updated_at
    BEFORE UPDATE ON issues
    FOR EACH ROW
    EXECUTE FUNCTION update_issue_updated_at();

CREATE TRIGGER issue_comments_updated_at
    BEFORE UPDATE ON issue_comments
    FOR EACH ROW
    EXECUTE FUNCTION update_issue_updated_at();

-- Log issue status changes
CREATE OR REPLACE FUNCTION log_issue_status_change()
RETURNS TRIGGER AS $$
BEGIN
    IF (TG_OP = 'UPDATE' AND OLD.status != NEW.status) THEN
        INSERT INTO issue_activity_log (issue_id, activity_type, details, metadata)
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

CREATE TRIGGER issues_status_change
    AFTER UPDATE ON issues
    FOR EACH ROW
    EXECUTE FUNCTION log_issue_status_change();

-- Log issue priority changes (safety/emergency auto-escalation)
CREATE OR REPLACE FUNCTION log_issue_priority_change()
RETURNS TRIGGER AS $$
BEGIN
    IF (TG_OP = 'UPDATE' AND OLD.priority != NEW.priority) THEN
        INSERT INTO issue_activity_log (issue_id, activity_type, details, metadata)
        VALUES (
            NEW.id,
            'priority_changed',
            format('Priority changed from %s to %s', OLD.priority, NEW.priority),
            jsonb_build_object('old_priority', OLD.priority, 'new_priority', NEW.priority)
        );
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER issues_priority_change
    AFTER UPDATE ON issues
    FOR EACH ROW
    EXECUTE FUNCTION log_issue_priority_change();

-- ============================================================================
-- Views for common queries
-- ============================================================================

-- Open issues with spatial context
CREATE OR REPLACE VIEW v_open_issues AS
SELECT 
    i.id,
    i.repository_id,
    i.number,
    i.title,
    i.issue_type,
    i.priority,
    i.status,
    i.assigned_to,
    i.assigned_team,
    i.reported_by,
    i.reported_via,
    i.created_at,
    b.name as building_name,
    f.name as floor_name,
    r.name as room_name,
    e.name as equipment_name,
    COUNT(DISTINCT ic.id) as comment_count,
    COUNT(DISTINCT ip.id) as photo_count,
    array_agg(DISTINCT il.name) FILTER (WHERE il.name IS NOT NULL) as labels
FROM issues i
LEFT JOIN buildings b ON b.id = i.building_id
LEFT JOIN floors f ON f.id = i.floor_id
LEFT JOIN rooms r ON r.id = i.room_id
LEFT JOIN equipment e ON e.id = i.equipment_id
LEFT JOIN issue_comments ic ON ic.issue_id = i.id
LEFT JOIN issue_photos ip ON ip.issue_id = i.id
LEFT JOIN issue_label_assignments ila ON ila.issue_id = i.id
LEFT JOIN issue_labels il ON il.id = ila.label_id
WHERE i.status IN ('open', 'in_progress')
GROUP BY i.id, b.name, f.name, r.name, e.name;

COMMENT ON VIEW v_open_issues IS 'Open issues with spatial context and counts';

-- Issue dashboard statistics
CREATE OR REPLACE VIEW v_issue_dashboard AS
SELECT 
    i.repository_id,
    COUNT(*) FILTER (WHERE i.status = 'open') as open_count,
    COUNT(*) FILTER (WHERE i.status = 'in_progress') as in_progress_count,
    COUNT(*) FILTER (WHERE i.status = 'resolved') as resolved_count,
    COUNT(*) FILTER (WHERE i.priority IN ('urgent', 'emergency')) as urgent_count,
    COUNT(*) FILTER (WHERE i.issue_type = 'safety') as safety_count,
    COUNT(*) FILTER (WHERE i.verified_by_reporter = false AND i.status = 'resolved') as unverified_count,
    AVG(EXTRACT(EPOCH FROM (i.resolved_at - i.created_at))) FILTER (WHERE i.resolved_at IS NOT NULL) as avg_resolution_time_seconds
FROM issues i
GROUP BY i.repository_id;

COMMENT ON VIEW v_issue_dashboard IS 'Issue statistics dashboard by repository';

-- Issues reported via AR (for mobile integration)
CREATE OR REPLACE VIEW v_ar_reported_issues AS
SELECT 
    i.*,
    ST_X(i.location::geometry) as location_x,
    ST_Y(i.location::geometry) as location_y,
    ST_Z(i.location::geometry) as location_z
FROM issues i
WHERE i.reported_via = 'mobile_ar' AND i.location IS NOT NULL;

COMMENT ON VIEW v_ar_reported_issues IS 'Issues reported via mobile AR with 3D coordinates';

-- ============================================================================
-- Schema documentation
-- ============================================================================
COMMENT ON SCHEMA public IS 'ArxOS spatial database schema - Migration 017 applied (Issue Tracking)';

