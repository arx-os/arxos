package handlers

import (
	"net/http"
	"strconv"
	"time"

	"github.com/go-chi/chi/v5"

	"github.com/arx-os/arxos/internal/domain"
	"github.com/arx-os/arxos/internal/interfaces/http/types"
	"github.com/arx-os/arxos/internal/usecase"
)

// MobileHandler handles mobile-specific HTTP requests for AR and spatial functionality
type MobileHandler struct {
	BaseHandler
	buildingUC  *usecase.BuildingUseCase
	equipmentUC *usecase.EquipmentUseCase
	logger      domain.Logger
}

// NewMobileHandler creates a new mobile handler
func NewMobileHandler(server *types.Server, buildingUC *usecase.BuildingUseCase, equipmentUC *usecase.EquipmentUseCase, logger domain.Logger) *MobileHandler {
	return &MobileHandler{
		BaseHandler: nil, // Will be injected by container
		buildingUC:  buildingUC,
		equipmentUC: equipmentUC,
		logger:      logger,
	}
}

// Mobile Equipment Response Types - simplified to match actual domain
type MobileEquipment struct {
	ID         string            `json:"id"`
	Name       string            `json:"name"`
	Type       string            `json:"type"`
	Model      string            `json:"model,omitempty"`
	Status     string            `json:"status"`
	Location   *MobileLocation   `json:"location,omitempty"`
	BuildingID string            `json:"building_id"`
	FloorID    string            `json:"floor_id,omitempty"`
	RoomID     string            `json:"room_id,omitempty"`
	CreatedAt  string            `json:"created_at"`
	UpdatedAt  string            `json:"updated_at"`
	ARMetadata *MobileARMetadata `json:"ar_metadata,omitempty"`
}

type MobileLocation struct {
	X float64 `json:"x"`
	Y float64 `json:"y"`
	Z float64 `json:"z"`
}

type MobileARMetadata struct {
	ARAnchorID         string  `json:"ar_anchor_id,omitempty"`
	HasARAnchor        bool    `json:"has_ar_anchor"`
	PositionConfidence float64 `json:"position_confidence"`
	LastARScan         string  `json:"last_ar_scan,omitempty"`
	ARStatus           string  `json:"ar_status"` // "mapped", "pending", "unknown"
}

type MobileEquipmentResponse struct {
	Equipment  []MobileEquipment `json:"equipment"`
	TotalCount int               `json:"total_count"`
	HasMore    bool              `json:"has_more"`
}

// HandleMobileEquipment handles GET /api/v1/mobile/equipment/building/{buildingId}
func (m *MobileHandler) HandleMobileEquipment(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	defer func() {
		m.LogRequest(r, http.StatusOK, time.Since(start))
	}()

	buildingID := chi.URLParam(r, "buildingId")
	if buildingID == "" {
		m.RespondJSON(w, http.StatusBadRequest, map[string]interface{}{
			"error": "building_id_required",
		})
		return
	}

	// Parse query parameters
	limit := 50 // Default limit for mobile
	offset := 0

	if limitStr := r.URL.Query().Get("limit"); limitStr != "" {
		if l, err := strconv.Atoi(limitStr); err == nil && l > 0 {
			limit = l
		}
	}

	if offsetStr := r.URL.Query().Get("offset"); offsetStr != "" {
		if o, err := strconv.Atoi(offsetStr); err == nil {
			offset = o
		}
	}

	// Create a simple filter for now
	// TODO: Enhance EquipmentFilter domain model with more fields
	filter := &domain.EquipmentFilter{
		Limit:  limit,
		Offset: offset,
	}

	// Get equipment using domain layer
	ctx := r.Context()
	equipment, err := m.equipmentUC.ListEquipment(ctx, filter)
	if err != nil {
		m.logger.Error("Failed to get mobile equipment", "building_id", buildingID, "error", err)
		m.RespondJSON(w, http.StatusInternalServerError, map[string]interface{}{
			"error": "failed_to_get_equipment",
		})
		return
	}

	// Filter equipment by building ID and convert to mobile format
	mobileEquipment := []MobileEquipment{}
	for _, eq := range equipment {
		if eq.BuildingID == buildingID {
			mobileEq := MobileEquipment{
				ID:         eq.ID,
				Name:       eq.Name,
				Type:       eq.Type,
				Model:      eq.Model,
				Status:     eq.Status,
				BuildingID: eq.BuildingID,
				FloorID:    eq.FloorID,
				RoomID:     eq.RoomID,
				CreatedAt:  eq.CreatedAt.Format(time.RFC3339),
				UpdatedAt:  eq.UpdatedAt.Format(time.RFC3339),
			}

			// Add location if available
			if eq.Location != nil {
				mobileEq.Location = &MobileLocation{
					X: eq.Location.X,
					Y: eq.Location.Y,
					Z: eq.Location.Z,
				}
			}

			// Add simplified AR metadata
			mobileEq.ARMetadata = &MobileARMetadata{
				HasARAnchor:        false,     // TODO: Check spatial_anchors table
				PositionConfidence: 0.8,       // Default confidence
				ARStatus:           "unknown", // TODO: Determine AR status
			}

			mobileEquipment = append(mobileEquipment, mobileEq)
		}
	}

	response := MobileEquipmentResponse{
		Equipment:  mobileEquipment,
		TotalCount: len(mobileEquipment),
		HasMore:    len(mobileEquipment) == limit, // Simple check
	}

	m.logger.Info("Mobile equipment retrieved", "building_id", buildingID, "count", len(mobileEquipment))
	m.RespondJSON(w, http.StatusOK, response)
}

// HandleMobileEquipmentDetail handles GET /api/v1/mobile/equipment/{equipmentId}
func (m *MobileHandler) HandleMobileEquipmentDetail(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	defer func() {
		m.LogRequest(r, http.StatusOK, time.Since(start))
	}()

	equipmentID := chi.URLParam(r, "equipmentId")
	if equipmentID == "" {
		m.RespondJSON(w, http.StatusBadRequest, map[string]interface{}{
			"error": "equipment_id_required",
		})
		return
	}

	// Get equipment using domain layer
	ctx := r.Context()
	equipment, err := m.equipmentUC.GetEquipment(ctx, equipmentID)
	if err != nil {
		m.logger.Error("Failed to get mobile equipment detail", "equipment_id", equipmentID, "error", err)
		m.RespondJSON(w, http.StatusNotFound, map[string]interface{}{
			"error": "equipment_not_found",
		})
		return
	}

	// Convert to mobile format
	mobileEq := MobileEquipment{
		ID:         equipment.ID,
		Name:       equipment.Name,
		Type:       equipment.Type,
		Model:      equipment.Model,
		Status:     equipment.Status,
		BuildingID: equipment.BuildingID,
		FloorID:    equipment.FloorID,
		RoomID:     equipment.RoomID,
		CreatedAt:  equipment.CreatedAt.Format(time.RFC3339),
		UpdatedAt:  equipment.UpdatedAt.Format(time.RFC3339),
	}

	if equipment.Location != nil {
		mobileEq.Location = &MobileLocation{
			X: equipment.Location.X,
			Y: equipment.Location.Y,
			Z: equipment.Location.Z,
		}
	}

	// Enhanced AR metadata for individual equipment
	mobileEq.ARMetadata = &MobileARMetadata{
		HasARAnchor:        false,                                                // TODO: Check spatial_anchors table for this equipment
		PositionConfidence: 0.9,                                                  // Higher confidence for individual equipment
		ARStatus:           "mapped",                                             // TODO: Determine actual AR mapping status
		LastARScan:         time.Now().Add(-24 * time.Hour).Format(time.RFC3339), // Mock data
	}

	m.logger.Info("Mobile equipment detail retrieved", "equipment_id", equipmentID)
	m.RespondJSON(w, http.StatusOK, map[string]interface{}{
		"equipment": mobileEq,
	})
}
