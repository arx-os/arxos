package handlers

import (
	"encoding/json"
	"fmt"
	"net/http"
	"strconv"
	"time"

	"github.com/arxos/arxos/core/backend/models"

	"github.com/gorilla/mux"
	"gorm.io/gorm"
)

// ExportActivityHandler handles export activity tracking
type ExportActivityHandler struct {
	db *gorm.DB
}

// NewExportActivityHandler creates a new export activity handler
func NewExportActivityHandler(db *gorm.DB) *ExportActivityHandler {
	return &ExportActivityHandler{db: db}
}

// CreateExportActivity tracks a new export request
func (h *ExportActivityHandler) CreateExportActivity(w http.ResponseWriter, r *http.Request) {
	var activity models.ExportActivity
	if err := json.NewDecoder(r.Body).Decode(&activity); err != nil {
		http.Error(w, "Invalid request body", http.StatusBadRequest)
		return
	}

	// Set default values
	activity.RequestedAt = time.Now()
	activity.Status = "requested"
	activity.IPAddress = getClientIP(r)
	activity.UserAgent = r.UserAgent()

	// Create the export activity
	if err := h.db.Create(&activity).Error; err != nil {
		http.Error(w, "Failed to create export activity", http.StatusInternalServerError)
		return
	}

	// Log the export activity
	models.LogExportChange(h.db, activity.UserID, activity.ID, "export_requested", map[string]interface{}{
		"export_type": activity.ExportType,
		"format":      activity.Format,
		"building_id": activity.BuildingID,
	}, r)

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusCreated)
	json.NewEncoder(w).Encode(map[string]interface{}{
		"id":     activity.ID,
		"status": "created",
	})
}

// UpdateExportActivity updates export completion status
func (h *ExportActivityHandler) UpdateExportActivity(w http.ResponseWriter, r *http.Request) {
	vars := mux.Vars(r)
	activityID, err := strconv.ParseUint(vars["id"], 10, 32)
	if err != nil {
		http.Error(w, "Invalid activity ID", http.StatusBadRequest)
		return
	}

	var updateData struct {
		Status         string     `json:"status"`
		FileSize       *int64     `json:"file_size,omitempty"`
		ProcessingTime *int       `json:"processing_time,omitempty"`
		ErrorMessage   string     `json:"error_message,omitempty"`
		CompletedAt    *time.Time `json:"completed_at,omitempty"`
		ExpiresAt      *time.Time `json:"expires_at,omitempty"`
	}

	if err := json.NewDecoder(r.Body).Decode(&updateData); err != nil {
		http.Error(w, "Invalid request body", http.StatusBadRequest)
		return
	}

	var activity models.ExportActivity
	if err := h.db.First(&activity, activityID).Error; err != nil {
		http.Error(w, "Export activity not found", http.StatusNotFound)
		return
	}

	// Update fields
	if updateData.Status != "" {
		activity.Status = updateData.Status
	}
	if updateData.FileSize != nil {
		activity.FileSize = *updateData.FileSize
	}
	if updateData.ProcessingTime != nil {
		activity.ProcessingTime = *updateData.ProcessingTime
	}
	if updateData.ErrorMessage != "" {
		activity.ErrorMessage = updateData.ErrorMessage
	}
	if updateData.CompletedAt != nil {
		activity.CompletedAt = updateData.CompletedAt
	}
	if updateData.ExpiresAt != nil {
		activity.ExpiresAt = updateData.ExpiresAt
	}

	activity.UpdatedAt = time.Now()

	if err := h.db.Save(&activity).Error; err != nil {
		http.Error(w, "Failed to update export activity", http.StatusInternalServerError)
		return
	}

	// Log the update
	models.LogExportChange(h.db, activity.UserID, activity.ID, "export_updated", map[string]interface{}{
		"status":          activity.Status,
		"file_size":       activity.FileSize,
		"processing_time": activity.ProcessingTime,
	}, r)

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{
		"id":     activity.ID,
		"status": "updated",
	})
}

// IncrementDownloadCount increments the download count for an export
func (h *ExportActivityHandler) IncrementDownloadCount(w http.ResponseWriter, r *http.Request) {
	vars := mux.Vars(r)
	activityID, err := strconv.ParseUint(vars["id"], 10, 32)
	if err != nil {
		http.Error(w, "Invalid activity ID", http.StatusBadRequest)
		return
	}

	var activity models.ExportActivity
	if err := h.db.First(&activity, activityID).Error; err != nil {
		http.Error(w, "Export activity not found", http.StatusNotFound)
		return
	}

	activity.DownloadCount++
	activity.UpdatedAt = time.Now()

	if err := h.db.Save(&activity).Error; err != nil {
		http.Error(w, "Failed to update download count", http.StatusInternalServerError)
		return
	}

	// Log the download
	models.LogExportChange(h.db, activity.UserID, activity.ID, "export_downloaded", map[string]interface{}{
		"download_count": activity.DownloadCount,
	}, r)

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{
		"id":             activity.ID,
		"download_count": activity.DownloadCount,
	})
}

// GetExportActivities retrieves export activities with filtering
func (h *ExportActivityHandler) GetExportActivities(w http.ResponseWriter, r *http.Request) {
	query := h.db.Model(&models.ExportActivity{}).Preload("User").Preload("Building")

	// Apply filters
	if userID := r.URL.Query().Get("user_id"); userID != "" {
		if id, err := strconv.ParseUint(userID, 10, 32); err == nil {
			query = query.Where("user_id = ?", id)
		}
	}

	if buildingID := r.URL.Query().Get("building_id"); buildingID != "" {
		if id, err := strconv.ParseUint(buildingID, 10, 32); err == nil {
			query = query.Where("building_id = ?", id)
		}
	}

	if exportType := r.URL.Query().Get("export_type"); exportType != "" {
		query = query.Where("export_type = ?", exportType)
	}

	if format := r.URL.Query().Get("format"); format != "" {
		query = query.Where("format = ?", format)
	}

	if status := r.URL.Query().Get("status"); status != "" {
		query = query.Where("status = ?", status)
	}

	if startDate := r.URL.Query().Get("start_date"); startDate != "" {
		query = query.Where("created_at >= ?", startDate)
	}

	if endDate := r.URL.Query().Get("end_date"); endDate != "" {
		query = query.Where("created_at <= ?", endDate)
	}

	// Pagination
	page, _ := strconv.Atoi(r.URL.Query().Get("page"))
	if page < 1 {
		page = 1
	}
	limit, _ := strconv.Atoi(r.URL.Query().Get("limit"))
	if limit < 1 || limit > 100 {
		limit = 20
	}
	offset := (page - 1) * limit

	var activities []models.ExportActivity
	var total int64

	// Get total count
	query.Model(&models.ExportActivity{}).Count(&total)

	// Get paginated results
	if err := query.Order("created_at DESC").Offset(offset).Limit(limit).Find(&activities).Error; err != nil {
		http.Error(w, "Failed to retrieve export activities", http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{
		"activities": activities,
		"pagination": map[string]interface{}{
			"page":  page,
			"limit": limit,
			"total": total,
			"pages": (total + int64(limit) - 1) / int64(limit),
		},
	})
}

// GetExportDashboard retrieves export analytics dashboard data
func (h *ExportActivityHandler) GetExportDashboard(w http.ResponseWriter, r *http.Request) {
	var dashboard models.ExportDashboard

	// Get today's stats
	var todayStats struct {
		Exports   int64 `json:"exports"`
		Downloads int64 `json:"downloads"`
		FileSize  int64 `json:"file_size"`
	}
	h.db.Model(&models.ExportActivity{}).
		Select("COUNT(*) as exports, COALESCE(SUM(download_count), 0) as downloads, COALESCE(SUM(file_size), 0) as file_size").
		Where("DATE(created_at) = CURRENT_DATE").
		Scan(&todayStats)

	dashboard.TodayExports = int(todayStats.Exports)
	dashboard.TodayDownloads = int(todayStats.Downloads)
	dashboard.TodayFileSize = todayStats.FileSize

	// Get week's stats
	var weekStats struct {
		Exports   int64 `json:"exports"`
		Downloads int64 `json:"downloads"`
	}
	h.db.Model(&models.ExportActivity{}).
		Select("COUNT(*) as exports, COALESCE(SUM(download_count), 0) as downloads").
		Where("created_at >= CURRENT_DATE - INTERVAL '7 days'").
		Scan(&weekStats)

	dashboard.WeekExports = int(weekStats.Exports)
	dashboard.WeekDownloads = int(weekStats.Downloads)

	// Get month's stats
	var monthStats struct {
		Exports   int64 `json:"exports"`
		Downloads int64 `json:"downloads"`
	}
	h.db.Model(&models.ExportActivity{}).
		Select("COUNT(*) as exports, COALESCE(SUM(download_count), 0) as downloads").
		Where("created_at >= CURRENT_DATE - INTERVAL '30 days'").
		Scan(&monthStats)

	dashboard.MonthExports = int(monthStats.Exports)
	dashboard.MonthDownloads = int(monthStats.Downloads)

	// Get active and failed exports
	var statusStats struct {
		Active int64 `json:"active"`
		Failed int64 `json:"failed"`
	}
	h.db.Model(&models.ExportActivity{}).
		Select("COUNT(CASE WHEN status IN ('requested', 'processing') THEN 1 END) as active, COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed").
		Scan(&statusStats)

	dashboard.ActiveExports = int(statusStats.Active)
	dashboard.FailedExports = int(statusStats.Failed)

	// Get average processing time
	var avgTime struct {
		AvgTime float64 `json:"avg_time"`
	}
	h.db.Model(&models.ExportActivity{}).
		Select("COALESCE(AVG(processing_time), 0) as avg_time").
		Where("processing_time IS NOT NULL").
		Scan(&avgTime)

	dashboard.AvgProcessingTime = int(avgTime.AvgTime)

	// Get top formats
	var formatStats []struct {
		Format string `json:"format"`
		Count  int64  `json:"count"`
	}
	h.db.Model(&models.ExportActivity{}).
		Select("format, COUNT(*) as count").
		Group("format").
		Order("count DESC").
		Limit(5).
		Scan(&formatStats)

	dashboard.TopFormats = make(map[string]int)
	for _, stat := range formatStats {
		dashboard.TopFormats[stat.Format] = int(stat.Count)
	}

	// Get top export types
	var typeStats []struct {
		ExportType string `json:"export_type"`
		Count      int64  `json:"count"`
	}
	h.db.Model(&models.ExportActivity{}).
		Select("export_type, COUNT(*) as count").
		Group("export_type").
		Order("count DESC").
		Limit(5).
		Scan(&typeStats)

	dashboard.TopExportTypes = make(map[string]int)
	for _, stat := range typeStats {
		dashboard.TopExportTypes[stat.ExportType] = int(stat.Count)
	}

	// Get top users
	var userStats []models.UserExportStats
	h.db.Model(&models.ExportActivity{}).
		Select("user_id, COUNT(*) as export_count, COALESCE(SUM(download_count), 0) as download_count, COALESCE(SUM(file_size), 0) as total_file_size").
		Group("user_id").
		Order("export_count DESC").
		Limit(10).
		Scan(&userStats)

	// Get usernames for top users
	for i := range userStats {
		var user models.User
		if err := h.db.First(&user, userStats[i].UserID).Error; err == nil {
			userStats[i].Username = user.Username
		}
	}

	dashboard.TopUsers = userStats

	// Get recent exports
	var recentExports []models.ExportActivity
	h.db.Preload("User").Preload("Building").
		Order("created_at DESC").
		Limit(10).
		Find(&recentExports)

	dashboard.RecentExports = recentExports

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(dashboard)
}

// GetExportAnalytics retrieves export analytics data
func (h *ExportActivityHandler) GetExportAnalytics(w http.ResponseWriter, r *http.Request) {
	period := r.URL.Query().Get("period")
	if period == "" {
		period = "daily"
	}

	startDate := r.URL.Query().Get("start_date")
	endDate := r.URL.Query().Get("end_date")

	query := h.db.Model(&models.ExportAnalytics{}).Where("period = ?", period)

	if startDate != "" {
		query = query.Where("date >= ?", startDate)
	}
	if endDate != "" {
		query = query.Where("date <= ?", endDate)
	}

	var analytics []models.ExportAnalytics
	if err := query.Order("date DESC").Find(&analytics).Error; err != nil {
		http.Error(w, "Failed to retrieve export analytics", http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(analytics)
}

// CreateDataVendorUsage tracks data vendor API usage
func (h *ExportActivityHandler) CreateDataVendorUsage(w http.ResponseWriter, r *http.Request) {
	var usage models.DataVendorUsage
	if err := json.NewDecoder(r.Body).Decode(&usage); err != nil {
		http.Error(w, "Invalid request body", http.StatusBadRequest)
		return
	}

	// Set default values
	usage.CreatedAt = time.Now()
	usage.IPAddress = getClientIP(r)
	usage.UserAgent = r.UserAgent()

	// Get vendor name from API key
	var apiKey models.DataVendorAPIKey
	if err := h.db.First(&apiKey, usage.APIKeyID).Error; err != nil {
		http.Error(w, "Invalid API key", http.StatusBadRequest)
		return
	}
	usage.VendorName = apiKey.VendorName

	// Check rate limit
	var recentUsage int64
	h.db.Model(&models.DataVendorUsage{}).
		Where("api_key_id = ? AND created_at >= NOW() - INTERVAL '1 hour'", usage.APIKeyID).
		Count(&recentUsage)

	if int(recentUsage) >= apiKey.RateLimit {
		usage.RateLimitHit = true
		usage.Status = "rate_limited"
		usage.ErrorCode = "RATE_LIMIT_EXCEEDED"
		usage.ErrorMessage = "Rate limit exceeded"
	}

	// Create the usage record
	if err := h.db.Create(&usage).Error; err != nil {
		http.Error(w, "Failed to create data vendor usage record", http.StatusInternalServerError)
		return
	}

	// Log the usage
	models.LogChange(h.db, 0, "data_vendor_usage", fmt.Sprintf("%d", usage.ID), "api_request", map[string]interface{}{
		"vendor_name":    usage.VendorName,
		"request_type":   usage.RequestType,
		"building_id":    usage.BuildingID,
		"format":         usage.Format,
		"rate_limit_hit": usage.RateLimitHit,
	})

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusCreated)
	json.NewEncoder(w).Encode(map[string]interface{}{
		"id":             usage.ID,
		"status":         usage.Status,
		"rate_limit_hit": usage.RateLimitHit,
	})
}

// GetDataVendorUsage retrieves data vendor usage statistics
func (h *ExportActivityHandler) GetDataVendorUsage(w http.ResponseWriter, r *http.Request) {
	query := h.db.Model(&models.DataVendorUsage{}).Preload("APIKey").Preload("Building")

	// Apply filters
	if apiKeyID := r.URL.Query().Get("api_key_id"); apiKeyID != "" {
		if id, err := strconv.ParseUint(apiKeyID, 10, 32); err == nil {
			query = query.Where("api_key_id = ?", id)
		}
	}

	if vendorName := r.URL.Query().Get("vendor_name"); vendorName != "" {
		query = query.Where("vendor_name = ?", vendorName)
	}

	if requestType := r.URL.Query().Get("request_type"); requestType != "" {
		query = query.Where("request_type = ?", requestType)
	}

	if status := r.URL.Query().Get("status"); status != "" {
		query = query.Where("status = ?", status)
	}

	if startDate := r.URL.Query().Get("start_date"); startDate != "" {
		query = query.Where("created_at >= ?", startDate)
	}

	if endDate := r.URL.Query().Get("end_date"); endDate != "" {
		query = query.Where("created_at <= ?", endDate)
	}

	// Pagination
	page, _ := strconv.Atoi(r.URL.Query().Get("page"))
	if page < 1 {
		page = 1
	}
	limit, _ := strconv.Atoi(r.URL.Query().Get("limit"))
	if limit < 1 || limit > 100 {
		limit = 20
	}
	offset := (page - 1) * limit

	var usage []models.DataVendorUsage
	var total int64

	// Get total count
	query.Model(&models.DataVendorUsage{}).Count(&total)

	// Get paginated results
	if err := query.Order("created_at DESC").Offset(offset).Limit(limit).Find(&usage).Error; err != nil {
		http.Error(w, "Failed to retrieve data vendor usage", http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{
		"usage": usage,
		"pagination": map[string]interface{}{
			"page":  page,
			"limit": limit,
			"total": total,
			"pages": (total + int64(limit) - 1) / int64(limit),
		},
	})
}

// Helper function to get client IP address
func getClientIP(r *http.Request) string {
	// Check for forwarded headers first
	if ip := r.Header.Get("X-Forwarded-For"); ip != "" {
		return ip
	}
	if ip := r.Header.Get("X-Real-IP"); ip != "" {
		return ip
	}
	// Fall back to remote address
	return r.RemoteAddr
}
