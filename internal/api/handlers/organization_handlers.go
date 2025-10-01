package handlers

import (
	"net/http"
	"time"

	"github.com/arx-os/arxos/internal/api/models"
	"github.com/arx-os/arxos/internal/api/types"
	domainmodels "github.com/arx-os/arxos/pkg/models"
)

// OrganizationHandler handles organization-related HTTP requests
type OrganizationHandler struct {
	*BaseHandler
}

// NewOrganizationHandler creates a new organization handler
func NewOrganizationHandler(server *types.Server) *OrganizationHandler {
	return &OrganizationHandler{
		BaseHandler: NewBaseHandler(server),
	}
}

// HandleGetOrganizations handles GET /api/v1/organizations
func (h *OrganizationHandler) HandleGetOrganizations(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	defer func() {
		h.LogRequest(r, http.StatusOK, time.Since(start))
	}()

	// Check authentication
	user, ok := h.RequireAuth(w, r)
	if !ok {
		return
	}

	// Parse pagination
	limit, offset := h.ParsePagination(r)

	// Parse filters (placeholder for future use)
	_ = models.OrganizationFilter{
		Plan:   r.URL.Query().Get("plan"),
		Active: nil, // Could parse from query string if needed
	}

	// Get organizations through the service
	organizations, err := h.server.Services.Organization.ListOrganizations(r.Context(), user.ID)
	if err != nil {
		h.HandleError(w, r, err, "Failed to retrieve organizations")
		return
	}

	// Convert to response format
	orgResponses := make([]*models.OrganizationResponse, 0, len(organizations))
	for _, org := range organizations {
		if o, ok := org.(*domainmodels.Organization); ok {
			orgResponses = append(orgResponses, models.OrganizationToResponse(o))
		}
	}

	h.RespondPaginated(w, orgResponses, limit, offset, len(orgResponses))
}

// HandleGetOrganization handles GET /api/v1/organizations/{id}
func (h *OrganizationHandler) HandleGetOrganization(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	defer func() {
		h.LogRequest(r, http.StatusOK, time.Since(start))
	}()

	// Check authentication
	user, ok := h.RequireAuth(w, r)
	if !ok {
		return
	}

	// Parse organization ID
	orgID, err := h.ParseID(r, "id")
	if err != nil {
		h.RespondError(w, http.StatusBadRequest, "Invalid organization ID")
		return
	}

	// Get organization from service
	org, err := h.server.Services.Organization.GetOrganization(r.Context(), orgID)
	if err != nil {
		h.HandleError(w, r, err, "Organization not found")
		return
	}

	// Check if user has access to this organization
	if !h.server.HasOrgAccess(r.Context(), user, orgID) {
		h.RespondError(w, http.StatusForbidden, "Access denied")
		return
	}

	// Convert to response format
	if o, ok := org.(*domainmodels.Organization); ok {
		h.RespondJSON(w, http.StatusOK, models.OrganizationToResponse(o))
	} else {
		h.RespondError(w, http.StatusInternalServerError, "Invalid organization data")
	}
}

// HandleCreateOrganization handles POST /api/v1/organizations
func (h *OrganizationHandler) HandleCreateOrganization(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	defer func() {
		h.LogRequest(r, http.StatusCreated, time.Since(start))
	}()

	// Check authentication
	user, ok := h.RequireAuth(w, r)
	if !ok {
		return
	}

	// Parse request
	var req models.CreateOrganizationRequest
	if err := h.ParseJSON(r, &req); err != nil {
		h.RespondError(w, http.StatusBadRequest, "Invalid request body")
		return
	}

	// Validate request
	if err := h.ValidateRequest(req); err != nil {
		h.RespondError(w, http.StatusBadRequest, "Validation failed")
		return
	}

	// Create organization
	org, err := h.server.Services.Organization.CreateOrganization(r.Context(), req.Name, req.Description, user.ID)
	if err != nil {
		h.HandleError(w, r, err, "Failed to create organization")
		return
	}

	// Convert to response format
	if o, ok := org.(*domainmodels.Organization); ok {
		h.RespondJSON(w, http.StatusCreated, models.OrganizationToResponse(o))
	} else {
		h.RespondError(w, http.StatusInternalServerError, "Invalid organization data")
	}
}

// HandleUpdateOrganization handles PUT /api/v1/organizations/{id}
func (h *OrganizationHandler) HandleUpdateOrganization(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	defer func() {
		h.LogRequest(r, http.StatusOK, time.Since(start))
	}()

	// Check authentication
	user, ok := h.RequireAuth(w, r)
	if !ok {
		return
	}

	// Parse organization ID
	orgID, err := h.ParseID(r, "id")
	if err != nil {
		h.RespondError(w, http.StatusBadRequest, "Invalid organization ID")
		return
	}

	// Check if user has admin access to this organization
	role, err := h.server.Services.Organization.GetMemberRole(r.Context(), orgID, user.ID)
	if err != nil {
		h.HandleError(w, r, err, "Failed to check organization access")
		return
	}

	if role != "admin" && string(user.Role) != string(domainmodels.UserRoleAdmin) {
		h.RespondError(w, http.StatusForbidden, "Admin access required")
		return
	}

	// Parse request
	var req models.UpdateOrganizationRequest
	if err := h.ParseJSON(r, &req); err != nil {
		h.RespondError(w, http.StatusBadRequest, "Invalid request body")
		return
	}

	// Validate request
	if err := h.ValidateRequest(req); err != nil {
		h.RespondError(w, http.StatusBadRequest, "Validation failed")
		return
	}

	// Convert to updates map
	updates := make(map[string]interface{})
	if req.Name != nil && *req.Name != "" {
		updates["name"] = *req.Name
	}
	if req.Description != nil && *req.Description != "" {
		updates["description"] = *req.Description
	}
	if req.Website != nil && *req.Website != "" {
		updates["website"] = *req.Website
	}
	if req.Address != nil && *req.Address != "" {
		updates["address"] = *req.Address
	}
	if req.Phone != nil && *req.Phone != "" {
		updates["phone"] = *req.Phone
	}

	// Update organization
	org, err := h.server.Services.Organization.UpdateOrganization(r.Context(), orgID, updates)
	if err != nil {
		h.HandleError(w, r, err, "Failed to update organization")
		return
	}

	// Convert to response format
	if o, ok := org.(*domainmodels.Organization); ok {
		h.RespondJSON(w, http.StatusOK, models.OrganizationToResponse(o))
	} else {
		h.RespondError(w, http.StatusInternalServerError, "Invalid organization data")
	}
}

// HandleDeleteOrganization handles DELETE /api/v1/organizations/{id}
func (h *OrganizationHandler) HandleDeleteOrganization(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	defer func() {
		h.LogRequest(r, http.StatusOK, time.Since(start))
	}()

	// Check authentication
	user, ok := h.RequireAuth(w, r)
	if !ok {
		return
	}

	// Parse organization ID
	orgID, err := h.ParseID(r, "id")
	if err != nil {
		h.RespondError(w, http.StatusBadRequest, "Invalid organization ID")
		return
	}

	// Check if user has admin access to this organization
	role, err := h.server.Services.Organization.GetMemberRole(r.Context(), orgID, user.ID)
	if err != nil {
		h.HandleError(w, r, err, "Failed to check organization access")
		return
	}

	if role != "admin" && string(user.Role) != string(domainmodels.UserRoleAdmin) {
		h.RespondError(w, http.StatusForbidden, "Admin access required")
		return
	}

	// Delete organization
	if err := h.server.Services.Organization.DeleteOrganization(r.Context(), orgID); err != nil {
		h.HandleError(w, r, err, "Failed to delete organization")
		return
	}

	h.RespondSuccess(w, nil, "Organization deleted successfully")
}

// HandleGetMembers handles GET /api/v1/organizations/{id}/members
func (h *OrganizationHandler) HandleGetMembers(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	defer func() {
		h.LogRequest(r, http.StatusOK, time.Since(start))
	}()

	// Check authentication
	user, ok := h.RequireAuth(w, r)
	if !ok {
		return
	}

	// Parse organization ID
	orgID, err := h.ParseID(r, "id")
	if err != nil {
		h.RespondError(w, http.StatusBadRequest, "Invalid organization ID")
		return
	}

	// Check if user has access to this organization
	if !h.server.HasOrgAccess(r.Context(), user, orgID) {
		h.RespondError(w, http.StatusForbidden, "Access denied")
		return
	}

	// Get members
	members, err := h.server.Services.Organization.GetMembers(r.Context(), orgID)
	if err != nil {
		h.HandleError(w, r, err, "Failed to retrieve members")
		return
	}

	h.RespondJSON(w, http.StatusOK, members)
}

// HandleAddMember handles POST /api/v1/organizations/{id}/members
func (h *OrganizationHandler) HandleAddMember(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	defer func() {
		h.LogRequest(r, http.StatusCreated, time.Since(start))
	}()

	// Check authentication
	user, ok := h.RequireAuth(w, r)
	if !ok {
		return
	}

	// Parse organization ID
	orgID, err := h.ParseID(r, "id")
	if err != nil {
		h.RespondError(w, http.StatusBadRequest, "Invalid organization ID")
		return
	}

	// Check if user has admin access to this organization
	role, err := h.server.Services.Organization.GetMemberRole(r.Context(), orgID, user.ID)
	if err != nil {
		h.HandleError(w, r, err, "Failed to check organization access")
		return
	}

	if role != "admin" && string(user.Role) != string(domainmodels.UserRoleAdmin) {
		h.RespondError(w, http.StatusForbidden, "Admin access required")
		return
	}

	// Parse request
	var req models.AddMemberRequest
	if err := h.ParseJSON(r, &req); err != nil {
		h.RespondError(w, http.StatusBadRequest, "Invalid request body")
		return
	}

	// Validate request
	if err := h.ValidateRequest(req); err != nil {
		h.RespondError(w, http.StatusBadRequest, "Validation failed")
		return
	}

	// Add member
	if err := h.server.Services.Organization.AddMember(r.Context(), orgID, req.UserID, req.Role); err != nil {
		h.HandleError(w, r, err, "Failed to add member")
		return
	}

	h.RespondSuccess(w, nil, "Member added successfully")
}

// HandleUpdateMemberRole handles PUT /api/v1/organizations/{id}/members/{user_id}
func (h *OrganizationHandler) HandleUpdateMemberRole(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	defer func() {
		h.LogRequest(r, http.StatusOK, time.Since(start))
	}()

	// Check authentication
	user, ok := h.RequireAuth(w, r)
	if !ok {
		return
	}

	// Parse organization ID
	orgID, err := h.ParseID(r, "id")
	if err != nil {
		h.RespondError(w, http.StatusBadRequest, "Invalid organization ID")
		return
	}

	// Parse user ID
	userID, err := h.ParseID(r, "user_id")
	if err != nil {
		h.RespondError(w, http.StatusBadRequest, "Invalid user ID")
		return
	}

	// Check if user has admin access to this organization
	role, err := h.server.Services.Organization.GetMemberRole(r.Context(), orgID, user.ID)
	if err != nil {
		h.HandleError(w, r, err, "Failed to check organization access")
		return
	}

	if role != "admin" && string(user.Role) != string(domainmodels.UserRoleAdmin) {
		h.RespondError(w, http.StatusForbidden, "Admin access required")
		return
	}

	// Parse request
	var req models.UpdateMemberRoleRequest
	if err := h.ParseJSON(r, &req); err != nil {
		h.RespondError(w, http.StatusBadRequest, "Invalid request body")
		return
	}

	// Validate request
	if err := h.ValidateRequest(req); err != nil {
		h.RespondError(w, http.StatusBadRequest, "Validation failed")
		return
	}

	// Update member role
	if err := h.server.Services.Organization.UpdateMemberRole(r.Context(), orgID, userID, req.Role); err != nil {
		h.HandleError(w, r, err, "Failed to update member role")
		return
	}

	h.RespondSuccess(w, nil, "Member role updated successfully")
}

// HandleRemoveMember handles DELETE /api/v1/organizations/{id}/members/{user_id}
func (h *OrganizationHandler) HandleRemoveMember(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	defer func() {
		h.LogRequest(r, http.StatusOK, time.Since(start))
	}()

	// Check authentication
	user, ok := h.RequireAuth(w, r)
	if !ok {
		return
	}

	// Parse organization ID
	orgID, err := h.ParseID(r, "id")
	if err != nil {
		h.RespondError(w, http.StatusBadRequest, "Invalid organization ID")
		return
	}

	// Parse user ID
	userID, err := h.ParseID(r, "user_id")
	if err != nil {
		h.RespondError(w, http.StatusBadRequest, "Invalid user ID")
		return
	}

	// Check if user has admin access to this organization
	role, err := h.server.Services.Organization.GetMemberRole(r.Context(), orgID, user.ID)
	if err != nil {
		h.HandleError(w, r, err, "Failed to check organization access")
		return
	}

	if role != "admin" && string(user.Role) != string(domainmodels.UserRoleAdmin) {
		h.RespondError(w, http.StatusForbidden, "Admin access required")
		return
	}

	// Remove member
	if err := h.server.Services.Organization.RemoveMember(r.Context(), orgID, userID); err != nil {
		h.HandleError(w, r, err, "Failed to remove member")
		return
	}

	h.RespondSuccess(w, nil, "Member removed successfully")
}

// HandleCreateInvitation handles POST /api/v1/organizations/{id}/invitations
func (h *OrganizationHandler) HandleCreateInvitation(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	defer func() {
		h.LogRequest(r, http.StatusCreated, time.Since(start))
	}()

	// Check authentication
	user, ok := h.RequireAuth(w, r)
	if !ok {
		return
	}

	// Parse organization ID
	orgID, err := h.ParseID(r, "id")
	if err != nil {
		h.RespondError(w, http.StatusBadRequest, "Invalid organization ID")
		return
	}

	// Check if user has admin access to this organization
	role, err := h.server.Services.Organization.GetMemberRole(r.Context(), orgID, user.ID)
	if err != nil {
		h.HandleError(w, r, err, "Failed to check organization access")
		return
	}

	if role != "admin" && string(user.Role) != string(domainmodels.UserRoleAdmin) {
		h.RespondError(w, http.StatusForbidden, "Admin access required")
		return
	}

	// Parse request
	var req models.CreateInvitationRequest
	if err := h.ParseJSON(r, &req); err != nil {
		h.RespondError(w, http.StatusBadRequest, "Invalid request body")
		return
	}

	// Validate request
	if err := h.ValidateRequest(req); err != nil {
		h.RespondError(w, http.StatusBadRequest, "Validation failed")
		return
	}

	// Create invitation
	invitation, err := h.server.Services.Organization.CreateInvitation(r.Context(), orgID, req.Email, req.Role)
	if err != nil {
		h.HandleError(w, r, err, "Failed to create invitation")
		return
	}

	h.RespondJSON(w, http.StatusCreated, invitation)
}

// HandleGetInvitations handles GET /api/v1/organizations/{id}/invitations
func (h *OrganizationHandler) HandleGetInvitations(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	defer func() {
		h.LogRequest(r, http.StatusOK, time.Since(start))
	}()

	// Check authentication
	user, ok := h.RequireAuth(w, r)
	if !ok {
		return
	}

	// Parse organization ID
	orgID, err := h.ParseID(r, "id")
	if err != nil {
		h.RespondError(w, http.StatusBadRequest, "Invalid organization ID")
		return
	}

	// Check if user has admin access to this organization
	role, err := h.server.Services.Organization.GetMemberRole(r.Context(), orgID, user.ID)
	if err != nil {
		h.HandleError(w, r, err, "Failed to check organization access")
		return
	}

	if role != "admin" && string(user.Role) != string(domainmodels.UserRoleAdmin) {
		h.RespondError(w, http.StatusForbidden, "Admin access required")
		return
	}

	// Get pending invitations
	invitations, err := h.server.Services.Organization.ListPendingInvitations(r.Context(), orgID)
	if err != nil {
		h.HandleError(w, r, err, "Failed to retrieve invitations")
		return
	}

	h.RespondJSON(w, http.StatusOK, invitations)
}

// HandleAcceptInvitation handles POST /api/v1/invitations/accept
func (h *OrganizationHandler) HandleAcceptInvitation(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	defer func() {
		h.LogRequest(r, http.StatusOK, time.Since(start))
	}()

	// Check authentication
	_, ok := h.RequireAuth(w, r)
	if !ok {
		return
	}

	// Parse request
	var req models.AcceptInvitationRequest
	if err := h.ParseJSON(r, &req); err != nil {
		h.RespondError(w, http.StatusBadRequest, "Invalid request body")
		return
	}

	// Validate request
	if err := h.ValidateRequest(req); err != nil {
		h.RespondError(w, http.StatusBadRequest, "Validation failed")
		return
	}

	// Accept invitation
	if err := h.server.Services.Organization.AcceptInvitation(r.Context(), req.Token); err != nil {
		h.HandleError(w, r, err, "Failed to accept invitation")
		return
	}

	h.RespondSuccess(w, nil, "Invitation accepted successfully")
}

// HandleRevokeInvitation handles DELETE /api/v1/organizations/{id}/invitations/{invitation_id}
func (h *OrganizationHandler) HandleRevokeInvitation(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	defer func() {
		h.LogRequest(r, http.StatusOK, time.Since(start))
	}()

	// Check authentication
	user, ok := h.RequireAuth(w, r)
	if !ok {
		return
	}

	// Parse organization ID
	orgID, err := h.ParseID(r, "id")
	if err != nil {
		h.RespondError(w, http.StatusBadRequest, "Invalid organization ID")
		return
	}

	// Parse invitation ID
	invitationID, err := h.ParseID(r, "invitation_id")
	if err != nil {
		h.RespondError(w, http.StatusBadRequest, "Invalid invitation ID")
		return
	}

	// Check if user has admin access to this organization
	role, err := h.server.Services.Organization.GetMemberRole(r.Context(), orgID, user.ID)
	if err != nil {
		h.HandleError(w, r, err, "Failed to check organization access")
		return
	}

	if role != "admin" && string(user.Role) != string(domainmodels.UserRoleAdmin) {
		h.RespondError(w, http.StatusForbidden, "Admin access required")
		return
	}

	// Revoke invitation
	if err := h.server.Services.Organization.RevokeInvitation(r.Context(), orgID, invitationID); err != nil {
		h.HandleError(w, r, err, "Failed to revoke invitation")
		return
	}

	h.RespondSuccess(w, nil, "Invitation revoked successfully")
}

// Legacy handler functions for backward compatibility
func HandleGetOrganizations(s *types.Server) http.HandlerFunc {
	handler := NewOrganizationHandler(s)
	return handler.HandleGetOrganizations
}

func HandleGetOrganization(s *types.Server) http.HandlerFunc {
	handler := NewOrganizationHandler(s)
	return handler.HandleGetOrganization
}

func HandleCreateOrganization(s *types.Server) http.HandlerFunc {
	handler := NewOrganizationHandler(s)
	return handler.HandleCreateOrganization
}

func HandleUpdateOrganization(s *types.Server) http.HandlerFunc {
	handler := NewOrganizationHandler(s)
	return handler.HandleUpdateOrganization
}

func HandleDeleteOrganization(s *types.Server) http.HandlerFunc {
	handler := NewOrganizationHandler(s)
	return handler.HandleDeleteOrganization
}

func HandleGetMembers(s *types.Server) http.HandlerFunc {
	handler := NewOrganizationHandler(s)
	return handler.HandleGetMembers
}

func HandleAddMember(s *types.Server) http.HandlerFunc {
	handler := NewOrganizationHandler(s)
	return handler.HandleAddMember
}

func HandleUpdateMemberRole(s *types.Server) http.HandlerFunc {
	handler := NewOrganizationHandler(s)
	return handler.HandleUpdateMemberRole
}

func HandleRemoveMember(s *types.Server) http.HandlerFunc {
	handler := NewOrganizationHandler(s)
	return handler.HandleRemoveMember
}

func HandleCreateInvitation(s *types.Server) http.HandlerFunc {
	handler := NewOrganizationHandler(s)
	return handler.HandleCreateInvitation
}

func HandleGetInvitations(s *types.Server) http.HandlerFunc {
	handler := NewOrganizationHandler(s)
	return handler.HandleGetInvitations
}

func HandleAcceptInvitation(s *types.Server) http.HandlerFunc {
	handler := NewOrganizationHandler(s)
	return handler.HandleAcceptInvitation
}

func HandleRevokeInvitation(s *types.Server) http.HandlerFunc {
	handler := NewOrganizationHandler(s)
	return handler.HandleRevokeInvitation
}
