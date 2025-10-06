package models

import (
	"time"

	"github.com/arx-os/arxos/pkg/models"
)

// OrganizationFilter represents filters for organization queries
type OrganizationFilter struct {
	Plan   string `json:"plan"`
	Active *bool  `json:"active"`
}

// OrganizationListResponse represents the response for listing organizations
type OrganizationListResponse struct {
	Organizations []*models.Organization `json:"organizations"`
	Total         int                    `json:"total"`
	Limit         int                    `json:"limit"`
	Offset        int                    `json:"offset"`
}

// CreateOrganizationRequest represents the request to create an organization
type CreateOrganizationRequest struct {
	Name        string         `json:"name" validate:"required"`
	Description string         `json:"description"`
	Plan        string         `json:"plan" validate:"required,oneof=free pro enterprise"`
	IsActive    bool           `json:"is_active"`
	Metadata    map[string]any `json:"metadata"`
}

// UpdateOrganizationRequest represents the request to update an organization
type UpdateOrganizationRequest struct {
	Name        *string        `json:"name,omitempty"`
	Description *string        `json:"description,omitempty"`
	Plan        *string        `json:"plan,omitempty"`
	IsActive    *bool          `json:"is_active,omitempty"`
	Metadata    map[string]any `json:"metadata,omitempty"`
}

// OrganizationResponse represents an organization in API responses
type OrganizationResponse struct {
	ID          string         `json:"id"`
	Name        string         `json:"name"`
	Description string         `json:"description"`
	Plan        string         `json:"plan"`
	IsActive    bool           `json:"is_active"`
	Metadata    map[string]any `json:"metadata"`
	CreatedAt   time.Time      `json:"created_at"`
	UpdatedAt   time.Time      `json:"updated_at"`
}

// OrganizationUsersResponse represents the response for listing organization users
type OrganizationUsersResponse struct {
	Users  []*models.User `json:"users"`
	Total  int            `json:"total"`
	Limit  int            `json:"limit"`
	Offset int            `json:"offset"`
}

// AddUserToOrganizationRequest represents the request to add a user to an organization
type AddUserToOrganizationRequest struct {
	UserID string `json:"user_id" validate:"required"`
	Role   string `json:"role" validate:"required"`
}

// OrganizationStats represents organization statistics
type OrganizationStats struct {
	TotalOrganizations          int `json:"total_organizations"`
	ActiveOrganizations         int `json:"active_organizations"`
	FreePlanOrganizations       int `json:"free_plan_organizations"`
	ProPlanOrganizations        int `json:"pro_plan_organizations"`
	EnterprisePlanOrganizations int `json:"enterprise_plan_organizations"`
}

// OrganizationUsage represents organization usage statistics
type OrganizationUsage struct {
	OrganizationID string    `json:"organization_id"`
	Plan           string    `json:"plan"`
	UsersCount     int       `json:"users_count"`
	BuildingsCount int       `json:"buildings_count"`
	StorageUsed    int64     `json:"storage_used"`
	APIRequests    int64     `json:"api_requests"`
	LastUpdated    time.Time `json:"last_updated"`
}
