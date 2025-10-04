package handlers

import (
	"encoding/json"
	"fmt"
	"net/http"
	"strconv"
	"time"

	"github.com/arx-os/arxos/internal/domain"
	"github.com/arx-os/arxos/internal/interfaces/http/models"
	"github.com/arx-os/arxos/internal/interfaces/http/types"
	"github.com/arx-os/arxos/internal/usecase"
	pkgmodels "github.com/arx-os/arxos/pkg/models"
)

// OrganizationHandler handles organization-related HTTP requests
type OrganizationHandler struct {
	BaseHandler
	organizationService *usecase.OrganizationUseCase
}

// NewOrganizationHandler creates a new organization handler
func NewOrganizationHandler(server *types.Server, organizationService *usecase.OrganizationUseCase) *OrganizationHandler {
	return &OrganizationHandler{
		BaseHandler:         nil, // Will be injected by container
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
	activeStr := r.URL.Query().Get("active")
	var active *bool
	if activeStr != "" {
		activeVal := activeStr == "true"
		active = &activeVal
	}

	planStr := r.URL.Query().Get("plan")
	var plan *string
	if planStr != "" {
		plan = &planStr
	}

	filter := &domain.OrganizationFilter{
		Plan:   plan,
		Active: active,
	}

	// Get organizations through the service
	organizations, err := h.organizationService.ListOrganizations(r.Context(), filter)
	if err != nil {
		h.RespondError(w, http.StatusInternalServerError, err)
		return
	}

	// Convert domain organizations to HTTP models
	var orgModels []*pkgmodels.Organization
	for _, org := range organizations {
		orgModels = append(orgModels, &pkgmodels.Organization{
			ID:          org.ID,
			Name:        org.Name,
			Description: org.Description,
			Plan:        pkgmodels.Plan(org.Plan),
			IsActive:    org.Active,
			CreatedAt:   org.CreatedAt,
			UpdatedAt:   org.UpdatedAt,
		})
	}

	// Convert to response format
	response := models.OrganizationListResponse{
		Organizations: orgModels,
		Total:         len(orgModels), // This should come from the service
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
		h.RespondError(w, http.StatusBadRequest, nil)
		return
	}

	// Get organization from service
	organization, err := h.organizationService.GetOrganization(r.Context(), orgID)
	if err != nil {
		h.RespondError(w, http.StatusNotFound, err)
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
		h.RespondError(w, http.StatusBadRequest, err)
		return
	}

	// Validate request
	if err := h.validateCreateOrganizationRequest(&req); err != nil {
		h.RespondError(w, http.StatusBadRequest, err)
		return
	}

	// Convert HTTP model to domain model
	domainReq := &domain.CreateOrganizationRequest{
		Name:        req.Name,
		Description: req.Description,
		Plan:        req.Plan,
	}

	// Create organization through service
	organization, err := h.organizationService.CreateOrganization(r.Context(), domainReq)
	if err != nil {
		h.RespondError(w, http.StatusInternalServerError, err)
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
		h.RespondError(w, http.StatusBadRequest, nil)
		return
	}

	// Parse request body
	var req models.UpdateOrganizationRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		h.RespondError(w, http.StatusBadRequest, err)
		return
	}

	// Convert HTTP model to domain model
	domainReq := &domain.UpdateOrganizationRequest{
		ID:          orgID,
		Name:        req.Name,
		Description: req.Description,
		Plan:        req.Plan,
		Active:      req.IsActive,
	}

	// Update organization through service
	organization, err := h.organizationService.UpdateOrganization(r.Context(), domainReq)
	if err != nil {
		h.RespondError(w, http.StatusInternalServerError, err)
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
		h.RespondError(w, http.StatusBadRequest, nil)
		return
	}

	// Delete organization through service
	if err := h.organizationService.DeleteOrganization(r.Context(), orgID); err != nil {
		h.RespondError(w, http.StatusInternalServerError, err)
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
		h.RespondError(w, http.StatusBadRequest, nil)
		return
	}

	// Parse pagination parameters
	limit, offset := h.parsePagination(r)

	// Get organization users through service
	users, err := h.organizationService.GetOrganizationUsers(r.Context(), orgID)
	if err != nil {
		h.RespondError(w, http.StatusInternalServerError, err)
		return
	}

	// Convert domain users to HTTP models
	var userModels []*pkgmodels.User
	for _, user := range users {
		userModels = append(userModels, &pkgmodels.User{
			ID:        user.ID,
			Email:     user.Email,
			FullName:  user.Name,
			Role:      user.Role,
			IsActive:  user.Active,
			CreatedAt: user.CreatedAt,
			UpdatedAt: user.UpdatedAt,
		})
	}

	// Convert to response format
	response := models.OrganizationUsersResponse{
		Users:  userModels,
		Total:  len(userModels), // This should come from the service
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
