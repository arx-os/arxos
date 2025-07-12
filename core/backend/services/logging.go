package services

import (
	"encoding/json"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"runtime"
	"sync"
	"time"

	"arx/models"

	"go.uber.org/zap"
	"go.uber.org/zap/zapcore"
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

// LoggingService handles structured logging throughout the application
type LoggingService struct {
	logger *zap.Logger
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

	// Configure zap logger
	config := zap.NewProductionConfig()
	config.OutputPaths = []string{
		filepath.Join(logDir, "application.log"),
		"stdout",
	}
	config.ErrorOutputPaths = []string{
		filepath.Join(logDir, "error.log"),
		"stderr",
	}
	config.EncoderConfig.TimeKey = "timestamp"
	config.EncoderConfig.EncodeTime = zapcore.ISO8601TimeEncoder
	config.EncoderConfig.EncodeLevel = zapcore.CapitalLevelEncoder

	logger, err := config.Build()
	if err != nil {
		return nil, fmt.Errorf("failed to create logger: %w", err)
	}

	ls := &LoggingService{
		logger:           logger,
		db:               db,
		logDir:           logDir,
		maxLogSize:       100 * 1024 * 1024,  // 100MB
		maxLogAge:        7 * 24 * time.Hour, // 7 days
		maxLogBackups:    10,
		performanceStats: make(map[string]*PerformanceStats),
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

	// Rename current log file
	if err := os.Rename(logFile, backupFile); err != nil {
		ls.logger.Error("Failed to rotate log file", zap.Error(err))
		return
	}

	// Clean up old backup files
	ls.cleanupOldLogs()

	// Reopen log file
	ls.logger.Info("Log file rotated", zap.String("backup_file", backupFile))
}

// cleanupOldLogs removes old log files
func (ls *LoggingService) cleanupOldLogs() {
	files, err := filepath.Glob(filepath.Join(ls.logDir, "*.log.*"))
	if err != nil {
		return
	}

	// Sort files by modification time (oldest first)
	type fileInfo struct {
		path    string
		modTime time.Time
	}

	var fileInfos []fileInfo
	for _, file := range files {
		info, err := os.Stat(file)
		if err != nil {
			continue
		}
		fileInfos = append(fileInfos, fileInfo{file, info.ModTime()})
	}

	// Remove files older than maxLogAge
	cutoff := time.Now().Add(-ls.maxLogAge)
	for _, fi := range fileInfos {
		if fi.modTime.Before(cutoff) {
			os.Remove(fi.path)
			ls.logger.Info("Removed old log file", zap.String("file", fi.path))
		}
	}
}

// Log logs a message with the given level and context
func (ls *LoggingService) Log(level LogLevel, message string, ctx *LogContext, fields ...zap.Field) {
	// Add context fields
	if ctx != nil {
		fields = append(fields,
			zap.String("request_id", ctx.RequestID),
			zap.Uint("user_id", ctx.UserID),
			zap.String("user_role", ctx.UserRole),
			zap.String("ip_address", ctx.IPAddress),
			zap.String("user_agent", ctx.UserAgent),
			zap.String("endpoint", ctx.Endpoint),
			zap.String("method", ctx.Method),
			zap.String("session_id", ctx.SessionID),
		)

		if ctx.BuildingID != nil {
			fields = append(fields, zap.Uint("building_id", *ctx.BuildingID))
		}

		if ctx.ObjectType != "" {
			fields = append(fields, zap.String("object_type", ctx.ObjectType))
		}

		if ctx.ObjectID != "" {
			fields = append(fields, zap.String("object_id", ctx.ObjectID))
		}

		if ctx.Metadata != nil {
			fields = append(fields, zap.Any("metadata", ctx.Metadata))
		}
	}

	// Add caller information
	if pc, file, line, ok := runtime.Caller(2); ok {
		fields = append(fields,
			zap.String("caller", fmt.Sprintf("%s:%d", filepath.Base(file), line)),
			zap.String("function", runtime.FuncForPC(pc).Name()),
		)
	}

	// Log based on level
	switch level {
	case LogLevelDebug:
		ls.logger.Debug(message, fields...)
	case LogLevelInfo:
		ls.logger.Info(message, fields...)
	case LogLevelWarning:
		ls.logger.Warn(message, fields...)
	case LogLevelError:
		ls.logger.Error(message, fields...)
	case LogLevelFatal:
		ls.logger.Fatal(message, fields...)
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

	ls.Log(level, "API Request",
		ctx,
		zap.Int("status_code", statusCode),
		zap.Duration("duration", duration),
		zap.Int64("response_size", responseSize),
	)

	// Track performance
	ls.trackPerformance(ctx.Endpoint, duration)
}

// LogAPIError logs an API error
func (ls *LoggingService) LogAPIError(ctx *LogContext, err error, statusCode int) {
	ls.Log(LogLevelError, "API Error",
		ctx,
		zap.Error(err),
		zap.Int("status_code", statusCode),
		zap.String("error_type", "api_error"),
	)

	// Store error in database for monitoring
	ls.storeErrorLog(ctx, err, "api_error", statusCode)
}

// LogExportJob logs an export job
func (ls *LoggingService) LogExportJob(ctx *LogContext, exportType, format, status string, duration time.Duration, fileSize int64) {
	level := LogLevelInfo
	if status == "failed" {
		level = LogLevelError
	}

	ls.Log(level, "Export Job",
		ctx,
		zap.String("export_type", exportType),
		zap.String("format", format),
		zap.String("status", status),
		zap.Duration("duration", duration),
		zap.Int64("file_size", fileSize),
	)

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

	ls.Log(level, "Security Event",
		ctx,
		zap.String("event_type", eventType),
		zap.String("severity", severity),
		zap.Any("details", details),
	)

	// Store security event in database
	ls.storeSecurityEvent(ctx, eventType, severity, details)
}

// LogDatabaseOperation logs a database operation
func (ls *LoggingService) LogDatabaseOperation(ctx *LogContext, operation, table string, duration time.Duration, rowsAffected int64) {
	ls.Log(LogLevelDebug, "Database Operation",
		ctx,
		zap.String("operation", operation),
		zap.String("table", table),
		zap.Duration("duration", duration),
		zap.Int64("rows_affected", rowsAffected),
	)

	// Track performance
	ls.trackPerformance(fmt.Sprintf("db_%s_%s", operation, table), duration)
}

// LogSystemEvent logs a system event
func (ls *LoggingService) LogSystemEvent(ctx *LogContext, eventType, message string, metadata map[string]interface{}) {
	ls.Log(LogLevelInfo, "System Event",
		ctx,
		zap.String("event_type", eventType),
		zap.String("message", message),
		zap.Any("metadata", metadata),
	)
}

// LogPerformance logs performance metrics
func (ls *LoggingService) LogPerformance(ctx *LogContext, operation string, duration time.Duration, metadata map[string]interface{}) {
	ls.Log(LogLevelDebug, "Performance",
		ctx,
		zap.String("operation", operation),
		zap.Duration("duration", duration),
		zap.Any("metadata", metadata),
	)

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
	return ls.logger.Sync()
}
