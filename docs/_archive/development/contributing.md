# Contributing to ArxOS

Guidelines for contributing to the ArxOS project.

---

## Welcome

Thank you for considering contributing to ArxOS! We welcome contributions of all kinds:

- Bug reports
- Feature requests
- Code contributions
- Documentation improvements
- Testing and QA
- Community support

---

## Getting Started

### 1. Fork and Clone

```bash
# Fork the repository on GitHub
# Then clone your fork

git clone https://github.com/YOUR_USERNAME/arxos.git
cd arxos

# Add upstream remote
git remote add upstream https://github.com/arx-os/arxos.git
```

### 2. Set Up Development Environment

```bash
# Install Rust
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# Install development tools
rustup component add rustfmt clippy

# Build the project
cargo build

# Run tests
cargo test
```

### 3. Create a Branch

```bash
# Create feature branch
git checkout -b feature/my-new-feature

# Or bugfix branch
git checkout -b fix/bug-description
```

---

## Development Workflow

### 1. Make Changes

- Write clear, concise code
- Follow Rust idioms and conventions
- Add tests for new functionality
- Update documentation as needed

### 2. Format Code

```bash
# Format all code
cargo fmt

# Check formatting
cargo fmt -- --check
```

### 3. Lint Code

```bash
# Run clippy
cargo clippy --all-features

# Fix warnings
cargo clippy --all-features --fix
```

### 4. Test

```bash
# Run all tests
cargo test --all-features

# Run specific tests
cargo test test_name

# Run benchmarks (check only)
cargo bench --no-run
```

### 5. Commit

```bash
# Stage changes
git add .

# Commit with descriptive message
git commit -m "feat: Add support for IFC4 geometry"

# Follow conventional commits format
```

### 6. Push and Create PR

```bash
# Push to your fork
git push origin feature/my-new-feature

# Create Pull Request on GitHub
# Fill out the PR template
# Link related issues
```

---

## Commit Message Format

We follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

### Types

- `feat` – New feature
- `fix` – Bug fix
- `docs` – Documentation changes
- `style` – Code style (formatting, semicolons, etc.)
- `refactor` – Code refactoring
- `perf` – Performance improvements
- `test` – Adding or updating tests
- `build` – Build system or dependencies
- `ci` – CI configuration
- `chore` – Other changes (maintenance, etc.)

### Examples

```bash
feat(ifc): Add support for IFC4 advanced geometry
fix(git): Resolve merge conflict handling bug
docs(readme): Update installation instructions
test(core): Add tests for Building creation
refactor(cli): Simplify command parsing logic
```

---

## Code Style

### Rust Conventions

- Use `snake_case` for variables and functions
- Use `PascalCase` for types and traits
- Use `SCREAMING_SNAKE_CASE` for constants
- Max line length: 100 characters
- Use meaningful variable names

### Documentation

```rust
/// Brief description of function
///
/// More detailed explanation if needed.
///
/// # Arguments
///
/// * `name` - The building name
/// * `floors` - Number of floors
///
/// # Returns
///
/// A new `Building` instance
///
/// # Examples
///
/// ```
/// let building = Building::new("Office Tower", 10);
/// assert_eq!(building.name, "Office Tower");
/// ```
pub fn new(name: &str, floors: i32) -> Building {
    // Implementation
}
```

### Error Handling

```rust
// Use Result for operations that can fail
pub fn import_ifc(path: &str) -> Result<Building, ArxError> {
    let parser = IfcParser::new(path)?;
    let building = parser.parse()?;
    Ok(building)
}

// Avoid unwrap() in production code
// Use ? operator or proper error handling
```

### Testing

```rust
#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_feature_works() {
        let result = my_function();
        assert_eq!(result, expected);
    }

    #[test]
    #[should_panic(expected = "error message")]
    fn test_feature_panics() {
        invalid_operation();
    }
}
```

---

## Pull Request Guidelines

### Before Submitting

- [ ] Code compiles without errors
- [ ] All tests pass: `cargo test --all-features`
- [ ] Code is formatted: `cargo fmt`
- [ ] No clippy warnings: `cargo clippy --all-features`
- [ ] Documentation is updated
- [ ] Commit messages follow convention
- [ ] Branch is up to date with main

### PR Description

Include:

1. **What** – What does this PR do?
2. **Why** – Why is this change needed?
3. **How** – How does it work?
4. **Testing** – How was it tested?
5. **Related Issues** – Links to related issues

**Example:**

```markdown
## Description

Adds support for IFC4 advanced geometry types including IFCBOOLEANCLIPPINGRESULT.

## Motivation

Many modern IFC files use IFC4 geometry that was previously unsupported,
causing import failures.

## Implementation

- Added parser for IFCBOOLEANCLIPPINGRESULT entities
- Extended geometry extraction to handle boolean operations
- Added unit tests for new geometry types

## Testing

- Added test fixture: test_data/ifc4-boolean.ifc
- All existing tests pass
- New test: test_ifc4_boolean_geometry()

## Related Issues

Closes #123
Related to #456
```

---

## Issue Guidelines

### Bug Reports

Include:

1. **Description** – Clear description of the bug
2. **Steps to Reproduce** – How to trigger the bug
3. **Expected Behavior** – What should happen
4. **Actual Behavior** – What actually happens
5. **Environment** – OS, Rust version, ArxOS version
6. **Logs** – Relevant error messages or logs

**Example:**

```markdown
**Bug Description**
IFC import fails with "Invalid entity" error for IFC4 files.

**Steps to Reproduce**
1. Run: arx import building-ifc4.ifc
2. Observe error: "Invalid entity: IFCADVANCEDBREP"

**Expected Behavior**
IFC4 files should import successfully.

**Actual Behavior**
Import fails with error.

**Environment**
- OS: Windows 11
- Rust: 1.75.0
- ArxOS: 2.0.0

**Logs**
```
Error: Invalid entity: IFCADVANCEDBREP at line 4352
```
```

### Feature Requests

Include:

1. **Description** – What feature do you want?
2. **Use Case** – Why is it needed?
3. **Proposed Solution** – How might it work?
4. **Alternatives** – Other approaches considered?

---

## Code Review Process

### What We Look For

- **Correctness** – Does it work as intended?
- **Tests** – Are there adequate tests?
- **Documentation** – Is it documented?
- **Style** – Follows style guidelines?
- **Performance** – No obvious performance issues?
- **Maintainability** – Is it understandable?

### Review Timeline

- Initial review within 48 hours
- Follow-up reviews as changes are made
- Approval from at least one maintainer required

### Addressing Feedback

```bash
# Make requested changes
# Commit changes
git add .
git commit -m "refactor: Address review feedback"

# Push to update PR
git push origin feature/my-new-feature
```

---

## Areas to Contribute

### Good First Issues

Look for issues labeled `good-first-issue`:
- Documentation improvements
- Simple bug fixes
- Test coverage improvements
- Code cleanup

### Priority Areas

- IFC parser improvements
- 3D rendering enhancements
- Web interface features
- Sensor integration
- Performance optimization

### Documentation

- API documentation
- Usage examples
- Tutorial content
- Architecture diagrams

---

## Community

### Communication

- **GitHub Issues** – Bug reports, feature requests
- **GitHub Discussions** – General questions, ideas
- **Pull Requests** – Code contributions

### Code of Conduct

Be respectful and constructive:
- Welcome newcomers
- Provide helpful feedback
- Assume good intentions
- Focus on the code, not the person

---

## Development Tips

### Incremental Changes

- Make small, focused changes
- One feature/fix per PR
- Easier to review and merge

### Test-Driven Development

```bash
# 1. Write failing test
#[test]
fn test_new_feature() {
    assert_eq!(new_feature(), expected);
}

# 2. Implement feature
pub fn new_feature() -> Type {
    // Implementation
}

# 3. Run test
cargo test test_new_feature

# 4. Refactor if needed
```

### Debugging

```bash
# Enable debug logging
RUST_LOG=debug cargo run -- <command>

# Use dbg! macro
dbg!(&variable);

# Run with backtrace
RUST_BACKTRACE=1 cargo run -- <command>
```

---

## Release Process

### Versioning

We follow [Semantic Versioning](https://semver.org/):

- **MAJOR** – Incompatible API changes
- **MINOR** – Backward-compatible features
- **PATCH** – Backward-compatible bug fixes

### Changelog

All changes documented in `CHANGELOG.md`:

```markdown
## [2.1.0] - 2025-01-15

### Added
- Support for IFC4 advanced geometry
- New `arx query` command for ArxAddress queries

### Fixed
- Git merge conflict resolution bug
- IFC import memory leak

### Changed
- Improved performance of spatial queries
```

---

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

## Questions?

- Check existing issues and discussions
- Ask in GitHub Discussions
- Read the documentation

---

## Thank You!

Every contribution helps make ArxOS better. Thank you for being part of the project!

---

**See Also:**
- [Building Guide](./building.md) – Build instructions
- [Testing Guide](./testing.md) – Running tests
- [Architecture](../architecture.md) – System design
