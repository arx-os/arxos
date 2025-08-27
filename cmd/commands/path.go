package commands

import (
	"fmt"
	"path"
	"strings"
)

// PathResolver handles virtual building filesystem path operations
type PathResolver struct {
	buildingRoot string
}

// NewPathResolver creates a new resolver for the given building workspace
func NewPathResolver(buildingRoot string) *PathResolver {
	return &PathResolver{buildingRoot: buildingRoot}
}

// ResolvePath converts a path (absolute, relative, or special) to a normalized virtual path
func (pr *PathResolver) ResolvePath(currentPath, targetPath string) (string, error) {
	if targetPath == "" {
		return currentPath, nil
	}

	// Handle special paths
	switch targetPath {
	case ".", "":
		return currentPath, nil
	case "..":
		return pr.resolveParent(currentPath), nil
	case "~":
		return "/", nil
	case "-":
		// TODO: implement previous directory from session
		return currentPath, fmt.Errorf("previous directory not yet implemented")
	}

	// Handle absolute paths
	if strings.HasPrefix(targetPath, "/") {
		return normalizeVirtualPath(targetPath), nil
	}

	// Handle relative paths
	segments := strings.Split(targetPath, "/")
	resolved := currentPath

	for _, segment := range segments {
		if segment == "" || segment == "." {
			continue
		}
		if segment == ".." {
			resolved = pr.resolveParent(resolved)
		} else {
			resolved = path.Join(resolved, segment)
		}
	}

	return normalizeVirtualPath(resolved), nil
}

// resolveParent moves up one level in the virtual path
func (pr *PathResolver) resolveParent(currentPath string) string {
	if currentPath == "/" {
		return "/"
	}
	dir := path.Dir(currentPath)
	if dir == "." {
		return "/"
	}
	return dir
}

// ValidatePath checks if a virtual path is valid for the building structure
func (pr *PathResolver) ValidatePath(virtualPath string) error {
	if virtualPath == "/" {
		return nil // Root is always valid
	}

	// Check for invalid characters
	if strings.ContainsAny(virtualPath, "<>:\"|?*") {
		return fmt.Errorf("invalid characters in path: %s", virtualPath)
	}

	// Check for double slashes (except at start)
	if strings.Contains(virtualPath[1:], "//") {
		return fmt.Errorf("invalid double slashes in path: %s", virtualPath)
	}

	// Check for trailing slash (except root)
	if len(virtualPath) > 1 && strings.HasSuffix(virtualPath, "/") {
		return fmt.Errorf("trailing slash not allowed: %s", virtualPath)
	}

	return nil
}

// SplitPath breaks a virtual path into segments
func (pr *PathResolver) SplitPath(virtualPath string) []string {
	if virtualPath == "/" {
		return []string{}
	}
	segments := strings.Split(strings.TrimPrefix(virtualPath, "/"), "/")
	// Filter out empty segments
	result := make([]string, 0, len(segments))
	for _, seg := range segments {
		if seg != "" {
			result = append(result, seg)
		}
	}
	return result
}

// JoinPath combines path segments into a virtual path
func (pr *PathResolver) JoinPath(segments ...string) string {
	if len(segments) == 0 {
		return "/"
	}

	// Filter out empty segments and join
	validSegments := make([]string, 0, len(segments))
	for _, seg := range segments {
		if seg != "" && seg != "/" {
			validSegments = append(validSegments, seg)
		}
	}

	if len(validSegments) == 0 {
		return "/"
	}

	return "/" + strings.Join(validSegments, "/")
}

// IsSubPath checks if childPath is a subdirectory of parentPath
func (pr *PathResolver) IsSubPath(parentPath, childPath string) bool {
	if parentPath == "/" {
		return true // Root is parent of all paths
	}
	if childPath == "/" {
		return false // Root has no parent
	}

	parentSegments := pr.SplitPath(parentPath)
	childSegments := pr.SplitPath(childPath)

	if len(childSegments) < len(parentSegments) {
		return false
	}

	for i, seg := range parentSegments {
		if i >= len(childSegments) || childSegments[i] != seg {
			return false
		}
	}

	return true
}
