package repo

import (
	"context"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"time"

	"github.com/arx-os/arxos/internal/common/logger"
	"github.com/arx-os/arxos/internal/database"
	"github.com/arx-os/arxos/pkg/models"
)

// Repository represents a BIM repository
type Repository struct {
	Path        string
	Metadata    *Metadata
	ObjectStore *ObjectStore
	RefStore    *RefStore
	Config      *Config
	db          *database.SQLiteDB
}

// Metadata represents repository metadata
type Metadata struct {
	Version     string    `json:"version"`
	Name        string    `json:"name"`
	Description string    `json:"description"`
	Created     time.Time `json:"created"`
	Updated     time.Time `json:"updated"`
	Remote      string    `json:"remote,omitempty"`
}

// Config represents repository configuration
type Config struct {
	User  UserConfig  `json:"user"`
	Core  CoreConfig  `json:"core"`
	Hooks HooksConfig `json:"hooks,omitempty"`
}

// UserConfig represents user configuration
type UserConfig struct {
	Name  string `json:"name"`
	Email string `json:"email"`
}

// CoreConfig represents core configuration
type CoreConfig struct {
	AutoGC         bool `json:"auto_gc"`
	CompressionLvl int  `json:"compression_level"`
}

// HooksConfig represents hook configuration
type HooksConfig struct {
	PreCommit  string `json:"pre_commit,omitempty"`
	PostCommit string `json:"post_commit,omitempty"`
	PrePush    string `json:"pre_push,omitempty"`
	PostPull   string `json:"post_pull,omitempty"`
}

// OpenRepository opens an existing repository
func OpenRepository(path string) (*Repository, error) {
	// Check if .arxos directory exists
	arxosPath := filepath.Join(path, ".arxos")
	if _, err := os.Stat(arxosPath); err != nil {
		return nil, fmt.Errorf("not a BIM repository: %w", err)
	}

	// Load metadata
	metadataPath := filepath.Join(arxosPath, "repo.json")
	metadataJSON, err := os.ReadFile(metadataPath)
	if err != nil {
		return nil, fmt.Errorf("failed to read metadata: %w", err)
	}

	var metadata Metadata
	if err := json.Unmarshal(metadataJSON, &metadata); err != nil {
		return nil, fmt.Errorf("failed to parse metadata: %w", err)
	}

	// Load config
	config, err := loadConfig(arxosPath)
	if err != nil {
		logger.Warn("Failed to load config: %v", err)
		config = defaultConfig()
	}

	// Open database
	dbPath := filepath.Join(arxosPath, "local.db")
	dbConfig := database.NewConfig(dbPath)
	db := database.NewSQLiteDB(dbConfig)

	ctx := context.Background()
	if err := db.Connect(ctx, dbPath); err != nil {
		return nil, fmt.Errorf("failed to connect to database: %w", err)
	}

	repo := &Repository{
		Path:        path,
		Metadata:    &metadata,
		ObjectStore: NewObjectStore(path),
		RefStore:    NewRefStore(path),
		Config:      config,
		db:          db,
	}

	return repo, nil
}

// InitRepository initializes a new repository
func InitRepository(path, name, description string) (*Repository, error) {
	arxosPath := filepath.Join(path, ".arxos")

	// Check if already initialized
	if _, err := os.Stat(arxosPath); err == nil {
		return nil, fmt.Errorf("repository already initialized")
	}

	// Create directory structure
	dirs := []string{
		arxosPath,
		filepath.Join(arxosPath, "objects"),
		filepath.Join(arxosPath, "refs"),
		filepath.Join(arxosPath, "refs", "heads"),
		filepath.Join(arxosPath, "refs", "tags"),
		filepath.Join(arxosPath, "logs"),
		filepath.Join(arxosPath, "temp"),
		filepath.Join(arxosPath, "hooks"),
	}

	for _, dir := range dirs {
		if err := os.MkdirAll(dir, 0755); err != nil {
			return nil, fmt.Errorf("failed to create directory %s: %w", dir, err)
		}
	}

	// Create metadata
	metadata := &Metadata{
		Version:     "1.0.0",
		Name:        name,
		Description: description,
		Created:     time.Now(),
		Updated:     time.Now(),
	}

	// Save metadata
	if err := saveMetadata(arxosPath, metadata); err != nil {
		return nil, fmt.Errorf("failed to save metadata: %w", err)
	}

	// Create default config
	config := defaultConfig()
	if err := saveConfig(arxosPath, config); err != nil {
		return nil, fmt.Errorf("failed to save config: %w", err)
	}

	// Initialize object store
	objectStore := NewObjectStore(path)
	if err := objectStore.Initialize(); err != nil {
		return nil, fmt.Errorf("failed to initialize object store: %w", err)
	}

	// Initialize ref store
	refStore := NewRefStore(path)
	if err := refStore.Initialize(); err != nil {
		return nil, fmt.Errorf("failed to initialize ref store: %w", err)
	}

	// Initialize database
	dbPath := filepath.Join(arxosPath, "local.db")
	dbConfig := database.NewConfig(dbPath)
	db := database.NewSQLiteDB(dbConfig)

	ctx := context.Background()
	if err := db.Connect(ctx, dbPath); err != nil {
		return nil, fmt.Errorf("failed to initialize database: %w", err)
	}

	// Create initial commit
	repo := &Repository{
		Path:        path,
		Metadata:    metadata,
		ObjectStore: objectStore,
		RefStore:    refStore,
		Config:      config,
		db:          db,
	}

	if err := repo.CreateInitialCommit(); err != nil {
		return nil, fmt.Errorf("failed to create initial commit: %w", err)
	}

	logger.Info("Initialized BIM repository in %s", arxosPath)
	return repo, nil
}

// CreateInitialCommit creates the first commit in the repository
func (r *Repository) CreateInitialCommit() error {
	commit := &Commit{
		Parent:    "",
		Author:    r.Config.User.Name,
		Email:     r.Config.User.Email,
		Message:   "Initial commit",
		Timestamp: time.Now(),
		Tree:      "", // Empty tree for initial commit
	}

	// Create commit object
	commitJSON, err := json.Marshal(commit)
	if err != nil {
		return fmt.Errorf("failed to marshal commit: %w", err)
	}

	obj := &Object{
		Type:      ObjectTypeCommit,
		Size:      int64(len(commitJSON)),
		Timestamp: time.Now(),
		Content:   commitJSON,
	}

	commitID, err := r.ObjectStore.WriteObject(obj)
	if err != nil {
		return fmt.Errorf("failed to write commit object: %w", err)
	}

	// Update HEAD to point to main branch
	if err := r.RefStore.UpdateRef("HEAD", "ref: refs/heads/main"); err != nil {
		return fmt.Errorf("failed to update HEAD: %w", err)
	}

	// Update main branch to point to commit
	if err := r.RefStore.UpdateRef("refs/heads/main", commitID); err != nil {
		return fmt.Errorf("failed to update main branch: %w", err)
	}

	return nil
}

// Commit creates a new commit with changes
func (r *Repository) Commit(message string) error {
	// Get current changes
	changes, err := r.GetChanges()
	if err != nil {
		return fmt.Errorf("failed to get changes: %w", err)
	}

	if len(changes.Added) == 0 && len(changes.Modified) == 0 && len(changes.Deleted) == 0 {
		return fmt.Errorf("no changes to commit")
	}

	// Create tree from current state
	treeID, err := r.CreateTreeFromDatabase()
	if err != nil {
		return fmt.Errorf("failed to create tree: %w", err)
	}

	// Get parent commit
	parentID, err := r.RefStore.ResolveRef("HEAD")
	if err != nil {
		logger.Warn("No parent commit found")
		parentID = ""
	}

	// Create commit
	commit := &Commit{
		Parent:    parentID,
		Author:    r.Config.User.Name,
		Email:     r.Config.User.Email,
		Message:   message,
		Timestamp: time.Now(),
		Tree:      treeID,
		Changes:   changes,
	}

	commitJSON, err := json.Marshal(commit)
	if err != nil {
		return fmt.Errorf("failed to marshal commit: %w", err)
	}

	obj := &Object{
		Type:      ObjectTypeCommit,
		Size:      int64(len(commitJSON)),
		Timestamp: time.Now(),
		Content:   commitJSON,
	}

	commitID, err := r.ObjectStore.WriteObject(obj)
	if err != nil {
		return fmt.Errorf("failed to write commit: %w", err)
	}

	// Update current branch
	currentBranch, err := r.GetCurrentBranch()
	if err != nil {
		return fmt.Errorf("failed to get current branch: %w", err)
	}

	if err := r.RefStore.UpdateRef(fmt.Sprintf("refs/heads/%s", currentBranch), commitID); err != nil {
		return fmt.Errorf("failed to update branch: %w", err)
	}

	logger.Info("Created commit %s", commitID[:8])
	return nil
}

// GetChanges returns uncommitted changes
func (r *Repository) GetChanges() (*Changes, error) {
	// TODO: Implement change detection
	// Compare current database state with last commit
	changes := &Changes{
		Added:    []string{},
		Modified: []string{},
		Deleted:  []string{},
	}

	return changes, nil
}

// CreateTreeFromDatabase creates a tree object from current database state
func (r *Repository) CreateTreeFromDatabase() (string, error) {
	ctx := context.Background()

	// Get all data from database
	floorPlans, err := r.db.GetAllFloorPlans(ctx)
	if err != nil {
		return "", fmt.Errorf("failed to get floor plans: %w", err)
	}

	// Create snapshot
	snapshot := &Snapshot{
		Timestamp:  time.Now(),
		FloorPlans: floorPlans,
	}

	snapshotJSON, err := json.Marshal(snapshot)
	if err != nil {
		return "", fmt.Errorf("failed to marshal snapshot: %w", err)
	}

	// Create blob for snapshot
	blobID, err := r.ObjectStore.CreateBlob(snapshotJSON)
	if err != nil {
		return "", fmt.Errorf("failed to create blob: %w", err)
	}

	// Create tree with snapshot entry
	entries := []TreeEntry{
		{
			Name: "snapshot.json",
			Type: ObjectTypeBlob,
			ID:   blobID,
			Mode: "100644",
		},
	}

	treeID, err := r.ObjectStore.CreateTree(entries)
	if err != nil {
		return "", fmt.Errorf("failed to create tree: %w", err)
	}

	return treeID, nil
}

// GetCurrentBranch returns the current branch name
func (r *Repository) GetCurrentBranch() (string, error) {
	head, err := r.RefStore.ReadRef("HEAD")
	if err != nil {
		return "", fmt.Errorf("failed to read HEAD: %w", err)
	}

	// HEAD should be "ref: refs/heads/branchname"
	if len(head) > 16 && head[:5] == "ref: " {
		return filepath.Base(head[5:]), nil
	}

	return "main", nil
}

// GetRemote returns the configured remote
func (r *Repository) GetRemote(name string) *Remote {
	if r.Metadata.Remote == "" {
		return nil
	}

	return &Remote{
		Name: name,
		URL:  r.Metadata.Remote,
	}
}

// Close closes the repository
func (r *Repository) Close() error {
	if r.db != nil {
		return r.db.Close()
	}
	return nil
}

// Helper functions

func loadConfig(arxosPath string) (*Config, error) {
	configPath := filepath.Join(arxosPath, "config.json")
	data, err := os.ReadFile(configPath)
	if err != nil {
		return nil, err
	}

	var config Config
	if err := json.Unmarshal(data, &config); err != nil {
		return nil, err
	}

	return &config, nil
}

func saveConfig(arxosPath string, config *Config) error {
	configPath := filepath.Join(arxosPath, "config.json")
	data, err := json.MarshalIndent(config, "", "  ")
	if err != nil {
		return err
	}

	return os.WriteFile(configPath, data, 0644)
}

func saveMetadata(arxosPath string, metadata *Metadata) error {
	metadataPath := filepath.Join(arxosPath, "repo.json")
	data, err := json.MarshalIndent(metadata, "", "  ")
	if err != nil {
		return err
	}

	return os.WriteFile(metadataPath, data, 0644)
}

func defaultConfig() *Config {
	return &Config{
		User: UserConfig{
			Name:  os.Getenv("USER"),
			Email: fmt.Sprintf("%s@arxos.local", os.Getenv("USER")),
		},
		Core: CoreConfig{
			AutoGC:         false,
			CompressionLvl: 6,
		},
	}
}

// Types

type Commit struct {
	Parent    string    `json:"parent,omitempty"`
	Author    string    `json:"author"`
	Email     string    `json:"email"`
	Message   string    `json:"message"`
	Timestamp time.Time `json:"timestamp"`
	Tree      string    `json:"tree"`
	Changes   *Changes  `json:"changes,omitempty"`
}

type Changes struct {
	Added    []string `json:"added,omitempty"`
	Modified []string `json:"modified,omitempty"`
	Deleted  []string `json:"deleted,omitempty"`
}

type Snapshot struct {
	Timestamp  time.Time           `json:"timestamp"`
	FloorPlans []*models.FloorPlan `json:"floor_plans"`
}

type Remote struct {
	Name string
	URL  string
}