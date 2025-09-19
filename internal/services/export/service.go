package exportservice

import (
	"context"
	"encoding/csv"
	"encoding/json"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"strings"
	"time"

	"github.com/google/uuid"
	"github.com/arx-os/arxos/internal/adapters/postgis"
	"github.com/arx-os/arxos/internal/core/building"
	"github.com/arx-os/arxos/internal/core/equipment"
	"github.com/arx-os/arxos/internal/core/spatial"
)

// Service handles all export operations
type Service struct {
	buildingRepo  building.Repository
	equipmentRepo equipment.Repository
	spatialQueries *postgis.SpatialQueries
	db            *postgis.Client
}

// NewService creates a new export service
func NewService(db *postgis.Client, buildingRepo building.Repository, equipmentRepo equipment.Repository) *Service {
	return &Service{
		buildingRepo:  buildingRepo,
		equipmentRepo: equipmentRepo,
		spatialQueries: postgis.NewSpatialQueries(db),
		db:            db,
	}
}

// ExportOptions contains export configuration
type ExportOptions struct {
	BuildingID string
	Format     string // "csv", "json", "geojson", "bim", "ifc"
	OutputPath string
	Filter     equipment.Filter
}

// Export exports building data to the specified format
func (s *Service) Export(ctx context.Context, opts ExportOptions) error {
	// Validate format
	format := strings.ToLower(opts.Format)

	switch format {
	case "csv":
		return s.ExportCSV(ctx, opts)
	case "json":
		return s.ExportJSON(ctx, opts)
	case "geojson":
		return s.ExportGeoJSON(ctx, opts)
	case "bim":
		return s.ExportBIM(ctx, opts)
	case "ifc":
		return s.ExportIFC(ctx, opts)
	default:
		return fmt.Errorf("unsupported export format: %s", opts.Format)
	}
}

// ExportCSV exports equipment data to CSV
func (s *Service) ExportCSV(ctx context.Context, opts ExportOptions) error {
	// Get building
	bldg, err := s.buildingRepo.GetByArxosID(ctx, opts.BuildingID)
	if err != nil {
		return fmt.Errorf("failed to get building: %w", err)
	}

	// Get equipment
	filter := opts.Filter
	filter.BuildingID = bldg.ID
	equipmentList, err := s.equipmentRepo.List(ctx, filter)
	if err != nil {
		return fmt.Errorf("failed to list equipment: %w", err)
	}

	// Create output file
	file, err := os.Create(opts.OutputPath)
	if err != nil {
		return fmt.Errorf("failed to create file: %w", err)
	}
	defer file.Close()

	// Create CSV writer
	writer := csv.NewWriter(file)
	defer writer.Flush()

	// Write header
	header := []string{
		"ID", "Path", "Name", "Type", "Status",
		"Longitude", "Latitude", "Altitude",
		"Local_X", "Local_Y", "Local_Z",
		"Confidence", "Created", "Updated",
	}
	if err := writer.Write(header); err != nil {
		return fmt.Errorf("failed to write header: %w", err)
	}

	// Write equipment rows
	for _, eq := range equipmentList {
		row := []string{
			eq.ID.String(),
			eq.Path,
			eq.Name,
			eq.Type,
			eq.Status,
		}

		// Add position data
		if eq.Position != nil {
			row = append(row,
				fmt.Sprintf("%.6f", eq.Position.X),
				fmt.Sprintf("%.6f", eq.Position.Y),
				fmt.Sprintf("%.2f", eq.Position.Z),
			)
		} else {
			row = append(row, "", "", "")
		}

		// Add local position data
		if eq.PositionLocal != nil {
			row = append(row,
				fmt.Sprintf("%.0f", eq.PositionLocal.X),
				fmt.Sprintf("%.0f", eq.PositionLocal.Y),
				fmt.Sprintf("%.0f", eq.PositionLocal.Z),
			)
		} else {
			row = append(row, "", "", "")
		}

		// Add metadata
		row = append(row,
			fmt.Sprintf("%d", eq.Confidence),
			eq.CreatedAt.Format(time.RFC3339),
			eq.UpdatedAt.Format(time.RFC3339),
		)

		if err := writer.Write(row); err != nil {
			return fmt.Errorf("failed to write row: %w", err)
		}
	}

	return nil
}

// ExportJSON exports building and equipment data to JSON
func (s *Service) ExportJSON(ctx context.Context, opts ExportOptions) error {
	// Get building
	bldg, err := s.buildingRepo.GetByArxosID(ctx, opts.BuildingID)
	if err != nil {
		return fmt.Errorf("failed to get building: %w", err)
	}

	// Get equipment
	filter := opts.Filter
	filter.BuildingID = bldg.ID
	equipmentList, err := s.equipmentRepo.List(ctx, filter)
	if err != nil {
		return fmt.Errorf("failed to list equipment: %w", err)
	}

	// Create export data structure
	exportData := map[string]interface{}{
		"building": map[string]interface{}{
			"id":       bldg.ID,
			"arxos_id": bldg.ArxosID,
			"name":     bldg.Name,
			"address":  bldg.Address,
			"origin": map[string]float64{
				"latitude":  bldg.Origin.Latitude,
				"longitude": bldg.Origin.Longitude,
				"altitude":  bldg.Origin.Altitude,
			},
			"rotation":   bldg.Rotation,
			"created_at": bldg.CreatedAt,
			"updated_at": bldg.UpdatedAt,
		},
		"equipment": equipmentList,
		"metadata": map[string]interface{}{
			"exported_at": time.Now(),
			"format":      "json",
			"version":     "1.0",
			"count":       len(equipmentList),
		},
	}

	// Create output file
	file, err := os.Create(opts.OutputPath)
	if err != nil {
		return fmt.Errorf("failed to create file: %w", err)
	}
	defer file.Close()

	// Write JSON
	encoder := json.NewEncoder(file)
	encoder.SetIndent("", "  ")
	if err := encoder.Encode(exportData); err != nil {
		return fmt.Errorf("failed to encode JSON: %w", err)
	}

	return nil
}

// ExportGeoJSON exports equipment data as GeoJSON
func (s *Service) ExportGeoJSON(ctx context.Context, opts ExportOptions) error {
	// Get building
	bldg, err := s.buildingRepo.GetByArxosID(ctx, opts.BuildingID)
	if err != nil {
		return fmt.Errorf("failed to get building: %w", err)
	}

	// Get equipment with spatial data
	filter := opts.Filter
	filter.BuildingID = bldg.ID
	equipmentList, err := s.equipmentRepo.List(ctx, filter)
	if err != nil {
		return fmt.Errorf("failed to list equipment: %w", err)
	}

	// Create GeoJSON structure
	features := []map[string]interface{}{}

	for _, eq := range equipmentList {
		if eq.Position == nil {
			continue // Skip equipment without position
		}

		feature := map[string]interface{}{
			"type": "Feature",
			"geometry": map[string]interface{}{
				"type": "Point",
				"coordinates": []float64{
					eq.Position.X, // longitude
					eq.Position.Y, // latitude
					eq.Position.Z, // altitude
				},
			},
			"properties": map[string]interface{}{
				"id":         eq.ID.String(),
				"path":       eq.Path,
				"name":       eq.Name,
				"type":       eq.Type,
				"status":     eq.Status,
				"confidence": eq.Confidence,
				"building":   bldg.ArxosID,
			},
		}

		features = append(features, feature)
	}

	// Create FeatureCollection
	featureCollection := map[string]interface{}{
		"type": "FeatureCollection",
		"features": features,
		"properties": map[string]interface{}{
			"building_id":   bldg.ArxosID,
			"building_name": bldg.Name,
			"exported_at":   time.Now(),
		},
	}

	// Create output file
	file, err := os.Create(opts.OutputPath)
	if err != nil {
		return fmt.Errorf("failed to create file: %w", err)
	}
	defer file.Close()

	// Write GeoJSON
	encoder := json.NewEncoder(file)
	encoder.SetIndent("", "  ")
	if err := encoder.Encode(featureCollection); err != nil {
		return fmt.Errorf("failed to encode GeoJSON: %w", err)
	}

	return nil
}

// ExportBIM exports building data to .bim.txt format
func (s *Service) ExportBIM(ctx context.Context, opts ExportOptions) error {
	// Get building
	bldg, err := s.buildingRepo.GetByArxosID(ctx, opts.BuildingID)
	if err != nil {
		return fmt.Errorf("failed to get building: %w", err)
	}

	// Get all equipment
	filter := equipment.Filter{BuildingID: bldg.ID}
	equipmentList, err := s.equipmentRepo.List(ctx, filter)
	if err != nil {
		return fmt.Errorf("failed to list equipment: %w", err)
	}

	// Create output file
	file, err := os.Create(opts.OutputPath)
	if err != nil {
		return fmt.Errorf("failed to create file: %w", err)
	}
	defer file.Close()

	// Write BIM header
	fmt.Fprintf(file, "# ArxOS Building Information Model\n")
	fmt.Fprintf(file, "# Generated: %s\n\n", time.Now().Format(time.RFC3339))

	fmt.Fprintf(file, "BUILDING: %s %s\n", bldg.ArxosID, bldg.Name)
	if bldg.Address != "" {
		fmt.Fprintf(file, "ADDRESS: %s\n", bldg.Address)
	}
	fmt.Fprintf(file, "\n")

	// Group equipment by floor and room
	floors := s.organizeEquipmentByFloor(equipmentList)

	// Write floors
	for floorNum, rooms := range floors {
		fmt.Fprintf(file, "FLOOR: %d\n", floorNum)

		for roomNum, equipmentInRoom := range rooms {
			fmt.Fprintf(file, "  ROOM: %s\n", roomNum)

			for _, eq := range equipmentInRoom {
				// Extract equipment ID from path
				parts := strings.Split(eq.Path, "/")
				eqID := parts[len(parts)-1]

				fmt.Fprintf(file, "    EQUIPMENT: %s [%s] %s", eqID, eq.Type, eq.Name)

				if eq.Status != equipment.StatusUnknown && eq.Status != "" {
					fmt.Fprintf(file, " <%s>", strings.ToLower(eq.Status))
				}

				fmt.Fprintf(file, "\n")

				// Add metadata as comments
				if eq.PositionLocal != nil {
					fmt.Fprintf(file, "      # Grid: (%d, %d)\n",
						int(eq.PositionLocal.X/500), // Convert back to grid units
						int(eq.PositionLocal.Y/500))
				}
				if eq.Metadata != nil {
					for key, value := range eq.Metadata {
						fmt.Fprintf(file, "      # %s: %v\n", key, value)
					}
				}
			}
		}
		fmt.Fprintf(file, "\n")
	}

	return nil
}

// ExportIFC exports building data to IFC format
func (s *Service) ExportIFC(ctx context.Context, opts ExportOptions) error {
	// Get building
	bldg, err := s.buildingRepo.GetByArxosID(ctx, opts.BuildingID)
	if err != nil {
		return fmt.Errorf("failed to get building: %w", err)
	}

	// Get all equipment
	filter := equipment.Filter{BuildingID: bldg.ID}
	equipmentList, err := s.equipmentRepo.List(ctx, filter)
	if err != nil {
		return fmt.Errorf("failed to list equipment: %w", err)
	}

	// Create output file
	file, err := os.Create(opts.OutputPath)
	if err != nil {
		return fmt.Errorf("failed to create file: %w", err)
	}
	defer file.Close()

	// Write IFC header
	s.writeIFCHeader(file, bldg)

	// Write IFC data section
	fmt.Fprintln(file, "DATA;")

	// Write project hierarchy
	projectID := s.writeIFCProject(file, bldg)
	siteID := s.writeIFCSite(file, bldg, projectID)
	buildingID := s.writeIFCBuilding(file, bldg, siteID)

	// Write floors and equipment
	floors := s.organizeEquipmentByFloor(equipmentList)
	for floorNum, rooms := range floors {
		storyID := s.writeIFCBuildingStorey(file, floorNum, buildingID)

		for _, equipmentInRoom := range rooms {
			for _, eq := range equipmentInRoom {
				s.writeIFCEquipment(file, eq, storyID)
			}
		}
	}

	// Write IFC footer
	fmt.Fprintln(file, "ENDSEC;")
	fmt.Fprintln(file, "END-ISO-10303-21;")

	return nil
}

// Helper functions

func (s *Service) organizeEquipmentByFloor(equipmentList []*equipment.Equipment) map[int]map[string][]*equipment.Equipment {
	floors := make(map[int]map[string][]*equipment.Equipment)

	for _, eq := range equipmentList {
		// Parse floor and room from path (format: floor/room/equipment)
		parts := strings.Split(eq.Path, "/")
		if len(parts) < 2 {
			continue
		}

		var floor int
		fmt.Sscanf(parts[0], "%d", &floor)
		room := parts[1]

		if floors[floor] == nil {
			floors[floor] = make(map[string][]*equipment.Equipment)
		}

		floors[floor][room] = append(floors[floor][room], eq)
	}

	return floors
}

func (s *Service) writeIFCHeader(w io.Writer, bldg *building.Building) {
	fmt.Fprintln(w, "ISO-10303-21;")
	fmt.Fprintln(w, "HEADER;")
	fmt.Fprintf(w, "FILE_DESCRIPTION(('ArxOS Export'),'2;1');\n")
	fmt.Fprintf(w, "FILE_NAME('%s','%s',('ArxOS'),(''),'',' ',' ');\n",
		bldg.ArxosID, time.Now().Format("2006-01-02T15:04:05"))
	fmt.Fprintln(w, "FILE_SCHEMA(('IFC4'));")
	fmt.Fprintln(w, "ENDSEC;")
}

func (s *Service) writeIFCProject(w io.Writer, bldg *building.Building) int {
	id := 100
	fmt.Fprintf(w, "#%d=IFCPROJECT($,$,'%s','%s',$,$,$,$,$);\n",
		id, bldg.ArxosID, bldg.Name)
	return id
}

func (s *Service) writeIFCSite(w io.Writer, bldg *building.Building, projectID int) int {
	id := 200
	fmt.Fprintf(w, "#%d=IFCSITE($,$,'Site','%s',$,$,$,$,.ELEMENT.,(%f,%f,%f),$,$,$);\n",
		id, bldg.Address,
		bldg.Origin.Latitude,
		bldg.Origin.Longitude,
		bldg.Origin.Altitude)

	// Add relationship
	fmt.Fprintf(w, "#%d=IFCRELAGGREGATES($,$,$,$,#%d,(#%d));\n",
		id+1, projectID, id)

	return id
}

func (s *Service) writeIFCBuilding(w io.Writer, bldg *building.Building, siteID int) int {
	id := 300
	fmt.Fprintf(w, "#%d=IFCBUILDING($,$,'%s','%s',$,$,$,$,.ELEMENT.,$,$,$);\n",
		id, bldg.Name, bldg.ArxosID)

	// Add relationship
	fmt.Fprintf(w, "#%d=IFCRELAGGREGATES($,$,$,$,#%d,(#%d));\n",
		id+1, siteID, id)

	return id
}

func (s *Service) writeIFCBuildingStorey(w io.Writer, floor int, buildingID int) int {
	id := 400 + floor*100
	fmt.Fprintf(w, "#%d=IFCBUILDINGSTOREY($,$,'Floor %d','Level %d',$,$,$,$,.ELEMENT.,%f);\n",
		id, floor, floor, float64(floor)*3.0)

	// Add relationship
	fmt.Fprintf(w, "#%d=IFCRELAGGREGATES($,$,$,$,#%d,(#%d));\n",
		id+1, buildingID, id)

	return id
}

func (s *Service) writeIFCEquipment(w io.Writer, eq *equipment.Equipment, storyID int) {
	id := 1000 + int(eq.ID[0]) // Simple ID generation

	// Determine IFC type based on equipment type
	ifcType := "IFCBUILDINGELEMENTPROXY" // Default
	switch strings.ToLower(eq.Type) {
	case "hvac":
		ifcType = "IFCFLOWSEGMENT"
	case "electrical":
		ifcType = "IFCELECTRICALDISTRIBUTIONBOARD"
	case "plumbing":
		ifcType = "IFCPIPESEGMENT"
	}

	fmt.Fprintf(w, "#%d=%s($,$,'%s','%s',$,$,$,$);\n",
		id, ifcType, eq.Name, eq.Path)

	// Add relationship to storey
	fmt.Fprintf(w, "#%d=IFCRELCONTAINEDINSPATIALSTRUCTURE($,$,$,$,(#%d),#%d);\n",
		id+1, id, storyID)
}