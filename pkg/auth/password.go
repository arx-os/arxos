// Package auth provides password hashing and validation utilities.
package auth

import (
	"crypto/rand"
	"crypto/subtle"
	"encoding/base64"
	"fmt"
	"strings"

	"github.com/arx-os/arxos/pkg/errors"
	"golang.org/x/crypto/bcrypt"
)

// PasswordConfig holds configuration for password hashing
type PasswordConfig struct {
	// Cost for bcrypt hashing (4-31, default 12)
	Cost int

	// Minimum password length
	MinLength int

	// Maximum password length
	MaxLength int

	// Require special characters
	RequireSpecial bool

	// Require numbers
	RequireNumbers bool

	// Require uppercase
	RequireUppercase bool

	// Require lowercase
	RequireLowercase bool
}

// DefaultPasswordConfig returns a default password configuration
func DefaultPasswordConfig() *PasswordConfig {
	return &PasswordConfig{
		Cost:             12,
		MinLength:        8,
		MaxLength:        128,
		RequireSpecial:   true,
		RequireNumbers:   true,
		RequireUppercase: true,
		RequireLowercase: true,
	}
}

// PasswordManager handles password operations
type PasswordManager struct {
	config *PasswordConfig
}

// NewPasswordManager creates a new password manager
func NewPasswordManager(config *PasswordConfig) *PasswordManager {
	if config == nil {
		config = DefaultPasswordConfig()
	}
	return &PasswordManager{config: config}
}

// HashPassword hashes a password using bcrypt
func (pm *PasswordManager) HashPassword(password string) (string, error) {
	if err := pm.ValidatePasswordStrength(password); err != nil {
		return "", err
	}

	hash, err := bcrypt.GenerateFromPassword([]byte(password), pm.config.Cost)
	if err != nil {
		return "", errors.Wrap(err, errors.CodeInternal, "failed to hash password")
	}

	return string(hash), nil
}

// VerifyPassword verifies a password against its hash
func (pm *PasswordManager) VerifyPassword(password, hash string) error {
	if password == "" {
		return errors.New(errors.CodeInvalidInput, "password cannot be empty")
	}
	if hash == "" {
		return errors.New(errors.CodeInvalidInput, "hash cannot be empty")
	}

	err := bcrypt.CompareHashAndPassword([]byte(hash), []byte(password))
	if err != nil {
		return errors.New(errors.CodeUnauthorized, "invalid password")
	}

	return nil
}

// ValidatePasswordStrength validates password strength according to config
func (pm *PasswordManager) ValidatePasswordStrength(password string) error {
	if len(password) < pm.config.MinLength {
		return errors.New(errors.CodeInvalidInput, fmt.Sprintf("password must be at least %d characters long", pm.config.MinLength))
	}

	if len(password) > pm.config.MaxLength {
		return errors.New(errors.CodeInvalidInput, fmt.Sprintf("password must be no more than %d characters long", pm.config.MaxLength))
	}

	if pm.config.RequireSpecial && !hasSpecialChar(password) {
		return errors.New(errors.CodeInvalidInput, "password must contain at least one special character")
	}

	if pm.config.RequireNumbers && !hasNumber(password) {
		return errors.New(errors.CodeInvalidInput, "password must contain at least one number")
	}

	if pm.config.RequireUppercase && !hasUppercase(password) {
		return errors.New(errors.CodeInvalidInput, "password must contain at least one uppercase letter")
	}

	if pm.config.RequireLowercase && !hasLowercase(password) {
		return errors.New(errors.CodeInvalidInput, "password must contain at least one lowercase letter")
	}

	return nil
}

// GenerateSecurePassword generates a cryptographically secure random password
func (pm *PasswordManager) GenerateSecurePassword(length int) (string, error) {
	if length < pm.config.MinLength {
		length = pm.config.MinLength
	}
	if length > pm.config.MaxLength {
		length = pm.config.MaxLength
	}

	// Character sets
	lowercase := "abcdefghijklmnopqrstuvwxyz"
	uppercase := "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
	numbers := "0123456789"
	special := "!@#$%^&*()_+-=[]{}|;:,.<>?"

	// Build character set based on requirements
	charSet := lowercase
	if pm.config.RequireUppercase {
		charSet += uppercase
	}
	if pm.config.RequireNumbers {
		charSet += numbers
	}
	if pm.config.RequireSpecial {
		charSet += special
	}

	// Generate random password
	password := make([]byte, length)
	for i := range password {
		randomByte := make([]byte, 1)
		_, err := rand.Read(randomByte)
		if err != nil {
			return "", errors.Wrap(err, errors.CodeInternal, "failed to generate random password")
		}
		password[i] = charSet[randomByte[0]%byte(len(charSet))]
	}

	// Ensure password meets all requirements
	passwordStr := string(password)
	if err := pm.ValidatePasswordStrength(passwordStr); err != nil {
		// If generated password doesn't meet requirements, try again
		return pm.GenerateSecurePassword(length)
	}

	return passwordStr, nil
}

// GeneratePasswordResetToken generates a secure password reset token
func GeneratePasswordResetToken() (string, error) {
	bytes := make([]byte, 32)
	_, err := rand.Read(bytes)
	if err != nil {
		return "", errors.Wrap(err, errors.CodeInternal, "failed to generate reset token")
	}
	return base64.URLEncoding.EncodeToString(bytes), nil
}

// ConstantTimeCompare compares two strings in constant time
func ConstantTimeCompare(a, b string) bool {
	return subtle.ConstantTimeCompare([]byte(a), []byte(b)) == 1
}

// Helper functions for password validation

func hasSpecialChar(password string) bool {
	specialChars := "!@#$%^&*()_+-=[]{}|;:,.<>?"
	for _, char := range password {
		if strings.ContainsRune(specialChars, char) {
			return true
		}
	}
	return false
}

func hasNumber(password string) bool {
	for _, char := range password {
		if char >= '0' && char <= '9' {
			return true
		}
	}
	return false
}

func hasUppercase(password string) bool {
	for _, char := range password {
		if char >= 'A' && char <= 'Z' {
			return true
		}
	}
	return false
}

func hasLowercase(password string) bool {
	for _, char := range password {
		if char >= 'a' && char <= 'z' {
			return true
		}
	}
	return false
}

// PasswordStrength represents password strength levels
type PasswordStrength int

const (
	PasswordStrengthVeryWeak PasswordStrength = iota
	PasswordStrengthWeak
	PasswordStrengthFair
	PasswordStrengthGood
	PasswordStrengthStrong
)

// CalculatePasswordStrength calculates password strength score
func (pm *PasswordManager) CalculatePasswordStrength(password string) PasswordStrength {
	score := 0

	// Length scoring
	if len(password) >= 8 {
		score++
	}
	if len(password) >= 12 {
		score++
	}
	if len(password) >= 16 {
		score++
	}

	// Character variety scoring
	if hasLowercase(password) {
		score++
	}
	if hasUppercase(password) {
		score++
	}
	if hasNumber(password) {
		score++
	}
	if hasSpecialChar(password) {
		score++
	}

	// Bonus for very long passwords
	if len(password) >= 20 {
		score++
	}

	switch {
	case score <= 2:
		return PasswordStrengthVeryWeak
	case score <= 3:
		return PasswordStrengthWeak
	case score <= 4:
		return PasswordStrengthFair
	case score <= 6:
		return PasswordStrengthGood
	default:
		return PasswordStrengthStrong
	}
}

// GetPasswordStrengthString returns a human-readable strength description
func (pm *PasswordManager) GetPasswordStrengthString(password string) string {
	strength := pm.CalculatePasswordStrength(password)
	switch strength {
	case PasswordStrengthVeryWeak:
		return "Very Weak"
	case PasswordStrengthWeak:
		return "Weak"
	case PasswordStrengthFair:
		return "Fair"
	case PasswordStrengthGood:
		return "Good"
	case PasswordStrengthStrong:
		return "Strong"
	default:
		return "Unknown"
	}
}
