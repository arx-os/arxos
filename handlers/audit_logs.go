package handlers

import (
	"arxline/db"
	"arxline/models"
	"encoding/json"
	"net/http"
	"strconv"
)

// GET /api/audit-logs?building_id=...&object_id=...
func ListAuditLogs(w http.ResponseWriter, r *http.Request) {
	buildingID := r.URL.Query().Get("building_id")
	objectID := r.URL.Query().Get("object_id")

	page, _ := strconv.Atoi(r.URL.Query().Get("page"))
	if page < 1 {
		page = 1
	}
	pageSize, _ := strconv.Atoi(r.URL.Query().Get("page_size"))
	if pageSize < 1 || pageSize > 100 {
		pageSize = 20
	}
	offset := (page - 1) * pageSize

	var total int64
	query := db.DB.Model(&models.AuditLog{})
	if buildingID != "" {
		// TODO: Join with objects to filter by building if needed
	}
	if objectID != "" {
		query = query.Where("object_id = ?", objectID)
	}
	query.Count(&total)

	var logs []models.AuditLog
	query.Order("created_at desc").Offset(offset).Limit(pageSize).Find(&logs)

	resp := map[string]interface{}{
		"results":     logs,
		"page":        page,
		"page_size":   pageSize,
		"total":       total,
		"total_pages": (total + int64(pageSize) - 1) / int64(pageSize),
	}
	json.NewEncoder(w).Encode(resp)
}
