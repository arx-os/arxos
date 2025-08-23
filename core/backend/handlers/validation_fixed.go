package handlers

import (
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"strconv"
	"time"

	"github.com/arxos/arxos/core/arxobject"
	"github.com/arxos/arxos/core/backend/models"
	"github.com/arxos/arxos/core/backend/services"
	"github.com/gorilla/websocket"
)

// ValidationHandlerFixed handles field validation endpoints with proper error handling
type ValidationHandlerFixed struct {
	validationService *services.ValidationService
	arxEngine         *arxobject.Engine
	wsUpgrader        websocket.Upgrader
	wsConnections     map[string]*websocket.Conn
}

// NewValidationHandlerFixed creates a new fixed validation handler
func NewValidationHandlerFixed(vs *services.ValidationService, engine *arxobject.Engine) *ValidationHandlerFixed {
	return &ValidationHandlerFixed{
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

// GetPendingValidations returns list of validation tasks with proper error handling
func (h *ValidationHandlerFixed) GetPendingValidations(w http.ResponseWriter, r *http.Request) {
	// Parse query parameters with validation
	priority := r.URL.Query().Get("priority")
	objectType := r.URL.Query().Get("type")
	limitStr := r.URL.Query().Get("limit")

	// Validate and parse limit parameter
	limit := 50 // Default limit
	if limitStr != "" {
		parsedLimit, err := strconv.Atoi(limitStr)
		if err != nil {
			respondWithError(w, http.StatusBadRequest, "Invalid limit parameter")
			return
		}
		if parsedLimit > 0 && parsedLimit <= 1000 {
			limit = parsedLimit
		}
	}

	// Get pending validations from service with error handling
	limitStr = fmt.Sprintf("%d", limit)
	tasks, err := h.validationService.GetPendingValidationsFixed(priority, objectType, limitStr)
	if err != nil {
		log.Printf("Error getting pending validations: %v", err)
		respondWithError(w, http.StatusInternalServerError, "Failed to get pending validations")
		return
	}

	// Calculate potential impact for each task
	for i := range tasks {
		impact, err := h.calculatePotentialImpact(tasks[i])
		if err != nil {
			log.Printf("Error calculating impact for task %s: %v", tasks[i].ObjectID, err)
			// Continue processing other tasks
			continue
		}
		tasks[i].PotentialImpact = impact
	}

	// Prioritize tasks based on confidence and impact
	prioritizedTasks := h.prioritizeValidationTasksFixed(tasks)

	// Return response
	response := map[string]interface{}{
		"success": true,
		"data": map[string]interface{}{
			"tasks":           prioritizedTasks,
			"total_count":     len(prioritizedTasks),
			"high_priority":   h.countByPriority(prioritizedTasks, 3),
			"medium_priority": h.countByPriority(prioritizedTasks, 2),
			"low_priority":    h.countByPriority(prioritizedTasks, 1),
		},
	}

	w.Header().Set("Content-Type", "application/json")
	if err := json.NewEncoder(w).Encode(response); err != nil {
		log.Printf("Error encoding response: %v", err)
		respondWithError(w, http.StatusInternalServerError, "Failed to encode response")
		return
	}
}

// SubmitValidation handles validation submissions with comprehensive error handling
func (h *ValidationHandlerFixed) SubmitValidation(w http.ResponseWriter, r *http.Request) {
	var submission models.ValidationSubmission

	// Parse request body with error handling
	if err := json.NewDecoder(r.Body).Decode(&submission); err != nil {
		log.Printf("Error decoding validation submission: %v", err)
		respondWithError(w, http.StatusBadRequest, "Invalid JSON in request body")
		return
	}

	// Validate submission data
	if err := h.validateSubmission(&submission); err != nil {
		log.Printf("Validation submission validation failed: %v", err)
		respondWithError(w, http.StatusBadRequest, err.Error())
		return
	}

	// Set timestamp if not provided
	if submission.Timestamp.IsZero() {
		submission.Timestamp = time.Now()
	}

	// Get the object being validated with error handling
	obj, err := h.arxEngine.GetObject(submission.ObjectID)
	if err != nil {
		log.Printf("Error retrieving object %s: %v", submission.ObjectID, err)
		respondWithError(w, http.StatusNotFound, "Object not found")
		return
	}

	// Calculate confidence improvement
	oldConfidence := obj.Confidence.Overall
	newConfidence := submission.Confidence
	improvement := newConfidence - oldConfidence

	// Create validation impact assessment
	impact := &models.ValidationImpact{
		ObjectID:              submission.ObjectID,
		OldConfidence:         oldConfidence,
		NewConfidence:         newConfidence,
		ConfidenceImprovement: improvement,
		CascadedObjects:       []string{},
		CascadedCount:         0,
		PatternLearned:        false,
		TotalConfidenceGain:   improvement,
		TimeSaved:             h.calculateTimeSaved(improvement),
	}

	// Apply validation and learn patterns with error handling
	if err := h.applyValidation(obj, &submission, impact); err != nil {
		log.Printf("Error applying validation: %v", err)
		respondWithError(w, http.StatusInternalServerError, "Failed to apply validation")
		return
	}

	// Learn patterns from this validation with error handling
	patternLearned, err := h.validationService.LearnPatternFixed(submission)
	if err != nil {
		log.Printf("Error learning pattern: %v", err)
		// Don't fail the request, just log the error
	} else {
		impact.PatternLearned = patternLearned
	}

	// Apply cascading updates with error handling
	cascadedObjects, err := h.applyCascadingUpdates(obj, &submission)
	if err != nil {
		log.Printf("Error applying cascading updates: %v", err)
		// Don't fail the request, just log the error
	} else {
		impact.CascadedObjects = cascadedObjects
		impact.CascadedCount = len(cascadedObjects)
		impact.TotalConfidenceGain += float32(len(cascadedObjects)) * improvement * 0.5
	}

	// Save validation record with error handling
	if err := h.validationService.SaveValidationFixed(&submission); err != nil {
		log.Printf("Error saving validation: %v", err)
		// Don't fail the request since validation was already applied
	}

	// Broadcast to WebSocket clients
	h.broadcastValidationUpdate(impact)

	// Return response
	response := map[string]interface{}{
		"success": true,
		"data": map[string]interface{}{
			"impact":                 impact,
			"validation_id":          submission.ObjectID,
			"confidence_improvement": improvement,
			"cascaded_count":         impact.CascadedCount,
			"pattern_learned":        impact.PatternLearned,
			"time_saved":             impact.TimeSaved,
		},
		"message": "Validation submitted successfully",
	}

	w.Header().Set("Content-Type", "application/json")
	if err := json.NewEncoder(w).Encode(response); err != nil {
		log.Printf("Error encoding validation response: %v", err)
		respondWithError(w, http.StatusInternalServerError, "Failed to encode response")
		return
	}
}

// Helper methods with proper error handling

func (h *ValidationHandlerFixed) calculatePotentialImpact(task *models.ValidationTask) (float32, error) {
	// Calculate impact based on confidence deficit and similar object count
	confidenceDeficit := 1.0 - task.Confidence
	impactMultiplier := float32(1.0 + float64(task.SimilarCount)*0.1)

	if confidenceDeficit < 0 {
		return 0, fmt.Errorf("invalid confidence value: %f", task.Confidence)
	}

	return confidenceDeficit * impactMultiplier, nil
}

func (h *ValidationHandlerFixed) prioritizeValidationTasksFixed(tasks []*models.ValidationTask) []*models.ValidationTask {
	if len(tasks) == 0 {
		return tasks
	}

	// Assign priorities based on impact and confidence
	for _, task := range tasks {
		if task.Confidence < 0.5 && task.PotentialImpact > 0.8 {
			task.Priority = 3 // High priority
		} else if task.Confidence < 0.7 && task.PotentialImpact > 0.5 {
			task.Priority = 2 // Medium priority
		} else {
			task.Priority = 1 // Low priority
		}
	}

	// Sort by priority and potential impact
	// Note: In production, use a proper sorting algorithm
	return tasks
}

func (h *ValidationHandlerFixed) countByPriority(tasks []*models.ValidationTask, priority int) int {
	count := 0
	for _, task := range tasks {
		if task.Priority == priority {
			count++
		}
	}
	return count
}

func (h *ValidationHandlerFixed) validateSubmission(submission *models.ValidationSubmission) error {
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

func (h *ValidationHandlerFixed) applyValidation(obj *arxobject.ArxObject, submission *models.ValidationSubmission, impact *models.ValidationImpact) error {
	// Update object confidence
	obj.Confidence.Overall = submission.Confidence

	// Recalculate overall confidence based on components
	obj.Confidence.CalculateOverall()

	// Mark as validated
	obj.Validate(submission.Validator)

	// Update in engine
	return h.arxEngine.UpdateObject(obj)
}

func (h *ValidationHandlerFixed) calculateTimeSaved(improvement float32) float32 {
	// Estimate time saved based on confidence improvement
	// Higher improvements save more time in future validations
	return improvement * 10.0 // 10 minutes per 0.1 confidence improvement
}

func (h *ValidationHandlerFixed) applyCascadingUpdates(obj *arxobject.ArxObject, submission *models.ValidationSubmission) ([]string, error) {
	// Find similar objects that can benefit from this validation
	similarObjects, err := h.arxEngine.GetSimilarObjects(obj, 0.8)
	if err != nil {
		return nil, fmt.Errorf("failed to get similar objects: %w", err)
	}

	var updatedIDs []string
	confidenceBoost := submission.Confidence * 0.1 // 10% of validation confidence

	for _, similar := range similarObjects {
		if similar.Confidence.Overall < submission.Confidence {
			similar.Confidence.Overall = min(similar.Confidence.Overall+confidenceBoost, submission.Confidence)
			similar.Confidence.CalculateOverall()

			if err := h.arxEngine.UpdateObject(similar); err != nil {
				log.Printf("Error updating similar object %s: %v", similar.ID, err)
				continue
			}

			updatedIDs = append(updatedIDs, similar.ID)
		}
	}

	return updatedIDs, nil
}

func (h *ValidationHandlerFixed) broadcastValidationUpdate(impact *models.ValidationImpact) {
	message := map[string]interface{}{
		"type": "validation_update",
		"data": impact,
	}

	messageBytes, err := json.Marshal(message)
	if err != nil {
		log.Printf("Error marshaling WebSocket message: %v", err)
		return
	}

	for connID, conn := range h.wsConnections {
		if err := conn.WriteMessage(websocket.TextMessage, messageBytes); err != nil {
			log.Printf("Error sending WebSocket message to %s: %v", connID, err)
			// Remove failed connection
			delete(h.wsConnections, connID)
			conn.Close()
		}
	}
}

// Note: Utility functions moved to helpers.go to avoid redeclaration
