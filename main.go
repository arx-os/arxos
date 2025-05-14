// main.go
package main

import (
	"log"
	"net/http"
	"os"
	"os/signal"
	"syscall"

	"arxline/db"
	"arxline/handlers"
	"arxline/middleware/auth"

	"github.com/go-chi/chi/v5"
	"github.com/go-chi/chi/v5/middleware"
	"github.com/rs/cors"
)

func main() {
	// Initialize database
	db.Connect()
	db.Migrate()

	// Set up router
	r := chi.NewRouter()
	r.Use(middleware.Logger)
	r.Use(cors.AllowAll().Handler)

	r.Route("/api", func(r chi.Router) {
		r.Post("/register", handlers.Register)
		r.Post("/login", handlers.Login)

		r.Group(func(r chi.Router) {
			r.Use(auth.RequireAuth)
			r.Get("/projects", handlers.ListProjects)
			r.Post("/projects", handlers.CreateProject)
			r.Get("/projects/{id}", handlers.GetProject)

			// New endpoints (stubs to be implemented)
			r.Get("/buildings", handlers.ListBuildings)
			r.Post("/buildings", handlers.CreateBuilding)
			r.Get("/buildings/{id}", handlers.GetBuilding)
			r.Put("/buildings/{id}", handlers.UpdateBuilding)
			r.Get("/buildings/{id}/floors", handlers.ListFloors)
			r.Post("/markup", handlers.SubmitMarkup)
			r.Get("/logs/{building_id}", handlers.GetLogs)
			r.Get("/me", handlers.Me)
		})
	})

	// Graceful shutdown
	go func() {
		log.Println("🚀 Server running on :8080")
		if err := http.ListenAndServe(":8080", r); err != nil {
			log.Fatalf("Server failed: %v", err)
		}
	}()

	// Wait for termination signal
	sig := make(chan os.Signal, 1)
	signal.Notify(sig, os.Interrupt, syscall.SIGTERM)
	<-sig

	log.Println("Shutting down server...")
	db.Close()
	log.Println("Server stopped")
}
