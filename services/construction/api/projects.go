package api

import (
	"net/http"

	"github.com/go-chi/chi/v5"
)

// ProjectsHandler handles project-related API endpoints
func ProjectsHandler(r chi.Router) {
	r.Get("/", listProjects)
	r.Post("/", createProject)
	r.Get("/{id}", getProject)
	r.Put("/{id}", updateProject)
	r.Delete("/{id}", deleteProject)
}

func listProjects(w http.ResponseWriter, r *http.Request) {
	// TODO: Implement project listing
	w.WriteHeader(http.StatusOK)
	w.Write([]byte(`{"projects": []}`))
}

func createProject(w http.ResponseWriter, r *http.Request) {
	// TODO: Implement project creation
	w.WriteHeader(http.StatusCreated)
	w.Write([]byte(`{"id": "new-project-id"}`))
}

func getProject(w http.ResponseWriter, r *http.Request) {
	// TODO: Implement project retrieval
	projectID := chi.URLParam(r, "id")
	w.WriteHeader(http.StatusOK)
	w.Write([]byte(`{"id": "` + projectID + `", "name": "Sample Project"}`))
}

func updateProject(w http.ResponseWriter, r *http.Request) {
	// TODO: Implement project update
	projectID := chi.URLParam(r, "id")
	w.WriteHeader(http.StatusOK)
	w.Write([]byte(`{"id": "` + projectID + `", "updated": true}`))
}

func deleteProject(w http.ResponseWriter, r *http.Request) {
	// TODO: Implement project deletion
	projectID := chi.URLParam(r, "id")
	w.WriteHeader(http.StatusOK)
	w.Write([]byte(`{"id": "` + projectID + `", "deleted": true}`))
} 