package monitoring

import (
	"encoding/json"
	"fmt"
	"io"
	"log"
	"os"
	"path/filepath"
	"runtime"
	"sync"
	"time"

	"github.com/arxos/arxos/core/internal/models"
	"gorm.io/gorm"
)

// LogLevel represents the logging level
type LogLevel string

const (
	LogLevelDebug   LogLevel = "debug"
	LogLevelInfo    LogLevel = "info"
	LogLevelWarning LogLevel = "warning"
	LogLevelError   LogLevel = "error"
	LogLevelFatal   LogLevel = "fatal"
)

// LogContext represents the context for logging
type LogContext struct {
	RequestID  string                 `json:"request_id,omitempty"`
	UserID     uint                   `json:"user_id,omitempty"`
	UserRole   string                 `json:"user_role,omitempty"`
	IPAddress  string                 `json:"ip_address,omitempty"`
	UserAgent  string                 `json:"user_agent,omitempty"`
	Endpoint   string                 `json:"endpoint,omitempty"`
	Method     string                 `json:"method,omitempty"`
	SessionID  string                 `json:"session_id,omitempty"`
	BuildingID *uint                  `json:"building_id,omitempty"`
	ObjectType string                 `json:"object_type,omitempty"`
	ObjectID   string                 `json:"object_id,omitempty"`
	Metadata   map[string]interface{} `json:"metadata,omitempty"`
}

// LogEntry represents a single log entry
type LogEntry struct {
	Timestamp time.Time              `json:"timestamp"`
	Level     LogLevel               `json:"level"`
	Message   string                 `json:"message"`
	Context   *LogContext            `json:"context,omitempty"`
	Fields    map[string]interface{} `json:"fields,omitempty"`
	Caller    string                 `json:"caller,omitempty"`
	Function  string                 `json:"function,omitempty"`
}

// LoggingService handles structured logging throughout the application
type LoggingService struct {
	logger *log.Logger
	db     *gorm.DB

	// Log file management
	logDir       string
	logFile      *os.File
	logFileMutex sync.Mutex

	// Log rotation
	maxLogSize    int64
	maxLogAge     time.Duration
	maxLogBackups int

	// Performance tracking
	performanceMutex sync.RWMutex
	performanceStats map[string]*PerformanceStats

	// Log level filtering
	minLogLevel LogLevel
}

// PerformanceStats tracks performance metrics
type PerformanceStats struct {
	Count       int64         `json:"count"`
	TotalTime   time.Duration `json:"total_time"`
	MinTime     time.Duration `json:"min_time"`
	MaxTime     time.Duration `json:"max_time"`
	AvgTime     time.Duration `json:"avg_time"`
	LastUpdated time.Time     `json:"last_updated"`
}

// NewLoggingService creates a new logging service
func NewLoggingService(db *gorm.DB, logDir string) (*LoggingService, error) {
	// Create log directory if it doesn't exist
	if err := os.MkdirAll(logDir, 0755); err != nil {
		return nil, fmt.Errorf("failed to create log directory: %w", err)
	}

	// Open log file
	logFilePath := filepath.Join(logDir, "application.log")
	logFile, err := os.OpenFile(logFilePath, os.O_CREATE|os.O_WRONLY|os.O_APPEND, 0644)
	if err != nil {
		return nil, fmt.Errorf("failed to open log file: %w", err)
	}

	// Create multi-writer for both file and stdout
	multiWriter := io.MultiWriter(logFile, os.Stdout)

	ls := &LoggingService{
		logger:           log.New(multiWriter, "", 0), // No prefix, we'll format ourselves
		db:               db,
		logDir:           logDir,
		logFile:          logFile,
		maxLogSize:       100 * 1024 * 1024,  // 100MB
		maxLogAge:        7 * 24 * time.Hour, // 7 days
		maxLogBackups:    10,
		performanceStats: make(map[string]*PerformanceStats),
		minLogLevel:      LogLevelInfo,
	}

	// Set minimum log level from environment
	if level := os.Getenv("LOG_LEVEL"); level != "" {
		ls.minLogLevel = LogLevel(level)
	}

	// Start log rotation
	go ls.startLogRotation()

	return ls, nil
}

// startLogRotation handles log file rotation
func (ls *LoggingService) startLogRotation() {
	ticker := time.NewTicker(1 * time.Hour)
	defer ticker.Stop()

	for {
		select {
		case <-ticker.C:
			ls.rotateLogs()
		}
	}
}

// rotateLogs rotates log files based on size and age
func (ls *LoggingService) rotateLogs() {
	logFile := filepath.Join(ls.logDir, "application.log")

	// Check if log file exists and get its info
	info, err := os.Stat(logFile)
	if err != nil {
		return
	}

	// Rotate if file is too large or too old
	if info.Size() > ls.maxLogSize || time.Since(info.ModTime()) > ls.maxLogAge {
		ls.rotateLogFile(logFile)
	}
}

// rotateLogFile performs the actual log rotation
func (ls *LoggingService) rotateLogFile(logFile string) {
	ls.logFileMutex.Lock()
	defer ls.logFileMutex.Unlock()

	// Create backup filename with timestamp
	timestamp := time.Now().Format("2006-01-02-15-04-05")
	backupFile := logFile + "." + timestamp

	// Close current log file
	ls.logFile.Close()

	// Rename current log file
	if err := os.Rename(logFile, backupFile); err != nil {
		log.Printf("Failed to rotate log file: %v", err)
		return
	}

	// Clean up old backup files
	ls.cleanupOldLogs()

	// Reopen log file
	newLogFile, err := os.OpenFile(logFile, os.O_CREATE|os.O_WRONLY|os.O_APPEND, 0644)
	if err != nil {
		log.Printf("Failed to reopen log file: %v", err)
		return
	}

	ls.logFile = newLogFile
	multiWriter := io.MultiWriter(newLogFile, os.Stdout)
	ls.logger = log.New(multiWriter, "", 0)

	log.Printf("Log file rotated to: %s", backupFile)
}

// cleanupOldLogs removes old log files
func (ls *LoggingService) cleanupOldLogs() {
	files, err := filepath.Glob(filepath.Join(ls.logDir, "*.log.*"))
	if err != nil {
		return
	}

	// Remove files older than maxLogAge
	cutoff := time.Now().Add(-ls.maxLogAge)
	for _, file := range files {
		info, err := os.Stat(file)
		if err != nil {
			continue
		}
		if info.ModTime().Before(cutoff) {
			os.Remove(file)
			log.Printf("Removed old log file: %s", file)
		}
	}
}

// shouldLog checks if a message should be logged based on the level
func (ls *LoggingService) shouldLog(level LogLevel) bool {
	levelOrder := map[LogLevel]int{
		LogLevelDebug:   0,
		LogLevelInfo:    1,
		LogLevelWarning: 2,
		LogLevelError:   3,
		LogLevelFatal:   4,
	}

	return levelOrder[level] >= levelOrder[ls.minLogLevel]
}

// Log logs a message with the given level and context
func (ls *LoggingService) Log(level LogLevel, message string, ctx *LogContext, fields map[string]interface{}) {
	if !ls.shouldLog(level) {
		return
	}

	// Create log entry
	entry := LogEntry{
		Timestamp: time.Now(),
		Level:     level,
		Message:   message,
		Context:   ctx,
		Fields:    fields,
	}

	// Add caller information
	if pc, file, line, ok := runtime.Caller(2); ok {
		entry.Caller = fmt.Sprintf("%s:%d", filepath.Base(file), line)
		entry.Function = runtime.FuncForPC(pc).Name()
	}

	// Format and write log entry
	jsonEntry, err := json.Marshal(entry)
	if err != nil {
		ls.logger.Printf("Failed to marshal log entry: %v", err)
		return
	}

	ls.logger.Println(string(jsonEntry))

	// Handle fatal level
	if level == LogLevelFatal {
		os.Exit(1)
	}
}

// LogAPIRequest logs an API request
func (ls *LoggingService) LogAPIRequest(ctx *LogContext, statusCode int, duration time.Duration, responseSize int64) {
	level := LogLevelInfo
	if statusCode >= 400 {
		level = LogLevelWarning
	}
	if statusCode >= 500 {
		level = LogLevelError
	}

	fields := map[string]interface{}{
		"status_code":   statusCode,
		"duration":      duration.String(),
		"response_size": responseSize,
	}

	ls.Log(level, "API Request", ctx, fields)

	// Track performance
	ls.trackPerformance(ctx.Endpoint, duration)
}

// LogAPIError logs an API error
func (ls *LoggingService) LogAPIError(ctx *LogContext, err error, statusCode int) {
	fields := map[string]interface{}{
		"error":       err.Error(),
		"status_code": statusCode,
		"error_type":  "api_error",
	}

	ls.Log(LogLevelError, "API Error", ctx, fields)

	// Store error in database for monitoring
	ls.storeErrorLog(ctx, err, "api_error", statusCode)
}

// LogExportJob logs an export job
func (ls *LoggingService) LogExportJob(ctx *LogContext, exportType, format, status string, duration time.Duration, fileSize int64) {
	level := LogLevelInfo
	if status == "failed" {
		level = LogLevelError
	}

	fields := map[string]interface{}{
		"export_type": exportType,
		"format":      format,
		"status":      status,
		"duration":    duration.String(),
		"file_size":   fileSize,
	}

	ls.Log(level, "Export Job", ctx, fields)

	// Track performance
	ls.trackPerformance(fmt.Sprintf("export_%s", exportType), duration)
}

// LogSecurityEvent logs a security event
func (ls *LoggingService) LogSecurityEvent(ctx *LogContext, eventType, severity string, details map[string]interface{}) {
	level := LogLevelInfo
	switch severity {
	case "low":
		level = LogLevelInfo
	case "medium":
		level = LogLevelWarning
	case "high":
		level = LogLevelError
	case "critical":
		level = LogLevelFatal
	}

	fields := map[string]interface{}{
		"event_type": eventType,
		"severity":   severity,
		"details":    details,
	}

	ls.Log(level, "Security Event", ctx, fields)

	// Store security event in database
	ls.storeSecurityEvent(ctx, eventType, severity, details)
}

// LogDatabaseOperation logs a database operation
func (ls *LoggingService) LogDatabaseOperation(ctx *LogContext, operation, table string, duration time.Duration, rowsAffected int64) {
	fields := map[string]interface{}{
		"operation":     operation,
		"table":         table,
		"duration":      duration.String(),
		"rows_affected": rowsAffected,
	}

	ls.Log(LogLevelDebug, "Database Operation", ctx, fields)

	// Track performance
	ls.trackPerformance(fmt.Sprintf("db_%s_%s", operation, table), duration)
}

// LogSystemEvent logs a system event
func (ls *LoggingService) LogSystemEvent(ctx *LogContext, eventType, message string, metadata map[string]interface{}) {
	fields := map[string]interface{}{
		"event_type": eventType,
		"message":    message,
		"metadata":   metadata,
	}

	ls.Log(LogLevelInfo, "System Event", ctx, fields)
}

// LogPerformance logs performance metrics
func (ls *LoggingService) LogPerformance(ctx *LogContext, operation string, duration time.Duration, metadata map[string]interface{}) {
	fields := map[string]interface{}{
		"operation": operation,
		"duration":  duration.String(),
		"metadata":  metadata,
	}

	ls.Log(LogLevelDebug, "Performance", ctx, fields)

	// Track performance
	ls.trackPerformance(operation, duration)
}

// trackPerformance tracks performance statistics
func (ls *LoggingService) trackPerformance(operation string, duration time.Duration) {
	ls.performanceMutex.Lock()
	defer ls.performanceMutex.Unlock()

	stats, exists := ls.performanceStats[operation]
	if !exists {
		stats = &PerformanceStats{
			MinTime: duration,
			MaxTime: duration,
		}
		ls.performanceStats[operation] = stats
	}

	stats.Count++
	stats.TotalTime += duration
	stats.AvgTime = stats.TotalTime / time.Duration(stats.Count)

	if duration < stats.MinTime {
		stats.MinTime = duration
	}
	if duration > stats.MaxTime {
		stats.MaxTime = duration
	}

	stats.LastUpdated = time.Now()
}

// GetPerformanceStats returns performance statistics
func (ls *LoggingService) GetPerformanceStats() map[string]*PerformanceStats {
	ls.performanceMutex.RLock()
	defer ls.performanceMutex.RUnlock()

	stats := make(map[string]*PerformanceStats)
	for k, v := range ls.performanceStats {
		stats[k] = v
	}
	return stats
}

// storeErrorLog stores error information in the database
func (ls *LoggingService) storeErrorLog(ctx *LogContext, err error, errorType string, statusCode int) {
	detailsJSON, _ := json.Marshal(map[string]interface{}{
		"error_message": err.Error(),
		"status_code":   statusCode,
		"user_id":       ctx.UserID,
		"user_role":     ctx.UserRole,
	})

	errorLog := models.SecurityAlert{
		AlertType: errorType,
		Severity:  "error",
		IPAddress: ctx.IPAddress,
		UserAgent: ctx.UserAgent,
		Path:      ctx.Endpoint,
		Method:    ctx.Method,
		Details:   detailsJSON,
		CreatedAt: time.Now(),
	}

	ls.db.Create(&errorLog)
}

// storeSecurityEvent stores security event in the database
func (ls *LoggingService) storeSecurityEvent(ctx *LogContext, eventType, severity string, details map[string]interface{}) {
	detailsJSON, _ := json.Marshal(details)

	alert := models.SecurityAlert{
		AlertType: eventType,
		Severity:  severity,
		IPAddress: ctx.IPAddress,
		UserAgent: ctx.UserAgent,
		Path:      ctx.Endpoint,
		Method:    ctx.Method,
		Details:   detailsJSON,
		CreatedAt: time.Now(),
	}

	ls.db.Create(&alert)
}

// GetLogs retrieves logs from the database
func (ls *LoggingService) GetLogs(filters map[string]interface{}, limit, offset int) ([]map[string]interface{}, error) {
	query := ls.db.Model(&models.SecurityAlert{})

	// Apply filters
	if level, ok := filters["level"].(string); ok {
		query = query.Where("severity = ?", level)
	}
	if eventType, ok := filters["event_type"].(string); ok {
		query = query.Where("alert_type = ?", eventType)
	}
	if userID, ok := filters["user_id"].(uint); ok {
		query = query.Where("details->>'user_id' = ?", fmt.Sprintf("%d", userID))
	}
	if startDate, ok := filters["start_date"].(time.Time); ok {
		query = query.Where("created_at >= ?", startDate)
	}
	if endDate, ok := filters["end_date"].(time.Time); ok {
		query = query.Where("created_at <= ?", endDate)
	}

	// Get logs
	var alerts []models.SecurityAlert
	err := query.Order("created_at DESC").
		Limit(limit).
		Offset(offset).
		Find(&alerts).Error

	if err != nil {
		return nil, err
	}

	// Convert to map format
	var logs []map[string]interface{}
	for _, alert := range alerts {
		logs = append(logs, map[string]interface{}{
			"id":         alert.ID,
			"level":      alert.Severity,
			"event_type": alert.AlertType,
			"message":    alert.Details,
			"timestamp":  alert.CreatedAt,
			"ip_address": alert.IPAddress,
			"user_agent": alert.UserAgent,
		})
	}

	return logs, nil
}

// ExportLogs exports logs to a file
func (ls *LoggingService) ExportLogs(filters map[string]interface{}, format string, writer io.Writer) error {
	logs, err := ls.GetLogs(filters, 10000, 0) // Export up to 10,000 logs
	if err != nil {
		return err
	}

	switch format {
	case "json":
		return json.NewEncoder(writer).Encode(logs)
	case "csv":
		// Write CSV header
		writer.Write([]byte("Timestamp,Level,EventType,Message,IPAddress,UserAgent\n"))

		for _, log := range logs {
			line := fmt.Sprintf("%s,%s,%s,%v,%s,%s\n",
				log["timestamp"],
				log["level"],
				log["event_type"],
				log["message"],
				log["ip_address"],
				log["user_agent"],
			)
			writer.Write([]byte(line))
		}
	default:
		return fmt.Errorf("unsupported format: %s", format)
	}

	return nil
}

// Close closes the logging service
func (ls *LoggingService) Close() error {
	ls.logFileMutex.Lock()
	defer ls.logFileMutex.Unlock()

	if ls.logFile != nil {
		return ls.logFile.Close()
	}
	return nil
}