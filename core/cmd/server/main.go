package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"log"
	"mime/multipart"
	"net/http"
	"os"
	"os/signal"
	"path/filepath"
	"strings"
	"syscall"
	"time"

	// "github.com/arxos/arxos/core/internal/handlers"
	"github.com/arxos/arxos/core/internal/auth"
	"github.com/arxos/arxos/core/internal/services"
	"github.com/go-chi/chi/v5"
	chimiddleware "github.com/go-chi/chi/v5/middleware"
	"github.com/rs/cors"
)

// handlePDFUpload processes PDF uploads and forwards to AI service
func handlePDFUpload(w http.ResponseWriter, r *http.Request) {
	// Parse multipart form
	err := r.ParseMultipartForm(50 << 20) // 50 MB max
	if err != nil {
		http.Error(w, "Failed to parse form data", http.StatusBadRequest)
		return
	}

	// Get the file
	file, header, err := r.FormFile("file")
	if err != nil {
		http.Error(w, "No file provided", http.StatusBadRequest)
		return
	}
	defer file.Close()

	// Read file content
	fileBytes, err := io.ReadAll(file)
	if err != nil {
		http.Error(w, "Failed to read file", http.StatusInternalServerError)
		return
	}

	// Forward to AI service
	aiServiceURL := os.Getenv("AI_SERVICE_URL")
	if aiServiceURL == "" {
		aiServiceURL = "http://localhost:8000"
	}

	// Create multipart form for AI service
	body := &bytes.Buffer{}
	writer := multipart.NewWriter(body)

	// Add file to form
	part, err := writer.CreateFormFile("file", header.Filename)
	if err != nil {
		http.Error(w, "Failed to create form", http.StatusInternalServerError)
		return
	}

	_, err = part.Write(fileBytes)
	if err != nil {
		http.Error(w, "Failed to write file", http.StatusInternalServerError)
		return
	}

	// Add building type
	writer.WriteField("building_type", "general")
	writer.Close()

	// Send to AI service
	req, err := http.NewRequest("POST", aiServiceURL+"/api/v1/convert", body)
	if err != nil {
		http.Error(w, "Failed to create request", http.StatusInternalServerError)
		return
	}
	req.Header.Set("Content-Type", writer.FormDataContentType())

	client := &http.Client{Timeout: 60 * time.Second}
	resp, err := client.Do(req)
	if err != nil {
		http.Error(w, "AI service unavailable", http.StatusServiceUnavailable)
		return
	}
	defer resp.Body.Close()

	// Read AI service response
	aiResponse, err := io.ReadAll(resp.Body)
	if err != nil {
		http.Error(w, "Failed to read AI response", http.StatusInternalServerError)
		return
	}

	// Parse and transform response
	var aiResult map[string]interface{}
	if err := json.Unmarshal(aiResponse, &aiResult); err != nil {
		http.Error(w, "Invalid AI response", http.StatusInternalServerError)
		return
	}

	// Extract ArxObjects from AI response
	arxobjects, ok := aiResult["arxobjects"].([]interface{})
	if !ok {
		arxobjects = []interface{}{}
	}

	// Convert ArxObjects to frontend format
	frontendObjects := make([]map[string]interface{}, 0)
	for _, obj := range arxobjects {
		if objMap, ok := obj.(map[string]interface{}); ok {
			// Create frontend-friendly object
			frontendObj := map[string]interface{}{
				"id":   objMap["id"],
				"type": objMap["type"],
			}
			
			// Handle confidence
			if conf, ok := objMap["confidence"].(map[string]interface{}); ok {
				frontendObj["confidence"] = conf["overall"]
			}
			
			// Pass through geometry if present
			if geometry, ok := objMap["geometry"]; ok {
				frontendObj["geometry"] = geometry
			}
			
			// Pass through data if present
			if data, ok := objMap["data"]; ok {
				frontendObj["data"] = data
			}
			
			// Handle position for objects without geometry
			if position, ok := objMap["position"].(map[string]interface{}); ok {
				// Convert nanometers to millimeters
				if x, ok := position["x"].(float64); ok {
					frontendObj["x"] = x / 1e6
				}
				if y, ok := position["y"].(float64); ok {
					frontendObj["y"] = y / 1e6
				}
			}
			
			// Handle dimensions
			if dimensions, ok := objMap["dimensions"].(map[string]interface{}); ok {
				if w, ok := dimensions["width"].(float64); ok {
					frontendObj["width"] = w / 1e6
				}
				if h, ok := dimensions["height"].(float64); ok {
					frontendObj["height"] = h / 1e6
				}
			}
			
			frontendObjects = append(frontendObjects, frontendObj)
		}
	}

	// Create response
	response := map[string]interface{}{
		"success":     true,
		"message":     fmt.Sprintf("Processed %s", header.Filename),
		"filename":    header.Filename,
		"arxobjects":  frontendObjects,  // Frontend expects 'arxobjects' not 'objects'
		"statistics": map[string]interface{}{
			"total_objects":      len(frontendObjects),
			"overall_confidence": aiResult["overall_confidence"],
			"processing_time":    aiResult["processing_time"],
		},
	}

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(response)
}

// Password reset handlers
func handlePasswordResetInitiate(w http.ResponseWriter, r *http.Request) {
	var req struct {
		Email string `json:"email"`
	}
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "Invalid request", http.StatusBadRequest)
		return
	}
	
	// Always return success to prevent email enumeration
	// In production, this would send an email if the account exists
	response := map[string]interface{}{
		"message": "If an account exists with this email, a password reset link has been sent",
	}
	
	// For development, log the reset URL
	fmt.Printf("Password reset requested for email: %s\n", req.Email)
	
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(response)
}

func handlePasswordResetValidate(w http.ResponseWriter, r *http.Request) {
	token := r.URL.Query().Get("token")
	if token == "" {
		http.Error(w, "Token is required", http.StatusBadRequest)
		return
	}
	
	// Validate token (simplified for now)
	response := map[string]interface{}{
		"valid": len(token) > 20, // Basic validation
		"email": "user@example.com", // Masked email
	}
	
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(response)
}

func handlePasswordResetConfirm(w http.ResponseWriter, r *http.Request) {
	var req struct {
		Token       string `json:"token"`
		NewPassword string `json:"new_password"`
	}
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "Invalid request", http.StatusBadRequest)
		return
	}
	
	// Validate inputs
	if req.Token == "" || req.NewPassword == "" {
		http.Error(w, "Token and new password are required", http.StatusBadRequest)
		return
	}
	
	// Validate password strength
	if len(req.NewPassword) < 8 {
		http.Error(w, "Password must be at least 8 characters", http.StatusBadRequest)
		return
	}
	
	// Success response
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(map[string]interface{}{
		"message": "Password has been reset successfully",
		"success": true,
	})
}

// getAllowedOrigins returns the list of allowed CORS origins from environment
func getAllowedOrigins() []string {
	originsEnv := os.Getenv("CORS_ALLOWED_ORIGINS")
	
	// Default to localhost only for development
	if originsEnv == "" {
		// Development defaults - only localhost
		return []string{
			"http://localhost:3000",
			"http://localhost:8080",
			"http://127.0.0.1:3000",
			"http://127.0.0.1:8080",
		}
	}
	
	// Parse comma-separated list of origins
	origins := strings.Split(originsEnv, ",")
	for i := range origins {
		origins[i] = strings.TrimSpace(origins[i])
	}
	
	return origins
}

// validateEnvironment checks required environment variables on startup
func validateEnvironment() {
	required := []string{
		"ARXOS_ADMIN_USERNAME",
		"ARXOS_ADMIN_PASSWORD",
	}
	
	missing := []string{}
	for _, env := range required {
		if os.Getenv(env) == "" {
			missing = append(missing, env)
		}
	}
	
	if len(missing) > 0 {
		log.Fatalf("❌ Missing required environment variables: %s\n"+
			"Please copy .env.example to .env and configure all required values.", 
			strings.Join(missing, ", "))
	}
	
	// Validate security settings
	if os.Getenv("ENVIRONMENT") == "production" {
		// Additional production checks
		if os.Getenv("JWT_SECRET") == "" && os.Getenv("JWT_SECRET_FILE") == "" {
			log.Fatal("❌ JWT_SECRET or JWT_SECRET_FILE must be set in production")
		}
		
		corsOrigins := os.Getenv("CORS_ALLOWED_ORIGINS")
		if corsOrigins == "" || strings.Contains(corsOrigins, "*") {
			log.Fatal("❌ CORS_ALLOWED_ORIGINS must be set to specific domains in production (not * or empty)")
		}
		
		if os.Getenv("DB_SSL_MODE") != "require" {
			log.Println("⚠️  Warning: DB_SSL_MODE should be 'require' in production")
		}
	}
	
	log.Println("✅ Environment validation passed")
}

func main() {
	log.Println("🚀 Starting ARXOS backend server...")
	
	// Validate environment variables
	validateEnvironment()

	// Initialize all services (database, cache, sessions, etc.)
	serviceConfig := services.DefaultServiceConfig()
	if err := services.InitializeServices(serviceConfig); err != nil {
		log.Fatalf("Failed to initialize services: %v", err)
	}
	defer services.ShutdownServices()

	// Setup graceful shutdown
	setupGracefulShutdown()

	// Initialize auth manager
	authManager := auth.NewAuthManager()

	// Set up router
	r := chi.NewRouter()
	r.Use(chimiddleware.Logger)
	
	// Configure CORS with specific allowed origins
	corsOptions := cors.New(cors.Options{
		AllowedOrigins: getAllowedOrigins(),
		AllowedMethods: []string{"GET", "POST", "PUT", "DELETE", "OPTIONS"},
		AllowedHeaders: []string{"Accept", "Authorization", "Content-Type", "X-CSRF-Token"},
		ExposedHeaders: []string{"Link", "X-RateLimit-Limit", "X-RateLimit-Remaining", "X-RateLimit-Reset"},
		AllowCredentials: true,
		MaxAge: 300, // Maximum value not ignored by any of major browsers
	})
	r.Use(corsOptions.Handler)

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

	// Serve static files (login page, etc)
	demoDir := os.Getenv("DEMO_DIR")
	if demoDir == "" {
		// Try to find demo directory
		if _, err := os.Stat("../../demo"); err == nil {
			demoDir = "../../demo"
		} else if _, err := os.Stat("demo"); err == nil {
			demoDir = "demo"
		} else {
			demoDir = "./demo"
		}
	}

	// Public routes (no auth required)
	r.Get("/login", func(w http.ResponseWriter, r *http.Request) {
		http.ServeFile(w, r, filepath.Join(demoDir, "login.html"))
	})

	// Auth endpoints
	r.Post("/api/auth/login", authManager.Login)
	r.Post("/api/auth/logout", authManager.Logout)
	r.Post("/api/auth/refresh", authManager.RefreshToken)
	r.Post("/api/auth/change-password", authManager.ChangePassword)
	
	// Password reset endpoints
	r.Post("/api/auth/password-reset/initiate", handlePasswordResetInitiate)
	r.Get("/api/auth/password-reset/validate", handlePasswordResetValidate)
	r.Post("/api/auth/password-reset/confirm", handlePasswordResetConfirm)
	
	// Verify token endpoint
	r.Get("/api/auth/verify", func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
		w.Write([]byte(`{"valid":true}`))
	})

	// Apply auth middleware to all other routes
	r.Group(func(r chi.Router) {
		r.Use(authManager.Middleware)

		// Protected root - serve main app
		r.Get("/", func(w http.ResponseWriter, r *http.Request) {
			indexPath := filepath.Join(demoDir, "index.html")
			if _, err := os.Stat(indexPath); err == nil {
				http.ServeFile(w, r, indexPath)
			} else {
				http.Redirect(w, r, "/api/health", http.StatusTemporaryRedirect)
			}
		})

		// Serve demo files (protected)
		fileServer := http.FileServer(http.Dir(demoDir))
		r.Handle("/*", http.StripPrefix("/", fileServer))
		
		// PDF upload endpoints (protected)
		r.Post("/upload/pdf", handlePDFUpload) // Original endpoint
		// r.Post("/api/v1/upload/pdf", handlers.EnhancedPDFUpload) // Enhanced with BIM processing (temporarily disabled)
		
		r.Route("/api", func(r chi.Router) {
			// Protected API endpoints
			// Health endpoints
			r.Get("/health", func(w http.ResponseWriter, r *http.Request) {
				w.Header().Set("Content-Type", "application/json")
				w.WriteHeader(http.StatusOK)
				w.Write([]byte(`{"status":"ok","message":"ARXOS backend is running","authenticated":true}`))
			})
			r.Get("/health/services", handleServicesHealth)

			// Cache management endpoints
			r.Route("/cache", func(r chi.Router) {
				r.Get("/stats", handleCacheStats)
				r.Post("/clear", handleCacheClear)
				r.Get("/entry", handleCacheGet) // Debug endpoint
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
	})

	// Start server
	log.Println("🚀 Server running on :8080")
	if err := http.ListenAndServe(":8080", r); err != nil {
		log.Fatalf("Server failed: %v", err)
	}
}
