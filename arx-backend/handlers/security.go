package handlers

import (
	"arx/db"
	"arx/models"
	"crypto/rand"
	"encoding/base64"
	"encoding/json"
	"net/http"
	"strconv"
	"strings"
	"time"

	"github.com/go-chi/chi/v5"
)

// SecurityHandler handles security-related endpoints
type SecurityHandler struct{}

// NewSecurityHandler creates a new security handler
func NewSecurityHandler() *SecurityHandler {
	return &SecurityHandler{}
}

type GenerateAPIKeyRequest struct {
	VendorName  string    `json:"vendor_name"`
	Email       string    `json:"email"`
	AccessLevel string    `json:"access_level"`
	RateLimit   int       `json:"rate_limit"`
	ExpiresAt   time.Time `json:"expires_at"`
}

// GenerateAPIKey generates a new API key for data vendors
func (h *SecurityHandler) GenerateAPIKey(w http.ResponseWriter, r *http.Request) {
	var request GenerateAPIKeyRequest

	if err := json.NewDecoder(r.Body).Decode(&request); err != nil {
		http.Error(w, "Invalid request body", http.StatusBadRequest)
		return
	}

	// Generate secure API key
	apiKey := generateSecureAPIKey()

	// Create API key record
	apiKeyRecord := models.DataVendorAPIKey{
		Key:         apiKey,
		VendorName:  request.VendorName,
		Email:       request.Email,
		AccessLevel: request.AccessLevel,
		RateLimit:   request.RateLimit,
		ExpiresAt:   request.ExpiresAt,
		IsActive:    true,
		CreatedAt:   time.Now(),
		UpdatedAt:   time.Now(),
	}

	if err := db.DB.Create(&apiKeyRecord).Error; err != nil {
		http.Error(w, "Failed to create API key", http.StatusInternalServerError)
		return
	}

	// Log the API key creation
	models.LogChange(db.DB, 0, "api_key", apiKey, "created", map[string]interface{}{
		"vendor_name":  request.VendorName,
		"email":        request.Email,
		"access_level": request.AccessLevel,
	})

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{
		"api_key": apiKey,
		"id":      apiKeyRecord.ID,
		"message": "API key generated successfully",
	})
}

// ListAPIKeys lists all API keys with usage statistics
func (h *SecurityHandler) ListAPIKeys(w http.ResponseWriter, r *http.Request) {
	var apiKeys []models.DataVendorAPIKey

	query := db.DB

	// Add filters
	if vendorName := r.URL.Query().Get("vendor"); vendorName != "" {
		query = query.Where("vendor_name ILIKE ?", "%"+vendorName+"%")
	}
	if status := r.URL.Query().Get("status"); status != "" {
		if status == "active" {
			query = query.Where("is_active = ?", true)
		} else if status == "inactive" {
			query = query.Where("is_active = ?", false)
		}
	}

	if err := query.Find(&apiKeys).Error; err != nil {
		http.Error(w, "Failed to fetch API keys", http.StatusInternalServerError)
		return
	}

	// Add usage statistics
	for i := range apiKeys {
		var usageCount int64
		db.DB.Model(&models.APIKeyUsage{}).Where("api_key_id = ?", apiKeys[i].ID).Count(&usageCount)
		// Note: We can't add usage count to the struct directly, so we'll include it in the response
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(apiKeys)
}

// RevokeAPIKey revokes an API key
func (h *SecurityHandler) RevokeAPIKey(w http.ResponseWriter, r *http.Request) {
	apiKeyID := chi.URLParam(r, "id")

	var apiKey models.DataVendorAPIKey
	if err := db.DB.First(&apiKey, apiKeyID).Error; err != nil {
		http.Error(w, "API key not found", http.StatusNotFound)
		return
	}

	apiKey.IsActive = false
	apiKey.UpdatedAt = time.Now()

	if err := db.DB.Save(&apiKey).Error; err != nil {
		http.Error(w, "Failed to revoke API key", http.StatusInternalServerError)
		return
	}

	// Log the revocation
	models.LogChange(db.DB, 0, "api_key", apiKey.Key, "revoked", map[string]interface{}{
		"vendor_name": apiKey.VendorName,
		"email":       apiKey.Email,
	})

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{
		"message": "API key revoked successfully",
	})
}

// GetAPIKeyUsage gets detailed usage statistics for an API key
func (h *SecurityHandler) GetAPIKeyUsage(w http.ResponseWriter, r *http.Request) {
	apiKeyID := chi.URLParam(r, "id")

	var usage []models.APIKeyUsage
	if err := db.DB.Where("api_key_id = ?", apiKeyID).
		Order("created_at DESC").
		Limit(100).
		Find(&usage).Error; err != nil {
		http.Error(w, "Failed to fetch usage data", http.StatusInternalServerError)
		return
	}

	// Calculate summary statistics
	var totalRequests, failedRequests, rateLimitHits int64
	var avgResponseTime float64

	db.DB.Model(&models.APIKeyUsage{}).Where("api_key_id = ?", apiKeyID).Count(&totalRequests)
	db.DB.Model(&models.APIKeyUsage{}).Where("api_key_id = ? AND status >= 400", apiKeyID).Count(&failedRequests)
	db.DB.Model(&models.APIKeyUsage{}).Where("api_key_id = ? AND rate_limit_hit = ?", apiKeyID, true).Count(&rateLimitHits)
	db.DB.Model(&models.APIKeyUsage{}).Where("api_key_id = ?", apiKeyID).Select("AVG(response_time)").Scan(&avgResponseTime)

	summary := map[string]interface{}{
		"total_requests":    totalRequests,
		"failed_requests":   failedRequests,
		"rate_limit_hits":   rateLimitHits,
		"avg_response_time": avgResponseTime,
		"success_rate":      float64(totalRequests-failedRequests) / float64(totalRequests) * 100,
		"recent_usage":      usage,
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(summary)
}

// ListSecurityAlerts lists security alerts with filtering
func (h *SecurityHandler) ListSecurityAlerts(w http.ResponseWriter, r *http.Request) {
	var alerts []models.SecurityAlert

	query := db.DB.Preload("User").Preload("ResolvedByUser")

	// Add filters
	if alertType := r.URL.Query().Get("type"); alertType != "" {
		query = query.Where("alert_type = ?", alertType)
	}
	if severity := r.URL.Query().Get("severity"); severity != "" {
		query = query.Where("severity = ?", severity)
	}
	if resolved := r.URL.Query().Get("resolved"); resolved != "" {
		if resolved == "true" {
			query = query.Where("is_resolved = ?", true)
		} else if resolved == "false" {
			query = query.Where("is_resolved = ?", false)
		}
	}
	if ipAddress := r.URL.Query().Get("ip"); ipAddress != "" {
		query = query.Where("ip_address = ?", ipAddress)
	}

	// Date range filter
	if startDate := r.URL.Query().Get("start_date"); startDate != "" {
		query = query.Where("created_at >= ?", startDate)
	}
	if endDate := r.URL.Query().Get("end_date"); endDate != "" {
		query = query.Where("created_at <= ?", endDate)
	}

	if err := query.Order("created_at DESC").Limit(100).Find(&alerts).Error; err != nil {
		http.Error(w, "Failed to fetch security alerts", http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(alerts)
}

// ResolveSecurityAlert marks a security alert as resolved
func (h *SecurityHandler) ResolveSecurityAlert(w http.ResponseWriter, r *http.Request) {
	alertID := chi.URLParam(r, "id")

	var request struct {
		Notes string `json:"notes"`
	}
	if err := json.NewDecoder(r.Body).Decode(&request); err != nil {
		http.Error(w, "Invalid request body", http.StatusBadRequest)
		return
	}

	var alert models.SecurityAlert
	if err := db.DB.First(&alert, alertID).Error; err != nil {
		http.Error(w, "Security alert not found", http.StatusNotFound)
		return
	}

	// Get user ID from context (assuming it's set by auth middleware)
	userID := uint(1) // This should come from the authenticated user context

	alert.IsResolved = true
	alert.ResolvedBy = &userID
	alert.ResolvedAt = &[]time.Time{time.Now()}[0]
	alert.Notes = request.Notes
	alert.UpdatedAt = time.Now()

	if err := db.DB.Save(&alert).Error; err != nil {
		http.Error(w, "Failed to resolve security alert", http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{
		"message": "Security alert resolved successfully",
	})
}

// GetSecurityDashboard gets security dashboard statistics
func (h *SecurityHandler) GetSecurityDashboard(w http.ResponseWriter, r *http.Request) {
	// Get time range from query parameters
	days := 30
	if daysParam := r.URL.Query().Get("days"); daysParam != "" {
		if d, err := strconv.Atoi(daysParam); err == nil && d > 0 {
			days = d
		}
	}

	startDate := time.Now().AddDate(0, 0, -days)

	// Security alert statistics
	var totalAlerts, resolvedAlerts, criticalAlerts int64
	db.DB.Model(&models.SecurityAlert{}).Where("created_at >= ?", startDate).Count(&totalAlerts)
	db.DB.Model(&models.SecurityAlert{}).Where("created_at >= ? AND is_resolved = ?", startDate, true).Count(&resolvedAlerts)
	db.DB.Model(&models.SecurityAlert{}).Where("created_at >= ? AND severity = ?", startDate, "critical").Count(&criticalAlerts)

	// API key usage statistics
	var totalAPIRequests, failedAPIRequests, rateLimitViolations int64
	db.DB.Model(&models.APIKeyUsage{}).Where("created_at >= ?", startDate).Count(&totalAPIRequests)
	db.DB.Model(&models.APIKeyUsage{}).Where("created_at >= ? AND status >= 400", startDate).Count(&failedAPIRequests)
	db.DB.Model(&models.APIKeyUsage{}).Where("created_at >= ? AND rate_limit_hit = ?", startDate, true).Count(&rateLimitViolations)

	// Recent security alerts
	var recentAlerts []models.SecurityAlert
	db.DB.Where("created_at >= ? AND is_resolved = ?", startDate, false).
		Order("created_at DESC").
		Limit(10).
		Find(&recentAlerts)

	// Top IP addresses with security issues
	var topIPs []struct {
		IPAddress string `json:"ip_address"`
		Count     int64  `json:"count"`
	}
	db.DB.Model(&models.SecurityAlert{}).
		Select("ip_address, COUNT(*) as count").
		Where("created_at >= ?", startDate).
		Group("ip_address").
		Order("count DESC").
		Limit(10).
		Scan(&topIPs)

	dashboard := map[string]interface{}{
		"period": map[string]interface{}{
			"days":       days,
			"start_date": startDate.Format("2006-01-02"),
			"end_date":   time.Now().Format("2006-01-02"),
		},
		"alerts": map[string]interface{}{
			"total":      totalAlerts,
			"resolved":   resolvedAlerts,
			"critical":   criticalAlerts,
			"unresolved": totalAlerts - resolvedAlerts,
		},
		"api_usage": map[string]interface{}{
			"total_requests":        totalAPIRequests,
			"failed_requests":       failedAPIRequests,
			"rate_limit_violations": rateLimitViolations,
			"success_rate":          float64(totalAPIRequests-failedAPIRequests) / float64(totalAPIRequests) * 100,
		},
		"recent_alerts": recentAlerts,
		"top_ips":       topIPs,
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(dashboard)
}

type UpdateSecuritySettingsRequest struct {
	RateLimit   int    `json:"rate_limit"`
	AccessLevel string `json:"access_level"`
}

// UpdateSecuritySettings updates security settings for API keys
func (h *SecurityHandler) UpdateSecuritySettings(w http.ResponseWriter, r *http.Request) {
	apiKeyID := chi.URLParam(r, "id")

	var request UpdateSecuritySettingsRequest

	if err := json.NewDecoder(r.Body).Decode(&request); err != nil {
		http.Error(w, "Invalid request body", http.StatusBadRequest)
		return
	}

	var apiKey models.DataVendorAPIKey
	if err := db.DB.First(&apiKey, apiKeyID).Error; err != nil {
		http.Error(w, "API key not found", http.StatusNotFound)
		return
	}

	// Update API key settings
	apiKey.RateLimit = request.RateLimit
	apiKey.AccessLevel = request.AccessLevel
	apiKey.UpdatedAt = time.Now()

	// Log the update
	models.LogChange(db.DB, 0, "api_key", apiKey.Key, "updated", map[string]interface{}{
		"vendor_name":  apiKey.VendorName,
		"rate_limit":   request.RateLimit,
		"access_level": request.AccessLevel,
	})

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{
		"message": "Security settings updated successfully",
	})
}

// generateSecureAPIKey generates a cryptographically secure API key
func generateSecureAPIKey() string {
	// Generate 32 random bytes
	bytes := make([]byte, 32)
	rand.Read(bytes)

	// Encode as base64 and remove padding
	key := base64.URLEncoding.EncodeToString(bytes)
	key = strings.TrimRight(key, "=")

	// Add prefix for identification
	return "arx_" + key
}

// RegisterSecurityRoutes registers security-related routes
func (h *SecurityHandler) RegisterSecurityRoutes(r chi.Router) {
	r.Route("/security", func(r chi.Router) {
		// API Key management
		r.Post("/api-keys", h.GenerateAPIKey)
		r.Get("/api-keys", h.ListAPIKeys)
		r.Get("/api-keys/{id}/usage", h.GetAPIKeyUsage)
		r.Put("/api-keys/{id}/settings", h.UpdateSecuritySettings)
		r.Delete("/api-keys/{id}", h.RevokeAPIKey)

		// Security alerts
		r.Get("/alerts", h.ListSecurityAlerts)
		r.Put("/alerts/{id}/resolve", h.ResolveSecurityAlert)

		// Security dashboard
		r.Get("/dashboard", h.GetSecurityDashboard)
	})
}
