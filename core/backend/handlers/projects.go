// handlers/projects.go
package handlers

import (
	"arx/db"
	"arx/models"
	"encoding/json"
	"net/http"
	"strconv"
	"time"

	"github.com/go-chi/chi/v5"
)

func ListProjects(w http.ResponseWriter, r *http.Request) {
	user, err := GetUserFromRequest(r)
	if err != nil {
		http.Error(w, "Unauthorized", http.StatusUnauthorized)
		return
	}
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
	query := db.DB.Model(&models.Project{}).Where("user_id = ?", user.ID)
	query.Count(&total)

	var projects []models.Project
	query.Offset(offset).Limit(pageSize).Find(&projects)

	resp := map[string]interface{}{
		"results":     projects,
		"page":        page,
		"page_size":   pageSize,
		"total":       total,
		"total_pages": (total + int64(pageSize) - 1) / int64(pageSize),
	}
	json.NewEncoder(w).Encode(resp)
}

func CreateProject(w http.ResponseWriter, r *http.Request) {
	user, err := GetUserFromRequest(r)
	if err != nil {
		http.Error(w, "Unauthorized", http.StatusUnauthorized)
		return
	}

	var p models.Project
	json.NewDecoder(r.Body).Decode(&p)
	p.UserID = user.ID
	db.DB.Create(&p)
	json.NewEncoder(w).Encode(p)
}

func GetProject(w http.ResponseWriter, r *http.Request) {
	user, err := GetUserFromRequest(r)
	if err != nil {
		http.Error(w, "Unauthorized", http.StatusUnauthorized)
		return
	}

	idParam := chi.URLParam(r, "id")
	id, err := strconv.Atoi(idParam)
	if err != nil {
		http.Error(w, "Invalid ID", http.StatusBadRequest)
		return
	}

	var p models.Project
	db.DB.First(&p, id)
	if p.UserID != user.ID {
		http.Error(w, "Forbidden", http.StatusForbidden)
		return
	}
	json.NewEncoder(w).Encode(p)
}

func UpdateProject(w http.ResponseWriter, r *http.Request) {
	user, err := GetUserFromRequest(r)
	if err != nil {
		http.Error(w, "Unauthorized", http.StatusUnauthorized)
		return
	}

	idParam := chi.URLParam(r, "id")
	id, err := strconv.Atoi(idParam)
	if err != nil {
		http.Error(w, "Invalid ID", http.StatusBadRequest)
		return
	}

	var p models.Project
	if err := db.DB.First(&p, id).Error; err != nil {
		http.Error(w, "Project not found", http.StatusNotFound)
		return
	}

	if p.UserID != user.ID {
		http.Error(w, "Forbidden", http.StatusForbidden)
		return
	}

	var updateData models.Project
	if err := json.NewDecoder(r.Body).Decode(&updateData); err != nil {
		http.Error(w, "Invalid JSON", http.StatusBadRequest)
		return
	}

	// Update allowed fields
	p.Name = updateData.Name
	p.UpdatedAt = time.Now()

	db.DB.Save(&p)
	json.NewEncoder(w).Encode(p)
}

func DeleteProject(w http.ResponseWriter, r *http.Request) {
	user, err := GetUserFromRequest(r)
	if err != nil {
		http.Error(w, "Unauthorized", http.StatusUnauthorized)
		return
	}

	idParam := chi.URLParam(r, "id")
	id, err := strconv.Atoi(idParam)
	if err != nil {
		http.Error(w, "Invalid ID", http.StatusBadRequest)
		return
	}

	var p models.Project
	if err := db.DB.First(&p, id).Error; err != nil {
		http.Error(w, "Project not found", http.StatusNotFound)
		return
	}

	if p.UserID != user.ID {
		http.Error(w, "Forbidden", http.StatusForbidden)
		return
	}

	db.DB.Delete(&p)
	w.WriteHeader(http.StatusNoContent)
}

func GetProjectStatistics(w http.ResponseWriter, r *http.Request) {
	user, err := GetUserFromRequest(r)
	if err != nil {
		http.Error(w, "Unauthorized", http.StatusUnauthorized)
		return
	}

	idParam := chi.URLParam(r, "id")
	id, err := strconv.Atoi(idParam)
	if err != nil {
		http.Error(w, "Invalid ID", http.StatusBadRequest)
		return
	}

	var p models.Project
	if err := db.DB.First(&p, id).Error; err != nil {
		http.Error(w, "Project not found", http.StatusNotFound)
		return
	}

	if p.UserID != user.ID {
		http.Error(w, "Forbidden", http.StatusForbidden)
		return
	}

	// Get project statistics
	var floorCount int64
	db.DB.Model(&models.Floor{}).Where("project_id = ?", id).Count(&floorCount)

	var deviceCount int64
	db.DB.Model(&models.Device{}).Where("project_id = ?", id).Count(&deviceCount)

	var roomCount int64
	db.DB.Model(&models.Room{}).Where("project_id = ?", id).Count(&roomCount)

	stats := map[string]interface{}{
		"project_id":    id,
		"floors":        floorCount,
		"devices":       deviceCount,
		"rooms":         roomCount,
		"created_at":    p.CreatedAt,
		"last_modified": p.UpdatedAt,
	}

	json.NewEncoder(w).Encode(stats)
}
