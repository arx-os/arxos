## Description

Brief description of the changes in this PR.

## Type of Change

- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update
- [ ] Performance improvement
- [ ] Code refactoring
- [ ] Test improvements
- [ ] Mobile app changes

## Related Issues

Fixes #(issue number)
Closes #(issue number)
Related to #(issue number)

## Changes Made

### Core Changes
- [ ] Added new functionality
- [ ] Fixed existing bugs
- [ ] Updated architectural components

### Testing & Quality
- [ ] Added unit tests
- [ ] Added integration tests  
- [ ] Updated existing tests
- [ ] Updated test documentation

### Documentation
- [ ] Updated code comments
- [ ] Updated README files
- [ ] Updated API documentation
- [ ] Added or updated architectural diagrams

### Dependencies & Configuration
- [ ] Updated Go dependencies
- [ ] Updated CI/CD pipelines
- [ ] Updated Docker configurations
- [ ] Updated mobile dependencies (if applicable)

## Testing

### Automated Testing (CI/CD)
Our CI pipeline automatically runs the following tests:

#### ✅ **Code Quality & Linting**
- Go linter (golangci-lint) with custom rules
- Go formatting check (gofmt)
- Go modules validation (go mod tidy)
- Static analysis (golangci-lint)

#### ✅ **Unit Tests**
- Unit tests with race detection
- Code coverage (minimum 70% threshold)
- Performance benchmarks (for main branch)

#### ✅ **Integration Tests**
- PostGIS database integration tests
- Redis cache integration tests
- IfcOpenShell service integration tests
- Full application integration tests

#### ✅ **Mobile Tests** (if applicable)
- React Native linting
- Mobile unit tests with coverage
- iOS simulator build verification  
- Android debug build verification

#### ✅ **Security & Dependencies**
- Security vulnerability scanning (gosec)
- Dependency vulnerability checking
- Static security analysis

#### ✅ **Build & Deployment**
- Multi-platform binary builds
- Docker image building and testing
- Docker Compose integration testing

### Manual Testing Checklist
- [ ] **CLI Testing**: Verified CLI commands work correctly
- [ ] **API Testing**: Tested REST API endpoints (if applicable)
- [ ] **Database Testing**: Verified database migrations and queries
- [ ] **Mobile Testing**: Tested on iOS/Android devices (if applicable)
- [ ] **Edge Cases**: Tested error conditions and edge cases
- [ ] **Performance**: Verified no performance regressions

## Architectural Impact

### Service Architecture
- [ ] No changes to service interfaces
- [ ] Updated service implementations
- [ ] Added new internal services
- [ ] Modified external service integrations

### Database Schema
- [ ] No database changes
- [ ] Database migrations included
- [ ] Updated spatial data handling
- [ ] Modified indexing strategies

### API Changes
- [ ] No API changes (backward compatible)
- [ ] Added new API endpoints
- [ ] Modified existing API responses
- [ ] Breaking API changes (documented below)

### Mobile Integration
- [ ] No mobile app changes
- [ ] Updated mobile API clients
- [ ] Added new mobile functionality
- [ ] Modified AR/spatial features

## Performance Considerations

### Benchmarks
- [ ] No performance impact expected
- [ ] Performance improvements measured
- [ ] Performance regression possible (monitored)

### Resource Usage
- [ ] No memory/CPU impact
- [ ] Reduced memory/CPU usage
- [ ] Increased memory/CPU usage (justified below)

## Breaking Changes

### Database Changes
- [ ] No breaking database changes
- [ ] Database migrations required
- [ ] Schema breaking changes (list below)

### API Breaking Changes
- [ ] No breaking API changes
- [ ] Endpoint deprecations
- [ ] Response format changes
- [ ] Authentication changes

### Configuration Changes
- [ ] No config changes
- [ ] New required configuration
- [ ] Deprecated configuration options

**If breaking changes are present, document them here:**
```
- Change 1: Detailed description
- Change 2: Detailed description  
- Migration path: How to migrate
```

## Deployment Notes

### Docker/Container Changes
- [ ] No Docker changes
- [ ] Updated Docker base images
- [ ] New Docker services
- [ ] Changed Docker networking

### Environment Variables
- [ ] No new environment variables
- [ ] New optional environment variables
- [ ] New required environment variables (documented)

### Dependencies
- [ ] No dependency changes
- [ ] Updated dependencies (backward compatible)
- [ ] New dependencies added
- [ ] Dependency version bumps

## Code Review Checklist

### Code Quality
- [ ] Code follows project style guidelines
- [ ] Functions are small and focused
- [ ] Error handling is appropriate
- [ ] Logging is comprehensive but not excessive

### Testing
- [ ] Tests are comprehensive and meaningful
- [ ] Tests cover edge cases and error conditions
- [ ] Test data is realistic and varied
- [ ] Integration tests verify end-to-end functionality

### Documentation
- [ ] Code is well-commented for complex logic
- [ ] Public APIs are documented
- [ ] README files updated if necessary
- [ ] Architectural decisions are documented

### Security
- [ ] No sensitive data exposed in logs
- [ ] Input validation is implemented
- [ ] Authentication/authorization is appropriate
- [ ] Database queries are properly parameterized

## Additional Notes

### Known Issues
- [ ] No known issues
- [ ] Known issues documented below

```
- Issue 1: Description and proposed solution
- Issue 2: Description and proposed solution
```

### Future Work
- [ ] No follow-up work required
- [ ] Follow-up work documented in referenced issues
- [ ] Architectural improvements identified

### Special Considerations
- [ ] None
- [ ] Deployment timing considerations
- [ ] Configuration changes required
- [ ] Communication needed with other teams

## Screenshots (if applicable)

For UI changes, mobile app changes, or architectural diagrams:

### Before
<!-- Screenshot or diagram before changes -->

### After  
<!-- Screenshot or diagram after changes -->

---

**Reviewer Guidelines:**
1. Focus on architectural consistency and maintainability
2. Verify integration test coverage for service interactions
3. Check that spatial data operations are properly tested
4. Ensure mobile compatibility (if applicable)
5. Validate security considerations
6. Confirm no breaking changes unless explicitly documented