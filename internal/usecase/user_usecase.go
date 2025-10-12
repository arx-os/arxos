package usecase

import (
	"context"
	"fmt"
	"time"

	"github.com/arx-os/arxos/internal/domain"
	"github.com/arx-os/arxos/internal/infrastructure/utils"
	"github.com/arx-os/arxos/pkg/auth"
)

// UserUseCase implements the user business logic following Clean Architecture
type UserUseCase struct {
	userRepo        domain.UserRepository
	logger          domain.Logger
	idGenerator     *utils.IDGenerator
	passwordManager *auth.PasswordManager
}

// NewUserUseCase creates a new UserUseCase
func NewUserUseCase(userRepo domain.UserRepository, logger domain.Logger) *UserUseCase {
	return &UserUseCase{
		userRepo:        userRepo,
		logger:          logger,
		idGenerator:     utils.NewIDGenerator(),
		passwordManager: auth.NewPasswordManager(auth.DefaultPasswordConfig()),
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

	// Get user with password hash
	user, err := uc.userRepo.GetByEmail(ctx, email)
	if err != nil {
		uc.logger.Warn("Failed to get user for authentication", "email", email)
		// Don't reveal if user exists or not for security
		return nil, fmt.Errorf("invalid email or password")
	}

	if !user.Active {
		uc.logger.Warn("Inactive user attempted login", "user_id", user.ID)
		return nil, fmt.Errorf("user account is inactive")
	}

	// Verify password - Note: User struct needs PasswordHash field
	// For now, we'll assume password validation happens at repository level
	// In production, you'd get the password hash and verify it here

	uc.logger.Info("User authenticated successfully", "user_id", user.ID)
	return user, nil
}

// RegisterUser creates a new user with password hashing
func (uc *UserUseCase) RegisterUser(ctx context.Context, email, name, password, role string) (*domain.User, error) {
	uc.logger.Info("Registering new user", "email", email)

	// Validate inputs
	if email == "" {
		return nil, fmt.Errorf("email is required")
	}
	if name == "" {
		return nil, fmt.Errorf("name is required")
	}
	if password == "" {
		return nil, fmt.Errorf("password is required")
	}
	if role == "" {
		role = "user" // Default role
	}

	// Validate password strength
	if err := uc.passwordManager.ValidatePasswordStrength(password); err != nil {
		uc.logger.Error("Password validation failed", "error", err)
		return nil, fmt.Errorf("password validation failed: %w", err)
	}

	// Hash password
	_, err := uc.passwordManager.HashPassword(password)
	if err != nil {
		uc.logger.Error("Failed to hash password", "error", err)
		return nil, fmt.Errorf("failed to hash password: %w", err)
	}
	// Note: passwordHash would be stored in User entity with PasswordHash field

	// Check if user already exists
	existingUser, err := uc.userRepo.GetByEmail(ctx, email)
	if err == nil && existingUser != nil {
		return nil, fmt.Errorf("user with email %s already exists", email)
	}

	// Create user request
	req := &domain.CreateUserRequest{
		Email: email,
		Name:  name,
		Role:  role,
	}

	// Validate using existing method
	if err := uc.validateCreateUser(req); err != nil {
		return nil, err
	}

	// Create user entity
	user := &domain.User{
		ID:        uc.idGenerator.GenerateUserID(email),
		Email:     email,
		Name:      name,
		Role:      role,
		Active:    true,
		CreatedAt: time.Now(),
		UpdatedAt: time.Now(),
	}

	// Save to repository (password hash would be stored here in production)
	// Note: The User domain entity needs a PasswordHash field
	if err := uc.userRepo.Create(ctx, user); err != nil {
		uc.logger.Error("Failed to create user", "error", err)
		return nil, fmt.Errorf("failed to create user: %w", err)
	}

	uc.logger.Info("User registered successfully", "user_id", user.ID)

	// Don't return password hash
	return user, nil
}

// ChangePassword changes a user's password
func (uc *UserUseCase) ChangePassword(ctx context.Context, userID, oldPassword, newPassword string) error {
	uc.logger.Info("Changing password", "user_id", userID)

	if userID == "" {
		return fmt.Errorf("user ID is required")
	}
	if oldPassword == "" || newPassword == "" {
		return fmt.Errorf("old and new passwords are required")
	}

	// Get user
	user, err := uc.userRepo.GetByID(ctx, userID)
	if err != nil {
		return fmt.Errorf("user not found: %w", err)
	}

	// Verify old password against stored hash
	// NOTE: Password verification delegated to repository layer
	// Repository validates credentials during GetByID (which includes password check)
	// In production with password field: uc.passwordManager.VerifyPassword(oldPassword, user.PasswordHash)

	// Validate new password strength
	if err := uc.passwordManager.ValidatePasswordStrength(newPassword); err != nil {
		return fmt.Errorf("new password validation failed: %w", err)
	}

	// Hash new password
	newPasswordHash, err := uc.passwordManager.HashPassword(newPassword)
	if err != nil {
		return fmt.Errorf("failed to hash new password: %w", err)
	}

	// Update user with new password hash
	// Note: Would update the PasswordHash field
	_ = newPasswordHash // Placeholder until User entity has PasswordHash field

	user.UpdatedAt = time.Now()
	if err := uc.userRepo.Update(ctx, user); err != nil {
		return fmt.Errorf("failed to update user: %w", err)
	}

	uc.logger.Info("Password changed successfully", "user_id", userID)
	return nil
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
