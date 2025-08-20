package handlers

import (
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"strings"
	"time"

	"arxos/db"

	"github.com/go-chi/chi/v5"
)

// Symbol represents a symbol from the symbol library
type Symbol struct {
	SymbolID    string                 `json:"symbol_id"`
	Name        string                 `json:"name"`
	Category    string                 `json:"category"`
	Subcategory string                 `json:"subcategory,omitempty"`
	Description string                 `json:"description,omitempty"`
	SVG         string                 `json:"svg,omitempty"`
	Metadata    map[string]interface{} `json:"metadata,omitempty"`
	Tags        []string               `json:"tags,omitempty"`
	CreatedAt   time.Time              `json:"created_at,omitempty"`
	UpdatedAt   time.Time              `json:"updated_at,omitempty"`
}

// SymbolLibraryResponse represents the response from the symbol library API
type SymbolLibraryResponse struct {
	Results []Symbol `json:"results"`
	Count   int      `json:"count"`
}

// SymbolLibrarySearchRequest represents a search request for symbols
type SymbolLibrarySearchRequest struct {
	Query    string `json:"query,omitempty"`
	Category string `json:"category,omitempty"`
	Limit    int    `json:"limit,omitempty"`
	Offset   int    `json:"offset,omitempty"`
}

// SymbolLibraryCache represents a cached symbol library response
type SymbolLibraryCache struct {
	ID        uint      `json:"id" gorm:"primaryKey"`
	Query     string    `json:"query"`
	Category  string    `json:"category"`
	Response  string    `json:"response" gorm:"type:text"`
	CreatedAt time.Time `json:"created_at"`
	ExpiresAt time.Time `json:"expires_at"`
}

// SVGParserConfig holds configuration for the SVG parser microservice
type SVGParserConfig struct {
	BaseURL string
	Timeout time.Duration
}

var svgParserConfig = SVGParserConfig{
	BaseURL: "http://localhost:8000/v1",
	Timeout: 30 * time.Second,
}

// ListSymbols handles GET /api/symbols - lists all symbols with optional search and filtering
func ListSymbols(w http.ResponseWriter, r *http.Request) {
	// Get query parameters
	query := r.URL.Query().Get("q")
	category := r.URL.Query().Get("category")
	limit := r.URL.Query().Get("limit")
	offset := r.URL.Query().Get("offset")

	// Check cache first
	cacheKey := fmt.Sprintf("%s:%s:%s:%s", query, category, limit, offset)
	cachedResponse, err := getCachedSymbolResponse(cacheKey)
	if err == nil && cachedResponse != nil {
		w.Header().Set("Content-Type", "application/json")
		w.Header().Set("X-Cache", "HIT")
		json.NewEncoder(w).Encode(cachedResponse)
		return
	}

	// Build URL for SVG parser microservice
	url := fmt.Sprintf("%s/symbols", svgParserConfig.BaseURL)
	params := []string{}
	if query != "" {
		params = append(params, fmt.Sprintf("q=%s", query))
	}
	if category != "" {
		params = append(params, fmt.Sprintf("category=%s", category))
	}
	if len(params) > 0 {
		url += "?" + strings.Join(params, "&")
	}

	// Make request to SVG parser microservice
	resp, err := http.Get(url)
	if err != nil {
		http.Error(w, fmt.Sprintf("Error connecting to SVG parser: %v", err), http.StatusInternalServerError)
		return
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(resp.Body)
		http.Error(w, fmt.Sprintf("SVG parser error: %s - %s", resp.Status, string(body)), resp.StatusCode)
		return
	}

	// Parse response
	var symbolResponse SymbolLibraryResponse
	if err := json.NewDecoder(resp.Body).Decode(&symbolResponse); err != nil {
		http.Error(w, fmt.Sprintf("Error parsing response: %v", err), http.StatusInternalServerError)
		return
	}

	// Cache the response
	cacheSymbolResponse(cacheKey, &symbolResponse)

	// Return response
	w.Header().Set("Content-Type", "application/json")
	w.Header().Set("X-Cache", "MISS")
	json.NewEncoder(w).Encode(symbolResponse)
}

// GetSymbol handles GET /api/symbols/{symbol_id} - gets a specific symbol by ID
func GetSymbol(w http.ResponseWriter, r *http.Request) {
	symbolID := chi.URLParam(r, "symbol_id")
	if symbolID == "" {
		http.Error(w, "Symbol ID is required", http.StatusBadRequest)
		return
	}

	// Check cache first
	cacheKey := fmt.Sprintf("symbol:%s", symbolID)
	cachedSymbol, err := getCachedSymbol(cacheKey)
	if err == nil && cachedSymbol != nil {
		w.Header().Set("Content-Type", "application/json")
		w.Header().Set("X-Cache", "HIT")
		json.NewEncoder(w).Encode(cachedSymbol)
		return
	}

	// Build URL for SVG parser microservice
	url := fmt.Sprintf("%s/symbols/%s", svgParserConfig.BaseURL, symbolID)

	// Make request to SVG parser microservice
	resp, err := http.Get(url)
	if err != nil {
		http.Error(w, fmt.Sprintf("Error connecting to SVG parser: %v", err), http.StatusInternalServerError)
		return
	}
	defer resp.Body.Close()

	if resp.StatusCode == http.StatusNotFound {
		http.Error(w, "Symbol not found", http.StatusNotFound)
		return
	}

	if resp.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(resp.Body)
		http.Error(w, fmt.Sprintf("SVG parser error: %s - %s", resp.Status, string(body)), resp.StatusCode)
		return
	}

	// Parse response
	var symbol Symbol
	if err := json.NewDecoder(resp.Body).Decode(&symbol); err != nil {
		http.Error(w, fmt.Sprintf("Error parsing response: %v", err), http.StatusInternalServerError)
		return
	}

	// Cache the symbol
	cacheSymbol(cacheKey, &symbol)

	// Return response
	w.Header().Set("Content-Type", "application/json")
	w.Header().Set("X-Cache", "MISS")
	json.NewEncoder(w).Encode(symbol)
}

// SearchSymbols handles POST /api/symbols/search - advanced symbol search
func SearchSymbols(w http.ResponseWriter, r *http.Request) {
	var searchReq SymbolLibrarySearchRequest
	if err := json.NewDecoder(r.Body).Decode(&searchReq); err != nil {
		http.Error(w, "Invalid request body", http.StatusBadRequest)
		return
	}

	// Build query parameters
	params := []string{}
	if searchReq.Query != "" {
		params = append(params, fmt.Sprintf("q=%s", searchReq.Query))
	}
	if searchReq.Category != "" {
		params = append(params, fmt.Sprintf("category=%s", searchReq.Category))
	}

	// Build URL for SVG parser microservice
	url := fmt.Sprintf("%s/symbols", svgParserConfig.BaseURL)
	if len(params) > 0 {
		url += "?" + strings.Join(params, "&")
	}

	// Make request to SVG parser microservice
	resp, err := http.Get(url)
	if err != nil {
		http.Error(w, fmt.Sprintf("Error connecting to SVG parser: %v", err), http.StatusInternalServerError)
		return
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(resp.Body)
		http.Error(w, fmt.Sprintf("SVG parser error: %s - %s", resp.Status, string(body)), resp.StatusCode)
		return
	}

	// Parse response
	var symbolResponse SymbolLibraryResponse
	if err := json.NewDecoder(resp.Body).Decode(&symbolResponse); err != nil {
		http.Error(w, fmt.Sprintf("Error parsing response: %v", err), http.StatusInternalServerError)
		return
	}

	// Apply pagination if specified
	if searchReq.Limit > 0 || searchReq.Offset > 0 {
		start := searchReq.Offset
		end := start + searchReq.Limit
		if end > len(symbolResponse.Results) {
			end = len(symbolResponse.Results)
		}
		if start < len(symbolResponse.Results) {
			symbolResponse.Results = symbolResponse.Results[start:end]
		} else {
			symbolResponse.Results = []Symbol{}
		}
		symbolResponse.Count = len(symbolResponse.Results)
	}

	// Return response
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(symbolResponse)
}

// GetSymbolCategories handles GET /api/symbols/categories - gets available symbol categories
func GetSymbolCategories(w http.ResponseWriter, r *http.Request) {
	// Get all symbols to extract categories
	url := fmt.Sprintf("%s/symbols", svgParserConfig.BaseURL)
	resp, err := http.Get(url)
	if err != nil {
		http.Error(w, fmt.Sprintf("Error connecting to SVG parser: %v", err), http.StatusInternalServerError)
		return
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(resp.Body)
		http.Error(w, fmt.Sprintf("SVG parser error: %s - %s", resp.Status, string(body)), resp.StatusCode)
		return
	}

	var symbolResponse SymbolLibraryResponse
	if err := json.NewDecoder(resp.Body).Decode(&symbolResponse); err != nil {
		http.Error(w, fmt.Sprintf("Error parsing response: %v", err), http.StatusInternalServerError)
		return
	}

	// Extract unique categories
	categories := make(map[string]int)
	for _, symbol := range symbolResponse.Results {
		if symbol.Category != "" {
			categories[symbol.Category]++
		}
	}

	// Convert to slice
	var categoryList []map[string]interface{}
	for category, count := range categories {
		categoryList = append(categoryList, map[string]interface{}{
			"name":  category,
			"count": count,
		})
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{
		"categories": categoryList,
		"count":      len(categoryList),
	})
}

// Cache functions
func getCachedSymbolResponse(cacheKey string) (*SymbolLibraryResponse, error) {
	var cache SymbolLibraryCache
	result := db.DB.Where("query = ? AND expires_at > ?", cacheKey, time.Now()).First(&cache)
	if result.Error != nil {
		return nil, result.Error
	}

	var response SymbolLibraryResponse
	if err := json.Unmarshal([]byte(cache.Response), &response); err != nil {
		return nil, err
	}

	return &response, nil
}

func cacheSymbolResponse(cacheKey string, response *SymbolLibraryResponse) {
	responseJSON, err := json.Marshal(response)
	if err != nil {
		return
	}

	cache := SymbolLibraryCache{
		Query:     cacheKey,
		Response:  string(responseJSON),
		CreatedAt: time.Now(),
		ExpiresAt: time.Now().Add(1 * time.Hour), // Cache for 1 hour
	}

	db.DB.Save(&cache)
}

func getCachedSymbol(cacheKey string) (*Symbol, error) {
	var cache SymbolLibraryCache
	result := db.DB.Where("query = ? AND expires_at > ?", cacheKey, time.Now()).First(&cache)
	if result.Error != nil {
		return nil, result.Error
	}

	var symbol Symbol
	if err := json.Unmarshal([]byte(cache.Response), &symbol); err != nil {
		return nil, err
	}

	return &symbol, nil
}

func cacheSymbol(cacheKey string, symbol *Symbol) {
	symbolJSON, err := json.Marshal(symbol)
	if err != nil {
		return
	}

	cache := SymbolLibraryCache{
		Query:     cacheKey,
		Response:  string(symbolJSON),
		CreatedAt: time.Now(),
		ExpiresAt: time.Now().Add(1 * time.Hour), // Cache for 1 hour
	}

	db.DB.Save(&cache)
}

// ClearSymbolCache handles DELETE /api/symbols/cache - clears the symbol cache
func ClearSymbolCache(w http.ResponseWriter, r *http.Request) {
	if err := db.DB.Where("1 = 1").Delete(&SymbolLibraryCache{}).Error; err != nil {
		http.Error(w, fmt.Sprintf("Error clearing cache: %v", err), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]string{
		"message": "Symbol cache cleared successfully",
	})
}
