-- Migration 017: Issue Tracking System - Rollback
-- Description: Remove issue tracking tables
-- Author: ArxOS Team
-- Date: 2025-01-15

-- ============================================================================
-- Drop views
-- ============================================================================
DROP VIEW IF EXISTS v_ar_reported_issues CASCADE;
DROP VIEW IF EXISTS v_issue_dashboard CASCADE;
DROP VIEW IF EXISTS v_open_issues CASCADE;

-- ============================================================================
-- Drop triggers
-- ============================================================================
DROP TRIGGER IF EXISTS issues_priority_change ON issues;
DROP FUNCTION IF EXISTS log_issue_priority_change();

DROP TRIGGER IF EXISTS issues_status_change ON issues;
DROP FUNCTION IF EXISTS log_issue_status_change();

DROP TRIGGER IF EXISTS issue_comments_updated_at ON issue_comments;
DROP TRIGGER IF EXISTS issues_updated_at ON issues;
DROP FUNCTION IF EXISTS update_issue_updated_at();

-- ============================================================================
-- Drop tables (in reverse order of creation)
-- ============================================================================
DROP TABLE IF EXISTS issue_activity_log CASCADE;
DROP TABLE IF EXISTS issue_photos CASCADE;
DROP TABLE IF EXISTS issue_comments CASCADE;
DROP TABLE IF EXISTS issue_label_assignments CASCADE;
DROP TABLE IF EXISTS issue_labels CASCADE;
DROP TABLE IF EXISTS issues CASCADE;

-- ============================================================================
-- Schema documentation
-- ============================================================================
COMMENT ON SCHEMA public IS 'ArxOS spatial database schema - Migration 017 rolled back';

