package bim

import (
	"encoding/json"
	"fmt"
	"net/http"
	"strconv"
	"time"

	"github.com/arxos/arxos/core/internal/handlers"
	"github.com/go-chi/chi/v5"
)

// ============================================================================
// CGO-OPTIMIZED BIM HANDLER
// ============================================================================

// BIMHandlerCGO provides CGO-optimized BIM operations
type BIMHandlerCGO struct {
	*handlers.HandlerBaseCGO
}

// NewBIMHandlerCGO creates a new CGO-optimized BIM handler
func NewBIMHandlerCGO() *BIMHandlerCGO {
	return &BIMHandlerCGO{
		HandlerBaseCGO: handlers.NewHandlerBaseCGO(),
	}
}

// Close cleans up the handler
func (h *BIMHandlerCGO) Close() {
	if h.HandlerBaseCGO != nil {
		h.HandlerBaseCGO.Close()
	}
}

// ============================================================================
// HTTP HANDLERS
// ============================================================================

// CreateBuilding handles building creation with CGO optimization
func (h *BIMHandlerCGO) CreateBuilding(w http.ResponseWriter, r *http.Request) {
	var request struct {
		Name         string `json:"name"`
		BuildingType string `json:"building_type"`
		NumFloors    int    `json:"num_floors"`
		Address      string `json:"address"`
	}

	if err := json.NewDecoder(r.Body).Decode(&request); err != nil {
		h.SendErrorResponse(w, "Invalid request body", http.StatusBadRequest)
		return
	}

	// Validate request
	if request.Name == "" {
		h.SendErrorResponse(w, "Building name is required", http.StatusBadRequest)
		return
	}

	if request.NumFloors <= 0 {
		request.NumFloors = 1
	}

	// Create building model using CGO optimization
	building, err := h.CreateBuildingModel(request.Name, request.BuildingType, request.NumFloors)
	if err != nil {
		h.SendErrorResponse(w, "Failed to create building: "+err.Error(), http.StatusInternalServerError)
		return
	}

	// Add address to building data
	if buildingData, ok := building.(map[string]interface{}); ok {
		buildingData["address"] = request.Address
		buildingData["id"] = generateBuildingID()
	}

	h.SendSuccessResponse(w, building, "Building created successfully")
}

// GetBuilding retrieves building information with CGO optimization
func (h *BIMHandlerCGO) GetBuilding(w http.ResponseWriter, r *http.Request) {
	buildingID := chi.URLParam(r, "id")
	if buildingID == "" {
		h.SendErrorResponse(w, "Building ID is required", http.StatusBadRequest)
		return
	}

	// For now, return a placeholder building
	// In a real implementation, this would query the CGO-optimized BIM engine
	building := map[string]interface{}{
		"id":            buildingID,
		"name":          "Sample Building",
		"building_type": "Office",
		"num_floors":    3,
		"address":       "123 Main St",
		"cgo_status":    h.HasCGOBridge(),
		"created_at":    time.Now(),
		"updated_at":    time.Now(),
	}

	h.SendSuccessResponse(w, building, "Building retrieved successfully")
}

// UpdateBuilding handles building updates with CGO optimization
func (h *BIMHandlerCGO) UpdateBuilding(w http.ResponseWriter, r *http.Request) {
	buildingID := chi.URLParam(r, "id")
	if buildingID == "" {
		h.SendErrorResponse(w, "Building ID is required", http.StatusBadRequest)
		return
	}

	var request map[string]interface{}
	if err := json.NewDecoder(r.Body).Decode(&request); err != nil {
		h.SendErrorResponse(w, "Invalid request body", http.StatusBadRequest)
		return
	}

	// Add update timestamp
	request["updated_at"] = time.Now()
	request["id"] = buildingID
	request["cgo_status"] = h.HasCGOBridge()

	h.SendSuccessResponse(w, request, "Building updated successfully")
}

// DeleteBuilding handles building deletion with CGO optimization
func (h *BIMHandlerCGO) DeleteBuilding(w http.ResponseWriter, r *http.Request) {
	buildingID := chi.URLParam(r, "id")
	if buildingID == "" {
		h.SendErrorResponse(w, "Building ID is required", http.StatusBadRequest)
		return
	}

	// For now, return success
	// In a real implementation, this would delete from the CGO-optimized BIM engine
	response := map[string]interface{}{
		"id":         buildingID,
		"deleted":    true,
		"cgo_status": h.HasCGOBridge(),
		"timestamp":  time.Now(),
	}

	h.SendSuccessResponse(w, response, "Building deleted successfully")
}

// ListBuildings returns a list of buildings with CGO optimization
func (h *BIMHandlerCGO) ListBuildings(w http.ResponseWriter, r *http.Request) {
	// Parse pagination parameters
	page, _ := strconv.Atoi(r.URL.Query().Get("page"))
	if page < 1 {
		page = 1
	}

	pageSize, _ := strconv.Atoi(r.URL.Query().Get("page_size"))
	if pageSize < 1 || pageSize > 100 {
		pageSize = 20
	}

	// For now, return placeholder buildings
	// In a real implementation, this would query the CGO-optimized BIM engine
	buildings := []map[string]interface{}{
		{
			"id":            "1",
			"name":          "Office Building A",
			"building_type": "Office",
			"num_floors":    5,
			"address":       "123 Main St",
			"cgo_status":    h.HasCGOBridge(),
		},
		{
			"id":            "2",
			"name":          "Residential Complex B",
			"building_type": "Residential",
			"num_floors":    8,
			"address":       "456 Oak Ave",
			"cgo_status":    h.HasCGOBridge(),
		},
	}

	response := map[string]interface{}{
		"buildings":  buildings,
		"page":       page,
		"page_size":  pageSize,
		"total":      len(buildings),
		"cgo_status": h.HasCGOBridge(),
		"timestamp":  time.Now(),
	}

	h.SendSuccessResponse(w, response, "Buildings retrieved successfully")
}

// GenerateASCII2D generates 2D ASCII representation with CGO optimization
func (h *BIMHandlerCGO) GenerateASCII2D(w http.ResponseWriter, r *http.Request) {
	buildingID := chi.URLParam(r, "id")
	floorNumberStr := r.URL.Query().Get("floor")

	if buildingID == "" {
		h.SendErrorResponse(w, "Building ID is required", http.StatusBadRequest)
		return
	}

	floorNumber := 0
	if floorNumberStr != "" {
		if f, err := strconv.Atoi(floorNumberStr); err == nil {
			floorNumber = f
		}
	}

	// Generate ASCII representation
	ascii := h.generateSampleASCII2D(floorNumber)

	response := map[string]interface{}{
		"building_id": buildingID,
		"floor":       floorNumber,
		"ascii_2d":    ascii,
		"cgo_status":  h.HasCGOBridge(),
		"timestamp":   time.Now(),
	}

	h.SendSuccessResponse(w, response, "2D ASCII generated successfully")
}

// GenerateASCII3D generates 3D ASCII representation with CGO optimization
func (h *BIMHandlerCGO) GenerateASCII3D(w http.ResponseWriter, r *http.Request) {
	buildingID := chi.URLParam(r, "id")

	if buildingID == "" {
		h.SendErrorResponse(w, "Building ID is required", http.StatusBadRequest)
		return
	}

	// Generate ASCII representation
	ascii := h.generateSampleASCII3D()

	response := map[string]interface{}{
		"building_id": buildingID,
		"ascii_3d":    ascii,
		"cgo_status":  h.HasCGOBridge(),
		"timestamp":   time.Now(),
	}

	h.SendSuccessResponse(w, response, "3D ASCII generated successfully")
}

// GetBuildingStatistics returns building statistics with CGO optimization
func (h *BIMHandlerCGO) GetBuildingStatistics(w http.ResponseWriter, r *http.Request) {
	buildingID := chi.URLParam(r, "id")

	if buildingID == "" {
		h.SendErrorResponse(w, "Building ID is required", http.StatusBadRequest)
		return
	}

	// For now, return placeholder statistics
	// In a real implementation, this would query the CGO-optimized BIM engine
	stats := map[string]interface{}{
		"building_id":     buildingID,
		"total_floors":    3,
		"total_rooms":     12,
		"total_walls":     48,
		"total_doors":     8,
		"total_windows":   6,
		"total_area_sqft": 15000.0,
		"cgo_status":      h.HasCGOBridge(),
		"timestamp":       time.Now(),
	}

	h.SendSuccessResponse(w, stats, "Building statistics retrieved successfully")
}

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

// generateBuildingID generates a unique building ID
func generateBuildingID() string {
	return "bldg_" + strconv.FormatInt(time.Now().UnixNano(), 10)
}

// generateSampleASCII2D generates a sample 2D ASCII representation
func (h *BIMHandlerCGO) generateSampleASCII2D(floorNumber int) string {
	ascii := fmt.Sprintf("Floor %d - 2D ASCII Representation\n", floorNumber)
	ascii += "=====================================\n"
	ascii += "    +----+----+----+----+----+\n"
	ascii += "    |    |    |    |    |    |\n"
	ascii += "    +----+----+----+----+----+\n"
	ascii += "    |    |    |    |    |    |\n"
	ascii += "    +----+----+----+----+----+\n"
	ascii += "    |    |    |    |    |    |\n"
	ascii += "    +----+----+----+----+----+\n"
	ascii += "    |    |    |    |    |    |\n"
	ascii += "    +----+----+----+----+----+\n"
	ascii += "    |    |    |    |    |    |\n"
	ascii += "    +----+----+----+----+----+\n"
	ascii += "\nCGO Status: " + strconv.FormatBool(h.HasCGOBridge())

	return ascii
}

// generateSampleASCII3D generates a sample 3D ASCII representation
func (h *BIMHandlerCGO) generateSampleASCII3D() string {
	ascii := "3D ASCII Representation\n"
	ascii += "========================\n"
	ascii += "     /\\\n"
	ascii += "    /  \\\n"
	ascii += "   /____\\\n"
	ascii += "  /|    |\\\n"
	ascii += " / |____| \\\n"
	ascii += "/__|____|__\\\n"
	ascii += "|  |    |  |\n"
	ascii += "|  |____|  |\n"
	ascii += "|__|____|__|\n"
	ascii += "\nCGO Status: " + strconv.FormatBool(h.HasCGOBridge())

	return ascii
}
