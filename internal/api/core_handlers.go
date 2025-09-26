package api

import (
	"encoding/json"
	"net/http"
	"strconv"

	"github.com/arx-os/arxos/internal/ecosystem"
	"github.com/arx-os/arxos/internal/services"
	"github.com/go-chi/chi/v5"
)

// CoreHandlers handles Core tier API endpoints
type CoreHandlers struct {
	coreService *services.CoreService
}

// NewCoreHandlers creates a new CoreHandlers instance
func NewCoreHandlers(coreService *services.CoreService) *CoreHandlers {
	return &CoreHandlers{
		coreService: coreService,
	}
}

// DashboardStats represents dashboard statistics
type DashboardStats struct {
	Buildings       int `json:"buildings"`
	Equipment       int `json:"equipment"`
	SpatialFeatures int `json:"spatial_features"`
	APICallsToday   int `json:"api_calls_today"`
}

// Building represents a building entity
type Building struct {
	ID   string `json:"id"`
	Name string `json:"name"`
	Path string `json:"path"`
}

// Equipment represents an equipment entity
type Equipment struct {
	ID   string `json:"id"`
	Name string `json:"name"`
	Type string `json:"type"`
	Path string `json:"path"`
}

// RegisterCoreRoutes registers Core tier API routes
func (ch *CoreHandlers) RegisterCoreRoutes(r chi.Router) {
	r.Route("/api/v1/core", func(r chi.Router) {
		// Dashboard endpoints
		r.Get("/dashboard/stats", ch.handleDashboardStats)
		r.Get("/buildings/recent", ch.handleRecentBuildings)
		r.Get("/equipment/recent", ch.handleRecentEquipment)

		// Building management
		r.Get("/buildings", ch.handleListBuildings)
		r.Post("/buildings", ch.handleCreateBuilding)
		r.Get("/buildings/{id}", ch.handleGetBuilding)
		r.Put("/buildings/{id}", ch.handleUpdateBuilding)
		r.Delete("/buildings/{id}", ch.handleDeleteBuilding)

		// Equipment management
		r.Get("/equipment", ch.handleListEquipment)
		r.Post("/equipment", ch.handleCreateEquipment)
		r.Get("/equipment/{id}", ch.handleGetEquipment)
		r.Put("/equipment/{id}", ch.handleUpdateEquipment)
		r.Delete("/equipment/{id}", ch.handleDeleteEquipment)
	})
}

// Dashboard Stats Handler
func (ch *CoreHandlers) handleDashboardStats(w http.ResponseWriter, r *http.Request) {
	// For now, return mock data. In production, this would query the database
	stats := DashboardStats{
		Buildings:       12,
		Equipment:       45,
		SpatialFeatures: 128,
		APICallsToday:   234,
	}

	// If this is an HTMX request, return HTML fragment
	if r.Header.Get("HX-Request") == "true" {
		w.Header().Set("Content-Type", "text/html")
		w.Write([]byte(`
			<div class="tier-card core tier-fade-in">
				<div class="tier-card-body text-center">
					<div class="text-3xl font-bold text-blue-600">` + strconv.Itoa(stats.Buildings) + `</div>
					<div class="text-sm text-gray-600">Buildings</div>
				</div>
			</div>
			<div class="tier-card core tier-fade-in">
				<div class="tier-card-body text-center">
					<div class="text-3xl font-bold text-blue-600">` + strconv.Itoa(stats.Equipment) + `</div>
					<div class="text-sm text-gray-600">Equipment</div>
				</div>
			</div>
			<div class="tier-card core tier-fade-in">
				<div class="tier-card-body text-center">
					<div class="text-3xl font-bold text-blue-600">` + strconv.Itoa(stats.SpatialFeatures) + `</div>
					<div class="text-sm text-gray-600">Spatial Features</div>
				</div>
			</div>
			<div class="tier-card core tier-fade-in">
				<div class="tier-card-body text-center">
					<div class="text-3xl font-bold text-green-600">` + strconv.Itoa(stats.APICallsToday) + `</div>
					<div class="text-sm text-gray-600">API Calls Today</div>
				</div>
			</div>
		`))
		return
	}

	// Regular JSON API response
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(stats)
}

// Recent Buildings Handler
func (ch *CoreHandlers) handleRecentBuildings(w http.ResponseWriter, r *http.Request) {
	// For now, return mock data. In production, this would query the database
	buildings := []Building{
		{ID: "1", Name: "Main Office Building", Path: "/buildings/main-office"},
		{ID: "2", Name: "Warehouse Complex", Path: "/buildings/warehouse"},
		{ID: "3", Name: "Research Facility", Path: "/buildings/research"},
		{ID: "4", Name: "Manufacturing Plant", Path: "/buildings/manufacturing"},
		{ID: "5", Name: "Data Center", Path: "/buildings/datacenter"},
	}

	// If this is an HTMX request, return HTML fragment
	if r.Header.Get("HX-Request") == "true" {
		w.Header().Set("Content-Type", "text/html")
		html := ""
		for _, building := range buildings {
			html += `
				<div class="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
					<div>
						<h4 class="font-medium">` + building.Name + `</h4>
						<p class="text-sm text-gray-600">` + building.Path + `</p>
					</div>
					<span class="tier-status success">Active</span>
				</div>
			`
		}
		w.Write([]byte(html))
		return
	}

	// Regular JSON API response
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(buildings)
}

// Recent Equipment Handler
func (ch *CoreHandlers) handleRecentEquipment(w http.ResponseWriter, r *http.Request) {
	// For now, return mock data. In production, this would query the database
	equipment := []Equipment{
		{ID: "1", Name: "HVAC Unit A", Type: "HVAC", Path: "/buildings/main-office/hvac/unit-a"},
		{ID: "2", Name: "Lighting System", Type: "Lighting", Path: "/buildings/main-office/lighting/main"},
		{ID: "3", Name: "Security Camera", Type: "Security", Path: "/buildings/main-office/security/cam-01"},
		{ID: "4", Name: "Fire Suppression", Type: "Safety", Path: "/buildings/main-office/safety/fire-sys"},
		{ID: "5", Name: "Elevator Control", Type: "Transport", Path: "/buildings/main-office/transport/elevator"},
	}

	// If this is an HTMX request, return HTML fragment
	if r.Header.Get("HX-Request") == "true" {
		w.Header().Set("Content-Type", "text/html")
		html := ""
		for _, item := range equipment {
			html += `
				<div class="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
					<div>
						<h4 class="font-medium">` + item.Name + `</h4>
						<p class="text-sm text-gray-600">` + item.Type + ` • ` + item.Path + `</p>
					</div>
					<span class="tier-status success">Active</span>
				</div>
			`
		}
		w.Write([]byte(html))
		return
	}

	// Regular JSON API response
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(equipment)
}

// Building Management Handlers
func (ch *CoreHandlers) handleListBuildings(w http.ResponseWriter, r *http.Request) {
	// TODO: Implement actual building listing
	http.Error(w, "Not implemented", http.StatusNotImplemented)
}

func (ch *CoreHandlers) handleCreateBuilding(w http.ResponseWriter, r *http.Request) {
	var req ecosystem.CreateBuildingRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "Invalid JSON", http.StatusBadRequest)
		return
	}

	// TODO: Implement actual building creation
	building, err := ch.coreService.CreateBuilding(r.Context(), req)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(building)
}

func (ch *CoreHandlers) handleGetBuilding(w http.ResponseWriter, r *http.Request) {
	// TODO: Implement actual building retrieval
	http.Error(w, "Not implemented", http.StatusNotImplemented)
}

func (ch *CoreHandlers) handleUpdateBuilding(w http.ResponseWriter, r *http.Request) {
	// TODO: Implement actual building update
	http.Error(w, "Not implemented", http.StatusNotImplemented)
}

func (ch *CoreHandlers) handleDeleteBuilding(w http.ResponseWriter, r *http.Request) {
	// TODO: Implement actual building deletion
	http.Error(w, "Not implemented", http.StatusNotImplemented)
}

// Equipment Management Handlers
func (ch *CoreHandlers) handleListEquipment(w http.ResponseWriter, r *http.Request) {
	// TODO: Implement actual equipment listing
	http.Error(w, "Not implemented", http.StatusNotImplemented)
}

func (ch *CoreHandlers) handleCreateEquipment(w http.ResponseWriter, r *http.Request) {
	var req ecosystem.CreateEquipmentRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "Invalid JSON", http.StatusBadRequest)
		return
	}

	// TODO: Implement actual equipment creation
	equipment, err := ch.coreService.CreateEquipment(r.Context(), req)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(equipment)
}

func (ch *CoreHandlers) handleGetEquipment(w http.ResponseWriter, r *http.Request) {
	// TODO: Implement actual equipment retrieval
	http.Error(w, "Not implemented", http.StatusNotImplemented)
}

func (ch *CoreHandlers) handleUpdateEquipment(w http.ResponseWriter, r *http.Request) {
	// TODO: Implement actual equipment update
	http.Error(w, "Not implemented", http.StatusNotImplemented)
}

func (ch *CoreHandlers) handleDeleteEquipment(w http.ResponseWriter, r *http.Request) {
	// TODO: Implement actual equipment deletion
	http.Error(w, "Not implemented", http.StatusNotImplemented)
}
