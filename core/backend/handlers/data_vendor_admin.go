package handlers

import (
	"arxos/models"
	"arxos/services"
	"crypto/rand"
	"encoding/base64"
	"encoding/json"
	"fmt"
	"net/http"
	"strconv"
	"strings"
	"time"

	"github.com/go-chi/chi/v5"
	"gorm.io/gorm"
)

// DataVendorAdminHandler handles admin operations for data vendor management
type DataVendorAdminHandler struct {
	db                *gorm.DB
	loggingService    *services.LoggingService
	monitoringService *services.MonitoringService
}

// NewDataVendorAdminHandler creates a new data vendor admin handler
func NewDataVendorAdminHandler(db *gorm.DB, loggingService *services.LoggingService, monitoringService *services.MonitoringService) *DataVendorAdminHandler {
	return &DataVendorAdminHandler{
		db:                db,
		loggingService:    loggingService,
		monitoringService: monitoringService,
	}
}

// GetDashboard returns dashboard statistics for data vendor management
func (h *DataVendorAdminHandler) GetDashboard(w http.ResponseWriter, r *http.Request) {
	// Get dashboard metrics
	var metrics struct {
		ActiveKeys     int64                    `json:"active_keys"`
		TodayRequests  int64                    `json:"today_requests"`
		MonthlyRevenue float64                  `json:"monthly_revenue"`
		RateLimitHits  int64                    `json:"rate_limit_hits"`
		UsageTrends    []map[string]interface{} `json:"usage_trends"`
		TopVendors     []map[string]interface{} `json:"top_vendors"`
		RecentActivity []map[string]interface{} `json:"recent_activity"`
	}

	// Count active API keys
	h.db.Model(&models.DataVendorAPIKey{}).Where("is_active = ? AND expires_at > ?", true, time.Now()).Count(&metrics.ActiveKeys)

	// Count today's requests
	today := time.Now().Truncate(24 * time.Hour)
	h.db.Model(&models.APIKeyUsage{}).Where("created_at >= ?", today).Count(&metrics.TodayRequests)

	// Calculate monthly revenue (simplified - could be more complex based on pricing tiers)
	var monthlyUsage int64
	h.db.Model(&models.APIKeyUsage{}).Where("created_at >= ?", time.Now().AddDate(0, -1, 0)).Count(&monthlyUsage)
	metrics.MonthlyRevenue = float64(monthlyUsage) * 0.01 // $0.01 per request

	// Count rate limit hits
	h.db.Model(&models.APIKeyUsage{}).Where("rate_limit_hit = ?", true).Count(&metrics.RateLimitHits)

	// Get usage trends (last 7 days)
	var usageTrends []map[string]interface{}
	h.db.Raw(`
		SELECT DATE(created_at) as date, COUNT(*) as requests
		FROM api_key_usages
		WHERE created_at >= ?
		GROUP BY DATE(created_at)
		ORDER BY date
	`, time.Now().AddDate(0, 0, -7)).Scan(&usageTrends)
	metrics.UsageTrends = usageTrends

	// Get top vendors by request count
	var topVendors []map[string]interface{}
	h.db.Raw(`
		SELECT v.vendor_name, v.access_level, COUNT(u.id) as request_count
		FROM data_vendor_api_keys v
		LEFT JOIN api_key_usages u ON v.id = u.api_key_id
		WHERE v.is_active = true
		GROUP BY v.id, v.vendor_name, v.access_level
		ORDER BY request_count DESC
		LIMIT 10
	`).Scan(&topVendors)
	metrics.TopVendors = topVendors

	// Get recent activity
	var recentActivity []map[string]interface{}
	h.db.Raw(`
		SELECT v.vendor_name, u.endpoint, u.method, u.status, u.created_at
		FROM api_key_usages u
		JOIN data_vendor_api_keys v ON u.api_key_id = v.id
		ORDER BY u.created_at DESC
		LIMIT 20
	`).Scan(&recentActivity)
	metrics.RecentActivity = recentActivity

	respondWithJSON(w, http.StatusOK, metrics)
}

// GetAPIKeys returns all data vendor API keys
func (h *DataVendorAdminHandler) GetAPIKeys(w http.ResponseWriter, r *http.Request) {
	var keys []models.DataVendorAPIKey
	err := h.db.Order("created_at DESC").Find(&keys).Error
	if err != nil {
		respondWithError(w, http.StatusInternalServerError, "Failed to retrieve API keys")
		return
	}

	respondWithJSON(w, http.StatusOK, keys)
}

// CreateAPIKey creates a new data vendor API key
func (h *DataVendorAdminHandler) CreateAPIKey(w http.ResponseWriter, r *http.Request) {
	var request struct {
		VendorName  string    `json:"vendor_name"`
		Email       string    `json:"email"`
		AccessLevel string    `json:"access_level"`
		RateLimit   int       `json:"rate_limit"`
		ExpiresAt   time.Time `json:"expires_at"`
	}

	if err := json.NewDecoder(r.Body).Decode(&request); err != nil {
		respondWithError(w, http.StatusBadRequest, "Invalid request body")
		return
	}

	// Generate API key
	apiKey := generateAPIKey()

	// Create API key record
	key := models.DataVendorAPIKey{
		Key:         apiKey,
		VendorName:  request.VendorName,
		Email:       request.Email,
		AccessLevel: request.AccessLevel,
		RateLimit:   request.RateLimit,
		IsActive:    true,
		ExpiresAt:   request.ExpiresAt,
	}

	err := h.db.Create(&key).Error
	if err != nil {
		respondWithError(w, http.StatusInternalServerError, "Failed to create API key")
		return
	}

	// Log the creation
	h.loggingService.LogSecurityEvent(&services.LogContext{
		IPAddress: r.RemoteAddr,
		Endpoint:  r.URL.Path,
		Method:    r.Method,
	}, "api_key_created", "medium", map[string]interface{}{
		"vendor_name":  request.VendorName,
		"access_level": request.AccessLevel,
		"api_key_id":   key.ID,
	})

	respondWithJSON(w, http.StatusCreated, key)
}

// GetAPIKey returns a specific API key with usage statistics
func (h *DataVendorAdminHandler) GetAPIKey(w http.ResponseWriter, r *http.Request) {
	keyID := chi.URLParam(r, "id")
	if keyID == "" {
		respondWithError(w, http.StatusBadRequest, "API key ID required")
		return
	}

	id, err := strconv.ParseUint(keyID, 10, 32)
	if err != nil {
		respondWithError(w, http.StatusBadRequest, "Invalid API key ID")
		return
	}

	var key models.DataVendorAPIKey
	err = h.db.First(&key, id).Error
	if err != nil {
		respondWithError(w, http.StatusNotFound, "API key not found")
		return
	}

	// Get usage statistics
	var stats struct {
		TotalRequests int64      `json:"total_requests"`
		LastUsed      *time.Time `json:"last_used"`
		RateLimitHits int64      `json:"rate_limit_hits"`
	}

	h.db.Model(&models.APIKeyUsage{}).Where("api_key_id = ?", key.ID).Count(&stats.TotalRequests)
	h.db.Model(&models.APIKeyUsage{}).Where("api_key_id = ?", key.ID).Select("MAX(created_at)").Scan(&stats.LastUsed)
	h.db.Model(&models.APIKeyUsage{}).Where("api_key_id = ? AND rate_limit_hit = ?", key.ID, true).Count(&stats.RateLimitHits)

	// Combine key and stats
	response := map[string]interface{}{
		"key":   key,
		"stats": stats,
	}

	respondWithJSON(w, http.StatusOK, response)
}

// UpdateAPIKeyStatus updates the active status of an API key
func (h *DataVendorAdminHandler) UpdateAPIKeyStatus(w http.ResponseWriter, r *http.Request) {
	keyID := chi.URLParam(r, "id")
	if keyID == "" {
		respondWithError(w, http.StatusBadRequest, "API key ID required")
		return
	}

	id, err := strconv.ParseUint(keyID, 10, 32)
	if err != nil {
		respondWithError(w, http.StatusBadRequest, "Invalid API key ID")
		return
	}

	var request struct {
		IsActive bool `json:"is_active"`
	}

	if err := json.NewDecoder(r.Body).Decode(&request); err != nil {
		respondWithError(w, http.StatusBadRequest, "Invalid request body")
		return
	}

	var key models.DataVendorAPIKey
	err = h.db.First(&key, id).Error
	if err != nil {
		respondWithError(w, http.StatusNotFound, "API key not found")
		return
	}

	// Update status
	err = h.db.Model(&key).Update("is_active", request.IsActive).Error
	if err != nil {
		respondWithError(w, http.StatusInternalServerError, "Failed to update API key status")
		return
	}

	// Log the status change
	h.loggingService.LogSecurityEvent(&services.LogContext{
		IPAddress: r.RemoteAddr,
		Endpoint:  r.URL.Path,
		Method:    r.Method,
	}, "api_key_status_changed", "medium", map[string]interface{}{
		"vendor_name": key.VendorName,
		"api_key_id":  key.ID,
		"new_status":  request.IsActive,
	})

	respondWithJSON(w, http.StatusOK, map[string]interface{}{
		"message":   "API key status updated successfully",
		"is_active": request.IsActive,
	})
}

// GetUsageData returns API usage data with filters
func (h *DataVendorAdminHandler) GetUsageData(w http.ResponseWriter, r *http.Request) {
	// Parse query parameters
	dateRange := r.URL.Query().Get("date_range")
	vendor := r.URL.Query().Get("vendor")
	endpoint := r.URL.Query().Get("endpoint")
	status := r.URL.Query().Get("status")

	// Build query
	query := h.db.Model(&models.APIKeyUsage{}).Joins("JOIN data_vendor_api_keys ON api_key_usages.api_key_id = data_vendor_api_keys.id")

	// Apply filters
	if dateRange != "" {
		days, _ := strconv.Atoi(dateRange)
		if days > 0 {
			query = query.Where("api_key_usages.created_at >= ?", time.Now().AddDate(0, 0, -days))
		}
	}

	if vendor != "" {
		query = query.Where("data_vendor_api_keys.vendor_name = ?", vendor)
	}

	if endpoint != "" {
		query = query.Where("api_key_usages.endpoint = ?", endpoint)
	}

	if status != "" {
		query = query.Where("api_key_usages.status = ?", status)
	}

	// Get usage records
	var usage []models.APIKeyUsage
	err := query.Preload("APIKey").Order("api_key_usages.created_at DESC").Limit(100).Find(&usage).Error
	if err != nil {
		respondWithError(w, http.StatusInternalServerError, "Failed to retrieve usage data")
		return
	}

	// Calculate statistics
	var stats struct {
		TotalRequests   int64   `json:"total_requests"`
		SuccessRate     float64 `json:"success_rate"`
		AvgResponseTime int     `json:"avg_response_time"`
	}

	query.Count(&stats.TotalRequests)

	var successCount int64
	query.Where("api_key_usages.status >= ? AND api_key_usages.status < ?", 200, 300).Count(&successCount)
	if stats.TotalRequests > 0 {
		stats.SuccessRate = float64(successCount) / float64(stats.TotalRequests) * 100
	}

	var avgResponseTime float64
	query.Select("AVG(response_time)").Scan(&avgResponseTime)
	stats.AvgResponseTime = int(avgResponseTime)

	response := map[string]interface{}{
		"usage": usage,
		"stats": stats,
	}

	respondWithJSON(w, http.StatusOK, response)
}

// GetBillingData returns billing and revenue data
func (h *DataVendorAdminHandler) GetBillingData(w http.ResponseWriter, r *http.Request) {
	// Calculate billing metrics
	var metrics struct {
		MonthRevenue        float64                  `json:"month_revenue"`
		TotalVendors        int64                    `json:"total_vendors"`
		AvgRevenuePerVendor float64                  `json:"avg_revenue_per_vendor"`
		ActiveSubscriptions int64                    `json:"active_subscriptions"`
		RevenueTrends       []map[string]interface{} `json:"revenue_trends"`
		Billing             []map[string]interface{} `json:"billing"`
	}

	// Calculate monthly revenue (simplified pricing model)
	var monthlyUsage int64
	h.db.Model(&models.APIKeyUsage{}).Where("created_at >= ?", time.Now().AddDate(0, -1, 0)).Count(&monthlyUsage)
	metrics.MonthRevenue = float64(monthlyUsage) * 0.01 // $0.01 per request

	// Count total vendors
	h.db.Model(&models.DataVendorAPIKey{}).Count(&metrics.TotalVendors)

	// Calculate average revenue per vendor
	if metrics.TotalVendors > 0 {
		metrics.AvgRevenuePerVendor = metrics.MonthRevenue / float64(metrics.TotalVendors)
	}

	// Count active subscriptions
	h.db.Model(&models.DataVendorAPIKey{}).Where("is_active = ? AND expires_at > ?", true, time.Now()).Count(&metrics.ActiveSubscriptions)

	// Get revenue trends (last 12 months)
	var revenueTrends []map[string]interface{}
	h.db.Raw(`
		SELECT
			DATE_FORMAT(created_at, '%Y-%m') as month,
			COUNT(*) * 0.01 as revenue
		FROM api_key_usages
		WHERE created_at >= ?
		GROUP BY DATE_FORMAT(created_at, '%Y-%m')
		ORDER BY month
	`, time.Now().AddDate(0, -12, 0)).Scan(&revenueTrends)
	metrics.RevenueTrends = revenueTrends

	// Get billing data for each vendor
	var billing []map[string]interface{}
	h.db.Raw(`
		SELECT
			v.vendor_name,
			v.access_level as plan,
			CASE
				WHEN v.access_level = 'basic' THEN 50.0
				WHEN v.access_level = 'premium' THEN 150.0
				WHEN v.access_level = 'enterprise' THEN 500.0
				ELSE 0.0
			END as monthly_rate,
			COUNT(u.id) as usage_this_month,
			CASE
				WHEN COUNT(u.id) > 10000 THEN (COUNT(u.id) - 10000) * 0.005
				ELSE 0.0
			END as overage_charges,
			CASE
				WHEN v.access_level = 'basic' THEN 50.0
				WHEN v.access_level = 'premium' THEN 150.0
				WHEN v.access_level = 'enterprise' THEN 500.0
				ELSE 0.0
			END + CASE
				WHEN COUNT(u.id) > 10000 THEN (COUNT(u.id) - 10000) * 0.005
				ELSE 0.0
			END as total_due,
			CASE
				WHEN v.is_active AND v.expires_at > NOW() THEN 'active'
				ELSE 'inactive'
			END as status
		FROM data_vendor_api_keys v
		LEFT JOIN api_key_usages u ON v.id = u.api_key_id
			AND u.created_at >= ?
		GROUP BY v.id, v.vendor_name, v.access_level, v.is_active, v.expires_at
		ORDER BY total_due DESC
	`, time.Now().AddDate(0, -1, 0)).Scan(&billing)
	metrics.Billing = billing

	respondWithJSON(w, http.StatusOK, metrics)
}

// generateAPIKey generates a cryptographically secure API key
func generateAPIKey() string {
	// Generate 32 bytes of cryptographically secure random data
	randomBytes := make([]byte, 32)
	if _, err := rand.Read(randomBytes); err != nil {
		// Fallback to time-based generation if crypto/rand fails
		return "arx_" + strconv.FormatInt(time.Now().UnixNano(), 36) + "_" + strconv.FormatInt(time.Now().Unix(), 36)
	}

	// Convert to base64 and remove padding
	key := base64.URLEncoding.EncodeToString(randomBytes)
	key = strings.TrimRight(key, "=")

	// Add prefix for identification
	return "arx_" + key
}

// RotateAPIKey rotates an existing API key
func (h *DataVendorAdminHandler) RotateAPIKey(w http.ResponseWriter, r *http.Request) {
	id := chi.URLParam(r, "id")
	idInt, err := strconv.Atoi(id)
	if err != nil {
		respondWithError(w, http.StatusBadRequest, "Invalid API key ID")
		return
	}

	// Get the existing API key
	var existingKey models.DataVendorAPIKey
	err = h.db.First(&existingKey, idInt).Error
	if err != nil {
		respondWithError(w, http.StatusNotFound, "API key not found")
		return
	}

	// Generate new API key
	newAPIKey := generateAPIKey()

	// Create new API key record with same settings
	newKey := models.DataVendorAPIKey{
		Key:         newAPIKey,
		VendorName:  existingKey.VendorName,
		Email:       existingKey.Email,
		AccessLevel: existingKey.AccessLevel,
		RateLimit:   existingKey.RateLimit,
		IsActive:    true,
		ExpiresAt:   existingKey.ExpiresAt,
		CreatedAt:   time.Now(),
		UpdatedAt:   time.Now(),
	}

	// Save new key
	err = h.db.Create(&newKey).Error
	if err != nil {
		respondWithError(w, http.StatusInternalServerError, "Failed to create new API key")
		return
	}

	// Deactivate old key (soft delete)
	err = h.db.Model(&existingKey).Update("is_active", false).Error
	if err != nil {
		// Log error but don't fail the request
		fmt.Printf("Failed to deactivate old API key: %v\n", err)
	}

	// Log the API key rotation
	h.loggingService.LogSecurityEvent(&services.LogContext{
		IPAddress: r.RemoteAddr,
		Endpoint:  r.URL.Path,
		Method:    r.Method,
	}, "api_key_rotated", "high", map[string]interface{}{
		"vendor_name":    existingKey.VendorName,
		"old_api_key_id": existingKey.ID,
		"new_api_key_id": newKey.ID,
		"reason":         "security_rotation",
	})

	respondWithJSON(w, http.StatusOK, map[string]interface{}{
		"message":     "API key rotated successfully",
		"new_api_key": newAPIKey,
		"old_key_id":  existingKey.ID,
		"new_key_id":  newKey.ID,
		"expires_at":  newKey.ExpiresAt,
	})
}

// GetAPIKeyRotationHistory returns the rotation history for an API key
func (h *DataVendorAdminHandler) GetAPIKeyRotationHistory(w http.ResponseWriter, r *http.Request) {
	vendorName := r.URL.Query().Get("vendor")
	if vendorName == "" {
		respondWithError(w, http.StatusBadRequest, "Vendor name is required")
		return
	}

	// Get all API keys for the vendor (including inactive ones)
	var keys []models.DataVendorAPIKey
	err := h.db.Where("vendor_name = ?", vendorName).Order("created_at DESC").Find(&keys).Error
	if err != nil {
		respondWithError(w, http.StatusInternalServerError, "Failed to retrieve API key history")
		return
	}

	// Format response
	var history []map[string]interface{}
	for _, key := range keys {
		history = append(history, map[string]interface{}{
			"id":           key.ID,
			"key_preview":  key.Key[:8] + "..." + key.Key[len(key.Key)-4:],
			"is_active":    key.IsActive,
			"created_at":   key.CreatedAt,
			"expires_at":   key.ExpiresAt,
			"access_level": key.AccessLevel,
		})
	}

	respondWithJSON(w, http.StatusOK, map[string]interface{}{
		"vendor_name": vendorName,
		"history":     history,
		"total_keys":  len(history),
	})
}

// BulkRotateAPIKeys rotates API keys for vendors with expired or expiring keys
func (h *DataVendorAdminHandler) BulkRotateAPIKeys(w http.ResponseWriter, r *http.Request) {
	var request struct {
		VendorNames []string `json:"vendor_names"`
		Reason      string   `json:"reason"`
	}

	if err := json.NewDecoder(r.Body).Decode(&request); err != nil {
		respondWithError(w, http.StatusBadRequest, "Invalid request body")
		return
	}

	var results []map[string]interface{}

	for _, vendorName := range request.VendorNames {
		// Get active API keys for the vendor
		var keys []models.DataVendorAPIKey
		err := h.db.Where("vendor_name = ? AND is_active = ?", vendorName, true).Find(&keys).Error
		if err != nil {
			results = append(results, map[string]interface{}{
				"vendor_name": vendorName,
				"status":      "error",
				"message":     "Failed to retrieve API keys",
			})
			continue
		}

		for _, key := range keys {
			// Generate new API key
			newAPIKey := generateAPIKey()

			// Create new API key record
			newKey := models.DataVendorAPIKey{
				Key:         newAPIKey,
				VendorName:  key.VendorName,
				Email:       key.Email,
				AccessLevel: key.AccessLevel,
				RateLimit:   key.RateLimit,
				IsActive:    true,
				ExpiresAt:   key.ExpiresAt,
				CreatedAt:   time.Now(),
				UpdatedAt:   time.Now(),
			}

			// Save new key
			err := h.db.Create(&newKey).Error
			if err != nil {
				results = append(results, map[string]interface{}{
					"vendor_name": vendorName,
					"key_id":      key.ID,
					"status":      "error",
					"message":     "Failed to create new API key",
				})
				continue
			}

			// Deactivate old key
			h.db.Model(&key).Update("is_active", false)

			// Log the rotation
			h.loggingService.LogSecurityEvent(&services.LogContext{
				IPAddress: r.RemoteAddr,
				Endpoint:  r.URL.Path,
				Method:    r.Method,
			}, "api_key_bulk_rotated", "high", map[string]interface{}{
				"vendor_name":    vendorName,
				"old_api_key_id": key.ID,
				"new_api_key_id": newKey.ID,
				"reason":         request.Reason,
			})

			results = append(results, map[string]interface{}{
				"vendor_name": vendorName,
				"old_key_id":  key.ID,
				"new_key_id":  newKey.ID,
				"status":      "success",
				"message":     "API key rotated successfully",
			})
		}
	}

	respondWithJSON(w, http.StatusOK, map[string]interface{}{
		"message": "Bulk API key rotation completed",
		"results": results,
	})
}

// RegisterDataVendorAdminRoutes registers admin routes for data vendor management
func (h *DataVendorAdminHandler) RegisterDataVendorAdminRoutes(r chi.Router) {
	r.Get("/dashboard", h.GetDashboard)
	r.Get("/keys", h.GetAPIKeys)
	r.Post("/keys", h.CreateAPIKey)
	r.Get("/keys/{id}", h.GetAPIKey)
	r.Patch("/keys/{id}/status", h.UpdateAPIKeyStatus)
	r.Get("/usage", h.GetUsageData)
	r.Get("/billing", h.GetBillingData)
	r.Post("/keys/{id}/rotate", h.RotateAPIKey)
	r.Get("/keys/rotation-history", h.GetAPIKeyRotationHistory)
	r.Post("/keys/bulk-rotate", h.BulkRotateAPIKeys)
}
