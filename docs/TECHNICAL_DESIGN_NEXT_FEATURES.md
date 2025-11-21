# Technical Design and Architecture Plan
## Next Priority Features Implementation

**Project:** ArxOS CLI Enhancement
**Version:** 2.0
**Date:** 2025-11-20
**Author:** Technical Design Team
**Status:** Design Phase

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Architecture Overview](#architecture-overview)
3. [Feature 1: Unstage Command](#feature-1-unstage-command)
4. [Feature 2: History Command](#feature-2-history-command)
5. [Feature 3: Building Import/Export](#feature-3-building-importexport)
6. [Feature 4: Query Operations](#feature-4-query-operations)
7. [Integration Architecture](#integration-architecture)
8. [Testing Strategy](#testing-strategy)
9. [Performance Considerations](#performance-considerations)
10. [Security Considerations](#security-considerations)
11. [Deployment Plan](#deployment-plan)
12. [Future Extensibility](#future-extensibility)

---

## Executive Summary

This document provides a comprehensive technical design for implementing the next four high-priority features for the ArxOS CLI:

1. **Unstage Command** - Complete git workflow by enabling users to unstage changes
2. **History Command** - View commit logs and repository history
3. **Building Import/Export** - Import IFC files and export building data
4. **Query Operations** - Search and query building data using ArxAddress patterns

### Design Principles

- **Consistency**: Follow existing CLI patterns established in status/stage/commit commands
- **Reusability**: Leverage existing modules (git, ifc, core/operations)
- **Testability**: Design for comprehensive unit and integration testing
- **Performance**: Optimize for large building files and repositories
- **User Experience**: Clear, helpful output with proper error messages
- **Extensibility**: Design for future enhancements (TUI, batch operations)

### Implementation Priorities

| Feature | Priority | Complexity | Estimated LOC | Existing Code Reuse |
|---------|----------|------------|---------------|---------------------|
| Unstage Command | HIGH | Low | ~50 | 95% (git/staging.rs) |
| History Command | HIGH | Low | ~80 | 90% (git/diff.rs) |
| Building Import/Export | MEDIUM | Medium | ~200 | 80% (agent/ifc.rs) |
| Query Operations | MEDIUM | Medium | ~250 | 70% (core/domain/address.rs) |

---

## Architecture Overview

### Current CLI Architecture Pattern

```
User Input (clap CLI)
    ↓
Cli::execute() [cli/mod.rs]
    ↓
match Commands::*
    ↓
Handler Method (handle_*)
    ↓
Module Functions (git::*, core::operations::*)
    ↓
Result<Output, Error>
    ↓
Formatted Console Output
```

### Module Dependencies

```
cli/mod.rs
  ├── git::manager::BuildingGitManager
  │   ├── git::staging (stage, unstage)
  │   ├── git::commit (commit operations)
  │   ├── git::diff (status, diff, history)
  │   └── git::repository (repo management)
  │
  ├── agent::ifc (IFC import/export)
  │   ├── ifc::IFCProcessor
  │   └── export::ifc::IFCExporter
  │
  ├── core::operations
  │   ├── equipment (CRUD operations)
  │   ├── room (room operations)
  │   └── spatial (spatial queries)
  │
  └── core::domain::ArxAddress (addressing system)
```

### Error Handling Strategy

All features follow the established pattern:
- Return `Result<(), Box<dyn std::error::Error>>`
- Convert module-specific errors to Box<dyn Error>
- Provide user-friendly error messages
- Log errors for debugging when applicable

---

## Feature 1: Unstage Command

### Overview

Complete the git workflow by implementing the unstage command, allowing users to remove files from the staging area.

### User Stories

**As a user:**
- I want to unstage all staged files so I can start over with staging
- I want to unstage a specific file so I can exclude it from the next commit
- I want clear feedback about what was unstaged

### Technical Design

#### CLI Interface

```bash
# Unstage all files
arx unstage
arx unstage --all

# Unstage specific file
arx unstage building.yaml
arx unstage imports/floor-2.ifc

# With verbose output
arx unstage --verbose
```

#### Command Arguments

```rust
/// Unstage changes
Unstage {
    /// Unstage all files
    #[arg(long)]
    all: bool,
    /// Specific file to unstage
    file: Option<String>,
},
```

#### Implementation

**File:** `src/cli/mod.rs`

**Handler Method:**
```rust
fn handle_unstage(all: bool, file: Option<String>) -> Result<(), Box<dyn std::error::Error>> {
    use crate::git::manager::{BuildingGitManager, GitConfigManager};

    let config = GitConfigManager::load_from_arx_config_or_env();
    let mut manager = BuildingGitManager::new(".", "current", config)?;

    if all || file.is_none() {
        let count = manager.unstage_all()?;
        println!("✅ Unstaged {} file(s)", count);
        println!("💡 Files reset to HEAD state");
    } else if let Some(path) = file {
        manager.unstage_file(&path)?;
        println!("✅ Unstaged: {}", path);
    }

    Ok(())
}
```

**Integration Point:**
```rust
Commands::Unstage { all, file } => {
    Self::handle_unstage(all, file)
},
```

#### Existing Code Reuse

**Module:** `src/git/staging.rs`

Already implemented functions:
- `unstage_file(repo: &mut Repository, file_path: &str) -> Result<(), GitError>`
- `unstage_all(repo: &mut Repository) -> Result<usize, GitError>`

**BuildingGitManager methods:**
- `unstage_file(&mut self, file_path: &str) -> Result<(), GitError>`
- `unstage_all(&mut self) -> Result<usize, GitError>`

**Reuse:** ~95% - Only need CLI wrapper

#### Error Handling

**Error Scenarios:**
1. Not a git repository
   - **Error:** "Not a git repository"
   - **Action:** Display helpful message about running `git init`

2. File not staged
   - **Error:** "File not in index"
   - **Action:** Display message that file is not staged

3. No HEAD commit (empty repository)
   - **Behavior:** Clear the index (handled by unstage_all)
   - **Message:** "Cleared staging area (no commits yet)"

4. Invalid file path
   - **Error:** "File not found in repository"
   - **Action:** Display available staged files

#### Success Output

```bash
$ arx unstage --all
✅ Unstaged 3 file(s)
💡 Files reset to HEAD state

$ arx unstage building.yaml
✅ Unstaged: building.yaml
```

#### Testing Strategy

**Unit Tests:**
- Test unstage all in repository with commits
- Test unstage all in empty repository
- Test unstage specific file
- Test unstage non-existent file (error case)
- Test unstage in non-git directory (error case)

**Integration Tests:**
- Full workflow: stage → unstage → verify status
- Unstage partial changes → verify only unstaged files affected

---

## Feature 2: History Command

### Overview

Display commit history with filtering and formatting options, enabling users to review repository changes over time.

### User Stories

**As a user:**
- I want to view recent commits so I can see what changed
- I want to limit the number of commits shown so I don't get overwhelmed
- I want to see commit details (author, date, message) clearly formatted
- I want to filter history by file so I can track specific changes

### Technical Design

#### CLI Interface

```bash
# Show last 10 commits (default)
arx history

# Show last 50 commits
arx history --limit 50

# Show verbose details
arx history --verbose

# Show history for specific file
arx history --file building.yaml
```

#### Command Arguments

```rust
/// Show commit history
History {
    /// Number of commits to show (1-1000)
    #[arg(long, default_value = "10", value_parser = |s: &str| -> Result<usize, String> {
        let val: usize = s.parse()
            .map_err(|_| format!("must be a number between 1 and 1000"))?;
        if val < 1 || val > 1000 {
            Err(format!("Limit must be between 1 and 1000, got {}", val))
        } else {
            Ok(val)
        }
    })]
    limit: usize,

    /// Show detailed commit information
    #[arg(long)]
    verbose: bool,

    /// Show history for specific file
    #[arg(long)]
    file: Option<String>,
},
```

#### Implementation

**File:** `src/cli/mod.rs`

**Handler Method:**
```rust
fn handle_history(
    limit: usize,
    verbose: bool,
    file: Option<String>,
) -> Result<(), Box<dyn std::error::Error>> {
    use crate::git::manager::{BuildingGitManager, GitConfigManager};
    use chrono::{DateTime, Local, TimeZone};

    let config = GitConfigManager::load_from_arx_config_or_env();
    let manager = BuildingGitManager::new(".", "current", config)?;

    let commits = if let Some(file_path) = file {
        // Get history for specific file
        manager.get_file_history(&file_path)?
    } else {
        // Get general commit history
        manager.list_commits(limit)?
    };

    if commits.is_empty() {
        println!("📜 No commits yet");
        return Ok(());
    }

    println!("📜 Commit History ({} commits)", commits.len());
    println!();

    for commit in commits {
        // Format timestamp
        let datetime = Local.timestamp_opt(commit.time, 0)
            .single()
            .map(|dt| dt.format("%Y-%m-%d %H:%M:%S").to_string())
            .unwrap_or_else(|| "Unknown time".to_string());

        // Short hash (8 chars)
        let short_id = if commit.id.len() >= 8 {
            &commit.id[..8]
        } else {
            &commit.id
        };

        if verbose {
            println!("Commit: {}", commit.id);
            println!("Author: {}", commit.author);
            println!("Date:   {}", datetime);
            println!();
            println!("    {}", commit.message);
            println!();
            println!("---");
            println!();
        } else {
            // Compact format
            println!("{} {} ({})",
                short_id,
                commit.message,
                datetime
            );
        }
    }

    Ok(())
}
```

**Integration Point:**
```rust
Commands::History { limit, verbose, file } => {
    Self::handle_history(limit, verbose, file)
},
```

#### Existing Code Reuse

**Module:** `src/git/diff.rs`

Already implemented:
```rust
pub struct CommitInfo {
    pub id: String,
    pub message: String,
    pub author: String,
    pub time: i64,
}

pub fn list_commits(repo: &Repository, limit: usize) -> Result<Vec<CommitInfo>, GitError>
pub fn get_file_history(repo: &Repository, file_path: &str) -> Result<Vec<CommitInfo>, GitError>
```

**BuildingGitManager methods:**
- `list_commits(&self, limit: usize) -> Result<Vec<CommitInfo>, GitError>`
- `get_file_history(&self, file_path: &str) -> Result<Vec<CommitInfo>, GitError>`

**Reuse:** ~90% - Only need CLI wrapper and formatting

#### Output Formats

**Compact Format (Default):**
```bash
$ arx history
📜 Commit History (10 commits)

a1b2c3d4 Add floor 2 equipment (2025-11-20 14:30:00)
e5f6g7h8 Update HVAC system (2025-11-20 12:15:00)
i9j0k1l2 Initial building import (2025-11-19 16:45:00)
```

**Verbose Format:**
```bash
$ arx history --verbose
📜 Commit History (3 commits)

Commit: a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0
Author: John Doe <john@example.com>
Date:   2025-11-20 14:30:00

    Add floor 2 equipment

    Added 5 new HVAC units and updated mechanical room layout

---

Commit: e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0a1b2c3d4
Author: Jane Smith <jane@example.com>
Date:   2025-11-20 12:15:00

    Update HVAC system

---
```

#### Error Handling

**Error Scenarios:**
1. Not a git repository
   - **Error:** "Not a git repository"
   - **Message:** Suggest initializing with `arx init`

2. No commits yet
   - **Not an error** - Display "No commits yet"

3. File not found in history
   - **Error:** "File not found in repository history"
   - **Message:** "File may not exist or was never committed"

4. Invalid limit value
   - **Error:** Handled by clap validation
   - **Message:** "Limit must be between 1 and 1000"

#### Testing Strategy

**Unit Tests:**
- Test history in repository with commits
- Test history in empty repository
- Test history with limit parameter
- Test history for specific file
- Test file history for non-existent file
- Test verbose vs compact formatting

**Integration Tests:**
- Create commits → list history → verify all appear
- Filter by file → verify only relevant commits shown
- Limit to 5 → verify exactly 5 commits returned

---

## Feature 3: Building Import/Export

### Overview

Enable users to import IFC files into ArxOS format and export building data to various formats (IFC, YAML, JSON).

### User Stories

**As a user:**
- I want to import IFC files so I can work with standard building data
- I want to export to IFC so I can share with other tools
- I want to export to YAML/JSON for custom integrations
- I want dry-run mode so I can preview imports without making changes
- I want progress feedback for large files

### Technical Design

#### CLI Interface

```bash
# Import IFC file
arx import model.ifc
arx import --dry-run model.ifc       # Preview only
arx import --commit model.ifc        # Auto-commit after import

# Export building data
arx export --format ifc              # Export to IFC
arx export --format yaml             # Export to YAML
arx export --format json             # Export to JSON
arx export --output building.ifc     # Specify output file
```

#### Command Arguments

```rust
/// Import IFC file to Git repository
Import {
    /// Path to IFC file
    ifc_file: String,

    /// Git repository URL (optional - uses current dir if not specified)
    #[arg(long)]
    repo: Option<String>,

    /// Dry run - show what would be done without making changes
    #[arg(long)]
    dry_run: bool,

    /// Auto-commit after successful import
    #[arg(long)]
    commit: bool,
},

/// Export building data to Git repository or other formats
Export {
    /// Export format (git, ifc, yaml, json, gltf, usdz)
    #[arg(long, default_value = "yaml")]
    format: String,

    /// Output file path (required for non-git formats)
    #[arg(long)]
    output: Option<String>,

    /// Git repository URL (required for git format)
    #[arg(long)]
    repo: Option<String>,

    /// Export only changes (delta mode)
    #[arg(long)]
    delta: bool,
},
```

#### Implementation

**File:** `src/cli/mod.rs`

**Import Handler:**
```rust
fn handle_import(
    ifc_file: String,
    repo: Option<String>,
    dry_run: bool,
    commit: bool,
) -> Result<(), Box<dyn std::error::Error>> {
    use crate::agent::ifc::import_ifc;
    use crate::git::manager::{BuildingGitManager, GitConfigManager};
    use std::path::Path;

    println!("📥 Importing IFC file: {}", ifc_file);

    // Validate file exists and is readable
    let ifc_path = Path::new(&ifc_file);
    if !ifc_path.exists() {
        return Err(format!("IFC file not found: {}", ifc_file).into());
    }

    // Get repository root
    let repo_root = if let Some(repo_path) = repo {
        Path::new(&repo_path)
    } else {
        Path::new(".")
    };

    if dry_run {
        println!("🔍 DRY RUN MODE - No changes will be made");
        println!();

        // Perform dry-run analysis
        // Read file size
        let metadata = std::fs::metadata(ifc_path)?;
        println!("File size: {} MB", metadata.len() / 1024 / 1024);

        // Could add: count entities, estimate processing time
        println!("✅ Dry run complete - file is valid for import");
        return Ok(());
    }

    // Read IFC file
    let ifc_bytes = std::fs::read(ifc_path)?;
    let data_base64 = base64::engine::general_purpose::STANDARD.encode(&ifc_bytes);

    // Import using existing functionality
    let result = import_ifc(
        repo_root,
        &ifc_file,
        &data_base64,
    )?;

    println!("✅ Import successful!");
    println!();
    println!("Building: {}", result.building_name);
    println!("YAML output: {}", result.yaml_path);
    println!("Floors: {}", result.floors);
    println!("Rooms: {}", result.rooms);
    println!("Equipment: {}", result.equipment);
    println!();

    // Auto-commit if requested
    if commit {
        println!("💾 Committing changes...");
        let config = GitConfigManager::load_from_arx_config_or_env();
        let mut manager = BuildingGitManager::new(".", &result.building_name, config)?;

        let commit_msg = format!(
            "Import {} - {} floors, {} rooms, {} equipment",
            ifc_file,
            result.floors,
            result.rooms,
            result.equipment
        );

        let commit_id = manager.commit_staged(&commit_msg)?;
        println!("✅ Committed: {}", &commit_id[..8.min(commit_id.len())]);
    } else {
        println!("💡 Run 'arx commit \"message\"' to commit the changes");
    }

    Ok(())
}
```

**Export Handler:**
```rust
fn handle_export(
    format: String,
    output: Option<String>,
    repo: Option<String>,
    delta: bool,
) -> Result<(), Box<dyn std::error::Error>> {
    use crate::export::ifc::IFCExporter;
    use crate::persistence::{load_building_data_from_dir, PersistenceManager};
    use crate::yaml::BuildingYamlSerializer;

    println!("📤 Exporting building data");
    println!("Format: {}", format);

    // Load building data
    let building_data = load_building_data_from_dir()?;
    let building_name = &building_data.building.name;

    match format.as_str() {
        "ifc" => {
            let output_path = output.unwrap_or_else(||
                format!("{}.ifc", building_name)
            );

            println!("Output: {}", output_path);

            // Export using IFCExporter
            let exporter = IFCExporter::new();
            let ifc_bytes = exporter.export_building_data(&building_data)?;

            std::fs::write(&output_path, ifc_bytes)?;

            let size_mb = std::fs::metadata(&output_path)?.len() / 1024 / 1024;
            println!("✅ Exported {} MB to {}", size_mb, output_path);
        }

        "yaml" => {
            let output_path = output.unwrap_or_else(||
                format!("{}.yaml", building_name)
            );

            println!("Output: {}", output_path);

            let serializer = BuildingYamlSerializer::new();
            serializer.write_to_file(&building_data, &output_path)?;

            println!("✅ Exported YAML to {}", output_path);
        }

        "json" => {
            let output_path = output.unwrap_or_else(||
                format!("{}.json", building_name)
            );

            println!("Output: {}", output_path);

            let json = serde_json::to_string_pretty(&building_data)?;
            std::fs::write(&output_path, json)?;

            println!("✅ Exported JSON to {}", output_path);
        }

        _ => {
            return Err(format!(
                "Unsupported export format: {}. Supported: ifc, yaml, json",
                format
            ).into());
        }
    }

    Ok(())
}
```

**Integration Points:**
```rust
Commands::Import { ifc_file, repo, dry_run, commit } => {
    Self::handle_import(ifc_file, repo, dry_run, commit)
},

Commands::Export { format, output, repo, delta } => {
    Self::handle_export(format, output, repo, delta)
},
```

#### Existing Code Reuse

**Import - Module:** `src/agent/ifc.rs`

Already implemented:
```rust
pub fn import_ifc(
    repo_root: &Path,
    filename: &str,
    data_base64: &str,
) -> Result<IfcImportResult>

pub struct IfcImportResult {
    pub building_name: String,
    pub yaml_path: String,
    pub floors: usize,
    pub rooms: usize,
    pub equipment: usize,
}
```

**Export - Module:** `src/export/ifc.rs`

Check for existing IFCExporter implementation.

**Reuse:**
- Import: ~80% (need CLI integration and file handling)
- Export: ~70% (may need to add YAML/JSON export paths)

#### Output Examples

**Import Success:**
```bash
$ arx import building.ifc --commit
📥 Importing IFC file: building.ifc
✅ Import successful!

Building: Office Building North
YAML output: office-building-north.yaml
Floors: 5
Rooms: 120
Equipment: 450

💾 Committing changes...
✅ Committed: a1b2c3d4
```

**Import Dry Run:**
```bash
$ arx import building.ifc --dry-run
📥 Importing IFC file: building.ifc
🔍 DRY RUN MODE - No changes will be made

File size: 15 MB
Estimated floors: 5
Estimated rooms: 120

✅ Dry run complete - file is valid for import
```

**Export Success:**
```bash
$ arx export --format ifc --output building-v2.ifc
📤 Exporting building data
Format: ifc
Output: building-v2.ifc
✅ Exported 12 MB to building-v2.ifc
```

#### Error Handling

**Import Errors:**
1. File not found
2. Invalid IFC format
3. File too large (>50MB)
4. Parsing errors
5. Disk space issues

**Export Errors:**
1. No building data found
2. Unsupported format
3. Write permission denied
4. Insufficient disk space

#### Performance Considerations

**Large File Handling:**
- Show progress indicator for files >10MB
- Process in chunks for files >50MB
- Provide estimated time for large imports

**Memory Management:**
- Stream large files instead of loading entirely
- Clear intermediate data structures
- Use incremental parsing where possible

#### Testing Strategy

**Unit Tests:**
- Import valid IFC file
- Import invalid IFC file (error)
- Import with dry-run
- Import with auto-commit
- Export to each supported format
- Export with custom output path

**Integration Tests:**
- Full workflow: import → modify → export → reimport
- Large file handling (performance test)
- Multiple format exports (consistency check)

---

## Feature 4: Query Operations

### Overview

Enable powerful search and query capabilities using ArxAddress patterns with glob-style wildcards.

### User Stories

**As a user:**
- I want to search for equipment by pattern so I can find specific items
- I want to query all equipment in a room/floor/building
- I want to use wildcards to match multiple items
- I want results in different formats (table, JSON, YAML)
- I want to filter by equipment type, status, or properties

### Technical Design

#### CLI Interface

```bash
# Query by ArxAddress pattern
arx query "/usa/ny/*/floor-02/mech/*"           # All mech room equipment on floor 2
arx query "/usa/ny/brooklyn/*/*/hvac/boiler-*"  # All boilers in HVAC rooms

# Search by name/type
arx search "boiler"                              # Find all boilers
arx search --equipment-type HVAC                 # All HVAC equipment
arx search --status Critical                     # All critical equipment

# Format output
arx query "/*/floor-01/*" --format json
arx query "/*/floor-01/*" --format table         # Default
arx query "/*/floor-01/*" --format yaml
```

#### Command Arguments

```rust
/// Query equipment by ArxAddress glob pattern
Query {
    /// ArxAddress glob pattern with wildcards
    pattern: String,

    /// Output format (table, json, yaml)
    #[arg(long, default_value = "table")]
    format: String,

    /// Show detailed results
    #[arg(long)]
    verbose: bool,
},

/// Search building data
Search {
    /// Search query
    query: String,

    /// Search in equipment names
    #[arg(long)]
    equipment: bool,

    /// Search in room names
    #[arg(long)]
    rooms: bool,

    /// Search in building names
    #[arg(long)]
    buildings: bool,

    /// Equipment type filter
    #[arg(long)]
    equipment_type: Option<String>,

    /// Equipment status filter
    #[arg(long)]
    status: Option<String>,

    /// Case-sensitive search
    #[arg(long)]
    case_sensitive: bool,

    /// Use regex pattern matching
    #[arg(long)]
    regex: bool,

    /// Maximum number of results
    #[arg(long, default_value = "50")]
    limit: usize,

    /// Show detailed results
    #[arg(long)]
    verbose: bool,

    /// Open interactive browser
    #[arg(long)]
    interactive: bool,
},
```

#### Implementation

**File:** `src/cli/mod.rs`

**Query Handler:**
```rust
fn handle_query(
    pattern: String,
    format: String,
    verbose: bool,
) -> Result<(), Box<dyn std::error::Error>> {
    use crate::core::domain::ArxAddress;
    use crate::persistence::load_building_data_from_dir;
    use glob::Pattern;

    println!("🔍 Querying: {}", pattern);

    // Load building data
    let building_data = load_building_data_from_dir()?;

    // Convert pattern to glob matcher
    let glob_pattern = Pattern::new(&pattern)?;

    // Find matching equipment
    let mut results = Vec::new();

    for floor in &building_data.floors {
        for wing in &floor.wings {
            for room in &wing.rooms {
                for equipment in &room.equipment {
                    // Check if equipment has address
                    if let Some(ref address) = equipment.address {
                        if glob_pattern.matches(&address.path) {
                            results.push((
                                address.path.clone(),
                                equipment.clone(),
                            ));
                        }
                    }
                }
            }
        }
    }

    // Display results
    if results.is_empty() {
        println!("❌ No equipment found matching pattern");
        return Ok(());
    }

    println!("✅ Found {} results", results.len());
    println!();

    match format.as_str() {
        "table" => {
            // Table format
            println!("{:<50} {:<20} {:<15}", "Address", "Name", "Type");
            println!("{}", "-".repeat(85));

            for (address, equipment) in results {
                let addr_display = if address.len() > 47 {
                    format!("{}...", &address[..47])
                } else {
                    address.clone()
                };

                println!(
                    "{:<50} {:<20} {:<15}",
                    addr_display,
                    equipment.name,
                    format!("{:?}", equipment.equipment_type),
                );

                if verbose {
                    println!("  Status: {:?}", equipment.status);
                    if let Some(ref health) = equipment.health_status {
                        println!("  Health: {:?}", health);
                    }
                    println!();
                }
            }
        }

        "json" => {
            let json = serde_json::to_string_pretty(&results)?;
            println!("{}", json);
        }

        "yaml" => {
            let yaml = serde_yaml::to_string(&results)?;
            println!("{}", yaml);
        }

        _ => {
            return Err(format!(
                "Unsupported format: {}. Supported: table, json, yaml",
                format
            ).into());
        }
    }

    Ok(())
}
```

**Search Handler:**
```rust
fn handle_search(
    query: String,
    equipment_filter: bool,
    rooms_filter: bool,
    buildings_filter: bool,
    equipment_type: Option<String>,
    status: Option<String>,
    case_sensitive: bool,
    use_regex: bool,
    limit: usize,
    verbose: bool,
    interactive: bool,
) -> Result<(), Box<dyn std::error::Error>> {
    use crate::core::operations::equipment::list_equipment;
    use regex::Regex;

    if interactive {
        println!("⚠️  Interactive search browser not yet implemented");
        return Ok(());
    }

    println!("🔍 Searching for: {}", query);

    // Load equipment
    let all_equipment = list_equipment(None)?;

    // Build matcher
    let matcher: Box<dyn Fn(&str) -> bool> = if use_regex {
        let re = if case_sensitive {
            Regex::new(&query)?
        } else {
            Regex::new(&format!("(?i){}", query))?
        };
        Box::new(move |text: &str| re.is_match(text))
    } else {
        let query_lower = query.to_lowercase();
        if case_sensitive {
            Box::new(move |text: &str| text.contains(&query))
        } else {
            Box::new(move |text: &str|
                text.to_lowercase().contains(&query_lower)
            )
        }
    };

    // Filter equipment
    let mut results: Vec<_> = all_equipment.into_iter()
        .filter(|eq| {
            // Name match
            if !matcher(&eq.name) {
                return false;
            }

            // Equipment type filter
            if let Some(ref eq_type) = equipment_type {
                if format!("{:?}", eq.equipment_type) != *eq_type {
                    return false;
                }
            }

            // Status filter
            if let Some(ref status_filter) = status {
                if format!("{:?}", eq.status) != *status_filter {
                    return false;
                }
            }

            true
        })
        .take(limit)
        .collect();

    // Display results
    if results.is_empty() {
        println!("❌ No equipment found matching search");
        return Ok(());
    }

    println!("✅ Found {} results (showing up to {})", results.len(), limit);
    println!();

    println!("{:<30} {:<20} {:<15}", "Name", "Type", "Status");
    println!("{}", "-".repeat(65));

    for equipment in results {
        println!(
            "{:<30} {:<20} {:<15}",
            equipment.name,
            format!("{:?}", equipment.equipment_type),
            format!("{:?}", equipment.status),
        );

        if verbose {
            if let Some(ref addr) = equipment.address {
                println!("  Address: {}", addr.path);
            }
            if let Some(ref health) = equipment.health_status {
                println!("  Health: {:?}", health);
            }
            println!();
        }
    }

    Ok(())
}
```

**Integration Points:**
```rust
Commands::Query { pattern, format, verbose } => {
    Self::handle_query(pattern, format, verbose)
},

Commands::Search {
    query,
    equipment,
    rooms,
    buildings,
    equipment_type,
    status,
    case_sensitive,
    regex,
    limit,
    verbose,
    interactive,
} => {
    Self::handle_search(
        query,
        equipment,
        rooms,
        buildings,
        equipment_type,
        status,
        case_sensitive,
        regex,
        limit,
        verbose,
        interactive,
    )
},
```

#### Existing Code Reuse

**Module:** `src/core/domain/address.rs`

Already implemented:
```rust
pub struct ArxAddress {
    pub path: String,
}

impl ArxAddress {
    pub fn from_path(path: &str) -> Result<Self>
    pub fn validate(&self) -> Result<()>
    pub fn parts(&self) -> AddressParts
    // ... other methods
}
```

**Module:** `src/core/operations/equipment.rs`

Already implemented:
```rust
pub fn list_equipment(
    building_name: Option<&str>,
) -> Result<Vec<Equipment>, Box<dyn std::error::Error>>
```

**Reuse:** ~70% - Need to add glob matching and formatting

**New Dependencies:**
```toml
[dependencies]
glob = "0.3"  # For glob pattern matching
```

#### Output Examples

**Query - Table Format:**
```bash
$ arx query "/usa/ny/*/floor-02/mech/*"
🔍 Querying: /usa/ny/*/floor-02/mech/*
✅ Found 8 results

Address                                           Name                 Type
-------------------------------------------------------------------------------------
/usa/ny/brooklyn/ps-118/floor-02/mech/boiler-01   Boiler 1             HVAC
/usa/ny/brooklyn/ps-118/floor-02/mech/boiler-02   Boiler 2             HVAC
/usa/ny/brooklyn/ps-118/floor-02/mech/pump-01     Pump 1               Plumbing
```

**Query - JSON Format:**
```bash
$ arx query "/*/floor-01/*" --format json
🔍 Querying: /*/floor-01/*
✅ Found 12 results

[
  {
    "address": "/usa/ny/brooklyn/ps-118/floor-01/lobby/light-01",
    "name": "Lobby Light 1",
    "equipment_type": "Lighting",
    "status": "Operational"
  },
  ...
]
```

**Search - Basic:**
```bash
$ arx search "boiler"
🔍 Searching for: boiler
✅ Found 3 results (showing up to 50)

Name                           Type                 Status
-----------------------------------------------------------------
Boiler 1                       HVAC                 Operational
Boiler 2                       HVAC                 Operational
Backup Boiler                  HVAC                 Standby
```

**Search - Filtered:**
```bash
$ arx search "pump" --equipment-type Plumbing --status Critical
🔍 Searching for: pump
✅ Found 2 results (showing up to 50)

Name                           Type                 Status
-----------------------------------------------------------------
Primary Pump                   Plumbing             Critical
Backup Pump                    Plumbing             Critical
```

#### Error Handling

**Query Errors:**
1. Invalid glob pattern
2. No building data found
3. No equipment has addresses
4. Unsupported output format

**Search Errors:**
1. Invalid regex pattern
2. No building data found
3. No equipment found
4. Invalid filter values

#### Performance Considerations

**Optimization Strategies:**
1. **Index building**: Create in-memory index of addresses for fast lookup
2. **Lazy loading**: Only load full equipment details for matches
3. **Result limiting**: Default to 50 results, require explicit --all for unlimited
4. **Caching**: Cache building data if querying multiple times

**Benchmarks:**
- Query 1000 equipment items: <100ms
- Search with regex across 5000 items: <500ms
- Large building (10000+ items): <2s

#### Testing Strategy

**Unit Tests:**
- Parse valid glob patterns
- Match simple patterns (/usa/ny/*/floor-01/*)
- Match complex patterns with multiple wildcards
- Filter by equipment type
- Filter by status
- Case-sensitive vs insensitive search
- Regex matching

**Integration Tests:**
- Load building → query → verify results
- Search with filters → verify filtered correctly
- Export results to JSON → reimport → verify consistency

---

## Integration Architecture

### Component Interaction Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                         CLI Layer                            │
│  (cli/mod.rs - Command routing and handler methods)          │
└───────────┬────────────┬────────────┬────────────────────────┘
            │            │            │
            ▼            ▼            ▼
┌───────────────┐ ┌──────────────┐ ┌──────────────────────────┐
│  Git Module   │ │  IFC Module  │ │  Core Operations Module  │
│               │ │              │ │                          │
│ • staging.rs  │ │ • agent/ifc  │ │ • equipment.rs           │
│ • commit.rs   │ │ • export/ifc │ │ • room.rs                │
│ • diff.rs     │ │ • processor  │ │ • spatial.rs             │
│ • manager.rs  │ │              │ │ • domain/address.rs      │
└───────┬───────┘ └──────┬───────┘ └────────┬─────────────────┘
        │                │                  │
        └────────────────┴──────────────────┘
                         │
                         ▼
        ┌────────────────────────────────────┐
        │      Data Layer                    │
        │  • persistence::PersistenceManager │
        │  • yaml::BuildingYamlSerializer    │
        │  • git2::Repository                │
        └────────────────────────────────────┘
```

### Data Flow

**Command Execution Flow:**
```
User Input
  → clap::Parser
    → Cli::execute()
      → match Commands::*
        → handle_*() method
          → Module function call
            → Data layer operation
              → Result<Output, Error>
            ← Return result
          ← Format output
        ← Display to user
      ← Complete
    ← Return status
  ← Exit
```

### Error Propagation

```
Module Error (GitError, ArxError, etc.)
  → Convert to Box<dyn std::error::Error>
    → Propagate with ?
      → Catch in handler
        → Format user-friendly message
          → Display to stderr
            → Return Err() from execute()
              → Main returns exit code 1
```

---

## Testing Strategy

### Test Pyramid

```
              ┌─────────┐
              │   E2E   │  5-10 tests
              │  Tests  │  (Full CLI workflows)
            ┌─┴─────────┴─┐
            │ Integration │  20-30 tests
            │    Tests    │  (Module integration)
          ┌─┴─────────────┴─┐
          │   Unit Tests    │  100+ tests
          │  (Functions)    │  (Individual functions)
          └─────────────────┘
```

### Unit Tests

**Coverage Target:** 80%+ code coverage

**Test Categories:**

1. **Git Operations**
   - Unstage single file
   - Unstage all files
   - List commits with limit
   - Get file history
   - Error cases (no repo, invalid file)

2. **Import/Export**
   - Parse valid IFC
   - Handle invalid IFC
   - Export to each format
   - Validate output structure
   - Error cases (file not found, permission denied)

3. **Query Operations**
   - Parse glob patterns
   - Match simple patterns
   - Match complex wildcards
   - Filter by type/status
   - Format output (table, JSON, YAML)

**Test Framework:**
```rust
#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_handle_unstage_all() {
        // Setup: Create temp repo with staged files
        // Execute: Call handle_unstage with all=true
        // Verify: Check staging area is empty
    }

    #[test]
    fn test_handle_history_limit() {
        // Setup: Repo with 20 commits
        // Execute: Call handle_history with limit=10
        // Verify: Exactly 10 commits returned
    }
}
```

### Integration Tests

**Location:** `tests/cli/`

**Test Scenarios:**

1. **Git Workflow**
   ```rust
   #[test]
   fn test_full_git_workflow() {
       // stage files → commit → unstage → verify
   }
   ```

2. **Import-Export Roundtrip**
   ```rust
   #[test]
   fn test_import_export_roundtrip() {
       // import IFC → export YAML → compare data
   }
   ```

3. **Query Consistency**
   ```rust
   #[test]
   fn test_query_vs_search_consistency() {
       // query by address → search by name → verify same results
   }
   ```

### End-to-End Tests

**Location:** `tests/e2e/`

**Test Scenarios:**

1. **Complete Building Workflow**
   - Import IFC → query equipment → modify → commit → export

2. **Multi-User Scenario**
   - User A imports → commits → User B queries → modifies → commits

3. **Error Recovery**
   - Import fails → verify rollback → retry successfully

### Test Data

**Required Test Files:**
- `tests/fixtures/sample.ifc` - Small IFC file for testing
- `tests/fixtures/large.ifc` - Large IFC file (performance)
- `tests/fixtures/invalid.ifc` - Malformed IFC (error handling)
- `tests/fixtures/building.yaml` - Sample building data

### Continuous Integration

**CI Pipeline:**
```yaml
test:
  script:
    - cargo test --lib              # Unit tests
    - cargo test --test '*'         # Integration tests
    - cargo test --release          # Performance tests
    - cargo clippy -- -D warnings   # Linting
    - cargo fmt --check             # Format check
```

---

## Performance Considerations

### Benchmarks

**Target Performance:**

| Operation | Small (<1MB) | Medium (1-10MB) | Large (>10MB) |
|-----------|--------------|-----------------|---------------|
| Import IFC | <1s | <5s | <30s |
| Export IFC | <1s | <3s | <15s |
| Query (1000 items) | <100ms | <500ms | <2s |
| Search (regex) | <200ms | <1s | <5s |
| Git history (100 commits) | <50ms | <100ms | <200ms |

### Optimization Strategies

**1. Lazy Loading**
- Don't load full building data unless needed
- Stream large files instead of reading entirely
- Use iterators for large result sets

**2. Caching**
```rust
// Cache building data for repeated queries
lazy_static! {
    static ref BUILDING_CACHE: Mutex<HashMap<String, BuildingData>> =
        Mutex::new(HashMap::new());
}
```

**3. Parallel Processing**
- Parse IFC sections in parallel
- Process multiple floors concurrently
- Parallelize queries across buildings

**4. Progress Indicators**
```rust
use indicatif::ProgressBar;

let pb = ProgressBar::new(total_items);
for item in items {
    // Process item
    pb.inc(1);
}
pb.finish_with_message("Complete");
```

### Memory Management

**Limits:**
- Max IFC file size: 50MB
- Max query results in memory: 10,000 items
- Building data cache: 100MB max

**Strategies:**
- Use `Vec::with_capacity()` for known sizes
- Clear temporary buffers after processing
- Use streaming for large exports

---

## Security Considerations

### Input Validation

**File Path Validation:**
```rust
use crate::utils::path_safety::PathSafety;

// Validate all user-provided paths
PathSafety::validate_path_for_write(&output_path, repo_root)?;
PathSafety::validate_path_for_read(&input_path)?;
```

**Size Limits:**
- IFC uploads: 50MB maximum
- Query results: 10,000 items maximum
- Export files: 100MB maximum

**Pattern Validation:**
```rust
// Sanitize glob patterns to prevent ReDoS
fn validate_pattern(pattern: &str) -> Result<()> {
    // Limit pattern complexity
    if pattern.len() > 500 {
        return Err("Pattern too long".into());
    }

    // Prevent catastrophic backtracking
    if pattern.contains("**") && pattern.matches("**").count() > 3 {
        return Err("Too many recursive wildcards".into());
    }

    Ok(())
}
```

### Access Control

**File System:**
- Restrict file operations to repository directory
- Validate all paths against directory traversal
- Use temporary directories for intermediate files

**Git Operations:**
- Respect .gitignore
- Don't expose sensitive data in commits
- Validate commit messages for security issues

### Error Messages

**Information Disclosure:**
- Don't expose full file paths in error messages
- Sanitize error details (no stack traces to users)
- Log detailed errors separately for debugging

**Example:**
```rust
// Bad
Err(format!("Failed to read {}: {}", full_path, detailed_error).into())

// Good
eprintln!("Failed to read file");
log::error!("Failed to read {}: {}", full_path, detailed_error);
Err("File read error".into())
```

---

## Deployment Plan

### Phase 1: Development (Week 1)

**Tasks:**
1. Implement unstage command (Day 1)
2. Implement history command (Day 2)
3. Implement import command (Days 3-4)
4. Implement export command (Day 4)
5. Implement query command (Day 5)

**Deliverables:**
- All features implemented
- Unit tests passing
- Integration tests written

### Phase 2: Testing (Week 2)

**Tasks:**
1. Integration testing (Days 1-2)
2. Performance testing (Day 3)
3. Security review (Day 4)
4. Documentation (Day 5)

**Deliverables:**
- All tests passing
- Performance benchmarks met
- Security review complete
- User documentation updated

### Phase 3: Beta Release (Week 3)

**Tasks:**
1. Internal testing (Days 1-2)
2. Bug fixes (Days 3-4)
3. Beta release (Day 5)

**Deliverables:**
- Beta release to limited users
- Feedback collection process
- Bug tracking system

### Phase 4: Production Release (Week 4)

**Tasks:**
1. Address beta feedback (Days 1-3)
2. Final testing (Day 4)
3. Production release (Day 5)

**Deliverables:**
- Production release
- Release notes
- Migration guide

### Rollback Plan

If critical issues are discovered:
1. Revert CLI changes
2. Keep underlying modules (they're independently testable)
3. Fix issues in feature branch
4. Re-release after validation

---

## Future Extensibility

### Interactive TUI Modes

**Planned Enhancements:**

1. **Interactive History Browser**
   - Navigate commits with arrow keys
   - View diffs inline
   - Cherry-pick commits

2. **Interactive Query Builder**
   - Build complex queries visually
   - Preview results in real-time
   - Save frequent queries

3. **Interactive Import Wizard**
   - Step-by-step IFC import
   - Preview before committing
   - Configure mapping rules

### Batch Operations

**Planned Features:**

```bash
# Batch import multiple IFC files
arx import-batch ./ifc-files/*.ifc

# Batch export to multiple formats
arx export-all --formats ifc,yaml,json

# Batch query multiple patterns
arx query-batch patterns.txt
```

### API Integration

**Planned REST API:**

```bash
# Start API server
arx serve --port 8080

# API endpoints:
# POST /api/import - Import IFC
# GET /api/query/:pattern - Query equipment
# GET /api/export/:format - Export building
```

### Plugin System

**Planned Architecture:**

```rust
// Plugin trait
pub trait ArxPlugin {
    fn name(&self) -> &str;
    fn commands(&self) -> Vec<Command>;
    fn execute(&self, cmd: &Command) -> Result<()>;
}

// Register plugins
arx plugin install arxos-energy-analysis
arx plugin enable energy-analysis
arx energy analyze --building office-north
```

### Cloud Integration

**Planned Features:**

```bash
# Sync with cloud repository
arx cloud sync

# Share building with team
arx cloud share building-id --team architects

# Pull changes from cloud
arx cloud pull
```

---

## Appendix A: Code Structure

### Directory Layout

```
src/
├── cli/
│   ├── mod.rs           # Main CLI entry point (handlers here)
│   ├── args/
│   │   ├── mod.rs
│   │   ├── git.rs       # Git command args
│   │   ├── building.rs  # Import/export args
│   │   └── query.rs     # Query args
│   └── commands/
│       └── ...
│
├── git/
│   ├── mod.rs
│   ├── manager.rs
│   ├── staging.rs       # Used by unstage
│   ├── diff.rs          # Used by history
│   └── ...
│
├── agent/
│   └── ifc.rs           # Used by import
│
├── export/
│   └── ifc.rs           # Used by export
│
└── core/
    ├── operations/
    │   ├── equipment.rs # Used by search
    │   └── ...
    └── domain/
        └── address.rs   # Used by query
```

### File Size Estimates

| File | Current LOC | Added LOC | Final LOC |
|------|-------------|-----------|-----------|
| cli/mod.rs | ~200 | +400 | ~600 |
| cli/args/building.rs | ~50 | +50 | ~100 |
| cli/args/query.rs | 0 | +100 | ~100 |
| git/staging.rs | ~85 | 0 | ~85 |
| git/diff.rs | ~200 | 0 | ~200 |

**Total New LOC:** ~550 lines

---

## Appendix B: Dependencies

### New Dependencies Required

```toml
[dependencies]
# Already exist
git2 = "0.18"
serde = { version = "1.0", features = ["derive"] }
serde_json = "1.0"
serde_yaml = "0.9"
anyhow = "1.0"
chrono = "0.4"
clap = { version = "4.4", features = ["derive"] }
base64 = "0.21"

# New for query operations
glob = "0.3"           # Glob pattern matching
regex = "1.10"         # Regex search

# Optional for future
indicatif = "0.17"     # Progress bars (large file imports)
```

---

## Appendix C: Migration Guide

### For Existing Users

**No Breaking Changes:**
- All existing commands continue to work
- New commands are additive only
- Configuration remains backward compatible

**New Features Available:**
```bash
# New git commands
arx unstage
arx history

# New building commands
arx import model.ifc
arx export --format ifc

# New query commands
arx query "/usa/ny/*/floor-01/*"
arx search "boiler"
```

**Recommended Migration Path:**
1. Update to new version
2. Test existing workflows (stage, commit, status)
3. Try new unstage/history commands
4. Explore import/export features
5. Learn query patterns for advanced use

---

## Appendix D: Decision Log

### Key Design Decisions

**1. Why CLI handlers in cli/mod.rs instead of separate files?**
- **Decision:** Keep handlers in cli/mod.rs
- **Rationale:** Current pattern is working well, keeps routing close to handler, file size manageable
- **Alternative considered:** Separate cli/handlers/ directory
- **Trade-off:** Slightly larger file vs. more file navigation

**2. Why reuse existing agent/ifc.rs instead of new import module?**
- **Decision:** Reuse agent/ifc
- **Rationale:** Code already exists and is tested, just needs CLI wrapper
- **Alternative considered:** Create new cli/import module
- **Trade-off:** Some agent-specific code vs. duplication

**3. Why glob crate for pattern matching instead of custom impl?**
- **Decision:** Use glob crate
- **Rationale:** Well-tested, handles edge cases, standard patterns
- **Alternative considered:** Custom glob implementation
- **Trade-off:** External dependency vs. reinventing wheel

**4. Why table format as default output instead of JSON?**
- **Decision:** Table format default
- **Rationale:** Human-readable, matches Unix tradition (ls, ps, etc.)
- **Alternative considered:** JSON default
- **Trade-off:** Machine-readable by default vs. human-readable

---

## Appendix E: References

### Related Documentation

- [ArxOS Architecture Overview](./ARCHITECTURE.md)
- [CLI Roadmap](./CLI_ROADMAP.md)
- [Git Operations Guide](./git/README.md)
- [IFC Processing Guide](./ifc/README.md)
- [ArxAddress Specification](./ARXADDRESS_SPEC.md)

### External Resources

- [git2-rs Documentation](https://docs.rs/git2/)
- [Clap CLI Framework](https://docs.rs/clap/)
- [IFC Format Specification](https://technical.buildingsmart.org/standards/ifc/)
- [Glob Pattern Syntax](https://docs.rs/glob/)

---

**Document Version:** 1.0
**Last Updated:** 2025-11-20
**Next Review:** 2025-12-01
**Status:** Approved for Implementation
