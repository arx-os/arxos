package symbols

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"regexp"
	"strings"
	"time"

	"github.com/google/uuid"
	"gorm.io/gorm"
)

// Symbol represents a symbol in the system
type Symbol struct {
	ID          string                 `json:"id" gorm:"primaryKey"`
	Name        string                 `json:"name" gorm:"not null"`
	System      string                 `json:"system" gorm:"not null"`
	Category    string                 `json:"category"`
	Description string                 `json:"description"`
	SVG         SVGContent             `json:"svg" gorm:"embedded"`
	Properties  map[string]interface{} `json:"properties" gorm:"type:json"`
	Connections []Connection           `json:"connections" gorm:"type:json"`
	Tags        []string               `json:"tags" gorm:"type:json"`
	Metadata    map[string]interface{} `json:"metadata" gorm:"type:json"`
	Version     string                 `json:"version"`
	CreatedAt   time.Time              `json:"created_at"`
	UpdatedAt   time.Time              `json:"updated_at"`
}

// SVGContent represents the SVG content of a symbol
type SVGContent struct {
	Content string  `json:"content"`
	Width   float64 `json:"width,omitempty"`
	Height  float64 `json:"height,omitempty"`
	Scale   float64 `json:"scale,omitempty"`
}

// Connection represents a connection point for a symbol
type Connection struct {
	ID       string                 `json:"id"`
	Type     string                 `json:"type"`
	Position Point                  `json:"position"`
	Metadata map[string]interface{} `json:"metadata,omitempty"`
}

// Point represents a 2D point
type Point struct {
	X float64 `json:"x"`
	Y float64 `json:"y"`
}

// SymbolService provides CRUD operations for symbols
type SymbolService struct {
	db          *gorm.DB
	libraryPath string
	validator   *SymbolValidator
	renderer    *SymbolRenderer
	generator   *SymbolGenerator
	analytics   *SymbolAnalytics
}

// NewSymbolService creates a new symbol service instance
func NewSymbolService(db *gorm.DB, libraryPath string) *SymbolService {
	return &SymbolService{
		db:          db,
		libraryPath: libraryPath,
		validator:   NewSymbolValidator(),
		renderer:    NewSymbolRenderer(),
		generator:   NewSymbolGenerator(),
		analytics:   NewSymbolAnalytics(db),
	}
}

// CreateSymbol creates a new symbol with validation and file management
func (s *SymbolService) CreateSymbol(symbolData map[string]interface{}) (*Symbol, error) {
	// Validate symbol data
	if err := s.validator.ValidateSymbol(symbolData); err != nil {
		return nil, fmt.Errorf("invalid symbol data: %w", err)
	}

	// Generate symbol ID if not provided
	if id, exists := symbolData["id"]; !exists || id == "" {
		symbolData["id"] = s.generateSymbolID(symbolData)
	}

	symbolID := symbolData["id"].(string)

	// Check if symbol already exists
	if s.symbolExists(symbolID) {
		return nil, fmt.Errorf("symbol with ID '%s' already exists", symbolID)
	}

	// Convert to Symbol struct
	symbol, err := s.mapToSymbol(symbolData)
	if err != nil {
		return nil, fmt.Errorf("failed to convert symbol data: %w", err)
	}

	// Add creation metadata
	symbol = s.addCreationMetadata(symbol)

	// Determine file path
	filePath := s.determineSymbolFilePath(symbol)

	// Ensure system directory exists
	systemDir := filepath.Dir(filePath)
	if err := os.MkdirAll(systemDir, 0755); err != nil {
		return nil, fmt.Errorf("failed to create system directory: %w", err)
	}

	// Write symbol file
	if err := s.writeSymbolFile(filePath, symbol); err != nil {
		return nil, fmt.Errorf("failed to write symbol file: %w", err)
	}

	// Save to database
	if err := s.db.Create(symbol).Error; err != nil {
		return nil, fmt.Errorf("failed to save symbol to database: %w", err)
	}

	return symbol, nil
}

// GetSymbol retrieves a symbol by ID
func (s *SymbolService) GetSymbol(symbolID string) (*Symbol, error) {
	var symbol Symbol
	if err := s.db.Where("id = ?", symbolID).First(&symbol).Error; err != nil {
		if err == gorm.ErrRecordNotFound {
			return nil, fmt.Errorf("symbol '%s' not found", symbolID)
		}
		return nil, fmt.Errorf("failed to retrieve symbol: %w", err)
	}
	return &symbol, nil
}

// UpdateSymbol updates an existing symbol
func (s *SymbolService) UpdateSymbol(symbolID string, updates map[string]interface{}) (*Symbol, error) {
	// Get existing symbol
	existingSymbol, err := s.GetSymbol(symbolID)
	if err != nil {
		return nil, err
	}

	// Merge updates with existing data
	updatedSymbol := s.mergeSymbolData(existingSymbol, updates)

	// Validate updated symbol
	if err := s.validator.ValidateSymbol(s.mergeSymbolData(existingSymbol, updates)); err != nil {
		return nil, fmt.Errorf("updated symbol data is invalid: %w", err)
	}

	// Add update metadata
	updatedSymbol = s.addUpdateMetadata(updatedSymbol)

	// Determine file path
	filePath := s.determineSymbolFilePath(updatedSymbol)

	// Write updated symbol
	if err := s.writeSymbolFile(filePath, updatedSymbol); err != nil {
		return nil, fmt.Errorf("failed to write updated symbol file: %w", err)
	}

	// Update in database
	if err := s.db.Save(updatedSymbol).Error; err != nil {
		return nil, fmt.Errorf("failed to update symbol in database: %w", err)
	}

	return updatedSymbol, nil
}

// DeleteSymbol deletes a symbol by ID
func (s *SymbolService) DeleteSymbol(symbolID string) error {
	// Get symbol to determine file path
	symbol, err := s.GetSymbol(symbolID)
	if err != nil {
		return err
	}

	// Determine file path
	filePath := s.determineSymbolFilePath(symbol)

	// Delete the file
	if err := os.Remove(filePath); err != nil && !os.IsNotExist(err) {
		return fmt.Errorf("failed to delete symbol file: %w", err)
	}

	// Delete from database
	if err := s.db.Delete(symbol).Error; err != nil {
		return fmt.Errorf("failed to delete symbol from database: %w", err)
	}

	return nil
}

// ListSymbols lists all symbols or symbols for a specific system
func (s *SymbolService) ListSymbols(system string) ([]*Symbol, error) {
	var symbols []*Symbol
	query := s.db

	if system != "" {
		query = query.Where("system = ?", system)
	}

	if err := query.Find(&symbols).Error; err != nil {
		return nil, fmt.Errorf("failed to list symbols: %w", err)
	}

	return symbols, nil
}

// SearchSymbols searches for symbols based on query and system
func (s *SymbolService) SearchSymbols(query string, system string) ([]*Symbol, error) {
	var symbols []*Symbol
	dbQuery := s.db

	if system != "" {
		dbQuery = dbQuery.Where("system = ?", system)
	}

	if query != "" {
		dbQuery = dbQuery.Where("name ILIKE ? OR description ILIKE ? OR category ILIKE ?",
			"%"+query+"%", "%"+query+"%", "%"+query+"%")
	}

	if err := dbQuery.Find(&symbols).Error; err != nil {
		return nil, fmt.Errorf("failed to search symbols: %w", err)
	}

	return symbols, nil
}

// BulkCreateSymbols creates multiple symbols with validation
func (s *SymbolService) BulkCreateSymbols(symbols []map[string]interface{}) ([]*Symbol, []error) {
	var createdSymbols []*Symbol
	var errors []error

	for i, symbolData := range symbols {
		symbol, err := s.CreateSymbol(symbolData)
		if err != nil {
			errors = append(errors, fmt.Errorf("symbol %d (%s): %w", i+1, symbolData["name"], err))
			continue
		}
		createdSymbols = append(createdSymbols, symbol)
	}

	return createdSymbols, errors
}

// BulkUpdateSymbols updates multiple symbols
func (s *SymbolService) BulkUpdateSymbols(updates []map[string]interface{}) ([]*Symbol, []error) {
	var updatedSymbols []*Symbol
	var errors []error

	for i, update := range updates {
		symbolID, ok := update["id"].(string)
		if !ok {
			errors = append(errors, fmt.Errorf("update %d: missing symbol ID", i+1))
			continue
		}

		symbol, err := s.UpdateSymbol(symbolID, update)
		if err != nil {
			errors = append(errors, fmt.Errorf("symbol %s: %w", symbolID, err))
			continue
		}
		updatedSymbols = append(updatedSymbols, symbol)
	}

	return updatedSymbols, errors
}

// BulkDeleteSymbols deletes multiple symbols by ID
func (s *SymbolService) BulkDeleteSymbols(symbolIDs []string) map[string]error {
	results := make(map[string]error)

	for _, symbolID := range symbolIDs {
		if err := s.DeleteSymbol(symbolID); err != nil {
			results[symbolID] = err
		}
	}

	return results
}

// GetSymbolStatistics returns statistics about symbols in the library
func (s *SymbolService) GetSymbolStatistics() (map[string]interface{}, error) {
	var totalCount int64
	if err := s.db.Model(&Symbol{}).Count(&totalCount).Error; err != nil {
		return nil, fmt.Errorf("failed to count symbols: %w", err)
	}

	// Count by system
	var systemStats []struct {
		System string `json:"system"`
		Count  int64  `json:"count"`
	}
	if err := s.db.Model(&Symbol{}).
		Select("system, count(*) as count").
		Group("system").
		Scan(&systemStats).Error; err != nil {
		return nil, fmt.Errorf("failed to get system statistics: %w", err)
	}

	// Get recent symbols (last 10 created)
	var recentSymbols []*Symbol
	if err := s.db.Order("created_at DESC").Limit(10).Find(&recentSymbols).Error; err != nil {
		return nil, fmt.Errorf("failed to get recent symbols: %w", err)
	}

	stats := map[string]interface{}{
		"total_symbols":  totalCount,
		"systems":        systemStats,
		"recent_symbols": recentSymbols,
	}

	return stats, nil
}

// Helper methods

func (s *SymbolService) generateSymbolID(symbolData map[string]interface{}) string {
	name, _ := symbolData["name"].(string)
	if name == "" {
		system, _ := symbolData["system"].(string)
		if system == "" {
			system = "unknown"
		}
		return fmt.Sprintf("%s_%s", system, uuid.New().String()[:8])
	}

	// Normalize name to ID format
	normalized := s.normalizeNameToID(name)

	// Ensure uniqueness
	counter := 1
	symbolID := normalized
	for s.symbolExists(symbolID) {
		symbolID = fmt.Sprintf("%s_%d", normalized, counter)
		counter++
	}

	return symbolID
}

func (s *SymbolService) normalizeNameToID(name string) string {
	// Convert to lowercase
	normalized := strings.ToLower(name)

	// Replace spaces and special characters with underscores
	re := regexp.MustCompile(`[^a-z0-9]+`)
	normalized = re.ReplaceAllString(normalized, "_")

	// Remove leading/trailing underscores
	normalized = strings.Trim(normalized, "_")

	// Ensure it starts with a letter
	if normalized != "" && !isLetter(normalized[0]) {
		normalized = "symbol_" + normalized
	}

	// Limit length
	if len(normalized) > 50 {
		normalized = normalized[:50]
	}

	return normalized
}

func isLetter(r byte) bool {
	return (r >= 'a' && r <= 'z') || (r >= 'A' && r <= 'Z')
}

func (s *SymbolService) symbolExists(symbolID string) bool {
	var count int64
	s.db.Model(&Symbol{}).Where("id = ?", symbolID).Count(&count)
	return count > 0
}

func (s *SymbolService) determineSymbolFilePath(symbol *Symbol) string {
	system := strings.ToLower(symbol.System)
	symbolID := symbol.ID
	return filepath.Join(s.libraryPath, "symbols", system, symbolID+".json")
}

func (s *SymbolService) writeSymbolFile(filePath string, symbol *Symbol) error {
	data, err := json.MarshalIndent(symbol, "", "  ")
	if err != nil {
		return err
	}

	return os.WriteFile(filePath, data, 0644)
}

func (s *SymbolService) addCreationMetadata(symbol *Symbol) *Symbol {
	symbol.CreatedAt = time.Now()
	symbol.UpdatedAt = time.Now()
	symbol.Version = "1.0"

	if symbol.Metadata == nil {
		symbol.Metadata = make(map[string]interface{})
	}
	symbol.Metadata["created_by"] = "symbol_service"
	symbol.Metadata["created_date"] = time.Now().Format(time.RFC3339)

	return symbol
}

func (s *SymbolService) addUpdateMetadata(symbol *Symbol) *Symbol {
	symbol.UpdatedAt = time.Now()

	// Update version
	if symbol.Version != "" {
		parts := strings.Split(symbol.Version, ".")
		if len(parts) == 2 {
			if minor, err := parseInt(parts[1]); err == nil {
				symbol.Version = fmt.Sprintf("%s.%d", parts[0], minor+1)
			}
		}
	} else {
		symbol.Version = "1.1"
	}

	if symbol.Metadata == nil {
		symbol.Metadata = make(map[string]interface{})
	}
	symbol.Metadata["updated_by"] = "symbol_service"
	symbol.Metadata["updated_date"] = time.Now().Format(time.RFC3339)

	return symbol
}

func (s *SymbolService) mapToSymbol(data map[string]interface{}) (*Symbol, error) {
	jsonData, err := json.Marshal(data)
	if err != nil {
		return nil, err
	}

	var symbol Symbol
	if err := json.Unmarshal(jsonData, &symbol); err != nil {
		return nil, err
	}

	return &symbol, nil
}

func (s *SymbolService) mergeSymbolData(existing *Symbol, updates map[string]interface{}) *Symbol {
	// Convert existing symbol to map
	existingData, _ := json.Marshal(existing)
	var existingMap map[string]interface{}
	json.Unmarshal(existingData, &existingMap)

	// Merge updates
	for key, value := range updates {
		existingMap[key] = value
	}

	// Convert back to symbol
	mergedData, _ := json.Marshal(existingMap)
	var mergedSymbol Symbol
	json.Unmarshal(mergedData, &mergedSymbol)

	return &mergedSymbol
}

func parseInt(s string) (int, error) {
	var i int
	_, err := fmt.Sscanf(s, "%d", &i)
	return i, err
}
