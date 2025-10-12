package handlers

import (
	"fmt"
	"io"
	"net/http"
	"os"
	"path/filepath"
	"strconv"
	"strings"
	"time"

	"github.com/go-chi/chi/v5"

	"github.com/arx-os/arxos/internal/domain"
	"github.com/arx-os/arxos/internal/domain/types"
	"github.com/arx-os/arxos/internal/usecase"
)

// BASHandler handles BAS (Building Automation System) HTTP requests
type BASHandler struct {
	BaseHandler
	basImportUC   *usecase.BASImportUseCase
	basPointRepo  domain.BASPointRepository
	basSystemRepo domain.BASSystemRepository
	logger        domain.Logger
}

// NewBASHandler creates a new BAS handler with proper dependency injection
func NewBASHandler(
	base BaseHandler,
	basImportUC *usecase.BASImportUseCase,
	basPointRepo domain.BASPointRepository,
	basSystemRepo domain.BASSystemRepository,
	logger domain.Logger,
) *BASHandler {
	return &BASHandler{
		BaseHandler:   base,
		basImportUC:   basImportUC,
		basPointRepo:  basPointRepo,
		basSystemRepo: basSystemRepo,
		logger:        logger,
	}
}

// HandleImport handles POST /api/v1/bas/import
func (h *BASHandler) HandleImport(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	defer func() {
		h.LogRequest(r, http.StatusOK, time.Since(start))
	}()

	h.logger.Info("BAS import requested")

	// Parse multipart form (for file upload)
	err := r.ParseMultipartForm(32 << 20) // 32 MB max
	if err != nil {
		h.logger.Error("Failed to parse multipart form", "error", err)
		h.RespondError(w, http.StatusBadRequest, fmt.Errorf("invalid multipart form: %w", err))
		return
	}

	// Get file from form
	file, fileHeader, err := r.FormFile("file")
	if err != nil {
		h.RespondError(w, http.StatusBadRequest, fmt.Errorf("file is required: %w", err))
		return
	}
	defer file.Close()

	// Get required parameters
	buildingID := r.FormValue("building_id")
	systemType := r.FormValue("system_type")

	if buildingID == "" {
		h.RespondError(w, http.StatusBadRequest, fmt.Errorf("building_id is required"))
		return
	}
	if systemType == "" {
		systemType = "generic_bas"
	}

	// Optional parameters
	autoMap := r.FormValue("auto_map") == "true"
	autoCommit := r.FormValue("auto_commit") == "true"

	// Save uploaded file temporarily
	tempDir := os.TempDir()
	tempFilePath := filepath.Join(tempDir, fileHeader.Filename)

	tempFile, err := os.Create(tempFilePath)
	if err != nil {
		h.RespondError(w, http.StatusInternalServerError, fmt.Errorf("failed to create temp file: %w", err))
		return
	}
	defer os.Remove(tempFilePath) // Clean up
	defer tempFile.Close()

	_, err = io.Copy(tempFile, file)
	if err != nil {
		h.RespondError(w, http.StatusInternalServerError, fmt.Errorf("failed to save uploaded file: %w", err))
		return
	}

	// Get or create BAS system
	bid := types.FromString(buildingID)
	basSystemType := parseBASSystemType(systemType)

	// Create BAS system
	basSystemID := types.NewID()
	basSystem := &domain.BASSystem{
		ID:         basSystemID,
		BuildingID: bid,
		Name:       fmt.Sprintf("%s System", systemType),
		SystemType: basSystemType,
		Enabled:    true,
		ReadOnly:   true,
		Metadata:   make(map[string]interface{}),
		CreatedAt:  time.Now(),
		UpdatedAt:  time.Now(),
	}

	if err := h.basSystemRepo.Create(basSystem); err != nil {
		h.logger.Error("Failed to create BAS system", "error", err)
		h.RespondError(w, http.StatusInternalServerError, fmt.Errorf("failed to create BAS system: %w", err))
		return
	}

	// Build import request
	importReq := domain.ImportBASPointsRequest{
		FilePath:    tempFilePath,
		BuildingID:  bid,
		BASSystemID: basSystemID,
		SystemType:  basSystemType,
		AutoMap:     autoMap,
		AutoCommit:  autoCommit,
	}

	// Execute import
	result, err := h.basImportUC.ImportBASPoints(r.Context(), importReq)
	if err != nil {
		h.logger.Error("BAS import failed", "error", err)
		h.RespondError(w, http.StatusInternalServerError, err)
		return
	}

	// Return success response
	response := map[string]any{
		"success":         true,
		"import_id":       result.ImportID,
		"points_added":    result.PointsAdded,
		"points_modified": result.PointsModified,
		"points_deleted":  result.PointsDeleted,
		"points_mapped":   result.PointsMapped,
		"points_unmapped": result.PointsUnmapped,
		"duration_ms":     result.DurationMS,
		"status":          result.Status,
	}

	h.RespondJSON(w, http.StatusOK, response)
}

// HandleListSystems handles GET /api/v1/bas/systems
func (h *BASHandler) HandleListSystems(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	defer func() {
		h.LogRequest(r, http.StatusOK, time.Since(start))
	}()

	// Get building ID from query params
	buildingID := r.URL.Query().Get("building_id")
	if buildingID == "" {
		h.RespondError(w, http.StatusBadRequest, fmt.Errorf("building_id is required"))
		return
	}

	// List BAS systems
	bid := types.FromString(buildingID)
	systems, err := h.basSystemRepo.List(bid)
	if err != nil {
		h.logger.Error("Failed to list BAS systems", "error", err)
		h.RespondError(w, http.StatusInternalServerError, err)
		return
	}

	response := map[string]any{
		"systems":     systems,
		"building_id": buildingID,
		"count":       len(systems),
	}

	h.RespondJSON(w, http.StatusOK, response)
}

// HandleListPoints handles GET /api/v1/bas/points
func (h *BASHandler) HandleListPoints(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	defer func() {
		h.LogRequest(r, http.StatusOK, time.Since(start))
	}()

	// Build filter from query parameters
	filter := domain.BASPointFilter{}

	if buildingID := r.URL.Query().Get("building_id"); buildingID != "" {
		bid := types.FromString(buildingID)
		filter.BuildingID = &bid
	}

	if systemID := r.URL.Query().Get("system_id"); systemID != "" {
		sid := types.FromString(systemID)
		filter.BASSystemID = &sid
	}

	if roomID := r.URL.Query().Get("room_id"); roomID != "" {
		rid := types.FromString(roomID)
		filter.RoomID = &rid
	}

	if floorID := r.URL.Query().Get("floor_id"); floorID != "" {
		fid := types.FromString(floorID)
		filter.FloorID = &fid
	}

	if equipmentID := r.URL.Query().Get("equipment_id"); equipmentID != "" {
		eid := types.FromString(equipmentID)
		filter.EquipmentID = &eid
	}

	if pointType := r.URL.Query().Get("point_type"); pointType != "" {
		filter.PointType = pointType
	}

	if mappedStr := r.URL.Query().Get("mapped"); mappedStr != "" {
		mapped := mappedStr == "true"
		filter.Mapped = &mapped
	}

	// Parse limit and offset
	limit := 100
	offset := 0

	if limitStr := r.URL.Query().Get("limit"); limitStr != "" {
		if l, err := strconv.Atoi(limitStr); err == nil && l > 0 {
			limit = l
		}
	}

	if offsetStr := r.URL.Query().Get("offset"); offsetStr != "" {
		if o, err := strconv.Atoi(offsetStr); err == nil && o >= 0 {
			offset = o
		}
	}

	// Query points
	points, err := h.basPointRepo.List(filter, limit, offset)
	if err != nil {
		h.logger.Error("Failed to list BAS points", "error", err)
		h.RespondError(w, http.StatusInternalServerError, err)
		return
	}

	// Get total count
	count, err := h.basPointRepo.Count(filter)
	if err != nil {
		h.logger.Warn("Failed to count BAS points", "error", err)
		count = len(points) // Fallback to returned count
	}

	response := map[string]any{
		"points": points,
		"total":  count,
		"limit":  limit,
		"offset": offset,
	}

	h.RespondJSON(w, http.StatusOK, response)
}

// HandleGetPoint handles GET /api/v1/bas/points/{id}
func (h *BASHandler) HandleGetPoint(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	defer func() {
		h.LogRequest(r, http.StatusOK, time.Since(start))
	}()

	// Get point ID from URL
	pointID := chi.URLParam(r, "id")
	if pointID == "" {
		h.RespondError(w, http.StatusBadRequest, fmt.Errorf("point id is required"))
		return
	}

	// Get point
	pid := types.FromString(pointID)
	point, err := h.basPointRepo.GetByID(pid)
	if err != nil {
		h.logger.Error("Failed to get BAS point", "point_id", pointID, "error", err)
		h.RespondError(w, http.StatusNotFound, fmt.Errorf("BAS point not found"))
		return
	}

	h.RespondJSON(w, http.StatusOK, point)
}

// HandleMapPoint handles POST /api/v1/bas/points/{id}/map
func (h *BASHandler) HandleMapPoint(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	defer func() {
		h.LogRequest(r, http.StatusOK, time.Since(start))
	}()

	// Get point ID from URL
	pointID := chi.URLParam(r, "id")
	if pointID == "" {
		h.RespondError(w, http.StatusBadRequest, fmt.Errorf("point id is required"))
		return
	}

	// Parse request body
	var req struct {
		RoomID      *string `json:"room_id,omitempty"`
		EquipmentID *string `json:"equipment_id,omitempty"`
		Confidence  int     `json:"confidence"`
	}

	if err := h.ParseRequestBody(r, &req); err != nil {
		h.RespondError(w, http.StatusBadRequest, err)
		return
	}

	// Validate at least one target
	if req.RoomID == nil && req.EquipmentID == nil {
		h.RespondError(w, http.StatusBadRequest, fmt.Errorf("either room_id or equipment_id is required"))
		return
	}

	// Validate confidence
	if req.Confidence < 1 || req.Confidence > 3 {
		req.Confidence = 3 // Default to high confidence
	}

	// Parse IDs
	pid := types.FromString(pointID)

	// Map the point
	var err error
	if req.RoomID != nil {
		rid := types.FromString(*req.RoomID)
		err = h.basPointRepo.MapToRoom(pid, rid, req.Confidence)
	} else {
		eid := types.FromString(*req.EquipmentID)
		err = h.basPointRepo.MapToEquipment(pid, eid, req.Confidence)
	}

	if err != nil {
		h.logger.Error("Failed to map BAS point", "point_id", pointID, "error", err)
		h.RespondError(w, http.StatusInternalServerError, err)
		return
	}

	// Get updated point
	point, err := h.basPointRepo.GetByID(pid)
	if err != nil {
		h.logger.Warn("Failed to get updated point", "error", err)
		// Still return success since mapping worked
		h.RespondJSON(w, http.StatusOK, map[string]any{
			"success":    true,
			"point_id":   pointID,
			"confidence": req.Confidence,
		})
		return
	}

	h.RespondJSON(w, http.StatusOK, map[string]any{
		"success": true,
		"point":   point,
	})
}

// parseBASSystemType converts string to BASSystemType
func parseBASSystemType(systemType string) domain.BASSystemType {
	systemType = strings.ToLower(systemType)

	switch systemType {
	case "metasys", "johnson_controls_metasys":
		return domain.BASSystemTypeMetasys
	case "desigo", "siemens_desigo":
		return domain.BASSystemTypeDesigo
	case "honeywell", "honeywell_ebi":
		return domain.BASSystemTypeHoneywell
	case "niagara", "tridium_niagara":
		return domain.BASSystemTypeNiagara
	case "schneider", "schneider_electric":
		return domain.BASSystemTypeSchneiderElectric
	default:
		return domain.BASSystemTypeOther
	}
}
