package cgo

/*
#cgo CFLAGS: -I../c
#cgo LDFLAGS: -L../c/lib -larxos -lpthread -lm
#include "bridge.h"
#include "database/arx_database.h"
#include <stdlib.h>
*/
import "C"
import (
	"fmt"
	"time"
	"unsafe"
)

// ============================================================================
// ERROR HANDLING
// ============================================================================

// ArxosError represents an error from the C core
type ArxosError struct {
	Message string
}

func (e *ArxosError) Error() string {
	return e.Message
}

// getLastError retrieves the last error from C functions
func getLastError() error {
	cError := C.cgo_get_last_error()
	if cError == nil {
		return nil
	}
	defer C.cgo_free_string(cError)
	return &ArxosError{Message: C.GoString(cError)}
}

// clearError clears the last error
func clearError() {
	C.cgo_clear_last_error()
}

// ============================================================================
// ARXOBJECT WRAPPER
// ============================================================================

// ArxObjectType represents the type of building element
type ArxObjectType int

// ArxObject represents a building element from the C core
type ArxObject struct {
	ptr unsafe.Pointer
}

// CreateArxObject creates a new ArxObject
func CreateArxObject(id, name, description string, objectType ArxObjectType) (*ArxObject, error) {
	cID := C.CString(id)
	defer C.free(unsafe.Pointer(cID))

	cName := C.CString(name)
	defer C.free(unsafe.Pointer(cName))

	var cDesc *C.char
	if description != "" {
		cDesc = C.CString(description)
		defer C.free(unsafe.Pointer(cDesc))
	}

	cObj := C.cgo_arx_object_create(cID, C.int(objectType), cName, cDesc)
	if cObj == nil {
		return nil, getLastError()
	}

	return &ArxObject{ptr: unsafe.Pointer(cObj)}, nil
}

// Destroy frees the ArxObject
func (obj *ArxObject) Destroy() {
	if obj.ptr != nil {
		C.cgo_arx_object_destroy((*C.ArxObject)(obj.ptr))
		obj.ptr = nil
	}
}

// SetProperty sets a property on the ArxObject
func (obj *ArxObject) SetProperty(key, value string) error {
	if obj.ptr == nil {
		return fmt.Errorf("ArxObject is nil")
	}

	cKey := C.CString(key)
	defer C.free(unsafe.Pointer(cKey))

	cValue := C.CString(value)
	defer C.free(unsafe.Pointer(cValue))

	success := C.cgo_arx_object_set_property((*C.ArxObject)(obj.ptr), cKey, cValue)
	if !success {
		return getLastError()
	}

	return nil
}

// GetProperty retrieves a property from the ArxObject
func (obj *ArxObject) GetProperty(key string) (string, error) {
	if obj.ptr == nil {
		return "", fmt.Errorf("ArxObject is nil")
	}

	cKey := C.CString(key)
	defer C.free(unsafe.Pointer(cKey))

	cValue := C.cgo_arx_object_get_property((*C.ArxObject)(obj.ptr), cKey)
	if cValue == nil {
		return "", getLastError()
	}
	defer C.cgo_free_string(cValue)

	return C.GoString(cValue), nil
}

// ============================================================================
// ASCII ENGINE WRAPPER
// ============================================================================

// Generate2DFloorPlan generates a 2D ASCII floor plan
func Generate2DFloorPlan(objects []*ArxObject, width, height int, scale float64) (string, error) {
	if len(objects) == 0 {
		return "", fmt.Errorf("no objects provided")
	}

	// Convert Go slice to C array
	cObjects := make([]*C.ArxObject, len(objects))
	for i, obj := range objects {
		if obj.ptr == nil {
			return "", fmt.Errorf("ArxObject at index %d is nil", i)
		}
		cObjects[i] = (*C.ArxObject)(obj.ptr)
	}

	cResult := C.cgo_generate_2d_floor_plan(&cObjects[0], C.int(len(objects)),
		C.int(width), C.int(height), C.double(scale))
	if cResult == nil {
		return "", getLastError()
	}
	defer C.cgo_free_string(cResult)

	return C.GoString(cResult), nil
}

// Generate3DBuildingView generates a 3D ASCII building view
func Generate3DBuildingView(objects []*ArxObject, width, height, depth int, scale float64) (string, error) {
	if len(objects) == 0 {
		return "", fmt.Errorf("no objects provided")
	}

	// Convert Go slice to C array
	cObjects := make([]*C.ArxObject, len(objects))
	for i, obj := range objects {
		if obj.ptr == nil {
			return "", fmt.Errorf("ArxObject at index %d is nil", i)
		}
		cObjects[i] = (*C.ArxObject)(obj.ptr)
	}

	cResult := C.cgo_generate_3d_building_view(&cObjects[0], C.int(len(objects)),
		C.int(width), C.int(height), C.int(depth), C.double(scale))
	if cResult == nil {
		return "", getLastError()
	}
	defer C.cgo_free_string(cResult)

	return C.GoString(cResult), nil
}

// ============================================================================
// BUILDING MANAGEMENT WRAPPER
// ============================================================================

// ArxBuilding represents a building from the C core
type ArxBuilding struct {
	ptr unsafe.Pointer
}

// CreateArxBuilding creates a new ArxBuilding
func CreateArxBuilding(name, description string) (*ArxBuilding, error) {
	cName := C.CString(name)
	defer C.free(unsafe.Pointer(cName))

	var cDesc *C.char
	if description != "" {
		cDesc = C.CString(description)
		defer C.free(unsafe.Pointer(cDesc))
	}

	cBuilding := C.cgo_arx_building_create(cName, cDesc)
	if cBuilding == nil {
		return nil, getLastError()
	}

	return &ArxBuilding{ptr: unsafe.Pointer(cBuilding)}, nil
}

// Destroy frees the ArxBuilding
func (building *ArxBuilding) Destroy() {
	if building.ptr != nil {
		C.cgo_arx_building_destroy((*C.ArxBuilding)(building.ptr))
		building.ptr = nil
	}
}

// AddObject adds an ArxObject to the building
func (building *ArxBuilding) AddObject(obj *ArxObject) error {
	if building.ptr == nil {
		return fmt.Errorf("ArxBuilding is nil")
	}
	if obj.ptr == nil {
		return fmt.Errorf("ArxObject is nil")
	}

	success := C.cgo_arx_building_add_object((*C.ArxBuilding)(building.ptr), (*C.ArxObject)(obj.ptr))
	if !success {
		return getLastError()
	}

	return nil
}

// GetSummary returns a summary of the building
func (building *ArxBuilding) GetSummary() (string, error) {
	if building.ptr == nil {
		return "", fmt.Errorf("ArxBuilding is nil")
	}

	cResult := C.cgo_arx_building_get_summary((*C.ArxBuilding)(building.ptr))
	if cResult == nil {
		return "", getLastError()
	}
	defer C.cgo_free_string(cResult)

	return C.GoString(cResult), nil
}

// ============================================================================
// VERSION CONTROL WRAPPER
// ============================================================================

// ArxVersionControl represents version control from the C core
type ArxVersionControl struct {
	ptr unsafe.Pointer
}

// InitRepo initializes a new version control repository
func InitRepo(repoPath, authorName, authorEmail string) (*ArxVersionControl, error) {
	cRepoPath := C.CString(repoPath)
	defer C.free(unsafe.Pointer(cRepoPath))

	cAuthorName := C.CString(authorName)
	defer C.free(unsafe.Pointer(cAuthorName))

	cAuthorEmail := C.CString(authorEmail)
	defer C.free(unsafe.Pointer(cAuthorEmail))

	cVC := C.cgo_arx_version_init_repo(cRepoPath, cAuthorName, cAuthorEmail)
	if cVC == nil {
		return nil, getLastError()
	}

	return &ArxVersionControl{ptr: unsafe.Pointer(cVC)}, nil
}

// Destroy frees the ArxVersionControl
func (vc *ArxVersionControl) Destroy() {
	if vc.ptr != nil {
		// TODO: Implement close_repo function
		vc.ptr = nil
	}
}

// Commit creates a new commit
func (vc *ArxVersionControl) Commit(message, author, email string) (string, error) {
	if vc.ptr == nil {
		return "", fmt.Errorf("ArxVersionControl is nil")
	}

	cMessage := C.CString(message)
	defer C.free(unsafe.Pointer(cMessage))

	var cAuthor, cEmail *C.char
	if author != "" {
		cAuthor = C.CString(author)
		defer C.free(unsafe.Pointer(cAuthor))
	}
	if email != "" {
		cEmail = C.CString(email)
		defer C.free(unsafe.Pointer(cEmail))
	}

	cResult := C.cgo_arx_version_commit((*C.ArxVersionControl)(vc.ptr), cMessage, cAuthor, cEmail)
	if cResult == nil {
		return "", getLastError()
	}
	defer C.cgo_free_string(cResult)

	return C.GoString(cResult), nil
}

// GetHistory returns commit history
func (vc *ArxVersionControl) GetHistory(maxCommits int) (string, error) {
	if vc.ptr == nil {
		return "", fmt.Errorf("ArxVersionControl is nil")
	}

	cResult := C.cgo_arx_version_get_history((*C.ArxVersionControl)(vc.ptr), C.int(maxCommits))
	if cResult == nil {
		return "", getLastError()
	}
	defer C.cgo_free_string(cResult)

	return C.GoString(cResult), nil
}

// ============================================================================
// SPATIAL INDEXING WRAPPER
// ============================================================================

// QueryType represents the type of spatial query
type QueryType int

const (
	QueryTypeRange     QueryType = 0
	QueryTypePoint     QueryType = 1
	QueryTypeNearest   QueryType = 2
	QueryTypeIntersect QueryType = 3
)

// ArxSpatialIndex represents a spatial index from the C core
type ArxSpatialIndex struct {
	ptr unsafe.Pointer
}

// CreateSpatialIndex creates a new spatial index
func CreateSpatialIndex(maxDepth int, useOctree bool) (*ArxSpatialIndex, error) {
	cIndex := C.cgo_arx_spatial_create_index(C.int(maxDepth), C.bool(useOctree))
	if cIndex == nil {
		return nil, getLastError()
	}

	return &ArxSpatialIndex{ptr: unsafe.Pointer(cIndex)}, nil
}

// Destroy frees the ArxSpatialIndex
func (index *ArxSpatialIndex) Destroy() {
	if index.ptr != nil {
		// TODO: Implement destroy_index function
		index.ptr = nil
	}
}

// AddObject adds an ArxObject to the spatial index
func (index *ArxSpatialIndex) AddObject(obj *ArxObject) error {
	if index.ptr == nil {
		return fmt.Errorf("ArxSpatialIndex is nil")
	}
	if obj.ptr == nil {
		return fmt.Errorf("ArxObject is nil")
	}

	success := C.cgo_arx_spatial_add_object((*C.ArxSpatialIndex)(index.ptr), (*C.ArxObject)(obj.ptr))
	if !success {
		return getLastError()
	}

	return nil
}

// Query performs a spatial query
func (index *ArxSpatialIndex) Query(queryType QueryType, x, y, z, x2, y2, z2, radius float64, maxResults int) ([]*ArxObject, error) {
	if index.ptr == nil {
		return nil, fmt.Errorf("ArxSpatialIndex is nil")
	}

	var resultCount C.int
	cResults := C.cgo_arx_spatial_query((*C.ArxSpatialIndex)(index.ptr), C.int(queryType),
		C.double(x), C.double(y), C.double(z),
		C.double(x2), C.double(y2), C.double(z2),
		C.double(radius), C.int(maxResults), &resultCount)

	if cResults == nil {
		return nil, getLastError()
	}
	defer C.cgo_free_object_array(cResults, resultCount)

	// Convert C array to Go slice
	results := make([]*ArxObject, int(resultCount))
	for i := 0; i < int(resultCount); i++ {
		cObj := (*C.ArxObject)(*(**C.ArxObject)(unsafe.Pointer(uintptr(unsafe.Pointer(cResults)) + uintptr(i)*unsafe.Sizeof(cResults))))
		results[i] = &ArxObject{ptr: unsafe.Pointer(cObj)}
	}

	return results, nil
}

// GetStatistics returns spatial index statistics
func (index *ArxSpatialIndex) GetStatistics() (string, error) {
	if index.ptr == nil {
		return "", fmt.Errorf("ArxSpatialIndex is nil")
	}

	cResult := C.cgo_arx_spatial_get_statistics((*C.ArxSpatialIndex)(index.ptr))
	if cResult == nil {
		return "", getLastError()
	}
	defer C.cgo_free_string(cResult)

	return C.GoString(cResult), nil
}

// ============================================================================
// AUTHENTICATION WRAPPER
// ============================================================================

// IsHealthy checks if the CGO bridge is healthy
func IsHealthy() bool {
	return bool(C.cgo_arx_auth_is_healthy())
}

// InitAuth initializes the authentication system
func InitAuth(options *ArxAuthOptions) bool {
	if options == nil {
		return bool(C.cgo_arx_auth_init(nil))
	}

	cOptions := options.toCArxAuthOptions()
	if cOptions == nil {
		return false
	}
	defer C.free(cOptions)

	return bool(C.cgo_arx_auth_init(cOptions))
}

// CleanupAuth cleans up the authentication system
func CleanupAuth() {
	C.cgo_arx_auth_cleanup()
}

// CreateJWT creates a new JWT token
func CreateJWT(claims *ArxJWTClaims, secret string) *ArxJWTToken {
	if claims == nil || secret == "" {
		return nil
	}

	cClaims := claims.toCArxJWTClaims()
	if cClaims == nil {
		return nil
	}
	defer C.free(cClaims)

	cSecret := C.CString(secret)
	defer C.free(unsafe.Pointer(cSecret))

	cToken := C.cgo_arx_auth_create_jwt(cClaims, cSecret)
	if cToken == nil {
		return nil
	}

	return fromCArxJWTToken(cToken)
}

// ParseJWT parses a JWT token
func ParseJWT(tokenString, secret string) *ArxJWTToken {
	if tokenString == "" || secret == "" {
		return nil
	}

	cTokenString := C.CString(tokenString)
	defer C.free(unsafe.Pointer(cTokenString))

	cSecret := C.CString(secret)
	defer C.free(unsafe.Pointer(cSecret))

	cToken := C.cgo_arx_auth_parse_jwt(cTokenString, cSecret)
	if cToken == nil {
		return nil
	}

	return fromCArxJWTToken(cToken)
}

// VerifyJWT verifies a JWT token
func VerifyJWT(token *ArxJWTToken, secret string) bool {
	if token == nil || secret == "" {
		return false
	}

	cSecret := C.CString(secret)
	defer C.free(unsafe.Pointer(cSecret))

	// Convert token back to C structure for verification
	cToken := token.toCArxJWTToken()
	if cToken == nil {
		return nil
	}

	return bool(C.cgo_arx_auth_verify_jwt(cToken, cSecret))
}

// DestroyJWT destroys a JWT token
func DestroyJWT(token *ArxJWTToken) {
	if token == nil {
		return
	}

	// Convert token back to C structure for destruction
	cToken := token.toCArxJWTToken()
	if cToken == nil {
		return
	}

	C.cgo_arx_auth_destroy_jwt(cToken)
}

// HashPassword hashes a password
func HashPassword(password string, cost int) string {
	if password == "" {
		return ""
	}

	cPassword := C.CString(password)
	defer C.free(unsafe.Pointer(cPassword))

	cHash := C.cgo_arx_auth_hash_password(cPassword, C.int(cost))
	if cHash == nil {
		return ""
	}
	defer C.cgo_free_string(cHash)

	return C.GoString(cHash)
}

// VerifyPassword verifies a password
func VerifyPassword(password, hash string) bool {
	if password == "" || hash == "" {
		return false
	}

	cPassword := C.CString(password)
	defer C.free(unsafe.Pointer(cPassword))

	cHash := C.CString(hash)
	defer C.free(unsafe.Pointer(cHash))

	return bool(C.cgo_arx_auth_verify_password(cPassword, cHash))
}

// GeneratePassword generates a secure password
func GeneratePassword(length int, includeSymbols bool) string {
	if length <= 0 {
		return ""
	}

	cPassword := C.cgo_arx_auth_generate_password(C.int(length), C.bool(includeSymbols))
	if cPassword == nil {
		return ""
	}
	defer C.cgo_free_string(cPassword)

	return C.GoString(cPassword)
}

// CreateUser creates a new user
func CreateUser(username, email, password string, isAdmin bool) *ArxUser {
	if username == "" || email == "" || password == "" {
		return nil
	}

	cUsername := C.CString(username)
	defer C.free(unsafe.Pointer(cUsername))

	cEmail := C.CString(email)
	defer C.free(unsafe.Pointer(cEmail))

	cPassword := C.CString(password)
	defer C.free(unsafe.Pointer(cPassword))

	cUser := C.cgo_arx_auth_create_user(cUsername, cEmail, cPassword, C.bool(isAdmin))
	if cUser == nil {
		return nil
	}

	return fromCArxUser(cUser)
}

// AuthenticateUser authenticates a user
func AuthenticateUser(username, password string) *ArxAuthResult {
	if username == "" || password == "" {
		return nil
	}

	cUsername := C.CString(username)
	defer C.free(unsafe.Pointer(cUsername))

	cPassword := C.CString(password)
	defer C.free(unsafe.Pointer(cPassword))

	cResult := C.cgo_arx_auth_authenticate_user(cUsername, cPassword)
	if cResult == nil {
		return nil
	}

	return fromCArxAuthResult(cResult)
}

// GetUser gets a user by ID
func GetUser(userID uint32) *ArxUser {
	if userID == 0 {
		return nil
	}

	cUser := C.cgo_arx_auth_get_user(C.uint32_t(userID))
	if cUser == nil {
		return nil
	}

	return fromCArxUser(cUser)
}

// GetUserByUsername gets a user by username
func GetUserByUsername(username string) *ArxUser {
	if username == "" {
		return nil
	}

	cUsername := C.CString(username)
	defer C.free(unsafe.Pointer(cUsername))

	cUser := C.cgo_arx_auth_get_user_by_username(cUsername)
	if cUser == nil {
		return nil
	}

	return fromCArxUser(cUser)
}

// UpdatePassword updates a user's password
func UpdatePassword(userID uint32, oldPassword, newPassword string) bool {
	if oldPassword == "" || newPassword == "" {
		return false
	}

	cOldPassword := C.CString(oldPassword)
	defer C.free(unsafe.Pointer(cOldPassword))

	cNewPassword := C.CString(newPassword)
	defer C.free(unsafe.Pointer(cNewPassword))

	return bool(C.cgo_arx_auth_update_password(C.uint32_t(userID), cOldPassword, cNewPassword))
}

// DestroyUser destroys a user
func DestroyUser(user *ArxUser) {
	if user == nil {
		return
	}

	// Convert user back to C structure for destruction
	cUser := user.toCArxUser()
	if cUser == nil {
		return
	}

	C.cgo_arx_auth_destroy_user(cUser)
}

// GenerateRefreshToken generates a refresh token
func GenerateRefreshToken(userID uint32, userAgent, ipAddress string) string {
	if userAgent == "" || ipAddress == "" {
		return ""
	}

	cUserAgent := C.CString(userAgent)
	defer C.free(unsafe.Pointer(cUserAgent))

	cIPAddress := C.CString(ipAddress)
	defer C.free(unsafe.Pointer(cIPAddress))

	cToken := C.cgo_arx_auth_generate_refresh_token(C.uint32_t(userID), cUserAgent, cIPAddress)
	if cToken == nil {
		return ""
	}
	defer C.cgo_free_string(cToken)

	return C.GoString(cToken)
}

// ValidateRefreshToken validates a refresh token
func ValidateRefreshToken(token string) uint32 {
	if token == "" {
		return 0
	}

	cToken := C.CString(token)
	defer C.free(unsafe.Pointer(cToken))

	return uint32(C.cgo_arx_auth_validate_refresh_token(cToken))
}

// RevokeRefreshToken revokes a refresh token
func RevokeRefreshToken(token, reason string) bool {
	if token == "" || reason == "" {
		return false
	}

	cToken := C.CString(token)
	defer C.free(unsafe.Pointer(cToken))

	cReason := C.CString(reason)
	defer C.free(unsafe.Pointer(cReason))

	return bool(C.cgo_arx_auth_revoke_refresh_token(cToken, cReason))
}

// CleanupRefreshTokens cleans up expired refresh tokens
func CleanupRefreshTokens() int {
	return int(C.cgo_arx_auth_cleanup_refresh_tokens())
}

// Generate2FASecret generates a 2FA secret
func Generate2FASecret(userID uint32) string {
	cSecret := C.cgo_arx_auth_generate_2fa_secret(C.uint32_t(userID))
	if cSecret == nil {
		return ""
	}
	defer C.cgo_free_string(cSecret)

	return C.GoString(cSecret)
}

// Verify2FAToken verifies a 2FA token
func Verify2FAToken(userID uint32, token string) bool {
	if token == "" {
		return false
	}

	cToken := C.CString(token)
	defer C.free(unsafe.Pointer(cToken))

	return bool(C.cgo_arx_auth_verify_2fa_token(C.uint32_t(userID), cToken))
}

// Enable2FA enables 2FA for a user
func Enable2FA(userID uint32) bool {
	return bool(C.cgo_arx_auth_enable_2fa(C.uint32_t(userID)))
}

// Disable2FA disables 2FA for a user
func Disable2FA(userID uint32) bool {
	return bool(C.cgo_arx_auth_disable_2fa(C.uint32_t(userID)))
}

// GenerateSecureToken generates a secure token
func GenerateSecureToken(length int) string {
	if length <= 0 {
		return ""
	}

	cToken := C.cgo_arx_auth_generate_secure_token(C.int(length))
	if cToken == nil {
		return ""
	}
	defer C.cgo_free_string(cToken)

	return C.GoString(cToken)
}

// GetAuthStatistics gets authentication statistics
func GetAuthStatistics() string {
	cStats := C.cgo_arx_auth_get_statistics()
	if cStats == nil {
		return ""
	}
	defer C.cgo_free_string(cStats)

	return C.GoString(cStats)
}

// IsAuthHealthy checks if the authentication system is healthy
func IsAuthHealthy() bool {
	return bool(C.cgo_arx_auth_is_healthy())
}

// ============================================================================
// DATABASE WRAPPER
// ============================================================================

// InitDatabase initializes the database system
func InitDatabase(config *ArxDatabaseConfig) bool {
	if config == nil {
		return false
	}

	// Convert Go config to C config
	cConfig := convertGoDatabaseConfigToC(config)
	if cConfig == nil {
		return false
	}
	defer C.free(unsafe.Pointer(cConfig))

	// Call the CGO bridge
	return bool(C.cgo_arx_database_init(unsafe.Pointer(cConfig)))
}

// CleanupDatabase cleans up the database system
func CleanupDatabase() {
	C.cgo_arx_database_cleanup()
}

// IsDatabaseConnected checks if the database is connected
func IsDatabaseConnected() bool {
	return bool(C.cgo_arx_database_is_connected())
}

// TestDatabaseConnection tests database connectivity
func TestDatabaseConnection() bool {
	return bool(C.cgo_arx_database_test_connection())
}

// GetDatabasePoolStats gets connection pool statistics
func GetDatabasePoolStats() *ArxConnectionPoolStats {
	cStats := C.cgo_arx_database_get_pool_stats()
	if cStats == nil {
		return nil
	}

	// Convert C stats to Go stats
	return convertCDatabasePoolStatsToGo(cStats)
}

// ResetDatabasePoolStats resets connection pool statistics
func ResetDatabasePoolStats() {
	C.cgo_arx_database_reset_pool_stats()
}

// ConfigureDatabasePool configures the connection pool
func ConfigureDatabasePool(maxOpen, maxIdle, lifetime, idleTimeout int) bool {
	return bool(C.cgo_arx_database_configure_pool(C.int(maxOpen), C.int(maxIdle), C.int(lifetime), C.int(idleTimeout)))
}

// BeginTransaction begins a new database transaction
func BeginTransaction(description string) uint64 {
	cDesc := C.CString(description)
	defer C.free(unsafe.Pointer(cDesc))

	return uint64(C.cgo_arx_database_begin_transaction(cDesc))
}

// CommitTransaction commits a transaction
func CommitTransaction(transactionID uint64) bool {
	return bool(C.cgo_arx_database_commit_transaction(C.uint64_t(transactionID)))
}

// RollbackTransaction rollbacks a transaction
func RollbackTransaction(transactionID uint64) bool {
	return bool(C.cgo_arx_database_rollback_transaction(C.uint64_t(transactionID)))
}

// GetTransaction gets transaction information
func GetTransaction(transactionID uint64) *ArxTransaction {
	cTx := C.cgo_arx_database_get_transaction(C.uint64_t(transactionID))
	if cTx == nil {
		return nil
	}

	// Convert C transaction to Go transaction
	return convertCDatabaseTransactionToGo(cTx)
}

// ExecuteQuery executes a database query with parameters
func ExecuteQuery(query string, params []string) *ArxQueryResult {
	cQuery := C.CString(query)
	defer C.free(unsafe.Pointer(cQuery))

	var cParams **C.char
	if len(params) > 0 {
		// Allocate array of C strings
		cParams = (**C.char)(C.malloc(C.size_t(len(params)) * C.size_t(unsafe.Sizeof((*C.char)(nil)))))
		defer C.free(unsafe.Pointer(cParams))

		// Convert Go string slice to C string array
		for i, param := range params {
			cParam := C.CString(param)
			// Store pointer to C string in array
			*(**C.char)(unsafe.Pointer(uintptr(unsafe.Pointer(cParams)) + uintptr(i)*unsafe.Sizeof((*C.char)(nil)))) = cParam
			defer C.free(unsafe.Pointer(cParam))
		}
	}

	cResult := C.cgo_arx_database_execute_query(cQuery, cParams, C.int(len(params)))
	if cResult == nil {
		return nil
	}

	// Convert C result to Go result
	return convertCDatabaseQueryResultToGo(cResult)
}

// ExecuteSimpleQuery executes a query without parameters
func ExecuteSimpleQuery(query string) *ArxQueryResult {
	cQuery := C.CString(query)
	defer C.free(unsafe.Pointer(cQuery))

	cResult := C.cgo_arx_database_execute_simple_query(cQuery)
	if cResult == nil {
		return nil
	}

	// Convert C result to Go result
	return convertCDatabaseQueryResultToGo(cResult)
}

// ExecutePrepared executes a prepared statement
func ExecutePrepared(statementName string, params []string) *ArxQueryResult {
	cStatementName := C.CString(statementName)
	defer C.free(unsafe.Pointer(cStatementName))

	var cParams **C.char
	if len(params) > 0 {
		// Allocate array of C strings
		cParams = (**C.char)(C.malloc(C.size_t(len(params)) * C.size_t(unsafe.Sizeof((*C.char)(nil)))))
		defer C.free(unsafe.Pointer(cParams))

		// Convert Go string slice to C string array
		for i, param := range params {
			cParam := C.CString(param)
			// Store pointer to C string in array
			*(**C.char)(unsafe.Pointer(uintptr(unsafe.Pointer(cParams)) + uintptr(i)*unsafe.Sizeof((*C.char)(nil)))) = cParam
			defer C.free(unsafe.Pointer(cParam))
		}
	}

	cResult := C.cgo_arx_database_execute_prepared(cStatementName, cParams, C.int(len(params)))
	if cResult == nil {
		return nil
	}

	// Convert C result to Go result
	return convertCDatabaseQueryResultToGo(cResult)
}

// PrepareStatement prepares a statement for later execution
func PrepareStatement(statementName, query string) bool {
	cStatementName := C.CString(statementName)
	defer C.free(unsafe.Pointer(cStatementName))

	cQuery := C.CString(query)
	defer C.free(unsafe.Pointer(cQuery))

	return bool(C.cgo_arx_database_prepare_statement(cStatementName, cQuery))
}

// FreeQueryResult frees a query result
func FreeQueryResult(result *ArxQueryResult) {
	if result != nil {
		// Convert Go result back to C result for cleanup
		cResult := convertGoDatabaseQueryResultToC(result)
		if cResult != nil {
			C.cgo_arx_database_free_result(unsafe.Pointer(cResult))
		}
	}
}

// GetFieldValue gets a field value by column name
func GetFieldValue(result *ArxQueryResult, rowIndex int, columnName string) string {
	if result == nil {
		return ""
	}

	// Convert Go result back to C result
	cResult := convertGoDatabaseQueryResultToC(result)
	if cResult == nil {
		return ""
	}

	cColumnName := C.CString(columnName)
	defer C.free(unsafe.Pointer(cColumnName))

	cValue := C.cgo_arx_database_get_field_value(unsafe.Pointer(cResult), C.int(rowIndex), cColumnName)
	if cValue == nil {
		return ""
	}

	return C.GoString(cValue)
}

// GetFieldValueByIndex gets a field value by column index
func GetFieldValueByIndex(result *ArxQueryResult, rowIndex, columnIndex int) string {
	if result == nil {
		return ""
	}

	// Convert Go result back to C result
	cResult := convertGoDatabaseQueryResultToC(result)
	if cResult == nil {
		return ""
	}

	cValue := C.cgo_arx_database_get_field_value_by_index(unsafe.Pointer(cResult), C.int(rowIndex), C.int(columnIndex))
	if cValue == nil {
		return ""
	}

	return C.GoString(cValue)
}

// EscapeString escapes a string for safe SQL usage
func EscapeString(input string) string {
	cInput := C.CString(input)
	defer C.free(unsafe.Pointer(cInput))

	cEscaped := C.cgo_arx_database_escape_string(cInput)
	if cEscaped == nil {
		return input
	}
	defer C.free(unsafe.Pointer(cEscaped))

	return C.GoString(cEscaped)
}

// GetDatabaseLastError returns the last database error
func GetDatabaseLastError() string {
	cError := C.cgo_arx_database_get_last_error()
	if cError == nil {
		return ""
	}

	return C.GoString(cError)
}

// ClearDatabaseLastError clears the last database error
func ClearDatabaseLastError() {
	C.cgo_arx_database_clear_last_error()
}

// GetDatabaseMetrics returns database performance metrics
func GetDatabaseMetrics() *ArxDatabaseMetrics {
	cMetrics := C.cgo_arx_database_get_metrics()
	if cMetrics == nil {
		return nil
	}

	// Convert C metrics to Go metrics
	return convertCDatabaseMetricsToGo(cMetrics)
}

// ResetDatabaseMetrics resets database performance metrics
func ResetDatabaseMetrics() {
	C.cgo_arx_database_reset_metrics()
}

// IsDatabaseHealthy checks if the database is healthy
func IsDatabaseHealthy() bool {
	return bool(C.cgo_arx_database_is_healthy())
}

// CreateTable creates a database table
func CreateTable(tableName, schema string) bool {
	cTableName := C.CString(tableName)
	defer C.free(unsafe.Pointer(cTableName))

	cSchema := C.CString(schema)
	defer C.free(unsafe.Pointer(cSchema))

	return bool(C.cgo_arx_database_create_table(cTableName, cSchema))
}

// DropTable drops a database table
func DropTable(tableName string) bool {
	cTableName := C.CString(tableName)
	defer C.free(unsafe.Pointer(cTableName))

	return bool(C.cgo_arx_database_drop_table(cTableName))
}

// TableExists checks if a table exists
func TableExists(tableName string) bool {
	cTableName := C.CString(tableName)
	defer C.free(unsafe.Pointer(cTableName))

	return bool(C.cgo_arx_database_table_exists(cTableName))
}

// GetTableSchema gets a table's schema
func GetTableSchema(tableName string) string {
	cTableName := C.CString(tableName)
	defer C.free(unsafe.Pointer(cTableName))

	cSchema := C.cgo_arx_database_get_table_schema(cTableName)
	if cSchema == nil {
		return ""
	}
	defer C.free(unsafe.Pointer(cSchema))

	return C.GoString(cSchema)
}

// CreateIndex creates a database index
func CreateIndex(tableName, indexName, columns, indexType string) bool {
	cTableName := C.CString(tableName)
	defer C.free(unsafe.Pointer(cTableName))

	cIndexName := C.CString(indexName)
	defer C.free(unsafe.Pointer(cIndexName))

	cColumns := C.CString(columns)
	defer C.free(unsafe.Pointer(cColumns))

	cIndexType := C.CString(indexType)
	defer C.free(unsafe.Pointer(cIndexType))

	return bool(C.cgo_arx_database_create_index(cTableName, cIndexName, cColumns, cIndexType))
}

// DropIndex drops a database index
func DropIndex(tableName, indexName string) bool {
	cTableName := C.CString(tableName)
	defer C.free(unsafe.Pointer(cTableName))

	cIndexName := C.CString(indexName)
	defer C.free(unsafe.Pointer(cIndexName))

	return bool(C.cgo_arx_database_drop_index(cTableName, cIndexName))
}

// CreateBackup creates a database backup
func CreateBackup(backupPath string) bool {
	cBackupPath := C.CString(backupPath)
	defer C.free(unsafe.Pointer(cBackupPath))

	return bool(C.cgo_arx_database_create_backup(cBackupPath))
}

// RestoreBackup restores a database from backup
func RestoreBackup(backupPath string) bool {
	cBackupPath := C.CString(backupPath)
	defer C.free(unsafe.Pointer(cBackupPath))

	return bool(C.cgo_arx_database_restore_backup(cBackupPath))
}

// VerifyBackup verifies backup integrity
func VerifyBackup(backupPath string) bool {
	cBackupPath := C.CString(backupPath)
	defer C.free(unsafe.Pointer(cBackupPath))

	return bool(C.cgo_arx_database_verify_backup(cBackupPath))
}

// ============================================================================
// WALL COMPOSITION WRAPPER
// ============================================================================

// WallCompositionEngine represents the C wall composition engine
type WallCompositionEngine struct {
	ptr unsafe.Pointer
}

// CreateWallCompositionEngine creates a new wall composition engine
func CreateWallCompositionEngine(maxGapDistance, parallelThreshold, confidenceThreshold float64) (*WallCompositionEngine, error) {
	cEngine := C.cgo_wall_composition_engine_create(C.double(maxGapDistance), C.double(parallelThreshold), C.double(confidenceThreshold))
	if cEngine == nil {
		return nil, getLastError()
	}

	return &WallCompositionEngine{ptr: unsafe.Pointer(cEngine)}, nil
}

// Destroy frees the wall composition engine
func (e *WallCompositionEngine) Destroy() {
	if e.ptr != nil {
		C.cgo_wall_composition_engine_destroy((*C.arx_wall_composition_engine_t)(e.ptr))
		e.ptr = nil
	}
}

// CreateWallSegment creates a new wall segment
func CreateWallSegment(id uint64, startX, startY, startZ, endX, endY, endZ, height, thickness, confidence float64) (*WallSegment, error) {
	cSegment := C.cgo_wall_segment_create(C.uint64_t(id),
		C.double(startX), C.double(startY), C.double(startZ),
		C.double(endX), C.double(endY), C.double(endZ),
		C.double(height), C.double(thickness), C.double(confidence))

	if cSegment == nil {
		return nil, getLastError()
	}

	// Convert C segment to Go segment
	segment := FromCWallSegment((*CWallSegment)(unsafe.Pointer(cSegment)))
	return &segment, nil
}

// CreateCurvedWallSegment creates a new curved wall segment
func CreateCurvedWallSegment(id uint64, curveType CurveType, centerX, centerY, centerZ, radius, startAngle, endAngle, height, thickness, confidence float64) (*CurvedWallSegment, error) {
	cSegment := C.cgo_curved_wall_segment_create(C.uint64_t(id), C.arx_curve_type_t(curveType),
		C.double(centerX), C.double(centerY), C.double(centerZ),
		C.double(radius), C.double(startAngle), C.double(endAngle),
		C.double(height), C.double(thickness), C.double(confidence))

	if cSegment == nil {
		return nil, getLastError()
	}

	// Convert C segment to Go segment
	segment := CurvedWallSegment{
		Base:                FromCWallSegment((*CWallSegment)(unsafe.Pointer(&(*C.arx_curved_wall_segment_t)(unsafe.Pointer(cSegment)).base))),
		CurveType:           curveType,
		Radius:              radius,
		StartAngle:          startAngle,
		EndAngle:            endAngle,
		Center:              SmartPoint3D{X: int64(centerX), Y: int64(centerY), Z: int64(centerZ), Unit: UnitMillimeter},
		CurveLength:         0.0, // Will be calculated by C
		ApproximationPoints: 32,
	}

	return &segment, nil
}

// ComposeWalls composes walls from segments using the engine
func (e *WallCompositionEngine) ComposeWalls(segments []*WallSegment) ([]*WallStructure, error) {
	if e.ptr == nil {
		return nil, fmt.Errorf("WallCompositionEngine is nil")
	}

	if len(segments) == 0 {
		return []*WallStructure{}, nil
	}

	// Convert Go segments to C segments
	cSegments := make([]*C.arx_wall_segment_t, len(segments))
	for i, segment := range segments {
		cSeg := segment.ToCWallSegment()
		cSegments[i] = (*C.arx_wall_segment_t)(unsafe.Pointer(cSeg))
	}

	var structureCount C.uint32_t
	cStructures := C.cgo_wall_composition_compose_walls((*C.arx_wall_composition_engine_t)(e.ptr),
		(**C.arx_wall_segment_t)(unsafe.Pointer(&cSegments[0])),
		C.uint32_t(len(segments)), &structureCount)

	if cStructures == nil {
		return nil, getLastError()
	}

	// Convert C structures to Go structures
	goStructures := make([]*WallStructure, structureCount)
	for i := uint32(0); i < uint32(structureCount); i++ {
		cStructure := (*C.arx_wall_structure_t)(unsafe.Pointer(uintptr(unsafe.Pointer(cStructures)) + uintptr(i)*unsafe.Sizeof(*cStructures)))
		structure := FromCWallStructure(cStructure)
		goStructures[i] = &structure
	}

	// Free C structures
	C.cgo_wall_composition_free_structures(cStructures, structureCount)

	return goStructures, nil
}

// DetectConnections detects connections between wall segments
func (e *WallCompositionEngine) DetectConnections(segments []*WallSegment) ([]*WallConnection, error) {
	if e.ptr == nil {
		return nil, fmt.Errorf("WallCompositionEngine is nil")
	}

	if len(segments) == 0 {
		return []*WallConnection{}, nil
	}

	// Convert Go segments to C segments
	cSegments := make([]*C.arx_wall_segment_t, len(segments))
	for i, segment := range segments {
		cSeg := segment.ToCWallSegment()
		cSegments[i] = (*C.arx_wall_segment_t)(unsafe.Pointer(cSeg))
	}

	var connectionCount C.uint32_t
	cConnections := C.cgo_wall_composition_detect_connections((*C.arx_wall_composition_engine_t)(e.ptr),
		(**C.arx_wall_segment_t)(unsafe.Pointer(&cSegments[0])),
		C.uint32_t(len(segments)), &connectionCount)

	if cConnections == nil {
		return nil, getLastError()
	}

	// Convert C connections to Go connections
	goConnections := make([]*WallConnection, connectionCount)
	for i := uint32(0); i < uint32(connectionCount); i++ {
		cConnection := (*C.arx_wall_connection_t)(unsafe.Pointer(uintptr(unsafe.Pointer(cConnections)) + uintptr(i)*unsafe.Sizeof(*cConnections)))
		connection := FromCWallConnection(cConnection)
		goConnections[i] = &connection
	}

	// Free C connections
	C.cgo_wall_composition_free_connections(cConnections, connectionCount)

	return goConnections, nil
}

// GetWallStructureProperties gets properties from a wall structure
func GetWallStructureProperties(structure *WallStructure) (totalLength, maxHeight, overallConfidence float64) {
	if structure == nil {
		return 0.0, 0.0, 0.0
	}

	cStructure := structure.ToCWallStructure()
	C.cgo_wall_structure_get_properties((*C.arx_wall_structure_t)(unsafe.Pointer(cStructure)),
		(*C.double)(unsafe.Pointer(&totalLength)),
		(*C.double)(unsafe.Pointer(&maxHeight)),
		(*C.double)(unsafe.Pointer(&overallConfidence)))

	return totalLength, maxHeight, overallConfidence
}

// ============================================================================
// DATABASE TYPE CONVERSION FUNCTIONS
// ============================================================================

// convertGoDatabaseConfigToC converts Go ArxDatabaseConfig to C ArxDatabaseConfig
func convertGoDatabaseConfigToC(config *ArxDatabaseConfig) unsafe.Pointer {
	if config == nil {
		return nil
	}

	// Allocate C config structure
	cConfig := C.malloc(C.sizeof_ArxDatabaseConfig)
	if cConfig == nil {
		return nil
	}

	// Convert Go config to C config
	cConfigPtr := (*C.ArxDatabaseConfig)(cConfig)
	
	// Convert string fields
	if config.Host != "" {
		cConfigPtr.host = C.CString(config.Host)
	}
	if config.Database != "" {
		cConfigPtr.database = C.CString(config.Database)
	}
	if config.Username != "" {
		cConfigPtr.username = C.CString(config.Username)
	}
	if config.Password != "" {
		cConfigPtr.password = C.CString(config.Password)
	}
	if config.SSLMode != "" {
		cConfigPtr.ssl_mode = C.CString(config.SSLMode)
	}
	if config.ConnectionString != "" {
		cConfigPtr.connection_string = C.CString(config.ConnectionString)
	}

	// Convert primitive fields
	cConfigPtr.type = C.int(config.Type)
	cConfigPtr.port = C.int(config.Port)
	cConfigPtr.max_connections = C.int(config.MaxConnections)
	cConfigPtr.max_idle_connections = C.int(config.MaxIdleConnections)
	cConfigPtr.connection_lifetime_seconds = C.int(config.ConnectionLifetimeSecs)
	cConfigPtr.idle_timeout_seconds = C.int(config.IdleTimeoutSecs)
	cConfigPtr.enable_prepared_statements = C.bool(config.EnablePreparedStmts)
	cConfigPtr.log_level = C.int(config.LogLevel)
	cConfigPtr.enable_metrics = C.bool(config.EnableMetrics)

	return cConfig
}

// convertCDatabasePoolStatsToGo converts C ArxConnectionPoolStats to Go ArxConnectionPoolStats
func convertCDatabasePoolStatsToGo(cStats unsafe.Pointer) *ArxConnectionPoolStats {
	if cStats == nil {
		return nil
	}

	stats := (*C.ArxConnectionPoolStats)(cStats)
	
	return &ArxConnectionPoolStats{
		MaxOpenConnections: int(stats.max_open_connections),
		OpenConnections:    int(stats.open_connections),
		InUseConnections:   int(stats.in_use_connections),
		IdleConnections:    int(stats.idle_connections),
		WaitCount:          int64(stats.wait_count),
		WaitDurationMs:     float64(stats.wait_duration_ms),
		MaxIdleClosed:      int64(stats.max_idle_closed),
		MaxLifetimeClosed:  int64(stats.max_lifetime_closed),
		LastStatsUpdate:    time.Unix(int64(stats.last_stats_update), 0),
	}
}

// convertCDatabaseTransactionToGo converts C ArxTransaction to Go ArxTransaction
func convertCDatabaseTransactionToGo(cTx unsafe.Pointer) *ArxTransaction {
	if cTx == nil {
		return nil
	}

	tx := (*C.ArxTransaction)(cTx)
	
	return &ArxTransaction{
		TransactionID:  uint64(tx.transaction_id),
		StartTime:      time.Unix(int64(tx.start_time), 0),
		IsActive:       bool(tx.is_active),
		StatementCount: int(tx.statement_count),
		Description:    C.GoString(tx.description),
	}
}

// convertCDatabaseQueryResultToGo converts C ArxQueryResult to Go ArxQueryResult
func convertCDatabaseQueryResultToGo(cResult unsafe.Pointer) *ArxQueryResult {
	if cResult == nil {
		return nil
	}

	result := (*C.ArxQueryResult)(cResult)
	
	// Convert column names
	var columnNames []string
	if result.column_names != nil {
		for i := 0; i < int(result.column_count); i++ {
			colName := C.GoString(*(**C.char)(unsafe.Pointer(uintptr(unsafe.Pointer(result.column_names)) + uintptr(i)*unsafe.Sizeof((*C.char)(nil)))))
			columnNames = append(columnNames, colName)
		}
	}

	// Convert rows
	var rows [][]string
	if result.rows != nil {
		for i := 0; i < int(result.row_count); i++ {
			var row []string
			rowPtr := *(***C.char)(unsafe.Pointer(uintptr(unsafe.Pointer(result.rows)) + uintptr(i)*unsafe.Sizeof((*C.char)(nil)))))
			if rowPtr != nil {
				for j := 0; j < int(result.column_count); j++ {
					cellValue := C.GoString(*(**C.char)(unsafe.Pointer(uintptr(unsafe.Pointer(rowPtr)) + uintptr(j)*unsafe.Sizeof((*C.char)(nil)))))
					row = append(row, cellValue)
				}
			}
			rows = append(rows, row)
		}
	}

	return &ArxQueryResult{
		ColumnNames:  columnNames,
		Rows:         rows,
		RowCount:     int(result.row_count),
		ColumnCount:  int(result.column_count),
		AffectedRows: int64(result.affected_rows),
		LastInsertID: uint64(result.last_insert_id),
		ErrorMessage: C.GoString(result.error_message),
	}
}

// convertGoDatabaseQueryResultToC converts Go ArxQueryResult back to C ArxQueryResult
// This is used for cleanup operations
func convertGoDatabaseQueryResultToC(result *ArxQueryResult) unsafe.Pointer {
	if result == nil {
		return nil
	}

	// For cleanup purposes, we just need a pointer to identify the result
	// The actual C result structure is managed by the C core
	// This is a simplified conversion for memory management
	return unsafe.Pointer(uintptr(0x1)) // Placeholder pointer for cleanup
}

// convertCDatabaseMetricsToGo converts C ArxDatabaseMetrics to Go ArxDatabaseMetrics
func convertCDatabaseMetricsToGo(cMetrics unsafe.Pointer) *ArxDatabaseMetrics {
	if cMetrics == nil {
		return nil
	}

	metrics := (*C.ArxDatabaseMetrics)(cMetrics)
	
	return &ArxDatabaseMetrics{
		TotalQueries:       uint64(metrics.total_queries),
		SuccessfulQueries:  uint64(metrics.successful_queries),
		FailedQueries:      uint64(metrics.failed_queries),
		AvgQueryTimeMs:     float64(metrics.avg_query_time_ms),
		SlowestQueryTimeMs: float64(metrics.slowest_query_time_ms),
		FastestQueryTimeMs: float64(metrics.fastest_query_time_ms),
		CacheHits:          uint64(metrics.cache_hits),
		CacheMisses:        uint64(metrics.cache_misses),
		ConnectionErrors:   uint64(metrics.connection_errors),
		TransactionCount:   uint64(metrics.transaction_count),
		RollbackCount:      uint64(metrics.rollback_count),
		LastMetricsReset:   time.Unix(int64(metrics.last_metrics_reset), 0),
	}
}
