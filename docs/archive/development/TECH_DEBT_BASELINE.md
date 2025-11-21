# Technical Debt Baseline Metrics

**Assessment Date:** November 16, 2025
**Assessor:** Code Quality Audit
**Baseline Established:** November 16, 2025

---

## Current State Metrics

### Critical Issues

| Metric | Current | Target | Gap | Priority |
|--------|---------|--------|-----|----------|
| **Unwrap/Expect Count** | 316 | <50 | -266 | 🔴 CRITICAL |
| **Duplicate Modules** | 2 | 0 | -2 | 🔴 CRITICAL |
| **TODO Comments** | 92 | <10 | -82 | 🔴 CRITICAL |
| **TypeScript `as any`** | 27 | 0 | -27 | 🔴 CRITICAL |

### Code Quality Issues

| Metric | Current | Target | Gap | Priority |
|--------|---------|--------|-----|----------|
| **Clone Usage** | 329 | <30 | -299 | 🟡 HIGH |
| **Large Files (>500 lines)** | 24 | <3 | -21 | 🟡 HIGH |
| **Clippy Warnings** | 93 | 0 | -93 | 🟡 HIGH |

### Testing Metrics

| Metric | Current | Notes |
|--------|---------|-------|
| **Integration Test Files** | 60 | Good coverage structure |
| **Test Functions** | 1026 | Substantial test suite |
| **Build Status** | ✅ PASS | No compilation errors |

---

## Top 10 Largest Files (Refactoring Targets)

| Rank | File | Lines | Refactoring Priority |
|------|------|-------|---------------------|
| 1 | `src/ifc/hierarchy/builder.rs` | 987 | 🔴 HIGH |
| 2 | `src/render3d/effects.rs` | 944 | 🔴 HIGH |
| 3 | `src/render3d/renderer.rs` | 904 | 🔴 HIGH |
| 4 | `src/tui/users.rs` | 857 | 🔴 HIGH |
| 5 | `src/render3d/interactive.rs` | 848 | 🔴 HIGH |
| 6 | `src/core/error/mod.rs` | 791 | 🟡 MEDIUM |
| 7 | `src/ifc/enhanced/spatial_index.rs` | 782 | 🟡 MEDIUM |
| 8 | `src/render3d/animation.rs` | 762 | 🔴 HIGH |
| 9 | `src/tui/theme_manager.rs` | 720 | 🟡 MEDIUM |
| 10 | `src/tui/help/content.rs` | 720 | 🟢 LOW (mostly content) |

---

## Duplicate Module Details

### Module Set 1: Domain
- **Legacy:** `/src/domain/` (incomplete stub)
  - `address.rs` - 9,980 bytes
  - `economy.rs` - 1,678 bytes
  - `mod.rs` - Basic exports

- **Current:** `/src/core/domain/` (complete implementation)
  - `address.rs` - 20,179 bytes (full ArxAddress system)
  - `economy.rs` - 2,537 bytes (complete economy logic)
  - `mod.rs` - Complete exports with RESERVED_SYSTEMS

**Action:** Delete `/src/domain/` entirely, use only `/src/core/domain/`

### Module Set 2: Spatial
- **Legacy:** `/src/spatial/`
  - `types.rs` - 3,398 bytes
  - `grid.rs` - 8,153 bytes

- **Current:** `/src/core/spatial/`
  - `types.rs` - 9,093 bytes (extended types)
  - `grid.rs` - 8,286 bytes (updated grid system)

**Action:** Delete `/src/spatial/` entirely, use only `/src/core/spatial/`

---

## Clippy Warnings Breakdown (93 total)

### By Category (estimated)
- Missing documentation: ~40%
- Unused code/imports: ~20%
- Complexity warnings: ~15%
- Performance warnings: ~15%
- Style warnings: ~10%

### Action Required
1. Run `cargo clippy --all-features` to get full list
2. Fix critical warnings first (performance, correctness)
3. Address style warnings in bulk
4. Enable documentation linting incrementally

---

## Progress Tracking Formula

### Overall Health Score
```
Health Score = (Metrics Meeting Targets / Total Metrics) × 100

Current: 0/6 = 0%
Phase 1 Target: 4/6 = 67%
Phase 2 Target: 5/6 = 83%
Final Target: 6/6 = 100%
```

### Weekly Targets

| Week | Focus | Target Metrics |
|------|-------|----------------|
| **Week 1-2** | Critical fixes | Duplicate Modules: 0<br>TODOs with issues: 92<br>`as any`: <10 |
| **Week 3-4** | Error handling | Unwrap/Expect: <200<br>Large files: <18 |
| **Week 5-6** | Quality improvements | Unwrap/Expect: <100<br>Clones: <200 |
| **Week 7-8** | Final cleanup | All metrics at target |

---

## Risk Assessment

### High-Risk Areas (Requires Careful Refactoring)

1. **IFC Hierarchy Builder** (987 lines)
   - Complex state management
   - Many dependencies
   - Critical for IFC import
   - **Risk:** Breaking IFC processing
   - **Mitigation:** Comprehensive integration tests before refactoring

2. **Render3D Effects** (944 lines)
   - Performance-critical code
   - Complex graphics algorithms
   - **Risk:** Performance regression
   - **Mitigation:** Benchmark before/after

3. **TUI Users Module** (857 lines)
   - State management complexity
   - Event handling logic
   - **Risk:** UI bugs
   - **Mitigation:** Manual testing checklist

### Medium-Risk Areas

4. **Render3D Renderer** (904 lines)
5. **Render3D Interactive** (848 lines)
6. **Spatial Index** (782 lines)

### Low-Risk Areas (Safe to Refactor)

7. **Theme Manager** (720 lines) - Mostly configuration
8. **Help Content** (720 lines) - Mostly text content
9. **Error Modal** (605 lines) - UI logic, well-isolated

---

## Dependency Audit

### Rust Dependencies
- **Total:** 80+ dependencies
- **Outdated:** Run `cargo outdated` to check
- **Security:** Run `cargo audit` regularly
- **Unused:** Run `cargo machete` to detect

### npm Dependencies (PWA)
- **Total:** 40+ dependencies
- **Outdated:** Run `npm outdated`
- **Security:** Run `npm audit`
- **Bundle size:** Monitor with `npm run build -- --analyze`

---

## Test Coverage Goals

### Current Coverage (Estimated)
- **Core modules:** ~70%
- **IFC processing:** ~60%
- **Git operations:** ~75%
- **TUI components:** ~40%
- **Render3D:** ~50%
- **CLI commands:** ~30%

### Phase 1 Targets
- Core modules: 75%
- IFC processing: 70%
- Git operations: 85%
- CLI commands: 60%

### Final Targets
- Core modules: 85%
- IFC processing: 80%
- Git operations: 90%
- CLI commands: 75%
- TUI components: 60%
- Render3D: 70%

---

## Automation & Tooling

### Recommended CI/CD Additions

```yaml
# .github/workflows/tech-debt-metrics.yml
name: Tech Debt Metrics

on:
  pull_request:
  push:
    branches: [main]

jobs:
  metrics:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Check Tech Debt Metrics
        run: ./scripts/check_tech_debt.sh
      - name: Fail if metrics regressed
        run: |
          # Fail if unwrap count increased
          # Fail if new large files added
          # etc.
```

### Pre-commit Hooks

Add to `.pre-commit-config.yaml`:
```yaml
repos:
  - repo: local
    hooks:
      - id: check-unwrap
        name: Check for new unwrap() calls
        entry: bash -c 'git diff --cached | grep -q "\.unwrap()" && echo "Error: unwrap() detected" && exit 1 || exit 0'
        language: system

      - id: check-as-any
        name: Check for new as any casts
        entry: bash -c 'git diff --cached | grep -q "as any" && echo "Error: as any detected" && exit 1 || exit 0'
        language: system
```

---

## Success Criteria

### Phase 1 Success (Week 2)
- ✅ Zero duplicate modules
- ✅ All TODOs have GitHub issue tracking
- ✅ CLI commands return errors for unimplemented features
- ✅ TypeScript `as any` reduced to <10
- ✅ Build passes with zero errors
- ✅ Clippy warnings reduced to <50

### Phase 2 Success (Week 4)
- ✅ Unwrap/Expect count <200
- ✅ Large files reduced to <18
- ✅ Error handling standardized
- ✅ Top 5 largest files refactored

### Phase 3 Success (Week 6)
- ✅ Unwrap/Expect count <100
- ✅ Clone usage <200
- ✅ Test coverage >75% for critical paths
- ✅ Large files reduced to <10

### Final Success (Week 8)
- ✅ All metrics meeting targets
- ✅ Zero clippy warnings
- ✅ Zero `as any` in production code
- ✅ Documentation coverage >90%
- ✅ All integration tests passing

---

## Comparison to Industry Standards

### Rust Projects (Similar Size)
- **Unwrap Usage:** Typically <1% of function calls
  - ArxOS: Currently ~0.7% (316/45000 lines) ✅ Acceptable
  - Target: <0.1% (50/45000 lines)

- **File Size:** Typically <400 lines per file
  - ArxOS: 24 files >500 lines ⚠️ Above average
  - Industry average: 250-300 lines per file

- **Clone Usage:** Varies by domain
  - ArxOS: 329 clones (high for performance-critical code)
  - Recommendation: Profile and reduce in hot paths

### TypeScript Projects
- **Type Safety:** Should be 100% typed
  - ArxOS: 27 `as any` casts ⚠️ Below standard
  - Target: 0 unsafe casts

---

## Next Steps

1. **Week 1 Kickoff:**
   - [ ] Create GitHub project board
   - [ ] Create issues for Phase 1 tasks
   - [ ] Assign ownership
   - [ ] Schedule daily standups

2. **Weekly Reviews:**
   - [ ] Run `./scripts/check_tech_debt.sh` every Friday
   - [ ] Update TECHNICAL_DEBT_REMEDIATION.md progress
   - [ ] Adjust priorities based on findings
   - [ ] Celebrate wins! 🎉

3. **Communication:**
   - [ ] Share plan with team
   - [ ] Get stakeholder buy-in
   - [ ] Set realistic expectations
   - [ ] Plan for dedicated tech debt time

---

**Baseline Established:** November 16, 2025, 11:53 AM EST
**Next Assessment:** Weekly (every Friday)
**Full Completion Target:** January 15, 2026 (8-10 weeks)
