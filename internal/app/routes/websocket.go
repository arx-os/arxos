package routes

import (
	"encoding/json"
	"net/http"

	"github.com/arx-os/arxos/internal/app/handlers"
	"github.com/arx-os/arxos/internal/app/types"
	"github.com/arx-os/arxos/internal/common/logger"
	"github.com/arx-os/arxos/internal/infra/messaging"
	"github.com/go-chi/chi/v5"
)

// WebSocketRoutes sets up WebSocket routes following Clean Architecture principles
type WebSocketRoutes struct {
	router chi.Router
	hub    *messaging.WebSocketHub
	logger logger.Logger
}

// NewWebSocketRoutes creates a new WebSocket routes handler
func NewWebSocketRoutes(services *types.Services, logger logger.Logger) *WebSocketRoutes {
	// Create WebSocket hub
	hub := messaging.NewWebSocketHub(messaging.DefaultWebSocketConfig())

	// Start the hub in a goroutine
	go hub.Run()

	return &WebSocketRoutes{
		router: chi.NewRouter(),
		hub:    hub,
		logger: logger,
	}
}

// SetupRoutes configures all WebSocket routes
func (ws *WebSocketRoutes) SetupRoutes(services *types.Services) {
	// Create WebSocket handler
	wsHandler := handlers.NewWebSocketHandler(services, ws.hub, ws.logger)

	// WebSocket middleware
	ws.router.Use(ws.corsMiddleware())
	ws.router.Use(ws.loggingMiddleware())

	// Building monitoring routes
	ws.router.Route("/buildings", func(r chi.Router) {
		r.Get("/{buildingID}/monitor", wsHandler.HandleWebSocket)
		r.Get("/{buildingID}/updates", wsHandler.HandleBuildingUpdates)
	})

	// Equipment monitoring routes
	ws.router.Route("/equipment", func(r chi.Router) {
		r.Get("/{equipmentID}/monitor", wsHandler.HandleEquipmentMonitoring)
	})

	// Spatial queries routes
	ws.router.Route("/spatial", func(r chi.Router) {
		r.Get("/queries", wsHandler.HandleSpatialQueries)
	})

	// Analytics routes
	ws.router.Route("/analytics", func(r chi.Router) {
		r.Get("/realtime", wsHandler.HandleAnalytics)
	})

	// Workflow routes
	ws.router.Route("/workflows", func(r chi.Router) {
		r.Get("/{workflowID}/updates", wsHandler.HandleWorkflowUpdates)
	})

	// WebSocket statistics route
	ws.router.Get("/stats", func(w http.ResponseWriter, r *http.Request) {
		stats := wsHandler.GetWebSocketStats()
		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(stats)
	})
}

// GetRouter returns the configured router
func (ws *WebSocketRoutes) GetRouter() chi.Router {
	return ws.router
}

// GetHub returns the WebSocket hub for external access
func (ws *WebSocketRoutes) GetHub() *messaging.WebSocketHub {
	return ws.hub
}

// Middleware functions
func (ws *WebSocketRoutes) corsMiddleware() func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			// Set CORS headers for WebSocket connections
			w.Header().Set("Access-Control-Allow-Origin", "*")
			w.Header().Set("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
			w.Header().Set("Access-Control-Allow-Headers", "Accept, Authorization, Content-Type, X-CSRF-Token, X-User-ID, X-Room")
			w.Header().Set("Access-Control-Allow-Credentials", "true")

			// Handle preflight requests
			if r.Method == "OPTIONS" {
				w.WriteHeader(http.StatusOK)
				return
			}

			next.ServeHTTP(w, r)
		})
	}
}

func (ws *WebSocketRoutes) loggingMiddleware() func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			// Log WebSocket connection attempts
			// Note: Actual WebSocket upgrade logging happens in the handler
			next.ServeHTTP(w, r)
		})
	}
}
