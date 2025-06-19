// main.go
package main

import (
	"log"
	"net/http"
	"os"
	"os/signal"
	"syscall"

	"arxline/db"
	"arxline/handlers"
	"arxline/middleware/auth"
	"arxline/models"

	"github.com/go-chi/chi/v5"
	"github.com/go-chi/chi/v5/middleware"
	"github.com/joho/godotenv"
	"github.com/rs/cors"
)

func main() {
	godotenv.Load() // Load .env file
	// Initialize database
	db.Connect()
	db.Migrate()
	models.SeedCategories(db.DB)

	// Set up router
	r := chi.NewRouter()
	r.Use(middleware.Logger)
	r.Use(cors.AllowAll().Handler)

	r.Route("/api", func(r chi.Router) {
		r.Post("/register", handlers.Register)
		r.Post("/login", handlers.Login)

		r.Group(func(r chi.Router) {
			r.Use(auth.RequireAuth)
			r.Get("/floor/svg", handlers.ServeFloorSVG)
			r.Get("/object/{objectId}/info", handlers.ServeObjectInfo)
			r.Post("/object/{objectId}/comment", handlers.PostObjectComment)

			r.Get("/projects", handlers.ListProjects)
			r.Post("/projects", handlers.CreateProject)
			r.Get("/projects/{id}", handlers.GetProject)

			// New endpoints (stubs to be implemented)
			r.Get("/buildings", handlers.ListBuildings)
			r.Post("/buildings", handlers.CreateBuilding)
			r.Get("/buildings/{id}", handlers.GetBuilding)
			r.Put("/buildings/{id}", handlers.UpdateBuilding)
			r.Get("/buildings/{id}/floors", handlers.ListFloors)
			r.Post("/markup", handlers.SubmitMarkup)
			r.Get("/logs/{building_id}", handlers.GetLogs)
			r.Get("/me", handlers.Me)
			r.Get("/markups", db.ListMarkups)
			r.Delete("/markup/{id}", handlers.DeleteMarkup)

			// HTMX endpoints for dynamic select loading
			r.Get("/buildings", handlers.HTMXListBuildings)
			r.Get("/buildings/{id}/floors", handlers.HTMXListFloors)

			r.Post("/drawings", handlers.CreateDrawing)
			r.Get("/drawings/{drawingID}/last_modified", handlers.GetDrawingLastModified)

			r.Put("/comment/{id}", handlers.EditComment)
			r.Delete("/comment/{id}", handlers.DeleteComment)

			// BIM Object endpoints (edit)
			r.Group(func(r chi.Router) {
				r.Use(auth.RequireRole("admin", "editor"))
				// r.Patch("/wall/{id}", handlers.UpdateWall)
				// r.Post("/wall/{id}/lock", handlers.LockWall)
				// r.Post("/wall/{id}/unlock", handlers.UnlockWall)
				// r.Post("/wall/{id}/assign", handlers.AssignWall)
				// r.Post("/wall/{id}/status", handlers.UpdateWallStatus)
				// r.Patch("/door/{id}", handlers.UpdateDoor)
				// r.Post("/door/{id}/lock", handlers.LockDoor)
				// r.Post("/door/{id}/unlock", handlers.UnlockDoor)
				// r.Post("/door/{id}/assign", handlers.AssignDoor)
				// r.Post("/door/{id}/status", handlers.UpdateDoorStatus)
				r.Patch("/room/{id}", handlers.UpdateRoom)
				r.Post("/room/{id}/lock", handlers.LockRoom)
				r.Post("/room/{id}/unlock", handlers.UnlockRoom)
				r.Post("/room/{id}/assign", handlers.AssignRoom)
				r.Post("/room/{id}/status", handlers.UpdateRoomStatus)
				// r.Patch("/window/{id}", handlers.UpdateWindow)
				// r.Post("/window/{id}/lock", handlers.LockWindow)
				// r.Post("/window/{id}/unlock", handlers.UnlockWindow)
				// r.Post("/window/{id}/assign", handlers.AssignWindow)
				// r.Post("/window/{id}/status", handlers.UpdateWindowStatus)
				r.Patch("/device/{id}", handlers.UpdateDeviceDetails)
				r.Post("/device/{id}/lock", handlers.LockDevice)
				r.Post("/device/{id}/unlock", handlers.UnlockDevice)
				r.Post("/device/{id}/assign", handlers.AssignDevice)
				r.Post("/device/{id}/status", handlers.UpdateDeviceStatus)
				r.Patch("/label/{id}", handlers.UpdateLabel)
				r.Post("/label/{id}/lock", handlers.LockLabel)
				r.Post("/label/{id}/unlock", handlers.UnlockLabel)
				r.Post("/label/{id}/assign", handlers.AssignLabel)
				r.Post("/label/{id}/status", handlers.UpdateLabelStatus)
				r.Patch("/zone/{id}", handlers.UpdateZone)
				r.Post("/zone/{id}/lock", handlers.LockZone)
				r.Post("/zone/{id}/unlock", handlers.UnlockZone)
				r.Post("/zone/{id}/assign", handlers.AssignZone)
				r.Post("/zone/{id}/status", handlers.UpdateZoneStatus)
			})

			// Paginated list endpoints for BIM objects
			// r.Get("/walls", handlers.ListWalls)
			r.Get("/rooms", handlers.ListRooms)
			// r.Get("/doors", handlers.ListDoors)
			// r.Get("/windows", handlers.ListWindows)
			r.Get("/devices", handlers.ListDevices)
			r.Get("/labels", handlers.ListLabels)
			r.Get("/zones", handlers.ListZones)

			// BIM Export endpoints
			r.Get("/bim/export/json", handlers.ExportBIMAsJSON)
			// r.Get("/bim/export/geojson", handlers.ExportBIMAsGeoJSON)
			r.Get("/bim/export/ifc", handlers.ExportBIMAsIFC)
			r.Get("/bim/export/dxf", handlers.ExportBIMAsDXF)
			r.Get("/bim/export/svg", handlers.ExportBIMAsSVG)

			// Category admin endpoints (admin only)
			r.Group(func(r chi.Router) {
				r.Use(auth.RequireRole("admin"))
				r.Post("/categories", handlers.CreateCategory)
				r.Get("/categories", handlers.ListCategories)
				r.Put("/categories/{id}", handlers.UpdateCategory)
				r.Delete("/categories/{id}", handlers.DeleteCategory)
				// User-category permission admin endpoints
				r.Post("/user-category-permissions", handlers.AssignUserCategoryPermission)
				r.Get("/user-category-permissions", handlers.ListUserCategoryPermissions)
				r.Delete("/user-category-permissions/{id}", handlers.RevokeUserCategoryPermission)
			})

			r.Get("/audit-logs", handlers.ListAuditLogs)

			r.Post("/buildings/{id}/chat", handlers.PostChatMessage)
			r.Get("/buildings/{id}/chat", handlers.ListChatMessages)

			r.Get("/svg-objects", handlers.ListSVGObjects)

			r.Get("/api/properties", handlers.HTMXListBuildingsSidebar)

			r.Get("/api/device-catalog", handlers.HTMXDeviceCatalog)

			r.Get("/device/{id}", handlers.GetDevice)

			r.Post("/routes", handlers.CreateRoute)
			r.Get("/route/{id}", handlers.GetRoute)
			r.Patch("/route/{id}", handlers.UpdateRoute)

			r.Get("/api/object-types", handlers.GetObjectTypesRegistry)
			r.Get("/api/behavior-profiles", handlers.GetBehaviorProfilesRegistry)

			r.Post("/floor/{id}/snapshot", handlers.SaveFloorSnapshot)
			r.Post("/floor/{id}/undo", handlers.UndoFloorVersion)
			r.Post("/floor/{id}/redo", handlers.RedoFloorVersion)
			r.Get("/floor/{id}/history", handlers.ListFloorHistory)
			r.Get("/floor/{id}/version/{version}", handlers.GetFloorVersion)
			r.Delete("/floor/{id}/version/{version}", handlers.DeleteFloorVersion)
			r.Post("/floor/{id}/restore/{version}", handlers.RestoreFloorVersion)
			r.Get("/floor/{id}/compare", handlers.CompareFloorVersions)
		})
	})

	// Graceful shutdown
	go func() {
		log.Println("🚀 Server running on :8080")
		if err := http.ListenAndServe(":8080", r); err != nil {
			log.Fatalf("Server failed: %v", err)
		}
	}()

	// Wait for termination signal
	sig := make(chan os.Signal, 1)
	signal.Notify(sig, os.Interrupt, syscall.SIGTERM)
	<-sig

	log.Println("Shutting down server...")
	db.Close()
	log.Println("Server stopped")
}
