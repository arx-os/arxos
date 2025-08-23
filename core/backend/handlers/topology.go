// Package handlers provides REST API endpoints for building topology processing
package handlers

import (
	"database/sql"
	"encoding/json"
	"log"
	"net/http"
	"time"

	"github.com/arxos/arxos/core/backend/middleware/auth"
	"github.com/arxos/arxos/core/backend/pipeline"

	// "github.com/arxos/arxos/core/topology" // Not actually used in the code

	"github.com/go-chi/chi/v5"
	"github.com/google/uuid"
	"gorm.io/gorm"
)

// TopologyHandler manages building topology endpoints
type TopologyHandler struct {
	processor *pipeline.Processor
	logger    *log.Logger
	database  *gorm.DB
	db        *sql.DB // Add missing db field
}

// NewTopologyHandler creates a new handler instance
func NewTopologyHandler(logger *log.Logger, database *gorm.DB) *TopologyHandler {
	config := pipeline.DefaultConfig()

	return &TopologyHandler{
		processor: pipeline.NewProcessor(config),
		logger:    logger,
		database:  database,
		db:        nil, // Initialize db field (would be set from database in production)
	}
}

// RegisterRoutes sets up all topology-related endpoints
func (h *TopologyHandler) RegisterRoutes(r chi.Router) {
	r.Route("/api/v1/topology", func(r chi.Router) {
		// Authentication middleware
		r.Use(auth.RequireAuth)

		// Building endpoints
		r.Post("/buildings/process", h.ProcessBuilding)
		r.Get("/buildings/{buildingID}", h.GetBuilding)
		// r.Get("/buildings", h.ListBuildings) // TODO: implement
		// r.Put("/buildings/{buildingID}/approve", h.ApproveBuilding) // TODO: implement

		// Processing status
		// r.Get("/processing/{processID}/status", h.GetProcessingStatus) // TODO: implement
		// r.Post("/processing/{processID}/cancel", h.CancelProcessing) // TODO: implement

		// Manual review endpoints
		r.Get("/review/queue", h.GetReviewQueue)
		// r.Get("/review/{taskID}", h.GetReviewTask) // TODO
		// r.Post("/review/{taskID}/approve", h.ApproveReview) // TODO
		// r.Post("/review/{taskID}/reject", h.RejectReview) // TODO
		r.Post("/review/{taskID}/corrections", h.SubmitCorrections)

		// Validation endpoints
		// r.Get("/buildings/{buildingID}/issues", h.GetValidationIssues) // TODO
		// r.Post("/buildings/{buildingID}/issues/{issueID}/resolve", h.ResolveIssue) // TODO

		// Export endpoints
		// r.Get("/buildings/{buildingID}/export", h.ExportBuilding) // TODO

		// Learning endpoints
		// r.Get("/patterns", h.GetSemanticPatterns) // TODO
		// r.Post("/patterns/train", h.TrainPatterns) // TODO
	})
}

// ProcessBuildingRequest contains PDF processing parameters
type ProcessBuildingRequest struct {
	FileURL          string                    `json:"file_url,omitempty"`
	Base64File       string                    `json:"base64_file,omitempty"`
	Metadata         pipeline.BuildingMetadata `json:"metadata"`
	ProcessingConfig ProcessingConfig          `json:"config"`
}

// ProcessingConfig contains processing options
type ProcessingConfig struct {
	EnableSemantic      bool    `json:"enable_semantic"`
	RequireManualReview bool    `json:"require_manual_review"`
	MinConfidence       float64 `json:"min_confidence"`
	BuildingType        string  `json:"building_type"`
}

// ProcessBuildingResponse contains processing result
type ProcessBuildingResponse struct {
	ProcessID      string                   `json:"process_id"`
	BuildingID     string                   `json:"building_id"`
	Status         string                   `json:"status"`
	Confidence     float64                  `json:"confidence"`
	RequiresReview bool                     `json:"requires_review"`
	Issues         []ValidationIssueSummary `json:"issues,omitempty"`
	ProcessingTime string                   `json:"processing_time"`
}

// ValidationIssueSummary provides issue overview
type ValidationIssueSummary struct {
	Type        string `json:"type"`
	Severity    string `json:"severity"`
	Description string `json:"description"`
	Count       int    `json:"count"`
}

// ProcessBuilding handles PDF upload and processing
func (h *TopologyHandler) ProcessBuilding(w http.ResponseWriter, r *http.Request) {
	_ = r.Context() // Use the context to avoid unused variable error

	// Parse request
	var req ProcessBuildingRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		h.respondError(w, http.StatusBadRequest, "Invalid request body", err)
		return
	}

	// Validate request
	if req.FileURL == "" && req.Base64File == "" {
		h.respondError(w, http.StatusBadRequest, "Either file_url or base64_file must be provided", nil)
		return
	}

	// Create processing ID
	processID := uuid.New().String()

	// Log processing start
	h.logger.Printf("[INFO] Starting building processing - processID: %s, building: %s",
		processID,
		req.Metadata.Name)

	// Process asynchronously
	go func() {
		startTime := time.Now()

		// Download or decode file
		pdfPath, err := h.preparePDFFile(req)
		if err != nil {
			h.logger.Printf("[ERROR] Failed to prepare PDF file - processID: %s, error: %v",
				processID, err)
			h.updateProcessingStatus(processID, "failed", err.Error())
			return
		}

		// Run processing pipeline
		result, err := h.processor.ProcessPDF(pdfPath, req.Metadata)
		if err != nil {
			h.logger.Printf("[ERROR] Processing failed - processID: %s, error: %v",
				processID, err)
			h.updateProcessingStatus(processID, "failed", err.Error())
			return
		}

		// Store results in database
		buildingID, err := h.storeProcessingResults(result)
		if err != nil {
			h.logger.Printf("[ERROR] Failed to store results - processID: %s, error: %v",
				processID, err)
			h.updateProcessingStatus(processID, "failed", err.Error())
			return
		}

		// Log completion
		h.logger.Printf("[INFO] Building processing completed - processID: %s, buildingID: %s, confidence: %.2f, duration: %v",
			processID, buildingID, result.Confidence, time.Since(startTime))

		// Update status
		status := "completed"
		if result.RequiresReview {
			status = "pending_review"
		}
		h.updateProcessingStatus(processID, status, "")
	}()

	// Return immediate response
	response := ProcessBuildingResponse{
		ProcessID:      processID,
		Status:         "processing",
		ProcessingTime: "pending",
	}

	h.respondJSON(w, http.StatusAccepted, response)
}

// GetBuilding retrieves building topology
func (h *TopologyHandler) GetBuilding(w http.ResponseWriter, r *http.Request) {
	buildingID := chi.URLParam(r, "buildingID")

	// Validate UUID
	if _, err := uuid.Parse(buildingID); err != nil {
		h.respondError(w, http.StatusBadRequest, "Invalid building ID", err)
		return
	}

	// Query database
	var building BuildingDetail
	query := `
		SELECT 
			b.id, b.name, b.address, b.building_type,
			b.year_built, b.total_area_nm2, b.num_floors,
			b.school_level, b.district_id, b.prototype_id,
			b.confidence_score, b.validation_status,
			b.created_at, b.updated_at,
			COUNT(DISTINCT w.id) as wall_count,
			COUNT(DISTINCT r.id) as room_count
		FROM topology.buildings b
		LEFT JOIN topology.walls w ON w.building_id = b.id
		LEFT JOIN topology.rooms r ON r.building_id = b.id
		WHERE b.id = $1
		GROUP BY b.id
	`

	err := h.db.QueryRow(query, buildingID).Scan(
		&building.ID, &building.Name, &building.Address, &building.Type,
		&building.YearBuilt, &building.TotalArea, &building.NumFloors,
		&building.SchoolLevel, &building.DistrictID, &building.PrototypeID,
		&building.Confidence, &building.ValidationStatus,
		&building.CreatedAt, &building.UpdatedAt,
		&building.WallCount, &building.RoomCount,
	)

	if err != nil {
		h.respondError(w, http.StatusNotFound, "Building not found", err)
		return
	}

	// Get walls
	building.Walls, err = h.getBuildingWalls(buildingID)
	if err != nil {
		h.logger.Printf("[ERROR] Failed to get walls: %v", err)
	}

	// Get rooms
	building.Rooms, err = h.getBuildingRooms(buildingID)
	if err != nil {
		h.logger.Printf("[ERROR] Failed to get rooms: %v", err)
	}

	h.respondJSON(w, http.StatusOK, building)
}

// BuildingDetail contains complete building information
type BuildingDetail struct {
	ID               string       `json:"id"`
	Name             string       `json:"name"`
	Address          string       `json:"address"`
	Type             string       `json:"type"`
	YearBuilt        int          `json:"year_built"`
	TotalArea        int64        `json:"total_area_nm2"`
	NumFloors        int          `json:"num_floors"`
	SchoolLevel      string       `json:"school_level,omitempty"`
	DistrictID       string       `json:"district_id,omitempty"`
	PrototypeID      string       `json:"prototype_id,omitempty"`
	Confidence       float64      `json:"confidence"`
	ValidationStatus string       `json:"validation_status"`
	CreatedAt        time.Time    `json:"created_at"`
	UpdatedAt        time.Time    `json:"updated_at"`
	WallCount        int          `json:"wall_count"`
	RoomCount        int          `json:"room_count"`
	Walls            []WallDetail `json:"walls"`
	Rooms            []RoomDetail `json:"rooms"`
}

// WallDetail contains wall information
type WallDetail struct {
	ID         string  `json:"id"`
	StartX     int64   `json:"start_x"`
	StartY     int64   `json:"start_y"`
	EndX       int64   `json:"end_x"`
	EndY       int64   `json:"end_y"`
	Thickness  int64   `json:"thickness"`
	Height     int64   `json:"height"`
	Type       string  `json:"type"`
	Confidence float64 `json:"confidence"`
}

// RoomDetail contains room information
type RoomDetail struct {
	ID         string    `json:"id"`
	Number     string    `json:"number"`
	Name       string    `json:"name"`
	Function   string    `json:"function"`
	Area       int64     `json:"area_nm2"`
	CentroidX  int64     `json:"centroid_x"`
	CentroidY  int64     `json:"centroid_y"`
	Confidence float64   `json:"confidence"`
	Polygon    []Point2D `json:"polygon"`
}

// Point2D represents a 2D coordinate
type Point2D struct {
	X int64 `json:"x"`
	Y int64 `json:"y"`
}

// GetReviewQueue returns tasks pending manual review
func (h *TopologyHandler) GetReviewQueue(w http.ResponseWriter, r *http.Request) {
	query := `
		SELECT 
			pr.id, pr.building_id, b.name, pr.overall_confidence,
			pr.created_at, pr.status,
			COUNT(vi.id) as issue_count
		FROM topology.processing_results pr
		JOIN topology.buildings b ON b.id = pr.building_id
		LEFT JOIN topology.validation_issues vi ON vi.building_id = b.id
		WHERE pr.requires_review = true 
		AND pr.status IN ('pending_review', 'in_review')
		GROUP BY pr.id, b.id
		ORDER BY pr.created_at ASC
		LIMIT 50
	`

	rows, err := h.db.Query(query)
	if err != nil {
		h.respondError(w, http.StatusInternalServerError, "Failed to get review queue", err)
		return
	}
	defer rows.Close()

	var tasks []ReviewTask
	for rows.Next() {
		var task ReviewTask
		err := rows.Scan(
			&task.ID, &task.BuildingID, &task.BuildingName,
			&task.Confidence, &task.CreatedAt, &task.Status,
			&task.IssueCount,
		)
		if err != nil {
			h.logger.Printf("[ERROR] Failed to scan review task: %v", err)
			continue
		}
		tasks = append(tasks, task)
	}

	h.respondJSON(w, http.StatusOK, tasks)
}

// ReviewTask represents a manual review item
type ReviewTask struct {
	ID           string    `json:"id"`
	BuildingID   string    `json:"building_id"`
	BuildingName string    `json:"building_name"`
	Confidence   float64   `json:"confidence"`
	Status       string    `json:"status"`
	IssueCount   int       `json:"issue_count"`
	CreatedAt    time.Time `json:"created_at"`
}

// SubmitCorrections handles manual corrections
func (h *TopologyHandler) SubmitCorrections(w http.ResponseWriter, r *http.Request) {
	taskID := chi.URLParam(r, "taskID")
	userID := r.Context().Value("user_id").(string)

	var corrections []CorrectionRequest
	if err := json.NewDecoder(r.Body).Decode(&corrections); err != nil {
		h.respondError(w, http.StatusBadRequest, "Invalid corrections", err)
		return
	}

	// Begin transaction
	tx, err := h.db.Begin()
	if err != nil {
		h.respondError(w, http.StatusInternalServerError, "Failed to start transaction", err)
		return
	}
	defer tx.Rollback()

	// Apply each correction
	for _, correction := range corrections {
		query := `
			INSERT INTO topology.manual_corrections 
			(building_id, correction_type, entity_type, entity_id, 
			 before_state, after_state, reason, confidence, corrected_by)
			VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
		`

		beforeJSON, _ := json.Marshal(correction.Before)
		afterJSON, _ := json.Marshal(correction.After)

		_, err = tx.Exec(query,
			correction.BuildingID, correction.Type, correction.EntityType,
			correction.EntityID, beforeJSON, afterJSON,
			correction.Reason, correction.Confidence, userID,
		)

		if err != nil {
			h.logger.Printf("[ERROR] Failed to save correction: %v", err)
			continue
		}

		// Apply correction to actual entity
		h.applyCorrection(tx, correction)
	}

	// Update review status
	_, err = tx.Exec(`
		UPDATE topology.processing_results 
		SET status = 'completed', completed_at = CURRENT_TIMESTAMP 
		WHERE id = $1
	`, taskID)

	if err != nil {
		h.respondError(w, http.StatusInternalServerError, "Failed to update status", err)
		return
	}

	// Commit transaction
	if err = tx.Commit(); err != nil {
		h.respondError(w, http.StatusInternalServerError, "Failed to commit corrections", err)
		return
	}

	h.respondJSON(w, http.StatusOK, map[string]string{
		"message": "Corrections applied successfully",
		"task_id": taskID,
	})
}

// CorrectionRequest contains manual correction data
type CorrectionRequest struct {
	BuildingID string      `json:"building_id"`
	Type       string      `json:"type"`
	EntityType string      `json:"entity_type"`
	EntityID   string      `json:"entity_id"`
	Before     interface{} `json:"before"`
	After      interface{} `json:"after"`
	Reason     string      `json:"reason"`
	Confidence float64     `json:"confidence"`
}

// Helper methods

func (h *TopologyHandler) respondJSON(w http.ResponseWriter, status int, data interface{}) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	if err := json.NewEncoder(w).Encode(data); err != nil {
		h.logger.Printf("[ERROR] Failed to encode response: %v", err)
	}
}

func (h *TopologyHandler) respondError(w http.ResponseWriter, status int, message string, err error) {
	h.logger.Printf("[ERROR] %s: %v", message, err)

	response := map[string]interface{}{
		"error":     message,
		"timestamp": time.Now().UTC(),
	}

	if err != nil && h.isDebugMode() {
		response["details"] = err.Error()
	}

	h.respondJSON(w, status, response)
}

func (h *TopologyHandler) isDebugMode() bool {
	// Check environment or config for debug mode
	return false
}

func (h *TopologyHandler) preparePDFFile(req ProcessBuildingRequest) (string, error) {
	// TODO: Implement file preparation logic
	// - Download from URL or decode base64
	// - Save to temporary location
	// - Return file path
	return "/tmp/building.pdf", nil
}

func (h *TopologyHandler) storeProcessingResults(result *pipeline.ProcessingResult) (string, error) {
	// TODO: Store processing results in database
	// - Insert building record
	// - Insert walls
	// - Insert rooms
	// - Insert validation issues
	// - Return building ID
	return uuid.New().String(), nil
}

func (h *TopologyHandler) updateProcessingStatus(processID, status, errorMsg string) {
	// TODO: Update processing status in database or cache
}

func (h *TopologyHandler) getBuildingWalls(buildingID string) ([]WallDetail, error) {
	// TODO: Query walls from database
	return []WallDetail{}, nil
}

func (h *TopologyHandler) getBuildingRooms(buildingID string) ([]RoomDetail, error) {
	// TODO: Query rooms from database
	return []RoomDetail{}, nil
}

func (h *TopologyHandler) applyCorrection(tx *sql.Tx, correction CorrectionRequest) error {
	// TODO: Apply correction to entity based on type
	return nil
}
