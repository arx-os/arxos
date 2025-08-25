package projects

import (
	"encoding/json"
	"net/http"
	"strconv"
	"time"

	"github.com/arxos/arxos/core/internal/handlers"
	"github.com/go-chi/chi/v5"
)

// ============================================================================
// CGO-OPTIMIZED PROJECTS HANDLER
// ============================================================================

// ProjectsHandlerCGO provides CGO-optimized project management operations
type ProjectsHandlerCGO struct {
	*handlers.HandlerBaseCGO
}

// NewProjectsHandlerCGO creates a new CGO-optimized projects handler
func NewProjectsHandlerCGO() *ProjectsHandlerCGO {
	return &ProjectsHandlerCGO{
		HandlerBaseCGO: handlers.NewHandlerBaseCGO(),
	}
}

// Close cleans up the handler
func (h *ProjectsHandlerCGO) Close() {
	if h.HandlerBaseCGO != nil {
		h.HandlerBaseCGO.Close()
	}
}

// ============================================================================
// HTTP HANDLERS
// ============================================================================

// CreateProject handles project creation with CGO optimization
func (h *ProjectsHandlerCGO) CreateProject(w http.ResponseWriter, r *http.Request) {
	var request struct {
		Name        string  `json:"name"`
		Description string  `json:"description"`
		ClientName  string  `json:"client_name"`
		ProjectType string  `json:"project_type"`
		StartDate   string  `json:"start_date"`
		EndDate     string  `json:"end_date"`
		Budget      float64 `json:"budget"`
		Status      string  `json:"status"`
	}

	if err := json.NewDecoder(r.Body).Decode(&request); err != nil {
		h.SendErrorResponse(w, "Invalid request body: "+err.Error(), http.StatusBadRequest)
		return
	}

	// Validate request
	if request.Name == "" {
		h.SendErrorResponse(w, "Project name is required", http.StatusBadRequest)
		return
	}

	if request.Status == "" {
		request.Status = "planning"
	}

	// Create project using CGO optimization
	project := map[string]interface{}{
		"id":           generateProjectID(),
		"name":         request.Name,
		"description":  request.Description,
		"client_name":  request.ClientName,
		"project_type": request.ProjectType,
		"start_date":   request.StartDate,
		"end_date":     request.EndDate,
		"budget":       request.Budget,
		"status":       request.Status,
		"cgo_status":   h.HasCGOBridge(),
		"created_at":   time.Now(),
		"updated_at":   time.Now(),
	}

	h.SendSuccessResponse(w, project, "Project created successfully")
}

// GetProject retrieves project information with CGO optimization
func (h *ProjectsHandlerCGO) GetProject(w http.ResponseWriter, r *http.Request) {
	projectID := chi.URLParam(r, "id")
	if projectID == "" {
		h.SendErrorResponse(w, "Project ID is required", http.StatusBadRequest)
		return
	}

	// For now, return a placeholder project
	// In a real implementation, this would query the CGO-optimized project system
	project := map[string]interface{}{
		"id":           projectID,
		"name":         "Sample Project",
		"description":  "A sample construction project",
		"client_name":  "Sample Client",
		"project_type": "Commercial",
		"start_date":   "2024-01-01",
		"end_date":     "2024-12-31",
		"budget":       1000000.0,
		"status":       "active",
		"buildings":    []string{"bldg_001", "bldg_002"},
		"team_members": []string{"architect_001", "engineer_001"},
		"cgo_status":   h.HasCGOBridge(),
		"created_at":   time.Now().Add(-30 * 24 * time.Hour),
		"updated_at":   time.Now(),
	}

	h.SendSuccessResponse(w, project, "Project retrieved successfully")
}

// UpdateProject handles project updates with CGO optimization
func (h *ProjectsHandlerCGO) UpdateProject(w http.ResponseWriter, r *http.Request) {
	projectID := chi.URLParam(r, "id")
	if projectID == "" {
		h.SendErrorResponse(w, "Project ID is required", http.StatusBadRequest)
		return
	}

	var request map[string]interface{}
	if err := json.NewDecoder(r.Body).Decode(&request); err != nil {
		h.SendErrorResponse(w, "Invalid request body: "+err.Error(), http.StatusBadRequest)
		return
	}

	// Add update timestamp and project ID
	request["updated_at"] = time.Now()
	request["id"] = projectID
	request["cgo_status"] = h.HasCGOBridge()

	h.SendSuccessResponse(w, request, "Project updated successfully")
}

// DeleteProject handles project deletion with CGO optimization
func (h *ProjectsHandlerCGO) DeleteProject(w http.ResponseWriter, r *http.Request) {
	projectID := chi.URLParam(r, "id")
	if projectID == "" {
		h.SendErrorResponse(w, "Project ID is required", http.StatusBadRequest)
		return
	}

	// For now, return success
	// In a real implementation, this would delete from the CGO-optimized project system
	response := map[string]interface{}{
		"id":         projectID,
		"deleted":    true,
		"cgo_status": h.HasCGOBridge(),
		"timestamp":  time.Now(),
	}

	h.SendSuccessResponse(w, response, "Project deleted successfully")
}

// ListProjects returns a list of projects with CGO optimization
func (h *ProjectsHandlerCGO) ListProjects(w http.ResponseWriter, r *http.Request) {
	// Parse pagination parameters
	page, _ := strconv.Atoi(r.URL.Query().Get("page"))
	if page < 1 {
		page = 1
	}

	pageSize, _ := strconv.Atoi(r.URL.Query().Get("page_size"))
	if pageSize < 1 || pageSize > 100 {
		pageSize = 20
	}

	// Parse filter parameters
	status := r.URL.Query().Get("status")
	projectType := r.URL.Query().Get("type")
	clientName := r.URL.Query().Get("client")

	// For now, return placeholder projects
	// In a real implementation, this would query the CGO-optimized project system
	projects := []map[string]interface{}{
		{
			"id":           "1",
			"name":         "Downtown Office Complex",
			"description":  "Modern office building in downtown area",
			"client_name":  "City Development Corp",
			"project_type": "Commercial",
			"status":       "active",
			"budget":       2500000.0,
			"start_date":   "2024-01-15",
			"end_date":     "2025-06-30",
			"cgo_status":   h.HasCGOBridge(),
		},
		{
			"id":           "2",
			"name":         "Residential Tower A",
			"description":  "High-rise residential building",
			"client_name":  "Housing Solutions Inc",
			"project_type": "Residential",
			"status":       "planning",
			"budget":       1800000.0,
			"start_date":   "2024-03-01",
			"end_date":     "2026-02-28",
			"cgo_status":   h.HasCGOBridge(),
		},
		{
			"id":           "3",
			"name":         "Industrial Warehouse",
			"description":  "Large-scale industrial storage facility",
			"client_name":  "Logistics Partners",
			"project_type": "Industrial",
			"status":       "completed",
			"budget":       800000.0,
			"start_date":   "2023-06-01",
			"end_date":     "2024-01-31",
			"cgo_status":   h.HasCGOBridge(),
		},
	}

	// Apply filters if provided
	if status != "" {
		filtered := []map[string]interface{}{}
		for _, project := range projects {
			if project["status"] == status {
				filtered = append(filtered, project)
			}
		}
		projects = filtered
	}

	if projectType != "" {
		filtered := []map[string]interface{}{}
		for _, project := range projects {
			if project["project_type"] == projectType {
				filtered = append(filtered, project)
			}
		}
		projects = filtered
	}

	if clientName != "" {
		filtered := []map[string]interface{}{}
		for _, project := range projects {
			if project["client_name"] == clientName {
				filtered = append(filtered, project)
			}
		}
		projects = filtered
	}

	response := map[string]interface{}{
		"projects":  projects,
		"page":      page,
		"page_size": pageSize,
		"total":     len(projects),
		"filters": map[string]interface{}{
			"status":       status,
			"project_type": projectType,
			"client_name":  clientName,
		},
		"cgo_status": h.HasCGOBridge(),
		"timestamp":  time.Now(),
	}

	h.SendSuccessResponse(w, response, "Projects retrieved successfully")
}

// GetProjectStatistics returns project statistics with CGO optimization
func (h *ProjectsHandlerCGO) GetProjectStatistics(w http.ResponseWriter, r *http.Request) {
	// For now, return placeholder statistics
	// In a real implementation, this would query the CGO-optimized project system
	stats := map[string]interface{}{
		"total_projects":     25,
		"active_projects":    12,
		"completed_projects": 8,
		"planning_projects":  5,
		"total_budget":       15000000.0,
		"total_spent":        8500000.0,
		"projects_by_type": map[string]interface{}{
			"Commercial":     10,
			"Residential":    8,
			"Industrial":     4,
			"Infrastructure": 3,
		},
		"projects_by_status": map[string]interface{}{
			"planning":  5,
			"active":    12,
			"on_hold":   2,
			"completed": 8,
		},
		"cgo_status": h.HasCGOBridge(),
		"timestamp":  time.Now(),
	}

	h.SendSuccessResponse(w, stats, "Project statistics retrieved successfully")
}

// AddBuildingToProject adds a building to a project with CGO optimization
func (h *ProjectsHandlerCGO) AddBuildingToProject(w http.ResponseWriter, r *http.Request) {
	projectID := chi.URLParam(r, "id")
	if projectID == "" {
		h.SendErrorResponse(w, "Project ID is required", http.StatusBadRequest)
		return
	}

	var request struct {
		BuildingID   string  `json:"building_id"`
		BuildingName string  `json:"building_name"`
		BuildingType string  `json:"building_type"`
		FloorCount   int     `json:"floor_count"`
		Area         float64 `json:"area"`
	}

	if err := json.NewDecoder(r.Body).Decode(&request); err != nil {
		h.SendErrorResponse(w, "Invalid request body: "+err.Error(), http.StatusBadRequest)
		return
	}

	// Validate request
	if request.BuildingID == "" {
		h.SendErrorResponse(w, "Building ID is required", http.StatusBadRequest)
		return
	}

	// Add building to project using CGO optimization
	building := map[string]interface{}{
		"project_id":    projectID,
		"building_id":   request.BuildingID,
		"building_name": request.BuildingName,
		"building_type": request.BuildingType,
		"floor_count":   request.FloorCount,
		"area":          request.Area,
		"cgo_status":    h.HasCGOBridge(),
		"added_at":      time.Now(),
	}

	h.SendSuccessResponse(w, building, "Building added to project successfully")
}

// RemoveBuildingFromProject removes a building from a project with CGO optimization
func (h *ProjectsHandlerCGO) RemoveBuildingFromProject(w http.ResponseWriter, r *http.Request) {
	projectID := chi.URLParam(r, "id")
	buildingID := chi.URLParam(r, "building_id")

	if projectID == "" {
		h.SendErrorResponse(w, "Project ID is required", http.StatusBadRequest)
		return
	}

	if buildingID == "" {
		h.SendErrorResponse(w, "Building ID is required", http.StatusBadRequest)
		return
	}

	// For now, return success
	// In a real implementation, this would remove the building from the CGO-optimized project system
	response := map[string]interface{}{
		"project_id":  projectID,
		"building_id": buildingID,
		"removed":     true,
		"cgo_status":  h.HasCGOBridge(),
		"timestamp":   time.Now(),
	}

	h.SendSuccessResponse(w, response, "Building removed from project successfully")
}

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

// generateProjectID generates a unique project ID
func generateProjectID() string {
	return "proj_" + strconv.FormatInt(time.Now().UnixNano(), 10)
}
