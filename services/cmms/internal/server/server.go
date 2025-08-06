package server

import (
	"arx-cmms/pkg/cmms"
	"arx-cmms/pkg/models"
	"context"
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"strconv"
	"time"

	"github.com/gorilla/mux"
)

// Server represents the CMMS HTTP server
type Server struct {
	client *cmms.Client
	router *mux.Router
	server *http.Server
}

// NewServer creates a new CMMS HTTP server
func NewServer(client *cmms.Client, port int) *Server {
	router := mux.NewRouter()
	
	server := &Server{
		client: client,
		router: router,
		server: &http.Server{
			Addr:         fmt.Sprintf(":%d", port),
			Handler:      router,
			ReadTimeout:  15 * time.Second,
			WriteTimeout: 15 * time.Second,
			IdleTimeout:  60 * time.Second,
		},
	}
	
	server.setupRoutes()
	return server
}

// setupRoutes configures all the API routes
func (s *Server) setupRoutes() {
	// Health check
	s.router.HandleFunc("/health", s.healthHandler).Methods("GET")
	
	// API routes
	api := s.router.PathPrefix("/api/cmms").Subrouter()
	
	// Connections
	api.HandleFunc("/connections", s.listConnectionsHandler).Methods("GET")
	api.HandleFunc("/connections", s.createConnectionHandler).Methods("POST")
	api.HandleFunc("/connections/{id}", s.getConnectionHandler).Methods("GET")
	api.HandleFunc("/connections/{id}", s.updateConnectionHandler).Methods("PUT")
	api.HandleFunc("/connections/{id}", s.deleteConnectionHandler).Methods("DELETE")
	api.HandleFunc("/connections/{id}/test", s.testConnectionHandler).Methods("POST")
	api.HandleFunc("/connections/{id}/sync", s.syncConnectionHandler).Methods("POST")
	
	// Mappings
	api.HandleFunc("/connections/{id}/mappings", s.getMappingsHandler).Methods("GET")
	api.HandleFunc("/connections/{id}/mappings", s.createMappingHandler).Methods("POST")
	
	// Sync logs
	api.HandleFunc("/connections/{id}/sync-logs", s.getSyncLogsHandler).Methods("GET")
	
	// Maintenance data
	api.HandleFunc("/maintenance-schedules", s.getMaintenanceSchedulesHandler).Methods("GET")
	api.HandleFunc("/work-orders", s.getWorkOrdersHandler).Methods("GET")
	api.HandleFunc("/equipment-specs", s.getEquipmentSpecsHandler).Methods("GET")
}

// Start starts the HTTP server
func (s *Server) Start() error {
	log.Printf("🚀 CMMS HTTP Server starting on port %s", s.server.Addr)
	return s.server.ListenAndServe()
}

// Shutdown gracefully shuts down the server
func (s *Server) Shutdown(ctx context.Context) error {
	return s.server.Shutdown(ctx)
}

// healthHandler handles health check requests
func (s *Server) healthHandler(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(map[string]interface{}{
		"status":    "healthy",
		"timestamp": time.Now().UTC(),
		"service":   "cmms",
	})
}

// listConnectionsHandler handles GET /api/cmms/connections
func (s *Server) listConnectionsHandler(w http.ResponseWriter, r *http.Request) {
	connections, err := s.client.ListConnections()
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(connections)
}

// createConnectionHandler handles POST /api/cmms/connections
func (s *Server) createConnectionHandler(w http.ResponseWriter, r *http.Request) {
	var conn models.CMMSConnection
	if err := json.NewDecoder(r.Body).Decode(&conn); err != nil {
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}
	
	if err := s.client.CreateConnection(&conn); err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusCreated)
	json.NewEncoder(w).Encode(conn)
}

// getConnectionHandler handles GET /api/cmms/connections/{id}
func (s *Server) getConnectionHandler(w http.ResponseWriter, r *http.Request) {
	vars := mux.Vars(r)
	id, err := strconv.Atoi(vars["id"])
	if err != nil {
		http.Error(w, "Invalid connection ID", http.StatusBadRequest)
		return
	}
	
	conn, err := s.client.GetConnection(id)
	if err != nil {
		http.Error(w, err.Error(), http.StatusNotFound)
		return
	}
	
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(conn)
}

// updateConnectionHandler handles PUT /api/cmms/connections/{id}
func (s *Server) updateConnectionHandler(w http.ResponseWriter, r *http.Request) {
	vars := mux.Vars(r)
	id, err := strconv.Atoi(vars["id"])
	if err != nil {
		http.Error(w, "Invalid connection ID", http.StatusBadRequest)
		return
	}
	
	var conn models.CMMSConnection
	if err := json.NewDecoder(r.Body).Decode(&conn); err != nil {
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}
	
	conn.ID = id
	if err := s.client.UpdateConnection(&conn); err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(conn)
}

// deleteConnectionHandler handles DELETE /api/cmms/connections/{id}
func (s *Server) deleteConnectionHandler(w http.ResponseWriter, r *http.Request) {
	vars := mux.Vars(r)
	id, err := strconv.Atoi(vars["id"])
	if err != nil {
		http.Error(w, "Invalid connection ID", http.StatusBadRequest)
		return
	}
	
	if err := s.client.DeleteConnection(id); err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	
	w.WriteHeader(http.StatusNoContent)
}

// testConnectionHandler handles POST /api/cmms/connections/{id}/test
func (s *Server) testConnectionHandler(w http.ResponseWriter, r *http.Request) {
	vars := mux.Vars(r)
	id, err := strconv.Atoi(vars["id"])
	if err != nil {
		http.Error(w, "Invalid connection ID", http.StatusBadRequest)
		return
	}
	
	if err := s.client.TestConnection(id); err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{
		"status":  "success",
		"message": "Connection test successful",
	})
}

// syncConnectionHandler handles POST /api/cmms/connections/{id}/sync
func (s *Server) syncConnectionHandler(w http.ResponseWriter, r *http.Request) {
	vars := mux.Vars(r)
	id, err := strconv.Atoi(vars["id"])
	if err != nil {
		http.Error(w, "Invalid connection ID", http.StatusBadRequest)
		return
	}
	
	var req struct {
		SyncType string `json:"sync_type"`
	}
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}
	
	ctx := r.Context()
	if err := s.client.SyncConnection(ctx, id, req.SyncType); err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{
		"status":  "success",
		"message": "Sync completed successfully",
	})
}

// getMappingsHandler handles GET /api/cmms/connections/{id}/mappings
func (s *Server) getMappingsHandler(w http.ResponseWriter, r *http.Request) {
	vars := mux.Vars(r)
	id, err := strconv.Atoi(vars["id"])
	if err != nil {
		http.Error(w, "Invalid connection ID", http.StatusBadRequest)
		return
	}
	
	mappings, err := s.client.GetMappings(id)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(mappings)
}

// createMappingHandler handles POST /api/cmms/connections/{id}/mappings
func (s *Server) createMappingHandler(w http.ResponseWriter, r *http.Request) {
	vars := mux.Vars(r)
	id, err := strconv.Atoi(vars["id"])
	if err != nil {
		http.Error(w, "Invalid connection ID", http.StatusBadRequest)
		return
	}
	
	var mapping models.CMMSMapping
	if err := json.NewDecoder(r.Body).Decode(&mapping); err != nil {
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}
	
	mapping.CMMSConnectionID = id
	if err := s.client.CreateMapping(&mapping); err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusCreated)
	json.NewEncoder(w).Encode(mapping)
}

// getSyncLogsHandler handles GET /api/cmms/connections/{id}/sync-logs
func (s *Server) getSyncLogsHandler(w http.ResponseWriter, r *http.Request) {
	vars := mux.Vars(r)
	id, err := strconv.Atoi(vars["id"])
	if err != nil {
		http.Error(w, "Invalid connection ID", http.StatusBadRequest)
		return
	}
	
	limit := 100 // default limit
	if limitStr := r.URL.Query().Get("limit"); limitStr != "" {
		if l, err := strconv.Atoi(limitStr); err == nil {
			limit = l
		}
	}
	
	logs, err := s.client.GetSyncLogs(id, limit)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(logs)
}

// getMaintenanceSchedulesHandler handles GET /api/cmms/maintenance-schedules
func (s *Server) getMaintenanceSchedulesHandler(w http.ResponseWriter, r *http.Request) {
	// TODO: Implement maintenance schedules retrieval
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode([]interface{}{})
}

// getWorkOrdersHandler handles GET /api/cmms/work-orders
func (s *Server) getWorkOrdersHandler(w http.ResponseWriter, r *http.Request) {
	// TODO: Implement work orders retrieval
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode([]interface{}{})
}

// getEquipmentSpecsHandler handles GET /api/cmms/equipment-specs
func (s *Server) getEquipmentSpecsHandler(w http.ResponseWriter, r *http.Request) {
	// TODO: Implement equipment specs retrieval
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode([]interface{}{})
} 