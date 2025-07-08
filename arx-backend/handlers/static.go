package handlers

import (
	"net/http"
	"os"
	"path/filepath"
	"strings"
)

// Asset version string (could be set at build time or from env)
var assetVersion = "v1.0.0" // TODO: automate this with build hash or env

// ServeStaticAssets serves static files with versioning and cache headers
func ServeStaticAssets(w http.ResponseWriter, r *http.Request) {
	// Example: /static/v1.0.0/app.js
	path := r.URL.Path
	if !strings.HasPrefix(path, "/static/") {
		http.NotFound(w, r)
		return
	}

	// Extract version and file path
	parts := strings.SplitN(strings.TrimPrefix(path, "/static/"), "/", 2)
	if len(parts) != 2 {
		http.NotFound(w, r)
		return
	}
	version, filePath := parts[0], parts[1]

	// Set cache headers
	w.Header().Set("Cache-Control", "public, max-age=31536000")
	w.Header().Set("ETag", version)

	// Optionally: check version matches current assetVersion
	// if version != assetVersion { ... }

	// Serve from CDN or local fallback
	// For now, serve from local ./static directory
	localPath := filepath.Join("static", filePath)
	if _, err := os.Stat(localPath); os.IsNotExist(err) {
		http.NotFound(w, r)
		return
	}
	http.ServeFile(w, r, localPath)
}
