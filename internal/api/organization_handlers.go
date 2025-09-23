package api

import (
	"encoding/json"
	"net/http"
	"strconv"
	"strings"

	"github.com/arx-os/arxos/pkg/models"
	"github.com/gorilla/mux"
)

// handleGetOrganizations handles GET /api/v1/organizations
func (s *Server) handleGetOrganizations(w http.ResponseWriter, r *http.Request) {
	// Check authentication
	user, err := s.getCurrentUser(r)
	if err != nil {
		s.respondError(w, http.StatusUnauthorized, "Authentication required")
		return
	}

	// Parse query parameters
	limit := 100
	offset := 0

	if l := r.URL.Query().Get("limit"); l != "" {
		if parsed, err := strconv.Atoi(l); err == nil && parsed > 0 && parsed <= 1000 {
			limit = parsed
		}
	}

	if o := r.URL.Query().Get("offset"); o != "" {
		if parsed, err := strconv.Atoi(o); err == nil && parsed >= 0 {
			offset = parsed
		}
	}

	// Get organizations through the service
	organizations, err := s.services.Organization.ListOrganizations(r.Context(), user.ID)

	if err != nil {
		s.respondError(w, http.StatusInternalServerError, "Failed to retrieve organizations")
		return
	}

	s.respondJSON(w, http.StatusOK, map[string]interface{}{
		"organizations": organizations,
		"limit":         limit,
		"offset":        offset,
		"total":         len(organizations),
	})
}

// handleGetOrganization handles GET /api/v1/organizations/{id}
func (s *Server) handleGetOrganization(w http.ResponseWriter, r *http.Request) {
	// Check authentication
	user, err := s.getCurrentUser(r)
	if err != nil {
		s.respondError(w, http.StatusUnauthorized, "Authentication required")
		return
	}

	// Get organization ID from URL
	vars := mux.Vars(r)
	orgID := vars["id"]

	// Get organization from service
	org, err := s.services.Organization.GetOrganization(r.Context(), orgID)
	if err != nil {
		s.respondError(w, http.StatusNotFound, "Organization not found")
		return
	}

	// Check if user has access to this organization
	if !s.hasOrgAccess(r.Context(), user, org.ID) {
		s.respondError(w, http.StatusForbidden, "Access denied")
		return
	}

	s.respondJSON(w, http.StatusOK, org)
}

// handleCreateOrganization handles POST /api/v1/organizations
func (s *Server) handleCreateOrganization(w http.ResponseWriter, r *http.Request) {
	// Check authentication
	user, err := s.getCurrentUser(r)
	if err != nil {
		s.respondError(w, http.StatusUnauthorized, "Authentication required")
		return
	}

	var req models.OrganizationCreateRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		s.respondError(w, http.StatusBadRequest, "Invalid request body")
		return
	}

	// Validate required fields
	if req.Name == "" || req.Slug == "" {
		s.respondError(w, http.StatusBadRequest, "Name and slug are required")
		return
	}

	// Create organization through service
	if s.services.Organization == nil {
		s.respondError(w, http.StatusNotImplemented, "Organization service not configured")
		return
	}

	// Convert request to Organization model
	org := &models.Organization{
		Name:        req.Name,
		Slug:        req.Slug,
		Description: req.Description,
		Website:     req.Website,
		LogoURL:     req.LogoURL,
		Address:     req.Address,
		City:        req.City,
		State:       req.State,
		Country:     req.Country,
		PostalCode:  req.PostalCode,
		Plan:        models.PlanFree, // Default to free plan
		Status:      "active",
		IsActive:    true,
	}

	err = s.services.Organization.CreateOrganization(r.Context(), org, user.ID)
	if err != nil {
		if strings.Contains(err.Error(), "already exists") {
			s.respondError(w, http.StatusConflict, "Organization slug already exists")
		} else {
			s.respondError(w, http.StatusInternalServerError, "Failed to create organization")
		}
		return
	}

	s.respondJSON(w, http.StatusCreated, org)
}

// handleUpdateOrganization handles PUT /api/v1/organizations/{id}
func (s *Server) handleUpdateOrganization(w http.ResponseWriter, r *http.Request) {
	// Check authentication
	user, err := s.getCurrentUser(r)
	if err != nil {
		s.respondError(w, http.StatusUnauthorized, "Authentication required")
		return
	}

	// Get organization ID from URL
	vars := mux.Vars(r)
	orgID := vars["id"]

	// Check if user has admin access to this organization
	if user.Role != string(models.UserRoleAdmin) {
		role, err := s.services.Organization.GetMemberRole(r.Context(), orgID, user.ID)
		if err != nil || role == nil || (*role != models.RoleOwner && *role != models.RoleAdmin) {
			s.respondError(w, http.StatusForbidden, "Admin access required")
			return
		}
	}

	var req models.OrganizationUpdateRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		s.respondError(w, http.StatusBadRequest, "Invalid request body")
		return
	}

	// Update organization through service
	if s.services.Organization == nil {
		s.respondError(w, http.StatusNotImplemented, "Organization service not configured")
		return
	}

	// Convert update request to Organization model
	org, err := s.services.Organization.GetOrganization(r.Context(), orgID)
	if err != nil {
		s.respondError(w, http.StatusNotFound, "Organization not found")
		return
	}

	// Apply updates
	if req.Name != "" {
		org.Name = req.Name
	}
	if req.Description != "" {
		org.Description = req.Description
	}
	if req.Website != "" {
		org.Website = req.Website
	}
	if req.LogoURL != "" {
		org.LogoURL = req.LogoURL
	}

	err = s.services.Organization.UpdateOrganization(r.Context(), org)
	if err != nil {
		s.respondError(w, http.StatusInternalServerError, "Failed to update organization")
		return
	}

	s.respondJSON(w, http.StatusOK, org)
}

// handleDeleteOrganization handles DELETE /api/v1/organizations/{id}
func (s *Server) handleDeleteOrganization(w http.ResponseWriter, r *http.Request) {
	// Check authentication
	user, err := s.getCurrentUser(r)
	if err != nil {
		s.respondError(w, http.StatusUnauthorized, "Authentication required")
		return
	}

	// Get organization ID from URL
	vars := mux.Vars(r)
	orgID := vars["id"]

	// Check if user has owner access to this organization
	if user.Role != string(models.UserRoleAdmin) {
		role, err := s.services.Organization.GetMemberRole(r.Context(), orgID, user.ID)
		if err != nil || role == nil || *role != models.RoleOwner {
			s.respondError(w, http.StatusForbidden, "Owner access required")
			return
		}
	}

	// Delete organization
	err = s.services.Organization.DeleteOrganization(r.Context(), orgID)
	if err != nil {
		if strings.Contains(err.Error(), "not found") {
			s.respondError(w, http.StatusNotFound, "Organization not found")
		} else {
			s.respondError(w, http.StatusInternalServerError, "Failed to delete organization")
		}
		return
	}

	s.respondJSON(w, http.StatusOK, map[string]interface{}{
		"success": true,
		"message": "Organization deleted successfully",
	})
}

// handleGetOrganizationMembers handles GET /api/v1/organizations/{id}/members
func (s *Server) handleGetOrganizationMembers(w http.ResponseWriter, r *http.Request) {
	// Check authentication
	user, err := s.getCurrentUser(r)
	if err != nil {
		s.respondError(w, http.StatusUnauthorized, "Authentication required")
		return
	}

	// Get organization ID from URL
	vars := mux.Vars(r)
	orgID := vars["id"]

	// Check if user has access to this organization
	if !s.hasOrgAccess(r.Context(), user, orgID) {
		s.respondError(w, http.StatusForbidden, "Access denied")
		return
	}

	// Get members from database
	members, err := s.services.Organization.GetMembers(r.Context(), orgID)
	if err != nil {
		s.respondError(w, http.StatusInternalServerError, "Failed to retrieve members")
		return
	}

	s.respondJSON(w, http.StatusOK, map[string]interface{}{
		"members": members,
		"total":   len(members),
	})
}

// handleAddOrganizationMember handles POST /api/v1/organizations/{id}/members
func (s *Server) handleAddOrganizationMember(w http.ResponseWriter, r *http.Request) {
	// Check authentication
	user, err := s.getCurrentUser(r)
	if err != nil {
		s.respondError(w, http.StatusUnauthorized, "Authentication required")
		return
	}

	// Get organization ID from URL
	vars := mux.Vars(r)
	orgID := vars["id"]

	// Check if user has admin access to this organization
	if user.Role != string(models.UserRoleAdmin) {
		role, err := s.services.Organization.GetMemberRole(r.Context(), orgID, user.ID)
		if err != nil || role == nil || (*role != models.RoleOwner && *role != models.RoleAdmin) {
			s.respondError(w, http.StatusForbidden, "Admin access required")
			return
		}
	}

	var req struct {
		UserID string `json:"user_id"`
		Role   string `json:"role"`
	}

	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		s.respondError(w, http.StatusBadRequest, "Invalid request body")
		return
	}

	// Validate required fields
	if req.UserID == "" || req.Role == "" {
		s.respondError(w, http.StatusBadRequest, "User ID and role are required")
		return
	}

	// Add member to organization
	err = s.services.Organization.AddMember(r.Context(), orgID, req.UserID, models.Role(req.Role))
	if err != nil {
		if strings.Contains(err.Error(), "already") {
			s.respondError(w, http.StatusConflict, "User is already a member")
		} else {
			s.respondError(w, http.StatusInternalServerError, "Failed to add member")
		}
		return
	}

	s.respondJSON(w, http.StatusCreated, map[string]interface{}{
		"success": true,
		"message": "Member added successfully",
	})
}

// handleUpdateOrganizationMember handles PUT /api/v1/organizations/{id}/members/{user_id}
func (s *Server) handleUpdateOrganizationMember(w http.ResponseWriter, r *http.Request) {
	// Check authentication
	user, err := s.getCurrentUser(r)
	if err != nil {
		s.respondError(w, http.StatusUnauthorized, "Authentication required")
		return
	}

	// Get organization ID and user ID from URL
	vars := mux.Vars(r)
	orgID := vars["id"]
	memberUserID := vars["user_id"]

	// Check if user has admin access to this organization
	if user.Role != string(models.UserRoleAdmin) {
		role, err := s.services.Organization.GetMemberRole(r.Context(), orgID, user.ID)
		if err != nil || role == nil || (*role != models.RoleOwner && *role != models.RoleAdmin) {
			s.respondError(w, http.StatusForbidden, "Admin access required")
			return
		}

		// Prevent non-owners from changing owner roles
		targetRole, err := s.services.Organization.GetMemberRole(r.Context(), orgID, memberUserID)
		if err == nil && targetRole != nil && *targetRole == models.RoleOwner && *role != models.RoleOwner {
			s.respondError(w, http.StatusForbidden, "Only owners can modify owner roles")
			return
		}
	}

	var req models.OrganizationMemberUpdateRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		s.respondError(w, http.StatusBadRequest, "Invalid request body")
		return
	}

	// Update member role
	err = s.services.Organization.UpdateMemberRole(r.Context(), orgID, memberUserID, models.Role(req.Role))
	if err != nil {
		if strings.Contains(err.Error(), "not found") {
			s.respondError(w, http.StatusNotFound, "Member not found")
		} else {
			s.respondError(w, http.StatusInternalServerError, "Failed to update member")
		}
		return
	}

	s.respondJSON(w, http.StatusOK, map[string]interface{}{
		"success": true,
		"message": "Member updated successfully",
	})
}

// handleRemoveOrganizationMember handles DELETE /api/v1/organizations/{id}/members/{user_id}
func (s *Server) handleRemoveOrganizationMember(w http.ResponseWriter, r *http.Request) {
	// Check authentication
	user, err := s.getCurrentUser(r)
	if err != nil {
		s.respondError(w, http.StatusUnauthorized, "Authentication required")
		return
	}

	// Get organization ID and user ID from URL
	vars := mux.Vars(r)
	orgID := vars["id"]
	memberUserID := vars["user_id"]

	// Check if user has admin access to this organization
	if user.Role != string(models.UserRoleAdmin) {
		role, err := s.services.Organization.GetMemberRole(r.Context(), orgID, user.ID)
		if err != nil || role == nil || (*role != models.RoleOwner && *role != models.RoleAdmin) {
			// Allow users to remove themselves
			if memberUserID != user.ID {
				s.respondError(w, http.StatusForbidden, "Admin access required")
				return
			}
		}
	}

	// Remove member from organization
	err = s.services.Organization.RemoveMember(r.Context(), orgID, memberUserID)
	if err != nil {
		if strings.Contains(err.Error(), "not found") {
			s.respondError(w, http.StatusNotFound, "Member not found")
		} else {
			s.respondError(w, http.StatusInternalServerError, "Failed to remove member")
		}
		return
	}

	s.respondJSON(w, http.StatusOK, map[string]interface{}{
		"success": true,
		"message": "Member removed successfully",
	})
}

// handleCreateOrganizationInvitation handles POST /api/v1/organizations/{id}/invitations
func (s *Server) handleCreateOrganizationInvitation(w http.ResponseWriter, r *http.Request) {
	// Check authentication
	user, err := s.getCurrentUser(r)
	if err != nil {
		s.respondError(w, http.StatusUnauthorized, "Authentication required")
		return
	}

	// Get organization ID from URL
	vars := mux.Vars(r)
	orgID := vars["id"]

	// Check if user has admin access to this organization
	if user.Role != string(models.UserRoleAdmin) {
		role, err := s.services.Organization.GetMemberRole(r.Context(), orgID, user.ID)
		if err != nil || role == nil || (*role != models.RoleOwner && *role != models.RoleAdmin) {
			s.respondError(w, http.StatusForbidden, "Admin access required")
			return
		}
	}

	var req models.OrganizationInviteRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		s.respondError(w, http.StatusBadRequest, "Invalid request body")
		return
	}

	// Validate required fields
	if req.Email == "" || req.Role == "" {
		s.respondError(w, http.StatusBadRequest, "Email and role are required")
		return
	}

	// Create invitation through service
	if s.services.Organization == nil {
		s.respondError(w, http.StatusNotImplemented, "Organization service not configured")
		return
	}

	invitation, err := s.services.Organization.CreateInvitation(r.Context(), orgID, req.Email, models.Role(req.Role), user.ID)
	if err != nil {
		s.respondError(w, http.StatusInternalServerError, "Failed to create invitation")
		return
	}

	s.respondJSON(w, http.StatusCreated, invitation)
}

// handleGetOrganizationInvitations handles GET /api/v1/organizations/{id}/invitations
func (s *Server) handleGetOrganizationInvitations(w http.ResponseWriter, r *http.Request) {
	// Check authentication
	user, err := s.getCurrentUser(r)
	if err != nil {
		s.respondError(w, http.StatusUnauthorized, "Authentication required")
		return
	}

	// Get organization ID from URL
	vars := mux.Vars(r)
	orgID := vars["id"]

	// Check if user has access to this organization
	if user.Role != string(models.UserRoleAdmin) {
		role, err := s.services.Organization.GetMemberRole(r.Context(), orgID, user.ID)
		if err != nil || role == nil || (*role != models.RoleOwner && *role != models.RoleAdmin) {
			s.respondError(w, http.StatusForbidden, "Admin access required")
			return
		}
	}

	// Get invitations from database
	invitations, err := s.services.Organization.ListPendingInvitations(r.Context(), orgID)
	if err != nil {
		s.respondError(w, http.StatusInternalServerError, "Failed to retrieve invitations")
		return
	}

	s.respondJSON(w, http.StatusOK, map[string]interface{}{
		"invitations": invitations,
		"total":       len(invitations),
	})
}

// handleAcceptOrganizationInvitation handles POST /api/v1/invitations/accept
func (s *Server) handleAcceptOrganizationInvitation(w http.ResponseWriter, r *http.Request) {
	// Check authentication
	user, err := s.getCurrentUser(r)
	if err != nil {
		s.respondError(w, http.StatusUnauthorized, "Authentication required")
		return
	}

	var req struct {
		Token string `json:"token"`
	}

	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		s.respondError(w, http.StatusBadRequest, "Invalid request body")
		return
	}

	// Validate required fields
	if req.Token == "" {
		s.respondError(w, http.StatusBadRequest, "Token is required")
		return
	}

	// Accept invitation
	err = s.services.Organization.AcceptInvitation(r.Context(), req.Token, user.ID)
	if err != nil {
		if strings.Contains(err.Error(), "not found") || strings.Contains(err.Error(), "expired") {
			s.respondError(w, http.StatusBadRequest, "Invalid or expired invitation")
		} else if strings.Contains(err.Error(), "already") {
			s.respondError(w, http.StatusConflict, "Already a member of this organization")
		} else {
			s.respondError(w, http.StatusInternalServerError, "Failed to accept invitation")
		}
		return
	}

	s.respondJSON(w, http.StatusOK, map[string]interface{}{
		"success": true,
		"message": "Invitation accepted successfully",
	})
}

// handleRevokeOrganizationInvitation handles DELETE /api/v1/organizations/{id}/invitations/{invitation_id}
func (s *Server) handleRevokeOrganizationInvitation(w http.ResponseWriter, r *http.Request) {
	// Check authentication
	user, err := s.getCurrentUser(r)
	if err != nil {
		s.respondError(w, http.StatusUnauthorized, "Authentication required")
		return
	}

	// Get organization ID and invitation ID from URL
	vars := mux.Vars(r)
	orgID := vars["id"]
	invitationID := vars["invitation_id"]

	// Check if user has admin access to this organization
	if user.Role != string(models.UserRoleAdmin) {
		role, err := s.services.Organization.GetMemberRole(r.Context(), orgID, user.ID)
		if err != nil || role == nil || (*role != models.RoleOwner && *role != models.RoleAdmin) {
			s.respondError(w, http.StatusForbidden, "Admin access required")
			return
		}
	}

	// Revoke invitation
	err = s.services.Organization.RevokeInvitation(r.Context(), invitationID)
	if err != nil {
		if strings.Contains(err.Error(), "not found") {
			s.respondError(w, http.StatusNotFound, "Invitation not found")
		} else if strings.Contains(err.Error(), "already accepted") {
			s.respondError(w, http.StatusBadRequest, "Cannot revoke accepted invitation")
		} else {
			s.respondError(w, http.StatusInternalServerError, "Failed to revoke invitation")
		}
		return
	}

	s.respondJSON(w, http.StatusOK, map[string]interface{}{
		"success": true,
		"message": "Invitation revoked successfully",
	})
}
