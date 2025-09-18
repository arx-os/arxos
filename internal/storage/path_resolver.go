package storage

import (
	"fmt"
	"regexp"
	"strings"
)

// PathResolver handles ArxOS path parsing and validation
type PathResolver struct {
	// Path patterns for validation
	buildingPattern  *regexp.Regexp
	floorPattern     *regexp.Regexp
	roomPattern      *regexp.Regexp
	componentPattern *regexp.Regexp
}

// NewPathResolver creates a new path resolver
func NewPathResolver() *PathResolver {
	return &PathResolver{
		buildingPattern:  regexp.MustCompile(`^[A-Z]{5}-[A-Z]{2}-[A-Z]{2}-[A-Z]{2}-[A-Z]{3}-\d{4}$`),
		floorPattern:     regexp.MustCompile(`^floor-\d{2}$`),
		roomPattern:      regexp.MustCompile(`^room-[A-Z0-9]+$`),
		componentPattern: regexp.MustCompile(`^[a-zA-Z0-9_-]+$`),
	}
}

// ArxOSPath represents a parsed ArxOS path
type ArxOSPath struct {
	Building  string
	Floor     string
	Room      string
	System    string
	Component string
	Raw       string
	Depth     int
}

// Parse parses an ArxOS path into its components
func (pr *PathResolver) Parse(path string) (*ArxOSPath, error) {
	// Remove leading slash and split
	path = strings.TrimPrefix(path, "/")
	if path == "" {
		return &ArxOSPath{Raw: "/", Depth: 0}, nil
	}

	parts := strings.Split(path, "/")
	result := &ArxOSPath{
		Raw:   "/" + path,
		Depth: len(parts),
	}

	// Parse each level
	for i, part := range parts {
		switch i {
		case 0:
			// Building ID (ARXOS format)
			if !pr.buildingPattern.MatchString(part) && !pr.componentPattern.MatchString(part) {
				return nil, fmt.Errorf("invalid building ID: %s", part)
			}
			result.Building = part

		case 1:
			// Could be floor, system, or room
			if strings.HasPrefix(part, "floor-") {
				result.Floor = part
			} else if isSystemType(part) {
				result.System = part
			} else if strings.HasPrefix(part, "room-") {
				result.Room = part
			} else {
				result.Component = part
			}

		case 2:
			// Could be room or component
			if result.Floor != "" && strings.HasPrefix(part, "room-") {
				result.Room = part
			} else if result.Floor != "" && isSystemType(part) {
				result.System = part
			} else {
				result.Component = part
			}

		case 3:
			// System or component
			if isSystemType(part) {
				result.System = part
			} else {
				result.Component = part
			}

		case 4:
			// Component
			result.Component = part

		default:
			// Additional path components
			result.Component = strings.Join(parts[i:], "/")
			break
		}
	}

	return result, nil
}

// Format creates an ArxOS path from components
func (pr *PathResolver) Format(components *ArxOSPath) string {
	var parts []string

	if components.Building != "" {
		parts = append(parts, components.Building)
	}
	if components.Floor != "" {
		parts = append(parts, components.Floor)
	}
	if components.Room != "" {
		parts = append(parts, components.Room)
	}
	if components.System != "" {
		parts = append(parts, components.System)
	}
	if components.Component != "" {
		parts = append(parts, components.Component)
	}

	if len(parts) == 0 {
		return "/"
	}

	return "/" + strings.Join(parts, "/")
}

// Validate checks if an ArxOS path is valid
func (pr *PathResolver) Validate(path string) error {
	_, err := pr.Parse(path)
	return err
}

// IsAbsolute checks if a path is absolute (starts with /)
func (pr *PathResolver) IsAbsolute(path string) bool {
	return strings.HasPrefix(path, "/")
}

// Join combines path segments
func (pr *PathResolver) Join(base string, segments ...string) string {
	// Start with base
	result := strings.TrimSuffix(base, "/")

	// Add each segment
	for _, segment := range segments {
		segment = strings.Trim(segment, "/")
		if segment != "" {
			result = result + "/" + segment
		}
	}

	return result
}

// Parent returns the parent path
func (pr *PathResolver) Parent(path string) string {
	path = strings.TrimSuffix(path, "/")
	lastSlash := strings.LastIndex(path, "/")
	if lastSlash <= 0 {
		return "/"
	}
	return path[:lastSlash]
}

// Base returns the last component of the path
func (pr *PathResolver) Base(path string) string {
	path = strings.TrimSuffix(path, "/")
	lastSlash := strings.LastIndex(path, "/")
	if lastSlash < 0 {
		return path
	}
	return path[lastSlash+1:]
}

// Normalize cleans up a path
func (pr *PathResolver) Normalize(path string) string {
	// Remove duplicate slashes
	path = regexp.MustCompile(`/+`).ReplaceAllString(path, "/")

	// Remove trailing slash unless it's root
	if path != "/" {
		path = strings.TrimSuffix(path, "/")
	}

	// Ensure leading slash
	if !strings.HasPrefix(path, "/") {
		path = "/" + path
	}

	return path
}

// Match checks if a path matches a pattern
func (pr *PathResolver) Match(pattern, path string) (bool, error) {
	// Normalize both
	pattern = pr.Normalize(pattern)
	path = pr.Normalize(path)

	// Convert ArxOS pattern to regex
	// * matches any single component
	// ** matches any number of components
	regexPattern := strings.ReplaceAll(pattern, "**", ".*")
	regexPattern = strings.ReplaceAll(regexPattern, "*", "[^/]+")
	regexPattern = "^" + regexPattern + "$"

	return regexp.MatchString(regexPattern, path)
}

// RelativePath returns the relative path from base to target
func (pr *PathResolver) RelativePath(base, target string) (string, error) {
	baseParsed, err := pr.Parse(base)
	if err != nil {
		return "", fmt.Errorf("invalid base path: %w", err)
	}

	targetParsed, err := pr.Parse(target)
	if err != nil {
		return "", fmt.Errorf("invalid target path: %w", err)
	}

	// Must be in same building
	if baseParsed.Building != targetParsed.Building {
		return "", fmt.Errorf("paths are in different buildings")
	}

	// Build relative path
	var result []string

	// Compare floors
	if baseParsed.Floor != targetParsed.Floor {
		if baseParsed.Floor != "" {
			result = append(result, "..")
		}
		if targetParsed.Floor != "" {
			result = append(result, targetParsed.Floor)
		}
	}

	// Compare rooms
	if baseParsed.Room != targetParsed.Room {
		if baseParsed.Room != "" && targetParsed.Floor == baseParsed.Floor {
			result = append(result, "..")
		}
		if targetParsed.Room != "" {
			result = append(result, targetParsed.Room)
		}
	}

	// Add system and component
	if targetParsed.System != "" && targetParsed.System != baseParsed.System {
		result = append(result, targetParsed.System)
	}
	if targetParsed.Component != "" {
		result = append(result, targetParsed.Component)
	}

	if len(result) == 0 {
		return ".", nil
	}

	return strings.Join(result, "/"), nil
}
