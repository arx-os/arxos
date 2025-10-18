/**
 * End-to-End Workflow Tests
 * Comprehensive tests for complete workflows including IFC import, BAS mapping, Git workflow, and PR approval
 */

package workflow

import (
	"bytes"
	"context"
	"encoding/json"
	"io"
	"mime/multipart"
	"net/http"
	"os"
	"path/filepath"
	"testing"
	"time"

	"github.com/arx-os/arxos/internal/app"
	"github.com/arx-os/arxos/internal/config"
	"github.com/arx-os/arxos/test/helpers"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

// E2EWorkflowTestSuite manages end-to-end workflow tests
type E2EWorkflowTestSuite struct {
	app        *app.Container
	config     *config.Config
	server     *http.Server
	httpClient *http.Client
	testDir    string
	authToken  string
}

// NewE2EWorkflowTestSuite creates a new E2E workflow test suite
func NewE2EWorkflowTestSuite(t *testing.T) *E2EWorkflowTestSuite {
	// Load test configuration
	cfg := helpers.LoadTestConfig(t)

	// Create application container
	container := app.NewContainer()
	ctx := context.Background()
	err := container.Initialize(ctx, cfg)
	if err != nil {
		t.Skipf("Cannot initialize container (database may not be available): %v", err)
		return nil
	}

	// Create test directory
	testDir := t.TempDir()

	// Create HTTP client
	httpClient := &http.Client{
		Timeout: 60 * time.Second, // Longer timeout for E2E tests
	}

	return &E2EWorkflowTestSuite{
		app:        container,
		config:     cfg,
		httpClient: httpClient,
		testDir:    testDir,
	}
}

// SetupTestEnvironment prepares the E2E test environment
func (suite *E2EWorkflowTestSuite) SetupTestEnvironment(t *testing.T) {
	// Setup authentication
	suite.setupAuthentication(t)
}

// TeardownTestEnvironment cleans up the E2E test environment
func (suite *E2EWorkflowTestSuite) TeardownTestEnvironment(t *testing.T) {
	if suite.server != nil {
		ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
		defer cancel()
		suite.server.Shutdown(ctx)
	}
}

// setupAuthentication sets up authentication for E2E tests
func (suite *E2EWorkflowTestSuite) setupAuthentication(t *testing.T) {
	// For E2E tests, we'll use a mock token
	suite.authToken = "mock-jwt-token-for-e2e-testing"
}

// makeAuthenticatedRequest makes an authenticated HTTP request
func (suite *E2EWorkflowTestSuite) makeAuthenticatedRequest(method, url string, body []byte) (*http.Response, error) {
	req, err := http.NewRequest(method, url, bytes.NewBuffer(body))
	if err != nil {
		return nil, err
	}

	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Authorization", "Bearer "+suite.authToken)

	return suite.httpClient.Do(req)
}

// TestIFCImportWorkflow tests the complete IFC import workflow
func TestIFCImportWorkflow(t *testing.T) {
	suite := NewE2EWorkflowTestSuite(t)
	if suite == nil {
		t.Skip("Test suite initialization failed")
		return
	}

	suite.SetupTestEnvironment(t)
	defer suite.TeardownTestEnvironment(t)

	t.Run("CompleteIFCImportWorkflow", func(t *testing.T) {
		// Step 1: Create a building
		buildingID := suite.createTestBuilding(t)

		// Step 2: Create a mock IFC file
		ifcFile := suite.createMockIFCFile(t)

		// Step 3: Import IFC file
		importResult := suite.importIFCFile(t, buildingID, ifcFile)

		// Step 4: Verify import results
		suite.verifyIFCImport(t, buildingID, importResult)

		// Step 5: Check extracted components
		suite.verifyExtractedComponents(t, buildingID)
	})
}

// TestBASMappingWorkflow tests the complete BAS mapping workflow
func TestBASMappingWorkflow(t *testing.T) {
	suite := NewE2EWorkflowTestSuite(t)
	if suite == nil {
		t.Skip("Test suite initialization failed")
		return
	}

	suite.SetupTestEnvironment(t)
	defer suite.TeardownTestEnvironment(t)

	t.Run("CompleteBASMappingWorkflow", func(t *testing.T) {
		// Step 1: Create a building
		buildingID := suite.createTestBuilding(t)

		// Step 2: Import BAS points
		basPoints := suite.importBASPoints(t, buildingID)

		// Step 3: Map BAS points to equipment
		suite.mapBASPointsToEquipment(t, buildingID, basPoints)

		// Step 4: Verify mapping results
		suite.verifyBASMapping(t, buildingID, basPoints)

		// Step 5: Test path-based queries
		suite.testPathBasedQueries(t, buildingID)
	})
}

// TestGitWorkflow tests the complete Git workflow
func TestGitWorkflow(t *testing.T) {
	suite := NewE2EWorkflowTestSuite(t)
	if suite == nil {
		t.Skip("Test suite initialization failed")
		return
	}

	suite.SetupTestEnvironment(t)
	defer suite.TeardownTestEnvironment(t)

	t.Run("CompleteGitWorkflow", func(t *testing.T) {
		// Step 1: Create a building
		buildingID := suite.createTestBuilding(t)

		// Step 2: Create initial commit
		initialCommit := suite.createInitialCommit(t, buildingID)

		// Step 3: Create a branch
		branchName := suite.createBranch(t, buildingID)

		// Step 4: Make changes on branch
		suite.makeChangesOnBranch(t, buildingID, branchName)

		// Step 5: Create pull request
		prID := suite.createPullRequest(t, buildingID, branchName)

		// Step 6: Review and approve PR
		suite.reviewAndApprovePR(t, prID)

		// Step 7: Merge PR
		suite.mergePullRequest(t, prID)

		// Step 8: Verify merge results
		suite.verifyMergeResults(t, buildingID, initialCommit)
	})
}

// TestPRApprovalWorkflow tests the complete PR approval workflow
func TestPRApprovalWorkflow(t *testing.T) {
	suite := NewE2EWorkflowTestSuite(t)
	if suite == nil {
		t.Skip("Test suite initialization failed")
		return
	}

	suite.SetupTestEnvironment(t)
	defer suite.TeardownTestEnvironment(t)

	t.Run("CompletePRApprovalWorkflow", func(t *testing.T) {
		// Step 1: Create a building
		buildingID := suite.createTestBuilding(t)

		// Step 2: Create a branch and make changes
		branchName := suite.createBranch(t, buildingID)
		suite.makeChangesOnBranch(t, buildingID, branchName)

		// Step 3: Create pull request
		prID := suite.createPullRequest(t, buildingID, branchName)

		// Step 4: Add reviewers
		suite.addReviewers(t, prID)

		// Step 5: Request changes
		suite.requestChanges(t, prID)

		// Step 6: Address review comments
		suite.addressReviewComments(t, buildingID, branchName)

		// Step 7: Approve PR
		suite.approvePullRequest(t, prID)

		// Step 8: Merge PR
		suite.mergePullRequest(t, prID)
	})
}

// Helper methods for E2E tests

func (suite *E2EWorkflowTestSuite) createTestBuilding(t *testing.T) string {
	reqBody := map[string]any{
		"name":          "E2E Test Building",
		"address":       "123 E2E Street",
		"city":          "Test City",
		"state":         "TS",
		"zip_code":      "12345",
		"country":       "Test Country",
		"building_type": "office",
	}

	jsonBody, err := json.Marshal(reqBody)
	require.NoError(t, err)

	resp, err := suite.makeAuthenticatedRequest("POST", "http://localhost:8080/api/v1/buildings", jsonBody)
	require.NoError(t, err)
	defer resp.Body.Close()

	assert.Equal(t, http.StatusCreated, resp.StatusCode)

	var response map[string]any
	err = json.NewDecoder(resp.Body).Decode(&response)
	require.NoError(t, err)

	buildingID := response["id"].(string)
	require.NotEmpty(t, buildingID)

	return buildingID
}

func (suite *E2EWorkflowTestSuite) createMockIFCFile(t *testing.T) string {
	// Create a mock IFC file for testing
	ifcContent := `ISO-10303-21;
HEADER;
FILE_DESCRIPTION(('ViewDefinition [CoordinationView]'),'2;1');
FILE_NAME('test.ifc','2023-01-01T00:00:00',('Test User'),('Test Organization'),'Test System','Test System','');
FILE_SCHEMA(('IFC4'));
ENDSEC;

DATA;
#1=IFCPROJECT('0K$lz2v0X8EwW3$q5H2L9M',#2,'Test Project',$,$,$,$,$,#3);
#2=IFCOWNERHISTORY(#5,#6,$,.ADDED.,$,$,$,0);
#3=IFCGEOMETRICREPRESENTATIONCONTEXT($,'Model',3,1.E-05,#4,$);
#4=IFCAXIS2PLACEMENT3D(#7,#8,#9);
#5=IFCPERSONANDORGANIZATION(#10,#11,$);
#6=IFCAPPLICATION(#12,#13,'Test Application','Test Version');
#7=IFCCARTESIANPOINT((0.,0.,0.));
#8=IFCDIRECTION((0.,0.,1.));
#9=IFCDIRECTION((1.,0.,0.));
#10=IFCPERSON('Test User',$,$,$,$,$,$,$);
#11=IFCORGANIZATION('Test Organization',$,$,$);
#12=IFCAPPLICATION($,$,'Test Application','Test Version');
#13=IFCAPPLICATION($,$,'Test Application','Test Version');
ENDSEC;

END-ISO-10303-21;`

	ifcFile := filepath.Join(suite.testDir, "test.ifc")
	err := os.WriteFile(ifcFile, []byte(ifcContent), 0644)
	require.NoError(t, err)

	return ifcFile
}

func (suite *E2EWorkflowTestSuite) importIFCFile(t *testing.T, buildingID, ifcFile string) map[string]any {
	// Create multipart form data for file upload
	var buf bytes.Buffer
	writer := multipart.NewWriter(&buf)

	// Add building ID
	err := writer.WriteField("building_id", buildingID)
	require.NoError(t, err)

	// Add file
	file, err := os.Open(ifcFile)
	require.NoError(t, err)
	defer file.Close()

	part, err := writer.CreateFormFile("file", "test.ifc")
	require.NoError(t, err)

	_, err = io.Copy(part, file)
	require.NoError(t, err)

	err = writer.Close()
	require.NoError(t, err)

	// Make request
	req, err := http.NewRequest("POST", "http://localhost:8080/api/v1/ifc/import", &buf)
	require.NoError(t, err)

	req.Header.Set("Content-Type", writer.FormDataContentType())
	req.Header.Set("Authorization", "Bearer "+suite.authToken)

	resp, err := suite.httpClient.Do(req)
	require.NoError(t, err)
	defer resp.Body.Close()

	assert.Equal(t, http.StatusOK, resp.StatusCode)

	var response map[string]any
	err = json.NewDecoder(resp.Body).Decode(&response)
	require.NoError(t, err)

	return response
}

func (suite *E2EWorkflowTestSuite) verifyIFCImport(t *testing.T, buildingID string, importResult map[string]any) {
	// Verify import was successful
	assert.Equal(t, "completed", importResult["status"])
	assert.NotNil(t, importResult["import_id"])

	// Check that components were extracted
	components := importResult["components"].([]any)
	assert.Greater(t, len(components), 0)
}

func (suite *E2EWorkflowTestSuite) verifyExtractedComponents(t *testing.T, buildingID string) {
	// Get building components
	resp, err := suite.makeAuthenticatedRequest("GET", "http://localhost:8080/api/v1/buildings/"+buildingID+"/components", nil)
	require.NoError(t, err)
	defer resp.Body.Close()

	assert.Equal(t, http.StatusOK, resp.StatusCode)

	var response map[string]any
	err = json.NewDecoder(resp.Body).Decode(&response)
	require.NoError(t, err)

	components := response["components"].([]any)
	assert.Greater(t, len(components), 0)
}

func (suite *E2EWorkflowTestSuite) importBASPoints(t *testing.T, buildingID string) []map[string]any {
	// Create mock BAS points
	basPoints := []map[string]any{
		{
			"name":      "TEMP-01",
			"path":      "/B1/F1/R1/HVAC/TEMP-01",
			"type":      "temperature",
			"data_type": "real",
			"value":     22.5,
		},
		{
			"name":      "HUMID-01",
			"path":      "/B1/F1/R1/HVAC/HUMID-01",
			"type":      "humidity",
			"data_type": "real",
			"value":     45.0,
		},
	}

	// Import BAS points
	reqBody := map[string]any{
		"building_id": buildingID,
		"points":      basPoints,
	}

	jsonBody, err := json.Marshal(reqBody)
	require.NoError(t, err)

	resp, err := suite.makeAuthenticatedRequest("POST", "http://localhost:8080/api/v1/bas/import", jsonBody)
	require.NoError(t, err)
	defer resp.Body.Close()

	assert.Equal(t, http.StatusOK, resp.StatusCode)

	var response map[string]any
	err = json.NewDecoder(resp.Body).Decode(&response)
	require.NoError(t, err)

	return basPoints
}

func (suite *E2EWorkflowTestSuite) mapBASPointsToEquipment(t *testing.T, buildingID string, basPoints []map[string]any) {
	// Map BAS points to equipment
	for _, point := range basPoints {
		reqBody := map[string]any{
			"equipment_path": "/B1/F1/R1/HVAC/EQUIP-01",
			"point_id":       point["name"],
		}

		jsonBody, err := json.Marshal(reqBody)
		require.NoError(t, err)

		resp, err := suite.makeAuthenticatedRequest("POST", "http://localhost:8080/api/v1/bas/points/"+point["name"].(string)+"/map", jsonBody)
		require.NoError(t, err)
		resp.Body.Close()

		assert.Equal(t, http.StatusOK, resp.StatusCode)
	}
}

func (suite *E2EWorkflowTestSuite) verifyBASMapping(t *testing.T, buildingID string, basPoints []map[string]any) {
	// Verify BAS points are mapped
	for _, point := range basPoints {
		resp, err := suite.makeAuthenticatedRequest("GET", "http://localhost:8080/api/v1/bas/points/"+point["name"].(string), nil)
		require.NoError(t, err)
		defer resp.Body.Close()

		assert.Equal(t, http.StatusOK, resp.StatusCode)

		var response map[string]any
		err = json.NewDecoder(resp.Body).Decode(&response)
		require.NoError(t, err)

		assert.NotNil(t, response["equipment_id"])
	}
}

func (suite *E2EWorkflowTestSuite) testPathBasedQueries(t *testing.T, buildingID string) {
	// Test exact path query
	resp, err := suite.makeAuthenticatedRequest("GET", "http://localhost:8080/api/v1/equipment/path/B1/F1/R1/HVAC/EQUIP-01", nil)
	require.NoError(t, err)
	defer resp.Body.Close()

	// Should return 200 or 404
	assert.True(t, resp.StatusCode == http.StatusOK || resp.StatusCode == http.StatusNotFound)

	// Test pattern query
	resp, err = suite.makeAuthenticatedRequest("GET", "http://localhost:8080/api/v1/equipment/path-pattern?pattern=/B1/F1/*/HVAC/*", nil)
	require.NoError(t, err)
	defer resp.Body.Close()

	assert.Equal(t, http.StatusOK, resp.StatusCode)
}

func (suite *E2EWorkflowTestSuite) createInitialCommit(t *testing.T, buildingID string) string {
	// Create initial commit
	reqBody := map[string]any{
		"building_id": buildingID,
		"message":     "Initial commit",
		"changes":     []string{"building_created"},
	}

	jsonBody, err := json.Marshal(reqBody)
	require.NoError(t, err)

	resp, err := suite.makeAuthenticatedRequest("POST", "http://localhost:8080/api/v1/vc/commit", jsonBody)
	require.NoError(t, err)
	defer resp.Body.Close()

	assert.Equal(t, http.StatusOK, resp.StatusCode)

	var response map[string]any
	err = json.NewDecoder(resp.Body).Decode(&response)
	require.NoError(t, err)

	commitID := response["commit_id"].(string)
	require.NotEmpty(t, commitID)

	return commitID
}

func (suite *E2EWorkflowTestSuite) createBranch(t *testing.T, buildingID string) string {
	// Create a branch
	branchName := "feature/test-changes"
	reqBody := map[string]any{
		"building_id": buildingID,
		"branch_name": branchName,
		"base_branch": "main",
	}

	jsonBody, err := json.Marshal(reqBody)
	require.NoError(t, err)

	resp, err := suite.makeAuthenticatedRequest("POST", "http://localhost:8080/api/v1/vc/branch", jsonBody)
	require.NoError(t, err)
	defer resp.Body.Close()

	assert.Equal(t, http.StatusOK, resp.StatusCode)

	return branchName
}

func (suite *E2EWorkflowTestSuite) makeChangesOnBranch(t *testing.T, buildingID, branchName string) {
	// Make changes on the branch (e.g., add equipment)
	reqBody := map[string]any{
		"building_id": buildingID,
		"name":        "Branch Test Equipment",
		"type":        "HVAC",
		"model":       "Branch Model 3000",
	}

	jsonBody, err := json.Marshal(reqBody)
	require.NoError(t, err)

	resp, err := suite.makeAuthenticatedRequest("POST", "http://localhost:8080/api/v1/equipment", jsonBody)
	require.NoError(t, err)
	defer resp.Body.Close()

	assert.Equal(t, http.StatusCreated, resp.StatusCode)
}

func (suite *E2EWorkflowTestSuite) createPullRequest(t *testing.T, buildingID, branchName string) string {
	// Create pull request
	reqBody := map[string]any{
		"building_id":   buildingID,
		"title":         "Test Pull Request",
		"description":   "Test PR for E2E workflow",
		"source_branch": branchName,
		"target_branch": "main",
	}

	jsonBody, err := json.Marshal(reqBody)
	require.NoError(t, err)

	resp, err := suite.makeAuthenticatedRequest("POST", "http://localhost:8080/api/v1/pr", jsonBody)
	require.NoError(t, err)
	defer resp.Body.Close()

	assert.Equal(t, http.StatusCreated, resp.StatusCode)

	var response map[string]any
	err = json.NewDecoder(resp.Body).Decode(&response)
	require.NoError(t, err)

	prID := response["id"].(string)
	require.NotEmpty(t, prID)

	return prID
}

func (suite *E2EWorkflowTestSuite) reviewAndApprovePR(t *testing.T, prID string) {
	// Approve pull request
	reqBody := map[string]any{
		"action":  "approve",
		"comment": "Looks good!",
	}

	jsonBody, err := json.Marshal(reqBody)
	require.NoError(t, err)

	resp, err := suite.makeAuthenticatedRequest("POST", "http://localhost:8080/api/v1/pr/"+prID+"/review", jsonBody)
	require.NoError(t, err)
	defer resp.Body.Close()

	assert.Equal(t, http.StatusOK, resp.StatusCode)
}

func (suite *E2EWorkflowTestSuite) mergePullRequest(t *testing.T, prID string) {
	// Merge pull request
	reqBody := map[string]any{
		"merge_message": "Merge test PR",
	}

	jsonBody, err := json.Marshal(reqBody)
	require.NoError(t, err)

	resp, err := suite.makeAuthenticatedRequest("POST", "http://localhost:8080/api/v1/pr/"+prID+"/merge", jsonBody)
	require.NoError(t, err)
	defer resp.Body.Close()

	assert.Equal(t, http.StatusOK, resp.StatusCode)
}

func (suite *E2EWorkflowTestSuite) verifyMergeResults(t *testing.T, buildingID, initialCommit string) {
	// Verify merge results
	resp, err := suite.makeAuthenticatedRequest("GET", "http://localhost:8080/api/v1/vc/"+buildingID+"/commits", nil)
	require.NoError(t, err)
	defer resp.Body.Close()

	assert.Equal(t, http.StatusOK, resp.StatusCode)

	var response map[string]any
	err = json.NewDecoder(resp.Body).Decode(&response)
	require.NoError(t, err)

	commits := response["commits"].([]any)
	assert.Greater(t, len(commits), 1) // Should have more than initial commit
}

func (suite *E2EWorkflowTestSuite) addReviewers(t *testing.T, prID string) {
	// Add reviewers to PR
	reqBody := map[string]any{
		"reviewers": []string{"reviewer1@example.com", "reviewer2@example.com"},
	}

	jsonBody, err := json.Marshal(reqBody)
	require.NoError(t, err)

	resp, err := suite.makeAuthenticatedRequest("POST", "http://localhost:8080/api/v1/pr/"+prID+"/reviewers", jsonBody)
	require.NoError(t, err)
	defer resp.Body.Close()

	assert.Equal(t, http.StatusOK, resp.StatusCode)
}

func (suite *E2EWorkflowTestSuite) requestChanges(t *testing.T, prID string) {
	// Request changes on PR
	reqBody := map[string]any{
		"action":  "request_changes",
		"comment": "Please fix the equipment naming convention",
	}

	jsonBody, err := json.Marshal(reqBody)
	require.NoError(t, err)

	resp, err := suite.makeAuthenticatedRequest("POST", "http://localhost:8080/api/v1/pr/"+prID+"/review", jsonBody)
	require.NoError(t, err)
	defer resp.Body.Close()

	assert.Equal(t, http.StatusOK, resp.StatusCode)
}

func (suite *E2EWorkflowTestSuite) addressReviewComments(t *testing.T, buildingID, branchName string) {
	// Address review comments by making additional changes
	reqBody := map[string]any{
		"building_id": buildingID,
		"name":        "Updated Branch Test Equipment",
		"type":        "HVAC",
		"model":       "Updated Branch Model 3000",
	}

	jsonBody, err := json.Marshal(reqBody)
	require.NoError(t, err)

	resp, err := suite.makeAuthenticatedRequest("POST", "http://localhost:8080/api/v1/equipment", jsonBody)
	require.NoError(t, err)
	defer resp.Body.Close()

	assert.Equal(t, http.StatusCreated, resp.StatusCode)
}

func (suite *E2EWorkflowTestSuite) approvePullRequest(t *testing.T, prID string) {
	// Approve pull request after changes
	reqBody := map[string]any{
		"action":  "approve",
		"comment": "Changes look good, approved!",
	}

	jsonBody, err := json.Marshal(reqBody)
	require.NoError(t, err)

	resp, err := suite.makeAuthenticatedRequest("POST", "http://localhost:8080/api/v1/pr/"+prID+"/review", jsonBody)
	require.NoError(t, err)
	defer resp.Body.Close()

	assert.Equal(t, http.StatusOK, resp.StatusCode)
}
