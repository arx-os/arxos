// Package path provides unified Unix-style path handling for ArxOS
package path

import (
	"fmt"
	"path"
	"strings"
)

// ArxPath represents a normalized Unix-style path in the ArxOS system
type ArxPath string

// Normalize converts any path format to Unix-style ArxOS path
// Examples:
//   building_demo -> /building/demo
//   building:demo -> /building/demo
//   /buildings/demo -> /building/demo
//   electrical/panel-a -> /electrical/panel-a
func Normalize(input string) ArxPath {
	// Handle empty input
	if input == "" {
		return "/"
	}
	
	// Remove any leading/trailing whitespace
	input = strings.TrimSpace(input)
	
	// Handle different separators
	// Replace colons with slashes (building:demo -> building/demo)
	input = strings.ReplaceAll(input, ":", "/")
	
	// Replace underscores between path segments with slashes
	// but preserve underscores within names (panel_a stays panel_a)
	input = normalizeUnderscores(input)
	
	// Ensure path starts with /
	if !strings.HasPrefix(input, "/") {
		input = "/" + input
	}
	
	// Clean the path (remove duplicates, resolve . and ..)
	cleaned := path.Clean(input)
	
	// Normalize common variations
	cleaned = normalizeVariations(cleaned)
	
	return ArxPath(cleaned)
}

// String returns the string representation of the path
func (p ArxPath) String() string {
	return string(p)
}

// Parent returns the parent path
func (p ArxPath) Parent() ArxPath {
	parent := path.Dir(string(p))
	if parent == "." {
		return "/"
	}
	return ArxPath(parent)
}

// Base returns the last element of the path
func (p ArxPath) Base() string {
	return path.Base(string(p))
}

// Join joins path elements to create a new path
func (p ArxPath) Join(elements ...string) ArxPath {
	parts := []string{string(p)}
	parts = append(parts, elements...)
	joined := path.Join(parts...)
	return ArxPath(joined)
}

// Split splits the path into segments
func (p ArxPath) Split() []string {
	cleaned := strings.Trim(string(p), "/")
	if cleaned == "" {
		return []string{}
	}
	return strings.Split(cleaned, "/")
}

// IsRoot returns true if this is the root path
func (p ArxPath) IsRoot() bool {
	return string(p) == "/"
}

// IsAbsolute returns true if the path is absolute (starts with /)
func (p ArxPath) IsAbsolute() bool {
	return strings.HasPrefix(string(p), "/")
}

// Contains returns true if the path contains the substring
func (p ArxPath) Contains(substr string) bool {
	return strings.Contains(string(p), substr)
}

// HasPrefix returns true if the path starts with the prefix
func (p ArxPath) HasPrefix(prefix string) bool {
	return strings.HasPrefix(string(p), prefix)
}

// Depth returns the depth of the path (number of segments)
func (p ArxPath) Depth() int {
	if p.IsRoot() {
		return 0
	}
	return len(p.Split())
}

// Validate checks if the path is valid
func (p ArxPath) Validate() error {
	// Check for invalid characters
	invalid := []string{"..", "~", "$", "&", "|", ";", "`", "\\"}
	pathStr := string(p)
	
	for _, char := range invalid {
		if strings.Contains(pathStr, char) {
			return fmt.Errorf("invalid character in path: %s", char)
		}
	}
	
	// Check path length
	if len(pathStr) > 4096 {
		return fmt.Errorf("path too long: %d characters (max 4096)", len(pathStr))
	}
	
	// Check segment length
	segments := p.Split()
	for _, segment := range segments {
		if len(segment) > 255 {
			return fmt.Errorf("segment too long: %s (%d characters, max 255)", 
				segment, len(segment))
		}
	}
	
	return nil
}

// GetSystem returns the system type from the path
// Examples: /electrical/panel -> "electrical"
func (p ArxPath) GetSystem() string {
	segments := p.Split()
	if len(segments) > 0 {
		return segments[0]
	}
	return ""
}

// GetObjectType attempts to determine object type from path
// Examples: /electrical/panel/main -> "panel"
func (p ArxPath) GetObjectType() string {
	segments := p.Split()
	if len(segments) >= 2 {
		// Usually the second segment indicates type
		return segments[1]
	}
	return ""
}

// ToFileSystemPath converts to a filesystem-safe path
// Replaces problematic characters for filesystem storage
func (p ArxPath) ToFileSystemPath() string {
	// Replace colons with underscores for Windows compatibility
	result := strings.ReplaceAll(string(p), ":", "_")
	
	// Ensure valid for filesystem
	result = strings.ReplaceAll(result, "<", "_")
	result = strings.ReplaceAll(result, ">", "_")
	result = strings.ReplaceAll(result, "|", "_")
	result = strings.ReplaceAll(result, "?", "_")
	result = strings.ReplaceAll(result, "*", "_")
	
	return result
}

// Match checks if the path matches a pattern (supports wildcards)
func (p ArxPath) Match(pattern string) bool {
	matched, _ := path.Match(pattern, string(p))
	return matched
}

// Helper functions

// normalizeUnderscores handles underscore conversion intelligently
func normalizeUnderscores(input string) string {
	// Known patterns that should be converted
	patterns := map[string]string{
		"building_": "building/",
		"floor_":    "floor/",
		"room_":     "room/",
		"zone_":     "zone/",
	}
	
	result := input
	for pattern, replacement := range patterns {
		result = strings.ReplaceAll(result, pattern, replacement)
	}
	
	return result
}

// normalizeVariations handles common path variations
func normalizeVariations(input string) string {
	replacements := map[string]string{
		"/buildings/": "/building/",
		"/floors/":    "/floor/",
		"/rooms/":     "/room/",
		"/systems/":   "/system/",
		"/zones/":     "/zone/",
	}
	
	result := input
	for old, new := range replacements {
		result = strings.ReplaceAll(result, old, new)
	}
	
	return result
}

// Compare compares two paths for equality
func Compare(p1, p2 string) bool {
	return Normalize(p1) == Normalize(p2)
}

// MustParse parses a path and panics on error
func MustParse(input string) ArxPath {
	p := Normalize(input)
	if err := p.Validate(); err != nil {
		panic(fmt.Sprintf("invalid path %s: %v", input, err))
	}
	return p
}

// ParseMultiple parses multiple paths
func ParseMultiple(inputs ...string) []ArxPath {
	paths := make([]ArxPath, len(inputs))
	for i, input := range inputs {
		paths[i] = Normalize(input)
	}
	return paths
}

// CommonPrefix finds the common prefix of multiple paths
func CommonPrefix(paths ...ArxPath) ArxPath {
	if len(paths) == 0 {
		return "/"
	}
	
	if len(paths) == 1 {
		return paths[0]
	}
	
	// Split all paths
	segments := make([][]string, len(paths))
	minLen := int(^uint(0) >> 1) // Max int
	
	for i, p := range paths {
		segments[i] = p.Split()
		if len(segments[i]) < minLen {
			minLen = len(segments[i])
		}
	}
	
	// Find common prefix
	var common []string
	for i := 0; i < minLen; i++ {
		segment := segments[0][i]
		allMatch := true
		
		for j := 1; j < len(segments); j++ {
			if segments[j][i] != segment {
				allMatch = false
				break
			}
		}
		
		if allMatch {
			common = append(common, segment)
		} else {
			break
		}
	}
	
	if len(common) == 0 {
		return "/"
	}
	
	return ArxPath("/" + strings.Join(common, "/"))
}

// IsSubpathOf checks if this path is a subpath of another
func (p ArxPath) IsSubpathOf(parent ArxPath) bool {
	return strings.HasPrefix(string(p), string(parent))
}

// RelativeTo returns the relative path from base to p
func (p ArxPath) RelativeTo(base ArxPath) (string, error) {
	if !p.IsAbsolute() || !base.IsAbsolute() {
		return "", fmt.Errorf("both paths must be absolute")
	}
	
	rel, err := path.Rel(string(base), string(p))
	if err != nil {
		return "", err
	}
	
	return rel, nil
}