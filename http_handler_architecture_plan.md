# HTTP Handler Architecture Fix Plan

## 🎯 **Clean Architecture Compliance Design**

### **1. Unified BaseHandler Interface**

```go
// internal/interfaces/http/handlers/base.go
package handlers

import (
    "context"
    "encoding/json"
    "net/http"
    "time"
    
    "github.com/arx-os/arxos/internal/domain"
    "github.com/arx-os/arxos/pkg/auth"
)

// BaseHandler defines the common HTTP handler interface following Clean Architecture
type BaseHandler interface {
    // HTTP Response Helpers
    RespondJSON(w http.ResponseWriter, statusCode int, data interface{})
    RespondError(w http.ResponseWriter, statusCode int, err error)
    
    // Request Validation
    ValidateContentType(r *http.Request, expectedType string) error
    ValidateRequest(r *http.Request) error
    
    // Authentication & Authorization
    GetUserFromContext(ctx context.Context) (*domain.User, error)
    RequireAuth(next http.Handler) http.Handler
    
    // Logging & Monitoring
    LogRequest(r *http.Request, statusCode int, duration time.Duration)
    LogError(r *http.Request, err error, statusCode int)
}

// BaseHandlerImpl provides concrete implementation of BaseHandler
type BaseHandlerImpl struct {
    logger     domain.Logger
    jwtManager *auth.JWTManager
    validator  domain.Validator
}

func (h *BaseHandlerImpl) RespondJSON(w http.ResponseWriter, statusCode int, data interface{}) {
    w.Header().Set("Content-Type", "application/json")
    w.WriteHeader(statusCode)
    
    if data != nil {
        json.NewEncoder(w).Encode(data)
    }
}

func (h *BaseHandlerImpl) RespondError(w http.ResponseWriter, statusCode int, err error) {
    h.logger.Error("HTTP error", "status", statusCode, "error", err)
    
    errorResponse := map[string]interface{}{
        "error":   http.StatusText(statusCode),
        "message": err.Error(),
        "status":  statusCode,
    }
    
    h.RespondJSON(w, statusCode, errorResponse)
}

// Other methods...
```

### **2. Clean Architecture Handler Structure**

```go
// Example: internal/interfaces/http/handlers/building_handler.go
package handlers

import (
    "context"
    "net/http"
    "time"

    "github.com/go-chi/chi/v5"
    "github.com/arx-os/arxos/internal/domain"
    "github.com/arx-os/arxos/internal/usecase"
)

// BuildingHandler implements Clean Architecture HTTP interface
type BuildingHandler struct {
    BaseHandler
    useCase usecase.BuildingUseCase
    logger  domain.Logger
}

// NewBuildingHandler creates new BuildingHandler with dependency injection
func NewBuildingHandler(
    base BaseHandler,
    useCase usecase.BuildingUseCase,
    logger domain.Logger,
) *BuildingHandler {
    return &BuildingHandler{
        BaseHandler: base,
        useCase:     useCase,
        logger:      logger,
    }
}

// ListBuildings implements GET /api/v1/buildings
func (h *BuildingHandler) ListBuildings(w http.ResponseWriter, r *http.Request) {
    start := time.Now()
    ctx := r.Context()
    
    defer func() {
        h.LogRequest(r, http.StatusOK, time.Since(start))
    }()

    // Parse query parameters
    filter := h.parseBuildingFilter(r)
    
    // Call use case (Clean Architecture)
    buildings, err := h.useCase.ListBuildings(ctx, filter)
    if err != nil {
        h.RespondError(w, http.StatusInternalServerError, err)
        return
    }

    // Transform domain entities to HTTP response models
    response := h.transformBuildingsToResponse(buildings)
    h.RespondJSON(w, http.StatusOK, response)
}

// CreateBuilding implements POST /api/v1/buildings)
func (h *BuildingHandler) CreateBuilding(w http.ResponseWriter, r *http.Request) {
    start := time.Now()
    ctx := r.Context()
    
    defer func() {
        h.LogRequest(r, http.StatusCreated, time.Since(start))
    }()

    // Validate content type
    if err := h.ValidateContentType(r, "application/json"); err != nil {
        h.RespondError(w, http.StatusBadRequest, err)
        return
    }

    // Parse request body
    var req domain.CreateBuildingRequest
    if err := h.parseRequestBody(r, &req); err != nil {
        h.RespondError(w, http.StatusBadRequest, err)
        return
    }

    // Call use case (Clean Architecture)
    building, err := h.useCase.CreateBuilding(ctx, &req)
    if err != nil {
        h.RespondError(w, http.StatusInternalServerError, err)
        return
    }

    // Transform domain entity to HTTP response model
    response := h.transformBuildingToResponse(building)
    h.RespondJSON(w, http.StatusCreated, response)
}

// Other CRUD methods follow same pattern...
```

### **3. Dependency Injection Container Integration**

```go
// internal/app/container.go - Add HTTP handlers
type Container struct {
    // ... existing fields ...
    
    // HTTP Handlers
    buildingHandler    *handlers.BuildingHandler
    authHandler        *handlers.AuthHandler
    equipmentHandler   *handlers.EquipmentHandler
    spatialHandler     *handlers.SpatialHandler
    mobileHandlers     *handlers.MobileHandlers
}

func (c *Container) initHTTPHandlers() {
    baseHandler := handlers.NewBaseHandler(c.logger, c.jwtManager, c.validator)
    
    c.buildingHandler = handlers.NewBuildingHandler(
        baseHandler,
        c.GetBuildingUseCase(),
        c.logger,
    )
    
    c.authHandler = handlers.NewAuthHandler(
        baseHandler,
        c.GetUserUseCase(),
        c.jwtManager,
        c.logger,
    )
    
    // Other handlers...
}
```

### **4. Mobile Handler Integration**

```go
// internal/interfaces/http/handlers/mobile_handlers.go
package handlers

// MobileHandlers groups all mobile-specific endpoints
type MobileHandlers struct {
    AuthHandler        *AuthHandler
    EquipmentHandler   *EquipmentHandler
    SpatialHandler     *SpatialHandler
}

// NewMobileHandlers creates mobile handlers with proper dependencies
func NewMobileHandlers(
    base BaseHandler,
    userUC usecase.UserUseCase,
    buildingUC usecase.BuildingUseCase,
    equipmentUC usecase.EquipmentUseCase,
    spatialRepo domain.SpatialRepository,
    logger domain.Logger,
) *MobileHandlers {
    return &MobileHandlers{
        AuthHandler: NewAuthHandler(base, userUC, logger),
        EquipmentHandler: NewEquipmentHandler(base, buildingUC, equipmentUC, logger),
        SpatialHandler: NewSpatialHandler(base, buildingUC, equipmentUC, spatialRepo, logger),
    }
}
```

### **5. Router Configuration Fix**

```go
// internal/interfaces/http/router.go
func NewRouter(config *RouterConfig) chi.Router {
    router := chi.NewRouter()
    
    // Apply middleware in correct order
    router.Use(middleware.RequestID)
    router.Use(middleware.RealIP)
    router.Use(middleware.Logger)
    router.Use(middleware.Recoverer)
    router.Use(middleware.Timeout(60 * time.Second))
    router.Use(middleware.NewCompressor().Handler()) // Add compression
    
    // Get handlers from container
    handlers := config.Container.GetHTTPHandlers()
    
    // Public routes
    router.Get("/health", handlers.APIHandler.HandleHealth)
    router.Get("/api/info", handlers.APIHandler.HandleAPIInfo)
    
    // Protected API routes
    router.Route("/api/v1", func(r chi.Router) {
        // Apply authentication middleware
        r.Use(authMiddleware(config.JWTManager))
        
        // Building endpoints
        r.Route("/buildings", func(r chi.Router) {
            r.Get("/", handlers.BuildingHandler.ListBuildings)
            r.Post("/", handlers.BuildingHandler.CreateBuilding)
            r.Get("/{id}", handlers.BuildingHandler.GetBuilding)
            r.Put("/{id}", handlers.BuildingHandler.UpdateBuilding)
            r.Delete("/{id}", handlers.BuildingHandler.DeleteBuilding)
        })
        
        // Mobile endpoints
        r.Route("/mobile", func(r chi.Router) {
            r.Route("/auth", func(r chi.Router) {
                r.Post("/login", handlers.MobileHandlers.AuthHandler.Login)
                r.Post("/register", handlers.MobileHandlers.AuthHandler.Register)
                r.Post("/refresh", handlers.MobileHandlers.AuthHandler.RefreshToken)
                r.Group(func(r chi.Router) {
                    r.Use(authMiddleware(config.JWTManager))
                    r.Get("/profile", handlers.MobileHandlers.AuthHandler.Profile)
                    r.Post("/logout", handlers.MobileHandlers.AuthHandler.Logout)
                })
            })
            
            r.Route("/equipment", func(r chi.Router) {
                r.Use(authMiddleware(config.JWTManager))
                r.Get("/building/{buildingId}", handlers.MobileHandlers.EquipmentHandler.GetByBuilding)
                r.Get("/{id}", handlers.MobileHandlers.EquipmentHandler.GetByID)
            })
            
            r.Route("/spatial", func(r chi.Router) {
                r.Use(authMiddleware(config.JWTManager))
                r.Post("/anchors", handlers.MobileHandlers.SpatialHandler.CreateAnchor)
                r.Get("/anchors/building/{buildingId}", handlers.MobileHandlers.SpatialHandler.GetAnchorsByBuilding)
                r.Get("/nearby/equipment", handlers.MobileHandlers.SpatialHandler.GetNearbyEquipment)
            })
        })
    })
    
    return router
}
```

## 📦 **Required Package Updates**

### **go.mod additions:**
```go
require (
    github.com/go-chi/chi/v5 v5.0.10
    github.com/golang-jwt/jwt/v5 v5.2.0
    github.com/go-chi/cors v1.2.1
    gopkg.in/yaml.v2 v2.4.0
    github.com/stretchr/testify v1.8.4 // for testing
)
```

## 🧪 **Testing Strategy**

```go
// internal/interfaces/http/handlers/building_handler_test.go
func TestBuildingHandler_CreateBuilding(t *testing.T) {
    // Arrange
    mockUseCase := &MockBuildingUseCase{}
    mockLogger := &MockLogger{}
    baseHandler := &MockBaseHandler{}
    
    handler := NewBuildingHandler(baseHandler, mockUseCase, mockLogger)
    
    // Create test request
    reqBody := CreateBuildingRequest{
        Name:    "Test Building",
        Address: "123 Test St",
    }
    
    req := createTestRequest("POST", "/api/v1/buildings", reqBody)
    
    // Setup expectations
    expectedBuilding := &domain.Building{
        ID:   "test-id",
        Name: "Test Building",
    }
    mockUseCase.On("CreateBuilding", mock.Anything, mock.Anything).Return(expectedBuilding, nil)
    
    // Act
    w := httptest.NewRecorder()
    handler.CreateBuilding(w, req)
    
    // Assert
    assert.Equal(t, http.StatusCreated, w.Code)
    mockUseCase.AssertExpectations(t)
}
```

## 🚀 **Implementation Phases**

### **Phase 1: Foundation (Days 1-2)**
1. Create unified BaseHandler interface and implementation
2. Add missing package dependencies to go.mod
3. Fix import statements in all handler files
4. Update Container to inject handler dependencies

### **Phase 2: Handler Refactoring (Days 3-4)**
1. Refactor BuildingHandler to use Clean Architecture
2. Refactor AuthHandler with proper JWT integration
3. Refactor EquipmentHandler with use case calls
4. Update SpatialHandler with repository integration

### **Phase 3: Mobile Handler Implementation (Days 5-6)**
1. Complete MobileAuthHandler implementation
2. Complete MobileEquipmentHandler implementation  
3. Complete MobileSpatialHandler implementation
4. Create unified MobileHandlers group

### **Phase 4: Router & Middleware (Days 7-8)**
1. Fix router configuration with proper middleware
2. Implement authentication middleware
3. Add CORS configuration
4. Add rate limiting and security headers

### **Phase 5: Testing & Integration (Days 9-10)**
1. Write comprehensive handler tests
2. Integration testing with real use cases
3. End-to-end API testing
4. Performance optimization

### **Phase 6: Documentation & Cleanup (Day 11)**
1. Update API documentation
2. Clean up unused code
3. Performance benchmarking
4. Security audit

## 📊 **Success Metrics**

- ✅ All handlers compile without errors
- ✅ Clean Architecture compliance verified
- ✅ End-to-end API testing passes
- ✅ Authentication middleware working
- ✅ Mobile endpoints functional
- ✅ Performance tests pass
- ✅ Security scans clean
- ✅ 80%+ test coverage

## 🎯 **Expected Outcome**

After implementation, ArxOS will have:
1. **Proper Clean Architecture**: HTTP handlers only interface layer, use cases handle business logic
2. **Robust Error Handling**: Consistent error responses and logging
3. **Secure Authentication**: JWT-based auth with refresh tokens
4. **Mobile-First API**: Optimized endpoints for React Native integration
5. **Production Ready**: Rate limiting, CORS, compression, monitoring
6. **Testable Architecture**: Mockable dependencies and comprehensive tests

This refactoring will result in enterprise-grade HTTP handler architecture that properly follows Clean Architecture principles while providing robust mobile and web API endpoints for ArxOS.
