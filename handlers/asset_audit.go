package handlers

import (
	"arx/db"
	"arx/models"
	"encoding/json"
	"fmt"
	"net/http"
	"time"

	"github.com/go-chi/chi/v5"
	"github.com/google/uuid"
	"gorm.io/gorm"
)

// CreateBuildingAssetWithAudit creates a new building asset with audit logging
func CreateBuildingAssetWithAudit(w http.ResponseWriter, r *http.Request) {
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

// UpdateBuildingAssetWithAudit updates an existing asset with audit logging
func UpdateBuildingAssetWithAudit(w http.ResponseWriter, r *http.Request) {
	userID, err := getUserIDFromToken(r)
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

// DeleteBuildingAssetWithAudit deletes an asset with audit logging
func DeleteBuildingAssetWithAudit(w http.ResponseWriter, r *http.Request) {
	userID, err := getUserIDFromToken(r)
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

// ExportBuildingInventoryWithAudit exports building assets with audit logging
func ExportBuildingInventoryWithAudit(w http.ResponseWriter, r *http.Request) {
	userID, err := getUserIDFromToken(r)
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

	if err := query.Find(&assets).Error; err != nil {
		http.Error(w, "Failed to retrieve assets", http.StatusInternalServerError)
		return
	}

	// Create export record
	exportRecord := models.BuildingAssetInventory{
		BuildingID:    uint(0), // Will be set below
		InventoryDate: time.Now(),
		TotalAssets:   len(assets),
		ExportFormat:  format,
		CreatedBy:     userID,
		CreatedAt:     time.Now(),
	}

	// Set building ID from first asset
	if len(assets) > 0 {
		exportRecord.BuildingID = assets[0].BuildingID
	}

	// Create the export record
	if err := db.DB.Create(&exportRecord).Error; err != nil {
		http.Error(w, "Failed to create export record", http.StatusInternalServerError)
		return
	}

	// Log the export activity
	exportPayload := map[string]interface{}{
		"building_id":         buildingID,
		"format":              format,
		"total_assets":        len(assets),
		"include_history":     includeHistory == "true",
		"include_maintenance": includeMaintenance == "true",
		"include_valuations":  includeValuations == "true",
	}

	if err := models.LogExportChange(db.DB, userID, exportRecord.ID, "export_inventory", exportPayload, r); err != nil {
		// Log error but don't fail the request
		fmt.Printf("Failed to log export activity: %v\n", err)
	}

	// Export based on format
	switch format {
	case "csv":
		exportToCSV(w, assets)
	case "json":
		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(assets)
	case "xml":
		w.Header().Set("Content-Type", "application/xml")
		exportToXML(w, assets)
	default:
		http.Error(w, "Unsupported export format", http.StatusBadRequest)
	}
}

// Helper function to export to XML (simplified)
func exportToXML(w http.ResponseWriter, assets []models.BuildingAsset) {
	w.Write([]byte("<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n"))
	w.Write([]byte("<assets>\n"))

	for _, asset := range assets {
		w.Write([]byte(fmt.Sprintf("  <asset>\n")))
		w.Write([]byte(fmt.Sprintf("    <id>%s</id>\n", asset.ID)))
		w.Write([]byte(fmt.Sprintf("    <asset_type>%s</asset_type>\n", asset.AssetType)))
		w.Write([]byte(fmt.Sprintf("    <system>%s</system>\n", asset.System)))
		w.Write([]byte(fmt.Sprintf("    <status>%s</status>\n", asset.Status)))
		w.Write([]byte(fmt.Sprintf("    <estimated_value>%.2f</estimated_value>\n", asset.EstimatedValue)))
		w.Write([]byte(fmt.Sprintf("  </asset>\n")))
	}

	w.Write([]byte("</assets>\n"))
}
