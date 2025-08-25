package gitops

import (
	"context"
	"database/sql"
	"fmt"
	"strings"
	"time"

	"github.com/google/uuid"
	"github.com/jmoiron/sqlx"
	"github.com/pkg/errors"
	
	"github.com/arxos/core/internal/state"
)

// Branch represents a building configuration branch
type Branch struct {
	ID          string    `db:"id" json:"id"`
	BuildingID  string    `db:"building_id" json:"building_id"`
	BranchName  string    `db:"branch_name" json:"branch_name"`
	BaseStateID *string   `db:"base_state_id" json:"base_state_id,omitempty"`
	HeadStateID *string   `db:"head_state_id" json:"head_state_id,omitempty"`
	
	Description      string          `db:"description" json:"description,omitempty"`
	IsProtected      bool            `db:"is_protected" json:"is_protected"`
	IsDefault        bool            `db:"is_default" json:"is_default"`
	MergeRequirements sql.NullString `db:"merge_requirements" json:"-"`
	
	CreatedBy     string    `db:"created_by" json:"created_by"`
	CreatedByName string    `db:"created_by_name" json:"created_by_name"`
	CreatedAt     time.Time `db:"created_at" json:"created_at"`
	UpdatedAt     time.Time `db:"updated_at" json:"updated_at"`
	
	CommitsAhead  int        `db:"commits_ahead" json:"commits_ahead"`
	CommitsBehind int        `db:"commits_behind" json:"commits_behind"`
	LastActivityAt *time.Time `db:"last_activity_at" json:"last_activity_at,omitempty"`
	
	Metadata sql.NullString `db:"metadata" json:"-"`
}

// BranchProtectionRule defines protection rules for branches
type BranchProtectionRule struct {
	ID             string `db:"id" json:"id"`
	BuildingID     string `db:"building_id" json:"building_id"`
	BranchPattern  string `db:"branch_pattern" json:"branch_pattern"`
	
	RequirePR              bool     `db:"require_pr" json:"require_pr"`
	RequireApprovals       int      `db:"require_approvals" json:"require_approvals"`
	DismissStaleReviews    bool     `db:"dismiss_stale_reviews" json:"dismiss_stale_reviews"`
	RequireStatusChecks    bool     `db:"require_status_checks" json:"require_status_checks"`
	RequiredStatusCheckNames []string `db:"required_status_check_names" json:"required_status_check_names"`
	RequireUpToDate        bool     `db:"require_up_to_date" json:"require_up_to_date"`
	
	RestrictPush     bool     `db:"restrict_push" json:"restrict_push"`
	PushAllowlist    []string `db:"push_allowlist" json:"push_allowlist"`
	RestrictMerge    bool     `db:"restrict_merge" json:"restrict_merge"`
	MergeAllowlist   []string `db:"merge_allowlist" json:"merge_allowlist"`
	AllowForcePush   bool     `db:"allow_force_push" json:"allow_force_push"`
	AllowDeletions   bool     `db:"allow_deletions" json:"allow_deletions"`
	
	EnforceAdmins bool `db:"enforce_admins" json:"enforce_admins"`
	IsActive      bool `db:"is_active" json:"is_active"`
	
	CreatedAt time.Time `db:"created_at" json:"created_at"`
	UpdatedAt time.Time `db:"updated_at" json:"updated_at"`
}

// BranchManager manages building configuration branches
type BranchManager struct {
	db           *sqlx.DB
	stateManager *state.Manager
}

// NewBranchManager creates a new branch manager
func NewBranchManager(db *sqlx.DB, stateManager *state.Manager) *BranchManager {
	return &BranchManager{
		db:           db,
		stateManager: stateManager,
	}
}

// CreateBranch creates a new branch
func (bm *BranchManager) CreateBranch(ctx context.Context, req *CreateBranchRequest) (*Branch, error) {
	// Validate request
	if err := req.Validate(); err != nil {
		return nil, errors.Wrap(err, "invalid branch request")
	}
	
	// Check if branch already exists
	exists, err := bm.BranchExists(ctx, req.BuildingID, req.BranchName)
	if err != nil {
		return nil, errors.Wrap(err, "failed to check branch existence")
	}
	if exists {
		return nil, fmt.Errorf("branch '%s' already exists", req.BranchName)
	}
	
	// Begin transaction
	tx, err := bm.db.BeginTxx(ctx, nil)
	if err != nil {
		return nil, errors.Wrap(err, "failed to begin transaction")
	}
	defer tx.Rollback()
	
	// Determine base state
	var baseStateID *string
	if req.SourceBranch != "" {
		// Create from existing branch
		sourceBranch, err := bm.GetBranch(ctx, req.BuildingID, req.SourceBranch)
		if err != nil {
			return nil, errors.Wrapf(err, "source branch '%s' not found", req.SourceBranch)
		}
		baseStateID = sourceBranch.HeadStateID
	} else if req.SourceStateID != "" {
		// Create from specific state
		baseStateID = &req.SourceStateID
	} else {
		// Create from default branch HEAD
		defaultBranch, err := bm.GetDefaultBranch(ctx, req.BuildingID)
		if err == nil && defaultBranch != nil {
			baseStateID = defaultBranch.HeadStateID
		}
	}
	
	// Create branch
	branch := &Branch{
		ID:            uuid.New().String(),
		BuildingID:    req.BuildingID,
		BranchName:    req.BranchName,
		BaseStateID:   baseStateID,
		HeadStateID:   baseStateID, // Initially points to same state
		Description:   req.Description,
		IsProtected:   req.Protected,
		IsDefault:     false,
		CreatedBy:     req.CreatedBy,
		CreatedByName: req.CreatedByName,
		CreatedAt:     time.Now(),
		UpdatedAt:     time.Now(),
	}
	
	// Insert branch
	_, err = tx.NamedExecContext(ctx, `
		INSERT INTO state_branches (
			id, building_id, branch_name, base_state_id, head_state_id,
			description, is_protected, is_default, created_by, created_by_name,
			created_at, updated_at
		) VALUES (
			:id, :building_id, :branch_name, :base_state_id, :head_state_id,
			:description, :is_protected, :is_default, :created_by, :created_by_name,
			:created_at, :updated_at
		)
	`, branch)
	if err != nil {
		return nil, errors.Wrap(err, "failed to create branch")
	}
	
	// If this is the first branch, make it default
	var branchCount int
	err = tx.GetContext(ctx, &branchCount, 
		"SELECT COUNT(*) FROM state_branches WHERE building_id = $1", req.BuildingID)
	if err == nil && branchCount == 1 {
		_, err = tx.ExecContext(ctx, 
			"UPDATE state_branches SET is_default = true WHERE id = $1", branch.ID)
		if err == nil {
			branch.IsDefault = true
		}
	}
	
	// Commit transaction
	if err = tx.Commit(); err != nil {
		return nil, errors.Wrap(err, "failed to commit transaction")
	}
	
	return branch, nil
}

// GetBranch retrieves a branch by name
func (bm *BranchManager) GetBranch(ctx context.Context, buildingID, branchName string) (*Branch, error) {
	var branch Branch
	err := bm.db.GetContext(ctx, &branch, `
		SELECT * FROM state_branches 
		WHERE building_id = $1 AND branch_name = $2
	`, buildingID, branchName)
	if err != nil {
		return nil, errors.Wrap(err, "failed to get branch")
	}
	
	// Calculate commits ahead/behind
	if branch.IsDefault {
		// Default branch is never behind
		branch.CommitsBehind = 0
	} else {
		// Calculate relative to default branch
		defaultBranch, err := bm.GetDefaultBranch(ctx, buildingID)
		if err == nil && defaultBranch != nil {
			ahead, behind := bm.calculateCommitDifference(ctx, &branch, defaultBranch)
			branch.CommitsAhead = ahead
			branch.CommitsBehind = behind
		}
	}
	
	return &branch, nil
}

// ListBranches lists all branches for a building
func (bm *BranchManager) ListBranches(ctx context.Context, buildingID string) ([]*Branch, error) {
	var branches []*Branch
	err := bm.db.SelectContext(ctx, &branches, `
		SELECT * FROM state_branches 
		WHERE building_id = $1 
		ORDER BY is_default DESC, created_at DESC
	`, buildingID)
	if err != nil {
		return nil, errors.Wrap(err, "failed to list branches")
	}
	
	// Calculate commits ahead/behind for each branch
	defaultBranch, _ := bm.GetDefaultBranch(ctx, buildingID)
	for _, branch := range branches {
		if !branch.IsDefault && defaultBranch != nil {
			ahead, behind := bm.calculateCommitDifference(ctx, branch, defaultBranch)
			branch.CommitsAhead = ahead
			branch.CommitsBehind = behind
		}
	}
	
	return branches, nil
}

// UpdateBranch updates branch properties
func (bm *BranchManager) UpdateBranch(ctx context.Context, req *UpdateBranchRequest) (*Branch, error) {
	// Get existing branch
	branch, err := bm.GetBranch(ctx, req.BuildingID, req.BranchName)
	if err != nil {
		return nil, err
	}
	
	// Update fields
	if req.Description != nil {
		branch.Description = *req.Description
	}
	if req.Protected != nil {
		branch.IsProtected = *req.Protected
	}
	
	branch.UpdatedAt = time.Now()
	
	// Update in database
	_, err = bm.db.NamedExecContext(ctx, `
		UPDATE state_branches 
		SET description = :description, is_protected = :is_protected, updated_at = :updated_at
		WHERE id = :id
	`, branch)
	if err != nil {
		return nil, errors.Wrap(err, "failed to update branch")
	}
	
	return branch, nil
}

// DeleteBranch deletes a branch
func (bm *BranchManager) DeleteBranch(ctx context.Context, buildingID, branchName string, force bool) error {
	// Get branch
	branch, err := bm.GetBranch(ctx, buildingID, branchName)
	if err != nil {
		return err
	}
	
	// Check if default branch
	if branch.IsDefault {
		return fmt.Errorf("cannot delete default branch")
	}
	
	// Check if protected
	if branch.IsProtected && !force {
		return fmt.Errorf("cannot delete protected branch (use force to override)")
	}
	
	// Check for unmerged commits
	if branch.CommitsAhead > 0 && !force {
		return fmt.Errorf("branch has %d unmerged commits (use force to override)", branch.CommitsAhead)
	}
	
	// Delete branch
	_, err = bm.db.ExecContext(ctx, 
		"DELETE FROM state_branches WHERE id = $1", branch.ID)
	if err != nil {
		return errors.Wrap(err, "failed to delete branch")
	}
	
	return nil
}

// SetDefaultBranch sets the default branch for a building
func (bm *BranchManager) SetDefaultBranch(ctx context.Context, buildingID, branchName string) error {
	// Begin transaction
	tx, err := bm.db.BeginTxx(ctx, nil)
	if err != nil {
		return errors.Wrap(err, "failed to begin transaction")
	}
	defer tx.Rollback()
	
	// Clear current default
	_, err = tx.ExecContext(ctx, `
		UPDATE state_branches 
		SET is_default = false 
		WHERE building_id = $1 AND is_default = true
	`, buildingID)
	if err != nil {
		return errors.Wrap(err, "failed to clear current default")
	}
	
	// Set new default
	result, err := tx.ExecContext(ctx, `
		UPDATE state_branches 
		SET is_default = true, updated_at = $2
		WHERE building_id = $1 AND branch_name = $3
	`, buildingID, time.Now(), branchName)
	if err != nil {
		return errors.Wrap(err, "failed to set new default")
	}
	
	rowsAffected, _ := result.RowsAffected()
	if rowsAffected == 0 {
		return fmt.Errorf("branch '%s' not found", branchName)
	}
	
	// Commit transaction
	if err = tx.Commit(); err != nil {
		return errors.Wrap(err, "failed to commit transaction")
	}
	
	return nil
}

// GetDefaultBranch gets the default branch for a building
func (bm *BranchManager) GetDefaultBranch(ctx context.Context, buildingID string) (*Branch, error) {
	var branch Branch
	err := bm.db.GetContext(ctx, &branch, `
		SELECT * FROM state_branches 
		WHERE building_id = $1 AND is_default = true
		LIMIT 1
	`, buildingID)
	if err != nil {
		if err == sql.ErrNoRows {
			return nil, nil
		}
		return nil, errors.Wrap(err, "failed to get default branch")
	}
	return &branch, nil
}

// BranchExists checks if a branch exists
func (bm *BranchManager) BranchExists(ctx context.Context, buildingID, branchName string) (bool, error) {
	var exists bool
	err := bm.db.GetContext(ctx, &exists, `
		SELECT EXISTS(SELECT 1 FROM state_branches WHERE building_id = $1 AND branch_name = $2)
	`, buildingID, branchName)
	return exists, err
}

// CommitToBranch creates a new state commit on a branch
func (bm *BranchManager) CommitToBranch(ctx context.Context, buildingID, branchName string, opts state.CaptureOptions) (*state.BuildingState, error) {
	// Get branch
	branch, err := bm.GetBranch(ctx, buildingID, branchName)
	if err != nil {
		return nil, err
	}
	
	// Check if branch is protected
	if branch.IsProtected {
		// Check protection rules
		if err := bm.checkProtectionRules(ctx, buildingID, branchName, opts.AuthorID); err != nil {
			return nil, err
		}
	}
	
	// Capture new state
	newState, err := bm.stateManager.CaptureState(ctx, buildingID, branchName, opts)
	if err != nil {
		return nil, errors.Wrap(err, "failed to capture state")
	}
	
	// Update branch HEAD
	branch.HeadStateID = &newState.ID
	branch.UpdatedAt = time.Now()
	branch.LastActivityAt = &branch.UpdatedAt
	
	_, err = bm.db.ExecContext(ctx, `
		UPDATE state_branches 
		SET head_state_id = $1, updated_at = $2, last_activity_at = $3
		WHERE id = $4
	`, newState.ID, branch.UpdatedAt, branch.LastActivityAt, branch.ID)
	if err != nil {
		return nil, errors.Wrap(err, "failed to update branch HEAD")
	}
	
	return newState, nil
}

// GetBranchHistory gets the commit history for a branch
func (bm *BranchManager) GetBranchHistory(ctx context.Context, buildingID, branchName string, limit, offset int) ([]*state.BuildingState, error) {
	var states []*state.BuildingState
	err := bm.db.SelectContext(ctx, &states, `
		SELECT * FROM building_states 
		WHERE building_id = $1 AND branch_name = $2
		ORDER BY created_at DESC
		LIMIT $3 OFFSET $4
	`, buildingID, branchName, limit, offset)
	if err != nil {
		return nil, errors.Wrap(err, "failed to get branch history")
	}
	return states, nil
}

// CompareBranches compares two branches
func (bm *BranchManager) CompareBranches(ctx context.Context, buildingID, branch1, branch2 string) (*BranchComparison, error) {
	// Get both branches
	b1, err := bm.GetBranch(ctx, buildingID, branch1)
	if err != nil {
		return nil, errors.Wrapf(err, "failed to get branch %s", branch1)
	}
	
	b2, err := bm.GetBranch(ctx, buildingID, branch2)
	if err != nil {
		return nil, errors.Wrapf(err, "failed to get branch %s", branch2)
	}
	
	comparison := &BranchComparison{
		Branch1: b1,
		Branch2: b2,
	}
	
	// Find common ancestor
	commonAncestor, err := bm.findCommonAncestor(ctx, b1, b2)
	if err != nil {
		return nil, errors.Wrap(err, "failed to find common ancestor")
	}
	comparison.CommonAncestorID = commonAncestor
	
	// Count unique commits
	if b1.HeadStateID != nil && b2.HeadStateID != nil {
		comparison.Branch1UniqueCommits = bm.countUniqueCommits(ctx, *b1.HeadStateID, commonAncestor)
		comparison.Branch2UniqueCommits = bm.countUniqueCommits(ctx, *b2.HeadStateID, commonAncestor)
	}
	
	// Check if branches can be merged
	comparison.CanMerge = bm.canMerge(ctx, b1, b2)
	
	return comparison, nil
}

// Helper methods

func (bm *BranchManager) calculateCommitDifference(ctx context.Context, branch, targetBranch *Branch) (ahead, behind int) {
	if branch.HeadStateID == nil || targetBranch.HeadStateID == nil {
		return 0, 0
	}
	
	// Find common ancestor
	commonAncestor, _ := bm.findCommonAncestor(ctx, branch, targetBranch)
	
	// Count commits from branch HEAD to common ancestor
	ahead = bm.countUniqueCommits(ctx, *branch.HeadStateID, commonAncestor)
	
	// Count commits from target HEAD to common ancestor
	behind = bm.countUniqueCommits(ctx, *targetBranch.HeadStateID, commonAncestor)
	
	return ahead, behind
}

func (bm *BranchManager) findCommonAncestor(ctx context.Context, branch1, branch2 *Branch) (string, error) {
	if branch1.BaseStateID != nil && branch2.BaseStateID != nil {
		// If one branch was created from the other, use that as common ancestor
		if *branch1.BaseStateID == *branch2.HeadStateID {
			return *branch1.BaseStateID, nil
		}
		if *branch2.BaseStateID == *branch1.HeadStateID {
			return *branch2.BaseStateID, nil
		}
	}
	
	// For now, use the base of the newer branch as common ancestor
	// In production, would traverse the commit graph
	if branch1.CreatedAt.After(branch2.CreatedAt) && branch1.BaseStateID != nil {
		return *branch1.BaseStateID, nil
	}
	if branch2.BaseStateID != nil {
		return *branch2.BaseStateID, nil
	}
	
	return "", fmt.Errorf("no common ancestor found")
}

func (bm *BranchManager) countUniqueCommits(ctx context.Context, fromStateID, toStateID string) int {
	if fromStateID == toStateID {
		return 0
	}
	
	var count int
	err := bm.db.GetContext(ctx, &count, `
		WITH RECURSIVE commit_chain AS (
			SELECT id, parent_state_id, 1 as depth
			FROM building_states
			WHERE id = $1
			
			UNION ALL
			
			SELECT s.id, s.parent_state_id, c.depth + 1
			FROM building_states s
			JOIN commit_chain c ON s.id = c.parent_state_id
			WHERE c.parent_state_id IS NOT NULL 
			  AND c.parent_state_id != $2
			  AND c.depth < 100  -- Prevent infinite recursion
		)
		SELECT COUNT(*) FROM commit_chain
	`, fromStateID, toStateID)
	
	if err != nil {
		return 0
	}
	
	return count
}

func (bm *BranchManager) canMerge(ctx context.Context, sourceBranch, targetBranch *Branch) bool {
	// Check if branches have diverged
	if sourceBranch.HeadStateID == nil || targetBranch.HeadStateID == nil {
		return false
	}
	
	// Check if source is already merged
	if *sourceBranch.HeadStateID == *targetBranch.HeadStateID {
		return false
	}
	
	// Check protection rules
	if targetBranch.IsProtected {
		// Would need PR for protected branches
		return false
	}
	
	return true
}

func (bm *BranchManager) checkProtectionRules(ctx context.Context, buildingID, branchName, userID string) error {
	// Get protection rules for the branch
	var rules []BranchProtectionRule
	err := bm.db.SelectContext(ctx, &rules, `
		SELECT * FROM branch_protection_rules 
		WHERE building_id = $1 AND is_active = true
		  AND ($2 LIKE branch_pattern OR branch_pattern = $2)
		ORDER BY created_at DESC
		LIMIT 1
	`, buildingID, branchName)
	
	if err != nil || len(rules) == 0 {
		// No protection rules
		return nil
	}
	
	rule := rules[0]
	
	// Check push restrictions
	if rule.RestrictPush {
		allowed := false
		for _, allowedUser := range rule.PushAllowlist {
			if allowedUser == userID {
				allowed = true
				break
			}
		}
		if !allowed {
			return fmt.Errorf("push to branch '%s' is restricted", branchName)
		}
	}
	
	// Check if PR is required
	if rule.RequirePR {
		return fmt.Errorf("direct commits to branch '%s' are not allowed, pull request required", branchName)
	}
	
	return nil
}

// Request types

// CreateBranchRequest represents a request to create a branch
type CreateBranchRequest struct {
	BuildingID    string `json:"building_id" validate:"required"`
	BranchName    string `json:"branch_name" validate:"required"`
	SourceBranch  string `json:"source_branch"`
	SourceStateID string `json:"source_state_id"`
	Description   string `json:"description"`
	Protected     bool   `json:"protected"`
	CreatedBy     string `json:"created_by" validate:"required"`
	CreatedByName string `json:"created_by_name" validate:"required"`
}

// Validate validates the create branch request
func (r *CreateBranchRequest) Validate() error {
	if r.BuildingID == "" {
		return fmt.Errorf("building ID is required")
	}
	if r.BranchName == "" {
		return fmt.Errorf("branch name is required")
	}
	if strings.Contains(r.BranchName, " ") {
		return fmt.Errorf("branch name cannot contain spaces")
	}
	if r.CreatedBy == "" || r.CreatedByName == "" {
		return fmt.Errorf("creator information is required")
	}
	return nil
}

// UpdateBranchRequest represents a request to update a branch
type UpdateBranchRequest struct {
	BuildingID  string  `json:"building_id" validate:"required"`
	BranchName  string  `json:"branch_name" validate:"required"`
	Description *string `json:"description"`
	Protected   *bool   `json:"protected"`
}

// BranchComparison represents a comparison between two branches
type BranchComparison struct {
	Branch1              *Branch `json:"branch1"`
	Branch2              *Branch `json:"branch2"`
	CommonAncestorID     string  `json:"common_ancestor_id"`
	Branch1UniqueCommits int     `json:"branch1_unique_commits"`
	Branch2UniqueCommits int     `json:"branch2_unique_commits"`
	CanMerge             bool    `json:"can_merge"`
	HasConflicts         bool    `json:"has_conflicts"`
}