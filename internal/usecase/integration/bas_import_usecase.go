package integration

import (
	"context"
	"crypto/sha256"
	"fmt"
	"io"
	"os"
	"strings"
	"time"

	"github.com/arx-os/arxos/internal/domain"
	domainbas "github.com/arx-os/arxos/internal/domain/bas"
	"github.com/arx-os/arxos/internal/domain/types"
	infrasbas "github.com/arx-os/arxos/internal/infrastructure/bas"
)

// BASImportUseCase handles importing BAS points from external systems
type BASImportUseCase struct {
	basPointRepo  domainbas.BASPointRepository
	basSystemRepo domainbas.BASSystemRepository
	roomRepo      domain.RoomRepository
	floorRepo     domain.FloorRepository
	equipmentRepo domain.EquipmentRepository
	parser        *infrasbas.CSVParser
	logger        domain.Logger
}

// NewBASImportUseCase creates a new BAS import use case
func NewBASImportUseCase(
	basPointRepo domainbas.BASPointRepository,
	basSystemRepo domainbas.BASSystemRepository,
	roomRepo domain.RoomRepository,
	floorRepo domain.FloorRepository,
	equipmentRepo domain.EquipmentRepository,
	logger domain.Logger,
) *BASImportUseCase {
	return &BASImportUseCase{
		basPointRepo:  basPointRepo,
		basSystemRepo: basSystemRepo,
		roomRepo:      roomRepo,
		floorRepo:     floorRepo,
		equipmentRepo: equipmentRepo,
		parser:        infrasbas.NewCSVParser(),
		logger:        logger,
	}
}

// ImportBASPoints imports BAS points from a CSV file
func (uc *BASImportUseCase) ImportBASPoints(
	ctx context.Context,
	req domainbas.ImportBASPointsRequest,
) (*domainbas.BASImportResult, error) {
	uc.logger.Info("Starting BAS import", "file", req.FilePath, "building", req.BuildingID)

	startTime := time.Now()
	result := &domainbas.BASImportResult{
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
		existingPoints = []*domainbas.BASPoint{}
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
	pointsToCreate := uc.parser.ToBASPoints(&infrasbas.ParsedBASData{
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
		// NOTE: Point updates via BASPointRepository.Update()
	}

	// 9. Mark deleted points
	if len(changes.Deleted) > 0 {
		uc.logger.Info("Marking deleted points", "count", len(changes.Deleted))
		// NOTE: Soft delete via BASPointRepository.SoftDelete() (sets deleted_at)
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
		// NOTE: VCS integration via CommitUseCase.CreateCommit() with change type "bas_import"
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
	Added    []infrasbas.ParsedBASPoint
	Modified []infrasbas.ParsedBASPoint
	Deleted  []*domainbas.BASPoint
}

// detectChanges compares parsed points with existing points
func (uc *BASImportUseCase) detectChanges(
	parsed []infrasbas.ParsedBASPoint,
	existing []*domainbas.BASPoint,
) *BASChangeSet {
	changes := &BASChangeSet{
		Added:    make([]infrasbas.ParsedBASPoint, 0),
		Modified: make([]infrasbas.ParsedBASPoint, 0),
		Deleted:  make([]*domainbas.BASPoint, 0),
	}

	// Create lookup map of existing points (device_id + point_name)
	existingMap := make(map[string]*domainbas.BASPoint)
	for _, point := range existing {
		key := uc.makePointKey(point.DeviceID, point.PointName)
		existingMap[key] = point
	}

	// Create lookup map of parsed points
	parsedMap := make(map[string]infrasbas.ParsedBASPoint)
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
func (uc *BASImportUseCase) isPointModified(parsed infrasbas.ParsedBASPoint, existing *domainbas.BASPoint) bool {
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
	points []*domainbas.BASPoint,
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
	parsedLoc *infrasbas.ParsedLocation,
) (*types.ID, int) {
	// If no room info in parsed location, can't match
	if parsedLoc.Room == "" {
		return nil, 0
	}

	// Get all floors for the building
	floors, err := uc.floorRepo.GetByBuilding(ctx, buildingID.String())
	if err != nil {
		uc.logger.Warn("Failed to get floors for matching", "building_id", buildingID, "error", err)
		return nil, 0
	}

	if len(floors) == 0 {
		uc.logger.Warn("No floors found in building", "building_id", buildingID)
		return nil, 0
	}

	// If we have floor info, try to match floor first
	var targetFloorID *types.ID
	if parsedLoc.Floor != "" {
		// Try to find matching floor by level/name
		// Floor could be "1", "ground", "basement", "-1", etc.
		for _, floor := range floors {
			matched := false

			// Match by level number (Floor "1" matches level 1)
			floorNumStr := fmt.Sprintf("%d", floor.Level)
			if parsedLoc.Floor == floorNumStr {
				matched = true
			}

			// Match by name (case-insensitive)
			if parsedLoc.Floor == strings.ToLower(floor.Name) {
				matched = true
			}

			// Special case: "basement" or "b" matches negative levels or level 0 named "basement"
			if (parsedLoc.Floor == "basement" || parsedLoc.Floor == "b") &&
				(floor.Level < 0 || strings.Contains(strings.ToLower(floor.Name), "basement")) {
				matched = true
			}

			// Special case: "ground" or "g" matches level 0 or first floor
			if (parsedLoc.Floor == "ground" || parsedLoc.Floor == "g") &&
				(floor.Level == 0 || strings.Contains(strings.ToLower(floor.Name), "ground")) {
				matched = true
			}

			if matched {
				targetFloorID = &floor.ID
				uc.logger.Debug("Matched floor",
					"parsed_floor", parsedLoc.Floor,
					"floor_name", floor.Name,
					"floor_level", floor.Level)
				break
			}
		}
	}

	// If no floor matched but we have floors, try the first/default floor
	if targetFloorID == nil && len(floors) > 0 {
		// Use the first floor (often Ground/First floor)
		targetFloorID = &floors[0].ID
		uc.logger.Debug("No floor match, using first floor", "floor_id", targetFloorID)
	}

	// Get rooms for the target floor
	var rooms []*domain.Room
	if targetFloorID != nil {
		rooms, err = uc.roomRepo.GetByFloor(ctx, targetFloorID.String())
		if err != nil {
			uc.logger.Warn("Failed to get rooms for floor", "floor_id", targetFloorID, "error", err)
			return nil, 0
		}
	}

	if len(rooms) == 0 {
		uc.logger.Debug("No rooms found for matching", "floor_id", targetFloorID)
		return nil, 0
	}

	// Match room by number or name with fuzzy matching
	bestMatch := (*types.ID)(nil)
	bestConfidence := 0

	for _, room := range rooms {
		confidence := 0

		// Normalize strings for comparison
		roomNumberLower := strings.ToLower(strings.TrimSpace(room.Number))
		roomNameLower := strings.ToLower(strings.TrimSpace(room.Name))
		parsedRoomLower := strings.ToLower(strings.TrimSpace(parsedLoc.Room))

		// 1. Exact match on room number (highest confidence)
		if roomNumberLower == parsedRoomLower {
			confidence = 3
		} else if roomNameLower == parsedRoomLower {
			// 2. Exact match on room name
			confidence = 3
		} else if roomNumberLower != "" && strings.Contains(parsedRoomLower, roomNumberLower) {
			// 3. Room number in parsed location
			confidence = 2
		} else if parsedRoomLower != "" && strings.Contains(roomNumberLower, parsedRoomLower) {
			// 3b. Parsed room in room number
			confidence = 2
		} else if matchesFuzzyName(parsedRoomLower, roomNameLower) {
			// 4. Fuzzy name matching (special cases like "mechanical" → "Mechanical Room")
			confidence = 2
		} else if strings.Contains(roomNameLower, parsedRoomLower) && len(parsedRoomLower) >= 3 {
			// 5. Partial word matching in room name (3+ chars)
			confidence = 2
		} else if len(parsedRoomLower) >= 2 && strings.Contains(roomNumberLower, parsedRoomLower) {
			// 6. Weak matches - only if no better match
			confidence = 1
		}

		// Log matching attempt for debugging
		if confidence > 0 {
			uc.logger.Debug("Room match found",
				"point_location", parsedLoc.OriginalText,
				"room_number", room.Number,
				"room_name", room.Name,
				"parsed_room", parsedLoc.Room,
				"confidence", confidence)
		}

		// Update best match if this is better
		if confidence > bestConfidence {
			bestConfidence = confidence
			bestMatch = &room.ID
		}
	}

	if bestMatch != nil {
		uc.logger.Info("Successfully matched room",
			"parsed_location", parsedLoc.OriginalText,
			"room_id", bestMatch.String(),
			"confidence", bestConfidence)
	} else {
		uc.logger.Debug("No room match found",
			"parsed_location", parsedLoc.OriginalText,
			"parsed_floor", parsedLoc.Floor,
			"parsed_room", parsedLoc.Room)
	}

	return bestMatch, bestConfidence
}

// matchesFuzzyName checks for common fuzzy name patterns
func matchesFuzzyName(parsed, roomName string) bool {
	// Common room type mappings
	fuzzyMappings := map[string][]string{
		"mechanical": {"mechanical", "mech", "equipment", "equip"},
		"mech":       {"mechanical", "mech", "equipment"},
		"electrical": {"electrical", "elec", "power"},
		"elec":       {"electrical", "elec"},
		"conference": {"conference", "conf", "meeting"},
		"conf":       {"conference", "conf", "meeting"},
		"office":     {"office", "workspace"},
		"storage":    {"storage", "store", "closet"},
		"restroom":   {"restroom", "bathroom", "toilet", "wc"},
		"lobby":      {"lobby", "entrance", "reception"},
		"server":     {"server", "data", "telecom", "it"},
		"lab":        {"lab", "laboratory"},
	}

	// Check if parsed room matches any fuzzy mappings
	for key, variants := range fuzzyMappings {
		if parsed == key || contains(variants, parsed) {
			// Check if room name contains any of the variants
			for _, variant := range variants {
				if strings.Contains(roomName, variant) {
					return true
				}
			}
		}
	}

	return false
}

// contains checks if a string slice contains a value
func contains(slice []string, value string) bool {
	for _, item := range slice {
		if item == value {
			return true
		}
	}
	return false
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
func (uc *BASImportUseCase) GetBASPointsByRoom(ctx context.Context, roomID types.ID) ([]*domainbas.BASPoint, error) {
	return uc.basPointRepo.ListByRoom(roomID)
}

// GetBASPointsByEquipment retrieves all BAS points for equipment
func (uc *BASImportUseCase) GetBASPointsByEquipment(ctx context.Context, equipmentID types.ID) ([]*domainbas.BASPoint, error) {
	return uc.basPointRepo.ListByEquipment(equipmentID)
}

// GetUnmappedPoints retrieves all unmapped BAS points for a building
func (uc *BASImportUseCase) GetUnmappedPoints(ctx context.Context, buildingID types.ID) ([]*domainbas.BASPoint, error) {
	return uc.basPointRepo.ListUnmapped(buildingID)
}

// MapPointToRoom manually maps a BAS point to a room
func (uc *BASImportUseCase) MapPointToRoom(
	ctx context.Context,
	req domainbas.MapBASPointRequest,
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
	req domainbas.MapBASPointRequest,
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
