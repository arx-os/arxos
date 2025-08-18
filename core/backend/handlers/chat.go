package handlers

import (
	"encoding/json"
	"net/http"
	"regexp"
	"strconv"

	"github.com/arxos/arxos/core/backend/db"
	"github.com/arxos/arxos/core/backend/models"

	"github.com/go-chi/chi/v5"
)

// POST /api/buildings/{id}/chat
func PostChatMessage(w http.ResponseWriter, r *http.Request) {
	user, err := GetUserFromRequest(r)
	if err != nil {
		http.Error(w, "Unauthorized", http.StatusUnauthorized)
		return
	}
	buildingIDStr := chi.URLParam(r, "id")
	buildingID, err := strconv.Atoi(buildingIDStr)
	if err != nil {
		http.Error(w, "Invalid building ID", http.StatusBadRequest)
		return
	}
	var msg models.ChatMessage
	if err := json.NewDecoder(r.Body).Decode(&msg); err != nil {
		http.Error(w, "Invalid body", http.StatusBadRequest)
		return
	}

	// Parse references
	userRe := regexp.MustCompile(`@([a-zA-Z0-9_\-]+)`)   // @username
	catalogRe := regexp.MustCompile(`\$([0-9]+)`)        // $catalog_id (numeric)
	objectRe := regexp.MustCompile(`#([a-zA-Z0-9_\-]+)`) // #object_id

	usernames := userRe.FindAllStringSubmatch(msg.Message, -1)
	catalogIDs := catalogRe.FindAllStringSubmatch(msg.Message, -1)
	objectIDs := objectRe.FindAllStringSubmatch(msg.Message, -1)

	// Validate @username
	for _, match := range usernames {
		if len(match) < 2 {
			continue
		}
		var u models.User
		err := db.DB.Where("username = ?", match[1]).First(&u).Error
		if err != nil {
			http.Error(w, "Invalid @username reference: @"+match[1], http.StatusBadRequest)
			return
		}
	}
	// Validate $catalog_id
	for _, match := range catalogIDs {
		if len(match) < 2 {
			continue
		}
		var c models.CatalogItem
		err := db.DB.Where("id = ?", match[1]).First(&c).Error
		if err != nil {
			http.Error(w, "Invalid $catalog_id reference: $"+match[1], http.StatusBadRequest)
			return
		}
	}
	// Validate #object_id
	for _, match := range objectIDs {
		if len(match) < 2 {
			continue
		}
		var o models.SVGObject
		err := db.DB.Where("object_id = ?", match[1]).First(&o).Error
		if err != nil {
			http.Error(w, "Invalid #object_id reference: #"+match[1], http.StatusBadRequest)
			return
		}
	}

	// Store references in JSON
	references := map[string]interface{}{
		"usernames":   []string{},
		"catalog_ids": []string{},
		"object_ids":  []string{},
	}
	for _, match := range usernames {
		if len(match) >= 2 {
			references["usernames"] = append(references["usernames"].([]string), match[1])
		}
	}
	for _, match := range catalogIDs {
		if len(match) >= 2 {
			references["catalog_ids"] = append(references["catalog_ids"].([]string), match[1])
		}
	}
	for _, match := range objectIDs {
		if len(match) >= 2 {
			references["object_ids"] = append(references["object_ids"].([]string), match[1])
		}
	}
	refsJSON, _ := json.Marshal(references)
	msg.References = refsJSON

	msg.UserID = user.ID
	msg.BuildingID = uint(buildingID)
	if err := db.DB.Create(&msg).Error; err != nil {
		http.Error(w, "Failed to save message", http.StatusInternalServerError)
		return
	}
	w.WriteHeader(http.StatusCreated)
	json.NewEncoder(w).Encode(map[string]interface{}{
		"id":          msg.ID,
		"building_id": msg.BuildingID,
		"user_id":     msg.UserID,
		"message":     msg.Message,
		"created_at":  msg.CreatedAt,
		"references":  msg.References,
	})
}

// GET /api/buildings/{id}/chat
func ListChatMessages(w http.ResponseWriter, r *http.Request) {
	buildingIDStr := chi.URLParam(r, "id")
	buildingID, err := strconv.Atoi(buildingIDStr)
	if err != nil {
		http.Error(w, "Invalid building ID", http.StatusBadRequest)
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
	db.DB.Model(&models.ChatMessage{}).Where("building_id = ?", buildingID).Count(&total)

	var messages []models.ChatMessage
	db.DB.Where("building_id = ?", buildingID).Order("created_at asc").Offset(offset).Limit(pageSize).Find(&messages)

	// Prepare regexes for reference parsing
	catalogRe := regexp.MustCompile(`\\$([0-9]+)`)
	objectRe := regexp.MustCompile(`#([a-zA-Z0-9_\-]+)`)

	var enriched []map[string]interface{}
	for _, msg := range messages {
		// User info
		var user models.User
		db.DB.First(&user, msg.UserID)

		// Parse references
		catalogIDs := catalogRe.FindAllStringSubmatch(msg.Message, -1)
		objectIDs := objectRe.FindAllStringSubmatch(msg.Message, -1)

		// Catalog refs
		catalogRefs := []models.CatalogItem{}
		for _, match := range catalogIDs {
			if len(match) < 2 {
				continue
			}
			var c models.CatalogItem
			if err := db.DB.Where("id = ?", match[1]).First(&c).Error; err == nil {
				catalogRefs = append(catalogRefs, c)
			}
		}
		// Object refs
		objectRefs := []models.SVGObject{}
		for _, match := range objectIDs {
			if len(match) < 2 {
				continue
			}
			var o models.SVGObject
			if err := db.DB.Where("object_id = ?", match[1]).First(&o).Error; err == nil {
				objectRefs = append(objectRefs, o)
			}
		}

		// Build enriched message
		item := map[string]interface{}{
			"id":          msg.ID,
			"building_id": msg.BuildingID,
			"user_id":     msg.UserID,
			"message":     msg.Message,
			"created_at":  msg.CreatedAt,
			"user": map[string]interface{}{
				"id":       user.ID,
				"username": user.Username,
				"role":     user.Role,
				"email":    user.Email,
			},
			"catalog_refs": catalogRefs,
			"object_refs":  objectRefs,
		}
		enriched = append(enriched, item)
	}

	resp := map[string]interface{}{
		"results":     enriched,
		"page":        page,
		"page_size":   pageSize,
		"total":       total,
		"total_pages": (total + int64(pageSize) - 1) / int64(pageSize),
	}
	json.NewEncoder(w).Encode(resp)
}
