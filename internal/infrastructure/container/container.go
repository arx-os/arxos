package container

import (
	"database/sql"
	"fmt"

	"github.com/arx-os/arxos/internal/domain"
	"github.com/arx-os/arxos/internal/infrastructure/bas"
	"github.com/arx-os/arxos/internal/infrastructure/logger"
	"github.com/arx-os/arxos/internal/infrastructure/postgis"
	"github.com/arx-os/arxos/internal/usecase"
)

// Container holds all application dependencies
// This implements dependency injection for clean architecture
type Container struct {
	// Database
	DB *sql.DB

	// Infrastructure
	Logger domain.Logger

	// Repositories
	BASPointRepo       domain.BASPointRepository
	BASSystemRepo      domain.BASSystemRepository
	BranchRepo         domain.BranchRepository
	CommitRepo         domain.CommitRepository
	PullRequestRepo    domain.PullRequestRepository
	IssueRepo          domain.IssueRepository
	ContributorRepo    domain.ContributorRepository
	TeamRepo           domain.TeamRepository
	BuildingRepo       domain.BuildingRepository
	FloorRepo          domain.FloorRepository
	RoomRepo           domain.RoomRepository
	EquipmentRepo      domain.EquipmentRepository

	// Parsers
	BASCSVParser *bas.CSVParser

	// Use Cases
	BASImportUC    *usecase.BASImportUseCase
	BranchUC       *usecase.BranchUseCase
	CommitUC       *usecase.CommitUseCase
	PullRequestUC  *usecase.PullRequestUseCase
	IssueUC        *usecase.IssueUseCase
	ContributorUC  *usecase.ContributorUseCase
}

// Config holds configuration for the container
type Config struct {
	DatabaseURL string
	LogLevel    string
}

// New creates a new service container with all dependencies wired
func New(cfg Config) (*Container, error) {
	// Initialize database connection
	db, err := initDatabase(cfg.DatabaseURL)
	if err != nil {
		return nil, fmt.Errorf("failed to initialize database: %w", err)
	}

	// Initialize logger
	log := logger.New(cfg.LogLevel)

	// Initialize repositories
	basPointRepo := postgis.NewBASPointRepository(db)
	basSystemRepo := postgis.NewBASSystemRepository(db)
	branchRepo := postgis.NewBranchRepository(db)
	// commitRepo := postgis.NewCommitRepository(db) // TODO: Implement
	pullRequestRepo := postgis.NewPullRequestRepository(db)
	issueRepo := postgis.NewIssueRepository(db)
	// contributorRepo := postgis.NewContributorRepository(db) // TODO: Implement
	// teamRepo := postgis.NewTeamRepository(db) // TODO: Implement
	// buildingRepo := postgis.NewBuildingRepository(db) // TODO: Implement
	// floorRepo := postgis.NewFloorRepository(db) // TODO: Implement
	// roomRepo := postgis.NewRoomRepository(db) // TODO: Implement
	// equipmentRepo := postgis.NewEquipmentRepository(db) // TODO: Implement

	// Initialize parsers
	basCSVParser := bas.NewCSVParser()

	// Initialize use cases with dependencies
	// Note: Some use cases require repositories we haven't implemented yet
	// For now, we'll pass nil and they'll be wired in future iterations
	
	basImportUC := usecase.NewBASImportUseCase(
		basPointRepo,
		basSystemRepo,
		nil, // roomRepo - TODO: Implement RoomRepository
		nil, // equipmentRepo - TODO: Implement EquipmentRepository
		log,
	)

	branchUC := usecase.NewBranchUseCase(
		branchRepo,
		nil, // commitRepo - TODO: Wire when implemented
		log,
	)

	// commitUC := usecase.NewCommitUseCase(...) // TODO: Implement

	pullRequestUC := usecase.NewPullRequestUseCase(
		pullRequestRepo,
		branchRepo,
		nil, // commitRepo - TODO: Wire when implemented
		nil, // assignmentRepo - TODO: Wire when implemented
		log,
	)

	issueUC := usecase.NewIssueUseCase(
		issueRepo,
		branchUC,
		pullRequestUC,
		log,
	)

	// contributorUC := usecase.NewContributorUseCase(...) // TODO: Implement

	return &Container{
		DB:     db,
		Logger: log,

		// Repositories
		BASPointRepo:    basPointRepo,
		BASSystemRepo:   basSystemRepo,
		BranchRepo:      branchRepo,
		PullRequestRepo: pullRequestRepo,
		IssueRepo:       issueRepo,

		// Parsers
		BASCSVParser: basCSVParser,

		// Use Cases
		BASImportUC:   basImportUC,
		BranchUC:      branchUC,
		PullRequestUC: pullRequestUC,
		IssueUC:       issueUC,
	}, nil
}

// Close closes all resources
func (c *Container) Close() error {
	if c.DB != nil {
		return c.DB.Close()
	}
	return nil
}

// initDatabase initializes the database connection
func initDatabase(databaseURL string) (*sql.DB, error) {
	// Parse database URL if needed
	if databaseURL == "" {
		return nil, fmt.Errorf("database URL is required")
	}

	// Open database connection
	db, err := sql.Open("postgres", databaseURL)
	if err != nil {
		return nil, fmt.Errorf("failed to open database: %w", err)
	}

	// Test connection
	if err := db.Ping(); err != nil {
		return nil, fmt.Errorf("failed to ping database: %w", err)
	}

	// Configure connection pool
	db.SetMaxOpenConns(25)
	db.SetMaxIdleConns(5)

	return db, nil
}

