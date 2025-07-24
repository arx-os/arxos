package export

import (
	"encoding/json"
	"fmt"
	"sync"
	"time"

	"go.uber.org/zap"
)

// ExportTrackingStatus represents the status of export tracking
type ExportTrackingStatus string

const (
	ExportTrackingStatusPending   ExportTrackingStatus = "pending"
	ExportTrackingStatusRunning   ExportTrackingStatus = "running"
	ExportTrackingStatusCompleted ExportTrackingStatus = "completed"
	ExportTrackingStatusFailed    ExportTrackingStatus = "failed"
	ExportTrackingStatusCancelled ExportTrackingStatus = "cancelled"
	ExportTrackingStatusPaused    ExportTrackingStatus = "paused"
)

// ExportProgress represents the progress of an export job
type ExportProgress struct {
	JobID          string                 `json:"job_id"`
	Status         ExportTrackingStatus   `json:"status"`
	Progress       float64                `json:"progress"` // 0.0 to 1.0
	CurrentStep    string                 `json:"current_step"`
	TotalSteps     int                    `json:"total_steps"`
	CompletedSteps int                    `json:"completed_steps"`
	StartTime      time.Time              `json:"start_time"`
	EstimatedEnd   *time.Time             `json:"estimated_end,omitempty"`
	LastUpdate     time.Time              `json:"last_update"`
	Error          *ExportError           `json:"error,omitempty"`
	Warnings       []ExportWarning        `json:"warnings,omitempty"`
	Metadata       map[string]interface{} `json:"metadata,omitempty"`
}

// ExportError represents an error during export
type ExportError struct {
	Code        string                 `json:"code"`
	Message     string                 `json:"message"`
	Details     map[string]interface{} `json:"details,omitempty"`
	Timestamp   time.Time              `json:"timestamp"`
	Recoverable bool                   `json:"recoverable"`
}

// ExportWarning represents a warning during export
type ExportWarning struct {
	Code      string                 `json:"code"`
	Message   string                 `json:"message"`
	Details   map[string]interface{} `json:"details,omitempty"`
	Timestamp time.Time              `json:"timestamp"`
	Severity  string                 `json:"severity"` // low, medium, high
}

// ExportTrackingEvent represents an event during export tracking
type ExportTrackingEvent struct {
	JobID     string                 `json:"job_id"`
	EventType string                 `json:"event_type"`
	Message   string                 `json:"message"`
	Timestamp time.Time              `json:"timestamp"`
	Data      map[string]interface{} `json:"data,omitempty"`
	Severity  string                 `json:"severity"` // info, warning, error
}

// ExportTrackingConfig represents configuration for export tracking
type ExportTrackingConfig struct {
	UpdateInterval      time.Duration `json:"update_interval"`
	RetentionPeriod     time.Duration `json:"retention_period"`
	MaxConcurrentJobs   int           `json:"max_concurrent_jobs"`
	EnableNotifications bool          `json:"enable_notifications"`
	EnableMetrics       bool          `json:"enable_metrics"`
}

// ExportTrackingService provides comprehensive export tracking functionality
type ExportTrackingService struct {
	logger *zap.Logger
	mu     sync.RWMutex

	// Progress tracking
	progress map[string]*ExportProgress
	events   map[string][]ExportTrackingEvent

	// Configuration
	config *ExportTrackingConfig

	// Callbacks
	progressCallbacks map[string][]func(*ExportProgress)
	eventCallbacks    map[string][]func(ExportTrackingEvent)

	// Metrics
	metrics *ExportTrackingMetrics
}

// ExportTrackingMetrics represents metrics for export tracking
type ExportTrackingMetrics struct {
	TotalJobsStarted   int64
	TotalJobsCompleted int64
	TotalJobsFailed    int64
	AverageJobDuration time.Duration
	ActiveJobs         int
	LastUpdate         time.Time
}

// NewExportTrackingService creates a new export tracking service
func NewExportTrackingService(logger *zap.Logger, config *ExportTrackingConfig) (*ExportTrackingService, error) {
	if config == nil {
		config = &ExportTrackingConfig{
			UpdateInterval:      5 * time.Second,
			RetentionPeriod:     24 * time.Hour,
			MaxConcurrentJobs:   100,
			EnableNotifications: true,
			EnableMetrics:       true,
		}
	}

	ets := &ExportTrackingService{
		logger:            logger,
		progress:          make(map[string]*ExportProgress),
		events:            make(map[string][]ExportTrackingEvent),
		config:            config,
		progressCallbacks: make(map[string][]func(*ExportProgress)),
		eventCallbacks:    make(map[string][]func(ExportTrackingEvent)),
		metrics:           &ExportTrackingMetrics{},
	}

	// Start cleanup routine
	go ets.cleanupRoutine()

	logger.Info("Export tracking service initialized",
		zap.Duration("update_interval", config.UpdateInterval),
		zap.Duration("retention_period", config.RetentionPeriod),
		zap.Int("max_concurrent_jobs", config.MaxConcurrentJobs))

	return ets, nil
}

// StartTracking starts tracking an export job
func (ets *ExportTrackingService) StartTracking(jobID string, totalSteps int) error {
	ets.mu.Lock()
	defer ets.mu.Unlock()

	if _, exists := ets.progress[jobID]; exists {
		return fmt.Errorf("job %s is already being tracked", jobID)
	}

	progress := &ExportProgress{
		JobID:          jobID,
		Status:         ExportTrackingStatusPending,
		Progress:       0.0,
		CurrentStep:    "Initializing",
		TotalSteps:     totalSteps,
		CompletedSteps: 0,
		StartTime:      time.Now(),
		LastUpdate:     time.Now(),
	}

	ets.progress[jobID] = progress
	ets.events[jobID] = []ExportTrackingEvent{}

	// Add start event
	ets.addEvent(jobID, "job_started", "Export job started", "info", nil)

	ets.logger.Info("Started tracking export job",
		zap.String("job_id", jobID),
		zap.Int("total_steps", totalSteps))

	return nil
}

// UpdateProgress updates the progress of an export job
func (ets *ExportTrackingService) UpdateProgress(jobID string, progress float64, currentStep string, completedSteps int) error {
	ets.mu.Lock()
	defer ets.mu.Unlock()

	jobProgress, exists := ets.progress[jobID]
	if !exists {
		return fmt.Errorf("job %s is not being tracked", jobID)
	}

	// Update progress
	jobProgress.Progress = progress
	jobProgress.CurrentStep = currentStep
	jobProgress.CompletedSteps = completedSteps
	jobProgress.LastUpdate = time.Now()

	// Update status based on progress
	if progress >= 1.0 {
		jobProgress.Status = ExportTrackingStatusCompleted
	} else if jobProgress.Status == ExportTrackingStatusPending {
		jobProgress.Status = ExportTrackingStatusRunning
	}

	// Calculate estimated end time
	if progress > 0 {
		elapsed := time.Since(jobProgress.StartTime)
		estimatedTotal := time.Duration(float64(elapsed) / progress)
		estimatedEnd := jobProgress.StartTime.Add(estimatedTotal)
		jobProgress.EstimatedEnd = &estimatedEnd
	}

	// Trigger callbacks
	ets.triggerProgressCallbacks(jobID, jobProgress)

	// Add progress event
	ets.addEvent(jobID, "progress_updated", fmt.Sprintf("Progress: %.1f%% - %s", progress*100, currentStep), "info", map[string]interface{}{
		"progress":        progress,
		"current_step":    currentStep,
		"completed_steps": completedSteps,
	})

	return nil
}

// CompleteJob marks an export job as completed
func (ets *ExportTrackingService) CompleteJob(jobID string, result *ExportResult) error {
	ets.mu.Lock()
	defer ets.mu.Unlock()

	jobProgress, exists := ets.progress[jobID]
	if !exists {
		return fmt.Errorf("job %s is not being tracked", jobID)
	}

	jobProgress.Status = ExportTrackingStatusCompleted
	jobProgress.Progress = 1.0
	jobProgress.CompletedSteps = jobProgress.TotalSteps
	jobProgress.CurrentStep = "Completed"
	jobProgress.LastUpdate = time.Now()

	// Add completion event
	ets.addEvent(jobID, "job_completed", "Export job completed successfully", "info", map[string]interface{}{
		"result": result,
	})

	// Update metrics
	ets.metrics.TotalJobsCompleted++
	ets.metrics.ActiveJobs--
	ets.metrics.LastUpdate = time.Now()

	// Trigger callbacks
	ets.triggerProgressCallbacks(jobID, jobProgress)

	ets.logger.Info("Export job completed",
		zap.String("job_id", jobID),
		zap.Duration("duration", time.Since(jobProgress.StartTime)))

	return nil
}

// FailJob marks an export job as failed
func (ets *ExportTrackingService) FailJob(jobID string, err error) error {
	ets.mu.Lock()
	defer ets.mu.Unlock()

	jobProgress, exists := ets.progress[jobID]
	if !exists {
		return fmt.Errorf("job %s is not being tracked", jobID)
	}

	jobProgress.Status = ExportTrackingStatusFailed
	jobProgress.LastUpdate = time.Now()
	jobProgress.Error = &ExportError{
		Code:        "EXPORT_FAILED",
		Message:     err.Error(),
		Timestamp:   time.Now(),
		Recoverable: false,
	}

	// Add failure event
	ets.addEvent(jobID, "job_failed", fmt.Sprintf("Export job failed: %s", err.Error()), "error", map[string]interface{}{
		"error": err.Error(),
	})

	// Update metrics
	ets.metrics.TotalJobsFailed++
	ets.metrics.ActiveJobs--
	ets.metrics.LastUpdate = time.Now()

	// Trigger callbacks
	ets.triggerProgressCallbacks(jobID, jobProgress)

	ets.logger.Error("Export job failed",
		zap.String("job_id", jobID),
		zap.Error(err),
		zap.Duration("duration", time.Since(jobProgress.StartTime)))

	return nil
}

// CancelJob cancels an export job
func (ets *ExportTrackingService) CancelJob(jobID string, reason string) error {
	ets.mu.Lock()
	defer ets.mu.Unlock()

	jobProgress, exists := ets.progress[jobID]
	if !exists {
		return fmt.Errorf("job %s is not being tracked", jobID)
	}

	jobProgress.Status = ExportTrackingStatusCancelled
	jobProgress.LastUpdate = time.Now()

	// Add cancellation event
	ets.addEvent(jobID, "job_cancelled", fmt.Sprintf("Export job cancelled: %s", reason), "warning", map[string]interface{}{
		"reason": reason,
	})

	// Update metrics
	ets.metrics.ActiveJobs--
	ets.metrics.LastUpdate = time.Now()

	// Trigger callbacks
	ets.triggerProgressCallbacks(jobID, jobProgress)

	ets.logger.Info("Export job cancelled",
		zap.String("job_id", jobID),
		zap.String("reason", reason))

	return nil
}

// PauseJob pauses an export job
func (ets *ExportTrackingService) PauseJob(jobID string, reason string) error {
	ets.mu.Lock()
	defer ets.mu.Unlock()

	jobProgress, exists := ets.progress[jobID]
	if !exists {
		return fmt.Errorf("job %s is not being tracked", jobID)
	}

	jobProgress.Status = ExportTrackingStatusPaused
	jobProgress.LastUpdate = time.Now()

	// Add pause event
	ets.addEvent(jobID, "job_paused", fmt.Sprintf("Export job paused: %s", reason), "warning", map[string]interface{}{
		"reason": reason,
	})

	// Trigger callbacks
	ets.triggerProgressCallbacks(jobID, jobProgress)

	ets.logger.Info("Export job paused",
		zap.String("job_id", jobID),
		zap.String("reason", reason))

	return nil
}

// ResumeJob resumes a paused export job
func (ets *ExportTrackingService) ResumeJob(jobID string) error {
	ets.mu.Lock()
	defer ets.mu.Unlock()

	jobProgress, exists := ets.progress[jobID]
	if !exists {
		return fmt.Errorf("job %s is not being tracked", jobID)
	}

	if jobProgress.Status != ExportTrackingStatusPaused {
		return fmt.Errorf("job %s is not paused", jobID)
	}

	jobProgress.Status = ExportTrackingStatusRunning
	jobProgress.LastUpdate = time.Now()

	// Add resume event
	ets.addEvent(jobID, "job_resumed", "Export job resumed", "info", nil)

	// Trigger callbacks
	ets.triggerProgressCallbacks(jobID, jobProgress)

	ets.logger.Info("Export job resumed",
		zap.String("job_id", jobID))

	return nil
}

// AddWarning adds a warning to an export job
func (ets *ExportTrackingService) AddWarning(jobID string, code string, message string, severity string) error {
	ets.mu.Lock()
	defer ets.mu.Unlock()

	jobProgress, exists := ets.progress[jobID]
	if !exists {
		return fmt.Errorf("job %s is not being tracked", jobID)
	}

	warning := ExportWarning{
		Code:      code,
		Message:   message,
		Timestamp: time.Now(),
		Severity:  severity,
	}

	jobProgress.Warnings = append(jobProgress.Warnings, warning)

	// Add warning event
	ets.addEvent(jobID, "warning_added", message, "warning", map[string]interface{}{
		"code":     code,
		"severity": severity,
	})

	ets.logger.Warn("Export job warning",
		zap.String("job_id", jobID),
		zap.String("code", code),
		zap.String("message", message),
		zap.String("severity", severity))

	return nil
}

// GetProgress returns the progress of an export job
func (ets *ExportTrackingService) GetProgress(jobID string) (*ExportProgress, error) {
	ets.mu.RLock()
	defer ets.mu.RUnlock()

	progress, exists := ets.progress[jobID]
	if !exists {
		return nil, fmt.Errorf("job %s is not being tracked", jobID)
	}

	return progress, nil
}

// GetEvents returns the events for an export job
func (ets *ExportTrackingService) GetEvents(jobID string) ([]ExportTrackingEvent, error) {
	ets.mu.RLock()
	defer ets.mu.RUnlock()

	events, exists := ets.events[jobID]
	if !exists {
		return nil, fmt.Errorf("job %s is not being tracked", jobID)
	}

	return events, nil
}

// GetAllProgress returns all active export job progress
func (ets *ExportTrackingService) GetAllProgress() map[string]*ExportProgress {
	ets.mu.RLock()
	defer ets.mu.RUnlock()

	result := make(map[string]*ExportProgress)
	for jobID, progress := range ets.progress {
		result[jobID] = progress
	}

	return result
}

// GetMetrics returns the tracking metrics
func (ets *ExportTrackingService) GetMetrics() *ExportTrackingMetrics {
	ets.mu.RLock()
	defer ets.mu.RUnlock()

	return ets.metrics
}

// RegisterProgressCallback registers a callback for progress updates
func (ets *ExportTrackingService) RegisterProgressCallback(jobID string, callback func(*ExportProgress)) {
	ets.mu.Lock()
	defer ets.mu.Unlock()

	ets.progressCallbacks[jobID] = append(ets.progressCallbacks[jobID], callback)
}

// RegisterEventCallback registers a callback for event updates
func (ets *ExportTrackingService) RegisterEventCallback(jobID string, callback func(ExportTrackingEvent)) {
	ets.mu.Lock()
	defer ets.mu.Unlock()

	ets.eventCallbacks[jobID] = append(ets.eventCallbacks[jobID], callback)
}

// StopTracking stops tracking an export job
func (ets *ExportTrackingService) StopTracking(jobID string) error {
	ets.mu.Lock()
	defer ets.mu.Unlock()

	if _, exists := ets.progress[jobID]; !exists {
		return fmt.Errorf("job %s is not being tracked", jobID)
	}

	delete(ets.progress, jobID)
	delete(ets.events, jobID)
	delete(ets.progressCallbacks, jobID)
	delete(ets.eventCallbacks, jobID)

	ets.logger.Info("Stopped tracking export job",
		zap.String("job_id", jobID))

	return nil
}

// addEvent adds an event to the tracking
func (ets *ExportTrackingService) addEvent(jobID string, eventType string, message string, severity string, data map[string]interface{}) {
	event := ExportTrackingEvent{
		JobID:     jobID,
		EventType: eventType,
		Message:   message,
		Timestamp: time.Now(),
		Data:      data,
		Severity:  severity,
	}

	ets.events[jobID] = append(ets.events[jobID], event)

	// Trigger event callbacks
	ets.triggerEventCallbacks(jobID, event)
}

// triggerProgressCallbacks triggers progress callbacks
func (ets *ExportTrackingService) triggerProgressCallbacks(jobID string, progress *ExportProgress) {
	if callbacks, exists := ets.progressCallbacks[jobID]; exists {
		for _, callback := range callbacks {
			go callback(progress)
		}
	}
}

// triggerEventCallbacks triggers event callbacks
func (ets *ExportTrackingService) triggerEventCallbacks(jobID string, event ExportTrackingEvent) {
	if callbacks, exists := ets.eventCallbacks[jobID]; exists {
		for _, callback := range callbacks {
			go callback(event)
		}
	}
}

// cleanupRoutine runs the cleanup routine
func (ets *ExportTrackingService) cleanupRoutine() {
	ticker := time.NewTicker(ets.config.RetentionPeriod)
	defer ticker.Stop()

	for range ticker.C {
		ets.cleanup()
	}
}

// cleanup removes old tracking data
func (ets *ExportTrackingService) cleanup() {
	ets.mu.Lock()
	defer ets.mu.Unlock()

	cutoff := time.Now().Add(-ets.config.RetentionPeriod)

	for jobID, progress := range ets.progress {
		if progress.LastUpdate.Before(cutoff) &&
			(progress.Status == ExportTrackingStatusCompleted ||
				progress.Status == ExportTrackingStatusFailed ||
				progress.Status == ExportTrackingStatusCancelled) {

			delete(ets.progress, jobID)
			delete(ets.events, jobID)
			delete(ets.progressCallbacks, jobID)
			delete(ets.eventCallbacks, jobID)

			ets.logger.Debug("Cleaned up old tracking data",
				zap.String("job_id", jobID))
		}
	}
}

// ExportProgressToJSON converts progress to JSON
func (ets *ExportTrackingService) ExportProgressToJSON(progress *ExportProgress) ([]byte, error) {
	return json.Marshal(progress)
}

// ExportEventsToJSON converts events to JSON
func (ets *ExportTrackingService) ExportEventsToJSON(events []ExportTrackingEvent) ([]byte, error) {
	return json.Marshal(events)
}

// ImportProgressFromJSON imports progress from JSON
func (ets *ExportTrackingService) ImportProgressFromJSON(data []byte) (*ExportProgress, error) {
	var progress ExportProgress
	if err := json.Unmarshal(data, &progress); err != nil {
		return nil, err
	}
	return &progress, nil
}

// ImportEventsFromJSON imports events from JSON
func (ets *ExportTrackingService) ImportEventsFromJSON(data []byte) ([]ExportTrackingEvent, error) {
	var events []ExportTrackingEvent
	if err := json.Unmarshal(data, &events); err != nil {
		return nil, err
	}
	return events, nil
}
