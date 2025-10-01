package handlers

import (
	"encoding/json"
	"fmt"
	"net/http"
	"strconv"
	"time"

	"github.com/arx-os/arxos/internal/interfaces/http/models"
	"github.com/arx-os/arxos/internal/interfaces/http/types"
	"github.com/arx-os/arxos/internal/usecase"
)

// OrganizationHandler handles organization-related HTTP requests
type OrganizationHandler struct {
	*BaseHandler
	organizationService *usecase.OrganizationUseCase
}

// NewOrganizationHandler creates a new organization handler
func NewOrganizationHandler(server *types.Server, organizationService *usecase.OrganizationUseCase) *OrganizationHandler {
	return &OrganizationHandler{
		BaseHandler:         NewBaseHandler(server),
		organizationService: organizationService,
	}
}

// HandleGetOrganizations handles GET /api/v1/organizations
func (h *OrganizationHandler) HandleGetOrganizations(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	defer func() {
		h.LogRequest(r, http.StatusOK, time.Since(start))
	}()

	// Parse pagination parameters
	limit, offset := h.parsePagination(r)

	// Parse filters
	filter := models.OrganizationFilter{
		Plan:   r.URL.Query().Get("plan"),
		Active: h.parseBoolQuery(r.URL.Query().Get("active")),
	}

	// Get organizations through the service
	organizations, err := h.organizationService.ListOrganizations(r.Context(), filter, limit, offset)
	if err != nil {
		h.HandleError(w, r, err, http.StatusInternalServerError)
		return
	}

	// Convert to response format
	response := models.OrganizationListResponse{
		Organizations: organizations,
		Total:         len(organizations), // This should come from the service
		Limit:         limit,
		Offset:        offset,
	}

	h.RespondJSON(w, http.StatusOK, response)
}

// HandleGetOrganization handles GET /api/v1/organizations/{id}
func (h *OrganizationHandler) HandleGetOrganization(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	defer func() {
		h.LogRequest(r, http.StatusOK, time.Since(start))
	}()

	// Extract organization ID from URL path
	orgID := h.extractIDFromPath(r.URL.Path, "/api/v1/organizations/")
	if orgID == "" {
		h.HandleError(w, r, nil, http.StatusBadRequest)
		return
	}

	// Get organization from service
	organization, err := h.organizationService.GetOrganization(r.Context(), orgID)
	if err != nil {
		h.HandleError(w, r, err, http.StatusNotFound)
		return
	}

	h.RespondJSON(w, http.StatusOK, organization)
}

// HandleCreateOrganization handles POST /api/v1/organizations
func (h *OrganizationHandler) HandleCreateOrganization(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	defer func() {
		h.LogRequest(r, http.StatusCreated, time.Since(start))
	}()

	// Parse request body
	var req models.CreateOrganizationRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		h.HandleError(w, r, err, http.StatusBadRequest)
		return
	}

	// Validate request
	if err := h.validateCreateOrganizationRequest(&req); err != nil {
		h.HandleError(w, r, err, http.StatusBadRequest)
		return
	}

	// Create organization through service
	organization, err := h.organizationService.CreateOrganization(r.Context(), req)
	if err != nil {
		h.HandleError(w, r, err, http.StatusInternalServerError)
		return
	}

	h.RespondJSON(w, http.StatusCreated, organization)
}

// HandleUpdateOrganization handles PUT /api/v1/organizations/{id}
func (h *OrganizationHandler) HandleUpdateOrganization(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	defer func() {
		h.LogRequest(r, http.StatusOK, time.Since(start))
	}()

	// Extract organization ID from URL path
	orgID := h.extractIDFromPath(r.URL.Path, "/api/v1/organizations/")
	if orgID == "" {
		h.HandleError(w, r, nil, http.StatusBadRequest)
		return
	}

	// Parse request body
	var req models.UpdateOrganizationRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		h.HandleError(w, r, err, http.StatusBadRequest)
		return
	}

	// Update organization through service
	organization, err := h.organizationService.UpdateOrganization(r.Context(), orgID, req)
	if err != nil {
		h.HandleError(w, r, err, http.StatusInternalServerError)
		return
	}

	h.RespondJSON(w, http.StatusOK, organization)
}

// HandleDeleteOrganization handles DELETE /api/v1/organizations/{id}
func (h *OrganizationHandler) HandleDeleteOrganization(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	defer func() {
		h.LogRequest(r, http.StatusNoContent, time.Since(start))
	}()

	// Extract organization ID from URL path
	orgID := h.extractIDFromPath(r.URL.Path, "/api/v1/organizations/")
	if orgID == "" {
		h.HandleError(w, r, nil, http.StatusBadRequest)
		return
	}

	// Delete organization through service
	if err := h.organizationService.DeleteOrganization(r.Context(), orgID); err != nil {
		h.HandleError(w, r, err, http.StatusInternalServerError)
		return
	}

	w.WriteHeader(http.StatusNoContent)
}

// HandleGetOrganizationUsers handles GET /api/v1/organizations/{id}/users
func (h *OrganizationHandler) HandleGetOrganizationUsers(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	defer func() {
		h.LogRequest(r, http.StatusOK, time.Since(start))
	}()

	// Extract organization ID from URL path
	orgID := h.extractIDFromPath(r.URL.Path, "/api/v1/organizations/")
	if orgID == "" {
		h.HandleError(w, r, nil, http.StatusBadRequest)
		return
	}

	// Parse pagination parameters
	limit, offset := h.parsePagination(r)

	// Get organization users through service
	users, err := h.organizationService.GetOrganizationUsers(r.Context(), orgID, limit, offset)
	if err != nil {
		h.HandleError(w, r, err, http.StatusInternalServerError)
		return
	}

	// Convert to response format
	response := models.OrganizationUsersResponse{
		Users:  users,
		Total:  len(users), // This should come from the service
		Limit:  limit,
		Offset: offset,
	}

	h.RespondJSON(w, http.StatusOK, response)
}

// Helper methods

func (h *OrganizationHandler) parsePagination(r *http.Request) (int, int) {
	limitStr := r.URL.Query().Get("limit")
	offsetStr := r.URL.Query().Get("offset")

	limit := 20 // default
	offset := 0 // default

	if limitStr != "" {
		if l, err := strconv.Atoi(limitStr); err == nil && l > 0 {
			limit = l
		}
	}

	if offsetStr != "" {
		if o, err := strconv.Atoi(offsetStr); err == nil && o >= 0 {
			offset = o
		}
	}

	return limit, offset
}

func (h *OrganizationHandler) parseBoolQuery(value string) *bool {
	if value == "" {
		return nil
	}
	if value == "true" {
		b := true
		return &b
	}
	if value == "false" {
		b := false
		return &b
	}
	return nil
}

func (h *OrganizationHandler) extractIDFromPath(path, prefix string) string {
	if len(path) <= len(prefix) {
		return ""
	}
	return path[len(prefix):]
}

func (h *OrganizationHandler) validateCreateOrganizationRequest(req *models.CreateOrganizationRequest) error {
	if req.Name == "" {
		return fmt.Errorf("name is required")
	}
	if req.Plan == "" {
		return fmt.Errorf("plan is required")
	}
	return nil
}
