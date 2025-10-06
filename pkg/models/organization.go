package models

import (
	"time"
)

// Plan represents subscription plan levels
type Plan string

const (
	PlanFree         Plan = "free"
	PlanStarter      Plan = "starter"
	PlanProfessional Plan = "professional"
	PlanEnterprise   Plan = "enterprise"
)

// Organization represents a company or team using the system
type Organization struct {
	ID                    string         `json:"id"`
	Name                  string         `json:"name"`
	Slug                  string         `json:"slug"`
	Description           string         `json:"description,omitempty"`
	Website               string         `json:"website,omitempty"`
	LogoURL               string         `json:"logo_url,omitempty"`
	Address               string         `json:"address,omitempty"`
	City                  string         `json:"city,omitempty"`
	State                 string         `json:"state,omitempty"`
	Country               string         `json:"country,omitempty"`
	PostalCode            string         `json:"postal_code,omitempty"`
	Phone                 string         `json:"phone,omitempty"`
	Email                 string         `json:"email,omitempty"`
	Plan                  Plan           `json:"plan"`
	Status                string         `json:"status"`
	MaxUsers              int            `json:"max_users"`
	MaxBuildings          int            `json:"max_buildings"`
	Settings              map[string]any `json:"settings,omitempty"`
	Metadata              map[string]any `json:"metadata,omitempty"`
	IsActive              bool           `json:"is_active"`
	SubscriptionTier      string         `json:"subscription_tier"`
	SubscriptionExpiresAt *time.Time     `json:"subscription_expires_at,omitempty"`
	CreatedAt             time.Time      `json:"created_at"`
	UpdatedAt             time.Time      `json:"updated_at"`
}

// OrganizationMember represents a user's membership in an organization
type OrganizationMember struct {
	ID             string         `json:"id"`
	OrganizationID string         `json:"organization_id"`
	UserID         string         `json:"user_id"`
	Role           string         `json:"role"`
	Permissions    map[string]any `json:"permissions,omitempty"`
	JoinedAt       time.Time      `json:"joined_at"`
	InvitedBy      string         `json:"invited_by,omitempty"`
	User           *User          `json:"user,omitempty"`         // Populated when needed
	Organization   *Organization  `json:"organization,omitempty"` // Populated when needed
}

// OrganizationInvitation represents an invitation to join an organization
type OrganizationInvitation struct {
	ID             string        `json:"id"`
	OrganizationID string        `json:"organization_id"`
	Email          string        `json:"email"`
	Role           string        `json:"role"`
	Token          string        `json:"-"` // Never expose in JSON
	InvitedBy      string        `json:"invited_by"`
	AcceptedAt     *time.Time    `json:"accepted_at,omitempty"`
	ExpiresAt      time.Time     `json:"expires_at"`
	CreatedAt      time.Time     `json:"created_at"`
	Organization   *Organization `json:"organization,omitempty"`    // Populated when needed
	InvitedByUser  *User         `json:"invited_by_user,omitempty"` // Populated when needed
}

// OrganizationCreateRequest represents an organization creation request
type OrganizationCreateRequest struct {
	Name        string         `json:"name" validate:"required,min=2,max=100"`
	Slug        string         `json:"slug" validate:"required,min=2,max=50,alphanum"`
	Description string         `json:"description,omitempty"`
	Website     string         `json:"website,omitempty" validate:"omitempty,url"`
	LogoURL     string         `json:"logo_url,omitempty" validate:"omitempty,url"`
	Address     string         `json:"address,omitempty"`
	City        string         `json:"city,omitempty"`
	State       string         `json:"state,omitempty"`
	Country     string         `json:"country,omitempty"`
	PostalCode  string         `json:"postal_code,omitempty"`
	Phone       string         `json:"phone,omitempty"`
	Email       string         `json:"email,omitempty" validate:"omitempty,email"`
	Settings    map[string]any `json:"settings,omitempty"`
}

// OrganizationUpdateRequest represents an organization update request
type OrganizationUpdateRequest struct {
	Name        string         `json:"name,omitempty" validate:"omitempty,min=2,max=100"`
	Description string         `json:"description,omitempty"`
	Website     string         `json:"website,omitempty" validate:"omitempty,url"`
	LogoURL     string         `json:"logo_url,omitempty" validate:"omitempty,url"`
	Address     string         `json:"address,omitempty"`
	City        string         `json:"city,omitempty"`
	State       string         `json:"state,omitempty"`
	Country     string         `json:"country,omitempty"`
	PostalCode  string         `json:"postal_code,omitempty"`
	Phone       string         `json:"phone,omitempty"`
	Email       string         `json:"email,omitempty" validate:"omitempty,email"`
	Settings    map[string]any `json:"settings,omitempty"`
}

// OrganizationMemberUpdateRequest represents a member update request
type OrganizationMemberUpdateRequest struct {
	Role        string         `json:"role" validate:"required,oneof=owner admin member viewer"`
	Permissions map[string]any `json:"permissions,omitempty"`
}

// OrganizationInviteRequest represents an invitation request
type OrganizationInviteRequest struct {
	Email string `json:"email" validate:"required,email"`
	Role  string `json:"role" validate:"required,oneof=admin member viewer"`
}

// OrganizationInviteResponse represents an invitation response
type OrganizationInviteResponse struct {
	ID             string    `json:"id"`
	OrganizationID string    `json:"organization_id"`
	Email          string    `json:"email"`
	Role           string    `json:"role"`
	ExpiresAt      time.Time `json:"expires_at"`
	CreatedAt      time.Time `json:"created_at"`
}

// OrganizationRole represents organization member roles
type OrganizationRole string

const (
	OrgRoleOwner  OrganizationRole = "owner"
	OrgRoleAdmin  OrganizationRole = "admin"
	OrgRoleMember OrganizationRole = "member"
	OrgRoleViewer OrganizationRole = "viewer"
)

// UserRole represents system-wide user roles
type UserRole string

const (
	UserRoleAdmin      UserRole = "admin"
	UserRoleManager    UserRole = "manager"
	UserRoleTechnician UserRole = "technician"
	UserRoleViewer     UserRole = "viewer"
)

// SubscriptionTier represents subscription levels
type SubscriptionTier string

const (
	TierFree         SubscriptionTier = "free"
	TierBasic        SubscriptionTier = "basic"
	TierProfessional SubscriptionTier = "professional"
	TierEnterprise   SubscriptionTier = "enterprise"
)
