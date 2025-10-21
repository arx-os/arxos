package handlers

import (
	"github.com/arx-os/arxos/internal/domain/versioncontrol"
	"fmt"
	"net/http"
	"strconv"
	"time"

	"github.com/go-chi/chi/v5"

	"github.com/arx-os/arxos/internal/domain"
	"github.com/arx-os/arxos/internal/domain/types"
	vcuc "github.com/arx-os/arxos/internal/usecase/versioncontrol"
)

// PRHandler handles Pull Request HTTP requests
type PRHandler struct {
	BaseHandler
	prUC     *vcuc.PullRequestUseCase
	branchUC *vcuc.BranchUseCase
	logger   domain.Logger
}

// NewPRHandler creates a new PR handler with proper dependency injection
func NewPRHandler(
	base BaseHandler,
	prUC *vcuc.PullRequestUseCase,
	branchUC *vcuc.BranchUseCase,
	logger domain.Logger,
) *PRHandler {
	return &PRHandler{
		BaseHandler: base,
		prUC:        prUC,
		branchUC:    branchUC,
		logger:      logger,
	}
}

// HandleCreatePR handles POST /api/v1/pr
func (h *PRHandler) HandleCreatePR(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	defer func() {
		h.LogRequest(r, http.StatusCreated, time.Since(start))
	}()

	h.logger.Info("Create PR requested")

	// Parse request body
	var req versioncontrol.CreatePRRequest
	if err := h.ParseRequestBody(r, &req); err != nil {
		h.RespondError(w, http.StatusBadRequest, err)
		return
	}

	// Create PR
	pr, err := h.prUC.CreatePullRequest(r.Context(), req)
	if err != nil {
		h.logger.Error("Failed to create PR", "error", err)
		h.RespondError(w, http.StatusInternalServerError, err)
		return
	}

	h.RespondJSON(w, http.StatusCreated, map[string]any{
		"success": true,
		"pr":      pr,
	})
}

// HandleListPRs handles GET /api/v1/pr
func (h *PRHandler) HandleListPRs(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	defer func() {
		h.LogRequest(r, http.StatusOK, time.Since(start))
	}()

	// Get repository ID from query params
	repositoryID := r.URL.Query().Get("repository_id")
	if repositoryID == "" {
		h.RespondError(w, http.StatusBadRequest, fmt.Errorf("repository_id is required"))
		return
	}

	// Build filter
	filter := versioncontrol.PRFilter{}

	rid := types.FromString(repositoryID)
	filter.RepositoryID = &rid

	if status := r.URL.Query().Get("status"); status != "" {
		prStatus := versioncontrol.PRStatus(status)
		filter.Status = &prStatus
	}

	if assignedTo := r.URL.Query().Get("assigned_to"); assignedTo != "" {
		aid := types.FromString(assignedTo)
		filter.AssignedTo = &aid
	}

	// Parse pagination
	limit := 50
	offset := 0

	if limitStr := r.URL.Query().Get("limit"); limitStr != "" {
		if l, err := strconv.Atoi(limitStr); err == nil && l > 0 {
			limit = l
		}
	}

	if offsetStr := r.URL.Query().Get("offset"); offsetStr != "" {
		if o, err := strconv.Atoi(offsetStr); err == nil && o >= 0 {
			offset = o
		}
	}

	// List PRs
	prs, err := h.prUC.ListPullRequests(r.Context(), filter, limit, offset)
	if err != nil {
		h.logger.Error("Failed to list PRs", "error", err)
		h.RespondError(w, http.StatusInternalServerError, err)
		return
	}

	response := map[string]any{
		"pull_requests": prs,
		"repository_id": repositoryID,
		"count":         len(prs),
		"limit":         limit,
		"offset":        offset,
	}

	h.RespondJSON(w, http.StatusOK, response)
}

// HandleGetPR handles GET /api/v1/pr/{id}
func (h *PRHandler) HandleGetPR(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	defer func() {
		h.LogRequest(r, http.StatusOK, time.Since(start))
	}()

	// Get PR ID from URL
	prIDStr := chi.URLParam(r, "id")
	if prIDStr == "" {
		h.RespondError(w, http.StatusBadRequest, fmt.Errorf("pr id is required"))
		return
	}

	prID, err := strconv.Atoi(prIDStr)
	if err != nil {
		h.RespondError(w, http.StatusBadRequest, fmt.Errorf("invalid pr id"))
		return
	}

	// Get repository ID from query (required to identify PR)
	repositoryID := r.URL.Query().Get("repository_id")
	if repositoryID == "" {
		h.RespondError(w, http.StatusBadRequest, fmt.Errorf("repository_id is required"))
		return
	}

	// Get PR
	rid := types.FromString(repositoryID)
	pr, err := h.prUC.GetPullRequest(r.Context(), rid, prID)
	if err != nil {
		h.logger.Error("Failed to get PR", "pr_id", prID, "error", err)
		h.RespondError(w, http.StatusNotFound, fmt.Errorf("pull request not found"))
		return
	}

	h.RespondJSON(w, http.StatusOK, pr)
}

// HandleApprovePR handles POST /api/v1/pr/{id}/approve
func (h *PRHandler) HandleApprovePR(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	defer func() {
		h.LogRequest(r, http.StatusOK, time.Since(start))
	}()

	// Get PR ID from URL
	prIDStr := chi.URLParam(r, "id")
	if prIDStr == "" {
		h.RespondError(w, http.StatusBadRequest, fmt.Errorf("pr id is required"))
		return
	}

	prID, err := strconv.Atoi(prIDStr)
	if err != nil {
		h.RespondError(w, http.StatusBadRequest, fmt.Errorf("invalid pr id"))
		return
	}

	// Parse request body (optional comment)
	var req struct {
		RepositoryID string `json:"repository_id"`
		Comment      string `json:"comment,omitempty"`
	}

	if err := h.ParseRequestBody(r, &req); err != nil {
		h.RespondError(w, http.StatusBadRequest, err)
		return
	}

	if req.RepositoryID == "" {
		h.RespondError(w, http.StatusBadRequest, fmt.Errorf("repository_id is required"))
		return
	}

	// Get user from context for reviewer ID
	user, err := h.GetUserFromContext(r.Context())
	if err != nil {
		h.RespondError(w, http.StatusUnauthorized, err)
		return
	}

	// Approve PR
	rid := types.FromString(req.RepositoryID)

	// Get the PR to get its ID
	pr, err := h.prUC.GetPullRequest(r.Context(), rid, prID)
	if err != nil {
		h.RespondError(w, http.StatusNotFound, fmt.Errorf("pull request not found"))
		return
	}

	if err := h.prUC.ApprovePullRequest(r.Context(), pr.ID, user.ID, req.Comment); err != nil {
		h.logger.Error("Failed to approve PR", "pr_id", prID, "error", err)
		h.RespondError(w, http.StatusInternalServerError, err)
		return
	}

	h.RespondJSON(w, http.StatusOK, map[string]any{
		"success": true,
		"pr_id":   prID,
		"message": "Pull request approved",
	})
}

// HandleMergePR handles POST /api/v1/pr/{id}/merge
func (h *PRHandler) HandleMergePR(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	defer func() {
		h.LogRequest(r, http.StatusOK, time.Since(start))
	}()

	// Get PR ID from URL
	prIDStr := chi.URLParam(r, "id")
	if prIDStr == "" {
		h.RespondError(w, http.StatusBadRequest, fmt.Errorf("pr id is required"))
		return
	}

	prID, err := strconv.Atoi(prIDStr)
	if err != nil {
		h.RespondError(w, http.StatusBadRequest, fmt.Errorf("invalid pr id"))
		return
	}

	// Parse request body
	var req struct {
		RepositoryID string `json:"repository_id"`
		Message      string `json:"message,omitempty"`
	}

	if err := h.ParseRequestBody(r, &req); err != nil {
		h.RespondError(w, http.StatusBadRequest, err)
		return
	}

	if req.RepositoryID == "" {
		h.RespondError(w, http.StatusBadRequest, fmt.Errorf("repository_id is required"))
		return
	}

	// Get user from context
	user, err := h.GetUserFromContext(r.Context())
	if err != nil {
		h.RespondError(w, http.StatusUnauthorized, err)
		return
	}

	// Get the PR to get its ID
	rid := types.FromString(req.RepositoryID)
	pr, err := h.prUC.GetPullRequest(r.Context(), rid, prID)
	if err != nil {
		h.RespondError(w, http.StatusNotFound, fmt.Errorf("pull request not found"))
		return
	}

	// Merge PR
	mergeReq := versioncontrol.MergePRRequest{
		PRID:     pr.ID,
		MergedBy: user.ID,
		Message:  req.Message,
		Strategy: "merge", // Default merge strategy
	}

	if err := h.prUC.MergePullRequest(r.Context(), mergeReq); err != nil {
		h.logger.Error("Failed to merge PR", "pr_id", prID, "error", err)
		h.RespondError(w, http.StatusInternalServerError, err)
		return
	}

	h.RespondJSON(w, http.StatusOK, map[string]any{
		"success": true,
		"pr_id":   prID,
		"message": "Pull request merged successfully",
	})
}

// HandleClosePR handles POST /api/v1/pr/{id}/close
func (h *PRHandler) HandleClosePR(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	defer func() {
		h.LogRequest(r, http.StatusOK, time.Since(start))
	}()

	// Get PR ID from URL
	prIDStr := chi.URLParam(r, "id")
	if prIDStr == "" {
		h.RespondError(w, http.StatusBadRequest, fmt.Errorf("pr id is required"))
		return
	}

	prID, err := strconv.Atoi(prIDStr)
	if err != nil {
		h.RespondError(w, http.StatusBadRequest, fmt.Errorf("invalid pr id"))
		return
	}

	// Parse request body
	var req struct {
		RepositoryID string `json:"repository_id"`
		Reason       string `json:"reason,omitempty"`
	}

	if err := h.ParseRequestBody(r, &req); err != nil {
		h.RespondError(w, http.StatusBadRequest, err)
		return
	}

	if req.RepositoryID == "" {
		h.RespondError(w, http.StatusBadRequest, fmt.Errorf("repository_id is required"))
		return
	}

	// Get the PR to get its ID
	rid := types.FromString(req.RepositoryID)
	pr, err := h.prUC.GetPullRequest(r.Context(), rid, prID)
	if err != nil {
		h.RespondError(w, http.StatusNotFound, fmt.Errorf("pull request not found"))
		return
	}

	// Close PR
	if err := h.prUC.ClosePullRequest(r.Context(), pr.ID, req.Reason); err != nil {
		h.logger.Error("Failed to close PR", "pr_id", prID, "error", err)
		h.RespondError(w, http.StatusInternalServerError, err)
		return
	}

	h.RespondJSON(w, http.StatusOK, map[string]any{
		"success": true,
		"pr_id":   prID,
		"message": "Pull request closed",
	})
}

// HandleAddComment handles POST /api/v1/pr/{id}/comments
func (h *PRHandler) HandleAddComment(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	defer func() {
		h.LogRequest(r, http.StatusCreated, time.Since(start))
	}()

	// Get PR ID from URL
	prIDStr := chi.URLParam(r, "id")
	if prIDStr == "" {
		h.RespondError(w, http.StatusBadRequest, fmt.Errorf("pr id is required"))
		return
	}

	prID, err := strconv.Atoi(prIDStr)
	if err != nil {
		h.RespondError(w, http.StatusBadRequest, fmt.Errorf("invalid pr id"))
		return
	}

	// Parse request body
	var req struct {
		RepositoryID string `json:"repository_id"`
		Comment      string `json:"comment"`
	}

	if err := h.ParseRequestBody(r, &req); err != nil {
		h.RespondError(w, http.StatusBadRequest, err)
		return
	}

	if req.RepositoryID == "" {
		h.RespondError(w, http.StatusBadRequest, fmt.Errorf("repository_id is required"))
		return
	}

	if req.Comment == "" {
		h.RespondError(w, http.StatusBadRequest, fmt.Errorf("comment is required"))
		return
	}

	// Get user from context
	user, err := h.GetUserFromContext(r.Context())
	if err != nil {
		h.RespondError(w, http.StatusUnauthorized, err)
		return
	}

	// NOTE: Comment storage implementation
	// Comments are tracked in pr_comments table via PullRequestRepository
	// This endpoint acknowledges the comment for now
	// Full implementation requires: PullRequestRepository.AddComment(prID, authorID, comment)
	// Database table exists (pr_comments), just needs repository method
	h.logger.Info("Comment acknowledged for PR",
		"pr_id", prID,
		"author", user.ID,
		"comment_length", len(req.Comment),
		"note", "Comment persistence requires PullRequestRepository.AddComment method")

	h.RespondJSON(w, http.StatusCreated, map[string]any{
		"success": true,
		"pr_id":   prID,
		"message": "Comment acknowledged (persistence pending PullRequestRepository enhancement)",
		"author":  user.ID.String(),
	})
}
