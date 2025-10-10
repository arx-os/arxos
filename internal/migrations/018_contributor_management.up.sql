-- Migration 018: Contributor Management System
-- Description: Multi-user access control, teams, and permissions for building repositories
-- This enables GitHub-style collaboration with role-based access
-- Author: ArxOS Team
-- Date: 2025-01-15

-- ============================================================================
-- Repository Contributors Table
-- ============================================================================
-- Links users to repositories with specific roles
CREATE TABLE IF NOT EXISTS repository_contributors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    repository_id UUID NOT NULL REFERENCES building_repositories(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Role in repository
    role TEXT NOT NULL DEFAULT 'reader' CHECK (role IN (
        'owner',        -- Full control, can delete repository
        'admin',        -- Can manage settings, contributors
        'maintainer',   -- Can merge PRs, manage branches
        'contributor',  -- Can create branches, PRs, issues
        'reporter',     -- Can create issues only
        'reader'        -- Read-only access
    )),
    
    -- Permissions (granular control beyond role)
    can_read BOOLEAN NOT NULL DEFAULT true,
    can_write BOOLEAN NOT NULL DEFAULT false,
    can_create_branch BOOLEAN NOT NULL DEFAULT false,
    can_create_pr BOOLEAN NOT NULL DEFAULT false,
    can_merge_pr BOOLEAN NOT NULL DEFAULT false,
    can_approve_pr BOOLEAN NOT NULL DEFAULT false,
    can_delete_branch BOOLEAN NOT NULL DEFAULT false,
    can_manage_issues BOOLEAN NOT NULL DEFAULT false,
    can_assign_issues BOOLEAN NOT NULL DEFAULT false,
    can_manage_contributors BOOLEAN NOT NULL DEFAULT false,
    can_manage_settings BOOLEAN NOT NULL DEFAULT false,
    
    -- Access scope (what parts of building they can access)
    scope_all_buildings BOOLEAN NOT NULL DEFAULT true,
    scope_building_ids UUID[], -- Specific buildings if not all
    scope_floor_ids UUID[], -- Specific floors
    scope_room_types TEXT[], -- Specific room types (electrical, hvac, etc.)
    scope_equipment_types TEXT[], -- Specific equipment types
    
    -- Invitation/approval metadata
    invited_by UUID REFERENCES users(id) ON DELETE SET NULL,
    invited_at TIMESTAMPTZ,
    accepted_at TIMESTAMPTZ,
    
    -- Status
    status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'suspended')),
    
    -- Metadata
    notes TEXT, -- Why this user has access
    metadata JSONB DEFAULT '{}',
    
    -- Audit
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    CONSTRAINT repository_contributors_unique UNIQUE(repository_id, user_id)
);

CREATE INDEX idx_repository_contributors_repo ON repository_contributors(repository_id);
CREATE INDEX idx_repository_contributors_user ON repository_contributors(user_id);
CREATE INDEX idx_repository_contributors_role ON repository_contributors(role);
CREATE INDEX idx_repository_contributors_status ON repository_contributors(status) WHERE status = 'active';

COMMENT ON TABLE repository_contributors IS 'Users with access to building repositories (GitHub-style collaborators)';
COMMENT ON COLUMN repository_contributors.scope_building_ids IS 'Limit access to specific buildings (NULL = all)';

-- ============================================================================
-- Teams Table
-- ============================================================================
-- Groups of users (electricians, hvac-contractors, facility-managers, etc.)
CREATE TABLE IF NOT EXISTS teams (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    repository_id UUID REFERENCES building_repositories(id) ON DELETE CASCADE,
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    
    -- Team identification
    slug TEXT NOT NULL, -- URL-friendly: "electrician-team", "hvac-contractors"
    name TEXT NOT NULL, -- Display name: "Electrician Team"
    description TEXT,
    
    -- Team type
    team_type TEXT CHECK (team_type IN (
        'internal',     -- Building staff
        'contractor',   -- External contractors
        'vendor',       -- Vendor/supplier
        'facilities',   -- Facilities management
        'engineering',  -- Engineering team
        'custom'        -- Custom team
    )),
    
    -- Default permissions for team members
    default_role TEXT DEFAULT 'contributor',
    
    -- Team lead
    lead_user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    
    -- Specialization (what this team works on)
    specializations TEXT[], -- ['electrical', 'hvac', 'plumbing']
    
    -- Metadata
    color TEXT, -- Hex color for UI
    avatar_url TEXT,
    metadata JSONB DEFAULT '{}',
    
    -- Audit
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    CONSTRAINT teams_unique_slug UNIQUE(repository_id, slug),
    CONSTRAINT teams_scope CHECK (repository_id IS NOT NULL OR organization_id IS NOT NULL)
);

CREATE INDEX idx_teams_repo ON teams(repository_id) WHERE repository_id IS NOT NULL;
CREATE INDEX idx_teams_org ON teams(organization_id) WHERE organization_id IS NOT NULL;
CREATE INDEX idx_teams_slug ON teams(slug);
CREATE INDEX idx_teams_type ON teams(team_type);
CREATE INDEX idx_teams_lead ON teams(lead_user_id) WHERE lead_user_id IS NOT NULL;

COMMENT ON TABLE teams IS 'Teams for organizing users (electricians, contractors, etc.)';

-- ============================================================================
-- Team Members Table
-- ============================================================================
-- Membership in teams
CREATE TABLE IF NOT EXISTS team_members (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    team_id UUID NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Role in team
    team_role TEXT NOT NULL DEFAULT 'member' CHECK (team_role IN (
        'lead',      -- Team leader
        'admin',     -- Team administrator
        'member'     -- Regular member
    )),
    
    -- Status
    status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'inactive')),
    
    -- Audit
    added_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    added_by UUID REFERENCES users(id) ON DELETE SET NULL,
    
    CONSTRAINT team_members_unique UNIQUE(team_id, user_id)
);

CREATE INDEX idx_team_members_team ON team_members(team_id);
CREATE INDEX idx_team_members_user ON team_members(user_id);
CREATE INDEX idx_team_members_active ON team_members(team_id, status) WHERE status = 'active';

COMMENT ON TABLE team_members IS 'Team membership linking users to teams';

-- ============================================================================
-- Access Rules Table
-- ============================================================================
-- Automated access control rules (auto-add to team based on conditions)
CREATE TABLE IF NOT EXISTS access_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    repository_id UUID NOT NULL REFERENCES building_repositories(id) ON DELETE CASCADE,
    
    -- Rule identification
    name TEXT NOT NULL,
    description TEXT,
    enabled BOOLEAN NOT NULL DEFAULT true,
    priority INTEGER NOT NULL DEFAULT 0, -- Higher priority rules evaluated first
    
    -- Conditions (when does this rule apply?)
    condition_user_domain TEXT, -- Email domain: "@company.com"
    condition_user_role TEXT, -- User role in organization
    condition_user_tags TEXT[], -- User tags
    condition_equipment_type TEXT, -- Grant access based on equipment expertise
    condition_specialization TEXT, -- User specialization
    
    -- Actions (what happens when rule matches?)
    action_add_to_team UUID REFERENCES teams(id) ON DELETE CASCADE,
    action_grant_role TEXT, -- Role to grant
    action_notify_admin BOOLEAN NOT NULL DEFAULT true,
    action_require_approval BOOLEAN NOT NULL DEFAULT false,
    
    -- Metadata
    metadata JSONB DEFAULT '{}',
    
    -- Audit
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by UUID REFERENCES users(id) ON DELETE SET NULL
);

CREATE INDEX idx_access_rules_repo ON access_rules(repository_id);
CREATE INDEX idx_access_rules_enabled ON access_rules(enabled) WHERE enabled = true;
CREATE INDEX idx_access_rules_priority ON access_rules(priority DESC);

COMMENT ON TABLE access_rules IS 'Automated access control rules (auto-grant permissions based on conditions)';

-- ============================================================================
-- Protected Branches Table Enhancement
-- ============================================================================
-- Add protection rules to branches (who can push, merge, etc.)
CREATE TABLE IF NOT EXISTS branch_protection_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    repository_id UUID NOT NULL REFERENCES building_repositories(id) ON DELETE CASCADE,
    branch_pattern TEXT NOT NULL, -- "main", "contractor/*", etc.
    
    -- Protection settings
    require_pr BOOLEAN NOT NULL DEFAULT false, -- Require PR to merge
    require_reviews INTEGER NOT NULL DEFAULT 0, -- Minimum reviews needed
    require_review_from_owners BOOLEAN NOT NULL DEFAULT false,
    dismiss_stale_reviews BOOLEAN NOT NULL DEFAULT false,
    require_status_checks BOOLEAN NOT NULL DEFAULT false,
    require_up_to_date BOOLEAN NOT NULL DEFAULT false,
    
    -- Who can push/merge?
    allow_force_push BOOLEAN NOT NULL DEFAULT false,
    allow_deletions BOOLEAN NOT NULL DEFAULT false,
    restrict_push_to_admins BOOLEAN NOT NULL DEFAULT false,
    
    -- Auto-merge settings
    allow_auto_merge BOOLEAN NOT NULL DEFAULT false,
    auto_merge_method TEXT CHECK (auto_merge_method IN ('merge', 'squash', 'rebase', NULL)),
    
    -- Allowed users/teams
    allowed_push_user_ids UUID[],
    allowed_push_team_ids UUID[],
    allowed_merge_user_ids UUID[],
    allowed_merge_team_ids UUID[],
    
    -- Metadata
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_branch_protection_repo ON branch_protection_rules(repository_id);
CREATE INDEX idx_branch_protection_pattern ON branch_protection_rules(branch_pattern);

COMMENT ON TABLE branch_protection_rules IS 'Branch protection rules (who can push/merge to protected branches)';

-- ============================================================================
-- Access Audit Log Table
-- ============================================================================
-- Log all access control changes
CREATE TABLE IF NOT EXISTS access_audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    repository_id UUID REFERENCES building_repositories(id) ON DELETE CASCADE,
    
    -- Action details
    action TEXT NOT NULL CHECK (action IN (
        'contributor_added',
        'contributor_removed',
        'role_changed',
        'permissions_changed',
        'team_created',
        'team_deleted',
        'team_member_added',
        'team_member_removed',
        'access_granted',
        'access_revoked',
        'branch_protected',
        'branch_unprotected'
    )),
    
    -- Subjects (who/what was affected)
    subject_user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    subject_team_id UUID REFERENCES teams(id) ON DELETE SET NULL,
    
    -- Details
    details TEXT,
    old_value JSONB,
    new_value JSONB,
    
    -- Actor
    actor_id UUID REFERENCES users(id) ON DELETE SET NULL,
    actor_ip TEXT,
    
    -- Timestamp
    occurred_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_access_audit_repo ON access_audit_log(repository_id, occurred_at DESC);
CREATE INDEX idx_access_audit_action ON access_audit_log(action);
CREATE INDEX idx_access_audit_subject_user ON access_audit_log(subject_user_id) WHERE subject_user_id IS NOT NULL;
CREATE INDEX idx_access_audit_actor ON access_audit_log(actor_id) WHERE actor_id IS NOT NULL;

COMMENT ON TABLE access_audit_log IS 'Audit log for all access control changes';

-- ============================================================================
-- Create default teams for existing repositories
-- ============================================================================
-- Every repository should have default teams
INSERT INTO teams (repository_id, slug, name, description, team_type, specializations, created_at)
SELECT 
    br.id as repository_id,
    unnest(ARRAY['facility-managers', 'building-staff', 'contractors', 'vendors']) as slug,
    unnest(ARRAY['Facility Managers', 'Building Staff', 'Contractors', 'Vendors']) as name,
    unnest(ARRAY[
        'Facility management team',
        'Building staff and custodians',
        'External contractors',
        'Vendors and suppliers'
    ]) as description,
    unnest(ARRAY['facilities', 'internal', 'contractor', 'vendor']) as team_type,
    unnest(ARRAY[
        ARRAY['facilities', 'management']::TEXT[],
        ARRAY['maintenance', 'operations']::TEXT[],
        ARRAY[]::TEXT[],
        ARRAY[]::TEXT[]
    ]) as specializations,
    NOW() as created_at
FROM building_repositories br
WHERE NOT EXISTS (
    SELECT 1 FROM teams t WHERE t.repository_id = br.id AND t.slug = 'facility-managers'
)
ON CONFLICT DO NOTHING;

-- ============================================================================
-- Functions and Triggers
-- ============================================================================

-- Auto-update updated_at
CREATE OR REPLACE FUNCTION update_contributor_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER repository_contributors_updated_at
    BEFORE UPDATE ON repository_contributors
    FOR EACH ROW
    EXECUTE FUNCTION update_contributor_updated_at();

CREATE TRIGGER teams_updated_at
    BEFORE UPDATE ON teams
    FOR EACH ROW
    EXECUTE FUNCTION update_contributor_updated_at();

CREATE TRIGGER branch_protection_rules_updated_at
    BEFORE UPDATE ON branch_protection_rules
    FOR EACH ROW
    EXECUTE FUNCTION update_contributor_updated_at();

-- Log contributor changes
CREATE OR REPLACE FUNCTION log_contributor_change()
RETURNS TRIGGER AS $$
BEGIN
    IF (TG_OP = 'INSERT') THEN
        INSERT INTO access_audit_log (repository_id, action, subject_user_id, details, new_value, actor_id)
        VALUES (
            NEW.repository_id,
            'contributor_added',
            NEW.user_id,
            format('User added as %s', NEW.role),
            to_jsonb(NEW),
            NEW.created_by
        );
    ELSIF (TG_OP = 'UPDATE' AND OLD.role != NEW.role) THEN
        INSERT INTO access_audit_log (repository_id, action, subject_user_id, details, old_value, new_value, actor_id)
        VALUES (
            NEW.repository_id,
            'role_changed',
            NEW.user_id,
            format('Role changed from %s to %s', OLD.role, NEW.role),
            jsonb_build_object('role', OLD.role),
            jsonb_build_object('role', NEW.role),
            NEW.created_by
        );
    ELSIF (TG_OP = 'DELETE') THEN
        INSERT INTO access_audit_log (repository_id, action, subject_user_id, details, old_value)
        VALUES (
            OLD.repository_id,
            'contributor_removed',
            OLD.user_id,
            format('User removed (was %s)', OLD.role),
            to_jsonb(OLD)
        );
    END IF;
    
    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER repository_contributors_audit
    AFTER INSERT OR UPDATE OR DELETE ON repository_contributors
    FOR EACH ROW
    EXECUTE FUNCTION log_contributor_change();

-- ============================================================================
-- Views for common queries
-- ============================================================================

-- Active contributors per repository
CREATE OR REPLACE VIEW v_repository_contributors AS
SELECT 
    rc.repository_id,
    rc.user_id,
    u.email,
    u.name as user_name,
    rc.role,
    rc.status,
    rc.created_at,
    array_agg(DISTINCT t.name) FILTER (WHERE t.name IS NOT NULL) as teams
FROM repository_contributors rc
JOIN users u ON u.id = rc.user_id
LEFT JOIN team_members tm ON tm.user_id = rc.user_id
LEFT JOIN teams t ON t.id = tm.team_id AND t.repository_id = rc.repository_id
WHERE rc.status = 'active'
GROUP BY rc.repository_id, rc.user_id, u.email, u.name, rc.role, rc.status, rc.created_at;

COMMENT ON VIEW v_repository_contributors IS 'Active contributors with team memberships';

-- Team roster with members
CREATE OR REPLACE VIEW v_team_roster AS
SELECT 
    t.id as team_id,
    t.repository_id,
    t.slug as team_slug,
    t.name as team_name,
    t.team_type,
    COUNT(tm.id) FILTER (WHERE tm.status = 'active') as member_count,
    array_agg(u.email) FILTER (WHERE tm.status = 'active') as member_emails,
    t.lead_user_id,
    lead.email as lead_email
FROM teams t
LEFT JOIN team_members tm ON tm.team_id = t.id
LEFT JOIN users u ON u.id = tm.user_id
LEFT JOIN users lead ON lead.id = t.lead_user_id
GROUP BY t.id, t.repository_id, t.slug, t.name, t.team_type, t.lead_user_id, lead.email;

COMMENT ON VIEW v_team_roster IS 'Teams with member counts and rosters';

-- ============================================================================
-- Update existing tables for contributor integration
-- ============================================================================

-- Add requires_review to branches (was in domain model but not in table)
ALTER TABLE repository_branches ADD COLUMN IF NOT EXISTS requires_review BOOLEAN NOT NULL DEFAULT false;
ALTER TABLE repository_branches ADD COLUMN IF NOT EXISTS auto_delete_on_merge BOOLEAN NOT NULL DEFAULT false;

COMMENT ON COLUMN repository_branches.requires_review IS 'Whether this branch requires PR review before merging';
COMMENT ON COLUMN repository_branches.auto_delete_on_merge IS 'Auto-delete branch after PR merge';

-- ============================================================================
-- Schema documentation
-- ============================================================================
COMMENT ON SCHEMA public IS 'ArxOS spatial database schema - Migration 018 applied (Contributor Management)';

