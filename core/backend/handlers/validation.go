package handlers

import (
	"encoding/json"
	"fmt"
	"net/http"
	"strconv"
	"time"

	"github.com/arxos/arxos/core/arxobject"
	"github.com/arxos/arxos/core/backend/models"
	"github.com/arxos/arxos/core/backend/services"
	"github.com/gorilla/websocket"
)

// ValidationHandler handles field validation endpoints
type ValidationHandler struct {
	validationService *services.ValidationService
	arxEngine         *arxobject.Engine
	wsUpgrader        websocket.Upgrader
	wsConnections     map[string]*websocket.Conn
}

// NewValidationHandler creates a new validation handler
func NewValidationHandler(vs *services.ValidationService, engine *arxobject.Engine) *ValidationHandler {
	return &ValidationHandler{
		validationService: vs,
		arxEngine:         engine,
		wsUpgrader: websocket.Upgrader{
			CheckOrigin: func(r *http.Request) bool {
				// In production, implement proper origin checking
				return true
			},
		},
		wsConnections: make(map[string]*websocket.Conn),
	}
}

// Use models.ValidationSubmission instead of local definition

// Deprecated: Use models.ValidationTask instead
type ValidationTask = models.ValidationTask

// Deprecated: Use models.ValidationImpact instead
type ValidationImpact = models.ValidationImpact

// Deprecated: Use models.ValidationSubmission instead
type ValidationSubmission = models.ValidationSubmission

// GetPendingValidations returns list of validation tasks
func (h *ValidationHandler) GetPendingValidations(w http.ResponseWriter, r *http.Request) {
	// Get query parameters for filtering
	priority := r.URL.Query().Get("priority")
	objectType := r.URL.Query().Get("type")
	limit := r.URL.Query().Get("limit")

	// Get pending validations from service
	tasks, err := h.validationService.GetPendingValidations(priority, objectType, limit)
	if err != nil {
		respondWithError(w, http.StatusInternalServerError, "Failed to get pending validations")
		return
	}

	// Calculate potential impact for each task
	for i := range tasks {
		tasks[i].PotentialImpact = h.calculateValidationImpact(tasks[i].ObjectID)
		tasks[i].SimilarCount = h.countSimilarObjects(tasks[i].ObjectID)
	}

	// Sort by priority and impact
	tasks = h.prioritizeValidationTasks(tasks)

	respondWithJSON(w, http.StatusOK, map[string]interface{}{
		"validations": tasks,
		"total":       len(tasks),
	})
}

// FlagForValidation flags an object for validation
func (h *ValidationHandler) FlagForValidation(w http.ResponseWriter, r *http.Request) {
	var request struct {
		ObjectID string `json:"object_id"`
		Reason   string `json:"reason,omitempty"`
		Priority int    `json:"priority,omitempty"`
	}

	if err := json.NewDecoder(r.Body).Decode(&request); err != nil {
		respondWithError(w, http.StatusBadRequest, "Invalid request")
		return
	}

	// Convert string ID to uint64
	objectID, err := strconv.ParseUint(request.ObjectID, 10, 64)
	if err != nil {
		respondWithError(w, http.StatusBadRequest, "Invalid object ID format")
		return
	}

	// Get object from engine
	obj, exists := h.arxEngine.GetObject(objectID)
	if !exists {
		respondWithError(w, http.StatusNotFound, "Object not found")
		return
	}

	// Create validation task
	task := &models.ValidationTask{
		ObjectID:   request.ObjectID,
		ObjectType: fmt.Sprintf("%d", obj.Type),
		Confidence: obj.Confidence.Overall,
		Priority:   h.calculatePriority(obj, request.Priority),
		CreatedAt:  time.Now(),
	}

	// Save to database
	if err := h.validationService.CreateValidationTask(task); err != nil {
		respondWithError(w, http.StatusInternalServerError, "Failed to create validation task")
		return
	}

	respondWithJSON(w, http.StatusOK, map[string]interface{}{
		"success":    true,
		"validation": task,
	})
}

// SubmitValidation processes a validation submission
func (h *ValidationHandler) SubmitValidation(w http.ResponseWriter, r *http.Request) {
	var submission ValidationSubmission

	if err := json.NewDecoder(r.Body).Decode(&submission); err != nil {
		respondWithError(w, http.StatusBadRequest, "Invalid submission")
		return
	}

	// Validate submission
	if err := h.validateSubmission(&submission); err != nil {
		respondWithError(w, http.StatusBadRequest, err.Error())
		return
	}

	// Get object from engine
	obj, err := h.arxEngine.GetObject(submission.ObjectID)
	if err != nil {
		respondWithError(w, http.StatusNotFound, "Object not found")
		return
	}

	// Store old confidence for comparison
	oldConfidence := obj.Confidence.Overall

	// Update object confidence based on validation
	h.updateObjectConfidence(obj, &submission)

	// Find similar objects for pattern learning
	similarObjects := h.findSimilarObjects(obj)

	// Apply validation cascade
	cascadedObjects := h.applyCascadeValidation(obj, similarObjects, submission.Confidence)

	// Check if pattern should be learned
	patternLearned := false
	if len(cascadedObjects) >= 3 {
		patternLearned = h.validationService.LearnPattern(obj, similarObjects, submission)
	}

	// Calculate impact
	impact := ValidationImpact{
		ObjectID:              submission.ObjectID,
		OldConfidence:         oldConfidence,
		NewConfidence:         obj.Confidence.Overall,
		ConfidenceImprovement: obj.Confidence.Overall - oldConfidence,
		CascadedObjects:       getObjectIDs(cascadedObjects),
		CascadedCount:         len(cascadedObjects),
		PatternLearned:        patternLearned,
		TotalConfidenceGain:   h.calculateTotalGain(cascadedObjects, oldConfidence),
		TimeSaved:             float32(len(cascadedObjects)) * 2.5, // Estimate 2.5 min per object
	}

	// Save validation to database
	if err := h.validationService.SaveValidation(&submission, &impact); err != nil {
		respondWithError(w, http.StatusInternalServerError, "Failed to save validation")
		return
	}

	// Broadcast update via WebSocket
	h.broadcastValidationUpdate(impact)

	respondWithJSON(w, http.StatusOK, map[string]interface{}{
		"success": true,
		"impact":  impact,
	})
}

// GetValidationHistory returns validation history
func (h *ValidationHandler) GetValidationHistory(w http.ResponseWriter, r *http.Request) {
	// Get query parameters
	objectID := r.URL.Query().Get("object_id")
	validator := r.URL.Query().Get("validator")
	startDate := r.URL.Query().Get("start_date")
	endDate := r.URL.Query().Get("end_date")

	// Get history from service
	history, err := h.validationService.GetValidationHistory(objectID, validator, startDate, endDate)
	if err != nil {
		respondWithError(w, http.StatusInternalServerError, "Failed to get validation history")
		return
	}

	// Calculate statistics
	stats := h.calculateValidationStats(history)

	respondWithJSON(w, http.StatusOK, map[string]interface{}{
		"history": history,
		"stats":   stats,
	})
}

// GetValidationLeaderboard returns top validators
func (h *ValidationHandler) GetValidationLeaderboard(w http.ResponseWriter, r *http.Request) {
	period := r.URL.Query().Get("period") // daily, weekly, monthly, all-time
	if period == "" {
		period = "weekly"
	}

	leaderboard, err := h.validationService.GetLeaderboard(period)
	if err != nil {
		respondWithError(w, http.StatusInternalServerError, "Failed to get leaderboard")
		return
	}

	respondWithJSON(w, http.StatusOK, map[string]interface{}{
		"leaderboard": leaderboard,
		"period":      period,
	})
}

// WebSocketHandler handles WebSocket connections for real-time updates
func (h *ValidationHandler) WebSocketHandler(w http.ResponseWriter, r *http.Request) {
	conn, err := h.wsUpgrader.Upgrade(w, r, nil)
	if err != nil {
		http.Error(w, "Failed to upgrade connection", http.StatusBadRequest)
		return
	}
	defer conn.Close()

	// Generate connection ID
	connID := fmt.Sprintf("conn_%d", time.Now().UnixNano())
	h.wsConnections[connID] = conn
	defer delete(h.wsConnections, connID)

	// Keep connection alive and handle messages
	for {
		messageType, _, err := conn.ReadMessage()
		if err != nil {
			break
		}

		// Send ping to keep connection alive
		if messageType == websocket.PingMessage {
			conn.WriteMessage(websocket.PongMessage, []byte{})
		}
	}
}

// Helper functions

func (h *ValidationHandler) validateSubmission(submission *ValidationSubmission) error {
	if submission.ObjectID == "" {
		return fmt.Errorf("object_id is required")
	}
	if submission.ValidationType == "" {
		return fmt.Errorf("validation_type is required")
	}
	if submission.Validator == "" {
		return fmt.Errorf("validator is required")
	}
	if submission.Confidence < 0 || submission.Confidence > 1 {
		return fmt.Errorf("confidence must be between 0 and 1")
	}
	return nil
}

func (h *ValidationHandler) updateObjectConfidence(obj *arxobject.ArxObject, submission *ValidationSubmission) {
	// Update confidence based on validation type
	switch submission.ValidationType {
	case "dimension":
		// Dimension validation improves position and properties
		obj.Confidence.Position = min(obj.Confidence.Position+0.3*submission.Confidence, 0.95)
		obj.Confidence.Properties = min(obj.Confidence.Properties+0.25*submission.Confidence, 0.95)

	case "type":
		// Type validation improves classification
		obj.Confidence.Classification = min(obj.Confidence.Classification+0.35*submission.Confidence, 0.95)

	case "material":
		// Material validation improves properties
		obj.Confidence.Properties = min(obj.Confidence.Properties+0.4*submission.Confidence, 0.95)

	case "relationship":
		// Relationship validation
		obj.Confidence.Relationships = min(obj.Confidence.Relationships+0.4*submission.Confidence, 0.95)

	default:
		// Generic validation - small boost to all
		obj.Confidence.Classification = min(obj.Confidence.Classification+0.1*submission.Confidence, 0.95)
		obj.Confidence.Position = min(obj.Confidence.Position+0.1*submission.Confidence, 0.95)
		obj.Confidence.Properties = min(obj.Confidence.Properties+0.1*submission.Confidence, 0.95)
	}

	// Recalculate overall confidence
	obj.Confidence.CalculateOverall()

	// Mark as validated
	obj.Validate(submission.Validator)
}

func (h *ValidationHandler) findSimilarObjects(obj *arxobject.ArxObject) []*arxobject.ArxObject {
	var similar []*arxobject.ArxObject

	// Get objects in spatial proximity
	x, y, _ := obj.GetPositionMeters()
	nearbyIDs := h.arxEngine.QueryRegion(
		float32(x-10), float32(y-10),
		float32(x+10), float32(y+10),
	)

	// Filter for same type and similar properties
	for _, id := range nearbyIDs {
		if id == obj.ID {
			continue
		}

		nearbyObj, err := h.arxEngine.GetObject(id)
		if err != nil {
			continue
		}

		// Check if similar type and needs validation
		if nearbyObj.Type == obj.Type && nearbyObj.NeedsValidation() {
			similar = append(similar, nearbyObj)
		}
	}

	return similar
}

func (h *ValidationHandler) applyCascadeValidation(
	validated *arxobject.ArxObject,
	similar []*arxobject.ArxObject,
	validationConfidence float32,
) []*arxobject.ArxObject {

	var cascaded []*arxobject.ArxObject

	for _, obj := range similar {
		// Calculate cascade confidence based on similarity
		similarity := h.calculateSimilarity(validated, obj)
		cascadeConfidence := validationConfidence * similarity * 0.9 // 90% max cascade

		if cascadeConfidence > obj.Confidence.Overall {
			// Apply cascaded confidence boost
			boost := (cascadeConfidence - obj.Confidence.Overall) * 0.5
			obj.Confidence.Classification = min(obj.Confidence.Classification+boost, 0.90)
			obj.Confidence.Position = min(obj.Confidence.Position+boost*0.8, 0.90)
			obj.Confidence.Properties = min(obj.Confidence.Properties+boost*0.7, 0.90)
			obj.Confidence.CalculateOverall()

			cascaded = append(cascaded, obj)
		}
	}

	return cascaded
}

func (h *ValidationHandler) calculateSimilarity(obj1, obj2 *arxobject.ArxObject) float32 {
	if obj1.Type != obj2.Type {
		return 0
	}

	similarity := float32(0.5) // Base similarity for same type

	// Check dimensional similarity
	if obj1.Width > 0 && obj2.Width > 0 {
		widthRatio := float32(min64(obj1.Width, obj2.Width)) / float32(max64(obj1.Width, obj2.Width))
		similarity += widthRatio * 0.25
	}

	if obj1.Height > 0 && obj2.Height > 0 {
		heightRatio := float32(min64(obj1.Height, obj2.Height)) / float32(max64(obj1.Height, obj2.Height))
		similarity += heightRatio * 0.25
	}

	return min(similarity, 1.0)
}

func (h *ValidationHandler) calculateValidationImpact(objectID string) float32 {
	obj, err := h.arxEngine.GetObject(objectID)
	if err != nil {
		return 0
	}

	// Impact based on object criticality and confidence gap
	criticality := h.getObjectCriticality(obj.Type)
	confidenceGap := 1.0 - obj.Confidence.Overall

	// Count similar objects that would benefit
	similar := h.findSimilarObjects(obj)
	cascadeImpact := float32(len(similar)) / 10.0 // Normalize by 10

	impact := criticality*confidenceGap*0.5 + min(cascadeImpact, 1.0)*0.5
	return min(impact, 1.0)
}

func (h *ValidationHandler) countSimilarObjects(objectID string) int {
	obj, err := h.arxEngine.GetObject(objectID)
	if err != nil {
		return 0
	}

	similar := h.findSimilarObjects(obj)
	return len(similar)
}

func (h *ValidationHandler) prioritizeValidationTasks(tasks []*models.ValidationTask) []*models.ValidationTask {
	// Sort by priority (descending) and potential impact (descending)
	// This is a simple bubble sort for clarity - use sort.Slice in production
	for i := 0; i < len(tasks); i++ {
		for j := i + 1; j < len(tasks); j++ {
			if tasks[j].Priority > tasks[i].Priority ||
				(tasks[j].Priority == tasks[i].Priority && tasks[j].PotentialImpact > tasks[i].PotentialImpact) {
				tasks[i], tasks[j] = tasks[j], tasks[i]
			}
		}
	}
	return tasks
}

func (h *ValidationHandler) calculatePriority(obj *arxobject.ArxObject, userPriority int) int {
	if userPriority > 0 {
		return userPriority
	}

	// Auto-calculate priority based on object type and confidence
	basePriority := 5

	// Critical objects get higher priority - simplified calculation
	if obj.Type == "structural" {
		basePriority += 3
	} else if obj.Type == "fire_safety" {
		basePriority += 2
	}

	// Low confidence increases priority
	if obj.Confidence.Overall < 0.3 {
		basePriority += 3
	} else if obj.Confidence.Overall < 0.6 {
		basePriority += 1
	}

	if basePriority > 10 {
		return 10
	}
	return basePriority
}

func (h *ValidationHandler) getObjectCriticality(objType string) float32 {
	// Simplified criticality calculation based on string type
	switch objType {
	case "structural":
		return 1.0
	case "fire_safety":
		return 0.9
	case "electrical", "hvac", "plumbing":
		return 0.7
	default:
		return 0.5
	}
}

func (h *ValidationHandler) calculateTotalGain(cascaded []*arxobject.ArxObject, baseOldConfidence float32) float32 {
	totalGain := float32(0)
	for _, obj := range cascaded {
		// Assume similar initial confidence
		gain := obj.Confidence.Overall - baseOldConfidence
		if gain > 0 {
			totalGain += gain
		}
	}
	return totalGain
}

func (h *ValidationHandler) broadcastValidationUpdate(impact ValidationImpact) {
	update := map[string]interface{}{
		"type":           "confidence_update",
		"object_id":      impact.ObjectID,
		"old_confidence": impact.OldConfidence,
		"new_confidence": impact.NewConfidence,
		"timestamp":      time.Now(),
	}

	if impact.PatternLearned {
		update["pattern_learned"] = true
		update["objects_improved"] = impact.CascadedCount
	}

	message, _ := json.Marshal(update)

	// Broadcast to all connected clients
	for _, conn := range h.wsConnections {
		conn.WriteMessage(websocket.TextMessage, message)
	}
}

func (h *ValidationHandler) calculateValidationStats(history []models.ValidationRecord) map[string]interface{} {
	if len(history) == 0 {
		return map[string]interface{}{
			"total": 0,
		}
	}

	totalImprovement := float32(0)
	totalCascaded := 0
	patternsLearned := 0

	for _, record := range history {
		totalImprovement += record.ConfidenceImprovement
		totalCascaded += record.CascadedCount
		if record.PatternLearned {
			patternsLearned++
		}
	}

	return map[string]interface{}{
		"total":                 len(history),
		"average_improvement":   totalImprovement / float32(len(history)),
		"total_cascaded":        totalCascaded,
		"patterns_learned":      patternsLearned,
		"efficiency_multiplier": float32(totalCascaded) / float32(len(history)),
	}
}

// Helper utility functions

func parseObjectID(id string) uint64 {
	// Deprecated: Objects now use string IDs directly
	var result uint64
	fmt.Sscanf(id, "%d", &result)
	return result
}

func getObjectTypeName(t string) string {
	// Objects now use string types directly
	return t
}

func getObjectIDs(objects []*arxobject.ArxObject) []string {
	ids := make([]string, len(objects))
	for i, obj := range objects {
		ids[i] = obj.ID
	}
	return ids
}

func min(a, b float32) float32 {
	if a < b {
		return a
	}
	return b
}

func max64(a, b int64) int64 {
	if a > b {
		return a
	}
	return b
}

func min64(a, b int64) int64 {
	if a < b {
		return a
	}
	return b
}

// Use respondWithJSON and respondWithError from helpers.go
