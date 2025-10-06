# ArxOS Coding Standards

## Overview
This document outlines the coding standards and best practices for the ArxOS project to ensure code quality, consistency, and maintainability.

## Go Language Standards

### Type Aliases (Go 1.18+)

#### ✅ Use `any` instead of `interface{}`
- **Required**: Always use `any` instead of `interface{}` for empty interface types
- **Rationale**: `any` is the modern Go 1.18+ alias for `interface{}` and is more readable
- **Examples**:
  ```go
  // ✅ Correct
  func ProcessData(data any) error
  var config map[string]any
  
  // ❌ Incorrect
  func ProcessData(data interface{}) error
  var config map[string]interface{}
  ```

#### ✅ Use `comparable` for comparable types
- **Required**: Use `comparable` constraint for types that support `==` and `!=`
- **Examples**:
  ```go
  // ✅ Correct
  func FindDuplicates[T comparable](items []T) []T
  
  // ❌ Incorrect
  func FindDuplicates[T any](items []T) []T
  ```

### Interface Design

#### ✅ Prefer specific interfaces over empty interfaces
- **Required**: Design interfaces with specific methods rather than using `any`
- **Examples**:
  ```go
  // ✅ Correct
  type Logger interface {
      Info(msg string, fields ...any)
      Error(msg string, fields ...any)
  }
  
  // ❌ Incorrect
  type Service interface {
      Process(data any) any
  }
  ```

#### ✅ Use interface composition
- **Recommended**: Compose interfaces from smaller, focused interfaces
- **Examples**:
  ```go
  // ✅ Correct
  type ReadWriter interface {
      Reader
      Writer
  }
  ```

### Generic Constraints

#### ✅ Use appropriate type constraints
- **Required**: Use specific constraints when possible
- **Examples**:
  ```go
  // ✅ Correct
  func Max[T constraints.Ordered](a, b T) T
  
  // ❌ Incorrect
  func Max[T any](a, b T) T
  ```

### Error Handling

#### ✅ Use structured error types
- **Required**: Define specific error types instead of generic errors
- **Examples**:
  ```go
  // ✅ Correct
  type ValidationError struct {
      Field   string
      Message string
  }
  
  func (e ValidationError) Error() string {
      return fmt.Sprintf("validation failed for field %s: %s", e.Field, e.Message)
  }
  ```

### Configuration and Data Structures

#### ✅ Use `map[string]any` for flexible data
- **Required**: Use `map[string]any` for configuration and flexible data structures
- **Examples**:
  ```go
  // ✅ Correct
  type Config struct {
      Settings map[string]any `json:"settings"`
  }
  
  // ❌ Incorrect
  type Config struct {
      Settings map[string]interface{} `json:"settings"`
  }
  ```

## Code Organization

### Package Structure
- **Required**: Follow standard Go package organization
- **Required**: Use meaningful package names that describe functionality
- **Required**: Keep packages focused and cohesive

### Naming Conventions
- **Required**: Use descriptive names for types, functions, and variables
- **Required**: Follow Go naming conventions (exported vs unexported)
- **Required**: Use consistent naming patterns across the codebase

### Documentation
- **Required**: Document all exported types, functions, and methods
- **Required**: Use clear, concise documentation
- **Required**: Include examples for complex functionality

## Testing Standards

### Test Organization
- **Required**: Place tests in the same package as the code being tested
- **Required**: Use descriptive test names that explain the scenario
- **Required**: Follow the pattern: `TestFunctionName_Scenario_ExpectedResult`

### Test Data
- **Required**: Use `any` type for test data structures
- **Examples**:
  ```go
  // ✅ Correct
  func TestProcessData(t *testing.T) {
      testData := map[string]any{
          "name": "test",
          "value": 42,
      }
  }
  ```

## Performance Considerations

### Memory Allocation
- **Recommended**: Minimize allocations in hot paths
- **Recommended**: Use object pools for frequently allocated objects
- **Recommended**: Prefer value types over pointer types when appropriate

### Concurrency
- **Required**: Use appropriate synchronization primitives
- **Required**: Document concurrency assumptions
- **Required**: Handle context cancellation properly

## Security Standards

### Input Validation
- **Required**: Validate all external inputs
- **Required**: Use structured validation with specific error types
- **Required**: Sanitize data before processing

### Error Information
- **Required**: Don't expose sensitive information in error messages
- **Required**: Log errors appropriately without leaking data

## Tooling Integration

### Linting
- **Required**: All code must pass `golangci-lint` checks
- **Required**: Use configured linters including `gofmt`, `govet`, `golint`
- **Required**: Address all linter warnings before merging

### Formatting
- **Required**: Use `gofmt` for code formatting
- **Required**: Use `goimports` for import organization
- **Required**: Follow standard Go formatting conventions

## Review Process

### Code Review Checklist
- [ ] Code follows all coding standards
- [ ] No usage of `interface{}` (use `any` instead)
- [ ] Appropriate use of generics and type constraints
- [ ] Proper error handling
- [ ] Adequate test coverage
- [ ] Documentation is complete and accurate
- [ ] Performance implications considered
- [ ] Security considerations addressed

### Pre-commit Checks
- [ ] Code compiles without errors
- [ ] All tests pass
- [ ] Linting passes
- [ ] No `interface{}` usage detected
- [ ] Documentation updated if needed

## Enforcement

### Automated Checks
- **Required**: CI/CD pipeline must enforce all standards
- **Required**: Pre-commit hooks must run linting and formatting
- **Required**: Automated detection of `interface{}` usage

### Manual Review
- **Required**: All code changes must be reviewed
- **Required**: Reviewers must verify compliance with standards
- **Required**: Standards violations must be addressed before merging

## Migration Guidelines

### Legacy Code
- **Required**: Update legacy code to follow current standards
- **Required**: Prioritize high-impact areas first
- **Required**: Document migration progress

### New Code
- **Required**: All new code must follow current standards
- **Required**: No exceptions for "quick fixes" or "temporary code"
- **Required**: Standards apply to all code, including tests and examples

---

## Quick Reference

### Type Aliases
- `interface{}` → `any`
- Use `comparable` for comparable types
- Use specific constraints in generics

### Common Patterns
- `map[string]any` for flexible data
- Specific interfaces over empty interfaces
- Structured error types
- Proper context handling

### Tools
- `golangci-lint` for comprehensive linting
- `gofmt` and `goimports` for formatting
- Custom scripts for `interface{}` detection

This document should be reviewed and updated regularly to reflect evolving Go best practices and project needs.
