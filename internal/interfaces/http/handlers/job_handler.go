package handlers

import (
	"encoding/json"
	"fmt"
	"net/http"
	"time"

	"github.com/arx-os/arxos/internal/domain"
	"github.com/arx-os/arxos/internal/infrastructure/jobs"
	"github.com/arx-os/arxos/internal/interfaces/http/types"
)

// JobHandler handles job-related HTTP requests
type JobHandler struct {
	*types.BaseHandler
	jobQueue *jobs.JobQueue
	logger   domain.Logger
}

// NewJobHandler creates a new job handler
func NewJobHandler(
	server *types.Server,
	jobQueue *jobs.JobQueue,
	logger domain.Logger,
) *JobHandler {
	return &JobHandler{
		BaseHandler: types.NewBaseHandler(server),
		jobQueue:    jobQueue,
		logger:      logger,
	}
}

// CreateJobRequest represents a job creation request
type CreateJobRequest struct {
	Type        string                 `json:"type"`
	Priority    int                    `json:"priority"`
	Data        map[string]interface{} `json:"data"`
	ScheduledAt *time.Time             `json:"scheduled_at,omitempty"`
	MaxAttempts int                    `json:"max_attempts,omitempty"`
	Metadata    map[string]interface{} `json:"metadata,omitempty"`
}

// JobResponse represents a job response
type JobResponse struct {
	ID          string                 `json:"id"`
	Type        string                 `json:"type"`
	Priority    int                    `json:"priority"`
	Status      string                 `json:"status"`
	CreatedAt   time.Time              `json:"created_at"`
	ScheduledAt time.Time              `json:"scheduled_at"`
	Attempts    int                    `json:"attempts"`
	MaxAttempts int                    `json:"max_attempts"`
	Result      interface{}            `json:"result,omitempty"`
	Error       string                 `json:"error,omitempty"`
	Metadata    map[string]interface{} `json:"metadata,omitempty"`
}

// JobStatsResponse represents job queue statistics
type JobStatsResponse struct {
	Running       bool                     `json:"running"`
	QueueSize     int                      `json:"queue_size"`
	MaxWorkers    int                      `json:"max_workers"`
	ActiveWorkers int                      `json:"active_workers"`
	Workers       []map[string]interface{} `json:"workers"`
	Config        map[string]interface{}   `json:"config"`
}

// CreateJob creates a new background job
func (h *JobHandler) CreateJob(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	defer func() {
		h.LogRequest(r, http.StatusOK, time.Since(start))
	}()

	h.logger.Info("Job creation requested")

	// Validate content type
	if !h.ValidateContentType(r, "application/json") {
		h.HandleError(w, r, fmt.Errorf("content type must be application/json"), http.StatusBadRequest)
		return
	}

	var req CreateJobRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		h.HandleError(w, r, fmt.Errorf("invalid request body: %v", err), http.StatusBadRequest)
		return
	}

	// Validate request
	if req.Type == "" {
		h.HandleError(w, r, fmt.Errorf("job type is required"), http.StatusBadRequest)
		return
	}

	// Create job
	job := jobs.NewJob(req.Type, req.Data)

	// Set priority
	if req.Priority > 0 {
		job.Priority = jobs.Priority(req.Priority)
	}

	// Set scheduled time
	if req.ScheduledAt != nil {
		job.ScheduledAt = *req.ScheduledAt
	}

	// Set max attempts
	if req.MaxAttempts > 0 {
		job.MaxAttempts = req.MaxAttempts
	}

	// Set metadata
	if req.Metadata != nil {
		job.Metadata = req.Metadata
	}

	// Enqueue job
	if err := h.jobQueue.Enqueue(*job); err != nil {
		h.logger.Error("Failed to enqueue job", "error", err)
		h.HandleError(w, r, fmt.Errorf("failed to enqueue job: %v", err), http.StatusInternalServerError)
		return
	}

	// Create response
	response := JobResponse{
		ID:          job.ID,
		Type:        job.Type,
		Priority:    int(job.Priority),
		Status:      string(job.Status),
		CreatedAt:   job.CreatedAt,
		ScheduledAt: job.ScheduledAt,
		Attempts:    job.Attempts,
		MaxAttempts: job.MaxAttempts,
		Metadata:    job.Metadata,
	}

	h.logger.Info("Job created successfully", "job_id", job.ID, "type", job.Type)
	h.RespondJSON(w, http.StatusCreated, response)
}

// CreateBulkJobs creates multiple jobs
func (h *JobHandler) CreateBulkJobs(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	defer func() {
		h.LogRequest(r, http.StatusOK, time.Since(start))
	}()

	h.logger.Info("Bulk job creation requested")

	// Validate content type
	if !h.ValidateContentType(r, "application/json") {
		h.HandleError(w, r, fmt.Errorf("content type must be application/json"), http.StatusBadRequest)
		return
	}

	var reqs []CreateJobRequest
	if err := json.NewDecoder(r.Body).Decode(&reqs); err != nil {
		h.HandleError(w, r, fmt.Errorf("invalid request body: %v", err), http.StatusBadRequest)
		return
	}

	if len(reqs) == 0 {
		h.HandleError(w, r, fmt.Errorf("jobs array cannot be empty"), http.StatusBadRequest)
		return
	}

	var responses []JobResponse
	var errors []string

	// Process each job
	for i, req := range reqs {
		if req.Type == "" {
			errors = append(errors, fmt.Sprintf("Job %d: type is required", i))
			continue
		}

		// Create job
		job := jobs.NewJob(req.Type, req.Data)

		// Set priority
		if req.Priority > 0 {
			job.Priority = jobs.Priority(req.Priority)
		}

		// Set scheduled time
		if req.ScheduledAt != nil {
			job.ScheduledAt = *req.ScheduledAt
		}

		// Set max attempts
		if req.MaxAttempts > 0 {
			job.MaxAttempts = req.MaxAttempts
		}

		// Set metadata
		if req.Metadata != nil {
			job.Metadata = req.Metadata
		}

		// Enqueue job
		if err := h.jobQueue.Enqueue(*job); err != nil {
			errors = append(errors, fmt.Sprintf("Job %d: failed to enqueue: %v", i, err))
			continue
		}

		// Create response
		response := JobResponse{
			ID:          job.ID,
			Type:        job.Type,
			Priority:    int(job.Priority),
			Status:      string(job.Status),
			CreatedAt:   job.CreatedAt,
			ScheduledAt: job.ScheduledAt,
			Attempts:    job.Attempts,
			MaxAttempts: job.MaxAttempts,
			Metadata:    job.Metadata,
		}

		responses = append(responses, response)
	}

	result := map[string]interface{}{
		"created": len(responses),
		"failed":  len(errors),
		"jobs":    responses,
	}

	if len(errors) > 0 {
		result["errors"] = errors
	}

	h.logger.Info("Bulk job creation completed", "created", len(responses), "failed", len(errors))
	h.RespondJSON(w, http.StatusCreated, result)
}

// GetJobStats returns job queue statistics
func (h *JobHandler) GetJobStats(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	defer func() {
		h.LogRequest(r, http.StatusOK, time.Since(start))
	}()

	h.logger.Debug("Job stats requested")

	stats := h.jobQueue.GetQueueStats()

	response := JobStatsResponse{
		Running:       stats["running"].(bool),
		QueueSize:     stats["queue_size"].(int),
		MaxWorkers:    stats["max_workers"].(int),
		ActiveWorkers: stats["active_workers"].(int),
		Workers:       stats["workers"].([]map[string]interface{}),
		Config:        stats["config"].(map[string]interface{}),
	}

	h.RespondJSON(w, http.StatusOK, response)
}

// CreateScheduledJob creates a scheduled job
func (h *JobHandler) CreateScheduledJob(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	defer func() {
		h.LogRequest(r, http.StatusOK, time.Since(start))
	}()

	h.logger.Info("Scheduled job creation requested")

	// Validate content type
	if !h.ValidateContentType(r, "application/json") {
		h.HandleError(w, r, fmt.Errorf("content type must be application/json"), http.StatusBadRequest)
		return
	}

	var req struct {
		Type        string                 `json:"type"`
		Priority    int                    `json:"priority"`
		Data        map[string]interface{} `json:"data"`
		ScheduledAt time.Time              `json:"scheduled_at"`
		MaxAttempts int                    `json:"max_attempts,omitempty"`
		Metadata    map[string]interface{} `json:"metadata,omitempty"`
	}

	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		h.HandleError(w, r, fmt.Errorf("invalid request body: %v", err), http.StatusBadRequest)
		return
	}

	// Validate request
	if req.Type == "" {
		h.HandleError(w, r, fmt.Errorf("job type is required"), http.StatusBadRequest)
		return
	}

	if req.ScheduledAt.IsZero() {
		h.HandleError(w, r, fmt.Errorf("scheduled_at is required"), http.StatusBadRequest)
		return
	}

	// Create scheduled job
	job := jobs.NewScheduledJob(req.Type, req.Data, req.ScheduledAt)

	// Set priority
	if req.Priority > 0 {
		job.Priority = jobs.Priority(req.Priority)
	}

	// Set max attempts
	if req.MaxAttempts > 0 {
		job.MaxAttempts = req.MaxAttempts
	}

	// Set metadata
	if req.Metadata != nil {
		job.Metadata = req.Metadata
	}

	// Enqueue job
	if err := h.jobQueue.Enqueue(*job); err != nil {
		h.logger.Error("Failed to enqueue scheduled job", "error", err)
		h.HandleError(w, r, fmt.Errorf("failed to enqueue scheduled job: %v", err), http.StatusInternalServerError)
		return
	}

	// Create response
	response := JobResponse{
		ID:          job.ID,
		Type:        job.Type,
		Priority:    int(job.Priority),
		Status:      string(job.Status),
		CreatedAt:   job.CreatedAt,
		ScheduledAt: job.ScheduledAt,
		Attempts:    job.Attempts,
		MaxAttempts: job.MaxAttempts,
		Metadata:    job.Metadata,
	}

	h.logger.Info("Scheduled job created successfully", "job_id", job.ID, "type", job.Type, "scheduled_at", job.ScheduledAt)
	h.RespondJSON(w, http.StatusCreated, response)
}

// CreateRecurringJob creates a recurring job
func (h *JobHandler) CreateRecurringJob(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	defer func() {
		h.LogRequest(r, http.StatusOK, time.Since(start))
	}()

	h.logger.Info("Recurring job creation requested")

	// Validate content type
	if !h.ValidateContentType(r, "application/json") {
		h.HandleError(w, r, fmt.Errorf("content type must be application/json"), http.StatusBadRequest)
		return
	}

	var req struct {
		Type        string                 `json:"type"`
		Priority    int                    `json:"priority"`
		Data        map[string]interface{} `json:"data"`
		Interval    string                 `json:"interval"` // e.g., "1h", "30m", "1d"
		StartAt     *time.Time             `json:"start_at,omitempty"`
		EndAt       *time.Time             `json:"end_at,omitempty"`
		MaxAttempts int                    `json:"max_attempts,omitempty"`
		Metadata    map[string]interface{} `json:"metadata,omitempty"`
	}

	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		h.HandleError(w, r, fmt.Errorf("invalid request body: %v", err), http.StatusBadRequest)
		return
	}

	// Validate request
	if req.Type == "" {
		h.HandleError(w, r, fmt.Errorf("job type is required"), http.StatusBadRequest)
		return
	}

	if req.Interval == "" {
		h.HandleError(w, r, fmt.Errorf("interval is required"), http.StatusBadRequest)
		return
	}

	// Parse interval
	_, err := time.ParseDuration(req.Interval)
	if err != nil {
		h.HandleError(w, r, fmt.Errorf("invalid interval format: %v", err), http.StatusBadRequest)
		return
	}

	// Determine start time
	startAt := time.Now()
	if req.StartAt != nil {
		startAt = *req.StartAt
	}

	// Create first job
	job := jobs.NewScheduledJob(req.Type, req.Data, startAt)

	// Set priority
	if req.Priority > 0 {
		job.Priority = jobs.Priority(req.Priority)
	}

	// Set max attempts
	if req.MaxAttempts > 0 {
		job.MaxAttempts = req.MaxAttempts
	}

	// Set metadata
	if req.Metadata != nil {
		job.Metadata = req.Metadata
	}

	// Add recurring job metadata
	job.Metadata["recurring"] = true
	job.Metadata["interval"] = req.Interval
	if req.EndAt != nil {
		job.Metadata["end_at"] = req.EndAt
	}

	// Enqueue job
	if err := h.jobQueue.Enqueue(*job); err != nil {
		h.logger.Error("Failed to enqueue recurring job", "error", err)
		h.HandleError(w, r, fmt.Errorf("failed to enqueue recurring job: %v", err), http.StatusInternalServerError)
		return
	}

	// Create response
	response := JobResponse{
		ID:          job.ID,
		Type:        job.Type,
		Priority:    int(job.Priority),
		Status:      string(job.Status),
		CreatedAt:   job.CreatedAt,
		ScheduledAt: job.ScheduledAt,
		Attempts:    job.Attempts,
		MaxAttempts: job.MaxAttempts,
		Metadata:    job.Metadata,
	}

	h.logger.Info("Recurring job created successfully", "job_id", job.ID, "type", job.Type, "interval", req.Interval)
	h.RespondJSON(w, http.StatusCreated, response)
}

// GetJobTypes returns available job types
func (h *JobHandler) GetJobTypes(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	defer func() {
		h.LogRequest(r, http.StatusOK, time.Since(start))
	}()

	h.logger.Debug("Job types requested")

	jobTypes := []map[string]interface{}{
		{
			"type":        "ifc_import",
			"description": "Import IFC files into the system",
			"parameters": map[string]interface{}{
				"repository_id": "string (required)",
				"ifc_data":      "bytes (required)",
			},
		},
		{
			"type":        "ifc_export",
			"description": "Export IFC files from the system",
			"parameters": map[string]interface{}{
				"repository_id": "string (required)",
				"ifc_file_id":   "string (required)",
				"format":        "string (optional, default: IFC4)",
			},
		},
		{
			"type":        "ifc_validate",
			"description": "Validate IFC file structure",
			"parameters": map[string]interface{}{
				"ifc_data": "bytes (required)",
			},
		},
		{
			"type":        "analytics",
			"description": "Generate analytics reports",
			"parameters": map[string]interface{}{
				"analysis_type": "string (required)",
				"building_id":   "string (required)",
				"start_date":    "string (optional)",
				"end_date":      "string (optional)",
			},
		},
		{
			"type":        "notification",
			"description": "Send notifications",
			"parameters": map[string]interface{}{
				"type":      "string (required: email, sms, push, webhook)",
				"recipient": "string (required)",
				"message":   "string (required)",
			},
		},
	}

	h.RespondJSON(w, http.StatusOK, map[string]interface{}{
		"job_types": jobTypes,
		"count":     len(jobTypes),
	})
}
