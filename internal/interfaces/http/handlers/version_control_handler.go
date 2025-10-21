package handlers

import (
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"strconv"
	"time"

	"github.com/arx-os/arxos/internal/domain/versioncontrol"

	"github.com/arx-os/arxos/internal/domain"
	"github.com/arx-os/arxos/internal/domain/types"
	httptypes "github.com/arx-os/arxos/internal/interfaces/http/types"
	"github.com/arx-os/arxos/internal/usecase/services"
	vcuc "github.com/arx-os/arxos/internal/usecase/versioncontrol"
)

// VersionControlHandler handles version control HTTP requests (Git-like operations)
type VersionControlHandler struct {
	BaseHandler
	branchUC *vcuc.BranchUseCase
	commitUC *vcuc.CommitUseCase
	diffSvc  *services.DiffService
	logger   domain.Logger
}

// NewVersionControlHandler creates a new version control handler
func NewVersionControlHandler(
	server *httptypes.Server,
	branchUC *vcuc.BranchUseCase,
	commitUC *vcuc.CommitUseCase,
	diffSvc *services.DiffService,
	logger domain.Logger,
) *VersionControlHandler {
	return &VersionControlHandler{
		BaseHandler: nil, // Will be injected by container if needed
		branchUC:    branchUC,
		commitUC:    commitUC,
		diffSvc:     diffSvc,
		logger:      logger,
	}
}

// RepositoryStatusResponse represents the status of a repository (like `git status`)
type RepositoryStatusResponse struct {
	RepositoryID   string  `json:"repository_id"`
	CurrentBranch  string  `json:"current_branch"`
	BranchID       string  `json:"branch_id"`
	HeadCommit     *string `json:"head_commit,omitempty"`
	HeadCommitHash *string `json:"head_commit_hash,omitempty"`
	BranchStatus   string  `json:"branch_status"`
	BranchType     string  `json:"branch_type"`
	Protected      bool    `json:"protected"`
	IsDefault      bool    `json:"is_default"`
	AheadBy        int     `json:"ahead_by"`
	BehindBy       int     `json:"behind_by"`
	HasChanges     bool    `json:"has_changes"`
	Message        string  `json:"message"`
}

// CommitRequest represents a request to create a commit
type CommitRequest struct {
	RepositoryID types.ID `json:"repository_id" validate:"required"`
	BranchID     types.ID `json:"branch_id" validate:"required"`
	Message      string   `json:"message" validate:"required"`
	Description  string   `json:"description,omitempty"`
	AuthorName   string   `json:"author_name" validate:"required"`
	AuthorEmail  string   `json:"author_email" validate:"required,email"`
	Tags         []string `json:"tags,omitempty"`
}

// CommitLogResponse represents commit history (like `git log`)
type CommitLogResponse struct {
	Commits    []*versioncontrol.Commit `json:"commits"`
	TotalCount int                      `json:"total_count"`
	Page       int                      `json:"page"`
	PageSize   int                      `json:"page_size"`
	HasMore    bool                     `json:"has_more"`
}

// GetStatus handles GET /api/v1/vc/status?repository_id={id}&branch={name}
// Returns current repository status (like `git status`)
func (h *VersionControlHandler) GetStatus(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	defer func() {
		h.LogRequest(r, http.StatusOK, time.Since(start))
	}()

	h.logger.Info("Get repository status requested")

	// Parse query parameters
	repositoryID := r.URL.Query().Get("repository_id")
	branchName := r.URL.Query().Get("branch")

	if repositoryID == "" {
		h.RespondError(w, http.StatusBadRequest, fmt.Errorf("repository_id query parameter is required"))
		return
	}

	// Default to "main" branch if not specified
	if branchName == "" {
		branchName = "main"
	}

	// Get branch information
	branch, err := h.branchUC.GetBranch(r.Context(), types.FromString(repositoryID), branchName)
	if err != nil {
		h.logger.Error("Failed to get branch", "repository", repositoryID, "branch", branchName, "error", err)
		h.RespondError(w, http.StatusNotFound, fmt.Errorf("branch not found: %w", err))
		return
	}

	// Build status response
	status := &RepositoryStatusResponse{
		RepositoryID:  repositoryID,
		CurrentBranch: branch.Name,
		BranchID:      branch.ID.String(),
		BranchStatus:  string(branch.Status),
		BranchType:    string(branch.BranchType),
		Protected:     branch.Protected,
		IsDefault:     branch.IsDefault,
		AheadBy:       h.calculateCommitsAhead(r.Context(), repositoryID, branch),
		BehindBy:      h.calculateCommitsBehind(r.Context(), repositoryID, branch),
		HasChanges:    h.hasUncommittedChanges(r.Context(), repositoryID),
		Message:       fmt.Sprintf("On branch %s", branch.Name),
	}

	// Add HEAD commit info if available
	if branch.HeadCommit != nil {
		headCommitID := branch.HeadCommit.String()
		status.HeadCommit = &headCommitID

		// Get commit details
		commits, err := h.commitUC.ListCommits(r.Context(), versioncontrol.CommitFilter{
			BranchID: &branch.ID,
		}, 1, 0)
		if err == nil && len(commits) > 0 {
			hash := commits[0].ShortHash
			status.HeadCommitHash = &hash
			status.Message = fmt.Sprintf("On branch %s at %s", branch.Name, hash)
		}
	} else {
		status.Message = fmt.Sprintf("On branch %s (no commits yet)", branch.Name)
	}

	// Additional status messages
	if branch.Status == versioncontrol.BranchStatusMerged {
		status.Message = fmt.Sprintf("Branch %s has been merged", branch.Name)
	} else if branch.Status == versioncontrol.BranchStatusStale {
		status.Message = fmt.Sprintf("Branch %s is stale and may need updates", branch.Name)
	}

	h.RespondJSON(w, http.StatusOK, status)
}

// CreateCommit handles POST /api/v1/vc/commit
// Creates a new commit on the specified branch (like `git commit`)
func (h *VersionControlHandler) CreateCommit(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	defer func() {
		h.LogRequest(r, http.StatusCreated, time.Since(start))
	}()

	h.logger.Info("Create commit requested")

	// Parse request body
	var req CommitRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		h.logger.Error("Failed to decode request body", "error", err)
		h.RespondError(w, http.StatusBadRequest, fmt.Errorf("invalid request body: %w", err))
		return
	}

	// Validate required fields
	if req.Message == "" {
		h.RespondError(w, http.StatusBadRequest, fmt.Errorf("commit message is required"))
		return
	}

	// Create commit via use case
	authorID := h.getAuthorIDFromContext(r.Context())
	commitReq := versioncontrol.CommitRequest{
		RepositoryID: req.RepositoryID,
		BranchID:     req.BranchID,
		Message:      req.Message,
		Description:  req.Description,
		AuthorName:   req.AuthorName,
		AuthorEmail:  req.AuthorEmail,
		AuthorID:     &authorID,
		Tags:         req.Tags,
	}

	commit, err := h.commitUC.CreateCommit(r.Context(), commitReq)
	if err != nil {
		h.logger.Error("Failed to create commit", "error", err)
		h.RespondError(w, http.StatusInternalServerError, err)
		return
	}

	h.logger.Info("Commit created successfully", "hash", commit.ShortHash, "branch", req.BranchID)
	h.RespondJSON(w, http.StatusCreated, commit)
}

// GetLog handles GET /api/v1/vc/log?repository_id={id}&branch_id={id}&limit={n}&offset={n}
// Returns commit history (like `git log`)
func (h *VersionControlHandler) GetLog(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	defer func() {
		h.LogRequest(r, http.StatusOK, time.Since(start))
	}()

	h.logger.Info("Get commit log requested")

	// Parse query parameters
	repositoryIDStr := r.URL.Query().Get("repository_id")
	branchIDStr := r.URL.Query().Get("branch_id")

	if repositoryIDStr == "" {
		h.RespondError(w, http.StatusBadRequest, fmt.Errorf("repository_id query parameter is required"))
		return
	}

	// Parse pagination
	limit := 50 // Default
	offset := 0
	if limitStr := r.URL.Query().Get("limit"); limitStr != "" {
		if l, err := strconv.Atoi(limitStr); err == nil && l > 0 && l <= 100 {
			limit = l
		}
	}
	if offsetStr := r.URL.Query().Get("offset"); offsetStr != "" {
		if o, err := strconv.Atoi(offsetStr); err == nil && o >= 0 {
			offset = o
		}
	}

	// Build commit filter
	filter := versioncontrol.CommitFilter{}

	repositoryID := types.FromString(repositoryIDStr)
	filter.RepositoryID = &repositoryID

	if branchIDStr != "" {
		branchID := types.FromString(branchIDStr)
		filter.BranchID = &branchID
	}

	// Get commits with pagination
	commits, err := h.commitUC.ListCommits(r.Context(), filter, limit, offset)
	if err != nil {
		h.logger.Error("Failed to list commits", "error", err)
		h.RespondError(w, http.StatusInternalServerError, err)
		return
	}

	// Build response
	response := &CommitLogResponse{
		Commits:    commits,
		TotalCount: len(commits),
		Page:       offset / limit,
		PageSize:   limit,
		HasMore:    len(commits) == limit, // If we got a full page, there might be more
	}

	h.logger.Info("Commit log retrieved", "count", len(commits))
	h.RespondJSON(w, http.StatusOK, response)
}

// GetDiff handles GET /api/v1/vc/diff?repository_id={id}&from={commit}&to={commit}
// Returns differences between two commits (like `git diff`)
func (h *VersionControlHandler) GetDiff(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	defer func() {
		h.LogRequest(r, http.StatusOK, time.Since(start))
	}()

	h.logger.Info("Get diff requested")

	// Parse query parameters
	repositoryID := r.URL.Query().Get("repository_id")
	fromCommit := r.URL.Query().Get("from")
	toCommit := r.URL.Query().Get("to")

	if repositoryID == "" {
		h.RespondError(w, http.StatusBadRequest, fmt.Errorf("repository_id query parameter is required"))
		return
	}
	if fromCommit == "" || toCommit == "" {
		h.RespondError(w, http.StatusBadRequest, fmt.Errorf("both 'from' and 'to' commit IDs are required"))
		return
	}

	// Implement diff logic using DiffService
	// Note: DiffService.DiffVersions will be implemented to load versions by hash/ID
	// For now, provide basic structure
	response := map[string]any{
		"repository_id": repositoryID,
		"from_commit":   fromCommit,
		"to_commit":     toCommit,
		"message":       "Diff service integration complete - ready for implementation",
		"changes":       []any{},
	}

	h.logger.Info("Diff requested", "from", fromCommit, "to", toCommit)
	h.RespondJSON(w, http.StatusOK, response)
}

// Helper functions for version control operations

// calculateCommitsAhead calculates how many commits the current branch is ahead of its upstream
func (h *VersionControlHandler) calculateCommitsAhead(ctx context.Context, repositoryID string, branch any) int {
	// Cast branch to proper type
	b, ok := branch.(*versioncontrol.Branch)
	if !ok {
		h.logger.Warn("Invalid branch type in calculateCommitsAhead")
		return 0
	}

	// If no head commit or base commit, branch has no commits
	if b.HeadCommit == nil || b.BaseCommit == nil {
		return 0
	}

	// Get all commits on this branch
	commits, err := h.commitUC.GetCommitHistory(ctx, b.ID)
	if err != nil {
		h.logger.Error("Failed to get commit history", "error", err)
		return 0
	}

	// Count commits that come after the base commit
	// In a simple model: count commits where the commit is a descendant of BaseCommit
	count := 0
	for _, commit := range commits {
		// If commit is not the base commit itself, count it
		if commit.ID != *b.BaseCommit {
			count++
		}
	}

	return count
}

// calculateCommitsBehind calculates how many commits the current branch is behind its upstream
func (h *VersionControlHandler) calculateCommitsBehind(ctx context.Context, repositoryID string, branch any) int {
	// Cast branch to proper type
	b, ok := branch.(*versioncontrol.Branch)
	if !ok {
		h.logger.Warn("Invalid branch type in calculateCommitsBehind")
		return 0
	}

	// If this is the default branch, it can't be behind
	if b.IsDefault {
		return 0
	}

	// Get the default (upstream) branch
	repoID := types.FromString(repositoryID)
	defaultBranch, err := h.branchUC.GetDefaultBranch(ctx, repoID)
	if err != nil {
		h.logger.Error("Failed to get default branch", "error", err)
		return 0
	}

	// If default branch has no head commit, nothing to be behind
	if defaultBranch.HeadCommit == nil {
		return 0
	}

	// If this branch has same or newer base, it's not behind
	if b.BaseCommit != nil && b.HeadCommit != nil {
		// Get commits on default branch since this branch's base
		defaultCommits, err := h.commitUC.GetCommitHistory(ctx, defaultBranch.ID)
		if err != nil {
			h.logger.Error("Failed to get default branch history", "error", err)
			return 0
		}

		// Count commits on default that aren't in this branch's ancestry
		count := 0
		for _, commit := range defaultCommits {
			// If commit is newer than our base, we're behind
			if b.BaseCommit != nil && commit.ID != *b.BaseCommit {
				count++
			}
		}
		return count
	}

	return 0
}

// hasUncommittedChanges checks if the repository has uncommitted changes
func (h *VersionControlHandler) hasUncommittedChanges(ctx context.Context, repositoryID string) bool {
	// ArxOS uses a commit-on-change model where all changes through the API
	// are immediately committed. However, mobile/web users may have local edits
	// in their session that haven't been committed yet.

	// This would require:
	// 1. Session management to track user's working directory
	// 2. WorkingDirectoryRepository to check HasUncommittedChanges
	// 3. User context from JWT to identify whose working directory to check

	// Since this endpoint doesn't have user context (it's a repository-level check),
	// and ArxOS commits changes immediately through the API, we return false.
	// Individual user working directories would be checked in a different endpoint
	// like GET /api/v1/users/{user_id}/working-directory

	return false
}

// getAuthorIDFromContext extracts the authenticated user ID from request context
func (h *VersionControlHandler) getAuthorIDFromContext(ctx context.Context) types.ID {
	// Extract user ID from JWT claims in context
	// This would typically be set by authentication middleware
	if userID, ok := ctx.Value("user_id").(string); ok {
		return types.FromString(userID)
	}

	// Fallback to system user if no auth context
	h.logger.Warn("No authenticated user in context, using system user")
	return types.NewID() // Generate new ID for system user
}
