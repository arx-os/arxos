-- Migration 015: Git Workflow Enhancement - Rollback
-- Description: Remove Git workflow tables
-- Author: ArxOS Team
-- Date: 2025-01-15

-- ============================================================================
-- Drop views
-- ============================================================================
DROP VIEW IF EXISTS v_unresolved_conflicts CASCADE;
DROP VIEW IF EXISTS v_active_branches CASCADE;

-- ============================================================================
-- Drop triggers
-- ============================================================================
DROP TRIGGER IF EXISTS repository_branch_states_updated_at ON repository_branch_states;
DROP TRIGGER IF EXISTS repository_branches_updated_at ON repository_branches;
DROP FUNCTION IF EXISTS update_repository_workflow_updated_at();

-- ============================================================================
-- Drop tables (in reverse order of creation)
-- ============================================================================
DROP TABLE IF EXISTS merge_conflicts CASCADE;
DROP TABLE IF EXISTS working_directories CASCADE;
DROP TABLE IF EXISTS repository_branch_states CASCADE;
DROP TABLE IF EXISTS commit_changes CASCADE;
DROP TABLE IF EXISTS repository_commits CASCADE;
DROP TABLE IF EXISTS repository_branches CASCADE;

-- ============================================================================
-- Schema documentation
-- ============================================================================
COMMENT ON SCHEMA public IS 'ArxOS spatial database schema - Migration 015 rolled back';

