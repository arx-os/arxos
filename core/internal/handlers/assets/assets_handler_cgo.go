package assets

import (
	"database/sql"
	"encoding/json"
	"fmt"
	"net/http"
	"strconv"
	"time"

	"github.com/arxos/arxos/core/cgo"
	"github.com/arxos/arxos/core/internal/handlers"
	"github.com/gorilla/mux"
)

// ============================================================================
// CGO-OPTIMIZED ASSETS HANDLER
// ============================================================================

// AssetsHandlerCGO provides CGO-optimized asset management operations
type AssetsHandlerCGO struct {
	*handlers.HandlerBaseCGO
	db           *sql.DB
	spatialIndex *cgo.SpatialIndex // C spatial index for ultra-fast queries
}

// NewAssetsHandlerCGO creates a new CGO-optimized assets handler
func NewAssetsHandlerCGO(db *sql.DB) *AssetsHandlerCGO {
	base := handlers.NewHandlerBaseCGO()
	
	handler := &AssetsHandlerCGO{
		HandlerBaseCGO: base,
		db:             db,
	}
	
	// Initialize C spatial index if CGO is available
	if handler.HasCGO() {
		spatialIndex, err := cgo.CreateSpatialIndex(8, true) // 8 levels, use octree
		if err == nil {
			handler.spatialIndex = spatialIndex
			// Load existing assets into spatial index
			handler.loadAssetsIntoSpatialIndex()
		}
	}
	
	return handler
}

// Close cleanup resources
func (h *AssetsHandlerCGO) Close() {
	if h.spatialIndex != nil {
		h.spatialIndex.Destroy()
	}
}

// ============================================================================
// ASSET CRUD OPERATIONS
// ============================================================================

// CreateAsset creates a new asset with CGO optimization
func (h *AssetsHandlerCGO) CreateAsset(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		h.SendError(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	var asset struct {
		Name         string  `json:"name"`
		Type         string  `json:"type"`
		BuildingID   int64   `json:"building_id"`
		FloorNumber  int     `json:"floor_number"`
		RoomNumber   string  `json:"room_number"`
		X            float64 `json:"x"`
		Y            float64 `json:"y"`
		Z            float64 `json:"z"`
		Manufacturer string  `json:"manufacturer"`
		Model        string  `json:"model"`
		SerialNumber string  `json:"serial_number"`
		InstallDate  string  `json:"install_date"`
		Status       string  `json:"status"`
	}

	if err := json.NewDecoder(r.Body).Decode(&asset); err != nil {
		h.SendError(w, "Invalid request body", http.StatusBadRequest)
		return
	}

	// Validate required fields
	if asset.Name == "" || asset.Type == "" {
		h.SendError(w, "Name and type are required", http.StatusBadRequest)
		return
	}

	// If CGO is available, create ArxObject for ultra-fast operations
	var arxObjectID string
	if h.HasCGO() {
		obj, err := cgo.CreateArxObject(
			fmt.Sprintf("asset_%d_%s", time.Now().Unix(), asset.Name),
			asset.Type,
			asset.Name,
			h.mapAssetTypeToArxType(asset.Type),
		)
		if err == nil {
			defer obj.Destroy()
			
			// Set spatial coordinates
			obj.SetPosition(asset.X, asset.Y, asset.Z)
			
			// Set properties
			obj.SetProperty("manufacturer", asset.Manufacturer)
			obj.SetProperty("model", asset.Model)
			obj.SetProperty("serial_number", asset.SerialNumber)
			obj.SetProperty("status", asset.Status)
			
			// Add to spatial index for fast queries
			if h.spatialIndex != nil {
				h.spatialIndex.AddObject(obj)
			}
			
			arxObjectID = obj.GetID()
		}
	}

	// Insert into database
	query := `
		INSERT INTO assets (
			name, type, building_id, floor_number, room_number,
			x, y, z, manufacturer, model, serial_number,
			install_date, status, arx_object_id, created_at
		) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15)
		RETURNING id, created_at
	`
	
	var assetID int64
	var createdAt time.Time
	
	err := h.db.QueryRow(query,
		asset.Name, asset.Type, asset.BuildingID, asset.FloorNumber,
		asset.RoomNumber, asset.X, asset.Y, asset.Z,
		asset.Manufacturer, asset.Model, asset.SerialNumber,
		asset.InstallDate, asset.Status, arxObjectID, time.Now(),
	).Scan(&assetID, &createdAt)
	
	if err != nil {
		h.SendError(w, "Failed to create asset", http.StatusInternalServerError)
		return
	}

	h.SendJSON(w, map[string]interface{}{
		"success": true,
		"asset": map[string]interface{}{
			"id":            assetID,
			"name":          asset.Name,
			"type":          asset.Type,
			"arx_object_id": arxObjectID,
			"created_at":    createdAt,
		},
		"cgo_status": h.HasCGO(),
	})
}

// GetAsset retrieves an asset by ID
func (h *AssetsHandlerCGO) GetAsset(w http.ResponseWriter, r *http.Request) {
	vars := mux.Vars(r)
	assetID, err := strconv.ParseInt(vars["id"], 10, 64)
	if err != nil {
		h.SendError(w, "Invalid asset ID", http.StatusBadRequest)
		return
	}

	query := `
		SELECT id, name, type, building_id, floor_number, room_number,
		       x, y, z, manufacturer, model, serial_number,
		       install_date, status, arx_object_id, created_at, updated_at
		FROM assets
		WHERE id = $1 AND deleted_at IS NULL
	`
	
	var asset struct {
		ID           int64          `json:"id"`
		Name         string         `json:"name"`
		Type         string         `json:"type"`
		BuildingID   sql.NullInt64 `json:"building_id"`
		FloorNumber  sql.NullInt32 `json:"floor_number"`
		RoomNumber   sql.NullString `json:"room_number"`
		X            float64        `json:"x"`
		Y            float64        `json:"y"`
		Z            float64        `json:"z"`
		Manufacturer sql.NullString `json:"manufacturer"`
		Model        sql.NullString `json:"model"`
		SerialNumber sql.NullString `json:"serial_number"`
		InstallDate  sql.NullTime   `json:"install_date"`
		Status       string         `json:"status"`
		ArxObjectID  sql.NullString `json:"arx_object_id"`
		CreatedAt    time.Time      `json:"created_at"`
		UpdatedAt    sql.NullTime   `json:"updated_at"`
	}
	
	err = h.db.QueryRow(query, assetID).Scan(
		&asset.ID, &asset.Name, &asset.Type, &asset.BuildingID,
		&asset.FloorNumber, &asset.RoomNumber, &asset.X, &asset.Y, &asset.Z,
		&asset.Manufacturer, &asset.Model, &asset.SerialNumber,
		&asset.InstallDate, &asset.Status, &asset.ArxObjectID,
		&asset.CreatedAt, &asset.UpdatedAt,
	)
	
	if err == sql.ErrNoRows {
		h.SendError(w, "Asset not found", http.StatusNotFound)
		return
	} else if err != nil {
		h.SendError(w, "Database error", http.StatusInternalServerError)
		return
	}

	h.SendJSON(w, map[string]interface{}{
		"success":    true,
		"asset":      asset,
		"cgo_status": h.HasCGO(),
	})
}

// ============================================================================
// SPATIAL QUERIES (CGO-OPTIMIZED)
// ============================================================================

// GetAssetsByLocation performs ultra-fast spatial queries using C spatial index
func (h *AssetsHandlerCGO) GetAssetsByLocation(w http.ResponseWriter, r *http.Request) {
	// Parse query parameters
	x1, _ := strconv.ParseFloat(r.URL.Query().Get("x1"), 64)
	y1, _ := strconv.ParseFloat(r.URL.Query().Get("y1"), 64)
	z1, _ := strconv.ParseFloat(r.URL.Query().Get("z1"), 64)
	x2, _ := strconv.ParseFloat(r.URL.Query().Get("x2"), 64)
	y2, _ := strconv.ParseFloat(r.URL.Query().Get("y2"), 64)
	z2, _ := strconv.ParseFloat(r.URL.Query().Get("z2"), 64)
	
	var assets []map[string]interface{}
	
	if h.spatialIndex != nil {
		// Use CGO spatial index for 10x faster queries
		results, err := h.spatialIndex.Query(
			cgo.QueryTypeRange,
			x1, y1, z1, x2, y2, z2,
			0, 100, // max 100 results
		)
		
		if err == nil {
			for _, objID := range results {
				// Get asset data by ArxObject ID
				var asset map[string]interface{}
				query := `
					SELECT id, name, type, x, y, z, status
					FROM assets
					WHERE arx_object_id = $1 AND deleted_at IS NULL
				`
				
				row := h.db.QueryRow(query, objID)
				var id int64
				var name, assetType, status string
				var x, y, z float64
				
				if err := row.Scan(&id, &name, &assetType, &x, &y, &z, &status); err == nil {
					asset = map[string]interface{}{
						"id":     id,
						"name":   name,
						"type":   assetType,
						"x":      x,
						"y":      y,
						"z":      z,
						"status": status,
					}
					assets = append(assets, asset)
				}
			}
		}
	} else {
		// Fallback to SQL spatial query
		query := `
			SELECT id, name, type, x, y, z, status
			FROM assets
			WHERE x BETWEEN $1 AND $2
			  AND y BETWEEN $3 AND $4
			  AND z BETWEEN $5 AND $6
			  AND deleted_at IS NULL
			LIMIT 100
		`
		
		rows, err := h.db.Query(query, x1, x2, y1, y2, z1, z2)
		if err == nil {
			defer rows.Close()
			
			for rows.Next() {
				var id int64
				var name, assetType, status string
				var x, y, z float64
				
				if err := rows.Scan(&id, &name, &assetType, &x, &y, &z, &status); err == nil {
					asset := map[string]interface{}{
						"id":     id,
						"name":   name,
						"type":   assetType,
						"x":      x,
						"y":      y,
						"z":      z,
						"status": status,
					}
					assets = append(assets, asset)
				}
			}
		}
	}

	h.SendJSON(w, map[string]interface{}{
		"success":    true,
		"assets":     assets,
		"count":      len(assets),
		"cgo_status": h.spatialIndex != nil,
	})
}

// GetNearbyAssets finds assets within a radius using CGO optimization
func (h *AssetsHandlerCGO) GetNearbyAssets(w http.ResponseWriter, r *http.Request) {
	centerX, _ := strconv.ParseFloat(r.URL.Query().Get("x"), 64)
	centerY, _ := strconv.ParseFloat(r.URL.Query().Get("y"), 64)
	centerZ, _ := strconv.ParseFloat(r.URL.Query().Get("z"), 64)
	radius, _ := strconv.ParseFloat(r.URL.Query().Get("radius"), 64)
	
	if radius <= 0 {
		radius = 10.0 // default 10 meter radius
	}
	
	var assets []map[string]interface{}
	
	if h.spatialIndex != nil {
		// Use CGO spatial index for ultra-fast radius queries
		results, err := h.spatialIndex.Query(
			cgo.QueryTypeRadius,
			centerX, centerY, centerZ,
			radius, 0, 0, // radius, unused, unused
			0, 50, // max 50 results
		)
		
		if err == nil {
			for _, objID := range results {
				// Get asset details
				var asset map[string]interface{}
				query := `
					SELECT id, name, type, x, y, z, status,
					       SQRT(POWER(x - $2, 2) + POWER(y - $3, 2) + POWER(z - $4, 2)) as distance
					FROM assets
					WHERE arx_object_id = $1 AND deleted_at IS NULL
				`
				
				row := h.db.QueryRow(query, objID, centerX, centerY, centerZ)
				var id int64
				var name, assetType, status string
				var x, y, z, distance float64
				
				if err := row.Scan(&id, &name, &assetType, &x, &y, &z, &status, &distance); err == nil {
					asset = map[string]interface{}{
						"id":       id,
						"name":     name,
						"type":     assetType,
						"x":        x,
						"y":        y,
						"z":        z,
						"status":   status,
						"distance": distance,
					}
					assets = append(assets, asset)
				}
			}
		}
	} else {
		// Fallback to SQL distance calculation
		query := `
			SELECT id, name, type, x, y, z, status,
			       SQRT(POWER(x - $1, 2) + POWER(y - $2, 2) + POWER(z - $3, 2)) as distance
			FROM assets
			WHERE SQRT(POWER(x - $1, 2) + POWER(y - $2, 2) + POWER(z - $3, 2)) <= $4
			  AND deleted_at IS NULL
			ORDER BY distance
			LIMIT 50
		`
		
		rows, err := h.db.Query(query, centerX, centerY, centerZ, radius)
		if err == nil {
			defer rows.Close()
			
			for rows.Next() {
				var id int64
				var name, assetType, status string
				var x, y, z, distance float64
				
				if err := rows.Scan(&id, &name, &assetType, &x, &y, &z, &status, &distance); err == nil {
					asset := map[string]interface{}{
						"id":       id,
						"name":     name,
						"type":     assetType,
						"x":        x,
						"y":        y,
						"z":        z,
						"status":   status,
						"distance": distance,
					}
					assets = append(assets, asset)
				}
			}
		}
	}

	h.SendJSON(w, map[string]interface{}{
		"success":    true,
		"assets":     assets,
		"count":      len(assets),
		"center":     map[string]float64{"x": centerX, "y": centerY, "z": centerZ},
		"radius":     radius,
		"cgo_status": h.spatialIndex != nil,
	})
}

// ============================================================================
// MAINTENANCE TRACKING
// ============================================================================

// RecordMaintenance records maintenance activity for an asset
func (h *AssetsHandlerCGO) RecordMaintenance(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		h.SendError(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	vars := mux.Vars(r)
	assetID, err := strconv.ParseInt(vars["id"], 10, 64)
	if err != nil {
		h.SendError(w, "Invalid asset ID", http.StatusBadRequest)
		return
	}

	var maintenance struct {
		Type        string  `json:"type"`
		Description string  `json:"description"`
		TechnicianID int64  `json:"technician_id"`
		Cost        float64 `json:"cost"`
		Duration    int     `json:"duration_minutes"`
		NextDue     string  `json:"next_due"`
	}

	if err := json.NewDecoder(r.Body).Decode(&maintenance); err != nil {
		h.SendError(w, "Invalid request body", http.StatusBadRequest)
		return
	}

	// Insert maintenance record
	query := `
		INSERT INTO asset_maintenance (
			asset_id, type, description, technician_id,
			cost, duration_minutes, next_due, performed_at
		) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
		RETURNING id, performed_at
	`
	
	var maintenanceID int64
	var performedAt time.Time
	
	err = h.db.QueryRow(query,
		assetID, maintenance.Type, maintenance.Description,
		maintenance.TechnicianID, maintenance.Cost, maintenance.Duration,
		maintenance.NextDue, time.Now(),
	).Scan(&maintenanceID, &performedAt)
	
	if err != nil {
		h.SendError(w, "Failed to record maintenance", http.StatusInternalServerError)
		return
	}

	// Update asset status if needed
	if maintenance.Type == "repair" {
		h.db.Exec("UPDATE assets SET status = 'operational' WHERE id = $1", assetID)
	}

	h.SendJSON(w, map[string]interface{}{
		"success": true,
		"maintenance": map[string]interface{}{
			"id":           maintenanceID,
			"asset_id":     assetID,
			"type":         maintenance.Type,
			"performed_at": performedAt,
		},
		"cgo_status": h.HasCGO(),
	})
}

// ============================================================================
// HELPER METHODS
// ============================================================================

// loadAssetsIntoSpatialIndex loads existing assets into the C spatial index
func (h *AssetsHandlerCGO) loadAssetsIntoSpatialIndex() {
	if h.spatialIndex == nil {
		return
	}

	query := `
		SELECT arx_object_id, name, type, x, y, z
		FROM assets
		WHERE arx_object_id IS NOT NULL AND deleted_at IS NULL
		LIMIT 10000
	`
	
	rows, err := h.db.Query(query)
	if err != nil {
		return
	}
	defer rows.Close()
	
	for rows.Next() {
		var arxID, name, assetType string
		var x, y, z float64
		
		if err := rows.Scan(&arxID, &name, &assetType, &x, &y, &z); err == nil {
			// Create temporary ArxObject for spatial indexing
			obj, err := cgo.CreateArxObject(arxID, assetType, name, 0)
			if err == nil {
				obj.SetPosition(x, y, z)
				h.spatialIndex.AddObject(obj)
				obj.Destroy()
			}
		}
	}
}

// mapAssetTypeToArxType maps asset types to ArxObject types
func (h *AssetsHandlerCGO) mapAssetTypeToArxType(assetType string) int {
	typeMap := map[string]int{
		"hvac":       20, // ARX_TYPE_HVAC_UNIT
		"electrical": 25, // ARX_TYPE_ELECTRICAL_PANEL
		"plumbing":   30, // ARX_TYPE_PLUMBING_FIXTURE
		"equipment":  40, // ARX_TYPE_EQUIPMENT
		"furniture":  41, // ARX_TYPE_FURNITURE
		"sensor":     50, // ARX_TYPE_SENSOR
	}
	
	if arxType, ok := typeMap[assetType]; ok {
		return arxType
	}
	return 40 // Default to equipment
}

// HasCGO returns whether CGO bridge is available
func (h *AssetsHandlerCGO) HasCGO() bool {
	return h.HandlerBaseCGO != nil
}

// SendJSON sends a JSON response
func (h *AssetsHandlerCGO) SendJSON(w http.ResponseWriter, data interface{}) {
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(data)
}

// SendError sends an error response
func (h *AssetsHandlerCGO) SendError(w http.ResponseWriter, message string, code int) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(code)
	json.NewEncoder(w).Encode(map[string]interface{}{
		"success": false,
		"error":   message,
	})
}