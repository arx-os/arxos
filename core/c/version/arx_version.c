/**
 * @file arx_version.c
 * @brief ArxVersionControl System Implementation
 * 
 * Implements Git-like version control for building data, including commits,
 * branches, diffs, and change tracking. Enables building infrastructure
 * as code with full history and rollback capabilities.
 */

#include "arx_version.h"
#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#include <pthread.h>
#include <time.h>
#include <openssl/sha.h>

// ============================================================================
// INTERNAL HELPER FUNCTIONS
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
 * @brief Free string safely
 */
static void safe_free(char* str) {
    if (str) {
        free(str);
    }
}

/**
 * @brief Generate SHA-256 hash for commit
 */
static char* generate_commit_hash(const ArxCommit* commit) {
    if (!commit) return NULL;
    
    // Create hash input string
    char hash_input[1024];
    snprintf(hash_input, sizeof(hash_input), "%s%s%ld%s%s",
             commit->message ? commit->message : "",
             commit->author ? commit->author : "",
             commit->timestamp,
             commit->parent_hash ? commit->parent_hash : "",
             commit->branch_name ? commit->branch_name : "");
    
    // Generate SHA-256 hash
    unsigned char hash[SHA256_DIGEST_LENGTH];
    SHA256((unsigned char*)hash_input, strlen(hash_input), hash);
    
    // Convert to hex string
    char* hash_str = malloc(SHA256_DIGEST_LENGTH * 2 + 1);
    if (!hash_str) return NULL;
    
    for (int i = 0; i < SHA256_DIGEST_LENGTH; i++) {
        sprintf(hash_str + (i * 2), "%02x", hash[i]);
    }
    
    return hash_str;
}

/**
 * @brief Ensure array capacity
 */
static bool ensure_array_capacity(void** array, int* count, int* capacity, size_t element_size) {
    if (*count >= *capacity) {
        int new_capacity = *capacity == 0 ? 16 : *capacity * 2;
        void** new_array = realloc(*array, new_capacity * element_size);
        if (!new_array) return false;
        
        *array = new_array;
        *capacity = new_capacity;
    }
    return true;
}

/**
 * @brief Initialize repository configuration with defaults
 */
static void init_repo_config(ArxRepoConfig* config) {
    config->name = NULL;
    config->description = NULL;
    config->author_name = safe_strdup("ARXOS User");
    config->author_email = safe_strdup("user@arxos.com");
    config->default_branch = safe_strdup("main");
    config->auto_commit = false;
    config->max_history = 1000;
    config->compression = true;
}

/**
 * @brief Initialize version control structure
 */
static void init_version_control(ArxVersionControl* vc) {
    vc->repo_path = NULL;
    vc->current_branch = safe_strdup("main");
    vc->is_initialized = false;
    
    vc->commits = NULL;
    vc->commit_count = 0;
    vc->commit_capacity = 0;
    
    vc->branches = NULL;
    vc->branch_count = 0;
    vc->branch_capacity = 0;
    
    vc->staged_changes = NULL;
    vc->staged_count = 0;
    vc->staged_capacity = 0;
    
    vc->working_changes = NULL;
    vc->working_count = 0;
    vc->working_capacity = 0;
    
    vc->is_allocated = true;
}

// ============================================================================
// REPOSITORY MANAGEMENT
// ============================================================================

ArxVersionControl* arx_version_init_repo(const char* repo_path, const ArxRepoConfig* config) {
    if (!repo_path) return NULL;
    
    ArxVersionControl* vc = malloc(sizeof(ArxVersionControl));
    if (!vc) return NULL;
    
    // Initialize configuration
    if (config) {
        vc->config = *config;
        // Deep copy strings
        vc->config.name = safe_strdup(config->name);
        vc->config.description = safe_strdup(config->description);
        vc->config.author_name = safe_strdup(config->author_name);
        vc->config.author_email = safe_strdup(config->author_email);
        vc->config.default_branch = safe_strdup(config->default_branch);
    } else {
        init_repo_config(&vc->config);
    }
    
    // Initialize structure
    init_version_control(vc);
    vc->repo_path = safe_strdup(repo_path);
    
    // Initialize thread safety
    if (pthread_rwlock_init(&vc->lock, NULL) != 0) {
        arx_version_close_repo(vc);
        return NULL;
    }
    
    // Create initial branch
    ArxBranch* main_branch = malloc(sizeof(ArxBranch));
    if (main_branch) {
        main_branch->name = safe_strdup(vc->config.default_branch);
        main_branch->head_commit = NULL;
        main_branch->upstream = NULL;
        main_branch->is_remote = false;
        main_branch->is_current = true;
        main_branch->last_updated = time(NULL);
        main_branch->description = safe_strdup("Main development branch");
        
        vc->branches[0] = main_branch;
        vc->branch_count = 1;
        vc->branch_capacity = 16;
        vc->branches = malloc(16 * sizeof(ArxBranch*));
        vc->branches[0] = main_branch;
    }
    
    vc->is_initialized = true;
    return vc;
}

ArxVersionControl* arx_version_open_repo(const char* repo_path) {
    if (!repo_path) return NULL;
    
    // TODO: Implement loading existing repository from disk
    // For now, create a new repository
    ArxRepoConfig config = {0};
    return arx_version_init_repo(repo_path, &config);
}

void arx_version_close_repo(ArxVersionControl* vc) {
    if (!vc) return;
    
    // Acquire write lock
    pthread_rwlock_wrlock(&vc->lock);
    
    // Free configuration strings
    safe_free(vc->config.name);
    safe_free(vc->config.description);
    safe_free(vc->config.author_name);
    safe_free(vc->config.author_email);
    safe_free(vc->config.default_branch);
    
    // Free repository path
    safe_free(vc->repo_path);
    safe_free(vc->current_branch);
    
    // Free commits
    for (int i = 0; i < vc->commit_count; i++) {
        if (vc->commits[i]) {
            // Free commit strings
            safe_free(vc->commits[i]->hash);
            safe_free(vc->commits[i]->message);
            safe_free(vc->commits[i]->author);
            safe_free(vc->commits[i]->email);
            safe_free(vc->commits[i]->parent_hash);
            safe_free(vc->commits[i]->branch_name);
            safe_free(vc->commits[i]->tag_name);
            
            // Free parent hashes array
            if (vc->commits[i]->parent_hashes) {
                for (int j = 0; j < vc->commits[i]->parent_count; j++) {
                    safe_free(vc->commits[i]->parent_hashes[j]);
                }
                free(vc->commits[i]->parent_hashes);
            }
            
            // Free changes array
            if (vc->commits[i]->changes) {
                for (int j = 0; j < vc->commits[i]->change_count; j++) {
                    if (vc->commits[i]->changes[j]) {
                        safe_free(vc->commits[i]->changes[j]->object_id);
                        safe_free(vc->commits[i]->changes[j]->old_object_id);
                        safe_free(vc->commits[i]->changes[j]->author);
                        safe_free(vc->commits[i]->changes[j]->message);
                        free(vc->commits[i]->changes[j]);
                    }
                }
                free(vc->commits[i]->changes);
            }
            
            free(vc->commits[i]);
        }
    }
    free(vc->commits);
    
    // Free branches
    for (int i = 0; i < vc->branch_count; i++) {
        if (vc->branches[i]) {
            safe_free(vc->branches[i]->name);
            safe_free(vc->branches[i]->head_commit);
            safe_free(vc->branches[i]->upstream);
            safe_free(vc->branches[i]->description);
            free(vc->branches[i]);
        }
    }
    free(vc->branches);
    
    // Free staged changes
    for (int i = 0; i < vc->staged_count; i++) {
        if (vc->staged_changes[i]) {
            safe_free(vc->staged_changes[i]->object_id);
            safe_free(vc->staged_changes[i]->old_object_id);
            safe_free(vc->staged_changes[i]->author);
            safe_free(vc->staged_changes[i]->message);
            free(vc->staged_changes[i]);
        }
    }
    free(vc->staged_changes);
    
    // Free working changes
    for (int i = 0; i < vc->working_count; i++) {
        if (vc->working_changes[i]) {
            safe_free(vc->working_changes[i]->object_id);
            safe_free(vc->working_changes[i]->old_object_id);
            safe_free(vc->working_changes[i]->author);
            safe_free(vc->working_changes[i]->message);
            free(vc->working_changes[i]);
        }
    }
    free(vc->working_changes);
    
    // Destroy thread lock
    pthread_rwlock_unlock(&vc->lock);
    pthread_rwlock_destroy(&vc->lock);
    
    // Free version control structure
    free(vc);
}

bool arx_version_is_initialized(const ArxVersionControl* vc) {
    if (!vc) return false;
    
    pthread_rwlock_rdlock((pthread_rwlock_t*)&vc->lock);
    bool initialized = vc->is_initialized;
    pthread_rwlock_unlock((pthread_rwlock_t*)&vc->lock);
    
    return initialized;
}

// ============================================================================
// COMMIT MANAGEMENT
// ============================================================================

char* arx_version_commit(ArxVersionControl* vc, const char* message, 
                        const char* author, const char* email) {
    if (!vc || !message) return NULL;
    
    pthread_rwlock_wrlock(&vc->lock);
    
    // Create new commit
    ArxCommit* commit = malloc(sizeof(ArxCommit));
    if (!commit) {
        pthread_rwlock_unlock(&vc->lock);
        return NULL;
    }
    
    // Initialize commit
    commit->message = safe_strdup(message);
    commit->author = safe_strdup(author ? author : vc->config.author_name);
    commit->email = safe_strdup(email ? email : vc->config.author_email);
    commit->timestamp = time(NULL);
    commit->branch_name = safe_strdup(vc->current_branch);
    commit->is_merge = false;
    commit->is_tagged = false;
    commit->tag_name = NULL;
    
    // Set parent hash (current HEAD)
    if (vc->commit_count > 0) {
        commit->parent_hash = safe_strdup(vc->commits[vc->commit_count - 1]->hash);
        commit->parent_count = 1;
        commit->parent_hashes = malloc(sizeof(char*));
        commit->parent_hashes[0] = safe_strdup(commit->parent_hash);
    } else {
        commit->parent_hash = NULL;
        commit->parent_count = 0;
        commit->parent_hashes = NULL;
    }
    
    // Copy staged changes
    commit->changes = malloc(vc->staged_count * sizeof(ArxChange*));
    commit->change_count = vc->staged_count;
    
    for (int i = 0; i < vc->staged_count; i++) {
        if (vc->staged_changes[i]) {
            commit->changes[i] = malloc(sizeof(ArxChange));
            if (commit->changes[i]) {
                *commit->changes[i] = *vc->staged_changes[i];
                // Deep copy strings
                commit->changes[i]->object_id = safe_strdup(vc->staged_changes[i]->object_id);
                commit->changes[i]->old_object_id = safe_strdup(vc->staged_changes[i]->old_object_id);
                commit->changes[i]->author = safe_strdup(vc->staged_changes[i]->author);
                commit->changes[i]->message = safe_strdup(vc->staged_changes[i]->message);
            }
        }
    }
    
    // Generate commit hash
    commit->hash = generate_commit_hash(commit);
    
    // Add commit to repository
    if (!ensure_array_capacity((void**)&vc->commits, &vc->commit_count, 
                              &vc->commit_capacity, sizeof(ArxCommit*))) {
        // Cleanup on failure
        free(commit);
        pthread_rwlock_unlock(&vc->lock);
        return NULL;
    }
    
    vc->commits[vc->commit_count] = commit;
    vc->commit_count++;
    
    // Update current branch HEAD
    for (int i = 0; i < vc->branch_count; i++) {
        if (vc->branches[i] && vc->branches[i]->is_current) {
            vc->branches[i]->head_commit = safe_strdup(commit->hash);
            vc->branches[i]->last_updated = commit->timestamp;
            break;
        }
    }
    
    // Clear staged changes
    for (int i = 0; i < vc->staged_count; i++) {
        if (vc->staged_changes[i]) {
            safe_free(vc->staged_changes[i]->object_id);
            safe_free(vc->staged_changes[i]->old_object_id);
            safe_free(vc->staged_changes[i]->author);
            safe_free(vc->staged_changes[i]->message);
            free(vc->staged_changes[i]);
        }
    }
    vc->staged_count = 0;
    
    pthread_rwlock_unlock(&vc->lock);
    
    return safe_strdup(commit->hash);
}

ArxCommit* arx_version_get_commit(const ArxVersionControl* vc, const char* hash) {
    if (!vc || !hash) return NULL;
    
    pthread_rwlock_rdlock((pthread_rwlock_t*)&vc->lock);
    
    for (int i = 0; i < vc->commit_count; i++) {
        if (vc->commits[i] && strcmp(vc->commits[i]->hash, hash) == 0) {
            ArxCommit* commit = vc->commits[i];
            pthread_rwlock_unlock((pthread_rwlock_t*)&vc->lock);
            return commit;
        }
    }
    
    pthread_rwlock_unlock((pthread_rwlock_t*)&vc->lock);
    return NULL;
}

ArxCommit** arx_version_get_history(const ArxVersionControl* vc, 
                                   const char* start_hash, int max_count, int* count) {
    if (!vc || !count) {
        if (count) *count = 0;
        return NULL;
    }
    
    pthread_rwlock_rdlock((pthread_rwlock_t*)&vc->lock);
    
    int start_index = 0;
    if (start_hash) {
        // Find start commit
        for (int i = 0; i < vc->commit_count; i++) {
            if (vc->commits[i] && strcmp(vc->commits[i]->hash, start_hash) == 0) {
                start_index = i;
                break;
            }
        }
    }
    
    int available_count = vc->commit_count - start_index;
    int result_count = (max_count > 0 && max_count < available_count) ? max_count : available_count;
    
    if (result_count <= 0) {
        *count = 0;
        pthread_rwlock_unlock((pthread_rwlock_t*)&vc->lock);
        return NULL;
    }
    
    // Allocate result array
    ArxCommit** result = malloc(result_count * sizeof(ArxCommit*));
    if (!result) {
        *count = 0;
        pthread_rwlock_unlock((pthread_rwlock_t*)&vc->lock);
        return NULL;
    }
    
    // Copy commits (in reverse chronological order)
    for (int i = 0; i < result_count; i++) {
        result[i] = vc->commits[start_index + i];
    }
    
    *count = result_count;
    pthread_rwlock_unlock((pthread_rwlock_t*)&vc->lock);
    return result;
}

ArxDiff* arx_version_get_diff(const ArxVersionControl* vc, 
                              const char* from_hash, const char* to_hash) {
    if (!vc || !from_hash || !to_hash) return NULL;
    
    // TODO: Implement diff generation
    // This would compare the two commits and generate a list of changes
    
    ArxDiff* diff = malloc(sizeof(ArxDiff));
    if (!diff) return NULL;
    
    diff->from_commit = safe_strdup(from_hash);
    diff->to_commit = safe_strdup(to_hash);
    diff->changes = NULL;
    diff->change_count = 0;
    diff->created_at = time(NULL);
    diff->summary = safe_strdup("Diff not yet implemented");
    
    return diff;
}

// ============================================================================
// BRANCH MANAGEMENT
// ============================================================================

bool arx_version_create_branch(ArxVersionControl* vc, const char* branch_name, 
                              const char* start_point) {
    if (!vc || !branch_name) return false;
    
    pthread_rwlock_wrlock(&vc->lock);
    
    // Check if branch already exists
    for (int i = 0; i < vc->branch_count; i++) {
        if (vc->branches[i] && strcmp(vc->branches[i]->name, branch_name) == 0) {
            pthread_rwlock_unlock(&vc->lock);
            return false; // Branch already exists
        }
    }
    
    // Create new branch
    ArxBranch* branch = malloc(sizeof(ArxBranch));
    if (!branch) {
        pthread_rwlock_unlock(&vc->lock);
        return false;
    }
    
    branch->name = safe_strdup(branch_name);
    branch->upstream = NULL;
    branch->is_remote = false;
    branch->is_current = false;
    branch->last_updated = time(NULL);
    branch->description = safe_strdup("New branch");
    
    // Set head commit
    if (start_point) {
        branch->head_commit = safe_strdup(start_point);
    } else if (vc->commit_count > 0) {
        branch->head_commit = safe_strdup(vc->commits[vc->commit_count - 1]->hash);
    } else {
        branch->head_commit = NULL;
    }
    
    // Add branch to repository
    if (!ensure_array_capacity((void**)&vc->branches, &vc->branch_count, 
                              &vc->branch_capacity, sizeof(ArxBranch*))) {
        free(branch);
        pthread_rwlock_unlock(&vc->lock);
        return false;
    }
    
    vc->branches[vc->branch_count] = branch;
    vc->branch_count++;
    
    pthread_rwlock_unlock(&vc->lock);
    return true;
}

bool arx_version_checkout_branch(ArxVersionControl* vc, const char* branch_name) {
    if (!vc || !branch_name) return false;
    
    pthread_rwlock_wrlock(&vc->lock);
    
    // Find branch
    ArxBranch* target_branch = NULL;
    for (int i = 0; i < vc->branch_count; i++) {
        if (vc->branches[i] && strcmp(vc->branches[i]->name, branch_name) == 0) {
            target_branch = vc->branches[i];
            break;
        }
    }
    
    if (!target_branch) {
        pthread_rwlock_unlock(&vc->lock);
        return false; // Branch not found
    }
    
    // Update current branch
    for (int i = 0; i < vc->branch_count; i++) {
        if (vc->branches[i]) {
            vc->branches[i]->is_current = (vc->branches[i] == target_branch);
        }
    }
    
    vc->current_branch = safe_strdup(branch_name);
    
    pthread_rwlock_unlock(&vc->lock);
    return true;
}

bool arx_version_delete_branch(ArxVersionControl* vc, const char* branch_name, bool force) {
    if (!vc || !branch_name) return false;
    
    pthread_rwlock_wrlock(&vc->lock);
    
    for (int i = 0; i < vc->branch_count; i++) {
        if (vc->branches[i] && strcmp(vc->branches[i]->name, branch_name) == 0) {
            // Check if it's the current branch
            if (vc->branches[i]->is_current && !force) {
                pthread_rwlock_unlock(&vc->lock);
                return false; // Cannot delete current branch without force
            }
            
            // Free branch resources
            safe_free(vc->branches[i]->name);
            safe_free(vc->branches[i]->head_commit);
            safe_free(vc->branches[i]->upstream);
            safe_free(vc->branches[i]->description);
            free(vc->branches[i]);
            
            // Remove from array
            for (int j = i; j < vc->branch_count - 1; j++) {
                vc->branches[j] = vc->branches[j + 1];
            }
            vc->branch_count--;
            
            pthread_rwlock_unlock(&vc->lock);
            return true;
        }
    }
    
    pthread_rwlock_unlock(&vc->lock);
    return false; // Branch not found
}

ArxBranch** arx_version_get_branches(const ArxVersionControl* vc, int* count) {
    if (!vc || !count) {
        if (count) *count = 0;
        return NULL;
    }
    
    pthread_rwlock_rdlock((pthread_rwlock_t*)&vc->lock);
    
    if (vc->branch_count == 0) {
        *count = 0;
        pthread_rwlock_unlock((pthread_rwlock_t*)&vc->lock);
        return NULL;
    }
    
    // Allocate result array
    ArxBranch** result = malloc(vc->branch_count * sizeof(ArxBranch*));
    if (!result) {
        *count = 0;
        pthread_rwlock_unlock((pthread_rwlock_t*)&vc->lock);
        return NULL;
    }
    
    // Copy branch pointers
    for (int i = 0; i < vc->branch_count; i++) {
        result[i] = vc->branches[i];
    }
    
    *count = vc->branch_count;
    pthread_rwlock_unlock((pthread_rwlock_t*)&vc->lock);
    return result;
}

const char* arx_version_get_current_branch(const ArxVersionControl* vc) {
    if (!vc) return NULL;
    
    pthread_rwlock_rdlock((pthread_rwlock_t*)&vc->lock);
    const char* current = vc->current_branch;
    pthread_rwlock_unlock((pthread_rwlock_t*)&vc->lock);
    
    return current;
}

// ============================================================================
// CHANGE TRACKING
// ============================================================================

bool arx_version_stage_changes(ArxVersionControl* vc, ArxChange** changes, int change_count) {
    if (!vc || !changes || change_count <= 0) return false;
    
    pthread_rwlock_wrlock(&vc->lock);
    
    // Add each change to staged
    for (int i = 0; i < change_count; i++) {
        if (changes[i]) {
            if (!ensure_array_capacity((void**)&vc->staged_changes, &vc->staged_count, 
                                     &vc->staged_capacity, sizeof(ArxChange*))) {
                pthread_rwlock_unlock(&vc->lock);
                return false;
            }
            
            // Create copy of change
            ArxChange* staged_change = malloc(sizeof(ArxChange));
            if (staged_change) {
                *staged_change = *changes[i];
                // Deep copy strings
                staged_change->object_id = safe_strdup(changes[i]->object_id);
                staged_change->old_object_id = safe_strdup(changes[i]->old_object_id);
                staged_change->author = safe_strdup(changes[i]->author);
                staged_change->message = safe_strdup(changes[i]->message);
                
                vc->staged_changes[vc->staged_count] = staged_change;
                vc->staged_count++;
            }
        }
    }
    
    pthread_rwlock_unlock(&vc->lock);
    return true;
}

ArxChange** arx_version_get_staged_changes(const ArxVersionControl* vc, int* count) {
    if (!vc || !count) {
        if (count) *count = 0;
        return NULL;
    }
    
    pthread_rwlock_rdlock((pthread_rwlock_t*)&vc->lock);
    
    if (vc->staged_count == 0) {
        *count = 0;
        pthread_rwlock_unlock((pthread_rwlock_t*)&vc->lock);
        return NULL;
    }
    
    // Allocate result array
    ArxChange** result = malloc(vc->staged_count * sizeof(ArxChange*));
    if (!result) {
        *count = 0;
        pthread_rwlock_unlock((pthread_rwlock_t*)&vc->lock);
        return NULL;
    }
    
    // Copy staged changes
    for (int i = 0; i < vc->staged_count; i++) {
        result[i] = vc->staged_changes[i];
    }
    
    *count = vc->staged_count;
    pthread_rwlock_unlock((pthread_rwlock_t*)&vc->lock);
    return result;
}

bool arx_version_has_uncommitted_changes(const ArxVersionControl* vc) {
    if (!vc) return false;
    
    pthread_rwlock_rdlock((pthread_rwlock_t*)&vc->lock);
    bool has_changes = (vc->staged_count > 0 || vc->working_count > 0);
    pthread_rwlock_unlock((pthread_rwlock_t*)&vc->lock);
    
    return has_changes;
}

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

char* arx_version_get_status(const ArxVersionControl* vc) {
    if (!vc) return NULL;
    
    pthread_rwlock_rdlock((pthread_rwlock_t*)&vc->lock);
    
    // Calculate required buffer size
    size_t buffer_size = 1024;
    char* status = malloc(buffer_size);
    if (!status) {
        pthread_rwlock_unlock((pthread_rwlock_t*)&vc->lock);
        return NULL;
    }
    
    snprintf(status, buffer_size,
             "Repository: %s\n"
             "Current Branch: %s\n"
             "Total Commits: %d\n"
             "Total Branches: %d\n"
             "Staged Changes: %d\n"
             "Working Changes: %d\n"
             "Last Commit: %s",
             vc->repo_path ? vc->repo_path : "Unknown",
             vc->current_branch ? vc->current_branch : "Unknown",
             vc->commit_count,
             vc->branch_count,
             vc->staged_count,
             vc->working_count,
             vc->commit_count > 0 ? 
                 ctime(&vc->commits[vc->commit_count - 1]->timestamp) : "None");
    
    pthread_rwlock_unlock((pthread_rwlock_t*)&vc->lock);
    return status;
}

size_t arx_version_get_memory_usage(const ArxVersionControl* vc) {
    if (!vc) return 0;
    
    size_t usage = sizeof(ArxVersionControl);
    
    // Add configuration string sizes
    if (vc->config.name) usage += strlen(vc->config.name) + 1;
    if (vc->config.description) usage += strlen(vc->config.description) + 1;
    if (vc->config.author_name) usage += strlen(vc->config.author_name) + 1;
    if (vc->config.author_email) usage += strlen(vc->config.author_email) + 1;
    if (vc->config.default_branch) usage += strlen(vc->config.default_branch) + 1;
    
    // Add repository path and current branch
    if (vc->repo_path) usage += strlen(vc->repo_path) + 1;
    if (vc->current_branch) usage += strlen(vc->current_branch) + 1;
    
    // Add commits array size
    usage += vc->commit_capacity * sizeof(ArxCommit*);
    
    // Add branches array size
    usage += vc->branch_capacity * sizeof(ArxBranch*);
    
    // Add staged and working changes array sizes
    usage += vc->staged_capacity * sizeof(ArxChange*);
    usage += vc->working_capacity * sizeof(ArxChange*);
    
    return usage;
}
