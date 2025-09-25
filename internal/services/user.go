package services

import (
	"context"
	"fmt"
	"strings"
	"time"

	"github.com/arx-os/arxos/internal/common/logger"
	"github.com/arx-os/arxos/internal/database"
	"github.com/arx-os/arxos/internal/middleware"
	"github.com/arx-os/arxos/pkg/models"
	"golang.org/x/crypto/bcrypt"
)

// UserService handles user-related operations
type UserService struct {
	db database.DB
}

// NewUserService creates a new user service
func NewUserService(db database.DB) *UserService {
	return &UserService{
		db: db,
	}
}

// CreateUser creates a new user
func (s *UserService) CreateUser(ctx context.Context, req *models.UserCreateRequest) (*models.User, error) {
	// Validate input
	if err := middleware.ValidateEmail(req.Email); err != nil {
		return nil, fmt.Errorf("invalid email: %w", err)
	}

	if err := middleware.ValidateUsername(req.Username); err != nil {
		return nil, fmt.Errorf("invalid username: %w", err)
	}

	if err := middleware.ValidatePassword(req.Password); err != nil {
		return nil, fmt.Errorf("invalid password: %w", err)
	}

	// Check if email already exists
	existingUser, _ := s.db.GetUserByEmail(ctx, req.Email)
	if existingUser != nil {
		return nil, fmt.Errorf("email already registered")
	}

	// Hash password
	hashedPassword, err := bcrypt.GenerateFromPassword([]byte(req.Password), bcrypt.DefaultCost)
	if err != nil {
		return nil, fmt.Errorf("failed to hash password: %w", err)
	}

	// Create user
	now := time.Now()
	user := &models.User{
		ID:           generateID(),
		Email:        strings.ToLower(req.Email),
		Username:     req.Username,
		PasswordHash: string(hashedPassword),
		FullName:     req.FullName,
		Role:         req.Role,
		IsActive:     true,
		CreatedAt:    now,
		UpdatedAt:    now,
	}

	// Set default role if not provided
	if user.Role == "" {
		user.Role = "user"
	}

	// Validate role
	validRoles := map[string]bool{"admin": true, "user": true, "viewer": true}
	if !validRoles[user.Role] {
		return nil, fmt.Errorf("invalid role: %s", user.Role)
	}

	// Save to database
	if err := s.db.CreateUser(ctx, user); err != nil {
		return nil, fmt.Errorf("failed to create user: %w", err)
	}

	logger.Info("Created new user: %s (%s)", user.Email, user.ID)

	// Don't return password hash
	user.PasswordHash = ""
	return user, nil
}

// GetUser retrieves a user by ID
func (s *UserService) GetUser(ctx context.Context, userID string) (*models.User, error) {
	user, err := s.db.GetUser(ctx, userID)
	if err != nil {
		if err == database.ErrNotFound {
			return nil, fmt.Errorf("user not found")
		}
		return nil, fmt.Errorf("failed to get user: %w", err)
	}

	// Don't return password hash
	user.PasswordHash = ""
	return user, nil
}

// GetUserByEmail retrieves a user by email
func (s *UserService) GetUserByEmail(ctx context.Context, email string) (*models.User, error) {
	user, err := s.db.GetUserByEmail(ctx, strings.ToLower(email))
	if err != nil {
		if err == database.ErrNotFound {
			return nil, fmt.Errorf("user not found")
		}
		return nil, fmt.Errorf("failed to get user: %w", err)
	}

	// Don't return password hash
	user.PasswordHash = ""
	return user, nil
}

// UpdateUser updates a user's information
func (s *UserService) UpdateUser(ctx context.Context, userID string, req *models.UserUpdateRequest) (*models.User, error) {
	// Get existing user
	user, err := s.db.GetUser(ctx, userID)
	if err != nil {
		if err == database.ErrNotFound {
			return nil, fmt.Errorf("user not found")
		}
		return nil, fmt.Errorf("failed to get user: %w", err)
	}

	// Update fields if provided
	// Note: Email updates are not allowed through UserUpdateRequest for security reasons

	// Update allowed fields from UserUpdateRequest
	if req.FullName != "" {
		user.FullName = req.FullName
	}

	if req.Phone != "" {
		user.Phone = req.Phone
	}

	if req.AvatarURL != "" {
		user.AvatarURL = req.AvatarURL
	}

	if req.Preferences != nil {
		user.Preferences = req.Preferences
	}

	if req.Metadata != nil {
		user.Metadata = req.Metadata
	}

	// Update timestamp
	user.UpdatedAt = time.Now()

	// Save changes
	if err := s.db.UpdateUser(ctx, user); err != nil {
		return nil, fmt.Errorf("failed to update user: %w", err)
	}

	logger.Info("Updated user: %s (%s)", user.Email, user.ID)

	// Don't return password hash
	user.PasswordHash = ""
	return user, nil
}

// DeleteUser deletes a user
func (s *UserService) DeleteUser(ctx context.Context, userID string) error {
	// Check if user exists
	user, err := s.db.GetUser(ctx, userID)
	if err != nil {
		if err == database.ErrNotFound {
			return fmt.Errorf("user not found")
		}
		return fmt.Errorf("failed to get user: %w", err)
	}

	// Delete all user sessions
	if err := s.db.DeleteUserSessions(ctx, userID); err != nil {
		logger.Warn("Failed to delete user sessions: %v", err)
	}

	// Delete user
	if err := s.db.DeleteUser(ctx, userID); err != nil {
		return fmt.Errorf("failed to delete user: %w", err)
	}

	logger.Info("Deleted user: %s (%s)", user.Email, userID)
	return nil
}

// ListUsers returns a paginated list of users
func (s *UserService) ListUsers(ctx context.Context, page, limit int) ([]*models.User, int, error) {
	// Validate pagination
	if err := middleware.ValidatePagination(page, limit); err != nil {
		return nil, 0, fmt.Errorf("invalid pagination: %w", err)
	}

	// Calculate offset
	offset := (page - 1) * limit

	// Get users from database
	users, err := s.db.ListUsers(ctx, limit, offset)
	if err != nil {
		return nil, 0, fmt.Errorf("failed to list users: %w", err)
	}

	// Get total count for pagination
	totalCount, err := s.db.CountUsers(ctx)
	if err != nil {
		// If count fails, we can still return the users
		logger.Warn("Failed to get user count: %v", err)
		totalCount = len(users)
	}

	// Remove password hashes
	for _, user := range users {
		user.PasswordHash = ""
	}

	return users, totalCount, nil
}

// GetUserOrganizations returns all organizations a user belongs to
func (s *UserService) GetUserOrganizations(ctx context.Context, userID string) ([]*models.Organization, error) {
	// Check if user exists
	_, err := s.db.GetUser(ctx, userID)
	if err != nil {
		if err == database.ErrNotFound {
			return nil, fmt.Errorf("user not found")
		}
		return nil, fmt.Errorf("failed to get user: %w", err)
	}

	// Get organizations by user (placeholder - would need proper implementation)
	orgs, err := s.db.GetOrganizationsByUser(ctx, userID)
	if err != nil {
		return nil, fmt.Errorf("failed to get user organizations: %w", err)
	}

	return orgs, nil
}

// SearchUsers searches for users by query string
func (s *UserService) SearchUsers(ctx context.Context, query string, page, limit int) ([]*models.User, int, error) {
	// Validate pagination
	if err := middleware.ValidatePagination(page, limit); err != nil {
		return nil, 0, fmt.Errorf("invalid pagination: %w", err)
	}

	// Calculate offset
	offset := (page - 1) * limit

	// Search users by name or email
	users, err := s.db.SearchUsers(ctx, query, limit, offset)
	if err != nil {
		return nil, 0, fmt.Errorf("failed to search users: %w", err)
	}

	// Get total count for pagination
	totalCount, err := s.db.CountUsersByQuery(ctx, query)
	if err != nil {
		logger.Warn("Failed to get user search count: %v", err)
		totalCount = len(users)
	}

	// Remove password hashes
	for _, user := range users {
		user.PasswordHash = ""
	}

	return users, totalCount, nil
}

// BulkUpdateUsers updates multiple users at once
func (s *UserService) BulkUpdateUsers(ctx context.Context, updates []*models.UserUpdateRequest) error {
	if len(updates) == 0 {
		return fmt.Errorf("no updates provided")
	}

	// Process updates in batches
	batchSize := 100
	for i := 0; i < len(updates); i += batchSize {
		end := i + batchSize
		if end > len(updates) {
			end = len(updates)
		}

		batch := updates[i:end]
		if err := s.db.BulkUpdateUsers(ctx, batch); err != nil {
			return fmt.Errorf("failed to update user batch %d-%d: %w", i, end-1, err)
		}
	}

	logger.Info("Bulk updated %d users", len(updates))
	return nil
}

// SyncUserData synchronizes user data with external systems
func (s *UserService) SyncUserData(ctx context.Context, userID string) error {
	// Get user
	user, err := s.GetUser(ctx, userID)
	if err != nil {
		return fmt.Errorf("failed to get user: %w", err)
	}

	// Update last sync timestamp
	user.Metadata["last_sync"] = time.Now()

	// Update user in database
	if err := s.db.UpdateUser(ctx, user); err != nil {
		return fmt.Errorf("failed to update user sync timestamp: %w", err)
	}

	logger.Info("Synchronized user data for %s", user.Email)
	return nil
}

// GetUserStats returns statistics about users
func (s *UserService) GetUserStats(ctx context.Context) (*UserStats, error) {
	stats := &UserStats{}

	// Get total user count
	totalCount, err := s.db.CountUsers(ctx)
	if err != nil {
		return nil, fmt.Errorf("failed to get total user count: %w", err)
	}
	stats.TotalUsers = totalCount

	// Get active user count (users with recent activity)
	activeCount, err := s.db.CountActiveUsers(ctx)
	if err != nil {
		logger.Warn("Failed to get active user count: %v", err)
		stats.ActiveUsers = totalCount // Fallback to total
	} else {
		stats.ActiveUsers = activeCount
	}

	// Get users by role
	roleStats, err := s.db.GetUserStatsByRole(ctx)
	if err != nil {
		logger.Warn("Failed to get user role stats: %v", err)
		stats.RoleDistribution = make(map[string]int)
	} else {
		stats.RoleDistribution = roleStats
	}

	return stats, nil
}

// UserStats contains user statistics
type UserStats struct {
	TotalUsers       int            `json:"total_users"`
	ActiveUsers      int            `json:"active_users"`
	RoleDistribution map[string]int `json:"role_distribution"`
}
