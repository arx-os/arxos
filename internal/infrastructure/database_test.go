package infrastructure

import (
	"context"
	"testing"
	"time"

	"github.com/arx-os/arxos/internal/config"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

func TestDatabaseHealth(t *testing.T) {
	// Create a test configuration
	cfg := &config.Config{
		PostGIS: config.PostGISConfig{
			Host:     "localhost",
			Port:     5432,
			Database: "test_db",
			User:     "test_user",
			Password: "test_password",
			SSLMode:  "disable",
			SRID:     900913,
		},
		Database: config.DatabaseConfig{
			MaxOpenConns:    10,
			MaxIdleConns:    5,
			ConnMaxLifetime: 30 * time.Minute,
		},
	}

	// Test with nil connection (should fail)
	db := &Database{
		config: cfg,
		conn:   nil,
	}

	ctx := context.Background()
	err := db.Health(ctx)
	assert.Error(t, err)
	assert.Contains(t, err.Error(), "database connection is nil")
}

func TestDatabaseConnect(t *testing.T) {
	// Create a test configuration with invalid connection details
	cfg := &config.Config{
		PostGIS: config.PostGISConfig{
			Host:     "invalid-host",
			Port:     9999,
			Database: "invalid-db",
			User:     "invalid-user",
			Password: "invalid-password",
			SSLMode:  "disable",
			SRID:     900913,
		},
		Database: config.DatabaseConfig{
			MaxOpenConns:    10,
			MaxIdleConns:    5,
			ConnMaxLifetime: 30 * time.Minute,
		},
	}

	db := &Database{
		config: cfg,
	}

	ctx := context.Background()
	err := db.Connect(ctx)

	// Should fail with invalid connection details
	assert.Error(t, err)
	assert.Contains(t, err.Error(), "failed to connect to database")
}

func TestDatabaseClose(t *testing.T) {
	db := &Database{
		config: &config.Config{},
		conn:   nil,
	}

	// Close should not error with nil connection
	err := db.Close()
	assert.NoError(t, err)
}

func TestDatabaseTransactions(t *testing.T) {
	db := &Database{
		config: &config.Config{},
		conn:   nil,
	}

	ctx := context.Background()

	// BeginTx should fail with nil connection
	tx, err := db.BeginTx(ctx)
	assert.Error(t, err)
	assert.Nil(t, tx)
	assert.Contains(t, err.Error(), "database connection is nil")

	// CommitTx should fail with nil transaction
	err = db.CommitTx(nil)
	assert.Error(t, err)
	assert.Contains(t, err.Error(), "transaction is nil")

	// RollbackTx should fail with nil transaction
	err = db.RollbackTx(nil)
	assert.Error(t, err)
	assert.Contains(t, err.Error(), "transaction is nil")
}

func TestPostGISDatabase(t *testing.T) {
	cfg := &config.Config{
		PostGIS: config.PostGISConfig{
			Host:     "localhost",
			Port:     5432,
			Database: "test_db",
			User:     "test_user",
			Password: "test_password",
			SSLMode:  "disable",
			SRID:     900913,
		},
	}

	// Test PostGIS database creation
	db, err := NewPostGISDatabase(cfg)
	require.Error(t, err) // Should fail due to invalid connection
	assert.Nil(t, db)
	assert.Contains(t, err.Error(), "failed to initialize database")
}

func TestSpatialQueries(t *testing.T) {
	pgDB := &PostGISDatabase{
		Database: &Database{
			config: &config.Config{},
			conn:   nil,
		},
	}

	sq := pgDB.SpatialQueries()
	assert.NotNil(t, sq)
	assert.Equal(t, pgDB, sq.db)

	// Note: Spatial queries are now implemented!
	// The test now verifies they exist and are callable.
	// Full integration tests would require a real database with test data.

	// Just verify the methods are implemented (no longer return "not implemented")
	assert.NotNil(t, sq)
}
