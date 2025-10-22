package serialization

import (
	"fmt"
	"path/filepath"
	"strings"
)

// PathToGitFile converts a universal path to Git file path
// Example: /B1/3/301/HVAC/VAV-301 → equipment/B1/3/301/HVAC/VAV-301.yml
func PathToGitFile(universalPath string) string {
	// Remove leading slash if present
	path := strings.TrimPrefix(universalPath, "/")

	// Add equipment prefix and .yml extension
	return filepath.Join("equipment", path+".yml")
}

// GitFileToPath converts a Git file path to universal path
// Example: equipment/B1/3/301/HVAC/VAV-301.yml → /B1/3/301/HVAC/VAV-301
func GitFileToPath(gitFilePath string) string {
	// Remove equipment/ prefix
	path := strings.TrimPrefix(gitFilePath, "equipment/")

	// Remove .yml extension
	path = strings.TrimSuffix(path, ".yml")

	// Add leading slash
	return "/" + path
}

// ValidateUniversalPath validates that a path follows the universal naming convention
// Format: /BUILDING/FLOOR/ROOM/SYSTEM/EQUIPMENT
func ValidateUniversalPath(path string) error {
	if path == "" {
		return fmt.Errorf("path cannot be empty")
	}

	// Must start with /
	if !strings.HasPrefix(path, "/") {
		return fmt.Errorf("path must start with /")
	}

	// Remove leading slash and split
	parts := strings.Split(strings.TrimPrefix(path, "/"), "/")

	// Must have at least 2 parts (building/equipment minimum)
	if len(parts) < 2 {
		return fmt.Errorf("path must have at least 2 parts: /BUILDING/EQUIPMENT")
	}

	// Each part must not be empty
	for i, part := range parts {
		if part == "" {
			return fmt.Errorf("path part %d cannot be empty", i)
		}
	}

	return nil
}

// ExtractPathComponents extracts components from a universal path
func ExtractPathComponents(path string) (building, floor, room, system, equipment string) {
	parts := strings.Split(strings.TrimPrefix(path, "/"), "/")

	if len(parts) >= 1 {
		building = parts[0]
	}
	if len(parts) >= 2 {
		floor = parts[1]
	}
	if len(parts) >= 3 {
		room = parts[2]
	}
	if len(parts) >= 4 {
		system = parts[3]
	}
	if len(parts) >= 5 {
		equipment = parts[4]
	}

	return building, floor, room, system, equipment
}

// BuildPathFromComponents builds a universal path from components
func BuildPathFromComponents(building, floor, room, system, equipment string) string {
	var parts []string

	if building != "" {
		parts = append(parts, building)
	}
	if floor != "" {
		parts = append(parts, floor)
	}
	if room != "" {
		parts = append(parts, room)
	}
	if system != "" {
		parts = append(parts, system)
	}
	if equipment != "" {
		parts = append(parts, equipment)
	}

	if len(parts) == 0 {
		return ""
	}

	return "/" + strings.Join(parts, "/")
}

// GetPathPrefix returns the path prefix for a given level
// Example: /B1/3/301/HVAC/VAV-301 with level 2 returns /B1/3
func GetPathPrefix(path string, level int) string {
	parts := strings.Split(strings.TrimPrefix(path, "/"), "/")

	if level <= 0 || level > len(parts) {
		return ""
	}

	return "/" + strings.Join(parts[:level], "/")
}

// IsPathUnderPrefix checks if a path is under a given prefix
// Example: /B1/3/301/HVAC/VAV-301 is under /B1/3
func IsPathUnderPrefix(path, prefix string) bool {
	if prefix == "" {
		return true
	}

	// Ensure prefix ends with / for proper matching
	if !strings.HasSuffix(prefix, "/") {
		prefix = prefix + "/"
	}

	return strings.HasPrefix(path+"/", prefix)
}
