package services

import (
	"errors"
	"fmt"
	"regexp"
	"strings"
	"time"
	
	"github.com/arxos/arxos/core/internal/db"
	"github.com/arxos/arxos/core/internal/models"
	"golang.org/x/crypto/bcrypt"
	"gorm.io/gorm"
)

var (
	ErrUserNotFound     = errors.New("user not found")
	ErrUserExists       = errors.New("user already exists")
	ErrInvalidEmail     = errors.New("invalid email format")
	ErrWeakPassword     = errors.New("password does not meet requirements")
	ErrInvalidTenant    = errors.New("invalid tenant")
	ErrAccountLocked    = errors.New("account is locked")
	ErrAccountInactive  = errors.New("account is inactive")
)

// UserService handles user management operations
type UserService struct {
	db *gorm.DB
}

// NewUserService creates a new user service instance
func NewUserService() *UserService {
	return &UserService{
		db: db.DB,
	}
}

// CreateUserRequest represents a user creation request
type CreateUserRequest struct {
	TenantID  string `json:"tenant_id"`
	Email     string `json:"email" validate:"required,email"`
	Username  string `json:"username" validate:"required,min=3,max=20"`
	Password  string `json:"password" validate:"required,min=8"`
	FirstName string `json:"first_name"`
	LastName  string `json:"last_name"`
	Phone     string `json:"phone"`
	Role      string `json:"role"`
}

// UpdateUserRequest represents a user update request
type UpdateUserRequest struct {
	Email      *string                `json:"email,omitempty"`
	FirstName  *string                `json:"first_name,omitempty"`
	LastName   *string                `json:"last_name,omitempty"`
	Phone      *string                `json:"phone,omitempty"`
	AvatarURL  *string                `json:"avatar_url,omitempty"`
	Status     *string                `json:"status,omitempty"`
	Metadata   map[string]interface{} `json:"metadata,omitempty"`
	Preferences map[string]interface{} `json:"preferences,omitempty"`
}

// UserResponse represents a user in API responses
type UserResponse struct {
	ID             uint                   `json:"id"`
	TenantID       string                 `json:"tenant_id"`
	Email          string                 `json:"email"`
	Username       string                 `json:"username"`
	FirstName      string                 `json:"first_name"`
	LastName       string                 `json:"last_name"`
	Phone          string                 `json:"phone"`
	AvatarURL      string                 `json:"avatar_url"`
	Status         string                 `json:"status"`
	EmailVerified  bool                   `json:"email_verified"`
	LastLoginAt    *time.Time            `json:"last_login_at"`
	LoginCount     int                   `json:"login_count"`
	Roles          []string              `json:"roles"`
	Metadata       map[string]interface{} `json:"metadata"`
	Preferences    map[string]interface{} `json:"preferences"`
	CreatedAt      time.Time             `json:"created_at"`
	UpdatedAt      time.Time             `json:"updated_at"`
}

// CreateUser creates a new user
func (s *UserService) CreateUser(req CreateUserRequest) (*UserResponse, error) {
	// Validate email format
	if !isValidEmail(req.Email) {
		return nil, ErrInvalidEmail
	}
	
	// Validate password strength
	if !isStrongPassword(req.Password) {
		return nil, ErrWeakPassword
	}
	
	// Check if user already exists
	var existingUser models.User
	if err := s.db.Where("email = ? OR username = ?", req.Email, req.Username).First(&existingUser).Error; err == nil {
		return nil, ErrUserExists
	}
	
	// Hash password
	hashedPassword, err := bcrypt.GenerateFromPassword([]byte(req.Password), bcrypt.DefaultCost)
	if err != nil {
		return nil, fmt.Errorf("failed to hash password: %w", err)
	}
	
	// Create user
	user := models.User{
		TenantID:  req.TenantID,
		Email:     req.Email,
		Username:  req.Username,
		Password:  string(hashedPassword),
		FirstName: req.FirstName,
		LastName:  req.LastName,
		Phone:     req.Phone,
		Status:    "active",
		Role:      req.Role,
	}
	
	if user.Role == "" {
		user.Role = "user"
	}
	
	// Start transaction
	tx := s.db.Begin()
	
	// Create user
	if err := tx.Create(&user).Error; err != nil {
		tx.Rollback()
		return nil, fmt.Errorf("failed to create user: %w", err)
	}
	
	// Assign default role
	if err := s.assignDefaultRole(tx, user.ID, req.TenantID); err != nil {
		tx.Rollback()
		return nil, fmt.Errorf("failed to assign default role: %w", err)
	}
	
	// Commit transaction
	if err := tx.Commit().Error; err != nil {
		return nil, fmt.Errorf("failed to commit transaction: %w", err)
	}
	
	// Get user with roles
	return s.GetUser(user.ID)
}

// GetUser retrieves a user by ID
func (s *UserService) GetUser(userID uint) (*UserResponse, error) {
	var user models.User
	if err := s.db.First(&user, userID).Error; err != nil {
		if errors.Is(err, gorm.ErrRecordNotFound) {
			return nil, ErrUserNotFound
		}
		return nil, fmt.Errorf("failed to get user: %w", err)
	}
	
	// Get user roles
	roles, err := s.getUserRoles(userID)
	if err != nil {
		return nil, fmt.Errorf("failed to get user roles: %w", err)
	}
	
	// Convert to response
	return &UserResponse{
		ID:            user.ID,
		TenantID:      user.TenantID,
		Email:         user.Email,
		Username:      user.Username,
		FirstName:     user.FirstName,
		LastName:      user.LastName,
		Phone:         user.Phone,
		AvatarURL:     user.AvatarURL,
		Status:        user.Status,
		EmailVerified: user.EmailVerified,
		LastLoginAt:   user.LastLoginAt,
		LoginCount:    user.LoginCount,
		Roles:         roles,
		Metadata:      user.Metadata,
		Preferences:   user.Preferences,
		CreatedAt:     user.CreatedAt,
		UpdatedAt:     user.UpdatedAt,
	}, nil
}

// UpdateUser updates user information
func (s *UserService) UpdateUser(userID uint, req UpdateUserRequest) (*UserResponse, error) {
	var user models.User
	if err := s.db.First(&user, userID).Error; err != nil {
		if errors.Is(err, gorm.ErrRecordNotFound) {
			return nil, ErrUserNotFound
		}
		return nil, fmt.Errorf("failed to get user: %w", err)
	}
	
	// Update fields
	updates := make(map[string]interface{})
	
	if req.Email != nil {
		if !isValidEmail(*req.Email) {
			return nil, ErrInvalidEmail
		}
		updates["email"] = *req.Email
		updates["email_verified"] = false // Reset verification on email change
	}
	
	if req.FirstName != nil {
		updates["first_name"] = *req.FirstName
	}
	
	if req.LastName != nil {
		updates["last_name"] = *req.LastName
	}
	
	if req.Phone != nil {
		updates["phone"] = *req.Phone
	}
	
	if req.AvatarURL != nil {
		updates["avatar_url"] = *req.AvatarURL
	}
	
	if req.Status != nil {
		updates["status"] = *req.Status
	}
	
	if req.Metadata != nil {
		updates["metadata"] = req.Metadata
	}
	
	if req.Preferences != nil {
		updates["preferences"] = req.Preferences
	}
	
	// Update user
	if err := s.db.Model(&user).Updates(updates).Error; err != nil {
		return nil, fmt.Errorf("failed to update user: %w", err)
	}
	
	return s.GetUser(userID)
}

// DeleteUser soft deletes a user
func (s *UserService) DeleteUser(userID uint) error {
	result := s.db.Delete(&models.User{}, userID)
	if result.Error != nil {
		return fmt.Errorf("failed to delete user: %w", result.Error)
	}
	
	if result.RowsAffected == 0 {
		return ErrUserNotFound
	}
	
	return nil
}

// ListUsers retrieves a paginated list of users
func (s *UserService) ListUsers(tenantID string, offset, limit int) ([]*UserResponse, int64, error) {
	var users []models.User
	var total int64
	
	// Count total users
	if err := s.db.Model(&models.User{}).Where("tenant_id = ?", tenantID).Count(&total).Error; err != nil {
		return nil, 0, fmt.Errorf("failed to count users: %w", err)
	}
	
	// Get paginated users
	if err := s.db.Where("tenant_id = ?", tenantID).
		Offset(offset).
		Limit(limit).
		Order("created_at DESC").
		Find(&users).Error; err != nil {
		return nil, 0, fmt.Errorf("failed to list users: %w", err)
	}
	
	// Convert to responses
	responses := make([]*UserResponse, len(users))
	for i, user := range users {
		roles, _ := s.getUserRoles(user.ID)
		responses[i] = &UserResponse{
			ID:            user.ID,
			TenantID:      user.TenantID,
			Email:         user.Email,
			Username:      user.Username,
			FirstName:     user.FirstName,
			LastName:      user.LastName,
			Phone:         user.Phone,
			AvatarURL:     user.AvatarURL,
			Status:        user.Status,
			EmailVerified: user.EmailVerified,
			LastLoginAt:   user.LastLoginAt,
			LoginCount:    user.LoginCount,
			Roles:         roles,
			CreatedAt:     user.CreatedAt,
			UpdatedAt:     user.UpdatedAt,
		}
	}
	
	return responses, total, nil
}

// ChangePassword changes a user's password
func (s *UserService) ChangePassword(userID uint, oldPassword, newPassword string) error {
	var user models.User
	if err := s.db.First(&user, userID).Error; err != nil {
		if errors.Is(err, gorm.ErrRecordNotFound) {
			return ErrUserNotFound
		}
		return fmt.Errorf("failed to get user: %w", err)
	}
	
	// Verify old password
	if err := bcrypt.CompareHashAndPassword([]byte(user.Password), []byte(oldPassword)); err != nil {
		return errors.New("incorrect password")
	}
	
	// Validate new password strength
	if !isStrongPassword(newPassword) {
		return ErrWeakPassword
	}
	
	// Hash new password
	hashedPassword, err := bcrypt.GenerateFromPassword([]byte(newPassword), bcrypt.DefaultCost)
	if err != nil {
		return fmt.Errorf("failed to hash password: %w", err)
	}
	
	// Update password
	if err := s.db.Model(&user).Update("password", string(hashedPassword)).Error; err != nil {
		return fmt.Errorf("failed to update password: %w", err)
	}
	
	return nil
}

// AuthenticateUser validates user credentials
func (s *UserService) AuthenticateUser(email, password string) (*UserResponse, error) {
	var user models.User
	if err := s.db.Where("email = ? OR username = ?", email, email).First(&user).Error; err != nil {
		if errors.Is(err, gorm.ErrRecordNotFound) {
			return nil, ErrUserNotFound
		}
		return nil, fmt.Errorf("failed to get user: %w", err)
	}
	
	// Check account status
	if user.Status != "active" {
		return nil, ErrAccountInactive
	}
	
	// Check if account is locked
	if user.LockedUntil != nil && time.Now().Before(*user.LockedUntil) {
		return nil, ErrAccountLocked
	}
	
	// Verify password
	if err := bcrypt.CompareHashAndPassword([]byte(user.Password), []byte(password)); err != nil {
		// Increment failed login attempts
		s.incrementFailedAttempts(user.ID)
		return nil, errors.New("invalid credentials")
	}
	
	// Reset failed attempts and update login info
	now := time.Now()
	updates := map[string]interface{}{
		"failed_login_attempts": 0,
		"last_login_at":        now,
		"login_count":          user.LoginCount + 1,
	}
	s.db.Model(&user).Updates(updates)
	
	return s.GetUser(user.ID)
}

// Helper functions

func (s *UserService) assignDefaultRole(tx *gorm.DB, userID uint, tenantID string) error {
	// Get default "user" role for tenant
	var role struct {
		ID string
	}
	
	if err := tx.Raw(`
		SELECT id FROM roles 
		WHERE tenant_id = ? AND name = 'user' 
		LIMIT 1
	`, tenantID).Scan(&role).Error; err != nil {
		return err
	}
	
	// Assign role to user
	_, err := tx.Exec(`
		INSERT INTO user_roles (user_id, role_id, granted_at)
		VALUES (?, ?, ?)
	`, userID, role.ID, time.Now()).Rows()
	
	return err
}

func (s *UserService) getUserRoles(userID uint) ([]string, error) {
	var roles []string
	err := s.db.Raw(`
		SELECT r.name 
		FROM roles r
		JOIN user_roles ur ON ur.role_id = r.id
		WHERE ur.user_id = ?
	`, userID).Scan(&roles).Error
	
	return roles, err
}

func (s *UserService) incrementFailedAttempts(userID uint) {
	var user models.User
	s.db.First(&user, userID)
	
	attempts := user.FailedLoginAttempts + 1
	updates := map[string]interface{}{
		"failed_login_attempts": attempts,
	}
	
	// Lock account after 5 failed attempts
	if attempts >= 5 {
		lockUntil := time.Now().Add(30 * time.Minute)
		updates["locked_until"] = lockUntil
	}
	
	s.db.Model(&user).Updates(updates)
}

// isValidEmail validates email format
func isValidEmail(email string) bool {
	emailRegex := regexp.MustCompile(`^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$`)
	return emailRegex.MatchString(email)
}

// isStrongPassword checks password strength
func isStrongPassword(password string) bool {
	if len(password) < 8 {
		return false
	}
	
	hasUpper := regexp.MustCompile(`[A-Z]`).MatchString(password)
	hasLower := regexp.MustCompile(`[a-z]`).MatchString(password)
	hasNumber := regexp.MustCompile(`[0-9]`).MatchString(password)
	hasSpecial := regexp.MustCompile(`[!@#$%^&*(),.?":{}|<>]`).MatchString(password)
	
	// Require at least 3 out of 4 character types
	strength := 0
	if hasUpper {
		strength++
	}
	if hasLower {
		strength++
	}
	if hasNumber {
		strength++
	}
	if hasSpecial {
		strength++
	}
	
	return strength >= 3
}