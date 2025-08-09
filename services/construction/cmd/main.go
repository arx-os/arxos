package main

import (
	"log"
	"net/http"

	"github.com/go-chi/chi/v5"
	"github.com/go-chi/chi/v5/middleware"
	"github.com/go-chi/cors"

	"arxos/construction/api"
)

func main() {
	r := chi.NewRouter()

	// Middleware
	r.Use(middleware.Logger)
	r.Use(middleware.Recoverer)
	r.Use(cors.Handler(cors.Options{
		AllowedOrigins:   []string{"*"},
		AllowedMethods:   []string{"GET", "POST", "PUT", "DELETE", "OPTIONS"},
		AllowedHeaders:   []string{"Accept", "Authorization", "Content-Type"},
		ExposedHeaders:   []string{"Link"},
		AllowCredentials: true,
		MaxAge:           300,
	}))

	// Routes
	r.Route("/api/v1", func(r chi.Router) {
		r.Route("/projects", api.ProjectsHandler)
		r.Route("/schedules", api.SchedulesHandler)
		r.Route("/documents", api.DocumentsHandler)
		r.Route("/inspections", api.InspectionsHandler)
		r.Route("/safety", api.SafetyHandler)
		r.Route("/reporting", api.ReportingHandler)
	})

	log.Fatal(http.ListenAndServe(":8080", r))
}
