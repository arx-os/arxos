package search

import (
	"context"
	"fmt"
	"strings"
	"sync"
	"time"

	"github.com/joelpate/arxos/pkg/models"
)

// SearchEngine provides fast, real-time search capabilities
type SearchEngine struct {
	mu          sync.RWMutex
	buildingIdx map[string]*models.FloorPlan
	equipmentIdx map[string]*models.Equipment
	roomIdx     map[string]*models.Room
	textIdx     map[string][]string // text -> [entity IDs]
}

// NewSearchEngine creates a new search engine
func NewSearchEngine() *SearchEngine {
	return &SearchEngine{
		buildingIdx:  make(map[string]*models.FloorPlan),
		equipmentIdx: make(map[string]*models.Equipment),
		roomIdx:      make(map[string]*models.Room),
		textIdx:      make(map[string][]string),
	}
}

// SearchResult represents a search result
type SearchResult struct {
	ID          string      `json:"id"`
	Type        string      `json:"type"` // building, room, equipment
	Name        string      `json:"name"`
	Description string      `json:"description"`
	Location    string      `json:"location"`
	Status      string      `json:"status,omitempty"`
	Score       float64     `json:"score"`
	Data        interface{} `json:"data"`
}

// SearchOptions configures search behavior
type SearchOptions struct {
	Query      string   `json:"query"`
	Types      []string `json:"types"`      // Filter by entity types
	Status     []string `json:"status"`     // Filter by status
	BuildingID string   `json:"building_id"` // Filter by building
	Limit      int      `json:"limit"`
	Offset     int      `json:"offset"`
	SortBy     string   `json:"sort_by"` // relevance, name, updated
}

// Index adds or updates an entity in the search index
func (s *SearchEngine) Index(ctx context.Context, entityType string, id string, data interface{}) error {
	s.mu.Lock()
	defer s.mu.Unlock()

	switch entityType {
	case "building":
		if fp, ok := data.(*models.FloorPlan); ok {
			s.buildingIdx[id] = fp
			s.indexText(fp.Name, id)
			s.indexText(fp.Building, id)
		}
	case "equipment":
		if eq, ok := data.(*models.Equipment); ok {
			s.equipmentIdx[id] = eq
			s.indexText(eq.Name, id)
			s.indexText(eq.Type, id)
			s.indexText(eq.Notes, id)
		}
	case "room":
		if rm, ok := data.(*models.Room); ok {
			s.roomIdx[id] = rm
			s.indexText(rm.Name, id)
		}
	default:
		return fmt.Errorf("unknown entity type: %s", entityType)
	}

	return nil
}

// indexText adds text to the inverted index
func (s *SearchEngine) indexText(text string, entityID string) {
	if text == "" {
		return
	}

	// Tokenize and normalize
	tokens := s.tokenize(text)
	for _, token := range tokens {
		ids := s.textIdx[token]
		// Check if ID already exists
		exists := false
		for _, id := range ids {
			if id == entityID {
				exists = true
				break
			}
		}
		if !exists {
			s.textIdx[token] = append(ids, entityID)
		}
	}
}

// tokenize breaks text into searchable tokens
func (s *SearchEngine) tokenize(text string) []string {
	// Convert to lowercase and split
	text = strings.ToLower(text)
	words := strings.Fields(text)
	
	tokens := make([]string, 0, len(words)*2)
	for _, word := range words {
		// Remove punctuation
		word = strings.Trim(word, ".,!?;:'\"")
		if word != "" {
			tokens = append(tokens, word)
			// Add prefixes for partial matching
			for i := 1; i <= len(word) && i <= 5; i++ {
				tokens = append(tokens, word[:i])
			}
		}
	}
	
	return tokens
}

// Search performs a search query
func (s *SearchEngine) Search(ctx context.Context, opts SearchOptions) ([]SearchResult, error) {
	s.mu.RLock()
	defer s.mu.RUnlock()

	if opts.Limit == 0 {
		opts.Limit = 20
	}

	results := []SearchResult{}
	
	// Tokenize query
	queryTokens := s.tokenize(opts.Query)
	if len(queryTokens) == 0 {
		return results, nil
	}

	// Find matching entity IDs
	entityScores := make(map[string]float64)
	for _, token := range queryTokens {
		if ids, ok := s.textIdx[token]; ok {
			for _, id := range ids {
				entityScores[id] += 1.0
			}
		}
	}

	// Convert to results
	for id, score := range entityScores {
		// Check buildings
		if building, ok := s.buildingIdx[id]; ok {
			if s.matchesFilters(opts, "building", nil) {
				results = append(results, SearchResult{
					ID:          id,
					Type:        "building",
					Name:        building.Name,
					Description: fmt.Sprintf("%s - Level %d", building.Building, building.Level),
					Score:       score,
					Data:        building,
				})
			}
		}
		
		// Check equipment
		if equipment, ok := s.equipmentIdx[id]; ok {
			if s.matchesFilters(opts, "equipment", equipment) {
				results = append(results, SearchResult{
					ID:          id,
					Type:        "equipment",
					Name:        equipment.Name,
					Description: equipment.Type,
					Status:      string(equipment.Status),
					Score:       score,
					Data:        equipment,
				})
			}
		}
		
		// Check rooms
		if room, ok := s.roomIdx[id]; ok {
			if s.matchesFilters(opts, "room", nil) {
				results = append(results, SearchResult{
					ID:          id,
					Type:        "room",
					Name:        room.Name,
					Description: fmt.Sprintf("Room %s", room.ID),
					Score:       score,
					Data:        room,
				})
			}
		}
	}

	// Sort by score
	s.sortResults(results, opts.SortBy)

	// Apply pagination
	start := opts.Offset
	end := opts.Offset + opts.Limit
	if start > len(results) {
		return []SearchResult{}, nil
	}
	if end > len(results) {
		end = len(results)
	}

	return results[start:end], nil
}

// matchesFilters checks if an entity matches search filters
func (s *SearchEngine) matchesFilters(opts SearchOptions, entityType string, equipment *models.Equipment) bool {
	// Type filter
	if len(opts.Types) > 0 {
		found := false
		for _, t := range opts.Types {
			if t == entityType {
				found = true
				break
			}
		}
		if !found {
			return false
		}
	}

	// Status filter (only for equipment)
	if len(opts.Status) > 0 && equipment != nil {
		found := false
		for _, status := range opts.Status {
			if string(equipment.Status) == status {
				found = true
				break
			}
		}
		if !found {
			return false
		}
	}

	return true
}

// sortResults sorts search results
func (s *SearchEngine) sortResults(results []SearchResult, sortBy string) {
	// Simple bubble sort for now (in production, use sort.Slice)
	for i := 0; i < len(results); i++ {
		for j := i + 1; j < len(results); j++ {
			swap := false
			switch sortBy {
			case "name":
				swap = results[i].Name > results[j].Name
			default: // relevance
				swap = results[i].Score < results[j].Score
			}
			if swap {
				results[i], results[j] = results[j], results[i]
			}
		}
	}
}

// Suggest provides search suggestions based on partial input
func (s *SearchEngine) Suggest(ctx context.Context, prefix string, limit int) []string {
	s.mu.RLock()
	defer s.mu.RUnlock()

	if limit == 0 {
		limit = 10
	}

	suggestions := []string{}
	prefix = strings.ToLower(prefix)

	// Find all tokens that start with prefix
	seen := make(map[string]bool)
	for token := range s.textIdx {
		if strings.HasPrefix(token, prefix) && !seen[token] {
			// Get the original text (approximation)
			for _, id := range s.textIdx[token] {
				if building, ok := s.buildingIdx[id]; ok && !seen[building.Name] {
					suggestions = append(suggestions, building.Name)
					seen[building.Name] = true
				}
				if equipment, ok := s.equipmentIdx[id]; ok && !seen[equipment.Name] {
					suggestions = append(suggestions, equipment.Name)
					seen[equipment.Name] = true
				}
				if room, ok := s.roomIdx[id]; ok && !seen[room.Name] {
					suggestions = append(suggestions, room.Name)
					seen[room.Name] = true
				}
			}
		}
		if len(suggestions) >= limit {
			break
		}
	}

	return suggestions
}

// Clear removes all data from the search index
func (s *SearchEngine) Clear() {
	s.mu.Lock()
	defer s.mu.Unlock()

	s.buildingIdx = make(map[string]*models.FloorPlan)
	s.equipmentIdx = make(map[string]*models.Equipment)
	s.roomIdx = make(map[string]*models.Room)
	s.textIdx = make(map[string][]string)
}

// Stats returns search engine statistics
func (s *SearchEngine) Stats() map[string]int {
	s.mu.RLock()
	defer s.mu.RUnlock()

	return map[string]int{
		"buildings":    len(s.buildingIdx),
		"equipment":    len(s.equipmentIdx),
		"rooms":        len(s.roomIdx),
		"text_tokens":  len(s.textIdx),
	}
}

// RecentSearches tracks and returns recent search queries
type RecentSearches struct {
	mu       sync.RWMutex
	searches []SearchQuery
	maxSize  int
}

// SearchQuery represents a search query with metadata
type SearchQuery struct {
	Query     string    `json:"query"`
	Timestamp time.Time `json:"timestamp"`
	Results   int       `json:"results"`
	UserID    string    `json:"user_id,omitempty"`
}

// NewRecentSearches creates a new recent searches tracker
func NewRecentSearches(maxSize int) *RecentSearches {
	return &RecentSearches{
		searches: make([]SearchQuery, 0, maxSize),
		maxSize:  maxSize,
	}
}

// Add adds a search query to recent searches
func (r *RecentSearches) Add(query SearchQuery) {
	r.mu.Lock()
	defer r.mu.Unlock()

	r.searches = append(r.searches, query)
	if len(r.searches) > r.maxSize {
		r.searches = r.searches[1:]
	}
}

// Get returns recent searches
func (r *RecentSearches) Get(limit int) []SearchQuery {
	r.mu.RLock()
	defer r.mu.RUnlock()

	if limit == 0 || limit > len(r.searches) {
		limit = len(r.searches)
	}

	// Return most recent first
	result := make([]SearchQuery, limit)
	for i := 0; i < limit; i++ {
		result[i] = r.searches[len(r.searches)-1-i]
	}

	return result
}

// Popular returns the most popular search terms
func (r *RecentSearches) Popular(limit int) []string {
	r.mu.RLock()
	defer r.mu.RUnlock()

	counts := make(map[string]int)
	for _, search := range r.searches {
		counts[search.Query]++
	}

	// Sort by count (simple implementation)
	popular := make([]string, 0, len(counts))
	for query := range counts {
		popular = append(popular, query)
	}

	// Sort by frequency
	for i := 0; i < len(popular); i++ {
		for j := i + 1; j < len(popular); j++ {
			if counts[popular[i]] < counts[popular[j]] {
				popular[i], popular[j] = popular[j], popular[i]
			}
		}
	}

	if limit > 0 && limit < len(popular) {
		popular = popular[:limit]
	}

	return popular
}