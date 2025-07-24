package security

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"sync"
	"time"
)

// AuditLevel represents audit log levels
type AuditLevel string

const (
	LevelInfo     AuditLevel = "info"
	LevelWarning  AuditLevel = "warning"
	LevelError    AuditLevel = "error"
	LevelCritical AuditLevel = "critical"
)

// AuditEvent represents an audit event
type AuditEvent struct {
	ID            string                 `json:"id"`
	Timestamp     time.Time              `json:"timestamp"`
	Level         AuditLevel             `json:"level"`
	Category      string                 `json:"category"`
	Action        string                 `json:"action"`
	UserID        string                 `json:"user_id,omitempty"`
	SessionID     string                 `json:"session_id,omitempty"`
	IPAddress     string                 `json:"ip_address,omitempty"`
	UserAgent     string                 `json:"user_agent,omitempty"`
	Resource      string                 `json:"resource,omitempty"`
	Details       map[string]interface{} `json:"details"`
	Message       string                 `json:"message"`
	CorrelationID string                 `json:"correlation_id,omitempty"`
	Metadata      map[string]interface{} `json:"metadata"`
}

// ComplianceRecord represents a compliance record
type ComplianceRecord struct {
	ID           string                 `json:"id"`
	Standard     string                 `json:"standard"` // GDPR, HIPAA, SOC2, etc.
	Requirement  string                 `json:"requirement"`
	Status       string                 `json:"status"` // compliant, non-compliant, pending
	Evidence     string                 `json:"evidence"`
	AuditEventID string                 `json:"audit_event_id"`
	CreatedAt    time.Time              `json:"created_at"`
	UpdatedAt    time.Time              `json:"updated_at"`
	Metadata     map[string]interface{} `json:"metadata"`
}

// AuditService provides audit logging and compliance tracking
type AuditService struct {
	logDir          string
	logFile         *os.File
	logMutex        sync.Mutex
	events          []*AuditEvent
	eventsMutex     sync.RWMutex
	maxEvents       int
	complianceDB    map[string]*ComplianceRecord
	complianceMutex sync.RWMutex
	handlers        []AuditEventHandler
	handlersMutex   sync.RWMutex
}

// AuditEventHandler defines the interface for audit event handlers
type AuditEventHandler interface {
	HandleAuditEvent(event *AuditEvent) error
}

// NewAuditService creates a new audit service
func NewAuditService(logDir string) (*AuditService, error) {
	if err := os.MkdirAll(logDir, 0755); err != nil {
		return nil, fmt.Errorf("failed to create log directory: %w", err)
	}

	logFile, err := os.OpenFile(
		filepath.Join(logDir, "audit.log"),
		os.O_APPEND|os.O_CREATE|os.O_WRONLY,
		0644,
	)
	if err != nil {
		return nil, fmt.Errorf("failed to open audit log file: %w", err)
	}

	return &AuditService{
		logDir:       logDir,
		logFile:      logFile,
		events:       make([]*AuditEvent, 0),
		maxEvents:    10000, // Keep last 10k events in memory
		complianceDB: make(map[string]*ComplianceRecord),
		handlers:     make([]AuditEventHandler, 0),
	}, nil
}

// LogEvent logs an audit event
func (as *AuditService) LogEvent(level AuditLevel, category, action, message string, details map[string]interface{}) *AuditEvent {
	event := &AuditEvent{
		ID:        generateEventID(),
		Timestamp: time.Now(),
		Level:     level,
		Category:  category,
		Action:    action,
		Message:   message,
		Details:   details,
		Metadata:  make(map[string]interface{}),
	}

	// Add to memory
	as.eventsMutex.Lock()
	as.events = append(as.events, event)
	if len(as.events) > as.maxEvents {
		as.events = as.events[1:] // Remove oldest event
	}
	as.eventsMutex.Unlock()

	// Write to file
	as.writeEventToFile(event)

	// Trigger handlers
	as.triggerHandlers(event)

	return event
}

// LogSecurityEvent logs a security-related audit event
func (as *AuditService) LogSecurityEvent(level AuditLevel, action, message string, userID, sessionID, ipAddress string, details map[string]interface{}) *AuditEvent {
	event := as.LogEvent(level, "security", action, message, details)
	event.UserID = userID
	event.SessionID = sessionID
	event.IPAddress = ipAddress
	return event
}

// LogAccessEvent logs an access-related audit event
func (as *AuditService) LogAccessEvent(level AuditLevel, action, resource, message string, userID, sessionID, ipAddress string, details map[string]interface{}) *AuditEvent {
	event := as.LogEvent(level, "access", action, message, details)
	event.UserID = userID
	event.SessionID = sessionID
	event.IPAddress = ipAddress
	event.Resource = resource
	return event
}

// LogDataEvent logs a data-related audit event
func (as *AuditService) LogDataEvent(level AuditLevel, action, message string, userID string, dataType string, recordCount int, details map[string]interface{}) *AuditEvent {
	if details == nil {
		details = make(map[string]interface{})
	}
	details["data_type"] = dataType
	details["record_count"] = recordCount

	event := as.LogEvent(level, "data", action, message, details)
	event.UserID = userID
	return event
}

// LogPolicyEvent logs a policy-related audit event
func (as *AuditService) LogPolicyEvent(eventType, policyID string, details map[string]interface{}) *AuditEvent {
	message := fmt.Sprintf("Policy event: %s", eventType)
	if details == nil {
		details = make(map[string]interface{})
	}
	details["policy_id"] = policyID

	event := as.LogEvent(LevelInfo, "policy", eventType, message, details)
	return event
}

// LogAccessRequest logs an access request for audit
func (as *AuditService) LogAccessRequest(request *AccessRequest, decision *AccessDecision) *AuditEvent {
	details := map[string]interface{}{
		"request_id":   request.ID,
		"resource_id":  request.ResourceID,
		"action":       request.Action,
		"granted":      decision.Granted,
		"reason":       decision.Reason,
		"policy_id":    decision.PolicyID,
		"evaluated_at": decision.EvaluatedAt,
	}

	level := LevelInfo
	if !decision.Granted {
		level = LevelWarning
	}

	event := as.LogEvent(level, "access_control", "access_request",
		fmt.Sprintf("Access %s for user %s to resource %s",
			decision.Granted, request.UserID, request.ResourceID), details)

	event.UserID = request.UserID
	event.SessionID = request.SessionID
	event.IPAddress = request.IPAddress
	event.Resource = request.ResourceID
	event.CorrelationID = request.ID

	return event
}

// writeEventToFile writes an audit event to the log file
func (as *AuditService) writeEventToFile(event *AuditEvent) {
	as.logMutex.Lock()
	defer as.logMutex.Unlock()

	eventJSON, err := json.Marshal(event)
	if err != nil {
		// Log error to stderr since we can't write to audit log
		fmt.Fprintf(os.Stderr, "Failed to marshal audit event: %v\n", err)
		return
	}

	if _, err := as.logFile.Write(append(eventJSON, '\n')); err != nil {
		fmt.Fprintf(os.Stderr, "Failed to write audit event: %v\n", err)
	}

	// Sync to ensure data is written to disk
	as.logFile.Sync()
}

// triggerHandlers triggers all registered audit event handlers
func (as *AuditService) triggerHandlers(event *AuditEvent) {
	as.handlersMutex.RLock()
	handlers := make([]AuditEventHandler, len(as.handlers))
	copy(handlers, as.handlers)
	as.handlersMutex.RUnlock()

	for _, handler := range handlers {
		go func(h AuditEventHandler) {
			if err := h.HandleAuditEvent(event); err != nil {
				fmt.Fprintf(os.Stderr, "Audit handler error: %v\n", err)
			}
		}(handler)
	}
}

// AddHandler adds an audit event handler
func (as *AuditService) AddHandler(handler AuditEventHandler) {
	as.handlersMutex.Lock()
	as.handlers = append(as.handlers, handler)
	as.handlersMutex.Unlock()
}

// GetEvents returns audit events with optional filtering
func (as *AuditService) GetEvents(filters map[string]interface{}, limit int) []*AuditEvent {
	as.eventsMutex.RLock()
	defer as.eventsMutex.RUnlock()

	var filteredEvents []*AuditEvent
	for _, event := range as.events {
		if as.matchesFilters(event, filters) {
			filteredEvents = append(filteredEvents, event)
		}
	}

	// Apply limit
	if limit > 0 && len(filteredEvents) > limit {
		filteredEvents = filteredEvents[len(filteredEvents)-limit:]
	}

	return filteredEvents
}

// matchesFilters checks if an event matches the given filters
func (as *AuditService) matchesFilters(event *AuditEvent, filters map[string]interface{}) bool {
	for key, value := range filters {
		switch key {
		case "level":
			if event.Level != value {
				return false
			}
		case "category":
			if event.Category != value {
				return false
			}
		case "action":
			if event.Action != value {
				return false
			}
		case "user_id":
			if event.UserID != value {
				return false
			}
		case "session_id":
			if event.SessionID != value {
				return false
			}
		case "ip_address":
			if event.IPAddress != value {
				return false
			}
		case "resource":
			if event.Resource != value {
				return false
			}
		case "start_time":
			if startTime, ok := value.(time.Time); ok {
				if event.Timestamp.Before(startTime) {
					return false
				}
			}
		case "end_time":
			if endTime, ok := value.(time.Time); ok {
				if event.Timestamp.After(endTime) {
					return false
				}
			}
		}
	}
	return true
}

// AddComplianceRecord adds a compliance record
func (as *AuditService) AddComplianceRecord(record *ComplianceRecord) error {
	if record.ID == "" {
		record.ID = generateComplianceID()
	}

	record.CreatedAt = time.Now()
	record.UpdatedAt = time.Now()

	as.complianceMutex.Lock()
	as.complianceDB[record.ID] = record
	as.complianceMutex.Unlock()

	// Log compliance event
	as.LogEvent(LevelInfo, "compliance", "record_added",
		fmt.Sprintf("Compliance record added for %s: %s", record.Standard, record.Requirement),
		map[string]interface{}{
			"compliance_id": record.ID,
			"standard":      record.Standard,
			"requirement":   record.Requirement,
			"status":        record.Status,
		})

	return nil
}

// UpdateComplianceRecord updates a compliance record
func (as *AuditService) UpdateComplianceRecord(recordID string, updates map[string]interface{}) error {
	as.complianceMutex.Lock()
	record, exists := as.complianceDB[recordID]
	if !exists {
		as.complianceMutex.Unlock()
		return fmt.Errorf("compliance record not found: %s", recordID)
	}

	// Update fields
	if status, ok := updates["status"].(string); ok {
		record.Status = status
	}
	if evidence, ok := updates["evidence"].(string); ok {
		record.Evidence = evidence
	}
	if auditEventID, ok := updates["audit_event_id"].(string); ok {
		record.AuditEventID = auditEventID
	}

	record.UpdatedAt = time.Now()
	as.complianceMutex.Unlock()

	// Log compliance update
	as.LogEvent(LevelInfo, "compliance", "record_updated",
		fmt.Sprintf("Compliance record updated: %s", recordID),
		map[string]interface{}{
			"compliance_id": recordID,
			"updates":       updates,
		})

	return nil
}

// GetComplianceRecord retrieves a compliance record
func (as *AuditService) GetComplianceRecord(recordID string) (*ComplianceRecord, error) {
	as.complianceMutex.RLock()
	defer as.complianceMutex.RUnlock()

	record, exists := as.complianceDB[recordID]
	if !exists {
		return nil, fmt.Errorf("compliance record not found: %s", recordID)
	}

	return record, nil
}

// ListComplianceRecords returns all compliance records
func (as *AuditService) ListComplianceRecords() []*ComplianceRecord {
	as.complianceMutex.RLock()
	defer as.complianceMutex.RUnlock()

	records := make([]*ComplianceRecord, 0, len(as.complianceDB))
	for _, record := range as.complianceDB {
		records = append(records, record)
	}

	return records
}

// GetComplianceStats returns compliance statistics
func (as *AuditService) GetComplianceStats() map[string]interface{} {
	as.complianceMutex.RLock()
	defer as.complianceMutex.RUnlock()

	totalRecords := len(as.complianceDB)
	compliantCount := 0
	nonCompliantCount := 0
	pendingCount := 0

	standards := make(map[string]int)

	for _, record := range as.complianceDB {
		switch record.Status {
		case "compliant":
			compliantCount++
		case "non-compliant":
			nonCompliantCount++
		case "pending":
			pendingCount++
		}
		standards[record.Standard]++
	}

	return map[string]interface{}{
		"total_records":   totalRecords,
		"compliant":       compliantCount,
		"non_compliant":   nonCompliantCount,
		"pending":         pendingCount,
		"standards":       standards,
		"compliance_rate": float64(compliantCount) / float64(totalRecords) * 100,
	}
}

// ExportAuditLog exports audit events to a file
func (as *AuditService) ExportAuditLog(filename string, filters map[string]interface{}) error {
	events := as.GetEvents(filters, 0)

	file, err := os.Create(filename)
	if err != nil {
		return fmt.Errorf("failed to create export file: %w", err)
	}
	defer file.Close()

	encoder := json.NewEncoder(file)
	for _, event := range events {
		if err := encoder.Encode(event); err != nil {
			return fmt.Errorf("failed to encode event: %w", err)
		}
	}

	return nil
}

// GetAuditStats returns audit statistics
func (as *AuditService) GetAuditStats() map[string]interface{} {
	as.eventsMutex.RLock()
	defer as.eventsMutex.RUnlock()

	totalEvents := len(as.events)
	levelCounts := make(map[string]int)
	categoryCounts := make(map[string]int)
	actionCounts := make(map[string]int)

	for _, event := range as.events {
		levelCounts[string(event.Level)]++
		categoryCounts[event.Category]++
		actionCounts[event.Action]++
	}

	return map[string]interface{}{
		"total_events":    totalEvents,
		"level_counts":    levelCounts,
		"category_counts": categoryCounts,
		"action_counts":   actionCounts,
	}
}

// generateEventID generates a unique event ID
func generateEventID() string {
	return fmt.Sprintf("event_%d", time.Now().UnixNano())
}

// generateComplianceID generates a unique compliance record ID
func generateComplianceID() string {
	return fmt.Sprintf("comp_%d", time.Now().UnixNano())
}

// Close closes the audit service
func (as *AuditService) Close() error {
	as.logMutex.Lock()
	defer as.logMutex.Unlock()

	if as.logFile != nil {
		return as.logFile.Close()
	}
	return nil
}
