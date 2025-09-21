package api

import (
	"github.com/gin-gonic/gin"
	swaggerFiles "github.com/swaggo/files"
	ginSwagger "github.com/swaggo/gin-swagger"
)

// @title ArxOS API
// @version 2.0
// @description Building Information Management System API
// @termsOfService https://arxos.io/terms

// @contact.name API Support
// @contact.url https://arxos.io/support
// @contact.email support@arxos.io

// @license.name MIT
// @license.url https://opensource.org/licenses/MIT

// @host localhost:8080
// @BasePath /api/v1

// @securityDefinitions.apikey ApiKeyAuth
// @in header
// @name Authorization

// @securityDefinitions.basic BasicAuth

// SwaggerInfo holds exported Swagger Info for programmatic lookup
var SwaggerInfo = struct {
	Version     string
	Host        string
	BasePath    string
	Schemes     []string
	Title       string
	Description string
}{
	Version:     "2.0",
	Host:        "localhost:8080",
	BasePath:    "/api/v1",
	Schemes:     []string{"http", "https"},
	Title:       "ArxOS API",
	Description: "Building Information Management System API",
}

// SetupSwagger configures Swagger documentation endpoints
func SetupSwagger(router *gin.Engine) {
	// Swagger endpoint
	router.GET("/swagger/*any", ginSwagger.WrapHandler(swaggerFiles.Handler))
}

// SuccessResponse represents a successful API response
// @Description Standard success response
type SuccessResponse struct {
	Success bool        `json:"success" example:"true"`
	Data    interface{} `json:"data"`
}

// ErrorResponse represents an error API response
// @Description Standard error response
type ErrorResponse struct {
	Success bool   `json:"success" example:"false"`
	Error   string `json:"error" example:"Internal server error"`
	Code    string `json:"code,omitempty" example:"ERR_INTERNAL"`
}

// PaginatedResponse represents a paginated API response
// @Description Paginated response with metadata
type PaginatedResponse struct {
	Success bool        `json:"success" example:"true"`
	Data    interface{} `json:"data"`
	Meta    Pagination  `json:"meta"`
}

// Pagination represents pagination metadata
// @Description Pagination information
type Pagination struct {
	Total      int `json:"total" example:"100"`
	Page       int `json:"page" example:"1"`
	PerPage    int `json:"per_page" example:"20"`
	TotalPages int `json:"total_pages" example:"5"`
}

// AuthRequest represents authentication request
// @Description Authentication credentials
type AuthRequest struct {
	Email    string `json:"email" binding:"required,email" example:"user@example.com"`
	Password string `json:"password" binding:"required,min=8" example:"password123"`
}

