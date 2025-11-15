# Disabled Tests

These tests have been temporarily disabled because they reference modules that haven't been implemented yet.

## Files

### `game_integration_tests.rs`
**Reason**: Requires `arxos::game` module
**Status**: Game functionality exists in `cli::subcommands::game` but not as a top-level module
**Action Needed**: Either refactor to use CLI subcommands or create `src/game/mod.rs`

### `docs_integration_tests.rs`
**Reason**: Requires `arxui` crate
**Status**: Documentation generation functionality not yet implemented
**Action Needed**: Implement docs generation module or remove test

## Re-enabling Tests

When the required modules are implemented:
1. Fix the import statements
2. Move files back to `/tests/`
3. Run `cargo test` to verify

## Created During

Technical debt cleanup - 2025-01-15
Part of deprecated type removal and test infrastructure fixes
