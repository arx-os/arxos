package handlers

import (
	"arx/db"
	"arx/models"
	"encoding/csv"
	"encoding/json"
	"fmt"
	"net/http"
	"strconv"
	"strings"
	"time"

	"github.com/go-chi/chi/v5"
	"gorm.io/gorm"

	"arx/services"
)

// DataVendorHandler handles data vendor API endpoints
type DataVendorHandler struct {
	db                *gorm.DB
	loggingService    *services.LoggingService
	monitoringService *services.MonitoringService
}

// NewDataVendorHandler creates a new data vendor handler
func NewDataVendorHandler(db *gorm.DB, loggingService *services.LoggingService, monitoringService *services.MonitoringService) *DataVendorHandler {
	return &DataVendorHandler{
		db:                db,
		loggingService:    loggingService,
		monitoringService: monitoringService,
	}
}

// DataVendorAPIKey represents an API key for data vendor access
type DataVendorAPIKey struct {
	ID          uint      `gorm:"primaryKey" json:"id"`
	Key         string    `gorm:"uniqueIndex;not null" json:"key"`
	VendorName  string    `gorm:"not null" json:"vendor_name"`
	Email       string    `gorm:"not null" json:"email"`
	AccessLevel string    `gorm:"default:'basic'" json:"access_level"` // basic, premium, enterprise
	RateLimit   int       `gorm:"default:1000" json:"rate_limit"`      // requests per hour
	IsActive    bool      `gorm:"default:true" json:"is_active"`
	ExpiresAt   time.Time `json:"expires_at"`
	CreatedAt   time.Time `json:"created_at"`
	UpdatedAt   time.Time `json:"updated_at"`
}

// DataVendorRequest represents a data request from a vendor
type DataVendorRequest struct {
	ID          uint      `gorm:"primaryKey" json:"id"`
	APIKeyID    uint      `gorm:"index;not null" json:"api_key_id"`
	RequestType string    `gorm:"not null" json:"request_type"` // building_inventory, asset_details, etc.
	BuildingID  uint      `gorm:"index" json:"building_id"`
	Format      string    `gorm:"default:'json'" json:"format"`
	Filters     string    `gorm:"type:text" json:"filters"`
	IPAddress   string    `json:"ip_address"`
	UserAgent   string    `json:"user_agent"`
	Status      string    `gorm:"default:'completed'" json:"status"`
	CreatedAt   time.Time `json:"created_at"`
}

// GetBuildingInventory provides building asset inventory data
func GetBuildingInventory(w http.ResponseWriter, r *http.Request) {
	// Authenticate API key
	apiKey, err := authenticateAPIKey(r)
	if err != nil {
		http.Error(w, "Invalid API key", http.StatusUnauthorized)
		return
	}

	// Check rate limit
	if err := checkRateLimit(apiKey); err != nil {
		http.Error(w, "Rate limit exceeded", http.StatusTooManyRequests)
		return
	}

	buildingID := chi.URLParam(r, "buildingId")
	format := r.URL.Query().Get("format")
	if format == "" {
		format = "json"
	}
	includeHistory := r.URL.Query().Get("includeHistory")
	includeMaintenance := r.URL.Query().Get("includeMaintenance")
	includeValuations := r.URL.Query().Get("includeValuations")
	system := r.URL.Query().Get("system")
	assetType := r.URL.Query().Get("assetType")

	// Log the request
	logDataRequest(apiKey.ID, "building_inventory", buildingID, format, r)

	// Get building assets
	var assets []models.BuildingAsset
	query := db.DB.Model(&models.BuildingAsset{}).Where("building_id = ?", buildingID)

	if system != "" {
		query = query.Where("system = ?", system)
	}
	if assetType != "" {
		query = query.Where("asset_type = ?", assetType)
	}

	// Include related data based on access level
	if apiKey.AccessLevel == "premium" || apiKey.AccessLevel == "enterprise" {
		if includeHistory == "true" {
			query = query.Preload("History")
		}
		if includeMaintenance == "true" {
			query = query.Preload("Maintenance")
		}
		if includeValuations == "true" {
			query = query.Preload("Valuations")
		}
	}

	if err := query.Preload("Building").Preload("Floor").Find(&assets).Error; err != nil {
		http.Error(w, "Failed to retrieve assets", http.StatusInternalServerError)
		return
	}

	// Filter sensitive data based on access level
	filterSensitiveData(assets, apiKey.AccessLevel)

	// Return in requested format
	switch format {
	case "json":
		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(map[string]interface{}{
			"building_id":  buildingID,
			"total_assets": len(assets),
			"assets":       assets,
			"exported_at":  time.Now(),
			"vendor":       apiKey.VendorName,
		})
	case "csv":
		exportInventoryToCSV(w, assets, buildingID)
	default:
		http.Error(w, "Unsupported format", http.StatusBadRequest)
	}
}

// GetBuildingSummary provides building summary statistics
func GetBuildingSummary(w http.ResponseWriter, r *http.Request) {
	apiKey, err := authenticateAPIKey(r)
	if err != nil {
		http.Error(w, "Invalid API key", http.StatusUnauthorized)
		return
	}

	if err := checkRateLimit(apiKey); err != nil {
		http.Error(w, "Rate limit exceeded", http.StatusTooManyRequests)
		return
	}

	buildingID := chi.URLParam(r, "buildingId")
	logDataRequest(apiKey.ID, "building_summary", buildingID, "json", r)

	var summary struct {
		BuildingID      uint                   `json:"building_id"`
		TotalAssets     int64                  `json:"total_assets"`
		Systems         map[string]int         `json:"systems"`
		AssetTypes      map[string]int         `json:"asset_types"`
		TotalValue      float64                `json:"total_value"`
		AverageAge      float64                `json:"average_age"`
		EfficiencyStats map[string]interface{} `json:"efficiency_stats"`
		LastUpdated     time.Time              `json:"last_updated"`
	}

	// Get building info
	var building models.Building
	if err := db.DB.First(&building, buildingID).Error; err != nil {
		http.Error(w, "Building not found", http.StatusNotFound)
		return
	}

	summary.BuildingID = building.ID
	summary.LastUpdated = time.Now()

	// Get total assets
	db.DB.Model(&models.BuildingAsset{}).Where("building_id = ?", buildingID).Count(&summary.TotalAssets)

	// Get system breakdown
	var systemResults []struct {
		System string
		Count  int
	}
	db.DB.Model(&models.BuildingAsset{}).Select("system, count(*) as count").
		Where("building_id = ?", buildingID).Group("system").Scan(&systemResults)

	summary.Systems = make(map[string]int)
	for _, result := range systemResults {
		summary.Systems[result.System] = result.Count
	}

	// Get asset type breakdown
	var typeResults []struct {
		AssetType string
		Count     int
	}
	db.DB.Model(&models.BuildingAsset{}).Select("asset_type, count(*) as count").
		Where("building_id = ?", buildingID).Group("asset_type").Scan(&typeResults)

	summary.AssetTypes = make(map[string]int)
	for _, result := range typeResults {
		summary.AssetTypes[result.AssetType] = result.Count
	}

	// Get total value (only for premium/enterprise)
	if apiKey.AccessLevel == "premium" || apiKey.AccessLevel == "enterprise" {
		db.DB.Model(&models.BuildingAsset{}).Select("COALESCE(SUM(estimated_value), 0)").
			Where("building_id = ?", buildingID).Scan(&summary.TotalValue)
	}

	// Get average age
	db.DB.Model(&models.BuildingAsset{}).Select("COALESCE(AVG(age), 0)").
		Where("building_id = ?", buildingID).Scan(&summary.AverageAge)

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(summary)
}

// GetAvailableBuildings lists buildings available to the vendor
func GetAvailableBuildings(w http.ResponseWriter, r *http.Request) {
	apiKey, err := authenticateAPIKey(r)
	if err != nil {
		http.Error(w, "Invalid API key", http.StatusUnauthorized)
		return
	}

	if err := checkRateLimit(apiKey); err != nil {
		http.Error(w, "Rate limit exceeded", http.StatusTooManyRequests)
		return
	}

	logDataRequest(apiKey.ID, "available_buildings", "", "json", r)

	var buildings []models.Building
	if err := db.DB.Find(&buildings).Error; err != nil {
		http.Error(w, "Failed to retrieve buildings", http.StatusInternalServerError)
		return
	}

	// Filter sensitive building information
	var publicBuildings []map[string]interface{}
	for _, building := range buildings {
		publicBuildings = append(publicBuildings, map[string]interface{}{
			"id":      building.ID,
			"name":    building.Name,
			"address": building.Address,
		})
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{
		"buildings":   publicBuildings,
		"total":       len(publicBuildings),
		"exported_at": time.Now(),
	})
}

// Helper methods

func authenticateAPIKey(r *http.Request) (*models.DataVendorAPIKey, error) {
	authHeader := r.Header.Get("Authorization")
	if authHeader == "" {
		return nil, fmt.Errorf("no authorization header")
	}

	// Extract API key from "Bearer <key>" format
	parts := strings.Split(authHeader, " ")
	if len(parts) != 2 || parts[0] != "Bearer" {
		return nil, fmt.Errorf("invalid authorization format")
	}

	apiKey := parts[1]

	var key models.DataVendorAPIKey
	if err := db.DB.Where("key = ? AND is_active = ? AND expires_at > ?",
		apiKey, true, time.Now()).First(&key).Error; err != nil {
		return nil, err
	}

	return &key, nil
}

func checkRateLimit(apiKey *models.DataVendorAPIKey) error {
	// Count requests in the last hour
	var count int64
	oneHourAgo := time.Now().Add(-time.Hour)

	db.DB.Model(&models.DataVendorRequest{}).Where("api_key_id = ? AND created_at > ?",
		apiKey.ID, oneHourAgo).Count(&count)

	if int(count) >= apiKey.RateLimit {
		return fmt.Errorf("rate limit exceeded")
	}

	return nil
}

func logDataRequest(apiKeyID uint, requestType, buildingID, format string, r *http.Request) {
	request := models.DataVendorRequest{
		APIKeyID:    apiKeyID,
		RequestType: requestType,
		Format:      format,
		IPAddress:   r.RemoteAddr,
		UserAgent:   r.Header.Get("User-Agent"),
		Status:      "completed",
		CreatedAt:   time.Now(),
	}

	if buildingID != "" {
		if id, err := strconv.ParseUint(buildingID, 10, 32); err == nil {
			request.BuildingID = uint(id)
		}
	}

	db.DB.Create(&request)
}

func filterSensitiveData(assets []models.BuildingAsset, accessLevel string) {
	for i := range assets {
		// Remove sensitive metadata for basic access
		if accessLevel == "basic" {
			assets[i].Metadata = nil
			assets[i].EstimatedValue = 0
			assets[i].ReplacementCost = 0
		}

		// Remove detailed specifications for basic access
		if accessLevel == "basic" {
			assets[i].Specifications = nil
		}
	}
}

func exportInventoryToCSV(w http.ResponseWriter, assets []models.BuildingAsset, buildingID string) {
	w.Header().Set("Content-Type", "text/csv")
	w.Header().Set("Content-Disposition", fmt.Sprintf("attachment; filename=building_%s_assets.csv", buildingID))

	writer := csv.NewWriter(w)
	defer writer.Flush()

	// Write header
	header := []string{
		"Asset ID", "Asset Type", "System", "Subsystem", "Floor", "Room", "Age",
		"Efficiency Rating", "Lifecycle Stage", "Status", "Created At",
	}
	writer.Write(header)

	// Write data
	for _, asset := range assets {
		row := []string{
			asset.ID,
			asset.AssetType,
			asset.System,
			asset.Subsystem,
			asset.Location.Floor,
			asset.Location.Room,
			fmt.Sprintf("%d", asset.Age),
			asset.EfficiencyRating,
			asset.LifecycleStage,
			asset.Status,
			asset.CreatedAt.Format("2006-01-02 15:04:05"),
		}
		writer.Write(row)
	}
}

// validateAPIKey validates the API key and returns vendor information
func (h *DataVendorHandler) validateAPIKey(apiKey string) (*models.DataVendorAPIKey, error) {
	var vendorKey models.DataVendorAPIKey
	err := h.db.Where("key = ? AND is_active = ? AND expires_at > ?", apiKey, true, time.Now()).First(&vendorKey).Error
	if err != nil {
		return nil, err
	}

	// Update last used timestamp
	h.db.Model(&vendorKey).Update("last_used", time.Now())

	return &vendorKey, nil
}

// logVendorRequest logs a vendor API request for auditing and billing
func (h *DataVendorHandler) logVendorRequest(vendorKey *models.DataVendorAPIKey, r *http.Request, statusCode int, duration time.Duration, responseSize int64) {
	// Create log context
	ctx := &services.LogContext{
		RequestID: r.Header.Get("X-Request-ID"),
		IPAddress: r.RemoteAddr,
		Endpoint:  r.URL.Path,
		Method:    r.Method,
		UserAgent: r.UserAgent(),
		Metadata: map[string]interface{}{
			"vendor_name":  vendorKey.VendorName,
			"vendor_email": vendorKey.Email,
			"access_level": vendorKey.AccessLevel,
			"api_key_id":   vendorKey.ID,
		},
	}

	// Log the request
	h.loggingService.LogAPIRequest(ctx, statusCode, duration, responseSize)

	// Record metrics
	h.monitoringService.RecordAPIRequest(r.Method, r.URL.Path, strconv.Itoa(statusCode), "data_vendor", duration)

	// Store API key usage for billing
	usage := models.APIKeyUsage{
		APIKeyID:     vendorKey.ID,
		Endpoint:     r.URL.Path,
		Method:       r.Method,
		Status:       statusCode,
		ResponseTime: int(duration.Milliseconds()),
		IPAddress:    r.RemoteAddr,
		UserAgent:    r.UserAgent(),
		RequestSize:  0, // Could be calculated from request body
		ResponseSize: responseSize,
		CreatedAt:    time.Now(),
	}

	h.db.Create(&usage)
}

// GetAvailableBuildings returns list of buildings available to data vendors
func (h *DataVendorHandler) GetAvailableBuildings(w http.ResponseWriter, r *http.Request) {
	start := time.Now()

	// Validate API key
	apiKey := r.Header.Get("X-API-Key")
	if apiKey == "" {
		respondWithError(w, http.StatusUnauthorized, "API key required")
		return
	}

	vendorKey, err := h.validateAPIKey(apiKey)
	if err != nil {
		respondWithError(w, http.StatusUnauthorized, "Invalid or expired API key")
		return
	}

	// Check rate limiting
	if !h.checkRateLimit(vendorKey, r.URL.Path) {
		h.loggingService.LogSecurityEvent(&services.LogContext{
			IPAddress: r.RemoteAddr,
			Endpoint:  r.URL.Path,
			Method:    r.Method,
		}, "rate_limit_exceeded", "high", map[string]interface{}{
			"vendor_name": vendorKey.VendorName,
			"api_key_id":  vendorKey.ID,
		})
		respondWithError(w, http.StatusTooManyRequests, "Rate limit exceeded")
		return
	}

	// Get query parameters
	limitStr := r.URL.Query().Get("limit")
	offsetStr := r.URL.Query().Get("offset")
	status := r.URL.Query().Get("status")

	limit := 50 // default limit
	if limitStr != "" {
		if l, err := strconv.Atoi(limitStr); err == nil && l > 0 {
			limit = l
		}
	}

	offset := 0
	if offsetStr != "" {
		if o, err := strconv.Atoi(offsetStr); err == nil && o >= 0 {
			offset = o
		}
	}

	// Build query
	query := h.db.Model(&models.Building{}).Where("is_active = ?", true)

	// Apply status filter
	if status != "" {
		query = query.Where("status = ?", status)
	}

	// Apply access level restrictions
	switch vendorKey.AccessLevel {
	case "basic":
		query = query.Where("access_level IN (?)", []string{"public", "basic"})
	case "premium":
		query = query.Where("access_level IN (?)", []string{"public", "basic", "premium"})
	case "enterprise":
		// Enterprise has access to all buildings
	default:
		query = query.Where("access_level = ?", "public")
	}

	// Get total count
	var total int64
	query.Count(&total)

	// Get buildings
	var buildings []models.Building
	err = query.Select("id, name, address, city, state, zip_code, building_type, status, access_level, created_at, updated_at").
		Limit(limit).
		Offset(offset).
		Order("created_at DESC").
		Find(&buildings).Error

	if err != nil {
		h.loggingService.LogAPIError(&services.LogContext{
			IPAddress: r.RemoteAddr,
			Endpoint:  r.URL.Path,
			Method:    r.Method,
		}, err, http.StatusInternalServerError)
		respondWithError(w, http.StatusInternalServerError, "Failed to retrieve buildings")
		return
	}

	// Prepare response
	response := map[string]interface{}{
		"buildings": buildings,
		"pagination": map[string]interface{}{
			"total":    total,
			"limit":    limit,
			"offset":   offset,
			"has_more": offset+limit < int(total),
		},
		"vendor_info": map[string]interface{}{
			"vendor_name":  vendorKey.VendorName,
			"access_level": vendorKey.AccessLevel,
			"rate_limit":   vendorKey.RateLimit,
		},
	}

	// Log the request
	duration := time.Since(start)
	responseSize := int64(len(fmt.Sprintf("%+v", response)))
	h.logVendorRequest(vendorKey, r, http.StatusOK, duration, responseSize)

	respondWithJSON(w, http.StatusOK, response)
}

// GetBuildingInventory returns detailed inventory for a specific building
func (h *DataVendorHandler) GetBuildingInventory(w http.ResponseWriter, r *http.Request) {
	start := time.Now()

	// Validate API key
	apiKey := r.Header.Get("X-API-Key")
	if apiKey == "" {
		respondWithError(w, http.StatusUnauthorized, "API key required")
		return
	}

	vendorKey, err := h.validateAPIKey(apiKey)
	if err != nil {
		respondWithError(w, http.StatusUnauthorized, "Invalid or expired API key")
		return
	}

	// Check rate limiting
	if !h.checkRateLimit(vendorKey, r.URL.Path) {
		h.loggingService.LogSecurityEvent(&services.LogContext{
			IPAddress: r.RemoteAddr,
			Endpoint:  r.URL.Path,
			Method:    r.Method,
		}, "rate_limit_exceeded", "high", map[string]interface{}{
			"vendor_name": vendorKey.VendorName,
			"api_key_id":  vendorKey.ID,
		})
		respondWithError(w, http.StatusTooManyRequests, "Rate limit exceeded")
		return
	}

	// Get building ID from URL
	buildingID := chi.URLParam(r, "buildingId")
	if buildingID == "" {
		respondWithError(w, http.StatusBadRequest, "Building ID required")
		return
	}

	// Check if building exists and vendor has access
	var building models.Building
	err = h.db.Where("id = ? AND is_active = ?", buildingID, true).First(&building).Error
	if err != nil {
		respondWithError(w, http.StatusNotFound, "Building not found")
		return
	}

	// Check access level
	if !h.hasBuildingAccess(vendorKey, &building) {
		respondWithError(w, http.StatusForbidden, "Access denied to this building")
		return
	}

	// Get query parameters
	limitStr := r.URL.Query().Get("limit")
	offsetStr := r.URL.Query().Get("offset")
	category := r.URL.Query().Get("category")
	status := r.URL.Query().Get("status")

	limit := 100 // default limit
	if limitStr != "" {
		if l, err := strconv.Atoi(limitStr); err == nil && l > 0 {
			limit = l
		}
	}

	offset := 0
	if offsetStr != "" {
		if o, err := strconv.Atoi(offsetStr); err == nil && o >= 0 {
			offset = o
		}
	}

	// Build query for assets
	query := h.db.Model(&models.BuildingAsset{}).Where("building_id = ?", buildingID)

	// Apply filters
	if category != "" {
		query = query.Where("category = ?", category)
	}
	if status != "" {
		query = query.Where("status = ?", status)
	}

	// Get total count
	var total int64
	query.Count(&total)

	// Get assets
	var assets []models.BuildingAsset
	err = query.Limit(limit).
		Offset(offset).
		Order("created_at DESC").
		Find(&assets).Error

	if err != nil {
		h.loggingService.LogAPIError(&services.LogContext{
			IPAddress: r.RemoteAddr,
			Endpoint:  r.URL.Path,
			Method:    r.Method,
		}, err, http.StatusInternalServerError)
		respondWithError(w, http.StatusInternalServerError, "Failed to retrieve building inventory")
		return
	}

	// Prepare response
	response := map[string]interface{}{
		"building": map[string]interface{}{
			"id":      building.ID,
			"name":    building.Name,
			"address": building.Address,
		},
		"inventory": assets,
		"pagination": map[string]interface{}{
			"total":    total,
			"limit":    limit,
			"offset":   offset,
			"has_more": offset+limit < int(total),
		},
		"vendor_info": map[string]interface{}{
			"vendor_name":  vendorKey.VendorName,
			"access_level": vendorKey.AccessLevel,
		},
	}

	// Log the request
	duration := time.Since(start)
	responseSize := int64(len(fmt.Sprintf("%+v", response)))
	h.logVendorRequest(vendorKey, r, http.StatusOK, duration, responseSize)

	respondWithJSON(w, http.StatusOK, response)
}

// GetBuildingSummary returns summary statistics for a building
func (h *DataVendorHandler) GetBuildingSummary(w http.ResponseWriter, r *http.Request) {
	start := time.Now()

	// Validate API key
	apiKey := r.Header.Get("X-API-Key")
	if apiKey == "" {
		respondWithError(w, http.StatusUnauthorized, "API key required")
		return
	}

	vendorKey, err := h.validateAPIKey(apiKey)
	if err != nil {
		respondWithError(w, http.StatusUnauthorized, "Invalid or expired API key")
		return
	}

	// Check rate limiting
	if !h.checkRateLimit(vendorKey, r.URL.Path) {
		h.loggingService.LogSecurityEvent(&services.LogContext{
			IPAddress: r.RemoteAddr,
			Endpoint:  r.URL.Path,
			Method:    r.Method,
		}, "rate_limit_exceeded", "high", map[string]interface{}{
			"vendor_name": vendorKey.VendorName,
			"api_key_id":  vendorKey.ID,
		})
		respondWithError(w, http.StatusTooManyRequests, "Rate limit exceeded")
		return
	}

	// Get building ID from URL
	buildingID := chi.URLParam(r, "buildingId")
	if buildingID == "" {
		respondWithError(w, http.StatusBadRequest, "Building ID required")
		return
	}

	// Check if building exists and vendor has access
	var building models.Building
	err = h.db.Where("id = ? AND is_active = ?", buildingID, true).First(&building).Error
	if err != nil {
		respondWithError(w, http.StatusNotFound, "Building not found")
		return
	}

	// Check access level
	if !h.hasBuildingAccess(vendorKey, &building) {
		respondWithError(w, http.StatusForbidden, "Access denied to this building")
		return
	}

	// Get summary statistics
	var summary struct {
		TotalAssets       int64            `json:"total_assets"`
		TotalValue        float64          `json:"total_value"`
		AvgAge            float64          `json:"avg_age"`
		MaintenanceDue    int64            `json:"maintenance_due"`
		CriticalAssets    int64            `json:"critical_assets"`
		CategoryBreakdown map[string]int64 `json:"category_breakdown"`
	}

	// Get total assets and value
	h.db.Model(&models.BuildingAsset{}).
		Where("building_id = ?", buildingID).
		Select("COUNT(*) as total_assets, COALESCE(SUM(current_value), 0) as total_value").
		Scan(&summary)

	// Get average age
	h.db.Model(&models.BuildingAsset{}).
		Where("building_id = ? AND installation_date IS NOT NULL", buildingID).
		Select("AVG(EXTRACT(YEAR FROM AGE(CURRENT_DATE, installation_date))) as avg_age").
		Scan(&summary)

	// Get maintenance due count
	h.db.Model(&models.BuildingAsset{}).
		Where("building_id = ? AND next_maintenance_date <= ?", buildingID, time.Now().AddDate(0, 1, 0)).
		Count(&summary.MaintenanceDue)

	// Get critical assets count
	h.db.Model(&models.BuildingAsset{}).
		Where("building_id = ? AND criticality = ?", buildingID, "critical").
		Count(&summary.CriticalAssets)

	// Get category breakdown
	var categoryStats []struct {
		Category string
		Count    int64
	}
	h.db.Model(&models.BuildingAsset{}).
		Where("building_id = ?", buildingID).
		Select("category, COUNT(*) as count").
		Group("category").
		Scan(&categoryStats)

	summary.CategoryBreakdown = make(map[string]int64)
	for _, stat := range categoryStats {
		summary.CategoryBreakdown[stat.Category] = stat.Count
	}

	// Prepare response
	response := map[string]interface{}{
		"building": map[string]interface{}{
			"id":      building.ID,
			"name":    building.Name,
			"address": building.Address,
		},
		"summary": summary,
		"vendor_info": map[string]interface{}{
			"vendor_name":  vendorKey.VendorName,
			"access_level": vendorKey.AccessLevel,
		},
	}

	// Log the request
	duration := time.Since(start)
	responseSize := int64(len(fmt.Sprintf("%+v", response)))
	h.logVendorRequest(vendorKey, r, http.StatusOK, duration, responseSize)

	respondWithJSON(w, http.StatusOK, response)
}

// GetIndustryBenchmarks returns industry benchmark data
func (h *DataVendorHandler) GetIndustryBenchmarks(w http.ResponseWriter, r *http.Request) {
	start := time.Now()

	// Validate API key
	apiKey := r.Header.Get("X-API-Key")
	if apiKey == "" {
		respondWithError(w, http.StatusUnauthorized, "API key required")
		return
	}

	vendorKey, err := h.validateAPIKey(apiKey)
	if err != nil {
		respondWithError(w, http.StatusUnauthorized, "Invalid or expired API key")
		return
	}

	// Check rate limiting
	if !h.checkRateLimit(vendorKey, r.URL.Path) {
		h.loggingService.LogSecurityEvent(&services.LogContext{
			IPAddress: r.RemoteAddr,
			Endpoint:  r.URL.Path,
			Method:    r.Method,
		}, "rate_limit_exceeded", "high", map[string]interface{}{
			"vendor_name": vendorKey.VendorName,
			"api_key_id":  vendorKey.ID,
		})
		respondWithError(w, http.StatusTooManyRequests, "Rate limit exceeded")
		return
	}

	// Get query parameters
	buildingType := r.URL.Query().Get("building_type")
	region := r.URL.Query().Get("region")

	// Build query for benchmarks
	query := h.db.Model(&models.IndustryBenchmark{})

	if buildingType != "" {
		query = query.Where("building_type = ?", buildingType)
	}
	if region != "" {
		query = query.Where("region = ?", region)
	}

	var benchmarks []models.IndustryBenchmark
	err = query.Order("created_at DESC").Find(&benchmarks).Error

	if err != nil {
		h.loggingService.LogAPIError(&services.LogContext{
			IPAddress: r.RemoteAddr,
			Endpoint:  r.URL.Path,
			Method:    r.Method,
		}, err, http.StatusInternalServerError)
		respondWithError(w, http.StatusInternalServerError, "Failed to retrieve industry benchmarks")
		return
	}

	// Prepare response
	response := map[string]interface{}{
		"benchmarks": benchmarks,
		"filters": map[string]interface{}{
			"building_type": buildingType,
			"region":        region,
		},
		"vendor_info": map[string]interface{}{
			"vendor_name":  vendorKey.VendorName,
			"access_level": vendorKey.AccessLevel,
		},
	}

	// Log the request
	duration := time.Since(start)
	responseSize := int64(len(fmt.Sprintf("%+v", response)))
	h.logVendorRequest(vendorKey, r, http.StatusOK, duration, responseSize)

	respondWithJSON(w, http.StatusOK, response)
}

// checkRateLimit checks if the vendor has exceeded their rate limit
func (h *DataVendorHandler) checkRateLimit(vendorKey *models.DataVendorAPIKey, endpoint string) bool {
	// Count requests in the last minute
	var count int64
	h.db.Model(&models.APIKeyUsage{}).
		Where("api_key_id = ? AND created_at > ?", vendorKey.ID, time.Now().Add(-time.Minute)).
		Count(&count)

	return int(count) < vendorKey.RateLimit
}

// hasBuildingAccess checks if the vendor has access to the building
func (h *DataVendorHandler) hasBuildingAccess(vendorKey *models.DataVendorAPIKey, building *models.Building) bool {
	switch vendorKey.AccessLevel {
	case "basic":
		return building.AccessLevel == "public" || building.AccessLevel == "basic"
	case "premium":
		return building.AccessLevel == "public" || building.AccessLevel == "basic" || building.AccessLevel == "premium"
	case "enterprise":
		return true // Enterprise has access to all buildings
	default:
		return building.AccessLevel == "public"
	}
}

// RegisterDataVendorRoutes registers data vendor API routes
func (h *DataVendorHandler) RegisterDataVendorRoutes(r chi.Router) {
	r.Get("/buildings", h.GetAvailableBuildings)
	r.Get("/buildings/{buildingId}/inventory", h.GetBuildingInventory)
	r.Get("/buildings/{buildingId}/summary", h.GetBuildingSummary)
	r.Get("/industry-benchmarks", h.GetIndustryBenchmarks)
}
