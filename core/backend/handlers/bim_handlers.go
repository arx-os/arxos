package handlers

import (
	"encoding/json"
	"fmt"
	"math"
	"net/http"
	"strconv"
	
	"github.com/go-chi/chi/v5"
	"github.com/gorilla/websocket"
	
	// "github.com/arxos/arxos/core/bim"
)

var upgrader = websocket.Upgrader{
	CheckOrigin: func(r *http.Request) bool {
		return true // Allow all origins for dev
	},
}

// BIMHandler manages building information model endpoints
// Temporarily simplified until BIM module is set up
type BIMHandler struct {
	// model    *bim.BuildingModel
	clients  map[*websocket.Conn]bool
	broadcast chan interface{} // chan bim.Update
}

// NewBIMHandler creates a new BIM handler
// Temporarily disabled until BIM module is properly set up
/*
func NewBIMHandler(model *bim.BuildingModel) *BIMHandler {
	h := &BIMHandler{
		model:     model,
		clients:   make(map[*websocket.Conn]bool),
		broadcast: make(chan bim.Update),
	}
	
	// Start broadcasting updates
	go h.handleBroadcast()
	
	// Subscribe to model updates
	go h.subscribeToModel()
	
	return h
}
*/

// GetFloorSVG returns SVG representation of a floor
func (h *BIMHandler) GetFloorSVG(w http.ResponseWriter, r *http.Request) {
	floorID := chi.URLParam(r, "floorID")
	
	// Find floor
	var floor *bim.Floor
	for _, f := range h.model.Floors {
		if f.ID == floorID || strconv.Itoa(f.Number) == floorID {
			floor = f
			break
		}
	}
	
	if floor == nil {
		http.Error(w, "Floor not found", http.StatusNotFound)
		return
	}
	
	// Generate SVG
	svg := floor.RenderToSVG()
	
	// Return as HTML fragment for HTMX
	w.Header().Set("Content-Type", "text/html")
	w.Write([]byte(svg))
}

// CreateWall handles wall creation
func (h *BIMHandler) CreateWall(w http.ResponseWriter, r *http.Request) {
	var req struct {
		FloorID   string      `json:"floor_id"`
		Start     bim.Point3D `json:"start"`
		End       bim.Point3D `json:"end"`
		Thickness float64     `json:"thickness"`
		Type      string      `json:"type"`
	}
	
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}
	
	// Find floor
	var floor *bim.Floor
	for _, f := range h.model.Floors {
		if f.ID == req.FloorID || strconv.Itoa(f.Number) == req.FloorID {
			floor = f
			break
		}
	}
	
	if floor == nil {
		http.Error(w, "Floor not found", http.StatusNotFound)
		return
	}
	
	// Determine wall type
	wallType := bim.WallTypeInterior
	if req.Type == "exterior" {
		wallType = bim.WallTypeExterior
	}
	
	// Add wall to floor
	wall := floor.AddWall(req.Start, req.End, req.Thickness, wallType)
	
	// Broadcast update
	h.broadcast <- bim.Update{
		Type:     "wall_added",
		FloorID:  floor.ID,
		ObjectID: wall.ID,
		Data:     wall,
	}
	
	// Return wall data
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(wall)
}

// CreateOutlet handles outlet creation
func (h *BIMHandler) CreateOutlet(w http.ResponseWriter, r *http.Request) {
	var req struct {
		WallID   string  `json:"wall_id"`
		Position float64 `json:"position"` // 0-1 along wall
		Height   float64 `json:"height"`
		Type     string  `json:"type"`
	}
	
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}
	
	// Find wall
	var wall *bim.Wall
	for _, floor := range h.model.Floors {
		for _, w := range floor.Walls {
			if w.ID == req.WallID {
				wall = w
				break
			}
		}
	}
	
	if wall == nil {
		http.Error(w, "Wall not found", http.StatusNotFound)
		return
	}
	
	// Add outlet to wall
	outlet := wall.AddOutlet(req.Position, req.Height)
	
	// Broadcast update
	h.broadcast <- bim.Update{
		Type:     "outlet_added",
		ObjectID: outlet.ID,
		Data:     outlet,
	}
	
	// Return outlet data
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(outlet)
}

// GetObjectProperties returns properties panel HTML for selected object
func (h *BIMHandler) GetObjectProperties(w http.ResponseWriter, r *http.Request) {
	objectID := chi.URLParam(r, "objectID")
	
	if objectID == "none" {
		// Return default panel
		html := `
		<div class="property-group">
			<h3>No Selection</h3>
			<div class="property-row">
				<span class="property-label">Select an object to view properties</span>
			</div>
		</div>`
		
		w.Header().Set("Content-Type", "text/html")
		w.Write([]byte(html))
		return
	}
	
	// Find object (simplified - in real app would have proper object registry)
	var html string
	
	// Check if it's a wall
	for _, floor := range h.model.Floors {
		for _, wall := range floor.Walls {
			if wall.ID == objectID {
				html = h.renderWallProperties(wall)
				break
			}
		}
	}
	
	if html == "" {
		html = `<div class="property-group"><h3>Object not found</h3></div>`
	}
	
	w.Header().Set("Content-Type", "text/html")
	w.Write([]byte(html))
}

func (h *BIMHandler) renderWallProperties(wall *bim.Wall) string {
	wallType := "Interior"
	if wall.Type == bim.WallTypeExterior {
		wallType = "Exterior"
	}
	
	length := calculateWallLength(wall)
	
	return fmt.Sprintf(`
	<div class="property-group">
		<h3>Wall Properties</h3>
		<div class="property-row">
			<span class="property-label">ID:</span>
			<span class="property-value">%s</span>
		</div>
		<div class="property-row">
			<span class="property-label">Type:</span>
			<select class="property-input" 
			        hx-post="/api/objects/%s/update" 
			        hx-trigger="change"
			        name="type">
				<option value="interior" %s>Interior</option>
				<option value="exterior" %s>Exterior</option>
			</select>
		</div>
		<div class="property-row">
			<span class="property-label">Length:</span>
			<span class="property-value">%.1f mm</span>
		</div>
		<div class="property-row">
			<span class="property-label">Thickness:</span>
			<input class="property-input" 
			       type="number" 
			       value="%.0f"
			       hx-post="/api/objects/%s/update"
			       hx-trigger="change delay:500ms"
			       name="thickness">
		</div>
		<div class="property-row">
			<span class="property-label">Height:</span>
			<span class="property-value">%.0f mm</span>
		</div>
	</div>
	
	<div class="property-group">
		<h3>Hosted Objects</h3>
		<div class="property-row">
			<span class="property-label">Outlets:</span>
			<span class="property-value">%d</span>
		</div>
		<div class="property-row">
			<span class="property-label">Switches:</span>
			<span class="property-value">0</span>
		</div>
		<button class="property-input" style="width: 100%%; margin-top: 8px;"
		        hx-post="/api/walls/%s/add-outlet"
		        hx-trigger="click">
			Add Outlet
		</button>
	</div>
	
	<div class="property-group">
		<h3>Material</h3>
		<div class="property-row">
			<span class="property-label">Type:</span>
			<select class="property-input">
				<option>Drywall</option>
				<option>Concrete</option>
				<option>Brick</option>
				<option>Glass</option>
			</select>
		</div>
		<div class="property-row">
			<span class="property-label">Fire Rating:</span>
			<select class="property-input">
				<option>1 Hour</option>
				<option>2 Hour</option>
				<option>None</option>
			</select>
		</div>
	</div>`,
		wall.ID,
		wall.ID,
		selected(wallType == "Interior"),
		selected(wallType == "Exterior"),
		length,
		wall.Thickness,
		wall.ID,
		wall.Height,
		len(wall.HostedObjects),
		wall.ID,
	)
}

func selected(cond bool) string {
	if cond {
		return "selected"
	}
	return ""
}

func calculateWallLength(wall *bim.Wall) float64 {
	dx := wall.EndPoint.X - wall.StartPoint.X
	dy := wall.EndPoint.Y - wall.StartPoint.Y
	return math.Sqrt(dx*dx + dy*dy)
}

// WebSocket handling

func (h *BIMHandler) HandleWebSocket(w http.ResponseWriter, r *http.Request) {
	conn, err := upgrader.Upgrade(w, r, nil)
	if err != nil {
		return
	}
	defer conn.Close()
	
	h.clients[conn] = true
	
	// Send initial state
	conn.WriteJSON(map[string]interface{}{
		"type": "connected",
		"data": "BIM WebSocket connected",
	})
	
	// Handle incoming messages
	for {
		var msg map[string]interface{}
		err := conn.ReadJSON(&msg)
		if err != nil {
			delete(h.clients, conn)
			break
		}
		
		// Process message (simplified)
		switch msg["type"] {
		case "ping":
			conn.WriteJSON(map[string]string{"type": "pong"})
		}
	}
}

func (h *BIMHandler) handleBroadcast() {
	for {
		update := <-h.broadcast
		
		// Send to all connected clients
		for client := range h.clients {
			err := client.WriteJSON(update)
			if err != nil {
				client.Close()
				delete(h.clients, client)
			}
		}
	}
}

func (h *BIMHandler) subscribeToModel() {
	updates := h.model.Subscribe()
	
	for update := range updates {
		h.broadcast <- update
	}
}

// DeleteObject handles object deletion
func (h *BIMHandler) DeleteObject(w http.ResponseWriter, r *http.Request) {
	objectID := chi.URLParam(r, "objectID")
	
	// Find and delete object (simplified)
	deleted := false
	
	for _, floor := range h.model.Floors {
		// Check walls
		for i, wall := range floor.Walls {
			if wall.ID == objectID {
				// Remove wall
				floor.Walls = append(floor.Walls[:i], floor.Walls[i+1:]...)
				deleted = true
				
				// Broadcast deletion
				h.broadcast <- bim.Update{
					Type:     "object_deleted",
					ObjectID: objectID,
					Data:     map[string]string{"id": objectID},
				}
				break
			}
		}
	}
	
	if !deleted {
		http.Error(w, "Object not found", http.StatusNotFound)
		return
	}
	
	w.WriteHeader(http.StatusNoContent)
}

// UpdateObject handles object property updates
func (h *BIMHandler) UpdateObject(w http.ResponseWriter, r *http.Request) {
	objectID := chi.URLParam(r, "objectID")
	
	// Parse form values (HTMX sends as form data)
	r.ParseForm()
	
	// Find and update object
	for _, floor := range h.model.Floors {
		for _, wall := range floor.Walls {
			if wall.ID == objectID {
				// Update properties based on form data
				if thickness := r.FormValue("thickness"); thickness != "" {
					if val, err := strconv.ParseFloat(thickness, 64); err == nil {
						wall.Thickness = val
					}
				}
				
				if wallType := r.FormValue("type"); wallType != "" {
					if wallType == "exterior" {
						wall.Type = bim.WallTypeExterior
					} else {
						wall.Type = bim.WallTypeInterior
					}
				}
				
				// Mark floor as dirty for re-render
				floor.isDirty = true
				
				// Broadcast update
				h.broadcast <- bim.Update{
					Type:     "object_updated",
					ObjectID: objectID,
					Data:     wall,
				}
				
				// Return updated properties panel
				html := h.renderWallProperties(wall)
				w.Header().Set("Content-Type", "text/html")
				w.Write([]byte(html))
				return
			}
		}
	}
	
	http.Error(w, "Object not found", http.StatusNotFound)
}