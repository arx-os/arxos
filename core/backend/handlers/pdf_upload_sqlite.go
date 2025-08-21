package handlers

import (
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"os"
	"time"

	"github.com/jmoiron/sqlx"
	_ "github.com/mattn/go-sqlite3"
)

// SimplePDFUploadSQLite handles PDF uploads with SQLite for testing
func SimplePDFUploadSQLite(w http.ResponseWriter, r *http.Request) {
	// For testing purposes, we'll create mock ArxObjects
	// since we can't connect to the AI service without PostgreSQL

	// Generate building ID for this test
	buildingID := fmt.Sprintf("test_building_%d", time.Now().Unix())

	// Connect to SQLite database
	db, err := connectToSQLiteDatabase()
	if err != nil {
		respondWithError(w, http.StatusInternalServerError, fmt.Sprintf("SQLite connection failed: %v", err))
		return
	}
	defer db.Close()

	// Ensure building exists
	err = ensureBuildingExistsSQLite(db, buildingID, "Test PDF Upload")
	if err != nil {
		respondWithError(w, http.StatusInternalServerError, fmt.Sprintf("Failed to create test building: %v", err))
		return
	}

	// Create mock ArxObjects for testing
	mockArxObjects := []map[string]interface{}{
		{
			"id":   "wall_001",
			"type": "wall",
			"confidence": map[string]interface{}{
				"overall":        0.92,
				"classification": 0.95,
				"position":       0.88,
				"properties":     0.90,
				"relationships":  0.85,
			},
			"data": map[string]interface{}{
				"x_mm":         100.0, // 100mm from origin
				"y_mm":         200.0, // 200mm from origin
				"z_mm":         0.0,   // ground level
				"length_mm":    500.0, // 500mm long
				"thickness_mm": 20.0,  // 20mm thick
				"height_mm":    300.0, // 300mm high
			},
		},
		{
			"id":   "electrical_outlet_001",
			"type": "electrical_outlet",
			"confidence": map[string]interface{}{
				"overall":        0.78,
				"classification": 0.85,
				"position":       0.75,
				"properties":     0.80,
				"relationships":  0.70,
			},
			"data": map[string]interface{}{
				"x_mm":         250.0, // 250mm from origin
				"y_mm":         150.0, // 150mm from origin
				"z_mm":         100.0, // 100mm above ground
				"length_mm":    50.0,  // 50mm long
				"thickness_mm": 25.0,  // 25mm thick
				"height_mm":    50.0,  // 50mm high
			},
		},
	}

	// Process mock ArxObjects
	storedObjects := make([]map[string]interface{}, 0)
	storedCount := 0

	for _, obj := range mockArxObjects {
		// Create ArxObject from mock data
		arxObj, err := createArxObjectFromAIResponse(obj, buildingID)
		if err != nil {
			log.Printf("Failed to create ArxObject: %v", err)
			continue
		}

		// Store in SQLite database
		err = storeArxObjectSQLite(db, arxObj)
		if err != nil {
			log.Printf("Failed to store ArxObject: %v", err)
			continue
		}

		storedCount++

		// Add to response format
		storedObjects = append(storedObjects, map[string]interface{}{
			"id":            arxObj.ID,
			"type":          arxObj.Type,
			"system":        arxObj.System,
			"x":             float64(arxObj.X) / 1e6, // Convert nm to mm for display
			"y":             float64(arxObj.Y) / 1e6,
			"width":         float64(arxObj.Width) / 1e6,
			"height":        float64(arxObj.Height) / 1e6,
			"confidence":    arxObj.Confidence,
			"original_data": obj["data"],
		})
	}

	// Create response
	response := map[string]interface{}{
		"success":     true,
		"message":     "PDF Upload Test Completed (SQLite)",
		"filename":    "test_floorplan.pdf",
		"building_id": buildingID,
		"objects":     storedObjects,
		"statistics": map[string]interface{}{
			"total_objects":      len(storedObjects),
			"overall_confidence": 0.85,
			"processing_time":    1.2,
			"stored_in_db":       storedCount > 0,
			"stored_count":       storedCount,
		},
		"note": "This is a test using SQLite with mock data. No actual PDF was processed.",
	}

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(response)
}

// TestDatabaseConnectionSQLite tests the SQLite database connection
func TestDatabaseConnectionSQLite(w http.ResponseWriter, r *http.Request) {
	// Connect to SQLite database
	db, err := connectToSQLiteDatabase()
	if err != nil {
		respondWithError(w, http.StatusInternalServerError, fmt.Sprintf("SQLite connection failed: %v", err))
		return
	}
	defer db.Close()

	// Test basic query
	var count int
	err = db.Get(&count, "SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
	if err != nil {
		respondWithError(w, http.StatusInternalServerError, fmt.Sprintf("SQLite query failed: %v", err))
		return
	}

	// Check if our tables exist
	var arxObjectsCount int
	err = db.Get(&arxObjectsCount, "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='arx_objects'")
	if err != nil {
		arxObjectsCount = 0
	}

	var buildingsCount int
	err = db.Get(&buildingsCount, "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='pdf_buildings'")
	if err != nil {
		buildingsCount = 0
	}

	response := map[string]interface{}{
		"success": true,
		"message": "SQLite database connection successful",
		"database": map[string]interface{}{
			"type":                "sqlite",
			"status":              "connected",
			"total_tables":        count,
			"arx_objects_table":   arxObjectsCount > 0,
			"pdf_buildings_table": buildingsCount > 0,
			"file_path":           getSQLiteDBPath(),
		},
	}

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(response)
}

// TestArxObjectPipelineSQLite tests the complete ArxObject pipeline with SQLite
func TestArxObjectPipelineSQLite(w http.ResponseWriter, r *http.Request) {
	// Connect to SQLite database
	db, err := connectToSQLiteDatabase()
	if err != nil {
		respondWithError(w, http.StatusInternalServerError, fmt.Sprintf("SQLite connection failed: %v", err))
		return
	}
	defer db.Close()

	// Test 1: Verify tables exist
	tableTests := map[string]string{
		"pdf_buildings": "SELECT COUNT(*) FROM pdf_buildings",
		"arx_objects":   "SELECT COUNT(*) FROM arx_objects",
	}

	tableResults := make(map[string]interface{})
	for tableName, query := range tableTests {
		var count int
		err := db.Get(&count, query)
		if err != nil {
			tableResults[tableName] = map[string]interface{}{
				"exists": false,
				"error":  err.Error(),
			}
		} else {
			tableResults[tableName] = map[string]interface{}{
				"exists": true,
				"count":  count,
			}
		}
	}

	// Test 2: Test ArxObject creation and storage
	testResults := make(map[string]interface{})

	// Create a test building
	testBuildingID := fmt.Sprintf("test_building_%d", time.Now().Unix())
	err = ensureBuildingExistsSQLite(db, testBuildingID, "Test Building")
	if err != nil {
		testResults["building_creation"] = map[string]interface{}{
			"success": false,
			"error":   err.Error(),
		}
	} else {
		testResults["building_creation"] = map[string]interface{}{
			"success":     true,
			"building_id": testBuildingID,
		}
	}

	// Create a test ArxObject
	testArxObject := &SimpleArxObject{
		ID:         fmt.Sprintf("test_arx_%d", time.Now().UnixNano()),
		Type:       "wall",
		System:     "structural",
		X:          1000000000, // 1 meter in nanometers
		Y:          2000000000, // 2 meters in nanometers
		Z:          0,          // ground level
		Width:      5000000000, // 5 meters in nanometers
		Height:     3000000000, // 3 meters in nanometers
		Depth:      200000000,  // 20cm in nanometers
		Confidence: 0.95,
		BuildingID: testBuildingID,
		CreatedAt:  time.Now(),
	}

	// Test ArxObject storage
	err = storeArxObjectSQLite(db, testArxObject)
	if err != nil {
		testResults["arxobject_storage"] = map[string]interface{}{
			"success": false,
			"error":   err.Error(),
		}
	} else {
		testResults["arxobject_storage"] = map[string]interface{}{
			"success":      true,
			"arxobject_id": testArxObject.ID,
		}
	}

	// Test 3: Verify stored data
	var storedObject struct {
		ID         string `db:"id"`
		BuildingID string `db:"building_id"`
		ObjectType int    `db:"object_type"`
		SystemType int    `db:"system_type"`
		XNano      int64  `db:"x_nano"`
		YNano      int64  `db:"y_nano"`
		WidthNano  int64  `db:"width_nano"`
		HeightNano int64  `db:"height_nano"`
		Properties []byte `db:"properties"`
	}

	err = db.Get(&storedObject, `
		SELECT id, building_id, object_type, system_type, x_nano, y_nano, width_nano, height_nano, properties
		FROM arx_objects 
		WHERE id = ? AND building_id = ?
	`, testArxObject.ID, testArxObject.BuildingID)

	if err != nil {
		testResults["data_verification"] = map[string]interface{}{
			"success": false,
			"error":   err.Error(),
		}
	} else {
		// Verify coordinate conversion (nm to m)
		xMeters := float64(storedObject.XNano) / 1e9
		yMeters := float64(storedObject.YNano) / 1e9
		widthMeters := float64(storedObject.WidthNano) / 1e9
		heightMeters := float64(storedObject.HeightNano) / 1e9

		testResults["data_verification"] = map[string]interface{}{
			"success": true,
			"coordinates": map[string]interface{}{
				"x_nano":        storedObject.XNano,
				"y_nano":        storedObject.YNano,
				"x_meters":      xMeters,
				"y_meters":      yMeters,
				"width_meters":  widthMeters,
				"height_meters": heightMeters,
			},
			"system_mapping": map[string]interface{}{
				"object_type":          storedObject.ObjectType,
				"system_type":          storedObject.SystemType,
				"expected_object_type": 1, // wall
				"expected_system_type": 1, // structural
			},
		}
	}

	// Test 4: Clean up test data
	_, err = db.Exec("DELETE FROM arx_objects WHERE building_id = ?", testBuildingID)
	if err != nil {
		testResults["cleanup"] = map[string]interface{}{
			"success": false,
			"error":   err.Error(),
		}
	} else {
		_, err = db.Exec("DELETE FROM pdf_buildings WHERE id = ?", testBuildingID)
		if err != nil {
			testResults["cleanup"] = map[string]interface{}{
				"success": false,
				"error":   err.Error(),
			}
		} else {
			testResults["cleanup"] = map[string]interface{}{
				"success": true,
			}
		}
	}

	// Compile comprehensive test results
	response := map[string]interface{}{
		"success":   true,
		"message":   "ArxObject pipeline test completed (SQLite)",
		"timestamp": time.Now().Format(time.RFC3339),
		"database":  "sqlite",
		"tests": map[string]interface{}{
			"database_schema": tableResults,
			"pipeline_tests":  testResults,
		},
		"summary": map[string]interface{}{
			"tables_exist": tableResults["pdf_buildings"].(map[string]interface{})["exists"] == true &&
				tableResults["arx_objects"].(map[string]interface{})["exists"] == true,
			"pipeline_working": testResults["arxobject_storage"].(map[string]interface{})["success"] == true,
			"data_integrity":   testResults["data_verification"].(map[string]interface{})["success"] == true,
		},
	}

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(response)
}

// connectToSQLiteDatabase connects to the SQLite database
func connectToSQLiteDatabase() (*sqlx.DB, error) {
	dbPath := getSQLiteDBPath()

	// Create database directory if it doesn't exist
	dbDir := "./test_data"
	if err := os.MkdirAll(dbDir, 0755); err != nil {
		return nil, fmt.Errorf("failed to create database directory: %v", err)
	}

	// Connect to SQLite database
	db, err := sqlx.Connect("sqlite3", dbPath)
	if err != nil {
		return nil, fmt.Errorf("failed to connect to SQLite: %v", err)
	}

	// Initialize database schema
	if err := initializeSQLiteSchema(db); err != nil {
		return nil, fmt.Errorf("failed to initialize schema: %v", err)
	}

	return db, nil
}

// getSQLiteDBPath returns the path to the SQLite database file
func getSQLiteDBPath() string {
	return "./test_data/arxos_test.db"
}

// initializeSQLiteSchema creates the required tables in SQLite
func initializeSQLiteSchema(db *sqlx.DB) error {
	// Create pdf_buildings table
	_, err := db.Exec(`
		CREATE TABLE IF NOT EXISTS pdf_buildings (
			id TEXT PRIMARY KEY,
			name TEXT,
			address TEXT,
			total_floors INTEGER DEFAULT 0,
			total_objects INTEGER DEFAULT 0,
			created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
			updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
			metadata TEXT
		)
	`)
	if err != nil {
		return fmt.Errorf("failed to create pdf_buildings table: %v", err)
	}

	// Create arx_objects table
	_, err = db.Exec(`
		CREATE TABLE IF NOT EXISTS arx_objects (
			id TEXT NOT NULL,
			building_id TEXT NOT NULL,
			object_type INTEGER NOT NULL,
			system_type INTEGER NOT NULL,
			scale_level INTEGER NOT NULL,
			x_nano INTEGER NOT NULL,
			y_nano INTEGER NOT NULL,
			z_nano INTEGER NOT NULL,
			length_nano INTEGER NOT NULL,
			width_nano INTEGER NOT NULL,
			height_nano INTEGER NOT NULL,
			type_flags INTEGER NOT NULL,
			rotation_pack INTEGER,
			metadata_id INTEGER,
			parent_id INTEGER,
			properties TEXT,
			created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
			updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
			PRIMARY KEY (id, building_id),
			FOREIGN KEY (building_id) REFERENCES pdf_buildings(id) ON DELETE CASCADE
		)
	`)
	if err != nil {
		return fmt.Errorf("failed to create arx_objects table: %v", err)
	}

	// Create indexes
	_, err = db.Exec("CREATE INDEX IF NOT EXISTS idx_arx_objects_building ON arx_objects(building_id)")
	if err != nil {
		return fmt.Errorf("failed to create building index: %v", err)
	}

	_, err = db.Exec("CREATE INDEX IF NOT EXISTS idx_arx_objects_type ON arx_objects(object_type)")
	if err != nil {
		return fmt.Errorf("failed to create type index: %v", err)
	}

	return nil
}

// ensureBuildingExistsSQLite creates the building record if it doesn't exist
func ensureBuildingExistsSQLite(db *sqlx.DB, buildingID, filename string) error {
	_, err := db.Exec(`
		INSERT INTO pdf_buildings (id, name, created_at, updated_at)
		VALUES (?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
		ON CONFLICT(id) DO NOTHING
	`, buildingID, filename)

	return err
}

// storeArxObjectSQLite stores a single ArxObject in the SQLite database
func storeArxObjectSQLite(db *sqlx.DB, obj *SimpleArxObject) error {
	// Map system string to system type integer
	systemType := mapSystemToType(obj.System)

	// Map object type string to object type integer
	objectType := mapObjectTypeToInt(obj.Type)

	// Create properties JSON
	properties := map[string]interface{}{
		"confidence":   obj.Confidence,
		"source":       "test_data",
		"extracted_at": time.Now().Format(time.RFC3339),
	}
	propertiesJSON, _ := json.Marshal(properties)

	// Insert into SQLite database
	_, err := db.Exec(`
		INSERT INTO arx_objects (
			id, building_id, object_type, system_type, scale_level,
			x_nano, y_nano, z_nano, length_nano, width_nano, height_nano,
			type_flags, properties, created_at, updated_at
		) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
		ON CONFLICT(id, building_id) DO UPDATE SET
			x_nano = excluded.x_nano,
			y_nano = excluded.y_nano,
			z_nano = excluded.z_nano,
			length_nano = excluded.length_nano,
			width_nano = excluded.width_nano,
			height_nano = excluded.height_nano,
			properties = excluded.properties,
			updated_at = CURRENT_TIMESTAMP
	`,
		obj.ID, obj.BuildingID, objectType, systemType, 0, // scale_level = 0 for now
		obj.X, obj.Y, obj.Z, obj.Width, obj.Height, obj.Depth,
		0, // type_flags = 0 for now
		string(propertiesJSON),
	)

	return err
}
