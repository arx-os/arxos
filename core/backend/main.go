package main

import (
	"log"
	"net/http"
	"time"

	"github.com/go-chi/chi/v5"
	chimiddleware "github.com/go-chi/chi/v5/middleware"
	"github.com/rs/cors"
)

func main() {
	log.Println("🚀 Starting ARXOS backend server...")

	// Set up router
	r := chi.NewRouter()
	r.Use(chimiddleware.Logger)
	r.Use(cors.AllowAll().Handler)

	// Add request logging middleware
	r.Use(func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			start := time.Now()

			// Call next handler
			next.ServeHTTP(w, r)

			// Log request
			duration := time.Since(start)
			log.Printf("Request: %s %s - Duration: %v", r.Method, r.URL.Path, duration)
		})
	})

	// TODO: Serve main application interface
	// For now, redirect to API health check
	r.Get("/", func(w http.ResponseWriter, r *http.Request) {
		http.Redirect(w, r, "/api/health", http.StatusTemporaryRedirect)
	})

	r.Route("/api", func(r chi.Router) {
		// Public health check endpoint
		r.Get("/health", func(w http.ResponseWriter, r *http.Request) {
			w.Header().Set("Content-Type", "application/json")
			w.WriteHeader(http.StatusOK)
			w.Write([]byte(`{"status":"ok","message":"ARXOS backend is running"}`))
		})

		// SQLite test endpoints (for testing without PostgreSQL)
		r.Get("/test/sqlite/db", func(w http.ResponseWriter, r *http.Request) {
			w.Header().Set("Content-Type", "application/json")
			w.WriteHeader(http.StatusOK)
			w.Write([]byte(`{"success":true,"message":"SQLite test endpoint ready"}`))
		})

		r.Get("/test/sqlite/arxobject-pipeline", func(w http.ResponseWriter, r *http.Request) {
			w.Header().Set("Content-Type", "application/json")
			w.WriteHeader(http.StatusOK)
			w.Write([]byte(`{"success":true,"message":"ArxObject pipeline test endpoint ready"}`))
		})

		r.Post("/test/sqlite/pdf-upload", func(w http.ResponseWriter, r *http.Request) {
			w.Header().Set("Content-Type", "application/json")
			w.WriteHeader(http.StatusOK)
			w.Write([]byte(`{"success":true,"message":"PDF upload test endpoint ready"}`))
		})
	})

	// Start server
	log.Println("🚀 Server running on :3000")
	if err := http.ListenAndServe(":3000", r); err != nil {
		log.Fatalf("Server failed: %v", err)
	}
}
