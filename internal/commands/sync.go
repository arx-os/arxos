package commands

import (
	"context"
	"encoding/json"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"

	"github.com/arx-os/arxos/internal/bim"
	"github.com/arx-os/arxos/internal/common/logger"
	"github.com/arx-os/arxos/internal/database"
	"github.com/arx-os/arxos/pkg/models"
)

// ExecuteSync handles bidirectional sync between database and BIM files
func ExecuteSync(opts SyncOptions) error {
	switch opts.Direction {
	case "db-to-bim":
		return syncDatabaseToBIM(opts)
	case "bim-to-db":
		return syncBIMToDatabase(opts)
	default:
		return fmt.Errorf("invalid sync direction: %s", opts.Direction)
	}
}

func syncDatabaseToBIM(opts SyncOptions) error {
	ctx := context.Background()

	// Connect to database
	db, err := database.NewPostGISConnection(ctx)
	if err != nil {
		return fmt.Errorf("failed to connect to database: %w", err)
	}
	defer db.Close()

	// Determine which buildings to sync
	var buildingIDs []string
	if opts.BuildingID != "" {
		buildingIDs = []string{opts.BuildingID}
	} else {
		// Sync all buildings
		buildings, err := db.GetAllFloorPlans(ctx)
		if err != nil {
			return fmt.Errorf("failed to load buildings: %w", err)
		}
		for _, b := range buildings {
			buildingIDs = append(buildingIDs, b.ID)
		}
	}

	// Export each building to BIM
	for _, id := range buildingIDs {
		logger.Info("Syncing building %s to BIM format", id)

		building, err := db.GetFloorPlan(ctx, id)
		if err != nil {
			logger.Error("Failed to load building %s: %v", id, err)
			continue
		}

		// Convert to BIM
		bimBuilding := convertToSimpleBIM(building)

		// Determine output path
		outputPath := filepath.Join(opts.GitRepo, id, "building.bim.txt")
		if opts.GitRepo == "" {
			outputPath = fmt.Sprintf("%s.bim.txt", id)
		}

		// Create directory if needed
		if dir := filepath.Dir(outputPath); dir != "." {
			if err := os.MkdirAll(dir, 0755); err != nil {
				return fmt.Errorf("failed to create directory: %w", err)
			}
		}

		// Write BIM file
		file, err := os.Create(outputPath)
		if err != nil {
			return fmt.Errorf("failed to create file: %w", err)
		}

		// Write as JSON for SimpleBuilding
		encoder := json.NewEncoder(file)
		encoder.SetIndent("", "  ")
		if err := encoder.Encode(bimBuilding); err != nil {
			file.Close()
			return fmt.Errorf("failed to write BIM: %w", err)
		}
		file.Close()

		logger.Info("Exported %s to %s", id, outputPath)
	}

	// Git operations if requested
	if opts.GitRepo != "" && opts.AutoCommit {
		return gitCommit(opts.GitRepo, "Sync from database")
	}

	return nil
}

func syncBIMToDatabase(opts SyncOptions) error {
	ctx := context.Background()

	// Connect to database
	db, err := database.NewPostGISConnection(ctx)
	if err != nil {
		return fmt.Errorf("failed to connect to database: %w", err)
	}
	defer db.Close()

	// Find BIM files
	var bimFiles []string
	if opts.GitRepo != "" {
		// Find all .bim.txt files in repo
		err := filepath.Walk(opts.GitRepo, func(path string, info os.FileInfo, err error) error {
			if err != nil {
				return err
			}
			if filepath.Ext(path) == ".txt" && filepath.Base(path) == "building.bim.txt" {
				bimFiles = append(bimFiles, path)
			}
			return nil
		})
		if err != nil {
			return fmt.Errorf("failed to scan directory: %w", err)
		}
	} else if opts.BuildingID != "" {
		// Single file
		bimFiles = []string{fmt.Sprintf("%s.bim.txt", opts.BuildingID)}
	} else {
		return fmt.Errorf("specify either --building-id or --git-repo")
	}

	// Import each BIM file
	parser := bim.NewParser()
	for _, path := range bimFiles {
		logger.Info("Importing BIM file: %s", path)

		file, err := os.Open(path)
		if err != nil {
			logger.Error("Failed to open %s: %v", path, err)
			continue
		}

		building, err := parser.Parse(file)
		file.Close()
		if err != nil {
			logger.Error("Failed to parse %s: %v", path, err)
			continue
		}

		// Convert to database model
		// TODO: Properly convert complex BIM to FloorPlan
		dbModel := &models.FloorPlan{
			ID:   filepath.Base(filepath.Dir(path)),
			Name: building.Name,
		}

		// Save to database
		if err := db.SaveFloorPlan(ctx, dbModel); err != nil {
			// Try update if save fails
			if err := db.UpdateFloorPlan(ctx, dbModel); err != nil {
				logger.Error("Failed to save %s: %v", dbModel.ID, err)
				continue
			}
		}

		logger.Info("Imported %s to database", dbModel.ID)
	}

	return nil
}

func gitCommit(repoPath, message string) error {
	// Change to repo directory
	originalDir, err := os.Getwd()
	if err != nil {
		return err
	}
	defer os.Chdir(originalDir)

	if err := os.Chdir(repoPath); err != nil {
		return err
	}

	// Git add
	cmd := exec.Command("git", "add", "-A")
	if output, err := cmd.CombinedOutput(); err != nil {
		return fmt.Errorf("git add failed: %s", output)
	}

	// Git commit
	cmd = exec.Command("git", "commit", "-m", message)
	if output, err := cmd.CombinedOutput(); err != nil {
		// Check if there's nothing to commit
		if len(output) > 0 {
			logger.Debug("Git commit output: %s", output)
		}
		return nil // Ignore if nothing to commit
	}

	logger.Info("Committed changes to Git")
	return nil
}
