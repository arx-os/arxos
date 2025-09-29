package compliance

import (
	"context"
	"fmt"
	"net/http"
	"time"

	"github.com/arx-os/arxos/internal/common/logger"
)

// AuditEvent represents an audit event
type AuditEvent struct {
	ID         string                 `json:"id"`
	Timestamp  time.Time              `json:"timestamp"`
	UserID     string                 `json:"user_id"`
	SessionID  string                 `json:"session_id"`
	Action     string                 `json:"action"`
	Resource   string                 `json:"resource"`
	ResourceID string                 `json:"resource_id"`
	Result     AuditResult            `json:"result"`
	IPAddress  string                 `json:"ip_address"`
	UserAgent  string                 `json:"user_agent"`
	Metadata   map[string]interface{} `json:"metadata"`
	RiskLevel  RiskLevel              `json:"risk_level"`
	Compliance []ComplianceStandard   `json:"compliance"`
}

// AuditResult represents the result of an audit event
type AuditResult string

const (
	AuditResultSuccess AuditResult = "success"
	AuditResultFailure AuditResult = "failure"
	AuditResultDenied  AuditResult = "denied"
)

// RiskLevel represents the risk level of an audit event
type RiskLevel string

const (
	RiskLevelLow      RiskLevel = "low"
	RiskLevelMedium   RiskLevel = "medium"
	RiskLevelHigh     RiskLevel = "high"
	RiskLevelCritical RiskLevel = "critical"
)

// ComplianceStandard represents a compliance standard
type ComplianceStandard string

const (
	ComplianceSOC2     ComplianceStandard = "SOC2"
	ComplianceGDPR     ComplianceStandard = "GDPR"
	ComplianceHIPAA    ComplianceStandard = "HIPAA"
	ComplianceISO27001 ComplianceStandard = "ISO27001"
	CompliancePCI      ComplianceStandard = "PCI"
)

// AuditLogger provides audit logging capabilities
type AuditLogger struct {
	config     *AuditConfig
	events     chan *AuditEvent
	processors []AuditProcessor
}

// AuditConfig holds audit configuration
type AuditConfig struct {
	Enabled       bool                 `json:"enabled"`
	BufferSize    int                  `json:"buffer_size"`
	FlushInterval time.Duration        `json:"flush_interval"`
	Retention     time.Duration        `json:"retention"`
	Standards     []ComplianceStandard `json:"standards"`
}

// AuditProcessor processes audit events
type AuditProcessor interface {
	Process(ctx context.Context, event *AuditEvent) error
}

// NewAuditLogger creates a new audit logger
func NewAuditLogger(config *AuditConfig) *AuditLogger {
	al := &AuditLogger{
		config:     config,
		events:     make(chan *AuditEvent, config.BufferSize),
		processors: make([]AuditProcessor, 0),
	}

	// Start event processing
	go al.processEvents()

	return al
}

// LogEvent logs an audit event
func (al *AuditLogger) LogEvent(ctx context.Context, event *AuditEvent) error {
	if !al.config.Enabled {
		return nil
	}

	// Set default values
	if event.ID == "" {
		event.ID = generateEventID()
	}
	if event.Timestamp.IsZero() {
		event.Timestamp = time.Now()
	}
	if event.RiskLevel == "" {
		event.RiskLevel = al.calculateRiskLevel(event)
	}
	if event.Compliance == nil {
		event.Compliance = al.determineComplianceStandards(event)
	}

	// Send event to processing channel
	select {
	case al.events <- event:
		return nil
	default:
		return fmt.Errorf("audit event buffer full")
	}
}

// AddProcessor adds an audit processor
func (al *AuditLogger) AddProcessor(processor AuditProcessor) {
	al.processors = append(al.processors, processor)
}

// processEvents processes audit events
func (al *AuditLogger) processEvents() {
	ticker := time.NewTicker(al.config.FlushInterval)
	defer ticker.Stop()

	for {
		select {
		case event := <-al.events:
			al.processEvent(event)
		case <-ticker.C:
			// Periodic flush
			al.flushEvents()
		}
	}
}

// processEvent processes a single audit event
func (al *AuditLogger) processEvent(event *AuditEvent) {
	ctx := context.Background()

	for _, processor := range al.processors {
		if err := processor.Process(ctx, event); err != nil {
			logger.Error("Failed to process audit event: %v", err)
		}
	}
}

// flushEvents flushes pending events
func (al *AuditLogger) flushEvents() {
	// Implementation for flushing events to persistent storage
	logger.Debug("Flushing audit events")
}

// calculateRiskLevel calculates the risk level for an event
func (al *AuditLogger) calculateRiskLevel(event *AuditEvent) RiskLevel {
	// Simple risk calculation based on action and result
	switch event.Action {
	case "login", "logout":
		if event.Result == AuditResultSuccess {
			return RiskLevelLow
		}
		return RiskLevelMedium
	case "create", "update", "delete":
		if event.Result == AuditResultSuccess {
			return RiskLevelMedium
		}
		return RiskLevelHigh
	case "admin", "privileged":
		return RiskLevelHigh
	case "security", "authentication":
		if event.Result == AuditResultFailure {
			return RiskLevelCritical
		}
		return RiskLevelHigh
	default:
		return RiskLevelLow
	}
}

// determineComplianceStandards determines applicable compliance standards
func (al *AuditLogger) determineComplianceStandards(event *AuditEvent) []ComplianceStandard {
	standards := make([]ComplianceStandard, 0)

	// Always include configured standards
	for _, standard := range al.config.Standards {
		standards = append(standards, standard)
	}

	// Add standards based on event type
	switch event.Action {
	case "login", "logout", "authentication":
		standards = append(standards, ComplianceSOC2, ComplianceISO27001)
	case "data_access", "data_modification":
		standards = append(standards, ComplianceGDPR, ComplianceHIPAA)
	case "payment", "financial":
		standards = append(standards, CompliancePCI)
	}

	return standards
}

// DatabaseAuditProcessor processes audit events to database
type DatabaseAuditProcessor struct {
	db Database
}

// Database interface for audit storage
type Database interface {
	StoreAuditEvent(ctx context.Context, event *AuditEvent) error
	QueryAuditEvents(ctx context.Context, query *AuditQuery) ([]*AuditEvent, error)
}

// NewDatabaseAuditProcessor creates a new database audit processor
func NewDatabaseAuditProcessor(db Database) *DatabaseAuditProcessor {
	return &DatabaseAuditProcessor{
		db: db,
	}
}

// Process processes an audit event to database
func (dap *DatabaseAuditProcessor) Process(ctx context.Context, event *AuditEvent) error {
	return dap.db.StoreAuditEvent(ctx, event)
}

// AuditQuery represents a query for audit events
type AuditQuery struct {
	UserID    string                 `json:"user_id,omitempty"`
	Action    string                 `json:"action,omitempty"`
	Resource  string                 `json:"resource,omitempty"`
	Result    AuditResult            `json:"result,omitempty"`
	RiskLevel RiskLevel              `json:"risk_level,omitempty"`
	StartTime time.Time              `json:"start_time,omitempty"`
	EndTime   time.Time              `json:"end_time,omitempty"`
	Limit     int                    `json:"limit,omitempty"`
	Offset    int                    `json:"offset,omitempty"`
	Metadata  map[string]interface{} `json:"metadata,omitempty"`
}

// FileAuditProcessor processes audit events to file
type FileAuditProcessor struct {
	filePath string
}

// NewFileAuditProcessor creates a new file audit processor
func NewFileAuditProcessor(filePath string) *FileAuditProcessor {
	return &FileAuditProcessor{
		filePath: filePath,
	}
}

// Process processes an audit event to file
func (fap *FileAuditProcessor) Process(ctx context.Context, event *AuditEvent) error {
	// Implementation for writing to audit log file
	logger.Debug("Writing audit event to file: %s", fap.filePath)
	return nil
}

// ComplianceChecker provides compliance checking capabilities
type ComplianceChecker struct {
	standards map[ComplianceStandard]*ComplianceRule
}

// ComplianceRule represents a compliance rule
type ComplianceRule struct {
	Standard    ComplianceStandard     `json:"standard"`
	Name        string                 `json:"name"`
	Description string                 `json:"description"`
	Severity    RiskLevel              `json:"severity"`
	Enabled     bool                   `json:"enabled"`
	Check       func(*AuditEvent) bool `json:"-"`
}

// NewComplianceChecker creates a new compliance checker
func NewComplianceChecker() *ComplianceChecker {
	cc := &ComplianceChecker{
		standards: make(map[ComplianceStandard]*ComplianceRule),
	}

	// Register default compliance rules
	cc.registerDefaultRules()

	return cc
}

// CheckCompliance checks compliance for an audit event
func (cc *ComplianceChecker) CheckCompliance(event *AuditEvent) []ComplianceViolation {
	violations := make([]ComplianceViolation, 0)

	for _, standard := range event.Compliance {
		if rule, exists := cc.standards[standard]; exists && rule.Enabled {
			if !rule.Check(event) {
				violation := ComplianceViolation{
					Standard:    standard,
					Rule:        rule.Name,
					Description: rule.Description,
					Severity:    rule.Severity,
					Event:       event,
					Timestamp:   time.Now(),
				}
				violations = append(violations, violation)
			}
		}
	}

	return violations
}

// ComplianceViolation represents a compliance violation
type ComplianceViolation struct {
	Standard    ComplianceStandard `json:"standard"`
	Rule        string             `json:"rule"`
	Description string             `json:"description"`
	Severity    RiskLevel          `json:"severity"`
	Event       *AuditEvent        `json:"event"`
	Timestamp   time.Time          `json:"timestamp"`
}

// registerDefaultRules registers default compliance rules
func (cc *ComplianceChecker) registerDefaultRules() {
	// SOC2 rules
	cc.standards[ComplianceSOC2] = &ComplianceRule{
		Standard:    ComplianceSOC2,
		Name:        "Authentication Required",
		Description: "All administrative actions must be authenticated",
		Severity:    RiskLevelHigh,
		Enabled:     true,
		Check: func(event *AuditEvent) bool {
			return event.UserID != "" || event.Action == "public_access"
		},
	}

	// GDPR rules
	cc.standards[ComplianceGDPR] = &ComplianceRule{
		Standard:    ComplianceGDPR,
		Name:        "Data Access Logging",
		Description: "All personal data access must be logged",
		Severity:    RiskLevelCritical,
		Enabled:     true,
		Check: func(event *AuditEvent) bool {
			return event.Action != "data_access" || event.UserID != ""
		},
	}

	// HIPAA rules
	cc.standards[ComplianceHIPAA] = &ComplianceRule{
		Standard:    ComplianceHIPAA,
		Name:        "Health Data Protection",
		Description: "Health data access must be authorized and logged",
		Severity:    RiskLevelCritical,
		Enabled:     true,
		Check: func(event *AuditEvent) bool {
			return event.Resource != "health_data" || event.UserID != ""
		},
	}
}

// AuditMiddleware provides HTTP audit middleware
type AuditMiddleware struct {
	auditLogger *AuditLogger
}

// NewAuditMiddleware creates a new audit middleware
func NewAuditMiddleware(auditLogger *AuditLogger) *AuditMiddleware {
	return &AuditMiddleware{
		auditLogger: auditLogger,
	}
}

// Middleware returns the HTTP middleware function
func (am *AuditMiddleware) Middleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		// Extract user information from context
		userID := ""
		if user := r.Context().Value("user"); user != nil {
			if u, ok := user.(map[string]interface{}); ok {
				if id, exists := u["id"]; exists {
					userID = id.(string)
				}
			}
		}

		// Create audit event
		event := &AuditEvent{
			UserID:    userID,
			Action:    fmt.Sprintf("HTTP %s", r.Method),
			Resource:  r.URL.Path,
			IPAddress: r.RemoteAddr,
			UserAgent: r.UserAgent(),
			Metadata: map[string]interface{}{
				"method":  r.Method,
				"url":     r.URL.String(),
				"headers": r.Header,
				"query":   r.URL.Query(),
			},
		}

		// Log request start
		am.auditLogger.LogEvent(r.Context(), event)

		// Continue with request
		next.ServeHTTP(w, r)

		// Log request completion
		event.Result = AuditResultSuccess
		am.auditLogger.LogEvent(r.Context(), event)
	})
}

// Helper function to generate event ID
func generateEventID() string {
	return fmt.Sprintf("audit_%d", time.Now().UnixNano())
}
