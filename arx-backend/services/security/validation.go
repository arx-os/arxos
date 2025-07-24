package security

import (
	"crypto/sha256"
	"encoding/hex"
	"fmt"
	"net/mail"
	"net/url"
	"regexp"
	"strings"
	"sync"
	"time"
	"unicode"
)

// ValidationRule represents a validation rule
type ValidationRule struct {
	ID         string                 `json:"id"`
	Name       string                 `json:"name"`
	Type       string                 `json:"type"`
	Pattern    string                 `json:"pattern,omitempty"`
	MinLength  int                    `json:"min_length,omitempty"`
	MaxLength  int                    `json:"max_length,omitempty"`
	MinValue   float64                `json:"min_value,omitempty"`
	MaxValue   float64                `json:"max_value,omitempty"`
	Required   bool                   `json:"required"`
	CustomFunc string                 `json:"custom_func,omitempty"`
	Message    string                 `json:"message"`
	Severity   string                 `json:"severity"` // error, warning, info
	CreatedAt  time.Time              `json:"created_at"`
	IsActive   bool                   `json:"is_active"`
	Metadata   map[string]interface{} `json:"metadata"`
}

// ValidationResult represents a validation result
type ValidationResult struct {
	IsValid     bool                   `json:"is_valid"`
	Errors      []ValidationError      `json:"errors"`
	Warnings    []ValidationError      `json:"warnings"`
	Info        []ValidationError      `json:"info"`
	ValidatedAt time.Time              `json:"validated_at"`
	Metadata    map[string]interface{} `json:"metadata"`
}

// ValidationError represents a validation error
type ValidationError struct {
	Field    string                 `json:"field"`
	Rule     string                 `json:"rule"`
	Message  string                 `json:"message"`
	Value    interface{}            `json:"value"`
	Severity string                 `json:"severity"`
	Line     int                    `json:"line,omitempty"`
	Column   int                    `json:"column,omitempty"`
	Metadata map[string]interface{} `json:"metadata"`
}

// ValidationService provides input validation and sanitization
type ValidationService struct {
	rules         map[string]*ValidationRule
	rulesMutex    sync.RWMutex
	patterns      map[string]*regexp.Regexp
	patternsMutex sync.RWMutex
}

// NewValidationService creates a new validation service
func NewValidationService() *ValidationService {
	vs := &ValidationService{
		rules:    make(map[string]*ValidationRule),
		patterns: make(map[string]*regexp.Regexp),
	}

	// Initialize default validation rules
	vs.initializeDefaultRules()

	return vs
}

// initializeDefaultRules sets up default validation rules
func (vs *ValidationService) initializeDefaultRules() {
	defaultRules := []*ValidationRule{
		{
			ID:        "email",
			Name:      "Email Validation",
			Type:      "email",
			Required:  true,
			Message:   "Invalid email format",
			Severity:  "error",
			IsActive:  true,
			CreatedAt: time.Now(),
		},
		{
			ID:        "password",
			Name:      "Password Validation",
			Type:      "password",
			MinLength: 8,
			MaxLength: 128,
			Required:  true,
			Message:   "Password must be between 8 and 128 characters",
			Severity:  "error",
			IsActive:  true,
			CreatedAt: time.Now(),
		},
		{
			ID:        "username",
			Name:      "Username Validation",
			Type:      "username",
			MinLength: 3,
			MaxLength: 50,
			Pattern:   `^[a-zA-Z0-9_-]+$`,
			Required:  true,
			Message:   "Username must be 3-50 characters and contain only letters, numbers, underscores, and hyphens",
			Severity:  "error",
			IsActive:  true,
			CreatedAt: time.Now(),
		},
		{
			ID:        "url",
			Name:      "URL Validation",
			Type:      "url",
			Required:  true,
			Message:   "Invalid URL format",
			Severity:  "error",
			IsActive:  true,
			CreatedAt: time.Now(),
		},
		{
			ID:        "sql_injection",
			Name:      "SQL Injection Prevention",
			Type:      "sql_injection",
			Pattern:   `(?i)(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION|--|/\*|\*/)`,
			Required:  true,
			Message:   "Potential SQL injection detected",
			Severity:  "error",
			IsActive:  true,
			CreatedAt: time.Now(),
		},
		{
			ID:        "xss",
			Name:      "XSS Prevention",
			Type:      "xss",
			Pattern:   `(?i)(<script|javascript:|vbscript:|onload=|onerror=|onclick=)`,
			Required:  true,
			Message:   "Potential XSS attack detected",
			Severity:  "error",
			IsActive:  true,
			CreatedAt: time.Now(),
		},
	}

	for _, rule := range defaultRules {
		vs.AddRule(rule)
	}
}

// AddRule adds a new validation rule
func (vs *ValidationService) AddRule(rule *ValidationRule) error {
	if rule.ID == "" {
		rule.ID = generateRuleID()
	}

	rule.CreatedAt = time.Now()

	// Compile pattern if provided
	if rule.Pattern != "" {
		pattern, err := regexp.Compile(rule.Pattern)
		if err != nil {
			return fmt.Errorf("invalid pattern: %w", err)
		}
		vs.patternsMutex.Lock()
		vs.patterns[rule.ID] = pattern
		vs.patternsMutex.Unlock()
	}

	vs.rulesMutex.Lock()
	vs.rules[rule.ID] = rule
	vs.rulesMutex.Unlock()

	return nil
}

// Validate validates data against rules
func (vs *ValidationService) Validate(data map[string]interface{}, ruleIDs []string) *ValidationResult {
	result := &ValidationResult{
		IsValid:     true,
		Errors:      make([]ValidationError, 0),
		Warnings:    make([]ValidationError, 0),
		Info:        make([]ValidationError, 0),
		ValidatedAt: time.Now(),
		Metadata:    make(map[string]interface{}),
	}

	vs.rulesMutex.RLock()
	rules := make([]*ValidationRule, 0)
	if len(ruleIDs) == 0 {
		// Apply all active rules
		for _, rule := range vs.rules {
			if rule.IsActive {
				rules = append(rules, rule)
			}
		}
	} else {
		// Apply specific rules
		for _, ruleID := range ruleIDs {
			if rule, exists := vs.rules[ruleID]; exists && rule.IsActive {
				rules = append(rules, rule)
			}
		}
	}
	vs.rulesMutex.RUnlock()

	for _, rule := range rules {
		for field, value := range data {
			if validationError := vs.validateField(field, value, rule); validationError != nil {
				switch rule.Severity {
				case "error":
					result.Errors = append(result.Errors, *validationError)
					result.IsValid = false
				case "warning":
					result.Warnings = append(result.Warnings, *validationError)
				case "info":
					result.Info = append(result.Info, *validationError)
				}
			}
		}
	}

	return result
}

// validateField validates a single field against a rule
func (vs *ValidationService) validateField(field string, value interface{}, rule *ValidationRule) *ValidationError {
	// Check if field is required
	if rule.Required && (value == nil || value == "") {
		return &ValidationError{
			Field:    field,
			Rule:     rule.ID,
			Message:  rule.Message,
			Value:    value,
			Severity: rule.Severity,
		}
	}

	// Skip validation if value is empty and not required
	if value == nil || value == "" {
		return nil
	}

	// Convert value to string for validation
	valueStr := fmt.Sprintf("%v", value)

	// Apply validation based on rule type
	switch rule.Type {
	case "email":
		if !vs.isValidEmail(valueStr) {
			return &ValidationError{
				Field:    field,
				Rule:     rule.ID,
				Message:  rule.Message,
				Value:    value,
				Severity: rule.Severity,
			}
		}
	case "password":
		if !vs.isValidPassword(valueStr, rule) {
			return &ValidationError{
				Field:    field,
				Rule:     rule.ID,
				Message:  rule.Message,
				Value:    value,
				Severity: rule.Severity,
			}
		}
	case "username":
		if !vs.isValidUsername(valueStr, rule) {
			return &ValidationError{
				Field:    field,
				Rule:     rule.ID,
				Message:  rule.Message,
				Value:    value,
				Severity: rule.Severity,
			}
		}
	case "url":
		if !vs.isValidURL(valueStr) {
			return &ValidationError{
				Field:    field,
				Rule:     rule.ID,
				Message:  rule.Message,
				Value:    value,
				Severity: rule.Severity,
			}
		}
	case "sql_injection":
		if vs.containsSQLInjection(valueStr, rule) {
			return &ValidationError{
				Field:    field,
				Rule:     rule.ID,
				Message:  rule.Message,
				Value:    value,
				Severity: rule.Severity,
			}
		}
	case "xss":
		if vs.containsXSS(valueStr, rule) {
			return &ValidationError{
				Field:    field,
				Rule:     rule.ID,
				Message:  rule.Message,
				Value:    value,
				Severity: rule.Severity,
			}
		}
	case "length":
		if !vs.isValidLength(valueStr, rule) {
			return &ValidationError{
				Field:    field,
				Rule:     rule.ID,
				Message:  rule.Message,
				Value:    value,
				Severity: rule.Severity,
			}
		}
	case "pattern":
		if !vs.matchesPattern(valueStr, rule) {
			return &ValidationError{
				Field:    field,
				Rule:     rule.ID,
				Message:  rule.Message,
				Value:    value,
				Severity: rule.Severity,
			}
		}
	}

	return nil
}

// isValidEmail validates email format
func (vs *ValidationService) isValidEmail(email string) bool {
	_, err := mail.ParseAddress(email)
	return err == nil
}

// isValidPassword validates password strength
func (vs *ValidationService) isValidPassword(password string, rule *ValidationRule) bool {
	if len(password) < rule.MinLength || len(password) > rule.MaxLength {
		return false
	}

	// Check for at least one uppercase, lowercase, digit, and special character
	var hasUpper, hasLower, hasDigit, hasSpecial bool
	for _, char := range password {
		switch {
		case unicode.IsUpper(char):
			hasUpper = true
		case unicode.IsLower(char):
			hasLower = true
		case unicode.IsDigit(char):
			hasDigit = true
		case unicode.IsPunct(char) || unicode.IsSymbol(char):
			hasSpecial = true
		}
	}

	return hasUpper && hasLower && hasDigit && hasSpecial
}

// isValidUsername validates username format
func (vs *ValidationService) isValidUsername(username string, rule *ValidationRule) bool {
	if len(username) < rule.MinLength || len(username) > rule.MaxLength {
		return false
	}

	if rule.Pattern != "" {
		vs.patternsMutex.RLock()
		pattern, exists := vs.patterns[rule.ID]
		vs.patternsMutex.RUnlock()
		if exists && !pattern.MatchString(username) {
			return false
		}
	}

	return true
}

// isValidURL validates URL format
func (vs *ValidationService) isValidURL(urlStr string) bool {
	_, err := url.ParseRequestURI(urlStr)
	return err == nil
}

// containsSQLInjection checks for SQL injection patterns
func (vs *ValidationService) containsSQLInjection(input string, rule *ValidationRule) bool {
	if rule.Pattern != "" {
		vs.patternsMutex.RLock()
		pattern, exists := vs.patterns[rule.ID]
		vs.patternsMutex.RUnlock()
		if exists && pattern.MatchString(strings.ToUpper(input)) {
			return true
		}
	}
	return false
}

// containsXSS checks for XSS attack patterns
func (vs *ValidationService) containsXSS(input string, rule *ValidationRule) bool {
	if rule.Pattern != "" {
		vs.patternsMutex.RLock()
		pattern, exists := vs.patterns[rule.ID]
		vs.patternsMutex.RUnlock()
		if exists && pattern.MatchString(strings.ToLower(input)) {
			return true
		}
	}
	return false
}

// isValidLength validates string length
func (vs *ValidationService) isValidLength(input string, rule *ValidationRule) bool {
	length := len(input)
	return length >= rule.MinLength && length <= rule.MaxLength
}

// matchesPattern validates against a regex pattern
func (vs *ValidationService) matchesPattern(input string, rule *ValidationRule) bool {
	if rule.Pattern != "" {
		vs.patternsMutex.RLock()
		pattern, exists := vs.patterns[rule.ID]
		vs.patternsMutex.RUnlock()
		if exists {
			return pattern.MatchString(input)
		}
	}
	return true
}

// SanitizeInput sanitizes input data
func (vs *ValidationService) SanitizeInput(input string) string {
	// Remove null bytes
	input = strings.ReplaceAll(input, "\x00", "")

	// Remove control characters except newline and tab
	var result strings.Builder
	for _, char := range input {
		if char == '\n' || char == '\t' || (char >= 32 && char <= 126) {
			result.WriteRune(char)
		}
	}

	return result.String()
}

// HashSensitiveData hashes sensitive data for storage
func (vs *ValidationService) HashSensitiveData(data string) string {
	hash := sha256.Sum256([]byte(data))
	return hex.EncodeToString(hash[:])
}

// GetRule retrieves a validation rule by ID
func (vs *ValidationService) GetRule(ruleID string) (*ValidationRule, error) {
	vs.rulesMutex.RLock()
	defer vs.rulesMutex.RUnlock()

	rule, exists := vs.rules[ruleID]
	if !exists {
		return nil, fmt.Errorf("rule not found: %s", ruleID)
	}

	return rule, nil
}

// ListRules returns all validation rules
func (vs *ValidationService) ListRules() []*ValidationRule {
	vs.rulesMutex.RLock()
	defer vs.rulesMutex.RUnlock()

	rules := make([]*ValidationRule, 0, len(vs.rules))
	for _, rule := range vs.rules {
		rules = append(rules, rule)
	}

	return rules
}

// UpdateRule updates a validation rule
func (vs *ValidationService) UpdateRule(ruleID string, updates map[string]interface{}) error {
	vs.rulesMutex.Lock()
	rule, exists := vs.rules[ruleID]
	if !exists {
		vs.rulesMutex.Unlock()
		return fmt.Errorf("rule not found: %s", ruleID)
	}

	// Update fields
	if name, ok := updates["name"].(string); ok {
		rule.Name = name
	}
	if message, ok := updates["message"].(string); ok {
		rule.Message = message
	}
	if severity, ok := updates["severity"].(string); ok {
		rule.Severity = severity
	}
	if isActive, ok := updates["is_active"].(bool); ok {
		rule.IsActive = isActive
	}
	if pattern, ok := updates["pattern"].(string); ok {
		rule.Pattern = pattern
		// Recompile pattern
		if pattern != "" {
			compiledPattern, err := regexp.Compile(pattern)
			if err != nil {
				vs.rulesMutex.Unlock()
				return fmt.Errorf("invalid pattern: %w", err)
			}
			vs.patterns[ruleID] = compiledPattern
		}
	}

	vs.rulesMutex.Unlock()
	return nil
}

// RemoveRule removes a validation rule
func (vs *ValidationService) RemoveRule(ruleID string) error {
	vs.rulesMutex.Lock()
	defer vs.rulesMutex.Unlock()

	if _, exists := vs.rules[ruleID]; !exists {
		return fmt.Errorf("rule not found: %s", ruleID)
	}

	delete(vs.rules, ruleID)

	// Remove compiled pattern
	vs.patternsMutex.Lock()
	delete(vs.patterns, ruleID)
	vs.patternsMutex.Unlock()

	return nil
}

// generateRuleID generates a unique rule ID
func generateRuleID() string {
	return fmt.Sprintf("rule_%d", time.Now().UnixNano())
}

// GetValidationStats returns validation statistics
func (vs *ValidationService) GetValidationStats() map[string]interface{} {
	vs.rulesMutex.RLock()
	defer vs.rulesMutex.RUnlock()

	totalRules := len(vs.rules)
	activeRules := 0
	errorRules := 0
	warningRules := 0
	infoRules := 0

	for _, rule := range vs.rules {
		if rule.IsActive {
			activeRules++
		}
		switch rule.Severity {
		case "error":
			errorRules++
		case "warning":
			warningRules++
		case "info":
			infoRules++
		}
	}

	return map[string]interface{}{
		"total_rules":   totalRules,
		"active_rules":  activeRules,
		"error_rules":   errorRules,
		"warning_rules": warningRules,
		"info_rules":    infoRules,
	}
}
