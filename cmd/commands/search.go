package commands

import (
	"fmt"
	"regexp"
	"strings"
	"time"
)

// ============================================================================
// SEARCH ENGINE CORE
// ============================================================================

// SearchEngine provides advanced search capabilities for building data
type SearchEngine struct {
	indexer *ArxObjectIndexer
	cache   map[string]*SearchResult
}

// NewSearchEngine creates a new search engine instance
func NewSearchEngine(indexer *ArxObjectIndexer) *SearchEngine {
	return &SearchEngine{
		indexer: indexer,
		cache:   make(map[string]*SearchResult),
	}
}

// SearchResult represents the result of a search operation
type SearchResult struct {
	Query       string                 `json:"query"`
	TotalHits   int                    `json:"total_hits"`
	Results     []SearchHit            `json:"results"`
	ExecutionTime time.Duration        `json:"execution_time"`
	Timestamp   time.Time              `json:"timestamp"`
	Metadata    map[string]interface{} `json:"metadata"`
}

// SearchHit represents a single search result
type SearchHit struct {
	ObjectID    string                 `json:"object_id"`
	Path        string                 `json:"path"`
	Type        string                 `json:"type"`
	Name        string                 `json:"name"`
	Description string                 `json:"description"`
	Score       float64                `json:"score"`
	Properties  map[string]interface{} `json:"properties"`
	Location    *Point3D               `json:"location,omitempty"`
	Metadata    map[string]interface{} `json:"metadata"`
}

// Query represents a search query with filters and options
type Query struct {
	Text        string                 `json:"text"`         // Free text search
	Type        string                 `json:"type"`         // Object type filter
	Status      string                 `json:"status"`       // Status filter
	Path        string                 `json:"path"`         // Path filter
	Properties  map[string]interface{} `json:"properties"`   // Property filters
	Spatial     *SpatialQuery          `json:"spatial"`      // Spatial constraints
	Logical     *LogicalQuery          `json:"logical"`      // Logical operators
	Limit       int                    `json:"limit"`        // Result limit
	Offset      int                    `json:"offset"`       // Result offset
	SortBy      string                 `json:"sort_by"`      // Sort field
	SortOrder   string                 `json:"sort_order"`   // asc/desc
}

// SpatialQuery represents spatial search constraints
type SpatialQuery struct {
	Type      string    `json:"type"`       // within, near, intersects
	Bounds    *BoundingBox `json:"bounds"`  // Bounding box for within/intersects
	Point     *Point3D  `json:"point"`      // Center point for near
	Distance  float64   `json:"distance"`   // Distance in millimeters
}

// LogicalQuery represents logical operations between filters
type LogicalQuery struct {
	Operator string   `json:"operator"` // AND, OR, NOT
	Queries  []*Query `json:"queries"`  // Sub-queries
}

// Point3D represents a 3D point in space
type Point3D struct {
	X float64 `json:"x"`
	Y float64 `json:"y"`
	Z float64 `json:"z"`
}

// BoundingBox represents a 3D bounding box
type BoundingBox struct {
	Min Point3D `json:"min"`
	Max Point3D `json:"max"`
}

// ============================================================================
// SEARCH EXECUTION
// ============================================================================

// Search executes a search query and returns results
func (se *SearchEngine) Search(query *Query) (*SearchResult, error) {
	startTime := time.Now()
	
	// Check cache first
	cacheKey := se.generateCacheKey(query)
	if cached, exists := se.cache[cacheKey]; exists && se.isCacheValid(cached) {
		return cached, nil
	}
	
	// Execute search
	results, err := se.executeSearch(query)
	if err != nil {
		return nil, fmt.Errorf("search execution failed: %w", err)
	}
	
	// Apply sorting and pagination
	se.sortResults(results, query.SortBy, query.SortOrder)
	paginatedResults := se.paginateResults(results, query.Limit, query.Offset)
	
	// Create search result
	searchResult := &SearchResult{
		Query:        se.queryToString(query),
		TotalHits:    len(results),
		Results:      paginatedResults,
		ExecutionTime: time.Since(startTime),
		Timestamp:    time.Now().UTC(),
		Metadata: map[string]interface{}{
			"cache_hit": false,
			"query_type": se.getQueryType(query),
		},
	}
	
	// Cache the result
	se.cache[cacheKey] = searchResult
	
	return searchResult, nil
}

// executeSearch performs the actual search operation
func (se *SearchEngine) executeSearch(query *Query) ([]SearchHit, error) {
	var results []SearchHit
	
	// Get all objects from indexer
	objects, err := se.indexer.GetAllObjects()
	if err != nil {
		return nil, fmt.Errorf("failed to get objects: %w", err)
	}
	
	// Apply filters
	for _, obj := range objects {
		hit := se.objectToSearchHit(obj)
		
		// Apply text filter
		if query.Text != "" && !se.matchesText(hit, query.Text) {
			continue
		}
		
		// Apply type filter
		if query.Type != "" && !se.matchesType(hit, query.Type) {
			continue
		}
		
		// Apply status filter
		if query.Status != "" && !se.matchesStatus(hit, query.Status) {
			continue
		}
		
		// Apply path filter
		if query.Path != "" && !se.matchesPath(hit, query.Path) {
			continue
		}
		
		// Apply property filters
		if query.Properties != nil && !se.matchesProperties(hit, query.Properties) {
			continue
		}
		
		// Apply spatial filters
		if query.Spatial != nil && !se.matchesSpatial(hit, query.Spatial) {
			continue
		}
		
		// Calculate relevance score
		hit.Score = se.calculateScore(hit, query)
		
		results = append(results, hit)
	}
	
	return results, nil
}

// ============================================================================
// FILTER MATCHING
// ============================================================================

// matchesText checks if a search hit matches text criteria
func (se *SearchEngine) matchesText(hit SearchHit, text string) bool {
	text = strings.ToLower(text)
	
	// Check name
	if strings.Contains(strings.ToLower(hit.Name), text) {
		return true
	}
	
	// Check description
	if strings.Contains(strings.ToLower(hit.Description), text) {
		return true
	}
	
	// Check properties
	for _, value := range hit.Properties {
		if str, ok := value.(string); ok {
			if strings.Contains(strings.ToLower(str), text) {
				return true
			}
		}
	}
	
	return false
}

// matchesType checks if a search hit matches type criteria
func (se *SearchEngine) matchesType(hit SearchHit, objectType string) bool {
	// Support wildcard matching
	if strings.Contains(objectType, "*") {
		pattern := strings.ReplaceAll(objectType, "*", ".*")
		matched, _ := regexp.MatchString(pattern, hit.Type)
		return matched
	}
	
	return strings.EqualFold(hit.Type, objectType)
}

// matchesStatus checks if a search hit matches status criteria
func (se *SearchEngine) matchesStatus(hit SearchHit, status string) bool {
	if statusValue, exists := hit.Properties["status"]; exists {
		return strings.EqualFold(fmt.Sprintf("%v", statusValue), status)
	}
	return false
}

// matchesPath checks if a search hit matches path criteria
func (se *SearchEngine) matchesPath(hit SearchHit, pathPattern string) bool {
	// Support wildcard matching
	if strings.Contains(pathPattern, "*") {
		pattern := strings.ReplaceAll(pathPattern, "*", ".*")
		matched, _ := regexp.MatchString(pattern, hit.Path)
		return matched
	}
	
	return strings.Contains(hit.Path, pathPattern)
}

// matchesProperties checks if a search hit matches property criteria
func (se *SearchEngine) matchesProperties(hit SearchHit, filters map[string]interface{}) bool {
	for key, expectedValue := range filters {
		if actualValue, exists := hit.Properties[key]; exists {
			if !se.propertyValuesMatch(actualValue, expectedValue) {
				return false
			}
		} else {
			return false
		}
	}
	return true
}

// propertyValuesMatch checks if two property values match
func (se *SearchEngine) propertyValuesMatch(actual, expected interface{}) bool {
	switch exp := expected.(type) {
	case string:
		if str, ok := actual.(string); ok {
			return strings.EqualFold(str, exp)
		}
	case int, int64:
		if num, ok := actual.(int); ok {
			return num == exp
		}
	case float64:
		if num, ok := actual.(float64); ok {
			return num == exp
		}
	case bool:
		if b, ok := actual.(bool); ok {
			return b == exp
		}
	}
	return false
}

// matchesSpatial checks if a search hit matches spatial criteria
func (se *SearchEngine) matchesSpatial(hit SearchHit, spatial *SpatialQuery) bool {
	if hit.Location == nil {
		return false
	}
	
	switch spatial.Type {
	case "within":
		return se.isPointWithinBounds(*hit.Location, *spatial.Bounds)
	case "near":
		return se.isPointNearPoint(*hit.Location, *spatial.Point, spatial.Distance)
	case "intersects":
		// For now, assume all objects intersect (simplified)
		return true
	default:
		return false
	}
	
	return false
}

// ============================================================================
// SPATIAL OPERATIONS
// ============================================================================

// isPointWithinBounds checks if a point is within a bounding box
func (se *SearchEngine) isPointWithinBounds(point Point3D, bounds BoundingBox) bool {
	return point.X >= bounds.Min.X && point.X <= bounds.Max.X &&
		   point.Y >= bounds.Min.Y && point.Y <= bounds.Max.Y &&
		   point.Z >= bounds.Min.Z && point.Z <= bounds.Max.Z
}

// isPointNearPoint checks if a point is within distance of another point
func (se *SearchEngine) isPointNearPoint(point1, point2 Point3D, distance float64) bool {
	dx := point1.X - point2.X
	dy := point1.Y - point2.Y
	dz := point1.Z - point2.Z
	
	actualDistance := dx*dx + dy*dy + dz*dz
	return actualDistance <= distance*distance
}

// ============================================================================
// SCORING AND RANKING
// ============================================================================

// calculateScore calculates relevance score for a search hit
func (se *SearchEngine) calculateScore(hit SearchHit, query *Query) float64 {
	score := 1.0
	
	// Boost exact matches
	if query.Text != "" {
		if strings.EqualFold(hit.Name, query.Text) {
			score += 10.0
		} else if strings.Contains(strings.ToLower(hit.Name), strings.ToLower(query.Text)) {
			score += 5.0
		}
	}
	
	// Boost by type relevance
	if query.Type != "" && strings.EqualFold(hit.Type, query.Type) {
		score += 3.0
	}
	
	// Boost by path relevance
	if query.Path != "" && strings.Contains(hit.Path, query.Path) {
		score += 2.0
	}
	
	// Boost by property matches
	if query.Properties != nil {
		for key, expectedValue := range query.Properties {
			if actualValue, exists := hit.Properties[key]; exists {
				if se.propertyValuesMatch(actualValue, expectedValue) {
					score += 1.0
				}
			}
		}
	}
	
	return score
}

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

// generateCacheKey creates a cache key for a query
func (se *SearchEngine) generateCacheKey(query *Query) string {
	// Simple hash-based cache key
	return fmt.Sprintf("%s-%s-%s-%d", query.Text, query.Type, query.Status, time.Now().Unix()/300) // 5-minute cache windows
}

// isCacheValid checks if cached result is still valid
func (se *SearchEngine) isCacheValid(result *SearchResult) bool {
	// Cache valid for 5 minutes
	return time.Since(result.Timestamp) < 5*time.Minute
}

// queryToString converts a query to a readable string
func (se *SearchEngine) queryToString(query *Query) string {
	parts := []string{}
	
	if query.Text != "" {
		parts = append(parts, fmt.Sprintf("text:'%s'", query.Text))
	}
	if query.Type != "" {
		parts = append(parts, fmt.Sprintf("type:%s", query.Type))
	}
	if query.Status != "" {
		parts = append(parts, fmt.Sprintf("status:%s", query.Status))
	}
	if query.Path != "" {
		parts = append(parts, fmt.Sprintf("path:%s", query.Path))
	}
	
	if len(parts) == 0 {
		return "all"
	}
	
	return strings.Join(parts, " ")
}

// getQueryType determines the type of query
func (se *SearchEngine) getQueryType(query *Query) string {
	if query.Spatial != nil {
		return "spatial"
	}
	if query.Logical != nil {
		return "logical"
	}
	if query.Text != "" {
		return "text"
	}
	return "filter"
}

// sortResults sorts search results by the specified field and order
func (se *SearchEngine) sortResults(results []SearchHit, sortBy, sortOrder string) {
	// Implementation will be added based on sorting requirements
	// For now, results are already sorted by score (highest first)
}

// paginateResults applies pagination to search results
func (se *SearchEngine) paginateResults(results []SearchHit, limit, offset int) []SearchHit {
	if limit <= 0 {
		limit = len(results)
	}
	
	start := offset
	if start >= len(results) {
		return []SearchHit{}
	}
	
	end := start + limit
	if end > len(results) {
		end = len(results)
	}
	
	return results[start:end]
}

// objectToSearchHit converts an ArxObject to a SearchHit
func (se *SearchEngine) objectToSearchHit(obj *ArxObjectMetadata) SearchHit {
	return SearchHit{
		ObjectID:    obj.ID,
		Path:        obj.ID, // Simplified path for now
		Type:        obj.Type,
		Name:        obj.Name,
		Description: obj.Description,
		Score:       0.0, // Will be calculated later
		Properties:  obj.Properties,
		Location:    nil, // Will be populated from spatial data when available
		Metadata:    make(map[string]interface{}),
	}
}
