// handlers/safety.go
package handlers

import (
	"encoding/json"
	"net/http"
	"strconv"
	"time"

	"github.com/go-chi/chi/v5"
)

// SafetyIncident represents a safety incident
type SafetyIncident struct {
	ID          uint      `json:"id"`
	ProjectID   uint      `json:"project_id"`
	FloorID     uint      `json:"floor_id"`
	Location    string    `json:"location"`
	Type        string    `json:"type"`     // hazard, incident, near_miss, violation
	Severity    string    `json:"severity"` // low, medium, high, critical
	Description string    `json:"description"`
	ReportedBy  uint      `json:"reported_by"`
	Status      string    `json:"status"` // open, investigating, resolved, closed
	CreatedAt   time.Time `json:"created_at"`
	UpdatedAt   time.Time `json:"updated_at"`
}

// SafetyInspection represents a safety inspection
type SafetyInspection struct {
	ID          uint       `json:"id"`
	ProjectID   uint       `json:"project_id"`
	FloorID     uint       `json:"floor_id"`
	InspectorID uint       `json:"inspector_id"`
	Type        string     `json:"type"`   // routine, incident, compliance
	Status      string     `json:"status"` // scheduled, in_progress, completed
	Score       int        `json:"score"`  // 0-100
	Notes       string     `json:"notes"`
	ScheduledAt time.Time  `json:"scheduled_at"`
	CompletedAt *time.Time `json:"completed_at"`
	CreatedAt   time.Time  `json:"created_at"`
	UpdatedAt   time.Time  `json:"updated_at"`
}

// SafetyChecklist represents a safety checklist item
type SafetyChecklist struct {
	ID          uint   `json:"id"`
	Category    string `json:"category"`
	Item        string `json:"item"`
	Description string `json:"description"`
	Required    bool   `json:"required"`
	Active      bool   `json:"active"`
}

// ListSafetyIncidents returns all safety incidents for a project
func ListSafetyIncidents(w http.ResponseWriter, r *http.Request) {
	user, err := GetUserFromRequest(r)
	if err != nil {
		http.Error(w, "Unauthorized", http.StatusUnauthorized)
		return
	}

	projectID, err := extractProjectID(r)
	if err != nil {
		http.Error(w, "Invalid project ID", http.StatusBadRequest)
		return
	}

	page, _ := strconv.Atoi(r.URL.Query().Get("page"))
	if page < 1 {
		page = 1
	}
	pageSize, _ := strconv.Atoi(r.URL.Query().Get("page_size"))
	if pageSize < 1 || pageSize > 100 {
		pageSize = 20
	}
	// Get incidents from database (placeholder - would need actual table)
	var incidents []SafetyIncident
	// db.DB.Where("project_id = ?", projectID).Offset(offset).Limit(pageSize).Find(&incidents)

	// Mock data for now
	incidents = []SafetyIncident{
		{
			ID:          1,
			ProjectID:   projectID,
			FloorID:     1,
			Location:    "Main Building - Floor 1",
			Type:        "hazard",
			Severity:    "medium",
			Description: "Wet floor in corridor - slip hazard",
			ReportedBy:  user.ID,
			Status:      "open",
			CreatedAt:   time.Now(),
			UpdatedAt:   time.Now(),
		},
	}

	resp := map[string]interface{}{
		"incidents":   incidents,
		"page":        page,
		"page_size":   pageSize,
		"total":       len(incidents),
		"total_pages": 1,
	}
	json.NewEncoder(w).Encode(resp)
}

// CreateSafetyIncident creates a new safety incident
func CreateSafetyIncident(w http.ResponseWriter, r *http.Request) {
	user, err := GetUserFromRequest(r)
	if err != nil {
		http.Error(w, "Unauthorized", http.StatusUnauthorized)
		return
	}

	var incident SafetyIncident
	if err := json.NewDecoder(r.Body).Decode(&incident); err != nil {
		http.Error(w, "Invalid JSON", http.StatusBadRequest)
		return
	}

	// Validate required fields
	if incident.Location == "" || incident.Type == "" || incident.Description == "" {
		http.Error(w, "Location, type, and description are required", http.StatusBadRequest)
		return
	}

	incident.ReportedBy = user.ID
	incident.Status = "open"
	incident.CreatedAt = time.Now()
	incident.UpdatedAt = time.Now()

	// Save to database (placeholder)
	// db.DB.Create(&incident)

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusCreated)
	json.NewEncoder(w).Encode(incident)
}

// GetSafetyIncident returns a specific safety incident
func GetSafetyIncident(w http.ResponseWriter, r *http.Request) {
	user, err := GetUserFromRequest(r)
	if err != nil {
		http.Error(w, "Unauthorized", http.StatusUnauthorized)
		return
	}

	incidentID := chi.URLParam(r, "id")
	id, err := strconv.Atoi(incidentID)
	if err != nil {
		http.Error(w, "Invalid incident ID", http.StatusBadRequest)
		return
	}

	// Get incident from database (placeholder)
	var incident SafetyIncident
	// db.DB.First(&incident, id)

	// Mock data
	incident = SafetyIncident{
		ID:          uint(id),
		ProjectID:   1,
		FloorID:     1,
		Location:    "Main Building - Floor 1",
		Type:        "hazard",
		Severity:    "medium",
		Description: "Wet floor in corridor - slip hazard",
		ReportedBy:  user.ID,
		Status:      "open",
		CreatedAt:   time.Now(),
		UpdatedAt:   time.Now(),
	}

	json.NewEncoder(w).Encode(incident)
}

// UpdateSafetyIncident updates a safety incident
func UpdateSafetyIncident(w http.ResponseWriter, r *http.Request) {
	_, err := GetUserFromRequest(r)
	if err != nil {
		http.Error(w, "Unauthorized", http.StatusUnauthorized)
		return
	}

	incidentID := chi.URLParam(r, "id")
	id, err := strconv.Atoi(incidentID)
	if err != nil {
		http.Error(w, "Invalid incident ID", http.StatusBadRequest)
		return
	}

	var updateData SafetyIncident
	if err := json.NewDecoder(r.Body).Decode(&updateData); err != nil {
		http.Error(w, "Invalid JSON", http.StatusBadRequest)
		return
	}

	// Update incident in database (placeholder)
	// db.DB.Model(&SafetyIncident{}).Where("id = ?", id).Updates(updateData)

	updateData.ID = uint(id)
	updateData.UpdatedAt = time.Now()

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(updateData)
}

// ListSafetyInspections returns all safety inspections for a project
func ListSafetyInspections(w http.ResponseWriter, r *http.Request) {
	user, err := GetUserFromRequest(r)
	if err != nil {
		http.Error(w, "Unauthorized", http.StatusUnauthorized)
		return
	}

	projectID, err := extractProjectID(r)
	if err != nil {
		http.Error(w, "Invalid project ID", http.StatusBadRequest)
		return
	}

	// Get inspections from database (placeholder)
	var inspections []SafetyInspection
	// db.DB.Where("project_id = ?", projectID).Find(&inspections)

	// Mock data
	inspections = []SafetyInspection{
		{
			ID:          1,
			ProjectID:   projectID,
			FloorID:     1,
			InspectorID: user.ID,
			Type:        "routine",
			Status:      "completed",
			Score:       85,
			Notes:       "Overall good safety practices, minor issues found",
			ScheduledAt: time.Now().AddDate(0, 0, -7),
			CompletedAt: &time.Time{},
			CreatedAt:   time.Now(),
			UpdatedAt:   time.Now(),
		},
	}

	resp := map[string]interface{}{
		"inspections": inspections,
	}
	json.NewEncoder(w).Encode(resp)
}

// CreateSafetyInspection creates a new safety inspection
func CreateSafetyInspection(w http.ResponseWriter, r *http.Request) {
	user, err := GetUserFromRequest(r)
	if err != nil {
		http.Error(w, "Unauthorized", http.StatusUnauthorized)
		return
	}

	var inspection SafetyInspection
	if err := json.NewDecoder(r.Body).Decode(&inspection); err != nil {
		http.Error(w, "Invalid JSON", http.StatusBadRequest)
		return
	}

	// Validate required fields
	if inspection.Type == "" {
		http.Error(w, "Inspection type is required", http.StatusBadRequest)
		return
	}

	inspection.InspectorID = user.ID
	inspection.Status = "scheduled"
	inspection.CreatedAt = time.Now()
	inspection.UpdatedAt = time.Now()

	// Save to database (placeholder)
	// db.DB.Create(&inspection)

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusCreated)
	json.NewEncoder(w).Encode(inspection)
}

// GetSafetyChecklist returns the safety checklist
func GetSafetyChecklist(w http.ResponseWriter, r *http.Request) {
	// Get checklist from database (placeholder)
	var checklist []SafetyChecklist
	// db.DB.Where("active = ?", true).Find(&checklist)

	// Mock data
	checklist = []SafetyChecklist{
		{
			ID:          1,
			Category:    "Personal Protective Equipment",
			Item:        "Hard hats",
			Description: "All workers must wear hard hats in construction areas",
			Required:    true,
			Active:      true,
		},
		{
			ID:          2,
			Category:    "Fall Protection",
			Item:        "Safety harnesses",
			Description: "Harnesses required when working at heights above 6 feet",
			Required:    true,
			Active:      true,
		},
		{
			ID:          3,
			Category:    "Fire Safety",
			Item:        "Fire extinguishers",
			Description: "Fire extinguishers must be accessible and properly maintained",
			Required:    true,
			Active:      true,
		},
	}

	resp := map[string]interface{}{
		"checklist": checklist,
	}
	json.NewEncoder(w).Encode(resp)
}

// GetSafetyStatistics returns safety statistics for a project
func GetSafetyStatistics(w http.ResponseWriter, r *http.Request) {
	_, err := GetUserFromRequest(r)
	if err != nil {
		http.Error(w, "Unauthorized", http.StatusUnauthorized)
		return
	}

	_, err = extractProjectID(r)
	if err != nil {
		http.Error(w, "Invalid project ID", http.StatusBadRequest)
		return
	}

	// Calculate statistics from database (placeholder)
	stats := map[string]interface{}{
		"total_incidents":            5,
		"open_incidents":             2,
		"resolved_incidents":         3,
		"critical_incidents":         1,
		"high_incidents":             2,
		"medium_incidents":           1,
		"low_incidents":              1,
		"total_inspections":          8,
		"completed_inspections":      6,
		"scheduled_inspections":      2,
		"average_inspection_score":   87,
		"days_since_last_incident":   12,
		"days_since_last_inspection": 3,
	}

	json.NewEncoder(w).Encode(stats)
}

// CreateSafetyReport creates a safety report
func CreateSafetyReport(w http.ResponseWriter, r *http.Request) {
	user, err := GetUserFromRequest(r)
	if err != nil {
		http.Error(w, "Unauthorized", http.StatusUnauthorized)
		return
	}

	var report struct {
		ProjectID  uint   `json:"project_id"`
		ReportType string `json:"report_type"` // daily, weekly, monthly, incident
		StartDate  string `json:"start_date"`
		EndDate    string `json:"end_date"`
		Format     string `json:"format"` // pdf, excel, json
	}

	if err := json.NewDecoder(r.Body).Decode(&report); err != nil {
		http.Error(w, "Invalid JSON", http.StatusBadRequest)
		return
	}

	// Generate report (placeholder)
	reportID := "SAF-" + time.Now().Format("20060102-150405")
	reportData := map[string]interface{}{
		"report_id":    reportID,
		"project_id":   report.ProjectID,
		"report_type":  report.ReportType,
		"start_date":   report.StartDate,
		"end_date":     report.EndDate,
		"format":       report.Format,
		"generated_by": user.ID,
		"generated_at": time.Now(),
		"status":       "completed",
		"download_url": "/api/safety/reports/" + reportID,
	}

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusCreated)
	json.NewEncoder(w).Encode(reportData)
}
