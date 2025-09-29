package handlers

import (
	"net/http"

	"github.com/arx-os/arxos/internal/app/types"
	"github.com/arx-os/arxos/internal/common/logger"
	"github.com/arx-os/arxos/internal/infra/messaging"
)

// WebSocketHandler handles WebSocket connections following Clean Architecture principles
type WebSocketHandler struct {
	*BaseHandler
	hub *messaging.WebSocketHub
}

// NewWebSocketHandler creates a new WebSocket handler with dependency injection
func NewWebSocketHandler(services *types.Services, hub *messaging.WebSocketHub, logger logger.Logger) *WebSocketHandler {
	return &WebSocketHandler{
		BaseHandler: NewBaseHandler(services, logger),
		hub:         hub,
	}
}

// HandleWebSocket handles WebSocket connections for building monitoring
func (h *WebSocketHandler) HandleWebSocket(w http.ResponseWriter, r *http.Request) {
	h.LogRequest(r, "websocket_connection")

	// Extract building ID from URL path
	buildingID, err := h.GetPathParam(r, "buildingID")
	if err != nil {
		h.WriteErrorResponse(w, http.StatusBadRequest, "Building ID is required", err)
		return
	}

	// Validate building exists
	// Note: This would call the domain service to validate building existence
	// For now, we'll proceed with the connection

	// Set room based on building ID for targeted messaging
	r.Header.Set("X-Room", "building:"+buildingID)

	// Handle WebSocket upgrade
	if err := h.hub.HandleWebSocket(w, r); err != nil {
		h.LogError(r, "websocket_connection", err)
		h.WriteErrorResponse(w, http.StatusInternalServerError, "Failed to establish WebSocket connection", nil)
		return
	}

	h.logger.Info("WebSocket connection established", "building_id", buildingID)
}

// HandleBuildingUpdates handles WebSocket connections for building updates
func (h *WebSocketHandler) HandleBuildingUpdates(w http.ResponseWriter, r *http.Request) {
	h.LogRequest(r, "building_updates")

	// Extract building ID from URL path
	buildingID, err := h.GetPathParam(r, "buildingID")
	if err != nil {
		h.WriteErrorResponse(w, http.StatusBadRequest, "Building ID is required", err)
		return
	}

	// Set room for building-specific updates
	r.Header.Set("X-Room", "building_updates:"+buildingID)

	// Handle WebSocket upgrade
	if err := h.hub.HandleWebSocket(w, r); err != nil {
		h.LogError(r, "building_updates", err)
		h.WriteErrorResponse(w, http.StatusInternalServerError, "Failed to establish WebSocket connection", nil)
		return
	}

	h.logger.Info("Building updates WebSocket connection established", "building_id", buildingID)
}

// HandleEquipmentMonitoring handles WebSocket connections for equipment monitoring
func (h *WebSocketHandler) HandleEquipmentMonitoring(w http.ResponseWriter, r *http.Request) {
	h.LogRequest(r, "equipment_monitoring")

	// Extract equipment ID from URL path
	equipmentID, err := h.GetPathParam(r, "equipmentID")
	if err != nil {
		h.WriteErrorResponse(w, http.StatusBadRequest, "Equipment ID is required", err)
		return
	}

	// Set room for equipment-specific monitoring
	r.Header.Set("X-Room", "equipment:"+equipmentID)

	// Handle WebSocket upgrade
	if err := h.hub.HandleWebSocket(w, r); err != nil {
		h.LogError(r, "equipment_monitoring", err)
		h.WriteErrorResponse(w, http.StatusInternalServerError, "Failed to establish WebSocket connection", nil)
		return
	}

	h.logger.Info("Equipment monitoring WebSocket connection established", "equipment_id", equipmentID)
}

// HandleSpatialQueries handles WebSocket connections for real-time spatial queries
func (h *WebSocketHandler) HandleSpatialQueries(w http.ResponseWriter, r *http.Request) {
	h.LogRequest(r, "spatial_queries")

	// Extract query parameters
	queryType := h.GetQueryParam(r, "type")
	if queryType == "" {
		h.WriteErrorResponse(w, http.StatusBadRequest, "Query type is required", nil)
		return
	}

	// Set room based on query type
	r.Header.Set("X-Room", "spatial_queries:"+queryType)

	// Handle WebSocket upgrade
	if err := h.hub.HandleWebSocket(w, r); err != nil {
		h.LogError(r, "spatial_queries", err)
		h.WriteErrorResponse(w, http.StatusInternalServerError, "Failed to establish WebSocket connection", nil)
		return
	}

	h.logger.Info("Spatial queries WebSocket connection established", "query_type", queryType)
}

// HandleAnalytics handles WebSocket connections for real-time analytics
func (h *WebSocketHandler) HandleAnalytics(w http.ResponseWriter, r *http.Request) {
	h.LogRequest(r, "analytics")

	// Extract analytics parameters
	metricType := h.GetQueryParam(r, "metric")
	buildingID := h.GetQueryParam(r, "building_id")

	// Set room based on analytics type
	room := "analytics"
	if metricType != "" {
		room += ":" + metricType
	}
	if buildingID != "" {
		room += ":building:" + buildingID
	}
	r.Header.Set("X-Room", room)

	// Handle WebSocket upgrade
	if err := h.hub.HandleWebSocket(w, r); err != nil {
		h.LogError(r, "analytics", err)
		h.WriteErrorResponse(w, http.StatusInternalServerError, "Failed to establish WebSocket connection", nil)
		return
	}

	h.logger.Info("Analytics WebSocket connection established", "metric_type", metricType, "building_id", buildingID)
}

// HandleWorkflowUpdates handles WebSocket connections for workflow updates
func (h *WebSocketHandler) HandleWorkflowUpdates(w http.ResponseWriter, r *http.Request) {
	h.LogRequest(r, "workflow_updates")

	// Extract workflow ID from URL path
	workflowID, err := h.GetPathParam(r, "workflowID")
	if err != nil {
		h.WriteErrorResponse(w, http.StatusBadRequest, "Workflow ID is required", err)
		return
	}

	// Set room for workflow-specific updates
	r.Header.Set("X-Room", "workflow:"+workflowID)

	// Handle WebSocket upgrade
	if err := h.hub.HandleWebSocket(w, r); err != nil {
		h.LogError(r, "workflow_updates", err)
		h.WriteErrorResponse(w, http.StatusInternalServerError, "Failed to establish WebSocket connection", nil)
		return
	}

	h.logger.Info("Workflow updates WebSocket connection established", "workflow_id", workflowID)
}

// BroadcastBuildingUpdate broadcasts a building update to all connected clients
func (h *WebSocketHandler) BroadcastBuildingUpdate(buildingID string, update interface{}) error {
	room := "building:" + buildingID
	return h.hub.BroadcastToRoom(room, update)
}

// BroadcastEquipmentUpdate broadcasts an equipment update to all connected clients
func (h *WebSocketHandler) BroadcastEquipmentUpdate(equipmentID string, update interface{}) error {
	room := "equipment:" + equipmentID
	return h.hub.BroadcastToRoom(room, update)
}

// BroadcastSpatialUpdate broadcasts a spatial update to all connected clients
func (h *WebSocketHandler) BroadcastSpatialUpdate(queryType string, update interface{}) error {
	room := "spatial_queries:" + queryType
	return h.hub.BroadcastToRoom(room, update)
}

// BroadcastAnalyticsUpdate broadcasts an analytics update to all connected clients
func (h *WebSocketHandler) BroadcastAnalyticsUpdate(metricType, buildingID string, update interface{}) error {
	room := "analytics:" + metricType
	if buildingID != "" {
		room += ":building:" + buildingID
	}
	return h.hub.BroadcastToRoom(room, update)
}

// BroadcastWorkflowUpdate broadcasts a workflow update to all connected clients
func (h *WebSocketHandler) BroadcastWorkflowUpdate(workflowID string, update interface{}) error {
	room := "workflow:" + workflowID
	return h.hub.BroadcastToRoom(room, update)
}

// GetWebSocketStats returns WebSocket connection statistics
func (h *WebSocketHandler) GetWebSocketStats() map[string]interface{} {
	return h.hub.GetStats()
}
