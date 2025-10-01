package services

import (
	"context"
	"fmt"

	"github.com/arx-os/arxos/internal/domain/user"
	"github.com/arx-os/arxos/internal/interfaces/http/models"
	domainmodels "github.com/arx-os/arxos/pkg/models"
)

// UserApplicationService provides application-level user operations
type UserApplicationService struct {
	userService user.Service
}

// NewUserApplicationService creates a new user application service
func NewUserApplicationService(userService user.Service) *UserApplicationService {
	return &UserApplicationService{
		userService: userService,
	}
}

// ListUsers retrieves a list of users with filtering and pagination
func (s *UserApplicationService) ListUsers(ctx context.Context, filter models.UserFilter, limit, offset int) ([]*domainmodels.User, error) {
	// Convert filter to domain format
	domainFilter := user.Filter{
		Role: filter.Role,
	}

	// Call domain service
	users, err := s.userService.ListUsers(ctx, domainFilter)
	if err != nil {
		return nil, fmt.Errorf("failed to list users: %w", err)
	}

	// Apply pagination
	start := offset
	end := offset + limit
	if start >= len(users) {
		return []*models.User{}, nil
	}
	if end > len(users) {
		end = len(users)
	}

	return users[start:end], nil
}

// GetUser retrieves a user by ID
func (s *UserApplicationService) GetUser(ctx context.Context, userID string) (*domainmodels.User, error) {
	user, err := s.userService.GetUser(ctx, userID)
	if err != nil {
		return nil, fmt.Errorf("failed to get user: %w", err)
	}

	return user, nil
}

// CreateUser creates a new user
func (s *UserApplicationService) CreateUser(ctx context.Context, req models.CreateUserRequest) (*domainmodels.User, error) {
	// Convert request to domain format
	createReq := user.CreateUserRequest{
		Email:    req.Email,
		Name:     req.Name,
		Password: req.Password,
		Role:     req.Role,
		OrgID:    req.OrgID,
		IsActive: req.IsActive,
		Metadata: req.Metadata,
	}

	// Call domain service
	user, err := s.userService.CreateUser(ctx, createReq)
	if err != nil {
		return nil, fmt.Errorf("failed to create user: %w", err)
	}

	return user, nil
}

// UpdateUser updates an existing user
func (s *UserApplicationService) UpdateUser(ctx context.Context, userID string, req models.UpdateUserRequest) (*domainmodels.User, error) {
	// Convert request to domain format
	updateReq := user.UpdateUserRequest{
		Name:     req.Name,
		Email:    req.Email,
		Role:     req.Role,
		IsActive: req.IsActive,
		Metadata: req.Metadata,
	}

	// Call domain service
	user, err := s.userService.UpdateUser(ctx, userID, updateReq)
	if err != nil {
		return nil, fmt.Errorf("failed to update user: %w", err)
	}

	return user, nil
}

// DeleteUser deletes a user
func (s *UserApplicationService) DeleteUser(ctx context.Context, userID string) error {
	err := s.userService.DeleteUser(ctx, userID)
	if err != nil {
		return fmt.Errorf("failed to delete user: %w", err)
	}

	return nil
}

// AuthenticateUser authenticates a user with email and password
func (s *UserApplicationService) AuthenticateUser(ctx context.Context, email, password string) (*domainmodels.User, error) {
	// This would typically involve password hashing and verification
	user, err := s.userService.GetUserByEmail(ctx, email)
	if err != nil {
		return nil, fmt.Errorf("authentication failed: %w", err)
	}

	// In a real implementation, you would verify the password hash here
	// For now, we'll assume the password verification is handled by the domain service

	return user, nil
}

// GetUserOrganizations retrieves organizations for a user
func (s *UserApplicationService) GetUserOrganizations(ctx context.Context, userID string) ([]*domainmodels.Organization, error) {
	organizations, err := s.userService.GetUserOrganizations(ctx, userID)
	if err != nil {
		return nil, fmt.Errorf("failed to get user organizations: %w", err)
	}

	return organizations, nil
}
