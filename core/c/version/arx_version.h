/**
 * @file arx_version.h
 * @brief ArxVersionControl System
 * 
 * Provides Git-like version control for building data, including commits,
 * branches, diffs, and change tracking. This enables building infrastructure
 * as code with full history and rollback capabilities.
 */

#ifndef ARX_VERSION_H
#define ARX_VERSION_H

#include <time.h>
#include <stdbool.h>
#include <stdint.h>
#include "../arxobject/arxobject.h"

#ifdef __cplusplus
extern "C" {
#endif

// Forward declarations
typedef struct ArxCommit ArxCommit;
typedef struct ArxBranch ArxBranch;
typedef struct ArxDiff ArxDiff;
typedef struct ArxChange ArxChange;
typedef struct ArxVersionControl ArxVersionControl;

/**
 * @brief Change types for tracking modifications
 */
typedef enum {
    ARX_CHANGE_ADD,      // Object added
    ARX_CHANGE_REMOVE,   // Object removed
    ARX_CHANGE_MODIFY,   // Object modified
    ARX_CHANGE_MOVE,     // Object moved
    ARX_CHANGE_RENAME    // Object renamed
} ArxChangeType;

/**
 * @brief Change record for tracking object modifications
 */
typedef struct ArxChange {
    ArxChangeType type;
    char* object_id;
    char* old_object_id;  // For renames/moves
    ArxObject* old_object; // For modifications (snapshot)
    ArxObject* new_object; // For modifications/additions
    ArxPoint3D old_position; // For moves
    ArxPoint3D new_position; // For moves
    time_t timestamp;
    char* author;
    char* message;
} ArxChange;

/**
 * @brief Diff between two states
 */
typedef struct ArxDiff {
    char* from_commit;
    char* to_commit;
    ArxChange** changes;
    int change_count;
    time_t created_at;
    char* summary;
} ArxDiff;

/**
 * @brief Commit structure
 */
typedef struct ArxCommit {
    char* hash;           // SHA-256 hash of commit
    char* message;        // Commit message
    time_t timestamp;     // Commit timestamp
    char* author;         // Author name
    char* email;          // Author email
    
    // Change tracking
    ArxChange** changes;  // Array of changes in this commit
    int change_count;     // Number of changes
    
    // Parent relationships
    char* parent_hash;    // Parent commit hash
    char** parent_hashes; // For merge commits
    int parent_count;     // Number of parents
    
    // Metadata
    char* branch_name;    // Branch this commit was made on
    bool is_merge;        // Is this a merge commit
    bool is_tagged;       // Is this commit tagged
    char* tag_name;       // Tag name if tagged
} ArxCommit;

/**
 * @brief Branch structure
 */
typedef struct ArxBranch {
    char* name;           // Branch name
    char* head_commit;    // Current HEAD commit hash
    char* upstream;       // Upstream branch name
    bool is_remote;       // Is this a remote branch
    bool is_current;      // Is this the current branch
    time_t last_updated;  // Last update time
    char* description;    // Branch description
} ArxBranch;

/**
 * @brief Repository configuration
 */
typedef struct {
    char* name;           // Repository name
    char* description;    // Repository description
    char* author_name;    // Default author name
    char* author_email;   // Default author email
    char* default_branch; // Default branch name
    bool auto_commit;     // Auto-commit changes
    int max_history;      // Maximum history to keep
    bool compression;     // Enable compression
} ArxRepoConfig;

/**
 * @brief Main version control structure
 */
typedef struct ArxVersionControl {
    ArxRepoConfig config;
    
    // Repository state
    char* repo_path;      // Repository file path
    char* current_branch; // Current branch name
    bool is_initialized;  // Is repository initialized
    
    // Commit history
    ArxCommit** commits;  // All commits
    int commit_count;     // Number of commits
    int commit_capacity;  // Capacity of commits array
    
    // Branch management
    ArxBranch** branches; // All branches
    int branch_count;     // Number of branches
    int branch_capacity;  // Capacity of branches array
    
    // Working state
    ArxChange** staged_changes;   // Staged changes
    int staged_count;             // Number of staged changes
    int staged_capacity;          // Capacity of staged array
    
    ArxChange** working_changes;  // Working directory changes
    int working_count;            // Number of working changes
    int working_capacity;         // Capacity of working array
    
    // Thread safety
    pthread_rwlock_t lock;
    
    // Memory management
    bool is_allocated;
} ArxVersionControl;

// ============================================================================
// REPOSITORY MANAGEMENT
// ============================================================================

/**
 * @brief Initialize a new version control repository
 * @param repo_path Path to repository
 * @param config Repository configuration
 * @return New ArxVersionControl instance or NULL on failure
 */
ArxVersionControl* arx_version_init_repo(const char* repo_path, const ArxRepoConfig* config);

/**
 * @brief Open an existing repository
 * @param repo_path Path to repository
 * @return ArxVersionControl instance or NULL on failure
 */
ArxVersionControl* arx_version_open_repo(const char* repo_path);

/**
 * @brief Close and cleanup repository
 * @param vc Version control instance to close
 */
void arx_version_close_repo(ArxVersionControl* vc);

/**
 * @brief Check if repository is initialized
 * @param vc Version control instance
 * @return true if initialized, false otherwise
 */
bool arx_version_is_initialized(const ArxVersionControl* vc);

// ============================================================================
// COMMIT MANAGEMENT
// ============================================================================

/**
 * @brief Create a new commit
 * @param vc Version control instance
 * @param message Commit message
 * @param author Author name (NULL for default)
 * @param email Author email (NULL for default)
 * @return New commit hash or NULL on failure
 */
char* arx_version_commit(ArxVersionControl* vc, const char* message, 
                        const char* author, const char* email);

/**
 * @brief Get commit by hash
 * @param vc Version control instance
 * @param hash Commit hash
 * @return ArxCommit pointer or NULL if not found
 */
ArxCommit* arx_version_get_commit(const ArxVersionControl* vc, const char* hash);

/**
 * @brief Get commit history
 * @param vc Version control instance
 * @param start_hash Starting commit hash (NULL for HEAD)
 * @param max_count Maximum number of commits to return
 * @param count Output parameter for actual count
 * @return Array of ArxCommit pointers or NULL if none found
 */
ArxCommit** arx_version_get_history(const ArxVersionControl* vc, 
                                   const char* start_hash, int max_count, int* count);

/**
 * @brief Get commit diff
 * @param vc Version control instance
 * @param from_hash From commit hash
 * @param to_hash To commit hash
 * @return ArxDiff pointer or NULL on failure
 */
ArxDiff* arx_version_get_diff(const ArxVersionControl* vc, 
                              const char* from_hash, const char* to_hash);

// ============================================================================
// BRANCH MANAGEMENT
// ============================================================================

/**
 * @brief Create a new branch
 * @param vc Version control instance
 * @param branch_name Branch name
 * @param start_point Starting commit hash (NULL for current HEAD)
 * @return true on success, false on failure
 */
bool arx_version_create_branch(ArxVersionControl* vc, const char* branch_name, 
                              const char* start_point);

/**
 * @brief Switch to a branch
 * @param vc Version control instance
 * @param branch_name Branch name to switch to
 * @return true on success, false on failure
 */
bool arx_version_checkout_branch(ArxVersionControl* vc, const char* branch_name);

/**
 * @brief Delete a branch
 * @param vc Version control instance
 * @param branch_name Branch name to delete
 * @param force Force deletion even if not merged
 * @return true on success, false on failure
 */
bool arx_version_delete_branch(ArxVersionControl* vc, const char* branch_name, bool force);

/**
 * @brief Get all branches
 * @param vc Version control instance
 * @param count Output parameter for number of branches
 * @return Array of ArxBranch pointers or NULL if none found
 */
ArxBranch** arx_version_get_branches(const ArxVersionControl* vc, int* count);

/**
 * @brief Get current branch
 * @param vc Version control instance
 * @return Current branch name or NULL if none
 */
const char* arx_version_get_current_branch(const ArxVersionControl* vc);

// ============================================================================
// CHANGE TRACKING
// ============================================================================

/**
 * @brief Stage changes for commit
 * @param vc Version control instance
 * @param changes Array of changes to stage
 * @param change_count Number of changes
 * @return true on success, false on failure
 */
bool arx_version_stage_changes(ArxVersionControl* vc, ArxChange** changes, int change_count);

/**
 * @brief Unstage changes
 * @param vc Version control instance
 * @param changes Array of changes to unstage
 * @param change_count Number of changes
 * @return true on success, false on failure
 */
bool arx_version_unstage_changes(ArxVersionControl* vc, ArxChange** changes, int change_count);

/**
 * @brief Get staged changes
 * @param vc Version control instance
 * @param count Output parameter for number of staged changes
 * @return Array of ArxChange pointers or NULL if none staged
 */
ArxChange** arx_version_get_staged_changes(const ArxVersionControl* vc, int* count);

/**
 * @brief Get working directory changes
 * @param vc Version control instance
 * @param count Output parameter for number of working changes
 * @return Array of ArxChange pointers or NULL if none
 */
ArxChange** arx_version_get_working_changes(const ArxVersionControl* vc, int* count);

/**
 * @brief Reset working directory to last commit
 * @param vc Version control instance
 * @param hard Hard reset (discard all changes)
 * @return true on success, false on failure
 */
bool arx_version_reset_working_directory(ArxVersionControl* vc, bool hard);

// ============================================================================
// MERGE OPERATIONS
// ============================================================================

/**
 * @brief Merge a branch into current branch
 * @param vc Version control instance
 * @param source_branch Source branch to merge
 * @param message Merge commit message
 * @return true on success, false on failure
 */
bool arx_version_merge_branch(ArxVersionControl* vc, const char* source_branch, 
                             const char* message);

/**
 * @brief Check for merge conflicts
 * @param vc Version control instance
 * @param count Output parameter for number of conflicts
 * @return Array of conflict descriptions or NULL if no conflicts
 */
char** arx_version_check_merge_conflicts(const ArxVersionControl* vc, int* count);

/**
 * @brief Resolve merge conflicts
 * @param vc Version control instance
 * @param resolutions Array of conflict resolutions
 * @param resolution_count Number of resolutions
 * @return true on success, false on failure
 */
bool arx_version_resolve_merge_conflicts(ArxVersionControl* vc, 
                                       const char** resolutions, int resolution_count);

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

/**
 * @brief Generate commit hash
 * @param commit Commit to hash
 * @return Generated hash string or NULL on failure
 */
char* arx_version_generate_hash(const ArxCommit* commit);

/**
 * @brief Get repository status
 * @param vc Version control instance
 * @return Status string or NULL on failure
 */
char* arx_version_get_status(const ArxVersionControl* vc);

/**
 * @brief Get repository statistics
 * @param vc Version control instance
 * @return Statistics string or NULL on failure
 */
char* arx_version_get_stats(const ArxVersionControl* vc);

/**
 * @brief Check if repository has uncommitted changes
 * @param vc Version control instance
 * @return true if has changes, false otherwise
 */
bool arx_version_has_uncommitted_changes(const ArxVersionControl* vc);

/**
 * @brief Get repository memory usage
 * @param vc Version control instance
 * @return Memory usage in bytes
 */
size_t arx_version_get_memory_usage(const ArxVersionControl* vc);

#ifdef __cplusplus
}
#endif

#endif // ARX_VERSION_H
