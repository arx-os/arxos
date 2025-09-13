// Package docs contains API documentation for ArxOS
//
//	@title			ArxOS API
//	@version		1.0
//	@description	ArxOS (Augmented Reality Extended Operating System) provides building management and AR visualization capabilities.
//	@description	This API enables CRUD operations for buildings, equipment, organizations, and user management.
//
//	@contact.name	ArxOS API Support
//	@contact.url	https://github.com/arx-os/arxos
//	@contact.email	support@arxos.io
//
//	@license.name	MIT
//	@license.url	https://opensource.org/licenses/MIT
//
//	@host		localhost:8080
//	@BasePath	/api/v1
//
//	@securityDefinitions.bearer	BearerAuth
//	@in							header
//	@name						Authorization
//	@description				JWT Bearer token authentication. Format: 'Bearer {token}'
//
//	@tag.name			Authentication
//	@tag.description	User authentication and session management
//
//	@tag.name			Buildings
//	@tag.description	Building and floor plan management
//
//	@tag.name			Equipment
//	@tag.description	Equipment management and status tracking
//
//	@tag.name			Organizations
//	@tag.description	Organization and team management
//
//	@tag.name			Upload
//	@tag.description	File upload and processing services
//
//	@tag.name			Health
//	@tag.description	System health and monitoring endpoints
//
//	@x-api-id	arxos-api-v1
package docs