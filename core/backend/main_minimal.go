package main

import (
	"database/sql"
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"os"
	"time"

	"github.com/go-chi/chi/v5"
	"github.com/go-chi/chi/v5/middleware"
	"github.com/gorilla/websocket"
	"github.com/joho/godotenv"
	_ "github.com/lib/pq"
	"github.com/rs/cors"
)

func main() {
	// Load environment variables
	godotenv.Load()

	// Database connection
	dbURL := os.Getenv("DATABASE_URL")
	if dbURL == "" {
		// Use the existing arxos_db_pg17 database with current user
		dbURL = "postgres://joelpate@localhost/arxos_db_pg17?sslmode=disable"
	}

	db, err := sql.Open("postgres", dbURL)
	if err != nil {
		log.Printf("Warning: Database connection failed: %v", err)
		log.Println("Running without database - demo mode")
		db = nil
	} else {
		if err := db.Ping(); err != nil {
			log.Printf("Warning: Database ping failed: %v", err)
			db = nil
		} else {
			log.Println("✅ Database connected successfully")
		}
	}

	// Initialize services
	var tileService *TileService
	if db != nil {
		tileService = NewTileService(db)
		log.Println("✅ Tile service initialized with database")
	} else {
		tileService = NewTileService(nil)
		log.Println("⚠️  Tile service running in demo mode")
	}

	// Initialize WebSocket hub
	wsHub := NewHub()
	go wsHub.Run()
	log.Println("✅ WebSocket hub started")

	// Initialize PDF upload handler
	pdfHandler := NewPDFUploadHandler(db, tileService, wsHub)
	log.Println("✅ PDF upload handler initialized")

	// Setup router
	r := chi.NewRouter()
	r.Use(middleware.Logger)
	r.Use(middleware.Recoverer)
	r.Use(cors.AllowAll().Handler)

	// Health check
	r.Get("/health", func(w http.ResponseWriter, r *http.Request) {
		status := map[string]interface{}{
			"status": "healthy",
			"time":   time.Now(),
			"services": map[string]bool{
				"database":  db != nil,
				"tiles":     true,
				"websocket": true,
			},
		}
		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(status)
	})

	// API routes
	r.Route("/api", func(r chi.Router) {
		// Tile service endpoints
		r.Get("/tiles/{zoom}/{x}/{y}", func(w http.ResponseWriter, r *http.Request) {
			zoom := chi.URLParam(r, "zoom")
			x := chi.URLParam(r, "x")
			y := chi.URLParam(r, "y")

			var zoomInt, xInt, yInt int
			fmt.Sscanf(zoom, "%d", &zoomInt)
			fmt.Sscanf(x, "%d", &xInt)
			fmt.Sscanf(y, "%d", &yInt)

			objects, err := tileService.GetTile(zoomInt, xInt, yInt)
			if err != nil {
				http.Error(w, err.Error(), http.StatusInternalServerError)
				return
			}

			w.Header().Set("Content-Type", "application/json")
			w.Header().Set("Cache-Control", "public, max-age=300")
			json.NewEncoder(w).Encode(objects)
		})

		// Get all ArxObjects (for testing)
		r.Get("/arxobjects", func(w http.ResponseWriter, r *http.Request) {
			objects := tileService.GetAllObjects()
			w.Header().Set("Content-Type", "application/json")
			json.NewEncoder(w).Encode(objects)
		})

		// Create ArxObject
		r.Post("/arxobjects", func(w http.ResponseWriter, r *http.Request) {
			var obj ArxObject
			if err := json.NewDecoder(r.Body).Decode(&obj); err != nil {
				http.Error(w, err.Error(), http.StatusBadRequest)
				return
			}

			if err := tileService.CreateObject(&obj); err != nil {
				http.Error(w, err.Error(), http.StatusInternalServerError)
				return
			}

			// Broadcast update via WebSocket
			update := ArxObjectUpdate{
				Action: "create",
				Object: obj,
			}
			if data, err := json.Marshal(update); err == nil {
				wsHub.broadcast <- data
			}

			w.Header().Set("Content-Type", "application/json")
			json.NewEncoder(w).Encode(obj)
		})

		// PDF upload endpoint
		r.Post("/upload/pdf", pdfHandler.HandleUpload)

		// Building info
		r.Get("/buildings", func(w http.ResponseWriter, r *http.Request) {
			buildings := []map[string]interface{}{
				{
					"id":          "1",
					"name":        "Office Building",
					"floors":      5,
					"area":        50000,
					"objects":     1247,
					"confidence":  0.95,
					"created_at":  time.Now(),
				},
				{
					"id":          "2",
					"name":        "Hospital Complex",
					"floors":      8,
					"area":        120000,
					"objects":     3892,
					"confidence":  0.87,
					"created_at":  time.Now(),
				},
			}
			w.Header().Set("Content-Type", "application/json")
			json.NewEncoder(w).Encode(buildings)
		})
	})

	// WebSocket endpoint
	r.HandleFunc("/ws", func(w http.ResponseWriter, r *http.Request) {
		upgrader := websocket.Upgrader{
			CheckOrigin: func(r *http.Request) bool {
				return true // Allow all origins in development
			},
		}

		conn, err := upgrader.Upgrade(w, r, nil)
		if err != nil {
			log.Printf("WebSocket upgrade failed: %v", err)
			return
		}

		client := &Client{
			hub:  wsHub,
			conn: conn,
			send: make(chan []byte, 256),
		}

		client.hub.register <- client
		go client.writePump()
		go client.readPump()
	})

	// Static file server for HTML files
	r.Get("/*", func(w http.ResponseWriter, r *http.Request) {
		http.ServeFile(w, r, "../../"+r.URL.Path)
	})

	// Start server
	port := os.Getenv("PORT")
	if port == "" {
		port = "8080"
	}

	log.Printf("🚀 Server starting on http://localhost:%s", port)
	log.Println("📊 Health check: http://localhost:" + port + "/health")
	log.Println("🗺️  Tiles API: http://localhost:" + port + "/api/tiles/{z}/{x}/{y}")
	log.Println("🔌 WebSocket: ws://localhost:" + port + "/ws")
	
	if err := http.ListenAndServe(":"+port, r); err != nil {
		log.Fatalf("Server failed: %v", err)
	}
}