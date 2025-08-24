package admin

import (
	"encoding/json"
	"fmt"
	"net/http"
	"strconv"
	"time"

	"github.com/arxos/arxos/core/internal/db"
	"github.com/arxos/arxos/core/internal/models"
)

// GET /api/audit-logs?building_id=...&object_id=...&asset_id=...&user_id=...&date_from=...&date_to=...&action=...
func ListAuditLogs(w http.ResponseWriter, r *http.Request) {
	// Parse query parameters
	buildingID := r.URL.Query().Get("building_id")
	objectID := r.URL.Query().Get("object_id")
	assetID := r.URL.Query().Get("asset_id")
	userID := r.URL.Query().Get("user_id")
	dateFrom := r.URL.Query().Get("date_from")
	dateTo := r.URL.Query().Get("date_to")
	action := r.URL.Query().Get("action")
	objectType := r.URL.Query().Get("object_type")
	exportID := r.URL.Query().Get("export_id")
	ipAddress := r.URL.Query().Get("ip_address")

	// Pagination
	page, _ := strconv.Atoi(r.URL.Query().Get("page"))
	if page < 1 {
		page = 1
	}
	pageSize, _ := strconv.Atoi(r.URL.Query().Get("page_size"))
	if pageSize < 1 || pageSize > 100 {
		pageSize = 20
	}
	offset := (page - 1) * pageSize

	// Build query
	var total int64
	query := db.DB.Model(&models.AuditLog{})

	// Apply filters
	if buildingID != "" {
		if buildingIDInt, err := strconv.ParseUint(buildingID, 10, 32); err == nil {
			query = query.Where("building_id = ?", buildingIDInt)
		}
	}

	if objectID != "" {
		query = query.Where("object_id = ?", objectID)
	}

	if assetID != "" {
		query = query.Where("asset_id = ?", assetID)
	}

	if userID != "" {
		if userIDInt, err := strconv.ParseUint(userID, 10, 32); err == nil {
			query = query.Where("user_id = ?", userIDInt)
		}
	}

	if dateFrom != "" {
		if dateFromTime, err := time.Parse("2006-01-02", dateFrom); err == nil {
			query = query.Where("created_at >= ?", dateFromTime)
		}
	}

	if dateTo != "" {
		if dateToTime, err := time.Parse("2006-01-02", dateTo); err == nil {
			// Add one day to include the entire day
			dateToTime = dateToTime.Add(24 * time.Hour)
			query = query.Where("created_at < ?", dateToTime)
		}
	}

	if action != "" {
		query = query.Where("action = ?", action)
	}

	if objectType != "" {
		query = query.Where("object_type = ?", objectType)
	}

	if exportID != "" {
		if exportIDInt, err := strconv.ParseUint(exportID, 10, 32); err == nil {
			query = query.Where("export_id = ?", exportIDInt)
		}
	}

	if ipAddress != "" {
		query = query.Where("ip_address LIKE ?", "%"+ipAddress+"%")
	}

	// Count total results
	query.Count(&total)

	// Get paginated results
	var logs []models.AuditLog
	query.Order("created_at desc").Offset(offset).Limit(pageSize).Find(&logs)

	// Check if export is requested
	exportFormat := r.URL.Query().Get("export")
	if exportFormat != "" {
		exportAuditLogs(w, logs, exportFormat)
		return
	}

	// Return JSON response
	resp := map[string]interface{}{
		"results":     logs,
		"page":        page,
		"page_size":   pageSize,
		"total":       total,
		"total_pages": (total + int64(pageSize) - 1) / int64(pageSize),
		"filters": map[string]interface{}{
			"building_id": buildingID,
			"object_id":   objectID,
			"asset_id":    assetID,
			"user_id":     userID,
			"date_from":   dateFrom,
			"date_to":     dateTo,
			"action":      action,
			"object_type": objectType,
			"export_id":   exportID,
			"ip_address":  ipAddress,
		},
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(resp)
}

// GET /api/audit-logs/asset/{asset_id} - Get audit logs for a specific asset
func GetAssetAuditLogs(w http.ResponseWriter, r *http.Request) {
	// Extract asset ID from URL path
	assetID := r.URL.Query().Get("asset_id")
	if assetID == "" {
		http.Error(w, "Asset ID is required", http.StatusBadRequest)
		return
	}

	// Set the asset_id filter and delegate to ListAuditLogs
	r.URL.Query().Set("asset_id", assetID)
	r.URL.Query().Set("object_type", "asset")
	ListAuditLogs(w, r)
}

// GET /api/audit-logs/export/{export_id} - Get audit logs for a specific export
func GetExportAuditLogs(w http.ResponseWriter, r *http.Request) {
	// Extract export ID from URL path
	exportID := r.URL.Query().Get("export_id")
	if exportID == "" {
		http.Error(w, "Export ID is required", http.StatusBadRequest)
		return
	}

	// Set the export_id filter and delegate to ListAuditLogs
	r.URL.Query().Set("export_id", exportID)
	r.URL.Query().Set("object_type", "export")
	ListAuditLogs(w, r)
}

// GET /api/audit-logs/user/{user_id} - Get audit logs for a specific user
func GetUserAuditLogs(w http.ResponseWriter, r *http.Request) {
	// Extract user ID from URL path
	userID := r.URL.Query().Get("user_id")
	if userID == "" {
		http.Error(w, "User ID is required", http.StatusBadRequest)
		return
	}

	// Set the user_id filter and delegate to ListAuditLogs
	r.URL.Query().Set("user_id", userID)
	ListAuditLogs(w, r)
}

// Helper function to export audit logs in different formats
func exportAuditLogs(w http.ResponseWriter, logs []models.AuditLog, format string) {
	switch format {
	case "csv":
		exportAuditLogsCSV(w, logs)
	case "json":
		exportAuditLogsJSON(w, logs)
	case "xml":
		exportAuditLogsXML(w, logs)
	default:
		http.Error(w, "Unsupported export format", http.StatusBadRequest)
	}
}

func exportAuditLogsCSV(w http.ResponseWriter, logs []models.AuditLog) {
	w.Header().Set("Content-Type", "text/csv")
	w.Header().Set("Content-Disposition", "attachment; filename=audit_logs.csv")

	// Write CSV header
	w.Write([]byte("ID,User ID,Object Type,Object ID,Action,IP Address,User Agent,Building ID,Floor ID,Asset ID,Export ID,Created At\n"))

	// Write data rows
	for _, log := range logs {
		line := fmt.Sprintf("%d,%d,%s,%s,%s,%s,%s,%v,%v,%v,%v,%s\n",
			log.ID,
			log.UserID,
			log.ObjectType,
			log.ObjectID,
			log.Action,
			log.IPAddress,
			log.UserAgent,
			log.BuildingID,
			log.FloorID,
			log.AssetID,
			log.ExportID,
			log.CreatedAt.Format("2006-01-02 15:04:05"),
		)
		w.Write([]byte(line))
	}
}

func exportAuditLogsJSON(w http.ResponseWriter, logs []models.AuditLog) {
	w.Header().Set("Content-Type", "application/json")
	w.Header().Set("Content-Disposition", "attachment; filename=audit_logs.json")

	json.NewEncoder(w).Encode(map[string]interface{}{
		"export_date":   time.Now().Format("2006-01-02 15:04:05"),
		"total_records": len(logs),
		"logs":          logs,
	})
}

func exportAuditLogsXML(w http.ResponseWriter, logs []models.AuditLog) {
	w.Header().Set("Content-Type", "application/xml")
	w.Header().Set("Content-Disposition", "attachment; filename=audit_logs.xml")

	// Simple XML export - in production, you might want to use a proper XML library
	w.Write([]byte("<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n"))
	w.Write([]byte("<audit_logs>\n"))
	w.Write([]byte(fmt.Sprintf("  <export_date>%s</export_date>\n", time.Now().Format("2006-01-02 15:04:05"))))
	w.Write([]byte(fmt.Sprintf("  <total_records>%d</total_records>\n", len(logs))))

	for _, log := range logs {
		w.Write([]byte("  <log>\n"))
		w.Write([]byte(fmt.Sprintf("    <id>%d</id>\n", log.ID)))
		w.Write([]byte(fmt.Sprintf("    <user_id>%d</user_id>\n", log.UserID)))
		w.Write([]byte(fmt.Sprintf("    <object_type>%s</object_type>\n", log.ObjectType)))
		w.Write([]byte(fmt.Sprintf("    <object_id>%s</object_id>\n", log.ObjectID)))
		w.Write([]byte(fmt.Sprintf("    <action>%s</action>\n", log.Action)))
		w.Write([]byte(fmt.Sprintf("    <ip_address>%s</ip_address>\n", log.IPAddress)))
		w.Write([]byte(fmt.Sprintf("    <created_at>%s</created_at>\n", log.CreatedAt.Format("2006-01-02 15:04:05"))))
		w.Write([]byte("  </log>\n"))
	}

	w.Write([]byte("</audit_logs>\n"))
}
