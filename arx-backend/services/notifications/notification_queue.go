package notifications

import (
	"context"
	"fmt"
	"sync"
	"time"

	"github.com/arxos/arx-backend/models"
)

// NewNotificationQueue creates a new notification queue
func NewNotificationQueue(
	service *EnhancedNotificationService,
	workers int,
	ctx context.Context,
) *NotificationQueue {
	queue := &NotificationQueue{
		queue:   make(chan *models.NotificationEnhanced, 1000), // Buffer size
		workers: workers,
		ctx:     ctx,
		service: service,
	}

	return queue
}

// Start starts the notification queue workers
func (nq *NotificationQueue) Start() {
	var wg sync.WaitGroup

	// Start workers
	for i := 0; i < nq.workers; i++ {
		wg.Add(1)
		go func(workerID int) {
			defer wg.Done()
			nq.worker(workerID)
		}(i)
	}

	// Wait for context cancellation
	<-nq.ctx.Done()

	// Close queue channel
	close(nq.queue)

	// Wait for all workers to finish
	wg.Wait()
}

// worker processes notifications from the queue
func (nq *NotificationQueue) worker(workerID int) {
	for {
		select {
		case notification, ok := <-nq.queue:
			if !ok {
				// Channel closed, worker should exit
				return
			}
			nq.processNotification(notification, workerID)
		case <-nq.ctx.Done():
			// Context cancelled, worker should exit
			return
		}
	}
}

// processNotification processes a single notification
func (nq *NotificationQueue) processNotification(
	notification *models.NotificationEnhanced,
	workerID int,
) {
	// Add worker context
	workerCtx := context.WithValue(nq.ctx, "worker_id", workerID)

	// Process with retry logic
	err := nq.processWithRetry(workerCtx, notification)
	if err != nil {
		// Log error and update notification status
		fmt.Printf("Worker %d: Failed to process notification %d: %v\n", workerID, notification.ID, err)

		notification.Status = models.NotificationStatusFailed
		notification.ErrorMessage = err.Error()
		notification.UpdatedAt = time.Now()

		if err := nq.service.db.Save(notification).Error; err != nil {
			fmt.Printf("Worker %d: Failed to update notification status: %v\n", workerID, err)
		}
	}
}

// processWithRetry processes notification with retry logic
func (nq *NotificationQueue) processWithRetry(
	ctx context.Context,
	notification *models.NotificationEnhanced,
) error {
	maxRetries := nq.service.config.RetryConfig.MaxRetries
	retryDelay := nq.service.config.RetryConfig.RetryDelay
	backoffMultiplier := nq.service.config.RetryConfig.BackoffMultiplier
	maxRetryDelay := nq.service.config.RetryConfig.MaxRetryDelay

	for attempt := 0; attempt <= maxRetries; attempt++ {
		// Check if context is cancelled
		select {
		case <-ctx.Done():
			return fmt.Errorf("context cancelled")
		default:
		}

		// Process notification
		err := nq.service.SendNotification(notification)
		if err == nil {
			// Success
			return nil
		}

		// If this is the last attempt, return error
		if attempt == maxRetries {
			return fmt.Errorf("failed after %d attempts: %w", maxRetries+1, err)
		}

		// Calculate delay for next retry
		delay := retryDelay
		if attempt > 0 {
			delay = time.Duration(float64(delay) * backoffMultiplier)
			if delay > maxRetryDelay {
				delay = maxRetryDelay
			}
		}

		// Add jitter if enabled
		if nq.service.config.RetryConfig.Jitter {
			delay = addJitter(delay)
		}

		// Update retry count
		notification.RetryCount = attempt + 1
		notification.UpdatedAt = time.Now()

		if err := nq.service.db.Save(notification).Error; err != nil {
			fmt.Printf("Failed to update retry count: %v\n", err)
		}

		// Wait before retry
		select {
		case <-ctx.Done():
			return fmt.Errorf("context cancelled during retry delay")
		case <-time.After(delay):
			// Continue to next attempt
		}
	}

	return fmt.Errorf("unexpected retry loop exit")
}

// Enqueue adds a notification to the queue
func (nq *NotificationQueue) Enqueue(notification *models.NotificationEnhanced) error {
	select {
	case nq.queue <- notification:
		return nil
	case <-nq.ctx.Done():
		return fmt.Errorf("queue context cancelled")
	default:
		return fmt.Errorf("queue is full")
	}
}

// EnqueueBatch adds multiple notifications to the queue
func (nq *NotificationQueue) EnqueueBatch(notifications []*models.NotificationEnhanced) error {
	for _, notification := range notifications {
		if err := nq.Enqueue(notification); err != nil {
			return fmt.Errorf("failed to enqueue notification %d: %w", notification.ID, err)
		}
	}
	return nil
}

// GetQueueStats returns queue statistics
func (nq *NotificationQueue) GetQueueStats() map[string]interface{} {
	nq.mu.RLock()
	defer nq.mu.RUnlock()

	return map[string]interface{}{
		"queue_length": len(nq.queue),
		"workers":      nq.workers,
		"capacity":     cap(nq.queue),
	}
}

// addJitter adds random jitter to delay to prevent thundering herd
func addJitter(delay time.Duration) time.Duration {
	// Add ±10% jitter
	jitter := time.Duration(float64(delay) * 0.1)
	return delay + time.Duration(float64(jitter)*float64(time.Now().UnixNano()%100)/100.0)
}

// NotificationProcessor handles notification processing with advanced features
type NotificationProcessor struct {
	service *EnhancedNotificationService
	queue   *NotificationQueue
	stats   *ProcessorStats
	mu      sync.RWMutex
}

// ProcessorStats holds processor statistics
type ProcessorStats struct {
	ProcessedCount     int64
	SuccessCount       int64
	FailureCount       int64
	AverageProcessTime time.Duration
	LastProcessed      time.Time
	mu                 sync.RWMutex
}

// NewNotificationProcessor creates a new notification processor
func NewNotificationProcessor(service *EnhancedNotificationService) *NotificationProcessor {
	return &NotificationProcessor{
		service: service,
		queue:   service.queue,
		stats:   &ProcessorStats{},
	}
}

// ProcessNotification processes a notification with advanced features
func (np *NotificationProcessor) ProcessNotification(notification *models.NotificationEnhanced) error {
	startTime := time.Now()

	// Validate notification
	if err := np.validateNotification(notification); err != nil {
		return fmt.Errorf("notification validation failed: %w", err)
	}

	// Check rate limits
	if err := np.checkRateLimits(notification); err != nil {
		return fmt.Errorf("rate limit exceeded: %w", err)
	}

	// Enqueue for processing
	if err := np.queue.Enqueue(notification); err != nil {
		return fmt.Errorf("failed to enqueue notification: %w", err)
	}

	// Update statistics
	np.updateStats(true, time.Since(startTime))

	return nil
}

// ProcessNotificationBatch processes multiple notifications
func (np *NotificationProcessor) ProcessNotificationBatch(notifications []*models.NotificationEnhanced) error {
	startTime := time.Now()

	// Validate all notifications
	for i, notification := range notifications {
		if err := np.validateNotification(notification); err != nil {
			return fmt.Errorf("notification %d validation failed: %w", i, err)
		}
	}

	// Check rate limits for batch
	if err := np.checkBatchRateLimits(notifications); err != nil {
		return fmt.Errorf("batch rate limit exceeded: %w", err)
	}

	// Enqueue batch
	if err := np.queue.EnqueueBatch(notifications); err != nil {
		return fmt.Errorf("failed to enqueue notification batch: %w", err)
	}

	// Update statistics
	np.updateStats(true, time.Since(startTime))

	return nil
}

// validateNotification validates a notification
func (np *NotificationProcessor) validateNotification(notification *models.NotificationEnhanced) error {
	if notification == nil {
		return fmt.Errorf("notification is nil")
	}

	if notification.Title == "" {
		return fmt.Errorf("notification title is required")
	}

	if notification.Message == "" {
		return fmt.Errorf("notification message is required")
	}

	if !notification.Type.IsValid() {
		return fmt.Errorf("invalid notification type: %s", notification.Type)
	}

	if !notification.Priority.IsValid() {
		return fmt.Errorf("invalid notification priority: %s", notification.Priority)
	}

	channels := notification.GetChannels()
	for _, channel := range channels {
		if !channel.IsValid() {
			return fmt.Errorf("invalid notification channel: %s", channel)
		}
	}

	return nil
}

// checkRateLimits checks rate limits for a notification
func (np *NotificationProcessor) checkRateLimits(notification *models.NotificationEnhanced) error {
	// Check global rate limit
	np.mu.Lock()
	defer np.mu.Unlock()

	// Simple rate limiting - can be enhanced with more sophisticated algorithms
	now := time.Now()
	if np.stats.LastProcessed.Add(time.Second) == now {
		// Rate limit: 1 notification per second
		return fmt.Errorf("rate limit exceeded")
	}

	np.stats.LastProcessed = now
	return nil
}

// checkBatchRateLimits checks rate limits for a batch of notifications
func (np *NotificationProcessor) checkBatchRateLimits(notifications []*models.NotificationEnhanced) error {
	// Check batch rate limit
	if len(notifications) > 100 {
		return fmt.Errorf("batch size too large: %d", len(notifications))
	}

	return nil
}

// updateStats updates processor statistics
func (np *NotificationProcessor) updateStats(success bool, processTime time.Duration) {
	np.stats.mu.Lock()
	defer np.stats.mu.Unlock()

	np.stats.ProcessedCount++
	if success {
		np.stats.SuccessCount++
	} else {
		np.stats.FailureCount++
	}

	// Update average process time
	if np.stats.ProcessedCount > 0 {
		totalTime := np.stats.AverageProcessTime * time.Duration(np.stats.ProcessedCount-1)
		np.stats.AverageProcessTime = (totalTime + processTime) / time.Duration(np.stats.ProcessedCount)
	}
}

// GetStats returns processor statistics
func (np *NotificationProcessor) GetStats() *ProcessorStats {
	np.stats.mu.RLock()
	defer np.stats.mu.RUnlock()

	// Create a copy to avoid race conditions
	stats := &ProcessorStats{
		ProcessedCount:     np.stats.ProcessedCount,
		SuccessCount:       np.stats.SuccessCount,
		FailureCount:       np.stats.FailureCount,
		AverageProcessTime: np.stats.AverageProcessTime,
		LastProcessed:      np.stats.LastProcessed,
	}

	return stats
}

// NotificationScheduler handles scheduled notifications
type NotificationScheduler struct {
	service *EnhancedNotificationService
	jobs    map[string]*ScheduledJob
	mu      sync.RWMutex
	ctx     context.Context
	cancel  context.CancelFunc
}

// ScheduledJob represents a scheduled notification job
type ScheduledJob struct {
	ID            string
	Notification  *models.NotificationEnhanced
	ScheduledAt   time.Time
	Interval      time.Duration
	MaxExecutions int
	Executions    int
	Active        bool
}

// NewNotificationScheduler creates a new notification scheduler
func NewNotificationScheduler(service *EnhancedNotificationService) *NotificationScheduler {
	ctx, cancel := context.WithCancel(context.Background())

	scheduler := &NotificationScheduler{
		service: service,
		jobs:    make(map[string]*ScheduledJob),
		ctx:     ctx,
		cancel:  cancel,
	}

	// Start scheduler worker
	go scheduler.run()

	return scheduler
}

// ScheduleNotification schedules a notification for future delivery
func (ns *NotificationScheduler) ScheduleNotification(
	notification *models.NotificationEnhanced,
	scheduledAt time.Time,
) error {
	if scheduledAt.Before(time.Now()) {
		return fmt.Errorf("scheduled time must be in the future")
	}

	job := &ScheduledJob{
		ID:           fmt.Sprintf("job_%d_%d", notification.ID, scheduledAt.Unix()),
		Notification: notification,
		ScheduledAt:  scheduledAt,
		Active:       true,
	}

	ns.mu.Lock()
	ns.jobs[job.ID] = job
	ns.mu.Unlock()

	return nil
}

// ScheduleRecurringNotification schedules a recurring notification
func (ns *NotificationScheduler) ScheduleRecurringNotification(
	notification *models.NotificationEnhanced,
	interval time.Duration,
	maxExecutions int,
) error {
	if interval <= 0 {
		return fmt.Errorf("interval must be positive")
	}

	job := &ScheduledJob{
		ID:            fmt.Sprintf("recurring_%d_%d", notification.ID, time.Now().Unix()),
		Notification:  notification,
		ScheduledAt:   time.Now().Add(interval),
		Interval:      interval,
		MaxExecutions: maxExecutions,
		Active:        true,
	}

	ns.mu.Lock()
	ns.jobs[job.ID] = job
	ns.mu.Unlock()

	return nil
}

// CancelScheduledNotification cancels a scheduled notification
func (ns *NotificationScheduler) CancelScheduledNotification(jobID string) error {
	ns.mu.Lock()
	defer ns.mu.Unlock()

	if _, exists := ns.jobs[jobID]; !exists {
		return fmt.Errorf("job not found: %s", jobID)
	}

	delete(ns.jobs, jobID)
	return nil
}

// run runs the scheduler worker
func (ns *NotificationScheduler) run() {
	ticker := time.NewTicker(1 * time.Second)
	defer ticker.Stop()

	for {
		select {
		case <-ns.ctx.Done():
			return
		case <-ticker.C:
			ns.processScheduledJobs()
		}
	}
}

// processScheduledJobs processes scheduled jobs
func (ns *NotificationScheduler) processScheduledJobs() {
	now := time.Now()
	var jobsToExecute []*ScheduledJob

	ns.mu.RLock()
	for _, job := range ns.jobs {
		if job.Active && now.After(job.ScheduledAt) {
			jobsToExecute = append(jobsToExecute, job)
		}
	}
	ns.mu.RUnlock()

	// Execute jobs
	for _, job := range jobsToExecute {
		ns.executeJob(job)
	}
}

// executeJob executes a scheduled job
func (ns *NotificationScheduler) executeJob(job *ScheduledJob) {
	// Create a copy of the notification for execution
	notification := &models.NotificationEnhanced{
		Title:       job.Notification.Title,
		Message:     job.Notification.Message,
		Type:        job.Notification.Type,
		Priority:    job.Notification.Priority,
		RecipientID: job.Notification.RecipientID,
		SenderID:    job.Notification.SenderID,
		ConfigID:    job.Notification.ConfigID,
		TemplateID:  job.Notification.TemplateID,
		Status:      models.NotificationStatusPending,
		CreatedAt:   time.Now(),
		UpdatedAt:   time.Now(),
	}

	// Copy channels
	if err := notification.SetChannels(job.Notification.GetChannels()); err != nil {
		fmt.Printf("Failed to set channels for scheduled job %s: %v\n", job.ID, err)
		return
	}

	// Copy template data
	if job.Notification.TemplateData != nil {
		if err := notification.SetTemplateData(job.Notification.GetTemplateData()); err != nil {
			fmt.Printf("Failed to set template data for scheduled job %s: %v\n", job.ID, err)
			return
		}
	}

	// Copy metadata
	if job.Notification.Metadata != nil {
		if err := notification.SetMetadata(job.Notification.GetMetadata()); err != nil {
			fmt.Printf("Failed to set metadata for scheduled job %s: %v\n", job.ID, err)
			return
		}
	}

	// Save notification to database
	if err := ns.service.db.Create(notification).Error; err != nil {
		fmt.Printf("Failed to create scheduled notification for job %s: %v\n", job.ID, err)
		return
	}

	// Send notification
	if err := ns.service.SendNotification(notification); err != nil {
		fmt.Printf("Failed to send scheduled notification for job %s: %v\n", job.ID, err)
	}

	// Update job execution count
	job.Executions++

	// Handle recurring jobs
	if job.Interval > 0 {
		if job.MaxExecutions > 0 && job.Executions >= job.MaxExecutions {
			// Max executions reached, deactivate job
			job.Active = false
		} else {
			// Schedule next execution
			job.ScheduledAt = time.Now().Add(job.Interval)
		}
	} else {
		// One-time job, deactivate
		job.Active = false
	}

	// Remove completed jobs
	if !job.Active {
		ns.mu.Lock()
		delete(ns.jobs, job.ID)
		ns.mu.Unlock()
	}
}

// GetScheduledJobs returns all scheduled jobs
func (ns *NotificationScheduler) GetScheduledJobs() []*ScheduledJob {
	ns.mu.RLock()
	defer ns.mu.RUnlock()

	jobs := make([]*ScheduledJob, 0, len(ns.jobs))
	for _, job := range ns.jobs {
		jobs = append(jobs, job)
	}

	return jobs
}

// Shutdown gracefully shuts down the scheduler
func (ns *NotificationScheduler) Shutdown() {
	ns.cancel()
}
