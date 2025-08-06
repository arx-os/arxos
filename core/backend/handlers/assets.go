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
	"github.com/google/uuid"
	"gorm.io/gorm"
)

// getUserRoleFromToken extracts user role from JWT token
func getUserRoleFromToken(r *http.Request) (string, error) {
	userID, err := getUserIDFromToken(r)
	if err != nil {
		return "", err
	}

	var user models.User
	if err := db.DB.Select("role").Where("id = ?", userID).First(&user).Error; err != nil {
		return "", err
	}

	return user.Role, nil
}

// GetBuildingAssets retrieves assets for a building with optimized queries and eager loading
func GetBuildingAssets(w http.ResponseWriter, r *http.Request) {
	_, err := getUserIDFromToken(r)
	if err != nil {
		http.Error(w, "Unauthorized", http.StatusUnauthorized)
		return
	}

	buildingID := chi.URLParam(r, "buildingId")

	// Parse query parameters
	page, _ := strconv.Atoi(r.URL.Query().Get("page"))
	if page < 1 {
		page = 1
	}
	pageSize, _ := strconv.Atoi(r.URL.Query().Get("page_size"))
	if pageSize < 1 || pageSize > 100 {
		pageSize = 50
	}

	// Parse filters
	system := r.URL.Query().Get("system")
	assetType := r.URL.Query().Get("asset_type")
	status := r.URL.Query().Get("status")
	floorID := r.URL.Query().Get("floor_id")
	roomID := r.URL.Query().Get("room_id")
	search := r.URL.Query().Get("search")
	sortBy := r.URL.Query().Get("sort_by")
	if sortBy == "" {
		sortBy = "created_at"
	}
	sortOrder := r.URL.Query().Get("sort_order")
	if sortOrder == "" {
		sortOrder = "desc"
	}

	// Build cache key based on all filters
	cacheKey := fmt.Sprintf("assets:list:building:%s:page:%d:size:%d:system:%s:type:%s:status:%s:floor:%s:room:%s:search:%s:sort:%s:%s",
		buildingID, page, pageSize, system, assetType, status, floorID, roomID, search, sortBy, sortOrder)

	// Try to get from cache first
	cacheService := GetCacheService()
	if cacheService != nil {
		if cached, err := cacheService.Get(cacheKey); err == nil && cached != nil {
			w.Header().Set("Content-Type", "application/json")
			w.Header().Set("X-Cache", "HIT")
			json.NewEncoder(w).Encode(cached)
			return
		}
	}

	offset := (page - 1) * pageSize

	// Build optimized query with eager loading
	query := db.DB.Model(&models.BuildingAsset{}).
		Preload("Building").
		Preload("Floor").
		Where("building_id = ?", buildingID)

	// Apply filters
	if system != "" {
		query = query.Where("system = ?", system)
	}
	if assetType != "" {
		query = query.Where("asset_type = ?", assetType)
	}
	if status != "" {
		query = query.Where("status = ?", status)
	}
	if floorID != "" {
		query = query.Where("floor_id = ?", floorID)
	}
	if roomID != "" {
		query = query.Where("room_id = ?", roomID)
	}
	if search != "" {
		searchTerm := "%" + strings.ToLower(search) + "%"
		query = query.Where("LOWER(asset_type) LIKE ? OR LOWER(system) LIKE ? OR LOWER(subsystem) LIKE ?",
			searchTerm, searchTerm, searchTerm)
	}

	// Get total count with same filters
	var total int64
	countQuery := db.DB.Model(&models.BuildingAsset{}).Where("building_id = ?", buildingID)
	if system != "" {
		countQuery = countQuery.Where("system = ?", system)
	}
	if assetType != "" {
		countQuery = countQuery.Where("asset_type = ?", assetType)
	}
	if status != "" {
		countQuery = countQuery.Where("status = ?", status)
	}
	if floorID != "" {
		countQuery = countQuery.Where("floor_id = ?", floorID)
	}
	if roomID != "" {
		countQuery = countQuery.Where("room_id = ?", roomID)
	}
	if search != "" {
		searchTerm := "%" + strings.ToLower(search) + "%"
		countQuery = countQuery.Where("LOWER(asset_type) LIKE ? OR LOWER(system) LIKE ? OR LOWER(subsystem) LIKE ?",
			searchTerm, searchTerm, searchTerm)
	}
	countQuery.Count(&total)

	// Apply sorting
	validSortFields := map[string]string{
		"asset_type": "asset_type", "system": "system", "status": "status",
		"created_at": "created_at", "updated_at": "updated_at", "age": "age",
		"estimated_value": "estimated_value", "efficiency_rating": "efficiency_rating",
	}
	if sortField, exists := validSortFields[sortBy]; exists {
		if sortOrder == "desc" {
			query = query.Order(sortField + " DESC")
		} else {
			query = query.Order(sortField + " ASC")
		}
	}

	var assets []models.BuildingAsset
	if err := query.Offset(offset).Limit(pageSize).Find(&assets).Error; err != nil {
		http.Error(w, "Failed to retrieve assets", http.StatusInternalServerError)
		return
	}

	// Get summary statistics
	var summary struct {
		TotalAssets     int64          `json:"total_assets"`
		Systems         map[string]int `json:"systems"`
		AssetTypes      map[string]int `json:"asset_types"`
		TotalValue      float64        `json:"total_value"`
		AverageAge      float64        `json:"average_age"`
		Status          map[string]int `json:"status"`
		EfficiencyStats map[string]int `json:"efficiency_stats"`
	}

	// Get summary with single optimized query
	var stats []struct {
		System           string  `json:"system"`
		AssetType        string  `json:"asset_type"`
		Status           string  `json:"status"`
		EfficiencyRating string  `json:"efficiency_rating"`
		Count            int     `json:"count"`
		TotalValue       float64 `json:"total_value"`
		TotalAge         int     `json:"total_age"`
	}

	summaryQuery := db.DB.Model(&models.BuildingAsset{}).
		Select("system, asset_type, status, efficiency_rating, COUNT(*) as count, COALESCE(SUM(estimated_value), 0) as total_value, COALESCE(SUM(age), 0) as total_age").
		Where("building_id = ?", buildingID)

	// Apply same filters to summary
	if system != "" {
		summaryQuery = summaryQuery.Where("system = ?", system)
	}
	if assetType != "" {
		summaryQuery = summaryQuery.Where("asset_type = ?", assetType)
	}
	if status != "" {
		summaryQuery = summaryQuery.Where("status = ?", status)
	}
	if floorID != "" {
		summaryQuery = summaryQuery.Where("floor_id = ?", floorID)
	}
	if roomID != "" {
		summaryQuery = summaryQuery.Where("room_id = ?", roomID)
	}
	if search != "" {
		searchTerm := "%" + strings.ToLower(search) + "%"
		summaryQuery = summaryQuery.Where("LOWER(asset_type) LIKE ? OR LOWER(system) LIKE ? OR LOWER(subsystem) LIKE ?",
			searchTerm, searchTerm, searchTerm)
	}

	summaryQuery.Group("system, asset_type, status, efficiency_rating").Scan(&stats)

	// Process summary statistics
	summary.Systems = make(map[string]int)
	summary.AssetTypes = make(map[string]int)
	summary.Status = make(map[string]int)
	summary.EfficiencyStats = make(map[string]int)

	var totalAge int
	for _, stat := range stats {
		summary.Systems[stat.System] += stat.Count
		summary.AssetTypes[stat.AssetType] += stat.Count
		summary.Status[stat.Status] += stat.Count
		summary.EfficiencyStats[stat.EfficiencyRating] += stat.Count
		summary.TotalValue += stat.TotalValue
		totalAge += stat.TotalAge
		summary.TotalAssets += int64(stat.Count)
	}

	if summary.TotalAssets > 0 {
		summary.AverageAge = float64(totalAge) / float64(summary.TotalAssets)
	}

	resp := map[string]interface{}{
		"results":     assets,
		"page":        page,
		"page_size":   pageSize,
		"total":       total,
		"total_pages": (total + int64(pageSize) - 1) / int64(pageSize),
		"summary":     summary,
		"filters": map[string]interface{}{
			"system":     system,
			"asset_type": assetType,
			"status":     status,
			"floor_id":   floorID,
			"room_id":    roomID,
			"search":     search,
			"sort_by":    sortBy,
			"sort_order": sortOrder,
		},
	}

	// Cache the result for 5 minutes
	if cacheService != nil {
		cacheService.Set(cacheKey, resp, 5*time.Minute)
		w.Header().Set("X-Cache", "MISS")
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(resp)
}

// GetBuildingAsset retrieves a specific asset with optimized eager loading
func GetBuildingAsset(w http.ResponseWriter, r *http.Request) {
	_, err := getUserIDFromToken(r)
	if err != nil {
		http.Error(w, "Unauthorized", http.StatusUnauthorized)
		return
	}

	assetID := chi.URLParam(r, "assetId")

	// Try to get from cache first
	cacheService := GetCacheService()
	if cacheService != nil {
		cacheKey := fmt.Sprintf("asset:details:%s", assetID)
		if cached, err := cacheService.Get(cacheKey); err == nil && cached != nil {
			w.Header().Set("Content-Type", "application/json")
			w.Header().Set("X-Cache", "HIT")
			json.NewEncoder(w).Encode(cached)
			return
		}
	}

	// Build optimized query with all related data
	var asset models.BuildingAsset
	query := db.DB.Model(&models.BuildingAsset{}).
		Preload("Building").
		Preload("Floor").
		Preload("History", func(db *gorm.DB) *gorm.DB {
			return db.Order("event_date DESC").Limit(10) // Limit history to last 10 events
		}).
		Preload("Maintenance", func(db *gorm.DB) *gorm.DB {
			return db.Order("scheduled_date DESC").Limit(5) // Limit maintenance to last 5 records
		}).
		Preload("Valuations", func(db *gorm.DB) *gorm.DB {
			return db.Order("valuation_date DESC").Limit(5) // Limit valuations to last 5 records
		}).
		Where("id = ?", assetID)

	if err := query.First(&asset).Error; err != nil {
		if err == gorm.ErrRecordNotFound {
			http.Error(w, "Asset not found", http.StatusNotFound)
			return
		}
		http.Error(w, "Failed to retrieve asset", http.StatusInternalServerError)
		return
	}

	// Get related assets in the same system
	var relatedAssets []models.BuildingAsset
	db.DB.Model(&models.BuildingAsset{}).
		Select("id, asset_type, system, status, location_floor, location_room").
		Where("building_id = ? AND system = ? AND id != ?", asset.BuildingID, asset.System, assetID).
		Limit(10).
		Find(&relatedAssets)

	// Build response with all data
	response := map[string]interface{}{
		"asset":          asset,
		"related_assets": relatedAssets,
		"metadata": map[string]interface{}{
			"history_count":     len(asset.History),
			"maintenance_count": len(asset.Maintenance),
			"valuation_count":   len(asset.Valuations),
			"related_count":     len(relatedAssets),
		},
	}

	// Cache the result for 10 minutes
	if cacheService != nil {
		cacheKey := fmt.Sprintf("asset:details:%s", assetID)
		cacheService.Set(cacheKey, response, 10*time.Minute)
		w.Header().Set("X-Cache", "MISS")
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(response)
}

// CreateBuildingAsset creates a new building asset with optimized validation
func CreateBuildingAsset(w http.ResponseWriter, r *http.Request) {
	userID, err := getUserIDFromToken(r)
	if err != nil {
		http.Error(w, "Unauthorized", http.StatusUnauthorized)
		return
	}

	var asset models.BuildingAsset
	if err := json.NewDecoder(r.Body).Decode(&asset); err != nil {
		http.Error(w, "Invalid JSON", http.StatusBadRequest)
		return
	}

	// Validate required fields
	if asset.BuildingID == 0 || asset.AssetType == "" || asset.System == "" {
		http.Error(w, "Building ID, asset type, and system are required", http.StatusBadRequest)
		return
	}

	// Verify building exists and user has access
	var building models.Building
	if err := db.DB.Select("id, owner_id").Where("id = ?", asset.BuildingID).First(&building).Error; err != nil {
		if err == gorm.ErrRecordNotFound {
			http.Error(w, "Building not found", http.StatusNotFound)
			return
		}
		http.Error(w, "DB error", http.StatusInternalServerError)
		return
	}

	// Check if user has access to this building (simplified - in real app, check permissions)
	if building.OwnerID != userID {
		http.Error(w, "Forbidden", http.StatusForbidden)
		return
	}

	// Generate unique ID
	asset.ID = uuid.New().String()
	asset.CreatedAt = time.Now()
	asset.UpdatedAt = time.Now()
	asset.CreatedBy = userID

	// Calculate age if installation date is provided
	if asset.History != nil && len(asset.History) > 0 {
		for _, history := range asset.History {
			if history.EventType == "installation" {
				asset.Age = int(time.Since(history.EventDate).Hours() / 24 / 365)
				break
			}
		}
	}

	// Calculate efficiency rating based on industry benchmarks
	if err := calculateEfficiencyRating(&asset); err != nil {
		http.Error(w, "Failed to calculate efficiency rating", http.StatusInternalServerError)
		return
	}

	// Determine lifecycle stage
	asset.LifecycleStage = determineLifecycleStage(asset.Age, asset.EfficiencyRating)

	// Use transaction for data consistency
	tx := db.DB.Begin()
	if err := tx.Create(&asset).Error; err != nil {
		tx.Rollback()
		http.Error(w, "Failed to create asset", http.StatusInternalServerError)
		return
	}
	tx.Commit()

	// Invalidate asset-related caches
	cacheService := GetCacheService()
	if cacheService != nil {
		// Invalidate asset list cache for this building
		cacheService.InvalidatePattern(fmt.Sprintf("assets:list:building:%d*", asset.BuildingID))
		// Invalidate asset relationships cache
		cacheService.InvalidatePattern(fmt.Sprintf("assets:relationships:building:%d*", asset.BuildingID))
	}

	// Log the asset creation
	if err := models.LogAssetChange(db.DB, userID, asset.ID, "create", nil, &asset, r); err != nil {
		// Log error but don't fail the request
		fmt.Printf("Failed to log asset creation: %v\n", err)
	}

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusCreated)
	json.NewEncoder(w).Encode(asset)
}

// UpdateBuildingAsset updates an existing asset with optimized validation
func UpdateBuildingAsset(w http.ResponseWriter, r *http.Request) {
	userID, err := getUserIDFromToken(r)
	if err != nil {
		http.Error(w, "Unauthorized", http.StatusUnauthorized)
		return
	}

	// Get user role from token
	userRole, err := getUserRoleFromToken(r)
	if err != nil {
		http.Error(w, "Unauthorized", http.StatusUnauthorized)
		return
	}

	assetID := chi.URLParam(r, "assetId")

	// Get the current asset state for audit logging
	var currentAsset models.BuildingAsset
	if err := db.DB.Where("id = ?", assetID).First(&currentAsset).Error; err != nil {
		if err == gorm.ErrRecordNotFound {
			http.Error(w, "Asset not found", http.StatusNotFound)
			return
		}
		http.Error(w, "Failed to retrieve asset", http.StatusInternalServerError)
		return
	}

	// Check access permissions
	if !hasAssetModificationPermission(userID, userRole, &currentAsset) {
		http.Error(w, "Forbidden: insufficient permissions to modify this asset", http.StatusForbidden)
		return
	}

	var asset models.BuildingAsset
	if err := json.NewDecoder(r.Body).Decode(&asset); err != nil {
		http.Error(w, "Invalid JSON", http.StatusBadRequest)
		return
	}

	asset.UpdatedAt = time.Now()

	// Recalculate derived fields
	if err := calculateEfficiencyRating(&asset); err != nil {
		http.Error(w, "Failed to calculate efficiency rating", http.StatusInternalServerError)
		return
	}
	asset.LifecycleStage = determineLifecycleStage(asset.Age, asset.EfficiencyRating)

	// Use transaction for data consistency
	tx := db.DB.Begin()
	if err := tx.Model(&models.BuildingAsset{}).Where("id = ?", assetID).Updates(asset).Error; err != nil {
		tx.Rollback()
		http.Error(w, "Failed to update asset", http.StatusInternalServerError)
		return
	}
	tx.Commit()

	// Invalidate asset-related caches
	cacheService := GetCacheService()
	if cacheService != nil {
		// Invalidate asset details cache
		cacheService.Delete(fmt.Sprintf("asset:details:%s", assetID))
		// Invalidate asset list cache for this building
		cacheService.InvalidatePattern(fmt.Sprintf("assets:list:building:%d*", currentAsset.BuildingID))
		// Invalidate asset relationships cache
		cacheService.InvalidatePattern(fmt.Sprintf("assets:relationships:building:%d*", currentAsset.BuildingID))
	}

	// Log the asset update with before/after comparison
	if err := models.LogAssetChange(db.DB, userID, assetID, "update", &currentAsset, &asset, r); err != nil {
		// Log error but don't fail the request
		fmt.Printf("Failed to log asset update: %v\n", err)
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{"message": "Asset updated successfully"})
}

// BulkCreateAssets creates multiple assets in a single operation
func BulkCreateAssets(w http.ResponseWriter, r *http.Request) {
	userID, err := getUserIDFromToken(r)
	if err != nil {
		http.Error(w, "Unauthorized", http.StatusUnauthorized)
		return
	}

	var request struct {
		BuildingID uint                   `json:"building_id"`
		Assets     []models.BuildingAsset `json:"assets"`
	}

	if err := json.NewDecoder(r.Body).Decode(&request); err != nil {
		http.Error(w, "Invalid JSON", http.StatusBadRequest)
		return
	}

	if len(request.Assets) == 0 {
		http.Error(w, "No assets provided", http.StatusBadRequest)
		return
	}

	if len(request.Assets) > 100 {
		http.Error(w, "Maximum 100 assets allowed per bulk operation", http.StatusBadRequest)
		return
	}

	// Verify building exists and user has access
	var building models.Building
	if err := db.DB.Select("id, owner_id").Where("id = ?", request.BuildingID).First(&building).Error; err != nil {
		if err == gorm.ErrRecordNotFound {
			http.Error(w, "Building not found", http.StatusNotFound)
			return
		}
		http.Error(w, "DB error", http.StatusInternalServerError)
		return
	}

	if building.OwnerID != userID {
		http.Error(w, "Forbidden", http.StatusForbidden)
		return
	}

	// Process assets
	var createdAssets []models.BuildingAsset
	var errors []string

	tx := db.DB.Begin()
	defer func() {
		if r := recover(); r != nil {
			tx.Rollback()
		}
	}()

	for i, asset := range request.Assets {
		// Validate required fields
		if asset.AssetType == "" || asset.System == "" {
			errors = append(errors, fmt.Sprintf("Asset %d: asset type and system are required", i+1))
			continue
		}

		// Set required fields
		asset.ID = uuid.New().String()
		asset.BuildingID = request.BuildingID
		asset.CreatedAt = time.Now()
		asset.UpdatedAt = time.Now()
		asset.CreatedBy = userID

		// Calculate derived fields
		if err := calculateEfficiencyRating(&asset); err != nil {
			errors = append(errors, fmt.Sprintf("Asset %d: failed to calculate efficiency rating", i+1))
			continue
		}
		asset.LifecycleStage = determineLifecycleStage(asset.Age, asset.EfficiencyRating)

		// Create asset
		if err := tx.Create(&asset).Error; err != nil {
			errors = append(errors, fmt.Sprintf("Asset %d: %v", i+1, err))
			continue
		}

		createdAssets = append(createdAssets, asset)
	}

	if len(errors) > 0 {
		tx.Rollback()
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusBadRequest)
		json.NewEncoder(w).Encode(map[string]interface{}{
			"message": "Some assets failed to create",
			"errors":  errors,
			"created": len(createdAssets),
			"failed":  len(errors),
		})
		return
	}

	tx.Commit()

	// Invalidate caches
	cacheService := GetCacheService()
	if cacheService != nil {
		cacheService.InvalidatePattern(fmt.Sprintf("assets:list:building:%d*", request.BuildingID))
		cacheService.InvalidatePattern(fmt.Sprintf("assets:relationships:building:%d*", request.BuildingID))
	}

	// Log bulk creation
	for _, asset := range createdAssets {
		if err := models.LogAssetChange(db.DB, userID, asset.ID, "create", nil, &asset, r); err != nil {
			fmt.Printf("Failed to log asset creation: %v\n", err)
		}
	}

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusCreated)
	json.NewEncoder(w).Encode(map[string]interface{}{
		"message": "Assets created successfully",
		"created": len(createdAssets),
		"assets":  createdAssets,
	})
}

// BulkUpdateAssets updates multiple assets in a single operation
func BulkUpdateAssets(w http.ResponseWriter, r *http.Request) {
	userID, err := getUserIDFromToken(r)
	if err != nil {
		http.Error(w, "Unauthorized", http.StatusUnauthorized)
		return
	}

	var request struct {
		AssetIDs []string               `json:"asset_ids"`
		Updates  map[string]interface{} `json:"updates"`
	}

	if err := json.NewDecoder(r.Body).Decode(&request); err != nil {
		http.Error(w, "Invalid JSON", http.StatusBadRequest)
		return
	}

	if len(request.AssetIDs) == 0 {
		http.Error(w, "No asset IDs provided", http.StatusBadRequest)
		return
	}

	if len(request.AssetIDs) > 50 {
		http.Error(w, "Maximum 50 assets allowed per bulk update", http.StatusBadRequest)
		return
	}

	// Verify all assets exist and user has access
	var assets []models.BuildingAsset
	if err := db.DB.Where("id IN ?", request.AssetIDs).Find(&assets).Error; err != nil {
		http.Error(w, "Failed to retrieve assets", http.StatusInternalServerError)
		return
	}

	if len(assets) != len(request.AssetIDs) {
		http.Error(w, "Some assets not found", http.StatusNotFound)
		return
	}

	// Check permissions for all assets
	for _, asset := range assets {
		if asset.CreatedBy != userID {
			http.Error(w, "Forbidden: insufficient permissions", http.StatusForbidden)
			return
		}
	}

	// Add updated timestamp
	request.Updates["updated_at"] = time.Now()

	// Perform bulk update
	tx := db.DB.Begin()
	if err := tx.Model(&models.BuildingAsset{}).Where("id IN ?", request.AssetIDs).Updates(request.Updates).Error; err != nil {
		tx.Rollback()
		http.Error(w, "Failed to update assets", http.StatusInternalServerError)
		return
	}
	tx.Commit()

	// Invalidate caches for all affected buildings
	cacheService := GetCacheService()
	if cacheService != nil {
		buildingIDs := make(map[uint]bool)
		for _, asset := range assets {
			buildingIDs[asset.BuildingID] = true
		}
		for buildingID := range buildingIDs {
			cacheService.InvalidatePattern(fmt.Sprintf("assets:list:building:%d*", buildingID))
			cacheService.InvalidatePattern(fmt.Sprintf("assets:relationships:building:%d*", buildingID))
		}
		// Invalidate individual asset caches
		for _, assetID := range request.AssetIDs {
			cacheService.Delete(fmt.Sprintf("asset:details:%s", assetID))
		}
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{
		"message": "Assets updated successfully",
		"updated": len(request.AssetIDs),
	})
}

// ExportBuildingInventory exports building assets with optimized queries
func ExportBuildingInventory(w http.ResponseWriter, r *http.Request) {
	_, err := getUserIDFromToken(r)
	if err != nil {
		http.Error(w, "Unauthorized", http.StatusUnauthorized)
		return
	}

	buildingID := chi.URLParam(r, "buildingId")
	format := r.URL.Query().Get("format")
	if format == "" {
		format = "csv"
	}
	includeHistory := r.URL.Query().Get("includeHistory")
	includeMaintenance := r.URL.Query().Get("includeMaintenance")
	includeValuations := r.URL.Query().Get("includeValuations")

	// Build optimized query
	query := db.DB.Model(&models.BuildingAsset{}).Where("building_id = ?", buildingID)

	// Add eager loading based on options
	if includeHistory == "true" {
		query = query.Preload("History", func(db *gorm.DB) *gorm.DB {
			return db.Order("event_date DESC").Limit(5) // Limit to last 5 history records
		})
	}
	if includeMaintenance == "true" {
		query = query.Preload("Maintenance", func(db *gorm.DB) *gorm.DB {
			return db.Order("scheduled_date DESC").Limit(5) // Limit to last 5 maintenance records
		})
	}
	if includeValuations == "true" {
		query = query.Preload("Valuations", func(db *gorm.DB) *gorm.DB {
			return db.Order("valuation_date DESC").Limit(5) // Limit to last 5 valuation records
		})
	}

	query = query.Preload("Building").Preload("Floor")

	var assets []models.BuildingAsset
	if err := query.Find(&assets).Error; err != nil {
		http.Error(w, "Failed to retrieve assets", http.StatusInternalServerError)
		return
	}

	switch format {
	case "csv":
		exportToCSV(w, assets)
	case "json":
		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(assets)
	default:
		http.Error(w, "Unsupported format", http.StatusBadRequest)
	}
}

// Helper functions (reused from existing code)
func calculateEfficiencyRating(asset *models.BuildingAsset) error {
	// Implementation would calculate efficiency based on industry benchmarks
	// For now, set a default value
	asset.EfficiencyRating = "standard"
	return nil
}

func determineLifecycleStage(age int, efficiencyRating string) string {
	if age < 5 {
		return "new"
	} else if age < 15 {
		return "mature"
	} else if age < 25 {
		return "aging"
	} else {
		return "end_of_life"
	}
}

func exportToCSV(w http.ResponseWriter, assets []models.BuildingAsset) {
	w.Header().Set("Content-Type", "text/csv")
	w.Header().Set("Content-Disposition", "attachment; filename=building_assets.csv")

	writer := csv.NewWriter(w)
	defer writer.Flush()

	// Write header
	header := []string{
		"ID", "Asset Type", "System", "Subsystem", "Floor", "Room", "Age",
		"Efficiency Rating", "Lifecycle Stage", "Estimated Value", "Replacement Cost", "Status",
		"Created At", "Updated At",
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
			strconv.Itoa(asset.Age),
			asset.EfficiencyRating,
			asset.LifecycleStage,
			fmt.Sprintf("%.2f", asset.EstimatedValue),
			fmt.Sprintf("%.2f", asset.ReplacementCost),
			asset.Status,
			asset.CreatedAt.Format("2006-01-02 15:04:05"),
			asset.UpdatedAt.Format("2006-01-02 15:04:05"),
		}
		writer.Write(row)
	}
}

func hasAssetModificationPermission(userID uint, userRole string, asset *models.BuildingAsset) bool {
	// Admins can modify any asset
	if userRole == "admin" {
		return true
	}

	// Asset owners can modify their own assets
	if asset.CreatedBy == userID {
		return true
	}

	// Editors can modify assets in buildings they have access to
	if userRole == "editor" {
		// Check if user has access to the building
		var building models.Building
		if err := db.DB.Where("id = ?", asset.BuildingID).First(&building).Error; err == nil {
			// For now, assume editors have access to all buildings
			// In a more complex system, you'd check building-specific permissions
			return true
		}
	}

	// Maintenance users can modify assets they're assigned to maintain
	if userRole == "maintenance" {
		// Check if user is assigned to maintain this asset
		var maintenanceRecord models.AssetMaintenance
		if err := db.DB.Where("asset_id = ? AND assigned_to = ?", asset.ID, userID).First(&maintenanceRecord).Error; err == nil {
			return true
		}
	}

	return false
}
