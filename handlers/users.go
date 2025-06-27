// handlers/user.go
package handlers

import (
	"encoding/json"
	"net/http"
	"os"
	"strconv"
	"time"

	"arx/db"
	"arx/middleware/auth"
	"arx/models"

	"github.com/go-chi/chi/v5"
	"github.com/golang-jwt/jwt/v4"
	"golang.org/x/crypto/bcrypt"
)

type AuthRequest struct {
	Login    string `json:"login"`
	Email    string `json:"email"`
	Username string `json:"username"`
	Password string `json:"password"`
}

type AuthResponse struct {
	Token string `json:"token"`
}

// getUserIDFromToken extracts user ID from JWT token
func getUserIDFromToken(r *http.Request) (uint, error) {
	authHeader := r.Header.Get("Authorization")
	if authHeader == "" {
		return 0, http.ErrNoCookie
	}
	tokenStr := authHeader[7:]
	claims := &auth.Claims{}
	token, err := jwt.ParseWithClaims(tokenStr, claims, func(token *jwt.Token) (interface{}, error) {
		return []byte(os.Getenv("JWT_SECRET")), nil
	})
	if err != nil || !token.Valid {
		return 0, http.ErrNoCookie
	}
	return claims.UserID, nil
}

func Register(w http.ResponseWriter, r *http.Request) {
	var req AuthRequest
	json.NewDecoder(r.Body).Decode(&req)

	hash, err := bcrypt.GenerateFromPassword([]byte(req.Password), bcrypt.DefaultCost)
	if err != nil {
		http.Error(w, "Hash error", 500)
		return
	}

	user := models.User{Email: req.Email, Username: req.Username, Password: string(hash), Role: "user"}
	if err := db.DB.Create(&user).Error; err != nil {
		http.Error(w, "User exists or DB error", 400)
		return
	}

	token, _ := auth.GenerateJWT(user.ID, user.Role)
	json.NewEncoder(w).Encode(AuthResponse{Token: token})
}

func Login(w http.ResponseWriter, r *http.Request) {
	var req AuthRequest
	json.NewDecoder(r.Body).Decode(&req)

	var user models.User
	err := db.DB.Where("email = ? OR username = ?", req.Login, req.Login).First(&user).Error
	if err != nil {
		http.Error(w, "Invalid credentials", 400)
		return
	}

	err = bcrypt.CompareHashAndPassword([]byte(user.Password), []byte(req.Password))
	if err != nil {
		http.Error(w, "Invalid credentials", 400)
		return
	}

	token, _ := auth.GenerateJWT(user.ID, user.Role)
	json.NewEncoder(w).Encode(AuthResponse{Token: token})
}

func Me(w http.ResponseWriter, r *http.Request) {
	authHeader := r.Header.Get("Authorization")
	if authHeader == "" {
		http.Error(w, "Missing token", http.StatusUnauthorized)
		return
	}
	tokenStr := authHeader[7:]
	claims := &auth.Claims{}
	token, err := jwt.ParseWithClaims(tokenStr, claims, func(token *jwt.Token) (interface{}, error) {
		return []byte(os.Getenv("JWT_SECRET")), nil
	})
	if err != nil || !token.Valid {
		http.Error(w, "Invalid token", http.StatusUnauthorized)
		return
	}
	var user models.User
	if err := db.DB.First(&user, claims.UserID).Error; err != nil {
		http.Error(w, "User not found", http.StatusNotFound)
		return
	}
	json.NewEncoder(w).Encode(user)
}

// ListBuildings returns all buildings owned by the current user
func ListBuildings(w http.ResponseWriter, r *http.Request) {
	userID, err := getUserIDFromToken(r)
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
	query := db.DB.Model(&models.Building{}).Where("owner_id = ?", userID)
	query.Count(&total)

	var buildings []models.Building
	query.Offset(offset).Limit(pageSize).Find(&buildings)

	resp := map[string]interface{}{
		"results":     buildings,
		"page":        page,
		"page_size":   pageSize,
		"total":       total,
		"total_pages": (total + int64(pageSize) - 1) / int64(pageSize),
	}
	json.NewEncoder(w).Encode(resp)
}

// CreateBuilding creates a new building (Owner only)
func CreateBuilding(w http.ResponseWriter, r *http.Request) {
	userID, err := getUserIDFromToken(r)
	if err != nil {
		http.Error(w, "Unauthorized", http.StatusUnauthorized)
		return
	}
	var b models.Building
	if err := json.NewDecoder(r.Body).Decode(&b); err != nil {
		http.Error(w, "Invalid body", http.StatusBadRequest)
		return
	}
	b.OwnerID = userID
	if err := db.DB.Create(&b).Error; err != nil {
		http.Error(w, "DB error", http.StatusInternalServerError)
		return
	}
	json.NewEncoder(w).Encode(b)
}

// GetBuilding returns details for a specific building (owner only)
func GetBuilding(w http.ResponseWriter, r *http.Request) {
	userID, err := getUserIDFromToken(r)
	if err != nil {
		http.Error(w, "Unauthorized", http.StatusUnauthorized)
		return
	}
	idParam := chi.URLParam(r, "id")
	var b models.Building
	if err := db.DB.First(&b, idParam).Error; err != nil {
		http.Error(w, "Building not found", http.StatusNotFound)
		return
	}
	if b.OwnerID != userID {
		http.Error(w, "Forbidden", http.StatusForbidden)
		return
	}
	json.NewEncoder(w).Encode(b)
}

// UpdateBuilding updates building metadata (owner only)
func UpdateBuilding(w http.ResponseWriter, r *http.Request) {
	userID, err := getUserIDFromToken(r)
	if err != nil {
		http.Error(w, "Unauthorized", http.StatusUnauthorized)
		return
	}
	idParam := chi.URLParam(r, "id")
	var b models.Building
	if err := db.DB.First(&b, idParam).Error; err != nil {
		http.Error(w, "Building not found", http.StatusNotFound)
		return
	}
	if b.OwnerID != userID {
		http.Error(w, "Forbidden", http.StatusForbidden)
		return
	}
	var update models.Building
	if err := json.NewDecoder(r.Body).Decode(&update); err != nil {
		http.Error(w, "Invalid body", http.StatusBadRequest)
		return
	}
	b.Name = update.Name
	b.Address = update.Address
	if err := db.DB.Save(&b).Error; err != nil {
		http.Error(w, "DB error", http.StatusInternalServerError)
		return
	}
	json.NewEncoder(w).Encode(b)
}

// ListFloors returns all floors for a given building (owner only)
func ListFloors(w http.ResponseWriter, r *http.Request) {
	userID, err := getUserIDFromToken(r)
	if err != nil {
		http.Error(w, "Unauthorized", http.StatusUnauthorized)
		return
	}
	buildingID := chi.URLParam(r, "id")
	var b models.Building
	if err := db.DB.First(&b, buildingID).Error; err != nil {
		http.Error(w, "Building not found", http.StatusNotFound)
		return
	}
	if b.OwnerID != userID {
		http.Error(w, "Forbidden", http.StatusForbidden)
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
	query := db.DB.Model(&models.Floor{}).Where("building_id = ?", buildingID)
	query.Count(&total)

	var floors []models.Floor
	query.Offset(offset).Limit(pageSize).Find(&floors)

	resp := map[string]interface{}{
		"results":     floors,
		"page":        page,
		"page_size":   pageSize,
		"total":       total,
		"total_pages": (total + int64(pageSize) - 1) / int64(pageSize),
	}
	json.NewEncoder(w).Encode(resp)
}

// SubmitMarkup allows a user to submit a markup for a building/floor
func SubmitMarkup(w http.ResponseWriter, r *http.Request) {
	userID, err := getUserIDFromToken(r)
	if err != nil {
		http.Error(w, "Unauthorized", http.StatusUnauthorized)
		return
	}
	var m models.Markup
	if err := json.NewDecoder(r.Body).Decode(&m); err != nil {
		http.Error(w, "Invalid body", http.StatusBadRequest)
		return
	}
	// Validate Elements as MarkupElements
	var elements models.MarkupElements
	if err := json.Unmarshal([]byte(m.Elements), &elements); err != nil {
		http.Error(w, "Elements must be valid JSON with a symbols array", http.StatusBadRequest)
		return
	}
	for _, sym := range elements.Symbols {
		if sym.SymbolID == "" {
			http.Error(w, "Each symbol must have a symbol_id", http.StatusBadRequest)
			return
		}
		// x and y are required (0 is valid)
	}
	m.UserID = userID
	m.CreatedAt = time.Now()
	if err := db.DB.Create(&m).Error; err != nil {
		http.Error(w, "DB error", http.StatusInternalServerError)
		return
	}
	json.NewEncoder(w).Encode(m)
}

// ListMarkups returns all markups for the current user (with parsed symbols)
func ListMarkups(w http.ResponseWriter, r *http.Request) {
	userID, err := getUserIDFromToken(r)
	if err != nil {
		http.Error(w, "Unauthorized", http.StatusUnauthorized)
		return
	}
	var markups []models.Markup
	db.DB.Where("user_id = ?", userID).Find(&markups)
	// Parse Elements for each markup
	var result []map[string]interface{}
	for _, m := range markups {
		var elements models.MarkupElements
		_ = json.Unmarshal([]byte(m.Elements), &elements)
		item := map[string]interface{}{
			"id":          m.ID,
			"building_id": m.BuildingID,
			"floor_id":    m.FloorID,
			"user_id":     m.UserID,
			"system":      m.System,
			"created_at":  m.CreatedAt,
			"symbols":     elements.Symbols,
		}
		result = append(result, item)
	}
	json.NewEncoder(w).Encode(result)
}

// GetLogs returns all logs for a building
func GetLogs(w http.ResponseWriter, r *http.Request) {
	userID, err := getUserIDFromToken(r)
	if err != nil {
		http.Error(w, "Unauthorized", http.StatusUnauthorized)
		return
	}
	buildingID := chi.URLParam(r, "building_id")
	var b models.Building
	if err := db.DB.First(&b, buildingID).Error; err != nil {
		http.Error(w, "Building not found", http.StatusNotFound)
		return
	}
	if b.OwnerID != userID {
		http.Error(w, "Forbidden", http.StatusForbidden)
		return
	}
	var logs []models.Log
	db.DB.Where("building_id = ?", buildingID).Order("created_at desc").Find(&logs)
	json.NewEncoder(w).Encode(logs)
}

// HTMX: Return <option> list for all buildings owned by the user
func HTMXListBuildings(w http.ResponseWriter, r *http.Request) {
	userID, err := getUserIDFromToken(r)
	if err != nil {
		http.Error(w, "Unauthorized", http.StatusUnauthorized)
		return
	}
	var buildings []models.Building
	db.DB.Where("owner_id = ?", userID).Find(&buildings)
	w.Header().Set("Content-Type", "text/html")
	for _, b := range buildings {
		w.Write([]byte("<option value=\"" + itoa(b.ID) + "\">" + b.Name + "</option>"))
	}
}

// HTMX: Return <option> list for all floors in a building
func HTMXListFloors(w http.ResponseWriter, r *http.Request) {
	userID, err := getUserIDFromToken(r)
	if err != nil {
		http.Error(w, "Unauthorized", http.StatusUnauthorized)
		return
	}
	buildingID := chi.URLParam(r, "id")
	var b models.Building
	if err := db.DB.First(&b, buildingID).Error; err != nil {
		http.Error(w, "Building not found", http.StatusNotFound)
		return
	}
	if b.OwnerID != userID {
		http.Error(w, "Forbidden", http.StatusForbidden)
		return
	}
	var floors []models.Floor
	db.DB.Where("building_id = ?", buildingID).Find(&floors)
	w.Header().Set("Content-Type", "text/html")
	for _, f := range floors {
		w.Write([]byte("<option value=\"" + itoa(f.ID) + "\">" + f.Name + "</option>"))
	}
}

// HTMX: Return <li> list for all buildings by role (owner/shared)
func HTMXListBuildingsSidebar(w http.ResponseWriter, r *http.Request) {
	userID, err := getUserIDFromToken(r)
	if err != nil {
		http.Error(w, "Unauthorized", http.StatusUnauthorized)
		return
	}
	role := r.URL.Query().Get("role")
	var buildings []models.Building

	if role == "owner" {
		db.DB.Where("owner_id = ?", userID).Find(&buildings)
	} else if role == "shared" {
		// Join with user_category_permissions to find shared buildings
		db.DB.Raw(`
			SELECT DISTINCT b.* FROM buildings b
			JOIN user_category_permissions ucp ON ucp.project_id = b.project_id
			WHERE ucp.user_id = ? AND b.owner_id != ?`, userID, userID).Scan(&buildings)
	} else {
		http.Error(w, "Invalid role", http.StatusBadRequest)
		return
	}

	w.Header().Set("Content-Type", "text/html")
	for _, b := range buildings {
		w.Write([]byte("<li data-building-id=\"" + itoa(b.ID) + "\" class=\"cursor-pointer hover:bg-blue-50 rounded px-2 py-1\">" + b.Name + "</li>"))
	}
}

// Helper to convert uint to string
func itoa(i uint) string {
	return strconv.FormatUint(uint64(i), 10)
}

// DeleteMarkup deletes a markup by ID
func DeleteMarkup(w http.ResponseWriter, r *http.Request) {
	userID, err := getUserIDFromToken(r)
	if err != nil {
		http.Error(w, "Unauthorized", http.StatusUnauthorized)
		return
	}
	markupID := chi.URLParam(r, "id")
	var markup models.Markup
	if err := db.DB.First(&markup, markupID).Error; err != nil {
		http.Error(w, "Markup not found", http.StatusNotFound)
		return
	}
	if markup.UserID != userID {
		http.Error(w, "Forbidden", http.StatusForbidden)
		return
	}
	db.DB.Delete(&markup)
	w.WriteHeader(http.StatusNoContent)
}
