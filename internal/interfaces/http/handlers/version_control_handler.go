package handlers

import (
	"encoding/json"
	"fmt"
	"net/http"
	"strconv"
	"time"

	"github.com/arx-os/arxos/internal/domain"
	"github.com/arx-os/arxos/internal/domain/types"
	httptypes "github.com/arx-os/arxos/internal/interfaces/http/types"
	"github.com/arx-os/arxos/internal/usecase"
)

// VersionControlHandler handles version control HTTP requests (Git-like operations)
type VersionControlHandler struct {
	BaseHandler
	branchUC *usecase.BranchUseCase
	commitUC *usecase.CommitUseCase
	diffSvc  *usecase.DiffService
	logger   domain.Logger
}

// NewVersionControlHandler creates a new version control handler
func NewVersionControlHandler(
	server *httptypes.Server,
	branchUC *usecase.BranchUseCase,
	commitUC *usecase.CommitUseCase,
	diffSvc *usecase.DiffService,
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
	Commits    []*domain.Commit `json:"commits"`
	TotalCount int              `json:"total_count"`
	Page       int              `json:"page"`
	PageSize   int              `json:"page_size"`
	HasMore    bool             `json:"has_more"`
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
		AheadBy:       0,     // TODO: Calculate commits ahead of base
		BehindBy:      0,     // TODO: Calculate commits behind base
		HasChanges:    false, // TODO: Check for uncommitted changes
		Message:       fmt.Sprintf("On branch %s", branch.Name),
	}

	// Add HEAD commit info if available
	if branch.HeadCommit != nil {
		headCommitID := branch.HeadCommit.String()
		status.HeadCommit = &headCommitID

		// Get commit details
		commits, err := h.commitUC.ListCommits(r.Context(), domain.CommitFilter{
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
	if branch.Status == domain.BranchStatusMerged {
		status.Message = fmt.Sprintf("Branch %s has been merged", branch.Name)
	} else if branch.Status == domain.BranchStatusStale {
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
	authorID := types.NewID() // TODO: Get from authenticated user context
	commitReq := domain.CommitRequest{
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
	filter := domain.CommitFilter{}

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

	// TODO: Implement diff logic using DiffService
	// For now, return a placeholder response
	response := map[string]interface{}{
		"repository_id": repositoryID,
		"from_commit":   fromCommit,
		"to_commit":     toCommit,
		"message":       "Diff calculation not yet implemented - use DiffService.DiffVersions",
		"changes":       []interface{}{},
	}

	h.logger.Info("Diff requested (not yet fully implemented)", "from", fromCommit, "to", toCommit)
	h.RespondJSON(w, http.StatusOK, response)
}
