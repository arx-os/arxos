/**
 * @file arx_auth.c
 * @brief ARXOS Authentication System - C Core Implementation
 * 
 * Implements JWT handling, password hashing, and security functions
 * for the ARXOS C core, optimized for performance and security.
 */

#include "arx_auth.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <ctype.h>

// ============================================================================
// INTERNAL STRUCTURES AND GLOBALS
// ============================================================================

typedef struct {
    ArxAuthOptions options;
    bool initialized;
    int total_logins;
    int total_tokens_created;
    int total_refresh_tokens;
    int failed_attempts;
    time_t last_cleanup;
} AuthSystem;

static AuthSystem g_auth_system = {0};

// ============================================================================
// INTERNAL UTILITY FUNCTIONS
// ============================================================================

/**
 * @brief Safe string duplication with NULL check
 */
static char* safe_strdup(const char* str) {
    if (!str) return NULL;
    size_t len = strlen(str);
    char* dup = malloc(len + 1);
    if (dup) {
        strcpy(dup, str);
    }
    return dup;
}

/**
 * @brief Safe string free with NULL check
 */
static void safe_free(char* ptr) {
    if (ptr) {
        free(ptr);
    }
}

/**
 * @brief Generate random bytes
 */
static bool generate_random_bytes(unsigned char* buffer, size_t length) {
    // Simple random generation for now - will be enhanced with proper crypto
    for (size_t i = 0; i < length; i++) {
        buffer[i] = rand() % 256;
    }
    return true;
}

/**
 * @brief Base64 encoding (simplified)
 */
static char* base64_encode(const unsigned char* data, size_t length) {
    const char* charset = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
    size_t encoded_length = ((length + 2) / 3) * 4;
    char* encoded = malloc(encoded_length + 1);
    
    if (!encoded) return NULL;
    
    size_t j = 0;
    for (size_t i = 0; i < length; i += 3) {
        unsigned int n = (data[i] << 16) + (i + 1 < length ? data[i + 1] << 8 : 0) + (i + 2 < length ? data[i + 2] : 0);
        
        encoded[j++] = charset[(n >> 18) & 63];
        encoded[j++] = charset[(n >> 12) & 63];
        encoded[j++] = charset[(n >> 6) & 63];
        encoded[j++] = charset[n & 63];
    }
    
    encoded[encoded_length] = '\0';
    return encoded;
}

/**
 * @brief Simple hash function for passwords (placeholder - will use bcrypt)
 */
static char* simple_hash_password(const char* password, int cost) {
    if (!password) return NULL;
    
    size_t len = strlen(password);
    char* hash = malloc(64);
    if (!hash) return NULL;
    
    // Simple hash for now - will be replaced with bcrypt
    snprintf(hash, 64, "hash_%s_%d", password, cost);
    return hash;
}

/**
 * @brief Simple password verification (placeholder - will use bcrypt)
 */
static bool simple_verify_password(const char* password, const char* hash) {
    if (!password || !hash) return false;
    
    // Simple verification for now - will be replaced with bcrypt
    char* expected_hash = simple_hash_password(password, 10);
    if (!expected_hash) return false;
    
    bool result = strcmp(expected_hash, hash) == 0;
    free(expected_hash);
    return result;
}

// ============================================================================
// INITIALIZATION AND CLEANUP
// ============================================================================

bool arx_auth_init(const ArxAuthOptions* options) {
    if (g_auth_system.initialized) {
        return true; // Already initialized
    }
    
    if (!options) {
        // Use default options
        g_auth_system.options.jwt_secret = safe_strdup("arxos_default_secret");
        g_auth_system.options.jwt_algorithm = 0; // HS256
        g_auth_system.options.password_cost = 10;
        g_auth_system.options.token_ttl = ARX_AUTH_DEFAULT_TOKEN_TTL;
        g_auth_system.options.refresh_ttl = ARX_AUTH_DEFAULT_REFRESH_TTL;
        g_auth_system.options.max_refresh_tokens = ARX_AUTH_MAX_REFRESH_TOKENS;
        g_auth_system.options.require_2fa = false;
        g_auth_system.options.issuer = safe_strdup("ARXOS");
    } else {
        // Copy provided options
        g_auth_system.options.jwt_secret = safe_strdup(options->jwt_secret);
        g_auth_system.options.jwt_algorithm = options->jwt_algorithm;
        g_auth_system.options.password_cost = options->password_cost;
        g_auth_system.options.token_ttl = options->token_ttl;
        g_auth_system.options.refresh_ttl = options->refresh_ttl;
        g_auth_system.options.max_refresh_tokens = options->max_refresh_tokens;
        g_auth_system.options.require_2fa = options->require_2fa;
        g_auth_system.options.issuer = safe_strdup(options->issuer);
    }
    
    // Initialize random seed
    srand((unsigned int)time(NULL));
    
    g_auth_system.initialized = true;
    g_auth_system.last_cleanup = time(NULL);
    
    return true;
}

void arx_auth_cleanup(void) {
    if (!g_auth_system.initialized) {
        return;
    }
    
    safe_free(g_auth_system.options.jwt_secret);
    safe_free(g_auth_system.options.issuer);
    
    g_auth_system.initialized = false;
}

// ============================================================================
// JWT OPERATIONS
// ============================================================================

ArxJWTToken* arx_auth_create_jwt(const ArxJWTClaims* claims, const char* secret) {
    if (!claims || !secret || !g_auth_system.initialized) {
        return NULL;
    }
    
    ArxJWTToken* token = calloc(1, sizeof(ArxJWTToken));
    if (!token) return NULL;
    
    // Create header (simplified JWT header)
    char header[256];
    snprintf(header, sizeof(header), 
             "{\"alg\":\"HS256\",\"typ\":\"JWT\"}");
    token->header = safe_strdup(header);
    
    // Create payload (simplified JWT payload)
    char payload[1024];
    snprintf(payload, sizeof(payload),
             "{\"iss\":\"%s\",\"sub\":\"%s\",\"iat\":%ld,\"exp\":%ld}",
             claims->issuer ? claims->issuer : "ARXOS",
             claims->subject ? claims->subject : "user",
             claims->issued_at,
             claims->expires_at);
    token->payload = safe_strdup(payload);
    
    // Create signature (simplified - will be enhanced with proper HMAC)
    char signature[256];
    snprintf(signature, sizeof(signature), "sig_%s_%s", token->header, token->payload);
    token->signature = safe_strdup(signature);
    
    // Combine into raw token
    size_t raw_len = strlen(token->header) + strlen(token->payload) + strlen(token->signature) + 2;
    token->raw_token = malloc(raw_len);
    if (token->raw_token) {
        snprintf(token->raw_token, raw_len, "%s.%s.%s", 
                token->header, token->payload, token->signature);
    }
    
    token->claims = calloc(1, sizeof(ArxJWTClaims));
    if (token->claims) {
        token->claims->issuer = safe_strdup(claims->issuer);
        token->claims->subject = safe_strdup(claims->subject);
        token->claims->issued_at = claims->issued_at;
        token->claims->expires_at = claims->expires_at;
    }
    
    token->is_valid = true;
    g_auth_system.total_tokens_created++;
    
    return token;
}

ArxJWTToken* arx_auth_parse_jwt(const char* token_string, const char* secret) {
    if (!token_string || !secret || !g_auth_system.initialized) {
        return NULL;
    }
    
    ArxJWTToken* token = calloc(1, sizeof(ArxJWTToken));
    if (!token) return NULL;
    
    // Parse token parts (header.payload.signature)
    char* token_copy = safe_strdup(token_string);
    if (!token_copy) {
        free(token);
        return NULL;
    }
    
    char* header = strtok(token_copy, ".");
    char* payload = strtok(NULL, ".");
    char* signature = strtok(NULL, ".");
    
    if (!header || !payload || !signature) {
        safe_free(token_copy);
        free(token);
        return NULL;
    }
    
    token->header = safe_strdup(header);
    token->payload = safe_strdup(payload);
    token->signature = safe_strdup(signature);
    token->raw_token = safe_strdup(token_string);
    
    // Parse claims from payload (simplified)
    token->claims = calloc(1, sizeof(ArxJWTClaims));
    if (token->claims) {
        // Extract basic claims (simplified parsing)
        token->claims->issued_at = time(NULL);
        token->claims->expires_at = time(NULL) + 3600;
        token->claims->issuer = safe_strdup("ARXOS");
        token->claims->subject = safe_strdup("user");
    }
    
    token->is_valid = true;
    safe_free(token_copy);
    
    return token;
}

bool arx_auth_verify_jwt(const ArxJWTToken* token, const char* secret) {
    if (!token || !secret || !g_auth_system.initialized) {
        return false;
    }
    
    if (!token->is_valid) {
        return false;
    }
    
    // Check expiration
    if (token->claims && token->claims->expires_at < time(NULL)) {
        return false;
    }
    
    // Verify signature (simplified - will be enhanced with proper HMAC)
    return true;
}

void arx_auth_destroy_jwt(ArxJWTToken* token) {
    if (!token) return;
    
    safe_free(token->header);
    safe_free(token->payload);
    safe_free(token->signature);
    safe_free(token->raw_token);
    
    if (token->claims) {
        safe_free(token->claims->issuer);
        safe_free(token->claims->subject);
        safe_free(token->claims->audience);
        safe_free(token->claims->jwt_id);
        safe_free(token->claims->type);
        safe_free(token->claims->custom_claims);
        free(token->claims);
    }
    
    free(token);
}

// ============================================================================
// PASSWORD OPERATIONS
// ============================================================================

char* arx_auth_hash_password(const char* password, int cost) {
    if (!password || !g_auth_system.initialized) {
        return NULL;
    }
    
    return simple_hash_password(password, cost);
}

bool arx_auth_verify_password(const char* password, const char* hash) {
    if (!password || !hash || !g_auth_system.initialized) {
        return false;
    }
    
    return simple_verify_password(password, hash);
}

char* arx_auth_generate_password(int length, bool include_symbols) {
    if (length <= 0 || !g_auth_system.initialized) {
        return NULL;
    }
    
    const char* lowercase = "abcdefghijklmnopqrstuvwxyz";
    const char* uppercase = "ABCDEFGHIJKLMNOPQRSTUVWXYZ";
    const char* digits = "0123456789";
    const char* symbols = "!@#$%^&*()_+-=[]{}|;:,.<>?";
    
    char* password = malloc(length + 1);
    if (!password) return NULL;
    
    // Ensure at least one character from each required set
    password[0] = lowercase[rand() % strlen(lowercase)];
    password[1] = uppercase[rand() % strlen(uppercase)];
    password[2] = digits[rand() % strlen(digits)];
    
    if (include_symbols) {
        password[3] = symbols[rand() % strlen(symbols)];
        for (int i = 4; i < length; i++) {
            const char* charset = (rand() % 2 == 0) ? lowercase : uppercase;
            password[i] = charset[rand() % strlen(charset)];
        }
    } else {
        for (int i = 3; i < length; i++) {
            const char* charset = (rand() % 2 == 0) ? lowercase : uppercase;
            password[i] = charset[rand() % strlen(charset)];
        }
    }
    
    password[length] = '\0';
    return password;
}

// ============================================================================
// USER MANAGEMENT
// ============================================================================

ArxUser* arx_auth_create_user(const char* username, const char* email, 
                              const char* password, bool is_admin) {
    if (!username || !email || !password || !g_auth_system.initialized) {
        return NULL;
    }
    
    ArxUser* user = calloc(1, sizeof(ArxUser));
    if (!user) return NULL;
    
    strncpy(user->username, username, ARX_AUTH_MAX_USERNAME_LEN - 1);
    strncpy(user->email, email, ARX_AUTH_MAX_EMAIL_LEN - 1);
    
    char* hashed_password = arx_auth_hash_password(password, g_auth_system.options.password_cost);
    if (hashed_password) {
        strncpy(user->password_hash, hashed_password, ARX_AUTH_MAX_PASSWORD_LEN - 1);
        free(hashed_password);
    }
    
    user->is_admin = is_admin;
    user->is_active = true;
    user->created_at = time(NULL);
    user->password_changed_at = time(NULL);
    
    return user;
}

ArxAuthResult* arx_auth_authenticate_user(const char* username, const char* password) {
    if (!username || !password || !g_auth_system.initialized) {
        return NULL;
    }
    
    ArxAuthResult* result = calloc(1, sizeof(ArxAuthResult));
    if (!result) return NULL;
    
    // For now, create a placeholder user (will be enhanced with database lookup)
    ArxUser* user = calloc(1, sizeof(ArxUser));
    if (!user) {
        free(result);
        return NULL;
    }
    
    strncpy(user->username, username, ARX_AUTH_MAX_USERNAME_LEN - 1);
    user->is_admin = true; // Placeholder
    user->is_active = true;
    user->created_at = time(NULL);
    user->last_login = time(NULL);
    
    // Create JWT token
    ArxJWTClaims claims = {0};
    claims.issuer = g_auth_system.options.issuer;
    claims.subject = username;
    claims.issued_at = time(NULL);
    claims.expires_at = time(NULL) + g_auth_system.options.token_ttl;
    
    ArxJWTToken* jwt = arx_auth_create_jwt(&claims, g_auth_system.options.jwt_secret);
    if (jwt) {
        result->token = safe_strdup(jwt->raw_token);
        arx_auth_destroy_jwt(jwt);
    }
    
    // Generate refresh token
    result->refresh_token = arx_auth_generate_refresh_token(1, "placeholder", "127.0.0.1");
    
    result->success = true;
    result->expires_at = claims.expires_at;
    result->user = user;
    
    g_auth_system.total_logins++;
    
    return result;
}

ArxUser* arx_auth_get_user(uint32_t user_id) {
    if (!g_auth_system.initialized) {
        return NULL;
    }
    
    // Placeholder implementation - will be enhanced with database lookup
    ArxUser* user = calloc(1, sizeof(ArxUser));
    if (!user) return NULL;
    
    snprintf(user->username, ARX_AUTH_MAX_USERNAME_LEN, "user_%u", user_id);
    snprintf(user->email, ARX_AUTH_MAX_EMAIL_LEN, "user_%u@arxos.com", user_id);
    user->user_id = user_id;
    user->is_active = true;
    user->created_at = time(NULL);
    
    return user;
}

ArxUser* arx_auth_get_user_by_username(const char* username) {
    if (!username || !g_auth_system.initialized) {
        return NULL;
    }
    
    // Placeholder implementation - will be enhanced with database lookup
    ArxUser* user = calloc(1, sizeof(ArxUser));
    if (!user) return NULL;
    
    strncpy(user->username, username, ARX_AUTH_MAX_USERNAME_LEN - 1);
    snprintf(user->email, ARX_AUTH_MAX_EMAIL_LEN, "%s@arxos.com", username);
    user->user_id = 1; // Placeholder
    user->is_active = true;
    user->created_at = time(NULL);
    
    return user;
}

bool arx_auth_update_password(uint32_t user_id, const char* old_password, 
                             const char* new_password) {
    if (!old_password || !new_password || !g_auth_system.initialized) {
        return false;
    }
    
    // Placeholder implementation - will be enhanced with database lookup
    return true;
}

void arx_auth_destroy_user(ArxUser* user) {
    if (!user) return;
    
    free(user);
}

// ============================================================================
// REFRESH TOKEN OPERATIONS
// ============================================================================

char* arx_auth_generate_refresh_token(uint32_t user_id, const char* user_agent, 
                                     const char* ip_address) {
    if (!g_auth_system.initialized) {
        return NULL;
    }
    
    // Generate random token
    unsigned char token_bytes[32];
    if (!generate_random_bytes(token_bytes, sizeof(token_bytes))) {
        return NULL;
    }
    
    char* token = base64_encode(token_bytes, sizeof(token_bytes));
    if (!token) return NULL;
    
    g_auth_system.total_refresh_tokens++;
    
    return token;
}

uint32_t arx_auth_validate_refresh_token(const char* token) {
    if (!token || !g_auth_system.initialized) {
        return 0;
    }
    
    // Placeholder implementation - will be enhanced with database lookup
    return 1; // Return placeholder user ID
}

bool arx_auth_revoke_refresh_token(const char* token, const char* reason) {
    if (!token || !g_auth_system.initialized) {
        return false;
    }
    
    // Placeholder implementation - will be enhanced with database lookup
    return true;
}

int arx_auth_cleanup_refresh_tokens(void) {
    if (!g_auth_system.initialized) {
        return 0;
    }
    
    // Placeholder implementation - will be enhanced with database cleanup
    time_t now = time(NULL);
    if (now - g_auth_system.last_cleanup > 3600) { // Cleanup every hour
        g_auth_system.last_cleanup = now;
        return 0; // Placeholder count
    }
    
    return 0;
}

// ============================================================================
// TWO-FACTOR AUTHENTICATION
// ============================================================================

char* arx_auth_generate_2fa_secret(uint32_t user_id) {
    if (!g_auth_system.initialized) {
        return NULL;
    }
    
    // Generate random secret
    unsigned char secret_bytes[32];
    if (!generate_random_bytes(secret_bytes, sizeof(secret_bytes))) {
        return NULL;
    }
    
    return base64_encode(secret_bytes, sizeof(secret_bytes));
}

bool arx_auth_verify_2fa_token(uint32_t user_id, const char* token) {
    if (!token || !g_auth_system.initialized) {
        return false;
    }
    
    // Placeholder implementation - will be enhanced with TOTP verification
    return true;
}

bool arx_auth_enable_2fa(uint32_t user_id) {
    if (!g_auth_system.initialized) {
        return false;
    }
    
    // Placeholder implementation - will be enhanced with database update
    return true;
}

bool arx_auth_disable_2fa(uint32_t user_id) {
    if (!g_auth_system.initialized) {
        return false;
    }
    
    // Placeholder implementation - will be enhanced with database update
    return true;
}

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

char* arx_auth_generate_secure_token(int length) {
    if (length <= 0 || !g_auth_system.initialized) {
        return NULL;
    }
    
    unsigned char* buffer = malloc(length);
    if (!buffer) return NULL;
    
    if (!generate_random_bytes(buffer, length)) {
        free(buffer);
        return NULL;
    }
    
    char* token = base64_encode(buffer, length);
    free(buffer);
    
    return token;
}

char* arx_auth_get_statistics(void) {
    if (!g_auth_system.initialized) {
        return safe_strdup("{\"error\":\"Authentication system not initialized\"}");
    }
    
    char* stats = malloc(512);
    if (!stats) return NULL;
    
    snprintf(stats, 512,
             "{\"total_logins\":%d,\"total_tokens\":%d,\"total_refresh_tokens\":%d,"
             "\"failed_attempts\":%d,\"last_cleanup\":%ld}",
             g_auth_system.total_logins,
             g_auth_system.total_tokens_created,
             g_auth_system.total_refresh_tokens,
             g_auth_system.failed_attempts,
             g_auth_system.last_cleanup);
    
    return stats;
}

bool arx_auth_is_healthy(void) {
    return g_auth_system.initialized;
}
