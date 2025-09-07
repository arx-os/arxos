# Contributing to ArxOS

Thank you for your interest in contributing to ArxOS! We're building the future of building intelligence - where buildings become queryable databases.

## Code of Conduct

- Be respectful and inclusive
- Focus on constructive criticism
- Help others learn and grow
- Keep discussions professional

## How to Contribute

### 1. Report Bugs

Found a bug? Please create an issue with:
- Clear title and description
- Steps to reproduce
- Expected vs. actual behavior
- System information (OS, Rust version, PostgreSQL version)
- Error messages or logs

**Example Bug Report:**
```markdown
Title: TRACE command fails with circular references

Description: When tracing electrical paths with circular references, the command hangs.

Steps:
1. Run `arxos-terminal`
2. Enter: `TRACE outlet_2B UPSTREAM`
3. System hangs if circuit has circular reference

Expected: Should detect and handle circular references
System: macOS 14.0, Rust 1.75, PostgreSQL 15
```

### 2. Suggest Features

Have an idea? Open a discussion first:
- Explain the problem it solves
- Provide use cases
- Consider backward compatibility
- Discuss implementation approach

### 3. Submit Code

#### Setup Development Environment

```bash
# Fork and clone
git clone https://github.com/YOUR_USERNAME/arxos.git
cd arxos

# Install dependencies
brew install postgresql postgis
cargo build

# Setup database
createdb arxos_dev
psql arxos_dev < schema.sql

# Run tests
cargo test
```

#### Code Standards

**Rust Style:**
- Follow standard Rust conventions
- Use `cargo fmt` before committing
- Run `cargo clippy` and fix warnings
- Add tests for new functionality
- Document public APIs

**Commit Messages:**
```
type: brief description

Longer explanation if needed. Explain what and why,
not how. Reference issues like #123.

Co-authored-by: Name <email>
```

Types: `feat`, `fix`, `docs`, `test`, `refactor`, `perf`, `style`, `chore`

**Examples:**
```
feat: add circuit load balancing algorithm

Implements automatic load distribution across circuits
using graph traversal. Prevents overload conditions
by redistributing connections.
Closes #45.

fix: correct spatial index for 3D queries

PostGIS spatial index wasn't properly handling Z-axis.
Added 3D index for height-based queries.
```

#### Testing

**Unit Tests:**
```rust
#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_building_path_parsing() {
        let path = "/building_42/electrical/circuits/15";
        let parsed = BuildingPath::parse(path).unwrap();
        assert_eq!(parsed.building_id, "building_42");
        assert_eq!(parsed.system, "electrical");
    }
}
```

**Integration Tests:**
```rust
// tests/query_integration.rs
#[tokio::test]
async fn test_trace_upstream() {
    let db = setup_test_db().await;
    let engine = QueryEngine::new(db);
    
    let result = engine.execute("TRACE outlet_2B UPSTREAM").await;
    assert!(result.unwrap().contains("main_panel"));
}
```

**Run All Tests:**
```bash
cargo test
cargo test --all-features
```

### 4. Improve Documentation

Documentation is crucial! You can help by:
- Fixing typos and grammar
- Adding examples
- Clarifying confusing sections
- Creating tutorials
- Writing guides for specific use cases

**Documentation Files:**
- `README.md` - Quick start and overview
- `ARCHITECTURE.md` - System design and structure
- `CONTRIBUTING.md` - This file
- `schema.sql` - Database schema documentation

### 5. Review Pull Requests

Help review others' PRs:
- Test the changes locally
- Review code quality
- Check for breaking changes
- Suggest improvements
- Be constructive and kind

## Pull Request Process

1. **Fork and Branch**
   ```bash
   git checkout -b feature/amazing-feature
   ```

2. **Make Changes**
   - Write clean, documented code
   - Add tests
   - Update documentation

3. **Test Thoroughly**
   ```bash
   cargo fmt
   cargo clippy
   cargo test
   cargo build --release
   ```

4. **Submit PR**
   - Clear title and description
   - Reference related issues
   - Include screenshots if UI changes
   - List breaking changes

5. **Address Review**
   - Respond to feedback
   - Make requested changes
   - Keep PR updated with main

## Development Guidelines

### Project Structure

```
src/
├── main.rs         # Entry point and CLI
├── models.rs       # Core data models (BuildingObject, Location, etc.)
├── database.rs     # PostgreSQL integration
├── terminal.rs     # Terminal interface and commands
└── query.rs        # SQL-like query engine
```

### Key Principles

1. **Terminal First**: Terminal is the primary interface
2. **Offline First**: Must work without internet
3. **Hierarchical Paths**: Buildings as file systems
4. **Graph Relationships**: Everything is connected
5. **SQL Queries**: Familiar query language
6. **Progressive Enhancement**: Start simple, add complexity

### Performance Considerations

- Queries should complete in < 100ms
- Spatial queries use PostGIS indexes
- Graph traversal uses BFS/DFS with cycle detection
- WebSocket uses binary protocol for efficiency
- State sync is delta-based

### Security

- Never store credentials in code
- Validate all user input
- Use parameterized queries
- Sanitize file paths
- Rate limit API endpoints
- Authenticate WebSocket connections

## Areas Needing Help

### High Priority
- [ ] PDF floor plan parsing
- [ ] Advanced circuit tracing algorithms
- [ ] Time-series query optimization
- [ ] AR marker detection
- [ ] BILT smart contracts

### Good First Issues
- [ ] Add more SQL query examples
- [ ] Improve error messages
- [ ] Add terminal color themes
- [ ] Create Docker setup
- [ ] Write integration tests

### Documentation
- [ ] Video tutorials
- [ ] API client libraries
- [ ] Query cookbook
- [ ] Deployment guides

## Getting Help

### Discord
Join our Discord for real-time help: discord.gg/arxos

### Office Hours
Weekly community calls on Thursdays at 2 PM EST

### Documentation
- [Architecture Guide](ARCHITECTURE.md)
- [README](README.md)

## Recognition

Contributors are recognized in:
- [AUTHORS.md](AUTHORS.md) file
- Release notes
- Project website
- Annual contributor report

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

## Questions?

Feel free to:
- Open an issue for questions
- Ask in Discord
- Email: contribute@arxos.io

Thank you for helping make buildings queryable! 🏢💻