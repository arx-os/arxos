// Package handlers provides REST API endpoints for building topology processing
package handlers

import (
	"encoding/json"
	"fmt"
	"net/http"
	"time"

	// "github.com/arxos/arxos/core/backend/db"
	// "github.com/arxos/arxos/core/backend/middleware"
	"github.com/arxos/arxos/core/pipeline"
	// "github.com/arxos/arxos/core/topology"

	"github.com/go-chi/chi/v5"
	"github.com/google/uuid"
	"go.uber.org/zap"
	"gorm.io/gorm"
)

// TopologyHandler manages building topology endpoints
type TopologyHandler struct {
	processor *pipeline.Processor
	logger    *zap.Logger
	database  *gorm.DB
}

// NewTopologyHandler creates a new handler instance
func NewTopologyHandler(logger *zap.Logger, database *gorm.DB) *TopologyHandler {
	config := pipeline.DefaultConfig()
	
	return &TopologyHandler{
		processor: pipeline.NewProcessor(config),
		logger:    logger,
		database:  database,
	}
}

// RegisterRoutes sets up all topology-related endpoints
func (h *TopologyHandler) RegisterRoutes(r chi.Router) {
	r.Route("/api/v1/topology", func(r chi.Router) {
		// Authentication middleware  
		// r.Use(middleware.RequireAuth) // TODO: Enable when auth middleware is ready
		
		// Building endpoints
		r.Post("/buildings/process", h.ProcessBuilding)
		r.Get("/buildings/{buildingID}", h.GetBuilding)
		r.Get("/buildings", h.ListBuildings)
		r.Put("/buildings/{buildingID}/approve", h.ApproveBuilding)
		
		// Processing status
		r.Get("/processing/{processID}/status", h.GetProcessingStatus)
		r.Post("/processing/{processID}/cancel", h.CancelProcessing)
		
		// Manual review endpoints
		r.Get("/review/queue", h.GetReviewQueue)
		r.Get("/review/{taskID}", h.GetReviewTask)
		r.Post("/review/{taskID}/approve", h.ApproveReview)
		r.Post("/review/{taskID}/reject", h.RejectReview)
		r.Post("/review/{taskID}/corrections", h.SubmitCorrections)
		
		// Validation endpoints
		r.Get("/buildings/{buildingID}/issues", h.GetValidationIssues)
		r.Post("/buildings/{buildingID}/issues/{issueID}/resolve", h.ResolveIssue)
		
		// Export endpoints
		r.Get("/buildings/{buildingID}/export", h.ExportBuilding)
		
		// Learning endpoints
		r.Get("/patterns", h.GetSemanticPatterns)
		r.Post("/patterns/train", h.TrainPatterns)
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
	ProcessID     string                   `json:"process_id"`
	BuildingID    string                   `json:"building_id"`
	Status        string                   `json:"status"`
	Confidence    float64                  `json:"confidence"`
	RequiresReview bool                    `json:"requires_review"`
	Issues        []ValidationIssueSummary `json:"issues,omitempty"`
	ProcessingTime string                  `json:"processing_time"`
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
	// ctx := r.Context() // TODO: Use context when implementing
	
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
	h.logger.Info("Starting building processing",
		zap.String("process_id", processID),
		zap.String("building_name", req.Metadata.BuildingName),
		zap.String("building_type", req.Metadata.BuildingType),
	)
	
	// Process asynchronously
	go func() {
		startTime := time.Now()
		
		// Download or decode file
		pdfPath, err := h.preparePDFFile(req)
		if err != nil {
			h.logger.Error("Failed to prepare PDF file",
				zap.String("process_id", processID),
				zap.Error(err),
			)
			h.updateProcessingStatus(processID, "failed", err.Error())
			return
		}
		
		// Run processing pipeline
		result, err := h.processor.ProcessPDF(pdfPath, req.Metadata)
		if err != nil {
			h.logger.Error("Processing failed",
				zap.String("process_id", processID),
				zap.Error(err),
			)
			h.updateProcessingStatus(processID, "failed", err.Error())
			return
		}
		
		// Store results in database
		buildingID, err := h.storeProcessingResults(result)
		if err != nil {
			h.logger.Error("Failed to store results",
				zap.String("process_id", processID),
				zap.Error(err),
			)
			h.updateProcessingStatus(processID, "failed", err.Error())
			return
		}
		
		// Log completion
		h.logger.Info("Building processing completed",
			zap.String("process_id", processID),
			zap.String("building_id", buildingID),
			zap.Float64("confidence", result.Confidence),
			zap.Duration("processing_time", time.Since(startTime)),
		)
		
		// Update status
		status := "completed"
		if result.RequiresReview {
			status = "pending_review"
		}
		h.updateProcessingStatus(processID, status, "")
	}()
	
	// Return immediate response
	response := ProcessBuildingResponse{
		ProcessID:  processID,
		Status:     "processing",
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
	
	// Query database using GORM
	var building BuildingDetail
	
	// Use GORM to query the building with counts
	type BuildingWithCounts struct {
		BuildingDetail
		WallCount int `gorm:"column:wall_count"`
		RoomCount int `gorm:"column:room_count"`
	}
	
	var result BuildingWithCounts
	err := h.database.Table("topology.buildings b").
		Select(`b.id, b.name, b.address, b.building_type as type,
			b.year_built, b.total_area_nm2 as total_area, b.num_floors,
			b.school_level, b.district_id, b.prototype_id,
			b.confidence_score as confidence, b.validation_status,
			b.created_at, b.updated_at,
			(SELECT COUNT(*) FROM topology.walls WHERE building_id = b.id) as wall_count,
			(SELECT COUNT(*) FROM topology.rooms WHERE building_id = b.id) as room_count`).
		Where("b.id = ?", buildingID).
		Scan(&result).Error
	
	building = result.BuildingDetail
	building.WallCount = result.WallCount
	building.RoomCount = result.RoomCount
	
	if err != nil {
		h.respondError(w, http.StatusNotFound, "Building not found", err)
		return
	}
	
	// Get walls
	building.Walls, err = h.getBuildingWalls(buildingID)
	if err != nil {
		h.logger.Error("Failed to get walls", zap.Error(err))
	}
	
	// Get rooms
	building.Rooms, err = h.getBuildingRooms(buildingID)
	if err != nil {
		h.logger.Error("Failed to get rooms", zap.Error(err))
	}
	
	h.respondJSON(w, http.StatusOK, building)
}

// BuildingDetail contains complete building information
type BuildingDetail struct {
	ID               string        `json:"id"`
	Name             string        `json:"name"`
	Address          string        `json:"address"`
	Type             string        `json:"type"`
	YearBuilt        int           `json:"year_built"`
	TotalArea        int64         `json:"total_area_nm2"`
	NumFloors        int           `json:"num_floors"`
	SchoolLevel      string        `json:"school_level,omitempty"`
	DistrictID       string        `json:"district_id,omitempty"`
	PrototypeID      string        `json:"prototype_id,omitempty"`
	Confidence       float64       `json:"confidence"`
	ValidationStatus string        `json:"validation_status"`
	CreatedAt        time.Time     `json:"created_at"`
	UpdatedAt        time.Time     `json:"updated_at"`
	WallCount        int           `json:"wall_count"`
	RoomCount        int           `json:"room_count"`
	Walls            []WallDetail  `json:"walls"`
	Rooms            []RoomDetail  `json:"rooms"`
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
	var tasks []ReviewTask
	
	// Use GORM to query review tasks
	err := h.database.Table("topology.processing_results pr").
		Select(`pr.id, pr.building_id, b.name as building_name, 
			pr.overall_confidence as confidence, pr.created_at, pr.status,
			(SELECT COUNT(*) FROM topology.validation_issues WHERE building_id = b.id) as issue_count`).
		Joins("JOIN topology.buildings b ON b.id = pr.building_id").
		Where("pr.requires_review = ? AND pr.status IN ?", true, []string{"pending_review", "in_review"}).
		Order("pr.created_at ASC").
		Limit(50).
		Scan(&tasks).Error
	
	if err != nil {
		h.respondError(w, http.StatusInternalServerError, "Failed to get review queue", err)
		return
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
	userID := "system" // Default until auth context is available
	if uid := r.Context().Value("user_id"); uid != nil {
		userID = uid.(string)
	}
	
	var corrections []CorrectionRequest
	if err := json.NewDecoder(r.Body).Decode(&corrections); err != nil {
		h.respondError(w, http.StatusBadRequest, "Invalid corrections", err)
		return
	}
	
	// Begin transaction
	tx := h.database.Begin()
	if tx.Error != nil {
		h.respondError(w, http.StatusInternalServerError, "Failed to start transaction", tx.Error)
		return
	}
	defer tx.Rollback()
	
	// Define correction struct for GORM
	type ManualCorrection struct {
		BuildingID    string          `gorm:"column:building_id"`
		CorrectionType string         `gorm:"column:correction_type"`
		EntityType    string          `gorm:"column:entity_type"`
		EntityID      string          `gorm:"column:entity_id"`
		BeforeState   json.RawMessage `gorm:"column:before_state;type:jsonb"`
		AfterState    json.RawMessage `gorm:"column:after_state;type:jsonb"`
		Reason        string          `gorm:"column:reason"`
		Confidence    float64         `gorm:"column:confidence"`
		CorrectedBy   string          `gorm:"column:corrected_by"`
	}
	
	// Apply each correction
	for _, correction := range corrections {
		beforeJSON, _ := json.Marshal(correction.Before)
		afterJSON, _ := json.Marshal(correction.After)
		
		manualCorrection := ManualCorrection{
			BuildingID:     correction.BuildingID,
			CorrectionType: correction.Type,
			EntityType:     correction.EntityType,
			EntityID:       correction.EntityID,
			BeforeState:    beforeJSON,
			AfterState:     afterJSON,
			Reason:         correction.Reason,
			Confidence:     correction.Confidence,
			CorrectedBy:    userID,
		}
		
		err := tx.Table("topology.manual_corrections").Create(&manualCorrection).Error
		if err != nil {
			h.logger.Error("Failed to save correction", zap.Error(err))
			continue
		}
		
		// Apply correction to actual entity
		h.applyCorrection(tx, correction)
	}
	
	// Update review status
	err := tx.Table("topology.processing_results").
		Where("id = ?", taskID).
		Updates(map[string]interface{}{
			"status":       "completed",
			"completed_at": time.Now(),
		}).Error
	
	if err != nil {
		h.respondError(w, http.StatusInternalServerError, "Failed to update status", err)
		return
	}
	
	// Commit transaction
	if err = tx.Commit().Error; err != nil {
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
		h.logger.Error("Failed to encode response", zap.Error(err))
	}
}

func (h *TopologyHandler) respondError(w http.ResponseWriter, status int, message string, err error) {
	h.logger.Error(message, zap.Error(err))
	
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
	var walls []WallDetail
	err := h.database.Table("topology.walls").
		Select("id, start_x, start_y, end_x, end_y, thickness, height, type, confidence").
		Where("building_id = ?", buildingID).
		Order("created_at ASC").
		Scan(&walls).Error
	
	if err != nil {
		return nil, err
	}
	return walls, nil
}

func (h *TopologyHandler) getBuildingRooms(buildingID string) ([]RoomDetail, error) {
	var rooms []RoomDetail
	err := h.database.Table("topology.rooms").
		Select("id, number, name, function, area_nm2, centroid_x, centroid_y, confidence").
		Where("building_id = ?", buildingID).
		Order("number ASC").
		Scan(&rooms).Error
	
	if err != nil {
		return nil, err
	}
	
	// Get polygon data for each room
	for i := range rooms {
		var polygonData []byte
		err = h.database.Table("topology.rooms").
			Select("polygon").
			Where("id = ?", rooms[i].ID).
			Scan(&polygonData).Error
		
		if err == nil && polygonData != nil {
			// Parse polygon JSON into Point2D array
			json.Unmarshal(polygonData, &rooms[i].Polygon)
		}
	}
	
	return rooms, nil
}

func (h *TopologyHandler) applyCorrection(tx *gorm.DB, correction CorrectionRequest) error {
	// Apply correction to entity based on type
	switch correction.EntityType {
	case "wall":
		// Update wall with correction data
		if afterData, ok := correction.After.(map[string]interface{}); ok {
			updates := make(map[string]interface{})
			if thickness, ok := afterData["thickness"]; ok {
				updates["thickness"] = thickness
			}
			if wallType, ok := afterData["type"]; ok {
				updates["type"] = wallType
			}
			if height, ok := afterData["height"]; ok {
				updates["height"] = height
			}
			if len(updates) > 0 {
				updates["confidence"] = correction.Confidence
				return tx.Table("topology.walls").
					Where("id = ?", correction.EntityID).
					Updates(updates).Error
			}
		}
		
	case "room":
		// Update room with correction data
		if afterData, ok := correction.After.(map[string]interface{}); ok {
			updates := make(map[string]interface{})
			if function, ok := afterData["function"]; ok {
				updates["function"] = function
			}
			if name, ok := afterData["name"]; ok {
				updates["name"] = name
			}
			if area, ok := afterData["area_nm2"]; ok {
				updates["area_nm2"] = area
			}
			if len(updates) > 0 {
				updates["confidence"] = correction.Confidence
				return tx.Table("topology.rooms").
					Where("id = ?", correction.EntityID).
					Updates(updates).Error
			}
		}
		
	case "building":
		// Update building with correction data
		if afterData, ok := correction.After.(map[string]interface{}); ok {
			updates := make(map[string]interface{})
			if buildingType, ok := afterData["building_type"]; ok {
				updates["building_type"] = buildingType
			}
			if totalArea, ok := afterData["total_area_nm2"]; ok {
				updates["total_area_nm2"] = totalArea
			}
			if numFloors, ok := afterData["num_floors"]; ok {
				updates["num_floors"] = numFloors
			}
			if len(updates) > 0 {
				updates["confidence_score"] = correction.Confidence
				return tx.Table("topology.buildings").
					Where("id = ?", correction.BuildingID).
					Updates(updates).Error
			}
		}
	}
	
	return nil
}

// Additional handler methods needed for routes

// ListBuildings returns list of buildings
func (h *TopologyHandler) ListBuildings(w http.ResponseWriter, r *http.Request) {
	// Get query parameters
	limit := r.URL.Query().Get("limit")
	offset := r.URL.Query().Get("offset")
	buildingType := r.URL.Query().Get("type")
	status := r.URL.Query().Get("status")
	
	// Build query
	query := h.database.Table("topology.buildings").
		Select("id, name, address, building_type, year_built, total_area_nm2, num_floors, confidence_score, validation_status, created_at")
	
	if buildingType != "" {
		query = query.Where("building_type = ?", buildingType)
	}
	if status != "" {
		query = query.Where("validation_status = ?", status)
	}
	
	// Apply pagination
	if limit != "" {
		var l int
		fmt.Sscanf(limit, "%d", &l)
		query = query.Limit(l)
	}
	if offset != "" {
		var o int
		fmt.Sscanf(offset, "%d", &o)
		query = query.Offset(o)
	}
	
	var buildings []BuildingDetail
	err := query.Order("created_at DESC").Scan(&buildings).Error
	
	if err != nil {
		h.respondError(w, http.StatusInternalServerError, "Failed to get buildings", err)
		return
	}
	
	h.respondJSON(w, http.StatusOK, buildings)
}

// ApproveBuilding approves a building
func (h *TopologyHandler) ApproveBuilding(w http.ResponseWriter, r *http.Request) {
	// TODO: Implement
	h.respondJSON(w, http.StatusOK, map[string]string{"status": "approved"})
}

// GetProcessingStatus returns processing status
func (h *TopologyHandler) GetProcessingStatus(w http.ResponseWriter, r *http.Request) {
	// TODO: Implement
	h.respondJSON(w, http.StatusOK, map[string]string{"status": "processing"})
}

// CancelProcessing cancels processing
func (h *TopologyHandler) CancelProcessing(w http.ResponseWriter, r *http.Request) {
	// TODO: Implement
	h.respondJSON(w, http.StatusOK, map[string]string{"status": "cancelled"})
}

// GetReviewTask returns a review task
func (h *TopologyHandler) GetReviewTask(w http.ResponseWriter, r *http.Request) {
	// TODO: Implement
	h.respondJSON(w, http.StatusOK, ReviewTask{})
}

// ApproveReview approves a review
func (h *TopologyHandler) ApproveReview(w http.ResponseWriter, r *http.Request) {
	// TODO: Implement
	h.respondJSON(w, http.StatusOK, map[string]string{"status": "approved"})
}

// RejectReview rejects a review
func (h *TopologyHandler) RejectReview(w http.ResponseWriter, r *http.Request) {
	// TODO: Implement
	h.respondJSON(w, http.StatusOK, map[string]string{"status": "rejected"})
}

// GetValidationIssues returns validation issues
func (h *TopologyHandler) GetValidationIssues(w http.ResponseWriter, r *http.Request) {
	// TODO: Implement
	h.respondJSON(w, http.StatusOK, []interface{}{})
}

// ResolveIssue resolves an issue
func (h *TopologyHandler) ResolveIssue(w http.ResponseWriter, r *http.Request) {
	// TODO: Implement
	h.respondJSON(w, http.StatusOK, map[string]string{"status": "resolved"})
}

// ExportBuilding exports a building
func (h *TopologyHandler) ExportBuilding(w http.ResponseWriter, r *http.Request) {
	// TODO: Implement
	h.respondJSON(w, http.StatusOK, map[string]string{"status": "exported"})
}

// GetSemanticPatterns returns semantic patterns
func (h *TopologyHandler) GetSemanticPatterns(w http.ResponseWriter, r *http.Request) {
	// TODO: Implement
	h.respondJSON(w, http.StatusOK, []interface{}{})
}

// TrainPatterns trains patterns
func (h *TopologyHandler) TrainPatterns(w http.ResponseWriter, r *http.Request) {
	// TODO: Implement
	h.respondJSON(w, http.StatusOK, map[string]string{"status": "training"})
}