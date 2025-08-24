package bim

import (
	"github.com/arxos/arxos/core/internal/db"
	"github.com/arxos/arxos/core/internal/models"
	"encoding/json"
	"net/http"
	"strconv"
)

// GET /api/svg-objects?object_id=...&floor_id=...&type=...&label=...&page=...&page_size=...
func ListSVGObjects(w http.ResponseWriter, r *http.Request) {
	objectID := r.URL.Query().Get("object_id")
	floorID := r.URL.Query().Get("floor_id")
	typeStr := r.URL.Query().Get("type")
	label := r.URL.Query().Get("label")

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
	query := db.DB.Model(&models.SVGObject{})
	if objectID != "" {
		query = query.Where("object_id = ?", objectID)
	}
	if floorID != "" {
		query = query.Where("floor_id = ?", floorID)
	}
	if typeStr != "" {
		query = query.Where("type = ?", typeStr)
	}
	if label != "" {
		query = query.Where("label ILIKE ?", "%"+label+"%")
	}
	query.Count(&total)

	var objects []models.SVGObject
	query.Offset(offset).Limit(pageSize).Find(&objects)

	resp := map[string]interface{}{
		"results":     objects,
		"page":        page,
		"page_size":   pageSize,
		"total":       total,
		"total_pages": (total + int64(pageSize) - 1) / int64(pageSize),
	}
	json.NewEncoder(w).Encode(resp)
}
