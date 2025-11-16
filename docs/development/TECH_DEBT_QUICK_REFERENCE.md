# Technical Debt Quick Reference Card

**Last Updated:** 2025-11-16

## 🎯 Quick Commands

### Check Current Metrics
```bash
./scripts/check_tech_debt.sh
```

### Run Quality Checks
```bash
# Rust linting
cargo clippy --all-features

# Rust tests
cargo test

# TypeScript type checking
cd pwa && npm run type-check

# Full check
cargo clippy && cargo test && cd pwa && npm run type-check
```

### Before Committing
```bash
# Format code
cargo fmt
cd pwa && npm run format

# Check for unwraps you might have added
git diff | grep -i "unwrap"

# Run quick smoke tests
cargo test --lib
```

---

## 🚫 Code Patterns to AVOID

### ❌ DON'T: Use unwrap/expect
```rust
// BAD
let result = operation().unwrap();
let value = option.expect("should exist");

// GOOD
let result = operation()
    .context("Failed to perform operation")?;
let value = option
    .ok_or_else(|| ArxError::NotFound("value".into()))?;
```

### ❌ DON'T: Use 'as any' in TypeScript
```typescript
// BAD
const response = await client.send(command as any, payload);

// GOOD
interface CommandPayload {
  command: string;
  args: string[];
}
const response = await client.send(command, payload as CommandPayload);
```

### ❌ DON'T: Leave TODOs without tracking
```rust
// BAD
// TODO: Implement this feature

// GOOD
// TODO(#123): Implement room creation
// See: https://github.com/arx-os/arxos/issues/123
return Err(ArxError::NotImplemented(
    "Room creation tracked at: #123".into()
));
```

### ❌ DON'T: Clone unnecessarily
```rust
// BAD
fn process_building(building: &Building) {
    let copy = building.clone();  // Unnecessary clone
    for floor in &copy.floors { ... }
}

// GOOD
fn process_building(building: &Building) {
    for floor in &building.floors { ... }
}
```

### ❌ DON'T: Create large monolithic files
```rust
// BAD: single file with 900+ lines

// GOOD: break into modules
mod effects {
    pub mod visual;
    pub mod particle;
    pub mod animation;
}
```

---

## ✅ Code Patterns to FOLLOW

### ✓ DO: Proper Error Handling
```rust
use anyhow::Context;

fn load_building(path: &Path) -> Result<Building, ArxError> {
    let content = fs::read_to_string(path)
        .with_context(|| format!("Failed to read building file: {}", path.display()))?;

    let building: Building = serde_yaml::from_str(&content)
        .context("Failed to parse building YAML")?;

    Ok(building)
}
```

### ✓ DO: Type-Safe TypeScript
```typescript
// Define proper types
interface GitStatus {
  branch: string;
  modified: string[];
  staged: string[];
}

// Use type guards
function isGitStatus(obj: unknown): obj is GitStatus {
  return (
    typeof obj === 'object' &&
    obj !== null &&
    'branch' in obj &&
    typeof obj.branch === 'string'
  );
}

// Validate at runtime
const response = await fetchGitStatus();
if (!isGitStatus(response)) {
  throw new Error('Invalid git status response');
}
```

### ✓ DO: Use References Over Clones
```rust
// Use Arc for shared ownership
use std::sync::Arc;

#[derive(Clone)]
struct RenderState {
    config: Arc<RenderConfig>,  // Cheap clone
    entities: Vec<Entity>,       // Still cloned when needed
}

// Use Cow for conditional ownership
use std::borrow::Cow;

fn format_name<'a>(name: &'a str, uppercase: bool) -> Cow<'a, str> {
    if uppercase {
        Cow::Owned(name.to_uppercase())
    } else {
        Cow::Borrowed(name)
    }
}
```

### ✓ DO: Break Down Large Functions
```rust
// BEFORE: One large function
fn process_building(building: &Building) {
    // 200 lines of code...
}

// AFTER: Smaller focused functions
fn process_building(building: &Building) -> Result<()> {
    validate_building(building)?;
    let spatial_index = build_spatial_index(building)?;
    update_equipment_status(building, &spatial_index)?;
    Ok(())
}

fn validate_building(building: &Building) -> Result<()> { ... }
fn build_spatial_index(building: &Building) -> Result<SpatialIndex> { ... }
fn update_equipment_status(building: &Building, index: &SpatialIndex) -> Result<()> { ... }
```

### ✓ DO: Write Meaningful Tests
```rust
#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_building_creation_with_valid_data() {
        // Arrange
        let building_data = BuildingData {
            name: "Test Building".into(),
            floors: vec![],
        };

        // Act
        let result = Building::new(building_data);

        // Assert
        assert!(result.is_ok());
        let building = result.unwrap();
        assert_eq!(building.name, "Test Building");
    }

    #[test]
    fn test_building_creation_with_invalid_data() {
        // Arrange
        let building_data = BuildingData {
            name: "".into(),  // Invalid empty name
            floors: vec![],
        };

        // Act
        let result = Building::new(building_data);

        // Assert
        assert!(result.is_err());
        assert!(matches!(result, Err(ArxError::ValidationError(_))));
    }
}
```

---

## 📋 Pre-Commit Checklist

Before pushing your tech debt fixes:

- [ ] Run `./scripts/check_tech_debt.sh` to verify metrics improved
- [ ] Run `cargo fmt` to format Rust code
- [ ] Run `cargo clippy` and fix all warnings
- [ ] Run `cargo test` and ensure all tests pass
- [ ] Run `cd pwa && npm run type-check` for TypeScript
- [ ] Review your diff for any `unwrap()`, `as any`, or `TODO` additions
- [ ] Update `TECHNICAL_DEBT_REMEDIATION.md` progress section
- [ ] Ensure commit message follows `[TECH-DEBT]` format
- [ ] Link PR to related GitHub issue

---

## 🏷️ Issue Labels

Use these labels when creating GitHub issues:

| Label | When to Use |
|-------|-------------|
| `tech-debt` | All technical debt issues |
| `priority:critical` | Phase 1 - Must fix immediately |
| `priority:high` | Phase 2 - Fix soon |
| `priority:medium` | Phase 3 - Fix when possible |
| `priority:low` | Phase 4 - Nice to have |
| `type:refactor` | Code structure improvements |
| `type:performance` | Performance optimizations |
| `type:security` | Security-related fixes |
| `type:testing` | Test coverage improvements |
| `type:docs` | Documentation updates |

---

## 🔍 Finding Issues

### Search for Unwraps
```bash
# Find all unwrap() calls
grep -rn "\.unwrap()" src/ --include="*.rs"

# Find all expect() calls
grep -rn "\.expect(" src/ --include="*.rs"
```

### Search for Type Casts
```bash
# Find 'as any' in TypeScript
grep -rn "as any" pwa/src --include="*.ts" --include="*.tsx"

# Find type assertions in TypeScript
grep -rn " as " pwa/src --include="*.ts" --include="*.tsx"
```

### Search for TODOs
```bash
# Find all TODO comments
grep -rn "TODO:" src/ --include="*.rs"
grep -rn "FIXME:" src/ --include="*.rs"
grep -rn "HACK:" src/ --include="*.rs"
```

### Find Large Files
```bash
# Find Rust files > 500 lines
find src -name "*.rs" -type f -exec wc -l {} \; | awk '$1 > 500'

# Find TypeScript files > 300 lines
find pwa/src -name "*.ts" -o -name "*.tsx" -type f -exec wc -l {} \; | awk '$1 > 300'
```

### Find Clone Usage
```bash
# Find all .clone() calls
grep -rn "\.clone()" src/ --include="*.rs" | wc -l

# Find files with many clones (>5)
for file in $(find src -name "*.rs"); do
  count=$(grep -c "\.clone()" "$file" 2>/dev/null || echo 0)
  if [ $count -gt 5 ]; then
    echo "$file: $count clones"
  fi
done
```

---

## 📊 Metric Targets

| Metric | Current | Target | Status |
|--------|---------|--------|--------|
| Unwrap/Expect | 496 | <50 | 🔴 |
| `as any` | 26+ | 0 | 🔴 |
| TODO Comments | 92 | <10 | 🔴 |
| Duplicate Modules | 2 | 0 | 🔴 |
| Clone Usage | 89+ | <30 | 🔴 |
| Large Files (>500 lines) | 8 | <3 | 🔴 |
| Test Coverage | ~60% | >80% | 🟡 |

**Legend:**
- 🔴 Critical - Needs immediate attention
- 🟡 Warning - Approaching target
- 🟢 Good - Meeting target

---

## 🆘 Need Help?

### Common Questions

**Q: Can I use `.unwrap()` in tests?**
A: Yes, but prefer `.expect("meaningful message")` to make test failures clear.

**Q: What if I need to clone for ownership?**
A: Consider `Arc<T>`, `Cow<'a, T>`, or restructuring to use references.

**Q: How do I handle errors in async code?**
A: Use the `?` operator with proper error context, just like sync code.

**Q: Should I fix ALL tech debt in one PR?**
A: No! Make small, focused PRs. One issue category at a time.

**Q: What if fixing a TODO requires significant new features?**
A: Create a GitHub issue, return an error from the function, document it.

### Resources

- Full remediation plan: `TECHNICAL_DEBT_REMEDIATION.md`
- Architecture docs: `docs/core/ARCHITECTURE.md`
- Rust error handling: https://doc.rust-lang.org/book/ch09-00-error-handling.html
- TypeScript narrowing: https://www.typescriptlang.org/docs/handbook/2/narrowing.html

---

## 🎯 Remember

**Quality over Speed**
- It's okay to take time to do it right
- Small, tested incremental changes
- Review your own code before requesting review

**Test Everything**
- Write tests for the bug you're fixing
- Ensure existing tests still pass
- Add edge case tests

**Document Why, Not What**
- Explain the reason for the change
- Link to issues and discussions
- Update docs when behavior changes

**Ask for Help**
- Unsure about approach? Ask!
- Need architecture review? Request it!
- Stuck on a tricky refactor? Pair program!

---

**Keep this reference handy while working on tech debt remediation!**
