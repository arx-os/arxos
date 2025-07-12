// handlers/drawings.go
package handlers

import (
	"encoding/json"
	"net/http"
	"strconv"

	"arx/db"
	"arx/models"
	"os"

	"html/template"

	"bytes"
	"log"

	"fmt"

	"strings"

	"encoding/xml"
	"io"

	"github.com/go-chi/chi/v5"
)

// ElementInfo represents a parsed SVG element with its key attributes
type ElementInfo struct {
	Tag      string
	ID       string
	DataName string
	Attrs    map[string]string
}

func extractProjectID(r *http.Request) (uint, error) {
	projectIDStr := chi.URLParam(r, "projectID")
	if projectIDStr == "" {
		// Try to get from body if not in URL
		var body struct {
			ProjectID uint `json:"project_id"`
		}
		if err := json.NewDecoder(r.Body).Decode(&body); err == nil && body.ProjectID != 0 {
			return body.ProjectID, nil
		}
		return 0, http.ErrNoCookie
	}
	projectID, err := strconv.Atoi(projectIDStr)
	if err != nil {
		return 0, err
	}
	return uint(projectID), nil
}

func ListDrawings(w http.ResponseWriter, r *http.Request) {
	projectID, err := extractProjectID(r)
	if err != nil {
		http.Error(w, "Invalid project ID", http.StatusBadRequest)
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
	query := db.DB.Model(&models.Drawing{}).Where("project_id = ?", projectID)
	query.Count(&total)

	var drawings []models.Drawing
	query.Offset(offset).Limit(pageSize).Find(&drawings)

	resp := map[string]interface{}{
		"results":     drawings,
		"page":        page,
		"page_size":   pageSize,
		"total":       total,
		"total_pages": (total + int64(pageSize) - 1) / int64(pageSize),
	}
	json.NewEncoder(w).Encode(resp)
}

func CreateDrawing(w http.ResponseWriter, r *http.Request) {
	_, err := GetUserFromRequest(r)
	if err != nil {
		http.Error(w, "Unauthorized", http.StatusUnauthorized)
		return
	}

	projectID, err := extractProjectID(r)
	if err != nil {
		http.Error(w, "Invalid project ID", http.StatusBadRequest)
		return
	}

	var drawing models.Drawing
	if err := json.NewDecoder(r.Body).Decode(&drawing); err != nil {
		http.Error(w, "Invalid body", http.StatusBadRequest)
		return
	}
	drawing.ProjectID = projectID
	db.DB.Create(&drawing)
	json.NewEncoder(w).Encode(drawing)
}

func GetDrawing(w http.ResponseWriter, r *http.Request) {
	drawingIDStr := chi.URLParam(r, "drawingID")
	drawingID, err := strconv.Atoi(drawingIDStr)
	if err != nil {
		http.Error(w, "Invalid drawing ID", http.StatusBadRequest)
		return
	}

	projectID, err := extractProjectID(r)
	if err != nil {
		http.Error(w, "Invalid project ID", http.StatusBadRequest)
		return
	}

	var drawing models.Drawing
	if err := db.DB.Where("id = ? AND project_id = ?", drawingID, projectID).First(&drawing).Error; err != nil {
		http.Error(w, "Drawing not found", http.StatusNotFound)
		return
	}
	json.NewEncoder(w).Encode(drawing)
}

// GetDrawingLastModified returns the last modified timestamp for a Drawing
func GetDrawingLastModified(w http.ResponseWriter, r *http.Request) {
	drawingIDStr := chi.URLParam(r, "drawingID")
	drawingID, err := strconv.Atoi(drawingIDStr)
	if err != nil {
		http.Error(w, "Invalid drawing ID", http.StatusBadRequest)
		return
	}

	var drawing models.Drawing
	if err := db.DB.First(&drawing, drawingID).Error; err != nil {
		http.Error(w, "Drawing not found", http.StatusNotFound)
		return
	}

	response := struct {
		LastModified string `json:"last_modified"`
	}{
		LastModified: drawing.UpdatedAt.UTC().Format("2006-01-02T15:04:05Z07:00"),
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(response)
}

// ServeFloorSVG returns the SVG markup for the requested floor, with data-object-id attributes.
func ServeFloorSVG(w http.ResponseWriter, r *http.Request) {
	projectID, err := extractProjectID(r)
	if err != nil {
		http.Error(w, "Invalid project ID", http.StatusBadRequest)
		return
	}
	floorIDStr := r.URL.Query().Get("floor")
	if floorIDStr == "" {
		http.Error(w, "Missing floor ID", http.StatusBadRequest)
		return
	}
	var floor models.Floor
	if err := db.DB.Where("id = ? AND project_id = ?", floorIDStr, projectID).First(&floor).Error; err != nil {
		http.Error(w, "Floor not found", http.StatusNotFound)
		return
	}
	// Try to read SVG from file path if exists
	svgContent := ""
	var drawingID *uint = nil
	if floor.SVGPath != "" {
		data, err := os.ReadFile(floor.SVGPath)
		if err == nil {
			svgContent = string(data)
		}
	}
	if svgContent == "" {
		// Try to fetch from Drawing if SVGPath is empty or file not found
		var drawing models.Drawing
		if err := db.DB.Where("name = ? AND project_id = ?", floor.Name, projectID).First(&drawing).Error; err == nil {
			svgContent = drawing.SVG
			drawingID = &drawing.ID
		}
	}
	if svgContent == "" {
		svgContent = "<svg><!-- SVG not found --></svg>"
	}
	w.Header().Set("Content-Type", "application/json")
	response := struct {
		SVG       string `json:"svg"`
		DrawingID *uint  `json:"drawing_id"`
	}{
		SVG:       svgContent,
		DrawingID: drawingID,
	}
	json.NewEncoder(w).Encode(response)
}

// ServeObjectInfo returns HTML/HTMX partial with object info and comments, using Go templates.
func ServeObjectInfo(w http.ResponseWriter, r *http.Request) {
	objectID := chi.URLParam(r, "objectId")
	var svgObject models.SVGObject
	projectID, err := extractProjectID(r)
	if err != nil {
		http.Error(w, "Invalid project ID", http.StatusBadRequest)
		return
	}
	if err := db.DB.Where("id = ? AND project_id = ?", objectID, projectID).First(&svgObject).Error; err != nil {
		http.Error(w, "Object not found", http.StatusNotFound)
		return
	}
	var comments []models.Comment
	db.DB.Where("svg_object_id = ?", svgObject.ID).Order("created_at asc").Find(&comments)

	tmpl := template.Must(template.New("objectInfo").Parse(`
	<div id="object-comments">
		<h4>Object Info</h4>
		<div>ID: {{.Object.ObjectID}}<br>Type: {{.Object.Type}}<br>Label: {{.Object.Label}}</div>
		<h5>Comments</h5>
		<ul>
		{{range .Comments}}
			<li>{{.Content}}</li>
		{{else}}
			<li>No comments yet.</li>
		{{end}}
		</ul>
		<div id="comments-spinner" class="flex justify-center my-4 hidden">
			<svg class="animate-spin h-6 w-6 text-blue-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
				<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
				<path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z"></path>
			</svg>
		</div>
		<form class="bg-white p-4 rounded shadow flex flex-col gap-2"
			  hx-post="/api/object/{{.Object.ObjectID}}/comment"
			  hx-target="#object-comments"
			  hx-swap="outerHTML"
			  hx-indicator="#comments-spinner">
			<textarea name="comment" required></textarea>
			<button type="submit">Add Comment</button>
		</form>
	</div>
	`))
	w.Header().Set("Content-Type", "text/html")
	tmpl.Execute(w, map[string]interface{}{
		"Object":   svgObject,
		"Comments": comments,
	})
}

// PostObjectComment accepts a new comment and returns updated object info/comments partial.
func PostObjectComment(w http.ResponseWriter, r *http.Request) {
	objectID := chi.URLParam(r, "objectId")
	var svgObject models.SVGObject
	projectID, err := extractProjectID(r)
	if err != nil {
		http.Error(w, "Invalid project ID", http.StatusBadRequest)
		return
	}
	if err := db.DB.Where("id = ? AND project_id = ?", objectID, projectID).First(&svgObject).Error; err != nil {
		http.Error(w, "Object not found", http.StatusNotFound)
		return
	}
	if err := r.ParseForm(); err != nil {
		http.Error(w, "Invalid form", http.StatusBadRequest)
		return
	}
	commentText := r.FormValue("comment")
	user, err := GetUserFromRequest(r)
	if err != nil {
		http.Error(w, "Unauthorized", http.StatusUnauthorized)
		return
	}
	comment := models.Comment{
		SVGObjectID: svgObject.ID,
		UserID:      user.ID,
		Content:     commentText,
	}
	db.DB.Create(&comment)
	// Return updated comments partial
	ServeObjectInfo(w, r)
}

// EditComment allows a user to edit their own comment
func EditComment(w http.ResponseWriter, r *http.Request) {
	user, err := GetUserFromRequest(r)
	if err != nil {
		http.Error(w, "Unauthorized", http.StatusUnauthorized)
		return
	}
	commentID := chi.URLParam(r, "id")
	var comment models.Comment
	projectID, err := extractProjectID(r)
	if err != nil {
		http.Error(w, "Invalid project ID", http.StatusBadRequest)
		return
	}
	if err := db.DB.Where("id = ? AND project_id = ?", commentID, projectID).First(&comment).Error; err != nil {
		http.Error(w, "Comment not found", http.StatusNotFound)
		return
	}
	if comment.UserID != user.ID {
		http.Error(w, "Forbidden", http.StatusForbidden)
		return
	}
	if err := r.ParseForm(); err != nil {
		http.Error(w, "Invalid form", http.StatusBadRequest)
		return
	}
	newContent := r.FormValue("content")
	if newContent == "" {
		http.Error(w, "Content required", http.StatusBadRequest)
		return
	}
	comment.Content = newContent
	db.DB.Save(&comment)
	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(comment)
}

// DeleteComment allows a user to delete their own comment
func DeleteComment(w http.ResponseWriter, r *http.Request) {
	user, err := GetUserFromRequest(r)
	if err != nil {
		http.Error(w, "Unauthorized", http.StatusUnauthorized)
		return
	}
	commentID := chi.URLParam(r, "id")
	var comment models.Comment
	projectID, err := extractProjectID(r)
	if err != nil {
		http.Error(w, "Invalid project ID", http.StatusBadRequest)
		return
	}
	if err := db.DB.Where("id = ? AND project_id = ?", commentID, projectID).First(&comment).Error; err != nil {
		http.Error(w, "Comment not found", http.StatusNotFound)
		return
	}
	if comment.UserID != user.ID {
		http.Error(w, "Forbidden", http.StatusForbidden)
		return
	}
	db.DB.Delete(&comment)
	w.WriteHeader(http.StatusNoContent)
}

// BIMModelHandler receives BIMModel JSON and stores parsed objects
func UploadBIMModel(w http.ResponseWriter, r *http.Request) {
	user, err := GetUserFromRequest(r)
	if err != nil {
		http.Error(w, "Unauthorized", http.StatusUnauthorized)
		return
	}

	var bimModel models.BIMModel
	if err := json.NewDecoder(r.Body).Decode(&bimModel); err != nil {
		http.Error(w, "Invalid BIMModel JSON", http.StatusBadRequest)
		return
	}

	sourceSVG := r.URL.Query().Get("source_svg")
	layer := r.URL.Query().Get("layer")

	roomIDMap := make(map[string]bool)
	for i, room := range bimModel.Rooms {
		if !models.IsValidObjectId(room.ID) {
			http.Error(w, "Invalid room ID format in BIMModel", http.StatusBadRequest)
			return
		}
		roomIDMap[room.ID] = true
		bimModel.Rooms[i].SourceSVG = sourceSVG
		bimModel.Rooms[i].Layer = layer
		bimModel.Rooms[i].CreatedBy = user.ID
		bimModel.Rooms[i].Status = "draft"
		bimModel.Rooms[i].LockedBy = 0
		bimModel.Rooms[i].AssignedTo = 0
		if bimModel.Rooms[i].SVGID == "" && room.SVGID != "" {
			bimModel.Rooms[i].SVGID = room.SVGID
		}
		for j := range room.Devices {
			if !models.IsValidObjectId(room.Devices[j].ID) {
				http.Error(w, "Invalid device ID format in BIMModel", http.StatusBadRequest)
				return
			}
			bimModel.Rooms[i].Devices[j].RoomID = room.ID
			bimModel.Rooms[i].Devices[j].SourceSVG = sourceSVG
			bimModel.Rooms[i].Devices[j].Layer = layer
			bimModel.Rooms[i].Devices[j].CreatedBy = user.ID
			bimModel.Rooms[i].Devices[j].Status = "draft"
			bimModel.Rooms[i].Devices[j].LockedBy = 0
			bimModel.Rooms[i].Devices[j].AssignedTo = 0
			if bimModel.Rooms[i].Devices[j].SVGID == "" && room.Devices[j].SVGID != "" {
				bimModel.Rooms[i].Devices[j].SVGID = room.Devices[j].SVGID
			}
			valid, invalidFields := models.ValidateMetadataLinks(map[string]string{
				"panel_id":      bimModel.Rooms[i].Devices[j].PanelID,
				"circuit_id":    bimModel.Rooms[i].Devices[j].CircuitID,
				"upstream_id":   bimModel.Rooms[i].Devices[j].UpstreamID,
				"downstream_id": bimModel.Rooms[i].Devices[j].DownstreamID,
				"pipe_id":       bimModel.Rooms[i].Devices[j].PipeID,
			})
			if !valid {
				http.Error(w, "Invalid metadata link field(s) in BIMModel device: "+strings.Join(invalidFields, ", "), http.StatusBadRequest)
				_ = models.LogChange(db.DB, user.ID, "Device", bimModel.Rooms[i].Devices[j].ID, "validation_failed", map[string]interface{}{
					"error":          "Invalid metadata link field(s) in BIMModel device: " + strings.Join(invalidFields, ", "),
					"invalid_fields": invalidFields,
					"device":         bimModel.Rooms[i].Devices[j],
				})
				return
			}
		}
	}
	for i := range bimModel.Labels {
		if !models.IsValidObjectId(bimModel.Labels[i].ID) {
			http.Error(w, "Invalid label ID format in BIMModel", http.StatusBadRequest)
			return
		}
		bimModel.Labels[i].SourceSVG = sourceSVG
		bimModel.Labels[i].Layer = layer
		bimModel.Labels[i].CreatedBy = user.ID
		bimModel.Labels[i].Status = "draft"
		bimModel.Labels[i].LockedBy = 0
		bimModel.Labels[i].AssignedTo = 0
		if bimModel.Labels[i].SVGID == "" {
			bimModel.Labels[i].SVGID = bimModel.Labels[i].ID
		}
		valid, invalidFields := models.ValidateMetadataLinks(map[string]string{
			"upstream_id":   bimModel.Labels[i].UpstreamID,
			"downstream_id": bimModel.Labels[i].DownstreamID,
		})
		if !valid {
			http.Error(w, "Invalid metadata link field(s) in BIMModel label: "+strings.Join(invalidFields, ", "), http.StatusBadRequest)
			_ = models.LogChange(db.DB, user.ID, "Label", bimModel.Labels[i].ID, "validation_failed", map[string]interface{}{
				"error":          "Invalid metadata link field(s) in BIMModel label: " + strings.Join(invalidFields, ", "),
				"invalid_fields": invalidFields,
				"label":          bimModel.Labels[i],
			})
			return
		}
	}
	for i := range bimModel.Zones {
		if !models.IsValidObjectId(bimModel.Zones[i].ID) {
			http.Error(w, "Invalid zone ID format in BIMModel", http.StatusBadRequest)
			return
		}
		bimModel.Zones[i].SourceSVG = sourceSVG
		bimModel.Zones[i].Layer = layer
		bimModel.Zones[i].CreatedBy = user.ID
		bimModel.Zones[i].Status = "draft"
		bimModel.Zones[i].LockedBy = 0
		bimModel.Zones[i].AssignedTo = 0
		if bimModel.Zones[i].SVGID == "" {
			bimModel.Zones[i].SVGID = bimModel.Zones[i].ID
		}
	}

	var allDevices []models.Device
	for _, room := range bimModel.Rooms {
		allDevices = append(allDevices, room.Devices...)
	}
	if len(bimModel.Labels) > 0 {
		db.DB.Create(&bimModel.Labels)
	}
	if len(bimModel.Zones) > 0 {
		db.DB.Create(&bimModel.Zones)
	}
	w.WriteHeader(http.StatusCreated)
	json.NewEncoder(w).Encode(map[string]string{"status": "BIMModel received and stored"})

	// Webhook/notification support
	webhookURL := os.Getenv("BIM_WEBHOOK_URL")
	if webhookURL != "" {
		totalObjects := len(bimModel.Labels) + len(bimModel.Zones)
		payload := map[string]interface{}{
			"event":      "bim_imported",
			"count":      totalObjects,
			"source_svg": sourceSVG,
		}
		go func() {
			buf := new(bytes.Buffer)
			json.NewEncoder(buf).Encode(payload)
			resp, err := http.Post(webhookURL, "application/json", buf)
			if err != nil {
				log.Printf("[Webhook] Failed to notify: %v", err)
				return
			}
			defer resp.Body.Close()
			if resp.StatusCode >= 300 {
				log.Printf("[Webhook] Non-200 response: %v", resp.Status)
			}
		}()
	}
}

// GetBIMModel serves a BIMModel for a given project/building/floor
func GetBIMModel(w http.ResponseWriter, r *http.Request) {
	// TODO: Query and assemble BIMModel from DB for the requested context
	// For now, get floor_id from query param
	floorIDStr := r.URL.Query().Get("floor_id")
	var floorID uint
	if floorIDStr != "" {
		fmt.Sscanf(floorIDStr, "%d", &floorID)
	}
	bimModel := models.BIMModel{
		Rooms:   []models.Room{},
		Devices: []models.Device{},
		Labels:  []models.Label{},
		Zones:   []models.Zone{},
		Routes:  []models.Route{},
		Pins:    []models.Pin{},
	}
	// Query pins for this floor
	if floorID != 0 {
		var pins []models.Pin
		if err := models.DB.Where("floor_id = ?", floorID).Find(&pins).Error; err == nil {
			bimModel.Pins = pins
		}
	}
	json.NewEncoder(w).Encode(bimModel)
}

// Helper: Get all devices in a room
func GetDevicesInRoom(roomID string) ([]models.Device, error) {
	var devices []models.Device
	err := db.DB.Where("room_id = ?", roomID).Find(&devices).Error
	return devices, err
}

// Helper: Get all labels in a room
func GetLabelsInRoom(roomID string) ([]models.Label, error) {
	var labels []models.Label
	err := db.DB.Where("room_id = ?", roomID).Find(&labels).Error
	return labels, err
}

// --- Room Handlers ---
// PATCH /api/room/{id}           -> UpdateRoom
// POST  /api/room/{id}/lock      -> LockRoom
// POST  /api/room/{id}/unlock    -> UnlockRoom
// POST  /api/room/{id}/assign    -> AssignRoom
// POST  /api/room/{id}/status    -> UpdateRoomStatus

func UpdateRoom(w http.ResponseWriter, r *http.Request) {
	_, err := GetUserFromRequest(r)
	if err != nil {
		http.Error(w, "Unauthorized", http.StatusUnauthorized)
		return
	}
	roomID := chi.URLParam(r, "id")
	var room models.Room
	projectID, err := extractProjectID(r)
	if err != nil {
		http.Error(w, "Invalid project ID", http.StatusBadRequest)
		return
	}
	if err := db.DB.Where("id = ? AND project_id = ?", roomID, projectID).First(&room).Error; err != nil {
		http.Error(w, "Room not found", http.StatusNotFound)
		return
	}
	if !models.IsValidObjectId(room.ID) {
		http.Error(w, "Invalid room ID format", http.StatusBadRequest)
		return
	}
	var update struct {
		Status     *string `json:"status"`
		AssignedTo *uint   `json:"assigned_to"`
	}
	if err := json.NewDecoder(r.Body).Decode(&update); err != nil {
		http.Error(w, "Invalid body", http.StatusBadRequest)
		return
	}
	if update.Status != nil {
		room.Status = *update.Status
	}
	if update.AssignedTo != nil {
		room.AssignedTo = *update.AssignedTo
	}
	db.DB.Save(&room)
	json.NewEncoder(w).Encode(room)
}

func LockRoom(w http.ResponseWriter, r *http.Request) {
	user, err := GetUserFromRequest(r)
	if err != nil {
		http.Error(w, "Unauthorized", http.StatusUnauthorized)
		return
	}
	roomID := chi.URLParam(r, "id")
	var room models.Room
	projectID, err := extractProjectID(r)
	if err != nil {
		http.Error(w, "Invalid project ID", http.StatusBadRequest)
		return
	}
	if err := db.DB.Where("id = ? AND project_id = ?", roomID, projectID).First(&room).Error; err != nil {
		http.Error(w, "Room not found", http.StatusNotFound)
		return
	}
	if !models.IsValidObjectId(room.ID) {
		http.Error(w, "Invalid room ID format", http.StatusBadRequest)
		return
	}
	if room.LockedBy != 0 && room.LockedBy != user.ID {
		http.Error(w, "Room is already locked by another user", http.StatusForbidden)
		return
	}
	room.LockedBy = user.ID
	db.DB.Save(&room)
	json.NewEncoder(w).Encode(room)
}

func UnlockRoom(w http.ResponseWriter, r *http.Request) {
	user, err := GetUserFromRequest(r)
	if err != nil {
		http.Error(w, "Unauthorized", http.StatusUnauthorized)
		return
	}
	roomID := chi.URLParam(r, "id")
	var room models.Room
	projectID, err := extractProjectID(r)
	if err != nil {
		http.Error(w, "Invalid project ID", http.StatusBadRequest)
		return
	}
	if err := db.DB.Where("id = ? AND project_id = ?", roomID, projectID).First(&room).Error; err != nil {
		http.Error(w, "Room not found", http.StatusNotFound)
		return
	}
	if !models.IsValidObjectId(room.ID) {
		http.Error(w, "Invalid room ID format", http.StatusBadRequest)
		return
	}
	if room.LockedBy != user.ID {
		http.Error(w, "You do not own the lock", http.StatusForbidden)
		return
	}
	room.LockedBy = 0
	db.DB.Save(&room)
	json.NewEncoder(w).Encode(room)
}

func AssignRoom(w http.ResponseWriter, r *http.Request) {
	_, err := GetUserFromRequest(r)
	if err != nil {
		http.Error(w, "Unauthorized", http.StatusUnauthorized)
		return
	}
	roomID := chi.URLParam(r, "id")
	var room models.Room
	projectID, err := extractProjectID(r)
	if err != nil {
		http.Error(w, "Invalid project ID", http.StatusBadRequest)
		return
	}
	if err := db.DB.Where("id = ? AND project_id = ?", roomID, projectID).First(&room).Error; err != nil {
		http.Error(w, "Room not found", http.StatusNotFound)
		return
	}
	if !models.IsValidObjectId(room.ID) {
		http.Error(w, "Invalid room ID format", http.StatusBadRequest)
		return
	}
	var assign struct {
		AssignedTo uint `json:"assigned_to"`
	}
	if err := json.NewDecoder(r.Body).Decode(&assign); err != nil {
		http.Error(w, "Invalid body", http.StatusBadRequest)
		return
	}
	room.AssignedTo = assign.AssignedTo
	db.DB.Save(&room)
	json.NewEncoder(w).Encode(room)
}

func UpdateRoomStatus(w http.ResponseWriter, r *http.Request) {
	_, err := GetUserFromRequest(r)
	if err != nil {
		http.Error(w, "Unauthorized", http.StatusUnauthorized)
		return
	}
	roomID := chi.URLParam(r, "id")
	var room models.Room
	projectID, err := extractProjectID(r)
	if err != nil {
		http.Error(w, "Invalid project ID", http.StatusBadRequest)
		return
	}
	if err := db.DB.Where("id = ? AND project_id = ?", roomID, projectID).First(&room).Error; err != nil {
		http.Error(w, "Room not found", http.StatusNotFound)
		return
	}
	if !models.IsValidObjectId(room.ID) {
		http.Error(w, "Invalid room ID format", http.StatusBadRequest)
		return
	}
	var status struct {
		Status string `json:"status"`
	}
	if err := json.NewDecoder(r.Body).Decode(&status); err != nil {
		http.Error(w, "Invalid body", http.StatusBadRequest)
		return
	}
	room.Status = status.Status
	db.DB.Save(&room)
	json.NewEncoder(w).Encode(room)
}

// --- Wall Handlers ---
// PATCH /api/wall/{id}           -> UpdateWall
// POST  /api/wall/{id}/lock      -> LockWall
// POST  /api/wall/{id}/unlock    -> UnlockWall
// POST  /api/wall/{id}/assign    -> AssignWall
// POST  /api/wall/{id}/status    -> UpdateWallStatus

func UpdateWall(w http.ResponseWriter, r *http.Request) {
	_, err := GetUserFromRequest(r)
	if err != nil {
		http.Error(w, "Unauthorized", http.StatusUnauthorized)
		return
	}
	wallID := chi.URLParam(r, "id")
	var wall models.Wall
	projectID, err := extractProjectID(r)
	if err != nil {
		http.Error(w, "Invalid project ID", http.StatusBadRequest)
		return
	}
	if err := db.DB.Where("id = ? AND project_id = ?", wallID, projectID).First(&wall).Error; err != nil {
		http.Error(w, "Wall not found", http.StatusNotFound)
		return
	}
	if !models.IsValidObjectId(wall.ID) {
		http.Error(w, "Invalid wall ID format", http.StatusBadRequest)
		return
	}
	var update struct {
		Status     *string  `json:"status"`
		AssignedTo *uint    `json:"assigned_to"`
		Type       *string  `json:"type"`
		Material   *string  `json:"material"`
		Thickness  *float64 `json:"thickness"`
		Height     *float64 `json:"height"`
		FireRating *string  `json:"fire_rating"`
		Insulation *string  `json:"insulation"`
	}
	if err := json.NewDecoder(r.Body).Decode(&update); err != nil {
		http.Error(w, "Invalid body", http.StatusBadRequest)
		return
	}
	if update.Status != nil {
		wall.Status = *update.Status
	}
	if update.AssignedTo != nil {
		wall.AssignedTo = *update.AssignedTo
	}
	if update.Type != nil {
		wall.Type = *update.Type
	}
	if update.Material != nil {
		wall.Material = *update.Material
	}
	if update.Thickness != nil {
		wall.Thickness = *update.Thickness
	}
	if update.Height != nil {
		wall.Height = *update.Height
	}
	if update.FireRating != nil {
		wall.FireRating = *update.FireRating
	}
	if update.Insulation != nil {
		wall.Insulation = *update.Insulation
	}
	db.DB.Save(&wall)
	json.NewEncoder(w).Encode(wall)
}

func LockWall(w http.ResponseWriter, r *http.Request) {
	user, err := GetUserFromRequest(r)
	if err != nil {
		http.Error(w, "Unauthorized", http.StatusUnauthorized)
		return
	}
	wallID := chi.URLParam(r, "id")
	var wall models.Wall
	projectID, err := extractProjectID(r)
	if err != nil {
		http.Error(w, "Invalid project ID", http.StatusBadRequest)
		return
	}
	if err := db.DB.Where("id = ? AND project_id = ?", wallID, projectID).First(&wall).Error; err != nil {
		http.Error(w, "Wall not found", http.StatusNotFound)
		return
	}
	if !models.IsValidObjectId(wall.ID) {
		http.Error(w, "Invalid wall ID format", http.StatusBadRequest)
		return
	}
	if wall.LockedBy != 0 && wall.LockedBy != user.ID {
		http.Error(w, "Wall is already locked by another user", http.StatusForbidden)
		return
	}
	wall.LockedBy = user.ID
	db.DB.Save(&wall)
	json.NewEncoder(w).Encode(wall)
}

func UnlockWall(w http.ResponseWriter, r *http.Request) {
	user, err := GetUserFromRequest(r)
	if err != nil {
		http.Error(w, "Unauthorized", http.StatusUnauthorized)
		return
	}
	wallID := chi.URLParam(r, "id")
	var wall models.Wall
	projectID, err := extractProjectID(r)
	if err != nil {
		http.Error(w, "Invalid project ID", http.StatusBadRequest)
		return
	}
	if err := db.DB.Where("id = ? AND project_id = ?", wallID, projectID).First(&wall).Error; err != nil {
		http.Error(w, "Wall not found", http.StatusNotFound)
		return
	}
	if !models.IsValidObjectId(wall.ID) {
		http.Error(w, "Invalid wall ID format", http.StatusBadRequest)
		return
	}
	if wall.LockedBy != user.ID {
		http.Error(w, "You do not own the lock", http.StatusForbidden)
		return
	}
	wall.LockedBy = 0
	db.DB.Save(&wall)
	json.NewEncoder(w).Encode(wall)
}

func AssignWall(w http.ResponseWriter, r *http.Request) {
	_, err := GetUserFromRequest(r)
	if err != nil {
		http.Error(w, "Unauthorized", http.StatusUnauthorized)
		return
	}
	wallID := chi.URLParam(r, "id")
	var wall models.Wall
	projectID, err := extractProjectID(r)
	if err != nil {
		http.Error(w, "Invalid project ID", http.StatusBadRequest)
		return
	}
	if err := db.DB.Where("id = ? AND project_id = ?", wallID, projectID).First(&wall).Error; err != nil {
		http.Error(w, "Wall not found", http.StatusNotFound)
		return
	}
	if !models.IsValidObjectId(wall.ID) {
		http.Error(w, "Invalid wall ID format", http.StatusBadRequest)
		return
	}
	var assign struct {
		AssignedTo uint `json:"assigned_to"`
	}
	if err := json.NewDecoder(r.Body).Decode(&assign); err != nil {
		http.Error(w, "Invalid body", http.StatusBadRequest)
		return
	}
	wall.AssignedTo = assign.AssignedTo
	db.DB.Save(&wall)
	json.NewEncoder(w).Encode(wall)
}

func UpdateWallStatus(w http.ResponseWriter, r *http.Request) {
	_, err := GetUserFromRequest(r)
	if err != nil {
		http.Error(w, "Unauthorized", http.StatusUnauthorized)
		return
	}
	wallID := chi.URLParam(r, "id")
	var wall models.Wall
	projectID, err := extractProjectID(r)
	if err != nil {
		http.Error(w, "Invalid project ID", http.StatusBadRequest)
		return
	}
	if err := db.DB.Where("id = ? AND project_id = ?", wallID, projectID).First(&wall).Error; err != nil {
		http.Error(w, "Wall not found", http.StatusNotFound)
		return
	}
	if !models.IsValidObjectId(wall.ID) {
		http.Error(w, "Invalid wall ID format", http.StatusBadRequest)
		return
	}
	var status struct {
		Status string `json:"status"`
	}
	if err := json.NewDecoder(r.Body).Decode(&status); err != nil {
		http.Error(w, "Invalid body", http.StatusBadRequest)
		return
	}
	wall.Status = status.Status
	db.DB.Save(&wall)
	json.NewEncoder(w).Encode(wall)
}

// --- Device Handlers ---
// PATCH /api/device/{id}           -> UpdateDevice
// POST  /api/device/{id}/lock      -> LockDevice
// POST  /api/device/{id}/unlock    -> UnlockDevice
// POST  /api/device/{id}/assign    -> AssignDevice
// POST  /api/device/{id}/status    -> UpdateDeviceStatus

func UpdateDevice(w http.ResponseWriter, r *http.Request) {
	user, err := GetUserFromRequest(r)
	if err != nil {
		http.Error(w, "Unauthorized", http.StatusUnauthorized)
		return
	}
	deviceID := chi.URLParam(r, "id")
	var device models.Device
	projectID, err := extractProjectID(r)
	if err != nil {
		http.Error(w, "Invalid project ID", http.StatusBadRequest)
		return
	}
	if err := db.DB.Where("id = ? AND project_id = ?", deviceID, projectID).First(&device).Error; err != nil {
		http.Error(w, "Device not found", http.StatusNotFound)
		return
	}
	if !models.IsValidObjectId(device.ID) {
		http.Error(w, "Invalid device ID format", http.StatusBadRequest)
		return
	}
	valid, invalidFields := models.ValidateMetadataLinks(map[string]string{
		"panel_id":      device.PanelID,
		"circuit_id":    device.CircuitID,
		"upstream_id":   device.UpstreamID,
		"downstream_id": device.DownstreamID,
		"pipe_id":       device.PipeID,
	})
	if !valid {
		http.Error(w, "Invalid metadata link field(s) in device: "+strings.Join(invalidFields, ", "), http.StatusBadRequest)
		_ = models.LogChange(db.DB, user.ID, "Device", device.ID, "validation_failed", map[string]interface{}{
			"error":          "Invalid metadata link field(s) in device: " + strings.Join(invalidFields, ", "),
			"invalid_fields": invalidFields,
			"device":         device,
		})
		return
	}
	var update struct {
		Status     *string `json:"status"`
		AssignedTo *uint   `json:"assigned_to"`
	}
	if err := json.NewDecoder(r.Body).Decode(&update); err != nil {
		http.Error(w, "Invalid body", http.StatusBadRequest)
		return
	}
	if update.Status != nil {
		device.Status = *update.Status
	}
	if update.AssignedTo != nil {
		device.AssignedTo = *update.AssignedTo
	}
	db.DB.Save(&device)
	json.NewEncoder(w).Encode(device)
}

func LockDevice(w http.ResponseWriter, r *http.Request) {
	user, err := GetUserFromRequest(r)
	if err != nil {
		http.Error(w, "Unauthorized", http.StatusUnauthorized)
		return
	}
	deviceID := chi.URLParam(r, "id")
	var device models.Device
	projectID, err := extractProjectID(r)
	if err != nil {
		http.Error(w, "Invalid project ID", http.StatusBadRequest)
		return
	}
	if err := db.DB.Where("id = ? AND project_id = ?", deviceID, projectID).First(&device).Error; err != nil {
		http.Error(w, "Device not found", http.StatusNotFound)
		return
	}
	if !models.IsValidObjectId(device.ID) {
		http.Error(w, "Invalid device ID format", http.StatusBadRequest)
		return
	}
	if device.LockedBy != 0 && device.LockedBy != user.ID {
		http.Error(w, "Device is already locked by another user", http.StatusForbidden)
		return
	}
	device.LockedBy = user.ID
	db.DB.Save(&device)
	json.NewEncoder(w).Encode(device)
}

func UnlockDevice(w http.ResponseWriter, r *http.Request) {
	user, err := GetUserFromRequest(r)
	if err != nil {
		http.Error(w, "Unauthorized", http.StatusUnauthorized)
		return
	}
	deviceID := chi.URLParam(r, "id")
	var device models.Device
	projectID, err := extractProjectID(r)
	if err != nil {
		http.Error(w, "Invalid project ID", http.StatusBadRequest)
		return
	}
	if err := db.DB.Where("id = ? AND project_id = ?", deviceID, projectID).First(&device).Error; err != nil {
		http.Error(w, "Device not found", http.StatusNotFound)
		return
	}
	if !models.IsValidObjectId(device.ID) {
		http.Error(w, "Invalid device ID format", http.StatusBadRequest)
		return
	}
	if device.LockedBy != user.ID {
		http.Error(w, "You do not own the lock", http.StatusForbidden)
		return
	}
	device.LockedBy = 0
	db.DB.Save(&device)
	json.NewEncoder(w).Encode(device)
}

func AssignDevice(w http.ResponseWriter, r *http.Request) {
	_, err := GetUserFromRequest(r)
	if err != nil {
		http.Error(w, "Unauthorized", http.StatusUnauthorized)
		return
	}
	deviceID := chi.URLParam(r, "id")
	var device models.Device
	projectID, err := extractProjectID(r)
	if err != nil {
		http.Error(w, "Invalid project ID", http.StatusBadRequest)
		return
	}
	if err := db.DB.Where("id = ? AND project_id = ?", deviceID, projectID).First(&device).Error; err != nil {
		http.Error(w, "Device not found", http.StatusNotFound)
		return
	}
	if !models.IsValidObjectId(device.ID) {
		http.Error(w, "Invalid device ID format", http.StatusBadRequest)
		return
	}
	var assign struct {
		AssignedTo uint `json:"assigned_to"`
	}
	if err := json.NewDecoder(r.Body).Decode(&assign); err != nil {
		http.Error(w, "Invalid body", http.StatusBadRequest)
		return
	}
	device.AssignedTo = assign.AssignedTo
	db.DB.Save(&device)
	json.NewEncoder(w).Encode(device)
}

func UpdateDeviceStatus(w http.ResponseWriter, r *http.Request) {
	_, err := GetUserFromRequest(r)
	if err != nil {
		http.Error(w, "Unauthorized", http.StatusUnauthorized)
		return
	}
	deviceID := chi.URLParam(r, "id")
	var device models.Device
	projectID, err := extractProjectID(r)
	if err != nil {
		http.Error(w, "Invalid project ID", http.StatusBadRequest)
		return
	}
	if err := db.DB.Where("id = ? AND project_id = ?", deviceID, projectID).First(&device).Error; err != nil {
		http.Error(w, "Device not found", http.StatusNotFound)
		return
	}
	if !models.IsValidObjectId(device.ID) {
		http.Error(w, "Invalid device ID format", http.StatusBadRequest)
		return
	}
	var status struct {
		Status string `json:"status"`
	}
	if err := json.NewDecoder(r.Body).Decode(&status); err != nil {
		http.Error(w, "Invalid body", http.StatusBadRequest)
		return
	}
	device.Status = status.Status
	db.DB.Save(&device)
	json.NewEncoder(w).Encode(device)
}

// --- Label Handlers ---
// PATCH /api/label/{id}           -> UpdateLabel
// POST  /api/label/{id}/lock      -> LockLabel
// POST  /api/label/{id}/unlock    -> UnlockLabel
// POST  /api/label/{id}/assign    -> AssignLabel
// POST  /api/label/{id}/status    -> UpdateLabelStatus

func UpdateLabel(w http.ResponseWriter, r *http.Request) {
	user, err := GetUserFromRequest(r)
	if err != nil {
		http.Error(w, "Unauthorized", http.StatusUnauthorized)
		return
	}
	labelID := chi.URLParam(r, "id")
	var label models.Label
	projectID, err := extractProjectID(r)
	if err != nil {
		http.Error(w, "Invalid project ID", http.StatusBadRequest)
		return
	}
	if err := db.DB.Where("id = ? AND project_id = ?", labelID, projectID).First(&label).Error; err != nil {
		http.Error(w, "Label not found", http.StatusNotFound)
		return
	}
	if !models.IsValidObjectId(label.ID) {
		http.Error(w, "Invalid label ID format", http.StatusBadRequest)
		return
	}
	valid, invalidFields := models.ValidateMetadataLinks(map[string]string{
		"upstream_id":   label.UpstreamID,
		"downstream_id": label.DownstreamID,
	})
	if !valid {
		http.Error(w, "Invalid metadata link field(s) in label: "+strings.Join(invalidFields, ", "), http.StatusBadRequest)
		_ = models.LogChange(db.DB, user.ID, "Label", label.ID, "validation_failed", map[string]interface{}{
			"error":          "Invalid metadata link field(s) in label: " + strings.Join(invalidFields, ", "),
			"invalid_fields": invalidFields,
			"label":          label,
		})
		return
	}
	var update struct {
		Status     *string `json:"status"`
		AssignedTo *uint   `json:"assigned_to"`
	}
	if err := json.NewDecoder(r.Body).Decode(&update); err != nil {
		http.Error(w, "Invalid body", http.StatusBadRequest)
		return
	}
	if update.Status != nil {
		label.Status = *update.Status
	}
	if update.AssignedTo != nil {
		label.AssignedTo = *update.AssignedTo
	}
	db.DB.Save(&label)
	json.NewEncoder(w).Encode(label)
}

func LockLabel(w http.ResponseWriter, r *http.Request) {
	user, err := GetUserFromRequest(r)
	if err != nil {
		http.Error(w, "Unauthorized", http.StatusUnauthorized)
		return
	}
	labelID := chi.URLParam(r, "id")
	var label models.Label
	projectID, err := extractProjectID(r)
	if err != nil {
		http.Error(w, "Invalid project ID", http.StatusBadRequest)
		return
	}
	if err := db.DB.Where("id = ? AND project_id = ?", labelID, projectID).First(&label).Error; err != nil {
		http.Error(w, "Label not found", http.StatusNotFound)
		return
	}
	if !models.IsValidObjectId(label.ID) {
		http.Error(w, "Invalid label ID format", http.StatusBadRequest)
		return
	}
	if label.LockedBy != 0 && label.LockedBy != user.ID {
		http.Error(w, "Label is already locked by another user", http.StatusForbidden)
		return
	}
	label.LockedBy = user.ID
	db.DB.Save(&label)
	json.NewEncoder(w).Encode(label)
}

func UnlockLabel(w http.ResponseWriter, r *http.Request) {
	user, err := GetUserFromRequest(r)
	if err != nil {
		http.Error(w, "Unauthorized", http.StatusUnauthorized)
		return
	}
	labelID := chi.URLParam(r, "id")
	var label models.Label
	projectID, err := extractProjectID(r)
	if err != nil {
		http.Error(w, "Invalid project ID", http.StatusBadRequest)
		return
	}
	if err := db.DB.Where("id = ? AND project_id = ?", labelID, projectID).First(&label).Error; err != nil {
		http.Error(w, "Label not found", http.StatusNotFound)
		return
	}
	if !models.IsValidObjectId(label.ID) {
		http.Error(w, "Invalid label ID format", http.StatusBadRequest)
		return
	}
	if label.LockedBy != user.ID {
		http.Error(w, "You do not own the lock", http.StatusForbidden)
		return
	}
	label.LockedBy = 0
	db.DB.Save(&label)
	json.NewEncoder(w).Encode(label)
}

func UpdateLabelStatus(w http.ResponseWriter, r *http.Request) {
	_, err := GetUserFromRequest(r)
	if err != nil {
		http.Error(w, "Unauthorized", http.StatusUnauthorized)
		return
	}
	labelID := chi.URLParam(r, "id")
	var label models.Label
	projectID, err := extractProjectID(r)
	if err != nil {
		http.Error(w, "Invalid project ID", http.StatusBadRequest)
		return
	}
	if err := db.DB.Where("id = ? AND project_id = ?", labelID, projectID).First(&label).Error; err != nil {
		http.Error(w, "Label not found", http.StatusNotFound)
		return
	}
	if !models.IsValidObjectId(label.ID) {
		http.Error(w, "Invalid label ID format", http.StatusBadRequest)
		return
	}
	var status struct {
		Status string `json:"status"`
	}
	if err := json.NewDecoder(r.Body).Decode(&status); err != nil {
		http.Error(w, "Invalid body", http.StatusBadRequest)
		return
	}
	label.Status = status.Status
	db.DB.Save(&label)
	json.NewEncoder(w).Encode(label)
}

func AssignLabel(w http.ResponseWriter, r *http.Request) {
	_, err := GetUserFromRequest(r)
	if err != nil {
		http.Error(w, "Unauthorized", http.StatusUnauthorized)
		return
	}
	labelID := chi.URLParam(r, "id")
	var label models.Label
	projectID, err := extractProjectID(r)
	if err != nil {
		http.Error(w, "Invalid project ID", http.StatusBadRequest)
		return
	}
	if err := db.DB.Where("id = ? AND project_id = ?", labelID, projectID).First(&label).Error; err != nil {
		http.Error(w, "Label not found", http.StatusNotFound)
		return
	}
	if !models.IsValidObjectId(label.ID) {
		http.Error(w, "Invalid label ID format", http.StatusBadRequest)
		return
	}
	var assign struct {
		AssignedTo uint `json:"assigned_to"`
	}
	if err := json.NewDecoder(r.Body).Decode(&assign); err != nil {
		http.Error(w, "Invalid body", http.StatusBadRequest)
		return
	}
	label.AssignedTo = assign.AssignedTo
	db.DB.Save(&label)
	json.NewEncoder(w).Encode(label)
}

// --- Zone Handlers ---
// PATCH /api/zone/{id}           -> UpdateZone
// POST  /api/zone/{id}/lock      -> LockZone
// POST  /api/zone/{id}/unlock    -> UnlockZone
// POST  /api/zone/{id}/assign    -> AssignZone
// POST  /api/zone/{id}/status    -> UpdateZoneStatus

func UpdateZone(w http.ResponseWriter, r *http.Request) {
	_, err := GetUserFromRequest(r)
	if err != nil {
		http.Error(w, "Unauthorized", http.StatusUnauthorized)
		return
	}
	zoneID := chi.URLParam(r, "id")
	var zone models.Zone
	projectID, err := extractProjectID(r)
	if err != nil {
		http.Error(w, "Invalid project ID", http.StatusBadRequest)
		return
	}
	if err := db.DB.Where("id = ? AND project_id = ?", zoneID, projectID).First(&zone).Error; err != nil {
		http.Error(w, "Zone not found", http.StatusNotFound)
		return
	}
	if !models.IsValidObjectId(zone.ID) {
		http.Error(w, "Invalid zone ID format", http.StatusBadRequest)
		return
	}
	var update struct {
		Status     *string `json:"status"`
		AssignedTo *uint   `json:"assigned_to"`
	}
	if err := json.NewDecoder(r.Body).Decode(&update); err != nil {
		http.Error(w, "Invalid body", http.StatusBadRequest)
		return
	}
	if update.Status != nil {
		zone.Status = *update.Status
	}
	if update.AssignedTo != nil {
		zone.AssignedTo = *update.AssignedTo
	}
	db.DB.Save(&zone)
	json.NewEncoder(w).Encode(zone)
}

func LockZone(w http.ResponseWriter, r *http.Request) {
	user, err := GetUserFromRequest(r)
	if err != nil {
		http.Error(w, "Unauthorized", http.StatusUnauthorized)
		return
	}
	zoneID := chi.URLParam(r, "id")
	var zone models.Zone
	projectID, err := extractProjectID(r)
	if err != nil {
		http.Error(w, "Invalid project ID", http.StatusBadRequest)
		return
	}
	if err := db.DB.Where("id = ? AND project_id = ?", zoneID, projectID).First(&zone).Error; err != nil {
		http.Error(w, "Zone not found", http.StatusNotFound)
		return
	}
	if !models.IsValidObjectId(zone.ID) {
		http.Error(w, "Invalid zone ID format", http.StatusBadRequest)
		return
	}
	if zone.LockedBy != 0 && zone.LockedBy != user.ID {
		http.Error(w, "Zone is already locked by another user", http.StatusForbidden)
		return
	}
	zone.LockedBy = user.ID
	db.DB.Save(&zone)
	json.NewEncoder(w).Encode(zone)
}

func UnlockZone(w http.ResponseWriter, r *http.Request) {
	user, err := GetUserFromRequest(r)
	if err != nil {
		http.Error(w, "Unauthorized", http.StatusUnauthorized)
		return
	}
	zoneID := chi.URLParam(r, "id")
	var zone models.Zone
	projectID, err := extractProjectID(r)
	if err != nil {
		http.Error(w, "Invalid project ID", http.StatusBadRequest)
		return
	}
	if err := db.DB.Where("id = ? AND project_id = ?", zoneID, projectID).First(&zone).Error; err != nil {
		http.Error(w, "Zone not found", http.StatusNotFound)
		return
	}
	if !models.IsValidObjectId(zone.ID) {
		http.Error(w, "Invalid zone ID format", http.StatusBadRequest)
		return
	}
	if zone.LockedBy != user.ID {
		http.Error(w, "You do not own the lock", http.StatusForbidden)
		return
	}
	zone.LockedBy = 0
	db.DB.Save(&zone)
	json.NewEncoder(w).Encode(zone)
}

func AssignZone(w http.ResponseWriter, r *http.Request) {
	_, err := GetUserFromRequest(r)
	if err != nil {
		http.Error(w, "Unauthorized", http.StatusUnauthorized)
		return
	}
	zoneID := chi.URLParam(r, "id")
	var zone models.Zone
	projectID, err := extractProjectID(r)
	if err != nil {
		http.Error(w, "Invalid project ID", http.StatusBadRequest)
		return
	}
	if err := db.DB.Where("id = ? AND project_id = ?", zoneID, projectID).First(&zone).Error; err != nil {
		http.Error(w, "Zone not found", http.StatusNotFound)
		return
	}
	if !models.IsValidObjectId(zone.ID) {
		http.Error(w, "Invalid zone ID format", http.StatusBadRequest)
		return
	}
	var assign struct {
		AssignedTo uint `json:"assigned_to"`
	}
	if err := json.NewDecoder(r.Body).Decode(&assign); err != nil {
		http.Error(w, "Invalid body", http.StatusBadRequest)
		return
	}
	zone.AssignedTo = assign.AssignedTo
	db.DB.Save(&zone)
	json.NewEncoder(w).Encode(zone)
}

func UpdateZoneStatus(w http.ResponseWriter, r *http.Request) {
	_, err := GetUserFromRequest(r)
	if err != nil {
		http.Error(w, "Unauthorized", http.StatusUnauthorized)
		return
	}
	zoneID := chi.URLParam(r, "id")
	var zone models.Zone
	projectID, err := extractProjectID(r)
	if err != nil {
		http.Error(w, "Invalid project ID", http.StatusBadRequest)
		return
	}
	if err := db.DB.Where("id = ? AND project_id = ?", zoneID, projectID).First(&zone).Error; err != nil {
		http.Error(w, "Zone not found", http.StatusNotFound)
		return
	}
	if !models.IsValidObjectId(zone.ID) {
		http.Error(w, "Invalid zone ID format", http.StatusBadRequest)
		return
	}
	var status struct {
		Status string `json:"status"`
	}
	if err := json.NewDecoder(r.Body).Decode(&status); err != nil {
		http.Error(w, "Invalid body", http.StatusBadRequest)
		return
	}
	zone.Status = status.Status
	db.DB.Save(&zone)
	json.NewEncoder(w).Encode(zone)
}

// Paginated list endpoints for BIM objects

func ListRooms(w http.ResponseWriter, r *http.Request) {
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
	projectID, err := extractProjectID(r)
	if err != nil {
		http.Error(w, "Invalid project ID", http.StatusBadRequest)
		return
	}
	db.DB.Model(&models.Room{}).Where("project_id = ?", projectID).Count(&total)

	var rooms []models.Room
	db.DB.Where("project_id = ?", projectID).Offset(offset).Limit(pageSize).Find(&rooms)

	resp := map[string]interface{}{
		"results":     rooms,
		"page":        page,
		"page_size":   pageSize,
		"total":       total,
		"total_pages": (total + int64(pageSize) - 1) / int64(pageSize),
	}
	json.NewEncoder(w).Encode(resp)
}

func ListWalls(w http.ResponseWriter, r *http.Request) {
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
	projectID, err := extractProjectID(r)
	if err != nil {
		http.Error(w, "Invalid project ID", http.StatusBadRequest)
		return
	}
	db.DB.Model(&models.Wall{}).Where("project_id = ?", projectID).Count(&total)

	var walls []models.Wall
	db.DB.Where("project_id = ?", projectID).Offset(offset).Limit(pageSize).Find(&walls)

	resp := map[string]interface{}{
		"results":     walls,
		"page":        page,
		"page_size":   pageSize,
		"total":       total,
		"total_pages": (total + int64(pageSize) - 1) / int64(pageSize),
	}
	json.NewEncoder(w).Encode(resp)
}

func ListDevices(w http.ResponseWriter, r *http.Request) {
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
	projectID, err := extractProjectID(r)
	if err != nil {
		http.Error(w, "Invalid project ID", http.StatusBadRequest)
		return
	}
	db.DB.Model(&models.Device{}).Where("project_id = ?", projectID).Count(&total)

	var devices []models.Device
	db.DB.Where("project_id = ?", projectID).Offset(offset).Limit(pageSize).Find(&devices)

	resp := map[string]interface{}{
		"results":     devices,
		"page":        page,
		"page_size":   pageSize,
		"total":       total,
		"total_pages": (total + int64(pageSize) - 1) / int64(pageSize),
	}
	json.NewEncoder(w).Encode(resp)
}

func ListLabels(w http.ResponseWriter, r *http.Request) {
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
	projectID, err := extractProjectID(r)
	if err != nil {
		http.Error(w, "Invalid project ID", http.StatusBadRequest)
		return
	}
	db.DB.Model(&models.Label{}).Where("project_id = ?", projectID).Count(&total)

	var labels []models.Label
	db.DB.Where("project_id = ?", projectID).Offset(offset).Limit(pageSize).Find(&labels)

	resp := map[string]interface{}{
		"results":     labels,
		"page":        page,
		"page_size":   pageSize,
		"total":       total,
		"total_pages": (total + int64(pageSize) - 1) / int64(pageSize),
	}
	json.NewEncoder(w).Encode(resp)
}

func ListZones(w http.ResponseWriter, r *http.Request) {
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
	projectID, err := extractProjectID(r)
	if err != nil {
		http.Error(w, "Invalid project ID", http.StatusBadRequest)
		return
	}
	db.DB.Model(&models.Zone{}).Where("project_id = ?", projectID).Count(&total)

	var zones []models.Zone
	db.DB.Where("project_id = ?", projectID).Offset(offset).Limit(pageSize).Find(&zones)

	resp := map[string]interface{}{
		"results":     zones,
		"page":        page,
		"page_size":   pageSize,
		"total":       total,
		"total_pages": (total + int64(pageSize) - 1) / int64(pageSize),
	}
	json.NewEncoder(w).Encode(resp)
}

// Export BIM data as JSON
func ExportBIMAsJSON(w http.ResponseWriter, r *http.Request) {
	var bimModel models.BIMModel
	db.DB.Find(&bimModel.Rooms)
	db.DB.Find(&bimModel.Walls)
	db.DB.Find(&bimModel.Devices)
	db.DB.Find(&bimModel.Labels)
	db.DB.Find(&bimModel.Zones)
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(bimModel)
}

// Stub: Export as IFC-lite
func ExportBIMAsIFC(w http.ResponseWriter, r *http.Request) {
	w.WriteHeader(http.StatusNotImplemented)
	w.Write([]byte("IFC-lite export not implemented yet"))
}

// Stub: Export as DXF
func ExportBIMAsDXF(w http.ResponseWriter, r *http.Request) {
	w.WriteHeader(http.StatusNotImplemented)
	w.Write([]byte("DXF export not implemented yet"))
}

// Stub: Export as SVG
func ExportBIMAsSVG(w http.ResponseWriter, r *http.Request) {
	w.WriteHeader(http.StatusNotImplemented)
	w.Write([]byte("SVG export not implemented yet"))
}

// Device Catalog for HTMX
func HTMXDeviceCatalog(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "text/html")
	var items []models.CatalogItem
	db.DB.Find(&items)
	for _, item := range items {
		jsonData, _ := json.Marshal(map[string]interface{}{
			"id":           item.ID,
			"make":         item.Make,
			"model":        item.Model,
			"type":         item.Type,
			"display_name": item.Make + " " + item.Model,
			"system":       item.Type, // or map to system if needed
		})
		w.Write([]byte("<div class='device-item cursor-pointer hover:bg-blue-50 rounded px-2 py-1 mb-1 border' data-device='" + string(jsonData) + "'>" + item.Make + " " + item.Model + " (" + item.Type + ")</div>"))
	}
}

// SavePlacedDevice handles POST /api/devices to save a placed device from the markup modal
func SavePlacedDevice(w http.ResponseWriter, r *http.Request) {
	user, err := GetUserFromRequest(r)
	if err != nil {
		http.Error(w, "Unauthorized", http.StatusUnauthorized)
		return
	}
	var req struct {
		CatalogID uint `json:"catalog_id"`
		X         int  `json:"x"`
		Y         int  `json:"y"`
		FloorID   uint `json:"floor_id"`
		ProjectID uint `json:"project_id"`
	}
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "Invalid body", http.StatusBadRequest)
		return
	}
	var catalog models.CatalogItem
	if err := db.DB.First(&catalog, req.CatalogID).Error; err != nil {
		http.Error(w, "Catalog item not found", http.StatusBadRequest)
		return
	}
	device := models.Device{
		Type:   catalog.Type,
		System: "", // Optionally map from catalog.CategoryID or another field
		Geometry: models.Geometry{
			Type:   "Point",
			Points: []models.Point{{X: float64(req.X), Y: float64(req.Y)}},
		},
		ProjectID: req.ProjectID,
		CreatedBy: user.ID,
		Status:    "draft",
	}
	if !models.IsValidObjectId(device.ID) {
		http.Error(w, "Invalid device ID format", http.StatusBadRequest)
		return
	}
	db.DB.Create(&device)
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(device)
}

// GetDevice returns a device by ID as JSON
func GetDevice(w http.ResponseWriter, r *http.Request) {
	_, err := GetUserFromRequest(r)
	if err != nil {
		http.Error(w, "Unauthorized", http.StatusUnauthorized)
		return
	}
	deviceID := chi.URLParam(r, "id")
	projectID, err := extractProjectID(r)
	if err != nil {
		http.Error(w, "Invalid project ID", http.StatusBadRequest)
		return
	}
	var device models.Device
	if err := db.DB.Where("id = ? AND project_id = ?", deviceID, projectID).First(&device).Error; err != nil {
		http.Error(w, "Device not found", http.StatusNotFound)
		return
	}
	if !models.IsValidObjectId(device.ID) {
		http.Error(w, "Invalid device ID format", http.StatusBadRequest)
		return
	}
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(device)
}

// UpdateDeviceDetails allows PATCH to update device fields
func UpdateDeviceDetails(w http.ResponseWriter, r *http.Request) {
	_, err := GetUserFromRequest(r)
	if err != nil {
		http.Error(w, "Unauthorized", http.StatusUnauthorized)
		return
	}
	deviceID := chi.URLParam(r, "id")
	projectID, err := extractProjectID(r)
	if err != nil {
		http.Error(w, "Invalid project ID", http.StatusBadRequest)
		return
	}
	var device models.Device
	if err := db.DB.Where("id = ? AND project_id = ?", deviceID, projectID).First(&device).Error; err != nil {
		http.Error(w, "Device not found", http.StatusNotFound)
		return
	}
	if !models.IsValidObjectId(device.ID) {
		http.Error(w, "Invalid device ID format", http.StatusBadRequest)
		return
	}
	var update struct {
		CircuitNumber *string `json:"circuit_number"`
		Manufacturer  *string `json:"manufacturer"`
		ModelNumber   *string `json:"model_number"`
		SerialNumber  *string `json:"serial_number"`
		// Add more fields as needed
	}
	if err := json.NewDecoder(r.Body).Decode(&update); err != nil {
		http.Error(w, "Invalid body", http.StatusBadRequest)
		return
	}
	if update.CircuitNumber != nil {
		device.Subtype = *update.CircuitNumber // or use a dedicated field if available
	}
	if update.Manufacturer != nil {
		device.Layer = *update.Manufacturer // or use a dedicated field if available
	}
	if update.ModelNumber != nil {
		device.System = *update.ModelNumber // or use a dedicated field if available
	}
	if update.SerialNumber != nil {
		device.Category = *update.SerialNumber // or use a dedicated field if available
	}
	// Save changes
	db.DB.Save(&device)
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(device)
}

// CreateRoute handles POST /api/routes to create a new route
func CreateRoute(w http.ResponseWriter, r *http.Request) {
	user, err := GetUserFromRequest(r)
	if err != nil {
		http.Error(w, "Unauthorized", http.StatusUnauthorized)
		return
	}
	var req struct {
		ProjectID uint            `json:"project_id"`
		FloorID   uint            `json:"floor_id"`
		System    string          `json:"system"`
		Label     string          `json:"label"`
		Circuit   string          `json:"circuit"`
		Geometry  models.Geometry `json:"geometry"`
	}
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "Invalid body", http.StatusBadRequest)
		return
	}
	route := models.Route{
		ProjectID: req.ProjectID,
		FloorID:   req.FloorID,
		System:    req.System,
		Label:     req.Label,
		Circuit:   req.Circuit,
		Geometry:  req.Geometry,
		CreatedBy: user.ID,
	}
	db.DB.Create(&route)
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(route)
}

func ParseSVGElements(svg string) map[string]ElementInfo {
	decoder := xml.NewDecoder(strings.NewReader(svg))
	elements := make(map[string]ElementInfo)
	for {
		t, err := decoder.Token()
		if err == io.EOF {
			break
		}
		if err != nil {
			break
		}
		switch se := t.(type) {
		case xml.StartElement:
			attrs := make(map[string]string)
			var id string
			for _, attr := range se.Attr {
				attrs[attr.Name.Local] = attr.Value
				if attr.Name.Local == "id" {
					id = attr.Value
				}
			}
			if id != "" {
				elements[id] = ElementInfo{
					Tag:      se.Name.Local,
					ID:       id,
					DataName: attrs["data-name"],
					Attrs:    attrs,
				}
			}
		}
	}
	return elements
}
