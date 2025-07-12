package handlers

import (
	"arx/models"
	"encoding/json"
	"fmt"
	"net/http"
	"strconv"
	"time"

	"github.com/go-chi/chi/v5"
	"gorm.io/gorm"
)

// ComplianceReportingHandler handles compliance and reporting features
type ComplianceReportingHandler struct {
	db *gorm.DB
}

// NewComplianceReportingHandler creates a new compliance reporting handler
func NewComplianceReportingHandler(db *gorm.DB) *ComplianceReportingHandler {
	return &ComplianceReportingHandler{db: db}
}

// DataAccessLog represents a data access event for auditors
type DataAccessLog struct {
	ID          uint      `json:"id"`
	UserID      uint      `json:"user_id"`
	Username    string    `json:"username"`
	Email       string    `json:"email"`
	Action      string    `json:"action"` // view, export, modify, delete
	ObjectType  string    `json:"object_type"`
	ObjectID    string    `json:"object_id"`
	IPAddress   string    `json:"ip_address"`
	UserAgent   string    `json:"user_agent"`
	SessionID   string    `json:"session_id"`
	BuildingID  *uint     `json:"building_id"`
	FloorID     *uint     `json:"floor_id"`
	AssetID     *string   `json:"asset_id"`
	ExportID    *uint     `json:"export_id"`
	AccessLevel string    `json:"access_level"` // basic, premium, enterprise, admin
	CreatedAt   time.Time `json:"created_at"`
}

// ChangeHistoryReport represents a change history report
type ChangeHistoryReport struct {
	ID           uint                   `json:"id"`
	ObjectType   string                 `json:"object_type"`
	ObjectID     string                 `json:"object_id"`
	ChangeType   string                 `json:"change_type"` // created, updated, deleted
	UserID       uint                   `json:"user_id"`
	Username     string                 `json:"username"`
	FieldChanges map[string]interface{} `json:"field_changes"`
	Context      map[string]interface{} `json:"context"`
	IPAddress    string                 `json:"ip_address"`
	CreatedAt    time.Time              `json:"created_at"`
}

// ExportActivitySummary represents an export activity summary
type ExportActivitySummary struct {
	Period            string         `json:"period"`
	TotalExports      int            `json:"total_exports"`
	TotalDownloads    int            `json:"total_downloads"`
	TotalFileSize     int64          `json:"total_file_size"`
	UniqueUsers       int            `json:"unique_users"`
	FailedExports     int            `json:"failed_exports"`
	AvgProcessingTime int            `json:"avg_processing_time"`
	TopFormats        map[string]int `json:"top_formats"`
	TopExportTypes    map[string]int `json:"top_export_types"`
}

// DataRetentionPolicy represents a data retention policy
type DataRetentionPolicy struct {
	ID              uint      `json:"id"`
	ObjectType      string    `json:"object_type"`
	RetentionPeriod int       `json:"retention_period"` // in days
	ArchiveAfter    int       `json:"archive_after"`    // in days
	DeleteAfter     int       `json:"delete_after"`     // in days
	IsActive        bool      `json:"is_active"`
	Description     string    `json:"description"`
	CreatedAt       time.Time `json:"created_at"`
	UpdatedAt       time.Time `json:"updated_at"`
}

// GET /api/compliance/data-access-logs - Get data access logs for auditors
func (h *ComplianceReportingHandler) GetDataAccessLogs(w http.ResponseWriter, r *http.Request) {
	// Parse query parameters
	userID := r.URL.Query().Get("user_id")
	buildingID := r.URL.Query().Get("building_id")
	action := r.URL.Query().Get("action")
	objectType := r.URL.Query().Get("object_type")
	dateFrom := r.URL.Query().Get("date_from")
	dateTo := r.URL.Query().Get("date_to")
	accessLevel := r.URL.Query().Get("access_level")

	// Pagination
	page, _ := strconv.Atoi(r.URL.Query().Get("page"))
	if page < 1 {
		page = 1
	}
	pageSize, _ := strconv.Atoi(r.URL.Query().Get("page_size"))
	if pageSize < 1 || pageSize > 1000 {
		pageSize = 100 // Larger page size for compliance reports
	}
	offset := (page - 1) * pageSize

	// Build query with user information
	query := h.db.Table("audit_logs").
		Select("audit_logs.*, users.username, users.email").
		Joins("LEFT JOIN users ON audit_logs.user_id = users.id")

	// Apply filters
	if userID != "" {
		if userIDInt, err := strconv.ParseUint(userID, 10, 32); err == nil {
			query = query.Where("audit_logs.user_id = ?", userIDInt)
		}
	}

	if buildingID != "" {
		if buildingIDInt, err := strconv.ParseUint(buildingID, 10, 32); err == nil {
			query = query.Where("audit_logs.building_id = ?", buildingIDInt)
		}
	}

	if action != "" {
		query = query.Where("audit_logs.action = ?", action)
	}

	if objectType != "" {
		query = query.Where("audit_logs.object_type = ?", objectType)
	}

	if dateFrom != "" {
		if dateFromTime, err := time.Parse("2006-01-02", dateFrom); err == nil {
			query = query.Where("audit_logs.created_at >= ?", dateFromTime)
		}
	}

	if dateTo != "" {
		if dateToTime, err := time.Parse("2006-01-02", dateTo); err == nil {
			dateToTime = dateToTime.Add(24 * time.Hour)
			query = query.Where("audit_logs.created_at < ?", dateToTime)
		}
	}

	if accessLevel != "" {
		query = query.Where("users.role = ?", accessLevel)
	}

	// Count total results
	var total int64
	query.Count(&total)

	// Get paginated results
	var logs []DataAccessLog
	query.Order("audit_logs.created_at desc").Offset(offset).Limit(pageSize).Find(&logs)

	// Check if export is requested
	exportFormat := r.URL.Query().Get("export")
	if exportFormat != "" {
		exportDataAccessLogs(w, logs, exportFormat)
		return
	}

	// Return JSON response
	resp := map[string]interface{}{
		"results":     logs,
		"page":        page,
		"page_size":   pageSize,
		"total":       total,
		"total_pages": (total + int64(pageSize) - 1) / int64(pageSize),
		"filters": map[string]interface{}{
			"user_id":      userID,
			"building_id":  buildingID,
			"action":       action,
			"object_type":  objectType,
			"date_from":    dateFrom,
			"date_to":      dateTo,
			"access_level": accessLevel,
		},
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(resp)
}

// GET /api/compliance/change-history/{object_type}/{object_id} - Get change history for a specific object
func (h *ComplianceReportingHandler) GetChangeHistory(w http.ResponseWriter, r *http.Request) {
	objectType := chi.URLParam(r, "object_type")
	objectID := chi.URLParam(r, "object_id")

	if objectType == "" || objectID == "" {
		http.Error(w, "Object type and object ID are required", http.StatusBadRequest)
		return
	}

	// Parse query parameters
	dateFrom := r.URL.Query().Get("date_from")
	dateTo := r.URL.Query().Get("date_to")
	changeType := r.URL.Query().Get("change_type")

	// Build query
	query := h.db.Table("audit_logs").
		Select("audit_logs.*, users.username").
		Joins("LEFT JOIN users ON audit_logs.user_id = users.id").
		Where("audit_logs.object_type = ? AND audit_logs.object_id = ?", objectType, objectID)

	// Apply filters
	if dateFrom != "" {
		if dateFromTime, err := time.Parse("2006-01-02", dateFrom); err == nil {
			query = query.Where("audit_logs.created_at >= ?", dateFromTime)
		}
	}

	if dateTo != "" {
		if dateToTime, err := time.Parse("2006-01-02", dateTo); err == nil {
			dateToTime = dateToTime.Add(24 * time.Hour)
			query = query.Where("audit_logs.created_at < ?", dateToTime)
		}
	}

	if changeType != "" {
		query = query.Where("audit_logs.action = ?", changeType)
	}

	// Get results
	var changes []ChangeHistoryReport
	query.Order("audit_logs.created_at desc").Find(&changes)

	// Check if export is requested
	exportFormat := r.URL.Query().Get("export")
	if exportFormat != "" {
		exportChangeHistory(w, changes, exportFormat)
		return
	}

	// Return JSON response
	resp := map[string]interface{}{
		"object_type": objectType,
		"object_id":   objectID,
		"changes":     changes,
		"total":       len(changes),
		"filters": map[string]interface{}{
			"date_from":   dateFrom,
			"date_to":     dateTo,
			"change_type": changeType,
		},
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(resp)
}

// GET /api/compliance/export-activity-summary - Get export activity summary
func (h *ComplianceReportingHandler) GetExportActivitySummary(w http.ResponseWriter, r *http.Request) {
	period := r.URL.Query().Get("period") // daily, weekly, monthly, yearly
	if period == "" {
		period = "monthly"
	}

	dateFrom := r.URL.Query().Get("date_from")
	dateTo := r.URL.Query().Get("date_to")

	// Set default date range if not provided
	if dateFrom == "" {
		switch period {
		case "daily":
			dateFrom = time.Now().Format("2006-01-02")
		case "weekly":
			dateFrom = time.Now().AddDate(0, 0, -7).Format("2006-01-02")
		case "monthly":
			dateFrom = time.Now().AddDate(0, -1, 0).Format("2006-01-02")
		case "yearly":
			dateFrom = time.Now().AddDate(-1, 0, 0).Format("2006-01-02")
		}
	}

	if dateTo == "" {
		dateTo = time.Now().Format("2006-01-02")
	}

	// Parse dates
	startDate, err := time.Parse("2006-01-02", dateFrom)
	if err != nil {
		http.Error(w, "Invalid start date", http.StatusBadRequest)
		return
	}

	endDate, err := time.Parse("2006-01-02", dateTo)
	if err != nil {
		http.Error(w, "Invalid end date", http.StatusBadRequest)
		return
	}

	// Build query
	query := h.db.Model(&models.ExportActivity{}).Where("created_at BETWEEN ? AND ?", startDate, endDate)

	// Get summary statistics
	var summary ExportActivitySummary
	summary.Period = period

	// Total exports
	var totalExports int64
	query.Count(&totalExports)
	summary.TotalExports = int(totalExports)

	// Total downloads
	h.db.Model(&models.ExportActivity{}).Where("created_at BETWEEN ? AND ?", startDate, endDate).
		Select("COALESCE(SUM(download_count), 0)").Scan(&summary.TotalDownloads)

	// Total file size
	h.db.Model(&models.ExportActivity{}).Where("created_at BETWEEN ? AND ?", startDate, endDate).
		Select("COALESCE(SUM(file_size), 0)").Scan(&summary.TotalFileSize)

	// Unique users
	var uniqueUsers int64
	h.db.Model(&models.ExportActivity{}).Where("created_at BETWEEN ? AND ?", startDate, endDate).
		Distinct("user_id").Count(&uniqueUsers)
	summary.UniqueUsers = int(uniqueUsers)

	// Failed exports
	var failedExports int64
	h.db.Model(&models.ExportActivity{}).Where("created_at BETWEEN ? AND ? AND status = 'failed'", startDate, endDate).
		Count(&failedExports)
	summary.FailedExports = int(failedExports)

	// Average processing time
	h.db.Model(&models.ExportActivity{}).Where("created_at BETWEEN ? AND ? AND processing_time > 0", startDate, endDate).
		Select("COALESCE(AVG(processing_time), 0)").Scan(&summary.AvgProcessingTime)

	// Top formats
	var formatStats []struct {
		Format string
		Count  int
	}
	h.db.Model(&models.ExportActivity{}).Where("created_at BETWEEN ? AND ?", startDate, endDate).
		Select("format, COUNT(*) as count").
		Group("format").
		Order("count DESC").
		Limit(10).
		Find(&formatStats)

	summary.TopFormats = make(map[string]int)
	for _, stat := range formatStats {
		summary.TopFormats[stat.Format] = stat.Count
	}

	// Top export types
	var typeStats []struct {
		ExportType string
		Count      int
	}
	h.db.Model(&models.ExportActivity{}).Where("created_at BETWEEN ? AND ?", startDate, endDate).
		Select("export_type, COUNT(*) as count").
		Group("export_type").
		Order("count DESC").
		Limit(10).
		Find(&typeStats)

	summary.TopExportTypes = make(map[string]int)
	for _, stat := range typeStats {
		summary.TopExportTypes[stat.ExportType] = stat.Count
	}

	// Return JSON response
	resp := map[string]interface{}{
		"summary": summary,
		"filters": map[string]interface{}{
			"period":    period,
			"date_from": dateFrom,
			"date_to":   dateTo,
		},
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(resp)
}

// GET /api/compliance/data-retention-policies - Get data retention policies
func (h *ComplianceReportingHandler) GetDataRetentionPolicies(w http.ResponseWriter, r *http.Request) {
	var policies []DataRetentionPolicy
	h.db.Find(&policies)

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{
		"policies": policies,
		"total":    len(policies),
	})
}

// POST /api/compliance/data-retention-policies - Create a new data retention policy
func (h *ComplianceReportingHandler) CreateDataRetentionPolicy(w http.ResponseWriter, r *http.Request) {
	var policy DataRetentionPolicy
	if err := json.NewDecoder(r.Body).Decode(&policy); err != nil {
		http.Error(w, "Invalid request body", http.StatusBadRequest)
		return
	}

	policy.CreatedAt = time.Now()
	policy.UpdatedAt = time.Now()

	if err := h.db.Create(&policy).Error; err != nil {
		http.Error(w, "Failed to create retention policy", http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusCreated)
	json.NewEncoder(w).Encode(policy)
}

// PUT /api/compliance/data-retention-policies/{id} - Update a data retention policy
func (h *ComplianceReportingHandler) UpdateDataRetentionPolicy(w http.ResponseWriter, r *http.Request) {
	policyID := chi.URLParam(r, "id")
	if policyID == "" {
		http.Error(w, "Policy ID is required", http.StatusBadRequest)
		return
	}

	var policy DataRetentionPolicy
	if err := h.db.First(&policy, policyID).Error; err != nil {
		http.Error(w, "Policy not found", http.StatusNotFound)
		return
	}

	var updateData DataRetentionPolicy
	if err := json.NewDecoder(r.Body).Decode(&updateData); err != nil {
		http.Error(w, "Invalid request body", http.StatusBadRequest)
		return
	}

	// Update fields
	policy.RetentionPeriod = updateData.RetentionPeriod
	policy.ArchiveAfter = updateData.ArchiveAfter
	policy.DeleteAfter = updateData.DeleteAfter
	policy.IsActive = updateData.IsActive
	policy.Description = updateData.Description
	policy.UpdatedAt = time.Now()

	if err := h.db.Save(&policy).Error; err != nil {
		http.Error(w, "Failed to update retention policy", http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(policy)
}

// POST /api/compliance/archive-old-logs - Archive old audit logs
func (h *ComplianceReportingHandler) ArchiveOldLogs(w http.ResponseWriter, r *http.Request) {
	var request struct {
		ObjectType string `json:"object_type"`
		OlderThan  int    `json:"older_than_days"`
		DryRun     bool   `json:"dry_run"`
	}

	if err := json.NewDecoder(r.Body).Decode(&request); err != nil {
		http.Error(w, "Invalid request body", http.StatusBadRequest)
		return
	}

	if request.OlderThan <= 0 {
		request.OlderThan = 365 // Default to 1 year
	}

	cutoffDate := time.Now().AddDate(0, 0, -request.OlderThan)

	// Count logs that would be archived
	var count int64
	query := h.db.Model(&models.AuditLog{}).Where("created_at < ?", cutoffDate)
	if request.ObjectType != "" {
		query = query.Where("object_type = ?", request.ObjectType)
	}
	query.Count(&count)

	if request.DryRun {
		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(map[string]interface{}{
			"dry_run":         true,
			"logs_to_archive": count,
			"cutoff_date":     cutoffDate.Format("2006-01-02"),
			"object_type":     request.ObjectType,
		})
		return
	}

	// Archive logs (move to archive table or mark as archived)
	// For now, we'll just mark them as archived by updating a status field
	// In a real implementation, you might move them to a separate archive table
	result := h.db.Model(&models.AuditLog{}).Where("created_at < ?", cutoffDate)
	if request.ObjectType != "" {
		result = result.Where("object_type = ?", request.ObjectType)
	}
	result.Update("archived", true)

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{
		"archived_logs": count,
		"cutoff_date":   cutoffDate.Format("2006-01-02"),
		"object_type":   request.ObjectType,
	})
}

// Helper functions for exporting data
func exportDataAccessLogs(w http.ResponseWriter, logs []DataAccessLog, format string) {
	switch format {
	case "csv":
		exportDataAccessLogsCSV(w, logs)
	case "json":
		exportDataAccessLogsJSON(w, logs)
	default:
		http.Error(w, "Unsupported export format", http.StatusBadRequest)
	}
}

func exportDataAccessLogsCSV(w http.ResponseWriter, logs []DataAccessLog) {
	w.Header().Set("Content-Type", "text/csv")
	w.Header().Set("Content-Disposition", "attachment; filename=data_access_logs.csv")

	// Write CSV header
	w.Write([]byte("ID,User ID,Username,Email,Action,Object Type,Object ID,IP Address,User Agent,Session ID,Building ID,Floor ID,Asset ID,Export ID,Access Level,Created At\n"))

	// Write data rows
	for _, log := range logs {
		line := fmt.Sprintf("%d,%d,%s,%s,%s,%s,%s,%s,%s,%s,%v,%v,%v,%v,%s,%s\n",
			log.ID, log.UserID, log.Username, log.Email, log.Action, log.ObjectType, log.ObjectID,
			log.IPAddress, log.UserAgent, log.SessionID, log.BuildingID, log.FloorID, log.AssetID,
			log.ExportID, log.AccessLevel, log.CreatedAt.Format("2006-01-02 15:04:05"))
		w.Write([]byte(line))
	}
}

func exportDataAccessLogsJSON(w http.ResponseWriter, logs []DataAccessLog) {
	w.Header().Set("Content-Type", "application/json")
	w.Header().Set("Content-Disposition", "attachment; filename=data_access_logs.json")
	json.NewEncoder(w).Encode(logs)
}

func exportChangeHistory(w http.ResponseWriter, changes []ChangeHistoryReport, format string) {
	switch format {
	case "csv":
		exportChangeHistoryCSV(w, changes)
	case "json":
		exportChangeHistoryJSON(w, changes)
	default:
		http.Error(w, "Unsupported export format", http.StatusBadRequest)
	}
}

func exportChangeHistoryCSV(w http.ResponseWriter, changes []ChangeHistoryReport) {
	w.Header().Set("Content-Type", "text/csv")
	w.Header().Set("Content-Disposition", "attachment; filename=change_history.csv")

	// Write CSV header
	w.Write([]byte("ID,Object Type,Object ID,Change Type,User ID,Username,Field Changes,Context,IP Address,Created At\n"))

	// Write data rows
	for _, change := range changes {
		fieldChanges, _ := json.Marshal(change.FieldChanges)
		context, _ := json.Marshal(change.Context)

		line := fmt.Sprintf("%d,%s,%s,%s,%d,%s,%s,%s,%s,%s\n",
			change.ID, change.ObjectType, change.ObjectID, change.ChangeType,
			change.UserID, change.Username, string(fieldChanges), string(context),
			change.IPAddress, change.CreatedAt.Format("2006-01-02 15:04:05"))
		w.Write([]byte(line))
	}
}

func exportChangeHistoryJSON(w http.ResponseWriter, changes []ChangeHistoryReport) {
	w.Header().Set("Content-Type", "application/json")
	w.Header().Set("Content-Disposition", "attachment; filename=change_history.json")
	json.NewEncoder(w).Encode(changes)
}
