package handlers

import (
	"encoding/json"
	"net/http"
	"strconv"
	"time"

	"github.com/go-chi/chi/v5"

	"github.com/arx-os/arxos/internal/domain"
	"github.com/arx-os/arxos/internal/interfaces/http/types"
	"github.com/arx-os/arxos/internal/usecase"
)

// SpatialHandler handles spatial and AR-related HTTP requests for mobile clients
type SpatialHandler struct {
	BaseHandler
	buildingUC  *usecase.BuildingUseCase
	equipmentUC *usecase.EquipmentUseCase
	spatialRepo domain.SpatialRepository
	logger      domain.Logger
}

// NewSpatialHandler creates a new spatial handler
func NewSpatialHandler(server *types.Server, buildingUC *usecase.BuildingUseCase, equipmentUC *usecase.EquipmentUseCase, spatialRepo domain.SpatialRepository, logger domain.Logger) *SpatialHandler {
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

	// TODO: Implement spatial anchor creation
	// This would insert into spatial_anchors table using PostGIS

	// For now, simulate anchor creation
	anchor := SpatialAnchor{
		ID:          "anchor-" + strconv.FormatInt(time.Now().Unix(), 10),
		BuildingID:  anchorReq.BuildingID,
		Position:    anchorReq.Position,
		EquipmentID: anchorReq.EquipmentID,
		Confidence:  0.85, // Default confidence
		CreatedAt:   time.Now().Format(time.RFC3339),
		UpdatedAt:   time.Now().Format(time.RFC3339),
		AnchorType:  anchorReq.AnchorType,
		Metadata:    anchorReq.Metadata,
	}

	if anchor.AnchorType == "" {
		anchor.AnchorType = "reference"
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

	// TODO: Implement spatial anchor query using PostGIS
	// SELECT * FROM spatial_anchors WHERE building_id = $1 AND anchor_type = $2 ORDER BY confidence DESC LIMIT $3

	// For now, simulate anchor data
	anchors := []SpatialAnchor{
		{
			ID:          "anchor-equipment-001",
			BuildingID:  buildingID,
			Position:    SpatialPosition{X: 10.5, Y: 15.2, Z: 1.0},
			EquipmentID: "equipment-hvac-001",
			Confidence:  0.95,
			CreatedAt:   time.Now().Add(-7 * 24 * time.Hour).Format(time.RFC3339),
			UpdatedAt:   time.Now().Add(-1 * time.Hour).Format(time.RFC3339),
			AnchorType:  "equipment",
			Metadata:    map[string]any{"scan_source": "lidar"},
		},
		{
			ID:         "anchor-reference-001",
			BuildingID: buildingID,
			Position:   SpatialPosition{X: 0.0, Y: 0.0, Z: 0.0},
			Confidence: 1.0,
			CreatedAt:  time.Now().Add(-30 * 24 * time.Hour).Format(time.RFC3339),
			UpdatedAt:  time.Now().Add(-1 * time.Hour).Format(time.RFC3339),
			AnchorType: "reference",
			Metadata:   map[string]any{"origin": true},
		},
	}

	// Filter based on query parameters
	filteredAnchors := []SpatialAnchor{}
	for _, anchor := range anchors {
		if anchorType != "" && anchor.AnchorType != anchorType {
			continue
		}
		if hasEquipment == "true" && anchor.EquipmentID == "" {
			continue
		}
		if hasEquipment == "false" && anchor.EquipmentID != "" {
			continue
		}
		filteredAnchors = append(filteredAnchors, anchor)
	}

	// Trim to limit if needed
	if len(filteredAnchors) > limit {
		filteredAnchors = filteredAnchors[:limit]
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

	// TODO: Implement PostGIS spatial query for nearby equipment
	// This would use ST_DWithin function:
	// SELECT e.*, ST_Distance(e.position::geography, ST_Point($x,$y,$z)::geography) as distance
	// FROM equipment e
	// WHERE e.building_id = $1
	// AND ST_DWithin(e.position::geography, ST_Point($x,$y,$z)::geography, $radius)
	// ORDER BY ST_Distance(e.position, ST_Point($x,$y,$z)) ASC LIMIT $limit

	// For now, simulate nearby equipment data
	nearbyItems := []map[string]any{
		{
			"equipment": map[string]any{
				"id":          "hvac-001",
				"name":        "Main HVAC Unit",
				"type":        "hvac",
				"status":      "operational",
				"location":    map[string]float64{"x": 10.0, "y": 15.0, "z": 1.0},
				"building_id": buildingID,
			},
			"distance": 2.5,
			"bearing":  45.0,
		},
		{
			"equipment": map[string]any{
				"id":          "electrical-001",
				"name":        "Electrical Panel",
				"type":        "electrical",
				"status":      "operational",
				"location":    map[string]float64{"x": 5.0, "y": 8.0, "z": 1.5},
				"building_id": buildingID,
			},
			"distance": 6.2,
			"bearing":  180.0,
		},
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

	// TODO: Implement spatial mapping storage
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
			"description":          "",                          // TODO: Add Description field to Building domain model
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
