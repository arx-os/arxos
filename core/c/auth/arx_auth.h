/**
 * @file arx_auth.h
 * @brief ARXOS Authentication System - C Core
 * 
 * Provides JWT handling, password hashing, and security functions
 * for the ARXOS C core, optimized for performance and security.
 */

#ifndef ARXOS_AUTH_H
#define ARXOS_AUTH_H

#ifdef __cplusplus
extern "C" {
#endif

#include <stdbool.h>
#include <stdint.h>
#include <time.h>

// ============================================================================
// CONSTANTS AND CONFIGURATION
// ============================================================================

#define ARX_AUTH_MAX_USERNAME_LEN 64
#define ARX_AUTH_MAX_PASSWORD_LEN 128
#define ARX_AUTH_MAX_EMAIL_LEN 128
#define ARX_AUTH_MAX_TOKEN_LEN 512
#define ARX_AUTH_MAX_SECRET_LEN 64
#define ARX_AUTH_MAX_ISSUER_LEN 32
#define ARX_AUTH_MAX_SUBJECT_LEN 64
#define ARX_AUTH_MAX_AUDIENCE_LEN 64
#define ARX_AUTH_MAX_CLAIMS_LEN 1024

#define ARX_AUTH_DEFAULT_TOKEN_TTL 3600  // 1 hour in seconds
#define ARX_AUTH_DEFAULT_REFRESH_TTL 604800  // 7 days in seconds
#define ARX_AUTH_MAX_REFRESH_TOKENS 5

// ============================================================================
// DATA STRUCTURES
// ============================================================================

/**
 * @brief JWT Claims structure
 */
typedef struct {
    char* issuer;
    char* subject;
    char* audience;
    time_t issued_at;
    time_t not_before;
    time_t expires_at;
    char* jwt_id;
    char* type;
    char* custom_claims;  // JSON string for additional claims
} ArxJWTClaims;

/**
 * @brief JWT Token structure
 */
typedef struct {
    char* header;
    char* payload;
    char* signature;
    char* raw_token;
    ArxJWTClaims* claims;
    bool is_valid;
} ArxJWTToken;

/**
 * @brief User authentication data
 */
typedef struct {
    uint32_t user_id;
    char username[ARX_AUTH_MAX_USERNAME_LEN];
    char email[ARX_AUTH_MAX_EMAIL_LEN];
    char password_hash[ARX_AUTH_MAX_PASSWORD_LEN];
    bool is_admin;
    bool is_active;
    time_t created_at;
    time_t last_login;
    time_t password_changed_at;
} ArxUser;

/**
 * @brief Refresh token data
 */
typedef struct {
    char* token_hash;
    uint32_t user_id;
    time_t expires_at;
    time_t created_at;
    time_t last_used_at;
    char* user_agent;
    char* ip_address;
    bool is_revoked;
    time_t revoked_at;
    char* revoked_reason;
} ArxRefreshToken;

/**
 * @brief Two-factor authentication data
 */
typedef struct {
    uint32_t user_id;
    char secret[ARX_AUTH_MAX_SECRET_LEN];
    char* backup_codes_hash;
    bool is_enabled;
    time_t created_at;
    time_t last_used_at;
} ArxTwoFactorAuth;

/**
 * @brief Authentication options
 */
typedef struct {
    char* jwt_secret;
    int jwt_algorithm;  // 0=HS256, 1=HS384, 2=HS512
    int password_cost;  // bcrypt cost factor
    int token_ttl;      // Access token TTL in seconds
    int refresh_ttl;    // Refresh token TTL in seconds
    int max_refresh_tokens;
    bool require_2fa;
    char* issuer;
} ArxAuthOptions;

/**
 * @brief Authentication result
 */
typedef struct {
    bool success;
    char* error_message;
    char* token;
    char* refresh_token;
    time_t expires_at;
    ArxUser* user;
} ArxAuthResult;

// ============================================================================
// FUNCTION PROTOTYPES
// ============================================================================

// ============================================================================
// INITIALIZATION AND CLEANUP
// ============================================================================

/**
 * @brief Initialize the authentication system
 * @param options Authentication configuration options
 * @return true on success, false on failure
 */
bool arx_auth_init(const ArxAuthOptions* options);

/**
 * @brief Cleanup the authentication system
 */
void arx_auth_cleanup(void);

// ============================================================================
// JWT OPERATIONS
// ============================================================================

/**
 * @brief Create a new JWT token
 * @param claims JWT claims to include
 * @param secret Secret key for signing
 * @return Pointer to JWT token or NULL on failure
 */
ArxJWTToken* arx_auth_create_jwt(const ArxJWTClaims* claims, const char* secret);

/**
 * @brief Parse and validate a JWT token
 * @param token_string Raw JWT token string
 * @param secret Secret key for verification
 * @return Pointer to parsed JWT token or NULL on failure
 */
ArxJWTToken* arx_auth_parse_jwt(const char* token_string, const char* secret);

/**
 * @brief Verify JWT token signature and claims
 * @param token JWT token to verify
 * @param secret Secret key for verification
 * @return true if valid, false otherwise
 */
bool arx_auth_verify_jwt(const ArxJWTToken* token, const char* secret);

/**
 * @brief Destroy JWT token
 * @param token JWT token to destroy
 */
void arx_auth_destroy_jwt(ArxJWTToken* token);

// ============================================================================
// PASSWORD OPERATIONS
// ============================================================================

/**
 * @brief Hash a password using bcrypt
 * @param password Plain text password
 * @param cost bcrypt cost factor
 * @return Hashed password (caller must free) or NULL on failure
 */
char* arx_auth_hash_password(const char* password, int cost);

/**
 * @brief Verify a password against its hash
 * @param password Plain text password
 * @param hash Hashed password
 * @return true if password matches, false otherwise
 */
bool arx_auth_verify_password(const char* password, const char* hash);

/**
 * @brief Generate a secure random password
 * @param length Password length
 * @param include_symbols Whether to include symbols
 * @return Generated password (caller must free) or NULL on failure
 */
char* arx_auth_generate_password(int length, bool include_symbols);

// ============================================================================
// USER MANAGEMENT
// ============================================================================

/**
 * @brief Create a new user
 * @param username Username
 * @param email Email address
 * @param password Plain text password
 * @param is_admin Whether user is admin
 * @return Pointer to created user or NULL on failure
 */
ArxUser* arx_auth_create_user(const char* username, const char* email, 
                              const char* password, bool is_admin);

/**
 * @brief Authenticate a user
 * @param username Username or email
 * @param password Plain text password
 * @return Authentication result
 */
ArxAuthResult* arx_auth_authenticate_user(const char* username, const char* password);

/**
 * @brief Get user by ID
 * @param user_id User ID
 * @return Pointer to user or NULL if not found
 */
ArxUser* arx_auth_get_user(uint32_t user_id);

/**
 * @brief Get user by username
 * @param username Username
 * @return Pointer to user or NULL if not found
 */
ArxUser* arx_auth_get_user_by_username(const char* username);

/**
 * @brief Update user password
 * @param user_id User ID
 * @param old_password Old password
 * @param new_password New password
 * @return true on success, false on failure
 */
bool arx_auth_update_password(uint32_t user_id, const char* old_password, 
                             const char* new_password);

/**
 * @brief Destroy user
 * @param user User to destroy
 */
void arx_auth_destroy_user(ArxUser* user);

// ============================================================================
// REFRESH TOKEN OPERATIONS
// ============================================================================

/**
 * @brief Generate a refresh token
 * @param user_id User ID
 * @param user_agent User agent string
 * @param ip_address IP address
 * @return Refresh token (caller must free) or NULL on failure
 */
char* arx_auth_generate_refresh_token(uint32_t user_id, const char* user_agent, 
                                     const char* ip_address);

/**
 * @brief Validate a refresh token
 * @param token Refresh token
 * @return User ID if valid, 0 on failure
 */
uint32_t arx_auth_validate_refresh_token(const char* token);

/**
 * @brief Revoke a refresh token
 * @param token Refresh token to revoke
 * @param reason Reason for revocation
 * @return true on success, false on failure
 */
bool arx_auth_revoke_refresh_token(const char* token, const char* reason);

/**
 * @brief Clean up expired refresh tokens
 * @return Number of tokens cleaned up
 */
int arx_auth_cleanup_refresh_tokens(void);

// ============================================================================
// TWO-FACTOR AUTHENTICATION
// ============================================================================

/**
 * @brief Generate 2FA secret
 * @param user_id User ID
 * @return Secret key (caller must free) or NULL on failure
 */
char* arx_auth_generate_2fa_secret(uint32_t user_id);

/**
 * @brief Verify 2FA token
 * @param user_id User ID
 * @param token 2FA token
 * @return true if valid, false otherwise
 */
bool arx_auth_verify_2fa_token(uint32_t user_id, const char* token);

/**
 * @brief Enable 2FA for user
 * @param user_id User ID
 * @return true on success, false on failure
 */
bool arx_auth_enable_2fa(uint32_t user_id);

/**
 * @brief Disable 2FA for user
 * @param user_id User ID
 * @return true on success, false on failure
 */
bool arx_auth_disable_2fa(uint32_t user_id);

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

/**
 * @brief Generate a secure random token
 * @param length Token length in bytes
 * @return Generated token (caller must free) or NULL on failure
 */
char* arx_auth_generate_secure_token(int length);

/**
 * @brief Get current authentication statistics
 * @return Statistics string (caller must free) or NULL on failure
 */
char* arx_auth_get_statistics(void);

/**
 * @brief Check if authentication system is healthy
 * @return true if healthy, false otherwise
 */
bool arx_auth_is_healthy(void);

#ifdef __cplusplus
}
#endif

#endif // ARXOS_AUTH_H
