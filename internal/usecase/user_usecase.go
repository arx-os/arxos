package usecase

import (
	"context"
	"fmt"
	"time"

	"github.com/arx-os/arxos/internal/domain"
	"github.com/arx-os/arxos/internal/infrastructure/utils"
)

// UserUseCase implements the user business logic following Clean Architecture
type UserUseCase struct {
	userRepo    domain.UserRepository
	logger      domain.Logger
	idGenerator *utils.IDGenerator
}

// NewUserUseCase creates a new UserUseCase
func NewUserUseCase(userRepo domain.UserRepository, logger domain.Logger) *UserUseCase {
	return &UserUseCase{
		userRepo:    userRepo,
		logger:      logger,
		idGenerator: utils.NewIDGenerator(),
	}
}

// CreateUser creates a new user
func (uc *UserUseCase) CreateUser(ctx context.Context, req *domain.CreateUserRequest) (*domain.User, error) {
	uc.logger.Info("Creating user", "email", req.Email)

	// Validate business rules
	if err := uc.validateCreateUser(req); err != nil {
		uc.logger.Error("User validation failed", "error", err)
		return nil, fmt.Errorf("validation failed: %w", err)
	}

	// Check if user already exists
	existingUser, err := uc.userRepo.GetByEmail(ctx, req.Email)
	if err == nil && existingUser != nil {
		return nil, fmt.Errorf("user with email %s already exists", req.Email)
	}

	// Create user entity
	user := &domain.User{
		ID:        uc.idGenerator.GenerateUserID(req.Email),
		Email:     req.Email,
		Name:      req.Name,
		Role:      req.Role,
		Active:    true,
		CreatedAt: time.Now(),
		UpdatedAt: time.Now(),
	}

	// Save to repository
	if err := uc.userRepo.Create(ctx, user); err != nil {
		uc.logger.Error("Failed to create user", "error", err)
		return nil, fmt.Errorf("failed to create user: %w", err)
	}

	uc.logger.Info("User created successfully", "user_id", user.ID)
	return user, nil
}

// GetUser retrieves a user by ID
func (uc *UserUseCase) GetUser(ctx context.Context, id string) (*domain.User, error) {
	uc.logger.Info("Getting user", "user_id", id)

	if id == "" {
		return nil, fmt.Errorf("user ID is required")
	}

	user, err := uc.userRepo.GetByID(ctx, id)
	if err != nil {
		uc.logger.Error("Failed to get user", "user_id", id, "error", err)
		return nil, fmt.Errorf("failed to get user: %w", err)
	}

	return user, nil
}

// UpdateUser updates an existing user
func (uc *UserUseCase) UpdateUser(ctx context.Context, req *domain.UpdateUserRequest) (*domain.User, error) {
	uc.logger.Info("Updating user", "user_id", req.ID)

	// Get existing user
	user, err := uc.userRepo.GetByID(ctx, req.ID.String())
	if err != nil {
		uc.logger.Error("Failed to get user for update", "user_id", req.ID.String(), "error", err)
		return nil, fmt.Errorf("failed to get user: %w", err)
	}

	// Update fields if provided
	if req.Name != nil {
		user.Name = *req.Name
	}
	if req.Role != nil {
		user.Role = *req.Role
	}
	if req.Active != nil {
		user.Active = *req.Active
	}
	user.UpdatedAt = time.Now()

	// Validate business rules
	if err := uc.validateUpdateUser(user); err != nil {
		uc.logger.Error("User validation failed", "error", err)
		return nil, fmt.Errorf("validation failed: %w", err)
	}

	// Save to repository
	if err := uc.userRepo.Update(ctx, user); err != nil {
		uc.logger.Error("Failed to update user", "user_id", req.ID, "error", err)
		return nil, fmt.Errorf("failed to update user: %w", err)
	}

	uc.logger.Info("User updated successfully", "user_id", user.ID)
	return user, nil
}

// DeleteUser deletes a user
func (uc *UserUseCase) DeleteUser(ctx context.Context, id string) error {
	uc.logger.Info("Deleting user", "user_id", id)

	if id == "" {
		return fmt.Errorf("user ID is required")
	}

	// Check if user exists
	user, err := uc.userRepo.GetByID(ctx, id)
	if err != nil {
		uc.logger.Error("Failed to get user for deletion", "user_id", id, "error", err)
		return fmt.Errorf("failed to get user: %w", err)
	}

	// Business rule: Don't allow deletion of active users
	if user.Active {
		return fmt.Errorf("cannot delete active user")
	}

	// Delete from repository
	if err := uc.userRepo.Delete(ctx, id); err != nil {
		uc.logger.Error("Failed to delete user", "user_id", id, "error", err)
		return fmt.Errorf("failed to delete user: %w", err)
	}

	uc.logger.Info("User deleted successfully", "user_id", id)
	return nil
}

// ListUsers retrieves a list of users with optional filtering
func (uc *UserUseCase) ListUsers(ctx context.Context, filter *domain.UserFilter) ([]*domain.User, error) {
	uc.logger.Info("Listing users", "filter", filter)

	// Set default pagination if not provided
	if filter.Limit <= 0 {
		filter.Limit = 100
	}

	users, err := uc.userRepo.List(ctx, filter)
	if err != nil {
		uc.logger.Error("Failed to list users", "error", err)
		return nil, fmt.Errorf("failed to list users: %w", err)
	}

	uc.logger.Info("Users listed successfully", "count", len(users))
	return users, nil
}

// AuthenticateUser authenticates a user by email and password
func (uc *UserUseCase) AuthenticateUser(ctx context.Context, email, password string) (*domain.User, error) {
	uc.logger.Info("Authenticating user", "email", email)

	if email == "" || password == "" {
		return nil, fmt.Errorf("email and password are required")
	}

	user, err := uc.userRepo.GetByEmail(ctx, email)
	if err != nil {
		uc.logger.Error("Failed to get user for authentication", "email", email, "error", err)
		return nil, fmt.Errorf("authentication failed")
	}

	if !user.Active {
		return nil, fmt.Errorf("user account is inactive")
	}

	// TODO: Implement proper password verification
	// This is a placeholder - in real implementation, you would hash and compare passwords

	uc.logger.Info("User authenticated successfully", "user_id", user.ID)
	return user, nil
}

// GetUserOrganizations retrieves organizations for a user
func (uc *UserUseCase) GetUserOrganizations(ctx context.Context, userID string) ([]*domain.Organization, error) {
	uc.logger.Info("Getting user organizations", "user_id", userID)

	if userID == "" {
		return nil, fmt.Errorf("user ID is required")
	}

	organizations, err := uc.userRepo.GetOrganizations(ctx, userID)
	if err != nil {
		uc.logger.Error("Failed to get user organizations", "user_id", userID, "error", err)
		return nil, fmt.Errorf("failed to get user organizations: %w", err)
	}

	return organizations, nil
}

// Private helper methods

func (uc *UserUseCase) validateCreateUser(req *domain.CreateUserRequest) error {
	if req.Email == "" {
		return fmt.Errorf("email is required")
	}
	if req.Name == "" {
		return fmt.Errorf("name is required")
	}
	if req.Role == "" {
		return fmt.Errorf("role is required")
	}

	// Validate role
	validRoles := []string{"admin", "user", "viewer"}
	valid := false
	for _, role := range validRoles {
		if req.Role == role {
			valid = true
			break
		}
	}
	if !valid {
		return fmt.Errorf("invalid role: %s", req.Role)
	}

	return nil
}

func (uc *UserUseCase) validateUpdateUser(user *domain.User) error {
	if user.Name == "" {
		return fmt.Errorf("name cannot be empty")
	}
	if user.Role == "" {
		return fmt.Errorf("role cannot be empty")
	}

	// Validate role
	validRoles := []string{"admin", "user", "viewer"}
	valid := false
	for _, role := range validRoles {
		if user.Role == role {
			valid = true
			break
		}
	}
	if !valid {
		return fmt.Errorf("invalid role: %s", user.Role)
	}

	return nil
}
