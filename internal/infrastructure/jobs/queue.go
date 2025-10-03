package jobs

import (
	"context"
	"fmt"
	"sync"
	"time"

	"github.com/arx-os/arxos/internal/domain"
)

// JobQueue manages background job processing
type JobQueue struct {
	jobs      chan Job
	workers   []*Worker
	mu        sync.RWMutex
	logger    domain.Logger
	config    *QueueConfig
	running   bool
	ctx       context.Context
	cancel    context.CancelFunc
}

// QueueConfig represents job queue configuration
type QueueConfig struct {
	MaxWorkers    int           `json:"max_workers"`
	QueueSize     int           `json:"queue_size"`
	WorkerTimeout time.Duration `json:"worker_timeout"`
	RetryAttempts int           `json:"retry_attempts"`
	RetryDelay    time.Duration `json:"retry_delay"`
	CleanupInterval time.Duration `json:"cleanup_interval"`
}

// DefaultQueueConfig returns default queue configuration
func DefaultQueueConfig() *QueueConfig {
	return &QueueConfig{
		MaxWorkers:      5,
		QueueSize:       1000,
		WorkerTimeout:   30 * time.Minute,
		RetryAttempts:   3,
		RetryDelay:      5 * time.Second,
		CleanupInterval: 1 * time.Hour,
	}
}

// NewJobQueue creates a new job queue
func NewJobQueue(config *QueueConfig, logger domain.Logger) *JobQueue {
	if config == nil {
		config = DefaultQueueConfig()
	}

	ctx, cancel := context.WithCancel(context.Background())

	return &JobQueue{
		jobs:    make(chan Job, config.QueueSize),
		workers: make([]*Worker, 0, config.MaxWorkers),
		logger:  logger,
		config:  config,
		ctx:     ctx,
		cancel:  cancel,
	}
}

// Start starts the job queue
func (jq *JobQueue) Start() error {
	jq.mu.Lock()
	defer jq.mu.Unlock()

	if jq.running {
		return fmt.Errorf("job queue is already running")
	}

	jq.logger.Info("Starting job queue", 
		"max_workers", jq.config.MaxWorkers,
		"queue_size", jq.config.QueueSize,
	)

	// Start workers
	for i := 0; i < jq.config.MaxWorkers; i++ {
		worker := NewWorker(i, jq.jobs, jq.logger, jq.config)
		jq.workers = append(jq.workers, worker)
		go worker.Start(jq.ctx)
	}

	// Start cleanup routine
	go jq.startCleanupRoutine()

	jq.running = true
	jq.logger.Info("Job queue started successfully")
	return nil
}

// Stop stops the job queue
func (jq *JobQueue) Stop() error {
	jq.mu.Lock()
	defer jq.mu.Unlock()

	if !jq.running {
		return fmt.Errorf("job queue is not running")
	}

	jq.logger.Info("Stopping job queue")

	// Cancel context to signal workers to stop
	jq.cancel()

	// Wait for workers to finish
	for _, worker := range jq.workers {
		worker.Stop()
	}

	// Close job channel
	close(jq.jobs)

	jq.running = false
	jq.logger.Info("Job queue stopped successfully")
	return nil
}

// Enqueue adds a job to the queue
func (jq *JobQueue) Enqueue(job Job) error {
	jq.mu.RLock()
	defer jq.mu.RUnlock()

	if !jq.running {
		return fmt.Errorf("job queue is not running")
	}

	select {
	case jq.jobs <- job:
		jq.logger.Debug("Job enqueued", "job_id", job.ID, "type", job.Type)
		return nil
	case <-jq.ctx.Done():
		return fmt.Errorf("job queue is shutting down")
	default:
		return fmt.Errorf("job queue is full")
	}
}

// EnqueueWithPriority adds a job to the queue with priority
func (jq *JobQueue) EnqueueWithPriority(job Job, priority Priority) error {
	job.Priority = priority
	return jq.Enqueue(job)
}

// GetQueueStats returns queue statistics
func (jq *JobQueue) GetQueueStats() map[string]interface{} {
	jq.mu.RLock()
	defer jq.mu.RUnlock()

	workerStats := make([]map[string]interface{}, len(jq.workers))
	for i, worker := range jq.workers {
		workerStats[i] = worker.GetStats()
	}

	return map[string]interface{}{
		"running":       jq.running,
		"queue_size":    len(jq.jobs),
		"max_workers":   jq.config.MaxWorkers,
		"active_workers": len(jq.workers),
		"workers":       workerStats,
		"config":        jq.config,
	}
}

// startCleanupRoutine starts the cleanup routine
func (jq *JobQueue) startCleanupRoutine() {
	ticker := time.NewTicker(jq.config.CleanupInterval)
	defer ticker.Stop()

	for {
		select {
		case <-jq.ctx.Done():
			return
		case <-ticker.C:
			jq.cleanup()
		}
	}
}

// cleanup performs cleanup operations
func (jq *JobQueue) cleanup() {
	jq.logger.Debug("Performing job queue cleanup")
	
	// Clean up completed jobs, remove old logs, etc.
	// This would be implemented based on specific requirements
}

// Job represents a background job
type Job struct {
	ID          string                 `json:"id"`
	Type        string                 `json:"type"`
	Priority    Priority               `json:"priority"`
	Data        map[string]interface{} `json:"data"`
	CreatedAt   time.Time              `json:"created_at"`
	ScheduledAt time.Time              `json:"scheduled_at"`
	Attempts    int                    `json:"attempts"`
	MaxAttempts int                    `json:"max_attempts"`
	Status      JobStatus              `json:"status"`
	Result      interface{}            `json:"result,omitempty"`
	Error       string                 `json:"error,omitempty"`
	Metadata    map[string]interface{} `json:"metadata,omitempty"`
}

// Priority represents job priority
type Priority int

const (
	LowPriority Priority = iota
	NormalPriority
	HighPriority
	CriticalPriority
)

// JobStatus represents job status
type JobStatus string

const (
	JobStatusPending   JobStatus = "pending"
	JobStatusRunning   JobStatus = "running"
	JobStatusCompleted JobStatus = "completed"
	JobStatusFailed    JobStatus = "failed"
	JobStatusCancelled JobStatus = "cancelled"
)

// NewJob creates a new job
func NewJob(jobType string, data map[string]interface{}) *Job {
	return &Job{
		ID:          generateJobID(),
		Type:        jobType,
		Priority:    NormalPriority,
		Data:        data,
		CreatedAt:   time.Now(),
		ScheduledAt: time.Now(),
		Attempts:    0,
		MaxAttempts: 3,
		Status:      JobStatusPending,
		Metadata:    make(map[string]interface{}),
	}
}

// NewScheduledJob creates a new scheduled job
func NewScheduledJob(jobType string, data map[string]interface{}, scheduledAt time.Time) *Job {
	job := NewJob(jobType, data)
	job.ScheduledAt = scheduledAt
	return job
}

// generateJobID generates a unique job ID
func generateJobID() string {
	return fmt.Sprintf("job_%d", time.Now().UnixNano())
}

// Worker represents a job worker
type Worker struct {
	ID       int
	jobs     <-chan Job
	logger   domain.Logger
	config   *QueueConfig
	running  bool
	mu       sync.RWMutex
	stats    *WorkerStats
	processors map[string]JobProcessor
}

// WorkerStats represents worker statistics
type WorkerStats struct {
	JobsProcessed int64         `json:"jobs_processed"`
	JobsFailed    int64         `json:"jobs_failed"`
	JobsSucceeded int64         `json:"jobs_succeeded"`
	TotalTime     time.Duration `json:"total_time"`
	AverageTime   time.Duration `json:"average_time"`
	LastJobTime   time.Time     `json:"last_job_time"`
	Uptime        time.Duration `json:"uptime"`
	StartTime     time.Time     `json:"start_time"`
}

// NewWorker creates a new worker
func NewWorker(id int, jobs <-chan Job, logger domain.Logger, config *QueueConfig) *Worker {
	return &Worker{
		ID:       id,
		jobs:     jobs,
		logger:   logger,
		config:   config,
		stats:    &WorkerStats{StartTime: time.Now()},
		processors: make(map[string]JobProcessor),
	}
}

// RegisterProcessor registers a job processor
func (w *Worker) RegisterProcessor(jobType string, processor JobProcessor) {
	w.mu.Lock()
	defer w.mu.Unlock()
	w.processors[jobType] = processor
}

// Start starts the worker
func (w *Worker) Start(ctx context.Context) {
	w.mu.Lock()
	w.running = true
	w.mu.Unlock()

	w.logger.Info("Worker started", "worker_id", w.ID)

	for {
		select {
		case <-ctx.Done():
			w.logger.Info("Worker stopping", "worker_id", w.ID)
			w.mu.Lock()
			w.running = false
			w.mu.Unlock()
			return

		case job := <-w.jobs:
			w.processJob(job)
		}
	}
}

// Stop stops the worker
func (w *Worker) Stop() {
	w.mu.Lock()
	defer w.mu.Unlock()
	w.running = false
}

// processJob processes a job
func (w *Worker) processJob(job Job) {
	start := time.Now()
	
	w.mu.Lock()
	w.stats.LastJobTime = time.Now()
	w.mu.Unlock()

	w.logger.Debug("Processing job", 
		"worker_id", w.ID,
		"job_id", job.ID,
		"job_type", job.Type,
	)

	// Check if job is scheduled for the future
	if job.ScheduledAt.After(time.Now()) {
		// Re-queue the job for later
		time.Sleep(time.Until(job.ScheduledAt))
	}

	// Get processor for job type
	processor, exists := w.processors[job.Type]
	if !exists {
		w.logger.Error("No processor found for job type", 
			"worker_id", w.ID,
			"job_id", job.ID,
			"job_type", job.Type,
		)
		w.updateStats(false, time.Since(start))
		return
	}

	// Process the job
	ctx, cancel := context.WithTimeout(context.Background(), w.config.WorkerTimeout)
	defer cancel()

	result, err := processor.Process(ctx, job)
	
	duration := time.Since(start)
	
	if err != nil {
		w.logger.Error("Job processing failed", 
			"worker_id", w.ID,
			"job_id", job.ID,
			"error", err,
			"duration", duration,
		)
		w.updateStats(false, duration)
	} else {
		w.logger.Debug("Job processed successfully", 
			"worker_id", w.ID,
			"job_id", job.ID,
			"duration", duration,
		)
		w.updateStats(true, duration)
	}

	// Store result if needed
	if result != nil {
		w.logger.Debug("Job result", 
			"worker_id", w.ID,
			"job_id", job.ID,
			"result", result,
		)
	}
}

// updateStats updates worker statistics
func (w *Worker) updateStats(success bool, duration time.Duration) {
	w.mu.Lock()
	defer w.mu.Unlock()

	w.stats.JobsProcessed++
	if success {
		w.stats.JobsSucceeded++
	} else {
		w.stats.JobsFailed++
	}

	w.stats.TotalTime += duration
	w.stats.AverageTime = w.stats.TotalTime / time.Duration(w.stats.JobsProcessed)
	w.stats.Uptime = time.Since(w.stats.StartTime)
}

// GetStats returns worker statistics
func (w *Worker) GetStats() map[string]interface{} {
	w.mu.RLock()
	defer w.mu.RUnlock()

	return map[string]interface{}{
		"id":              w.ID,
		"running":         w.running,
		"jobs_processed":  w.stats.JobsProcessed,
		"jobs_succeeded":  w.stats.JobsSucceeded,
		"jobs_failed":     w.stats.JobsFailed,
		"total_time":      w.stats.TotalTime,
		"average_time":    w.stats.AverageTime,
		"last_job_time":   w.stats.LastJobTime,
		"uptime":          w.stats.Uptime,
		"start_time":      w.stats.StartTime,
	}
}

// JobProcessor defines the interface for job processors
type JobProcessor interface {
	Process(ctx context.Context, job Job) (interface{}, error)
	GetJobType() string
}

// BaseProcessor provides a base implementation for job processors
type BaseProcessor struct {
	jobType string
	logger  domain.Logger
}

// NewBaseProcessor creates a new base processor
func NewBaseProcessor(jobType string, logger domain.Logger) *BaseProcessor {
	return &BaseProcessor{
		jobType: jobType,
		logger:  logger,
	}
}

// GetJobType returns the job type
func (bp *BaseProcessor) GetJobType() string {
	return bp.jobType
}

// Process processes a job (to be implemented by specific processors)
func (bp *BaseProcessor) Process(ctx context.Context, job Job) (interface{}, error) {
	return nil, fmt.Errorf("Process method not implemented")
}
