// Package docs provides OpenAPI/Swagger documentation for the ArxOS API.
//
//	@title			ArxOS Building Intelligence API
//	@version		2.0.0
//	@description	REST API for ArxOS Building Information Management System
//	@termsOfService	https://arxos.io/terms
//
//	@contact.name	ArxOS Support
//	@contact.url	https://arxos.io/support
//	@contact.email	support@arxos.io
//
//	@license.name	Apache 2.0
//	@license.url	http://www.apache.org/licenses/LICENSE-2.0.html
//
//	@host		localhost:8080
//	@BasePath	/api/v1
//
//	@securityDefinitions.apikey	BearerAuth
//	@in							header
//	@name						Authorization
//	@description				Type "Bearer" followed by a space and JWT token.
//
//	@tag.name			Authentication
//	@tag.description	User authentication and session management
//
//	@tag.name			Buildings
//	@tag.description	Building and floor plan management
//
//	@tag.name			Equipment
//	@tag.description	Equipment and device management
//
//	@tag.name			Rooms
//	@tag.description	Room and space management
//
//	@tag.name			Users
//	@tag.description	User account management
//
//	@tag.name			Organizations
//	@tag.description	Organization management
//
//	@tag.name			Search
//	@tag.description	Search and discovery operations
package docs

import (
	_ "github.com/swaggo/swag"
)