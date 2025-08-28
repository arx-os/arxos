// Package navigation provides Unix-style filesystem navigation for building components
package navigation

import (
	"fmt"
	"strings"
	"sync"
)

// NavigationContext maintains the current navigation state
type NavigationContext struct {
	CurrentPath string
	History     []string
	mu          sync.RWMutex
}

var (
	globalContext *NavigationContext
	once          sync.Once
)

// GetContext returns the global navigation context
func GetContext() *NavigationContext {
	once.Do(func() {
		globalContext = &NavigationContext{
			CurrentPath: "/",
			History:     []string{"/"},
		}
	})
	return globalContext
}

// GetCurrentPath returns the current path
func (nc *NavigationContext) GetCurrentPath() string {
	nc.mu.RLock()
	defer nc.mu.RUnlock()
	return nc.CurrentPath
}

// SetCurrentPath updates the current path and adds to history
func (nc *NavigationContext) SetCurrentPath(newPath string) {
	nc.mu.Lock()
	defer nc.mu.Unlock()
	
	// Normalize path using simple path cleaning
	newPath = cleanPath(newPath)
	
	// Add to history if different from current
	if nc.CurrentPath != newPath {
		nc.History = append(nc.History, newPath)
		// Keep only last 100 items in history
		if len(nc.History) > 100 {
			nc.History = nc.History[len(nc.History)-100:]
		}
	}
	
	nc.CurrentPath = newPath
}

// NavigateTo changes to a new path (relative or absolute)
func (nc *NavigationContext) NavigateTo(targetPath string) error {
	nc.mu.Lock()
	defer nc.mu.Unlock()
	
	var newPath string
	
	// Handle special paths
	switch targetPath {
	case "~", "":
		newPath = "/"
	case "-":
		// Go to previous path
		if len(nc.History) >= 2 {
			newPath = nc.History[len(nc.History)-2]
		} else {
			newPath = nc.CurrentPath
		}
	default:
		if strings.HasPrefix(targetPath, "/") {
			// Absolute path
			newPath = targetPath
		} else {
			// Relative path - join with current path
			newPath = joinPath(nc.CurrentPath, targetPath)
		}
	}
	
	// Normalize path
	newPath = cleanPath(newPath)
	
	// Update current path and history
	if nc.CurrentPath != newPath {
		nc.History = append(nc.History, newPath)
		if len(nc.History) > 100 {
			nc.History = nc.History[len(nc.History)-100:]
		}
	}
	
	nc.CurrentPath = newPath
	return nil
}

// GetParentPath returns the parent path
func (nc *NavigationContext) GetParentPath() string {
	nc.mu.RLock()
	defer nc.mu.RUnlock()
	
	if nc.CurrentPath == "/" {
		return "/"
	}
	
	return parentPath(nc.CurrentPath)
}

// GetRelativePath returns a path relative to current location
func (nc *NavigationContext) GetRelativePath(targetPath string) string {
	nc.mu.RLock()
	defer nc.mu.RUnlock()
	
	if strings.HasPrefix(targetPath, "/") {
		// Already absolute
		return targetPath
	}
	
	return joinPath(nc.CurrentPath, targetPath)
}

// NormalizePath normalizes a building path
func NormalizePath(input string) string {
	return cleanPath(input)
}

// ParsePath breaks a path into components
func ParsePath(input string) []string {
	if input == "/" {
		return []string{}
	}
	cleaned := strings.Trim(cleanPath(input), "/")
	if cleaned == "" {
		return []string{}
	}
	return strings.Split(cleaned, "/")
}

// IsValidPath checks if a path follows Arxos conventions
func IsValidPath(p string) bool {
	// Check for basic invalid formats before cleaning
	if strings.Contains(p, "//") {
		return false
	}
	if len(p) > 1 && strings.HasSuffix(p, "/") {
		return false
	}
	if !strings.HasPrefix(p, "/") {
		return false
	}
	
	// Clean the path for system validation
	cleaned := cleanPath(p)
	
	// Root is always valid
	if cleaned == "/" {
		return true
	}
	
	// Check for valid building engineering system prefixes
	validSystems := []string{
		"/structural",  // walls, beams, columns, foundations
		"/electrical",  // panels, circuits, outlets, switches
		"/hvac",        // AHUs, VAVs, ducts, thermostats
		"/plumbing",    // pipes, fixtures, valves, pumps
		"/fire",        // sprinklers, alarms, detectors, pumps
		"/security",    // cameras, access, sensors
		"/network",     // switches, APs, cabling
		"/floors",      // floor-by-floor organization
		"/zones",       // spatial organization
		"/equipment",   // general equipment
	}
	
	// Check if path starts with a valid system
	for _, system := range validSystems {
		if strings.HasPrefix(cleaned, system) {
			return true
		}
	}
	
	return false
}

// GetSystemFromPath extracts the system name from a path
func GetSystemFromPath(input string) string {
	parts := ParsePath(input)
	if len(parts) > 0 {
		return parts[0]
	}
	return ""
}

// GetObjectTypeFromPath infers object type from path
func GetObjectTypeFromPath(p string) string {
	p = strings.ToLower(p)
	
	// Structural system components
	if strings.Contains(p, "wall") {
		return "wall"
	} else if strings.Contains(p, "beam") {
		return "beam"
	} else if strings.Contains(p, "column") {
		return "column"
	} else if strings.Contains(p, "foundation") {
		return "foundation"
	} else if strings.Contains(p, "slab") {
		return "slab"
	} else if strings.Contains(p, "door") {
		return "door"
	} else if strings.Contains(p, "window") {
		return "window"
	
	// Network system components (check before generic switch)  
	} else if strings.Contains(p, "/network/") && strings.Contains(p, "switch") {
		return "network_switch"
	
	// Electrical system components
	} else if strings.Contains(p, "panel") {
		return "panel"
	} else if strings.Contains(p, "outlet") {
		return "outlet"
	} else if strings.Contains(p, "switch") {
		return "switch"
	} else if strings.Contains(p, "circuit") {
		return "circuit"
	} else if strings.Contains(p, "breaker") {
		return "breaker"
	} else if strings.Contains(p, "conduit") {
		return "conduit"
	
	// HVAC system components
	} else if strings.Contains(p, "ahu") {
		return "ahu"
	} else if strings.Contains(p, "vav") {
		return "vav"
	} else if strings.Contains(p, "duct") {
		return "duct"
	} else if strings.Contains(p, "thermostat") {
		return "thermostat"
	} else if strings.Contains(p, "diffuser") {
		return "diffuser"
	} else if strings.Contains(p, "fan") {
		return "fan"
	
	// Plumbing system components
	} else if strings.Contains(p, "pipe") {
		return "pipe"
	} else if strings.Contains(p, "valve") {
		return "valve"
	} else if strings.Contains(p, "pump") {
		return "pump"
	} else if strings.Contains(p, "fixture") {
		return "fixture"
	} else if strings.Contains(p, "drain") {
		return "drain"
	} else if strings.Contains(p, "water") && strings.Contains(p, "heater") {
		return "water_heater"
	
	// Fire protection components
	} else if strings.Contains(p, "sprinkler") {
		return "sprinkler"
	} else if strings.Contains(p, "alarm") && !strings.Contains(p, "panel") {
		return "alarm"
	} else if strings.Contains(p, "detector") {
		return "detector"
	} else if strings.Contains(p, "extinguisher") {
		return "extinguisher"
	} else if strings.Contains(p, "fire") && strings.Contains(p, "pump") {
		return "fire_pump"
	
	// Security system components
	} else if strings.Contains(p, "camera") {
		return "camera"
	} else if strings.Contains(p, "access") {
		return "access_control"
	} else if strings.Contains(p, "keypad") {
		return "keypad"
	} else if strings.Contains(p, "reader") {
		return "card_reader"
	} else if strings.Contains(p, "ap") || strings.Contains(p, "access") && strings.Contains(p, "point") {
		return "access_point"
	} else if strings.Contains(p, "cable") {
		return "cable"
	} else if strings.Contains(p, "patch") {
		return "patch_panel"
	
	// Spatial components
	} else if strings.Contains(p, "room") {
		return "room"
	} else if strings.Contains(p, "floor") || strings.HasPrefix(p, "/floors/") {
		return "floor"
	} else if strings.Contains(p, "zone") {
		return "zone"
	
	// Generic sensor
	} else if strings.Contains(p, "sensor") {
		return "sensor"
	}
	
	// Default based on system
	system := GetSystemFromPath(p)
	switch system {
	case "structural":
		return "structural_component"
	case "electrical":
		return "electrical_component"
	case "hvac":
		return "hvac_component"
	case "plumbing":
		return "plumbing_component"
	case "fire":
		return "fire_component"
	case "security":
		return "security_component"
	case "network":
		return "network_component"
	case "floors":
		return "floor_component"
	case "zones":
		return "zone_component"
	default:
		return "component"
	}
}

// FormatPath formats a path for display
func FormatPath(p string) string {
	if p == "/" {
		return "/ (Building Root)"
	}
	
	system := GetSystemFromPath(p)
	if system != "" {
		return fmt.Sprintf("%s [%s]", p, system)
	}
	
	return p
}

// Helper functions for path manipulation

// cleanPath normalizes a path by removing double slashes, resolving .. and .
func cleanPath(p string) string {
	if p == "" {
		return "/"
	}
	
	// Ensure path starts with /
	if !strings.HasPrefix(p, "/") {
		p = "/" + p
	}
	
	// Split into components for processing
	parts := strings.Split(strings.Trim(p, "/"), "/")
	if len(parts) == 1 && parts[0] == "" {
		return "/"
	}
	
	// Process path components, handling .. and .
	result := []string{}
	for _, part := range parts {
		if part == "" || part == "." {
			continue // skip empty and current directory
		} else if part == ".." {
			if len(result) > 0 {
				result = result[:len(result)-1] // go up one level
			}
		} else {
			result = append(result, part)
		}
	}
	
	if len(result) == 0 {
		return "/"
	}
	
	return "/" + strings.Join(result, "/")
}

// joinPath joins two path components
func joinPath(parent, child string) string {
	if child == "" {
		return parent
	}
	if strings.HasPrefix(child, "/") {
		return cleanPath(child)
	}
	
	parent = strings.TrimSuffix(parent, "/")
	if parent == "" {
		parent = "/"
	}
	
	return cleanPath(parent + "/" + child)
}

// parentPath returns the parent directory of a path
func parentPath(p string) string {
	if p == "/" {
		return "/"
	}
	
	p = strings.TrimSuffix(p, "/")
	lastSlash := strings.LastIndex(p, "/")
	if lastSlash <= 0 {
		return "/"
	}
	
	return p[:lastSlash]
}