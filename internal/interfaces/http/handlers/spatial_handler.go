package handlers

import (
	"encoding/json"
	"net/http"
	"strconv"
	"time"

	"github.com/go-chi/chi/v5"

	"github.com/arx-os/arxos/internal/domain"
	"github.com/arx-os/arxos/internal/domain/spatial"
	"github.com/arx-os/arxos/internal/interfaces/http/types"
	"github.com/arx-os/arxos/internal/usecase/building"
)

// SpatialHandler handles spatial and AR-related HTTP requests for mobile clients
type SpatialHandler struct {
	BaseHandler
	buildingUC  *building.BuildingUseCase
	equipmentUC *building.EquipmentUseCase
	spatialRepo spatial.SpatialRepository
	logger      domain.Logger
}

// NewSpatialHandler creates a new spatial handler
func NewSpatialHandler(server *types.Server, buildingUC *building.BuildingUseCase, equipmentUC *building.EquipmentUseCase, spatialRepo spatial.SpatialRepository, logger domain.Logger) *SpatialHandler {
	return &SpatialHandler{
		BaseHandler: nil, // Will be injected by container
		buildingUC:  buildingUC,
		equipmentUC: equipmentUC,
		spatialRepo: spatialRepo,
		logger:      logger,
	}
}

// Spatial Response Types for Mobile AR - simplified to avoid cross-handler dependencies
type SpatialAnchor struct {
	ID          string          `json:"id"`
	BuildingID  string          `json:"building_id"`
	Position    SpatialPosition `json:"position"`
	EquipmentID string          `json:"equipment_id,omitempty"`
	Confidence  float64         `json:"confidence"`
	CreatedAt   string          `json:"created_at"`
	UpdatedAt   string          `json:"updated_at"`
	AnchorType  string          `json:"anchor_type"` // "equipment", "reference", "floor"
	Metadata    map[string]any  `json:"metadata,omitempty"`
}

type SpatialPosition struct {
	X float64 `json:"x"`
	Y float64 `json:"y"`
	Z float64 `json:"z"`
}

type NearbyEquipmentResponse struct {
	Equipment    []map[string]any `json:"equipment"`
	TotalFound   int              `json:"total_found"`
	SearchRadius float64          `json:"search_radius"`
}

// HandleCreateSpatialAnchor handles POST /api/v1/mobile/spatial/anchors
func (s *SpatialHandler) HandleCreateSpaticialAnchor(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	defer func() {
		s.LogRequest(r, http.StatusOK, time.Since(start))
	}()

	var anchorReq struct {
		BuildingID  string          `json:"building_id" validate:"required"`
		Position    SpatialPosition `json:"position" validate:"required"`
		EquipmentID string          `json:"equipment_id,omitempty"`
		AnchorType  string          `json:"anchor_type,omitempty"`
		Metadata    map[string]any  `json:"metadata,omitempty"`
	}

	if err := json.NewDecoder(r.Body).Decode(&anchorReq); err != nil {
		s.logger.Error("Invalid spatial anchor request", "error", err)
		s.RespondJSON(w, http.StatusBadRequest, map[string]any{
			"error": "invalid_anchor_request",
		})
		return
	}

	// Get user ID from auth context
	userID := r.Context().Value("user_id").(string)

	// Create anchor using spatial repository
	createReq := &spatial.CreateSpatialAnchorRequest{
		BuildingID:  anchorReq.BuildingID,
		EquipmentID: anchorReq.EquipmentID,
		Position: spatial.SpatialPosition{
			X: anchorReq.Position.X,
			Y: anchorReq.Position.Y,
			Z: anchorReq.Position.Z,
		},
		Confidence: 0.85, // Default confidence
		AnchorType: anchorReq.AnchorType,
		Metadata:   anchorReq.Metadata,
		CreatedBy:  userID,
	}

	if createReq.AnchorType == "" {
		createReq.AnchorType = "reference"
	}

	ctx := r.Context()
	domainAnchor, err := s.spatialRepo.CreateSpatialAnchor(ctx, createReq)
	if err != nil {
		s.logger.Error("Failed to create spatial anchor", "building_id", anchorReq.BuildingID, "error", err)
		s.RespondJSON(w, http.StatusInternalServerError, map[string]any{
			"error": "failed_to_create_anchor",
		})
		return
	}

	// Convert to response format
	anchor := SpatialAnchor{
		ID:          domainAnchor.ID,
		BuildingID:  domainAnchor.BuildingID,
		Position:    SpatialPosition{X: domainAnchor.Position.X, Y: domainAnchor.Position.Y, Z: domainAnchor.Position.Z},
		EquipmentID: domainAnchor.EquipmentID,
		Confidence:  domainAnchor.Confidence,
		CreatedAt:   domainAnchor.CreatedAt.Format(time.RFC3339),
		UpdatedAt:   domainAnchor.UpdatedAt.Format(time.RFC3339),
		AnchorType:  domainAnchor.AnchorType,
		Metadata:    domainAnchor.Metadata,
	}

	s.logger.Info("Spatial anchor created", "anchor_id", anchor.ID, "building_id", anchorReq.BuildingID, "user_id", userID)
	s.RespondJSON(w, http.StatusCreated, map[string]any{
		"anchor": anchor,
	})
}

// HandleGetSpatialAnchors handles GET /api/v1/mobile/spatial/anchors/building/{buildingId}
func (s *SpatialHandler) HandleGetSpatialAnchors(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	defer func() {
		s.LogRequest(r, http.StatusOK, time.Since(start))
	}()

	buildingID := chi.URLParam(r, "buildingId")
	if buildingID == "" {
		s.RespondJSON(w, http.StatusBadRequest, map[string]any{
			"error": "building_id_required",
		})
		return
	}

	// Parse optional filters
	anchorType := r.URL.Query().Get("type")
	hasEquipment := r.URL.Query().Get("has_equipment")
	limit := 100
	if limitStr := r.URL.Query().Get("limit"); limitStr != "" {
		if l, err := strconv.Atoi(limitStr); err == nil && l > 0 {
			limit = l
		}
	}

	// Query spatial anchors from database
	ctx := r.Context()
	filter := &spatial.SpatialAnchorFilter{
		Limit: &limit,
	}
	if anchorType != "" {
		filter.AnchorType = &anchorType
	}

	domainAnchors, err := s.spatialRepo.GetSpatialAnchorsByBuilding(ctx, buildingID, filter)
	if err != nil {
		s.logger.Error("Failed to get spatial anchors", "building_id", buildingID, "error", err)
		s.RespondJSON(w, http.StatusInternalServerError, map[string]any{
			"error": "failed_to_get_anchors",
		})
		return
	}

	// Convert to response format
	filteredAnchors := []SpatialAnchor{}
	for _, da := range domainAnchors {
		// Apply hasEquipment filter if specified
		if hasEquipment == "true" && da.EquipmentID == "" {
			continue
		}
		if hasEquipment == "false" && da.EquipmentID != "" {
			continue
		}

		anchor := SpatialAnchor{
			ID:          da.ID,
			BuildingID:  da.BuildingID,
			Position:    SpatialPosition{X: da.Position.X, Y: da.Position.Y, Z: da.Position.Z},
			EquipmentID: da.EquipmentID,
			Confidence:  da.Confidence,
			CreatedAt:   da.CreatedAt.Format(time.RFC3339),
			UpdatedAt:   da.UpdatedAt.Format(time.RFC3339),
			AnchorType:  da.AnchorType,
			Metadata:    da.Metadata,
		}
		filteredAnchors = append(filteredAnchors, anchor)
	}

	s.logger.Info("Spatial anchors retrieved", "building_id", buildingID, "count", len(filteredAnchors))
	s.RespondJSON(w, http.StatusOK, map[string]any{
		"anchors": filteredAnchors,
		"total":   len(filteredAnchors),
	})
}

// HandleNearbyEquipment handles GET /api/v1/mobile/spatial/nearby/equipment
func (s *SpatialHandler) HandleNearbyEquipment(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	defer func() {
		s.LogRequest(r, http.StatusOK, time.Since(start))
	}()

	// Parse query parameters
	buildingID := r.URL.Query().Get("building_id")
	if buildingID == "" {
		s.RespondJSON(w, http.StatusBadRequest, map[string]any{
			"error": "building_id_required",
		})
		return
	}

	var position SpatialPosition
	if xStr := r.URL.Query().Get("x"); xStr != "" {
		if x, err := strconv.ParseFloat(xStr, 64); err == nil {
			position.X = x
		}
	}
	if yStr := r.URL.Query().Get("y"); yStr != "" {
		if y, err := strconv.ParseFloat(yStr, 64); err == nil {
			position.Y = y
		}
	}
	if zStr := r.URL.Query().Get("z"); zStr != "" {
		if z, err := strconv.ParseFloat(zStr, 64); err == nil {
			position.Z = z
		}
	}

	radius := 10.0 // Default 10 meters
	if radiusStr := r.URL.Query().Get("radius"); radiusStr != "" {
		if r, err := strconv.ParseFloat(radiusStr, 64); err == nil && r > 0 {
			radius = r
		}
	}

	// Query nearby equipment using real PostGIS spatial repository
	ctx := r.Context()
	limit := 20
	if limitStr := r.URL.Query().Get("limit"); limitStr != "" {
		if l, err := strconv.Atoi(limitStr); err == nil && l > 0 {
			limit = l
		}
	}

	nearbyReq := &spatial.NearbyEquipmentRequest{
		BuildingID: buildingID,
		CenterX:    position.X,
		CenterY:    position.Y,
		CenterZ:    position.Z,
		Radius:     radius,
		Limit:      &limit,
	}

	nearbyResults, err := s.spatialRepo.FindNearbyEquipment(ctx, nearbyReq)
	if err != nil {
		s.logger.Error("Failed to find nearby equipment", "building_id", buildingID, "error", err)
		// Return empty results for better UX instead of error
		nearbyResults = []*spatial.NearbyEquipmentResult{}
	}

	// Convert to response format
	nearbyItems := []map[string]any{}
	for _, result := range nearbyResults {
		item := map[string]any{
			"equipment": map[string]any{
				"id":     result.EquipmentID,
				"name":   result.EquipmentName,
				"type":   result.EquipmentType,
				"status": result.EquipmentStatus,
			},
			"distance": result.Distance,
			"bearing":  result.Bearing,
		}
		nearbyItems = append(nearbyItems, item)
	}

	response := NearbyEquipmentResponse{
		Equipment:    nearbyItems,
		TotalFound:   len(nearbyItems),
		SearchRadius: radius,
	}

	s.logger.Info("Nearby equipment retrieved", "building_id", buildingID, "position", position, "count", len(nearbyItems))
	s.RespondJSON(w, http.StatusOK, response)
}

// HandleSpatialmapping handles POST /api/v1/mobile/spatial/mapping
func (s *SpatialHandler) HandleSpatialMapping(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	defer func() {
		s.LogRequest(r, http.StatusOK, time.Since(start))
	}()

	var mappingReq struct {
		BuildingID string            `json:"building_id" validate:"required"`
		SessionID  string            `json:"session_id" validate:"required"`
		Anchor     []SpatialAnchor   `json:"anchors"`
		Points     []SpatialPosition `json:"points"`
		Metadata   map[string]any    `json:"metadata"`
	}

	if err := json.NewDecoder(r.Body).Decode(&mappingReq); err != nil {
		s.logger.Error("Invalid spatial mapping request", "error", err)
		s.RespondJSON(w, http.StatusBadRequest, map[string]any{
			"error": "invalid_mapping_request",
		})
		return
	}

	// Get user ID from auth context
	userID := r.Context().Value("user_id").(string)

	// NOTE: Spatial mapping storage via SpatialRepository
	// This would:
	// 1. Store spatial anchors in spatial_anchors table
	// 2. Store point cloud data in point_clouds table
	// 3. Update scanned_regions table with coverage data
	// 4. Calculate building coverage percentage

	// For now, simulate mapping data processing
	mappingResult := map[string]any{
		"session_id":      mappingReq.SessionID,
		"building_id":     mappingReq.BuildingID,
		"anchors_created": len(mappingReq.Anchor),
		"points_stored":   len(mappingReq.Points),
		"coverage_added":  15.5, // Percentage
		"estimated_time":  time.Now().Format(time.RFC3339),
	}

	s.logger.Info("Spatial mapping data received", "building_id", mappingReq.BuildingID, "session_id", mappingReq.SessionID, "user_id", userID, "anchors", len(mappingReq.Anchor), "points", len(mappingReq.Points))
	s.RespondJSON(w, http.StatusOK, map[string]any{
		"mapping_result": mappingResult,
	})
}

// HandleBuildingsList handles GET /api/v1/mobile/spatial/buildings
func (s *SpatialHandler) HandleBuildingsList(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	defer func() {
		s.LogRequest(r, http.StatusOK, time.Since(start))
	}()

	// Parse query parameters
	limit := 20
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

	// Get buildings using domain layer
	ctx := r.Context()
	filter := &domain.BuildingFilter{
		Limit:  limit,
		Offset: offset,
	}

	buildings, err := s.buildingUC.ListBuildings(ctx, filter)
	if err != nil {
		s.logger.Error("Failed to get buildings", "error", err)
		s.RespondJSON(w, http.StatusInternalServerError, map[string]any{
			"error": "failed_to_get_buildings",
		})
		return
	}

	// Convert to mobile format
	mobileBuildings := make([]map[string]any, len(buildings))
	for i, building := range buildings {
		mobileBuilding := map[string]any{
			"id":                   building.ID,
			"name":                 building.Name,
			"address":              building.Address,
			"description":          "",                          // NOTE: Description field to be added to Building model
			"has_spatial_coverage": len(building.Equipment) > 0, // Placeholder logic
			"equipment_count":      len(building.Equipment),
			"last_scan":            building.UpdatedAt.Format(time.RFC3339),
			"created_at":           building.CreatedAt.Format(time.RFC3339),
			"updated_at":           building.UpdatedAt.Format(time.RFC3339),
		}
		mobileBuildings[i] = mobileBuilding
	}

	s.logger.Info("Mobile buildings list retrieved", "count", len(buildings))
	s.RespondJSON(w, http.StatusOK, map[string]any{
		"buildings": mobileBuildings,
		"total":     len(buildings),
		"has_more":  len(buildings) == limit,
	})
}
