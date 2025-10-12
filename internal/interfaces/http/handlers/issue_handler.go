package handlers

import (
	"fmt"
	"net/http"
	"strconv"
	"time"

	"github.com/go-chi/chi/v5"

	"github.com/arx-os/arxos/internal/domain"
	"github.com/arx-os/arxos/internal/domain/types"
	"github.com/arx-os/arxos/internal/usecase"
)

// IssueHandler handles Issue HTTP requests
type IssueHandler struct {
	BaseHandler
	issueUC *usecase.IssueUseCase
	logger  domain.Logger
}

// NewIssueHandler creates a new Issue handler with proper dependency injection
func NewIssueHandler(
	base BaseHandler,
	issueUC *usecase.IssueUseCase,
	logger domain.Logger,
) *IssueHandler {
	return &IssueHandler{
		BaseHandler: base,
		issueUC:     issueUC,
		logger:      logger,
	}
}

// HandleCreateIssue handles POST /api/v1/issues
func (h *IssueHandler) HandleCreateIssue(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	defer func() {
		h.LogRequest(r, http.StatusCreated, time.Since(start))
	}()

	h.logger.Info("Create issue requested")

	// Parse request body
	var req domain.CreateIssueRequest
	if err := h.ParseRequestBody(r, &req); err != nil {
		h.RespondError(w, http.StatusBadRequest, err)
		return
	}

	// Create issue
	issue, err := h.issueUC.CreateIssue(r.Context(), req)
	if err != nil {
		h.logger.Error("Failed to create issue", "error", err)
		h.RespondError(w, http.StatusInternalServerError, err)
		return
	}

	h.RespondJSON(w, http.StatusCreated, map[string]any{
		"success": true,
		"issue":   issue,
	})
}

// HandleListIssues handles GET /api/v1/issues
func (h *IssueHandler) HandleListIssues(w http.ResponseWriter, r *http.Request) {
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
	filter := domain.IssueFilter{}

	rid := types.FromString(repositoryID)
	filter.RepositoryID = &rid

	if status := r.URL.Query().Get("status"); status != "" {
		issueStatus := domain.IssueStatus(status)
		filter.Status = &issueStatus
	}

	if priority := r.URL.Query().Get("priority"); priority != "" {
		issuePriority := domain.IssuePriority(priority)
		filter.Priority = &issuePriority
	}

	if assignedTo := r.URL.Query().Get("assigned_to"); assignedTo != "" {
		aid := types.FromString(assignedTo)
		filter.AssignedTo = &aid
	}

	if issueType := r.URL.Query().Get("type"); issueType != "" {
		iType := domain.IssueType(issueType)
		filter.IssueType = &iType
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

	// List issues
	issues, err := h.issueUC.ListIssues(r.Context(), filter, limit, offset)
	if err != nil {
		h.logger.Error("Failed to list issues", "error", err)
		h.RespondError(w, http.StatusInternalServerError, err)
		return
	}

	response := map[string]any{
		"issues":        issues,
		"repository_id": repositoryID,
		"count":         len(issues),
		"limit":         limit,
		"offset":        offset,
	}

	h.RespondJSON(w, http.StatusOK, response)
}

// HandleGetIssue handles GET /api/v1/issues/{id}
func (h *IssueHandler) HandleGetIssue(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	defer func() {
		h.LogRequest(r, http.StatusOK, time.Since(start))
	}()

	// Get issue number from URL
	issueNumStr := chi.URLParam(r, "id")
	if issueNumStr == "" {
		h.RespondError(w, http.StatusBadRequest, fmt.Errorf("issue id is required"))
		return
	}

	issueNum, err := strconv.Atoi(issueNumStr)
	if err != nil {
		h.RespondError(w, http.StatusBadRequest, fmt.Errorf("invalid issue id"))
		return
	}

	// Get repository ID from query
	repositoryID := r.URL.Query().Get("repository_id")
	if repositoryID == "" {
		h.RespondError(w, http.StatusBadRequest, fmt.Errorf("repository_id is required"))
		return
	}

	// Get issue
	rid := types.FromString(repositoryID)
	issue, err := h.issueUC.GetIssue(r.Context(), rid, issueNum)
	if err != nil {
		h.logger.Error("Failed to get issue", "issue_num", issueNum, "error", err)
		h.RespondError(w, http.StatusNotFound, fmt.Errorf("issue not found"))
		return
	}

	h.RespondJSON(w, http.StatusOK, issue)
}

// HandleAssignIssue handles POST /api/v1/issues/{id}/assign
func (h *IssueHandler) HandleAssignIssue(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	defer func() {
		h.LogRequest(r, http.StatusOK, time.Since(start))
	}()

	// Get issue ID from URL
	issueIDStr := chi.URLParam(r, "id")
	if issueIDStr == "" {
		h.RespondError(w, http.StatusBadRequest, fmt.Errorf("issue id is required"))
		return
	}

	// Parse request body
	var req struct {
		AssignTo string `json:"assign_to"`
	}

	if err := h.ParseRequestBody(r, &req); err != nil {
		h.RespondError(w, http.StatusBadRequest, err)
		return
	}

	if req.AssignTo == "" {
		h.RespondError(w, http.StatusBadRequest, fmt.Errorf("assign_to is required"))
		return
	}

	// Assign issue
	// For now, log the assignment - full implementation requires AssignIssue method in use case
	h.logger.Info("Issue assignment requested", "issue_id", issueIDStr, "assign_to", req.AssignTo)

	h.RespondJSON(w, http.StatusOK, map[string]any{
		"success":     true,
		"issue_id":    issueIDStr,
		"assigned_to": req.AssignTo,
		"message":     "Issue assignment acknowledged (full implementation pending)",
	})
}

// HandleCloseIssue handles POST /api/v1/issues/{id}/close
func (h *IssueHandler) HandleCloseIssue(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	defer func() {
		h.LogRequest(r, http.StatusOK, time.Since(start))
	}()

	// Get issue ID from URL
	issueIDStr := chi.URLParam(r, "id")
	if issueIDStr == "" {
		h.RespondError(w, http.StatusBadRequest, fmt.Errorf("issue id is required"))
		return
	}

	// Parse request body
	var req struct {
		ResolutionNotes string `json:"resolution_notes,omitempty"`
	}

	if err := h.ParseRequestBody(r, &req); err != nil {
		h.RespondError(w, http.StatusBadRequest, err)
		return
	}

	// Get user from context
	user, err := h.GetUserFromContext(r.Context())
	if err != nil {
		h.RespondError(w, http.StatusUnauthorized, err)
		return
	}

	// Close issue
	issueID := types.FromString(issueIDStr)
	resolveReq := domain.ResolveIssueRequest{
		IssueID:         issueID,
		ResolvedBy:      user.ID,
		ResolutionNotes: req.ResolutionNotes,
	}

	if err := h.issueUC.ResolveIssue(r.Context(), resolveReq); err != nil {
		h.logger.Error("Failed to close issue", "issue_id", issueIDStr, "error", err)
		h.RespondError(w, http.StatusInternalServerError, err)
		return
	}

	h.RespondJSON(w, http.StatusOK, map[string]any{
		"success":  true,
		"issue_id": issueIDStr,
		"message":  "Issue closed successfully",
	})
}
