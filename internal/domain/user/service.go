package user

import (
	"context"
	"fmt"
	"time"

	"github.com/arx-os/arxos/internal/database"
	"github.com/arx-os/arxos/pkg/models"
	"github.com/google/uuid"
)

// Service defines the interface for user business logic following Clean Architecture principles
type Service interface {
	// User management
	CreateUser(ctx context.Context, req CreateUserRequest) (*User, error)
	GetUser(ctx context.Context, id uuid.UUID) (*User, error)
	GetUserByEmail(ctx context.Context, email string) (*User, error)
	UpdateUser(ctx context.Context, id uuid.UUID, req UpdateUserRequest) (*User, error)
	DeleteUser(ctx context.Context, id uuid.UUID) error
	ListUsers(ctx context.Context, req ListUsersRequest) ([]*User, error)

	// User authentication
	AuthenticateUser(ctx context.Context, email, password string) (*User, error)
	ChangePassword(ctx context.Context, userID uuid.UUID, req ChangePasswordRequest) error
	ResetPassword(ctx context.Context, req ResetPasswordRequest) error

	// User organizations
	GetUserOrganizations(ctx context.Context, userID uuid.UUID) ([]*models.Organization, error)
	AddUserToOrganization(ctx context.Context, userID, orgID uuid.UUID, role string) error
	RemoveUserFromOrganization(ctx context.Context, userID, orgID uuid.UUID) error

	// Legacy methods for backward compatibility
	GetUserLegacy(ctx context.Context, userID string) (*models.User, error)
	GetUserOrganizationsLegacy(ctx context.Context, userID string) ([]*models.Organization, error)
}

// User represents a user entity
type User struct {
	ID          uuid.UUID              `json:"id"`
	Email       string                 `json:"email"`
	Name        string                 `json:"name"`
	Role        string                 `json:"role"`
	IsActive    bool                   `json:"is_active"`
	LastLoginAt *time.Time             `json:"last_login_at,omitempty"`
	CreatedAt   time.Time              `json:"created_at"`
	UpdatedAt   time.Time              `json:"updated_at"`
	Metadata    map[string]interface{} `json:"metadata,omitempty"`
}

// Request types
type CreateUserRequest struct {
	Email    string                 `json:"email" validate:"required,email"`
	Name     string                 `json:"name" validate:"required"`
	Password string                 `json:"password" validate:"required,min=8"`
	Role     string                 `json:"role"`
	Metadata map[string]interface{} `json:"metadata,omitempty"`
}

type UpdateUserRequest struct {
	Name     *string                `json:"name,omitempty"`
	Role     *string                `json:"role,omitempty"`
	IsActive *bool                  `json:"is_active,omitempty"`
	Metadata map[string]interface{} `json:"metadata,omitempty"`
}

type ListUsersRequest struct {
	Role   string `json:"role"`
	Active *bool  `json:"active,omitempty"`
	Limit  int    `json:"limit" validate:"min=1,max=100"`
	Offset int    `json:"offset" validate:"min=0"`
}

type ChangePasswordRequest struct {
	CurrentPassword string `json:"current_password" validate:"required"`
	NewPassword     string `json:"new_password" validate:"required,min=8"`
}

type ResetPasswordRequest struct {
	Email string `json:"email" validate:"required,email"`
}

// service implements the user service following Clean Architecture principles
type service struct {
	db database.DB
}

// NewService creates a new user service with dependency injection
func NewService(db database.DB) Service {
	return &service{
		db: db,
	}
}

// CreateUser creates a new user
func (s *service) CreateUser(ctx context.Context, req CreateUserRequest) (*User, error) {
	// Validate request
	if err := s.validateCreateRequest(req); err != nil {
		return nil, fmt.Errorf("validation failed: %w", err)
	}

	// Check if user with email already exists
	existing, err := s.GetUserByEmail(ctx, req.Email)
	if err == nil && existing != nil {
		return nil, fmt.Errorf("user with email %s already exists", req.Email)
	}

	// Create user entity
	user := &User{
		ID:        uuid.New(),
		Email:     req.Email,
		Name:      req.Name,
		Role:      req.Role,
		IsActive:  true,
		Metadata:  req.Metadata,
		CreatedAt: time.Now(),
		UpdatedAt: time.Now(),
	}

	// Set default role if not provided
	if user.Role == "" {
		user.Role = "user"
	}

	// Validate entity
	if err := s.validateUser(user); err != nil {
		return nil, fmt.Errorf("entity validation failed: %w", err)
	}

	// TODO: Hash password and save to database
	// For now, just return the user entity
	return user, nil
}

// GetUser retrieves a user by ID
func (s *service) GetUser(ctx context.Context, id uuid.UUID) (*User, error) {
	// TODO: Implement database lookup
	// For now, return a mock user
	return &User{
		ID:        id,
		Email:     "user@example.com",
		Name:      "Test User",
		Role:      "user",
		IsActive:  true,
		CreatedAt: time.Now(),
		UpdatedAt: time.Now(),
	}, nil
}

// GetUserByEmail retrieves a user by email
func (s *service) GetUserByEmail(ctx context.Context, email string) (*User, error) {
	// TODO: Implement database lookup
	// For now, return nil (user not found)
	return nil, nil
}

// UpdateUser updates an existing user
func (s *service) UpdateUser(ctx context.Context, id uuid.UUID, req UpdateUserRequest) (*User, error) {
	// Get existing user
	user, err := s.GetUser(ctx, id)
	if err != nil {
		return nil, fmt.Errorf("failed to get user: %w", err)
	}
	if user == nil {
		return nil, fmt.Errorf("user not found")
	}

	// Update fields if provided
	if req.Name != nil {
		user.Name = *req.Name
	}
	if req.Role != nil {
		user.Role = *req.Role
	}
	if req.IsActive != nil {
		user.IsActive = *req.IsActive
	}
	if req.Metadata != nil {
		user.Metadata = req.Metadata
	}

	// Set updated timestamp
	user.UpdatedAt = time.Now()

	// Validate entity
	if err := s.validateUser(user); err != nil {
		return nil, fmt.Errorf("entity validation failed: %w", err)
	}

	// TODO: Save to database
	return user, nil
}

// DeleteUser deletes a user
func (s *service) DeleteUser(ctx context.Context, id uuid.UUID) error {
	// Check if user exists
	user, err := s.GetUser(ctx, id)
	if err != nil {
		return fmt.Errorf("failed to get user: %w", err)
	}
	if user == nil {
		return fmt.Errorf("user not found")
	}

	// TODO: Delete from database
	return nil
}

// ListUsers lists users with pagination
func (s *service) ListUsers(ctx context.Context, req ListUsersRequest) ([]*User, error) {
	// Validate request
	if err := s.validateListRequest(req); err != nil {
		return nil, fmt.Errorf("validation failed: %w", err)
	}

	// TODO: Implement database query with filters
	// For now, return empty list
	return []*User{}, nil
}

// AuthenticateUser authenticates a user with email and password
func (s *service) AuthenticateUser(ctx context.Context, email, password string) (*User, error) {
	// Get user by email
	user, err := s.GetUserByEmail(ctx, email)
	if err != nil {
		return nil, fmt.Errorf("failed to get user: %w", err)
	}
	if user == nil {
		return nil, fmt.Errorf("invalid credentials")
	}

	// TODO: Verify password hash
	// For now, just return the user
	return user, nil
}

// ChangePassword changes a user's password
func (s *service) ChangePassword(ctx context.Context, userID uuid.UUID, req ChangePasswordRequest) error {
	// Validate request
	if err := s.validateChangePasswordRequest(req); err != nil {
		return fmt.Errorf("validation failed: %w", err)
	}

	// Get user
	user, err := s.GetUser(ctx, userID)
	if err != nil {
		return fmt.Errorf("failed to get user: %w", err)
	}
	if user == nil {
		return fmt.Errorf("user not found")
	}

	// TODO: Verify current password and update to new password
	return nil
}

// ResetPassword initiates a password reset
func (s *service) ResetPassword(ctx context.Context, req ResetPasswordRequest) error {
	// Validate request
	if err := s.validateResetPasswordRequest(req); err != nil {
		return fmt.Errorf("validation failed: %w", err)
	}

	// TODO: Send password reset email
	return nil
}

// GetUserOrganizations retrieves organizations for a user
func (s *service) GetUserOrganizations(ctx context.Context, userID uuid.UUID) ([]*models.Organization, error) {
	// TODO: Implement database query
	// For now, return empty list
	return []*models.Organization{}, nil
}

// AddUserToOrganization adds a user to an organization
func (s *service) AddUserToOrganization(ctx context.Context, userID, orgID uuid.UUID, role string) error {
	// TODO: Implement database operation
	return nil
}

// RemoveUserFromOrganization removes a user from an organization
func (s *service) RemoveUserFromOrganization(ctx context.Context, userID, orgID uuid.UUID) error {
	// TODO: Implement database operation
	return nil
}

// Legacy methods for backward compatibility

// GetUserLegacy retrieves a user by string ID (legacy method)
func (s *service) GetUserLegacy(ctx context.Context, userID string) (*models.User, error) {
	// TODO: Implement database lookup
	// For now, return a mock user
	return &models.User{
		ID:    userID,
		Email: "user@example.com",
		Role:  "user",
	}, nil
}

// GetUserOrganizationsLegacy retrieves organizations for a user by string ID (legacy method)
func (s *service) GetUserOrganizationsLegacy(ctx context.Context, userID string) ([]*models.Organization, error) {
	// TODO: Implement database query
	// For now, return empty list
	return []*models.Organization{}, nil
}

// Helper methods for validation
func (s *service) validateCreateRequest(req CreateUserRequest) error {
	if req.Email == "" {
		return fmt.Errorf("email is required")
	}
	if req.Name == "" {
		return fmt.Errorf("name is required")
	}
	if req.Password == "" {
		return fmt.Errorf("password is required")
	}
	return nil
}

func (s *service) validateListRequest(req ListUsersRequest) error {
	if req.Limit <= 0 {
		req.Limit = 10 // Default limit
	}
	if req.Limit > 100 {
		return fmt.Errorf("limit cannot exceed 100")
	}
	if req.Offset < 0 {
		req.Offset = 0
	}
	return nil
}

func (s *service) validateUser(user *User) error {
	if user.Email == "" {
		return fmt.Errorf("email is required")
	}
	if user.Name == "" {
		return fmt.Errorf("name is required")
	}
	if user.Role == "" {
		return fmt.Errorf("role is required")
	}
	return nil
}

func (s *service) validateChangePasswordRequest(req ChangePasswordRequest) error {
	if req.CurrentPassword == "" {
		return fmt.Errorf("current password is required")
	}
	if req.NewPassword == "" {
		return fmt.Errorf("new password is required")
	}
	return nil
}

func (s *service) validateResetPasswordRequest(req ResetPasswordRequest) error {
	if req.Email == "" {
		return fmt.Errorf("email is required")
	}
	return nil
}
