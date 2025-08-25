package main

import (
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/arxos/arxos/core/internal/db"
	"github.com/arxos/arxos/core/internal/services"
)

// setupGracefulShutdown sets up signal handling for graceful shutdown
func setupGracefulShutdown() {
	sigChan := make(chan os.Signal, 1)
	signal.Notify(sigChan, os.Interrupt, syscall.SIGTERM)
	
	go func() {
		<-sigChan
		log.Println("Shutting down gracefully...")
		
		// Give ongoing requests 10 seconds to complete
		time.Sleep(10 * time.Second)
		
		// Shutdown services
		if err := services.ShutdownServices(); err != nil {
			log.Printf("Error during shutdown: %v", err)
		}
		
		log.Println("Shutdown complete")
		os.Exit(0)
	}()
}

// handleCacheStats returns cache statistics
func handleCacheStats(w http.ResponseWriter, r *http.Request) {
	cacheService := services.GetCacheService()
	if cacheService == nil {
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusServiceUnavailable)
		json.NewEncoder(w).Encode(map[string]string{
			"error": "Cache service not available",
		})
		return
	}

	stats, err := cacheService.GetStats()
	if err != nil {
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusInternalServerError)
		json.NewEncoder(w).Encode(map[string]string{
			"error": fmt.Sprintf("Failed to get cache stats: %v", err),
		})
		return
	}

	// Get additional database stats
	var dbStats struct {
		TotalEntries   int64
		ExpiredEntries int64
		AvgAccessCount float64
		TopKeys        []struct {
			Key         string `json:"key"`
			AccessCount int64  `json:"access_count"`
		} `json:"top_keys"`
	}

	// Count total and expired entries
	db.GormDB.Raw(`
		SELECT 
			COUNT(*) as total_entries,
			COUNT(CASE WHEN expires_at < CURRENT_TIMESTAMP THEN 1 END) as expired_entries,
			AVG(access_count) as avg_access_count
		FROM cache_entries
	`).Scan(&dbStats)

	// Get top accessed keys
	db.GormDB.Raw(`
		SELECT cache_key as key, access_count 
		FROM cache_entries 
		ORDER BY access_count DESC 
		LIMIT 10
	`).Scan(&dbStats.TopKeys)

	response := map[string]interface{}{
		"cache_stats": map[string]interface{}{
			"hits":       stats.Hits,
			"misses":     stats.Misses,
			"hit_rate":   stats.HitRate,
			"total_keys": stats.TotalKeys,
		},
		"database_stats": map[string]interface{}{
			"total_entries":    dbStats.TotalEntries,
			"expired_entries":  dbStats.ExpiredEntries,
			"avg_access_count": dbStats.AvgAccessCount,
			"top_accessed":     dbStats.TopKeys,
		},
		"timestamp": time.Now().Unix(),
	}

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(response)
}

// handleCacheClear clears all or specific cache entries
func handleCacheClear(w http.ResponseWriter, r *http.Request) {
	// Only allow POST method
	if r.Method != http.MethodPost {
		w.WriteHeader(http.StatusMethodNotAllowed)
		return
	}

	cacheService := services.GetCacheService()
	if cacheService == nil {
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusServiceUnavailable)
		json.NewEncoder(w).Encode(map[string]string{
			"error": "Cache service not available",
		})
		return
	}

	// Parse request body
	var req struct {
		Pattern string `json:"pattern"`
		Type    string `json:"type"` // "all", "expired", or "pattern"
	}
	
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		req.Type = "expired" // Default to clearing expired entries
	}

	var message string
	var cleared int64

	switch req.Type {
	case "all":
		// Clear all cache entries (requires admin permission in production)
		result := db.GormDB.Exec("TRUNCATE TABLE cache_entries, http_cache, confidence_cache")
		if result.Error != nil {
			w.Header().Set("Content-Type", "application/json")
			w.WriteHeader(http.StatusInternalServerError)
			json.NewEncoder(w).Encode(map[string]string{
				"error": fmt.Sprintf("Failed to clear cache: %v", result.Error),
			})
			return
		}
		message = "All cache entries cleared"
		
	case "pattern":
		// Clear by pattern
		if req.Pattern == "" {
			w.Header().Set("Content-Type", "application/json")
			w.WriteHeader(http.StatusBadRequest)
			json.NewEncoder(w).Encode(map[string]string{
				"error": "Pattern is required for pattern-based clearing",
			})
			return
		}
		
		if err := cacheService.InvalidatePattern(req.Pattern); err != nil {
			w.Header().Set("Content-Type", "application/json")
			w.WriteHeader(http.StatusInternalServerError)
			json.NewEncoder(w).Encode(map[string]string{
				"error": fmt.Sprintf("Failed to clear pattern: %v", err),
			})
			return
		}
		message = fmt.Sprintf("Cache entries matching pattern '%s' cleared", req.Pattern)
		
	default:
		// Clear expired entries (default)
		if err := services.CleanupExpiredCache(); err != nil {
			w.Header().Set("Content-Type", "application/json")
			w.WriteHeader(http.StatusInternalServerError)
			json.NewEncoder(w).Encode(map[string]string{
				"error": fmt.Sprintf("Failed to cleanup cache: %v", err),
			})
			return
		}
		message = "Expired cache entries cleared"
	}

	// Log the operation
	log.Printf("Cache clear operation: type=%s, pattern=%s, cleared=%d", req.Type, req.Pattern, cleared)

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(map[string]interface{}{
		"success": true,
		"message": message,
		"cleared": cleared,
	})
}

// handleServicesHealth returns health status of all services
func handleServicesHealth(w http.ResponseWriter, r *http.Request) {
	health := services.GetServicesHealth()
	
	// Determine overall status
	overallStatus := "healthy"
	for _, service := range health {
		if service.Status == "unhealthy" {
			overallStatus = "unhealthy"
			break
		} else if service.Status == "degraded" && overallStatus == "healthy" {
			overallStatus = "degraded"
		}
	}

	response := map[string]interface{}{
		"status":    overallStatus,
		"services":  health,
		"timestamp": time.Now().Unix(),
		"uptime":    time.Since(startTime).Seconds(),
	}

	w.Header().Set("Content-Type", "application/json")
	
	// Set appropriate status code
	statusCode := http.StatusOK
	if overallStatus == "unhealthy" {
		statusCode = http.StatusServiceUnavailable
	}
	
	w.WriteHeader(statusCode)
	json.NewEncoder(w).Encode(response)
}

// handleCacheGet retrieves a specific cache entry (for debugging)
func handleCacheGet(w http.ResponseWriter, r *http.Request) {
	key := r.URL.Query().Get("key")
	if key == "" {
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusBadRequest)
		json.NewEncoder(w).Encode(map[string]string{
			"error": "Key parameter is required",
		})
		return
	}

	cacheService := services.GetCacheService()
	if cacheService == nil {
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusServiceUnavailable)
		json.NewEncoder(w).Encode(map[string]string{
			"error": "Cache service not available",
		})
		return
	}

	value, err := cacheService.Get(key)
	if err != nil {
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusInternalServerError)
		json.NewEncoder(w).Encode(map[string]string{
			"error": fmt.Sprintf("Failed to get cache entry: %v", err),
		})
		return
	}

	if value == nil {
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusNotFound)
		json.NewEncoder(w).Encode(map[string]string{
			"error": "Key not found in cache",
		})
		return
	}

	ttl, _ := cacheService.TTL(key)
	exists, _ := cacheService.Exists(key)

	response := map[string]interface{}{
		"key":    key,
		"value":  value,
		"exists": exists,
		"ttl":    ttl.Seconds(),
	}

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(response)
}

// startTime tracks when the server started
var startTime = time.Now()