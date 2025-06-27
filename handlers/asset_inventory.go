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

	"os"

	"github.com/dgrijalva/jwt-go"
	"github.com/go-chi/chi/v5"
	"github.com/google/uuid"
	"gorm.io/gorm"
)

// CreateBuildingAsset creates a new building asset
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

	if err := db.DB.Create(&asset).Error; err != nil {
		http.Error(w, "Failed to create asset", http.StatusInternalServerError)
		return
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

// GetBuildingAssets retrieves assets for a building with filtering
func GetBuildingAssets(w http.ResponseWriter, r *http.Request) {
	_, err := getUserIDFromToken(r)
	if err != nil {
		http.Error(w, "Unauthorized", http.StatusUnauthorized)
		return
	}

	buildingID := chi.URLParam(r, "buildingId")
	system := r.URL.Query().Get("system")
	assetType := r.URL.Query().Get("assetType")
	status := r.URL.Query().Get("status")
	floorID := r.URL.Query().Get("floorId")
	roomID := r.URL.Query().Get("roomId")

	query := db.DB.Model(&models.BuildingAsset{}).Where("building_id = ?", buildingID)

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

	var assets []models.BuildingAsset
	if err := query.Preload("Building").Preload("Floor").Find(&assets).Error; err != nil {
		http.Error(w, "Failed to retrieve assets", http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(assets)
}

// GetBuildingAsset retrieves a specific asset
func GetBuildingAsset(w http.ResponseWriter, r *http.Request) {
	_, err := getUserIDFromToken(r)
	if err != nil {
		http.Error(w, "Unauthorized", http.StatusUnauthorized)
		return
	}

	assetID := chi.URLParam(r, "assetId")

	var asset models.BuildingAsset
	if err := db.DB.Preload("Building").Preload("Floor").
		Preload("History").Preload("Maintenance").Preload("Valuations").
		Where("id = ?", assetID).First(&asset).Error; err != nil {
		if err == gorm.ErrRecordNotFound {
			http.Error(w, "Asset not found", http.StatusNotFound)
			return
		}
		http.Error(w, "Failed to retrieve asset", http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(asset)
}

// UpdateBuildingAsset updates an existing asset
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

	if err := db.DB.Model(&models.BuildingAsset{}).Where("id = ?", assetID).Updates(asset).Error; err != nil {
		http.Error(w, "Failed to update asset", http.StatusInternalServerError)
		return
	}

	// Log the asset update with before/after comparison
	if err := models.LogAssetChange(db.DB, userID, assetID, "update", &currentAsset, &asset, r); err != nil {
		// Log error but don't fail the request
		fmt.Printf("Failed to log asset update: %v\n", err)
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{"message": "Asset updated successfully"})
}

// DeleteBuildingAsset deletes an asset
func DeleteBuildingAsset(w http.ResponseWriter, r *http.Request) {
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

	// Get the current asset state for audit logging and permission check
	var currentAsset models.BuildingAsset
	if err := db.DB.Where("id = ?", assetID).First(&currentAsset).Error; err != nil {
		if err == gorm.ErrRecordNotFound {
			http.Error(w, "Asset not found", http.StatusNotFound)
			return
		}
		http.Error(w, "Failed to retrieve asset", http.StatusInternalServerError)
		return
	}

	// Check access permissions - only admins and asset owners can delete
	if !hasAssetDeletionPermission(userID, userRole, &currentAsset) {
		http.Error(w, "Forbidden: insufficient permissions to delete this asset", http.StatusForbidden)
		return
	}

	if err := db.DB.Delete(&models.BuildingAsset{}, "id = ?", assetID).Error; err != nil {
		http.Error(w, "Failed to delete asset", http.StatusInternalServerError)
		return
	}

	// Log the asset deletion
	if err := models.LogAssetChange(db.DB, userID, assetID, "delete", &currentAsset, nil, r); err != nil {
		// Log error but don't fail the request
		fmt.Printf("Failed to log asset deletion: %v\n", err)
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{"message": "Asset deleted successfully"})
}

// AddAssetHistory adds a history record to an asset
func AddAssetHistory(w http.ResponseWriter, r *http.Request) {
	userID, err := getUserIDFromToken(r)
	if err != nil {
		http.Error(w, "Unauthorized", http.StatusUnauthorized)
		return
	}

	assetID := chi.URLParam(r, "assetId")

	var history models.AssetHistory
	if err := json.NewDecoder(r.Body).Decode(&history); err != nil {
		http.Error(w, "Invalid JSON", http.StatusBadRequest)
		return
	}

	history.AssetID = assetID
	history.CreatedAt = time.Now()
	history.CreatedBy = userID

	if err := db.DB.Create(&history).Error; err != nil {
		http.Error(w, "Failed to add history", http.StatusInternalServerError)
		return
	}

	// Update asset age if this is an installation event
	if history.EventType == "installation" {
		db.DB.Model(&models.BuildingAsset{}).Where("id = ?", assetID).
			Update("age", int(time.Since(history.EventDate).Hours()/24/365))
	}

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusCreated)
	json.NewEncoder(w).Encode(history)
}

// AddAssetMaintenance adds a maintenance record
func AddAssetMaintenance(w http.ResponseWriter, r *http.Request) {
	userID, err := getUserIDFromToken(r)
	if err != nil {
		http.Error(w, "Unauthorized", http.StatusUnauthorized)
		return
	}

	assetID := chi.URLParam(r, "assetId")

	var maintenance models.AssetMaintenance
	if err := json.NewDecoder(r.Body).Decode(&maintenance); err != nil {
		http.Error(w, "Invalid JSON", http.StatusBadRequest)
		return
	}

	maintenance.AssetID = assetID
	maintenance.CreatedAt = time.Now()
	maintenance.UpdatedAt = time.Now()
	maintenance.CreatedBy = userID

	if err := db.DB.Create(&maintenance).Error; err != nil {
		http.Error(w, "Failed to add maintenance", http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusCreated)
	json.NewEncoder(w).Encode(maintenance)
}

// AddAssetValuation adds a valuation record
func AddAssetValuation(w http.ResponseWriter, r *http.Request) {
	userID, err := getUserIDFromToken(r)
	if err != nil {
		http.Error(w, "Unauthorized", http.StatusUnauthorized)
		return
	}

	assetID := chi.URLParam(r, "assetId")

	var valuation models.AssetValuation
	if err := json.NewDecoder(r.Body).Decode(&valuation); err != nil {
		http.Error(w, "Invalid JSON", http.StatusBadRequest)
		return
	}

	valuation.AssetID = assetID
	valuation.CreatedAt = time.Now()
	valuation.CreatedBy = userID

	if err := db.DB.Create(&valuation).Error; err != nil {
		http.Error(w, "Failed to add valuation", http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusCreated)
	json.NewEncoder(w).Encode(valuation)
}

// ExportBuildingInventory exports building assets in various formats
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

	var assets []models.BuildingAsset
	query := db.DB.Model(&models.BuildingAsset{}).Where("building_id = ?", buildingID)

	if includeHistory == "true" {
		query = query.Preload("History")
	}
	if includeMaintenance == "true" {
		query = query.Preload("Maintenance")
	}
	if includeValuations == "true" {
		query = query.Preload("Valuations")
	}

	if err := query.Preload("Building").Preload("Floor").Find(&assets).Error; err != nil {
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

// GetBuildingInventorySummary provides summary statistics
func GetBuildingInventorySummary(w http.ResponseWriter, r *http.Request) {
	_, err := getUserIDFromToken(r)
	if err != nil {
		http.Error(w, "Unauthorized", http.StatusUnauthorized)
		return
	}

	buildingID := chi.URLParam(r, "buildingId")

	var summary struct {
		TotalAssets     int64                  `json:"total_assets"`
		Systems         map[string]int         `json:"systems"`
		AssetTypes      map[string]int         `json:"asset_types"`
		TotalValue      float64                `json:"total_value"`
		AverageAge      float64                `json:"average_age"`
		EfficiencyStats map[string]interface{} `json:"efficiency_stats"`
	}

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

	// Get total value
	db.DB.Model(&models.BuildingAsset{}).Select("COALESCE(SUM(estimated_value), 0)").
		Where("building_id = ?", buildingID).Scan(&summary.TotalValue)

	// Get average age
	db.DB.Model(&models.BuildingAsset{}).Select("COALESCE(AVG(age), 0)").
		Where("building_id = ?", buildingID).Scan(&summary.AverageAge)

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(summary)
}

// GetIndustryBenchmarks retrieves industry benchmarks
func GetIndustryBenchmarks(w http.ResponseWriter, r *http.Request) {
	_, err := getUserIDFromToken(r)
	if err != nil {
		http.Error(w, "Unauthorized", http.StatusUnauthorized)
		return
	}

	equipmentType := r.URL.Query().Get("equipmentType")
	system := r.URL.Query().Get("system")
	metric := r.URL.Query().Get("metric")

	query := db.DB.Model(&models.IndustryBenchmark{})

	if equipmentType != "" {
		query = query.Where("equipment_type = ?", equipmentType)
	}
	if system != "" {
		query = query.Where("system = ?", system)
	}
	if metric != "" {
		query = query.Where("metric = ?", metric)
	}

	var benchmarks []models.IndustryBenchmark
	if err := query.Find(&benchmarks).Error; err != nil {
		http.Error(w, "Failed to retrieve benchmarks", http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(benchmarks)
}

// Helper methods

func calculateEfficiencyRating(asset *models.BuildingAsset) error {
	// Get industry benchmark for this equipment type
	var benchmark models.IndustryBenchmark
	err := db.DB.Where("equipment_type = ? AND system = ? AND metric = ?",
		asset.AssetType, asset.System, "efficiency").First(&benchmark).Error

	if err == nil {
		// Calculate efficiency based on specifications and benchmark
		if asset.Specifications != nil {
			var specs map[string]interface{}
			if err := json.Unmarshal(asset.Specifications, &specs); err == nil {
				if efficiency, ok := specs["efficiency"].(float64); ok {
					percentage := (efficiency / benchmark.Value) * 100
					if percentage > 100 {
						percentage = 100
					}
					asset.EfficiencyRating = fmt.Sprintf("%.1f%%", percentage)
				}
			}
		}
	}

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

// hasAssetModificationPermission checks if user has permission to modify an asset
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

// hasAssetDeletionPermission checks if user has permission to delete an asset
func hasAssetDeletionPermission(userID uint, userRole string, asset *models.BuildingAsset) bool {
	// Only admins and asset owners can delete assets
	if userRole == "admin" {
		return true
	}

	// Asset owners can delete their own assets
	if asset.CreatedBy == userID {
		return true
	}

	return false
}

// getUserRoleFromToken extracts user role from JWT token
func getUserRoleFromToken(r *http.Request) (string, error) {
	authHeader := r.Header.Get("Authorization")
	if authHeader == "" {
		return "", fmt.Errorf("no authorization header")
	}

	tokenStr := strings.TrimPrefix(authHeader, "Bearer ")
	if tokenStr == authHeader {
		return "", fmt.Errorf("invalid authorization format")
	}

	// Parse JWT token
	token, err := jwt.Parse(tokenStr, func(token *jwt.Token) (interface{}, error) {
		return []byte(os.Getenv("JWT_SECRET")), nil
	})

	if err != nil || !token.Valid {
		return "", fmt.Errorf("invalid token")
	}

	if claims, ok := token.Claims.(jwt.MapClaims); ok {
		if role, exists := claims["role"].(string); exists {
			return role, nil
		}
	}

	return "", fmt.Errorf("role not found in token")
}
