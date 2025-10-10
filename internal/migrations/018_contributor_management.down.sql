-- Migration 018: Contributor Management System - Rollback
-- Description: Remove contributor management tables
-- Author: ArxOS Team
-- Date: 2025-01-15

-- ============================================================================
-- Drop views
-- ============================================================================
DROP VIEW IF EXISTS v_team_roster CASCADE;
DROP VIEW IF EXISTS v_repository_contributors CASCADE;

-- ============================================================================
-- Drop triggers
-- ============================================================================
DROP TRIGGER IF EXISTS repository_contributors_audit ON repository_contributors;
DROP FUNCTION IF EXISTS log_contributor_change();

DROP TRIGGER IF EXISTS branch_protection_rules_updated_at ON branch_protection_rules;
DROP TRIGGER IF EXISTS teams_updated_at ON teams;
DROP TRIGGER IF EXISTS repository_contributors_updated_at ON repository_contributors;
DROP FUNCTION IF EXISTS update_contributor_updated_at();

-- ============================================================================
-- Drop tables (in reverse order of creation)
-- ============================================================================
DROP TABLE IF EXISTS access_audit_log CASCADE;
DROP TABLE IF EXISTS branch_protection_rules CASCADE;
DROP TABLE IF EXISTS access_rules CASCADE;
DROP TABLE IF EXISTS team_members CASCADE;
DROP TABLE IF EXISTS teams CASCADE;
DROP TABLE IF EXISTS repository_contributors CASCADE;

-- ============================================================================
-- Remove columns added to existing tables
-- ============================================================================
ALTER TABLE repository_branches DROP COLUMN IF EXISTS requires_review;
ALTER TABLE repository_branches DROP COLUMN IF EXISTS auto_delete_on_merge;

-- ============================================================================
-- Schema documentation
-- ============================================================================
COMMENT ON SCHEMA public IS 'ArxOS spatial database schema - Migration 018 rolled back';

