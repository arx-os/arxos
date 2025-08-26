package commands

import (
	"encoding/json"
	"errors"
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"time"
)

// SessionState represents navigation context for a building workspace
type SessionState struct {
	BuildingID       string    `json:"building_id"`
	CWD              string    `json:"cwd"` // virtual path from building root, e.g. "/systems/electrical"
	PreviousCWD      string    `json:"previous_cwd,omitempty"`
	Zoom             int       `json:"zoom,omitempty"`
	LastIndexRefresh time.Time `json:"last_index_refresh,omitempty"`
}

// findBuildingRoot walks up from startDir to find a directory containing ".arxos/config"
func findBuildingRoot(startDir string) (string, error) {
	dir := startDir
	for {
		cfg := filepath.Join(dir, ".arxos", "config")
		if stat, err := os.Stat(cfg); err == nil && stat.IsDir() {
			return dir, nil
		}
		parent := filepath.Dir(dir)
		if parent == dir {
			break
		}
		dir = parent
	}
	return "", errors.New("not inside an arxos building workspace (missing .arxos/config)")
}

func sessionFilePath(buildingRoot string) string {
	return filepath.Join(buildingRoot, ".arxos", "config", "session.json")
}

// loadSession reads session.json if present; otherwise returns a default session
func loadSession(buildingRoot string) (*SessionState, error) {
	path := sessionFilePath(buildingRoot)
	data, err := os.ReadFile(path)
	if err != nil {
		if os.IsNotExist(err) {
			// derive building id from directory name if possible
			bID := filepath.Base(buildingRoot)
			return &SessionState{BuildingID: bID, CWD: "/"}, nil
		}
		return nil, fmt.Errorf("read session: %w", err)
	}
	var s SessionState
	if err := json.Unmarshal(data, &s); err != nil {
		return nil, fmt.Errorf("parse session: %w", err)
	}
	if s.CWD == "" {
		s.CWD = "/"
	}
	return &s, nil
}

// saveSession writes session.json atomically
func saveSession(buildingRoot string, s *SessionState) error {
	path := sessionFilePath(buildingRoot)
	if err := os.MkdirAll(filepath.Dir(path), 0755); err != nil {
		return fmt.Errorf("ensure session dir: %w", err)
	}
	tmp := path + ".tmp"
	b, err := json.MarshalIndent(s, "", "  ")
	if err != nil {
		return fmt.Errorf("marshal session: %w", err)
	}
	if err := os.WriteFile(tmp, b, 0644); err != nil {
		return fmt.Errorf("write temp session: %w", err)
	}
	if err := os.Rename(tmp, path); err != nil {
		return fmt.Errorf("commit session: %w", err)
	}
	return nil
}

// normalizeVirtualPath ensures a clean leading-slash path without trailing slash (except root)
func normalizeVirtualPath(p string) string {
	if p == "" {
		return "/"
	}
	// convert backslashes on Windows to forward slashes for virtual paths
	p = strings.ReplaceAll(p, "\\", "/")
	if !strings.HasPrefix(p, "/") {
		p = "/" + p
	}
	if len(p) > 1 && strings.HasSuffix(p, "/") {
		p = strings.TrimRight(p, "/")
	}
	return p
}
