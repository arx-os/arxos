package api

import (
	"context"
	"errors"
	"fmt"
	"sync"
	"time"

	"github.com/joelpate/arxos/internal/common/logger"
	"golang.org/x/crypto/bcrypt"
)

// UserServiceImpl implements the UserService interface
type UserServiceImpl struct {
	users map[string]*User // userID -> user
	mu    sync.RWMutex
	auth  AuthService // Reference to auth service for coordination
}

// NewUserService creates a new user service
func NewUserService(auth AuthService) UserService {
	return &UserServiceImpl{
		users: make(map[string]*User),
		auth:  auth,
	}
}

// GetUser retrieves a user by ID
func (s *UserServiceImpl) GetUser(ctx context.Context, userID string) (*User, error) {
	s.mu.RLock()
	defer s.mu.RUnlock()
	
	user, exists := s.users[userID]
	if !exists {
		return nil, fmt.Errorf("user not found: %s", userID)
	}
	
	// Return copy without password hash
	userCopy := *user
	userCopy.PasswordHash = ""
	return &userCopy, nil
}

// ListUsers returns all users with optional filtering
func (s *UserServiceImpl) ListUsers(ctx context.Context, filter UserFilter) ([]*User, error) {
	s.mu.RLock()
	defer s.mu.RUnlock()
	
	var users []*User
	for _, user := range s.users {
		// Apply filters
		if filter.Role != "" && user.Role != filter.Role {
			continue
		}
		if filter.OrgID != "" && user.OrgID != filter.OrgID {
			continue
		}
		if filter.Active != nil && user.Active != *filter.Active {
			continue
		}
		
		// Create copy without password hash
		userCopy := *user
		userCopy.PasswordHash = ""
		users = append(users, &userCopy)
	}
	
	return users, nil
}

// CreateUser creates a new user
func (s *UserServiceImpl) CreateUser(ctx context.Context, req CreateUserRequest) (*User, error) {
	// Check if email already exists
	s.mu.RLock()
	for _, user := range s.users {
		if user.Email == req.Email {
			s.mu.RUnlock()
			return nil, errors.New("email already in use")
		}
	}
	s.mu.RUnlock()
	
	// Hash password
	hashedPassword, err := bcrypt.GenerateFromPassword([]byte(req.Password), bcrypt.DefaultCost)
	if err != nil {
		return nil, fmt.Errorf("failed to hash password: %w", err)
	}
	
	// Create user
	user := &User{
		ID:           generateID(),
		Email:        req.Email,
		Name:         req.Name,
		PasswordHash: string(hashedPassword),
		Role:         req.Role,
		OrgID:        req.OrgID,
		Permissions:  req.Permissions,
		Active:       true,
		CreatedAt:    time.Now(),
		UpdatedAt:    time.Now(),
	}
	
	// Validate role
	if user.Role == "" {
		user.Role = "user"
	}
	if user.Role != "admin" && user.Role != "user" && user.Role != "viewer" {
		return nil, fmt.Errorf("invalid role: %s", user.Role)
	}
	
	// Store user
	s.mu.Lock()
	s.users[user.ID] = user
	s.mu.Unlock()
	
	logger.Info("Created user: %s (%s)", user.Email, user.ID)
	
	// Return copy without password hash
	userCopy := *user
	userCopy.PasswordHash = ""
	return &userCopy, nil
}

// UpdateUser updates an existing user
func (s *UserServiceImpl) UpdateUser(ctx context.Context, userID string, updates UserUpdate) (*User, error) {
	s.mu.Lock()
	defer s.mu.Unlock()
	
	user, exists := s.users[userID]
	if !exists {
		return nil, fmt.Errorf("user not found: %s", userID)
	}
	
	// Apply updates
	if updates.Name != nil {
		user.Name = *updates.Name
	}
	if updates.Email != nil {
		// Check if new email is already in use
		for _, u := range s.users {
			if u.ID != userID && u.Email == *updates.Email {
				return nil, errors.New("email already in use")
			}
		}
		user.Email = *updates.Email
	}
	if updates.Role != nil {
		if *updates.Role != "admin" && *updates.Role != "user" && *updates.Role != "viewer" {
			return nil, fmt.Errorf("invalid role: %s", *updates.Role)
		}
		user.Role = *updates.Role
	}
	if updates.OrgID != nil {
		user.OrgID = *updates.OrgID
	}
	if updates.Permissions != nil {
		user.Permissions = updates.Permissions
	}
	if updates.Active != nil {
		user.Active = *updates.Active
	}
	if updates.Password != nil {
		hashedPassword, err := bcrypt.GenerateFromPassword([]byte(*updates.Password), bcrypt.DefaultCost)
		if err != nil {
			return nil, fmt.Errorf("failed to hash password: %w", err)
		}
		user.PasswordHash = string(hashedPassword)
	}
	
	user.UpdatedAt = time.Now()
	
	logger.Info("Updated user: %s (%s)", user.Email, user.ID)
	
	// Return copy without password hash
	userCopy := *user
	userCopy.PasswordHash = ""
	return &userCopy, nil
}

// DeleteUser deletes a user
func (s *UserServiceImpl) DeleteUser(ctx context.Context, userID string) error {
	s.mu.Lock()
	defer s.mu.Unlock()
	
	user, exists := s.users[userID]
	if !exists {
		return fmt.Errorf("user not found: %s", userID)
	}
	
	delete(s.users, userID)
	
	logger.Info("Deleted user: %s (%s)", user.Email, userID)
	return nil
}

// GetUserByEmail retrieves a user by email
func (s *UserServiceImpl) GetUserByEmail(ctx context.Context, email string) (*User, error) {
	s.mu.RLock()
	defer s.mu.RUnlock()
	
	for _, user := range s.users {
		if user.Email == email {
			// Return copy without password hash
			userCopy := *user
			userCopy.PasswordHash = ""
			return &userCopy, nil
		}
	}
	
	return nil, fmt.Errorf("user not found with email: %s", email)
}

// GetUserPermissions retrieves user permissions
func (s *UserServiceImpl) GetUserPermissions(ctx context.Context, userID string) ([]string, error) {
	s.mu.RLock()
	defer s.mu.RUnlock()
	
	user, exists := s.users[userID]
	if !exists {
		return nil, fmt.Errorf("user not found: %s", userID)
	}
	
	// Combine role-based and explicit permissions
	permissions := make([]string, 0)
	
	// Add role-based permissions
	switch user.Role {
	case "admin":
		permissions = append(permissions, "admin:*", "write:*", "read:*")
	case "user":
		permissions = append(permissions, "write:own", "read:*")
	case "viewer":
		permissions = append(permissions, "read:*")
	}
	
	// Add explicit permissions
	permissions = append(permissions, user.Permissions...)
	
	return permissions, nil
}

// UpdateUserActivity updates last activity timestamp
func (s *UserServiceImpl) UpdateUserActivity(ctx context.Context, userID string) error {
	s.mu.Lock()
	defer s.mu.Unlock()
	
	user, exists := s.users[userID]
	if !exists {
		return fmt.Errorf("user not found: %s", userID)
	}
	
	user.LastActivityAt = time.Now()
	return nil
}

// SyncWithAuth synchronizes user data with auth service (for initialization)
func (s *UserServiceImpl) SyncWithAuth() error {
	// This method would sync user data between services
	// TODO: Implement proper user synchronization with database
	return nil
}

// Helper function to generate IDs
func generateID() string {
	return fmt.Sprintf("%d", time.Now().UnixNano())
}