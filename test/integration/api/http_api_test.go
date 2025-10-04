/**
 * API Integration Tests - Tests HTTP, GraphQL, and WebSocket APIs
 */

package integration

import (
	"bytes"
	"encoding/json"
	"fmt"
	"net/http"
	"net/http/httptest"
	"testing"
	"time"

	"github.com/arx-os/arxos/internal/app"
	"github.com/arx-os/arxos/internal/config"
	"github.com/arx-os/arxos/internal/interfaces/http/handlers"
	"github.com/arx-os/arxos/internal/interfaces/http/middleware"
	"github.com/arx-os/arxos/internal/interfaces/http/types"
	"github.com/gorilla/websocket"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

// APIIntegrationTestSuite manages API integration tests
type APIIntegrationTestSuite struct {
	app        *app.Container
	config     *config.Config
	server     *httptest.Server
	httpClient *http.Client
	wsConn     *websocket.Conn
}

// NewAPIIntegrationTestSuite creates a new API integration test suite
func NewAPIIntegrationTestSuite(t *testing.T) *APIIntegrationTestSuite {
	// Load test configuration
	cfg, err := config.Load("test/config/test_config.yaml")
	require.NoError(t, err)

	// Create application container
	container := app.NewContainer()
	// Container initialization happens automatically when accessing dependencies

	// Create HTTP client
	httpClient := &http.Client{
		Timeout: 30 * time.Second,
	}

	return &APIIntegrationTestSuite{
		app:        container,
		config:     cfg,
		httpClient: httpClient,
	}
}

// SetupTestEnvironment prepares the API test environment
func (suite *APIIntegrationTestSuite) SetupTestEnvironment(t *testing.T) {
	// Create test server
	mux := http.NewServeMux()

	// Setup middleware
	middlewareManager := middleware.NewMiddlewareManager(
		suite.app.GetLogger(),
		nil, // JWT Manager
	)

	// Create BaseHandler for test handlers
	testLogger := suite.app.GetLogger()
	baseHandler := handlers.NewBaseHandler(testLogger, nil) // No JWT manager needed for tests

	// Setup handlers using Clean Architecture
	buildingHandler := handlers.NewBuildingHandler(
		baseHandler,
		suite.app.GetBuildingUseCase(),
		testLogger,
	)

	equipmentHandler := handlers.NewEquipmentHandler(
		&types.Server{}, // Still uses old constructor for now
		suite.app.GetEquipmentUseCase(),
		testLogger,
	)

	userHandler := handlers.NewUserHandler(
		baseHandler,
		suite.app.GetUserUseCase(),
		testLogger,
	)

	// Register routes
	mux.HandleFunc("/api/v1/buildings", func(w http.ResponseWriter, r *http.Request) {
		switch r.Method {
		case http.MethodGet:
			buildingHandler.ListBuildings(w, r)
		case http.MethodPost:
			buildingHandler.CreateBuilding(w, r)
		}
	})

	mux.HandleFunc("/api/v1/buildings/", func(w http.ResponseWriter, r *http.Request) {
		switch r.Method {
		case http.MethodGet:
			buildingHandler.GetBuilding(w, r)
		case http.MethodPut:
			buildingHandler.UpdateBuilding(w, r)
		case http.MethodDelete:
			buildingHandler.DeleteBuilding(w, r)
		}
	})

	mux.HandleFunc("/api/v1/equipment", func(w http.ResponseWriter, r *http.Request) {
		switch r.Method {
		case http.MethodGet:
			equipmentHandler.ListEquipment(w, r)
		case http.MethodPost:
			equipmentHandler.CreateEquipment(w, r)
		}
	})

	mux.HandleFunc("/api/v1/users", func(w http.ResponseWriter, r *http.Request) {
		switch r.Method {
		case http.MethodGet:
			userHandler.ListUsers(w, r)
		case http.MethodPost:
			userHandler.CreateUser(w, r)
		}
	})

	// Apply middleware
	handler := middlewareManager.ApplyAPIMiddleware(mux)

	// Create test server
	suite.server = httptest.NewServer(handler)
}

// TeardownTestEnvironment cleans up the API test environment
func (suite *APIIntegrationTestSuite) TeardownTestEnvironment(t *testing.T) {
	if suite.wsConn != nil {
		suite.wsConn.Close()
	}

	if suite.server != nil {
		suite.server.Close()
	}

	// Note: Container doesn't have Close method, it's managed by Go's GC
}

// TestHTTPAPI tests HTTP API endpoints
func TestHTTPAPI(t *testing.T) {
	suite := NewAPIIntegrationTestSuite(t)
	suite.SetupTestEnvironment(t)
	defer suite.TeardownTestEnvironment(t)

	t.Run("CreateBuilding", func(t *testing.T) {
		// Create building request
		reqBody := map[string]interface{}{
			"name":    "API Test Building",
			"address": "123 API Street",
			"coordinates": map[string]float64{
				"x": 40.7128,
				"y": -74.0060,
				"z": 0,
			},
		}

		jsonBody, err := json.Marshal(reqBody)
		require.NoError(t, err)

		// Make HTTP request
		resp, err := suite.httpClient.Post(
			suite.server.URL+"/api/v1/buildings",
			"application/json",
			bytes.NewBuffer(jsonBody),
		)
		require.NoError(t, err)
		defer resp.Body.Close()

		// Verify response
		assert.Equal(t, http.StatusCreated, resp.StatusCode)

		var response map[string]interface{}
		err = json.NewDecoder(resp.Body).Decode(&response)
		require.NoError(t, err)

		assert.NotNil(t, response["id"])
		assert.Equal(t, "API Test Building", response["name"])
		assert.Equal(t, "123 API Street", response["address"])
	})

	t.Run("GetBuilding", func(t *testing.T) {
		// First create a building
		reqBody := map[string]interface{}{
			"name":    "Get Test Building",
			"address": "456 Get Street",
		}

		jsonBody, err := json.Marshal(reqBody)
		require.NoError(t, err)

		createResp, err := suite.httpClient.Post(
			suite.server.URL+"/api/v1/buildings",
			"application/json",
			bytes.NewBuffer(jsonBody),
		)
		require.NoError(t, err)
		defer createResp.Body.Close()

		var createResponse map[string]interface{}
		err = json.NewDecoder(createResp.Body).Decode(&createResponse)
		require.NoError(t, err)

		buildingID := createResponse["id"].(string)

		// Now get the building
		resp, err := suite.httpClient.Get(suite.server.URL + "/api/v1/buildings/" + buildingID)
		require.NoError(t, err)
		defer resp.Body.Close()

		assert.Equal(t, http.StatusOK, resp.StatusCode)

		var response map[string]interface{}
		err = json.NewDecoder(resp.Body).Decode(&response)
		require.NoError(t, err)

		assert.Equal(t, buildingID, response["id"])
		assert.Equal(t, "Get Test Building", response["name"])
	})

	t.Run("UpdateBuilding", func(t *testing.T) {
		// First create a building
		reqBody := map[string]interface{}{
			"name":    "Update Test Building",
			"address": "789 Update Street",
		}

		jsonBody, err := json.Marshal(reqBody)
		require.NoError(t, err)

		createResp, err := suite.httpClient.Post(
			suite.server.URL+"/api/v1/buildings",
			"application/json",
			bytes.NewBuffer(jsonBody),
		)
		require.NoError(t, err)
		defer createResp.Body.Close()

		var createResponse map[string]interface{}
		err = json.NewDecoder(createResp.Body).Decode(&createResponse)
		require.NoError(t, err)

		buildingID := createResponse["id"].(string)

		// Update the building
		updateBody := map[string]interface{}{
			"name":    "Updated Test Building",
			"address": "999 Updated Street",
		}

		updateJsonBody, err := json.Marshal(updateBody)
		require.NoError(t, err)

		req, err := http.NewRequest("PUT", suite.server.URL+"/api/v1/buildings/"+buildingID, bytes.NewBuffer(updateJsonBody))
		require.NoError(t, err)
		req.Header.Set("Content-Type", "application/json")

		resp, err := suite.httpClient.Do(req)
		require.NoError(t, err)
		defer resp.Body.Close()

		assert.Equal(t, http.StatusOK, resp.StatusCode)

		var response map[string]interface{}
		err = json.NewDecoder(resp.Body).Decode(&response)
		require.NoError(t, err)

		assert.Equal(t, "Updated Test Building", response["name"])
		assert.Equal(t, "999 Updated Street", response["address"])
	})

	t.Run("ListBuildings", func(t *testing.T) {
		// Create multiple buildings
		for i := 0; i < 3; i++ {
			reqBody := map[string]interface{}{
				"name":    fmt.Sprintf("List Test Building %d", i+1),
				"address": fmt.Sprintf("%d List Street", 100+i),
			}

			jsonBody, err := json.Marshal(reqBody)
			require.NoError(t, err)

			resp, err := suite.httpClient.Post(
				suite.server.URL+"/api/v1/buildings",
				"application/json",
				bytes.NewBuffer(jsonBody),
			)
			require.NoError(t, err)
			resp.Body.Close()
		}

		// List buildings
		resp, err := suite.httpClient.Get(suite.server.URL + "/api/v1/buildings")
		require.NoError(t, err)
		defer resp.Body.Close()

		assert.Equal(t, http.StatusOK, resp.StatusCode)

		var response map[string]interface{}
		err = json.NewDecoder(resp.Body).Decode(&response)
		require.NoError(t, err)

		buildings := response["buildings"].([]interface{})
		assert.GreaterOrEqual(t, len(buildings), 3)
	})

	t.Run("CreateEquipment", func(t *testing.T) {
		// First create a building
		buildingReqBody := map[string]interface{}{
			"name":    "Equipment Test Building",
			"address": "123 Equipment Street",
		}

		buildingJsonBody, err := json.Marshal(buildingReqBody)
		require.NoError(t, err)

		buildingResp, err := suite.httpClient.Post(
			suite.server.URL+"/api/v1/buildings",
			"application/json",
			bytes.NewBuffer(buildingJsonBody),
		)
		require.NoError(t, err)
		defer buildingResp.Body.Close()

		var buildingResponse map[string]interface{}
		err = json.NewDecoder(buildingResp.Body).Decode(&buildingResponse)
		require.NoError(t, err)

		buildingID := buildingResponse["id"].(string)

		// Create equipment
		equipmentReqBody := map[string]interface{}{
			"building_id": buildingID,
			"name":        "API Test Equipment",
			"type":        "HVAC",
			"model":       "Test Model 3000",
			"location": map[string]float64{
				"x": 40.7128,
				"y": -74.0060,
				"z": 5,
			},
		}

		equipmentJsonBody, err := json.Marshal(equipmentReqBody)
		require.NoError(t, err)

		resp, err := suite.httpClient.Post(
			suite.server.URL+"/api/v1/equipment",
			"application/json",
			bytes.NewBuffer(equipmentJsonBody),
		)
		require.NoError(t, err)
		defer resp.Body.Close()

		assert.Equal(t, http.StatusCreated, resp.StatusCode)

		var response map[string]interface{}
		err = json.NewDecoder(resp.Body).Decode(&response)
		require.NoError(t, err)

		assert.NotNil(t, response["id"])
		assert.Equal(t, "API Test Equipment", response["name"])
		assert.Equal(t, "HVAC", response["type"])
		assert.Equal(t, buildingID, response["building_id"])
	})

	t.Run("ErrorHandling", func(t *testing.T) {
		// Test invalid JSON
		resp, err := suite.httpClient.Post(
			suite.server.URL+"/api/v1/buildings",
			"application/json",
			bytes.NewBufferString("invalid json"),
		)
		require.NoError(t, err)
		defer resp.Body.Close()

		assert.Equal(t, http.StatusBadRequest, resp.StatusCode)

		// Test missing required fields
		reqBody := map[string]interface{}{
			"address": "Missing Name Street",
		}

		jsonBody, err := json.Marshal(reqBody)
		require.NoError(t, err)

		resp, err = suite.httpClient.Post(
			suite.server.URL+"/api/v1/buildings",
			"application/json",
			bytes.NewBuffer(jsonBody),
		)
		require.NoError(t, err)
		defer resp.Body.Close()

		assert.Equal(t, http.StatusBadRequest, resp.StatusCode)

		// Test non-existent resource
		resp, err = suite.httpClient.Get(suite.server.URL + "/api/v1/buildings/non-existent-id")
		require.NoError(t, err)
		defer resp.Body.Close()

		assert.Equal(t, http.StatusNotFound, resp.StatusCode)
	})
}

// TestGraphQLAPI tests GraphQL API endpoints
func TestGraphQLAPI(t *testing.T) {
	suite := NewAPIIntegrationTestSuite(t)
	suite.SetupTestEnvironment(t)
	defer suite.TeardownTestEnvironment(t)

	t.Run("GraphQLQuery", func(t *testing.T) {
		// GraphQL query
		query := `
			query {
				buildings {
					id
					name
					address
					coordinates {
						x
						y
						z
					}
				}
			}
		`

		reqBody := map[string]interface{}{
			"query": query,
		}

		jsonBody, err := json.Marshal(reqBody)
		require.NoError(t, err)

		resp, err := suite.httpClient.Post(
			suite.server.URL+"/graphql",
			"application/json",
			bytes.NewBuffer(jsonBody),
		)
		require.NoError(t, err)
		defer resp.Body.Close()

		assert.Equal(t, http.StatusOK, resp.StatusCode)

		var response map[string]interface{}
		err = json.NewDecoder(resp.Body).Decode(&response)
		require.NoError(t, err)

		assert.NotNil(t, response["data"])
		data := response["data"].(map[string]interface{})
		assert.NotNil(t, data["buildings"])
	})

	t.Run("GraphQLMutation", func(t *testing.T) {
		// GraphQL mutation
		mutation := `
			mutation {
				createBuilding(input: {
					name: "GraphQL Test Building"
					address: "123 GraphQL Street"
				}) {
					id
					name
					address
				}
			}
		`

		reqBody := map[string]interface{}{
			"query": mutation,
		}

		jsonBody, err := json.Marshal(reqBody)
		require.NoError(t, err)

		resp, err := suite.httpClient.Post(
			suite.server.URL+"/graphql",
			"application/json",
			bytes.NewBuffer(jsonBody),
		)
		require.NoError(t, err)
		defer resp.Body.Close()

		assert.Equal(t, http.StatusOK, resp.StatusCode)

		var response map[string]interface{}
		err = json.NewDecoder(resp.Body).Decode(&response)
		require.NoError(t, err)

		assert.NotNil(t, response["data"])
		data := response["data"].(map[string]interface{})
		assert.NotNil(t, data["createBuilding"])
	})

	t.Run("GraphQLErrorHandling", func(t *testing.T) {
		// Invalid GraphQL query
		query := `
			query {
				buildings {
					invalidField
				}
			}
		`

		reqBody := map[string]interface{}{
			"query": query,
		}

		jsonBody, err := json.Marshal(reqBody)
		require.NoError(t, err)

		resp, err := suite.httpClient.Post(
			suite.server.URL+"/graphql",
			"application/json",
			bytes.NewBuffer(jsonBody),
		)
		require.NoError(t, err)
		defer resp.Body.Close()

		assert.Equal(t, http.StatusOK, resp.StatusCode)

		var response map[string]interface{}
		err = json.NewDecoder(resp.Body).Decode(&response)
		require.NoError(t, err)

		assert.NotNil(t, response["errors"])
	})
}

// TestWebSocketAPI tests WebSocket API
func TestWebSocketAPI(t *testing.T) {
	suite := NewAPIIntegrationTestSuite(t)
	suite.SetupTestEnvironment(t)
	defer suite.TeardownTestEnvironment(t)

	t.Run("WebSocketConnection", func(t *testing.T) {
		// Connect to WebSocket
		wsURL := "ws" + suite.server.URL[4:] + "/ws"
		conn, _, err := websocket.DefaultDialer.Dial(wsURL, nil)
		require.NoError(t, err)
		defer conn.Close()

		suite.wsConn = conn

		// Test connection by sending ping
		err = conn.WriteMessage(websocket.PingMessage, []byte("ping"))
		require.NoError(t, err)

		// Wait for pong
		_, pongData, err := conn.ReadMessage()
		require.NoError(t, err)
		assert.Equal(t, "pong", string(pongData))
	})

	t.Run("WebSocketRealTimeUpdates", func(t *testing.T) {
		// Connect to WebSocket
		wsURL := "ws" + suite.server.URL[4:] + "/ws"
		conn, _, err := websocket.DefaultDialer.Dial(wsURL, nil)
		require.NoError(t, err)
		defer conn.Close()

		// Subscribe to building updates
		subscribeMsg := map[string]interface{}{
			"type":    "subscribe",
			"channel": "buildings",
		}

		err = conn.WriteJSON(subscribeMsg)
		require.NoError(t, err)

		// Create a building via HTTP API
		reqBody := map[string]interface{}{
			"name":    "WebSocket Test Building",
			"address": "123 WebSocket Street",
		}

		jsonBody, err := json.Marshal(reqBody)
		require.NoError(t, err)

		resp, err := suite.httpClient.Post(
			suite.server.URL+"/api/v1/buildings",
			"application/json",
			bytes.NewBuffer(jsonBody),
		)
		require.NoError(t, err)
		resp.Body.Close()

		// Wait for WebSocket update
		_, messageData, err := conn.ReadMessage()
		require.NoError(t, err)

		var update map[string]interface{}
		err = json.Unmarshal(messageData, &update)
		require.NoError(t, err)

		assert.Equal(t, "building_created", update["type"])
		assert.NotNil(t, update["data"])
	})
}

// TestAuthenticationAPI tests authentication endpoints
func TestAuthenticationAPI(t *testing.T) {
	suite := NewAPIIntegrationTestSuite(t)
	suite.SetupTestEnvironment(t)
	defer suite.TeardownTestEnvironment(t)

	t.Run("UserRegistration", func(t *testing.T) {
		reqBody := map[string]interface{}{
			"email":    "test@example.com",
			"name":     "Test User",
			"password": "testpassword123",
			"role":     "user",
		}

		jsonBody, err := json.Marshal(reqBody)
		require.NoError(t, err)

		resp, err := suite.httpClient.Post(
			suite.server.URL+"/api/v1/users",
			"application/json",
			bytes.NewBuffer(jsonBody),
		)
		require.NoError(t, err)
		defer resp.Body.Close()

		assert.Equal(t, http.StatusCreated, resp.StatusCode)

		var response map[string]interface{}
		err = json.NewDecoder(resp.Body).Decode(&response)
		require.NoError(t, err)

		assert.NotNil(t, response["id"])
		assert.Equal(t, "test@example.com", response["email"])
		assert.Equal(t, "Test User", response["name"])
	})

	t.Run("UserAuthentication", func(t *testing.T) {
		// First register a user
		registerBody := map[string]interface{}{
			"email":    "auth@example.com",
			"name":     "Auth User",
			"password": "authpassword123",
			"role":     "user",
		}

		registerJsonBody, err := json.Marshal(registerBody)
		require.NoError(t, err)

		registerResp, err := suite.httpClient.Post(
			suite.server.URL+"/api/v1/users",
			"application/json",
			bytes.NewBuffer(registerJsonBody),
		)
		require.NoError(t, err)
		registerResp.Body.Close()

		// Now authenticate
		authBody := map[string]interface{}{
			"email":    "auth@example.com",
			"password": "authpassword123",
		}

		authJsonBody, err := json.Marshal(authBody)
		require.NoError(t, err)

		resp, err := suite.httpClient.Post(
			suite.server.URL+"/api/v1/auth/login",
			"application/json",
			bytes.NewBuffer(authJsonBody),
		)
		require.NoError(t, err)
		defer resp.Body.Close()

		assert.Equal(t, http.StatusOK, resp.StatusCode)

		var response map[string]interface{}
		err = json.NewDecoder(resp.Body).Decode(&response)
		require.NoError(t, err)

		assert.NotNil(t, response["token"])
		assert.NotNil(t, response["user"])
	})
}
