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
)

// DataVendorHandler handles data vendor API access
type DataVendorHandler struct {
	db *gorm.DB
}

// NewDataVendorHandler creates a new data vendor handler
func NewDataVendorHandler(db *gorm.DB) *DataVendorHandler {
	return &DataVendorHandler{db: db}
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
