package handlers

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"log"
	"mime/multipart"
	"net/http"
	"os"
	"time"

	"github.com/jmoiron/sqlx"
	_ "github.com/lib/pq"
)

// SimplePDFUpload handles PDF uploads and forwards to AI service for processing
func SimplePDFUpload(w http.ResponseWriter, r *http.Request) {
	// Parse multipart form
	err := r.ParseMultipartForm(50 << 20) // 50 MB max
	if err != nil {
		respondWithError(w, http.StatusBadRequest, "Failed to parse form data")
		return
	}

	// Get the file
	file, header, err := r.FormFile("file")
	if err != nil {
		respondWithError(w, http.StatusBadRequest, "No file provided")
		return
	}
	defer file.Close()

	// Read file content
	fileBytes, err := io.ReadAll(file)
	if err != nil {
		respondWithError(w, http.StatusInternalServerError, "Failed to read file")
		return
	}

	// Forward to AI service
	aiServiceURL := os.Getenv("AI_SERVICE_URL")
	if aiServiceURL == "" {
		aiServiceURL = "http://localhost:5000"
	}

	// Create multipart form for AI service
	body := &bytes.Buffer{}
	writer := multipart.NewWriter(body)

	// Add file to form
	part, err := writer.CreateFormFile("file", header.Filename)
	if err != nil {
		respondWithError(w, http.StatusInternalServerError, "Failed to create form")
		return
	}

	_, err = part.Write(fileBytes)
	if err != nil {
		respondWithError(w, http.StatusInternalServerError, "Failed to write file")
		return
	}

	// Add building type
	writer.WriteField("building_type", "general")
	writer.Close()

	// Send to AI service
	req, err := http.NewRequest("POST", aiServiceURL+"/api/v1/convert", body)
	if err != nil {
		respondWithError(w, http.StatusInternalServerError, "Failed to create request")
		return
	}
	req.Header.Set("Content-Type", writer.FormDataContentType())

	client := &http.Client{Timeout: 60 * time.Second}
	resp, err := client.Do(req)
	if err != nil {
		respondWithError(w, http.StatusServiceUnavailable, "AI service unavailable")
		return
	}
	defer resp.Body.Close()

	// Read AI service response
	aiResponse, err := io.ReadAll(resp.Body)
	if err != nil {
		respondWithError(w, http.StatusInternalServerError, "Failed to read AI response")
		return
	}

	// Parse and transform response
	var aiResult map[string]interface{}
	if err := json.Unmarshal(aiResponse, &aiResult); err != nil {
		respondWithError(w, http.StatusInternalServerError, "Invalid AI response")
		return
	}

	// Extract ArxObjects from AI response
	arxobjects, ok := aiResult["arxobjects"].([]interface{})
	if !ok {
		arxobjects = []interface{}{}
	}

	// Generate building ID for this upload
	buildingID := fmt.Sprintf("building_%d", time.Now().Unix())

	// Store ArxObjects in database if we have any
	storedObjects := make([]map[string]interface{}, 0)
	storedCount := 0

	if len(arxobjects) > 0 {
		// Connect to database
		db, err := connectToDatabase()
		if err != nil {
			log.Printf("Failed to connect to database: %v", err)
			// Continue with response even if database connection fails
		} else {
			defer db.Close()

			// Ensure building exists
			err = ensureBuildingExists(db, buildingID, header.Filename)
			if err != nil {
				log.Printf("Failed to ensure building exists: %v", err)
			}

			// Store each ArxObject
			for _, obj := range arxobjects {
				if objMap, ok := obj.(map[string]interface{}); ok {
					// Create ArxObject from AI response
					arxObj, err := createArxObjectFromAIResponse(objMap, buildingID)
					if err != nil {
						log.Printf("Failed to create ArxObject: %v", err)
						continue
					}

					// Store in database
					err = storeArxObject(db, arxObj)
					if err != nil {
						log.Printf("Failed to store ArxObject: %v", err)
						continue
					}

					storedCount++

					// Add to frontend response format
					// Include geometry field for proper rendering
					frontendObj := map[string]interface{}{
						"id":         arxObj.ID,
						"type":       arxObj.Type,
						"system":     arxObj.System,
						"x":          float64(arxObj.X) / 1e6, // Convert nm to mm for display
						"y":          float64(arxObj.Y) / 1e6,
						"width":      float64(arxObj.Width) / 1e6,
						"height":     float64(arxObj.Height) / 1e6,
						"confidence": arxObj.Confidence,
						"data":       objMap["data"], // Include full data for debugging
					}
					
					// Pass through geometry if present
					if geometry, ok := objMap["geometry"]; ok {
						frontendObj["geometry"] = geometry
					}
					
					storedObjects = append(storedObjects, frontendObj)
				}
			}
		}
	}

	// Create response
	response := map[string]interface{}{
		"success":     true,
		"message":     fmt.Sprintf("Processed %s", header.Filename),
		"filename":    header.Filename,
		"building_id": buildingID,
		"objects":     storedObjects,
		"statistics": map[string]interface{}{
			"total_objects":      len(storedObjects),
			"overall_confidence": aiResult["overall_confidence"],
			"processing_time":    aiResult["processing_time"],
			"stored_in_db":       storedCount > 0,
			"stored_count":       storedCount,
		},
	}

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(response)
}

// TestDatabaseConnection tests the database connection and returns status
func TestDatabaseConnection(w http.ResponseWriter, r *http.Request) {
	// Connect to database
	db, err := connectToDatabase()
	if err != nil {
		respondWithError(w, http.StatusInternalServerError, fmt.Sprintf("Database connection failed: %v", err))
		return
	}
	defer db.Close()

	// Test basic query
	var count int
	err = db.Get(&count, "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public'")
	if err != nil {
		respondWithError(w, http.StatusInternalServerError, fmt.Sprintf("Database query failed: %v", err))
		return
	}

	// Check if our tables exist
	var arxObjectsCount int
	err = db.Get(&arxObjectsCount, "SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'arx_objects'")
	if err != nil {
		arxObjectsCount = 0
	}

	var buildingsCount int
	err = db.Get(&buildingsCount, "SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'pdf_buildings'")
	if err != nil {
		buildingsCount = 0
	}

	response := map[string]interface{}{
		"success": true,
		"message": "Database connection successful",
		"database": map[string]interface{}{
			"status":              "connected",
			"total_tables":        count,
			"arx_objects_table":   arxObjectsCount > 0,
			"pdf_buildings_table": buildingsCount > 0,
		},
	}

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(response)
}

// TestArxObjectPipeline tests the complete ArxObject creation and storage pipeline
func TestArxObjectPipeline(w http.ResponseWriter, r *http.Request) {
	// Connect to database
	db, err := connectToDatabase()
	if err != nil {
		respondWithError(w, http.StatusInternalServerError, fmt.Sprintf("Database connection failed: %v", err))
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
	err = ensureBuildingExists(db, testBuildingID, "Test Building")
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
	err = storeArxObject(db, testArxObject)
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
		WHERE id = $1 AND building_id = $2
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
	_, err = db.Exec("DELETE FROM arx_objects WHERE building_id = $1", testBuildingID)
	if err != nil {
		testResults["cleanup"] = map[string]interface{}{
			"success": false,
			"error":   err.Error(),
		}
	} else {
		_, err = db.Exec("DELETE FROM pdf_buildings WHERE id = $1", testBuildingID)
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
		"message":   "ArxObject pipeline test completed",
		"timestamp": time.Now().Format(time.RFC3339),
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

// TestAIServiceIntegration tests the AI service response processing with mock data
func TestAIServiceIntegration(w http.ResponseWriter, r *http.Request) {
	// Mock AI service response (simulating what the real AI service would return)
	mockAIResponse := map[string]interface{}{
		"arxobjects": []map[string]interface{}{
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
				"id":   "wall_002",
				"type": "wall",
				"confidence": map[string]interface{}{
					"overall":        0.87,
					"classification": 0.90,
					"position":       0.85,
					"properties":     0.88,
					"relationships":  0.80,
				},
				"data": map[string]interface{}{
					"x_mm":         600.0, // 600mm from origin
					"y_mm":         200.0, // 200mm from origin
					"z_mm":         0.0,   // ground level
					"length_mm":    400.0, // 400mm long
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
		},
		"overall_confidence": 0.86,
		"processing_time":    2.3,
	}

	// Generate building ID for this test
	buildingID := fmt.Sprintf("test_building_%d", time.Now().Unix())

	// Connect to database
	db, err := connectToDatabase()
	if err != nil {
		respondWithError(w, http.StatusInternalServerError, fmt.Sprintf("Database connection failed: %v", err))
		return
	}
	defer db.Close()

	// Ensure building exists
	err = ensureBuildingExists(db, buildingID, "AI Service Test Building")
	if err != nil {
		respondWithError(w, http.StatusInternalServerError, fmt.Sprintf("Failed to create test building: %v", err))
		return
	}

	// Process mock AI response (same logic as SimplePDFUpload)
	arxobjects := mockAIResponse["arxobjects"].([]map[string]interface{})

	storedObjects := make([]map[string]interface{}, 0)
	storedCount := 0

	for _, obj := range arxobjects {
		// Create ArxObject from AI response
		arxObj, err := createArxObjectFromAIResponse(obj, buildingID)
		if err != nil {
			log.Printf("Failed to create ArxObject: %v", err)
			continue
		}

		// Store in database
		err = storeArxObject(db, arxObj)
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

	// Create comprehensive test response
	response := map[string]interface{}{
		"success":           true,
		"message":           "AI Service Integration Test Completed",
		"building_id":       buildingID,
		"mock_ai_response":  mockAIResponse,
		"processed_objects": storedObjects,
		"statistics": map[string]interface{}{
			"total_objects":      len(storedObjects),
			"overall_confidence": mockAIResponse["overall_confidence"],
			"processing_time":    mockAIResponse["processing_time"],
			"stored_in_db":       storedCount > 0,
			"stored_count":       storedCount,
		},
		"coordinate_analysis": map[string]interface{}{
			"nanometer_precision": "All coordinates stored in nanometers (1nm = 1e-9m)",
			"conversion_example": map[string]interface{}{
				"wall_001_x": map[string]interface{}{
					"ai_input_mm":       100.0,
					"stored_nano":       100000000, // 100mm * 1e6
					"converted_back_mm": 100.0,     // 100000000 / 1e6
				},
			},
		},
		"system_classification": map[string]interface{}{
			"wall":              "structural",
			"electrical_outlet": "electrical",
		},
	}

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(response)
}

// Simple ArxObject structure for database storage
type SimpleArxObject struct {
	ID         string
	Type       string
	System     string
	X          int64 // nanometers
	Y          int64 // nanometers
	Z          int64 // nanometers
	Width      int64 // nanometers
	Height     int64 // nanometers
	Depth      int64 // nanometers
	Confidence float32
	BuildingID string
	CreatedAt  time.Time
}

// createArxObjectFromAIResponse converts AI service response to SimpleArxObject
func createArxObjectFromAIResponse(objMap map[string]interface{}, buildingID string) (*SimpleArxObject, error) {
	// Extract basic properties
	objType, ok := objMap["type"].(string)
	if !ok {
		return nil, fmt.Errorf("missing or invalid type")
	}

	// Determine system classification based on type
	system := determineSystemFromType(objType)

	// Create new ArxObject
	arxObj := &SimpleArxObject{
		ID:         fmt.Sprintf("arx_%d", time.Now().UnixNano()),
		Type:       objType,
		System:     system,
		BuildingID: buildingID,
		CreatedAt:  time.Now(),
		Confidence: 0.5, // Default confidence
	}

	// Extract and set position (convert from mm to nanometers)
	if data, ok := objMap["data"].(map[string]interface{}); ok {
		if xMm, ok := data["x_mm"].(float64); ok {
			arxObj.X = int64(xMm * 1e6) // Convert mm to nm
		}
		if yMm, ok := data["y_mm"].(float64); ok {
			arxObj.Y = int64(yMm * 1e6) // Convert mm to nm
		}
		if zMm, ok := data["z_mm"].(float64); ok {
			arxObj.Z = int64(zMm * 1e6) // Convert mm to nm
		}

		// Set dimensions
		if lengthMm, ok := data["length_mm"].(float64); ok {
			arxObj.Width = int64(lengthMm * 1e6) // Convert mm to nm
		}
		if thicknessMm, ok := data["thickness_mm"].(float64); ok {
			arxObj.Height = int64(thicknessMm * 1e6) // Convert mm to nm
		}
		if depthMm, ok := data["depth_mm"].(float64); ok {
			arxObj.Depth = int64(depthMm * 1e6) // Convert mm to nm
		}
	}

	// Fallback to geometry if data not available
	if arxObj.X == 0 && arxObj.Y == 0 {
		if geometry, ok := objMap["geometry"].(map[string]interface{}); ok {
			if coords, ok := geometry["coordinates"].([]interface{}); ok && len(coords) > 0 {
				if coord, ok := coords[0].([]interface{}); ok && len(coord) >= 2 {
					if xVal, ok := coord[0].(float64); ok {
						arxObj.X = int64(xVal * 1e6) // Convert to nm
					}
					if yVal, ok := coord[1].(float64); ok {
						arxObj.Y = int64(yVal * 1e6) // Convert to nm
					}
				}
			}
		}
	}

	// Set confidence scores
	if conf, ok := objMap["confidence"].(map[string]interface{}); ok {
		if overall, ok := conf["overall"].(float64); ok {
			arxObj.Confidence = float32(overall)
		}
	}

	return arxObj, nil
}

// connectToDatabase connects to the PostgreSQL database
func connectToDatabase() (*sqlx.DB, error) {
	dsn := os.Getenv("DATABASE_URL")
	if dsn == "" {
		dsn = "postgres://localhost/arxos?sslmode=disable"
	}

	return sqlx.Connect("postgres", dsn)
}

// ensureBuildingExists creates the building record if it doesn't exist
func ensureBuildingExists(db *sqlx.DB, buildingID, filename string) error {
	_, err := db.Exec(`
		INSERT INTO pdf_buildings (id, name, created_at, updated_at)
		VALUES ($1, $2, NOW(), NOW())
		ON CONFLICT (id) DO NOTHING
	`, buildingID, filename)

	return err
}

// storeArxObject stores a single ArxObject in the database
func storeArxObject(db *sqlx.DB, obj *SimpleArxObject) error {
	// Map system string to system type integer
	systemType := mapSystemToType(obj.System)

	// Map object type string to object type integer
	objectType := mapObjectTypeToInt(obj.Type)

	// Create properties JSON
	properties := map[string]interface{}{
		"confidence":   obj.Confidence,
		"source":       "ai_service",
		"extracted_at": time.Now().Format(time.RFC3339),
	}
	propertiesJSON, _ := json.Marshal(properties)

	// Insert into database using the actual schema
	_, err := db.Exec(`
		INSERT INTO arx_objects (
			id, building_id, object_type, system_type, scale_level,
			x_nano, y_nano, z_nano, length_nano, width_nano, height_nano,
			type_flags, properties, created_at, updated_at
		) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15)
		ON CONFLICT (id, building_id) DO UPDATE SET
			x_nano = EXCLUDED.x_nano,
			y_nano = EXCLUDED.y_nano,
			z_nano = EXCLUDED.z_nano,
			length_nano = EXCLUDED.length_nano,
			width_nano = EXCLUDED.width_nano,
			height_nano = EXCLUDED.height_nano,
			properties = EXCLUDED.properties,
			updated_at = NOW()
	`,
		obj.ID, obj.BuildingID, objectType, systemType, 0, // scale_level = 0 for now
		obj.X, obj.Y, obj.Z, obj.Width, obj.Height, obj.Depth,
		0, // type_flags = 0 for now
		propertiesJSON, obj.CreatedAt, obj.CreatedAt,
	)

	return err
}

// mapSystemToType maps system string to system type integer
func mapSystemToType(system string) int {
	switch system {
	case "structural":
		return 1
	case "electrical":
		return 2
	case "mechanical":
		return 3
	case "plumbing":
		return 4
	case "fire_protection":
		return 5
	case "architectural":
		return 6
	case "spatial":
		return 7
	default:
		return 0
	}
}

// mapObjectTypeToInt maps object type string to integer
func mapObjectTypeToInt(objType string) int {
	switch objType {
	case "wall":
		return 1
	case "column":
		return 2
	case "beam":
		return 3
	case "slab":
		return 4
	case "foundation":
		return 5
	case "roof":
		return 6
	case "door":
		return 7
	case "window":
		return 8
	case "electrical_outlet":
		return 101
	case "electrical_switch":
		return 102
	case "electrical_panel":
		return 103
	case "hvac_unit":
		return 201
	case "hvac_duct":
		return 202
	case "plumbing_pipe":
		return 301
	case "plumbing_fixture":
		return 302
	default:
		return 0
	}
}

// determineSystemFromType maps ArxObject types to building systems
func determineSystemFromType(objType string) string {
	switch objType {
	case "wall", "column", "beam", "slab", "foundation", "roof":
		return "structural"
	case "electrical_outlet", "electrical_switch", "electrical_panel", "electrical_conduit", "light_fixture":
		return "electrical"
	case "hvac_unit", "hvac_duct", "hvac_vent", "hvac_diffuser", "thermostat":
		return "mechanical"
	case "plumbing_pipe", "plumbing_fixture", "valve", "pump":
		return "plumbing"
	case "fire_sprinkler", "smoke_detector", "fire_alarm":
		return "fire_protection"
	case "door", "window", "opening":
		return "architectural"
	case "building", "floor", "room", "zone", "corridor", "stairwell", "elevator_shaft":
		return "spatial"
	default:
		return "general"
	}
}
