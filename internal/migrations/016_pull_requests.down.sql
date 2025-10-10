-- Migration 016: Pull Request System - Rollback
-- Description: Remove pull request tables
-- Author: ArxOS Team
-- Date: 2025-01-15

-- ============================================================================
-- Drop views
-- ============================================================================
DROP VIEW IF EXISTS v_pr_dashboard CASCADE;
DROP VIEW IF EXISTS v_open_pull_requests CASCADE;

-- ============================================================================
-- Drop triggers
-- ============================================================================
DROP TRIGGER IF EXISTS pull_requests_status_change ON pull_requests;
DROP FUNCTION IF EXISTS log_pr_status_change();

DROP TRIGGER IF EXISTS pr_comments_updated_at ON pr_comments;
DROP TRIGGER IF EXISTS pull_requests_updated_at ON pull_requests;
DROP FUNCTION IF EXISTS update_pr_updated_at();

-- ============================================================================
-- Drop tables (in reverse order of creation)
-- ============================================================================
DROP TABLE IF EXISTS pr_activity_log CASCADE;
DROP TABLE IF EXISTS pr_assignment_rules CASCADE;
DROP TABLE IF EXISTS pr_files CASCADE;
DROP TABLE IF EXISTS pr_comments CASCADE;
DROP TABLE IF EXISTS pr_reviews CASCADE;
DROP TABLE IF EXISTS pr_reviewers CASCADE;
DROP TABLE IF EXISTS pull_requests CASCADE;

-- ============================================================================
-- Schema documentation
-- ============================================================================
COMMENT ON SCHEMA public IS 'ArxOS spatial database schema - Migration 016 rolled back';

