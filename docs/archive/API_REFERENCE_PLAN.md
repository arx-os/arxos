# API Reference Documentation Plan

## Overview

Create comprehensive API reference documentation covering all public APIs: CLI commands, configuration, FFI functions, and core types. This document will serve as the definitive reference for developers integrating with ArxOS.

## Current State Analysis

### What Exists
- ✅ Rustdoc comments throughout codebase (in-code documentation)
- ✅ `USER_GUIDE.md` - User-facing guide with examples
- ✅ `CONFIGURATION.md` - Configuration documentation
- ✅ `MOBILE_FFI_INTEGRATION.md` - Mobile integration guide
- ✅ Command help text via `clap` (automatic)

### What's Missing
- ❌ Single comprehensive API reference document
- ❌ Compiled rustdoc HTML (not published)
- ❌ Searchable API index
- ❌ Structured FFI function reference
- ❌ Complete error code reference
- ❌ API usage examples per section

## Goals

1. **Single Source of Truth**: One document where developers can find everything
2. **Searchability**: Easy to find specific functions/commands
3. **Examples**: Real-world usage for every API
4. **Maintainability**: Can be updated as code changes
5. **Accessibility**: Hosted and linked from main README

## Structure Plan

### Option A: Single Large Document (Recommended)

```
docs/API_REFERENCE.md
├── Table of Contents (auto-generated links)
├── Introduction
├── CLI Commands (Complete Reference)
│   ├── Core Commands (import, export, validate)
│   ├── Git Operations (status, stage, commit, etc.)
│   ├── Data Management (room, equipment, spatial)
│   ├── Visualization (render, interactive)
│   ├── Search & Filter
│   ├── AR Integration
│   ├── Sensor Processing
│   └── System (config, health, watch)
├── Configuration API
│   ├── Configuration Structure
│   ├── Environment Variables
│   ├── Configuration Files
│   └── Validation Rules
├── Mobile FFI API
│   ├── C FFI Functions
│   ├── JNI Functions
│   ├── Data Structures
│   ├── Error Handling
│   └── Usage Examples (iOS/Android)
├── Core Rust API
│   ├── Building Management
│   ├── Spatial Operations
│   ├── IFC Processing
│   ├── YAML Serialization
│   └── Error Types
├── Error Reference
│   ├── Error Codes
│   ├── Error Types
│   └── Error Handling Patterns
└── Examples
    ├── CLI Usage Examples
    ├── FFI Integration Examples
    └── Programmatic Usage
```

**Pros:**
- Single file to maintain
- Easy to search (within document)
- Complete reference in one place
- Can be version-controlled with code

**Cons:**
- Large file (estimated 2000-3000 lines)
- May be overwhelming initially

### Option B: Modular Documentation (Alternative)

```
docs/api/
├── README.md (index)
├── cli.md
├── config.md
├── mobile-ffi.md
├── core-api.md
├── errors.md
└── examples/
    ├── cli-examples.md
    └── integration-examples.md
```

**Pros:**
- Smaller, focused files
- Easier navigation
- Can be edited independently

**Cons:**
- More files to maintain
- Harder to ensure consistency
- Cross-references needed

## Recommendation: Option A (Single Document)

**Rationale:**
- Most developer tools support "Go to Definition" in large documents
- Easier to search across all APIs
- Better for generating a single PDF/e-book
- Simpler maintenance (one file)
- Can still break into sections with clear headings

## Implementation Plan

### Phase 1: Content Collection & Organization (Day 1)

**Tasks:**
1. ✅ Extract all CLI commands from `src/cli/mod.rs`
   - List all commands with full signatures
   - Document all flags and options
   - Note defaults and validation rules

2. ✅ Extract all FFI functions from `crates/arxos/crates/arxos/src/mobile_ffi/ffi.rs` and `jni.rs`
   - List C FFI functions with signatures
   - List JNI functions with Java signatures
   - Document memory management
   - Document error handling

3. ✅ Extract configuration options from `src/config/mod.rs`
   - All configuration keys
   - Environment variables
   - Default values
   - Validation rules

4. ✅ Extract core types from `src/core/`
   - Public structs and enums
   - Key methods
   - Important traits

5. ✅ Document error types from `src/error/mod.rs`
   - All error variants
   - Error codes
   - Context information

### Phase 2: Documentation Writing (Day 2)

**Tasks:**
1. **CLI Commands Section**
   - For each command:
     - Full command signature
     - Description
     - All options/flags with types and defaults
     - Examples (2-3 per command)
     - Common use cases
     - Related commands

2. **Configuration API Section**
   - Complete configuration structure
   - Environment variable reference
   - File-based configuration
   - Precedence rules
   - Validation rules

3. **Mobile FFI Section**
   - C FFI functions (complete signatures)
   - JNI functions (complete signatures)
   - Data structure reference
   - Memory management rules
   - Error handling
   - iOS Swift examples
   - Android Kotlin examples

4. **Core API Section**
   - Key public types
   - Important methods
   - Usage patterns
   - Examples

5. **Error Reference Section**
   - Complete error enumeration
   - Error codes mapping
   - Error handling best practices

### Phase 3: Examples & Polish (Day 3)

**Tasks:**
1. Create comprehensive examples:
   - CLI command workflows
   - FFI integration workflows
   - Configuration examples
   - Error handling examples

2. Add cross-references:
   - Link related commands
   - Link to user guide sections
   - Link to configuration guide

3. Generate table of contents:
   - Auto-generate anchor links
   - Ensure all sections are linked

4. Final review:
   - Check all links
   - Verify examples work
   - Ensure completeness

### Phase 4: rustdoc Generation (Optional - Day 4)

**Tasks:**
1. Configure `Cargo.toml` for documentation:
   ```toml
   [package.metadata.docs.rs]
   features = ["android"]
   ```

2. Set up GitHub Pages or docs.rs:
   - Generate HTML docs
   - Host on GitHub Pages
   - Or publish to docs.rs

3. Add rustdoc link to main README

**Note:** rustdoc generation is nice-to-have, not required for initial implementation.

## Content Standards

### CLI Command Documentation Format

```markdown
### `arx import`

Import an IFC building file into the ArxOS repository.

**Signature:**
```bash
arx import <IFC_FILE> [OPTIONS]
```

**Arguments:**
- `IFC_FILE` (required): Path to IFC file to import

**Options:**
- `--repo <REPO>` (optional): Git repository URL (default: current directory)
- `--dry-run` (flag): Preview changes without making them

**Examples:**

```bash
# Basic import
arx import building.ifc

# Import to specific repository
arx import building.ifc --repo https://github.com/company/buildings.git

# Preview import changes
arx import building.ifc --dry-run
```

**Related Commands:**
- [`arx export`](#arx-export) - Export building data
- [`arx validate`](#arx-validate) - Validate IFC files

**See Also:**
- [IFC Processing Guide](./ifc_processing.md)
```

### FFI Function Documentation Format

```markdown
### `arxos_list_rooms`

List all rooms in a building.

**C Signature:**
```c
char* arxos_list_rooms(const char* building_name);
```

**JNI Signature:**
```java
public native String nativeListRooms(String buildingName);
```

**Parameters:**
- `building_name`: UTF-8 null-terminated string with building identifier

**Returns:**
- JSON string with array of room objects
- Must be freed with `arxos_free_string()`
- Returns error JSON on failure

**Error Codes:**
- `NotFound` (1): Building not found
- `InvalidData` (2): Invalid building name format

**Memory Management:**
The returned string must be freed by calling `arxos_free_string()`.

**Example (iOS/Swift):**
```swift
if let roomsJson = arxos_list_rooms("Main Building") {
    let rooms = try JSONDecoder().decode([Room].self, from: roomsJson.data(using: .utf8)!)
    arxos_free_string(roomsJson)
}
```

**Example (Android/Kotlin):**
```kotlin
val roomsJson = nativeListRooms("Main Building")
val rooms = Gson().fromJson(roomsJson, Array<Room>::class.java)
```
```

## Automation Strategy

### Option 1: Manual Documentation (Recommended Initially)

**Approach:** Write documentation manually by extracting information from code.

**Pros:**
- Full control over format and examples
- Can add contextual information
- Easier to maintain consistency
- Better for user-facing docs

**Cons:**
- Manual effort required
- Must update when code changes

### Option 2: Generate from Code (Future Enhancement)

**Approach:** Use scripts to extract information from code and generate docs.

**Tools:**
- Parse `clap` definitions for CLI commands
- Extract rustdoc comments
- Parse FFI function signatures

**Pros:**
- Automatic updates
- Always in sync with code

**Cons:**
- Requires tooling
- Less flexible formatting
- May need manual curation

### Recommendation

**Start with Manual, Plan for Automation**

1. **Phase 1-3**: Manual documentation (ensures quality)
2. **Future**: Add scripts to extract basic info, then curate manually
3. **Long-term**: Full automation where appropriate

## Maintenance Strategy

### When to Update

1. **New Commands/FFI Functions**: Add immediately
2. **Breaking Changes**: Update immediately
3. **New Options/Flags**: Add within same PR
4. **Documentation Improvements**: As needed

### How to Keep in Sync

1. **CI Check**: Add automated check to ensure:
   - All commands documented
   - All FFI functions documented
   - Examples compile/run

2. **PR Template**: Require documentation updates for API changes

3. **Regular Review**: Quarterly review of documentation completeness

## Success Criteria

✅ **Complete** when:
- Every CLI command has full documentation
- Every FFI function has signatures and examples
- Configuration options are fully documented
- Error codes are documented
- Examples work and are tested
- Document is linked from README
- Searchable/indexed (if possible)

## Timeline

- **Phase 1** (Day 1): Content collection - 4-6 hours
- **Phase 2** (Day 2): Documentation writing - 6-8 hours
- **Phase 3** (Day 3): Examples & polish - 4-6 hours
- **Phase 4** (Day 4, optional): rustdoc setup - 2-4 hours

**Total: 2-3 days** (as estimated)

## Questions to Resolve

1. **Hosting**: GitHub Pages vs docs.rs vs both?
   - **Recommendation**: Start with GitHub Pages (simple), add docs.rs later

2. **Format**: Markdown vs HTML vs both?
   - **Recommendation**: Markdown source (easy to edit), HTML generated for viewing

3. **Versioning**: How to handle API changes?
   - **Recommendation**: Version tags in document, link to versioned docs

4. **Examples**: Real code vs pseudocode?
   - **Recommendation**: Real, tested code examples

5. **Scope**: Include internal APIs or only public?
   - **Recommendation**: Public APIs only, internal APIs in code comments

## Next Steps

1. ✅ Review and approve this plan
2. Start Phase 1: Content collection
3. Create document structure
4. Begin documentation writing
5. Iterate based on feedback

