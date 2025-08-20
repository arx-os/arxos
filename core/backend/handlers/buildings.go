package handlers

import (
	"arxos/db"
	"arxos/models"
	"arxos/services"
	"encoding/json"
	"fmt"
	"net/http"
	"strconv"
	"strings"
	"time"

	"github.com/go-chi/chi/v5"
	"gorm.io/gorm"
)

// ListBuildings returns all buildings owned by the current user with optimized queries
func ListBuildings(w http.ResponseWriter, r *http.Request) {
	userID, err := getUserIDFromToken(r)
	if err != nil {
		http.Error(w, "Unauthorized", http.StatusUnauthorized)
		return
	}

	// Parse query parameters with validation
	page, _ := strconv.Atoi(r.URL.Query().Get("page"))
	if page < 1 {
		page = 1
	}
	pageSize, _ := strconv.Atoi(r.URL.Query().Get("page_size"))
	if pageSize < 1 || pageSize > 100 {
		pageSize = 20
	}

	// Parse filters
	status := r.URL.Query().Get("status")
	buildingType := r.URL.Query().Get("building_type")
	search := r.URL.Query().Get("search")
	sortBy := r.URL.Query().Get("sort_by")
	if sortBy == "" {
		sortBy = "created_at"
	}
	sortOrder := r.URL.Query().Get("sort_order")
	if sortOrder == "" {
		sortOrder = "desc"
	}

	// Build cache key with all parameters
	cacheKey := fmt.Sprintf("buildings:list:user:%d:page:%d:size:%d:status:%s:type:%s:search:%s:sort:%s:%s",
		userID, page, pageSize, status, buildingType, search, sortBy, sortOrder)

	// Try to get from cache first
	cacheService := services.GetCacheService()
	if cacheService != nil {
		if cached, err := cacheService.Get(cacheKey); err == nil && cached != nil {
			w.Header().Set("Content-Type", "application/json")
			w.Header().Set("X-Cache", "HIT")
			json.NewEncoder(w).Encode(cached)
			return
		}
	}

	offset := (page - 1) * pageSize

	// Build optimized query with proper joins
	query := db.DB.Model(&models.Building{}).
		Select("buildings.*, COUNT(DISTINCT floors.id) as floor_count, COUNT(DISTINCT building_assets.id) as asset_count").
		Joins("LEFT JOIN floors ON floors.building_id = buildings.id").
		Joins("LEFT JOIN building_assets ON building_assets.building_id = buildings.id").
		Where("buildings.owner_id = ?", userID).
		Group("buildings.id")

	// Apply filters
	if status != "" {
		query = query.Where("buildings.status = ?", status)
	}
	if buildingType != "" {
		query = query.Where("buildings.building_type = ?", buildingType)
	}
	if search != "" {
		searchTerm := "%" + strings.ToLower(search) + "%"
		query = query.Where("LOWER(buildings.name) LIKE ? OR LOWER(buildings.address) LIKE ?", searchTerm, searchTerm)
	}

	// Get total count with same filters
	var total int64
	countQuery := db.DB.Model(&models.Building{}).Where("owner_id = ?", userID)
	if status != "" {
		countQuery = countQuery.Where("status = ?", status)
	}
	if buildingType != "" {
		countQuery = countQuery.Where("building_type = ?", buildingType)
	}
	if search != "" {
		searchTerm := "%" + strings.ToLower(search) + "%"
		countQuery = countQuery.Where("LOWER(name) LIKE ? OR LOWER(address) LIKE ?", searchTerm, searchTerm)
	}
	countQuery.Count(&total)

	// Apply sorting
	validSortFields := map[string]string{
		"name": "buildings.name", "created_at": "buildings.created_at",
		"updated_at": "buildings.updated_at", "status": "buildings.status",
		"building_type": "buildings.building_type", "floor_count": "floor_count",
		"asset_count": "asset_count",
	}
	if sortField, exists := validSortFields[sortBy]; exists {
		if sortOrder == "desc" {
			query = query.Order(sortField + " DESC")
		} else {
			query = query.Order(sortField + " ASC")
		}
	}

	// Execute query with pagination
	var buildings []map[string]interface{}
	query.Offset(offset).Limit(pageSize).Scan(&buildings)

	// Transform results to include proper building objects
	var resultBuildings []models.Building
	for _, b := range buildings {
		building := models.Building{
			ID:           uint(b["id"].(int64)),
			Name:         b["name"].(string),
			Address:      b["address"].(string),
			City:         b["city"].(string),
			State:        b["state"].(string),
			ZipCode:      b["zip_code"].(string),
			BuildingType: b["building_type"].(string),
			Status:       b["status"].(string),
			AccessLevel:  b["access_level"].(string),
			OwnerID:      uint(b["owner_id"].(int64)),
			CreatedAt:    b["created_at"].(time.Time),
			UpdatedAt:    b["updated_at"].(time.Time),
		}
		resultBuildings = append(resultBuildings, building)
	}

	resp := map[string]interface{}{
		"results":     resultBuildings,
		"page":        page,
		"page_size":   pageSize,
		"total":       total,
		"total_pages": (total + int64(pageSize) - 1) / int64(pageSize),
		"filters": map[string]interface{}{
			"status":        status,
			"building_type": buildingType,
			"search":        search,
			"sort_by":       sortBy,
			"sort_order":    sortOrder,
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

// CreateBuilding creates a new building with optimized validation
func CreateBuilding(w http.ResponseWriter, r *http.Request) {
	userID, err := getUserIDFromToken(r)
	if err != nil {
		http.Error(w, "Unauthorized", http.StatusUnauthorized)
		return
	}

	var b models.Building
	if err := json.NewDecoder(r.Body).Decode(&b); err != nil {
		http.Error(w, "Invalid body", http.StatusBadRequest)
		return
	}

	// Validate required fields
	if b.Name == "" {
		http.Error(w, "Building name is required", http.StatusBadRequest)
		return
	}

	// Check for duplicate building names for this user
	var existingCount int64
	db.DB.Model(&models.Building{}).Where("owner_id = ? AND LOWER(name) = LOWER(?)", userID, b.Name).Count(&existingCount)
	if existingCount > 0 {
		http.Error(w, "Building with this name already exists", http.StatusConflict)
		return
	}

	b.OwnerID = userID
	b.CreatedAt = time.Now()
	b.UpdatedAt = time.Now()

	// Use transaction for data consistency
	tx := db.DB.Begin()
	if err := tx.Create(&b).Error; err != nil {
		tx.Rollback()
		http.Error(w, "DB error", http.StatusInternalServerError)
		return
	}
	tx.Commit()

	// Invalidate building list cache for this user
	cacheService := services.GetCacheService()
	if cacheService != nil {
		cacheService.InvalidatePattern(fmt.Sprintf("buildings:list:user:%d:*", userID))
	}

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusCreated)
	json.NewEncoder(w).Encode(b)
}

// GetBuilding returns details for a specific building with eager loading
func GetBuilding(w http.ResponseWriter, r *http.Request) {
	userID, err := getUserIDFromToken(r)
	if err != nil {
		http.Error(w, "Unauthorized", http.StatusUnauthorized)
		return
	}
	idParam := chi.URLParam(r, "id")

	// Try to get from cache first
	cacheService := services.GetCacheService()
	if cacheService != nil {
		cacheKey := fmt.Sprintf("building:details:%s:user:%d", idParam, userID)
		if cached, err := cacheService.Get(cacheKey); err == nil && cached != nil {
			w.Header().Set("Content-Type", "application/json")
			w.Header().Set("X-Cache", "HIT")
			json.NewEncoder(w).Encode(cached)
			return
		}
	}

	// Build optimized query with eager loading
	var b models.Building
	query := db.DB.Model(&models.Building{}).
		Select("buildings.*, COUNT(DISTINCT floors.id) as floor_count, COUNT(DISTINCT building_assets.id) as asset_count").
		Joins("LEFT JOIN floors ON floors.building_id = buildings.id").
		Joins("LEFT JOIN building_assets ON building_assets.building_id = buildings.id").
		Where("buildings.id = ? AND buildings.owner_id = ?", idParam, userID).
		Group("buildings.id")

	if err := query.First(&b).Error; err != nil {
		if err == gorm.ErrRecordNotFound {
			http.Error(w, "Building not found", http.StatusNotFound)
			return
		}
		http.Error(w, "DB error", http.StatusInternalServerError)
		return
	}

	// Load related data efficiently
	var floors []models.Floor
	db.DB.Where("building_id = ?", b.ID).Find(&floors)

	var assetSummary struct {
		TotalAssets int64          `json:"total_assets"`
		Systems     map[string]int `json:"systems"`
		AssetTypes  map[string]int `json:"asset_types"`
		TotalValue  float64        `json:"total_value"`
		Status      map[string]int `json:"status"`
	}

	// Get asset summary with single query
	var assetStats []struct {
		System     string  `json:"system"`
		AssetType  string  `json:"asset_type"`
		Status     string  `json:"status"`
		Count      int     `json:"count"`
		TotalValue float64 `json:"total_value"`
	}

	db.DB.Model(&models.BuildingAsset{}).
		Select("system, asset_type, status, COUNT(*) as count, COALESCE(SUM(estimated_value), 0) as total_value").
		Where("building_id = ?", b.ID).
		Group("system, asset_type, status").
		Scan(&assetStats)

	// Process asset statistics
	assetSummary.Systems = make(map[string]int)
	assetSummary.AssetTypes = make(map[string]int)
	assetSummary.Status = make(map[string]int)
	for _, stat := range assetStats {
		assetSummary.Systems[stat.System] += stat.Count
		assetSummary.AssetTypes[stat.AssetType] += stat.Count
		assetSummary.Status[stat.Status] += stat.Count
		assetSummary.TotalValue += stat.TotalValue
		assetSummary.TotalAssets += int64(stat.Count)
	}

	// Build response with all data
	response := map[string]interface{}{
		"building":      b,
		"floors":        floors,
		"asset_summary": assetSummary,
		"metadata": map[string]interface{}{
			"floor_count":  len(floors),
			"last_updated": b.UpdatedAt,
		},
	}

	// Cache the result for 10 minutes
	if cacheService != nil {
		cacheKey := fmt.Sprintf("building:details:%s:user:%d", idParam, userID)
		cacheService.Set(cacheKey, response, 10*time.Minute)
		w.Header().Set("X-Cache", "MISS")
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(response)
}

// UpdateBuilding updates building metadata with optimized validation
func UpdateBuilding(w http.ResponseWriter, r *http.Request) {
	userID, err := getUserIDFromToken(r)
	if err != nil {
		http.Error(w, "Unauthorized", http.StatusUnauthorized)
		return
	}
	idParam := chi.URLParam(r, "id")

	// Get the current building state
	var currentBuilding models.Building
	if err := db.DB.First(&currentBuilding, idParam).Error; err != nil {
		if err == gorm.ErrRecordNotFound {
			http.Error(w, "Building not found", http.StatusNotFound)
			return
		}
		http.Error(w, "DB error", http.StatusInternalServerError)
		return
	}
	if currentBuilding.OwnerID != userID {
		http.Error(w, "Forbidden", http.StatusForbidden)
		return
	}

	var update models.Building
	if err := json.NewDecoder(r.Body).Decode(&update); err != nil {
		http.Error(w, "Invalid body", http.StatusBadRequest)
		return
	}

	// Validate name uniqueness if changed
	if update.Name != "" && update.Name != currentBuilding.Name {
		var existingCount int64
		db.DB.Model(&models.Building{}).Where("owner_id = ? AND LOWER(name) = LOWER(?) AND id != ?",
			userID, update.Name, idParam).Count(&existingCount)
		if existingCount > 0 {
			http.Error(w, "Building with this name already exists", http.StatusConflict)
			return
		}
	}

	// Update only allowed fields
	updates := map[string]interface{}{
		"name":          update.Name,
		"address":       update.Address,
		"city":          update.City,
		"state":         update.State,
		"zip_code":      update.ZipCode,
		"building_type": update.BuildingType,
		"status":        update.Status,
		"access_level":  update.AccessLevel,
		"updated_at":    time.Now(),
	}

	// Use transaction for data consistency
	tx := db.DB.Begin()
	if err := tx.Model(&models.Building{}).Where("id = ?", idParam).Updates(updates).Error; err != nil {
		tx.Rollback()
		http.Error(w, "DB error", http.StatusInternalServerError)
		return
	}
	tx.Commit()

	// Invalidate building-related caches
	cacheService := services.GetCacheService()
	if cacheService != nil {
		// Invalidate building details cache
		cacheService.Delete(fmt.Sprintf("building:details:%s:user:%d", idParam, userID))
		// Invalidate building list cache for this user
		cacheService.InvalidatePattern(fmt.Sprintf("buildings:list:user:%d:*", userID))
		// Invalidate floor list cache for this building
		cacheService.InvalidatePattern(fmt.Sprintf("floors:list:building:%s:*", idParam))
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{
		"message":     "Building updated successfully",
		"building_id": idParam,
	})
}

// ListFloors returns all floors for a given building with optimized queries
func ListFloors(w http.ResponseWriter, r *http.Request) {
	userID, err := getUserIDFromToken(r)
	if err != nil {
		http.Error(w, "Unauthorized", http.StatusUnauthorized)
		return
	}
	buildingID := chi.URLParam(r, "id")

	// Verify building ownership
	var building models.Building
	if err := db.DB.Select("id, owner_id").Where("id = ?", buildingID).First(&building).Error; err != nil {
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

	// Parse pagination parameters
	page, _ := strconv.Atoi(r.URL.Query().Get("page"))
	if page < 1 {
		page = 1
	}
	pageSize, _ := strconv.Atoi(r.URL.Query().Get("page_size"))
	if pageSize < 1 || pageSize > 100 {
		pageSize = 20
	}

	// Build cache key
	cacheKey := fmt.Sprintf("floors:list:building:%s:user:%d:page:%d:size:%d", buildingID, userID, page, pageSize)

	// Try to get from cache first
	cacheService := services.GetCacheService()
	if cacheService != nil {
		if cached, err := cacheService.Get(cacheKey); err == nil && cached != nil {
			w.Header().Set("Content-Type", "application/json")
			w.Header().Set("X-Cache", "HIT")
			json.NewEncoder(w).Encode(cached)
			return
		}
	}

	offset := (page - 1) * pageSize

	// Build optimized query with asset counts
	query := db.DB.Model(&models.Floor{}).
		Select("floors.*, COUNT(DISTINCT building_assets.id) as asset_count").
		Joins("LEFT JOIN building_assets ON building_assets.floor_id = floors.id").
		Where("floors.building_id = ?", buildingID).
		Group("floors.id")

	var total int64
	db.DB.Model(&models.Floor{}).Where("building_id = ?", buildingID).Count(&total)

	var floors []map[string]interface{}
	query.Order("floors.name ASC").Offset(offset).Limit(pageSize).Scan(&floors)

	// Transform results
	var resultFloors []models.Floor
	for _, f := range floors {
		floor := models.Floor{
			ID:         uint(f["id"].(int64)),
			BuildingID: uint(f["building_id"].(int64)),
			Name:       f["name"].(string),
			SVGPath:    f["svg_path"].(string),
			CreatedAt:  f["created_at"].(time.Time),
			UpdatedAt:  f["updated_at"].(time.Time),
		}
		resultFloors = append(resultFloors, floor)
	}

	resp := map[string]interface{}{
		"results":     resultFloors,
		"page":        page,
		"page_size":   pageSize,
		"total":       total,
		"total_pages": (total + int64(pageSize) - 1) / int64(pageSize),
		"building_id": buildingID,
	}

	// Cache the result for 15 minutes
	if cacheService != nil {
		cacheService.Set(cacheKey, resp, 15*time.Minute)
		w.Header().Set("X-Cache", "MISS")
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(resp)
}

// HTMX: Return <li> list for all buildings by role (owner/shared) with optimized queries
func HTMXListBuildingsSidebar(w http.ResponseWriter, r *http.Request) {
	userID, err := getUserIDFromToken(r)
	if err != nil {
		http.Error(w, "Unauthorized", http.StatusUnauthorized)
		return
	}
	role := r.URL.Query().Get("role")
	var buildings []models.Building

	if role == "owner" {
		// Optimized query for owned buildings
		db.DB.Select("id, name, status, building_type").
			Where("owner_id = ?", userID).
			Order("name ASC").
			Find(&buildings)
	} else if role == "shared" {
		// Optimized query for shared buildings with proper joins
		db.DB.Raw(`
			SELECT DISTINCT b.id, b.name, b.status, b.building_type
			FROM buildings b
			JOIN user_category_permissions ucp ON ucp.project_id = b.project_id
			WHERE ucp.user_id = ? AND b.owner_id != ?
			ORDER BY b.name ASC`, userID, userID).Scan(&buildings)
	} else {
		http.Error(w, "Invalid role", http.StatusBadRequest)
		return
	}

	w.Header().Set("Content-Type", "text/html")
	for _, b := range buildings {
		statusClass := "text-gray-600"
		if b.Status == "active" {
			statusClass = "text-green-600"
		} else if b.Status == "inactive" {
			statusClass = "text-red-600"
		}

		w.Write([]byte(fmt.Sprintf(`<li data-building-id="%d" class="cursor-pointer hover:bg-blue-50 rounded px-2 py-1 flex justify-between items-center">
			<span>%s</span>
			<span class="text-xs %s">%s</span>
		</li>`, b.ID, b.Name, statusClass, b.Status)))
	}
}

// Helper to convert uint to string
func itoa(i uint) string {
	return strconv.FormatUint(uint64(i), 10)
}

// DeleteMarkup deletes a markup by ID with proper validation
func DeleteMarkup(w http.ResponseWriter, r *http.Request) {
	userID, err := getUserIDFromToken(r)
	if err != nil {
		http.Error(w, "Unauthorized", http.StatusUnauthorized)
		return
	}
	markupID := chi.URLParam(r, "id")

	var markup models.Markup
	if err := db.DB.First(&markup, markupID).Error; err != nil {
		if err == gorm.ErrRecordNotFound {
			http.Error(w, "Markup not found", http.StatusNotFound)
			return
		}
		http.Error(w, "DB error", http.StatusInternalServerError)
		return
	}

	if markup.UserID != userID {
		http.Error(w, "Forbidden", http.StatusForbidden)
		return
	}

	if err := db.DB.Delete(&markup).Error; err != nil {
		http.Error(w, "Failed to delete markup", http.StatusInternalServerError)
		return
	}

	w.WriteHeader(http.StatusNoContent)
}
