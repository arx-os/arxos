package security

import (
	"html"
	"net/url"
	"path/filepath"
	"regexp"
	"strings"
	"unicode"
)

// Sanitizer provides input sanitization functions
type Sanitizer struct {
	maxLength       int
	allowedPatterns map[string]*regexp.Regexp
}

// NewSanitizer creates a new sanitizer
func NewSanitizer() *Sanitizer {
	return &Sanitizer{
		maxLength: 1024 * 1024, // 1MB default max
		allowedPatterns: map[string]*regexp.Regexp{
			"email":    regexp.MustCompile(`^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$`),
			"uuid":     regexp.MustCompile(`^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$`),
			"arxos_id": regexp.MustCompile(`^ARXOS-[A-Z]{2}-[A-Z]{2}-[A-Z]{2}-[A-Z]{3}-\d{4}(/[\w-]+)*$`),
			"alphanum": regexp.MustCompile(`^[a-zA-Z0-9]+$`),
			"path":     regexp.MustCompile(`^[a-zA-Z0-9/_.-]+$`),
		},
	}
}

// SanitizeString sanitizes a string input
func (s *Sanitizer) SanitizeString(input string, maxLen int) string {
	// Trim whitespace
	input = strings.TrimSpace(input)

	// Check length
	if maxLen > 0 && len(input) > maxLen {
		input = input[:maxLen]
	}

	// Remove null bytes
	input = strings.ReplaceAll(input, "\x00", "")

	// Normalize unicode
	input = normalizeUnicode(input)

	return input
}

// SanitizeHTML sanitizes HTML content
func (s *Sanitizer) SanitizeHTML(input string) string {
	// Escape HTML entities
	return html.EscapeString(input)
}

// SanitizeSQL prevents SQL injection
func (s *Sanitizer) SanitizeSQL(input string) string {
	// Remove or escape SQL special characters
	replacements := map[string]string{
		"'":    "''",
		`"`:    `""`,
		"\\":   "\\\\",
		"\n":   " ",
		"\r":   " ",
		"\t":   " ",
		"\x00": "",
	}

	for old, new := range replacements {
		input = strings.ReplaceAll(input, old, new)
	}

	return input
}

// SanitizePath sanitizes file paths
func (s *Sanitizer) SanitizePath(input string) string {
	// Clean the path
	input = filepath.Clean(input)

	// Remove any .. sequences
	input = strings.ReplaceAll(input, "..", "")

	// Ensure it doesn't start with /
	input = strings.TrimPrefix(input, "/")

	// Remove any null bytes
	input = strings.ReplaceAll(input, "\x00", "")

	return input
}

// SanitizeURL sanitizes URLs
func (s *Sanitizer) SanitizeURL(input string) (string, error) {
	// Parse URL
	u, err := url.Parse(input)
	if err != nil {
		return "", err
	}

	// Only allow http and https
	if u.Scheme != "http" && u.Scheme != "https" {
		u.Scheme = "https"
	}

	// Remove any credentials
	u.User = nil

	// Clean path
	u.Path = filepath.Clean(u.Path)

	return u.String(), nil
}

// ValidateEmail validates an email address
func (s *Sanitizer) ValidateEmail(email string) bool {
	if pattern, exists := s.allowedPatterns["email"]; exists {
		return pattern.MatchString(email)
	}
	return false
}

// ValidateUUID validates a UUID
func (s *Sanitizer) ValidateUUID(uuid string) bool {
	if pattern, exists := s.allowedPatterns["uuid"]; exists {
		return pattern.MatchString(uuid)
	}
	return false
}

// ValidateArxOSID validates an ArxOS ID
func (s *Sanitizer) ValidateArxOSID(id string) bool {
	if pattern, exists := s.allowedPatterns["arxos_id"]; exists {
		return pattern.MatchString(id)
	}
	return false
}

// ValidateAlphanumeric validates alphanumeric strings
func (s *Sanitizer) ValidateAlphanumeric(input string) bool {
	if pattern, exists := s.allowedPatterns["alphanum"]; exists {
		return pattern.MatchString(input)
	}
	return false
}

// RemoveControlCharacters removes control characters
func RemoveControlCharacters(input string) string {
	return strings.Map(func(r rune) rune {
		if unicode.IsControl(r) && r != '\t' && r != '\n' && r != '\r' {
			return -1
		}
		return r
	}, input)
}

// normalizeUnicode normalizes unicode characters
func normalizeUnicode(input string) string {
	// Remove zero-width characters
	zeroWidth := []string{
		"\u200B", // Zero-width space
		"\u200C", // Zero-width non-joiner
		"\u200D", // Zero-width joiner
		"\uFEFF", // Zero-width no-break space
	}

	for _, char := range zeroWidth {
		input = strings.ReplaceAll(input, char, "")
	}

	return input
}

// InputValidator provides input validation
type InputValidator struct {
	rules map[string]ValidationRule
}

// ValidationRule defines a validation rule
type ValidationRule struct {
	Required  bool
	MinLength int
	MaxLength int
	Pattern   *regexp.Regexp
	Validator func(string) bool
}

// NewInputValidator creates a new input validator
func NewInputValidator() *InputValidator {
	return &InputValidator{
		rules: map[string]ValidationRule{
			"building_name": {
				Required:  true,
				MinLength: 1,
				MaxLength: 255,
				Pattern:   regexp.MustCompile(`^[a-zA-Z0-9\s._-]+$`),
			},
			"floor_level": {
				Required: true,
				Pattern:  regexp.MustCompile(`^-?\d+$`),
			},
			"equipment_id": {
				Required:  true,
				MinLength: 1,
				MaxLength: 100,
				Pattern:   regexp.MustCompile(`^[a-zA-Z0-9_/-]+$`),
			},
			"status": {
				Required: true,
				Validator: func(s string) bool {
					validStatuses := []string{
						"OPERATIONAL",
						"DEGRADED",
						"FAILED",
						"MAINTENANCE",
						"OFFLINE",
						"UNKNOWN",
					}
					for _, valid := range validStatuses {
						if s == valid {
							return true
						}
					}
					return false
				},
			},
		},
	}
}

// Validate validates input against a rule
func (v *InputValidator) Validate(ruleName string, input string) error {
	rule, exists := v.rules[ruleName]
	if !exists {
		return nil // No rule defined
	}

	// Check required
	if rule.Required && input == "" {
		return ErrRequired
	}

	// Check length
	if rule.MinLength > 0 && len(input) < rule.MinLength {
		return ErrTooShort
	}
	if rule.MaxLength > 0 && len(input) > rule.MaxLength {
		return ErrTooLong
	}

	// Check pattern
	if rule.Pattern != nil && !rule.Pattern.MatchString(input) {
		return ErrInvalidFormat
	}

	// Check custom validator
	if rule.Validator != nil && !rule.Validator(input) {
		return ErrInvalidValue
	}

	return nil
}

// Common validation errors
var (
	ErrRequired      = ValidationError{Message: "field is required"}
	ErrTooShort      = ValidationError{Message: "input is too short"}
	ErrTooLong       = ValidationError{Message: "input is too long"}
	ErrInvalidFormat = ValidationError{Message: "invalid format"}
	ErrInvalidValue  = ValidationError{Message: "invalid value"}
)

// ValidationError represents a validation error
type ValidationError struct {
	Message string
}

func (e ValidationError) Error() string {
	return e.Message
}

// XSSProtector provides XSS protection
type XSSProtector struct {
	allowedTags  []string
	allowedAttrs map[string][]string
}

// NewXSSProtector creates a new XSS protector
func NewXSSProtector() *XSSProtector {
	return &XSSProtector{
		allowedTags: []string{"p", "br", "strong", "em", "u", "span"},
		allowedAttrs: map[string][]string{
			"span": {"class"},
		},
	}
}

// Clean cleans potentially dangerous content
func (x *XSSProtector) Clean(input string) string {
	// For now, just escape everything
	// A full implementation would parse and filter HTML
	return html.EscapeString(input)
}

// CSRFProtector provides CSRF protection
type CSRFProtector struct {
	tokenLength int
}

// NewCSRFProtector creates a new CSRF protector
func NewCSRFProtector() *CSRFProtector {
	return &CSRFProtector{
		tokenLength: 32,
	}
}

// GenerateToken generates a CSRF token
func (c *CSRFProtector) GenerateToken() string {
	// This is a placeholder - real implementation would use crypto/rand
	const letters = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
	b := make([]byte, c.tokenLength)
	for i := range b {
		b[i] = letters[i%len(letters)]
	}
	return string(b)
}

// ValidateToken validates a CSRF token
func (c *CSRFProtector) ValidateToken(token string, sessionToken string) bool {
	// Simple comparison - real implementation would be more sophisticated
	return token == sessionToken && token != ""
}
