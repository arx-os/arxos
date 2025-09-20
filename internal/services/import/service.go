package importservice

import (
	"context"
	"fmt"
	"path/filepath"
	"strings"

	"github.com/jmoiron/sqlx"
	"github.com/arx-os/arxos/internal/adapters/postgis"
	"github.com/arx-os/arxos/internal/core/building"
	"github.com/arx-os/arxos/internal/core/equipment"
)

// Service handles all import operations with a single, unified pipeline
type Service struct {
	buildingRepo  building.Repository
	equipmentRepo equipment.Repository
	db            *postgis.Client
}

// NewService creates a new import service
func NewService(db *postgis.Client, buildingRepo building.Repository, equipmentRepo equipment.Repository) *Service {
	return &Service{
		buildingRepo:  buildingRepo,
		equipmentRepo: equipmentRepo,
		db:            db,
	}
}

// ImportFile imports a file based on its extension
func (s *Service) ImportFile(ctx context.Context, filePath string, buildingID string) error {
	ext := strings.ToLower(filepath.Ext(filePath))

	switch ext {
	case ".ifc":
		return s.ImportIFC(ctx, filePath, buildingID)
	case ".csv":
		return s.ImportCSV(ctx, filePath, buildingID)
	case ".json", ".geojson":
		return s.ImportJSON(ctx, filePath, buildingID)
	case ".txt":
		if strings.HasSuffix(filePath, ".bim.txt") {
			return s.ImportBIM(ctx, filePath, buildingID)
		}
		return fmt.Errorf("unsupported text file format")
	default:
		return fmt.Errorf("unsupported file format: %s", ext)
	}
}

// ImportIFC imports an IFC file directly to PostGIS
func (s *Service) ImportIFC(ctx context.Context, filePath string, buildingID string) error {
	// Parse IFC file
	parser := NewIFCParser()
	data, err := parser.Parse(filePath)
	if err != nil {
		return fmt.Errorf("failed to parse IFC file: %w", err)
	}

	// Create or update building
	bldg, err := s.ensureBuilding(ctx, buildingID, data.BuildingName)
	if err != nil {
		return fmt.Errorf("failed to ensure building: %w", err)
	}

	// Import equipment in a transaction
	return s.db.InTransaction(ctx, func(tx *sqlx.Tx) error {
		for _, eq := range data.Equipment {
			// Create equipment entity
			equip := equipment.NewEquipment(
				bldg.ID,
				eq.Path,
				eq.Name,
				eq.Type,
			)

			// Set position if available
			if eq.Position != nil {
				equip.Position = &equipment.Position{
					X: eq.Position.X,
					Y: eq.Position.Y,
					Z: eq.Position.Z,
				}
				equip.Confidence = equipment.ConfidenceEstimated
			}

			// Set metadata
			equip.Metadata = eq.Properties

			// Save to database
			if err := s.equipmentRepo.Create(ctx, equip); err != nil {
				// Update if already exists
				existing, getErr := s.equipmentRepo.GetByPath(ctx, bldg.ID, eq.Path)
				if getErr == nil && existing != nil {
					equip.ID = existing.ID
					if err := s.equipmentRepo.Update(ctx, equip); err != nil {
						return fmt.Errorf("failed to update equipment %s: %w", eq.Path, err)
					}
				} else {
					return fmt.Errorf("failed to create equipment %s: %w", eq.Path, err)
				}
			}
		}

		return nil
	})
}

// ImportCSV imports a CSV file directly to PostGIS
func (s *Service) ImportCSV(ctx context.Context, filePath string, buildingID string) error {
	// Parse CSV file
	parser := NewCSVParser()
	data, err := parser.Parse(filePath)
	if err != nil {
		return fmt.Errorf("failed to parse CSV file: %w", err)
	}

	// Create or update building
	bldg, err := s.ensureBuilding(ctx, buildingID, "")
	if err != nil {
		return fmt.Errorf("failed to ensure building: %w", err)
	}

	// Import equipment
	return s.db.InTransaction(ctx, func(tx *sqlx.Tx) error {
		for _, eq := range data.Equipment {
			// Create equipment entity
			equip := equipment.NewEquipment(
				bldg.ID,
				eq.Path,
				eq.Name,
				eq.Type,
			)

			// Set position if available
			if eq.Position != nil {
				equip.Position = &equipment.Position{
					X: eq.Position.X,
					Y: eq.Position.Y,
					Z: eq.Position.Z,
				}
				equip.Confidence = equipment.ConfidenceEstimated
			}

			// Set metadata
			equip.Metadata = eq.Properties

			// Save to database
			if err := s.equipmentRepo.Create(ctx, equip); err != nil {
				// Try update if exists
				existing, getErr := s.equipmentRepo.GetByPath(ctx, bldg.ID, eq.Path)
				if getErr == nil && existing != nil {
					equip.ID = existing.ID
					if err := s.equipmentRepo.Update(ctx, equip); err != nil {
						return fmt.Errorf("failed to update equipment: %w", err)
					}
				} else {
					return fmt.Errorf("failed to create equipment: %w", err)
				}
			}
		}

		return nil
	})
}

// ImportJSON imports a JSON/GeoJSON file directly to PostGIS
func (s *Service) ImportJSON(ctx context.Context, filePath string, buildingID string) error {
	// Parse JSON file
	parser := NewJSONParser()
	data, err := parser.Parse(filePath)
	if err != nil {
		return fmt.Errorf("failed to parse JSON file: %w", err)
	}

	// Create or update building
	bldg, err := s.ensureBuilding(ctx, buildingID, data.BuildingName)
	if err != nil {
		return fmt.Errorf("failed to ensure building: %w", err)
	}

	// Import equipment
	return s.db.InTransaction(ctx, func(tx *sqlx.Tx) error {
		for _, eq := range data.Equipment {
			// Create equipment entity
			equip := equipment.NewEquipment(
				bldg.ID,
				eq.Path,
				eq.Name,
				eq.Type,
			)

			// Set position if available
			if eq.Position != nil {
				equip.Position = &equipment.Position{
					X: eq.Position.X,
					Y: eq.Position.Y,
					Z: eq.Position.Z,
				}
				equip.Confidence = equipment.ConfidenceEstimated
			}

			// Set metadata
			equip.Metadata = eq.Properties

			// Save to database
			if err := s.equipmentRepo.Create(ctx, equip); err != nil {
				// Try update if exists
				existing, getErr := s.equipmentRepo.GetByPath(ctx, bldg.ID, eq.Path)
				if getErr == nil && existing != nil {
					equip.ID = existing.ID
					if err := s.equipmentRepo.Update(ctx, equip); err != nil {
						return fmt.Errorf("failed to update equipment %s: %w", eq.Path, err)
					}
				} else {
					return fmt.Errorf("failed to create equipment %s: %w", eq.Path, err)
				}
			}
		}
		return nil
	})
}

// ImportBIM imports a .bim.txt file directly to PostGIS
func (s *Service) ImportBIM(ctx context.Context, filePath string, buildingID string) error {
	// Parse BIM text file
	parser := NewBIMParser()
	data, err := parser.Parse(filePath)
	if err != nil {
		return fmt.Errorf("failed to parse BIM file: %w", err)
	}

	// Create or update building
	bldg, err := s.ensureBuilding(ctx, buildingID, data.BuildingName)
	if err != nil {
		return fmt.Errorf("failed to ensure building: %w", err)
	}

	// Import equipment
	return s.db.InTransaction(ctx, func(tx *sqlx.Tx) error {
		for _, eq := range data.Equipment {
			// Create equipment entity
			equip := equipment.NewEquipment(
				bldg.ID,
				eq.Path,
				eq.Name,
				eq.Type,
			)

			// Set position if available
			if eq.Position != nil {
				equip.Position = &equipment.Position{
					X: eq.Position.X,
					Y: eq.Position.Y,
					Z: eq.Position.Z,
				}
				equip.Confidence = equipment.ConfidenceEstimated
			}

			// Set metadata
			equip.Metadata = eq.Properties

			// Save to database
			if err := s.equipmentRepo.Create(ctx, equip); err != nil {
				// Try update if exists
				existing, getErr := s.equipmentRepo.GetByPath(ctx, bldg.ID, eq.Path)
				if getErr == nil && existing != nil {
					equip.ID = existing.ID
					if err := s.equipmentRepo.Update(ctx, equip); err != nil {
						return fmt.Errorf("failed to update equipment %s: %w", eq.Path, err)
					}
				} else {
					return fmt.Errorf("failed to create equipment %s: %w", eq.Path, err)
				}
			}
		}

		return nil
	})
}

// ensureBuilding creates or retrieves a building
func (s *Service) ensureBuilding(ctx context.Context, arxosID, name string) (*building.Building, error) {
	// Try to get existing building
	bldg, err := s.buildingRepo.GetByArxosID(ctx, arxosID)
	if err == nil && bldg != nil {
		return bldg, nil
	}

	// Create new building
	bldg = building.NewBuilding(arxosID, name)
	if name == "" {
		bldg.Name = arxosID
	}

	if err := s.buildingRepo.Create(ctx, bldg); err != nil {
		return nil, fmt.Errorf("failed to create building: %w", err)
	}

	return bldg, nil
}

// importGeoJSONFeatures imports GeoJSON features
func (s *Service) importGeoJSONFeatures(ctx context.Context, bldg *building.Building, features []interface{}) error {
	return s.db.InTransaction(ctx, func(tx *sqlx.Tx) error {
		for _, feature := range features {
			f, ok := feature.(map[string]interface{})
			if !ok {
				continue
			}

			// Extract properties
			props, _ := f["properties"].(map[string]interface{})
			geometry, _ := f["geometry"].(map[string]interface{})

			// Get equipment details
			path, _ := props["path"].(string)
			name, _ := props["name"].(string)
			eqType, _ := props["type"].(string)

			if path == "" {
				continue
			}

			// Create equipment
			equip := equipment.NewEquipment(bldg.ID, path, name, eqType)

			// Extract coordinates from geometry
			if geometry["type"] == "Point" {
				if coords, ok := geometry["coordinates"].([]interface{}); ok && len(coords) >= 2 {
					lon, _ := coords[0].(float64)
					lat, _ := coords[1].(float64)
					alt := 0.0
					if len(coords) >= 3 {
						alt, _ = coords[2].(float64)
					}

					equip.Position = &equipment.Position{
						X: lon,
						Y: lat,
						Z: alt,
					}
				}
			}

			// Save to database
			if err := s.equipmentRepo.Create(ctx, equip); err != nil {
				// Try update if exists
				existing, getErr := s.equipmentRepo.GetByPath(ctx, bldg.ID, path)
				if getErr == nil && existing != nil {
					equip.ID = existing.ID
					if err := s.equipmentRepo.Update(ctx, equip); err != nil {
						return fmt.Errorf("failed to update equipment: %w", err)
					}
				}
			}
		}

		return nil
	})
}

// importJSONEquipment imports regular JSON equipment
func (s *Service) importJSONEquipment(ctx context.Context, bldg *building.Building, equipmentList []interface{}) error {
	return s.db.InTransaction(ctx, func(tx *sqlx.Tx) error {
		for _, item := range equipmentList {
			eq, ok := item.(map[string]interface{})
			if !ok {
				continue
			}

			// Extract equipment details
			path, _ := eq["path"].(string)
			name, _ := eq["name"].(string)
			eqType, _ := eq["type"].(string)

			if path == "" {
				continue
			}

			// Create equipment
			equip := equipment.NewEquipment(bldg.ID, path, name, eqType)

			// Extract position
			if pos, ok := eq["position"].(map[string]interface{}); ok {
				x, _ := pos["x"].(float64)
				y, _ := pos["y"].(float64)
				z, _ := pos["z"].(float64)

				equip.Position = &equipment.Position{
					X: x,
					Y: y,
					Z: z,
				}
			}

			// Set status
			if status, ok := eq["status"].(string); ok {
				equip.Status = status
			}

			// Save to database
			if err := s.equipmentRepo.Create(ctx, equip); err != nil {
				// Try update if exists
				existing, getErr := s.equipmentRepo.GetByPath(ctx, bldg.ID, path)
				if getErr == nil && existing != nil {
					equip.ID = existing.ID
					if err := s.equipmentRepo.Update(ctx, equip); err != nil {
						return fmt.Errorf("failed to update equipment: %w", err)
					}
				}
			}
		}

		return nil
	})
}

// Helper function to parse position from CSV row
func parsePosition(row map[string]string) (lon, lat, alt float64) {
	// Try different column names
	lonStr := row["longitude"]
	if lonStr == "" {
		lonStr = row["lon"]
	}
	if lonStr == "" {
		lonStr = row["x"]
	}

	latStr := row["latitude"]
	if latStr == "" {
		latStr = row["lat"]
	}
	if latStr == "" {
		latStr = row["y"]
	}

	altStr := row["altitude"]
	if altStr == "" {
		altStr = row["alt"]
	}
	if altStr == "" {
		altStr = row["z"]
	}

	// Parse values
	fmt.Sscanf(lonStr, "%f", &lon)
	fmt.Sscanf(latStr, "%f", &lat)
	fmt.Sscanf(altStr, "%f", &alt)

	return lon, lat, alt
}