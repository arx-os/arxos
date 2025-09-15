package models

// CreateUserRequest represents a request to create a new user
type CreateUserRequest struct {
	Email    string `json:"email" validate:"required,email"`
	Username string `json:"username" validate:"required,min=3,max=30"`
	Password string `json:"password" validate:"required,min=8"`
	FullName string `json:"full_name" validate:"max=255"`
	Role     string `json:"role" validate:"omitempty,oneof=admin user viewer"`
}

// UpdateUserRequest represents a request to update user information
type UpdateUserRequest struct {
	Email    string `json:"email" validate:"omitempty,email"`
	Username string `json:"username" validate:"omitempty,min=3,max=30"`
	FullName string `json:"full_name" validate:"omitempty,max=255"`
	Role     string `json:"role" validate:"omitempty,oneof=admin user viewer"`
	Status   string `json:"status" validate:"omitempty,oneof=active inactive suspended"`
}

// CreateOrganizationRequest represents a request to create a new organization
type CreateOrganizationRequest struct {
	Name          string                 `json:"name" validate:"required,max=255"`
	Description   string                 `json:"description" validate:"max=1000"`
	Type          string                 `json:"type" validate:"omitempty,oneof=standard enterprise educational"`
	Settings      map[string]interface{} `json:"settings,omitempty"`
	CreatorUserID string                 `json:"-"` // Set internally, not from request
}

// UpdateOrganizationRequest represents a request to update organization information
type UpdateOrganizationRequest struct {
	Name        string                 `json:"name" validate:"omitempty,max=255"`
	Description string                 `json:"description" validate:"omitempty,max=1000"`
	Type        string                 `json:"type" validate:"omitempty,oneof=standard enterprise educational"`
	Status      string                 `json:"status" validate:"omitempty,oneof=active inactive suspended"`
	Settings    map[string]interface{} `json:"settings,omitempty"`
}

// AddOrganizationMemberRequest represents a request to add a member to an organization
type AddOrganizationMemberRequest struct {
	UserID string `json:"user_id" validate:"required"`
	Role   string `json:"role" validate:"required,oneof=admin member viewer"`
}

// UpdateOrganizationMemberRoleRequest represents a request to update a member's role
type UpdateOrganizationMemberRoleRequest struct {
	Role string `json:"role" validate:"required,oneof=admin member viewer"`
}

// CreateOrganizationInvitationRequest represents a request to create an invitation
type CreateOrganizationInvitationRequest struct {
	Email string `json:"email" validate:"required,email"`
	Role  string `json:"role" validate:"required,oneof=admin member viewer"`
}