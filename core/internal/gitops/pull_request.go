package gitops

import (
	"context"
	"database/sql"
	"encoding/json"
	"fmt"
	"time"

	"github.com/google/uuid"
	"github.com/jmoiron/sqlx"
)

// PullRequestManager manages pull requests for building configurations
type PullRequestManager struct {
	db          *sqlx.DB
	mergeEngine *MergeEngine
	branchMgr   *BranchManager
}

// NewPullRequestManager creates a new pull request manager
func NewPullRequestManager(db *sqlx.DB, mergeEngine *MergeEngine, branchMgr *BranchManager) *PullRequestManager {
	return &PullRequestManager{
		db:          db,
		mergeEngine: mergeEngine,
		branchMgr:   branchMgr,
	}
}

// PullRequest represents a pull request
type PullRequest struct {
	ID               string                 `json:"id" db:"id"`
	PRNumber         int                    `json:"pr_number" db:"pr_number"`
	BuildingID       string                 `json:"building_id" db:"building_id"`
	SourceBranch     string                 `json:"source_branch" db:"source_branch"`
	TargetBranch     string                 `json:"target_branch" db:"target_branch"`
	BaseStateID      *string                `json:"base_state_id" db:"base_state_id"`
	SourceStateID    *string                `json:"source_state_id" db:"source_state_id"`
	TargetStateID    *string                `json:"target_state_id" db:"target_state_id"`
	MergeStateID     *string                `json:"merge_state_id" db:"merge_state_id"`
	Title            string                 `json:"title" db:"title"`
	Description      string                 `json:"description" db:"description"`
	PRType           string                 `json:"pr_type" db:"pr_type"`
	Priority         string                 `json:"priority" db:"priority"`
	Status           string                 `json:"status" db:"status"`
	HasConflicts     bool                   `json:"has_conflicts" db:"has_conflicts"`
	ConflictDetails  json.RawMessage        `json:"conflict_details" db:"conflict_details"`
	AutoMergeable    bool                   `json:"auto_mergeable" db:"auto_mergeable"`
	RequiredApprovals int                   `json:"required_approvals" db:"required_approvals"`
	AuthorID         string                 `json:"author_id" db:"author_id"`
	AuthorName       string                 `json:"author_name" db:"author_name"`
	MergerID         *string                `json:"merger_id" db:"merger_id"`
	MergerName       *string                `json:"merger_name" db:"merger_name"`
	CreatedAt        time.Time              `json:"created_at" db:"created_at"`
	UpdatedAt        time.Time              `json:"updated_at" db:"updated_at"`
	ReadyForReviewAt *time.Time             `json:"ready_for_review_at" db:"ready_for_review_at"`
	ApprovedAt       *time.Time             `json:"approved_at" db:"approved_at"`
	MergedAt         *time.Time             `json:"merged_at" db:"merged_at"`
	ClosedAt         *time.Time             `json:"closed_at" db:"closed_at"`
	LinesAdded       int                    `json:"lines_added" db:"lines_added"`
	LinesRemoved     int                    `json:"lines_removed" db:"lines_removed"`
	FilesChanged     int                    `json:"files_changed" db:"files_changed"`
	CommentsCount    int                    `json:"comments_count" db:"comments_count"`
	CommitsCount     int                    `json:"commits_count" db:"commits_count"`
	Labels           []string               `json:"labels"`
	Metadata         map[string]interface{} `json:"metadata"`
}

// CreatePullRequestRequest represents a request to create a pull request
type CreatePullRequestRequest struct {
	BuildingID        string                 `json:"building_id"`
	SourceBranch      string                 `json:"source_branch"`
	TargetBranch      string                 `json:"target_branch"`
	Title             string                 `json:"title"`
	Description       string                 `json:"description"`
	PRType            string                 `json:"pr_type"`
	Priority          string                 `json:"priority"`
	AuthorID          string                 `json:"author_id"`
	AuthorName        string                 `json:"author_name"`
	Labels            []string               `json:"labels"`
	RequiredApprovals int                    `json:"required_approvals"`
	Metadata          map[string]interface{} `json:"metadata"`
}

// CreatePullRequest creates a new pull request
func (prm *PullRequestManager) CreatePullRequest(ctx context.Context, req *CreatePullRequestRequest) (*PullRequest, error) {
	// Validate branches exist
	sourceBranch, err := prm.branchMgr.GetBranch(ctx, req.BuildingID, req.SourceBranch)
	if err != nil {
		return nil, fmt.Errorf("source branch not found: %w", err)
	}

	targetBranch, err := prm.branchMgr.GetBranch(ctx, req.BuildingID, req.TargetBranch)
	if err != nil {
		return nil, fmt.Errorf("target branch not found: %w", err)
	}

	// Check for conflicts
	mergeResult, err := prm.mergeEngine.Merge(ctx, &MergeRequest{
		BuildingID:   req.BuildingID,
		SourceBranch: req.SourceBranch,
		TargetBranch: req.TargetBranch,
		Strategy:     MergeStrategyMerge,
		DryRun:       true,
	})
	if err != nil {
		return nil, fmt.Errorf("failed to check for conflicts: %w", err)
	}

	// Calculate diff statistics
	stats, err := prm.calculateDiffStats(ctx, sourceBranch.HeadStateID, targetBranch.HeadStateID)
	if err != nil {
		return nil, fmt.Errorf("failed to calculate diff stats: %w", err)
	}

	// Create pull request
	pr := &PullRequest{
		ID:                uuid.New().String(),
		BuildingID:        req.BuildingID,
		SourceBranch:      req.SourceBranch,
		TargetBranch:      req.TargetBranch,
		SourceStateID:     &sourceBranch.HeadStateID,
		TargetStateID:     &targetBranch.HeadStateID,
		Title:             req.Title,
		Description:       req.Description,
		PRType:            req.PRType,
		Priority:          req.Priority,
		Status:            "draft",
		HasConflicts:      len(mergeResult.Conflicts) > 0,
		AutoMergeable:     len(mergeResult.Conflicts) == 0,
		RequiredApprovals: req.RequiredApprovals,
		AuthorID:          req.AuthorID,
		AuthorName:        req.AuthorName,
		LinesAdded:        stats.LinesAdded,
		LinesRemoved:      stats.LinesRemoved,
		FilesChanged:      stats.FilesChanged,
		Labels:            req.Labels,
		CreatedAt:         time.Now(),
		UpdatedAt:         time.Now(),
	}

	if pr.PRType == "" {
		pr.PRType = "standard"
	}
	if pr.Priority == "" {
		pr.Priority = "normal"
	}
	if pr.RequiredApprovals == 0 {
		pr.RequiredApprovals = 1
	}

	// Store conflict details if any
	if len(mergeResult.Conflicts) > 0 {
		conflictJSON, _ := json.Marshal(mergeResult.Conflicts)
		pr.ConflictDetails = conflictJSON
	}

	// Begin transaction
	tx, err := prm.db.BeginTxx(ctx, nil)
	if err != nil {
		return nil, fmt.Errorf("failed to begin transaction: %w", err)
	}
	defer tx.Rollback()

	// Insert pull request
	query := `
		INSERT INTO pull_requests (
			id, building_id, source_branch, target_branch,
			base_state_id, source_state_id, target_state_id,
			title, description, pr_type, priority, status,
			has_conflicts, conflict_details, auto_mergeable,
			required_approvals, author_id, author_name,
			lines_added, lines_removed, files_changed,
			created_at, updated_at
		) VALUES (
			$1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12,
			$13, $14, $15, $16, $17, $18, $19, $20, $21, $22, $23
		) RETURNING pr_number`

	var prNumber int
	err = tx.QueryRowContext(ctx, query,
		pr.ID, pr.BuildingID, pr.SourceBranch, pr.TargetBranch,
		pr.BaseStateID, pr.SourceStateID, pr.TargetStateID,
		pr.Title, pr.Description, pr.PRType, pr.Priority, pr.Status,
		pr.HasConflicts, pr.ConflictDetails, pr.AutoMergeable,
		pr.RequiredApprovals, pr.AuthorID, pr.AuthorName,
		pr.LinesAdded, pr.LinesRemoved, pr.FilesChanged,
		pr.CreatedAt, pr.UpdatedAt).Scan(&prNumber)
	if err != nil {
		return nil, fmt.Errorf("failed to create pull request: %w", err)
	}
	pr.PRNumber = prNumber

	// Store conflicts if any
	if len(mergeResult.Conflicts) > 0 {
		for _, conflict := range mergeResult.Conflicts {
			baseValue, _ := json.Marshal(conflict.BaseValue)
			sourceValue, _ := json.Marshal(conflict.SourceValue)
			targetValue, _ := json.Marshal(conflict.TargetValue)

			_, err = tx.ExecContext(ctx, `
				INSERT INTO merge_conflicts (
					id, pr_id, conflict_type, object_id,
					base_value, source_value, target_value, status
				) VALUES ($1, $2, $3, $4, $5, $6, $7, 'unresolved')`,
				uuid.New().String(), pr.ID, conflict.Type, conflict.ObjectID,
				baseValue, sourceValue, targetValue)
			if err != nil {
				return nil, fmt.Errorf("failed to store conflict: %w", err)
			}
		}
	}

	// Create initial commit entries
	commits, err := prm.getCommitsBetween(ctx, targetBranch.HeadStateID, sourceBranch.HeadStateID)
	if err != nil {
		return nil, fmt.Errorf("failed to get commits: %w", err)
	}

	for i, commit := range commits {
		_, err = tx.ExecContext(ctx, `
			INSERT INTO pr_commits (
				id, pr_id, state_id, commit_message, commit_order,
				author_id, author_name, committed_at
			) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)`,
			uuid.New().String(), pr.ID, commit.StateID, commit.Message, i,
			commit.AuthorID, commit.AuthorName, commit.CommittedAt)
		if err != nil {
			return nil, fmt.Errorf("failed to store commit: %w", err)
		}
	}
	pr.CommitsCount = len(commits)

	if err := tx.Commit(); err != nil {
		return nil, fmt.Errorf("failed to commit transaction: %w", err)
	}

	return pr, nil
}

// GetPullRequest retrieves a pull request
func (prm *PullRequestManager) GetPullRequest(ctx context.Context, prID string) (*PullRequest, error) {
	var pr PullRequest
	
	query := `
		SELECT 
			id, pr_number, building_id, source_branch, target_branch,
			base_state_id, source_state_id, target_state_id, merge_state_id,
			title, description, pr_type, priority, status,
			has_conflicts, conflict_details, auto_mergeable,
			required_approvals, author_id, author_name,
			merger_id, merger_name,
			created_at, updated_at, ready_for_review_at,
			approved_at, merged_at, closed_at,
			lines_added, lines_removed, files_changed,
			comments_count, commits_count
		FROM pull_requests
		WHERE id = $1 OR CAST(pr_number AS TEXT) = $1`

	err := prm.db.GetContext(ctx, &pr, query, prID)
	if err != nil {
		if err == sql.ErrNoRows {
			return nil, fmt.Errorf("pull request not found")
		}
		return nil, fmt.Errorf("failed to get pull request: %w", err)
	}

	// Load labels
	var labels []string
	err = prm.db.SelectContext(ctx, &labels,
		"SELECT unnest(labels) FROM pull_requests WHERE id = $1", pr.ID)
	if err == nil {
		pr.Labels = labels
	}

	return &pr, nil
}

// UpdatePullRequestStatus updates the status of a pull request
func (prm *PullRequestManager) UpdatePullRequestStatus(ctx context.Context, prID string, status string) error {
	validStatuses := map[string]bool{
		"draft": true, "open": true, "review_required": true,
		"changes_requested": true, "approved": true,
		"merged": true, "closed": true, "locked": true,
	}

	if !validStatuses[status] {
		return fmt.Errorf("invalid status: %s", status)
	}

	query := `UPDATE pull_requests SET status = $1, updated_at = $2 WHERE id = $3`
	
	result, err := prm.db.ExecContext(ctx, query, status, time.Now(), prID)
	if err != nil {
		return fmt.Errorf("failed to update status: %w", err)
	}

	rows, _ := result.RowsAffected()
	if rows == 0 {
		return fmt.Errorf("pull request not found")
	}

	// Update timestamps based on status
	switch status {
	case "open":
		prm.db.ExecContext(ctx,
			"UPDATE pull_requests SET ready_for_review_at = $1 WHERE id = $2 AND ready_for_review_at IS NULL",
			time.Now(), prID)
	case "approved":
		prm.db.ExecContext(ctx,
			"UPDATE pull_requests SET approved_at = $1 WHERE id = $2",
			time.Now(), prID)
	case "merged":
		prm.db.ExecContext(ctx,
			"UPDATE pull_requests SET merged_at = $1 WHERE id = $2",
			time.Now(), prID)
	case "closed":
		prm.db.ExecContext(ctx,
			"UPDATE pull_requests SET closed_at = $1 WHERE id = $2",
			time.Now(), prID)
	}

	return nil
}

// MergePullRequest merges a pull request
func (prm *PullRequestManager) MergePullRequest(ctx context.Context, prID string, mergerID, mergerName string, strategy MergeStrategy) error {
	// Get pull request
	pr, err := prm.GetPullRequest(ctx, prID)
	if err != nil {
		return err
	}

	// Check status
	if pr.Status != "approved" && pr.Status != "open" {
		return fmt.Errorf("pull request must be approved before merging")
	}

	// Check for conflicts
	if pr.HasConflicts {
		return fmt.Errorf("pull request has unresolved conflicts")
	}

	// Perform merge
	mergeResult, err := prm.mergeEngine.Merge(ctx, &MergeRequest{
		BuildingID:   pr.BuildingID,
		SourceBranch: pr.SourceBranch,
		TargetBranch: pr.TargetBranch,
		Strategy:     strategy,
		Author:       mergerID,
		Message:      fmt.Sprintf("Merge pull request #%d: %s", pr.PRNumber, pr.Title),
		DryRun:       false,
	})
	if err != nil {
		return fmt.Errorf("merge failed: %w", err)
	}

	if !mergeResult.Success {
		return fmt.Errorf("merge failed: conflicts detected")
	}

	// Update pull request
	now := time.Now()
	query := `
		UPDATE pull_requests 
		SET status = 'merged',
		    merge_state_id = $1,
		    merger_id = $2,
		    merger_name = $3,
		    merged_at = $4,
		    updated_at = $5
		WHERE id = $6`

	_, err = prm.db.ExecContext(ctx, query,
		mergeResult.MergeStateID, mergerID, mergerName, now, now, prID)
	if err != nil {
		return fmt.Errorf("failed to update pull request: %w", err)
	}

	return nil
}

// AddReview adds a review to a pull request
func (prm *PullRequestManager) AddReview(ctx context.Context, prID string, review *PRReview) error {
	review.ID = uuid.New().String()
	review.SubmittedAt = time.Now()

	query := `
		INSERT INTO pr_reviews (
			id, pr_id, reviewer_id, reviewer_name, reviewer_role,
			status, body, commit_id, submitted_at
		) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)`

	_, err := prm.db.ExecContext(ctx, query,
		review.ID, prID, review.ReviewerID, review.ReviewerName, review.ReviewerRole,
		review.Status, review.Body, review.CommitID, review.SubmittedAt)
	if err != nil {
		return fmt.Errorf("failed to add review: %w", err)
	}

	// Update PR status based on review
	if review.Status == "approved" {
		// Check if we have enough approvals
		var approvalCount int
		prm.db.GetContext(ctx, &approvalCount,
			"SELECT COUNT(*) FROM pr_reviews WHERE pr_id = $1 AND status = 'approved' AND dismissed_at IS NULL",
			prID)

		var requiredApprovals int
		prm.db.GetContext(ctx, &requiredApprovals,
			"SELECT required_approvals FROM pull_requests WHERE id = $1", prID)

		if approvalCount >= requiredApprovals {
			prm.UpdatePullRequestStatus(ctx, prID, "approved")
		}
	} else if review.Status == "changes_requested" {
		prm.UpdatePullRequestStatus(ctx, prID, "changes_requested")
	}

	return nil
}

// AddComment adds a comment to a pull request
func (prm *PullRequestManager) AddComment(ctx context.Context, prID string, comment *PRComment) error {
	comment.ID = uuid.New().String()
	comment.CreatedAt = time.Now()
	comment.UpdatedAt = time.Now()

	query := `
		INSERT INTO pr_comments (
			id, pr_id, parent_comment_id, comment_type, line_number, file_path,
			body, author_id, author_name, created_at, updated_at
		) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)`

	_, err := prm.db.ExecContext(ctx, query,
		comment.ID, prID, comment.ParentCommentID, comment.CommentType,
		comment.LineNumber, comment.FilePath, comment.Body,
		comment.AuthorID, comment.AuthorName, comment.CreatedAt, comment.UpdatedAt)
	if err != nil {
		return fmt.Errorf("failed to add comment: %w", err)
	}

	// Update comment count
	prm.db.ExecContext(ctx,
		"UPDATE pull_requests SET comments_count = comments_count + 1 WHERE id = $1", prID)

	return nil
}

// ListPullRequests lists pull requests for a building
func (prm *PullRequestManager) ListPullRequests(ctx context.Context, buildingID string, status string) ([]*PullRequest, error) {
	query := `
		SELECT 
			id, pr_number, building_id, source_branch, target_branch,
			title, pr_type, priority, status, has_conflicts,
			author_name, created_at, updated_at
		FROM pull_requests
		WHERE building_id = $1`

	args := []interface{}{buildingID}
	if status != "" {
		query += " AND status = $2"
		args = append(args, status)
	}
	query += " ORDER BY created_at DESC"

	var prs []*PullRequest
	err := prm.db.SelectContext(ctx, &prs, query, args...)
	if err != nil {
		return nil, fmt.Errorf("failed to list pull requests: %w", err)
	}

	return prs, nil
}

// PRReview represents a pull request review
type PRReview struct {
	ID            string     `json:"id" db:"id"`
	PRID          string     `json:"pr_id" db:"pr_id"`
	ReviewerID    string     `json:"reviewer_id" db:"reviewer_id"`
	ReviewerName  string     `json:"reviewer_name" db:"reviewer_name"`
	ReviewerRole  string     `json:"reviewer_role" db:"reviewer_role"`
	Status        string     `json:"status" db:"status"`
	Body          string     `json:"body" db:"body"`
	CommitID      string     `json:"commit_id" db:"commit_id"`
	SubmittedAt   time.Time  `json:"submitted_at" db:"submitted_at"`
	DismissedAt   *time.Time `json:"dismissed_at" db:"dismissed_at"`
	DismissedBy   *string    `json:"dismissed_by" db:"dismissed_by"`
	DismissReason *string    `json:"dismiss_reason" db:"dismiss_reason"`
}

// PRComment represents a pull request comment
type PRComment struct {
	ID              string     `json:"id" db:"id"`
	PRID            string     `json:"pr_id" db:"pr_id"`
	ParentCommentID *string    `json:"parent_comment_id" db:"parent_comment_id"`
	CommentType     string     `json:"comment_type" db:"comment_type"`
	LineNumber      *int       `json:"line_number" db:"line_number"`
	FilePath        *string    `json:"file_path" db:"file_path"`
	Body            string     `json:"body" db:"body"`
	AuthorID        string     `json:"author_id" db:"author_id"`
	AuthorName      string     `json:"author_name" db:"author_name"`
	IsResolved      bool       `json:"is_resolved" db:"is_resolved"`
	ResolvedBy      *string    `json:"resolved_by" db:"resolved_by"`
	ResolvedAt      *time.Time `json:"resolved_at" db:"resolved_at"`
	CreatedAt       time.Time  `json:"created_at" db:"created_at"`
	UpdatedAt       time.Time  `json:"updated_at" db:"updated_at"`
	DeletedAt       *time.Time `json:"deleted_at" db:"deleted_at"`
}

// DiffStats represents statistics about changes
type DiffStats struct {
	LinesAdded   int
	LinesRemoved int
	FilesChanged int
}

// calculateDiffStats calculates statistics for changes between states
func (prm *PullRequestManager) calculateDiffStats(ctx context.Context, sourceStateID, targetStateID string) (*DiffStats, error) {
	// Simplified implementation - would calculate actual diff stats
	return &DiffStats{
		LinesAdded:   42,
		LinesRemoved: 17,
		FilesChanged: 3,
	}, nil
}

// Commit represents a commit in the PR
type Commit struct {
	StateID     string
	Message     string
	AuthorID    string
	AuthorName  string
	CommittedAt time.Time
}

// getCommitsBetween gets commits between two states
func (prm *PullRequestManager) getCommitsBetween(ctx context.Context, baseStateID, headStateID string) ([]Commit, error) {
	// Walk the parent chain from head to base
	commits := []Commit{}
	currentID := headStateID

	for currentID != baseStateID {
		var state struct {
			ID            string     `db:"id"`
			ParentStateID *string    `db:"parent_state_id"`
			CommitMessage string     `db:"commit_message"`
			CommittedBy   string     `db:"committed_by"`
			CreatedAt     time.Time  `db:"created_at"`
		}

		err := prm.db.GetContext(ctx, &state,
			"SELECT id, parent_state_id, commit_message, committed_by, created_at FROM building_states WHERE id = $1",
			currentID)
		if err != nil {
			return nil, err
		}

		commits = append(commits, Commit{
			StateID:     state.ID,
			Message:     state.CommitMessage,
			AuthorID:    state.CommittedBy,
			AuthorName:  state.CommittedBy, // Would look up actual name
			CommittedAt: state.CreatedAt,
		})

		if state.ParentStateID == nil {
			break
		}
		currentID = *state.ParentStateID
	}

	// Reverse to get chronological order
	for i, j := 0, len(commits)-1; i < j; i, j = i+1, j-1 {
		commits[i], commits[j] = commits[j], commits[i]
	}

	return commits, nil
}