package portfolio

import (
	"context"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"sync"
	"time"
	
	"github.com/joelpate/arxos/internal/database"
	"github.com/joelpate/arxos/internal/logger"
	"github.com/joelpate/arxos/internal/spatial"
	"github.com/joelpate/arxos/pkg/models"
)

// Building represents a single building in the portfolio
type Building struct {
	ID          string                 `json:"id"`
	Name        string                 `json:"name"`
	Address     string                 `json:"address"`
	Type        string                 `json:"type"` // office, retail, industrial, residential
	SquareFeet  float64                `json:"square_feet"`
	Floors      int                    `json:"floors"`
	YearBuilt   int                    `json:"year_built"`
	FloorPlans  map[string]*models.FloorPlan `json:"floor_plans"`
	Metadata    map[string]interface{} `json:"metadata"`
	LastUpdated time.Time              `json:"last_updated"`
	
	// Runtime components
	db           *database.SQLiteDB
	spatialIndex *spatial.SpatialIndex
	mu           sync.RWMutex
}

// Portfolio manages multiple buildings
type Portfolio struct {
	ID          string               `json:"id"`
	Name        string               `json:"name"`
	Owner       string               `json:"owner"`
	Buildings   map[string]*Building `json:"buildings"`
	BaseDir     string               `json:"base_dir"`
	CreatedAt   time.Time            `json:"created_at"`
	UpdatedAt   time.Time            `json:"updated_at"`
	
	// Runtime state
	activeBuilding string
	mu             sync.RWMutex
}

// Manager handles portfolio operations
type Manager struct {
	portfolios     map[string]*Portfolio
	activePortfolio string
	baseDir        string
	mu             sync.RWMutex
}

// NewManager creates a new portfolio manager
func NewManager(baseDir string) *Manager {
	if baseDir == "" {
		baseDir = ".arxos/portfolios"
	}
	
	return &Manager{
		portfolios: make(map[string]*Portfolio),
		baseDir:    baseDir,
	}
}

// CreatePortfolio creates a new portfolio
func (m *Manager) CreatePortfolio(name, owner string) (*Portfolio, error) {
	m.mu.Lock()
	defer m.mu.Unlock()
	
	id := fmt.Sprintf("portfolio_%d", time.Now().Unix())
	
	portfolio := &Portfolio{
		ID:        id,
		Name:      name,
		Owner:     owner,
		Buildings: make(map[string]*Building),
		BaseDir:   filepath.Join(m.baseDir, id),
		CreatedAt: time.Now(),
		UpdatedAt: time.Now(),
	}
	
	// Create directory structure
	if err := os.MkdirAll(portfolio.BaseDir, 0755); err != nil {
		return nil, fmt.Errorf("failed to create portfolio directory: %w", err)
	}
	
	// Save portfolio metadata
	if err := m.savePortfolio(portfolio); err != nil {
		return nil, fmt.Errorf("failed to save portfolio: %w", err)
	}
	
	m.portfolios[id] = portfolio
	m.activePortfolio = id
	
	logger.Info("Created portfolio: %s (%s)", name, id)
	
	return portfolio, nil
}

// LoadPortfolio loads an existing portfolio
func (m *Manager) LoadPortfolio(id string) (*Portfolio, error) {
	m.mu.Lock()
	defer m.mu.Unlock()
	
	if portfolio, exists := m.portfolios[id]; exists {
		return portfolio, nil
	}
	
	portfolioPath := filepath.Join(m.baseDir, id, "portfolio.json")
	data, err := os.ReadFile(portfolioPath)
	if err != nil {
		return nil, fmt.Errorf("failed to read portfolio file: %w", err)
	}
	
	var portfolio Portfolio
	if err := json.Unmarshal(data, &portfolio); err != nil {
		return nil, fmt.Errorf("failed to parse portfolio: %w", err)
	}
	
	// Load buildings
	for _, building := range portfolio.Buildings {
		if err := m.loadBuildingData(building); err != nil {
			logger.Warn("Failed to load building %s: %v", building.ID, err)
		}
	}
	
	m.portfolios[id] = &portfolio
	m.activePortfolio = id
	
	logger.Info("Loaded portfolio: %s with %d buildings", portfolio.Name, len(portfolio.Buildings))
	
	return &portfolio, nil
}

// AddBuilding adds a building to the active portfolio
func (m *Manager) AddBuilding(name, address, buildingType string, sqft float64, floors, yearBuilt int) (*Building, error) {
	m.mu.RLock()
	portfolio := m.portfolios[m.activePortfolio]
	m.mu.RUnlock()
	
	if portfolio == nil {
		return nil, fmt.Errorf("no active portfolio")
	}
	
	portfolio.mu.Lock()
	defer portfolio.mu.Unlock()
	
	id := fmt.Sprintf("building_%s_%d", sanitizeID(name), time.Now().Unix())
	
	building := &Building{
		ID:          id,
		Name:        name,
		Address:     address,
		Type:        buildingType,
		SquareFeet:  sqft,
		Floors:      floors,
		YearBuilt:   yearBuilt,
		FloorPlans:  make(map[string]*models.FloorPlan),
		Metadata:    make(map[string]interface{}),
		LastUpdated: time.Now(),
	}
	
	// Create building directory
	buildingDir := filepath.Join(portfolio.BaseDir, id)
	if err := os.MkdirAll(buildingDir, 0755); err != nil {
		return nil, fmt.Errorf("failed to create building directory: %w", err)
	}
	
	// Initialize database for building
	dbPath := filepath.Join(buildingDir, "building.db")
	building.db = database.NewSQLiteDB(database.NewConfig(dbPath))
	
	ctx := context.Background()
	if err := building.db.Connect(ctx, dbPath); err != nil {
		return nil, fmt.Errorf("failed to initialize building database: %w", err)
	}
	
	// Initialize spatial index
	building.spatialIndex = spatial.NewSpatialIndex()
	
	portfolio.Buildings[id] = building
	portfolio.UpdatedAt = time.Now()
	
	// Save updated portfolio
	if err := m.savePortfolio(portfolio); err != nil {
		return nil, fmt.Errorf("failed to save portfolio: %w", err)
	}
	
	logger.Info("Added building %s to portfolio %s", name, portfolio.Name)
	
	return building, nil
}

// GetBuilding retrieves a building by ID
func (m *Manager) GetBuilding(buildingID string) (*Building, error) {
	m.mu.RLock()
	defer m.mu.RUnlock()
	
	for _, portfolio := range m.portfolios {
		portfolio.mu.RLock()
		building, exists := portfolio.Buildings[buildingID]
		portfolio.mu.RUnlock()
		
		if exists {
			return building, nil
		}
	}
	
	return nil, fmt.Errorf("building %s not found", buildingID)
}

// SetActiveBuilding sets the active building for operations
func (m *Manager) SetActiveBuilding(buildingID string) error {
	building, err := m.GetBuilding(buildingID)
	if err != nil {
		return err
	}
	
	m.mu.RLock()
	portfolio := m.portfolios[m.activePortfolio]
	m.mu.RUnlock()
	
	if portfolio != nil {
		portfolio.mu.Lock()
		portfolio.activeBuilding = building.ID
		portfolio.mu.Unlock()
	}
	
	logger.Info("Set active building to: %s", building.Name)
	
	return nil
}

// GetActiveBuilding returns the currently active building
func (m *Manager) GetActiveBuilding() (*Building, error) {
	m.mu.RLock()
	portfolio := m.portfolios[m.activePortfolio]
	m.mu.RUnlock()
	
	if portfolio == nil {
		return nil, fmt.Errorf("no active portfolio")
	}
	
	portfolio.mu.RLock()
	defer portfolio.mu.RUnlock()
	
	if portfolio.activeBuilding == "" {
		return nil, fmt.Errorf("no active building")
	}
	
	building, exists := portfolio.Buildings[portfolio.activeBuilding]
	if !exists {
		return nil, fmt.Errorf("active building not found")
	}
	
	return building, nil
}

// AddFloorPlan adds a floor plan to a building
func (m *Manager) AddFloorPlan(buildingID string, plan *models.FloorPlan) error {
	building, err := m.GetBuilding(buildingID)
	if err != nil {
		return err
	}
	
	building.mu.Lock()
	defer building.mu.Unlock()
	
	// Save to database
	ctx := context.Background()
	if building.db != nil {
		if err := building.db.SaveFloorPlan(ctx, plan); err != nil {
			return fmt.Errorf("failed to save floor plan to database: %w", err)
		}
	}
	
	// Update spatial index
	if building.spatialIndex != nil {
		building.spatialIndex.IndexEquipment(plan.Equipment)
		building.spatialIndex.IndexRooms(plan.Rooms)
	}
	
	building.FloorPlans[plan.Name] = plan
	building.LastUpdated = time.Now()
	
	// Save building metadata
	if err := m.saveBuildingData(building); err != nil {
		return fmt.Errorf("failed to save building data: %w", err)
	}
	
	logger.Info("Added floor plan %s to building %s", plan.Name, building.Name)
	
	return nil
}

// QueryAcrossPortfolio executes a query across all buildings in the portfolio
func (m *Manager) QueryAcrossPortfolio(query string) ([]QueryResult, error) {
	m.mu.RLock()
	portfolio := m.portfolios[m.activePortfolio]
	m.mu.RUnlock()
	
	if portfolio == nil {
		return nil, fmt.Errorf("no active portfolio")
	}
	
	results := []QueryResult{}
	ctx := context.Background()
	
	portfolio.mu.RLock()
	defer portfolio.mu.RUnlock()
	
	for _, building := range portfolio.Buildings {
		if building.db == nil {
			continue
		}
		
		// Execute query on building database
		rows, err := building.db.Query(ctx, query)
		if err != nil {
			logger.Warn("Query failed for building %s: %v", building.Name, err)
			continue
		}
		
		// Process results
		for rows.Next() {
			result := QueryResult{
				BuildingID:   building.ID,
				BuildingName: building.Name,
			}
			// Process row data (simplified for example)
			results = append(results, result)
		}
		rows.Close()
	}
	
	logger.Info("Query across portfolio returned %d results", len(results))
	
	return results, nil
}

// FindEquipmentNearby finds equipment near a point across all buildings
func (m *Manager) FindEquipmentNearby(x, y, radius float64) ([]*EquipmentLocation, error) {
	m.mu.RLock()
	portfolio := m.portfolios[m.activePortfolio]
	m.mu.RUnlock()
	
	if portfolio == nil {
		return nil, fmt.Errorf("no active portfolio")
	}
	
	results := []*EquipmentLocation{}
	
	portfolio.mu.RLock()
	defer portfolio.mu.RUnlock()
	
	for _, building := range portfolio.Buildings {
		if building.spatialIndex == nil {
			continue
		}
		
		nearby := building.spatialIndex.FindNearbyEquipment(x, y, radius)
		
		for _, eq := range nearby {
			results = append(results, &EquipmentLocation{
				Equipment:    eq,
				BuildingID:   building.ID,
				BuildingName: building.Name,
			})
		}
	}
	
	return results, nil
}

// GetPortfolioStatistics returns statistics across the portfolio
func (m *Manager) GetPortfolioStatistics() (*PortfolioStats, error) {
	m.mu.RLock()
	portfolio := m.portfolios[m.activePortfolio]
	m.mu.RUnlock()
	
	if portfolio == nil {
		return nil, fmt.Errorf("no active portfolio")
	}
	
	stats := &PortfolioStats{
		PortfolioID:   portfolio.ID,
		PortfolioName: portfolio.Name,
		BuildingCount: len(portfolio.Buildings),
		BuildingStats: make(map[string]*BuildingStats),
	}
	
	portfolio.mu.RLock()
	defer portfolio.mu.RUnlock()
	
	for _, building := range portfolio.Buildings {
		buildingStats := &BuildingStats{
			Name:           building.Name,
			SquareFeet:     building.SquareFeet,
			Floors:         building.Floors,
			FloorPlanCount: len(building.FloorPlans),
		}
		
		// Count equipment across all floor plans
		for _, plan := range building.FloorPlans {
			buildingStats.TotalEquipment += len(plan.Equipment)
			buildingStats.TotalRooms += len(plan.Rooms)
			
			for _, eq := range plan.Equipment {
				switch eq.Status {
				case models.StatusNormal:
					buildingStats.NormalEquipment++
				case models.StatusNeedsRepair:
					buildingStats.NeedsRepairEquipment++
				case models.StatusFailed:
					buildingStats.FailedEquipment++
				}
			}
		}
		
		stats.BuildingStats[building.ID] = buildingStats
		stats.TotalSquareFeet += building.SquareFeet
		stats.TotalEquipment += buildingStats.TotalEquipment
		stats.TotalRooms += buildingStats.TotalRooms
	}
	
	return stats, nil
}

// ListPortfolios lists all available portfolios
func (m *Manager) ListPortfolios() ([]*PortfolioSummary, error) {
	entries, err := os.ReadDir(m.baseDir)
	if err != nil {
		if os.IsNotExist(err) {
			return []*PortfolioSummary{}, nil
		}
		return nil, fmt.Errorf("failed to read portfolios directory: %w", err)
	}
	
	summaries := []*PortfolioSummary{}
	
	for _, entry := range entries {
		if !entry.IsDir() {
			continue
		}
		
		portfolioPath := filepath.Join(m.baseDir, entry.Name(), "portfolio.json")
		data, err := os.ReadFile(portfolioPath)
		if err != nil {
			continue
		}
		
		var portfolio Portfolio
		if err := json.Unmarshal(data, &portfolio); err != nil {
			continue
		}
		
		summary := &PortfolioSummary{
			ID:            portfolio.ID,
			Name:          portfolio.Name,
			Owner:         portfolio.Owner,
			BuildingCount: len(portfolio.Buildings),
			CreatedAt:     portfolio.CreatedAt,
			UpdatedAt:     portfolio.UpdatedAt,
		}
		
		summaries = append(summaries, summary)
	}
	
	return summaries, nil
}

// Helper methods

func (m *Manager) savePortfolio(portfolio *Portfolio) error {
	portfolioPath := filepath.Join(portfolio.BaseDir, "portfolio.json")
	
	data, err := json.MarshalIndent(portfolio, "", "  ")
	if err != nil {
		return fmt.Errorf("failed to marshal portfolio: %w", err)
	}
	
	if err := os.WriteFile(portfolioPath, data, 0644); err != nil {
		return fmt.Errorf("failed to write portfolio file: %w", err)
	}
	
	return nil
}

func (m *Manager) loadBuildingData(building *Building) error {
	buildingDir := filepath.Join(m.baseDir, building.ID)
	
	// Load database
	dbPath := filepath.Join(buildingDir, "building.db")
	if _, err := os.Stat(dbPath); err == nil {
		building.db = database.NewSQLiteDB(database.NewConfig(dbPath))
		ctx := context.Background()
		if err := building.db.Connect(ctx, dbPath); err != nil {
			logger.Warn("Failed to connect to building database: %v", err)
		}
	}
	
	// Initialize spatial index
	building.spatialIndex = spatial.NewSpatialIndex()
	
	// Re-index equipment and rooms
	for _, plan := range building.FloorPlans {
		building.spatialIndex.IndexEquipment(plan.Equipment)
		building.spatialIndex.IndexRooms(plan.Rooms)
	}
	
	return nil
}

func (m *Manager) saveBuildingData(building *Building) error {
	buildingDir := filepath.Join(m.baseDir, m.activePortfolio, building.ID)
	buildingPath := filepath.Join(buildingDir, "building.json")
	
	data, err := json.MarshalIndent(building, "", "  ")
	if err != nil {
		return fmt.Errorf("failed to marshal building: %w", err)
	}
	
	if err := os.WriteFile(buildingPath, data, 0644); err != nil {
		return fmt.Errorf("failed to write building file: %w", err)
	}
	
	return nil
}

func sanitizeID(s string) string {
	// Simple sanitization for IDs
	result := ""
	for _, r := range s {
		if (r >= 'a' && r <= 'z') || (r >= 'A' && r <= 'Z') || (r >= '0' && r <= '9') || r == '_' {
			result += string(r)
		}
	}
	if result == "" {
		result = "building"
	}
	return result
}

// Data structures

type QueryResult struct {
	BuildingID   string
	BuildingName string
	Data         map[string]interface{}
}

type EquipmentLocation struct {
	Equipment    *models.Equipment
	BuildingID   string
	BuildingName string
}

type PortfolioStats struct {
	PortfolioID     string
	PortfolioName   string
	BuildingCount   int
	TotalSquareFeet float64
	TotalEquipment  int
	TotalRooms      int
	BuildingStats   map[string]*BuildingStats
}

type BuildingStats struct {
	Name                 string
	SquareFeet           float64
	Floors               int
	FloorPlanCount       int
	TotalEquipment       int
	TotalRooms           int
	NormalEquipment      int
	NeedsRepairEquipment int
	FailedEquipment      int
}

type PortfolioSummary struct {
	ID            string
	Name          string
	Owner         string
	BuildingCount int
	CreatedAt     time.Time
	UpdatedAt     time.Time
}