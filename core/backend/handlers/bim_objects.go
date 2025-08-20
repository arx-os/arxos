package handlers

import (
	"arxos/db"
	"arxos/models"
	"encoding/json"
	"net/http"
	"strconv"

	"github.com/go-chi/chi/v5"
)

// ===== WALL CRUD OPERATIONS =====

// CreateWall creates a new wall
func CreateWall(w http.ResponseWriter, r *http.Request) {
	userID, err := getUserIDFromToken(r)
	if err != nil {
		http.Error(w, "Unauthorized", http.StatusUnauthorized)
		return
	}

	var wall models.Wall
	if err := json.NewDecoder(r.Body).Decode(&wall); err != nil {
		http.Error(w, "Invalid JSON", http.StatusBadRequest)
		return
	}

	// Validate required fields
	if wall.ID == "" {
		http.Error(w, "Wall ID is required", http.StatusBadRequest)
		return
	}
	if !models.IsValidObjectId(wall.ID) {
		http.Error(w, "Invalid wall ID format", http.StatusBadRequest)
		return
	}
	if wall.Name == "" {
		http.Error(w, "Wall name is required", http.StatusBadRequest)
		return
	}
	if len(wall.Geometry.Points) < 2 {
		http.Error(w, "Wall must have at least 2 points", http.StatusBadRequest)
		return
	}

	// Set metadata
	wall.CreatedBy = userID
	wall.Status = "active"

	// Validate metadata links if provided
	if wall.RoomID1 != "" || wall.RoomID2 != "" {
		valid, invalidFields := models.ValidateMetadataLinks(map[string]string{
			"room_id_1": wall.RoomID1,
			"room_id_2": wall.RoomID2,
		})
		if !valid {
			http.Error(w, "Invalid metadata links: "+strconv.Itoa(len(invalidFields)), http.StatusBadRequest)
			return
		}
	}

	// Check if wall already exists
	var existingWall models.Wall
	if err := db.DB.Where("id = ?", wall.ID).First(&existingWall).Error; err == nil {
		http.Error(w, "Wall with this ID already exists", http.StatusConflict)
		return
	}

	// Create wall
	if err := db.DB.Create(&wall).Error; err != nil {
		http.Error(w, "Database error", http.StatusInternalServerError)
		return
	}

	// Log the creation
	models.LogChange(db.DB, userID, "Wall", wall.ID, "created", wall)

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusCreated)
	json.NewEncoder(w).Encode(wall)
}

// GetWall retrieves a specific wall
func GetWall(w http.ResponseWriter, r *http.Request) {
	_, err := getUserIDFromToken(r)
	if err != nil {
		http.Error(w, "Unauthorized", http.StatusUnauthorized)
		return
	}

	wallID := chi.URLParam(r, "id")
	if wallID == "" {
		http.Error(w, "Wall ID is required", http.StatusBadRequest)
		return
	}

	var wall models.Wall
	if err := db.DB.Where("id = ?", wallID).First(&wall).Error; err != nil {
		http.Error(w, "Wall not found", http.StatusNotFound)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(wall)
}

// DeleteWall deletes a wall
func DeleteWall(w http.ResponseWriter, r *http.Request) {
	userID, err := getUserIDFromToken(r)
	if err != nil {
		http.Error(w, "Unauthorized", http.StatusUnauthorized)
		return
	}

	wallID := chi.URLParam(r, "id")
	if wallID == "" {
		http.Error(w, "Wall ID is required", http.StatusBadRequest)
		return
	}

	var wall models.Wall
	if err := db.DB.Where("id = ?", wallID).First(&wall).Error; err != nil {
		http.Error(w, "Wall not found", http.StatusNotFound)
		return
	}

	// Check if wall is locked by another user
	if wall.LockedBy != 0 && wall.LockedBy != userID {
		http.Error(w, "Wall is locked by another user", http.StatusForbidden)
		return
	}

	// Delete wall
	if err := db.DB.Delete(&wall).Error; err != nil {
		http.Error(w, "Database error", http.StatusInternalServerError)
		return
	}

	// Log the deletion
	models.LogChange(db.DB, userID, "Wall", wallID, "deleted", map[string]interface{}{
		"wall_id": wallID,
	})

	w.WriteHeader(http.StatusNoContent)
}

// ===== DOOR CRUD OPERATIONS =====

// CreateDoor creates a new door (implemented as a special type of device)
func CreateDoor(w http.ResponseWriter, r *http.Request) {
	userID, err := getUserIDFromToken(r)
	if err != nil {
		http.Error(w, "Unauthorized", http.StatusUnauthorized)
		return
	}

	var door models.Device
	if err := json.NewDecoder(r.Body).Decode(&door); err != nil {
		http.Error(w, "Invalid JSON", http.StatusBadRequest)
		return
	}

	// Validate required fields
	if door.ID == "" {
		http.Error(w, "Door ID is required", http.StatusBadRequest)
		return
	}
	if !models.IsValidObjectId(door.ID) {
		http.Error(w, "Invalid door ID format", http.StatusBadRequest)
		return
	}
	if door.Type != "door" {
		http.Error(w, "Device type must be 'door'", http.StatusBadRequest)
		return
	}
	if len(door.Geometry.Points) == 0 {
		http.Error(w, "Door must have geometry", http.StatusBadRequest)
		return
	}

	// Set metadata
	door.CreatedBy = userID
	door.Status = "active"
	door.System = "architectural"

	// Check if door already exists
	var existingDoor models.Device
	if err := db.DB.Where("id = ?", door.ID).First(&existingDoor).Error; err == nil {
		http.Error(w, "Door with this ID already exists", http.StatusConflict)
		return
	}

	// Create door
	if err := db.DB.Create(&door).Error; err != nil {
		http.Error(w, "Database error", http.StatusInternalServerError)
		return
	}

	// Log the creation
	models.LogChange(db.DB, userID, "Door", door.ID, "created", door)

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusCreated)
	json.NewEncoder(w).Encode(door)
}

// GetDoor retrieves a specific door
func GetDoor(w http.ResponseWriter, r *http.Request) {
	_, err := getUserIDFromToken(r)
	if err != nil {
		http.Error(w, "Unauthorized", http.StatusUnauthorized)
		return
	}

	doorID := chi.URLParam(r, "id")
	if doorID == "" {
		http.Error(w, "Door ID is required", http.StatusBadRequest)
		return
	}

	var door models.Device
	if err := db.DB.Where("id = ? AND type = ?", doorID, "door").First(&door).Error; err != nil {
		http.Error(w, "Door not found", http.StatusNotFound)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(door)
}

// UpdateDoor updates a door
func UpdateDoor(w http.ResponseWriter, r *http.Request) {
	userID, err := getUserIDFromToken(r)
	if err != nil {
		http.Error(w, "Unauthorized", http.StatusUnauthorized)
		return
	}

	doorID := chi.URLParam(r, "id")
	if doorID == "" {
		http.Error(w, "Door ID is required", http.StatusBadRequest)
		return
	}

	var door models.Device
	if err := db.DB.Where("id = ? AND type = ?", doorID, "door").First(&door).Error; err != nil {
		http.Error(w, "Door not found", http.StatusNotFound)
		return
	}

	// Check if door is locked by another user
	if door.LockedBy != 0 && door.LockedBy != userID {
		http.Error(w, "Door is locked by another user", http.StatusForbidden)
		return
	}

	var updateData models.Device
	if err := json.NewDecoder(r.Body).Decode(&updateData); err != nil {
		http.Error(w, "Invalid JSON", http.StatusBadRequest)
		return
	}

	// Update allowed fields
	if updateData.Type != "" {
		door.Type = updateData.Type
	}
	if len(updateData.Geometry.Points) > 0 {
		door.Geometry = updateData.Geometry
	}
	if updateData.RoomID != "" {
		door.RoomID = updateData.RoomID
	}
	if updateData.Status != "" {
		door.Status = updateData.Status
	}

	// Save changes
	if err := db.DB.Save(&door).Error; err != nil {
		http.Error(w, "Database error", http.StatusInternalServerError)
		return
	}

	// Log the update
	models.LogChange(db.DB, userID, "Door", doorID, "updated", updateData)

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(door)
}

// DeleteDoor deletes a door
func DeleteDoor(w http.ResponseWriter, r *http.Request) {
	userID, err := getUserIDFromToken(r)
	if err != nil {
		http.Error(w, "Unauthorized", http.StatusUnauthorized)
		return
	}

	doorID := chi.URLParam(r, "id")
	if doorID == "" {
		http.Error(w, "Door ID is required", http.StatusBadRequest)
		return
	}

	var door models.Device
	if err := db.DB.Where("id = ? AND type = ?", doorID, "door").First(&door).Error; err != nil {
		http.Error(w, "Door not found", http.StatusNotFound)
		return
	}

	// Check if door is locked by another user
	if door.LockedBy != 0 && door.LockedBy != userID {
		http.Error(w, "Door is locked by another user", http.StatusForbidden)
		return
	}

	// Delete door
	if err := db.DB.Delete(&door).Error; err != nil {
		http.Error(w, "Database error", http.StatusInternalServerError)
		return
	}

	// Log the deletion
	models.LogChange(db.DB, userID, "Door", doorID, "deleted", map[string]interface{}{
		"door_id": doorID,
	})

	w.WriteHeader(http.StatusNoContent)
}

// ===== WINDOW CRUD OPERATIONS =====

// CreateWindow creates a new window (implemented as a special type of device)
func CreateWindow(w http.ResponseWriter, r *http.Request) {
	userID, err := getUserIDFromToken(r)
	if err != nil {
		http.Error(w, "Unauthorized", http.StatusUnauthorized)
		return
	}

	var window models.Device
	if err := json.NewDecoder(r.Body).Decode(&window); err != nil {
		http.Error(w, "Invalid JSON", http.StatusBadRequest)
		return
	}

	// Validate required fields
	if window.ID == "" {
		http.Error(w, "Window ID is required", http.StatusBadRequest)
		return
	}
	if !models.IsValidObjectId(window.ID) {
		http.Error(w, "Invalid window ID format", http.StatusBadRequest)
		return
	}
	if window.Type != "window" {
		http.Error(w, "Device type must be 'window'", http.StatusBadRequest)
		return
	}
	if len(window.Geometry.Points) == 0 {
		http.Error(w, "Window must have geometry", http.StatusBadRequest)
		return
	}

	// Set metadata
	window.CreatedBy = userID
	window.Status = "active"
	window.System = "architectural"

	// Check if window already exists
	var existingWindow models.Device
	if err := db.DB.Where("id = ?", window.ID).First(&existingWindow).Error; err == nil {
		http.Error(w, "Window with this ID already exists", http.StatusConflict)
		return
	}

	// Create window
	if err := db.DB.Create(&window).Error; err != nil {
		http.Error(w, "Database error", http.StatusInternalServerError)
		return
	}

	// Log the creation
	models.LogChange(db.DB, userID, "Window", window.ID, "created", window)

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusCreated)
	json.NewEncoder(w).Encode(window)
}

// GetWindow retrieves a specific window
func GetWindow(w http.ResponseWriter, r *http.Request) {
	_, err := getUserIDFromToken(r)
	if err != nil {
		http.Error(w, "Unauthorized", http.StatusUnauthorized)
		return
	}

	windowID := chi.URLParam(r, "id")
	if windowID == "" {
		http.Error(w, "Window ID is required", http.StatusBadRequest)
		return
	}

	var window models.Device
	if err := db.DB.Where("id = ? AND type = ?", windowID, "window").First(&window).Error; err != nil {
		http.Error(w, "Window not found", http.StatusNotFound)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(window)
}

// UpdateWindow updates a window
func UpdateWindow(w http.ResponseWriter, r *http.Request) {
	userID, err := getUserIDFromToken(r)
	if err != nil {
		http.Error(w, "Unauthorized", http.StatusUnauthorized)
		return
	}

	windowID := chi.URLParam(r, "id")
	if windowID == "" {
		http.Error(w, "Window ID is required", http.StatusBadRequest)
		return
	}

	var window models.Device
	if err := db.DB.Where("id = ? AND type = ?", windowID, "window").First(&window).Error; err != nil {
		http.Error(w, "Window not found", http.StatusNotFound)
		return
	}

	// Check if window is locked by another user
	if window.LockedBy != 0 && window.LockedBy != userID {
		http.Error(w, "Window is locked by another user", http.StatusForbidden)
		return
	}

	var updateData models.Device
	if err := json.NewDecoder(r.Body).Decode(&updateData); err != nil {
		http.Error(w, "Invalid JSON", http.StatusBadRequest)
		return
	}

	// Update allowed fields
	if updateData.Type != "" {
		window.Type = updateData.Type
	}
	if len(updateData.Geometry.Points) > 0 {
		window.Geometry = updateData.Geometry
	}
	if updateData.RoomID != "" {
		window.RoomID = updateData.RoomID
	}
	if updateData.Status != "" {
		window.Status = updateData.Status
	}

	// Save changes
	if err := db.DB.Save(&window).Error; err != nil {
		http.Error(w, "Database error", http.StatusInternalServerError)
		return
	}

	// Log the update
	models.LogChange(db.DB, userID, "Window", windowID, "updated", updateData)

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(window)
}

// DeleteWindow deletes a window
func DeleteWindow(w http.ResponseWriter, r *http.Request) {
	userID, err := getUserIDFromToken(r)
	if err != nil {
		http.Error(w, "Unauthorized", http.StatusUnauthorized)
		return
	}

	windowID := chi.URLParam(r, "id")
	if windowID == "" {
		http.Error(w, "Window ID is required", http.StatusBadRequest)
		return
	}

	var window models.Device
	if err := db.DB.Where("id = ? AND type = ?", windowID, "window").First(&window).Error; err != nil {
		http.Error(w, "Window not found", http.StatusNotFound)
		return
	}

	// Check if window is locked by another user
	if window.LockedBy != 0 && window.LockedBy != userID {
		http.Error(w, "Window is locked by another user", http.StatusForbidden)
		return
	}

	// Delete window
	if err := db.DB.Delete(&window).Error; err != nil {
		http.Error(w, "Database error", http.StatusInternalServerError)
		return
	}

	// Log the deletion
	models.LogChange(db.DB, userID, "Window", windowID, "deleted", map[string]interface{}{
		"window_id": windowID,
	})

	w.WriteHeader(http.StatusNoContent)
}

// ===== LIST OPERATIONS =====

// ListDoors returns all doors with pagination
func ListDoors(w http.ResponseWriter, r *http.Request) {
	_, err := getUserIDFromToken(r)
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
	query := db.DB.Model(&models.Device{}).Where("type = ?", "door")
	query.Count(&total)

	var doors []models.Device
	query.Offset(offset).Limit(pageSize).Find(&doors)

	resp := map[string]interface{}{
		"results":     doors,
		"page":        page,
		"page_size":   pageSize,
		"total":       total,
		"total_pages": (total + int64(pageSize) - 1) / int64(pageSize),
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(resp)
}

// ListWindows returns all windows with pagination
func ListWindows(w http.ResponseWriter, r *http.Request) {
	_, err := getUserIDFromToken(r)
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
	query := db.DB.Model(&models.Device{}).Where("type = ?", "window")
	query.Count(&total)

	var windows []models.Device
	query.Offset(offset).Limit(pageSize).Find(&windows)

	resp := map[string]interface{}{
		"results":     windows,
		"page":        page,
		"page_size":   pageSize,
		"total":       total,
		"total_pages": (total + int64(pageSize) - 1) / int64(pageSize),
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(resp)
}

// ===== ROOM CRUD OPERATIONS =====

// CreateRoom creates a new room
func CreateRoom(w http.ResponseWriter, r *http.Request) {
	userID, err := getUserIDFromToken(r)
	if err != nil {
		http.Error(w, "Unauthorized", http.StatusUnauthorized)
		return
	}

	var room models.Room
	if err := json.NewDecoder(r.Body).Decode(&room); err != nil {
		http.Error(w, "Invalid JSON", http.StatusBadRequest)
		return
	}

	// Validate required fields
	if room.ID == "" {
		http.Error(w, "Room ID is required", http.StatusBadRequest)
		return
	}
	if !models.IsValidObjectId(room.ID) {
		http.Error(w, "Invalid room ID format", http.StatusBadRequest)
		return
	}
	if room.Name == "" {
		http.Error(w, "Room name is required", http.StatusBadRequest)
		return
	}
	if len(room.Geometry.Points) < 3 {
		http.Error(w, "Room must have at least 3 points", http.StatusBadRequest)
		return
	}

	// Set metadata
	room.CreatedBy = userID
	room.Status = "active"

	// Check if room already exists
	var existingRoom models.Room
	if err := db.DB.Where("id = ?", room.ID).First(&existingRoom).Error; err == nil {
		http.Error(w, "Room with this ID already exists", http.StatusConflict)
		return
	}

	// Create room
	if err := db.DB.Create(&room).Error; err != nil {
		http.Error(w, "Database error", http.StatusInternalServerError)
		return
	}

	// Log the creation
	models.LogChange(db.DB, userID, "Room", room.ID, "created", room)

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusCreated)
	json.NewEncoder(w).Encode(room)
}

// GetRoom retrieves a specific room
func GetRoom(w http.ResponseWriter, r *http.Request) {
	_, err := getUserIDFromToken(r)
	if err != nil {
		http.Error(w, "Unauthorized", http.StatusUnauthorized)
		return
	}

	roomID := chi.URLParam(r, "id")
	if roomID == "" {
		http.Error(w, "Room ID is required", http.StatusBadRequest)
		return
	}

	var room models.Room
	if err := db.DB.Where("id = ?", roomID).First(&room).Error; err != nil {
		http.Error(w, "Room not found", http.StatusNotFound)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(room)
}

// DeleteRoom deletes a room
func DeleteRoom(w http.ResponseWriter, r *http.Request) {
	userID, err := getUserIDFromToken(r)
	if err != nil {
		http.Error(w, "Unauthorized", http.StatusUnauthorized)
		return
	}

	roomID := chi.URLParam(r, "id")
	if roomID == "" {
		http.Error(w, "Room ID is required", http.StatusBadRequest)
		return
	}

	var room models.Room
	if err := db.DB.Where("id = ?", roomID).First(&room).Error; err != nil {
		http.Error(w, "Room not found", http.StatusNotFound)
		return
	}

	// Check if room is locked by another user
	if room.LockedBy != 0 && room.LockedBy != userID {
		http.Error(w, "Room is locked by another user", http.StatusForbidden)
		return
	}

	// Delete room
	if err := db.DB.Delete(&room).Error; err != nil {
		http.Error(w, "Database error", http.StatusInternalServerError)
		return
	}

	// Log the deletion
	models.LogChange(db.DB, userID, "Room", roomID, "deleted", map[string]interface{}{
		"room_id": roomID,
	})

	w.WriteHeader(http.StatusNoContent)
}

// ===== DEVICE CRUD OPERATIONS =====

// CreateDevice creates a new device
func CreateDevice(w http.ResponseWriter, r *http.Request) {
	userID, err := getUserIDFromToken(r)
	if err != nil {
		http.Error(w, "Unauthorized", http.StatusUnauthorized)
		return
	}

	var device models.Device
	if err := json.NewDecoder(r.Body).Decode(&device); err != nil {
		http.Error(w, "Invalid JSON", http.StatusBadRequest)
		return
	}

	// Validate required fields
	if device.ID == "" {
		http.Error(w, "Device ID is required", http.StatusBadRequest)
		return
	}
	if !models.IsValidObjectId(device.ID) {
		http.Error(w, "Invalid device ID format", http.StatusBadRequest)
		return
	}
	if device.Type == "" {
		http.Error(w, "Device type is required", http.StatusBadRequest)
		return
	}
	if len(device.Geometry.Points) == 0 {
		http.Error(w, "Device must have geometry", http.StatusBadRequest)
		return
	}

	// Set metadata
	device.CreatedBy = userID
	device.Status = "active"

	// Validate metadata links if provided
	if device.PanelID != "" || device.CircuitID != "" || device.UpstreamID != "" || device.DownstreamID != "" {
		valid, _ := models.ValidateMetadataLinks(map[string]string{
			"panel_id":      device.PanelID,
			"circuit_id":    device.CircuitID,
			"upstream_id":   device.UpstreamID,
			"downstream_id": device.DownstreamID,
		})
		if !valid {
			http.Error(w, "Invalid metadata links", http.StatusBadRequest)
			return
		}
	}

	// Check if device already exists
	var existingDevice models.Device
	if err := db.DB.Where("id = ?", device.ID).First(&existingDevice).Error; err == nil {
		http.Error(w, "Device with this ID already exists", http.StatusConflict)
		return
	}

	// Create device
	if err := db.DB.Create(&device).Error; err != nil {
		http.Error(w, "Database error", http.StatusInternalServerError)
		return
	}

	// Log the creation
	models.LogChange(db.DB, userID, "Device", device.ID, "created", device)

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusCreated)
	json.NewEncoder(w).Encode(device)
}

// DeleteDevice deletes a device
func DeleteDevice(w http.ResponseWriter, r *http.Request) {
	userID, err := getUserIDFromToken(r)
	if err != nil {
		http.Error(w, "Unauthorized", http.StatusUnauthorized)
		return
	}

	deviceID := chi.URLParam(r, "id")
	if deviceID == "" {
		http.Error(w, "Device ID is required", http.StatusBadRequest)
		return
	}

	var device models.Device
	if err := db.DB.Where("id = ?", deviceID).First(&device).Error; err != nil {
		http.Error(w, "Device not found", http.StatusNotFound)
		return
	}

	// Check if device is locked by another user
	if device.LockedBy != 0 && device.LockedBy != userID {
		http.Error(w, "Device is locked by another user", http.StatusForbidden)
		return
	}

	// Delete device
	if err := db.DB.Delete(&device).Error; err != nil {
		http.Error(w, "Database error", http.StatusInternalServerError)
		return
	}

	// Log the deletion
	models.LogChange(db.DB, userID, "Device", deviceID, "deleted", map[string]interface{}{
		"device_id": deviceID,
	})

	w.WriteHeader(http.StatusNoContent)
}

// ===== LABEL CRUD OPERATIONS =====

// CreateLabel creates a new label
func CreateLabel(w http.ResponseWriter, r *http.Request) {
	userID, err := getUserIDFromToken(r)
	if err != nil {
		http.Error(w, "Unauthorized", http.StatusUnauthorized)
		return
	}

	var label models.Label
	if err := json.NewDecoder(r.Body).Decode(&label); err != nil {
		http.Error(w, "Invalid JSON", http.StatusBadRequest)
		return
	}

	// Validate required fields
	if label.ID == "" {
		http.Error(w, "Label ID is required", http.StatusBadRequest)
		return
	}
	if !models.IsValidObjectId(label.ID) {
		http.Error(w, "Invalid label ID format", http.StatusBadRequest)
		return
	}
	if label.Text == "" {
		http.Error(w, "Label text is required", http.StatusBadRequest)
		return
	}
	if len(label.Geometry.Points) == 0 {
		http.Error(w, "Label must have geometry", http.StatusBadRequest)
		return
	}

	// Set metadata
	label.CreatedBy = userID
	label.Status = "active"

	// Validate metadata links if provided
	if label.UpstreamID != "" || label.DownstreamID != "" {
		valid, _ := models.ValidateMetadataLinks(map[string]string{
			"upstream_id":   label.UpstreamID,
			"downstream_id": label.DownstreamID,
		})
		if !valid {
			http.Error(w, "Invalid metadata links", http.StatusBadRequest)
			return
		}
	}

	// Check if label already exists
	var existingLabel models.Label
	if err := db.DB.Where("id = ?", label.ID).First(&existingLabel).Error; err == nil {
		http.Error(w, "Label with this ID already exists", http.StatusConflict)
		return
	}

	// Create label
	if err := db.DB.Create(&label).Error; err != nil {
		http.Error(w, "Database error", http.StatusInternalServerError)
		return
	}

	// Log the creation
	models.LogChange(db.DB, userID, "Label", label.ID, "created", label)

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusCreated)
	json.NewEncoder(w).Encode(label)
}

// GetLabel retrieves a specific label
func GetLabel(w http.ResponseWriter, r *http.Request) {
	_, err := getUserIDFromToken(r)
	if err != nil {
		http.Error(w, "Unauthorized", http.StatusUnauthorized)
		return
	}

	labelID := chi.URLParam(r, "id")
	if labelID == "" {
		http.Error(w, "Label ID is required", http.StatusBadRequest)
		return
	}

	var label models.Label
	if err := db.DB.Where("id = ?", labelID).First(&label).Error; err != nil {
		http.Error(w, "Label not found", http.StatusNotFound)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(label)
}

// DeleteLabel deletes a label
func DeleteLabel(w http.ResponseWriter, r *http.Request) {
	userID, err := getUserIDFromToken(r)
	if err != nil {
		http.Error(w, "Unauthorized", http.StatusUnauthorized)
		return
	}

	labelID := chi.URLParam(r, "id")
	if labelID == "" {
		http.Error(w, "Label ID is required", http.StatusBadRequest)
		return
	}

	var label models.Label
	if err := db.DB.Where("id = ?", labelID).First(&label).Error; err != nil {
		http.Error(w, "Label not found", http.StatusNotFound)
		return
	}

	// Check if label is locked by another user
	if label.LockedBy != 0 && label.LockedBy != userID {
		http.Error(w, "Label is locked by another user", http.StatusForbidden)
		return
	}

	// Delete label
	if err := db.DB.Delete(&label).Error; err != nil {
		http.Error(w, "Database error", http.StatusInternalServerError)
		return
	}

	// Log the deletion
	models.LogChange(db.DB, userID, "Label", labelID, "deleted", map[string]interface{}{
		"label_id": labelID,
	})

	w.WriteHeader(http.StatusNoContent)
}

// ===== ZONE CRUD OPERATIONS =====

// CreateZone creates a new zone
func CreateZone(w http.ResponseWriter, r *http.Request) {
	userID, err := getUserIDFromToken(r)
	if err != nil {
		http.Error(w, "Unauthorized", http.StatusUnauthorized)
		return
	}

	var zone models.Zone
	if err := json.NewDecoder(r.Body).Decode(&zone); err != nil {
		http.Error(w, "Invalid JSON", http.StatusBadRequest)
		return
	}

	// Validate required fields
	if zone.ID == "" {
		http.Error(w, "Zone ID is required", http.StatusBadRequest)
		return
	}
	if !models.IsValidObjectId(zone.ID) {
		http.Error(w, "Invalid zone ID format", http.StatusBadRequest)
		return
	}
	if zone.Name == "" {
		http.Error(w, "Zone name is required", http.StatusBadRequest)
		return
	}
	if len(zone.Geometry.Points) < 3 {
		http.Error(w, "Zone must have at least 3 points", http.StatusBadRequest)
		return
	}

	// Set metadata
	zone.CreatedBy = userID
	zone.Status = "active"

	// Validate metadata links if provided
	if zone.UpstreamID != "" || zone.DownstreamID != "" {
		valid, _ := models.ValidateMetadataLinks(map[string]string{
			"upstream_id":   zone.UpstreamID,
			"downstream_id": zone.DownstreamID,
		})
		if !valid {
			http.Error(w, "Invalid metadata links", http.StatusBadRequest)
			return
		}
	}

	// Check if zone already exists
	var existingZone models.Zone
	if err := db.DB.Where("id = ?", zone.ID).First(&existingZone).Error; err == nil {
		http.Error(w, "Zone with this ID already exists", http.StatusConflict)
		return
	}

	// Create zone
	if err := db.DB.Create(&zone).Error; err != nil {
		http.Error(w, "Database error", http.StatusInternalServerError)
		return
	}

	// Log the creation
	models.LogChange(db.DB, userID, "Zone", zone.ID, "created", zone)

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusCreated)
	json.NewEncoder(w).Encode(zone)
}

// GetZone retrieves a specific zone
func GetZone(w http.ResponseWriter, r *http.Request) {
	_, err := getUserIDFromToken(r)
	if err != nil {
		http.Error(w, "Unauthorized", http.StatusUnauthorized)
		return
	}

	zoneID := chi.URLParam(r, "id")
	if zoneID == "" {
		http.Error(w, "Zone ID is required", http.StatusBadRequest)
		return
	}

	var zone models.Zone
	if err := db.DB.Where("id = ?", zoneID).First(&zone).Error; err != nil {
		http.Error(w, "Zone not found", http.StatusNotFound)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(zone)
}

// DeleteZone deletes a zone
func DeleteZone(w http.ResponseWriter, r *http.Request) {
	userID, err := getUserIDFromToken(r)
	if err != nil {
		http.Error(w, "Unauthorized", http.StatusUnauthorized)
		return
	}

	zoneID := chi.URLParam(r, "id")
	if zoneID == "" {
		http.Error(w, "Zone ID is required", http.StatusBadRequest)
		return
	}

	var zone models.Zone
	if err := db.DB.Where("id = ?", zoneID).First(&zone).Error; err != nil {
		http.Error(w, "Zone not found", http.StatusNotFound)
		return
	}

	// Check if zone is locked by another user
	if zone.LockedBy != 0 && zone.LockedBy != userID {
		http.Error(w, "Zone is locked by another user", http.StatusForbidden)
		return
	}

	// Delete zone
	if err := db.DB.Delete(&zone).Error; err != nil {
		http.Error(w, "Database error", http.StatusInternalServerError)
		return
	}

	// Log the deletion
	models.LogChange(db.DB, userID, "Zone", zoneID, "deleted", map[string]interface{}{
		"zone_id": zoneID,
	})

	w.WriteHeader(http.StatusNoContent)
}
