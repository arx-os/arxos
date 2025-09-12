package models

import (
	"time"
)

// Organization represents a tenant in the multi-tenant system
type Organization struct {
	ID          string            `json:"id" db:"id"`
	Name        string            `json:"name" db:"name"`
	Slug        string            `json:"slug" db:"slug"` // URL-friendly identifier
	Domain      string            `json:"domain,omitempty" db:"domain"` // Custom domain (optional)
	Plan        PlanType          `json:"plan" db:"plan"`
	Status      OrgStatus         `json:"status" db:"status"`
	Settings    OrgSettings       `json:"settings" db:"settings"`
	Metadata    map[string]string `json:"metadata" db:"metadata"`
	CreatedAt   time.Time         `json:"created_at" db:"created_at"`
	UpdatedAt   time.Time         `json:"updated_at" db:"updated_at"`
	
	// Billing
	StripeCustomerID string     `json:"-" db:"stripe_customer_id"`
	TrialEndsAt      *time.Time `json:"trial_ends_at,omitempty" db:"trial_ends_at"`
	
	// Limits
	MaxUsers      int `json:"max_users" db:"max_users"`
	MaxBuildings  int `json:"max_buildings" db:"max_buildings"`
	MaxStorage    int64 `json:"max_storage" db:"max_storage"` // bytes
	UsedStorage   int64 `json:"used_storage" db:"used_storage"`
}

// OrgStatus represents the organization status
type OrgStatus string

const (
	OrgStatusActive    OrgStatus = "active"
	OrgStatusTrial     OrgStatus = "trial"
	OrgStatusSuspended OrgStatus = "suspended"
	OrgStatusCanceled  OrgStatus = "canceled"
)

// PlanType represents subscription plans
type PlanType string

const (
	PlanFree       PlanType = "free"
	PlanStarter    PlanType = "starter"
	PlanProfessional PlanType = "professional"
	PlanEnterprise PlanType = "enterprise"
)

// OrgSettings contains organization-specific settings
type OrgSettings struct {
	TimeZone          string   `json:"timezone"`
	DateFormat        string   `json:"date_format"`
	AllowedDomains    []string `json:"allowed_domains"` // For email domain restriction
	RequireMFA        bool     `json:"require_mfa"`
	SessionTimeout    int      `json:"session_timeout"` // minutes
	IPWhitelist       []string `json:"ip_whitelist"`
	WebhookURL        string   `json:"webhook_url"`
	SlackWebhook      string   `json:"slack_webhook"`
}

// OrganizationMember represents a user's membership in an organization
type OrganizationMember struct {
	ID             string    `json:"id" db:"id"`
	OrganizationID string    `json:"organization_id" db:"organization_id"`
	UserID         string    `json:"user_id" db:"user_id"`
	Role           Role      `json:"role" db:"role"`
	Permissions    []string  `json:"permissions" db:"permissions"`
	InvitedBy      string    `json:"invited_by" db:"invited_by"`
	InvitedAt      time.Time `json:"invited_at" db:"invited_at"`
	JoinedAt       *time.Time `json:"joined_at,omitempty" db:"joined_at"`
	LastAccessAt   *time.Time `json:"last_access_at,omitempty" db:"last_access_at"`
	
	// Relationships
	User         *User         `json:"user,omitempty"`
	Organization *Organization `json:"organization,omitempty"`
}

// OrganizationInvitation represents an invitation to join an organization
type OrganizationInvitation struct {
	ID             string    `json:"id" db:"id"`
	OrganizationID string    `json:"organization_id" db:"organization_id"`
	Email          string    `json:"email" db:"email"`
	Role           Role      `json:"role" db:"role"`
	Token          string    `json:"-" db:"token"` // Never send token to client
	InvitedBy      string    `json:"invited_by" db:"invited_by"`
	ExpiresAt      time.Time `json:"expires_at" db:"expires_at"`
	AcceptedAt     *time.Time `json:"accepted_at,omitempty" db:"accepted_at"`
	CreatedAt      time.Time `json:"created_at" db:"created_at"`
	
	// Relationships
	Organization *Organization `json:"organization,omitempty"`
	InvitedByUser *User        `json:"invited_by_user,omitempty"`
}

// IsExpired checks if an invitation has expired
func (i *OrganizationInvitation) IsExpired() bool {
	return time.Now().After(i.ExpiresAt)
}

// IsAccepted checks if an invitation has been accepted
func (i *OrganizationInvitation) IsAccepted() bool {
	return i.AcceptedAt != nil
}

// Role represents user roles within an organization
type Role string

const (
	RoleOwner   Role = "owner"   // Full access, billing, can delete org
	RoleAdmin   Role = "admin"   // Full access except billing
	RoleManager Role = "manager" // Manage buildings and equipment
	RoleMember  Role = "member"  // View and edit assigned buildings
	RoleViewer  Role = "viewer"  // Read-only access
)

// Permission represents granular permissions
type Permission string

const (
	// Organization permissions
	PermOrgView   Permission = "org:view"
	PermOrgEdit   Permission = "org:edit"
	PermOrgDelete Permission = "org:delete"
	
	// Building permissions
	PermBuildingCreate Permission = "building:create"
	PermBuildingView   Permission = "building:view"
	PermBuildingEdit   Permission = "building:edit"
	PermBuildingDelete Permission = "building:delete"
	
	// Equipment permissions
	PermEquipmentCreate Permission = "equipment:create"
	PermEquipmentView   Permission = "equipment:view"
	PermEquipmentEdit   Permission = "equipment:edit"
	PermEquipmentDelete Permission = "equipment:delete"
	
	// User management permissions
	PermUserInvite  Permission = "user:invite"
	PermUserView    Permission = "user:view"
	PermUserEdit    Permission = "user:edit"
	PermUserRemove  Permission = "user:remove"
	
	// Billing permissions
	PermBillingView   Permission = "billing:view"
	PermBillingEdit   Permission = "billing:edit"
)

// GetPermissions returns the default permissions for a role
func (r Role) GetPermissions() []Permission {
	switch r {
	case RoleOwner:
		return []Permission{
			PermOrgView, PermOrgEdit, PermOrgDelete,
			PermBuildingCreate, PermBuildingView, PermBuildingEdit, PermBuildingDelete,
			PermEquipmentCreate, PermEquipmentView, PermEquipmentEdit, PermEquipmentDelete,
			PermUserInvite, PermUserView, PermUserEdit, PermUserRemove,
			PermBillingView, PermBillingEdit,
		}
	case RoleAdmin:
		return []Permission{
			PermOrgView, PermOrgEdit,
			PermBuildingCreate, PermBuildingView, PermBuildingEdit, PermBuildingDelete,
			PermEquipmentCreate, PermEquipmentView, PermEquipmentEdit, PermEquipmentDelete,
			PermUserInvite, PermUserView, PermUserEdit, PermUserRemove,
		}
	case RoleManager:
		return []Permission{
			PermOrgView,
			PermBuildingCreate, PermBuildingView, PermBuildingEdit,
			PermEquipmentCreate, PermEquipmentView, PermEquipmentEdit,
			PermUserView,
		}
	case RoleMember:
		return []Permission{
			PermOrgView,
			PermBuildingView, PermBuildingEdit,
			PermEquipmentView, PermEquipmentEdit,
		}
	case RoleViewer:
		return []Permission{
			PermOrgView,
			PermBuildingView,
			PermEquipmentView,
		}
	default:
		return []Permission{}
	}
}

// Invitation represents a pending invitation to join an organization
type Invitation struct {
	ID             string    `json:"id" db:"id"`
	OrganizationID string    `json:"organization_id" db:"organization_id"`
	Email          string    `json:"email" db:"email"`
	Role           Role      `json:"role" db:"role"`
	Token          string    `json:"-" db:"token"` // Hidden from JSON
	InvitedBy      string    `json:"invited_by" db:"invited_by"`
	InvitedAt      time.Time `json:"invited_at" db:"invited_at"`
	ExpiresAt      time.Time `json:"expires_at" db:"expires_at"`
	AcceptedAt     *time.Time `json:"accepted_at,omitempty" db:"accepted_at"`
	
	// Relationships
	Organization *Organization `json:"organization,omitempty"`
	InvitedByUser *User        `json:"invited_by_user,omitempty"`
}

// APIKey represents an API key for programmatic access
type APIKey struct {
	ID             string    `json:"id" db:"id"`
	OrganizationID string    `json:"organization_id" db:"organization_id"`
	Name           string    `json:"name" db:"name"`
	Key            string    `json:"key,omitempty" db:"key"` // Only shown once
	HashedKey      string    `json:"-" db:"hashed_key"`
	Permissions    []string  `json:"permissions" db:"permissions"`
	LastUsedAt     *time.Time `json:"last_used_at,omitempty" db:"last_used_at"`
	ExpiresAt      *time.Time `json:"expires_at,omitempty" db:"expires_at"`
	CreatedBy      string    `json:"created_by" db:"created_by"`
	CreatedAt      time.Time `json:"created_at" db:"created_at"`
	RevokedAt      *time.Time `json:"revoked_at,omitempty" db:"revoked_at"`
}

// AuditLog represents an audit trail entry
type AuditLog struct {
	ID             string            `json:"id" db:"id"`
	OrganizationID string            `json:"organization_id" db:"organization_id"`
	UserID         string            `json:"user_id" db:"user_id"`
	Action         string            `json:"action" db:"action"`
	ResourceType   string            `json:"resource_type" db:"resource_type"`
	ResourceID     string            `json:"resource_id" db:"resource_id"`
	Changes        map[string]interface{} `json:"changes" db:"changes"`
	IPAddress      string            `json:"ip_address" db:"ip_address"`
	UserAgent      string            `json:"user_agent" db:"user_agent"`
	CreatedAt      time.Time         `json:"created_at" db:"created_at"`
}

// CanPerform checks if a member can perform an action
func (m *OrganizationMember) CanPerform(permission Permission) bool {
	// Get role permissions
	rolePerms := m.Role.GetPermissions()
	for _, p := range rolePerms {
		if p == permission {
			return true
		}
	}
	
	// Check custom permissions
	for _, p := range m.Permissions {
		if Permission(p) == permission {
			return true
		}
	}
	
	return false
}

// IsExpired checks if an invitation has expired
func (i *Invitation) IsExpired() bool {
	return time.Now().After(i.ExpiresAt)
}

// IsActive checks if an API key is active
func (k *APIKey) IsActive() bool {
	if k.RevokedAt != nil {
		return false
	}
	if k.ExpiresAt != nil && time.Now().After(*k.ExpiresAt) {
		return false
	}
	return true
}

// GetPlanLimits returns the limits for a plan
func GetPlanLimits(plan PlanType) (maxUsers int, maxBuildings int, maxStorage int64) {
	switch plan {
	case PlanFree:
		return 3, 1, 100 * 1024 * 1024 // 100MB
	case PlanStarter:
		return 10, 5, 1 * 1024 * 1024 * 1024 // 1GB
	case PlanProfessional:
		return 50, 25, 10 * 1024 * 1024 * 1024 // 10GB
	case PlanEnterprise:
		return -1, -1, -1 // Unlimited
	default:
		return 3, 1, 100 * 1024 * 1024
	}
}