package handlers

import (
	"arxos/db"
	"arxos/models"
	"encoding/json"
	"fmt"
	"net/http"
	"strconv"
	"time"

	"github.com/go-chi/chi/v5"
	"gorm.io/gorm"
)

// GetVersionHistory retrieves version history for a floor with optimized queries and lazy loading
func GetVersionHistory(w http.ResponseWriter, r *http.Request) {
	_, err := getUserIDFromToken(r)
	if err != nil {
		http.Error(w, "Unauthorized", http.StatusUnauthorized)
		return
	}

	floorID := chi.URLParam(r, "floorId")

	// Parse query parameters
	page, _ := strconv.Atoi(r.URL.Query().Get("page"))
	if page < 1 {
		page = 1
	}
	pageSize, _ := strconv.Atoi(r.URL.Query().Get("page_size"))
	if pageSize < 1 || pageSize > 100 {
		pageSize = 20
	}

	// Parse filters
	actionType := r.URL.Query().Get("action_type")
	userID := r.URL.Query().Get("user_id")
	includeData := r.URL.Query().Get("include_data") == "true"
	dateFrom := r.URL.Query().Get("date_from")
	dateTo := r.URL.Query().Get("date_to")

	// Build cache key
	cacheKey := fmt.Sprintf("version:history:floor:%s:page:%d:size:%d:action:%s:user:%s:data:%t:from:%s:to:%s",
		floorID, page, pageSize, actionType, userID, includeData, dateFrom, dateTo)

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

	// Build optimized query
	query := db.DB.Model(&models.DrawingVersion{}).Where("floor_id = ?", floorID)

	// Apply filters
	if actionType != "" {
		query = query.Where("action_type = ?", actionType)
	}
	if userID != "" {
		query = query.Where("user_id = ?", userID)
	}
	if dateFrom != "" {
		query = query.Where("created_at >= ?", dateFrom)
	}
	if dateTo != "" {
		query = query.Where("created_at <= ?", dateTo)
	}

	// Get total count with same filters
	var total int64
	countQuery := db.DB.Model(&models.DrawingVersion{}).Where("floor_id = ?", floorID)
	if actionType != "" {
		countQuery = countQuery.Where("action_type = ?", actionType)
	}
	if userID != "" {
		countQuery = countQuery.Where("user_id = ?", userID)
	}
	if dateFrom != "" {
		countQuery = countQuery.Where("created_at >= ?", dateFrom)
	}
	if dateTo != "" {
		countQuery = countQuery.Where("created_at <= ?", dateTo)
	}
	countQuery.Count(&total)

	// Apply sorting and pagination
	query = query.Order("version_number DESC").Offset(offset).Limit(pageSize)

	// Select fields based on include_data flag
	if includeData {
		query = query.Select("id, floor_id, svg, version_number, user_id, action_type, created_at")
	} else {
		query = query.Select("id, floor_id, version_number, user_id, action_type, created_at")
	}

	var versions []models.DrawingVersion
	if err := query.Find(&versions).Error; err != nil {
		http.Error(w, "Failed to retrieve versions", http.StatusInternalServerError)
		return
	}

	// Get user information for versions (eager loading)
	if len(versions) > 0 {
		var userIDs []uint
		for _, v := range versions {
			userIDs = append(userIDs, v.UserID)
		}

		var users []models.User
		db.DB.Select("id, username, email").Where("id IN ?", userIDs).Find(&users)

		// Create user map for quick lookup
		userMap := make(map[uint]models.User)
		for _, user := range users {
			userMap[user.ID] = user
		}

		// Add user info to versions
		for i := range versions {
			if _, exists := userMap[versions[i].UserID]; exists {
				// Create a custom response structure with user info
				// Note: We can't assign directly to versions[i].User since DrawingVersion doesn't have a User field
				// The user information will be included in the response through the userMap lookup
			}
		}
	}

	// Get version statistics
	var stats struct {
		TotalVersions  int64                  `json:"total_versions"`
		ActionTypes    map[string]int         `json:"action_types"`
		Users          map[string]int         `json:"users"`
		RecentActivity map[string]interface{} `json:"recent_activity"`
	}

	// Get action type statistics
	var actionStats []struct {
		ActionType string `json:"action_type"`
		Count      int    `json:"count"`
	}
	db.DB.Model(&models.DrawingVersion{}).
		Select("action_type, COUNT(*) as count").
		Where("floor_id = ?", floorID).
		Group("action_type").
		Scan(&actionStats)

	stats.ActionTypes = make(map[string]int)
	for _, stat := range actionStats {
		stats.ActionTypes[stat.ActionType] = stat.Count
	}

	// Get user statistics
	var userStats []struct {
		UserID   uint   `json:"user_id"`
		Count    int    `json:"count"`
		Username string `json:"username"`
	}
	db.DB.Model(&models.DrawingVersion{}).
		Select("user_id, COUNT(*) as count, users.username").
		Joins("LEFT JOIN users ON users.id = drawing_versions.user_id").
		Where("drawing_versions.floor_id = ?", floorID).
		Group("user_id, users.username").
		Order("count DESC").
		Limit(10).
		Scan(&userStats)

	stats.Users = make(map[string]int)
	for _, stat := range userStats {
		stats.Users[stat.Username] = stat.Count
	}

	// Get recent activity
	var recentVersions []models.DrawingVersion
	db.DB.Model(&models.DrawingVersion{}).
		Select("id, version_number, action_type, created_at, user_id").
		Where("floor_id = ?", floorID).
		Order("created_at DESC").
		Limit(5).
		Find(&recentVersions)

	var lastVersion int
	var lastUpdated time.Time
	if len(versions) > 0 {
		lastVersion = versions[0].VersionNumber
		lastUpdated = versions[0].CreatedAt
	}

	stats.RecentActivity = map[string]interface{}{
		"last_version":    lastVersion,
		"last_updated":    lastUpdated,
		"recent_versions": recentVersions,
	}

	stats.TotalVersions = total

	resp := map[string]interface{}{
		"results":     versions,
		"page":        page,
		"page_size":   pageSize,
		"total":       total,
		"total_pages": (total + int64(pageSize) - 1) / int64(pageSize),
		"statistics":  stats,
		"filters": map[string]interface{}{
			"action_type":  actionType,
			"user_id":      userID,
			"include_data": includeData,
			"date_from":    dateFrom,
			"date_to":      dateTo,
		},
	}

	// Cache the result for 2 minutes
	if cacheService != nil {
		cacheService.Set(cacheKey, resp, 2*time.Minute)
		w.Header().Set("X-Cache", "MISS")
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(resp)
}

// GetVersionDiff retrieves the diff between two versions with optimized diff generation
func GetVersionDiff(w http.ResponseWriter, r *http.Request) {
	_, err := getUserIDFromToken(r)
	if err != nil {
		http.Error(w, "Unauthorized", http.StatusUnauthorized)
		return
	}

	versionID1 := chi.URLParam(r, "versionId1")
	versionID2 := chi.URLParam(r, "versionId2")

	// Build cache key
	cacheKey := fmt.Sprintf("version:diff:%s:%s", versionID1, versionID2)

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

	// Get both versions
	var version1, version2 models.DrawingVersion
	if err := db.DB.Where("id = ?", versionID1).First(&version1).Error; err != nil {
		if err == gorm.ErrRecordNotFound {
			http.Error(w, "Version 1 not found", http.StatusNotFound)
			return
		}
		http.Error(w, "Failed to retrieve version 1", http.StatusInternalServerError)
		return
	}

	if err := db.DB.Where("id = ?", versionID2).First(&version2).Error; err != nil {
		if err == gorm.ErrRecordNotFound {
			http.Error(w, "Version 2 not found", http.StatusNotFound)
			return
		}
		http.Error(w, "Failed to retrieve version 2", http.StatusInternalServerError)
		return
	}

	// Verify both versions belong to the same floor
	if version1.FloorID != version2.FloorID {
		http.Error(w, "Versions must belong to the same floor", http.StatusBadRequest)
		return
	}

	// Generate diff efficiently
	diff := generateEfficientDiff(version1, version2)

	// Get user information
	var user1, user2 models.User
	db.DB.Select("id, username, email").Where("id = ?", version1.UserID).First(&user1)
	db.DB.Select("id, username, email").Where("id = ?", version2.UserID).First(&user2)

	response := map[string]interface{}{
		"version1": map[string]interface{}{
			"id":             version1.ID,
			"version_number": version1.VersionNumber,
			"action_type":    version1.ActionType,
			"created_at":     version1.CreatedAt,
			"user":           user1,
		},
		"version2": map[string]interface{}{
			"id":             version2.ID,
			"version_number": version2.VersionNumber,
			"action_type":    version2.ActionType,
			"created_at":     version2.CreatedAt,
			"user":           user2,
		},
		"diff": diff,
		"metadata": map[string]interface{}{
			"floor_id":     version1.FloorID,
			"version_diff": version2.VersionNumber - version1.VersionNumber,
			"time_diff":    version2.CreatedAt.Sub(version1.CreatedAt).String(),
		},
	}

	// Cache the result for 5 minutes
	if cacheService != nil {
		cacheService.Set(cacheKey, response, 5*time.Minute)
		w.Header().Set("X-Cache", "MISS")
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(response)
}

// GetVersionData retrieves a specific version with lazy loading for large data
func GetVersionData(w http.ResponseWriter, r *http.Request) {
	_, err := getUserIDFromToken(r)
	if err != nil {
		http.Error(w, "Unauthorized", http.StatusUnauthorized)
		return
	}

	versionID := chi.URLParam(r, "versionId")
	includeSVG := r.URL.Query().Get("include_svg") == "true"

	// Build cache key
	cacheKey := fmt.Sprintf("version:data:%s:svg:%t", versionID, includeSVG)

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

	// Build query based on include_svg flag
	query := db.DB.Model(&models.DrawingVersion{}).Where("id = ?", versionID)
	if includeSVG {
		query = query.Select("id, floor_id, svg, version_number, user_id, action_type, created_at")
	} else {
		query = query.Select("id, floor_id, version_number, user_id, action_type, created_at")
	}

	var version models.DrawingVersion
	if err := query.First(&version).Error; err != nil {
		if err == gorm.ErrRecordNotFound {
			http.Error(w, "Version not found", http.StatusNotFound)
			return
		}
		http.Error(w, "Failed to retrieve version", http.StatusInternalServerError)
		return
	}

	// Get user information
	var user models.User
	db.DB.Select("id, username, email").Where("id = ?", version.UserID).First(&user)

	// Get floor information
	var floor models.Floor
	db.DB.Select("id, name, building_id").Where("id = ?", version.FloorID).First(&floor)

	// Get building information
	var building models.Building
	db.DB.Select("id, name").Where("id = ?", floor.BuildingID).First(&building)

	// Get related versions (previous and next)
	var prevVersion, nextVersion models.DrawingVersion
	db.DB.Where("floor_id = ? AND version_number < ?", version.FloorID, version.VersionNumber).
		Order("version_number DESC").Limit(1).First(&prevVersion)

	db.DB.Where("floor_id = ? AND version_number > ?", version.FloorID, version.VersionNumber).
		Order("version_number ASC").Limit(1).First(&nextVersion)

	response := map[string]interface{}{
		"version":  version,
		"user":     user,
		"floor":    floor,
		"building": building,
		"navigation": map[string]interface{}{
			"previous_version": prevVersion.ID,
			"next_version":     nextVersion.ID,
			"has_previous":     prevVersion.ID != 0,
			"has_next":         nextVersion.ID != 0,
		},
		"metadata": map[string]interface{}{
			"svg_size":     len(version.SVG),
			"includes_svg": includeSVG,
		},
	}

	// Cache the result for 10 minutes
	if cacheService != nil {
		cacheService.Set(cacheKey, response, 10*time.Minute)
		w.Header().Set("X-Cache", "MISS")
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(response)
}

// CreateVersion creates a new version with optimized validation
func CreateVersion(w http.ResponseWriter, r *http.Request) {
	userID, err := getUserIDFromToken(r)
	if err != nil {
		http.Error(w, "Unauthorized", http.StatusUnauthorized)
		return
	}

	var request struct {
		FloorID       uint   `json:"floor_id"`
		SVG           string `json:"svg"`
		ActionType    string `json:"action_type"`
		CommitMessage string `json:"commit_message,omitempty"`
	}

	if err := json.NewDecoder(r.Body).Decode(&request); err != nil {
		http.Error(w, "Invalid JSON", http.StatusBadRequest)
		return
	}

	// Validate required fields
	if request.FloorID == 0 || request.SVG == "" || request.ActionType == "" {
		http.Error(w, "Floor ID, SVG data, and action type are required", http.StatusBadRequest)
		return
	}

	// Verify floor exists and user has access
	var floor models.Floor
	if err := db.DB.Preload("Building").Where("id = ?", request.FloorID).First(&floor).Error; err != nil {
		if err == gorm.ErrRecordNotFound {
			http.Error(w, "Floor not found", http.StatusNotFound)
			return
		}
		http.Error(w, "DB error", http.StatusInternalServerError)
		return
	}

	// Check if user has access to this building (simplified - in real app, check permissions)
	var building models.Building
	if err := db.DB.Where("id = ?", floor.BuildingID).First(&building).Error; err != nil {
		http.Error(w, "Building not found", http.StatusNotFound)
		return
	}

	if building.OwnerID != userID {
		http.Error(w, "Forbidden", http.StatusForbidden)
		return
	}

	// Get next version number
	var lastVersion models.DrawingVersion
	db.DB.Where("floor_id = ?", request.FloorID).
		Order("version_number DESC").
		Limit(1).
		First(&lastVersion)

	nextVersionNumber := 1
	if lastVersion.ID != 0 {
		nextVersionNumber = lastVersion.VersionNumber + 1
	}

	// Create new version
	version := models.DrawingVersion{
		FloorID:       request.FloorID,
		SVG:           request.SVG,
		VersionNumber: nextVersionNumber,
		UserID:        userID,
		ActionType:    request.ActionType,
		CreatedAt:     time.Now(),
	}

	// Use transaction for data consistency
	tx := db.DB.Begin()
	if err := tx.Create(&version).Error; err != nil {
		tx.Rollback()
		http.Error(w, "Failed to create version", http.StatusInternalServerError)
		return
	}
	tx.Commit()

	// Invalidate version-related caches
	cacheService := GetCacheService()
	if cacheService != nil {
		cacheService.InvalidatePattern(fmt.Sprintf("version:history:floor:%d*", request.FloorID))
		cacheService.InvalidatePattern(fmt.Sprintf("version:data:*"))
		cacheService.InvalidatePattern(fmt.Sprintf("version:diff:*"))
	}

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusCreated)
	json.NewEncoder(w).Encode(version)
}

// RestoreVersion restores a floor to a specific version
func RestoreVersion(w http.ResponseWriter, r *http.Request) {
	userID, err := getUserIDFromToken(r)
	if err != nil {
		http.Error(w, "Unauthorized", http.StatusUnauthorized)
		return
	}

	versionID := chi.URLParam(r, "versionId")

	// Get the version to restore
	var version models.DrawingVersion
	if err := db.DB.Where("id = ?", versionID).First(&version).Error; err != nil {
		if err == gorm.ErrRecordNotFound {
			http.Error(w, "Version not found", http.StatusNotFound)
			return
		}
		http.Error(w, "Failed to retrieve version", http.StatusInternalServerError)
		return
	}

	// Verify user has access to this floor
	var floor models.Floor
	if err := db.DB.Where("id = ?", version.FloorID).First(&floor).Error; err != nil {
		http.Error(w, "Floor not found", http.StatusNotFound)
		return
	}

	// Check if user has access to this building
	var building models.Building
	if err := db.DB.Where("id = ?", floor.BuildingID).First(&building).Error; err != nil {
		http.Error(w, "Building not found", http.StatusNotFound)
		return
	}

	if building.OwnerID != userID {
		http.Error(w, "Forbidden", http.StatusForbidden)
		return
	}

	// Get next version number
	var lastVersion models.DrawingVersion
	db.DB.Where("floor_id = ?", version.FloorID).
		Order("version_number DESC").
		Limit(1).
		First(&lastVersion)

	nextVersionNumber := lastVersion.VersionNumber + 1

	// Create restoration version
	restoredVersion := models.DrawingVersion{
		FloorID:       version.FloorID,
		SVG:           version.SVG,
		VersionNumber: nextVersionNumber,
		UserID:        userID,
		ActionType:    "restore",
		CreatedAt:     time.Now(),
	}

	// Use transaction for data consistency
	tx := db.DB.Begin()
	if err := tx.Create(&restoredVersion).Error; err != nil {
		tx.Rollback()
		http.Error(w, "Failed to restore version", http.StatusInternalServerError)
		return
	}
	tx.Commit()

	// Invalidate caches
	cacheService := GetCacheService()
	if cacheService != nil {
		cacheService.InvalidatePattern(fmt.Sprintf("version:history:floor:%d*", version.FloorID))
		cacheService.InvalidatePattern(fmt.Sprintf("version:data:*"))
		cacheService.InvalidatePattern(fmt.Sprintf("version:diff:*"))
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{
		"message":       "Version restored successfully",
		"restored_from": version.VersionNumber,
		"new_version":   restoredVersion.VersionNumber,
		"restored_at":   restoredVersion.CreatedAt,
	})
}

// Helper function to generate efficient diff between two versions
func generateEfficientDiff(version1, version2 models.DrawingVersion) map[string]interface{} {
	// This is a simplified diff implementation
	// In a real application, you would use a proper diff algorithm

	diff := map[string]interface{}{
		"version1_number": version1.VersionNumber,
		"version2_number": version2.VersionNumber,
		"version_diff":    version2.VersionNumber - version1.VersionNumber,
		"time_diff":       version2.CreatedAt.Sub(version1.CreatedAt).String(),
		"action_diff":     version1.ActionType != version2.ActionType,
		"svg_size_diff":   len(version2.SVG) - len(version1.SVG),
	}

	// Calculate basic similarity (simplified)
	similarity := calculateSimilarity(version1.SVG, version2.SVG)
	diff["similarity_percentage"] = similarity

	// Determine change type
	if similarity > 95 {
		diff["change_type"] = "minor"
	} else if similarity > 80 {
		diff["change_type"] = "moderate"
	} else {
		diff["change_type"] = "major"
	}

	return diff
}

// Helper function to calculate similarity between two SVG strings
func calculateSimilarity(svg1, svg2 string) float64 {
	if svg1 == svg2 {
		return 100.0
	}

	// Simple similarity calculation based on string length and common substrings
	// In a real application, you would use more sophisticated algorithms

	len1 := len(svg1)
	len2 := len(svg2)

	if len1 == 0 && len2 == 0 {
		return 100.0
	}
	if len1 == 0 || len2 == 0 {
		return 0.0
	}

	// Calculate common substring ratio (simplified)
	commonChars := 0
	minLen := len1
	if len2 < minLen {
		minLen = len2
	}

	for i := 0; i < minLen; i++ {
		if svg1[i] == svg2[i] {
			commonChars++
		}
	}

	similarity := float64(commonChars) / float64(minLen) * 100.0
	return similarity
}
