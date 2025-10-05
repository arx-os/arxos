package validation

import (
	"fmt"
	"regexp"
	"strings"

	"github.com/arx-os/arxos/internal/domain/types"
	"github.com/google/uuid"
)

// IDValidator provides validation utilities for ID types
type IDValidator struct{}

// NewIDValidator creates a new ID validator
func NewIDValidator() *IDValidator {
	return &IDValidator{}
}

// ValidateID validates an ID and returns any validation errors
func (v *IDValidator) ValidateID(id types.ID) error {
	if id.IsEmpty() {
		return fmt.Errorf("ID cannot be empty")
	}

	if id.UUID != "" {
		if err := v.ValidateUUID(id.UUID); err != nil {
			return fmt.Errorf("invalid UUID: %w", err)
		}
	}

	if id.Legacy != "" {
		if err := v.ValidateLegacyID(id.Legacy); err != nil {
			return fmt.Errorf("invalid legacy ID: %w", err)
		}
	}

	return nil
}

// ValidateUUID validates a UUID string
func (v *IDValidator) ValidateUUID(uuidStr string) error {
	if uuidStr == "" {
		return fmt.Errorf("UUID cannot be empty")
	}

	if _, err := uuid.Parse(uuidStr); err != nil {
		return fmt.Errorf("invalid UUID format: %w", err)
	}

	return nil
}

// ValidateLegacyID validates a legacy TEXT ID
func (v *IDValidator) ValidateLegacyID(legacyID string) error {
	if legacyID == "" {
		return fmt.Errorf("legacy ID cannot be empty")
	}

	// Check length (reasonable limits)
	if len(legacyID) > 255 {
		return fmt.Errorf("legacy ID too long (max 255 characters)")
	}

	if len(legacyID) < 1 {
		return fmt.Errorf("legacy ID too short (min 1 character)")
	}

	// Check for invalid characters (basic validation)
	invalidChars := regexp.MustCompile(`[<>'"&]`)
	if invalidChars.MatchString(legacyID) {
		return fmt.Errorf("legacy ID contains invalid characters")
	}

	// Check for SQL injection patterns
	sqlPatterns := []string{
		"';", "--", "/*", "*/", "xp_", "sp_",
		"union", "select", "insert", "update", "delete",
		"drop", "create", "alter", "exec", "execute",
	}

	lowerID := strings.ToLower(legacyID)
	for _, pattern := range sqlPatterns {
		if strings.Contains(lowerID, pattern) {
			return fmt.Errorf("legacy ID contains potentially dangerous SQL pattern: %s", pattern)
		}
	}

	return nil
}

// ValidateIDString validates a string that could be either UUID or legacy ID
func (v *IDValidator) ValidateIDString(idStr string) error {
	if idStr == "" {
		return fmt.Errorf("ID string cannot be empty")
	}

	// Try to parse as UUID first
	if _, err := uuid.Parse(idStr); err == nil {
		return nil // Valid UUID
	}

	// Validate as legacy ID
	return v.ValidateLegacyID(idStr)
}

// IsValidUUID checks if a string is a valid UUID
func (v *IDValidator) IsValidUUID(uuidStr string) bool {
	_, err := uuid.Parse(uuidStr)
	return err == nil
}

// IsValidLegacyID checks if a string is a valid legacy ID
func (v *IDValidator) IsValidLegacyID(legacyID string) bool {
	return v.ValidateLegacyID(legacyID) == nil
}

// NormalizeID normalizes an ID string for consistent storage
func (v *IDValidator) NormalizeID(idStr string) string {
	if idStr == "" {
		return ""
	}

	// Trim whitespace
	idStr = strings.TrimSpace(idStr)

	// If it's a UUID, normalize it
	if _, err := uuid.Parse(idStr); err == nil {
		parsed, _ := uuid.Parse(idStr)
		return parsed.String()
	}

	// For legacy IDs, normalize case and trim
	return strings.TrimSpace(idStr)
}

// GenerateLegacyID generates a legacy-compatible ID for migration purposes
func (v *IDValidator) GenerateLegacyID(prefix string) string {
	if prefix == "" {
		prefix = "legacy"
	}

	// Generate a timestamp-based legacy ID
	timestamp := fmt.Sprintf("%d", uuid.New().Time())
	return fmt.Sprintf("%s_%s", prefix, timestamp)
}
