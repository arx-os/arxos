package user

import (
	"time"

	"github.com/google/uuid"
)

// User represents a system user
type User struct {
	ID           uuid.UUID  `json:"id" db:"id"`
	Email        string     `json:"email" db:"email"`
	FullName     string     `json:"full_name" db:"full_name"`
	PasswordHash string     `json:"-" db:"password_hash"`
	Role         string     `json:"role" db:"role"`
	Status       string     `json:"status" db:"status"`
	LastLogin    *time.Time `json:"last_login,omitempty" db:"last_login"`
	CreatedAt    time.Time  `json:"created_at" db:"created_at"`
	UpdatedAt    time.Time  `json:"updated_at" db:"updated_at"`
}

// UserSession represents an active user session
type UserSession struct {
	ID           uuid.UUID `json:"id" db:"id"`
	UserID       uuid.UUID `json:"user_id" db:"user_id"`
	Token        string    `json:"token" db:"token"`
	RefreshToken string    `json:"refresh_token" db:"refresh_token"`
	ExpiresAt    time.Time `json:"expires_at" db:"expires_at"`
	CreatedAt    time.Time `json:"created_at" db:"created_at"`
	UpdatedAt    time.Time `json:"updated_at" db:"updated_at"`
}

// PasswordResetToken represents a password reset request
type PasswordResetToken struct {
	ID        uuid.UUID `json:"id" db:"id"`
	UserID    uuid.UUID `json:"user_id" db:"user_id"`
	Token     string    `json:"token" db:"token"`
	Used      bool      `json:"used" db:"used"`
	ExpiresAt time.Time `json:"expires_at" db:"expires_at"`
	CreatedAt time.Time `json:"created_at" db:"created_at"`
}

// Organization represents a user organization
type Organization struct {
	ID          uuid.UUID `json:"id" db:"id"`
	Name        string    `json:"name" db:"name"`
	Description string    `json:"description" db:"description"`
	CreatedBy   uuid.UUID `json:"created_by" db:"created_by"`
	CreatedAt   time.Time `json:"created_at" db:"created_at"`
	UpdatedAt   time.Time `json:"updated_at" db:"updated_at"`
}

// OrganizationMember represents a user's membership in an organization
type OrganizationMember struct {
	OrganizationID uuid.UUID `json:"organization_id" db:"organization_id"`
	UserID         uuid.UUID `json:"user_id" db:"user_id"`
	Role           string    `json:"role" db:"role"`
	JoinedAt       time.Time `json:"joined_at" db:"joined_at"`
}

// OrganizationInvitation represents an invitation to join an organization
type OrganizationInvitation struct {
	ID             uuid.UUID  `json:"id" db:"id"`
	OrganizationID uuid.UUID  `json:"organization_id" db:"organization_id"`
	Email          string     `json:"email" db:"email"`
	Role           string     `json:"role" db:"role"`
	Token          string     `json:"token" db:"token"`
	InvitedBy      uuid.UUID  `json:"invited_by" db:"invited_by"`
	AcceptedAt     *time.Time `json:"accepted_at,omitempty" db:"accepted_at"`
	ExpiresAt      time.Time  `json:"expires_at" db:"expires_at"`
	CreatedAt      time.Time  `json:"created_at" db:"created_at"`
}

// NewUser creates a new user
func NewUser(email, fullName, passwordHash, role string) *User {
	return &User{
		ID:           uuid.New(),
		Email:        email,
		FullName:     fullName,
		PasswordHash: passwordHash,
		Role:         role,
		Status:       "active",
		CreatedAt:    time.Now(),
		UpdatedAt:    time.Now(),
	}
}

// User roles
const (
	RoleAdmin      = "admin"
	RoleManager    = "manager"
	RoleTechnician = "technician"
	RoleViewer     = "viewer"
)

// User statuses
const (
	StatusActive   = "active"
	StatusInactive = "inactive"
	StatusSuspended = "suspended"
)