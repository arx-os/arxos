package usecase

import (
	"context"
	"crypto/sha256"
	"fmt"
	"io"
	"os"
	"time"

	"github.com/arx-os/arxos/internal/domain"
	"github.com/arx-os/arxos/internal/domain/types"
	"github.com/arx-os/arxos/internal/infrastructure/bas"
)

// BASImportUseCase handles importing BAS points from external systems
type BASImportUseCase struct {
	basPointRepo   domain.BASPointRepository
	basSystemRepo  domain.BASSystemRepository
	roomRepo       domain.RoomRepository
	equipmentRepo  domain.EquipmentRepository
	parser         *bas.CSVParser
	logger         domain.Logger
}

// NewBASImportUseCase creates a new BAS import use case
func NewBASImportUseCase(
	basPointRepo domain.BASPointRepository,
	basSystemRepo domain.BASSystemRepository,
	roomRepo domain.RoomRepository,
	equipmentRepo domain.EquipmentRepository,
	logger domain.Logger,
) *BASImportUseCase {
	return &BASImportUseCase{
		basPointRepo:  basPointRepo,
		basSystemRepo: basSystemRepo,
		roomRepo:      roomRepo,
		equipmentRepo: equipmentRepo,
		parser:        bas.NewCSVParser(),
		logger:        logger,
	}
}

// ImportBASPoints imports BAS points from a CSV file
func (uc *BASImportUseCase) ImportBASPoints(
	ctx context.Context,
	req domain.ImportBASPointsRequest,
) (*domain.BASImportResult, error) {
	uc.logger.Info("Starting BAS import", "file", req.FilePath, "building", req.BuildingID)

	startTime := time.Now()
	result := &domain.BASImportResult{
		ImportID:  types.NewID(),
		Filename:  req.FilePath,
		StartedAt: startTime,
		Status:    "success",
	}

	// 1. Validate file
	if err := uc.parser.ValidateCSV(req.FilePath); err != nil {
		result.Status = "failed"
		result.ErrorMessage = fmt.Sprintf("File validation failed: %v", err)
		result.CompletedAt = time.Now()
		return result, fmt.Errorf("file validation failed: %w", err)
	}

	// 2. Calculate file hash (for duplicate detection)
	fileHash, fileSize, err := uc.calculateFileHash(req.FilePath)
	if err != nil {
		result.Status = "failed"
		result.ErrorMessage = fmt.Sprintf("Failed to hash file: %v", err)
		result.CompletedAt = time.Now()
		return result, fmt.Errorf("failed to hash file: %w", err)
	}
	result.FileHash = fileHash
	result.FileSize = fileSize

	// 3. Parse CSV file
	uc.logger.Info("Parsing CSV file", "size", fileSize)
	parsed, err := uc.parser.ParseCSV(req.FilePath)
	if err != nil {
		result.Status = "failed"
		result.ErrorMessage = fmt.Sprintf("CSV parsing failed: %v", err)
		result.CompletedAt = time.Now()
		return result, fmt.Errorf("CSV parsing failed: %w", err)
	}

	if len(parsed.ParseErrors) > 0 {
		uc.logger.Warn("Some rows failed to parse", "errors", len(parsed.ParseErrors))
		result.Errors = parsed.ParseErrors
		result.Status = "partial"
	}

	uc.logger.Info("Parsed CSV successfully", "points", len(parsed.Points), "errors", len(parsed.ParseErrors))

	// 4. Get existing points for comparison
	existingPoints, err := uc.basPointRepo.ListByBASSystem(req.BASSystemID)
	if err != nil {
		uc.logger.Warn("Failed to get existing points, assuming first import", "error", err)
		existingPoints = []*domain.BASPoint{}
	}

	// 5. Detect changes
	changes := uc.detectChanges(parsed.Points, existingPoints)
	uc.logger.Info("Change detection complete",
		"added", len(changes.Added),
		"modified", len(changes.Modified),
		"deleted", len(changes.Deleted))

	result.PointsAdded = len(changes.Added)
	result.PointsModified = len(changes.Modified)
	result.PointsDeleted = len(changes.Deleted)

	// 6. Convert parsed points to domain entities
	pointsToCreate := uc.parser.ToBASPoints(&bas.ParsedBASData{
		Points: changes.Added,
	}, req.BuildingID, req.BASSystemID)

	// 7. Import new points
	if len(pointsToCreate) > 0 {
		uc.logger.Info("Bulk creating points", "count", len(pointsToCreate))
		if err := uc.basPointRepo.BulkCreate(pointsToCreate); err != nil {
			result.Status = "failed"
			result.ErrorMessage = fmt.Sprintf("Failed to create points: %v", err)
			result.CompletedAt = time.Now()
			return result, fmt.Errorf("failed to create points: %w", err)
		}
	}

	// 8. Update modified points
	if len(changes.Modified) > 0 {
		uc.logger.Info("Updating modified points", "count", len(changes.Modified))
		// TODO: Implement point updates
	}

	// 9. Mark deleted points
	if len(changes.Deleted) > 0 {
		uc.logger.Info("Marking deleted points", "count", len(changes.Deleted))
		// TODO: Implement soft delete
	}

	// 10. Auto-map points if requested
	if req.AutoMap && len(pointsToCreate) > 0 {
		uc.logger.Info("Attempting auto-mapping", "points", len(pointsToCreate))
		mapped, unmapped := uc.autoMapPoints(ctx, pointsToCreate)
		result.PointsMapped = mapped
		result.PointsUnmapped = unmapped
		uc.logger.Info("Auto-mapping complete", "mapped", mapped, "unmapped", unmapped)
	} else {
		result.PointsUnmapped = len(pointsToCreate)
	}

	// 11. Create version commit if requested
	if req.AutoCommit && req.RepositoryID != nil {
		uc.logger.Info("Creating version commit", "repository", req.RepositoryID)
		// TODO: Integrate with version control system
		// For now, just log
		uc.logger.Info("Version commit would be created here")
	}

	// Complete
	result.CompletedAt = time.Now()
	result.DurationMS = int(result.CompletedAt.Sub(result.StartedAt).Milliseconds())

	uc.logger.Info("BAS import complete",
		"added", result.PointsAdded,
		"modified", result.PointsModified,
		"deleted", result.PointsDeleted,
		"mapped", result.PointsMapped,
		"duration_ms", result.DurationMS)

	return result, nil
}

// BASChangeSet represents changes between imports
type BASChangeSet struct {
	Added    []bas.ParsedBASPoint
	Modified []bas.ParsedBASPoint
	Deleted  []*domain.BASPoint
}

// detectChanges compares parsed points with existing points
func (uc *BASImportUseCase) detectChanges(
	parsed []bas.ParsedBASPoint,
	existing []*domain.BASPoint,
) *BASChangeSet {
	changes := &BASChangeSet{
		Added:    make([]bas.ParsedBASPoint, 0),
		Modified: make([]bas.ParsedBASPoint, 0),
		Deleted:  make([]*domain.BASPoint, 0),
	}

	// Create lookup map of existing points (device_id + point_name)
	existingMap := make(map[string]*domain.BASPoint)
	for _, point := range existing {
		key := uc.makePointKey(point.DeviceID, point.PointName)
		existingMap[key] = point
	}

	// Create lookup map of parsed points
	parsedMap := make(map[string]bas.ParsedBASPoint)
	for _, point := range parsed {
		key := uc.makePointKey(point.DeviceID, point.PointName)
		parsedMap[key] = point
	}

	// Find added and modified points
	for key, parsedPoint := range parsedMap {
		if existingPoint, exists := existingMap[key]; exists {
			// Point exists - check if modified
			if uc.isPointModified(parsedPoint, existingPoint) {
				changes.Modified = append(changes.Modified, parsedPoint)
			}
		} else {
			// Point doesn't exist - it's new
			changes.Added = append(changes.Added, parsedPoint)
		}
	}

	// Find deleted points
	for key, existingPoint := range existingMap {
		if _, exists := parsedMap[key]; !exists {
			// Point was in database but not in new import
			changes.Deleted = append(changes.Deleted, existingPoint)
		}
	}

	return changes
}

// makePointKey creates a unique key for a point
func (uc *BASImportUseCase) makePointKey(deviceID, pointName string) string {
	return fmt.Sprintf("%s:%s", deviceID, pointName)
}

// isPointModified checks if a point's metadata has changed
func (uc *BASImportUseCase) isPointModified(parsed bas.ParsedBASPoint, existing *domain.BASPoint) bool {
	// Check if description changed
	if parsed.Description != existing.Description {
		return true
	}

	// Check if units changed
	if parsed.Units != existing.Units {
		return true
	}

	// Check if object type changed
	if parsed.ObjectType != existing.ObjectType {
		return true
	}

	return false
}

// autoMapPoints attempts to automatically map points to rooms/equipment
func (uc *BASImportUseCase) autoMapPoints(
	ctx context.Context,
	points []*domain.BASPoint,
) (mapped, unmapped int) {
	for _, point := range points {
		if point.LocationText == "" {
			unmapped++
			continue
		}

		// Parse location text
		parsedLoc := uc.parser.ParseLocationText(point.LocationText)
		if parsedLoc == nil {
			unmapped++
			continue
		}

		// Try to find matching room
		roomID, confidence := uc.findMatchingRoom(ctx, point.BuildingID, parsedLoc)
		if roomID != nil {
			// Map to room
			if err := uc.basPointRepo.MapToRoom(point.ID, *roomID, confidence); err != nil {
				uc.logger.Warn("Failed to map point to room", "point", point.PointName, "error", err)
				unmapped++
			} else {
				mapped++
			}
		} else {
			unmapped++
		}
	}

	return mapped, unmapped
}

// findMatchingRoom attempts to find a room matching the parsed location
func (uc *BASImportUseCase) findMatchingRoom(
	ctx context.Context,
	buildingID types.ID,
	parsedLoc *bas.ParsedLocation,
) (*types.ID, int) {
	// TODO: Implement smart room matching
	// 1. Get all rooms in building
	// 2. Match by floor + room number/name
	// 3. Calculate confidence (1=fuzzy match, 2=good match, 3=exact match)
	
	// For now, return nil (unmapped)
	return nil, 0
}

// calculateFileHash computes SHA-256 hash of file
func (uc *BASImportUseCase) calculateFileHash(filePath string) (string, int64, error) {
	file, err := os.Open(filePath)
	if err != nil {
		return "", 0, err
	}
	defer file.Close()

	stat, err := file.Stat()
	if err != nil {
		return "", 0, err
	}

	hash := sha256.New()
	if _, err := io.Copy(hash, file); err != nil {
		return "", 0, err
	}

	return fmt.Sprintf("%x", hash.Sum(nil)), stat.Size(), nil
}

// GetBASPointsByRoom retrieves all BAS points for a room
func (uc *BASImportUseCase) GetBASPointsByRoom(ctx context.Context, roomID types.ID) ([]*domain.BASPoint, error) {
	return uc.basPointRepo.ListByRoom(roomID)
}

// GetBASPointsByEquipment retrieves all BAS points for equipment
func (uc *BASImportUseCase) GetBASPointsByEquipment(ctx context.Context, equipmentID types.ID) ([]*domain.BASPoint, error) {
	return uc.basPointRepo.ListByEquipment(equipmentID)
}

// GetUnmappedPoints retrieves all unmapped BAS points for a building
func (uc *BASImportUseCase) GetUnmappedPoints(ctx context.Context, buildingID types.ID) ([]*domain.BASPoint, error) {
	return uc.basPointRepo.ListUnmapped(buildingID)
}

// MapPointToRoom manually maps a BAS point to a room
func (uc *BASImportUseCase) MapPointToRoom(
	ctx context.Context,
	req domain.MapBASPointRequest,
) error {
	if req.RoomID == nil {
		return fmt.Errorf("room ID is required")
	}

	uc.logger.Info("Mapping BAS point to room",
		"point", req.PointID,
		"room", req.RoomID,
		"confidence", req.Confidence)

	return uc.basPointRepo.MapToRoom(req.PointID, *req.RoomID, req.Confidence)
}

// MapPointToEquipment manually maps a BAS point to equipment
func (uc *BASImportUseCase) MapPointToEquipment(
	ctx context.Context,
	req domain.MapBASPointRequest,
) error {
	if req.EquipmentID == nil {
		return fmt.Errorf("equipment ID is required")
	}

	uc.logger.Info("Mapping BAS point to equipment",
		"point", req.PointID,
		"equipment", req.EquipmentID,
		"confidence", req.Confidence)

	return uc.basPointRepo.MapToEquipment(req.PointID, *req.EquipmentID, req.Confidence)
}

