package handlers

import (
	"encoding/json"
	"log"
	"net/http"
	"strconv"

	"arxos/db"
	"arxos/models"

	"github.com/go-chi/chi/v5"
)

// POST /api/user-category-permissions
func AssignUserCategoryPermission(w http.ResponseWriter, r *http.Request) {
	user, err := GetUserFromRequest(r)
	if err != nil {
		http.Error(w, "Unauthorized", http.StatusUnauthorized)
		return
	}
	if user.Role != "admin" && user.Role != "builder" && user.Role != "inspector" && user.Role != "owner" {
		http.Error(w, "Forbidden: insufficient role", http.StatusForbidden)
		return
	}
	var perm models.UserCategoryPermission
	if err := json.NewDecoder(r.Body).Decode(&perm); err != nil {
		http.Error(w, "Invalid body", http.StatusBadRequest)
		return
	}
	if perm.UserID == 0 || perm.CategoryID == 0 || perm.ProjectID == 0 {
		http.Error(w, "user_id, category_id, and project_id are required", http.StatusBadRequest)
		return
	}
	if err := db.DB.Create(&perm).Error; err != nil {
		http.Error(w, "Failed to assign permission", http.StatusInternalServerError)
		return
	}
	log.Printf("User %d (%s) assigned category permission: %+v", user.ID, user.Role, perm)
	w.WriteHeader(http.StatusCreated)
	json.NewEncoder(w).Encode(perm)
}

// GET /api/user-category-permissions?project_id=...
func ListUserCategoryPermissions(w http.ResponseWriter, r *http.Request) {
	user, err := GetUserFromRequest(r)
	if err != nil {
		http.Error(w, "Unauthorized", http.StatusUnauthorized)
		return
	}
	if user.Role != "admin" && user.Role != "builder" && user.Role != "inspector" && user.Role != "owner" {
		http.Error(w, "Forbidden: insufficient role", http.StatusForbidden)
		return
	}
	projectIDStr := r.URL.Query().Get("project_id")
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
	query := db.DB.Model(&models.UserCategoryPermission{})
	if projectIDStr != "" {
		projectID, err := strconv.Atoi(projectIDStr)
		if err != nil {
			http.Error(w, "Invalid project_id", http.StatusBadRequest)
			return
		}
		query = query.Where("project_id = ?", projectID)
	}
	query.Count(&total)

	var perms []models.UserCategoryPermission
	query.Offset(offset).Limit(pageSize).Find(&perms)

	resp := map[string]interface{}{
		"results":     perms,
		"page":        page,
		"page_size":   pageSize,
		"total":       total,
		"total_pages": (total + int64(pageSize) - 1) / int64(pageSize),
	}
	log.Printf("User %d (%s) listed category permissions", user.ID, user.Role)
	json.NewEncoder(w).Encode(resp)
}

// DELETE /api/user-category-permissions/{id}
func RevokeUserCategoryPermission(w http.ResponseWriter, r *http.Request) {
	user, err := GetUserFromRequest(r)
	if err != nil {
		http.Error(w, "Unauthorized", http.StatusUnauthorized)
		return
	}
	if user.Role != "admin" && user.Role != "builder" && user.Role != "inspector" && user.Role != "owner" {
		http.Error(w, "Forbidden: insufficient role", http.StatusForbidden)
		return
	}
	idStr := chi.URLParam(r, "id")
	id, err := strconv.Atoi(idStr)
	if err != nil {
		http.Error(w, "Invalid permission ID", http.StatusBadRequest)
		return
	}
	if err := db.DB.Delete(&models.UserCategoryPermission{}, id).Error; err != nil {
		http.Error(w, "Failed to revoke permission", http.StatusInternalServerError)
		return
	}
	log.Printf("User %d (%s) revoked category permission ID %d", user.ID, user.Role, id)
	w.WriteHeader(http.StatusNoContent)
}
