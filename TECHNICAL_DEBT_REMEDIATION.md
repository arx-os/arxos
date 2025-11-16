# Technical Debt Remediation Plan
**Project:** ArxOS v2.0
**Date Created:** 2025-11-16
**Target Completion:** 8-10 weeks
**Status:** In Progress

## Executive Summary

This document tracks the systematic remediation of technical debt identified in the November 2025 code quality audit. The audit identified 70+ issues across 4 severity levels affecting both the Rust backend (`/src`) and React PWA (`/pwa`).

**Total Issues:** 70+
**Critical:** 8 | **High:** 19 | **Medium:** 28 | **Low:** 15

---

## Priority Matrix

| Phase | Focus Area | Tasks | Est. Effort | Status |
|-------|-----------|-------|-------------|--------|
| **Phase 1** | Critical Architecture | 10 tasks | 2-3 weeks | 🔴 Not Started |
| **Phase 2** | High-Priority Stability | 10 tasks | 3-4 weeks | ⚪ Pending |
| **Phase 3** | Medium-Priority Quality | 7 tasks | 2-3 weeks | ⚪ Pending |
| **Phase 4** | Low-Priority Polish | 3 tasks | 1-2 weeks | ⚪ Pending |

---

## Phase 1: Critical Issues (Week 1-2)

### 🎯 Goal: Fix architectural blockers and safety issues

#### Task 1.1: Module Consolidation (CRITICAL)
**Issue:** Duplicate domain and spatial modules cause maintenance nightmare
**Files Affected:**
- `/src/domain/` vs `/src/core/domain/`
- `/src/spatial/` vs `/src/core/spatial/`

**Action Items:**
- [ ] Verify `/src/core/domain/` has complete implementation
- [ ] Delete `/src/domain/address.rs` and `/src/domain/economy.rs`
- [ ] Delete `/src/domain/mod.rs`
- [ ] Delete `/src/spatial/types.rs` and `/src/spatial/grid.rs`
- [ ] Delete `/src/spatial/mod.rs`
- [ ] Update all imports: `use crate::domain::` → `use crate::core::domain::`
- [ ] Update all imports: `use crate::spatial::` → `use crate::core::spatial::`
- [ ] Run `cargo check` and fix all compilation errors
- [ ] Run full test suite: `cargo test`
- [ ] Document change in CHANGELOG.md

**Success Criteria:**
- Zero duplicate module definitions
- All tests passing
- Build succeeds without warnings

**Est. Time:** 4-6 hours
**Assignee:** TBD
**PR:** TBD

---

#### Task 1.2: Fix Critical Unwrap Usage
**Issue:** 496 unwrap/expect calls risk production panics
**Priority Files:**
1. `src/agent/workspace.rs:50-55` (5 unwraps in repo detection)
2. `src/persistence/economy.rs:73,92,93` (snapshot persistence)
3. `src/agent/collab.rs:210,219,222` (temp directory creation)

**Action Items:**
- [ ] Replace `TempDir::new().unwrap()` with proper error handling
- [ ] Replace `git2::Repository::init().unwrap()` with `?` operator
- [ ] Replace `detect_repo_root().unwrap()` with `?` operator
- [ ] Replace `canonicalize().unwrap()` with error context
- [ ] Add error context using `anyhow::Context`
- [ ] Update function signatures to return `Result<T, ArxError>`
- [ ] Add unit tests for error cases
- [ ] Document expected failure modes

**Pattern to Follow:**
```rust
// BEFORE
let tmp = TempDir::new().unwrap();
let repo = Repository::init(tmp.path()).unwrap();

// AFTER
let tmp = TempDir::new()
    .context("Failed to create temporary directory")?;
let repo = Repository::init(tmp.path())
    .context("Failed to initialize Git repository")?;
```

**Success Criteria:**
- Zero unwraps in agent/workspace.rs, persistence/economy.rs, agent/collab.rs
- All functions return proper Result types
- Error messages provide actionable context

**Est. Time:** 8-10 hours
**Assignee:** TBD
**PR:** TBD

---

#### Task 1.3: Fix Unimplemented CLI Commands
**Issue:** Commands print success but do nothing (92 TODOs)
**Files Affected:**
- `src/cli/commands/data.rs` - RoomCommands, EquipmentCommands

**Action Items:**
- [ ] Identify all unimplemented commands (search for "TODO:")
- [ ] Replace fake success with explicit error
- [ ] Create tracking issues for each unimplemented feature
- [ ] Update CLI help text to mark experimental commands
- [ ] Add `#[cfg(feature = "experimental")]` for incomplete features
- [ ] Document implemented vs planned commands in USER_GUIDE.md

**Pattern to Follow:**
```rust
// BEFORE
RoomCommands::Create { name, .. } => {
    println!("🏗️  Creating room: {}", name);
    // TODO: Implement room creation logic
    println!("✅ Room created successfully");
    Ok(())
}

// AFTER
RoomCommands::Create { .. } => {
    Err(ArxError::NotImplemented(
        "Room creation is not yet implemented. \
         Track progress at: https://github.com/arx-os/arxos/issues/XXX"
            .to_string()
    ))
}
```

**Success Criteria:**
- All unimplemented commands return clear errors
- GitHub issues created for each unimplemented feature
- User documentation reflects actual functionality

**Est. Time:** 2-3 hours
**Assignee:** TBD
**PR:** TBD

---

#### Task 1.4: Remove React Type Safety Issues
**Issue:** 26+ `as any` casts bypass TypeScript safety
**Files Affected:**
- `pwa/src/lib/commandExecutor.ts:85`
- `pwa/src/state/git.ts`
- `pwa/src/state/ifc.ts`

**Action Items:**
- [ ] Create proper TypeScript interfaces for command responses
- [ ] Replace `command as any` with typed interfaces
- [ ] Create type guards for runtime validation
- [ ] Replace `as unknown as GitStatus` with proper parsing
- [ ] Fix Buffer type handling in ifc.ts
- [ ] Enable `@typescript-eslint/no-explicit-any` lint rule
- [ ] Run `npm run type-check` and fix all errors

**Pattern to Follow:**
```typescript
// BEFORE
const response = await client.send(command as any, payload);

// AFTER
interface CommandResponse {
  success: boolean;
  data?: unknown;
  error?: string;
}

function isCommandResponse(obj: unknown): obj is CommandResponse {
  return typeof obj === 'object' && obj !== null && 'success' in obj;
}

const response = await client.send(command, payload);
if (!isCommandResponse(response)) {
  throw new Error('Invalid response format');
}
```

**Success Criteria:**
- Zero `as any` casts in production code
- All responses properly typed
- Type checking passes without errors

**Est. Time:** 6-8 hours
**Assignee:** TBD
**PR:** TBD

---

## Phase 2: High Priority (Week 3-4)

### 🎯 Goal: Improve stability and maintainability

#### Task 2.1: Standardize Error Handling
**Action Items:**
- [ ] Create domain-specific error types using `thiserror`
- [ ] Implement `anyhow::Context` for error propagation
- [ ] Create error formatting helper functions
- [ ] Define error message style guide
- [ ] Add structured error logging

**Est. Time:** 8-10 hours

---

#### Task 2.2: Refactor Large Files
**Target Files:**
- `render3d/effects.rs` (944 lines) → Break into effect types
- `render3d/renderer.rs` (904 lines) → Extract rendering pipeline
- `tui/users.rs` (857 lines) → Separate concerns

**Action Items:**
- [ ] Analyze each file for logical boundaries
- [ ] Extract modules/functions
- [ ] Update imports and re-exports
- [ ] Ensure tests still pass

**Est. Time:** 12-16 hours

---

#### Task 2.3: Reduce Clone Usage
**Priority Areas:**
- `render3d/animation.rs` (32 clones!)
- `ifc/enhanced/parser.rs` (6 clones)
- `core/operations/room.rs` (4 clones)

**Action Items:**
- [ ] Profile memory usage in render pipeline
- [ ] Replace clones with references where possible
- [ ] Use `Arc<T>` for shared immutable data
- [ ] Use `Cow<T>` for conditional ownership
- [ ] Benchmark before/after performance

**Est. Time:** 10-12 hours

---

#### Task 2.4: Input Validation Framework
**Action Items:**
- [ ] Create `src/validation/` module
- [ ] Implement path sanitization
- [ ] Add command argument validators
- [ ] Add bounds checking for numeric inputs
- [ ] Implement JSON schema validation
- [ ] Add security tests for validation

**Est. Time:** 10-12 hours

---

## Phase 3: Medium Priority (Week 5-6)

### 🎯 Goal: Improve quality and testing

#### Task 3.1: Improve Test Coverage
**Target Areas:**
- Room creation commands
- Equipment management
- Git operations edge cases
- Error recovery scenarios

**Action Items:**
- [ ] Add unit tests for unimplemented features
- [ ] Create integration test suite for Git ops
- [ ] Add property-based tests for address parsing
- [ ] Target 80%+ coverage for critical paths

**Est. Time:** 16-20 hours

---

#### Task 3.2: Performance Optimization
**Action Items:**
- [ ] Replace magic numbers with named constants
- [ ] Profile render pipeline with flamegraph
- [ ] Implement viewport culling for equipment rendering
- [ ] Add caching for spatial queries
- [ ] Optimize particle system allocations

**Est. Time:** 12-14 hours

---

#### Task 3.3: Accessibility Improvements (PWA)
**Action Items:**
- [ ] Add ARIA labels to interactive elements
- [ ] Implement keyboard navigation for FloorPlanCanvas
- [ ] Add focus ring styling
- [ ] Create accessible status updates
- [ ] Test with screen readers

**Est. Time:** 8-10 hours

---

## Phase 4: Low Priority (Week 7-8)

### 🎯 Goal: Polish and documentation

#### Task 4.1: Documentation
- [ ] Enable `missing_docs` lint incrementally
- [ ] Document public APIs
- [ ] Add usage examples
- [ ] Create architectural decision records

**Est. Time:** 8-10 hours

---

#### Task 4.2: Logging Standardization
- [ ] Replace `println!` with `log` macros
- [ ] Configure log levels per module
- [ ] Add structured logging context

**Est. Time:** 4-6 hours

---

#### Task 4.3: Dead Code Cleanup
- [ ] Remove commented-out code
- [ ] Delete deprecated functions
- [ ] Clean up unused imports

**Est. Time:** 3-4 hours

---

## Engineering Best Practices

### Git Workflow

#### Branch Naming Convention
```
tech-debt/critical/<issue-number>-<short-description>
tech-debt/high/<issue-number>-<short-description>
tech-debt/medium/<issue-number>-<short-description>
tech-debt/low/<issue-number>-<short-description>
```

**Examples:**
- `tech-debt/critical/001-remove-duplicate-modules`
- `tech-debt/critical/002-fix-unwrap-usage-agent`
- `tech-debt/high/003-refactor-effects-module`

#### Commit Message Format
```
[TECH-DEBT] <Type>: <Description>

<Body explaining what and why>

Fixes #<issue-number>
Part of Technical Debt Remediation Plan Phase <N>
```

**Types:** `fix`, `refactor`, `test`, `docs`, `perf`

**Examples:**
```
[TECH-DEBT] refactor: Remove duplicate domain module

Consolidate /src/domain/ into /src/core/domain/ to eliminate
maintenance burden and potential inconsistencies.

- Delete /src/domain/address.rs and /src/domain/economy.rs
- Update all imports to use crate::core::domain::
- Verify all tests pass

Fixes #123
Part of Technical Debt Remediation Plan Phase 1
```

---

### Pull Request Guidelines

#### PR Template for Tech Debt
```markdown
## Technical Debt Remediation

**Phase:** [1/2/3/4]
**Priority:** [Critical/High/Medium/Low]
**Issue:** Closes #XXX

### Changes
- [ ] List specific changes made
- [ ] Include before/after comparisons
- [ ] Document any breaking changes

### Testing
- [ ] All existing tests pass
- [ ] New tests added for fixed issues
- [ ] Manual testing completed

### Checklist
- [ ] Code follows project style guide
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
- [ ] No new compiler warnings
- [ ] Performance impact measured (if applicable)

### Remediation Plan Progress
- Phase 1: X/10 tasks complete
- Phase 2: X/10 tasks complete
- Phase 3: X/7 tasks complete
- Phase 4: X/3 tasks complete
```

---

### Code Review Checklist

**For Critical Issues:**
- [ ] No unwrap/expect introduced
- [ ] Error handling follows project patterns
- [ ] All edge cases have tests
- [ ] Documentation updated

**For Refactoring:**
- [ ] No behavior changes (unless documented)
- [ ] Tests cover all branches
- [ ] Performance benchmarks included
- [ ] Module boundaries clear

**For Type Safety:**
- [ ] No `as any` introduced
- [ ] Type guards used for runtime checks
- [ ] Generic types properly constrained
- [ ] Null checks before casts

---

## Progress Tracking

### Metrics

| Metric | Baseline (Nov 2025) | Target | Current |
|--------|---------------------|--------|---------|
| Unwrap/Expect Count | 496 | <50 | TBD |
| `as any` Count | 26+ | 0 | TBD |
| TODO Comments | 92 | <10 | TBD |
| Duplicate Modules | 2 | 0 | TBD |
| Clone Usage | 89+ | <30 | TBD |
| Files >500 Lines | 8 | <3 | TBD |
| Test Coverage | ~60% | >80% | TBD |

### Weekly Status Updates

#### Week 1
**Date:** TBD
**Tasks Completed:**
**Blockers:**
**Next Week:**

#### Week 2
**Date:** TBD
**Tasks Completed:**
**Blockers:**
**Next Week:**

---

## Risk Management

### Identified Risks

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Breaking changes during refactor | High | Medium | Comprehensive test suite, incremental changes |
| Performance regression | Medium | Low | Benchmark before/after, profiling |
| Merge conflicts | Medium | High | Small PRs, frequent merges |
| Timeline overrun | Medium | Medium | Prioritize critical issues, defer low priority |

### Rollback Plan

If a refactoring introduces critical bugs:
1. Immediately revert the problematic PR
2. Create hotfix branch from previous stable version
3. Document the issue in GitHub
4. Revise approach before re-attempting

---

## Success Criteria

### Phase 1 Complete When:
- [ ] Zero duplicate modules in codebase
- [ ] Zero unwraps in critical paths (agent, persistence)
- [ ] All unimplemented commands return errors
- [ ] Zero `as any` in React production code
- [ ] All tests passing
- [ ] Build succeeds without warnings

### Phase 2 Complete When:
- [ ] Error handling standardized across all modules
- [ ] No files >700 lines
- [ ] Clone usage reduced by 50%
- [ ] Input validation framework in place

### Phase 3 Complete When:
- [ ] Test coverage >80% for critical paths
- [ ] Performance benchmarks improved
- [ ] Accessibility audit passes

### Phase 4 Complete When:
- [ ] Documentation coverage >90%
- [ ] No `println!` in library code
- [ ] Zero commented-out dead code

---

## Resources

### Tools
- **Rust:** `cargo clippy`, `cargo test`, `cargo tarpaulin` (coverage)
- **TypeScript:** `npm run type-check`, `eslint`, `vitest`
- **Profiling:** `cargo flamegraph`, Chrome DevTools
- **Benchmarking:** `cargo bench`, `criterion`

### Documentation
- [Rust Error Handling Best Practices](https://doc.rust-lang.org/book/ch09-00-error-handling.html)
- [TypeScript Type Guards](https://www.typescriptlang.org/docs/handbook/2/narrowing.html)
- [React Testing Best Practices](https://kentcdodds.com/blog/common-mistakes-with-react-testing-library)

### References
- Original Audit Report: `docs/audits/2025-11-16-code-quality-audit.md`
- Architecture Documentation: `docs/core/ARCHITECTURE.md`
- Refactoring Guide: `REFACTORING_GUIDE.md`

---

## Questions or Concerns?

Contact the team lead or open an issue with label `tech-debt`.

---

**Last Updated:** 2025-11-16
**Next Review:** TBD
**Owner:** TBD
