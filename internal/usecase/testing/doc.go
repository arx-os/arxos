// Package testing provides test utilities for the use case layer.
//
// This package contains mock implementations of domain repositories,
// test fixtures for creating domain entities, and custom assertions
// for use case testing.
//
// # Mock Repositories
//
// Mock repositories implement domain repository interfaces using
// testify/mock for flexible test expectations:
//
//	mockRepo := new(testing.MockBuildingRepository)
//	mockRepo.On("GetByID", mock.Anything, "building-123").Return(testBuilding, nil)
//
// # Test Fixtures
//
// Fixtures provide convenient ways to create test data:
//
//	building := testing.CreateTestBuilding()
//	user := testing.CreateTestUserWith(
//	    testing.WithUserEmail("test@example.com"),
//	)
//
// # Organization
//
// Mocks are organized by domain area across multiple files:
//   - mocks_core.go: Core domain repositories (Building, User, Organization, etc.)
//   - mocks_versioncontrol.go: Version control repositories (Branch, Commit, PR, Issue, etc.)
//   - mocks_integration.go: Integration repositories (BAS, IFC, Spatial)
//   - mocks_infrastructure.go: Infrastructure mocks (Cache, Logger, Database)
//   - fixtures.go: Test data creation helpers
//
// # Best Practices
//
// When writing tests:
//  1. Import with alias to avoid conflict with stdlib testing package
//  2. Use mock.Anything for context parameters unless testing specific contexts
//  3. Always call AssertExpectations(t) to verify mock calls
//  4. Use fixtures for consistent test data
package testing
