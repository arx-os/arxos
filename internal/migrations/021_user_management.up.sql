-- Migration 006: User Management System
-- Description: Creates comprehensive user, session, and organization management tables

BEGIN;

-- ============================================================================
-- USERS TABLE
-- ============================================================================

-- Add new columns to existing users table from migration 001
-- Note: id column remains TEXT to avoid breaking existing data
ALTER TABLE users
  ADD COLUMN IF NOT EXISTS email_verified BOOLEAN DEFAULT false,
  ADD COLUMN IF NOT EXISTS phone TEXT,
  ADD COLUMN IF NOT EXISTS avatar_url TEXT,
  ADD COLUMN IF NOT EXISTS preferences JSONB DEFAULT '{}',
  ADD COLUMN IF NOT EXISTS metadata JSONB DEFAULT '{}',
  ADD COLUMN IF NOT EXISTS failed_login_attempts INT DEFAULT 0,
  ADD COLUMN IF NOT EXISTS locked_until TIMESTAMPTZ;

-- Update role check constraint if needed (skip if causes issues)
DO $$
BEGIN
    ALTER TABLE users DROP CONSTRAINT IF EXISTS users_role_check;
    ALTER TABLE users ADD CONSTRAINT users_role_check
        CHECK (role IN ('admin', 'manager', 'technician', 'viewer', 'user'));
EXCEPTION
    WHEN OTHERS THEN
        RAISE NOTICE 'Could not update users role constraint, skipping...';
END $$;

-- Create indices for users (IF NOT EXISTS for idempotency)
CREATE INDEX IF NOT EXISTS idx_users_is_active ON users(is_active);
CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at);

-- ============================================================================
-- ORGANIZATIONS TABLE
-- ============================================================================

-- Add new columns to existing organizations table from migration 001
ALTER TABLE organizations
  ADD COLUMN IF NOT EXISTS username TEXT UNIQUE,
  ADD COLUMN IF NOT EXISTS website TEXT,
  ADD COLUMN IF NOT EXISTS logo_url TEXT,
  ADD COLUMN IF NOT EXISTS address TEXT,
  ADD COLUMN IF NOT EXISTS city TEXT,
  ADD COLUMN IF NOT EXISTS state TEXT,
  ADD COLUMN IF NOT EXISTS country TEXT,
  ADD COLUMN IF NOT EXISTS postal_code TEXT,
  ADD COLUMN IF NOT EXISTS phone TEXT,
  ADD COLUMN IF NOT EXISTS email TEXT,
  ADD COLUMN IF NOT EXISTS settings JSONB DEFAULT '{}',
  ADD COLUMN IF NOT EXISTS metadata JSONB DEFAULT '{}',
  ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT true,
  ADD COLUMN IF NOT EXISTS subscription_tier TEXT DEFAULT 'free',
  ADD COLUMN IF NOT EXISTS subscription_expires_at TIMESTAMPTZ;

-- Update id column to UUID if it's still TEXT (from migration 001)
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'organizations'
        AND column_name = 'id'
        AND data_type = 'text'
    ) THEN
        -- Can't easily convert TEXT to UUID if data exists, so we'll skip for now
        -- This would need custom migration logic for existing data
        RAISE NOTICE 'Organizations table id column is TEXT, skipping UUID conversion';
    END IF;
END $$;

-- Create indices for organizations
CREATE INDEX IF NOT EXISTS idx_organizations_username ON organizations(username);
CREATE INDEX IF NOT EXISTS idx_organizations_is_active ON organizations(is_active);

-- ============================================================================
-- ORGANIZATION MEMBERS TABLE (Many-to-Many relationship)
-- ============================================================================

CREATE TABLE IF NOT EXISTS organization_members (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id TEXT NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role TEXT NOT NULL DEFAULT 'member' CHECK (role IN ('owner', 'admin', 'member', 'viewer')),
    permissions JSONB DEFAULT '{}',
    joined_at TIMESTAMPTZ DEFAULT NOW(),
    invited_by TEXT REFERENCES users(id),
    UNIQUE(organization_id, user_id)
);

-- Create indices for organization members
CREATE INDEX IF NOT EXISTS idx_org_members_org_id ON organization_members(organization_id);
CREATE INDEX IF NOT EXISTS idx_org_members_user_id ON organization_members(user_id);
CREATE INDEX IF NOT EXISTS idx_org_members_role ON organization_members(role);

-- ============================================================================
-- USER SESSIONS TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS user_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token TEXT UNIQUE NOT NULL,
    refresh_token TEXT UNIQUE NOT NULL,
    ip_address INET,
    user_agent TEXT,
    device_info JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT true,
    expires_at TIMESTAMPTZ NOT NULL,
    refresh_expires_at TIMESTAMPTZ NOT NULL,
    last_activity TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indices for sessions
CREATE INDEX IF NOT EXISTS idx_sessions_token ON user_sessions(token);
CREATE INDEX IF NOT EXISTS idx_sessions_refresh_token ON user_sessions(refresh_token);
CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON user_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_expires_at ON user_sessions(expires_at);
CREATE INDEX IF NOT EXISTS idx_sessions_is_active ON user_sessions(is_active);

-- ============================================================================
-- PASSWORD RESET TOKENS TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS password_reset_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token TEXT UNIQUE NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    used_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indices for password reset tokens
CREATE INDEX IF NOT EXISTS idx_password_reset_token ON password_reset_tokens(token);
CREATE INDEX IF NOT EXISTS idx_password_reset_user_id ON password_reset_tokens(user_id);
CREATE INDEX IF NOT EXISTS idx_password_reset_expires_at ON password_reset_tokens(expires_at);

-- ============================================================================
-- ORGANIZATION INVITATIONS TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS organization_invitations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id TEXT NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    email TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'member' CHECK (role IN ('admin', 'member', 'viewer')),
    token TEXT UNIQUE NOT NULL,
    invited_by TEXT NOT NULL REFERENCES users(id),
    accepted_at TIMESTAMPTZ,
    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indices for invitations
CREATE INDEX IF NOT EXISTS idx_org_invitations_token ON organization_invitations(token);
CREATE INDEX IF NOT EXISTS idx_org_invitations_email ON organization_invitations(email);
CREATE INDEX IF NOT EXISTS idx_org_invitations_org_id ON organization_invitations(organization_id);
CREATE INDEX IF NOT EXISTS idx_org_invitations_expires_at ON organization_invitations(expires_at);

-- ============================================================================
-- AUDIT LOG TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT REFERENCES users(id) ON DELETE SET NULL,
    organization_id TEXT REFERENCES organizations(id) ON DELETE SET NULL,
    action TEXT NOT NULL,
    resource_type TEXT,
    resource_id TEXT,
    changes JSONB DEFAULT '{}',
    ip_address INET,
    user_agent TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indices for audit logs
CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_org_id ON audit_logs(organization_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_action ON audit_logs(action);
CREATE INDEX IF NOT EXISTS idx_audit_logs_resource ON audit_logs(resource_type, resource_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at ON audit_logs(created_at);

-- ============================================================================
-- API KEYS TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS api_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT REFERENCES users(id) ON DELETE CASCADE,
    organization_id TEXT REFERENCES organizations(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    key_hash TEXT UNIQUE NOT NULL,
    last_four TEXT NOT NULL,
    permissions JSONB DEFAULT '{}',
    rate_limit INT DEFAULT 1000,
    is_active BOOLEAN DEFAULT true,
    last_used_at TIMESTAMPTZ,
    expires_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    CHECK (user_id IS NOT NULL OR organization_id IS NOT NULL)
);

-- Create indices for API keys
CREATE INDEX IF NOT EXISTS idx_api_keys_key_hash ON api_keys(key_hash);
CREATE INDEX IF NOT EXISTS idx_api_keys_user_id ON api_keys(user_id);
CREATE INDEX IF NOT EXISTS idx_api_keys_org_id ON api_keys(organization_id);
CREATE INDEX IF NOT EXISTS idx_api_keys_is_active ON api_keys(is_active);

-- ============================================================================
-- HELPER FUNCTIONS
-- ============================================================================

-- Function to automatically update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create triggers for updated_at
DO $$
BEGIN
    DROP TRIGGER IF EXISTS update_users_updated_at ON users;
    CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
        FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
EXCEPTION
    WHEN OTHERS THEN
        RAISE NOTICE 'Could not create users trigger, skipping...';
END $$;

DO $$
BEGIN
    DROP TRIGGER IF EXISTS update_organizations_updated_at ON organizations;
    CREATE TRIGGER update_organizations_updated_at BEFORE UPDATE ON organizations
        FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
EXCEPTION
    WHEN OTHERS THEN
        RAISE NOTICE 'Could not create organizations trigger, skipping...';
END $$;

-- Function to clean up expired sessions
CREATE OR REPLACE FUNCTION cleanup_expired_sessions()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM user_sessions
    WHERE expires_at < NOW() OR is_active = false;

    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Function to clean up expired password reset tokens
CREATE OR REPLACE FUNCTION cleanup_expired_password_tokens()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM password_reset_tokens
    WHERE expires_at < NOW() OR used_at IS NOT NULL;

    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- DEFAULT DATA
-- ============================================================================

-- Insert default admin user (password: admin123 - should be changed immediately)
INSERT INTO users (
    id,
    email,
    username,
    password_hash,
    full_name,
    role,
    email_verified
) VALUES (
    '00000000-0000-0000-0000-000000000001'::text,
    'admin@arxos.local',
    'admin',
    '$2a$10$YKU3.LZGZhJXPMxVBAUMqeFP8W5LJMGVnwvQXR5JCYzWfGVgsFwDO',
    'System Administrator',
    'admin',
    true
) ON CONFLICT (id) DO NOTHING;

-- Insert default organization (handle both TEXT and UUID id types)
INSERT INTO organizations (
    id,
    name,
    username,
    description
) VALUES (
    '00000000-0000-0000-0000-000000000002'::text,
    'Default Organization',
    'default',
    'Default organization for ArxOS system'
) ON CONFLICT (id) DO NOTHING;

-- Link admin to default organization
INSERT INTO organization_members (
    organization_id,
    user_id,
    role
) VALUES (
    '00000000-0000-0000-0000-000000000002',
    '00000000-0000-0000-0000-000000000001',
    'owner'
) ON CONFLICT (organization_id, user_id) DO NOTHING;

COMMIT;

-- Add comment to track migration
COMMENT ON SCHEMA public IS 'ArxOS user management schema - Migration 006 applied';
