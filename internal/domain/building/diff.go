package building

import (
	"fmt"
	"time"
)

// DiffResult represents the complete diff between two versions
type DiffResult struct {
	FromVersion   string           `json:"from_version"`
	ToVersion     string           `json:"to_version"`
	FromSnapshot  string           `json:"from_snapshot"`
	ToSnapshot    string           `json:"to_snapshot"`
	Summary       DiffSummary      `json:"summary"`
	BuildingDiff  *BuildingDiff    `json:"building_diff,omitempty"`
	EquipmentDiff *EquipmentDiff   `json:"equipment_diff,omitempty"`
	SpatialDiff   *SpatialDiff     `json:"spatial_diff,omitempty"`
	FilesDiff     *FilesDiff       `json:"files_diff,omitempty"`
	Changes       []DetailedChange `json:"changes"`
	CreatedAt     time.Time        `json:"created_at"`
}

// DiffSummary provides a high-level overview of changes
type DiffSummary struct {
	TotalChanges      int   `json:"total_changes"`
	BuildingsModified int   `json:"buildings_modified"`
	FloorsAdded       int   `json:"floors_added"`
	FloorsRemoved     int   `json:"floors_removed"`
	FloorsModified    int   `json:"floors_modified"`
	RoomsAdded        int   `json:"rooms_added"`
	RoomsRemoved      int   `json:"rooms_removed"`
	RoomsModified     int   `json:"rooms_modified"`
	EquipmentAdded    int   `json:"equipment_added"`
	EquipmentRemoved  int   `json:"equipment_removed"`
	EquipmentModified int   `json:"equipment_modified"`
	EquipmentMoved    int   `json:"equipment_moved"`
	FilesAdded        int   `json:"files_added"`
	FilesRemoved      int   `json:"files_removed"`
	FilesModified     int   `json:"files_modified"`
	SizeChanged       int64 `json:"size_changed"` // Net size change in bytes
}

// BuildingDiff represents changes to building structure
type BuildingDiff struct {
	MetadataChanges []FieldChange `json:"metadata_changes"`
	FloorsAdded     []FloorChange `json:"floors_added"`
	FloorsRemoved   []FloorChange `json:"floors_removed"`
	FloorsModified  []FloorDiff   `json:"floors_modified"`
	RoomsAdded      []RoomChange  `json:"rooms_added"`
	RoomsRemoved    []RoomChange  `json:"rooms_removed"`
	RoomsModified   []RoomDiff    `json:"rooms_modified"`
}

// EquipmentDiff represents changes to equipment inventory
type EquipmentDiff struct {
	Added        []EquipmentChange  `json:"added"`
	Removed      []EquipmentChange  `json:"removed"`
	Modified     []EquipmentChange  `json:"modified"`
	Moved        []EquipmentMove    `json:"moved"`
	Reclassified []EquipmentReclass `json:"reclassified"`
}

// SpatialDiff represents changes to spatial data
type SpatialDiff struct {
	GeometryChanges []GeometryChange `json:"geometry_changes"`
	PositionChanges []PositionChange `json:"position_changes"`
	BoundsChanged   bool             `json:"bounds_changed"`
	BoundsDiff      *BoundsDiff      `json:"bounds_diff,omitempty"`
}

// FilesDiff represents changes to files
type FilesDiff struct {
	Added    []FileChange `json:"added"`
	Removed  []FileChange `json:"removed"`
	Modified []FileChange `json:"modified"`
	Renamed  []FileRename `json:"renamed"`
	Moved    []FileMove   `json:"moved"`
}

// FieldChange represents a change to a single field
type FieldChange struct {
	Field    string      `json:"field"`
	OldValue interface{} `json:"old_value"`
	NewValue interface{} `json:"new_value"`
	Path     string      `json:"path"` // JSON path to field (e.g., "building.name")
}

// FloorChange represents an added or removed floor
type FloorChange struct {
	ID    string `json:"id"`
	Name  string `json:"name"`
	Level int    `json:"level"`
}

// FloorDiff represents changes to a floor
type FloorDiff struct {
	ID      string        `json:"id"`
	Name    string        `json:"name"`
	Changes []FieldChange `json:"changes"`
}

// RoomChange represents an added or removed room
type RoomChange struct {
	ID      string  `json:"id"`
	Name    string  `json:"name"`
	FloorID string  `json:"floor_id"`
	Area    float64 `json:"area,omitempty"`
}

// RoomDiff represents changes to a room
type RoomDiff struct {
	ID      string        `json:"id"`
	Name    string        `json:"name"`
	Changes []FieldChange `json:"changes"`
}

// EquipmentChange represents equipment that was added, removed, or modified
type EquipmentChange struct {
	ID           string        `json:"id"`
	Name         string        `json:"name"`
	Type         string        `json:"type"`
	Location     string        `json:"location,omitempty"`
	Changes      []FieldChange `json:"changes,omitempty"`      // For modified equipment
	Significance string        `json:"significance,omitempty"` // "minor", "major", "critical"
}

// EquipmentMove represents equipment that changed location
type EquipmentMove struct {
	ID         string   `json:"id"`
	Name       string   `json:"name"`
	Type       string   `json:"type"`
	FromFloor  string   `json:"from_floor"`
	ToFloor    string   `json:"to_floor"`
	FromRoom   string   `json:"from_room,omitempty"`
	ToRoom     string   `json:"to_room,omitempty"`
	FromCoords *Point3D `json:"from_coords,omitempty"`
	ToCoords   *Point3D `json:"to_coords,omitempty"`
	Distance   float64  `json:"distance"` // 3D distance in meters
}

// EquipmentReclass represents equipment that changed type
type EquipmentReclass struct {
	ID      string `json:"id"`
	Name    string `json:"name"`
	OldType string `json:"old_type"`
	NewType string `json:"new_type"`
}

// GeometryChange represents a change to spatial geometry
type GeometryChange struct {
	EntityType string  `json:"entity_type"` // "floor", "room", "equipment"
	EntityID   string  `json:"entity_id"`
	EntityName string  `json:"entity_name"`
	ChangeType string  `json:"change_type"`          // "shape", "size", "orientation"
	AreaDiff   float64 `json:"area_diff,omitempty"`  // Area change in sq meters
	PerimDiff  float64 `json:"perim_diff,omitempty"` // Perimeter change in meters
	Overlap    float64 `json:"overlap,omitempty"`    // Percentage overlap (0-100)
}

// PositionChange represents a change in position
type PositionChange struct {
	EntityType string   `json:"entity_type"` // "equipment", "room"
	EntityID   string   `json:"entity_id"`
	EntityName string   `json:"entity_name"`
	OldCoords  *Point3D `json:"old_coords"`
	NewCoords  *Point3D `json:"new_coords"`
	Distance   float64  `json:"distance"` // Distance moved in meters
}

// BoundsDiff represents changes to building bounds
type BoundsDiff struct {
	OldMinX float64 `json:"old_min_x"`
	OldMinY float64 `json:"old_min_y"`
	OldMaxX float64 `json:"old_max_x"`
	OldMaxY float64 `json:"old_max_y"`
	NewMinX float64 `json:"new_min_x"`
	NewMinY float64 `json:"new_min_y"`
	NewMaxX float64 `json:"new_max_x"`
	NewMaxY float64 `json:"new_max_y"`
}

// FileChange represents a file that was added, removed, or modified
type FileChange struct {
	Path     string `json:"path"`
	Name     string `json:"name"`
	Type     string `json:"type"` // "ifc", "pdf", "dwg", etc.
	OldHash  string `json:"old_hash,omitempty"`
	NewHash  string `json:"new_hash,omitempty"`
	OldSize  int64  `json:"old_size,omitempty"`
	NewSize  int64  `json:"new_size,omitempty"`
	SizeDiff int64  `json:"size_diff,omitempty"`
}

// FileRename represents a renamed file
type FileRename struct {
	OldPath string `json:"old_path"`
	NewPath string `json:"new_path"`
	Hash    string `json:"hash"` // Same hash = renamed, not modified
}

// FileMove represents a moved file
type FileMove struct {
	OldPath string `json:"old_path"`
	NewPath string `json:"new_path"`
	Hash    string `json:"hash"`
}

// DetailedChange represents a single granular change
type DetailedChange struct {
	Type        ChangeType  `json:"type"`
	Category    string      `json:"category"`    // "building", "equipment", "spatial", "file"
	EntityType  string      `json:"entity_type"` // "floor", "room", "equipment", etc.
	EntityID    string      `json:"entity_id,omitempty"`
	EntityName  string      `json:"entity_name,omitempty"`
	Path        string      `json:"path"`
	Description string      `json:"description"` // Human-readable description
	OldValue    interface{} `json:"old_value,omitempty"`
	NewValue    interface{} `json:"new_value,omitempty"`
	Severity    string      `json:"severity"` // "info", "minor", "major", "critical"
}

// Point3D represents a 3D point
type Point3D struct {
	X float64 `json:"x"`
	Y float64 `json:"y"`
	Z float64 `json:"z"`
}

// Distance calculates the 3D distance between two points
func (p Point3D) Distance(other Point3D) float64 {
	dx := p.X - other.X
	dy := p.Y - other.Y
	dz := p.Z - other.Z
	return float64(dx*dx + dy*dy + dz*dz)
}

// DiffOutputFormat represents the output format for diffs
type DiffOutputFormat string

const (
	DiffFormatUnified  DiffOutputFormat = "unified"  // Git-style unified diff
	DiffFormatJSON     DiffOutputFormat = "json"     // JSON format
	DiffFormatSemantic DiffOutputFormat = "semantic" // Human-readable semantic diff
	DiffFormatSummary  DiffOutputFormat = "summary"  // High-level summary only
)

// FormatDiff formats a diff result according to the specified format
func FormatDiff(diff *DiffResult, format DiffOutputFormat) (string, error) {
	switch format {
	case DiffFormatUnified:
		return FormatUnifiedDiff(diff), nil
	case DiffFormatJSON:
		return FormatJSONDiff(diff)
	case DiffFormatSemantic:
		return FormatSemanticDiff(diff), nil
	case DiffFormatSummary:
		return FormatSummaryDiff(diff), nil
	default:
		return "", fmt.Errorf("unsupported diff format: %s", format)
	}
}

// FormatUnifiedDiff formats a diff in Git-style unified format
func FormatUnifiedDiff(diff *DiffResult) string {
	var output string

	output += fmt.Sprintf("diff --arx %s..%s\n", diff.FromVersion, diff.ToVersion)
	output += fmt.Sprintf("--- a/%s\n", diff.FromSnapshot)
	output += fmt.Sprintf("+++ b/%s\n", diff.ToSnapshot)
	output += fmt.Sprintf("@@ Summary: %d changes @@\n\n", diff.Summary.TotalChanges)

	// Building changes
	if diff.BuildingDiff != nil {
		for _, change := range diff.BuildingDiff.MetadataChanges {
			output += fmt.Sprintf("-%s: %v\n", change.Field, change.OldValue)
			output += fmt.Sprintf("+%s: %v\n", change.Field, change.NewValue)
		}
	}

	// Equipment changes
	if diff.EquipmentDiff != nil {
		for _, eq := range diff.EquipmentDiff.Added {
			output += fmt.Sprintf("+ Added equipment: %s (%s)\n", eq.Name, eq.Type)
		}
		for _, eq := range diff.EquipmentDiff.Removed {
			output += fmt.Sprintf("- Removed equipment: %s (%s)\n", eq.Name, eq.Type)
		}
		for _, eq := range diff.EquipmentDiff.Modified {
			output += fmt.Sprintf("~ Modified equipment: %s (%s)\n", eq.Name, eq.Type)
			for _, change := range eq.Changes {
				output += fmt.Sprintf("  %s: %v → %v\n", change.Field, change.OldValue, change.NewValue)
			}
		}
		for _, move := range diff.EquipmentDiff.Moved {
			output += fmt.Sprintf("→ Moved equipment: %s from %s to %s (%.1fm)\n",
				move.Name, move.FromFloor, move.ToFloor, move.Distance)
		}
	}

	return output
}

// FormatJSONDiff formats a diff as JSON
func FormatJSONDiff(diff *DiffResult) (string, error) {
	data, err := SerializeObject(diff)
	if err != nil {
		return "", fmt.Errorf("failed to serialize diff: %w", err)
	}
	return string(data), nil
}

// FormatSemanticDiff formats a diff in human-readable semantic format
func FormatSemanticDiff(diff *DiffResult) string {
	var output string

	output += fmt.Sprintf("Building Changes: %s → %s\n", diff.FromVersion, diff.ToVersion)
	output += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"

	// Summary
	if diff.Summary.TotalChanges == 0 {
		return output + "No changes detected.\n"
	}

	output += fmt.Sprintf("Summary: %d total changes\n\n", diff.Summary.TotalChanges)

	// Equipment changes
	if diff.EquipmentDiff != nil {
		if len(diff.EquipmentDiff.Added) > 0 {
			output += "Equipment Added:\n"
			for _, eq := range diff.EquipmentDiff.Added {
				output += fmt.Sprintf("  + %s (%s) at %s\n", eq.Name, eq.Type, eq.Location)
			}
			output += "\n"
		}

		if len(diff.EquipmentDiff.Removed) > 0 {
			output += "Equipment Removed:\n"
			for _, eq := range diff.EquipmentDiff.Removed {
				output += fmt.Sprintf("  - %s (%s)\n", eq.Name, eq.Type)
			}
			output += "\n"
		}

		if len(diff.EquipmentDiff.Modified) > 0 {
			output += "Equipment Modified:\n"
			for _, eq := range diff.EquipmentDiff.Modified {
				output += fmt.Sprintf("  ↻ %s (%s)\n", eq.Name, eq.Type)
				for _, change := range eq.Changes {
					output += fmt.Sprintf("    • %s: %v → %v\n", change.Field, change.OldValue, change.NewValue)
				}
			}
			output += "\n"
		}

		if len(diff.EquipmentDiff.Moved) > 0 {
			output += "Equipment Moved:\n"
			for _, move := range diff.EquipmentDiff.Moved {
				output += fmt.Sprintf("  → %s: %s → %s (%.1fm)\n",
					move.Name, move.FromFloor, move.ToFloor, move.Distance)
			}
			output += "\n"
		}
	}

	// Building structure changes
	if diff.BuildingDiff != nil {
		if len(diff.BuildingDiff.FloorsAdded) > 0 {
			output += "Floors Added:\n"
			for _, floor := range diff.BuildingDiff.FloorsAdded {
				output += fmt.Sprintf("  + %s (Level %d)\n", floor.Name, floor.Level)
			}
			output += "\n"
		}

		if len(diff.BuildingDiff.RoomsAdded) > 0 {
			output += "Rooms Added:\n"
			for _, room := range diff.BuildingDiff.RoomsAdded {
				output += fmt.Sprintf("  + %s (%.1f m²)\n", room.Name, room.Area)
			}
			output += "\n"
		}
	}

	// Files changes
	if diff.FilesDiff != nil {
		if len(diff.FilesDiff.Added) > 0 {
			output += "Files Added:\n"
			for _, file := range diff.FilesDiff.Added {
				output += fmt.Sprintf("  + %s (%s, %.1f MB)\n",
					file.Name, file.Type, float64(file.NewSize)/(1024*1024))
			}
			output += "\n"
		}
	}

	return output
}

// FormatSummaryDiff formats only the summary
func FormatSummaryDiff(diff *DiffResult) string {
	s := diff.Summary
	return fmt.Sprintf(`Version Comparison: %s → %s
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Total Changes: %d

Building Structure:
  • Floors: +%d -%d ~%d
  • Rooms: +%d -%d ~%d

Equipment:
  • Added: %d
  • Removed: %d
  • Modified: %d
  • Moved: %d

Files:
  • Added: %d
  • Removed: %d
  • Modified: %d

Net Size Change: %+.2f MB
`,
		diff.FromVersion, diff.ToVersion,
		s.TotalChanges,
		s.FloorsAdded, s.FloorsRemoved, s.FloorsModified,
		s.RoomsAdded, s.RoomsRemoved, s.RoomsModified,
		s.EquipmentAdded,
		s.EquipmentRemoved,
		s.EquipmentModified,
		s.EquipmentMoved,
		s.FilesAdded,
		s.FilesRemoved,
		s.FilesModified,
		float64(s.SizeChanged)/(1024*1024),
	)
}
