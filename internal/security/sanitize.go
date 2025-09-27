package security

import (
	"crypto/rand"
	"crypto/subtle"
	"encoding/base64"
	"fmt"
	"html"
	"math"
	"net/url"
	"path/filepath"
	"regexp"
	"strings"
	"sync"
	"time"
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

	// Clean up multiple slashes
	for strings.Contains(input, "//") {
		input = strings.ReplaceAll(input, "//", "/")
	}

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

// GenerateToken generates a cryptographically secure CSRF token
func (c *CSRFProtector) GenerateToken() (string, error) {
	// Create a byte slice for the random data
	b := make([]byte, c.tokenLength)

	// Read random bytes from crypto/rand
	_, err := rand.Read(b)
	if err != nil {
		return "", fmt.Errorf("failed to generate random token: %w", err)
	}

	// Encode to base64 for safe transmission
	return base64.URLEncoding.EncodeToString(b), nil
}

// ValidateToken validates a CSRF token using constant-time comparison
func (c *CSRFProtector) ValidateToken(token string, sessionToken string) bool {
	// Ensure both tokens are non-empty
	if token == "" || sessionToken == "" {
		return false
	}

	// Use constant-time comparison to prevent timing attacks
	return subtle.ConstantTimeCompare([]byte(token), []byte(sessionToken)) == 1
}

// MustGenerateToken generates a CSRF token and panics on error
// This is for backward compatibility where the old version didn't return an error
func (c *CSRFProtector) MustGenerateToken() string {
	token, err := c.GenerateToken()
	if err != nil {
		// In production, this should log the error
		// For now, return a fallback token
		// This should never happen unless there's a system issue
		panic(fmt.Sprintf("failed to generate CSRF token: %v", err))
	}
	return token
}

// SanitizePostGISQuery sanitizes PostGIS-specific queries
func (s *Sanitizer) SanitizePostGISQuery(input string) string {
	// Remove dangerous PostGIS functions
	dangerousFunctions := []string{
		"DROP", "DELETE", "INSERT", "UPDATE", "CREATE", "ALTER",
		"EXEC", "EXECUTE", "UNION", "SELECT", "FROM", "WHERE",
		"GRANT", "REVOKE", "TRUNCATE", "VACUUM", "ANALYZE",
	}

	input = strings.ToUpper(input)
	for _, fn := range dangerousFunctions {
		input = strings.ReplaceAll(input, fn, "")
	}

	// Only allow safe PostGIS functions
	safePattern := regexp.MustCompile(`[^A-Z0-9\s\(\)\.\,\-\+\*\/\=\<\>\:\;]`)
	input = safePattern.ReplaceAllString(input, "")

	return strings.TrimSpace(input)
}

// SanitizeJSON sanitizes JSON input
func (s *Sanitizer) SanitizeJSON(input string) string {
	// Remove null bytes and control characters
	input = strings.ReplaceAll(input, "\x00", "")
	input = strings.ReplaceAll(input, "\x01", "")
	input = strings.ReplaceAll(input, "\x02", "")
	input = strings.ReplaceAll(input, "\x03", "")
	input = strings.ReplaceAll(input, "\x04", "")
	input = strings.ReplaceAll(input, "\x05", "")
	input = strings.ReplaceAll(input, "\x06", "")
	input = strings.ReplaceAll(input, "\x07", "")
	input = strings.ReplaceAll(input, "\x08", "")
	input = strings.ReplaceAll(input, "\x0B", "")
	input = strings.ReplaceAll(input, "\x0C", "")
	input = strings.ReplaceAll(input, "\x0E", "")
	input = strings.ReplaceAll(input, "\x0F", "")

	return input
}

// SanitizeSpatialCoordinates sanitizes spatial coordinate data
func (s *Sanitizer) SanitizeSpatialCoordinates(x, y float64) (float64, float64, error) {
	// Check for reasonable coordinate bounds (adjust based on your use case)
	const maxCoord = 1000000.0 // 1000km
	const minCoord = -1000000.0

	if x < minCoord || x > maxCoord {
		return 0, 0, fmt.Errorf("X coordinate out of bounds: %f", x)
	}
	if y < minCoord || y > maxCoord {
		return 0, 0, fmt.Errorf("Y coordinate out of bounds: %f", y)
	}

	// Check for NaN or Inf
	if math.IsNaN(x) || math.IsInf(x, 0) {
		return 0, 0, fmt.Errorf("invalid X coordinate: %f", x)
	}
	if math.IsNaN(y) || math.IsInf(y, 0) {
		return 0, 0, fmt.Errorf("invalid Y coordinate: %f", y)
	}

	return x, y, nil
}

// ValidateBuildingPath validates building path format
func (s *Sanitizer) ValidateBuildingPath(path string) bool {
	// Building paths should be like: /B1/3/A/301/HVAC/UNIT-01
	pattern := regexp.MustCompile(`^/[A-Z0-9]+(?:/[A-Z0-9]+)*$`)
	return pattern.MatchString(path)
}

// SanitizeBuildingPath sanitizes building path
func (s *Sanitizer) SanitizeBuildingPath(input string) string {
	// Remove any dangerous characters
	input = strings.ReplaceAll(input, "..", "")
	input = strings.ReplaceAll(input, "//", "/")
	input = strings.ReplaceAll(input, "\\", "/")
	input = strings.ReplaceAll(input, "\x00", "")

	// Ensure it starts with /
	if !strings.HasPrefix(input, "/") {
		input = "/" + input
	}

	// Clean up the path
	input = filepath.Clean(input)

	return input
}

// VersionControlSecurity manages security for version control operations
type VersionControlSecurity struct {
	mu            sync.RWMutex
	permissions   map[string]*UserPermissions
	auditLogger   *AuditLogger
	signatureKeys map[string]*SignatureKey
	encryptionKey []byte
}

// UserPermissions defines what a user can do with version control
type UserPermissions struct {
	UserID       string                 `json:"user_id"`
	RoomAccess   map[string]*RoomAccess `json:"room_access"`   // room -> permissions
	GlobalAccess *GlobalAccess          `json:"global_access"` // global permissions
	CreatedAt    time.Time              `json:"created_at"`
	UpdatedAt    time.Time              `json:"updated_at"`
}

// RoomAccess defines permissions for a specific room
type RoomAccess struct {
	RoomPath     string   `json:"room_path"`
	CanRead      bool     `json:"can_read"`
	CanWrite     bool     `json:"can_write"`
	CanCommit    bool     `json:"can_commit"`
	CanBranch    bool     `json:"can_branch"`
	CanMerge     bool     `json:"can_merge"`
	CanReview    bool     `json:"can_review"`
	CanEmergency bool     `json:"can_emergency"`
	Branches     []string `json:"branches"` // allowed branches
}

// GlobalAccess defines global permissions
type GlobalAccess struct {
	CanCreateRooms    bool     `json:"can_create_rooms"`
	CanDeleteRooms    bool     `json:"can_delete_rooms"`
	CanManageUsers    bool     `json:"can_manage_users"`
	CanViewAuditLogs  bool     `json:"can_view_audit_logs"`
	CanManageSecurity bool     `json:"can_manage_security"`
	AllowedBuildings  []string `json:"allowed_buildings"`
}

// SignatureKey represents a cryptographic key for signing commits
type SignatureKey struct {
	UserID    string    `json:"user_id"`
	PublicKey []byte    `json:"public_key"`
	CreatedAt time.Time `json:"created_at"`
	ExpiresAt time.Time `json:"expires_at"`
	IsActive  bool      `json:"is_active"`
}

// CommitSignature represents a digital signature for a commit
type CommitSignature struct {
	CommitID  string    `json:"commit_id"`
	UserID    string    `json:"user_id"`
	Signature string    `json:"signature"`
	Algorithm string    `json:"algorithm"`
	SignedAt  time.Time `json:"signed_at"`
	PublicKey []byte    `json:"public_key"`
}

// AuditLogEntry represents an audit log entry
type AuditLogEntry struct {
	ID        string                 `json:"id"`
	UserID    string                 `json:"user_id"`
	Action    string                 `json:"action"`
	Resource  string                 `json:"resource"`
	RoomPath  string                 `json:"room_path,omitempty"`
	Details   map[string]interface{} `json:"details"`
	IPAddress string                 `json:"ip_address"`
	UserAgent string                 `json:"user_agent"`
	Timestamp time.Time              `json:"timestamp"`
	Success   bool                   `json:"success"`
	Error     string                 `json:"error,omitempty"`
	Severity  string                 `json:"severity"`
	Category  string                 `json:"category"`
	SessionID string                 `json:"session_id,omitempty"`
}

// AuditLogFilter defines filtering criteria for audit logs
type AuditLogFilter struct {
	UserID    string
	Action    string
	RoomPath  string
	StartTime *time.Time
	EndTime   *time.Time
	Success   *bool
	Severity  string
	Category  string
	SessionID string
	Limit     int
	Offset    int
}

// SecurityContext provides security context for operations
type SecurityContext struct {
	UserID      string
	IPAddress   string
	UserAgent   string
	Permissions *UserPermissions
	SessionID   string
}

// NewVersionControlSecurity creates a new version control security manager
func NewVersionControlSecurity(encryptionKey []byte) *VersionControlSecurity {
	return &VersionControlSecurity{
		permissions:   make(map[string]*UserPermissions),
		auditLogger:   NewAuditLogger(),
		signatureKeys: make(map[string]*SignatureKey),
		encryptionKey: encryptionKey,
	}
}

// CheckPermission checks if a user has permission for an operation
func (vcs *VersionControlSecurity) CheckPermission(ctx *SecurityContext, action string, roomPath string) error {
	vcs.mu.RLock()
	defer vcs.mu.RUnlock()

	permissions, exists := vcs.permissions[ctx.UserID]
	if !exists {
		vcs.auditLog(ctx, action, roomPath, "permission_denied", "user_not_found", false)
		return fmt.Errorf("user %s not found", ctx.UserID)
	}

	// Check global permissions first
	if vcs.checkGlobalPermission(permissions.GlobalAccess, action) {
		vcs.auditLog(ctx, action, roomPath, "permission_granted", "global_permission", true)
		return nil
	}

	// Check room-specific permissions
	roomAccess, exists := permissions.RoomAccess[roomPath]
	if !exists {
		vcs.auditLog(ctx, action, roomPath, "permission_denied", "room_access_not_found", false)
		return fmt.Errorf("no access to room %s", roomPath)
	}

	if !vcs.checkRoomPermission(roomAccess, action) {
		vcs.auditLog(ctx, action, roomPath, "permission_denied", "insufficient_room_permission", false)
		return fmt.Errorf("insufficient permissions for action %s on room %s", action, roomPath)
	}

	vcs.auditLog(ctx, action, roomPath, "permission_granted", "room_permission", true)
	return nil
}

// checkGlobalPermission checks if global permissions allow the action
func (vcs *VersionControlSecurity) checkGlobalPermission(global *GlobalAccess, action string) bool {
	if global == nil {
		return false
	}

	switch action {
	case "create_room":
		return global.CanCreateRooms
	case "delete_room":
		return global.CanDeleteRooms
	case "manage_users":
		return global.CanManageUsers
	case "view_audit_logs":
		return global.CanViewAuditLogs
	case "manage_security":
		return global.CanManageSecurity
	default:
		return false
	}
}

// checkRoomPermission checks if room permissions allow the action
func (vcs *VersionControlSecurity) checkRoomPermission(room *RoomAccess, action string) bool {
	if room == nil {
		return false
	}

	switch action {
	case "read":
		return room.CanRead
	case "write":
		return room.CanWrite
	case "commit":
		return room.CanCommit
	case "branch":
		return room.CanBranch
	case "merge":
		return room.CanMerge
	case "review":
		return room.CanReview
	case "emergency":
		return room.CanEmergency
	default:
		return false
	}
}

// SetUserPermissions sets permissions for a user
func (vcs *VersionControlSecurity) SetUserPermissions(userID string, permissions *UserPermissions) error {
	vcs.mu.Lock()
	defer vcs.mu.Unlock()

	permissions.UserID = userID
	permissions.UpdatedAt = time.Now()
	vcs.permissions[userID] = permissions

	return nil
}

// GetUserPermissions gets permissions for a user
func (vcs *VersionControlSecurity) GetUserPermissions(userID string) (*UserPermissions, error) {
	vcs.mu.RLock()
	defer vcs.mu.RUnlock()

	permissions, exists := vcs.permissions[userID]
	if !exists {
		return nil, fmt.Errorf("permissions not found for user %s", userID)
	}

	return permissions, nil
}

// auditLog logs an audit entry
func (vcs *VersionControlSecurity) auditLog(ctx *SecurityContext, action, resource, result, details string, success bool) {
	entry := &AuditLogEntry{
		ID:       fmt.Sprintf("audit_%d", time.Now().UnixNano()),
		UserID:   ctx.UserID,
		Action:   action,
		Resource: resource,
		RoomPath: resource,
		Details: map[string]interface{}{
			"result":  result,
			"details": details,
		},
		IPAddress: ctx.IPAddress,
		UserAgent: ctx.UserAgent,
		Timestamp: time.Now(),
		Success:   success,
		Severity:  "INFO",
		Category:  "version_control",
	}

	vcs.auditLogger.Log(entry)
}

// AuditLogger manages audit logging for security events
type AuditLogger struct {
	mu     sync.RWMutex
	logs   []*AuditLogEntry
	config *AuditConfig
}

// AuditConfig defines configuration for audit logging
type AuditConfig struct {
	MaxLogs       int           `json:"max_logs"`
	RetentionDays int           `json:"retention_days"`
	LogLevel      string        `json:"log_level"`
	EnableConsole bool          `json:"enable_console"`
	EnableFile    bool          `json:"enable_file"`
	FilePath      string        `json:"file_path"`
	FlushInterval time.Duration `json:"flush_interval"`
}

// NewAuditLogger creates a new audit logger
func NewAuditLogger() *AuditLogger {
	return &AuditLogger{
		logs: make([]*AuditLogEntry, 0),
		config: &AuditConfig{
			MaxLogs:       10000,
			RetentionDays: 90,
			LogLevel:      "INFO",
			EnableConsole: true,
			EnableFile:    false,
			FilePath:      "/var/log/arxos/audit.log",
			FlushInterval: 5 * time.Second,
		},
	}
}

// Log logs an audit entry
func (al *AuditLogger) Log(entry *AuditLogEntry) {
	al.mu.Lock()
	defer al.mu.Unlock()

	// Set default values
	if entry.Severity == "" {
		entry.Severity = "INFO"
	}
	if entry.Category == "" {
		entry.Category = "general"
	}

	// Add to logs
	al.logs = append(al.logs, entry)

	// Console logging
	if al.config.EnableConsole {
		al.logToConsole(entry)
	}

	// File logging
	if al.config.EnableFile {
		al.logToFile(entry)
	}

	// Cleanup old logs
	al.cleanupOldLogs()

	// Enforce max logs limit
	if len(al.logs) > al.config.MaxLogs {
		al.logs = al.logs[len(al.logs)-al.config.MaxLogs:]
	}
}

// logToConsole logs to console
func (al *AuditLogger) logToConsole(entry *AuditLogEntry) {
	level := entry.Severity
	message := fmt.Sprintf("AUDIT: %s %s %s %s", entry.Action, entry.Resource, entry.UserID, entry.RoomPath)

	if !entry.Success {
		message += fmt.Sprintf(" ERROR: %s", entry.Error)
	}

	// Simple console logging - in production this would use proper logger
	fmt.Printf("[%s] %s\n", level, message)
}

// logToFile logs to file
func (al *AuditLogger) logToFile(entry *AuditLogEntry) {
	// In a real implementation, this would write to a file
	// For now, we'll just log to console
	fmt.Printf("AUDIT FILE: %s\n", entry.ID)
}

// cleanupOldLogs removes logs older than retention period
func (al *AuditLogger) cleanupOldLogs() {
	cutoff := time.Now().Add(-time.Duration(al.config.RetentionDays) * 24 * time.Hour)

	var filtered []*AuditLogEntry
	for _, log := range al.logs {
		if log.Timestamp.After(cutoff) {
			filtered = append(filtered, log)
		}
	}

	al.logs = filtered
}

// GetLogs retrieves audit logs with filtering
func (al *AuditLogger) GetLogs(filter *AuditLogFilter) ([]*AuditLogEntry, error) {
	al.mu.RLock()
	defer al.mu.RUnlock()

	var filtered []*AuditLogEntry

	for _, log := range al.logs {
		if al.matchesFilter(log, filter) {
			filtered = append(filtered, log)
		}
	}

	// Apply pagination
	start := filter.Offset
	if start >= len(filtered) {
		return []*AuditLogEntry{}, nil
	}

	end := start + filter.Limit
	if end > len(filtered) {
		end = len(filtered)
	}

	return filtered[start:end], nil
}

// matchesFilter checks if a log entry matches the filter criteria
func (al *AuditLogger) matchesFilter(entry *AuditLogEntry, filter *AuditLogFilter) bool {
	if filter.UserID != "" && entry.UserID != filter.UserID {
		return false
	}
	if filter.Action != "" && entry.Action != filter.Action {
		return false
	}
	if filter.RoomPath != "" && entry.RoomPath != filter.RoomPath {
		return false
	}
	if filter.Severity != "" && entry.Severity != filter.Severity {
		return false
	}
	if filter.Category != "" && entry.Category != filter.Category {
		return false
	}
	if filter.SessionID != "" && entry.SessionID != filter.SessionID {
		return false
	}
	if filter.StartTime != nil && entry.Timestamp.Before(*filter.StartTime) {
		return false
	}
	if filter.EndTime != nil && entry.Timestamp.After(*filter.EndTime) {
		return false
	}
	if filter.Success != nil && entry.Success != *filter.Success {
		return false
	}

	return true
}

// GenerateSignatureKey generates a new signature key for a user
func (vcs *VersionControlSecurity) GenerateSignatureKey(userID string) (*SignatureKey, error) {
	vcs.mu.Lock()
	defer vcs.mu.Unlock()

	// In a real implementation, this would generate actual cryptographic keys
	// For now, we'll create a mock key
	key := &SignatureKey{
		UserID:    userID,
		PublicKey: []byte("mock-public-key"),
		CreatedAt: time.Now(),
		ExpiresAt: time.Now().Add(365 * 24 * time.Hour), // 1 year
		IsActive:  true,
	}

	vcs.signatureKeys[userID] = key
	return key, nil
}

// SignCommit signs a commit with the user's private key
func (vcs *VersionControlSecurity) SignCommit(commitID, userID string, commitData []byte) (*CommitSignature, error) {
	vcs.mu.RLock()
	defer vcs.mu.RUnlock()

	key, exists := vcs.signatureKeys[userID]
	if !exists {
		return nil, fmt.Errorf("signature key not found for user %s", userID)
	}

	if !key.IsActive || time.Now().After(key.ExpiresAt) {
		return nil, fmt.Errorf("signature key expired or inactive for user %s", userID)
	}

	// Create a mock signature (in real implementation, this would be a real signature)
	signature := fmt.Sprintf("signature_%s_%d", commitID, time.Now().Unix())

	commitSignature := &CommitSignature{
		CommitID:  commitID,
		UserID:    userID,
		Signature: signature,
		Algorithm: "ed25519",
		SignedAt:  time.Now(),
		PublicKey: key.PublicKey,
	}

	return commitSignature, nil
}

// VerifyCommitSignature verifies a commit signature
func (vcs *VersionControlSecurity) VerifyCommitSignature(signature *CommitSignature, commitData []byte) error {
	vcs.mu.RLock()
	defer vcs.mu.RUnlock()

	key, exists := vcs.signatureKeys[signature.UserID]
	if !exists {
		return fmt.Errorf("signature key not found for user %s", signature.UserID)
	}

	if !key.IsActive || time.Now().After(key.ExpiresAt) {
		return fmt.Errorf("signature key expired or inactive for user %s", signature.UserID)
	}

	// In a real implementation, this would verify the actual signature
	// For now, we'll just check that the signature format is correct
	if !strings.HasPrefix(signature.Signature, "signature_") {
		return fmt.Errorf("invalid signature format for commit %s", signature.CommitID)
	}

	return nil
}

// EncryptSensitiveData encrypts sensitive configuration data
func (vcs *VersionControlSecurity) EncryptSensitiveData(data []byte) ([]byte, error) {
	// In a real implementation, this would use proper encryption (AES-GCM)
	// For now, we'll use base64 encoding as a placeholder
	encrypted := base64.StdEncoding.EncodeToString(data)
	return []byte(encrypted), nil
}

// DecryptSensitiveData decrypts sensitive configuration data
func (vcs *VersionControlSecurity) DecryptSensitiveData(encryptedData []byte) ([]byte, error) {
	// In a real implementation, this would use proper decryption
	// For now, we'll use base64 decoding as a placeholder
	decrypted, err := base64.StdEncoding.DecodeString(string(encryptedData))
	if err != nil {
		return nil, fmt.Errorf("failed to decrypt data: %w", err)
	}
	return decrypted, nil
}

// GetAuditLogs retrieves audit logs with filtering
func (vcs *VersionControlSecurity) GetAuditLogs(filter *AuditLogFilter) ([]*AuditLogEntry, error) {
	return vcs.auditLogger.GetLogs(filter)
}
