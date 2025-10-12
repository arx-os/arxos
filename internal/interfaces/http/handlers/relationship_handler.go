package handlers

import (
	"encoding/json"
	"fmt"
	"net/http"
	"strconv"
	"time"

	"github.com/go-chi/chi/v5"

	"github.com/arx-os/arxos/internal/domain"
	"github.com/arx-os/arxos/internal/domain/types"
)

// CreateRelationship handles POST /api/v1/equipment/{id}/relationships
func (h *EquipmentHandler) CreateRelationship(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	defer func() {
		h.LogRequest(r, http.StatusCreated, time.Since(start))
	}()

	equipmentID := chi.URLParam(r, "id")
	if equipmentID == "" {
		h.RespondError(w, http.StatusBadRequest, fmt.Errorf("equipment ID is required"))
		return
	}

	// Validate content type
	if err := h.ValidateContentType(r, "application/json"); err != nil {
		h.RespondError(w, http.StatusBadRequest, fmt.Errorf("content type must be application/json"))
		return
	}

	var req struct {
		ToItemID         string         `json:"to_item_id"`
		RelationshipType string         `json:"relationship_type"`
		Properties       map[string]any `json:"properties,omitempty"`
		Strength         float64        `json:"strength,omitempty"`
		Bidirectional    bool           `json:"bidirectional,omitempty"`
	}

	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		h.RespondError(w, http.StatusBadRequest, fmt.Errorf("invalid request body: %v", err))
		return
	}

	// Validate required fields
	if req.ToItemID == "" {
		h.RespondError(w, http.StatusBadRequest, fmt.Errorf("to_item_id is required"))
		return
	}
	if req.RelationshipType == "" {
		h.RespondError(w, http.StatusBadRequest, fmt.Errorf("relationship_type is required"))
		return
	}

	// Get user from context
	userID, _ := r.Context().Value("user_id").(string)

	// Create relationship
	createReq := &domain.CreateRelationshipRequest{
		FromItemID:       types.FromString(equipmentID),
		ToItemID:         types.FromString(req.ToItemID),
		RelationshipType: req.RelationshipType,
		Properties:       req.Properties,
		Strength:         req.Strength,
		Bidirectional:    req.Bidirectional,
		CreatedBy:        userID,
	}

	relationship, err := h.relationshipRepo.Create(r.Context(), createReq)
	if err != nil {
		h.logger.Error("Failed to create relationship", "error", err)
		h.RespondError(w, http.StatusInternalServerError, err)
		return
	}

	h.logger.Info("Relationship created", "relationship_id", relationship.ID, "from", equipmentID, "to", req.ToItemID)
	h.RespondJSON(w, http.StatusCreated, relationship)
}

// ListRelationships handles GET /api/v1/equipment/{id}/relationships
func (h *EquipmentHandler) ListRelationships(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	defer func() {
		h.LogRequest(r, http.StatusOK, time.Since(start))
	}()

	equipmentID := chi.URLParam(r, "id")
	if equipmentID == "" {
		h.RespondError(w, http.StatusBadRequest, fmt.Errorf("equipment ID is required"))
		return
	}

	// Parse query parameters
	direction := r.URL.Query().Get("direction") // "from", "to", "both"
	relType := r.URL.Query().Get("type")
	limit := 100

	if limitStr := r.URL.Query().Get("limit"); limitStr != "" {
		if l, err := strconv.Atoi(limitStr); err == nil && l > 0 {
			limit = l
		}
	}

	// Build filter based on direction
	var relationships []*domain.ItemRelationship
	var err error

	itemID := types.FromString(equipmentID)

	switch direction {
	case "from":
		filter := &domain.RelationshipFilter{
			FromItemID: &itemID,
			Limit:      limit,
		}
		if relType != "" {
			filter.RelationshipType = &relType
		}
		relationships, err = h.relationshipRepo.List(r.Context(), filter)

	case "to":
		filter := &domain.RelationshipFilter{
			ToItemID: &itemID,
			Limit:    limit,
		}
		if relType != "" {
			filter.RelationshipType = &relType
		}
		relationships, err = h.relationshipRepo.List(r.Context(), filter)

	default: // "both" or empty
		// Get relationships where item is either from or to
		filterFrom := &domain.RelationshipFilter{
			FromItemID: &itemID,
			Limit:      limit / 2,
		}
		filterTo := &domain.RelationshipFilter{
			ToItemID: &itemID,
			Limit:    limit / 2,
		}

		relsFrom, err1 := h.relationshipRepo.List(r.Context(), filterFrom)
		relsTo, err2 := h.relationshipRepo.List(r.Context(), filterTo)

		if err1 != nil {
			err = err1
		} else if err2 != nil {
			err = err2
		} else {
			relationships = append(relsFrom, relsTo...)
		}
	}

	if err != nil {
		h.logger.Error("Failed to list relationships", "equipment_id", equipmentID, "error", err)
		h.RespondError(w, http.StatusInternalServerError, err)
		return
	}

	response := map[string]any{
		"equipment_id":  equipmentID,
		"relationships": relationships,
		"count":         len(relationships),
	}

	h.RespondJSON(w, http.StatusOK, response)
}

// GetHierarchy handles GET /api/v1/equipment/{id}/hierarchy
func (h *EquipmentHandler) GetHierarchy(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	defer func() {
		h.LogRequest(r, http.StatusOK, time.Since(start))
	}()

	equipmentID := chi.URLParam(r, "id")
	if equipmentID == "" {
		h.RespondError(w, http.StatusBadRequest, fmt.Errorf("equipment ID is required"))
		return
	}

	// Parse query parameters
	direction := r.URL.Query().Get("direction") // "upstream", "downstream", "both"
	relType := r.URL.Query().Get("type")
	depth := 10

	if depthStr := r.URL.Query().Get("depth"); depthStr != "" {
		if d, err := strconv.Atoi(depthStr); err == nil && d > 0 {
			depth = d
		}
	}

	itemID := types.FromString(equipmentID)

	var relationships []*domain.ItemRelationship
	var err error

	switch direction {
	case "upstream":
		relationships, err = h.relationshipRepo.GetUpstream(r.Context(), itemID, relType, depth)
	case "downstream":
		relationships, err = h.relationshipRepo.GetDownstream(r.Context(), itemID, relType, depth)
	default: // "both"
		upstream, err1 := h.relationshipRepo.GetUpstream(r.Context(), itemID, relType, depth)
		downstream, err2 := h.relationshipRepo.GetDownstream(r.Context(), itemID, relType, depth)

		if err1 != nil {
			err = err1
		} else if err2 != nil {
			err = err2
		} else {
			relationships = append(upstream, downstream...)
		}
	}

	if err != nil {
		h.logger.Error("Failed to get hierarchy", "equipment_id", equipmentID, "error", err)
		h.RespondError(w, http.StatusInternalServerError, err)
		return
	}

	response := map[string]any{
		"equipment_id":  equipmentID,
		"direction":     direction,
		"depth":         depth,
		"relationships": relationships,
		"count":         len(relationships),
	}

	h.RespondJSON(w, http.StatusOK, response)
}

// DeleteRelationship handles DELETE /api/v1/equipment/{id}/relationships/{rel_id}
func (h *EquipmentHandler) DeleteRelationship(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	defer func() {
		h.LogRequest(r, http.StatusNoContent, time.Since(start))
	}()

	equipmentID := chi.URLParam(r, "id")
	relationshipID := chi.URLParam(r, "rel_id")

	if equipmentID == "" {
		h.RespondError(w, http.StatusBadRequest, fmt.Errorf("equipment ID is required"))
		return
	}
	if relationshipID == "" {
		h.RespondError(w, http.StatusBadRequest, fmt.Errorf("relationship ID is required"))
		return
	}

	// Delete relationship
	err := h.relationshipRepo.Delete(r.Context(), relationshipID)
	if err != nil {
		h.logger.Error("Failed to delete relationship", "relationship_id", relationshipID, "error", err)

		if err.Error() == "relationship not found" {
			h.RespondError(w, http.StatusNotFound, err)
			return
		}

		h.RespondError(w, http.StatusInternalServerError, err)
		return
	}

	h.logger.Info("Relationship deleted", "relationship_id", relationshipID)
	h.RespondJSON(w, http.StatusNoContent, nil)
}
