package handlers

import (
	"encoding/json"
	"fmt"
	"net/http"
	"strconv"
	"time"

	"github.com/go-chi/chi/v5"

	"github.com/arx-os/arxos/internal/domain"
	"github.com/arx-os/arxos/internal/domain/types"
	"github.com/arx-os/arxos/internal/usecase/auth"
)

// OrganizationHandler handles organization-related HTTP requests
type OrganizationHandler struct {
	BaseHandler
	organizationUC *auth.OrganizationUseCase
	logger         domain.Logger
}

// NewOrganizationHandler creates a new organization handler
func NewOrganizationHandler(base BaseHandler, organizationUC *auth.OrganizationUseCase, logger domain.Logger) *OrganizationHandler {
	return &OrganizationHandler{
		BaseHandler:    base,
		organizationUC: organizationUC,
		logger:         logger,
	}
}

// ListOrganizations handles GET /api/v1/organizations
func (h *OrganizationHandler) ListOrganizations(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	defer func() {
		h.LogRequest(r, http.StatusOK, time.Since(start))
	}()

	h.logger.Info("List organizations requested")

	// Parse query parameters
	limit := 10
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

	// Create filter
	filter := &domain.OrganizationFilter{
		Limit:  limit,
		Offset: offset,
	}

	// Call use case
	organizations, err := h.organizationUC.ListOrganizations(r.Context(), filter)
	if err != nil {
		h.logger.Error("Failed to list organizations", "error", err)
		h.RespondError(w, http.StatusInternalServerError, err)
		return
	}

	// Return response
	response := map[string]any{
		"organizations": organizations,
		"limit":         limit,
		"offset":        offset,
		"count":         len(organizations),
	}
	h.RespondJSON(w, http.StatusOK, response)
}

// GetOrganization handles GET /api/v1/organizations/{id}
func (h *OrganizationHandler) GetOrganization(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	defer func() {
		h.LogRequest(r, http.StatusOK, time.Since(start))
	}()

	h.logger.Info("Get organization requested")

	organizationID := chi.URLParam(r, "id")
	if organizationID == "" {
		h.RespondError(w, http.StatusBadRequest, fmt.Errorf("organization ID is required"))
		return
	}

	// Call use case
	organization, err := h.organizationUC.GetOrganization(r.Context(), organizationID)
	if err != nil {
		h.logger.Error("Failed to get organization", "organization_id", organizationID, "error", err)

		if err.Error() == "organization not found" {
			h.RespondError(w, http.StatusNotFound, err)
			return
		}

		h.RespondError(w, http.StatusInternalServerError, err)
		return
	}

	h.RespondJSON(w, http.StatusOK, organization)
}

// CreateOrganization handles POST /api/v1/organizations
func (h *OrganizationHandler) CreateOrganization(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	defer func() {
		h.LogRequest(r, http.StatusCreated, time.Since(start))
	}()

	h.logger.Info("Create organization requested")

	// Validate content type
	if err := h.ValidateContentType(r, "application/json"); err != nil {
		h.RespondError(w, http.StatusBadRequest, fmt.Errorf("content type must be application/json"))
		return
	}

	var req domain.CreateOrganizationRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		h.RespondError(w, http.StatusBadRequest, fmt.Errorf("invalid request body: %v", err))
		return
	}

	// Validate required fields
	if req.Name == "" {
		h.RespondError(w, http.StatusBadRequest, fmt.Errorf("organization name is required"))
		return
	}

	// Call use case
	organization, err := h.organizationUC.CreateOrganization(r.Context(), &req)
	if err != nil {
		h.logger.Error("Failed to create organization", "error", err)
		h.RespondError(w, http.StatusInternalServerError, err)
		return
	}

	h.logger.Info("Organization created", "organization_id", organization.ID)
	h.RespondJSON(w, http.StatusCreated, organization)
}

// UpdateOrganization handles PUT /api/v1/organizations/{id}
func (h *OrganizationHandler) UpdateOrganization(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	defer func() {
		h.LogRequest(r, http.StatusOK, time.Since(start))
	}()

	h.logger.Info("Update organization requested")

	organizationID := chi.URLParam(r, "id")
	if organizationID == "" {
		h.RespondError(w, http.StatusBadRequest, fmt.Errorf("organization ID is required"))
		return
	}

	// Validate content type
	if err := h.ValidateContentType(r, "application/json"); err != nil {
		h.RespondError(w, http.StatusBadRequest, fmt.Errorf("content type must be application/json"))
		return
	}

	var req domain.UpdateOrganizationRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		h.RespondError(w, http.StatusBadRequest, fmt.Errorf("invalid request body: %v", err))
		return
	}

	// Set ID from URL parameter
	req.ID = types.FromString(organizationID)

	// Call use case
	organization, err := h.organizationUC.UpdateOrganization(r.Context(), &req)
	if err != nil {
		h.logger.Error("Failed to update organization", "organization_id", organizationID, "error", err)

		if err.Error() == "organization not found" {
			h.RespondError(w, http.StatusNotFound, err)
			return
		}

		h.RespondError(w, http.StatusInternalServerError, err)
		return
	}

	h.logger.Info("Organization updated", "organization_id", organizationID)
	h.RespondJSON(w, http.StatusOK, organization)
}

// DeleteOrganization handles DELETE /api/v1/organizations/{id}
func (h *OrganizationHandler) DeleteOrganization(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	defer func() {
		h.LogRequest(r, http.StatusNoContent, time.Since(start))
	}()

	h.logger.Info("Delete organization requested")

	organizationID := chi.URLParam(r, "id")
	if organizationID == "" {
		h.RespondError(w, http.StatusBadRequest, fmt.Errorf("organization ID is required"))
		return
	}

	// Call use case
	err := h.organizationUC.DeleteOrganization(r.Context(), organizationID)
	if err != nil {
		h.logger.Error("Failed to delete organization", "organization_id", organizationID, "error", err)

		if err.Error() == "organization not found" {
			h.RespondError(w, http.StatusNotFound, err)
			return
		}

		h.RespondError(w, http.StatusInternalServerError, err)
		return
	}

	h.logger.Info("Organization deleted", "organization_id", organizationID)
	h.RespondJSON(w, http.StatusNoContent, nil)
}

// GetOrganizationUsers handles GET /api/v1/organizations/{id}/users
func (h *OrganizationHandler) GetOrganizationUsers(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	defer func() {
		h.LogRequest(r, http.StatusOK, time.Since(start))
	}()

	h.logger.Info("Get organization users requested")

	organizationID := chi.URLParam(r, "id")
	if organizationID == "" {
		h.RespondError(w, http.StatusBadRequest, fmt.Errorf("organization ID is required"))
		return
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

	// Call use case to get users by organization
	users, err := h.organizationUC.GetOrganizationUsers(r.Context(), organizationID)
	if err != nil {
		h.logger.Error("Failed to get organization users", "organization_id", organizationID, "error", err)
		h.RespondError(w, http.StatusInternalServerError, err)
		return
	}

	response := map[string]any{
		"organization_id": organizationID,
		"users":           users,
		"count":           len(users),
		"limit":           limit,
		"offset":          offset,
	}

	h.RespondJSON(w, http.StatusOK, response)
}
